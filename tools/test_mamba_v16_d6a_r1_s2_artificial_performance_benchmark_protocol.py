#!/usr/bin/env python3
"""Contract tests for the frozen D6-A R1 S2 artificial benchmark protocol."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCKER = ROOT / "tools" / "lock_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_protocol.py"
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_r1_s2_artificial_performance_benchmark_protocol_v1.json"


def load_locker():
    spec = importlib.util.spec_from_file_location("s2_benchmark_protocol_locker", LOCKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load S2 benchmark protocol locker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def must_reject(locker, protocol, message: str) -> None:
    try:
        locker.validate_protocol(protocol)
    except RuntimeError:
        return
    raise AssertionError(message)


def main() -> None:
    locker = load_locker()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    locker.validate_protocol(protocol)

    parent_hashes = dict(locker.EXPECTED_PARENT_LOCK)
    result_hashes = dict(locker.EXPECTED_RESULT)
    outputs = locker.build_outputs(protocol, parent_hashes, result_hashes)
    expected_names = {
        "benchmark_contract.json",
        "benchmark_execution.template.json",
        "files.sha256",
        "protocol_lock_receipt.json",
        "protocol_lock_report_zh.md",
        "protocol_v1.json",
        "synthetic_suite_binding.json",
    }
    assert set(outputs) == expected_names
    receipt = json.loads(outputs["protocol_lock_receipt.json"])
    assert receipt["status"] == "D6A_R1_S2_artificial_performance_benchmark_protocol_frozen_non_runnable"
    assert receipt["warmup_calls_planned"] == 28
    assert receipt["measurement_blocks_planned"] == 3
    assert receipt["timed_calls_per_candidate_planned"] == 504
    assert receipt["timed_observation_rows_planned"] == 1008
    assert receipt["warmup_calls_executed"] == receipt["timed_calls_executed"] == 0
    assert receipt["S2_artificial_performance_benchmark_execution_authorized"] is False
    assert receipt["D6_cases_accessed"] == receipt["optimizer_steps"] == 0

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for name, payload in outputs.items():
            (root / name).write_bytes(payload)
        assert locker.verify_manifest(root) == 6

    unsafe = copy.deepcopy(protocol)
    unsafe["frozen_parent"]["hard_assignment_exact"] = 167
    must_reject(locker, unsafe, "A non-exact S2 parent result was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["frozen_parent"]["certified_fast_path_cases"] = 95
    must_reject(locker, unsafe, "A changed frozen fast-route count was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["scope"]["D6_cases_accessed"] = 1
    must_reject(locker, unsafe, "D6 access was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["candidate_definitions"]["S2"]["timed_boundary"] = "reduced solve only"
    must_reject(locker, unsafe, "A partial S2 timing boundary was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["pre_timing_correctness_replay"]["required_before_any_timed_call"] = False
    must_reject(locker, unsafe, "Timing without correctness replay was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["pre_timing_correctness_replay"]["fallback_reasons_required"]["global_optimum_not_certified_unique"] = 39
    must_reject(locker, unsafe, "Changed frozen fallback routing was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["benchmark_design"]["authorized_now"] = True
    must_reject(locker, unsafe, "Benchmark execution was authorized by protocol lock")

    unsafe = copy.deepcopy(protocol)
    unsafe["benchmark_design"]["CPU_thread_environment"]["OMP_NUM_THREADS"] = 8
    must_reject(locker, unsafe, "Uncontrolled CPU threading was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["benchmark_design"]["warmup"]["rounds"] = 1
    must_reject(locker, unsafe, "Changed warmup schedule was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["benchmark_design"]["measurement"]["blocks"] = 2
    must_reject(locker, unsafe, "Changed measurement block count was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["benchmark_design"]["measurement"]["candidate_first_counts_per_block"]["S0"] = 168
    must_reject(locker, unsafe, "Unbalanced candidate ordering was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["benchmark_design"]["measurement"]["CUDA_synchronize_immediately_after_each_call"] = False
    must_reject(locker, unsafe, "Timing without post-call CUDA synchronization was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["benchmark_design"]["measurement"]["outlier_removal"] = "trim_slowest_1_percent"
    must_reject(locker, unsafe, "Post-hoc outlier removal was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["analysis_contract"]["formal_R0_denominator_used"] = True
    must_reject(locker, unsafe, "Formal R0 denominator was imported")

    unsafe = copy.deepcopy(protocol)
    unsafe["performance_hard_gate"]["median_of_3_overall_block_ratios_maximum"] = 1.0
    must_reject(locker, unsafe, "Weakened overall performance threshold was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["performance_hard_gate"]["aggregate_fallback_ratio_maximum"] = 2.0
    must_reject(locker, unsafe, "Weakened fallback threshold was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["result_classification"]["result_can_authorize_production_change"] = True
    must_reject(locker, unsafe, "Automatic production authorization was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["formal_efficiency_rerun_authorized"] = True
    must_reject(locker, unsafe, "Formal rerun permission was accepted")

    print("[ok] frozen S2 positive result and 168-case pre-timing replay are required")
    print("[ok] balanced 2-round warmup and 3x168 paired timing schedule are fixed")
    print("[ok] overall, fast-path, fallback and block-consistency gates are fixed")
    print("[locked] benchmark=false production=false formal_rerun=false training=false D6=false")


if __name__ == "__main__":
    main()
