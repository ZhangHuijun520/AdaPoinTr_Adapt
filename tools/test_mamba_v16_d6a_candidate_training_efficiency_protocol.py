#!/usr/bin/env python3
"""Static tests for the D6-A efficiency-before-training protocol."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "lock_mamba_v16_d6a_candidate_training_efficiency_protocol.py"
spec = importlib.util.spec_from_file_location("d6_protocol", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def main() -> None:
    protocol = json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
    module.validate_protocol(protocol)
    assert protocol["execution_order"][0] == "separate_efficiency_implementation_and_artificial_zero_step"
    assert protocol["efficiency_gate"]["failure_action"] == "freeze_efficiency_negative_and_stop_before_training"
    assert protocol["seed0_training_budget"]["development_access"] == "one_shot_after_exactly_1900_optimizer_steps"
    weights = protocol["loss_contract"]["R1"]["same_fold_weights"]
    assert list(weights) == ["A", "B", "C", "D"]
    assert all(0.0001 <= value["lambda_support"] <= 10000.0 for value in weights.values())
    assert all(0.0001 <= value["lambda_shape"] <= 10000.0 for value in weights.values())
    print("[ok] R0/R1 seed-0 budget and final-only one-shot-dev contract are fixed")
    print("[ok] artificial efficiency gate precedes every optimizer step")
    print("[ok] same-fold R1 weights and scalar-total-loss restrictions are fixed")
    print("[locked] efficiency_execution=false training=false seed1=false D6B=false confirmation=false")


if __name__ == "__main__":
    main()
