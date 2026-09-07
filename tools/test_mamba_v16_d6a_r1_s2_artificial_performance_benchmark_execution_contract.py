#!/usr/bin/env python3
"""Contract tests for S2 artificial benchmark authorization and execution."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZER = ROOT / "tools/authorize_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_execution.py"
PROTOCOL = ROOT / "docs/mamba_v16_d6a_r1_s2_artificial_performance_benchmark_execution_authorization_protocol_v1.json"
PREFLIGHT = ROOT / "tools/preflight_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_execution.py"
RUNNER = ROOT / "tools/run_mamba_v16_d6a_r1_s2_artificial_performance_benchmark.py"


def load_authorizer():
    spec = importlib.util.spec_from_file_location("s2_benchmark_authorizer", AUTHORIZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load S2 benchmark authorizer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def must_reject(authorizer, protocol, message: str) -> None:
    try:
        authorizer.validate_protocol(protocol)
    except RuntimeError:
        return
    raise AssertionError(message)


def main() -> None:
    authorizer = load_authorizer()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    authorizer.validate_protocol(protocol)

    unsafe = copy.deepcopy(protocol)
    unsafe["frozen_parent"]["cases"] = 167
    must_reject(authorizer, unsafe, "A changed S2 parent result was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["implementation_binding"]["S0_or_S2_change_authorized"] = True
    must_reject(authorizer, unsafe, "An S0/S2 implementation change was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["runtime"]["warmup_calls_total"] = 14
    must_reject(authorizer, unsafe, "A shortened warmup was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["runtime"]["timed_observation_rows"] = 1006
    must_reject(authorizer, unsafe, "A shortened measurement was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["runtime"]["CUDA_sync_before_and_after_each_timed_call"] = False
    must_reject(authorizer, unsafe, "Timing without CUDA synchronization was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["runtime"]["outlier_removal"] = "trim"
    must_reject(authorizer, unsafe, "Outlier removal was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["authorization_preflight"]["timed_calls"] = 1
    must_reject(authorizer, unsafe, "A timed preflight was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["performance_gate"]["aggregate_fallback_ratio_maximum"] = 2.0
    must_reject(authorizer, unsafe, "A weakened fallback gate was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["performance_gate"]["formal_R0_denominator_used"] = True
    must_reject(authorizer, unsafe, "The formal R0 denominator was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["result_contract"]["result_can_authorize_training"] = True
    must_reject(authorizer, unsafe, "Automatic training authorization was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["formal_efficiency_rerun_authorized"] = True
    must_reject(authorizer, unsafe, "Formal rerun permission was accepted")

    preflight_source = PREFLIGHT.read_text(encoding="utf-8")
    runner_source = RUNNER.read_text(encoding="utf-8")
    ast.parse(preflight_source, filename=str(PREFLIGHT))
    ast.parse(runner_source, filename=str(RUNNER))
    assert "import time" not in preflight_source
    assert "perf_counter" not in preflight_source
    assert '"warmup_calls": 0' in preflight_source
    assert '"timed_calls": 0' in preflight_source
    assert "time.perf_counter_ns()" in runner_source
    assert "torch.cuda.synchronize" in runner_source
    assert "correctness_replay(cases, device)" in runner_source
    assert "if replay_passed:" in runner_source
    assert "outliers_removed\": 0" in runner_source
    assert "slow_observations_retried\": 0" in runner_source
    assert "torch.profiler" not in runner_source

    print("[ok] frozen parent, source binding and one-execution authorization are fixed")
    print("[ok] zero-count CUDA preflight contains no timing API")
    print("[ok] 168-case replay precedes balanced 28-warmup / 1008-observation timing")
    print("[locked] production=false formal_rerun=false training=false seed1=false D6B=false")


if __name__ == "__main__":
    main()
