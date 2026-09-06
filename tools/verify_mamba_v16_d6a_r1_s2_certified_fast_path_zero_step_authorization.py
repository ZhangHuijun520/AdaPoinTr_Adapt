#!/usr/bin/env python3
"""Verify frozen S2 shadow implementation and zero-step authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_R1 = "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43"
EXPECTED_S1 = "e0583751a397dfb718e47bf681437dc4265c52b8b066f28a73dc65f169e65e73"
EXPECTED_PARENT_MANIFEST = "abc72d3d05637d1a19d028425a693d775728843447ea16301c2b1484dbd67494"
VERSION = "mamba-v16-d6a-r1-s2-certified-fast-path-implementation-zero-step-authorization-v1"


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
        wanted, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != wanted.lower():
            raise RuntimeError(f"S2 authorization artifact drifted: {path}")


def verify_authorization(config_dir: Path, authorization_dir: Path) -> dict[str, Any]:
    config_dir = config_dir.resolve()
    authorization_dir = authorization_dir.resolve()
    verify_manifest(authorization_dir)
    receipt_path = authorization_dir / "s2_zero_step_execution_authorization_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    valid = (
        receipt["authorization_version"] == VERSION
        and receipt["status"] == "D6A_R1_S2_certified_fast_path_implementation_zero_step_authorized"
        and receipt["parent_lock_sha256"]["manifest"] == EXPECTED_PARENT_MANIFEST
        and receipt["S2_isolated_shadow_implementation_authorized"] is True
        and receipt["S2_artificial_zero_step_authorized"] is True
        and receipt["S2_artificial_performance_benchmark_authorized"] is False
        and receipt["execution_started"] is False
        and receipt["equivalence_cases_completed"] == 0
        and receipt["certified_fast_path_cases_completed"] == 0
        and receipt["fallback_cases_completed"] == 0
        and receipt["performance_timing_calls"] == receipt["warmup_runs"] == receipt["timed_runs"] == 0
        and receipt["torch_profiler_traces"] == receipt["optimizer_steps"] == receipt["model_updates"] == 0
        and receipt["D6_cases_accessed"] == 0
        and receipt["S1_rerun_authorized"] is False
        and receipt["R1_production_implementation_change_authorized"] is False
        and receipt["formal_efficiency_rerun_authorized"] is False
        and receipt["seed0_training_authorized"] is False
        and receipt["seed1_training_authorized"] is False
        and receipt["D6B_authorized"] is False
        and receipt["protected_or_sealed_data_accessed"] is False
    )
    if not valid:
        raise RuntimeError("S2 zero-step authorization permission boundary drifted")

    config_meta = receipt["runtime_config"]
    config_path = config_dir / config_meta["name"]
    if not config_path.is_file() or sha256_file(config_path) != config_meta["sha256"]:
        raise RuntimeError("S2 zero-step runtime config drifted")
    manifest_hash, manifest_name = (
        authorization_dir / "runtime_config.sha256"
    ).read_text(encoding="ascii").strip().split(maxsplit=1)
    if manifest_name.lstrip("*") != config_meta["name"] or manifest_hash != config_meta["sha256"]:
        raise RuntimeError("S2 runtime-config manifest drifted")

    paths = {
        "production_R1": ROOT / "utils/mamba_d6a_slot_allocator.py",
        "S1_shadow": ROOT / "utils/mamba_d6a_r1_s1_exact_assignment.py",
        "S2_shadow": ROOT / "utils/mamba_d6a_r1_s2_certified_fast_path.py",
        "authorize": ROOT / "tools/authorize_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py",
        "verify": Path(__file__).resolve(),
        "preflight": ROOT / "tools/preflight_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py",
        "tests": ROOT / "tools/test_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py",
    }
    for name, path in paths.items():
        if not path.is_file() or sha256_file(path) != receipt["implementation_sha256"][name]:
            raise RuntimeError(f"S2 authorized implementation drifted: {path}")
    if receipt["implementation_sha256"]["production_R1"] != EXPECTED_R1:
        raise RuntimeError("Frozen production R1 changed")
    if receipt["implementation_sha256"]["S1_shadow"] != EXPECTED_S1:
        raise RuntimeError("Frozen S1 shadow changed")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not (
        config["status"] == "D6A_R1_S2_certified_fast_path_artificial_zero_step_authorized_not_started"
        and config["synthetic_equivalence_suite"]["total_cases"] == 168
        and len(config["synthetic_equivalence_suite"]["families"]) == 7
        and config["zero_step_contract"]["performance_timing_calls"] == 0
        and config["permission_boundary"]["S2_artificial_performance_benchmark_authorized"] is False
    ):
        raise RuntimeError("S2 authorized runtime-config semantics drifted")
    return receipt


__all__ = ["verify_authorization"]
