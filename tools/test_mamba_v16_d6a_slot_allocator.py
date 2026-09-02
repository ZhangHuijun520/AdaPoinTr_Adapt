#!/usr/bin/env python3
"""Artificial-data tests for the frozen D6-A slot32 implementation."""

from __future__ import annotations

import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.mamba_d5a_proposal import D5V1ContextHead as FrozenD5V1ContextHead
from utils.mamba_d6a_slot_allocator import (
    CANDIDATE_COUNT,
    D5V1ContextHead,
    D6R1SlotAllocator,
    PARAMETER_MAXIMUM,
    SLOT_COUNT,
    assignment_score,
    d6a_raw_losses,
    deterministic_global_assignment,
    inference_signature_has_no_ground_truth,
    slot_order_greedy_assignment_score,
    straight_through_assignment,
)


def expect_failure(function, label: str) -> None:
    try:
        function()
    except (ValueError, RuntimeError):
        return
    raise AssertionError(f"Expected hard failure: {label}")


def raw_outputs(slot_logits: torch.Tensor, point_logits: torch.Tensor | None = None):
    if point_logits is None:
        point_logits = torch.zeros(
            slot_logits.shape[0], slot_logits.shape[2], dtype=slot_logits.dtype
        )
    return {"slot_logits": slot_logits, "point_logits": point_logits}


def main() -> None:
    torch.manual_seed(1606)
    assert D5V1ContextHead is FrozenD5V1ContextHead
    model = D6R1SlotAllocator()
    assert model.trainable_parameter_count() <= PARAMETER_MAXIMUM
    assert model.trainable_parameter_count() == 94529
    assert inference_signature_has_no_ground_truth()

    logits = torch.randn(2, SLOT_COUNT, 96)
    hard_a, selected_a = deterministic_global_assignment(logits, fixed_candidates=False)
    hard_b, selected_b = deterministic_global_assignment(logits, fixed_candidates=False)
    assert torch.equal(hard_a, hard_b)
    assert torch.equal(selected_a, selected_b)
    assert selected_a.shape == (2, SLOT_COUNT)
    assert all(row.unique().numel() == SLOT_COUNT for row in selected_a)
    assert torch.all(
        assignment_score(logits, hard_a) + 1.0e-6
        >= slot_order_greedy_assignment_score(logits)
    )

    ties = torch.zeros(1, SLOT_COUNT, 64)
    _, selected_ties = deterministic_global_assignment(ties, fixed_candidates=False)
    assert torch.equal(selected_ties[0], torch.arange(SLOT_COUNT))

    production_logits = torch.zeros(1, SLOT_COUNT, CANDIDATE_COUNT)
    positive = torch.zeros(1, CANDIDATE_COUNT, dtype=torch.bool)
    positive[:, 100] = True
    baseline = d6a_raw_losses(raw_outputs(production_logits), positive)["L_support"]
    improved_logits = production_logits.clone()
    improved_logits[:, :, 100] = 8.0
    improved = d6a_raw_losses(raw_outputs(improved_logits), positive)["L_support"]
    assert improved < baseline

    collapsed = torch.full((1, SLOT_COUNT, CANDIDATE_COUNT), -12.0)
    collapsed[:, :, 0] = 12.0
    separated = torch.full_like(collapsed, -12.0)
    for slot in range(SLOT_COUNT):
        separated[:, slot, slot] = 12.0
    collapsed_shape = d6a_raw_losses(raw_outputs(collapsed), positive)["L_shape"]
    separated_shape = d6a_raw_losses(raw_outputs(separated), positive)["L_shape"]
    assert collapsed_shape > 0
    assert separated_shape < collapsed_shape

    random_production = torch.randn(1, SLOT_COUNT, CANDIDATE_COUNT)
    ste, hard, selected = straight_through_assignment(random_production)
    assert torch.equal(ste.detach(), hard)
    inferred_hard, inferred_selected = deterministic_global_assignment(random_production)
    assert torch.equal(hard, inferred_hard)
    assert torch.equal(selected, inferred_selected)

    expect_failure(
        lambda: d6a_raw_losses(raw_outputs(production_logits), torch.zeros_like(positive)),
        "empty positive mask",
    )
    expect_failure(
        lambda: deterministic_global_assignment(torch.zeros(1, SLOT_COUNT, 64)),
        "wrong production candidate count",
    )
    bad = production_logits.clone()
    bad[0, 0, 0] = float("nan")
    expect_failure(lambda: deterministic_global_assignment(bad), "NaN logits")
    expect_failure(
        lambda: model(torch.zeros(1, CANDIDATE_COUNT - 1, 27)),
        "short descriptors",
    )

    # Tiny artificial learning test: optimize logits only, never D6 data or model weights.
    learnable = torch.nn.Parameter(torch.zeros(1, SLOT_COUNT, CANDIDATE_COUNT))
    toy_positive = torch.zeros(1, CANDIDATE_COUNT, dtype=torch.bool)
    toy_positive[:, 17] = True
    optimizer = torch.optim.Adam([learnable], lr=1.0)
    for _ in range(12):
        optimizer.zero_grad(set_to_none=True)
        loss = d6a_raw_losses(raw_outputs(learnable), toy_positive)["L_support"]
        loss.backward()
        optimizer.step()
    learned = d6a_raw_losses(raw_outputs(learnable.detach()), toy_positive)
    assert 17 in learned["selected_indices"][0].tolist()

    print(f"[ok] R1 trainable parameters={model.trainable_parameter_count()} <= 100000")
    print("[ok] deterministic global assignment dominates forbidden slot-order greedy")
    print("[ok] tie, uniqueness, STE, support, shape and tiny-learning tests passed")
    print("[ok] inference signature contains descriptors only; GT leakage is absent")
    print("[locked] D6 cases=0 training=false calibration=false sealed=false")


if __name__ == "__main__":
    main()
