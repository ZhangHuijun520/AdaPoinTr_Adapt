#!/usr/bin/env python3
"""Static safety tests for the D4-A authorization and training pipeline."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> None:
    protocol = json.loads(
        text("docs/mamba_v14_d4a_training_authorization_protocol_v1.json")
    )
    scope = protocol["authorization_scope"]
    training = protocol["training"]
    assert protocol["protocol_id"] == "mamba-v14-d4a-training-authorization-v1"
    assert scope["D4A_head_only_training_authorized"] is True
    assert scope["training_started_by_authorization"] is False
    assert scope["T0_training_authorized"] is False
    assert scope["T1_training_authorized"] is False
    assert scope["T2_training_authorized"] is False
    assert scope["protected_data_access_authorized"] is False
    assert training["epochs"] == 50
    assert training["optimizer_steps_per_fold"] == 1900
    assert training["checkpoint_policy"] == "final_epoch_only"
    assert training["dev_evaluation_count_after_training"] == 1

    authorizer = text("tools/authorize_mamba_v14_d4a_training.py")
    runner = text("tools/run_mamba_v14_d4a_training_fold.py")
    freezer = text("tools/freeze_mamba_v14_d4a_training.py")
    preflight = text("scripts/preflight_mamba_v14_d4a_training.sh")
    launcher = text("scripts/launch_mamba_v14_d4a_training_tmux.sh")
    assert "import torch" not in authorizer
    assert "torch.optim" not in authorizer
    assert "training was not started" in authorizer
    assert 'rows[value].get("d4_fold")' in authorizer
    assert 'rows[value].get("fold")' not in authorizer
    assert '"dev_d4_fold_counts"' in authorizer
    assert runner.index("optimizer.step()") < runner.index("dev_ids = read_case_ids")
    assert "optimizer_steps != 1900" in runner
    assert '"checkpoint_policy": "final_epoch_only"' in runner
    assert "selected_positive > 0" in runner
    assert "hits == 400" in freezer
    assert "automatic" in freezer
    assert "python -u tools/run_mamba_v14_d4a_training_fold.py" not in preflight
    assert "run_mamba_v14_d4a_training.sh" in launcher
    print("[ok] authorization has no training side effect")
    print("[ok] 50-epoch/final-only/one-shot-dev contract is fixed")
    print("[ok] all-case gate cannot automatically start T0/T1/T2")
    print("[locked] selection=false protected=false")


if __name__ == "__main__":
    main()
