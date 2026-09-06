#!/usr/bin/env python3
"""Contract and representative equivalence tests for the isolated S1 zero-step."""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZER = ROOT / "tools/authorize_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py"
spec = importlib.util.spec_from_file_location("d6_s1_authorizer", AUTHORIZER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

PREFLIGHT = ROOT / "tools/preflight_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py"
preflight_spec = importlib.util.spec_from_file_location("d6_s1_preflight", PREFLIGHT)
preflight_module = importlib.util.module_from_spec(preflight_spec)
assert preflight_spec.loader is not None
preflight_spec.loader.exec_module(preflight_module)
artificial_scores = preflight_module.artificial_scores
from utils.mamba_d6a_r1_s1_exact_assignment import (  # noqa: E402
    frozen_reference_diagnostics,
    s1_exact_reduced_assignment,
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
    permission = protocol["permission_boundary"]
    assert permission["S1_isolated_implementation_authorized"] is True
    assert permission["S1_artificial_zero_step_authorized"] is True
    for key in (
        "S1_artificial_performance_benchmark_authorized",
        "S2_implementation_authorized",
        "R1_production_implementation_change_authorized",
        "formal_efficiency_rerun_authorized",
        "seed0_training_authorized",
        "seed1_training_authorized",
        "D6B_authorized",
        "protected_or_sealed_data_accessed",
    ):
        assert permission[key] is False

    unsafe = copy.deepcopy(protocol)
    unsafe["implementation_contract"]["cutoff_ties"] = "drop"
    must_reject(unsafe, "Dropped cutoff ties were accepted")
    unsafe = copy.deepcopy(protocol)
    unsafe["artificial_zero_step"]["timed_runs"] = 1
    must_reject(unsafe, "Timed execution was accepted")
    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["R1_production_implementation_change_authorized"] = True
    must_reject(unsafe, "Production R1 mutation was accepted")
    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["seed0_training_authorized"] = True
    must_reject(unsafe, "Training escalation was accepted")

    families = [item["name"] for item in protocol.get("synthetic_equivalence_suite", {}).get("families", [])]
    if not families:
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
    exact_cases = 0
    detected_mismatches = 0
    for family, seed in zip(families, seed_starts):
        logits = torch.from_numpy(artificial_scores(family, seed)).unsqueeze(0)
        s0_hard, s0_selected, s0_slots, s0_objective = frozen_reference_diagnostics(logits)
        s1 = s1_exact_reduced_assignment(logits)
        slot_exact = torch.equal(s0_slots, s1.slot_to_candidate)
        hard_exact = torch.equal(s0_hard, s1.hard_assignment)
        exact_cases += int(slot_exact and hard_exact and s0_objective == s1.adjusted_objective)
        detected_mismatches += int(not slot_exact)
        assert torch.equal(s0_selected, s1.selected_indices)
        assert np.isin(s0_slots.numpy(), s1.union_columns).all()
    assert exact_cases < 7
    assert detected_mismatches > 0

    preflight_source = inspect.getsource(preflight_module)
    for forbidden in ("perf_counter", "timeit", "torch.profiler"):
        assert forbidden not in preflight_source
    print("[ok] isolated S1 preserves the frozen epsilon, cutoff-tie and exact SciPy contracts")
    print("[ok] representative adversarial families expose tie-resolution mapping mismatch")
    print("[locked] timing=false production=false formal_rerun=false training=false D6=false")


if __name__ == "__main__":
    main()
