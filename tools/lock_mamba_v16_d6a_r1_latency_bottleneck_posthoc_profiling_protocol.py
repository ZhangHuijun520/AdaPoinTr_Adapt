#!/usr/bin/env python3
"""Freeze the non-runnable D6-A R1 latency post-hoc profiling contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_r1_latency_bottleneck_posthoc_profiling_protocol_v1.json"
PROTOCOL_ID = "mamba-v16-d6a-r1-latency-bottleneck-posthoc-profiling-v1"

REPO_PARENTS = {
    "negative_result_report": (
        "docs/mamba_v16_d6a_formal_efficiency_complete_negative_result_zh.md",
        "448bfabc5c8dc14580527122439e83c37fc96370e49c70e3ea164be8395ed28e",
    ),
    "efficiency_implementation": (
        "utils/mamba_d6a_efficiency.py",
        "7a42c8fafe09ba3a98a052dd002137b4a9ab3d71ef630585cc85a269dfd8428b",
    ),
    "R1_implementation": (
        "utils/mamba_d6a_slot_allocator.py",
        "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43",
    ),
    "formal_runner": (
        "tools/run_mamba_v16_d6a_formal_efficiency.py",
        "8a58790403800fef3646ee2fc91727244093d2b629b42ed1347e7d6584cdf4f5",
    ),
    "negative_archive_verifier": (
        "tools/verify_mamba_v16_d6a_formal_efficiency_negative_archive.py",
        "d722a402344f0ed0506d314e4d197abdfab38b8dbb311145d6e023be36ee94ff",
    ),
}

FORMAL_RESULT_FILES = {
    "result_manifest": ("files.sha256", "a448a65b1f83a9bde232395a18c491bc33b192ebd091a5a08b1a15be18cd35d3"),
    "candidate_metrics": ("formal_efficiency_candidate_metrics.json", "452a31019ec528991543dc33e31c6d30cb28b56873309f8303d45020af559e94"),
    "result_receipt": ("formal_efficiency_result_receipt.json", "3ef41b0e0c211935d2e0f900732dbf4d30b792e86c5144115d8850671a3d3303"),
    "result_report": ("formal_efficiency_result_report_zh.md", "dd6758baa8bc780397d315831978b7b5e085c44418d97a659e7ba75aca8f26d1"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    require(protocol["protocol_id"] == PROTOCOL_ID, "Protocol id drifted")
    require(
        protocol["status"]
        == "posthoc_profiling_preregistered_non_runnable_after_frozen_negative",
        "Protocol status drifted",
    )
    parent = protocol["frozen_parent"]
    require(parent["result_status"] == "D6A_formal_efficiency_gate_failed", "Parent result drifted")
    require(parent["R1_latency_ms_median"] == 292.5087884068489, "Frozen R1 latency drifted")
    require(parent["formal_gate_changed"] is False, "Formal gate changed")
    require(parent["formal_gate_rerun_authorized"] is False, "Formal rerun authorized")

    scope = protocol["scope"]
    require(scope["candidate"] == "R1_only", "Profiling is not R1-only")
    require(scope["data"] == "deterministic_artificial_descriptor_only", "Real data enabled")
    require(scope["descriptor_shape"] == [1, 8192, 27], "Descriptor shape drifted")
    require(scope["development_cases_accessed"] == 0, "Development access enabled")
    require(scope["checkpoint_accessed"] is False, "Checkpoint access enabled")
    require(scope["protected_or_sealed_data_accessed"] is False, "Sealed access enabled")

    execution = protocol["execution_contract"]
    require(execution["authorized_now"] is False, "Profiling execution authorized")
    require(execution["separate_execution_authorization_required"] is True, "Authorization bypassed")
    require(execution["blocks"] == 3, "Profiling blocks drifted")
    require(execution["warmup_runs_per_block"] == 5, "Warmup count drifted")
    require(execution["timed_runs_per_block"] == 20, "Timed count drifted")
    require(execution["total_timed_observations"] == 60, "Observation count drifted")
    require(execution["formal_efficiency_thresholds_evaluated"] is False, "Formal gate re-enabled")
    require(execution["optimizer_constructed"] is False, "Optimizer enabled")
    require(execution["optimizer_steps"] == 0 and execution["model_updates"] == 0, "Updates enabled")

    passes = {item["name"]: item for item in protocol["profiling_passes"]}
    require(
        set(passes)
        == {"exact_path_wall_clock", "global_assignment_decomposition", "torch_profiler_trace"},
        "Profiling passes drifted",
    )
    schedule = passes["torch_profiler_trace"]["schedule"]
    require(schedule == {"wait": 1, "warmup": 1, "active": 5, "repeat": 1}, "Trace schedule drifted")

    attribution = protocol["predeclared_attribution"]
    require(attribution["dominant_threshold"] == 0.5, "Attribution threshold drifted")
    require(attribution["causal_claim_authorized"] is False, "Causal claim enabled")
    require(attribution["optimized_alternative_benchmark_authorized"] is False, "Optimization enabled")

    permission = protocol["permission_boundary"]
    require(permission["protocol_lock_authorized"] is True, "Protocol lock disabled")
    for key in (
        "posthoc_profiling_execution_authorized",
        "formal_efficiency_rerun_authorized",
        "R1_implementation_change_authorized",
        "R2_implementation_authorized",
        "seed0_training_authorized",
        "seed1_training_authorized",
        "proposal_confirmation_authorized",
        "D6B_authorized",
        "candidate_selection_authorized",
        "protected_or_sealed_data_accessed",
    ):
        require(permission[key] is False, f"Forbidden permission enabled: {key}")


def verify_lineage(repo_root: Path, formal_result_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    repo_hashes = {}
    for key, (relative, expected) in REPO_PARENTS.items():
        path = repo_root / relative
        require(path.is_file(), f"Missing repository parent: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"Repository parent drifted: {relative}")
        repo_hashes[key] = actual

    result_hashes = {}
    for key, (name, expected) in FORMAL_RESULT_FILES.items():
        path = formal_result_dir / name
        require(path.is_file(), f"Missing formal result parent: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"Formal result parent drifted: {path}")
        result_hashes[key] = actual

    receipt = json.loads(
        (formal_result_dir / "formal_efficiency_result_receipt.json").read_text(encoding="utf-8")
    )
    require(receipt["status"] == "D6A_formal_efficiency_gate_failed", "Formal result is not negative")
    require(receipt["R1_to_R0_latency_ratio"] == 735.1363522524863, "Latency ratio drifted")
    require(receipt["all_efficiency_gates_passed"] is False, "Formal gate unexpectedly passed")
    require(receipt["optimizer_steps"] == 0 and receipt["model_updates"] == 0, "Formal result updated model")
    require(receipt["seed0_training_authorized"] is False, "Formal result authorized training")
    require(receipt["protected_or_sealed_data_accessed"] is False, "Formal result accessed sealed data")
    return repo_hashes, result_hashes


def build_outputs(
    protocol: Mapping[str, Any],
    repo_hashes: Mapping[str, str],
    result_hashes: Mapping[str, str],
) -> dict[str, bytes]:
    outputs = {
        "profiling_protocol_v1.json": PROTOCOL.read_bytes(),
        "profiling_contract.json": canonical_json(
            {
                "scope": protocol["scope"],
                "execution_contract": protocol["execution_contract"],
                "profiling_passes": protocol["profiling_passes"],
                "attribution": protocol["predeclared_attribution"],
                "required_outputs": protocol["required_outputs"],
            }
        ),
        "profiling_execution.template.json": canonical_json(
            {
                "runnable": False,
                "separate_execution_authorization_required": True,
                "protocol_id": PROTOCOL_ID,
                "candidate": "R1",
                "descriptor_seed": 160610,
                "formal_gate_evaluated": False,
                "optimizer_constructed": False,
                "training": False,
            }
        ),
    }
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "D6A_R1_latency_posthoc_profiling_protocol_frozen_non_runnable",
        "protocol_sha256": sha256_file(PROTOCOL),
        "repository_parent_sha256": dict(repo_hashes),
        "formal_result_parent_sha256": dict(result_hashes),
        "formal_result_status": "D6A_formal_efficiency_gate_failed",
        "frozen_R1_latency_ms_median": 292.5087884068489,
        "formal_gate_changed": False,
        "formal_gate_rerun": False,
        "profiling_runs": 0,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        **protocol["permission_boundary"],
    }
    outputs["protocol_lock_receipt.json"] = canonical_json(receipt)
    outputs["protocol_lock_report_zh.md"] = (
        "# Mamba v1.6 D6-A R1 latency post-hoc profiling protocol lock\n\n"
        "- Parent formal result：R1 median 292.508788407 ms；gate frozen negative。\n"
        "- Scope：R1-only、人工 1 x 8192 x 27 descriptor、D6 cases=0。\n"
        "- 固定观测：3 blocks x (5 warmup + 20 timed)，共 60 个 timed observation。\n"
        "- 固定分解：GPU forward、validation/sync、D2H、SciPy assignment、GPU reconstruction。\n"
        "- PyTorch trace：wait/warmup/active/repeat = 1/1/5/1。\n"
        "- 当前仅冻结不可运行协议；profiling execution 必须另行授权。\n"
        "- Formal gate 不重跑、不改变；training、seed-1、confirmation、D6-B、selection 均锁定。\n"
    ).encode("utf-8")
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    ).encode("ascii")
    return outputs


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        require(existing == dict(outputs), f"Existing profiling protocol lock drifted: {output_dir}")
        print(f"[locked] existing R1 latency profiling lock is byte-identical: {output_dir}")
        return
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            target = working / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        working.replace(output_dir)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise
    print(f"[saved] immutable R1 latency profiling protocol: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo_root", type=Path, default=ROOT)
    parser.add_argument("--formal_result_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    repo_hashes, result_hashes = verify_lineage(
        args.repo_root.resolve(), args.formal_result_dir.resolve()
    )
    outputs = build_outputs(protocol, repo_hashes, result_hashes)
    write_locked(outputs, args.out_dir.resolve())
    print("[done] D6-A R1 latency post-hoc profiling protocol frozen")
    print("[authorized-next] separate profiling execution authorization only")
    print("[locked] profiling=false training=false seed1=false D6B=false confirmation=false")


if __name__ == "__main__":
    main()
