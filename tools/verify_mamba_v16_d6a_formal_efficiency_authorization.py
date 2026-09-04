#!/usr/bin/env python3
"""Verify D6-A formal-efficiency runtime config and authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VERSION = "mamba-v16-d6a-formal-efficiency-execution-authorization-v1"
CONFIG_NAME = "MambaV16D6A_R0_R1_formal_efficiency_seed160610.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path) -> None:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing authorization manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Authorization artifact mismatch: {path}")


def verify_authorization(config_dir: Path, auth_dir: Path) -> dict[str, Any]:
    config_dir = config_dir.resolve()
    auth_dir = auth_dir.resolve()
    verify_manifest(auth_dir)
    receipt_path = auth_dir / "formal_efficiency_execution_authorization_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    sidecar = Path(str(receipt_path) + ".sha256")
    expected, name = sidecar.read_text(encoding="ascii").split()[:2]
    if Path(name).name != receipt_path.name or sha256_file(receipt_path) != expected:
        raise RuntimeError("Authorization receipt sidecar mismatch")
    if not (
        receipt.get("authorization_version") == VERSION
        and receipt.get("status") == "D6A_R0_R1_formal_efficiency_execution_authorized"
        and receipt.get("formal_efficiency_execution_authorized") is True
        and receipt.get("execution_started") is False
        and receipt.get("formal_warmup_runs_completed") == 0
        and receipt.get("formal_timed_runs_completed") == 0
        and receipt.get("latency_gate_evaluated") is False
        and receipt.get("peak_memory_gate_evaluated") is False
        and receipt.get("optimizer_constructed") is False
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("D6_cases_accessed") == 0
        and all(receipt.get(key) is False for key in (
            "seed0_training_authorized", "seed1_training_authorized",
            "proposal_confirmation_authorized", "D6B_authorized",
            "candidate_selection_authorized", "protected_or_sealed_data_accessed",
        ))
    ):
        raise RuntimeError("Unsafe formal-efficiency authorization semantics")
    for relative, expected_hash in receipt["implementation_sha256"].items():
        mapping = {
            "R0": "utils/mamba_d5a_proposal.py",
            "R1": "utils/mamba_d6a_slot_allocator.py",
            "efficiency": "utils/mamba_d6a_efficiency.py",
            "authorize": "tools/authorize_mamba_v16_d6a_formal_efficiency_execution.py",
            "verify": "tools/verify_mamba_v16_d6a_formal_efficiency_authorization.py",
            "preflight": "tools/preflight_mamba_v16_d6a_formal_efficiency_execution.py",
            "execute": "tools/run_mamba_v16_d6a_formal_efficiency.py",
            "tests": "tools/test_mamba_v16_d6a_formal_efficiency_execution_contract.py",
        }
        path = ROOT / mapping[relative]
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise RuntimeError(f"Authorized implementation drift: {path}")

    config_path = config_dir / CONFIG_NAME
    expected_config = receipt["runtime_config"]
    if not config_path.is_file() or sha256_file(config_path) != expected_config["sha256"]:
        raise RuntimeError("Formal-efficiency runtime config drifted")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    boundary = config.get("boundaries", {})
    if not (
        config.get("authorization_version") == VERSION
        and config.get("status") == "D6A_R0_R1_formal_efficiency_execution_authorized_not_started"
        and config.get("candidate_order") == ["R0", "R1"]
        and config.get("descriptor_seed") == 160610
        and config.get("descriptor_shape") == [1, 8192, 27]
        and config.get("dtype") == "float32"
        and config.get("model_residency") == "one_candidate_at_a_time_with_prior_candidate_deleted"
        and config.get("warmup_runs_per_candidate") == 10
        and config.get("timed_runs_per_candidate") == 50
        and config.get("latency_ratio_maximum") == 1.15
        and config.get("peak_memory_ratio_maximum") == 1.10
        and boundary.get("formal_efficiency_execution_authorized") is True
        and boundary.get("seed0_training_authorized") is False
        and boundary.get("seed1_training_authorized") is False
        and boundary.get("D6B_authorized") is False
        and boundary.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Unsafe formal-efficiency runtime config")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    args = parser.parse_args()
    verify_authorization(args.config_dir, args.authorization_dir)
    print("[ok] D6-A formal-efficiency authorization and runtime config match")
    print("[authorized] R0 then R1 artificial full-inference benchmark only")
    print("[locked] execution not started; training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
