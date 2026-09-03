#!/usr/bin/env python3
"""Verify a restored D6 development400 generation milestone archive."""

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
    "183ac5d7a1e6b3c2006ef0f933f1c78280da839dde492341c2c76ff6269e07c4"
)
EXPECTED_DATASET_MANIFEST_SHA256 = (
    "7c5967d6600aa2017e9c28aa3414594010b2033acf94c69f161f12889f243041"
)
EXPECTED_AUDIT_MANIFEST_SHA256 = (
    "fa14e67677aa64e1f0e2cdf96aa9d37062471ea3f774ca831d05bea1c95e7e7a"
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
        == "generated_training_locked_pending_D6_generation_audit"
        and receipt.get("source_skulls") == 100
        and receipt.get("derived_cases") == 400
        and receipt.get("D6A_R0_R1_implementation_frozen") is True
        and receipt.get("D6_gradient_calibration_authorized") is False
        and receipt.get("D6A_training_authorized") is False
        and receipt.get("D6_seed1_authorized") is False
        and receipt.get("D6B_training_authorized") is False
        and receipt.get("candidate_selection_authorized") is False
        and receipt.get("proposal_confirmation_accessed") is False
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
        and summary.get("D6A_R0_R1_implementation_frozen") is True
        and summary.get("D6_gradient_calibration_authorized") is False
        and summary.get("D6A_training_authorized") is False
        and summary.get("D6_seed1_authorized") is False
        and summary.get("D6B_training_authorized") is False
        and summary.get("D6_candidate_selection_authorized") is False
        and summary.get("proposal_confirmation_accessed") is False
        and summary.get("official_test_accessed") is False
        and summary.get("next_step")
        == "freeze_a_separate_D6_gradient_calibration_protocol"
    )
    if not required:
        raise RuntimeError("Generation audit summary semantics are invalid")


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
    logs = repo / "logs/mamba_v16_d6_contact_support"
    dataset = restore / "datasets/MUG500plusD6Development400_v1"
    locks = restore / "datasets/MUG500plusD6Development100_v1/data_locks"
    audit = logs / "development_generation_audit_v1"

    payload_count = verify_manifest(restore, "payload_manifest.sha256")
    if sha256_file(dataset / "files.sha256") != EXPECTED_DATASET_MANIFEST_SHA256:
        raise RuntimeError("Frozen generation files.sha256 drifted")
    if sha256_file(audit / "files.sha256") != EXPECTED_AUDIT_MANIFEST_SHA256:
        raise RuntimeError("Frozen audit files.sha256 drifted")
    verify_manifest(dataset)
    verify_manifest(audit)

    for name in (
        "mug500plus_d6_source125_acquisition_lock_v1",
        "mug500plus_d6_development100_qc_lock_v1",
        "mug500plus_d6_development_generation_fourfold_protocol_lock_v1",
    ):
        verify_manifest(locks / name)
    verify_manifest(logs / "d6a_slot32_mechanism_protocol_lock_v1")
    verify_manifest(logs / "d6a_synthetic_zero_step_v1")

    generation_receipt = read_json(dataset / "generation_receipt.json")
    audit_summary = read_json(audit / "generation_audit_summary.json")
    metadata = read_json(restore / "archive_metadata.json")
    validate_generation_receipt(generation_receipt)
    validate_audit_summary(audit_summary)
    verify_derived_cases(dataset, audit)

    if not (
        metadata.get("source_archive_stream_sha256")
        == EXPECTED_SOURCE_ARCHIVE_SHA256
        and metadata.get("source_archive_stream_bytes") == 11007297410
        and metadata.get("source_stl_count") == 100
        and metadata.get("source_stl_file_bytes") == 19914032900
        and metadata.get("derived_cases_archived") == 400
        and metadata.get("source_stl_archived") is False
        and metadata.get("proposal_confirmation_geometry_archived") is False
        and metadata.get("model_checkpoints_archived") is False
    ):
        raise RuntimeError("Archive metadata semantics are invalid")

    forbidden_suffixes = (".stl", ".pth", ".pt", ".ckpt")
    if any(
        path.is_file() and path.suffix.lower() in forbidden_suffixes
        for path in restore.rglob("*")
    ):
        raise RuntimeError("Source geometry or model checkpoint is unexpectedly archived")

    required = (
        repo / "docs/mamba_v16_d6_development_generation_archive_protocol_v1.json",
        repo / "tools/verify_mamba_v16_d6_development_generation_archive.py",
        logs
        / "development_protocol_lf_hotfix2_v1"
        / "normalization_receipt.json",
        logs
        / "development_protocol_zero_step_parent_hotfix1_v1"
        / "parent_hotfix_installation_receipt.json",
        restore / "environment_v1/conda_explicit.txt",
        restore / "environment_v1/python_packages.txt",
        restore / "environment_v1/runtime.json",
        restore / "environment_v1/git_repository.json",
        restore / "payload_manifest.sha256",
    )
    if not all(path.is_file() for path in required):
        raise RuntimeError("Archive documentation, receipts, or environment is missing")

    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] 100 sources / 400 derived cases and all case hashes match")
    print("[ok] generation, three locks, mechanism, zero-step and audit match")
    print("[excluded] source STL, confirmation geometry and checkpoints are absent")
    print(
        "[locked] calibration=false training=false seed1=false "
        "D6B=false selection=false confirmation=false"
    )


if __name__ == "__main__":
    main()
