#!/usr/bin/env python3
"""Verify, extract, and freeze one D4 MUG500+ source100 QC batch."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
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


EXPECTED_SOURCE_LOCK_RECEIPT_SHA256 = (
    "53f713aaa9a57739db0a47ced2219d0c57ad273677638bb0ef721ee8216a7222"
)
EXPECTED_SOURCE_LOCK_MANIFEST_SHA256 = (
    "d60bc9d118376a36bbe2dcd1b25b35cb8b5af06f37e0916ac811b73708493162"
)
EXPECTED_QC_ENGINE_SHA256 = (
    "9b5d406cd84ce806dbc80bad38edb5d48b999665a5a33c5b4cdcaf2bfe3c19cb"
)
EXPECTED_MEMBER_ALIAS_AMENDMENT_SHA256 = (
    "790049cb9b1e512cb07867248521f45dcfa9a03936eb1f2755f8ee16dcd562fb"
)
CLEAR_MEMBER_RE = re.compile(r"^(A\d{4})_clear\.stl$", re.IGNORECASE)
FROZEN_MEMBER_ALIASES = {
    "A0191-A0195.zip": {
        "A0192": {
            "basename": "A192_clear.stl",
            "file_size": 95738834,
            "crc32": "c2c447c1",
        }
    }
}


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
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def verify_hash_manifest(root: Path) -> None:
    manifest = root / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen source-lock hash mismatch: {path}")


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_batch_contract(
    source_lock_dir: Path, batch_id: int
) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    verify_hash_manifest(source_lock_dir)
    receipt_path = source_lock_dir / "source_acquisition_lock_receipt.json"
    if sha256_file(receipt_path) != EXPECTED_SOURCE_LOCK_RECEIPT_SHA256:
        raise RuntimeError("Unexpected D4 source100 lock receipt")
    if sha256_file(source_lock_dir / "files.sha256") != EXPECTED_SOURCE_LOCK_MANIFEST_SHA256:
        raise RuntimeError("Unexpected D4 source100 lock manifest")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("status") != "source100_acquisition_locked_payload_not_downloaded"
        or receipt.get("source_overlap") != 0
        or receipt.get("protected_data_accessed") is not False
        or receipt.get("payload_qc_authorized_next") is not True
        or receipt.get("synthetic_generation_authorized") is not False
        or receipt.get("D4_training_authorized") is not False
    ):
        raise RuntimeError("D4 source100 lock does not authorize geometry-only QC")

    plan = read_csv(source_lock_dir / f"batch_{batch_id:03d}_downloads.csv")
    all_sources = read_csv(source_lock_dir / "d4_source100_source_plan.csv")
    sources = [row for row in all_sources if int(row["batch_id"]) == batch_id]
    expected_count = int(receipt["counts"]["batch_source_skulls"][str(batch_id)])
    if not plan or len(sources) != expected_count:
        raise RuntimeError("Batch plan cardinality does not match the frozen receipt")
    planned_archives = {row["archive_name"] for row in plan}
    if {row["archive_name"] for row in sources} != planned_archives:
        raise RuntimeError("Batch source/archive mapping is incomplete")
    if len({row["source_id"] for row in sources}) != len(sources):
        raise RuntimeError("Batch source plan contains duplicate IDs")
    return plan, sources


def verify_archives(plan: Sequence[Dict[str, str]], archive_dir: Path) -> None:
    expected = {row["archive_name"] for row in plan}
    present = {path.name for path in archive_dir.glob("*.zip") if path.is_file()}
    if present != expected:
        raise RuntimeError(
            f"Archive directory differs from frozen batch: missing={sorted(expected-present)} "
            f"extra={sorted(present-expected)}"
        )
    for row in tqdm(plan, desc="Verify D4 source ZIPs"):
        path = archive_dir / row["archive_name"]
        if path.stat().st_size != int(row["size_bytes"]):
            raise RuntimeError(f"Official byte count mismatch: {path.name}")
        if md5_file(path) != row["md5"].lower():
            raise RuntimeError(f"Official MD5 mismatch: {path.name}")


def index_clear_members(
    archive: zipfile.ZipFile,
    expected_ids: Sequence[str],
    archive_name: str = "",
) -> Dict[str, zipfile.ZipInfo]:
    by_source: Dict[str, List[zipfile.ZipInfo]] = defaultdict(list)
    for info in archive.infolist():
        if info.is_dir():
            continue
        basename = PurePosixPath(info.filename.replace("\\", "/")).name
        match = CLEAR_MEMBER_RE.fullmatch(basename)
        if match:
            by_source[match.group(1).upper()].append(info)
    aliases = FROZEN_MEMBER_ALIASES.get(archive_name, {})
    for source_id, contract in aliases.items():
        matches = [
            info
            for info in archive.infolist()
            if not info.is_dir()
            and PurePosixPath(info.filename.replace("\\", "/")).name.casefold()
            == contract["basename"].casefold()
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Frozen member alias is absent or ambiguous: {archive_name}/{source_id}"
            )
        info = matches[0]
        if (
            info.file_size != int(contract["file_size"])
            or f"{info.CRC:08x}" != contract["crc32"]
        ):
            raise RuntimeError(
                f"Frozen member alias size/CRC mismatch: {archive_name}/{source_id}"
            )
        by_source[source_id].append(info)
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
    if stl_out_dir.exists() and any(stl_out_dir.iterdir()):
        raise RuntimeError(f"STL output directory is not empty: {stl_out_dir}")
    working.mkdir(parents=True)
    expected_by_archive: Dict[str, List[str]] = defaultdict(list)
    for row in sources:
        expected_by_archive[row["archive_name"]].append(row["source_id"])

    extraction_rows = []
    try:
        for row in tqdm(plan, desc="Extract frozen D4 clear STL"):
            archive_path = archive_dir / row["archive_name"]
            with zipfile.ZipFile(archive_path, "r", allowZip64=True) as archive:
                selected = index_clear_members(
                    archive,
                    expected_by_archive[row["archive_name"]],
                    row["archive_name"],
                )
                for source_id in sorted(selected):
                    info = selected[source_id]
                    destination = working / f"{source_id}_clear.stl"
                    digest = hashlib.sha256()
                    written = 0
                    with archive.open(info, "r") as source, destination.open("xb") as target:
                        while True:
                            chunk = source.read(8 * 1024 * 1024)
                            if not chunk:
                                break
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
                            "member_alias_applied": bool(
                                source_id
                                in FROZEN_MEMBER_ALIASES.get(row["archive_name"], {})
                            ),
                        }
                    )
        expected_ids = {row["source_id"] for row in sources}
        if {row["source_id"] for row in extraction_rows} != expected_ids:
            raise RuntimeError("Extracted source IDs differ from the frozen batch")
        if stl_out_dir.exists():
            stl_out_dir.rmdir()
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
        for row in tqdm(sources, desc="D4 source geometry QC")
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
    if qc_out_dir.exists() and any(qc_out_dir.iterdir()):
        raise RuntimeError(f"QC output directory is not empty: {qc_out_dir}")
    working.mkdir(parents=True)
    passed = [row for row in qc_rows if bool(row["qc_pass"])]
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
                "member_alias_applied",
            ),
            extraction_rows,
        ),
        "mug500plus_d4_source_qc_per_case.csv": csv_bytes(list(qc_rows[0]), qc_rows),
    }
    summary = {
        "protocol_id": "mamba-v14-d4-mug500plus-source100-qc-v1",
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
        "craniotomy_or_B_series_accessed": False,
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
    outputs["mug500plus_d4_source_qc_summary.json"] = canonical_json_bytes(summary)
    receipt = {
        "status": "batch_qc_passed" if len(passed) == len(qc_rows) else "batch_qc_failed_frozen",
        "batch_id": batch_id,
        "source_lock_receipt_sha256": EXPECTED_SOURCE_LOCK_RECEIPT_SHA256,
        "source_lock_manifest_sha256": EXPECTED_SOURCE_LOCK_MANIFEST_SHA256,
        "batch_download_plan_sha256": sha256_file(
            source_lock_dir / f"batch_{batch_id:03d}_downloads.csv"
        ),
        "batch_expected_ids_sha256": sha256_file(
            source_lock_dir / f"batch_{batch_id:03d}_expected_source_ids.txt"
        ),
        "extraction_qc_tool_sha256": sha256_file(Path(__file__).resolve()),
        "qc_engine_sha256": EXPECTED_QC_ENGINE_SHA256,
        "member_alias_amendment_sha256": EXPECTED_MEMBER_ALIAS_AMENDMENT_SHA256,
        "model_metrics_used": False,
        "protected_data_accessed": False,
        "synthetic_generation_authorized": False,
        "D4_training_authorized": False,
        "next_step": (
            "freeze_next_download_batch"
            if len(passed) == len(qc_rows)
            else "freeze_failure_and_amend_before_replacement"
        ),
    }
    outputs["batch_qc_receipt.json"] = canonical_json_bytes(receipt)
    outputs["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(outputs.items())
    ).encode("ascii")
    for name, payload in outputs.items():
        (working / name).write_bytes(payload)
    if qc_out_dir.exists():
        qc_out_dir.rmdir()
    os.replace(working, qc_out_dir)
    return {**summary, **receipt}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_lock_dir", type=Path, required=True)
    parser.add_argument("--batch_id", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--archive_dir", type=Path, required=True)
    parser.add_argument("--stl_out_dir", type=Path, required=True)
    parser.add_argument("--qc_out_dir", type=Path, required=True)
    parser.add_argument(
        "--member_alias_amendment",
        type=Path,
        default=Path(
            "docs/mamba_v14_d4_mug500plus_source100_qc_member_alias_amendment_v1.json"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    qc_engine = Path(__file__).resolve().with_name("qc_mug500plus_clear_stl.py")
    if sha256_file(qc_engine) != EXPECTED_QC_ENGINE_SHA256:
        raise RuntimeError("Frozen MUG500+ QC engine drifted")
    if sha256_file(args.member_alias_amendment) != EXPECTED_MEMBER_ALIAS_AMENDMENT_SHA256:
        raise RuntimeError("Frozen member-alias amendment drifted")
    amendment = json.loads(args.member_alias_amendment.read_text(encoding="utf-8"))
    if (
        amendment.get("status") != "frozen_before_geometry_qc"
        or amendment.get("scope", {}).get("generic_fuzzy_matching_forbidden") is not True
        or amendment.get("scope", {}).get("source_selection_changed") is not False
        or amendment.get("trigger", {}).get("model_executed_before_amendment") is not False
    ):
        raise RuntimeError("Member-alias amendment semantics changed")
    plan, sources = read_batch_contract(args.source_lock_dir, args.batch_id)
    verify_archives(plan, args.archive_dir)
    extraction_rows = extract_batch(plan, sources, args.archive_dir, args.stl_out_dir)
    qc_rows = qc_rows_for_sources(sources, args.stl_out_dir)
    result = freeze_qc(
        args.source_lock_dir,
        args.batch_id,
        extraction_rows,
        qc_rows,
        args.qc_out_dir,
    )
    print(f"[saved] {args.stl_out_dir}")
    print(f"[saved] {args.qc_out_dir}")
    print(
        f"[done] batch={args.batch_id:03d} pass={result['qc_pass_sources']} "
        f"fail={result['qc_fail_sources']} status={result['status']}"
    )
    print("[locked] model=false protected=false synthetic_generation=false training=false")


if __name__ == "__main__":
    main()
