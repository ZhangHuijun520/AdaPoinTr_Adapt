#!/usr/bin/env python3
"""Contract tests for D6-A R1 latency profiling authorization and execution."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/authorize_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py"
spec = importlib.util.spec_from_file_location("d6_r1_profile_auth", MODULE_PATH)
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
    runtime = protocol["runtime"]
    assert runtime["candidate_order"] == ["R1"]
    assert runtime["blocks"] == 3
    assert runtime["warmup_runs_per_block"] == 5
    assert runtime["timed_runs_per_block"] == 20
    assert runtime["total_timed_observations"] == 60
    assert runtime["torch_profiler_schedule"] == {
        "wait": 1, "warmup": 1, "active": 5, "repeat": 1
    }

    unsafe = copy.deepcopy(protocol)
    unsafe["runtime"]["candidate_order"] = ["R0", "R1"]
    must_reject(unsafe, "R0 gate rerun was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["authorization_preflight"]["timed_observations"] = 1
    must_reject(unsafe, "Timed preflight was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["seed0_training_authorized"] = True
    must_reject(unsafe, "Training permission escalation was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["result_contract"]["dominant_share_threshold"] = 0.25
    must_reject(unsafe, "Attribution threshold drift was accepted")

    profiler = (ROOT / "utils/mamba_d6a_r1_latency_profiler.py").read_text(encoding="utf-8")
    preflight = (
        ROOT / "tools/preflight_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py"
    ).read_text(encoding="utf-8")
    runner = (
        ROOT / "tools/run_mamba_v16_d6a_r1_latency_posthoc_profiling.py"
    ).read_text(encoding="utf-8")
    assert "linear_sum_assignment" in profiler
    assert "slot_logits_d2h_float64_numpy_ms" in profiler
    assert "torch.profiler.profile" in profiler
    assert "profile_r1(model, descriptors, trace_tmp)" in runner
    assert "profile_r1(" not in preflight
    assert '"profiling_blocks": 0' in preflight
    assert '"timed_observations": 0' in preflight
    assert '"torch_profiler_traces": 0' in preflight
    assert "proposal_confirmation" in preflight
    assert "proposal_confirmation" in runner
    for source in (profiler, preflight, runner):
        assert "optimizer.step" not in source
        assert "torch.optim" not in source
        assert "MUG500plusD6Development400" not in source

    print("[ok] R1-only 3x20 profiling and fixed torch trace contracts are fixed")
    print("[ok] zero-count preflight cannot enter timed loops or profiler trace")
    print("[ok] formal rerun, optimizer, D6 data, optimization, and training remain forbidden")
    print("[locked] execution not started; training=false seed1=false D6B=false confirmation=false")


if __name__ == "__main__":
    main()
