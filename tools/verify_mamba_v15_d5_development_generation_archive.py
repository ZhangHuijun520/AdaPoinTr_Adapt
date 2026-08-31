#!/usr/bin/env python3
"""Verify a restored D5 development400 generation milestone archive."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


EXPECTED_STATUS = (
    "generation_integrity_passed_"
    "model_training_selection_and_sealed_still_locked"
)
EXPECTED_FOLDS = {"A": 100, "B": 100, "C": 100, "D": 100}
EXPECTED_FAMILIES = {
    "ellipsoid_large",
    "ellipsoid_medium",
    "ellipsoid_small",
    "irregular_medium",
}
EXPECTED_SOURCE_ARCHIVE_SHA256 = (
    "9d3544766188369783d8adfa99a6592dc32ccea7715d9b43a97ab1f493091a21"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_manifest(root: Path, manifest_name: str = "files.sha256") -> int:
    manifest = root / manifest_name
    if not manifest.is_file():
        raise RuntimeError(f"Missing manifest: {manifest}")
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
        count += 1
    return count


def validate_generation_receipt(receipt: Mapping[str, Any]) -> None:
    required = (
        receipt.get("status")
        == "generated_training_locked_pending_D5_generation_audit"
        and receipt.get("source_skulls") == 100
        and receipt.get("derived_cases") == 400
        and receipt.get("D5A_model_implementation_authorized") is False
        and receipt.get("D5A_training_authorized") is False
        and receipt.get("D5B_training_authorized") is False
        and receipt.get("candidate_selection_authorized") is False
        and receipt.get("proposal_confirmation_accessed") is False
        and receipt.get("completion_holdout_accessed") is False
        and receipt.get("official_test_accessed") is False
    )
    if not required:
        raise RuntimeError("Generation receipt semantics are invalid")


def validate_audit_summary(summary: Mapping[str, Any]) -> None:
    required_true = (
        "source_assets_rehashed",
        "all_derived_hashes_verified",
        "all_derived_hashes_unique",
        "manifest_cases_bijective",
        "all_npz_contracts_verified",
        "all_geometry_gates_verified",
        "all_four_family_bindings_verified",
        "all_source_fold_bindings_verified",
        "portable_paths",
    )
    required = (
        summary.get("status") == EXPECTED_STATUS
        and summary.get("source_skulls") == 100
        and summary.get("derived_cases") == 400
        and summary.get("fold_case_counts") == EXPECTED_FOLDS
        and set(summary.get("defect_families", [])) == EXPECTED_FAMILIES
        and all(summary.get(key) is True for key in required_true)
        and summary.get("D5A_model_implementation_authorized") is False
        and summary.get("D5A_training_authorized") is False
        and summary.get("D5B_training_authorized") is False
        and summary.get("D5_candidate_selection_authorized") is False
        and summary.get("proposal_confirmation_accessed") is False
        and summary.get("completion_holdout_accessed") is False
        and summary.get("official_test_accessed") is False
    )
    if not required:
        raise RuntimeError("Generation audit summary semantics are invalid")


def validate_transport_receipt(receipt: Mapping[str, Any]) -> None:
    required = (
        receipt.get("status")
        == "canonical_git_overlay_installed_lock_exact_preflight_passed"
        and receipt.get("protocol_lock_replacement_performed") is False
        and receipt.get("protocol_lock_exact_replay") is True
        and receipt.get("development_sources") == 100
        and receipt.get("planned_cases") == 400
        and receipt.get("generation_started") is False
        and receipt.get("model_implementation_authorized") is False
        and receipt.get("training_authorized") is False
        and receipt.get("selection_started") is False
        and receipt.get("proposal_confirmation_accessed") is False
        and receipt.get("completion_holdout_accessed") is False
    )
    if not required:
        raise RuntimeError("Overlay transport receipt semantics are invalid")


def verify_derived_cases(dataset: Path, audit: Path) -> None:
    rows = list(
        csv.DictReader(
            (audit / "derived_case_audit.csv").open(encoding="utf-8", newline="")
        )
    )
    if len(rows) != 400:
        raise RuntimeError(f"Expected 400 audit rows, found {len(rows)}")

    case_ids = set()
    hashes = set()
    fold_counts: collections.Counter[str] = collections.Counter()
    family_counts: collections.Counter[str] = collections.Counter()
    source_ids = set()

    for row in rows:
        case_id = row["case_id"]
        path = dataset / "cases" / f"{case_id}.npz"
        expected_hash = row["derived_case_sha256"].lower()
        if case_id in case_ids or not path.is_file():
            raise RuntimeError(f"Missing or duplicate derived case: {case_id}")
        if path.stat().st_size != int(row["file_bytes"]):
            raise RuntimeError(f"Derived case byte mismatch: {case_id}")
        if sha256_file(path) != expected_hash or expected_hash in hashes:
            raise RuntimeError(f"Derived case SHA256 mismatch: {case_id}")
        case_ids.add(case_id)
        hashes.add(expected_hash)
        fold_counts[row["fold"]] += 1
        family_counts[row["defect_type"]] += 1
        source_ids.add(row["source_id"])

    actual_cases = {path.stem for path in (dataset / "cases").glob("*.npz")}
    if actual_cases != case_ids:
        raise RuntimeError("Derived case directory is not bijective with audit rows")
    if dict(sorted(fold_counts.items())) != EXPECTED_FOLDS:
        raise RuntimeError(f"Fold counts differ: {dict(fold_counts)}")
    if set(family_counts) != EXPECTED_FAMILIES or set(family_counts.values()) != {100}:
        raise RuntimeError(f"Defect-family counts differ: {dict(family_counts)}")
    if len(source_ids) != 100:
        raise RuntimeError(f"Expected 100 source IDs, found {len(source_ids)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()

    restore = args.restore_root.resolve()
    repo = restore / "adapointr_work/PoinTr"
    logs = repo / "logs/mamba_v15_d5_contact_support"
    dataset = restore / "datasets/MUG500plusD5Development400_v1"
    locks = restore / "datasets/MUG500plusD5Development100_v1/data_locks"
    audit = logs / "development_generation_audit_v1"
    transport = logs / "d5_overlay_transport_normalization_v1"

    payload_count = verify_manifest(restore, "payload_manifest.sha256")
    verify_manifest(dataset)
    verify_manifest(audit)
    verify_manifest(transport)

    for name in (
        "mug500plus_d5_source150_acquisition_lock_v1",
        "mug500plus_d5_development100_qc_lock_v1",
        "mug500plus_d5_development400_fourfold_protocol_lock_v1",
    ):
        verify_manifest(locks / name)

    generation_receipt = read_json(dataset / "generation_receipt.json")
    audit_summary = read_json(audit / "generation_audit_summary.json")
    transport_receipt = read_json(
        transport / "overlay_transport_normalization_receipt.json"
    )
    metadata = read_json(restore / "archive_metadata.json")
    validate_generation_receipt(generation_receipt)
    validate_audit_summary(audit_summary)
    validate_transport_receipt(transport_receipt)
    verify_derived_cases(dataset, audit)

    if not (
        metadata.get("source_archive_sha256") == EXPECTED_SOURCE_ARCHIVE_SHA256
        and metadata.get("source_stl_count") == 100
        and metadata.get("source_stl_bytes") == 16820263850
        and metadata.get("derived_cases_archived") == 400
        and metadata.get("source_stl_archived") is False
        and metadata.get("sealed_geometry_archived") is False
    ):
        raise RuntimeError("Archive metadata semantics are invalid")

    if any(path.is_file() for path in restore.rglob("*.stl")):
        raise RuntimeError("Source or sealed STL geometry is unexpectedly archived")

    required = (
        repo / "docs/mamba_v15_d5_development_generation_archive_protocol_v1.json",
        repo / "tools/verify_mamba_v15_d5_development_generation_archive.py",
        restore / "environment_v1/conda_explicit.txt",
        restore / "environment_v1/python_packages.txt",
        restore / "environment_v1/runtime.json",
        restore / "environment_v1/git_repository.json",
        restore / "payload_manifest.sha256",
    )
    if not all(path.is_file() for path in required):
        raise RuntimeError("Archive documentation or environment metadata is missing")

    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] 100 sources / 400 derived cases and all case hashes match")
    print("[ok] generation, three locks, audit, transport receipt and environment match")
    print("[excluded] source STL and sealed geometry are absent")
    print("[locked] model=false training=false selection=false sealed=false")


if __name__ == "__main__":
    main()
