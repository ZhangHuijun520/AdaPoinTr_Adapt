#!/usr/bin/env python3
"""Verify a restored D5-A V0/V1 zero-step credential archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


EXPECTED_STATUS = "D5A_V0_V1_zero_step_frozen_complete_training_still_locked"
EXPECTED_COMMIT = "1480a9bc0957528182c11bfddd722b53517b5388"
EXPECTED_TAG = "mamba-adapter-v15-d5a-zero-step-preflight-v1"
EXPECTED_D4_RESULT = (
    "2f9f061f8649d06b6c45006510a0a2e3a64e2ba1496f03a3e05dc24053bb325d"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_manifest(root: Path, name: str = "files.sha256") -> int:
    manifest = root / name
    if not manifest.is_file():
        raise RuntimeError(f"Missing manifest: {manifest}")
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, relative = line.split(maxsplit=1)
        path = root / relative.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
        count += 1
    return count


def verify_sidecar(path: Path) -> None:
    sidecar = Path(str(path) + ".sha256")
    if not sidecar.is_file():
        raise RuntimeError(f"Missing sidecar: {sidecar}")
    expected = sidecar.read_text(encoding="ascii").split()[0].lower()
    if sha256_file(path) != expected:
        raise RuntimeError(f"Receipt sidecar mismatch: {path}")


def validate_candidate(receipt: Mapping[str, Any]) -> None:
    if not (
        receipt.get("status") == "D5_candidate_training_protocol_locked_non_runnable"
        and receipt.get("candidate_count") == 2
        and receipt.get("fold_count") == 4
        and receipt.get("non_runnable_template_count") == 13
        and receipt.get("D5A_seed0_training_authorized") is False
        and receipt.get("D5A_seed1_training_authorized") is False
        and receipt.get("D5B_implementation_authorized") is False
        and receipt.get("D5B_training_authorized") is False
        and receipt.get("D5_candidate_selection_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Candidate protocol lock semantics are invalid")


def validate_zero(receipt: Mapping[str, Any]) -> None:
    if not (
        receipt.get("status") == "V0_V1_implementation_zero_step_preflight_passed"
        and receipt.get("folds") == 4
        and receipt.get("train_probe_cases") == 4
        and receipt.get("candidates_per_probe") == 2
        and receipt.get("backward_passes") == 8
        and receipt.get("optimizer_constructed") is False
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("checkpoint_loaded") is False
        and receipt.get("checkpoint_written") is False
        and receipt.get("dev_cases_accessed") == 0
        and receipt.get("D5A_seed0_training_authorized") is False
        and receipt.get("D5A_seed1_training_authorized") is False
        and receipt.get("D5B_implementation_authorized") is False
        and receipt.get("D5B_training_authorized") is False
        and receipt.get("D5_candidate_selection_authorized") is False
        and receipt.get("proposal_confirmation_accessed") is False
        and receipt.get("completion_holdout_accessed") is False
        and receipt.get("official_test_accessed") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Zero-step receipt semantics are invalid")


def validate_result(summary: Mapping[str, Any]) -> None:
    if not (
        summary.get("status") == EXPECTED_STATUS
        and summary.get("source_commit") == EXPECTED_COMMIT
        and summary.get("source_tag") == EXPECTED_TAG
        and summary.get("folds") == 4
        and summary.get("metric_rows") == 8
        and summary.get("backward_passes") == 8
        and summary.get("optimizer_constructed") is False
        and summary.get("optimizer_steps") == 0
        and summary.get("model_updates") == 0
        and summary.get("checkpoint_loaded") is False
        and summary.get("checkpoint_written") is False
        and summary.get("dev_cases_accessed") == 0
        and set(summary.get("candidate_aggregates", {})) == {"V0", "V1"}
        and summary.get("D5A_seed0_training_authorized") is False
        and summary.get("D5A_seed1_training_authorized") is False
        and summary.get("D5B_implementation_authorized") is False
        and summary.get("D5B_training_authorized") is False
        and summary.get("D5_candidate_selection_authorized") is False
        and summary.get("proposal_confirmation_accessed") is False
        and summary.get("completion_holdout_accessed") is False
        and summary.get("official_test_accessed") is False
        and summary.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Complete result summary semantics are invalid")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()

    restore = args.restore_root.resolve()
    repo = restore / "adapointr_work/PoinTr"
    logs = repo / "logs/mamba_v15_d5_contact_support"
    candidate = logs / "candidate_training_protocol_v1"
    zero = logs / "d5a_zero_step_preflight_v1"
    result = logs / "d5a_zero_step_result_freeze_v1"
    transport_dir = logs / "d5a_overlay_transport_normalization_v1"
    lineage_dir = logs / "d5a_d4_parent_lineage_hotfix1_v1"
    audit = logs / "development_generation_audit_v1"
    locks = restore / "datasets/MUG500plusD5Development100_v1/data_locks"

    payload_count = verify_manifest(restore, "payload_manifest.sha256")
    for root in (candidate, zero, result, audit):
        verify_manifest(root)
    for name in (
        "mug500plus_d5_development100_qc_lock_v1",
        "mug500plus_d5_development400_fourfold_protocol_lock_v1",
    ):
        verify_manifest(locks / name)

    transport_path = transport_dir / "overlay_transport_normalization_receipt.json"
    lineage_path = lineage_dir / "d4_parent_lineage_hotfix_receipt.json"
    verify_sidecar(transport_path)
    verify_sidecar(lineage_path)

    candidate_receipt = read_json(candidate / "protocol_lock_receipt.json")
    zero_receipt = read_json(zero / "zero_step_preflight_receipt.json")
    result_summary = read_json(result / "d5a_v0_v1_zero_step_result_summary.json")
    transport = read_json(transport_path)
    lineage = read_json(lineage_path)
    metadata = read_json(restore / "archive_metadata.json")

    validate_candidate(candidate_receipt)
    validate_zero(zero_receipt)
    validate_result(result_summary)

    rows = list(
        csv.DictReader(
            (zero / "fold_candidate_probe_metrics.csv").open(
                encoding="utf-8", newline=""
            )
        )
    )
    if len(rows) != 8 or {(row["fold"], row["candidate"]) for row in rows} != {
        (fold, candidate_name)
        for fold in ("A", "B", "C", "D")
        for candidate_name in ("V0", "V1")
    }:
        raise RuntimeError("Archived zero-step metric pairing is incomplete")

    if not (
        transport.get("status") == "transport_crlf_normalized_to_canonical_lf"
        and transport.get("semantic_drift_detected") is False
        and transport.get("training_started") is False
        and lineage.get("status") == "exact_frozen_parent_report_restored"
        and lineage.get("post_hotfix_sha256") == EXPECTED_D4_RESULT
        and lineage.get("report_content_changed") is False
        and lineage.get("training_started") is False
        and metadata.get("checkpoints_archived") == 0
        and metadata.get("npz_archived") == 0
        and metadata.get("stl_archived") == 0
        and metadata.get("sealed_geometry_archived") is False
        and metadata.get("training_started") is False
    ):
        raise RuntimeError("Transport, lineage, or archive boundary is invalid")

    forbidden_suffixes = (".pth", ".pt", ".ckpt", ".npz", ".stl")
    forbidden = [
        path
        for path in restore.rglob("*")
        if path.is_file() and path.name.lower().endswith(forbidden_suffixes)
    ]
    if forbidden:
        raise RuntimeError(f"Forbidden model/geometry artifacts archived: {forbidden[:5]}")

    required = (
        repo / "docs/mamba_v15_d5a_zero_step_result_freeze_protocol_v1.json",
        repo / "tools/freeze_mamba_v15_d5a_zero_step_result.py",
        repo / "tools/verify_mamba_v15_d5a_zero_step_archive.py",
        result / "d5a_v0_v1_zero_step_complete_result_zh.md",
        restore / "environment_v1/conda_explicit.txt",
        restore / "environment_v1/python_packages.txt",
        restore / "environment_v1/runtime.json",
        restore / "environment_v1/git_repository.json",
    )
    if not all(path.is_file() for path in required):
        raise RuntimeError("Required report, code, or environment metadata is missing")

    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] candidate lock, 8 zero-step rows, result report and receipts match")
    print("[excluded] checkpoints, NPZ, STL and sealed geometry are absent")
    print("[locked] training=false seed1=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
