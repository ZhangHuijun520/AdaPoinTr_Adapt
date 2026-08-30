#!/usr/bin/env python3
"""Boundary tests for the D4 candidate and training protocol lock."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from lock_mamba_v14_d4_candidate_training_protocol import (
    CANDIDATES,
    EXPECTED,
    FOLDS,
    PROTOCOL_PATH,
    render_files,
    validate_protocol,
    write_locked,
)


ROOT = Path(__file__).resolve().parents[1]


def expect_failure(function, text: str) -> None:
    try:
        function()
    except RuntimeError as exc:
        assert text.lower() in str(exc).lower(), (text, str(exc))
    else:
        raise AssertionError(f"Expected RuntimeError containing {text!r}")


def main() -> None:
    protocol_bytes = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_bytes)
    validate_protocol(protocol)

    lineage = {
        "scientific_protocol": EXPECTED["scientific_protocol"],
        "pd3_result": EXPECTED["pd3_result"],
        "fourfold_protocol": EXPECTED["fourfold_protocol"],
        "fourfold_receipt": EXPECTED["fourfold_receipt"],
        "fourfold_manifest": EXPECTED["fourfold_manifest"],
        "generation_audit_summary": EXPECTED["audit_summary"],
        "generation_audit_manifest": EXPECTED["audit_manifest"],
        "portable_manifest": EXPECTED["portable_manifest"],
    }
    implementations = {
        "protocol_locker": ROOT
        / "tools"
        / "lock_mamba_v14_d4_candidate_training_protocol.py",
        "tests": Path(__file__),
    }
    first = render_files(protocol, protocol_bytes, lineage, implementations)
    second = render_files(protocol, protocol_bytes, lineage, implementations)
    assert first == second

    config_names = sorted(
        name for name in first if name.startswith("configs/")
    )
    assert len(config_names) == 12
    assert {
        name.split("MambaV14D4_")[1].split("_")[0] for name in config_names
    } == set(CANDIDATES)

    for candidate in CANDIDATES:
        for fold in FOLDS:
            name = f"configs/MambaV14D4_{candidate}_fold{fold}_seed0.template.json"
            config = json.loads(first[name])
            execution = config["d4_execution"]
            assert execution["candidate"] == candidate
            assert execution["fold"] == fold
            assert execution["training_authorized"] is False
            assert execution["dev_evaluation_authorized"] is False
            assert execution["selection_authorized"] is False
            assert execution["protected_data_accessed"] is False
            assert config["max_epoch"] == 100
            assert config["total_bs"] == 8
            assert config["save_best_checkpoint"] is False
            model = config["model"]
            assert model["dense_contact_objective"]["enabled"] is False
            proposal = model["high_resolution_rim_proposal"]
            if candidate == "T0":
                assert proposal["enabled"] is False
                assert proposal["head_checkpoint"] is None
            else:
                assert proposal["enabled"] is True
                assert proposal["rim_queries"] == 32
                assert proposal["mandatory_top_score_count"] == 8
                assert proposal["ranked_pool_size"] == 256
                assert proposal["diversified_count"] == 24
                assert proposal["head_trainable"] is False
                assert f"fold{fold}" in proposal["head_checkpoint"]
            support = model["contact_support_preservation"]
            assert support["enabled"] is (candidate == "T2")
            if candidate == "T2":
                assert support["support_points"] == 32
                assert support["ordinary_generated_points"] == 8160
                assert support["normalized_offset_radius"] == 0.02

    d4a = json.loads(first["d4a_feasibility_contract.json"])
    assert d4a["D4A_execution_authorized"] is False
    assert d4a["T0_T1_T2_round_A_authorized"] is False
    selector = d4a["d4a_feasibility"]["selector"]
    assert (
        selector["mandatory_top_score_count"],
        selector["ranked_pool_size"],
        selector["diversified_count"],
    ) == (8, 256, 24)

    receipt = json.loads(first["protocol_lock_receipt.json"])
    assert receipt["non_runnable_template_count"] == 12
    assert receipt["D4A_execution_authorized"] is False
    assert receipt["D4_training_authorized"] is False
    assert receipt["D4_candidate_selection_authorized"] is False
    assert receipt["holdout_authorized"] is False
    assert receipt["protected_data_accessed"] is False
    assert receipt["implementation_and_zero_step_preflight_authorized_next"] is True

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "lock"
        write_locked(first, output)
        write_locked(second, output)
        changed = dict(second)
        changed["protocol_lock_report_zh.md"] += b"drift\n"
        expect_failure(lambda: write_locked(changed, output), "non-identical")

    changed = copy.deepcopy(protocol)
    changed["d4a_feasibility"]["selector"]["ranked_pool_size"] = 512
    expect_failure(lambda: validate_protocol(changed), "feasibility")

    changed = copy.deepcopy(protocol)
    changed["round_a_training_budget"]["epochs_per_training"] = 101
    expect_failure(lambda: validate_protocol(changed), "budget")

    changed = copy.deepcopy(protocol)
    changed["candidates"]["T2"]["ordinary_generated_points"] = 8192
    expect_failure(lambda: validate_protocol(changed), "candidate")

    changed = copy.deepcopy(protocol)
    changed["round_a_hard_gates"]["contact_relevance"][
        "nonfinite_counts_as_event"
    ] = False
    expect_failure(lambda: validate_protocol(changed), "safety")

    changed = copy.deepcopy(protocol)
    changed["lock_effect"]["D4_training_authorized"] = True
    expect_failure(lambda: validate_protocol(changed), "authorize")

    print("[ok] D4-A 8192/13D/top8+FPS24 feasibility contract is immutable")
    print("[ok] T0/T1/T2 budgets, folds, anti-gaming gates, and progression are fixed")
    print("[ok] 12 templates are deterministic and non-runnable")
    print("[locked] D4A=false training=false selection=false protected=false")


if __name__ == "__main__":
    main()
