#!/usr/bin/env python3
"""Static tests for the D6-A R1 S2 certified fast-path protocol."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "lock_mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_protocol.py"
spec = importlib.util.spec_from_file_location("d6_r1_s2_protocol", MODULE_PATH)
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

    suite = protocol["synthetic_equivalence_suite"]
    assert suite["total_cases"] == 168
    assert sum(item["cases"] for item in suite["families"]) == 168
    assert suite["families"][0] == {"name": "independent_normal", "cases": 64, "seed_start": 160610}
    certificate = protocol["certification_contract"]
    assert certificate["row_top_k"] == 32
    assert certificate["cutoff_ties"] == "include_all"
    assert certificate["global_uniqueness"]["edge_exclusion_solves"] == 32
    assert "cutoff_tie_or_near_tie_detected" in certificate["mandatory_fallback_conditions"]
    assert protocol["routing_integrity_gate"]["all_fallback_is_a_failure"] is True

    fake_repo = {key: value[1] for key, value in module.REPO_PARENTS.items()}
    fake_parent = dict(module.CANONICAL_PARENT)
    first = module.build_outputs(protocol, fake_repo, fake_parent)
    second = module.build_outputs(protocol, fake_repo, fake_parent)
    assert first == second
    assert set(first) == {
        "S0_S2_zero_step.template.json",
        "certified_fast_path_contract.json",
        "files.sha256",
        "protocol_lock_receipt.json",
        "protocol_lock_report_zh.md",
        "protocol_v1.json",
        "synthetic_equivalence_suite.json",
    }

    unsafe = copy.deepcopy(protocol)
    unsafe["candidate_definitions"]["S2"]["fallback"] = "return_uncertified_reduced_output"
    must_reject(unsafe, "Uncertified reduced output was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["certification_contract"]["cutoff_ties"] = "drop"
    must_reject(unsafe, "Dropped cutoff ties were accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["certification_contract"]["global_uniqueness"]["edge_exclusion_solves"] = 1
    must_reject(unsafe, "Incomplete second-best search was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["equivalence_hard_gate"]["slot_to_candidate_exact"] = "167/168"
    must_reject(unsafe, "Partial slot equivalence was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["equivalence_hard_gate"]["comparison_reference"] = "reuse_S2_fallback"
    must_reject(unsafe, "Non-independent S0 comparison was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["routing_integrity_gate"]["certified_fast_path_cases_minimum"] = 0
    must_reject(unsafe, "All-fallback loophole was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["routing_integrity_gate"]["false_positive_certificates_allowed"] = 1
    must_reject(unsafe, "False-positive certificate was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["artificial_zero_step"]["timed_runs"] = 1
    must_reject(unsafe, "Timing during zero-step was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["S2_shadow_implementation_authorized"] = True
    must_reject(unsafe, "S2 implementation permission was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["permission_boundary"]["formal_efficiency_rerun_authorized"] = True
    must_reject(unsafe, "Formal rerun permission was accepted")

    unsafe = copy.deepcopy(protocol)
    unsafe["scope"]["D6_cases_accessed"] = 1
    must_reject(unsafe, "D6 access was accepted")

    print("[ok] S2 cutoff and 32-edge-exclusion uniqueness certificates are fixed")
    print("[ok] uncertified tie/near-tie cases must execute and return complete S0")
    print("[ok] 168/168 exact outputs and >=96 certified fast-path cases are required")
    print("[locked] timing=false benchmark=false production=false training=false seed1=false D6B=false")


if __name__ == "__main__":
    main()
