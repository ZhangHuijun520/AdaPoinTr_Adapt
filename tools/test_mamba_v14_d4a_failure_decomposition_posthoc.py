#!/usr/bin/env python3
"""Static safety tests for the D4-A post-hoc decomposition."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> None:
    protocol = json.loads(
        text("docs/mamba_v14_d4a_failure_decomposition_posthoc_protocol_v1.json")
    )
    permissions = protocol["permissions"]
    runner = text("tools/run_mamba_v14_d4a_failure_decomposition_posthoc.py")
    assert protocol["status"] == "posthoc_observation_only_preregistered"
    assert permissions["post_hoc"] is True
    assert permissions["selection_inert"] is True
    assert permissions["model_updates"] == 0
    assert permissions["optimizer_steps"] == 0
    assert permissions["training_authorized"] is False
    assert permissions["T0_T1_T2_materialization_authorized"] is False
    assert permissions["protected_data_access_authorized"] is False
    assert "optimizer.step" not in runner
    assert ".backward(" not in runner
    assert ".train()" not in runner
    assert "torch.inference_mode()" in runner
    assert "ranking_miss_top256" in runner
    assert "selector_dropped_all_pool_positive" in runner
    assert '"model_updates": 0' in runner
    assert '"optimizer_steps": 0' in runner
    print("[ok] D4-A post-hoc replay is frozen-checkpoint and observation-only")
    print("[ok] top-256, top-8, and FPS-24 decomposition is explicit")
    print("[locked] original gate, T0/T1/T2, selection, and protected data")


if __name__ == "__main__":
    main()
