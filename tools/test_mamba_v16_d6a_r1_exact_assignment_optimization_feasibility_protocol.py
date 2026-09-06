#!/usr/bin/env python3
"""Static tests for the D6-A R1 exact-assignment optimization protocol."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "tools"
    / "lock_mamba_v16_d6a_r1_exact_assignment_optimization_feasibility_protocol.py"
)
spec = importlib.util.spec_from_file_location("d6_r1_exact_optimization_protocol", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def must_reject(protocol: dict, message: str) -> None:
    try:
        module.validate_protocol(protocol)
    except RuntimeError:
        return
    raise AssertionError(message)


def main() -> None:
    protocol = json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
    module.validate_protocol(protocol)

    candidates = protocol["candidate_definitions"]
    assert candidates["S0"]["role"] == "frozen exact reference"
    assert candidates["S1"]["row_top_k"] == protocol["scope"]["selector_shape"][0]
    assert candidates["S1"]["cutoff_ties"] == "include_all"
    assert candidates["S1"]["full_D2H_retained"] is True
    assert candidates["S2"]["benchmark_authorized"] is False

    suite = protocol["synthetic_equivalence_suite"]
    assert [item["cases"] for item in suite["families"]] == [64, 32, 8, 16, 16, 16, 16]
    assert sum(item["cases"] for item in suite["families"]) == 168

    fake_repo = {key: value[1] for key, value in module.REPO_PARENTS.items()}
    fake_result = {key: value[1] for key, value in module.PROFILING_RESULT_FILES.items()}
    fake_freeze = {key: value[1] for key, value in module.FREEZE_FILES.items()}
    first = module.build_outputs(protocol, fake_repo, fake_result, fake_freeze)
    second = module.build_outputs(protocol, fake_repo, fake_result, fake_freeze)
    assert first == second
    assert set(first) == {
        "S0_S1_benchmark.template.json",
        "files.sha256",
        "optimization_contract.json",
        "optimization_feasibility_protocol_v1.json",
        "protocol_lock_receipt.json",
        "protocol_lock_report_zh.md",
        "synthetic_equivalence_suite.json",
    }

    unsafe = copy.deepcopy(protocol)
    unsafe["candidate_definitions"]["S1"]["row_top_k"] = 16
    must_reject(unsafe, "Reduced S1 top-k was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["candidate_definitions"]["S1"]["cutoff_ties"] = "drop"
    must_reject(unsafe, "Dropped cutoff ties were accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["equivalence_hard_gate"]["slot_to_candidate_exact"] = "167/168"
    must_reject(unsafe, "Partial slot equivalence was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["equivalence_hard_gate"]["failure_action"] = "continue_to_benchmark"
    must_reject(unsafe, "Benchmark after equivalence failure was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["future_artificial_benchmark"]["CPU_thread_environment"]["OMP_NUM_THREADS"] = 8
    must_reject(unsafe, "Unfrozen CPU thread count was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["formal_gate_feasibility_check"]["unchanged_R1_to_R0_latency_ratio_maximum"] = 2.0
    must_reject(unsafe, "Changed formal threshold was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["S1_implementation_authorized"] = True
    must_reject(unsafe, "S1 implementation permission was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["formal_efficiency_rerun_authorized"] = True
    must_reject(unsafe, "Formal rerun permission was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["scope"]["D6_cases_accessed"] = 1
    must_reject(unsafe, "D6 case access was accepted")

    print("[ok] S0 reference and tie-safe S1 row-top32 union contracts are fixed")
    print("[ok] 168-case exact slot mapping, hard assignment, selected set, and objective gates are fixed")
    print("[ok] engineering speedups cannot change the frozen 1.15 formal gate or authorize training")
    print("[locked] optimization=false formal_rerun=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
