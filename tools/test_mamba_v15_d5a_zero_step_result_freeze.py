#!/usr/bin/env python3
"""Contract tests for the D5-A V0/V1 zero-step result freeze."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/freeze_mamba_v15_d5a_zero_step_result.py"
SPEC = importlib.util.spec_from_file_location("d5a_zero_result", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_receipt():
    receipt = {
        "status": "V0_V1_implementation_zero_step_preflight_passed",
        "folds": 4,
        "train_probe_cases": 4,
        "candidates_per_probe": 2,
        "backward_passes": 8,
        "optimizer_steps": 0,
        "model_updates": 0,
        "dev_cases_accessed": 0,
        "selected_hit_is_observation_only_not_a_gate": True,
        "probe_case_ids": {fold: f"case_{fold}" for fold in MODULE.FOLDS},
    }
    for key in (
        "optimizer_constructed",
        "checkpoint_loaded",
        "checkpoint_written",
        "D5A_seed0_training_authorized",
        "D5A_seed1_training_authorized",
        "development_all_training_authorized",
        "proposal_confirmation_access_authorized",
        "D5B_implementation_authorized",
        "D5B_training_authorized",
        "D5_candidate_selection_authorized",
        "selection_started",
        "proposal_confirmation_accessed",
        "completion_holdout_accessed",
        "official_test_accessed",
        "protected_or_sealed_data_accessed",
    ):
        receipt[key] = False
    return receipt


def make_rows():
    rows = []
    for fold in MODULE.FOLDS:
        for candidate, dimensions in (("V0", 13), ("V1", 27)):
            rows.append(
                {
                    "fold": fold,
                    "case_id": f"case_{fold}",
                    "candidate": candidate,
                    "candidate_count": 8192,
                    "positive_count": 24,
                    "descriptor_dimensions": dimensions,
                    "descriptor_abs_max": 1.0,
                    "logit_abs_max": 0.5,
                    "total_loss": 0.7 if candidate == "V0" else 2.1,
                    "case_balanced_bce": 0.7,
                    "positive_mass_nll": 0.0 if candidate == "V0" else 0.8,
                    "top32_margin": 0.0 if candidate == "V0" else 0.6,
                    "gradient_norm": 1.5,
                    "selected_count": 32,
                    "selected_positive_count_observation_only": 1,
                    "selected_hit_observation_only": 1,
                    "parameter_hash_unchanged": 1,
                    "optimizer_steps": 0,
                    "dev_cases_accessed": 0,
                }
            )
    return rows


def main():
    protocol = MODULE.read_json(MODULE.PROTOCOL_PATH)
    MODULE.validate_protocol(protocol)
    receipt = make_receipt()
    MODULE.validate_zero_receipt(receipt)
    aggregate = MODULE.aggregate_metrics(make_rows())
    assert aggregate["V0"]["descriptor_dimensions"] == 13
    assert aggregate["V1"]["descriptor_dimensions"] == 27
    assert aggregate["V0"]["selected_hit_observation_count"] == 4

    summary = {
        "status": "D5A_V0_V1_zero_step_frozen_complete_training_still_locked",
        "cuda_device_name": "synthetic CUDA device",
        "candidate_aggregates": aggregate,
    }
    report = MODULE.render_report(summary, make_rows()).decode("utf-8")
    assert "optimizer steps：0" in report
    assert "不是 gate" in report
    assert "D5A_seed0_training_authorized=false" in report
    print("[ok] D5-A zero-step result protocol and receipt contracts")
    print("[ok] eight probe rows and non-comparative aggregates are fixed")
    print("[locked] training=false seed1=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
