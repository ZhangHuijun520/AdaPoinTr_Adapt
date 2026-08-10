#!/usr/bin/env python
"""CPU checks for the preregistered D2.2 GT-rim geometry path."""

import os
import sys

import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from utils.mamba_d22_geometry import (
    build_gt_rim_proxy,
    directed_nearest_distances_chunked,
    global_moment_trust_loss,
    local_rim_undercoverage_loss,
)


def test_chunked_nearest_matches_full_cdist():
    torch.manual_seed(7)
    query = torch.randn(2, 11, 3, dtype=torch.float64, requires_grad=True)
    reference = torch.randn(2, 13, 3, dtype=torch.float64)

    actual = directed_nearest_distances_chunked(
        query,
        reference,
        query_chunk_size=4,
        reference_chunk_size=5,
    )
    expected = torch.cdist(query, reference).amin(dim=-1)
    assert torch.allclose(actual, expected, atol=1e-12, rtol=1e-12)

    actual.sum().backward()
    assert query.grad is not None
    assert torch.isfinite(query.grad).all()


def test_gt_rim_uses_manifest_scale_in_mm():
    partial = torch.tensor(
        [[[0.00, 0.0, 0.0], [0.01, 0.0, 0.0], [0.03, 0.0, 0.0]]],
        dtype=torch.float64,
    )
    target = torch.tensor([[[0.0, 0.0, 0.0]]], dtype=torch.float64)

    proxy = build_gt_rim_proxy(
        partial,
        target,
        normalization_scale=torch.tensor([100.0], dtype=torch.float64),
        rim_band_mm=2.0,
        query_chunk_size=2,
        reference_chunk_size=1,
    )

    assert proxy.mask.tolist() == [[True, True, False]]
    assert proxy.counts.tolist() == [2]
    assert torch.allclose(
        proxy.partial_to_gt_mm,
        torch.tensor([[0.0, 1.0, 3.0]], dtype=torch.float64),
    )


def test_empty_gt_rim_is_an_error():
    partial = torch.tensor([[[1.0, 0.0, 0.0]]])
    target = torch.tensor([[[0.0, 0.0, 0.0]]])

    try:
        build_gt_rim_proxy(
            partial,
            target,
            normalization_scale=torch.tensor([10.0]),
            rim_band_mm=2.0,
        )
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("empty GT-rim proxy did not raise ValueError")


def test_deadzone_is_zero_and_one_sided():
    partial = torch.tensor(
        [[[0.00, 0.0, 0.0], [0.04, 0.0, 0.0]]],
        dtype=torch.float64,
    )
    target = torch.tensor(
        [[[0.00, 0.0, 0.0], [0.02, 0.0, 0.0]]],
        dtype=torch.float64,
    )
    pred = torch.tensor(
        [[[0.05, 0.0, 0.0]]], dtype=torch.float64, requires_grad=True
    )
    mask = torch.tensor([[True, False]])
    result = local_rim_undercoverage_loss(
        pred,
        partial,
        target,
        normalization_scale=torch.tensor([100.0], dtype=torch.float64),
        gt_rim_mask=mask,
        deadzone_mm=5.0,
    )
    assert result.loss.item() == 0.0
    result.loss.backward()
    assert torch.count_nonzero(pred.grad).item() == 0

    # An extra coarse point away from the rim cannot add a symmetric penalty.
    pred_extra = torch.tensor(
        [[[0.05, 0.0, 0.0], [10.0, 0.0, 0.0]]], dtype=torch.float64
    )
    extra_result = local_rim_undercoverage_loss(
        pred_extra,
        partial,
        target,
        normalization_scale=torch.tensor([100.0], dtype=torch.float64),
        gt_rim_mask=mask,
        deadzone_mm=5.0,
    )
    assert extra_result.loss.item() == result.loss.item()


def test_moment_trust_tolerances():
    target = torch.tensor(
        [[[-0.1, 0.0, 0.0], [0.1, 0.0, 0.0]]], dtype=torch.float64
    )
    teacher_centroid = torch.zeros(1, 3, dtype=torch.float64)
    teacher_radius = torch.tensor([0.1], dtype=torch.float64)
    scale = torch.tensor([100.0], dtype=torch.float64)

    inside = torch.tensor(
        [[[-0.075, 0.0, 0.0], [0.125, 0.0, 0.0]]],
        dtype=torch.float64,
        requires_grad=True,
    )
    inside_result = global_moment_trust_loss(
        inside,
        target,
        scale,
        teacher_centroid,
        teacher_radius,
    )
    assert inside_result.loss.item() == 0.0
    inside_result.loss.backward()
    assert torch.count_nonzero(inside.grad).item() == 0

    outside = torch.tensor(
        [[[0.0, 0.0, 0.0], [0.3, 0.0, 0.0]]],
        dtype=torch.float64,
        requires_grad=True,
    )
    outside_result = global_moment_trust_loss(
        outside,
        target,
        scale,
        teacher_centroid,
        teacher_radius,
    )
    assert torch.isfinite(outside_result.loss)
    assert outside_result.loss.item() > 0
    outside_result.loss.backward()
    assert torch.count_nonzero(outside.grad).item() > 0


def main():
    test_chunked_nearest_matches_full_cdist()
    test_gt_rim_uses_manifest_scale_in_mm()
    test_empty_gt_rim_is_an_error()
    test_deadzone_is_zero_and_one_sided()
    test_moment_trust_tolerances()
    print("[ok] D2.2 chunked nearest-neighbor distances match full cdist")
    print("[ok] D2.2 GT-rim proxy applies manifest scale in millimeters")
    print("[ok] D2.2 empty GT-rim proxy is a hard error")
    print("[ok] D2.2 dead-zone has zero loss/gradient and remains one-sided")
    print("[ok] D2.2 trust tolerances have frozen zero/outside behavior")


if __name__ == "__main__":
    main()
