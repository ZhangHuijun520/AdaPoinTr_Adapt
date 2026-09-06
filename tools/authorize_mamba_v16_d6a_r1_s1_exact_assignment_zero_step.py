#!/usr/bin/env python3
"""Authorize isolated S1 implementation and one artificial equivalence zero-step."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/mamba_v16_d6a_r1_s1_exact_assignment_implementation_zero_step_authorization_protocol_v1.json"
REPORT = ROOT / "docs/mamba_v16_d6a_r1_s1_exact_assignment_implementation_zero_step_authorization_preregistered_protocol_zh.md"
VERSION = "mamba-v16-d6a-r1-s1-exact-assignment-implementation-zero-step-authorization-v1"
EXPECTED_LOCK = {
    "manifest": "4619426357e19f7f3673d2f6d793342eb1c42ecb32d62c49d228507d0beb8eff",
    "protocol": "faededb5862c940d5198420199a7ded4de7b3d7f20aecd72212e341f539714cc",
    "contract": "7032309e1a9103464103b5ee9530a66c45cc08422425afef137a1beba965b2a2",
    "receipt": "a76d894734219c538082fec1b38c5e2bd5fa232ad57cd84805f9d3036ce283f0",
    "suite": "d9c657af5e25be00333fccaa0a992946129391d1fa1f910b9fc0fb4131b2f7fc",
}
EXPECTED_R1 = "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def manifest_bytes(files: Mapping[str, bytes]) -> bytes:
    return "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())
    ).encode("ascii")


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    parent = protocol["frozen_parent"]
    implementation = protocol["implementation_contract"]
    zero = protocol["artificial_zero_step"]
    result = protocol["result_contract"]
    permission = protocol["permission_boundary"]
    if not (
        protocol["protocol_id"] == VERSION
        and protocol["status"] == "preregistered_after_frozen_optimization_feasibility_protocol_before_S1_execution"
        and parent["protocol_lock_manifest_sha256"] == EXPECTED_LOCK["manifest"]
        and parent["protocol_sha256"] == EXPECTED_LOCK["protocol"]
        and parent["contract_sha256"] == EXPECTED_LOCK["contract"]
        and parent["receipt_sha256"] == EXPECTED_LOCK["receipt"]
        and parent["suite_sha256"] == EXPECTED_LOCK["suite"]
        and implementation["production_R1_file_must_remain_sha256"] == EXPECTED_R1
        and implementation["input_shape"] == [1, 32, 8192]
        and implementation["row_top_k"] == 32
        and implementation["cutoff_ties"] == "include_all"
        and implementation["union_order"] == "ascending_original_candidate_index"
        and implementation["full_D2H_retained"] is True
        and implementation["fallback_to_S0"] is False
        and implementation["approximate_or_greedy_selection_allowed"] is False
        and zero["families"] == 7
        and zero["cases"] == 168
        and zero["S0_assignments"] == 168
        and zero["S1_assignments"] == 168
        and zero["slot_to_candidate_exact_required"] == "168/168"
        and zero["performance_timing_calls"] == 0
        and zero["warmup_runs"] == 0
        and zero["timed_runs"] == 0
        and zero["torch_profiler_traces"] == 0
        and zero["optimizer_steps"] == 0
        and zero["model_updates"] == 0
        and zero["D6_cases_accessed"] == 0
        and result["negative_status"] == "D6A_R1_S1_exact_assignment_artificial_zero_step_equivalence_failed"
        and result["all_168_cases_must_run_before_final_classification"] is True
        and result["all_168_cases_must_pass_before_success_classification"] is True
        and result["negative_result_freeze_required_on_any_failure"] is True
        and result["result_can_authorize_artificial_benchmark"] is False
        and result["result_can_authorize_production_change"] is False
        and result["result_can_authorize_formal_rerun"] is False
        and result["result_can_authorize_training"] is False
        and permission["S1_isolated_implementation_authorized"] is True
        and permission["S1_artificial_zero_step_authorized"] is True
        and permission["S1_artificial_performance_benchmark_authorized"] is False
        and permission["S2_implementation_authorized"] is False
        and permission["R1_production_implementation_change_authorized"] is False
        and permission["formal_efficiency_rerun_authorized"] is False
        and permission["seed0_training_authorized"] is False
        and permission["seed1_training_authorized"] is False
        and permission["D6B_authorized"] is False
        and permission["protected_or_sealed_data_accessed"] is False
    ):
        raise RuntimeError("D6-A R1 S1 zero-step authorization protocol drifted")


def verify_parent_lock(lock_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    expected_files = {
        "files.sha256": EXPECTED_LOCK["manifest"],
        "optimization_feasibility_protocol_v1.json": EXPECTED_LOCK["protocol"],
        "optimization_contract.json": EXPECTED_LOCK["contract"],
        "protocol_lock_receipt.json": EXPECTED_LOCK["receipt"],
        "synthetic_equivalence_suite.json": EXPECTED_LOCK["suite"],
    }
    for name, expected in expected_files.items():
        path = lock_dir / name
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"Frozen S1 feasibility parent drifted: {path}")
    for line in (lock_dir / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = lock_dir / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen S1 feasibility manifest member drifted: {path}")
    receipt = json.loads((lock_dir / "protocol_lock_receipt.json").read_text(encoding="utf-8"))
    suite = json.loads((lock_dir / "synthetic_equivalence_suite.json").read_text(encoding="utf-8"))
    if not (
        receipt["status"] == "D6A_R1_exact_assignment_optimization_feasibility_protocol_frozen_non_runnable"
        and receipt["equivalence_cases"] == 168
        and receipt["S1_implementation_authorized"] is False
        and receipt["S1_zero_step_authorized"] is False
        and receipt["S1_benchmark_authorized"] is False
        and receipt["formal_efficiency_rerun_authorized"] is False
        and receipt["optimizer_steps"] == 0
        and receipt["D6_cases_accessed"] == 0
        and suite["total_cases"] == 168
        and len(suite["families"]) == 7
        and suite["post_result_case_search_forbidden"] is True
    ):
        raise RuntimeError("Frozen S1 feasibility parent permission boundary drifted")
    return receipt, suite


def implementation_hashes() -> dict[str, str]:
    paths = {
        "production_R1": ROOT / "utils/mamba_d6a_slot_allocator.py",
        "S1_shadow": ROOT / "utils/mamba_d6a_r1_s1_exact_assignment.py",
        "authorize": Path(__file__).resolve(),
        "verify": ROOT / "tools/verify_mamba_v16_d6a_r1_s1_exact_assignment_zero_step_authorization.py",
        "preflight": ROOT / "tools/preflight_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py",
        "tests": ROOT / "tools/test_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py",
    }
    hashes = {}
    for name, path in paths.items():
        if not path.is_file():
            raise RuntimeError(f"Missing S1 zero-step implementation: {path}")
        hashes[name] = sha256_file(path)
    if hashes["production_R1"] != EXPECTED_R1:
        raise RuntimeError("Frozen production R1 implementation drifted")
    return hashes


def write_exact(root: Path, files: Mapping[str, bytes]) -> None:
    if root.exists():
        existing = {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }
        if existing != dict(files):
            raise RuntimeError(f"Refusing non-identical S1 authorization: {root}")
        print(f"[locked] existing S1 zero-step authorization is byte-identical: {root}")
        return
    root.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{root.name}.", dir=root.parent))
    try:
        for name, payload in files.items():
            path = working / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        working.replace(root)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol_lock_dir", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    parent_receipt, suite = verify_parent_lock(args.protocol_lock_dir.resolve())
    hashes = implementation_hashes()
    config_name = "MambaV16D6A_R1_S1_exact_assignment_artificial_zero_step_v1.json"
    config = {
        "authorization_version": VERSION,
        "status": "D6A_R1_S1_exact_assignment_artificial_zero_step_authorized_not_started",
        "synthetic_equivalence_suite": suite,
        "implementation_contract": protocol["implementation_contract"],
        "zero_step_contract": protocol["artificial_zero_step"],
        "result_contract": protocol["result_contract"],
        "permission_boundary": protocol["permission_boundary"],
    }
    config_payload = canonical_json(config)
    config_files = {config_name: config_payload}

    receipt = {
        "authorization_version": VERSION,
        "status": "D6A_R1_S1_exact_assignment_implementation_zero_step_authorized",
        "runtime_config": {"name": config_name, "sha256": sha256_bytes(config_payload)},
        "parent_lock_sha256": dict(EXPECTED_LOCK),
        "parent_status": parent_receipt["status"],
        "authorization_protocol_sha256": sha256_file(PROTOCOL),
        "authorization_report_sha256": sha256_file(REPORT),
        "implementation_sha256": hashes,
        "S1_isolated_implementation_authorized": True,
        "S1_artificial_zero_step_authorized": True,
        "S1_artificial_performance_benchmark_authorized": False,
        "execution_started": False,
        "equivalence_cases_completed": 0,
        "performance_timing_calls": 0,
        "warmup_runs": 0,
        "timed_runs": 0,
        "torch_profiler_traces": 0,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "R1_production_implementation_change_authorized": False,
        "formal_efficiency_rerun_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "run_one_separate_168_case_artificial_CUDA_zero_step",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "s1_zero_step_execution_authorization_receipt.json"
    authorization_files = {
        receipt_name: receipt_payload,
        f"{receipt_name}.sha256": f"{sha256_bytes(receipt_payload)}  {receipt_name}\n".encode("ascii"),
        "runtime_config.sha256": manifest_bytes(config_files),
        "execution_authorization_protocol_v1.json": canonical_json(protocol),
        "execution_authorization_report_zh.md": REPORT.read_bytes(),
    }
    authorization_files["files.sha256"] = manifest_bytes(authorization_files)
    write_exact(args.config_output_dir.resolve(), config_files)
    write_exact(args.authorization_output_dir.resolve(), authorization_files)
    print("[authorized] isolated S1 implementation and one 168-case artificial CUDA zero-step")
    print("[locked] benchmark=false production=false formal_rerun=false training=false D6=false")


if __name__ == "__main__":
    main()
