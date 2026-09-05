#!/usr/bin/env python3
"""Issue one frozen D6-A R1 latency post-hoc profiling authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/mamba_v16_d6a_r1_latency_posthoc_profiling_execution_authorization_protocol_v1.json"
REPORT = ROOT / "docs/mamba_v16_d6a_r1_latency_posthoc_profiling_execution_authorization_preregistered_protocol_zh.md"
VERSION = "mamba-v16-d6a-r1-latency-posthoc-profiling-execution-authorization-v1"
EXPECTED_LOCK = {
    "manifest": "259bc0e1dcbffda71d2a343ae090240f4a07ba40c2b2138a5cc6bb31ebc871b7",
    "protocol": "b93200400b48dc62f03c7703f3434d28fa76e3c88e4975e6562e28e340fdcea1",
    "receipt": "b074c94acb0b1e73228c030c7e8f50562d48d929f919dad5dfb6e3a35ad9af05",
}
EXPECTED_IMPLEMENTATION = {
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


def manifest_bytes(files: Mapping[str, bytes]) -> bytes:
    return "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())
    ).encode("ascii")


def verify_manifest(root: Path, expected_hash: str) -> None:
    manifest = root / "files.sha256"
    if not manifest.is_file() or sha256_file(manifest) != expected_hash:
        raise RuntimeError(f"Frozen profiling lock manifest drifted: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen profiling lock artifact drifted: {path}")


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    runtime = protocol.get("runtime", {})
    preflight = protocol.get("authorization_preflight", {})
    result = protocol.get("result_contract", {})
    boundary = protocol.get("permission_boundary", {})
    if not (
        protocol.get("protocol_id") == VERSION
        and protocol.get("status") == "preregistered_after_frozen_profiling_protocol_before_execution"
        and runtime.get("candidate") == "R1"
        and runtime.get("candidate_order") == ["R1"]
        and runtime.get("descriptor_seed") == 160610
        and runtime.get("descriptor_shape") == [1, 8192, 27]
        and runtime.get("blocks") == 3
        and runtime.get("warmup_runs_per_block") == 5
        and runtime.get("timed_runs_per_block") == 20
        and runtime.get("total_timed_observations") == 60
        and runtime.get("torch_profiler_schedule") == {"wait": 1, "warmup": 1, "active": 5, "repeat": 1}
        and runtime.get("completed_execution_rerun_authorized") is False
        and preflight.get("profiling_blocks") == 0
        and preflight.get("timed_observations") == 0
        and preflight.get("torch_profiler_traces") == 0
        and preflight.get("optimizer_steps") == 0
        and preflight.get("model_updates") == 0
        and preflight.get("D6_cases_accessed") == 0
        and result.get("dominant_share_threshold") == 0.5
        and result.get("formal_gate_changed") is False
        and result.get("formal_gate_rerun") is False
        and result.get("result_can_authorize_training") is False
        and result.get("result_can_authorize_implementation_change") is False
        and boundary.get("posthoc_profiling_execution_authorized") is True
        and boundary.get("execution_started") is False
        and boundary.get("formal_efficiency_rerun_authorized") is False
        and boundary.get("R1_implementation_change_authorized") is False
        and boundary.get("optimized_alternative_benchmark_authorized") is False
        and boundary.get("R2_implementation_authorized") is False
        and boundary.get("seed0_training_authorized") is False
        and boundary.get("seed1_training_authorized") is False
        and boundary.get("D6B_authorized") is False
        and boundary.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("D6-A R1 profiling execution authorization protocol drifted")


def verify_parent_lock(lock_dir: Path) -> dict[str, Any]:
    verify_manifest(lock_dir, EXPECTED_LOCK["manifest"])
    protocol_path = lock_dir / "profiling_protocol_v1.json"
    receipt_path = lock_dir / "protocol_lock_receipt.json"
    if sha256_file(protocol_path) != EXPECTED_LOCK["protocol"]:
        raise RuntimeError("Frozen profiling protocol drifted")
    if sha256_file(receipt_path) != EXPECTED_LOCK["receipt"]:
        raise RuntimeError("Frozen profiling lock receipt drifted")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        receipt.get("status") == "D6A_R1_latency_posthoc_profiling_protocol_frozen_non_runnable"
        and receipt.get("formal_result_status") == "D6A_formal_efficiency_gate_failed"
        and receipt.get("frozen_R1_latency_ms_median") == 292.5087884068489
        and receipt.get("formal_gate_changed") is False
        and receipt.get("formal_gate_rerun") is False
        and receipt.get("profiling_runs") == 0
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("D6_cases_accessed") == 0
        and receipt.get("posthoc_profiling_execution_authorized") is False
        and receipt.get("seed0_training_authorized") is False
        and receipt.get("seed1_training_authorized") is False
        and receipt.get("D6B_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Parent profiling lock permission boundary drifted")
    return receipt


def implementation_hashes() -> dict[str, str]:
    paths = {
        "R1": ROOT / "utils/mamba_d6a_slot_allocator.py",
        "efficiency": ROOT / "utils/mamba_d6a_efficiency.py",
        "profiler": ROOT / "utils/mamba_d6a_r1_latency_profiler.py",
        "authorize": Path(__file__).resolve(),
        "verify": ROOT / "tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_authorization.py",
        "preflight": ROOT / "tools/preflight_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py",
        "execute": ROOT / "tools/run_mamba_v16_d6a_r1_latency_posthoc_profiling.py",
        "tests": ROOT / "tools/test_mamba_v16_d6a_r1_latency_posthoc_profiling_execution_contract.py",
    }
    hashes = {}
    for name, path in paths.items():
        if not path.is_file():
            raise RuntimeError(f"Missing profiling implementation: {path}")
        hashes[name] = sha256_file(path)
    for name, expected in EXPECTED_IMPLEMENTATION.items():
        if hashes[name] != expected:
            raise RuntimeError(f"Frozen {name} implementation drifted")
    return hashes


def write_exact(root: Path, files: Mapping[str, bytes]) -> None:
    if root.exists():
        existing = {
            path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
        }
        mismatches = [
            name
            for name, payload in files.items()
            if not (root / name).is_file() or (root / name).read_bytes() != payload
        ]
        if existing != set(files) or mismatches:
            raise RuntimeError(f"Refusing non-identical profiling authorization: {mismatches}")
        print(f"[locked] existing R1 profiling authorization is byte-identical: {root}")
        return
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiling_lock_dir", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    parent_receipt = verify_parent_lock(args.profiling_lock_dir.resolve())
    runtime = protocol["runtime"]
    config = {
        "authorization_version": VERSION,
        "status": "D6A_R1_latency_posthoc_profiling_execution_authorized_not_started",
        **runtime,
        "formal_result_status": parent_receipt["formal_result_status"],
        "frozen_R1_latency_ms_median": parent_receipt["frozen_R1_latency_ms_median"],
        "result_contract": protocol["result_contract"],
        "boundaries": protocol["permission_boundary"],
    }
    config_name = "MambaV16D6A_R1_latency_posthoc_profiling_seed160610.json"
    config_payload = canonical_json(config)
    configs = {config_name: config_payload}
    write_exact(args.config_output_dir.resolve(), configs)

    receipt = {
        "authorization_version": VERSION,
        "status": "D6A_R1_latency_posthoc_profiling_execution_authorized",
        "runtime_config": {"name": config_name, "sha256": sha256_bytes(config_payload)},
        "lineage_sha256": {
            "profiling_lock_manifest": EXPECTED_LOCK["manifest"],
            "profiling_lock_protocol": EXPECTED_LOCK["protocol"],
            "profiling_lock_receipt": EXPECTED_LOCK["receipt"],
            "authorization_protocol": sha256_file(PROTOCOL),
            "authorization_report": sha256_file(REPORT),
        },
        "implementation_sha256": implementation_hashes(),
        "posthoc_profiling_execution_authorized": True,
        "execution_started": False,
        "profiling_blocks_completed": 0,
        "timed_observations_completed": 0,
        "torch_profiler_traces_completed": 0,
        "formal_gate_changed": False,
        "formal_gate_rerun": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "R1_implementation_change_authorized": False,
        "optimized_alternative_benchmark_authorized": False,
        "R2_implementation_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_zero_count_CUDA_authorization_preflight",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "profiling_execution_authorization_receipt.json"
    files = {
        receipt_name: receipt_payload,
        f"{receipt_name}.sha256": (
            f"{sha256_bytes(receipt_payload)}  {receipt_name}\n"
        ).encode("ascii"),
        "runtime_config.sha256": manifest_bytes(configs),
        "execution_authorization_protocol_v1.json": canonical_json(protocol),
        "execution_authorization_report_zh.md": REPORT.read_bytes(),
    }
    files["files.sha256"] = manifest_bytes(files)
    write_exact(args.authorization_output_dir.resolve(), files)
    print("[authorized] D6-A R1 artificial-descriptor post-hoc profiling only")
    print("[locked] execution not started; training=false seed1=false D6B=false sealed=false")
    print("[next] run separate zero-count CUDA authorization preflight")


if __name__ == "__main__":
    main()
