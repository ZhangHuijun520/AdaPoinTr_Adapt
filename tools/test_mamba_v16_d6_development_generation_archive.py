#!/usr/bin/env python3
"""Contract tests for the D6 development generation archive verifier."""

from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from verify_mamba_v16_d6_development_generation_archive import (  # noqa: E402
    EXPECTED_FAMILIES,
    EXPECTED_FOLDS,
    EXPECTED_STATUS,
    validate_audit_summary,
    validate_generation_receipt,
)


def expect_rejected(function, value) -> None:
    try:
        function(value)
    except RuntimeError:
        return
    raise AssertionError("Permissive archive semantics were accepted")


def main() -> None:
    generation = {
        "status": "generated_training_locked_pending_D6_generation_audit",
        "source_skulls": 100,
        "derived_cases": 400,
        "D6A_R0_R1_implementation_frozen": True,
        "D6_gradient_calibration_authorized": False,
        "D6A_training_authorized": False,
        "D6_seed1_authorized": False,
        "D6B_training_authorized": False,
        "candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "official_test_accessed": False,
    }
    validate_generation_receipt(generation)
    permissive = copy.deepcopy(generation)
    permissive["D6_gradient_calibration_authorized"] = True
    expect_rejected(validate_generation_receipt, permissive)

    audit = {
        "status": EXPECTED_STATUS,
        "source_skulls": 100,
        "derived_cases": 400,
        "fold_case_counts": EXPECTED_FOLDS,
        "defect_families": sorted(EXPECTED_FAMILIES),
        "source_assets_rehashed": True,
        "all_derived_hashes_verified": True,
        "all_derived_hashes_unique": True,
        "manifest_cases_bijective": True,
        "all_npz_contracts_verified": True,
        "all_geometry_gates_verified": True,
        "all_four_family_bindings_verified": True,
        "all_source_fold_bindings_verified": True,
        "portable_paths": True,
        "D6A_R0_R1_implementation_frozen": True,
        "D6_gradient_calibration_authorized": False,
        "D6A_training_authorized": False,
        "D6_seed1_authorized": False,
        "D6B_training_authorized": False,
        "D6_candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "official_test_accessed": False,
        "next_step": "freeze_a_separate_D6_gradient_calibration_protocol",
    }
    validate_audit_summary(audit)
    permissive = copy.deepcopy(audit)
    permissive["all_derived_hashes_verified"] = False
    expect_rejected(validate_audit_summary, permissive)
    permissive = copy.deepcopy(audit)
    permissive["D6_seed1_authorized"] = True
    expect_rejected(validate_audit_summary, permissive)

    print("[ok] D6 archive verifier accepts only frozen generation semantics")
    print("[ok] calibration, training, seed1, D6B and incomplete audit are rejected")
    print("[locked] source STL, confirmation geometry and checkpoints stay excluded")


if __name__ == "__main__":
    main()
