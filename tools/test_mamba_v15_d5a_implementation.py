#!/usr/bin/env python3
"""Deterministic contract tests for the Mamba v1.5 D5-A implementation."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import torch
from torch import nn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.mamba_d4a_proposal import geometry_descriptor_13d as d4_descriptor  # noqa: E402
from utils.mamba_d5a_proposal import (  # noqa: E402
    D4AProposalHead,
    D5V1ContextHead,
    d5_v1_set_level_loss,
    geometry_descriptor_13d,
    geometry_descriptor_27d,
    select_deterministic_top32,
    select_top8_conditioned_fps24,
)
PROTOCOL = REPO_ROOT / "docs/mamba_v15_d5a_zero_step_preflight_protocol_v1.json"
RUNNER = REPO_ROOT / "tools/preflight_mamba_v15_d5a_zero_step.py"
LAUNCHER = REPO_ROOT / "scripts/run_mamba_v15_d5a_zero_step_preflight.sh"


def load_preflight_validator():
    spec = importlib.util.spec_from_file_location("d5a_preflight_contract", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load D5-A preflight runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_preflight_protocol


def expect_failure(callback, label: str) -> None:
    try:
        callback()
    except (TypeError, ValueError, RuntimeError):
        return
    raise AssertionError(f"Expected failure: {label}")


def test_v0_exact_reference() -> None:
    torch.manual_seed(150)
    points = torch.rand(2, 73, 3, dtype=torch.float64) * 2.0 - 1.0
    actual = geometry_descriptor_13d(
        points, knn=16, epsilon=1.0e-8, query_chunk_size=17
    )
    expected = d4_descriptor(
        points, knn=16, epsilon=1.0e-8, query_chunk_size=17
    )
    assert actual.shape == (2, 73, 13)
    assert torch.equal(actual, expected)

    scores = torch.zeros(1, 300)
    coordinates = torch.zeros(1, 300, 3)
    coordinates[0, :, 0] = torch.arange(300)
    selected = select_top8_conditioned_fps24(scores, coordinates)
    assert selected[0, :8].tolist() == list(range(8))
    assert selected[0, 8].item() == 255


def test_v1_descriptor() -> None:
    torch.manual_seed(151)
    points = torch.rand(2, 73, 3, dtype=torch.float64) * 2.0 - 1.0
    first = geometry_descriptor_27d(points, query_chunk_size=19)
    second = geometry_descriptor_27d(points, query_chunk_size=31)
    assert first.shape == (2, 73, 27)
    assert torch.isfinite(first).all()
    assert torch.allclose(first, second, rtol=1.0e-10, atol=1.0e-11)
    assert torch.equal(first[..., :13], d4_descriptor(points, query_chunk_size=19))
    assert torch.allclose(
        first[..., 19:22].sum(dim=-1),
        torch.ones(2, 73, dtype=first.dtype),
        rtol=1.0e-9,
        atol=1.0e-9,
    )
    expect_failure(
        lambda: geometry_descriptor_27d(points, knn_large=31), "frozen kNN"
    )


def test_v1_head_loss_and_selector() -> None:
    torch.manual_seed(0)
    head = D5V1ContextHead()
    linear = [module for module in head.modules() if isinstance(module, nn.Linear)]
    assert [(item.in_features, item.out_features) for item in linear] == [
        (27, 64),
        (64, 64),
        (219, 128),
        (128, 64),
        (64, 1),
    ]
    descriptors = torch.randn(2, 96, 27)
    labels = torch.zeros(2, 96, dtype=torch.bool)
    labels[0, [3, 9, 40]] = True
    labels[1, [8, 17, 70, 71]] = True
    logits = head(descriptors)
    losses = d5_v1_set_level_loss(logits, labels)
    losses["total"].backward()
    assert logits.shape == (2, 96)
    assert set(losses) == {
        "total",
        "case_balanced_bce",
        "positive_mass_nll",
        "top32_margin",
    }
    assert all(torch.isfinite(value) for value in losses.values())
    assert all(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in head.parameters()
    )

    tied = select_deterministic_top32(torch.zeros(2, 96))
    assert tied.shape == (2, 32)
    assert tied[0].tolist() == list(range(32))
    scores = torch.arange(96, dtype=torch.float32).repeat(2, 1)
    selected = select_deterministic_top32(scores)
    assert selected[0].tolist() == list(range(95, 63, -1))
    expect_failure(
        lambda: d5_v1_set_level_loss(logits.detach(), labels, margin=0.5),
        "margin drift",
    )
    expect_failure(
        lambda: select_deterministic_top32(torch.zeros(1, 31)),
        "too few candidates",
    )


def test_static_zero_step_contract() -> None:
    validate_preflight_protocol = load_preflight_validator()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_preflight_protocol(protocol)
    assert protocol["protocol_id"] == "mamba-v15-d5a-zero-step-preflight-v1"
    assert protocol["scope"] == {
        "V0_V1_implementation_allowed": True,
        "zero_step_preflight_allowed": True,
        "D5A_seed0_training_allowed": False,
        "D5A_seed1_training_allowed": False,
        "development_evaluation_allowed": False,
        "proposal_confirmation_access_allowed": False,
        "D5B_implementation_allowed": False,
        "candidate_selection_allowed": False,
        "protected_or_sealed_data_access_allowed": False,
    }
    assert protocol["V1"]["descriptor_dimensions"] == 27
    assert protocol["V1"]["selector"] == "deterministic_score_top32"
    assert protocol["zero_step_contract"]["optimizer_constructed"] is False
    assert protocol["zero_step_contract"]["optimizer_steps"] == 0
    assert protocol["zero_step_contract"]["backward_passes"] == 8

    runner = RUNNER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "torch.optim" not in runner
    assert "optimizer.step" not in runner
    assert ".backward()" in runner
    assert '"dev_cases_accessed": 0' in runner
    assert '"D5A_seed0_training_authorized": False' in runner
    assert '"proposal_confirmation_accessed": False' in runner
    assert "preflight_mamba_v15_d5a_zero_step.py" in launcher
    assert "D5-A training was not started" in launcher

    changed = copy.deepcopy(protocol)
    changed["V1"]["selector"] = "fps"
    expect_failure(
        lambda: validate_preflight_protocol(changed), "selector drift"
    )
    changed = copy.deepcopy(protocol)
    changed["scope"]["D5A_seed0_training_allowed"] = True
    expect_failure(
        lambda: validate_preflight_protocol(changed), "training authorization"
    )


def main() -> None:
    test_v0_exact_reference()
    test_v1_descriptor()
    test_v1_head_loss_and_selector()
    test_static_zero_step_contract()
    print("[ok] V0 is exactly the frozen D4-A descriptor and selector")
    print("[ok] V1 27D multiscale context is chunk-invariant and finite")
    print("[ok] V1 context head, three losses, and stable top32 are fixed")
    print("[locked] optimizer=none training=false dev=false sealed=false D5B=false")


if __name__ == "__main__":
    main()
