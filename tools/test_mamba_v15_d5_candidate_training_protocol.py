#!/usr/bin/env python3
"""Boundary tests for the D5 candidate/training protocol lock."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from lock_mamba_v15_d5_candidate_training_protocol import (
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
    lineage = dict(EXPECTED)
    implementations = {
        "protocol_locker": ROOT / "tools" / "lock_mamba_v15_d5_candidate_training_protocol.py",
        "tests": Path(__file__),
    }
    first = render_files(protocol, protocol_bytes, lineage, implementations)
    second = render_files(protocol, protocol_bytes, lineage, implementations)
    assert first == second

    config_names = sorted(name for name in first if name.startswith("configs/"))
    assert len(config_names) == 13
    for candidate in CANDIDATES:
        for fold in FOLDS:
            name = f"configs/MambaV15D5_{candidate}_fold{fold}_seed0.template.json"
            config = json.loads(first[name])
            assert config["status"] == "locked_non_runnable_template"
            assert config["candidate"] == candidate
            assert config["fold"] == fold
            assert config["seed"] == 0
            assert config["training"]["epochs"] == 50
            assert config["training"]["batch_size_cases"] == 8
            assert all(value is False for value in config["authorization"].values())

    for fold in FOLDS:
        name = f"configs/MambaV15D5_V1_fold{fold}_seed1.template.json"
        config = json.loads(first[name])
        assert config["candidate"] == "V1"
        assert config["seed"] == 1
        assert config["authorization"]["training_authorized"] is False

    all_config = json.loads(
        first["configs/MambaV15D5_V1_development_all_seed0.template.json"]
    )
    assert all_config["fold"] is None
    assert all_config["stage"] == "development_all_confirmation_preparation"
    assert all_config["dev_data"] is None
    assert all_config["authorization"]["proposal_confirmation_access_authorized"] is False

    contracts = json.loads(first["d5a_candidate_contracts.json"])
    assert set(contracts["candidates"]) == set(CANDIDATES)
    assert contracts["candidates"]["V1"]["descriptor"]["total_dimensions"] == 27
    assert contracts["candidates"]["V1"]["selector"]["selected_count"] == 32
    assert contracts["candidates"]["V1"]["selector"][
        "fps_or_post_rank_diversification"
    ] is False

    receipt = json.loads(first["protocol_lock_receipt.json"])
    assert receipt["non_runnable_template_count"] == 13
    assert receipt["V0_V1_implementation_and_zero_step_preflight_authorized_next"] is True
    assert receipt["D5A_seed0_training_authorized"] is False
    assert receipt["D5A_seed1_training_authorized"] is False
    assert receipt["proposal_confirmation_access_authorized"] is False
    assert receipt["D5B_implementation_authorized"] is False
    assert receipt["D5B_training_authorized"] is False
    assert receipt["protected_or_sealed_data_accessed"] is False

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "lock"
        write_locked(first, output)
        write_locked(second, output)
        changed_files = dict(second)
        changed_files["protocol_lock_report_zh.md"] += b"drift\n"
        expect_failure(lambda: write_locked(changed_files, output), "non-identical")

    changed = copy.deepcopy(protocol)
    changed["candidates"]["V1"]["descriptor"]["total_dimensions"] = 28
    expect_failure(lambda: validate_protocol(changed), "V1 mechanism")

    changed = copy.deepcopy(protocol)
    changed["candidates"]["V1"]["selector"]["algorithm"] = "fps"
    expect_failure(lambda: validate_protocol(changed), "V1 mechanism")

    changed = copy.deepcopy(protocol)
    changed["candidates"]["V1"]["loss"]["top32_margin_weight"] = 0.5
    expect_failure(lambda: validate_protocol(changed), "V1 mechanism")

    changed = copy.deepcopy(protocol)
    changed["seed1_stability_budget"]["maximum_head_trainings"] = 8
    expect_failure(lambda: validate_protocol(changed), "staged training")

    changed = copy.deepcopy(protocol)
    changed["hard_gates"]["development_seed0"][
        "V1_selected32_contains_positive_400_of_400"
    ] = False
    expect_failure(lambda: validate_protocol(changed), "safety")

    changed = copy.deepcopy(protocol)
    changed["lock_effect"]["D5A_seed0_training_authorized"] = True
    expect_failure(lambda: validate_protocol(changed), "authorize")

    print("[ok] D5 V0 reference and V1 27D context/top32 contracts are immutable")
    print("[ok] seed0, gated seed1, confirmation, and D5-B boundaries are fixed")
    print("[ok] 13 templates are deterministic and non-runnable")
    print("[locked] training=false selection=false sealed=false D5B=false")


if __name__ == "__main__":
    main()
