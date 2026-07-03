#!/usr/bin/env python
"""Validate stable L1 Chamfer compatibility and zero-distance gradients."""

import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from extensions.chamfer_dist import (  # noqa: E402
    ChamferDistanceL1,
    ChamferDistanceL1Stable,
)


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(20260629)
    official = ChamferDistanceL1()
    stable = ChamferDistanceL1Stable(1e-12)

    prediction = torch.rand(2, 32, 3, device=device)
    reference = torch.rand(2, 48, 3, device=device)
    official_loss = official(prediction, reference)
    stable_loss = stable(prediction, reference)
    if not torch.allclose(official_loss, stable_loss, atol=1e-7, rtol=1e-6):
        raise AssertionError(
            f"Stable loss {stable_loss.item()} differs from official "
            f"{official_loss.item()} away from zero"
        )
    print(f"[ok] nonzero compatibility: {stable_loss.item():.9f}")

    exact = torch.rand(1, 64, 3, device=device, requires_grad=True)
    exact_loss = stable(exact, exact.detach())
    exact_loss.backward()
    if exact.grad is None or not torch.isfinite(exact.grad).all():
        raise AssertionError("Stable Chamfer has invalid exact-match gradients")
    print(f"[ok] exact-match loss: {exact_loss.item():.9f}")
    print(f"[ok] exact-match gradient norm: {exact.grad.norm().item():.9f}")
    print(f"[ok] stable Chamfer validation passed on {device}")


if __name__ == "__main__":
    main()
