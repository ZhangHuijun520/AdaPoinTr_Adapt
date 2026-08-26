#!/usr/bin/env python3
"""Verify S1 seed-0 training authorization and implementation hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
FOLDS = ("A", "B", "C", "D")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    args = parser.parse_args()
    config_dir = args.config_dir.resolve()
    auth_dir = args.authorization_dir.resolve()
    for line in (auth_dir / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = auth_dir / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"S1 authorization tree mismatch: {path}")
    receipt_path = auth_dir / "s1_seed0_training_authorization_receipt.json"
    expected, name = Path(str(receipt_path) + ".sha256").read_text().split()[:2]
    assert Path(name).name == receipt_path.name
    assert sha256_file(receipt_path) == expected.lower()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "S1_seed0_folds_A_D_training_authorized"
    assert receipt["candidate"] == "S1" and receipt["seed"] == 0
    assert receipt["fold_order"] == list(FOLDS)
    assert receipt["epochs"] == 100 and receipt["bncal_required"] is True
    assert receipt["development_evaluation_authorized"] is True
    assert receipt["S1_training_authorized"] is True
    assert receipt["S2_calibration_authorized"] is False
    assert receipt["S2_full_training_authorized"] is False
    assert receipt["holdout_authorized"] is False
    assert receipt["official_test_authorized"] is False
    assert receipt["selection_started"] is False
    for name, expected in receipt["implementation_sha256"].items():
        path = REPO_ROOT / name
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"S1 authorized implementation drift: {name}")
    expected_names = {f"MambaV13D3_S1_fold{fold}_seed0.yaml" for fold in FOLDS}
    assert {path.name for path in config_dir.glob("*.yaml")} == expected_names
    for fold in FOLDS:
        binding = receipt["folds"][fold]
        path = config_dir / f"MambaV13D3_S1_fold{fold}_seed0.yaml"
        assert sha256_file(path) == binding["authorized_config"]["sha256"]
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        execution = config["d3_execution"]
        assert execution["status"] == "runtime_authorized_s1_seed0"
        assert execution["candidate"] == "S1" and execution["fold"] == fold
        assert execution["training_authorized"] is True
        assert execution["S1_training_authorized"] is True
        assert execution["holdout_authorized"] is False
        assert execution["S2_authorized"] is False
        assert execution["selection_started"] is False
        dense = config["model"]["dense_contact_objective"]
        assert dense["enabled"] is True
        assert float(dense["weight"]) == float(binding["calibrated_weight"])
        assert dense["threshold_mm"] == 2.0
        serialized = path.read_text(encoding="utf-8")
        assert "locked_holdout_case_ids" not in serialized
        assert "manifest_split: locked_holdout" not in serialized
    print("[ok] S1 authorized configs, fold weights, and implementation hashes match")
    print("[authorized] S1 seed-0 folds A-D development-only execution")
    print("[locked] S2=false holdout=false official_test=false selection=false")


if __name__ == "__main__":
    main()
