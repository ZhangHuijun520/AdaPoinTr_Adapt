#!/usr/bin/env python3
"""Contract tests for D5-A V0/V1 seed-0 authorization and training pipeline."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile

try:
    import torch
except ModuleNotFoundError:  # Local archive/Git hosts may not carry the CUDA env.
    torch = None


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROTOCOL = ROOT / "docs/mamba_v15_d5a_seed0_training_authorization_protocol_v1.json"
AUTHORIZER = ROOT / "tools/authorize_mamba_v15_d5a_seed0_training.py"
RUNNER = ROOT / "tools/run_mamba_v15_d5a_seed0_training_fold.py"
FREEZER = ROOT / "tools/freeze_mamba_v15_d5a_seed0_training.py"
AUTH_SCRIPT = ROOT / "scripts/authorize_mamba_v15_d5a_seed0_training.sh"
PREFLIGHT_SCRIPT = ROOT / "scripts/preflight_mamba_v15_d5a_seed0_training.sh"
RUN_SCRIPT = ROOT / "scripts/run_mamba_v15_d5a_seed0_training.sh"
LAUNCH_SCRIPT = ROOT / "scripts/launch_mamba_v15_d5a_seed0_training_tmux.sh"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_fourfold(root: Path) -> tuple[dict[str, dict], list[str]]:
    defects = (
        "ellipsoid_large", "ellipsoid_medium", "ellipsoid_small", "irregular_medium"
    )
    folds = "ABCD"
    rows: dict[str, dict] = {}
    fold_cases = {fold: [] for fold in folds}
    all_cases = []
    for index in range(1, 101):
        source = f"A{index:04d}"
        fold = folds[(index - 1) % 4]
        for defect in defects:
            case_id = f"mug500plus__{source}__{defect}"
            all_cases.append(case_id)
            fold_cases[fold].append(case_id)
            rows[case_id] = {"case_id": case_id, "d5_fold": fold}
    for fold in folds:
        dev = sorted(fold_cases[fold])
        train = sorted(set(all_cases) - set(dev))
        (root / f"fold{fold}_dev_case_ids.txt").write_text(
            "\n".join(dev) + "\n", encoding="utf-8"
        )
        (root / f"fold{fold}_train_case_ids.txt").write_text(
            "\n".join(train) + "\n", encoding="utf-8"
        )
    return rows, all_cases


def main() -> None:
    authorizer = load_module("d5a_authorizer_contract", AUTHORIZER)
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    authorizer.validate_protocol(protocol)
    assert protocol["authorization_scope"]["training_order"] == [
        "V0_A", "V0_B", "V0_C", "V0_D",
        "V1_A", "V1_B", "V1_C", "V1_D",
    ]
    assert protocol["training"]["maximum_optimizer_steps_total"] == 15200
    assert protocol["hard_gate"]["V1_selected32_contains_positive_400_of_400"]
    assert protocol["hard_gate"]["automatic_seed1_execution"] is False

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        rows, all_cases = synthetic_fourfold(root)
        payloads, bindings = authorizer.runtime_configs(root, rows)
        assert len(all_cases) == 400
        assert len(payloads) == 8
        assert list(bindings) == [
            "V0_A", "V0_B", "V0_C", "V0_D",
            "V1_A", "V1_B", "V1_C", "V1_D",
        ]
        for name, payload in payloads.items():
            config = json.loads(payload)
            candidate = config["candidate"]
            assert name.startswith(f"MambaV15D5A_{candidate}_")
            assert config["descriptor"]["dimensions"] == (13 if candidate == "V0" else 27)
            assert config["training"]["optimizer_steps_expected"] == 1900
            assert config["boundaries"]["D5A_seed0_training_authorized"] is True
            assert config["boundaries"]["D5A_seed1_training_authorized"] is False
            assert config["boundaries"]["D5B_training_authorized"] is False

    if torch is not None:
        from utils.mamba_d5a_proposal import (
            D4AProposalHead,
            D5V1ContextHead,
            case_balanced_binary_cross_entropy,
            d5_v1_set_level_loss,
            select_deterministic_top32,
        )

        torch.manual_seed(0)
        labels = torch.zeros((2, 64), dtype=torch.bool)
        labels[0, :4] = True
        labels[1, 8:13] = True
        v0 = D4AProposalHead()
        logits_v0 = v0(torch.randn(2, 64, 13))
        loss_v0 = case_balanced_binary_cross_entropy(logits_v0, labels)
        loss_v0.backward()
        assert torch.isfinite(loss_v0)
        v1 = D5V1ContextHead()
        logits_v1 = v1(torch.randn(2, 64, 27))
        losses_v1 = d5_v1_set_level_loss(logits_v1, labels)
        losses_v1["total"].backward()
        selected = select_deterministic_top32(logits_v1.detach())
        assert selected.shape == (2, 32)
        assert torch.isfinite(losses_v1["total"])
    else:
        print("[skip-local] PyTorch tensor contract; required in server Conda preflight")

    authorizer_text = AUTHORIZER.read_text(encoding="utf-8")
    preflight_text = PREFLIGHT_SCRIPT.read_text(encoding="utf-8")
    run_text = RUN_SCRIPT.read_text(encoding="utf-8")
    runner_text = RUNNER.read_text(encoding="utf-8")
    freezer_text = FREEZER.read_text(encoding="utf-8")
    launcher_text = LAUNCH_SCRIPT.read_text(encoding="utf-8")
    assert "optimizer.step(" not in authorizer_text
    assert "subprocess" not in authorizer_text
    assert "bash scripts/run_mamba_v15_d5a_seed0_training.sh" not in preflight_text
    assert "optimizer_steps=0 training=false dev=false" in preflight_text
    assert "for candidate in V0 V1" in run_text
    assert "for fold in A B C D" in run_text
    assert "optimizer_steps != 1900" in runner_text
    assert "Dev IDs and NPZ assets remain unopened" in runner_text
    assert "V1_seed1_authorization_eligible_next" in freezer_text
    assert "D5A_seed1_training_authorized\": False" in freezer_text
    assert "preflight_mamba_v15_d5a_seed0_training.sh" in launcher_text
    assert "run_mamba_v15_d5a_seed0_training.sh" in launcher_text
    assert AUTH_SCRIPT.is_file()

    print("[ok] D5-A authorization is exactly V0/V1 x folds A-D at seed 0")
    print("[ok] 50-epoch/final-only/one-shot-dev and 400/400 V1 gate are fixed")
    print("[ok] authorization and preflight have no training side effect")
    print("[locked] seed1=false confirmation=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
