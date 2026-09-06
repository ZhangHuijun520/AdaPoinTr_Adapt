#!/usr/bin/env python3
"""Freeze the non-runnable D6-A R1 exact-assignment optimization protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    ROOT
    / "docs"
    / "mamba_v16_d6a_r1_exact_assignment_optimization_feasibility_protocol_v1.json"
)
PROTOCOL_ID = "mamba-v16-d6a-r1-exact-assignment-optimization-feasibility-v1"

REPO_PARENTS = {
    "profiling_complete_report": (
        "docs/mamba_v16_d6a_r1_latency_posthoc_profiling_complete_result_zh.md",
        "9cf353d16161848952d5e7ff8b24a4294ddb3236b7f2f03e623d64dea6163b1e",
    ),
    "R1_implementation": (
        "utils/mamba_d6a_slot_allocator.py",
        "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43",
    ),
    "profiling_implementation": (
        "utils/mamba_d6a_r1_latency_profiler.py",
        "2ad3cfd0e9a4db14c0c3459f304b0ba951ac1f63542e4f97b250a85ae8f2d157",
    ),
}

PROFILING_RESULT_FILES = {
    "result_manifest": (
        "files.sha256",
        "8c0fb421188abe6efdd0081013eb451cb87bf5a3768f9279b7bf16678709f385",
    ),
    "receipt": (
        "posthoc_profiling_receipt.json",
        "ba4382e9af597189ec75ff3ea12175d3a4add8ec9894e02ccab3301d6469a0d9",
    ),
    "report": (
        "posthoc_profiling_report_zh.md",
        "772e080e644d377a865e6cd40628a5a82550a639c8d01a3f2514c9c2fe7b173d",
    ),
    "assignment_metrics": (
        "r1_assignment_stage_metrics.csv",
        "99d6601c0994d8966412f0b23f29f4bf80f393ec569f663c67830c670c3dfe12",
    ),
    "exact_path_metrics": (
        "r1_exact_path_stage_metrics.csv",
        "2cd82f348c910d6b699b759661c1fcf99a064802aba4d02917d0e2880a40f327",
    ),
    "attribution_summary": (
        "r1_latency_attribution_summary.json",
        "b5f1ca7f37fde4c06a8564700799b2e32ae05b01842dd399047415f7d0607c37",
    ),
}

FREEZE_FILES = {
    "freeze_manifest": (
        "files.sha256",
        "c2fbcc4c6b894201cd5111877b9df6d66d0b0050f99365fb1751cedab633e2a4",
    ),
    "artifact_inventory": (
        "artifact_inventory.tsv",
        "698551249e7983fb98a42ad7fd7bc146b229c612013dded274d6a97e3d6d4c1f",
    ),
    "freeze_receipt": (
        "profiling_result_freeze_receipt.json",
        "4156c7a0fb75c7d4f4108bf2d3e14b9483a415ba21e8c56ff2b11c8a66f02501",
    ),
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
        == "optimization_feasibility_preregistered_non_runnable_after_frozen_profiling",
        "Protocol status drifted",
    )

    parent = protocol["frozen_parent"]
    require(parent["formal_result_status"] == "D6A_formal_efficiency_gate_failed", "Parent result drifted")
    require(
        parent["profiling_result_status"]
        == "D6A_R1_latency_posthoc_profiling_complete_observation_only",
        "Profiling parent drifted",
    )
    require(parent["profiling_classification"] == "scipy_global_assignment_dominant", "Attribution drifted")
    require(parent["scipy_assignment_profiled_share"] == 0.7087436968007994, "Attribution share drifted")
    require(parent["formal_gate_changed"] is False, "Formal gate changed")
    require(parent["formal_gate_rerun_authorized"] is False, "Formal rerun enabled")

    scope = protocol["scope"]
    require(scope["candidate"] == "R1_only", "Optimization is not R1-only")
    require(scope["selector_shape"] == [32, 8192], "Selector shape drifted")
    require(scope["data"] == "deterministic_artificial_assignment_matrices_only", "Real data enabled")
    require(scope["D6_cases_accessed"] == 0, "D6 access enabled")
    require(scope["checkpoint_accessed"] is False, "Checkpoint access enabled")
    require(scope["optimizer_constructed"] is False, "Optimizer enabled")
    require(scope["optimizer_steps"] == 0 and scope["model_updates"] == 0, "Updates enabled")

    candidates = protocol["candidate_definitions"]
    require(set(candidates) == {"S0", "S1", "S2"}, "Candidate definitions drifted")
    require(candidates["S1"]["row_top_k"] == 32, "S1 top-k drifted")
    require(candidates["S1"]["cutoff_ties"] == "include_all", "S1 cutoff ties dropped")
    require(candidates["S1"]["union_order"] == "ascending_original_candidate_index", "S1 union order drifted")
    require(candidates["S1"]["full_D2H_retained"] is True, "S1 silently reduced D2H")
    require(candidates["S1"]["fallback_to_S0_during_benchmark"] is False, "S1 fallback hid failures")
    require(candidates["S2"]["implementation_change_authorized"] is False, "S2 implementation enabled")
    require(candidates["S2"]["benchmark_authorized"] is False, "S2 benchmark enabled")

    boundary = protocol["mathematical_boundary"]
    require(boundary["tie_rule"] == "all columns tied at the row top32 cutoff must be retained", "Tie rule drifted")
    require("does not guarantee" in boundary["non_guarantee"], "Multi-optimum caveat removed")
    require("slot_to_candidate" in boundary["required_resolution"], "Slot mapping gate removed")

    suite = protocol["synthetic_equivalence_suite"]
    require(suite["matrix_shape"] == [32, 8192], "Synthetic shape drifted")
    require(suite["total_cases"] == 168, "Synthetic case count drifted")
    require(sum(item["cases"] for item in suite["families"]) == 168, "Synthetic family counts drifted")
    require(len(suite["families"]) == 7, "Synthetic families drifted")
    require(suite["post_result_case_search_forbidden"] is True, "Post-result search enabled")

    gate = protocol["equivalence_hard_gate"]
    require(gate["cases_required"] == 168, "Equivalence count drifted")
    for key in (
        "slot_to_candidate_exact",
        "sorted_selected_indices_exact",
        "hard_assignment_exact",
        "adjusted_objective_exact",
        "baseline_columns_contained_in_union",
    ):
        require(gate[key] == "168/168", f"Equivalence gate drifted: {key}")
    require(
        gate["failure_action"] == "freeze_S1_negative_and_stop_without_performance_benchmark",
        "Equivalence failure action drifted",
    )

    benchmark = protocol["future_artificial_benchmark"]
    require(benchmark["authorized_now"] is False, "Benchmark execution enabled")
    require(benchmark["separate_execution_authorization_required"] is True, "Benchmark authorization bypassed")
    require(benchmark["candidate_order_by_block"] == [["S0", "S1"], ["S1", "S0"], ["S0", "S1"]], "Order drifted")
    require(benchmark["timed_observations_per_candidate"] == 150, "Timed observations drifted")
    require(set(benchmark["CPU_thread_environment"].values()) == {1}, "CPU threads are not fixed")
    require(benchmark["formal_efficiency_thresholds_evaluated"] is False, "Formal gate re-enabled")

    engineering = protocol["engineering_progression_gate"]
    require(engineering["S1_scipy_solver_median_speedup_minimum"] == 4.0, "Solver gate drifted")
    require(engineering["S1_assignment_total_median_speedup_minimum"] == 2.0, "Assignment gate drifted")
    require(engineering["all_equivalence_hard_gates_required"] is True, "Equivalence bypassed")

    formal = protocol["formal_gate_feasibility_check"]
    require(formal["classification"] == "descriptive_non_formal_only", "Formal classification drifted")
    require(formal["unchanged_R1_to_R0_latency_ratio_maximum"] == 1.15, "Formal threshold drifted")
    require(formal["implied_R1_latency_ms_maximum"] == 0.4575819242745637, "Implied limit drifted")
    require(formal["formal_rerun_authorized_now"] is False, "Formal rerun authorized")
    require(formal["training_authorized_now"] is False, "Training authorized")

    permission = protocol["permission_boundary"]
    require(permission["protocol_lock_authorized"] is True, "Protocol lock disabled")
    for key, value in permission.items():
        if key != "protocol_lock_authorized":
            require(value is False, f"Forbidden permission enabled: {key}")


def verify_files(root: Path, expected_files: Mapping[str, tuple[str, str]]) -> dict[str, str]:
    hashes = {}
    for key, (relative, expected) in expected_files.items():
        path = root / relative
        require(path.is_file(), f"Missing frozen parent: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"Frozen parent drifted: {path}")
        hashes[key] = actual
    return hashes


def verify_lineage(
    repo_root: Path,
    profiling_result_dir: Path,
    freeze_dir: Path,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    repo_hashes = verify_files(repo_root, REPO_PARENTS)
    result_hashes = verify_files(profiling_result_dir, PROFILING_RESULT_FILES)
    freeze_hashes = verify_files(freeze_dir, FREEZE_FILES)

    result = json.loads((profiling_result_dir / "posthoc_profiling_receipt.json").read_text(encoding="utf-8"))
    require(
        result["status"] == "D6A_R1_latency_posthoc_profiling_complete_observation_only",
        "Profiling result status drifted",
    )
    require(result["timed_observations"] == 60, "Profiling observation count drifted")
    require(result["model_updates"] == 0 and result["D6_cases_accessed"] == 0, "Profiling boundary drifted")
    require(result["formal_gate_changed"] is False, "Profiling changed formal gate")
    require(result["seed0_training_authorized"] is False, "Profiling authorized seed-0 training")
    require(result["seed1_training_authorized"] is False, "Profiling authorized seed-1 training")
    require(result["R1_implementation_change_authorized"] is False, "Profiling authorized R1 changes")
    require(result["formal_gate_rerun"] is False, "Profiling authorized formal rerun")

    frozen = json.loads((freeze_dir / "profiling_result_freeze_receipt.json").read_text(encoding="utf-8"))
    require(frozen["status"] == "D6A_R1_latency_posthoc_profiling_result_frozen", "Freeze status drifted")
    require(frozen["artifact_count"] == 57, "Freeze inventory count drifted")
    require(frozen["formal_gate_changed"] is False, "Freeze changed formal gate")
    require(frozen["training_authorized"] is False, "Freeze authorized training")
    return repo_hashes, result_hashes, freeze_hashes


def build_outputs(
    protocol: Mapping[str, Any],
    repo_hashes: Mapping[str, str],
    result_hashes: Mapping[str, str],
    freeze_hashes: Mapping[str, str],
) -> dict[str, bytes]:
    outputs = {
        "optimization_feasibility_protocol_v1.json": PROTOCOL.read_bytes(),
        "optimization_contract.json": canonical_json(
            {
                "candidate_definitions": protocol["candidate_definitions"],
                "mathematical_boundary": protocol["mathematical_boundary"],
                "equivalence_hard_gate": protocol["equivalence_hard_gate"],
                "engineering_progression_gate": protocol["engineering_progression_gate"],
                "formal_gate_feasibility_check": protocol["formal_gate_feasibility_check"],
            }
        ),
        "synthetic_equivalence_suite.json": canonical_json(protocol["synthetic_equivalence_suite"]),
        "S0_S1_benchmark.template.json": canonical_json(
            {
                "runnable": False,
                "separate_execution_authorization_required": True,
                "protocol_id": PROTOCOL_ID,
                "candidate_order_by_block": protocol["future_artificial_benchmark"]["candidate_order_by_block"],
                "blocks": protocol["future_artificial_benchmark"]["blocks"],
                "warmup_runs_per_candidate_per_block": 10,
                "timed_runs_per_candidate_per_block": 50,
                "formal_gate_evaluated": False,
                "optimizer_constructed": False,
                "training": False,
            }
        ),
    }
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "D6A_R1_exact_assignment_optimization_feasibility_protocol_frozen_non_runnable",
        "protocol_sha256": sha256_file(PROTOCOL),
        "repository_parent_sha256": dict(repo_hashes),
        "profiling_result_parent_sha256": dict(result_hashes),
        "profiling_freeze_parent_sha256": dict(freeze_hashes),
        "equivalence_cases": 168,
        "S1_row_top_k": 32,
        "S1_cutoff_ties_included": True,
        "S1_full_D2H_retained": True,
        "formal_latency_ratio_maximum": 1.15,
        "implied_R1_latency_ms_maximum": 0.4575819242745637,
        "optimization_runs": 0,
        "formal_reruns": 0,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        **protocol["permission_boundary"],
    }
    outputs["protocol_lock_receipt.json"] = canonical_json(receipt)
    outputs["protocol_lock_report_zh.md"] = (
        "# Mamba v1.6 D6-A R1 exact-assignment optimization feasibility protocol lock\n\n"
        "- Parent：formal efficiency negative；profiling attribution = SciPy assignment dominant。\n"
        "- S0：完整 32 x 8192 CPU float64 SciPy reference。\n"
        "- S1：完整 D2H 后执行 tie-safe row-top32 union，再运行同一 SciPy solver。\n"
        "- Equivalence：168/168 slot mapping、selected indices、hard assignment 与 objective 全部一致。\n"
        "- Engineering gates：solver >= 4x；assignment total >= 2x。\n"
        "- 原 1.15x formal gate、R0 denominator 和负结果保持不变。\n"
        "- 当前只冻结不可运行协议；S1 implementation/zero-step 必须另行授权。\n"
        "- Optimization、formal rerun、training、seed-1、D6-B、selection、sealed 均锁定。\n"
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
        require(existing == dict(outputs), f"Existing optimization protocol lock drifted: {output_dir}")
        print(f"[locked] existing optimization protocol lock is byte-identical: {output_dir}")
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
    print(f"[saved] immutable R1 exact-assignment optimization protocol: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo_root", type=Path, default=ROOT)
    parser.add_argument("--profiling_result_dir", type=Path, required=True)
    parser.add_argument("--profiling_freeze_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    repo_hashes, result_hashes, freeze_hashes = verify_lineage(
        args.repo_root.resolve(),
        args.profiling_result_dir.resolve(),
        args.profiling_freeze_dir.resolve(),
    )
    outputs = build_outputs(protocol, repo_hashes, result_hashes, freeze_hashes)
    write_locked(outputs, args.out_dir.resolve())
    print("[done] D6-A R1 exact-assignment optimization feasibility protocol frozen")
    print("[authorized-next] separate S1 implementation and artificial zero-step only")
    print("[locked] optimization=false formal_rerun=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
