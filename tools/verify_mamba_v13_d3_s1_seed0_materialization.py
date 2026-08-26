#!/usr/bin/env python3
"""Verify the frozen, non-runnable S1 seed-0 materialized configs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import yaml


FOLDS = ("A", "B", "C", "D")
TARGET_RATIO = 0.075


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--receipt_dir", type=Path, required=True)
    args = parser.parse_args()
    config_dir = args.config_dir.resolve()
    receipt_dir = args.receipt_dir.resolve()

    for line in (receipt_dir / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = receipt_dir / name.lstrip("*")
        assert path.is_file() and sha256_file(path) == expected.lower()
    receipt_path = receipt_dir / "s1_seed0_materialization_receipt.json"
    sidecar = Path(str(receipt_path) + ".sha256").read_text(encoding="ascii").split()
    assert sidecar[0].lower() == sha256_file(receipt_path)
    assert Path(sidecar[1]).name == receipt_path.name
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "S1_seed0_fold_configs_materialized_training_locked"
    assert receipt["candidate"] == "S1" and receipt["seed"] == 0
    assert set(receipt["folds"]) == set(FOLDS) and receipt["fold_count"] == 4
    assert receipt["optimizer_steps"] == 0
    assert receipt["development_metrics_consumed"] is False
    assert receipt["weights_pooled_rounded_clipped_or_manually_adjusted"] is False
    assert receipt["S1_training_authorization_allowed_next"] is True
    assert receipt["S1_training_authorized"] is False
    assert receipt["S2_calibration_authorized"] is False
    assert receipt["S2_full_training_authorized"] is False
    assert receipt["holdout_authorized"] is False
    assert receipt["selection_started"] is False

    expected_names = {
        f"MambaV13D3_S1_fold{fold}_seed0.materialized.yaml" for fold in FOLDS
    }
    assert {path.name for path in config_dir.glob("*.yaml")} == expected_names
    for fold in FOLDS:
        binding = receipt["folds"][fold]
        ratio = float(binding["fold_raw_ratio_median"])
        weight = float(binding["calibrated_weight"])
        assert math.isclose(weight, TARGET_RATIO / ratio, rel_tol=1e-14, abs_tol=0.0)
        path = config_dir / f"MambaV13D3_S1_fold{fold}_seed0.materialized.yaml"
        assert sha256_file(path) == binding["materialized_config"]["sha256"]
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        execution = config["d3_execution"]
        dense = config["model"]["dense_contact_objective"]
        assert execution["status"] == "materialized_s1_seed0_training_not_authorized"
        assert execution["candidate"] == "S1" and execution["fold"] == fold
        assert execution["training_authorized"] is False
        assert execution["holdout_authorized"] is False
        assert execution["S1_training_authorized"] is False
        assert execution["S2_authorized"] is False
        assert execution["selection_started"] is False
        assert dense["enabled"] is True
        assert float(dense["weight"]) == weight
        assert dense["threshold_mm"] == 2.0
        assert dense["temperature_mm"] == 0.25
        assert dense["tail_fraction"] == 0.1
        serialized = path.read_text(encoding="utf-8")
        assert "locked_holdout_case_ids" not in serialized
        assert "manifest_split: locked_holdout" not in serialized
    print("[ok] four S1 fold weights exactly match frozen calibration receipts")
    print("[ok] all materialized config hashes and non-runnable semantics are valid")
    print("[locked] training=false S2=false holdout=false selection=false")


if __name__ == "__main__":
    main()
