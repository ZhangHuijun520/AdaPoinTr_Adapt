#!/usr/bin/env python3
"""Aggregate three D4 source batches and freeze the global 100-source QC lock."""

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
    "53f713aaa9a57739db0a47ced2219d0c57ad273677638bb0ef721ee8216a7222"
)
EXPECTED_SOURCE_LOCK_MANIFEST_SHA256 = (
    "d60bc9d118376a36bbe2dcd1b25b35cb8b5af06f37e0916ac811b73708493162"
)
EXPECTED_M1_MANIFEST_SHA256 = (
    "3892dbcad93418834daf1c1abb4915c8e73a0d6d538741ea8dc49539c8c522d0"
)
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


def verify_manifest(root: Path, expected_manifest_sha256: str | None = None) -> str:
    manifest = root / "files.sha256"
    manifest_hash = sha256_file(manifest)
    if expected_manifest_sha256 and manifest_hash != expected_manifest_sha256:
        raise RuntimeError(f"Unexpected frozen manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Hash-chain failure: {path}")
    return manifest_hash


def duplicate_groups(rows: Sequence[Dict[str, str]], field: str) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        value = row[field].strip().lower()
        if value:
            groups[value].append(row["case_id"])
    return {
        value: sorted(ids)
        for value, ids in groups.items()
        if len(ids) > 1
    }


def overlap_groups(
    current: Sequence[Dict[str, str]], prior: Sequence[Dict[str, str]], field: str
) -> Dict[str, Dict[str, List[str]]]:
    prior_groups: Dict[str, List[str]] = defaultdict(list)
    for row in prior:
        value = row[field].strip().lower()
        if value:
            prior_groups[value].append(row["case_id"])
    overlap = {}
    for row in current:
        value = row[field].strip().lower()
        if value in prior_groups:
            overlap[value] = {
                "d4": [row["case_id"]],
                "d3": sorted(prior_groups[value]),
            }
    return overlap


def bool_value(value: str) -> bool:
    return value.strip().lower() == "true"


def verify_protocol(protocol: Dict[str, Any]) -> None:
    if protocol.get("protocol_id") != "mamba-v14-d4-mug500plus-source100-final-qc-lock-v1":
        raise RuntimeError("Unexpected global source-QC protocol")
    gates = protocol.get("hard_gates", {})
    required_zero = (
        "duplicate_asset_sha256_within_d4",
        "duplicate_surface_fingerprint_within_d4",
        "asset_sha256_overlap_with_d3_healthy125",
        "surface_fingerprint_overlap_with_d3_healthy125",
        "source_id_overlap_with_d3_healthy125",
    )
    if any(gates.get(key) != 0 for key in required_zero):
        raise RuntimeError("Global duplicate/overlap gates changed")
    effect = protocol.get("success_effect", {})
    if (
        effect.get("D4_M2_protocol_preparation_authorized_next") is not True
        or any(
            effect.get(key) is not False
            for key in (
                "synthetic_generation_authorized",
                "D4_training_authorized",
                "D4_candidate_selection_authorized",
                "protected_split_access_authorized",
            )
        )
    ):
        raise RuntimeError("Global source-QC lock effects changed")


def collect_batches(
    source_lock_dir: Path, qc_root: Path, stl_root: Path
) -> tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, str]]:
    verify_manifest(source_lock_dir, EXPECTED_SOURCE_LOCK_MANIFEST_SHA256)
    receipt_path = source_lock_dir / "source_acquisition_lock_receipt.json"
    if sha256_file(receipt_path) != EXPECTED_SOURCE_LOCK_RECEIPT_SHA256:
        raise RuntimeError("D4 source acquisition lock drifted")
    expected_ids = [
        line.strip()
        for line in (source_lock_dir / "d4_source100_ids.txt").read_text().splitlines()
        if line.strip()
    ]
    if len(expected_ids) != 100 or len(set(expected_ids)) != 100:
        raise RuntimeError("Frozen D4 source100 ID list is invalid")

    extraction_rows: List[Dict[str, str]] = []
    qc_rows: List[Dict[str, str]] = []
    batch_hashes = {}
    for batch_id in BATCH_IDS:
        qc_dir = qc_root / f"batch_{batch_id:03d}"
        manifest_hash = verify_manifest(qc_dir)
        receipt = json.loads((qc_dir / "batch_qc_receipt.json").read_text())
        if (
            receipt.get("status") != "batch_qc_passed"
            or receipt.get("batch_id") != batch_id
            or receipt.get("model_metrics_used") is not False
            or receipt.get("protected_data_accessed") is not False
            or receipt.get("synthetic_generation_authorized") is not False
            or receipt.get("D4_training_authorized") is not False
        ):
            raise RuntimeError(f"Batch {batch_id:03d} receipt is not a frozen QC pass")
        batch_extract = read_csv(qc_dir / "extraction_manifest.csv")
        batch_qc = read_csv(qc_dir / "mug500plus_d4_source_qc_per_case.csv")
        if len(batch_extract) != len(batch_qc):
            raise RuntimeError(f"Batch {batch_id:03d} extraction/QC counts differ")
        extraction_by_id = {row["source_id"]: row for row in batch_extract}
        if set(extraction_by_id) != {row["case_id"] for row in batch_qc}:
            raise RuntimeError(f"Batch {batch_id:03d} extraction/QC IDs differ")
        for row in batch_qc:
            source_id = row["case_id"]
            extracted = extraction_by_id[source_id]
            asset_path = stl_root / f"batch_{batch_id:03d}" / f"{source_id}_clear.stl"
            if (
                not bool_value(row["qc_pass"])
                or row["source_asset_sha256"] != extracted["source_asset_sha256"]
                or not asset_path.is_file()
                or sha256_file(asset_path) != row["source_asset_sha256"]
            ):
                raise RuntimeError(f"Batch asset/QC verification failed: {source_id}")
            row["batch_id"] = str(batch_id)
            row["portable_source_path"] = (
                f"raw_v20/clear_stl/d4_source100_v1/batch_{batch_id:03d}/"
                f"{source_id}_clear.stl"
            )
            extracted["batch_id"] = str(batch_id)
        extraction_rows.extend(batch_extract)
        qc_rows.extend(batch_qc)
        batch_hashes[str(batch_id)] = manifest_hash

    if len(qc_rows) != 100 or {row["case_id"] for row in qc_rows} != set(expected_ids):
        raise RuntimeError("Aggregated QC rows do not equal the frozen source100 IDs")
    return extraction_rows, qc_rows, batch_hashes


def render_report(receipt: Dict[str, Any]) -> bytes:
    lines = [
        "# Mamba v1.4 D4 MUG500+ 100-source 最终 QC 数据锁报告",
        "",
        "> 本锁仅汇总三批模型无关结构 QC；未生成 synthetic defects，未训练模型，未访问保护集。",
        "",
        "## 结果",
        "",
        f"- 来源总数：{receipt['counts']['sources']}。",
        f"- 批次：{receipt['counts']['batches']}。",
        f"- QC 通过：{receipt['counts']['qc_pass']}。",
        "- D4 内文件 SHA256 重复：0。",
        "- D4 内表面指纹重复：0。",
        "- 与 D3 healthy125 文件 SHA256 重叠：0。",
        "- 与 D3 healthy125 表面指纹重叠：0。",
        "- 来源 ID 重叠：0。",
        "",
        "## 权限",
        "",
        "- 下一步仅授权 D4 M2 synthetic-defect 协议准备。",
        "- synthetic generation、训练、候选选择和保护集访问仍未授权。",
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
            raise RuntimeError("Refusing to overwrite a non-identical final source100 QC lock")
        print(f"[locked] existing final source100 QC lock is byte-identical: {output_dir}")
        return
    working = output_dir.with_name(f".{output_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Working final-lock directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in outputs.items():
        (working / name).write_bytes(payload)
    os.replace(working, output_dir)
    print(f"[saved] final D4 source100 QC lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_lock_dir", type=Path, required=True)
    parser.add_argument("--m1_lock_dir", type=Path, required=True)
    parser.add_argument("--qc_root", type=Path, required=True)
    parser.add_argument("--stl_root", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.protocol_json.read_bytes()
    protocol = json.loads(protocol_bytes)
    verify_protocol(protocol)
    extraction_rows, qc_rows, batch_hashes = collect_batches(
        args.source_lock_dir, args.qc_root, args.stl_root
    )
    verify_manifest(args.m1_lock_dir, EXPECTED_M1_MANIFEST_SHA256)
    prior = read_csv(args.m1_lock_dir / "healthy125_source_assets.csv")
    if len(prior) != 125 or any(row["qc_pass"].lower() != "true" for row in prior):
        raise RuntimeError("Prior D3 healthy125 asset lock is invalid")

    asset_duplicates = duplicate_groups(qc_rows, "source_asset_sha256")
    surface_duplicates = duplicate_groups(qc_rows, "source_surface_fingerprint_sha256")
    asset_overlap = overlap_groups(qc_rows, prior, "source_asset_sha256")
    surface_overlap = overlap_groups(qc_rows, prior, "source_surface_fingerprint_sha256")
    prior_ids = {row["case_id"] for row in prior}
    id_overlap = sorted({row["case_id"] for row in qc_rows} & prior_ids)
    if asset_duplicates or surface_duplicates or asset_overlap or surface_overlap or id_overlap:
        raise RuntimeError("Global D4/D3 duplicate or overlap hard gate failed")

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
        "source100_ids.txt": ("\n".join(row["case_id"] for row in qc_rows) + "\n").encode(),
        "source100_assets.csv": csv_bytes(asset_fields, qc_rows),
        "source100_extraction_manifest.csv": csv_bytes(list(extraction_rows[0]), extraction_rows),
        "source100_qc_per_case.csv": csv_bytes(list(qc_rows[0]), qc_rows),
    }
    audit = {
        "d4_sources": 100,
        "prior_d3_sources": 125,
        "d4_asset_sha256_duplicates": asset_duplicates,
        "d4_surface_fingerprint_duplicates": surface_duplicates,
        "asset_sha256_overlap_with_d3": asset_overlap,
        "surface_fingerprint_overlap_with_d3": surface_overlap,
        "source_id_overlap_with_d3": id_overlap,
        "all_hard_gates_passed": True,
    }
    outputs["source100_overlap_audit.json"] = canonical_json_bytes(audit)
    receipt = {
        "protocol_id": protocol["protocol_id"],
        "status": "source100_qc_locked_complete",
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_acquisition_receipt_sha256": EXPECTED_SOURCE_LOCK_RECEIPT_SHA256,
        "source_acquisition_manifest_sha256": EXPECTED_SOURCE_LOCK_MANIFEST_SHA256,
        "prior_m1_manifest_sha256": EXPECTED_M1_MANIFEST_SHA256,
        "batch_qc_manifest_sha256": batch_hashes,
        "finalizer_sha256": sha256_file(Path(__file__).resolve()),
        "counts": {"sources": 100, "batches": 3, "qc_pass": 100, "qc_fail": 0},
        "global_duplicate_and_overlap_gates_passed": True,
        "model_metrics_used": False,
        "protected_data_accessed": False,
        "D4_M2_protocol_preparation_authorized_next": True,
        "synthetic_generation_authorized": False,
        "D4_training_authorized": False,
        "D4_candidate_selection_authorized": False,
        "next_step": "preregister_D4_M2_generation_and_source_skull_four_fold_lock",
    }
    outputs["source100_qc_lock_receipt.json"] = canonical_json_bytes(receipt)
    outputs["source100_qc_lock_report_zh.md"] = render_report(receipt)
    outputs["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(outputs.items())
    ).encode("ascii")
    write_locked(outputs, args.out_dir)
    print("[done] sources=100 qc_pass=100 duplicate_or_overlap=0")
    print("[authorized-next] D4 M2 protocol preparation only")
    print("[locked] generation=false training=false selection=false protected=false")


if __name__ == "__main__":
    main()
