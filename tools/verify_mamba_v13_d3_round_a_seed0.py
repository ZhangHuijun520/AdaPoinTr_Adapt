#!/usr/bin/env python3
"""Verify the immutable D3 Round-A seed-0 gate-analysis result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result_dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.result_dir.resolve()
    manifest = root / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Round-A artifact mismatch: {path}")
    sidecar = root / "files.sha256.sha256"
    expected, name = sidecar.read_text(encoding="ascii").split()[:2]
    if Path(name).name != manifest.name or sha256_file(manifest) != expected.lower():
        raise RuntimeError("Round-A manifest sidecar mismatch")
    receipt = json.loads((root / "round_a_selection_receipt.json").read_text(encoding="utf-8"))
    gates = receipt["S1_gates"]
    if not (
        receipt.get("analysis_version") == "mamba-v13-d3-round-a-seed0-gate-analysis-v1"
        and receipt.get("status") == "round_a_frozen_negative_no_experimental_candidate_passed"
        and receipt.get("case_universe") == 400
        and receipt["S1"]["disaster_count"] <= receipt["S0"]["disaster_count"]
        and receipt["S1"]["dense_zero_contact_at_2mm_count"] > 0
        and gates["dense_zero_contact_at_2mm_equals_zero"] is False
        and gates["all_required_metrics_finite"] is False
        and receipt.get("S1_passed_all_gates") is False
        and receipt.get("S2_full_training_eligible") is False
        and receipt.get("round_a_gate_selection_completed") is True
        and receipt.get("seed1_authorized") is False
        and receipt.get("holdout_accessed") is False
        and receipt.get("holdout_authorized") is False
        and receipt.get("official_test_accessed") is False
        and receipt.get("candidate_or_rule_revision_authorized") is False
    ):
        raise RuntimeError("D3 Round-A frozen negative semantics are invalid")
    print("[ok] D3 Round-A files, pairing result, and negative semantics match")
    print("[negative] S1 failed dense-zero/finite gates; S2 is ineligible")
    print("[locked] seed1=false holdout=false official_test=false rule_revision=false")


if __name__ == "__main__":
    main()
