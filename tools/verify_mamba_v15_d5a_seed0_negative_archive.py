#!/usr/bin/env python3
"""Verify a restored D5-A seed-0 negative-result archive."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CANDIDATES = ("V0", "V1")
FOLDS = ("A", "B", "C", "D")
EXPECTED_TOTALS = {"V0": (322, 78), "V1": (368, 32)}
EXPECTED_RECALL = {
    "8": 308,
    "16": 343,
    "32": 368,
    "64": 393,
    "128": 400,
    "256": 400,
}
EXPECTED_TRANSITIONS = {
    "hit_to_hit": 312,
    "hit_to_miss": 10,
    "miss_to_hit": 56,
    "miss_to_miss": 22,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path) -> str:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
    return sha256_file(manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()

    restore = args.restore_root.resolve()
    repo = restore / "adapointr_work/PoinTr"
    logs = repo / "logs/mamba_v15_d5_contact_support"
    folds_root = logs / "d5a_seed0_head_only_v1"
    authorization = logs / "d5a_seed0_training_authorization_v1"
    completion = logs / "d5a_seed0_training_completion_v1"
    posthoc = logs / "d5a_seed0_csv_posthoc_v1"

    required_manifests = (
        logs / "candidate_training_protocol_v1",
        logs / "development_generation_audit_v1",
        logs / "d5a_zero_step_preflight_v1",
        authorization,
        completion,
        posthoc,
    )
    for root in required_manifests:
        verify_manifest(root)

    completion_receipt = json.loads(
        (completion / "d5a_seed0_training_completion_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    if not (
        completion_receipt.get("status")
        == "D5A_seed0_frozen_negative_V1_all_case_gate_failed"
        and completion_receipt.get("paired_development_cases") == 400
        and completion_receipt.get("development_sources") == 100
        and completion_receipt.get("all_required_outputs_finite") is True
        and completion_receipt.get("exact_V0_V1_case_pairing") is True
        and completion_receipt.get("V1_seed0_all_case_gate_passed") is False
        and completion_receipt.get("D5A_seed1_training_authorized") is False
        and completion_receipt.get("proposal_confirmation_access_authorized") is False
        and completion_receipt.get("D5B_training_authorized") is False
        and completion_receipt.get("D5_candidate_selection_authorized") is False
        and completion_receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Completion receipt semantics are invalid")

    for candidate in CANDIDATES:
        expected_hits, expected_misses = EXPECTED_TOTALS[candidate]
        candidate_receipt = completion_receipt["candidates"][candidate]
        if not (
            candidate_receipt.get("development_cases") == 400
            and candidate_receipt.get("selected_hits") == expected_hits
            and candidate_receipt.get("selected_misses") == expected_misses
        ):
            raise RuntimeError(f"{candidate} completion totals are invalid")

        folded_hits = 0
        for fold in FOLDS:
            root = folds_root / f"{candidate}_fold{fold}_seed0"
            manifest_sha = verify_manifest(root)
            run = json.loads((root / "run_receipt.json").read_text(encoding="utf-8"))
            summary = json.loads((root / "fold_summary.json").read_text(encoding="utf-8"))
            checkpoint = root / "head_final_epoch.pth"
            binding = candidate_receipt["folds"][fold]
            if not (
                run.get("candidate") == candidate
                and run.get("fold") == fold
                and run.get("optimizer_steps") == 1900
                and run.get("development_evaluation_count") == 1
                and run.get("protected_or_sealed_data_accessed") is False
                and summary.get("development_cases") == 100
                and checkpoint.is_file()
                and sha256_file(checkpoint)
                == run["artifacts"]["head_final_epoch"]["sha256"]
                and binding.get("files_manifest_sha256") == manifest_sha
                and binding.get("head_final_epoch_sha256") == sha256_file(checkpoint)
                and binding.get("hits") == summary.get("case_hits")
            ):
                raise RuntimeError(f"{candidate}/fold{fold} archive is invalid")
            folded_hits += int(summary["case_hits"])
        if folded_hits != expected_hits:
            raise RuntimeError(f"{candidate} fold hit total is invalid")

    posthoc_summary = json.loads(
        (posthoc / "d5a_seed0_csv_posthoc_summary.json").read_text(encoding="utf-8")
    )
    if not (
        posthoc_summary.get("status") == "D5A_seed0_negative_csv_posthoc_complete"
        and posthoc_summary.get("paired_cases") == 400
        and posthoc_summary.get("V0_hits") == 322
        and posthoc_summary.get("V0_misses") == 78
        and posthoc_summary.get("V1_hits") == 368
        and posthoc_summary.get("V1_misses") == 32
        and posthoc_summary.get("paired_transition_counts") == EXPECTED_TRANSITIONS
        and posthoc_summary.get("V1_counterfactual_recall_at_k") == EXPECTED_RECALL
        and posthoc_summary.get("V1_top32_miss_recoverable_at_64") == 25
        and posthoc_summary.get("V1_top32_miss_recoverable_at_128") == 32
        and posthoc_summary.get("V1_miss_rank_band_counts")
        == {"33-40": 9, "41-64": 16, "65-128": 7}
        and posthoc_summary.get("V1_miss_sources") == 30
        and posthoc_summary.get("V1_multi_miss_sources") == 2
        and posthoc_summary.get("model_updates") == 0
        and posthoc_summary.get("optimizer_steps") == 0
        and posthoc_summary.get("checkpoint_accessed") is False
        and posthoc_summary.get("geometry_accessed") is False
        and posthoc_summary.get("original_top32_gate_changed") is False
        and posthoc_summary.get("D5A_seed1_training_authorized") is False
        and posthoc_summary.get("D5B_training_authorized") is False
        and posthoc_summary.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("CSV-only post-hoc semantics are invalid")

    required = (
        repo / "docs/mamba_v15_d5a_seed0_complete_negative_result_and_csv_posthoc_zh.md",
        repo / "docs/mamba_v15_d5a_seed0_csv_posthoc_protocol_v1.json",
        repo / "tools/analyze_mamba_v15_d5a_seed0_csv_posthoc.py",
        repo / "scripts/run_mamba_v15_d5a_seed0_csv_posthoc.sh",
        restore / "environment_v1/conda_explicit.txt",
        restore / "environment_v1/python_packages.txt",
        restore / "environment_v1/runtime.json",
        restore / "environment_v1/git_repository.json",
        restore / "payload_manifest.sha256",
    )
    if not all(path.is_file() for path in required):
        raise RuntimeError("Archive documentation, code, or environment metadata is missing")

    print("[ok] eight D5-A final head checkpoints and fold receipts match")
    print("[ok] V0=322/400, V1=368/400 frozen-negative semantics match")
    print("[ok] CSV-only top-K, transition, and rank-band post-hoc semantics match")
    print("[locked] seed1=false confirmation=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
