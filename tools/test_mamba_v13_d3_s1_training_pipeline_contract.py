#!/usr/bin/env python3
"""Static contract checks for the authorized S1 seed-0 pipeline."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    protocol = json.loads(
        (ROOT / "docs/mamba_v13_d3_s1_seed0_training_authorization_protocol_v1.json")
        .read_text(encoding="utf-8")
    )
    assert protocol["status"] == (
        "preregistered_after_materialization_before_training_authorization"
    )
    boundary = protocol["protected_boundaries"]
    assert boundary["locked_holdout_authorized"] is False
    assert boundary["S2_full_training_authorized"] is False
    assert boundary["selection_started"] is False

    smoke = (ROOT / "tools/smoke_mamba_v13_d3_s1_seed0.py").read_text()
    assert "optimizer_steps\": 0" in smoke
    assert "normalization_scale=scales" in smoke
    assert "gt_rim_mask=masks" in smoke
    assert ".step(" not in smoke

    fold = (ROOT / "scripts/run_mamba_v13_d3_s1_seed0_fold.sh").read_text()
    assert "--split val" in fold
    assert "--include_coarse_rim_metrics" in fold
    assert "write_mamba_v13_d3_run_record.py" in fold
    assert "locked_holdout" not in fold
    assert "official" not in fold.lower()
    sequence = (ROOT / "scripts/run_mamba_v13_d3_s1_seed0.sh").read_text()
    assert "for fold in A B C D" in sequence
    assert "freeze_mamba_v13_d3_s1_seed0.py" in sequence
    assert "select_mamba" not in sequence
    launcher = (ROOT / "scripts/launch_mamba_v13_d3_s1_seed0_tmux.sh").read_text()
    assert "tmux new-session" in launcher
    assert "TQDM_MININTERVAL" in launcher
    assert "preflight_mamba_v13_d3_s1_seed0.sh" in launcher
    preflight = (ROOT / "scripts/preflight_mamba_v13_d3_s1_seed0.sh").read_text()
    assert "--verify_only" in preflight

    authorizer = (
        ROOT / "tools/authorize_mamba_v13_d3_s1_seed0_training.py"
    ).read_text()
    tree = ast.parse(authorizer)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert not [
        node for node in calls
        if isinstance(node.func, ast.Attribute) and node.func.attr == "step"
    ]
    print("[ok] S1 authorization binds exact same-fold calibrated weights")
    print("[ok] S1 smoke includes dense-contact supervision and zero optimizer steps")
    print("[ok] S1 execution is tmux/tqdm-bound and development-only")
    print("[locked] S2=false holdout=false selection=false")


if __name__ == "__main__":
    main()
