#!/usr/bin/env python3
"""Verify the S0-only runtime authorization and all four config hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


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
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    config_dir = args.config_dir.resolve()
    receipt_path = args.receipt.resolve()
    sidecar = Path(str(receipt_path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    assert fields[0].lower() == sha256_file(receipt_path)
    assert Path(fields[1]).name == receipt_path.name
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "S0_seed0_runtime_configs_authorized"
    assert receipt["candidate"] == "S0" and receipt["seed"] == 0
    assert receipt["folds"] == list(FOLDS)
    assert receipt["training_authorized"] is True
    assert receipt["S1_authorized"] is False
    assert receipt["S2_authorized"] is False
    assert receipt["holdout_authorized"] is False
    assert receipt["selection_started"] is False
    expected_names = {
        f"MambaV13D3_S0_fold{fold}_seed0.yaml" for fold in FOLDS
    }
    assert set(receipt["runtime_config_sha256"]) == expected_names
    assert {path.name for path in config_dir.glob("*.yaml")} == expected_names
    for fold in FOLDS:
        name = f"MambaV13D3_S0_fold{fold}_seed0.yaml"
        path = config_dir / name
        assert sha256_file(path) == receipt["runtime_config_sha256"][name]
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        execution = config["d3_execution"]
        assert execution["candidate"] == "S0"
        assert execution["fold"] == fold and execution["seed"] == 0
        assert execution["status"] == "runtime_authorized_s0_seed0"
        assert execution["training_authorized"] is True
        assert execution["holdout_authorized"] is False
        assert execution["S1_authorized"] is False
        assert execution["S2_authorized"] is False
        assert config["model"]["dense_contact_objective"]["enabled"] is False
        assert config["model"]["rim_query_allocation"]["enabled"] is False
        serialized = path.read_text(encoding="utf-8")
        assert "locked_holdout_case_ids" not in serialized
        assert "manifest_split: locked_holdout" not in serialized
    print("[ok] four S0 seed-0 runtime config hashes match the receipt")
    print("[authorized] S0 folds A-D only")
    print("[locked] S1=false S2=false holdout=false selection_started=false")


if __name__ == "__main__":
    main()
