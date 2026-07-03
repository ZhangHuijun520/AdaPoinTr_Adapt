#!/usr/bin/env python
"""Validate directional L1 Chamfer values, compatibility, and gradients."""

import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from extensions.chamfer_dist import (  # noqa: E402
    ChamferDistanceL1,
    ChamferDistanceL1Directional,
)


def assert_close(name, actual, expected, atol=1e-6):
    if not torch.allclose(actual, expected, atol=atol, rtol=1e-6):
        raise AssertionError(
            f"{name}: actual={actual.item():.9f}, expected={expected.item():.9f}"
        )
    print(f"[ok] {name}: {actual.item():.9f}")


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(20260629)

    prediction = torch.rand(2, 32, 3, device=device)
    reference = torch.rand(2, 48, 3, device=device)
    standard = ChamferDistanceL1()(prediction, reference)
    directional_one = ChamferDistanceL1Directional(1.0, 1.0)(
        prediction,
        reference,
    )
    assert_close("lambda=1 matches official ChamferDistanceL1", directional_one, standard)

    prediction = torch.tensor(
        [[[0.2, 0.0, 0.0]]],
        dtype=torch.float32,
        device=device,
        requires_grad=True,
    )
    reference = torch.tensor(
        [[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]]],
        dtype=torch.float32,
        device=device,
    )
    expected = {
        1.0: 0.6,
        2.0: 2.2 / 3.0,
        4.0: 4.2 / 5.0,
    }
    for coverage_weight, expected_value in expected.items():
        prediction.grad = None
        loss = ChamferDistanceL1Directional(1.0, coverage_weight)(
            prediction,
            reference,
        )
        assert_close(
            f"lambda={coverage_weight:g} analytic value",
            loss,
            torch.tensor(expected_value, device=device),
        )
        loss.backward()
        if prediction.grad is None or not torch.isfinite(prediction.grad).all():
            raise AssertionError(
                f"lambda={coverage_weight:g}: non-finite or missing gradient"
            )
        print(
            f"[ok] lambda={coverage_weight:g} gradient: "
            f"{prediction.grad.flatten().tolist()}"
        )

    print(f"[ok] directional Chamfer validation passed on {device}")


if __name__ == "__main__":
    main()
