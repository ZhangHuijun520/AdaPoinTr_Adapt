#!/usr/bin/env python3
"""Freeze the non-runnable D6-A R1 S2 artificial benchmark protocol."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_r1_s2_artificial_performance_benchmark_protocol_v1.json"
PROTOCOL_ID = "mamba-v16-d6a-r1-s2-artificial-performance-benchmark-v1"

EXPECTED_PARENT_LOCK = {
    "files.sha256": "abc72d3d05637d1a19d028425a693d775728843447ea16301c2b1484dbd67494",
    "S0_S2_zero_step.template.json": "1e946cdc2c9a5db721df73ff9114217d069455231957f961bd07ddb029e34b37",
    "certified_fast_path_contract.json": "4c8e0c8395596a314caafc8734a37d63702d95dbc6710fee159472d93cfb4594",
    "protocol_lock_receipt.json": "21d622cfcce240fc050c6751970dc162abe02e6998df106d387ab16590a3013b",
    "protocol_lock_report_zh.md": "25de660e0c001dd7cffc2f862de83eee1fb371304dffff21e6cbca3dc0b4d8a2",
    "protocol_v1.json": "360b2e8ed87371d84bb0be4d4c9170ff9b10f1fb8a5ed0a2b20cbf3133a14281",
    "synthetic_equivalence_suite.json": "864e11ab4edf3164963bcb68123499c2b52f02429a566e95cd2303322d14ebc0",
}

EXPECTED_RESULT = {
    "files.sha256": "5713a4fa4307cd0a68c8d429848b6055e2b0d888c2eea0c5e39cd9d965fcbeb6",
    "s2_artificial_equivalence_metrics.csv": "be1ea8643a169293cf258bd39473557f8a40f72da31427b84cfc5fcc85677244",
    "s2_certification_routing_metrics.csv": "182654d18b1c428f80f4f796449c35eafe17d782e11238fa7856811a302a4cc1",
    "s2_family_summary.csv": "102a7c4d3b5c0dff5410f17a3f6d88c14b2d755267d9dde2eacb0ed2c7c79fd0",
    "s2_artificial_zero_step_summary.json": "a3b9c5ede525f3b29e638abdc55f97c7367d8b760fb34d829d0472b3093813d1",
    "s2_artificial_zero_step_receipt.json": "85d8a0946504bb02d471b0087df7d6a8ccb929c01dc40df031088c6143a9c061",
    "s2_artificial_zero_step_report_zh.md": "a166d0fb514716d2e71477dc064243a3e0623a85c93477127f7f0d1d50e4df7b",
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


def verify_manifest(root: Path) -> int:
    manifest = root / "files.sha256"
    require(manifest.is_file(), f"Missing frozen manifest: {manifest}")
    resolved_root = root.resolve()
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        wanted, relative = line.split(maxsplit=1)
        posix = PurePosixPath(relative.lstrip("*"))
        require(not posix.is_absolute() and ".." not in posix.parts, f"Unsafe manifest path: {relative}")
        path = root.joinpath(*posix.parts).resolve()
        require(path == resolved_root or resolved_root in path.parents, f"Manifest path escaped root: {path}")
        require(path.is_file() and sha256_file(path) == wanted.lower(), f"Manifest mismatch: {path}")
        count += 1
    return count


def verify_hashes(root: Path, expected: Mapping[str, str]) -> dict[str, str]:
    observed = {}
    for name, wanted in expected.items():
        path = root / name
        require(path.is_file(), f"Missing frozen parent: {path}")
        actual = sha256_file(path)
        require(actual == wanted, f"Frozen parent drifted: {path}")
        observed[name] = actual
    return observed


def flag(row: Mapping[str, str], key: str) -> bool:
    return row[key].lower() == "true"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    require(protocol["protocol_id"] == PROTOCOL_ID, "Protocol id drifted")
    require(
        protocol["status"]
        == "preregistered_non_runnable_after_frozen_S2_positive_before_benchmark_authorization_or_execution",
        "Protocol status drifted",
    )

    parent = protocol["frozen_parent"]
    require(parent["S2_result_status"] == "D6A_R1_S2_certified_fast_path_artificial_zero_step_passed", "S2 status drifted")
    for key in ("cases", "slot_to_candidate_exact", "sorted_selected_indices_exact", "hard_assignment_exact", "adjusted_objective_exact"):
        require(parent[key] == 168, f"Frozen result count drifted: {key}")
    require(parent["certified_fast_path_cases"] == 96 and parent["fallback_s0_cases"] == 72, "Frozen routing drifted")
    require(parent["false_positive_certificates"] == 0, "Frozen false-positive count drifted")
    require(parent["result_hashes"] == EXPECTED_RESULT, "Frozen result hashes drifted")

    scope = protocol["scope"]
    require(scope["candidates"] == ["S0", "S2"], "Candidate set drifted")
    require(scope["selector_shape"] == [32, 8192], "Selector shape drifted")
    require(scope["data"] == "the_same_frozen_168_artificial_assignment_matrices_only", "Artificial suite changed")
    for key in ("checkpoints_accessed", "D6_cases_accessed", "STL_or_NPZ_accessed", "protocol_lock_timing_calls", "protocol_lock_warmup_calls", "protocol_lock_profiler_traces", "optimizer_steps", "model_updates"):
        require(scope[key] == 0, f"Protocol-lock boundary drifted: {key}")
    require(scope["optimizer_constructed"] is False and scope["protected_or_sealed_data_accessed"] is False, "Forbidden scope enabled")

    candidates = protocol["candidate_definitions"]
    require(set(candidates) == {"S0", "S2", "excluded_from_timing"}, "Candidate definitions drifted")
    require("complete 32x8192" in candidates["S0"]["timed_boundary"], "S0 complete path excluded")
    for term in ("full D2H", "32 edge-exclusion solves", "exact S0 fallback"):
        require(term in candidates["S2"]["timed_boundary"], f"S2 timed path excluded: {term}")
    require(candidates["S2"]["full_D2H_retained"] is True, "S2 D2H changed")
    require(candidates["S2"]["certified_fast_path_cases_expected"] == 96, "Fast route count drifted")
    require(candidates["S2"]["fallback_s0_cases_expected"] == 72, "Fallback count drifted")
    require(candidates["S0"]["implementation_change_authorized"] is False, "S0 changes enabled")
    require(candidates["S2"]["implementation_change_authorized"] is False, "S2 changes enabled")

    replay = protocol["pre_timing_correctness_replay"]
    require(replay["required_before_any_timed_call"] is True, "Pre-timing replay removed")
    require(replay["cases"] == replay["S0_calls"] == replay["S2_calls"] == 168, "Replay count drifted")
    for key in ("slot_to_candidate_exact_required", "sorted_selected_indices_exact_required", "hard_assignment_exact_required", "adjusted_objective_exact_required", "input_state_unchanged_required"):
        require(replay[key] == "168/168", f"Replay equivalence gate drifted: {key}")
    require(replay["certified_fast_path_cases_required"] == 96 and replay["fallback_s0_cases_required"] == 72, "Replay routing drifted")
    require(replay["fallback_reasons_required"] == {"cutoff_tie_or_near_tie": 32, "global_optimum_not_certified_unique": 40}, "Fallback reasons drifted")
    require(replay["false_positive_certificates_allowed"] == 0, "False positives enabled")
    require("without_any_timed_call" in replay["failure_action"], "Replay failure can leak into timing")

    design = protocol["benchmark_design"]
    require(design["authorized_now"] is False and design["separate_execution_authorization_required"] is True, "Benchmark enabled")
    require(design["execution_count_after_authorization"] == design["processes"] == design["CUDA_devices"] == 1, "Execution topology drifted")
    require(design["inference_context"] == "torch.inference_mode", "Inference context drifted")
    require(set(design["CPU_thread_environment"].values()) == {1}, "CPU thread controls drifted")
    warmup = design["warmup"]
    require(warmup["rounds"] == 2 and warmup["calls_per_candidate"] == 14 and warmup["total_calls"] == 28, "Warmup schedule drifted")
    require(warmup["timed"] is False, "Warmup became timed")
    measurement = design["measurement"]
    require(measurement["blocks"] == 3 and measurement["cases_per_block"] == 168, "Measurement blocks drifted")
    require(measurement["timed_calls_per_candidate"] == 504 and measurement["total_timed_calls"] == 1008, "Timed counts drifted")
    require("mod_2" in measurement["paired_order_rule"], "Paired alternation removed")
    require(measurement["candidate_first_counts_per_block"] == {"S0": 84, "S2": 84}, "Paired order is unbalanced")
    require(measurement["CUDA_synchronize_immediately_before_each_call"] is True, "Pre-call CUDA sync removed")
    require(measurement["CUDA_synchronize_immediately_after_each_call"] is True, "Post-call CUDA sync removed")
    require(measurement["clock"] == "time.perf_counter_ns", "Clock drifted")
    require(measurement["outlier_removal"] == "none" and measurement["retry_on_slow_observation"] is False, "Observation filtering enabled")
    require(measurement["torch_profiler_traces"] == 0, "Profiler enabled")

    analysis = protocol["analysis_contract"]
    require(analysis["primary_unit"] == "one_complete_168_case_measurement_block", "Primary unit drifted")
    require(analysis["primary_summary"] == "median_of_the_3_preregistered_block_ratios", "Primary summary drifted")
    require(analysis["percentile_method"] == "numpy_percentile_linear", "Percentile method drifted")
    require(analysis["all_raw_observations_retained"] is True, "Raw observations can be dropped")
    require(analysis["formal_R0_denominator_used"] is False and analysis["formal_efficiency_thresholds_evaluated"] is False, "Formal gate imported")

    gate = protocol["performance_hard_gate"]
    require(gate["all_observations_finite_and_strictly_positive"] is True, "Finite/positive gate removed")
    require(gate["timed_observation_rows_required"] == 1008, "Observation count gate drifted")
    require(gate["median_of_3_overall_block_ratios_maximum"] == 0.9, "Overall ratio threshold drifted")
    require(gate["each_overall_block_ratio_must_be_strictly_less_than"] == 1.0, "Block consistency threshold drifted")
    require(gate["aggregate_fast_path_ratio_maximum"] == 0.5, "Fast-path threshold drifted")
    require(gate["aggregate_fallback_ratio_maximum"] == 1.25, "Fallback threshold drifted")
    require(gate["all_conditions_required"] is True and gate["threshold_change_after_result_forbidden"] is True, "Gate conjunction weakened")

    result = protocol["result_classification"]
    require(result["positive_next_step"] == "separate_S2_production_path_shadow_integration_feasibility_protocol_only", "Positive result escalates too far")
    require(result["negative_next_step"] == "freeze_archive_and_stop_S2_while_retaining_S0", "Negative result action drifted")
    for key in ("result_can_authorize_production_change", "result_can_authorize_formal_efficiency_rerun", "result_can_authorize_training"):
        require(result[key] is False, f"Result permission enabled: {key}")

    require(len(protocol["required_future_outputs"]) == 7, "Future output contract drifted")
    permission = protocol["permission_boundary"]
    require(permission["protocol_lock_authorized"] is True, "Protocol lock disabled")
    for key, value in permission.items():
        if key != "protocol_lock_authorized":
            require(value is False, f"Forbidden permission enabled: {key}")


def verify_lineage(parent_lock_dir: Path, result_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    parent_hashes = verify_hashes(parent_lock_dir, EXPECTED_PARENT_LOCK)
    require(verify_manifest(parent_lock_dir) == 6, "S2 parent manifest count drifted")
    result_hashes = verify_hashes(result_dir, EXPECTED_RESULT)
    require(verify_manifest(result_dir) == 6, "S2 result manifest count drifted")

    parent_receipt = json.loads((parent_lock_dir / "protocol_lock_receipt.json").read_text(encoding="utf-8"))
    require(parent_receipt["status"] == "D6A_R1_S2_certified_fast_path_feasibility_protocol_frozen_non_runnable", "S2 parent status drifted")
    require(parent_receipt["equivalence_cases"] == 168 and parent_receipt["certified_fast_path_cases_minimum"] == 96, "S2 parent gates drifted")
    require(parent_receipt["timing_calls"] == parent_receipt["optimizer_steps"] == parent_receipt["D6_cases_accessed"] == 0, "S2 parent boundary drifted")

    receipt = json.loads((result_dir / "s2_artificial_zero_step_receipt.json").read_text(encoding="utf-8"))
    summary = json.loads((result_dir / "s2_artificial_zero_step_summary.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "D6A_R1_S2_certified_fast_path_artificial_zero_step_passed", "S2 result status drifted")
    for key in ("cases", "S0_assignments", "S2_assignments", "slot_to_candidate_exact", "sorted_selected_indices_exact", "hard_assignment_exact", "adjusted_objective_exact", "outputs_finite"):
        require(receipt[key] == 168, f"S2 result semantics drifted: {key}")
    require(receipt["certified_fast_path_cases"] == 96 and receipt["fallback_s0_cases"] == 72, "S2 result routes drifted")
    require(receipt["false_positive_certificates"] == 0 and receipt["all_gates_passed"] is True, "S2 result gate drifted")
    require(receipt["performance_timing_calls"] == receipt["warmup_runs"] == receipt["timed_runs"] == 0, "S2 zero-step timing drifted")
    require(receipt["optimizer_steps"] == receipt["model_updates"] == receipt["D6_cases_accessed"] == 0, "S2 result boundary drifted")
    require(summary["all_gates_passed"] is True, "S2 summary gate drifted")

    routing = read_csv(result_dir / "s2_certification_routing_metrics.csv")
    require(len(routing) == 168, "S2 routing row count drifted")
    route_counts = Counter(row["route"] for row in routing)
    reasons = Counter(row["fallback_reason"] for row in routing if row["route"] == "fallback_s0")
    require(route_counts == Counter({"certified_fast_path": 96, "fallback_s0": 72}), "S2 routing membership drifted")
    require(reasons == Counter({"cutoff_tie_or_near_tie": 32, "global_optimum_not_certified_unique": 40}), "S2 fallback reasons drifted")
    require(all(flag(row, "route_valid") and not flag(row, "false_positive_certificate") for row in routing), "Invalid S2 route")
    return parent_hashes, result_hashes


def build_outputs(protocol: Mapping[str, Any], parent_hashes: Mapping[str, str], result_hashes: Mapping[str, str]) -> dict[str, bytes]:
    outputs = {
        "benchmark_contract.json": canonical_json({
            "candidate_definitions": protocol["candidate_definitions"],
            "pre_timing_correctness_replay": protocol["pre_timing_correctness_replay"],
            "benchmark_design": protocol["benchmark_design"],
            "analysis_contract": protocol["analysis_contract"],
            "performance_hard_gate": protocol["performance_hard_gate"],
            "result_classification": protocol["result_classification"],
        }),
        "benchmark_execution.template.json": canonical_json({
            "runnable": False,
            "separate_execution_authorization_required": True,
            "protocol_id": PROTOCOL_ID,
            "correctness_replay_cases": 168,
            "warmup_calls_total": 28,
            "measurement_blocks": 3,
            "timed_calls_per_candidate": 504,
            "timed_observation_rows": 1008,
            "torch_profiler_traces": 0,
            "optimizer_constructed": False,
            "D6_cases_accessed": 0,
        }),
        "protocol_v1.json": PROTOCOL.read_bytes(),
        "synthetic_suite_binding.json": canonical_json({
            "source": "frozen_S2_positive_zero_step_result",
            "cases": 168,
            "case_order": protocol["scope"]["case_order"],
            "certified_fast_path_cases": 96,
            "fallback_s0_cases": 72,
            "fallback_reasons": protocol["pre_timing_correctness_replay"]["fallback_reasons_required"],
            "result_sha256": dict(result_hashes),
        }),
    }
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "D6A_R1_S2_artificial_performance_benchmark_protocol_frozen_non_runnable",
        "protocol_sha256": sha256_file(PROTOCOL),
        "S2_parent_lock_sha256": dict(parent_hashes),
        "S2_positive_result_sha256": dict(result_hashes),
        "correctness_replay_cases": 168,
        "expected_certified_fast_path_cases": 96,
        "expected_fallback_s0_cases": 72,
        "warmup_calls_planned": 28,
        "measurement_blocks_planned": 3,
        "timed_calls_per_candidate_planned": 504,
        "timed_observation_rows_planned": 1008,
        "warmup_calls_executed": 0,
        "timed_calls_executed": 0,
        "torch_profiler_traces": 0,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        **protocol["permission_boundary"],
        "next_step": protocol["next_step_after_lock"],
    }
    outputs["protocol_lock_receipt.json"] = canonical_json(receipt)
    outputs["protocol_lock_report_zh.md"] = (
        "# Mamba v1.6 D6-A R1 S2 artificial performance benchmark protocol lock\n\n"
        "- Parent：S2 zero-step 168/168 exact，fast/fallback=96/72，false-positive=0。\n"
        "- Timed path：完整 S0 对完整 S2，包含 D2H、certificate、fallback 与输出构造。\n"
        "- Pre-timing gate：先重放全部 168 例正确性和冻结路由；失败时 timed calls 必须为 0。\n"
        "- Warmup：7 个 family anchor x 2 轮 x 2 candidates，共 28 次，不计时。\n"
        "- Measurement：3 blocks x 168 cases x 2 candidates，共 1008 行；每 block 84/84 平衡先后顺序。\n"
        "- Performance gate：overall median block ratio <=0.90；每 block <1.00；fast <=0.50；fallback <=1.25。\n"
        "- 不删除异常值、不重试慢观测、不运行 profiler、不使用 formal R0 denominator。\n"
        "- 当前 warmup/timed/optimizer/D6 access 均为 0；benchmark execution 仍需另行授权。\n"
        "- Production、formal rerun、training、seed-1、D6-B、selection 与 sealed access 均锁定。\n"
    ).encode("utf-8")
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    ).encode("ascii")
    return outputs


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    outputs = dict(outputs)
    if output_dir.exists():
        existing = {
            path.relative_to(output_dir).as_posix(): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        require(existing == outputs, f"Existing S2 benchmark protocol lock drifted: {output_dir}")
        print(f"[locked] existing S2 benchmark protocol lock is byte-identical: {output_dir}")
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
    print(f"[saved] immutable S2 artificial benchmark protocol: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent_lock_dir", type=Path, required=True)
    parser.add_argument("--result_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    parent_hashes, result_hashes = verify_lineage(args.parent_lock_dir.resolve(), args.result_dir.resolve())
    outputs = build_outputs(protocol, parent_hashes, result_hashes)
    write_locked(outputs, args.out_dir.resolve())
    print("[done] D6-A R1 S2 artificial performance benchmark protocol frozen")
    print("[authorized-next] separate S2 artificial performance benchmark execution authorization only")
    print("[locked] benchmark=false production=false formal_rerun=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
