#!/usr/bin/env python3
"""Freeze the global D6 development100 QC lock from three frozen batches."""

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
    "865b9fb30ef52c532ae5dd4c5ff18405833dee0570144ee94957cf5c460dab71"
)
EXPECTED_SOURCE_LOCK_MANIFEST_SHA256 = (
    "d8509c44dd36575d46784972f70ec8f808754d3ffa84f390655ef3e5467c0fc1"
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
EXPECTED_D5_MANIFEST_SHA256 = (
    "cb2ec987d4f5e4259464a8083bb4ca3bb632d4212bf8f1cdb140f5b404d534b4"
)
EXPECTED_D5_RECEIPT_SHA256 = (
    "c9985f0c323edb0c0bfac3b02141cda2b371844804b215450f45f17494476e56"
)
EXPECTED_BATCH_TOOL_SHA256 = (
    "642f6fc422493cd1524104bd581438f6f4c4ccfa4372c3c9ee95e61f7615ab0c"
)
EXPECTED_BATCH_MANIFESTS = {
    1: "c34763228f72d7ec7320dbd08d9822801e306b3d7ead3556db1c5bd9aef85194",
    2: "94e0f5c669dd7a960ae9fd17b524d3fc0be6df40e03cca8a72cad69b10e80e50",
    3: "a69c852f479212ebd5617f7d8be6fd109265f79275e5f5eacf32f99a2df83001",
}
EXPECTED_BATCH_RECEIPTS = {
    1: "2a11bb1511f1c4a0e53a11420ad1dc75cedda7a0fc295f56fc6f19c6f3e955af",
    2: "ec49e2995b2d86751c60cd92890e3f1e7152b135bdd7eddb7775253a48c37ebf",
    3: "785a1bdd5cb973ecc224da48f0615deda7f41984ba7fb1ee580eba18838acd54",
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
                "d6": [row["case_id"]],
                "prior_d3_d4_d5_development": sorted(prior_groups[value]),
            }
    return overlaps


def verify_protocol(protocol: Dict[str, Any]) -> None:
    if protocol.get("protocol_id") != "mamba-v16-d6-development100-final-qc-lock-v1":
        raise RuntimeError("Unexpected D6 development100 final-QC protocol")
    gates = protocol.get("hard_gates", {})
    if any(value != 0 for value in gates.values()):
        raise RuntimeError("D6 development100 hard gates changed")
    transition = protocol.get("batch_003_transition", {})
    if (
        transition.get("generic_next_step_text_is_advisory_only") is not True
        or transition.get("geometry_or_gate_result_changed") is not False
    ):
        raise RuntimeError("Batch 003 transition semantics changed")
    effect = protocol.get("success_effect", {})
    if effect.get("D6_data_generation_protocol_preparation_authorized_next") is not True:
        raise RuntimeError("D6 next-step preparation authorization changed")
    locked = (
        "synthetic_generation_authorized",
        "D6_gradient_calibration_authorized",
        "D6_R0_R1_training_authorized",
        "D6_seed1_authorized",
        "D6B_authorized",
        "D6_candidate_selection_authorized",
        "D6_confirmation_access_authorized",
        "protected_split_access_authorized",
    )
    if any(effect.get(key) is not False for key in locked):
        raise RuntimeError("D6 final-lock permission boundary changed")


def collect_batches(
    source_lock_dir: Path,
    qc_root: Path,
    stl_root: Path,
) -> tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, str]]:
    verify_manifest(source_lock_dir, EXPECTED_SOURCE_LOCK_MANIFEST_SHA256)
    receipt_path = source_lock_dir / "source_acquisition_lock_receipt.json"
    if sha256_file(receipt_path) != EXPECTED_SOURCE_LOCK_RECEIPT_SHA256:
        raise RuntimeError("D6 source acquisition receipt drifted")
    source_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        source_receipt.get("status") != "source125_terminal_two_partition_acquisition_locked"
        or source_receipt.get("development_archive_download_authorized_next") is not True
        or source_receipt.get("development_extraction_authorized") is not False
        or source_receipt.get("D6_confirmation_access_authorized") is not False
        or source_receipt.get("protected_data_accessed") is not False
    ):
        raise RuntimeError("D6 source acquisition semantics changed")

    expected_ids = [
        line.strip()
        for line in (source_lock_dir / "d6_development100_ids.txt")
        .read_text(encoding="ascii")
        .splitlines()
        if line.strip()
    ]
    if len(expected_ids) != 100 or len(set(expected_ids)) != 100:
        raise RuntimeError("Frozen D6 development100 ID list is invalid")

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
            or receipt.get("D6_synthetic_generation_authorized") is not False
            or receipt.get("D6_R0_R1_training_authorized") is not False
            or receipt.get("D6_confirmation_access_authorized") is not False
        ):
            raise RuntimeError(f"{batch_name} is not a frozen development-only QC pass")

        batch_extract = read_csv(qc_dir / "extraction_manifest.csv")
        batch_qc = read_csv(qc_dir / "d6_development_source_qc_per_case.csv")
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
                f"raw_v20/clear_stl/d6_development100_v1/{batch_name}/"
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
        "# Mamba v1.6 D6 development100 最终 QC 数据锁报告",
        "",
        "> 本锁只汇总三批模型无关 QC；未读取 sealed 分区，未生成数据，未运行模型。",
        "",
        "## 结果",
        "",
        "- development 来源：100。",
        "- 批次：3（40 / 40 / 20）。",
        "- QC 通过/失败：100 / 0。",
        "- D6 内文件 SHA256 重复：0。",
        "- D6 内表面指纹重复：0。",
        "- 与 D3 healthy125 + D4 source100 + D5 development100 文件 SHA256 重叠：0。",
        "- 与上述 325 个既有几何来源的表面指纹重叠：0。",
        "- 与 D3/D4/D5 全部既有 375 来源 ID 重叠：0。",
        "- proposal confirmation25 文件：0。",
        "",
        "## 转换与权限",
        "",
        "- Batch 003 通用 next_step 文案由本最终锁正式取代，几何结果和门控未改变。",
        "- 下一步仅授权 D6 合成生成与来源四折协议准备。",
        "- synthetic generation、gradient calibration、R0/R1 training、seed-1、D6-B、候选选择及 confirmation/protected 访问仍锁定。",
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
            raise RuntimeError("Refusing to overwrite a non-identical D6 final QC lock")
        print(f"[locked] existing D6 development100 QC lock is byte-identical: {output_dir}")
        return
    working = output_dir.with_name(f".{output_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Working final-lock directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in outputs.items():
        (working / name).write_bytes(payload)
    os.replace(working, output_dir)
    print(f"[saved] D6 development100 final QC lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_lock_dir", type=Path, required=True)
    parser.add_argument("--d3_lock_dir", type=Path, required=True)
    parser.add_argument("--d4_lock_dir", type=Path, required=True)
    parser.add_argument("--d5_lock_dir", type=Path, required=True)
    parser.add_argument("--qc_root", type=Path, required=True)
    parser.add_argument("--stl_root", type=Path, required=True)
    parser.add_argument("--confirmation_sealed_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.protocol_json.read_bytes()
    protocol = json.loads(protocol_bytes)
    verify_protocol(protocol)
    sealed = [args.confirmation_sealed_dir]
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
    verify_manifest(args.d5_lock_dir, EXPECTED_D5_MANIFEST_SHA256)
    d5_receipt_path = args.d5_lock_dir / "development100_qc_lock_receipt.json"
    if sha256_file(d5_receipt_path) != EXPECTED_D5_RECEIPT_SHA256:
        raise RuntimeError("Prior D5 development100 QC receipt drifted")
    d5_rows = read_csv(args.d5_lock_dir / "development100_assets.csv")
    if (
        len(d3_rows) != 125
        or len(d4_rows) != 100
        or len(d5_rows) != 100
        or any(not bool_value(row["qc_pass"]) for row in d3_rows + d4_rows + d5_rows)
    ):
        raise RuntimeError("Prior D3/D4/D5 asset locks are invalid")
    prior_rows = d3_rows + d4_rows + d5_rows

    asset_duplicates = duplicate_groups(qc_rows, "source_asset_sha256")
    surface_duplicates = duplicate_groups(qc_rows, "source_surface_fingerprint_sha256")
    asset_overlap = overlap_groups(qc_rows, prior_rows, "source_asset_sha256")
    surface_overlap = overlap_groups(
        qc_rows, prior_rows, "source_surface_fingerprint_sha256"
    )
    prior_ids = {
        line.strip()
        for line in (args.source_lock_dir / "excluded_prior375_ids.txt")
        .read_text(encoding="ascii")
        .splitlines()
        if line.strip()
    }
    if len(prior_ids) != 375:
        raise RuntimeError("Frozen prior375 source-ID lineage is invalid")
    id_overlap = sorted({row["case_id"] for row in qc_rows} & prior_ids)
    if asset_duplicates or surface_duplicates or asset_overlap or surface_overlap or id_overlap:
        raise RuntimeError("D6 development100 duplicate or prior-overlap hard gate failed")
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
        "d6_development_sources": 100,
        "prior_d3_sources": 125,
        "prior_d4_sources": 100,
        "prior_d5_development_sources": 100,
        "prior_source_ids_checked": 375,
        "d6_asset_sha256_duplicates": asset_duplicates,
        "d6_surface_fingerprint_duplicates": surface_duplicates,
        "asset_sha256_overlap_with_prior_d3_d4_d5_development": asset_overlap,
        "surface_fingerprint_overlap_with_prior_d3_d4_d5_development": surface_overlap,
        "source_id_overlap_with_prior_d3_d4_d5_all_partitions": id_overlap,
        "proposal_confirmation_files": 0,
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
        "prior_d5_manifest_sha256": EXPECTED_D5_MANIFEST_SHA256,
        "prior_d5_receipt_sha256": EXPECTED_D5_RECEIPT_SHA256,
        "batch_qc_manifest_sha256": batch_hashes,
        "batch_qc_tool_sha256": EXPECTED_BATCH_TOOL_SHA256,
        "finalizer_sha256": sha256_file(Path(__file__).resolve()),
        "counts": {
            "sources": 100,
            "batches": 3,
            "qc_pass": 100,
            "qc_fail": 0,
            "prior_geometry_sources_checked": 325,
            "prior_source_ids_checked": 375,
        },
        "global_duplicate_and_overlap_gates_passed": True,
        "batch_003_generic_next_step_superseded": True,
        "batch_003_geometry_or_gate_result_changed": False,
        "model_metrics_used": False,
        "protected_data_accessed": False,
        "proposal_confirmation_accessed": False,
        "D6_data_generation_protocol_preparation_authorized_next": True,
        "synthetic_generation_authorized": False,
        "D6_gradient_calibration_authorized": False,
        "D6_R0_R1_training_authorized": False,
        "D6_seed1_authorized": False,
        "D6_confirmation_access_authorized": False,
        "D6B_authorized": False,
        "D6_candidate_selection_authorized": False,
        "next_step": "preregister_D6_synthetic_generation_and_source_fourfold_protocol",
    }
    outputs["development100_qc_lock_receipt.json"] = canonical_json_bytes(receipt)
    outputs["development100_qc_lock_report_zh.md"] = render_report(receipt)
    outputs["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(outputs.items())
    ).encode("ascii")
    write_locked(outputs, args.out_dir)
    verify_sealed_empty(sealed)
    print("[done] D6 development sources=100 qc_pass=100 duplicate_or_overlap=0")
    print("[authorized-next] D6 data-generation protocol preparation only")
    print("[locked] generation=false calibration=false training=false seed1=false confirmation=false")


if __name__ == "__main__":
    main()
