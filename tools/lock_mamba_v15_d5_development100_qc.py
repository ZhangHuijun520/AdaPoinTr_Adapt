#!/usr/bin/env python3
"""Freeze the global D5 development100 QC lock from three frozen batches."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


EXPECTED_SOURCE_LOCK_RECEIPT_SHA256 = (
    "64634d5c31a0d27ce27d10645d4bffa7f28cc22bf09f178ff363acf4c1d49015"
)
EXPECTED_SOURCE_LOCK_MANIFEST_SHA256 = (
    "9d512638287e782b31f83b566429990673e8af70bd5d01686654c2d0eb8ffa0b"
)
EXPECTED_D3_MANIFEST_SHA256 = (
    "3892dbcad93418834daf1c1abb4915c8e73a0d6d538741ea8dc49539c8c522d0"
)
EXPECTED_D4_MANIFEST_SHA256 = (
    "6103ebc8010441ad7a0c7eff4f96b3df0cae0e359de79258182b59917b5f12eb"
)
EXPECTED_D4_RECEIPT_SHA256 = (
    "c76cc14db549badb08bf2e9005b58f4825067c0af17431c989359e9697d0c98a"
)
EXPECTED_BATCH_TOOL_SHA256 = (
    "554cd7fa386eaac7deb65b404354b9edd4e60a2f80f38fd501fc308b39a00635"
)
EXPECTED_BATCH_MANIFESTS = {
    1: "66cd70a24dbdf4e59bba1e79e22e0d57ac3e562e611e2dc9f75d1444b48b7bae",
    2: "3d87463f9fdb7cb05f05c6b62dd17665746627e8b8e859d5c4f1eba103f62709",
    3: "06a161804fb98e7eed40a26900fdc92210fffaca4357c8876b003d870f6e9901",
}
EXPECTED_BATCH_RECEIPTS = {
    1: "59d3baf67716b253970169c1c12eb9c4ed35e0c4d29ecd63484fc0189e7642f4",
    2: "ee9a0fe4044a5ed8831bb570ad1822d92643573c0c96865012609cb8e3b6ad4b",
    3: "776f3be163394870781bdf8432735aa2ade6a537bbaf28250e333dced789e5c7",
}
BATCH_SOURCE_COUNTS = {1: 40, 2: 40, 3: 20}
BATCH_IDS = (1, 2, 3)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_manifest(root: Path, expected_hash: str | None = None) -> str:
    manifest = root / "files.sha256"
    manifest_hash = sha256_file(manifest)
    if expected_hash and manifest_hash != expected_hash:
        raise RuntimeError(f"Unexpected frozen manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise RuntimeError(f"Malformed frozen manifest line: {line}")
        expected, name = parts
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Hash-chain failure: {path}")
    return manifest_hash


def verify_sealed_empty(paths: Sequence[Path]) -> None:
    for path in paths:
        if not path.is_dir():
            raise RuntimeError(f"Sealed partition directory is missing: {path}")
        if any(item.is_file() for item in path.rglob("*")):
            raise RuntimeError(f"Sealed partition is not empty: {path}")


def bool_value(value: str) -> bool:
    return value.strip().lower() == "true"


def duplicate_groups(rows: Sequence[Dict[str, str]], field: str) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        value = row[field].strip().lower()
        if value:
            groups[value].append(row["case_id"])
    return {
        value: sorted(source_ids)
        for value, source_ids in groups.items()
        if len(source_ids) > 1
    }


def overlap_groups(
    current: Sequence[Dict[str, str]],
    prior: Sequence[Dict[str, str]],
    field: str,
) -> Dict[str, Dict[str, List[str]]]:
    prior_groups: Dict[str, List[str]] = defaultdict(list)
    for row in prior:
        value = row[field].strip().lower()
        if value:
            prior_groups[value].append(row["case_id"])
    overlaps: Dict[str, Dict[str, List[str]]] = {}
    for row in current:
        value = row[field].strip().lower()
        if value in prior_groups:
            overlaps[value] = {
                "d5": [row["case_id"]],
                "prior_d3_d4": sorted(prior_groups[value]),
            }
    return overlaps


def verify_protocol(protocol: Dict[str, Any]) -> None:
    if protocol.get("protocol_id") != "mamba-v15-d5-development100-final-qc-lock-v1":
        raise RuntimeError("Unexpected D5 development100 final-QC protocol")
    gates = protocol.get("hard_gates", {})
    if any(value != 0 for value in gates.values()):
        raise RuntimeError("D5 development100 hard gates changed")
    transition = protocol.get("batch_003_transition", {})
    if (
        transition.get("generic_next_step_text_is_advisory_only") is not True
        or transition.get("geometry_or_gate_result_changed") is not False
    ):
        raise RuntimeError("Batch 003 transition semantics changed")
    effect = protocol.get("success_effect", {})
    if effect.get("D5_data_generation_protocol_preparation_authorized_next") is not True:
        raise RuntimeError("D5 next-step preparation authorization changed")
    locked = (
        "synthetic_generation_authorized",
        "D5A_model_implementation_authorized",
        "D5A_training_authorized",
        "D5B_training_authorized",
        "D5_candidate_selection_authorized",
        "proposal_confirmation_access_authorized",
        "completion_holdout_access_authorized",
        "protected_split_access_authorized",
    )
    if any(effect.get(key) is not False for key in locked):
        raise RuntimeError("D5 final-lock permission boundary changed")


def collect_batches(
    source_lock_dir: Path,
    qc_root: Path,
    stl_root: Path,
) -> tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, str]]:
    verify_manifest(source_lock_dir, EXPECTED_SOURCE_LOCK_MANIFEST_SHA256)
    receipt_path = source_lock_dir / "source_acquisition_lock_receipt.json"
    if sha256_file(receipt_path) != EXPECTED_SOURCE_LOCK_RECEIPT_SHA256:
        raise RuntimeError("D5 source acquisition receipt drifted")
    source_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        source_receipt.get("status") != "source150_three_partition_acquisition_locked"
        or source_receipt.get("development_qc_authorized_next") is not True
        or source_receipt.get("protected_data_accessed") is not False
    ):
        raise RuntimeError("D5 source acquisition semantics changed")

    expected_ids = [
        line.strip()
        for line in (source_lock_dir / "d5_development100_ids.txt")
        .read_text(encoding="ascii")
        .splitlines()
        if line.strip()
    ]
    if len(expected_ids) != 100 or len(set(expected_ids)) != 100:
        raise RuntimeError("Frozen D5 development100 ID list is invalid")

    extraction_rows: List[Dict[str, str]] = []
    qc_rows: List[Dict[str, str]] = []
    batch_hashes: Dict[str, str] = {}
    for batch_id in BATCH_IDS:
        batch_name = f"batch_{batch_id:03d}"
        qc_dir = qc_root / batch_name
        manifest_hash = verify_manifest(qc_dir, EXPECTED_BATCH_MANIFESTS[batch_id])
        batch_receipt_path = qc_dir / "batch_qc_receipt.json"
        if sha256_file(batch_receipt_path) != EXPECTED_BATCH_RECEIPTS[batch_id]:
            raise RuntimeError(f"Unexpected {batch_name} receipt")
        receipt = json.loads(batch_receipt_path.read_text(encoding="utf-8"))
        if (
            receipt.get("status") != "batch_qc_passed"
            or receipt.get("batch_id") != batch_id
            or receipt.get("source_lock_receipt_sha256")
            != EXPECTED_SOURCE_LOCK_RECEIPT_SHA256
            or receipt.get("source_lock_manifest_sha256")
            != EXPECTED_SOURCE_LOCK_MANIFEST_SHA256
            or receipt.get("extraction_qc_tool_sha256") != EXPECTED_BATCH_TOOL_SHA256
            or receipt.get("model_metrics_used") is not False
            or receipt.get("protected_data_accessed") is not False
            or receipt.get("sealed_partitions_accessed") is not False
            or receipt.get("D5_synthetic_generation_authorized") is not False
            or receipt.get("D5A_training_authorized") is not False
        ):
            raise RuntimeError(f"{batch_name} is not a frozen development-only QC pass")

        batch_extract = read_csv(qc_dir / "extraction_manifest.csv")
        batch_qc = read_csv(qc_dir / "d5_development_source_qc_per_case.csv")
        expected_count = BATCH_SOURCE_COUNTS[batch_id]
        if len(batch_extract) != expected_count or len(batch_qc) != expected_count:
            raise RuntimeError(f"{batch_name} extraction/QC count differs from protocol")
        extraction_by_id = {row["source_id"]: row for row in batch_extract}
        if len(extraction_by_id) != expected_count:
            raise RuntimeError(f"{batch_name} extraction manifest has duplicate IDs")
        if set(extraction_by_id) != {row["case_id"] for row in batch_qc}:
            raise RuntimeError(f"{batch_name} extraction/QC IDs differ")

        stl_dir = stl_root / batch_name
        expected_stl_names = {f"{source_id}_clear.stl" for source_id in extraction_by_id}
        present_stl_names = {path.name for path in stl_dir.iterdir() if path.is_file()}
        if present_stl_names != expected_stl_names:
            raise RuntimeError(f"{batch_name} STL directory differs from frozen IDs")

        for original_row in batch_qc:
            row = dict(original_row)
            source_id = row["case_id"]
            extracted = dict(extraction_by_id[source_id])
            asset_path = stl_dir / f"{source_id}_clear.stl"
            if (
                not bool_value(row["qc_pass"])
                or row["source_asset_sha256"] != extracted["source_asset_sha256"]
                or sha256_file(asset_path) != row["source_asset_sha256"]
            ):
                raise RuntimeError(f"Frozen STL/QC verification failed: {source_id}")
            portable_path = (
                f"raw_v20/clear_stl/d5_source150_v1/development/{batch_name}/"
                f"{source_id}_clear.stl"
            )
            row["source_path"] = portable_path
            row["portable_source_path"] = portable_path
            row["batch_id"] = str(batch_id)
            extracted["batch_id"] = str(batch_id)
            extraction_rows.append(extracted)
            qc_rows.append(row)
        batch_hashes[str(batch_id)] = manifest_hash

    if len(qc_rows) != 100 or {row["case_id"] for row in qc_rows} != set(expected_ids):
        raise RuntimeError("Aggregated QC rows do not equal frozen development100 IDs")
    if len(extraction_rows) != 100:
        raise RuntimeError("Aggregated extraction rows do not equal 100")
    return extraction_rows, qc_rows, batch_hashes


def render_report(receipt: Dict[str, Any]) -> bytes:
    lines = [
        "# Mamba v1.5 D5 development100 最终 QC 数据锁报告",
        "",
        "> 本锁只汇总三批模型无关 QC；未读取 sealed 分区，未生成数据，未运行模型。",
        "",
        "## 结果",
        "",
        "- development 来源：100。",
        "- 批次：3（40 / 40 / 20）。",
        "- QC 通过/失败：100 / 0。",
        "- D5 内文件 SHA256 重复：0。",
        "- D5 内表面指纹重复：0。",
        "- 与 D3 healthy125 + D4 source100 文件 SHA256 重叠：0。",
        "- 与 D3 healthy125 + D4 source100 表面指纹重叠：0。",
        "- 与既有 225 来源 ID 重叠：0。",
        "- proposal confirmation / completion holdout 文件：0 / 0。",
        "",
        "## 转换与权限",
        "",
        "- Batch 003 通用 next_step 文案由本最终锁正式取代，几何结果和门控未改变。",
        "- 下一步仅授权 D5 数据生成与来源四折协议准备。",
        "- synthetic generation、模型实现、训练、候选选择及 sealed/protected 访问仍锁定。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_locked(outputs: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != outputs:
            raise RuntimeError("Refusing to overwrite a non-identical D5 final QC lock")
        print(f"[locked] existing D5 development100 QC lock is byte-identical: {output_dir}")
        return
    working = output_dir.with_name(f".{output_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Working final-lock directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in outputs.items():
        (working / name).write_bytes(payload)
    os.replace(working, output_dir)
    print(f"[saved] D5 development100 final QC lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_lock_dir", type=Path, required=True)
    parser.add_argument("--d3_lock_dir", type=Path, required=True)
    parser.add_argument("--d4_lock_dir", type=Path, required=True)
    parser.add_argument("--qc_root", type=Path, required=True)
    parser.add_argument("--stl_root", type=Path, required=True)
    parser.add_argument("--proposal_sealed_dir", type=Path, required=True)
    parser.add_argument("--completion_sealed_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.protocol_json.read_bytes()
    protocol = json.loads(protocol_bytes)
    verify_protocol(protocol)
    sealed = [args.proposal_sealed_dir, args.completion_sealed_dir]
    verify_sealed_empty(sealed)
    extraction_rows, qc_rows, batch_hashes = collect_batches(
        args.source_lock_dir, args.qc_root, args.stl_root
    )

    verify_manifest(args.d3_lock_dir, EXPECTED_D3_MANIFEST_SHA256)
    d3_rows = read_csv(args.d3_lock_dir / "healthy125_source_assets.csv")
    verify_manifest(args.d4_lock_dir, EXPECTED_D4_MANIFEST_SHA256)
    d4_receipt_path = args.d4_lock_dir / "source100_qc_lock_receipt.json"
    if sha256_file(d4_receipt_path) != EXPECTED_D4_RECEIPT_SHA256:
        raise RuntimeError("Prior D4 source100 QC receipt drifted")
    d4_rows = read_csv(args.d4_lock_dir / "source100_assets.csv")
    if (
        len(d3_rows) != 125
        or len(d4_rows) != 100
        or any(not bool_value(row["qc_pass"]) for row in d3_rows + d4_rows)
    ):
        raise RuntimeError("Prior D3/D4 asset locks are invalid")
    prior_rows = d3_rows + d4_rows

    asset_duplicates = duplicate_groups(qc_rows, "source_asset_sha256")
    surface_duplicates = duplicate_groups(qc_rows, "source_surface_fingerprint_sha256")
    asset_overlap = overlap_groups(qc_rows, prior_rows, "source_asset_sha256")
    surface_overlap = overlap_groups(
        qc_rows, prior_rows, "source_surface_fingerprint_sha256"
    )
    prior_ids = {row["case_id"] for row in prior_rows}
    id_overlap = sorted({row["case_id"] for row in qc_rows} & prior_ids)
    if asset_duplicates or surface_duplicates or asset_overlap or surface_overlap or id_overlap:
        raise RuntimeError("D5 development100 duplicate or prior-overlap hard gate failed")
    verify_sealed_empty(sealed)

    qc_rows.sort(key=lambda row: row["case_id"])
    extraction_rows.sort(key=lambda row: row["source_id"])
    asset_fields = (
        "case_id",
        "portable_source_path",
        "source_asset_sha256",
        "source_surface_fingerprint_sha256",
        "surface_fingerprint_algorithm_sha256",
        "file_bytes",
        "triangle_count",
        "qc_pass",
        "batch_id",
    )
    outputs = {
        "development100_ids.txt": (
            "\n".join(row["case_id"] for row in qc_rows) + "\n"
        ).encode("ascii"),
        "development100_assets.csv": csv_bytes(asset_fields, qc_rows),
        "development100_extraction_manifest.csv": csv_bytes(
            list(extraction_rows[0]), extraction_rows
        ),
        "development100_qc_per_case.csv": csv_bytes(list(qc_rows[0]), qc_rows),
    }
    audit = {
        "d5_development_sources": 100,
        "prior_d3_sources": 125,
        "prior_d4_sources": 100,
        "d5_asset_sha256_duplicates": asset_duplicates,
        "d5_surface_fingerprint_duplicates": surface_duplicates,
        "asset_sha256_overlap_with_prior_d3_d4": asset_overlap,
        "surface_fingerprint_overlap_with_prior_d3_d4": surface_overlap,
        "source_id_overlap_with_prior_d3_d4": id_overlap,
        "proposal_confirmation_files": 0,
        "completion_holdout_files": 0,
        "all_hard_gates_passed": True,
    }
    outputs["development100_overlap_audit.json"] = canonical_json_bytes(audit)
    receipt = {
        "protocol_id": protocol["protocol_id"],
        "status": "development100_qc_locked_complete",
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_acquisition_receipt_sha256": EXPECTED_SOURCE_LOCK_RECEIPT_SHA256,
        "source_acquisition_manifest_sha256": EXPECTED_SOURCE_LOCK_MANIFEST_SHA256,
        "prior_d3_manifest_sha256": EXPECTED_D3_MANIFEST_SHA256,
        "prior_d4_manifest_sha256": EXPECTED_D4_MANIFEST_SHA256,
        "prior_d4_receipt_sha256": EXPECTED_D4_RECEIPT_SHA256,
        "batch_qc_manifest_sha256": batch_hashes,
        "batch_qc_tool_sha256": EXPECTED_BATCH_TOOL_SHA256,
        "finalizer_sha256": sha256_file(Path(__file__).resolve()),
        "counts": {
            "sources": 100,
            "batches": 3,
            "qc_pass": 100,
            "qc_fail": 0,
            "prior_sources_checked": 225,
        },
        "global_duplicate_and_overlap_gates_passed": True,
        "batch_003_generic_next_step_superseded": True,
        "batch_003_geometry_or_gate_result_changed": False,
        "model_metrics_used": False,
        "protected_data_accessed": False,
        "proposal_confirmation_accessed": False,
        "completion_holdout_accessed": False,
        "D5_data_generation_protocol_preparation_authorized_next": True,
        "synthetic_generation_authorized": False,
        "D5A_model_implementation_authorized": False,
        "D5A_training_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "next_step": "preregister_D5_synthetic_generation_and_source_fourfold_protocol",
    }
    outputs["development100_qc_lock_receipt.json"] = canonical_json_bytes(receipt)
    outputs["development100_qc_lock_report_zh.md"] = render_report(receipt)
    outputs["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(outputs.items())
    ).encode("ascii")
    write_locked(outputs, args.out_dir)
    verify_sealed_empty(sealed)
    print("[done] D5 development sources=100 qc_pass=100 duplicate_or_overlap=0")
    print("[authorized-next] D5 data-generation protocol preparation only")
    print("[locked] generation=false model=false training=false selection=false sealed=false")


if __name__ == "__main__":
    main()
