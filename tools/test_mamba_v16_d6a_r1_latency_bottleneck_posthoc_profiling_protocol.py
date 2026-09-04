#!/usr/bin/env python3
"""Static contract tests for the D6-A R1 latency profiling protocol."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "lock_mamba_v16_d6a_r1_latency_bottleneck_posthoc_profiling_protocol.py"
spec = importlib.util.spec_from_file_location("d6_r1_latency_protocol", MODULE_PATH)
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

    passes = {item["name"]: item for item in protocol["profiling_passes"]}
    assignment = passes["global_assignment_decomposition"]["segments"]
    assert "slot_logits_d2h_float64_numpy" in assignment
    assert "scipy_linear_sum_assignment_cpu" in assignment
    assert "selected_indices_h2d" in assignment
    assert protocol["required_outputs"][-1] == "files.sha256"

    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["posthoc_profiling_execution_authorized"] = True
    must_reject(unsafe, "Execution permission escalation was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["scope"]["development_cases_accessed"] = 1
    must_reject(unsafe, "Development access was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["execution_contract"]["optimizer_steps"] = 1
    must_reject(unsafe, "Optimizer step was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["predeclared_attribution"]["dominant_threshold"] = 0.25
    must_reject(unsafe, "Post-observation attribution change was accepted")

    print("[ok] R1-only exact-path, assignment decomposition, and trace contracts are fixed")
    print("[ok] 3x20 timing observations and 50% descriptive attribution are fixed")
    print("[ok] development access, formal rerun, optimization, and permission escalation fail")
    print("[locked] profiling=false training=false seed1=false D6B=false confirmation=false")


if __name__ == "__main__":
    main()
