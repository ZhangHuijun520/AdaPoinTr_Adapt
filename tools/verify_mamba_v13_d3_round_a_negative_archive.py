#!/usr/bin/env python3
"""Verify a restored Mamba v1.3 D3 Round-A frozen-negative archive."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FOLDS = ("A", "B", "C", "D")
REPORT = "docs/mamba_v13_d3_round_a_s0_s1_s2_complete_negative_result_zh.md"
REPORT_SHA256 = "65ff436a3e7dc1795807a4b75538a969dafc4d7aae9f68189ff52dd671ccc516"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path, manifest: Path) -> None:
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Archive manifest mismatch: {path}")


def verify_sidecar(path: Path) -> None:
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    if (
        len(fields) < 2
        or Path(fields[1]).name != path.name
        or sha256_file(path) != fields[0].lower()
    ):
        raise RuntimeError(f"SHA256 sidecar mismatch: {path}")


def load_completion(root: Path, candidate: str) -> tuple[Path, dict]:
    relative = {
        "S0": "logs/mamba_v13_d3_mug500plus/s0_seed0_completion_v1/s0_seed0_completion_receipt.json",
        "S1": "logs/mamba_v13_d3_mug500plus/s1_seed0_completion_v1/s1_seed0_completion_receipt.json",
    }[candidate]
    path = root / relative
    verify_sidecar(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    expected_status = {
        "S0": "S0_seed0_frozen_ready_for_S2_feasibility",
        "S1": "S1_seed0_frozen_ready_for_preregistered_gate_analysis",
    }[candidate]
    if not (
        value.get("status") == expected_status
        and value.get("candidate") == candidate
        and value.get("seed") == 0
        and value.get("development_cases") == 400
        and value.get("holdout_authorized") is False
        and value.get("selection_started") is False
    ):
        raise RuntimeError(f"Invalid archived {candidate} completion")
    return path, value


def archived_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        raise RuntimeError(f"Expected a repository-relative archived path: {raw}")
    return root / path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()

    metadata = root / "metadata"
    verify_manifest(root, metadata / "METADATA.sha256")
    verify_manifest(root, metadata / "MANIFEST.sha256")
    verify_manifest(root, metadata / "BNCal_CHECKPOINTS.sha256")
    if sha256_file(root / REPORT) != REPORT_SHA256:
        raise RuntimeError("Archived complete negative-result report has drifted")

    checkpoint_paths = set()
    for candidate in ("S0", "S1"):
        _, completion = load_completion(root, candidate)
        for fold in FOLDS:
            record_path = archived_path(root, completion["run_records"][fold]["path"])
            verify_sidecar(record_path)
            if sha256_file(record_path) != completion["run_records"][fold]["sha256"]:
                raise RuntimeError(f"{candidate} fold {fold} run-record hash mismatch")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            if not (
                record.get("status") == "frozen_complete_development_fold"
                and record.get("candidate") == candidate
                and record.get("fold") == fold
                and record.get("seed") == 0
                and record.get("dev_cases") == 100
                and record.get("holdout_inference_consumed") is False
                and record.get("holdout_metrics_consumed") is False
                and record.get("holdout_visual_review_consumed") is False
                and record.get("selection_started") is False
            ):
                raise RuntimeError(f"Invalid archived {candidate} fold {fold} run record")
            checkpoint = record["artifacts"]["checkpoint"]
            checkpoint_path = archived_path(root, checkpoint["path"])
            if (
                checkpoint_path.name != "ckpt-last-bncal.pth"
                or not checkpoint_path.is_file()
                or sha256_file(checkpoint_path) != checkpoint["sha256"]
            ):
                raise RuntimeError(f"Invalid archived BNCal checkpoint: {checkpoint_path}")
            checkpoint_paths.add(checkpoint_path.resolve())

    archived_bncal = {path.resolve() for path in root.rglob("ckpt-last-bncal.pth")}
    if len(checkpoint_paths) != 8 or archived_bncal != checkpoint_paths:
        raise RuntimeError(
            f"Expected exactly eight receipt-bound BNCal checkpoints, found {len(archived_bncal)}"
        )

    s2_path = root / (
        "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_negative_freeze_v1/"
        "negative_result_receipt.json"
    )
    s2 = json.loads(s2_path.read_text(encoding="utf-8"))
    if not (
        s2.get("status") == "frozen_negative_high_hit_rate_failed_all_case_safety_gate"
        and s2.get("S2_full_training_authorized") is False
        and s2.get("holdout_accessed") is False
        and s2.get("selection_started") is False
    ):
        raise RuntimeError("Archived S2 negative-result semantics are invalid")

    gate_dir = root / "logs/mamba_v13_d3_mug500plus/round_a_seed0_gate_v1"
    verify_manifest(gate_dir, gate_dir / "files.sha256")
    gate = json.loads((gate_dir / "round_a_selection_receipt.json").read_text())
    if not (
        gate.get("status") == "round_a_frozen_negative_no_experimental_candidate_passed"
        and gate.get("S1_passed_all_gates") is False
        and gate.get("S2_full_training_eligible") is False
        and gate.get("seed1_authorized") is False
        and gate.get("round_a_gate_selection_completed") is True
        and gate.get("holdout_accessed") is False
        and gate.get("holdout_authorized") is False
        and gate.get("official_test_accessed") is False
        and gate.get("candidate_or_rule_revision_authorized") is False
    ):
        raise RuntimeError("Archived Round-A frozen-negative semantics are invalid")

    protected = (metadata / "PROTECTED_SPLITS.txt").read_text(encoding="utf-8")
    required_locks = (
        "seed1_authorized=false",
        "holdout_accessed=false",
        "official_test_accessed=false",
        "candidate_or_rule_revision_authorized=false",
    )
    if not all(item in protected for item in required_locks):
        raise RuntimeError("Protected-split archive declaration is incomplete")

    print("[ok] D3 Round-A archive manifest and eight BNCal checkpoints match")
    print("[ok] S0/S1/S2 lineage and Round-A frozen-negative semantics match")
    print("[locked] seed1=false holdout=false official_test=false rule_revision=false")


if __name__ == "__main__":
    main()
