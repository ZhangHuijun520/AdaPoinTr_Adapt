#!/usr/bin/env python3
"""Verify the D6-A R1 latency profiling runtime config and authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VERSION = "mamba-v16-d6a-r1-latency-posthoc-profiling-execution-authorization-v1"
CONFIG_NAME = "MambaV16D6A_R1_latency_posthoc_profiling_seed160610.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path) -> None:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing profiling authorization manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Profiling authorization artifact mismatch: {path}")


def verify_authorization(config_dir: Path, auth_dir: Path) -> dict[str, Any]:
    config_dir = config_dir.resolve()
    auth_dir = auth_dir.resolve()
    verify_manifest(auth_dir)
    receipt_path = auth_dir / "profiling_execution_authorization_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected, name = Path(str(receipt_path) + ".sha256").read_text(encoding="ascii").split()[:2]
    if Path(name).name != receipt_path.name or sha256_file(receipt_path) != expected:
        raise RuntimeError("Profiling authorization receipt sidecar mismatch")
    if not (
        receipt.get("authorization_version") == VERSION
        and receipt.get("status") == "D6A_R1_latency_posthoc_profiling_execution_authorized"
        and receipt.get("posthoc_profiling_execution_authorized") is True
        and receipt.get("execution_started") is False
        and receipt.get("profiling_blocks_completed") == 0
        and receipt.get("timed_observations_completed") == 0
        and receipt.get("torch_profiler_traces_completed") == 0
        and receipt.get("formal_gate_changed") is False
        and receipt.get("formal_gate_rerun") is False
        and receipt.get("optimizer_constructed") is False
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("D6_cases_accessed") == 0
        and all(
            receipt.get(key) is False
            for key in (
                "R1_implementation_change_authorized",
                "optimized_alternative_benchmark_authorized",
                "R2_implementation_authorized",
                "seed0_training_authorized",
                "seed1_training_authorized",
                "proposal_confirmation_authorized",
                "D6B_authorized",
                "candidate_selection_authorized",
                "protected_or_sealed_data_accessed",
            )
        )
    ):
        raise RuntimeError("Unsafe R1 profiling execution authorization semantics")

    mapping = {
        "R1": "utils/mamba_d6a_slot_allocator.py",
        "efficiency": "utils/mamba_d6a_efficiency.py",
        "profiler": "utils/mamba_d6a_r1_latency_profiler.py",
        "authorize": "tools/authorize_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py",
        "verify": "tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_authorization.py",
        "preflight": "tools/preflight_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py",
        "execute": "tools/run_mamba_v16_d6a_r1_latency_posthoc_profiling.py",
        "tests": "tools/test_mamba_v16_d6a_r1_latency_posthoc_profiling_execution_contract.py",
    }
    for name_key, expected_hash in receipt["implementation_sha256"].items():
        path = ROOT / mapping[name_key]
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise RuntimeError(f"Authorized profiling implementation drift: {path}")

    config_path = config_dir / CONFIG_NAME
    expected_config = receipt["runtime_config"]
    if not config_path.is_file() or sha256_file(config_path) != expected_config["sha256"]:
        raise RuntimeError("R1 profiling runtime config drifted")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    boundaries = config.get("boundaries", {})
    if not (
        config.get("authorization_version") == VERSION
        and config.get("status") == "D6A_R1_latency_posthoc_profiling_execution_authorized_not_started"
        and config.get("candidate") == "R1"
        and config.get("candidate_order") == ["R1"]
        and config.get("descriptor_seed") == 160610
        and config.get("descriptor_shape") == [1, 8192, 27]
        and config.get("blocks") == 3
        and config.get("warmup_runs_per_block") == 5
        and config.get("timed_runs_per_block") == 20
        and config.get("total_timed_observations") == 60
        and config.get("completed_execution_rerun_authorized") is False
        and config.get("formal_result_status") == "D6A_formal_efficiency_gate_failed"
        and config.get("frozen_R1_latency_ms_median") == 292.5087884068489
        and boundaries.get("posthoc_profiling_execution_authorized") is True
        and boundaries.get("execution_started") is False
        and boundaries.get("seed0_training_authorized") is False
        and boundaries.get("seed1_training_authorized") is False
        and boundaries.get("D6B_authorized") is False
        and boundaries.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Unsafe R1 profiling runtime config")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    args = parser.parse_args()
    verify_authorization(args.config_dir, args.authorization_dir)
    print("[ok] D6-A R1 profiling authorization and runtime config match")
    print("[authorized] one artificial-descriptor R1 profiling execution only")
    print("[locked] execution not started; training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
