#!/usr/bin/env python3
"""Static contract checks for S1 receipt-bound config materialization."""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    protocol = json.loads(
        (ROOT / "docs/mamba_v13_d3_s1_runtime_config_materialization_protocol_v1.json")
        .read_text(encoding="utf-8")
    )
    assert protocol["status"] == "preregistered_after_calibration_before_materialization"
    assert protocol["transformation"]["only_scientific_value_changed"] == (
        "model.dense_contact_objective.weight"
    )
    assert protocol["transformation"]["rounding_clipping_or_manual_adjustment"] is False
    state = protocol["materialized_config_state"]
    assert state["training_authorized"] is False
    assert state["holdout_authorized"] is False
    assert state["S2_authorized"] is False
    assert state["selection_started"] is False

    tool = (
        ROOT / "tools/materialize_mamba_v13_d3_s1_seed0_runtime_configs.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(tool)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    forbidden = [
        node for node in calls
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"step", "backward"}
    ]
    assert not forbidden
    assert "main.py" not in tool
    assert "builder.load_model" not in tool
    assert 'dense["weight"] = weight' in tool
    assert '"training_authorized": False' in tool
    assert '"holdout_authorized": False' in tool
    assert "TARGET_RATIO / ratio" in tool
    assert "rel_tol=1e-14" in tool

    weights = {
        "A": (464.0803776614586, 0.0001616099357140061),
        "B": (465.9677559959042, 0.00016095534301446222),
        "C": (462.2914591689445, 0.00016223531391825093),
        "D": (472.7584056921278, 0.00015864339818601108),
    }
    for ratio, weight in weights.values():
        assert math.isclose(weight, 0.075 / ratio, rel_tol=1e-14, abs_tol=0.0)

    script = (
        ROOT / "scripts/materialize_mamba_v13_d3_s1_seed0_configs.sh"
    ).read_text(encoding="utf-8")
    assert "run_mamba_v13_d3_s1" not in script
    assert "launch_mamba_v13_d3_s1" not in script
    assert "training authorization remains separate" in script
    print("[ok] S1 materialization changes only the same-fold calibrated weight")
    print("[ok] exact completion-receipt weights satisfy 0.075/raw_ratio")
    print("[locked] no training, S2, holdout, or selection entry point")


if __name__ == "__main__":
    main()
