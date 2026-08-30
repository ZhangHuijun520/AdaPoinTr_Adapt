#!/usr/bin/env python3
"""Verify a restored D4-A negative-result archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FOLDS = ("A", "B", "C", "D")
EXPECTED_HITS = {"A": 85, "B": 80, "C": 83, "D": 84}


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path) -> None:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()

    restore = args.restore_root.resolve()
    repo = restore / "adapointr_work/PoinTr"
    logs = repo / "logs/mamba_v14_d4_contact_support"
    folds = logs / "d4a_head_only_seed0_v1"
    authorization = logs / "d4a_training_authorization_v1"
    completion = logs / "d4a_training_completion_v1"
    posthoc = logs / "d4a_failure_decomposition_posthoc_v1"

    for root in (
        authorization,
        completion,
        posthoc,
        logs / "d4a_zero_step_preflight_v1",
        logs / "d4_candidate_training_protocol_v1",
        logs / "d4_m2_generation_audit_v1",
    ):
        verify_manifest(root)

    completion_receipt = json.loads(
        (completion / "d4a_training_completion_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    if not (
        completion_receipt.get("status")
        == "D4A_frozen_negative_all_case_gate_failed"
        and completion_receipt.get("development_cases") == 400
        and completion_receipt.get("development_sources") == 100
        and completion_receipt.get("selected_hits") == 332
        and completion_receipt.get("selected_misses") == 68
        and completion_receipt.get("all_required_outputs_finite") is True
        and completion_receipt.get("D4A_all_case_gate_passed") is False
        and completion_receipt.get("T0_T1_T2_materialization_authorized_next")
        is False
        and completion_receipt.get("protected_data_accessed") is False
    ):
        raise RuntimeError("Completion receipt semantics are invalid")

    for fold in FOLDS:
        root = folds / f"fold{fold}_seed0"
        verify_manifest(root)
        run = json.loads((root / "run_receipt.json").read_text(encoding="utf-8"))
        summary = json.loads((root / "fold_summary.json").read_text(encoding="utf-8"))
        checkpoint = root / run["artifacts"]["head_final_epoch"]["name"]
        if not (
            run.get("fold") == fold
            and run.get("optimizer_steps") == 1900
            and run.get("development_evaluation_count") == 1
            and run.get("protected_data_accessed") is False
            and checkpoint.is_file()
            and sha256_file(checkpoint)
            == run["artifacts"]["head_final_epoch"]["sha256"]
            and summary.get("case_hits") == EXPECTED_HITS[fold]
            and summary.get("fold_gate_passed") is False
        ):
            raise RuntimeError(f"Fold {fold} archive semantics are invalid")

    posthoc_summary = json.loads(
        (posthoc / "failure_decomposition_summary.json").read_text(
            encoding="utf-8"
        )
    )
    if not (
        posthoc_summary.get("status")
        == "D4A_negative_posthoc_failure_decomposition_complete"
        and posthoc_summary.get("original_hits") == 332
        and posthoc_summary.get("original_misses") == 68
        and posthoc_summary.get("miss_failure_stage_counts")
        == {
            "ranking_miss_top256": 2,
            "selector_dropped_all_pool_positive": 66,
        }
        and posthoc_summary.get("frozen_replay_exact") is True
        and posthoc_summary.get("model_updates") == 0
        and posthoc_summary.get("optimizer_steps") == 0
        and posthoc_summary.get("T0_T1_T2_materialization_authorized") is False
        and posthoc_summary.get("D4_candidate_selection_authorized") is False
        and posthoc_summary.get("protected_data_accessed") is False
    ):
        raise RuntimeError("Post-hoc archive semantics are invalid")

    required = (
        repo / "docs/mamba_v14_d4a_head_only_feasibility_complete_negative_result_zh.md",
        repo / "docs/mamba_v14_d4a_failure_decomposition_posthoc_protocol_v1.json",
        restore / "environment_v1/conda_explicit.txt",
        restore / "environment_v1/python_packages.txt",
        restore / "environment_v1/runtime.json",
        restore / "environment_v1/git_repository.json",
        restore / "payload_manifest.sha256",
    )
    if not all(path.is_file() for path in required):
        raise RuntimeError("Archive documentation or environment metadata is missing")

    print("[ok] four D4-A final head checkpoints and fold receipts match")
    print("[ok] 332/400 frozen-negative and 2/66 post-hoc semantics match")
    print("[locked] T0/T1/T2=false selection=false protected=false")


if __name__ == "__main__":
    main()
