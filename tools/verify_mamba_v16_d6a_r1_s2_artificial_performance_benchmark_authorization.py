#!/usr/bin/env python3
"""Verify frozen S2 artificial benchmark authorization and runtime config."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_STATUS = "D6A_R1_S2_artificial_performance_benchmark_execution_authorized"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(manifest: Path, root: Path) -> int:
    require(manifest.is_file(), f"Missing manifest: {manifest}")
    resolved = root.resolve()
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        wanted, relative = line.split(maxsplit=1)
        posix = PurePosixPath(relative.lstrip("*"))
        require(not posix.is_absolute() and ".." not in posix.parts, f"Unsafe manifest path: {relative}")
        path = root.joinpath(*posix.parts).resolve()
        require(path == resolved or resolved in path.parents, f"Manifest escaped root: {path}")
        require(path.is_file() and sha256_file(path) == wanted.lower(), f"Manifest mismatch: {path}")
        count += 1
    return count


def verify_authorization(config_dir: Path, authorization_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config_dir = config_dir.resolve()
    authorization_dir = authorization_dir.resolve()
    require(verify_manifest(authorization_dir / "files.sha256", authorization_dir) == 5, "Authorization manifest count drifted")
    receipt_path = authorization_dir / "benchmark_execution_authorization_receipt.json"
    checksum_path = authorization_dir / "benchmark_execution_authorization_receipt.json.sha256"
    require(receipt_path.is_file() and checksum_path.is_file(), "Missing authorization receipt")
    wanted_receipt = checksum_path.read_text(encoding="ascii").split()[0].lower()
    require(sha256_file(receipt_path) == wanted_receipt, "Authorization receipt checksum drifted")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    runtime = receipt["runtime_config"]
    require(verify_manifest(authorization_dir / "runtime_config.sha256", config_dir) == 1, "Runtime config manifest count drifted")
    config_path = config_dir / runtime["name"]
    require(config_path.is_file() and sha256_file(config_path) == runtime["sha256"], "Runtime config drifted")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    require(receipt["status"] == EXPECTED_STATUS, "Authorization status drifted")
    require(receipt["S2_artificial_performance_benchmark_execution_authorized"] is True, "Benchmark is not authorized")
    require(receipt["authorization_preflight_authorized"] is True and receipt["execution_started"] is False, "Authorization start state drifted")
    for key in ("correctness_replay_cases_completed", "warmup_calls_completed", "timed_calls_completed", "measurement_blocks_completed", "torch_profiler_traces", "optimizer_steps", "model_updates", "D6_cases_accessed"):
        require(receipt[key] == 0, f"Authorization zero-count boundary drifted: {key}")
    for key in ("S2_implementation_change_authorized", "R1_production_implementation_change_authorized", "formal_efficiency_rerun_authorized", "seed0_training_authorized", "seed1_training_authorized", "proposal_confirmation_authorized", "D6B_authorized", "candidate_selection_authorized", "protected_or_sealed_data_accessed"):
        require(receipt[key] is False, f"Forbidden authorization enabled: {key}")

    require(config["status"] == "D6A_R1_S2_artificial_performance_benchmark_authorized_not_started", "Runtime status drifted")
    require(len(config["cases"]) == 168 and [case["case_index"] for case in config["cases"]] == list(range(168)), "Runtime case order drifted")
    runtime_contract = config["runtime"]
    require(runtime_contract["warmup_calls_total"] == 28 and runtime_contract["timed_observation_rows"] == 1008, "Runtime counts drifted")
    require(runtime_contract["outlier_removal"] == "none" and runtime_contract["torch_profiler_traces"] == 0, "Runtime filtering/profiling drifted")

    for name, binding in receipt["implementation_sha256"].items():
        path = ROOT / binding["path"]
        require(path.is_file(), f"Missing authorized source: {path}")
        payload = path.read_bytes()
        require(sha256_bytes(payload) == binding["raw_sha256"], f"Authorized raw source drifted: {path}")
        require(sha256_bytes(payload.replace(b"\r\n", b"\n")) == binding["LF_normalized_sha256"], f"Authorized normalized source drifted: {path}")
        require(config["implementation_sha256"][name] == binding, f"Runtime source binding drifted: {name}")
    return receipt, config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    args = parser.parse_args()
    receipt, config = verify_authorization(args.config_dir, args.authorization_dir)
    print("[ok] S2 artificial benchmark authorization and runtime config match")
    print(f"[authorized] cases={len(config['cases'])} warmup={config['runtime']['warmup_calls_total']} timed={config['runtime']['timed_observation_rows']}")
    print("[locked] execution not started; production=false formal_rerun=false training=false D6=false")


if __name__ == "__main__":
    main()
