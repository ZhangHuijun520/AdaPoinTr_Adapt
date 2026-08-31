#!/usr/bin/env python3
"""Verify, extract, and freeze one D5 development source QC batch."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Sequence

from tqdm import tqdm

from qc_mug500plus_clear_stl import (
    FINGERPRINT_ALGORITHM_ID,
    FINGERPRINT_ALGORITHM_SHA256,
    MAXIMUM_BBOX_EXTENT_MM,
    MINIMUM_BBOX_ASPECT_RATIO,
    MINIMUM_BBOX_EXTENT_MM,
    MINIMUM_FILE_BYTES,
    MINIMUM_NONDEGENERATE_FRACTION,
    MINIMUM_TRIANGLES,
    apply_duplicate_gate,
    evaluate_stl,
)


EXPECTED_LOCK_RECEIPT_SHA256 = (
    "64634d5c31a0d27ce27d10645d4bffa7f28cc22bf09f178ff363acf4c1d49015"
)
EXPECTED_LOCK_MANIFEST_SHA256 = (
    "9d512638287e782b31f83b566429990673e8af70bd5d01686654c2d0eb8ffa0b"
)
EXPECTED_QC_ENGINE_SHA256 = (
    "9b5d406cd84ce806dbc80bad38edb5d48b999665a5a33c5b4cdcaf2bfe3c19cb"
)
CLEAR_MEMBER_RE = re.compile(r"^(A\d{4})_clear\.stl$", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
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
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_hash_manifest(root: Path) -> None:
    manifest = root / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen D5 source-lock hash mismatch: {path}")


def verify_sealed_empty(paths: Sequence[Path]) -> None:
    for path in paths:
        if not path.is_dir():
            raise RuntimeError(f"Sealed partition directory is missing: {path}")
        files = [item for item in path.rglob("*") if item.is_file()]
        if files:
            raise RuntimeError(f"Sealed partition is not empty: {path}")


def read_batch_contract(
    source_lock_dir: Path, batch_id: int
) -> tuple[List[Dict[str, str]], List[Dict[str, str]], List[str]]:
    verify_hash_manifest(source_lock_dir)
    receipt_path = source_lock_dir / "source_acquisition_lock_receipt.json"
    if sha256_file(receipt_path) != EXPECTED_LOCK_RECEIPT_SHA256:
        raise RuntimeError("Unexpected D5 source150 lock receipt")
    if sha256_file(source_lock_dir / "files.sha256") != EXPECTED_LOCK_MANIFEST_SHA256:
        raise RuntimeError("Unexpected D5 source150 lock manifest")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("status") != "source150_three_partition_acquisition_locked"
        or receipt.get("source_overlap") != 0
        or receipt.get("development_qc_authorized_next") is not True
        or receipt.get("protected_data_accessed") is not False
        or receipt.get("D5_synthetic_generation_authorized") is not False
        or receipt.get("D5A_training_authorized") is not False
    ):
        raise RuntimeError("D5 source150 lock does not authorize development-only QC")

    plan_name = f"development_batch_{batch_id:03d}_downloads.csv"
    ids_name = f"development_batch_{batch_id:03d}_expected_source_ids.txt"
    plan = read_csv(source_lock_dir / plan_name)
    expected_ids = [
        line.strip()
        for line in (source_lock_dir / ids_name).read_text(encoding="ascii").splitlines()
        if line.strip()
    ]
    source_plan = read_csv(source_lock_dir / "d5_source150_source_plan.csv")
    by_id = {row["source_id"]: row for row in source_plan}
    if len(by_id) != len(source_plan) or len(set(expected_ids)) != len(expected_ids):
        raise RuntimeError("D5 source plan or batch IDs contain duplicates")
    try:
        sources = [by_id[source_id] for source_id in expected_ids]
    except KeyError as exc:
        raise RuntimeError(f"Batch source is absent from the frozen source plan: {exc}") from exc
    if not plan or not expected_ids:
        raise RuntimeError("Frozen development batch is empty")
    if any(
        row.get("partition") != "development"
        or row.get("access_state") != "development_qc_authorized"
        for row in sources
    ):
        raise RuntimeError("Batch includes a non-development or sealed source")
    planned_archives = {row["archive_name"] for row in plan}
    if {row["archive_name"] for row in sources} != planned_archives:
        raise RuntimeError("Batch source/archive mapping is incomplete")
    if sum(int(row["skull_count"]) for row in plan) != len(expected_ids):
        raise RuntimeError("Batch source count differs from the frozen download plan")
    return plan, sources, expected_ids


def verify_archives(plan: Sequence[Dict[str, str]], archive_dir: Path) -> None:
    expected = {row["archive_name"] for row in plan}
    present = {path.name for path in archive_dir.iterdir() if path.is_file()}
    if present != expected:
        raise RuntimeError(
            f"Archive directory differs from frozen batch: missing={sorted(expected-present)} "
            f"extra={sorted(present-expected)}"
        )
    for row in tqdm(plan, desc="Verify D5 development ZIPs"):
        path = archive_dir / row["archive_name"]
        if path.stat().st_size != int(row["size_bytes"]):
            raise RuntimeError(f"Official byte count mismatch: {path.name}")
        if md5_file(path) != row["md5"].lower():
            raise RuntimeError(f"Official MD5 mismatch: {path.name}")


def index_clear_members(
    archive: zipfile.ZipFile, expected_ids: Sequence[str]
) -> Dict[str, zipfile.ZipInfo]:
    by_source: Dict[str, List[zipfile.ZipInfo]] = defaultdict(list)
    for info in archive.infolist():
        if info.is_dir():
            continue
        basename = PurePosixPath(info.filename.replace("\\", "/")).name
        match = CLEAR_MEMBER_RE.fullmatch(basename)
        if match:
            by_source[match.group(1).upper()].append(info)
    expected = set(expected_ids)
    found = set(by_source)
    if found != expected:
        raise RuntimeError(
            f"ZIP clear-STL membership differs from lock: missing={sorted(expected-found)} "
            f"extra={sorted(found-expected)}"
        )
    duplicates = sorted(source for source, values in by_source.items() if len(values) != 1)
    if duplicates:
        raise RuntimeError(f"ZIP contains duplicate clear-STL members: {duplicates}")
    selected = {source: values[0] for source, values in by_source.items()}
    for source, info in selected.items():
        basename = PurePosixPath(info.filename.replace("\\", "/")).name
        if basename != f"{source}_clear.stl":
            raise RuntimeError(f"Noncanonical clear-STL member basename: {basename}")
        if info.flag_bits & 0x1:
            raise RuntimeError(f"Encrypted ZIP member is forbidden: {source}")
        if info.file_size < MINIMUM_FILE_BYTES:
            raise RuntimeError(f"ZIP member is too small before extraction: {source}")
    return selected


def extract_batch(
    plan: Sequence[Dict[str, str]],
    sources: Sequence[Dict[str, str]],
    archive_dir: Path,
    stl_out_dir: Path,
) -> List[Dict[str, Any]]:
    working = stl_out_dir.with_name(f".{stl_out_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Working extraction directory requires inspection: {working}")
    if stl_out_dir.exists():
        raise RuntimeError(f"STL output path already exists: {stl_out_dir}")
    working.mkdir(parents=True)
    expected_by_archive: Dict[str, List[str]] = defaultdict(list)
    for row in sources:
        expected_by_archive[row["archive_name"]].append(row["source_id"])
    extraction_rows: List[Dict[str, Any]] = []
    try:
        for row in tqdm(plan, desc="Extract frozen D5 clear STL"):
            archive_path = archive_dir / row["archive_name"]
            with zipfile.ZipFile(archive_path, "r", allowZip64=True) as archive:
                selected = index_clear_members(
                    archive, expected_by_archive[row["archive_name"]]
                )
                for source_id in sorted(selected):
                    info = selected[source_id]
                    destination = working / f"{source_id}_clear.stl"
                    digest = hashlib.sha256()
                    written = 0
                    with archive.open(info, "r") as source, destination.open("xb") as target:
                        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
                            target.write(chunk)
                            digest.update(chunk)
                            written += len(chunk)
                    if written != info.file_size:
                        raise RuntimeError(f"Extracted byte count mismatch: {source_id}")
                    extraction_rows.append(
                        {
                            "source_id": source_id,
                            "archive_name": row["archive_name"],
                            "member_name": info.filename,
                            "zip_crc32": f"{info.CRC:08x}",
                            "uncompressed_bytes": info.file_size,
                            "extracted_bytes": written,
                            "source_asset_sha256": digest.hexdigest(),
                        }
                    )
        if {row["source_id"] for row in extraction_rows} != {
            row["source_id"] for row in sources
        }:
            raise RuntimeError("Extracted source IDs differ from the frozen batch")
        os.replace(working, stl_out_dir)
        return sorted(extraction_rows, key=lambda row: row["source_id"])
    except Exception:
        print(f"[inspect] interrupted extraction retained at: {working}")
        raise


def qc_rows_for_sources(
    sources: Sequence[Dict[str, str]], stl_out_dir: Path
) -> List[Dict[str, Any]]:
    rows = [
        evaluate_stl(stl_out_dir / f"{row['source_id']}_clear.stl")
        for row in tqdm(sources, desc="D5 development geometry QC")
    ]
    apply_duplicate_gate(rows)
    return rows


def freeze_qc(
    source_lock_dir: Path,
    batch_id: int,
    extraction_rows: Sequence[Dict[str, Any]],
    qc_rows: Sequence[Dict[str, Any]],
    qc_out_dir: Path,
) -> Dict[str, Any]:
    working = qc_out_dir.with_name(f".{qc_out_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Working QC directory requires inspection: {working}")
    if qc_out_dir.exists():
        raise RuntimeError(f"QC output path already exists: {qc_out_dir}")
    working.mkdir(parents=True)
    passed = [row for row in qc_rows if bool(row["qc_pass"])]
    summary = {
        "protocol_id": "mamba-v15-d5-development-batch-qc-v1",
        "batch_id": batch_id,
        "expected_sources": len(qc_rows),
        "qc_pass_sources": len(passed),
        "qc_fail_sources": len(qc_rows) - len(passed),
        "duplicate_surface_failures": sum(
            "duplicate_surface" in str(row["failure_reasons"]) for row in qc_rows
        ),
        "batch_local_duplicate_gate_only": True,
        "final_cross_batch_duplicate_gate_pending": True,
        "all_metrics_computed_without_model": True,
        "proposal_confirmation_files": 0,
        "completion_holdout_files": 0,
        "surface_fingerprint_algorithm_id": FINGERPRINT_ALGORITHM_ID,
        "surface_fingerprint_algorithm_sha256": FINGERPRINT_ALGORITHM_SHA256,
        "thresholds": {
            "minimum_file_bytes": MINIMUM_FILE_BYTES,
            "minimum_triangles": MINIMUM_TRIANGLES,
            "minimum_nondegenerate_fraction": MINIMUM_NONDEGENERATE_FRACTION,
            "minimum_bbox_extent_mm": MINIMUM_BBOX_EXTENT_MM,
            "maximum_bbox_extent_mm": MAXIMUM_BBOX_EXTENT_MM,
            "minimum_bbox_aspect_ratio": MINIMUM_BBOX_ASPECT_RATIO,
        },
    }
    status = "batch_qc_passed" if len(passed) == len(qc_rows) else "batch_qc_failed_frozen"
    receipt = {
        "status": status,
        "batch_id": batch_id,
        "source_lock_receipt_sha256": EXPECTED_LOCK_RECEIPT_SHA256,
        "source_lock_manifest_sha256": EXPECTED_LOCK_MANIFEST_SHA256,
        "batch_download_plan_sha256": sha256_file(
            source_lock_dir / f"development_batch_{batch_id:03d}_downloads.csv"
        ),
        "batch_expected_ids_sha256": sha256_file(
            source_lock_dir / f"development_batch_{batch_id:03d}_expected_source_ids.txt"
        ),
        "extraction_qc_tool_sha256": sha256_file(Path(__file__).resolve()),
        "qc_engine_sha256": EXPECTED_QC_ENGINE_SHA256,
        "model_metrics_used": False,
        "protected_data_accessed": False,
        "sealed_partitions_accessed": False,
        "D5_synthetic_generation_authorized": False,
        "D5A_model_implementation_authorized": False,
        "D5A_training_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "next_step": (
            "download_and_qc_next_development_batch"
            if len(passed) == len(qc_rows)
            else "freeze_failure_and_amend_before_replacement"
        ),
    }
    report = (
        "# Mamba v1.5 D5 Development Batch QC\n\n"
        "> 仅提取冻结 development clear STL；不读取 sealed 分区，不运行模型。\n\n"
        f"- batch：{batch_id:03d}。\n"
        f"- expected sources：{len(qc_rows)}。\n"
        f"- QC pass/fail：{len(passed)} / {len(qc_rows) - len(passed)}。\n"
        "- batch-local duplicate gate：已执行。\n"
        "- cross-batch duplicate gate：等待 100 个 development 来源完成。\n"
        "- proposal confirmation / completion holdout files：0 / 0。\n"
        "- model/protected access：False / False。\n"
        f"- status：`{status}`。\n"
    ).encode("utf-8")
    outputs = {
        "extraction_manifest.csv": csv_bytes(
            (
                "source_id",
                "archive_name",
                "member_name",
                "zip_crc32",
                "uncompressed_bytes",
                "extracted_bytes",
                "source_asset_sha256",
            ),
            extraction_rows,
        ),
        "d5_development_source_qc_per_case.csv": csv_bytes(list(qc_rows[0]), qc_rows),
        "batch_qc_summary.json": canonical_json_bytes(summary),
        "batch_qc_receipt.json": canonical_json_bytes(receipt),
        "batch_qc_report_zh.md": report,
    }
    outputs["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(outputs.items())
    ).encode("ascii")
    for name, payload in outputs.items():
        (working / name).write_bytes(payload)
    os.replace(working, qc_out_dir)
    return {**summary, **receipt}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_lock_dir", type=Path, required=True)
    parser.add_argument("--batch_id", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--archive_dir", type=Path, required=True)
    parser.add_argument("--stl_out_dir", type=Path, required=True)
    parser.add_argument("--qc_out_dir", type=Path, required=True)
    parser.add_argument("--proposal_sealed_dir", type=Path, required=True)
    parser.add_argument("--completion_sealed_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    qc_engine = Path(__file__).resolve().with_name("qc_mug500plus_clear_stl.py")
    if sha256_file(qc_engine) != EXPECTED_QC_ENGINE_SHA256:
        raise RuntimeError("Frozen MUG500+ QC engine drifted")
    sealed = [args.proposal_sealed_dir, args.completion_sealed_dir]
    verify_sealed_empty(sealed)
    plan, sources, _ = read_batch_contract(args.source_lock_dir, args.batch_id)
    verify_archives(plan, args.archive_dir)
    extraction_rows = extract_batch(plan, sources, args.archive_dir, args.stl_out_dir)
    qc_rows = qc_rows_for_sources(sources, args.stl_out_dir)
    verify_sealed_empty(sealed)
    result = freeze_qc(
        args.source_lock_dir,
        args.batch_id,
        extraction_rows,
        qc_rows,
        args.qc_out_dir,
    )
    verify_sealed_empty(sealed)
    print(f"[saved] {args.stl_out_dir}")
    print(f"[saved] {args.qc_out_dir}")
    print(
        f"[done] batch={args.batch_id:03d} pass={result['qc_pass_sources']} "
        f"fail={result['qc_fail_sources']} status={result['status']}"
    )
    print("[locked] sealed=empty model=false generation=false training=false")


if __name__ == "__main__":
    main()
