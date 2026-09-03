#!/usr/bin/env python3
"""Freeze four completed D6-A calibration folds and runtime weights."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FOLDS = ("A", "B", "C", "D")
VERSION = "mamba-v16-d6a-r1-gradient-calibration-completion-v1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_manifest(root: Path) -> None:
    for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen fold mismatch: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fold_root", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise RuntimeError(f"Completion output already exists: {output}")
    weights = {}
    fold_hashes = {}
    for fold in FOLDS:
        root = args.fold_root.resolve() / f"fold{fold}_seed0"
        verify_manifest(root)
        receipt_path = root / "calibration_fold_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not (
            receipt.get("status") == "D6A_R1_fold_gradient_calibration_complete"
            and receipt.get("fold") == fold
            and receipt.get("batches") == 8
            and receipt.get("optimizer_steps") == 0
            and receipt.get("model_updates") == 0
            and receipt.get("model_state_unchanged") is True
            and receipt.get("development_dev_cases_accessed") == 0
            and receipt.get("protected_or_sealed_data_accessed") is False
        ):
            raise RuntimeError(f"Invalid completed calibration fold: {fold}")
        weights[fold] = {
            "lambda_support": receipt["lambda_support"],
            "lambda_shape": receipt["lambda_shape"],
        }
        fold_hashes[fold] = {
            "manifest": sha256_file(root / "files.sha256"),
            "receipt": sha256_file(receipt_path),
        }
    completion = {
        "completion_version": VERSION,
        "status": "D6A_R1_gradient_calibration_folds_A_D_complete",
        "candidate": "R1", "seed": 0, "fold_weights": weights,
        "fold_lineage_sha256": fold_hashes,
        "optimizer_steps": 0, "model_updates": 0,
        "seed0_training_authorized": False, "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False, "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_receipt_bound_R1_runtime_config_materialization_and_training_authorization",
    }
    runtime = {
        "status": "D6A_R1_calibrated_fold_weights_frozen_training_not_authorized",
        "candidate": "R1", "seed": 0, "fold_weights": weights,
        "loss": "L_point + lambda_support * L_support + lambda_shape * L_shape",
        "training_authorized": False,
    }
    files = {
        "calibration_completion_receipt.json": canonical_json(completion),
        "r1_calibrated_fold_weights.json": canonical_json(runtime),
    }
    output.mkdir(parents=True)
    for name, payload in files.items():
        (output / name).write_bytes(payload)
    (output / "files.sha256").write_text(
        "".join(f"{hashlib.sha256(payload).hexdigest()}  {name}\n" for name, payload in sorted(files.items())),
        encoding="ascii",
    )
    print(f"[saved] immutable D6-A calibration completion: {output}")
    print("[done] folds=A-D; training remains unauthorized")
    print("[locked] seed1=false confirmation=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
