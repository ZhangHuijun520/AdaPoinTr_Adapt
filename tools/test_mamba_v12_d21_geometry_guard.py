#!/usr/bin/env python
"""CPU checks for the preregistered D2.1 coarse geometry guards."""

import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.AdaPoinTr import coarse_geometry_guard_components  # noqa: E402


def main():
    torch.manual_seed(17)
    gt = torch.randn(2, 64, 3)
    pred = gt[:, :16].clone().requires_grad_(True)

    baseline = coarse_geometry_guard_components(pred, gt)
    assert set(baseline) == {
        "centroid", "radius", "centroid_radius", "coverage_cvar"
    }
    assert torch.allclose(
        baseline["centroid_radius"],
        0.5 * (baseline["centroid"] + baseline["radius"]),
    )
    assert all(torch.isfinite(value) for value in baseline.values())

    translated = coarse_geometry_guard_components(pred + 3.0, gt)
    assert translated["centroid"] > baseline["centroid"]

    gt_centroid = gt.mean(dim=1, keepdim=True)
    contracted = gt_centroid + 0.5 * (pred - gt_centroid)
    contracted_losses = coarse_geometry_guard_components(contracted, gt)
    assert contracted_losses["radius"] > baseline["radius"]

    uncovered = pred + 10.0
    uncovered_losses = coarse_geometry_guard_components(uncovered, gt)
    assert uncovered_losses["coverage_cvar"] > baseline["coverage_cvar"]

    total = sum(baseline.values())
    total.backward()
    assert pred.grad is not None
    assert torch.isfinite(pred.grad).all()

    print("[ok] geometry components are finite and differentiable")
    print("[ok] centroid guard responds to translation")
    print("[ok] radius guard responds to contraction")
    print("[ok] coverage CVaR responds to coarse under-coverage")


if __name__ == "__main__":
    main()
