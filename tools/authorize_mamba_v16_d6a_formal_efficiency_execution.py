#!/usr/bin/env python3
"""Issue the frozen D6-A formal-efficiency execution authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/mamba_v16_d6a_formal_efficiency_execution_authorization_protocol_v1.json"
REPORT = ROOT / "docs/mamba_v16_d6a_formal_efficiency_execution_authorization_preregistered_protocol_zh.md"
VERSION = "mamba-v16-d6a-formal-efficiency-execution-authorization-v1"
EXPECTED = {
    "candidate_manifest": "79aad71cc9da046b1e87fbe102ec0c454a0118890b3f93dd00fe2bc82c2d1285",
    "candidate_receipt": "372fb304305e85e6cf0c63ea08b5c7f62ee2a026492daf34f6d045ee957c71bf",
    "candidate_protocol": "5060c7700e53d42a4100ebeacf35f662accd58c585fc82af1443fafffb17fc3e",
    "zero_manifest": "4e85572b1dd6cd044d6ce199623ab2583326a0c6916b4d3c01cdc641acb5f6b4",
    "zero_receipt": "60644275e58407e3b6b4e13abad2ef6c1490984ba31b782678f6963aded7408c",
    "zero_result_report": "ad015c313989f223330bd57e43f43276469fa06cce4228fa50d66b496ef9662a",
    "R0": "6cca9c11f302da3ca202f3e33547c62e4584eeb0fd81f9e96c20f2787e04f070",
    "R1": "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43",
    "efficiency": "7a42c8fafe09ba3a98a052dd002137b4a9ab3d71ef630585cc85a269dfd8428b",
}


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


def verify_manifest(root: Path, expected_hash: str) -> None:
    manifest = root / "files.sha256"
    if not manifest.is_file() or sha256_file(manifest) != expected_hash:
        raise RuntimeError(f"Frozen manifest drifted: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    scope = protocol.get("scope", {})
    benchmark = protocol.get("benchmark", {})
    preflight = protocol.get("authorization_preflight", {})
    boundary = protocol.get("permission_boundary", {})
    if not (
        protocol.get("protocol_id") == VERSION
        and protocol.get("status") == "preregistered_after_artificial_zero_step_before_formal_efficiency_execution"
        and scope.get("candidates") == ["R0", "R1"]
        and scope.get("candidate_order") == ["R0", "R1"]
        and scope.get("formal_efficiency_execution_authorized") is True
        and scope.get("completed_execution_rerun_authorized") is False
        and benchmark.get("descriptor_seed") == 160610
        and benchmark.get("descriptor_shape") == [1, 8192, 27]
        and benchmark.get("descriptor_dtype") == "float32"
        and benchmark.get("model_residency") == "one_candidate_at_a_time_with_prior_candidate_deleted"
        and benchmark.get("warmup_runs_per_candidate") == 10
        and benchmark.get("timed_runs_per_candidate") == 50
        and benchmark.get("R1_to_R0_latency_ratio_maximum") == 1.15
        and benchmark.get("R1_to_R0_peak_memory_ratio_maximum") == 1.10
        and preflight.get("formal_warmup_runs") == 0
        and preflight.get("formal_timed_runs") == 0
        and preflight.get("optimizer_steps") == 0
        and boundary.get("seed0_training_authorized") is False
        and boundary.get("seed1_training_authorized") is False
        and boundary.get("D6B_authorized") is False
        and boundary.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("D6-A formal-efficiency authorization protocol drifted")


def implementation_hashes() -> dict[str, str]:
    paths = {
        "R0": ROOT / "utils/mamba_d5a_proposal.py",
        "R1": ROOT / "utils/mamba_d6a_slot_allocator.py",
        "efficiency": ROOT / "utils/mamba_d6a_efficiency.py",
        "authorize": Path(__file__).resolve(),
        "verify": ROOT / "tools/verify_mamba_v16_d6a_formal_efficiency_authorization.py",
        "preflight": ROOT / "tools/preflight_mamba_v16_d6a_formal_efficiency_execution.py",
        "execute": ROOT / "tools/run_mamba_v16_d6a_formal_efficiency.py",
        "tests": ROOT / "tools/test_mamba_v16_d6a_formal_efficiency_execution_contract.py",
    }
    hashes = {}
    for name, path in paths.items():
        if not path.is_file():
            raise RuntimeError(f"Missing formal-efficiency implementation: {path}")
        hashes[name] = sha256_file(path)
    for name in ("R0", "R1", "efficiency"):
        if hashes[name] != EXPECTED[name]:
            raise RuntimeError(f"Frozen {name} implementation drifted")
    return hashes


def write_exact(root: Path, files: Mapping[str, bytes]) -> None:
    if root.exists():
        existing = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
        mismatches = [
            name for name, payload in files.items()
            if not (root / name).is_file() or (root / name).read_bytes() != payload
        ]
        if existing != set(files) or mismatches:
            raise RuntimeError(f"Refusing non-identical authorization: {mismatches}")
        print(f"[locked] existing authorization is byte-identical: {root}")
        return
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def manifest_bytes(files: Mapping[str, bytes]) -> bytes:
    return "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())
    ).encode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_lock_dir", type=Path, required=True)
    parser.add_argument("--zero_step_dir", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    candidate = args.candidate_lock_dir.resolve()
    zero = args.zero_step_dir.resolve()
    verify_manifest(candidate, EXPECTED["candidate_manifest"])
    verify_manifest(zero, EXPECTED["zero_manifest"])

    candidate_receipt_path = candidate / "protocol_lock_receipt.json"
    candidate_protocol_path = candidate / "candidate_training_efficiency_protocol_v1.json"
    zero_receipt_path = zero / "efficiency_zero_step_receipt.json"
    candidate_receipt = json.loads(candidate_receipt_path.read_text(encoding="utf-8"))
    zero_receipt = json.loads(zero_receipt_path.read_text(encoding="utf-8"))
    if not (
        sha256_file(candidate_receipt_path) == EXPECTED["candidate_receipt"]
        and sha256_file(candidate_protocol_path) == EXPECTED["candidate_protocol"]
        and candidate_receipt.get("status") == "D6A_candidate_training_efficiency_protocol_frozen_non_runnable"
        and candidate_receipt.get("efficiency_execution_authorized") is False
        and candidate_receipt.get("seed0_training_authorized") is False
    ):
        raise RuntimeError("Candidate protocol lock does not authorize this transition")
    if not (
        sha256_file(zero_receipt_path) == EXPECTED["zero_receipt"]
        and zero_receipt.get("status") == "D6A_R0_R1_full_inference_efficiency_artificial_zero_step_passed"
        and zero_receipt.get("formal_efficiency_execution_authorized") is False
        and zero_receipt.get("separate_formal_efficiency_execution_authorization_allowed_next") is True
        and zero_receipt.get("formal_warmup_runs") == 0
        and zero_receipt.get("formal_timed_runs") == 0
        and zero_receipt.get("state_hash_before") == zero_receipt.get("state_hash_after")
        and zero_receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Artificial zero-step does not authorize this transition")
    result_report = ROOT / "docs/mamba_v16_d6a_efficiency_implementation_zero_step_complete_result_zh.md"
    if sha256_file(result_report) != EXPECTED["zero_result_report"]:
        raise RuntimeError("D6-A efficiency zero-step complete result drifted")

    config = {
        "authorization_version": VERSION,
        "status": "D6A_R0_R1_formal_efficiency_execution_authorized_not_started",
        "candidate_order": ["R0", "R1"],
        "descriptor_seed": 160610,
        "descriptor_shape": [1, 8192, 27],
        "dtype": "float32",
        "device": "CUDA_required",
        "model_initialization": "torch_manual_seed_160610_once_then_construct_R0_then_R1",
        "model_residency": "one_candidate_at_a_time_with_prior_candidate_deleted",
        "warmup_runs_per_candidate": 10,
        "timed_runs_per_candidate": 50,
        "latency_statistic": "median",
        "latency_ratio_maximum": 1.15,
        "peak_memory_ratio_maximum": 1.10,
        "expected_initial_state_sha256": zero_receipt["state_hash_before"],
        "boundaries": {
            "formal_efficiency_execution_authorized": True,
            "seed0_training_authorized": False,
            "seed1_training_authorized": False,
            "proposal_confirmation_authorized": False,
            "D6B_authorized": False,
            "candidate_selection_authorized": False,
            "protected_or_sealed_data_accessed": False,
        },
    }
    config_name = "MambaV16D6A_R0_R1_formal_efficiency_seed160610.json"
    config_payload = canonical_json(config)
    configs = {config_name: config_payload}
    write_exact(args.config_output_dir.resolve(), configs)

    receipt = {
        "authorization_version": VERSION,
        "status": "D6A_R0_R1_formal_efficiency_execution_authorized",
        "runtime_config": {"name": config_name, "sha256": sha256_bytes(config_payload)},
        "lineage_sha256": {
            "candidate_lock_manifest": EXPECTED["candidate_manifest"],
            "candidate_lock_receipt": EXPECTED["candidate_receipt"],
            "zero_step_manifest": EXPECTED["zero_manifest"],
            "zero_step_receipt": EXPECTED["zero_receipt"],
            "zero_step_complete_result": EXPECTED["zero_result_report"],
            "authorization_protocol": sha256_file(PROTOCOL),
            "authorization_report": sha256_file(REPORT),
        },
        "implementation_sha256": implementation_hashes(),
        "formal_efficiency_execution_authorized": True,
        "execution_started": False,
        "formal_warmup_runs_completed": 0,
        "formal_timed_runs_completed": 0,
        "latency_gate_evaluated": False,
        "peak_memory_gate_evaluated": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_artificial_CUDA_authorization_preflight",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "formal_efficiency_execution_authorization_receipt.json"
    files = {
        receipt_name: receipt_payload,
        f"{receipt_name}.sha256": f"{sha256_bytes(receipt_payload)}  {receipt_name}\n".encode("ascii"),
        "runtime_config.sha256": manifest_bytes(configs),
        "execution_authorization_protocol_v1.json": canonical_json(protocol),
        "execution_authorization_report_zh.md": REPORT.read_bytes(),
    }
    files["files.sha256"] = manifest_bytes(files)
    write_exact(args.authorization_output_dir.resolve(), files)
    print("[authorized] D6-A R0/R1 formal efficiency execution only")
    print("[locked] execution not started; training=false seed1=false D6B=false sealed=false")
    print("[next] run separate artificial CUDA authorization preflight")


if __name__ == "__main__":
    main()
