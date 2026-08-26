#!/usr/bin/env python3
"""Static and arithmetic contract checks for S1 gradient calibration."""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    protocol = json.loads(
        (ROOT / "docs/mamba_v13_d3_s1_gradient_ratio_calibration_amendment_v1.json")
        .read_text(encoding="utf-8")
    )
    data = protocol["data_boundary"]
    model = protocol["model_state"]
    gradient = protocol["gradient_measurement"]
    permission = protocol["post_completion_permissions"]
    assert protocol["status"] == "preregistered_before_s1_calibration"
    assert data["allowed_partition"] == "development fold training subset only"
    assert data["batches_per_fold"] == 8 and data["batch_size"] == 8
    assert data["development_fold_evaluation_allowed"] is False
    assert data["locked_holdout_allowed"] is False
    assert model["optimizer_constructed"] is False and model["optimizer_steps"] == 0
    assert model["mamba_adapter_alpha_scale"] == 0.0
    assert gradient["target_ratio"] == 0.075
    assert gradient["clipping_allowed"] is False
    assert permission["S1_training_authorized_by_calibration_receipt"] is False
    assert permission["S2_calibration_authorized"] is False
    assert permission["S2_full_training_authorized"] is False
    assert permission["holdout_authorized"] is False
    assert permission["selection_started"] is False

    runner_path = ROOT / "tools/run_mamba_v13_d3_s1_calibration_fold.py"
    runner = runner_path.read_text(encoding="utf-8")
    tree = ast.parse(runner)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    forbidden_steps = [
        node for node in calls
        if isinstance(node.func, ast.Attribute) and node.func.attr == "step"
    ]
    assert not forbidden_steps
    assert "builder.load_model" not in runner
    assert "config.dataset.val" not in runner
    assert "build_optimizer" not in runner
    assert "model.set_mamba_adapter_scale(0.0)" in runner
    assert "range(BATCHES)" in runner
    assert "dense_contact_safety_loss" in runner
    assert "value.reshape(-1).view(torch.uint8)" in runner
    assert 'parser.add_argument("--hotfix_dir"' in runner
    assert "pre_batch_scalar_tensor_hash_repair_authorized" in runner
    assert "tensor_hash_hotfix_receipt" in runner
    assert runner.index("state_before = tensor_hash") < runner.index(
        "iterator = iter(loader)"
    )

    hotfix_authorizer = (
        ROOT / "tools/authorize_mamba_v13_d3_s1_calibration_hotfix1.py"
    ).read_text(encoding="utf-8")
    assert 'parser.add_argument("--failed_master_log"' in hotfix_authorizer
    assert 'rglob("calibration_receipt.json")' in hotfix_authorizer
    assert "before_data_iterator_creation" in hotfix_authorizer
    assert "batches_consumed_before_failure\": 0" in hotfix_authorizer
    assert '"Traceback (most recent call last):"' in hotfix_authorizer
    assert '"[tmux] calibration exit status: 1"' not in hotfix_authorizer
    assert "missing_fragments" in hotfix_authorizer
    assert "if output.exists():" in hotfix_authorizer
    assert "old_runner_sha == repaired_runner_sha" in hotfix_authorizer

    prepare = (
        ROOT / "scripts/prepare_mamba_v13_d3_s1_calibration.sh"
    ).read_text(encoding="utf-8")
    assert "the hotfix must not regenerate or replace base authorization" in prepare
    assert "authorize_mamba_v13_d3_s1_calibration_hotfix1.py" in prepare
    assert "python tools/authorize_mamba_v13_d3_s1_calibration.py" not in prepare

    authorizer = (
        ROOT / "tools/authorize_mamba_v13_d3_s1_calibration.py"
    ).read_text(encoding="utf-8")
    negative_freezer = (
        ROOT / "tools/freeze_mamba_v13_d3_s2_feasibility_negative.py"
    ).read_text(encoding="utf-8")
    frozen_negative_status = (
        "frozen_negative_high_hit_rate_failed_all_case_safety_gate"
    )
    assert frozen_negative_status in authorizer
    assert frozen_negative_status in negative_freezer
    assert "allowed_later_takeover" in authorizer
    assert "later_bound.get(relative) == current" in authorizer
    assert "Unfrozen implementation drift" in authorizer

    ratios = np.asarray([1.0, 4.0, 2.0, 8.0, 3.0, 7.0, 5.0, 6.0])
    median = float(np.median(ratios))
    assert median == 4.5
    assert math.isclose(0.075 / median, 1.0 / 60.0, rel_tol=1e-15)

    sequence = (ROOT / "scripts/run_mamba_v13_d3_s1_calibration.sh").read_text()
    assert "main.py" not in sequence
    assert "evaluate_skullfix" not in sequence
    assert "recalibrate_skullfix" not in sequence
    assert "run_mamba_v13_d3_s2" not in sequence.lower()
    assert "freeze_mamba_v13_d3_s1_calibration.py" in sequence

    print("[ok] S1 calibration is fold-training-only and consumes exactly 8x8 slots")
    print("[ok] gradient median and 0.075/raw-ratio weight are fixed")
    print("[ok] no optimizer step, checkpoint load, dev evaluation, or automatic training")
    print("[locked] S2=false holdout=false selection=false")


if __name__ == "__main__":
    main()
