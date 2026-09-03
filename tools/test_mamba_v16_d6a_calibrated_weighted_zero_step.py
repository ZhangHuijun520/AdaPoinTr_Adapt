#!/usr/bin/env python3
"""Static contracts for the D6-A calibrated weighted zero-step."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    protocol = json.loads(
        (ROOT / "docs/mamba_v16_d6a_calibrated_weighted_zero_step_protocol_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert protocol["candidate"] == "R1"
    assert protocol["seed"] == 0
    assert protocol["folds"] == ["A", "B", "C", "D"]
    assert protocol["input"]["cases_per_fold"] == 8
    assert protocol["input"]["total_case_slots"] == 32
    assert protocol["loss"]["weight_binding"] == "same_fold_only"
    assert protocol["measurements"]["cosines_are_observation_only_not_a_gate"] is True
    gates = protocol["hard_gates"]
    assert gates["optimizer_constructed"] is False
    assert gates["optimizer_steps"] == 0
    assert gates["model_updates"] == 0
    assert gates["checkpoint_written"] is False
    permissions = protocol["permissions_after_pass"]
    assert permissions["D6A_seed0_training_authorized"] is False
    assert permissions["D6A_seed1_training_authorized"] is False
    assert permissions["D6B_authorized"] is False
    runner = (ROOT / "tools/preflight_mamba_v16_d6a_calibrated_weighted_zero_step.py").read_text(
        encoding="utf-8"
    )
    assert "torch.optim" not in runner
    assert ".backward(" not in runner
    assert ".step(" not in runner
    assert "torch.autograd.grad" in runner
    print("[ok] same-fold calibrated weighted-loss zero-step contract is fixed")
    print("[ok] gradient cosines are observation-only and cannot authorize training")
    print("[locked] optimizer=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()

