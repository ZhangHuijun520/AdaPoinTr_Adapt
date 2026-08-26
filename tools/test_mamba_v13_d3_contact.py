#!/usr/bin/env python
"""CPU checks for the preregistered D3 contact and query primitives."""

import os
import sys

import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from utils.mamba_d3_contact import (
    assign_reference_rim_to_proxies,
    case_balanced_binary_cross_entropy,
    dense_contact_safety_loss,
    diversified_topk_indices,
    gather_points,
    normalized_softmin,
)


def test_softmin_is_cardinality_normalized():
    original = torch.tensor([0.5, 1.0, 2.0], dtype=torch.float64)
    duplicated = original.repeat(7)
    assert torch.allclose(
        normalized_softmin(original, 0.25),
        normalized_softmin(duplicated, 0.25),
        atol=1e-12,
        rtol=1e-12,
    )


def test_dense_contact_loss_has_finite_gradient_and_tail():
    partial = torch.tensor(
        [[[0.0, 0.0, 0.0], [0.01, 0.0, 0.0], [1.0, 0.0, 0.0]]],
        dtype=torch.float64,
    )
    pred = torch.tensor(
        [[[0.03, 0.0, 0.0], [0.04, 0.0, 0.0]]],
        dtype=torch.float64,
        requires_grad=True,
    )
    result = dense_contact_safety_loss(
        pred,
        partial,
        normalization_scale=torch.tensor([100.0], dtype=torch.float64),
        gt_rim_mask=torch.tensor([[True, True, False]]),
        query_chunk_size=1,
        reference_chunk_size=1,
    )
    assert result.loss.item() > 0
    assert result.tail_counts.tolist() == [1]
    result.loss.backward()
    assert pred.grad is not None and torch.isfinite(pred.grad).all()


def test_nearest_proxy_labels_and_balanced_bce():
    proxies = torch.tensor(
        [[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]]
    )
    partial = torch.tensor(
        [[[0.1, 0.0, 0.0], [0.9, 0.0, 0.0], [4.0, 0.0, 0.0]]]
    )
    labels = assign_reference_rim_to_proxies(
        proxies,
        partial,
        torch.tensor([[True, True, False]]),
    )
    assert labels.labels.tolist() == [[True, True, False]]
    logits = torch.tensor([[2.0, 1.0, -2.0]], requires_grad=True)
    loss = case_balanced_binary_cross_entropy(logits, labels.labels)
    loss.backward()
    assert logits.grad is not None and torch.isfinite(logits.grad).all()


def test_diversified_selection_is_deterministic_and_anchor_preserving():
    scores = torch.tensor([[10.0, 9.0, 8.0, 7.0]])
    coordinates = torch.tensor(
        [[[0.0, 0.0, 0.0], [0.1, 0.0, 0.0], [10.0, 0.0, 0.0], [20.0, 0.0, 0.0]]]
    )
    first = diversified_topk_indices(scores, coordinates, 2, 3)
    second = diversified_topk_indices(scores, coordinates, 2, 3)
    assert first.tolist() == [[0, 2]]
    assert torch.equal(first, second)
    assert torch.equal(gather_points(coordinates, first), coordinates[:, [0, 2]])


def main():
    test_softmin_is_cardinality_normalized()
    print("[ok] normalized soft-min is invariant to duplicate cardinality")
    test_dense_contact_loss_has_finite_gradient_and_tail()
    print("[ok] dense contact existence/tail loss is differentiable")
    test_nearest_proxy_labels_and_balanced_bce()
    print("[ok] nearest-proxy labels and case-balanced BCE")
    test_diversified_selection_is_deterministic_and_anchor_preserving()
    print("[ok] deterministic diversified selection preserves anchors")


if __name__ == "__main__":
    main()
