#!/usr/bin/env python3
"""Contract tests for the D5 development generation archive verifier."""

from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from verify_mamba_v15_d5_development_generation_archive import (  # noqa: E402
    EXPECTED_FAMILIES,
    EXPECTED_FOLDS,
    EXPECTED_STATUS,
    validate_audit_summary,
    validate_generation_receipt,
    validate_transport_receipt,
)


def expect_rejected(function, value) -> None:
    try:
        function(value)
    except RuntimeError:
        return
    raise AssertionError("Permissive archive semantics were accepted")


def main() -> None:
    generation = {
        "status": "generated_training_locked_pending_D5_generation_audit",
        "source_skulls": 100,
        "derived_cases": 400,
        "D5A_model_implementation_authorized": False,
        "D5A_training_authorized": False,
        "D5B_training_authorized": False,
        "candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "completion_holdout_accessed": False,
        "official_test_accessed": False,
    }
    validate_generation_receipt(generation)
    permissive = copy.deepcopy(generation)
    permissive["D5A_training_authorized"] = True
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
        "D5A_model_implementation_authorized": False,
        "D5A_training_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "completion_holdout_accessed": False,
        "official_test_accessed": False,
    }
    validate_audit_summary(audit)
    permissive = copy.deepcopy(audit)
    permissive["all_derived_hashes_verified"] = False
    expect_rejected(validate_audit_summary, permissive)

    transport = {
        "status": "canonical_git_overlay_installed_lock_exact_preflight_passed",
        "protocol_lock_replacement_performed": False,
        "protocol_lock_exact_replay": True,
        "development_sources": 100,
        "planned_cases": 400,
        "generation_started": False,
        "model_implementation_authorized": False,
        "training_authorized": False,
        "selection_started": False,
        "proposal_confirmation_accessed": False,
        "completion_holdout_accessed": False,
    }
    validate_transport_receipt(transport)
    permissive = copy.deepcopy(transport)
    permissive["selection_started"] = True
    expect_rejected(validate_transport_receipt, permissive)

    print("[ok] D5 archive verifier accepts only frozen generation semantics")
    print("[ok] training, selection, incomplete audit and transport drift are rejected")
    print("[locked] source STL and sealed geometry remain excluded")


if __name__ == "__main__":
    main()
