#!/usr/bin/env python3
"""Verify D5-A V0/V1 seed-0 runtime configs and authorization receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "mamba-v15-d5a-seed0-training-authorization-v1"
FOLDS = ("A", "B", "C", "D")
CANDIDATES = ("V0", "V1")
ORDER = tuple(f"{candidate}_{fold}" for candidate in CANDIDATES for fold in FOLDS)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path) -> str:
    manifest = root / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Authorization artifact mismatch: {path}")
    return sha256_file(manifest)


def verify_authorization(config_dir: Path, auth_dir: Path) -> dict[str, Any]:
    config_dir = config_dir.resolve()
    auth_dir = auth_dir.resolve()
    verify_manifest(auth_dir)
    receipt_path = auth_dir / "d5a_seed0_training_authorization_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    sidecar = Path(str(receipt_path) + ".sha256")
    expected, name = sidecar.read_text(encoding="ascii").split()[:2]
    if Path(name).name != receipt_path.name or sha256_file(receipt_path) != expected:
        raise RuntimeError("D5-A authorization receipt sidecar mismatch")
    if not (
        receipt.get("authorization_version") == VERSION
        and receipt.get("status") == "D5A_V0_V1_seed0_folds_A_D_training_authorized"
        and receipt.get("candidates") == list(CANDIDATES)
        and receipt.get("training_order") == list(ORDER)
        and receipt.get("epochs") == 50
        and receipt.get("batch_size") == 8
        and receipt.get("optimizer_steps_per_candidate_fold") == 1900
        and receipt.get("maximum_optimizer_steps_total") == 15200
        and receipt.get("D5A_seed0_training_authorized") is True
        and all(
            receipt.get(key) is False
            for key in (
                "D5A_seed1_training_authorized",
                "development_all_training_authorized",
                "proposal_confirmation_access_authorized",
                "D5B_implementation_authorized",
                "D5B_training_authorized",
                "D5_candidate_selection_authorized",
                "completion_holdout_access_authorized",
                "official_test_access_authorized",
                "training_started",
                "selection_started",
                "protected_or_sealed_data_accessed",
            )
        )
    ):
        raise RuntimeError("D5-A authorization receipt semantics are invalid")

    for relative, expected_hash in receipt["implementation_sha256"].items():
        path = REPO_ROOT / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise RuntimeError(f"Authorized implementation drift: {relative}")

    runtime_lines = (auth_dir / "runtime_configs.sha256").read_text(
        encoding="ascii"
    ).splitlines()
    if len(runtime_lines) != 8:
        raise RuntimeError("Expected eight authorized runtime configs")
    for candidate in CANDIDATES:
        for fold in FOLDS:
            key = f"{candidate}_{fold}"
            name = f"MambaV15D5A_{candidate}_fold{fold}_seed0.json"
            path = config_dir / name
            binding = receipt["folds"][key]["runtime_config"]
            if not path.is_file():
                raise RuntimeError(f"Missing D5-A runtime config: {name}")
            config = json.loads(path.read_text(encoding="utf-8"))
            boundaries = config.get("boundaries", {})
            expected_dim = 13 if candidate == "V0" else 27
            expected_selector = (
                "top8_plus_conditioned_FPS24_over_top256"
                if candidate == "V0"
                else "stable_score_top32"
            )
            if not (
                sha256_file(path) == binding["sha256"]
                and binding["name"] == name
                and config.get("candidate") == candidate
                and config.get("eligibility_candidate") is (candidate == "V1")
                and config.get("fold") == fold
                and config.get("seed") == 0
                and config.get("descriptor", {}).get("dimensions") == expected_dim
                and config.get("selector", {}).get("algorithm") == expected_selector
                and config.get("selector", {}).get("selected_count") == 32
                and config.get("training", {}).get("epochs") == 50
                and config.get("training", {}).get("optimizer_steps_expected") == 1900
                and config.get("training", {}).get("checkpoint_policy")
                == "final_epoch_only"
                and boundaries.get("D5A_seed0_training_authorized") is True
                and boundaries.get("D5A_seed1_training_authorized") is False
                and boundaries.get("proposal_confirmation_access_authorized") is False
                and boundaries.get("D5B_training_authorized") is False
                and boundaries.get("D5_candidate_selection_authorized") is False
                and boundaries.get("protected_or_sealed_data_accessed") is False
            ):
                raise RuntimeError(f"Unsafe D5-A runtime config: {key}")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    args = parser.parse_args()
    verify_authorization(args.config_dir, args.authorization_dir)
    print("[ok] D5-A authorization, eight runtime configs, and implementation match")
    print("[authorized] V0/V1 seed-0 folds A-D only")
    print("[locked] seed1=false confirmation=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
