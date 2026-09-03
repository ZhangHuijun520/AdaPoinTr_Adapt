#!/usr/bin/env python3
"""Contract tests for D6-A calibration authorization and execution."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    protocol = json.loads((ROOT / "docs/mamba_v16_d6a_gradient_calibration_execution_authorization_protocol_v1.json").read_text(encoding="utf-8"))
    assert protocol["scope"]["candidate"] == "R1"
    assert protocol["scope"]["folds"] == ["A", "B", "C", "D"]
    assert protocol["scope"]["completed_fold_rerun_authorized"] is False
    assert protocol["measurement"]["batches_per_fold"] == 8
    assert protocol["measurement"]["cases_per_batch"] == 8
    assert protocol["measurement"]["target_support_ratio"] == 0.5
    assert protocol["measurement"]["target_shape_ratio"] == 0.1
    assert protocol["cuda_preflight"]["D6_cases_accessed"] == 0
    assert protocol["cuda_preflight"]["optimizer_steps"] == 0
    assert protocol["execution_effect"]["seed0_training_authorized"] is False

    names = (
        "authorize_mamba_v16_d6a_gradient_calibration_execution.py",
        "verify_mamba_v16_d6a_gradient_calibration_execution_authorization.py",
        "preflight_mamba_v16_d6a_gradient_calibration_execution.py",
        "run_mamba_v16_d6a_gradient_calibration_fold.py",
        "freeze_mamba_v16_d6a_gradient_calibration.py",
    )
    for name in names:
        ast.parse((ROOT / "tools" / name).read_text(encoding="utf-8"), filename=name)
    runner = (ROOT / "tools/run_mamba_v16_d6a_gradient_calibration_fold.py").read_text(encoding="utf-8")
    preflight = (ROOT / "tools/preflight_mamba_v16_d6a_gradient_calibration_execution.py").read_text(encoding="utf-8")
    assert "torch.optim" not in runner
    assert ".backward(" not in runner
    assert "torch.autograd.grad" in runner
    assert "reference_rim_mask" in runner
    assert "median(" in runner
    assert "proposal_confirmation" in runner
    assert "MUG500plusD6Development400" not in preflight
    assert "D6_cases_accessed\": 0" in preflight
    print("[ok] D6-A calibration authorization and 8x8 fold execution are fixed")
    print("[ok] preflight is artificial-only; runner has no optimizer or backward side effect")
    print("[locked] training=false seed1=false confirmation=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
