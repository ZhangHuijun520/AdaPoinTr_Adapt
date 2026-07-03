#!/usr/bin/env python
"""Validate patch-local targets, values, and gradients on synthetic points."""

import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from extensions.chamfer_dist import ChamferDistanceL1  # noqa: E402
from models.AdaPoinTr import patch_local_chamfer  # noqa: E402


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    loss_func = ChamferDistanceL1()

    coarse = torch.tensor(
        [[[0.5, 0.0, 0.0], [10.5, 0.0, 0.0]]],
        dtype=torch.float32,
        device=device,
    )
    gt = torch.tensor(
        [[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
          [10.0, 0.0, 0.0], [11.0, 0.0, 0.0]]],
        dtype=torch.float32,
        device=device,
    )
    exact_fine = gt.clone().requires_grad_(True)
    exact_loss = patch_local_chamfer(
        coarse,
        exact_fine,
        gt,
        factor=2,
        loss_func=loss_func,
    )
    if not torch.allclose(exact_loss, torch.zeros_like(exact_loss), atol=1e-7):
        raise AssertionError(f"Exact patch loss is not zero: {exact_loss.item()}")
    print(f"[ok] exact patch-local loss: {exact_loss.item():.9f}")

    shifted_fine = (gt + torch.tensor(
        [0.25, 0.0, 0.0],
        device=device,
    )).requires_grad_(True)
    shifted_loss = patch_local_chamfer(
        coarse,
        shifted_fine,
        gt,
        factor=2,
        loss_func=loss_func,
    )
    expected = torch.tensor(0.25, device=device)
    if not torch.allclose(shifted_loss, expected, atol=1e-6, rtol=1e-6):
        raise AssertionError(
            f"Shifted patch loss={shifted_loss.item():.9f}, expected=0.25"
        )
    shifted_loss.backward()
    if shifted_fine.grad is None or not torch.isfinite(shifted_fine.grad).all():
        raise AssertionError("Patch-local loss produced invalid gradients")
    print(f"[ok] shifted patch-local loss: {shifted_loss.item():.9f}")
    print(f"[ok] finite gradient norm: {shifted_fine.grad.norm().item():.9f}")

    global_loss = torch.tensor(0.4, device=device)
    local_loss = torch.tensor(0.2, device=device)
    for weight, expected_value in ((0.0, 0.4), (0.5, 1.0 / 3.0), (1.0, 0.3)):
        combined = (global_loss + weight * local_loss) / (1.0 + weight)
        expected = torch.tensor(expected_value, device=device)
        if not torch.allclose(combined, expected, atol=1e-7):
            raise AssertionError(
                f"weight={weight}: combined={combined.item():.9f}, "
                f"expected={expected.item():.9f}"
            )
        print(f"[ok] weight={weight:g} combined loss: {combined.item():.9f}")

    print(f"[ok] patch-local validation passed on {device}")


if __name__ == "__main__":
    main()
