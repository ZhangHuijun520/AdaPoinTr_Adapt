#!/usr/bin/env python3
"""Verify D4-A runtime configs and the training authorization receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "mamba-v14-d4a-training-authorization-v1"
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    args = parser.parse_args()
    config_dir = args.config_dir.resolve()
    auth_dir = args.authorization_dir.resolve()
    verify_manifest(auth_dir)
    receipt_path = auth_dir / "d4a_training_authorization_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    sidecar = Path(str(receipt_path) + ".sha256")
    expected, name = sidecar.read_text(encoding="ascii").split()[:2]
    if Path(name).name != receipt_path.name or sha256_file(receipt_path) != expected:
        raise RuntimeError("Authorization receipt sidecar mismatch")
    if not (
        receipt.get("authorization_version") == VERSION
        and receipt.get("status")
        == "D4A_head_only_seed0_folds_A_D_training_authorized"
        and receipt.get("fold_order") == list(FOLDS)
        and receipt.get("epochs") == 50
        and receipt.get("batch_size") == 8
        and receipt.get("optimizer_steps_per_fold") == 1900
        and receipt.get("D4A_training_authorized") is True
        and receipt.get("T0_training_authorized") is False
        and receipt.get("T1_training_authorized") is False
        and receipt.get("T2_training_authorized") is False
        and receipt.get("D4_candidate_selection_authorized") is False
        and receipt.get("protected_data_accessed") is False
        and receipt.get("training_started") is False
        and receipt.get("selection_started") is False
    ):
        raise RuntimeError("D4-A authorization receipt semantics are invalid")

    implementation = receipt["implementation_sha256"]
    for relative, expected_hash in implementation.items():
        path = REPO_ROOT / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise RuntimeError(f"Authorized implementation drift: {relative}")

    runtime_lines = (
        auth_dir / "runtime_configs.sha256"
    ).read_text(encoding="ascii").splitlines()
    if len(runtime_lines) != 4:
        raise RuntimeError("Expected four authorized runtime configs")
    for fold in FOLDS:
        name = f"MambaV14D4A_fold{fold}_seed0.json"
        path = config_dir / name
        binding = receipt["folds"][fold]["runtime_config"]
        config = json.loads(path.read_text(encoding="utf-8"))
        if not (
            path.is_file()
            and sha256_file(path) == binding["sha256"]
            and binding["name"] == name
            and config.get("fold") == fold
            and config.get("seed") == 0
            and config.get("training", {}).get("epochs") == 50
            and config.get("training", {}).get("optimizer_steps_expected") == 1900
            and config.get("training", {}).get("checkpoint_policy")
            == "final_epoch_only"
            and config.get("boundaries", {}).get("D4A_training_authorized")
            is True
            and config.get("boundaries", {}).get("T0_training_authorized")
            is False
            and config.get("boundaries", {}).get("T1_training_authorized")
            is False
            and config.get("boundaries", {}).get("T2_training_authorized")
            is False
            and config.get("boundaries", {}).get("selection_started") is False
            and config.get("boundaries", {}).get("protected_data_accessed")
            is False
        ):
            raise RuntimeError(f"Unsafe D4-A runtime config: fold {fold}")
    print("[ok] D4-A authorization, four runtime configs, and implementation match")
    print("[authorized] D4-A head-only seed-0 folds A-D only")
    print("[locked] T0=false T1=false T2=false selection=false protected=false")


if __name__ == "__main__":
    main()
