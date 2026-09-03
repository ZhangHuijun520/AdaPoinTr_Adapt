#!/usr/bin/env python3
"""Verify D6-A R1 calibration configs and execution authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "mamba-v16-d6a-gradient-calibration-execution-authorization-v1"
FOLDS = ("A", "B", "C", "D")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path) -> None:
    for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Authorization artifact mismatch: {path}")


def verify_authorization(config_dir: Path, auth_dir: Path) -> dict[str, Any]:
    config_dir, auth_dir = config_dir.resolve(), auth_dir.resolve()
    verify_manifest(auth_dir)
    receipt_path = auth_dir / "d6a_gradient_calibration_execution_authorization_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    sidecar = Path(str(receipt_path) + ".sha256")
    expected, name = sidecar.read_text(encoding="ascii").split()[:2]
    if Path(name).name != receipt_path.name or sha256_file(receipt_path) != expected:
        raise RuntimeError("Authorization receipt sidecar mismatch")
    if not (
        receipt.get("authorization_version") == VERSION
        and receipt.get("status") == "D6A_R1_seed0_folds_A_D_gradient_calibration_authorized"
        and receipt.get("candidate") == "R1"
        and receipt.get("fold_order") == list(FOLDS)
        and receipt.get("seed") == 0
        and receipt.get("calibration_execution_authorized") is True
        and all(receipt.get(key) is False for key in (
            "calibration_started", "optimizer_constructed", "seed0_training_authorized",
            "seed1_training_authorized", "proposal_confirmation_authorized",
            "D6B_authorized", "candidate_selection_authorized",
            "protected_or_sealed_data_accessed",
        ))
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
    ):
        raise RuntimeError("Unsafe D6-A calibration authorization semantics")

    for relative, expected_hash in receipt["implementation_sha256"].items():
        path = REPO_ROOT / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise RuntimeError(f"Authorized implementation drift: {relative}")

    runtime_lines = (auth_dir / "runtime_configs.sha256").read_text(encoding="ascii").splitlines()
    if len(runtime_lines) != 4:
        raise RuntimeError("Expected four calibration runtime configs")
    for fold in FOLDS:
        name = f"MambaV16D6A_R1_gradient_calibration_fold{fold}_seed0.json"
        path = config_dir / name
        binding = receipt["folds"][fold]
        if not path.is_file() or sha256_file(path) != binding["config"]["sha256"]:
            raise RuntimeError(f"Missing or drifted config: {fold}")
        config = json.loads(path.read_text(encoding="utf-8"))
        boundary = config.get("boundaries", {})
        if not (
            config.get("status") == "D6A_R1_fold_gradient_calibration_authorized_not_started"
            and config.get("candidate") == "R1"
            and config.get("fold") == fold
            and config.get("seed") == 0
            and config.get("batches") == 8
            and config.get("batch_size") == 8
            and config.get("target_support_ratio") == 0.5
            and config.get("target_shape_ratio") == 0.1
            and boundary.get("calibration_execution_authorized") is True
            and boundary.get("seed0_training_authorized") is False
            and boundary.get("seed1_training_authorized") is False
            and boundary.get("proposal_confirmation_authorized") is False
            and boundary.get("D6B_authorized") is False
            and boundary.get("protected_or_sealed_data_accessed") is False
        ):
            raise RuntimeError(f"Unsafe calibration config: {fold}")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    args = parser.parse_args()
    verify_authorization(args.config_dir, args.authorization_dir)
    print("[ok] D6-A R1 calibration authorization and four configs match")
    print("[authorized] gradient calibration folds A-D only; execution not started")
    print("[locked] training=false seed1=false confirmation=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
