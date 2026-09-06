#!/usr/bin/env python3
"""Contract and representative tests for the isolated S2 zero-step."""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZER = ROOT / "tools/authorize_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py"
spec = importlib.util.spec_from_file_location("d6_s2_authorizer", AUTHORIZER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

PREFLIGHT = ROOT / "tools/preflight_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py"
preflight_spec = importlib.util.spec_from_file_location("d6_s2_preflight", PREFLIGHT)
preflight_module = importlib.util.module_from_spec(preflight_spec)
assert preflight_spec.loader is not None
preflight_spec.loader.exec_module(preflight_module)

from utils.mamba_d6a_r1_s1_exact_assignment import frozen_reference_diagnostics  # noqa: E402
from utils.mamba_d6a_r1_s2_certified_fast_path import (  # noqa: E402
    GUARD_MULTIPLIER,
    s2_certified_fast_path_assignment,
)


def must_reject(protocol: dict, message: str) -> None:
    try:
        module.validate_protocol(protocol)
    except RuntimeError:
        return
    raise AssertionError(message)


def main() -> None:
    protocol = json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
    module.validate_protocol(protocol)
    assert GUARD_MULTIPLIER == 256.0
    permission = protocol["permission_boundary"]
    assert permission["S2_isolated_shadow_implementation_authorized"] is True
    assert permission["S2_artificial_zero_step_authorized"] is True
    for key in (
        "S2_artificial_performance_benchmark_authorized",
        "S1_rerun_authorized",
        "R1_production_implementation_change_authorized",
        "formal_efficiency_rerun_authorized",
        "seed0_training_authorized",
        "seed1_training_authorized",
        "D6B_authorized",
        "protected_or_sealed_data_accessed",
    ):
        assert permission[key] is False

    unsafe = copy.deepcopy(protocol)
    unsafe["implementation_contract"]["guard_multiplier"] = 0.0
    must_reject(unsafe, "Disabled numerical guard was accepted")
    unsafe = copy.deepcopy(protocol)
    unsafe["implementation_contract"]["uncertified_route"] = "return_reduced"
    must_reject(unsafe, "Uncertified reduced output was accepted")
    unsafe = copy.deepcopy(protocol)
    unsafe["artificial_zero_step"]["certified_fast_path_cases_minimum"] = 0
    must_reject(unsafe, "All-fallback routing gate was accepted")
    unsafe = copy.deepcopy(protocol)
    unsafe["artificial_zero_step"]["timed_runs"] = 1
    must_reject(unsafe, "Timed execution was accepted")
    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["R1_production_implementation_change_authorized"] = True
    must_reject(unsafe, "Production R1 mutation was accepted")
    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["seed0_training_authorized"] = True
    must_reject(unsafe, "Training escalation was accepted")

    families = [
        "independent_normal",
        "collision_heavy_shared_candidate_bias",
        "identical_rows",
        "exact_tie_groups",
        "near_ties_float32",
        "shared_top32_adversarial",
        "top32_cutoff_ties",
    ]
    seed_starts = [160610, 260610, 360610, 460610, 560610, 660610, 760610]
    routes: dict[str, str] = {}
    for family, seed in zip(families, seed_starts):
        logits = torch.from_numpy(preflight_module.artificial_scores(family, seed)).unsqueeze(0)
        s0_hard, s0_selected, s0_slots, s0_objective = frozen_reference_diagnostics(logits)
        s2 = s2_certified_fast_path_assignment(logits)
        assert torch.equal(s0_slots, s2.slot_to_candidate)
        assert torch.equal(s0_selected, s2.selected_indices)
        assert torch.equal(s0_hard, s2.hard_assignment)
        assert s0_objective == s2.adjusted_objective
        assert s2.route in {"certified_fast_path", "fallback_s0"}
        if s2.route == "fallback_s0":
            assert s2.fallback_reason != "none"
        routes[family] = s2.route
    assert routes["independent_normal"] == "certified_fast_path"
    assert routes["collision_heavy_shared_candidate_bias"] == "certified_fast_path"
    assert routes["top32_cutoff_ties"] == "fallback_s0"

    preflight_source = inspect.getsource(preflight_module)
    for forbidden in ("perf_counter", "timeit", "torch.profiler"):
        assert forbidden not in preflight_source
    print("[ok] S2 representative families preserve exact S0 slot, selected, hard and objective outputs")
    print("[ok] normal/collision cases certify while cutoff ties execute complete S0 fallback")
    print("[locked] timing=false benchmark=false production=false formal_rerun=false training=false D6=false")


if __name__ == "__main__":
    main()
