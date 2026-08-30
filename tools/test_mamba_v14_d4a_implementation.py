#!/usr/bin/env python3
"""Deterministic contract tests for the Mamba v1.4 D4-A implementation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch
from torch import nn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.mamba_d4a_proposal import (  # noqa: E402
    D4AProposalHead,
    case_balanced_binary_cross_entropy,
    geometry_descriptor_13d,
    select_top8_conditioned_fps24,
)


PROTOCOL = (
    REPO_ROOT / "docs/mamba_v14_d4a_zero_step_preflight_protocol_v1.json"
)
RUNNER = REPO_ROOT / "tools/preflight_mamba_v14_d4a_zero_step.py"
LAUNCHER = REPO_ROOT / "scripts/run_mamba_v14_d4a_zero_step_preflight.sh"


def reference_descriptor(points: torch.Tensor, knn: int, epsilon: float):
    batch_size, point_count, _ = points.shape
    distances = torch.cdist(points, points)
    diagonal = torch.arange(point_count)
    distances[:, diagonal, diagonal] = float("inf")
    neighbor_distances, neighbor_indices = torch.topk(
        distances, k=knn, dim=-1, largest=False, sorted=True
    )
    batch = torch.arange(batch_size).view(batch_size, 1, 1)
    neighbors = points[batch.expand(-1, point_count, knn), neighbor_indices]
    centroid = neighbors.mean(dim=2)
    offset = centroid - points
    stats = torch.stack(
        (
            neighbor_distances.mean(dim=-1),
            neighbor_distances.std(dim=-1, unbiased=False),
            neighbor_distances.amax(dim=-1),
        ),
        dim=-1,
    )
    centered = neighbors - centroid.unsqueeze(2)
    covariance = torch.einsum(
        "bnki,bnkj->bnij", centered, centered
    ) / float(knn)
    eigenvalues = torch.linalg.eigvalsh(covariance)
    normalized = eigenvalues.clamp_min(0.0) / eigenvalues.sum(
        dim=-1, keepdim=True
    ).clamp_min(epsilon)
    radius = torch.linalg.vector_norm(points, dim=-1, keepdim=True)
    return torch.cat((points, offset, stats, normalized, radius), dim=-1)


def expect_failure(callback, label: str) -> None:
    try:
        callback()
    except (TypeError, ValueError, RuntimeError):
        return
    raise AssertionError(f"Expected failure: {label}")


def test_descriptor() -> None:
    torch.manual_seed(14)
    points = torch.rand(2, 41, 3, dtype=torch.float64) * 2.0 - 1.0
    actual = geometry_descriptor_13d(
        points, knn=5, epsilon=1.0e-8, query_chunk_size=7
    )
    expected = reference_descriptor(points, 5, 1.0e-8)
    assert actual.shape == (2, 41, 13)
    assert torch.isfinite(actual).all()
    assert torch.allclose(actual, expected, rtol=1.0e-10, atol=1.0e-11)
    assert torch.allclose(actual[..., :3], points)
    assert torch.allclose(
        actual[..., 9:12].sum(dim=-1),
        torch.ones(2, 41, dtype=actual.dtype),
        rtol=1.0e-9,
        atol=1.0e-9,
    )

    expect_failure(
        lambda: geometry_descriptor_13d(points, knn=41), "knn range"
    )
    expect_failure(
        lambda: geometry_descriptor_13d(points.float().nan_to_num() * float("nan")),
        "non-finite points",
    )


def test_head_and_loss() -> None:
    torch.manual_seed(0)
    head = D4AProposalHead()
    linear = [module for module in head.modules() if isinstance(module, nn.Linear)]
    gelu = [module for module in head.modules() if isinstance(module, nn.GELU)]
    assert [(item.in_features, item.out_features) for item in linear] == [
        (13, 128),
        (128, 64),
        (64, 1),
    ]
    assert len(gelu) == 2
    descriptors = torch.randn(2, 64, 13)
    labels = torch.zeros(2, 64, dtype=torch.bool)
    labels[0, :5] = True
    labels[1, 8:17] = True
    logits = head(descriptors)
    loss = case_balanced_binary_cross_entropy(logits, labels)
    loss.backward()
    assert logits.shape == (2, 64)
    assert torch.isfinite(loss)
    assert all(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in head.parameters()
    )
    expect_failure(
        lambda: case_balanced_binary_cross_entropy(
            logits.detach(), torch.zeros_like(labels)
        ),
        "empty positive class",
    )


def test_selector() -> None:
    point_count = 300
    scores = torch.zeros(1, point_count)
    coordinates = torch.zeros(1, point_count, 3)
    coordinates[0, :, 0] = torch.arange(point_count, dtype=torch.float32)
    selected = select_top8_conditioned_fps24(scores, coordinates)
    selected_list = selected[0].tolist()
    assert selected.shape == (1, 32)
    assert selected_list[:8] == list(range(8))
    assert selected_list[8] == 255
    assert len(set(selected_list)) == 32
    assert all(0 <= value < 256 for value in selected_list)

    tied_coordinates = torch.zeros(1, point_count, 3)
    tied = select_top8_conditioned_fps24(scores, tied_coordinates)
    assert tied[0].tolist() == list(range(32))
    expect_failure(
        lambda: select_top8_conditioned_fps24(
            scores, coordinates, ranked_pool_size=31
        ),
        "pool smaller than selected budget",
    )


def test_static_execution_contract() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["protocol_id"] == "mamba-v14-d4a-zero-step-preflight-v1"
    assert protocol["scope"] == {
        "implementation_allowed": True,
        "zero_step_preflight_allowed": True,
        "D4A_training_allowed": False,
        "D4_full_training_allowed": False,
        "development_evaluation_allowed": False,
        "candidate_selection_allowed": False,
        "protected_data_access_allowed": False,
    }
    assert protocol["descriptor"]["candidate_count"] == 8192
    assert protocol["descriptor"]["query_chunk_size"] == 512
    assert protocol["selector"]["selected_count"] == 32
    assert protocol["zero_step_contract"]["optimizer_constructed"] is False
    assert protocol["zero_step_contract"]["optimizer_steps"] == 0

    runner = RUNNER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "torch.optim" not in runner
    assert "optimizer.step" not in runner
    assert "loss.backward()" in runner
    assert "dev_cases_accessed\": 0" in runner
    assert "D4A_training_authorized\": False" in runner
    assert "protected_data_accessed\": False" in runner
    assert "preflight_mamba_v14_d4a_zero_step.py" in launcher
    assert "D4A training was not started" in launcher


def main() -> None:
    test_descriptor()
    test_head_and_loss()
    test_selector()
    test_static_execution_contract()
    print("[ok] D4-A chunked 13D descriptor matches the full reference")
    print("[ok] 13-128-64-1 head and case-balanced BCE backward are finite")
    print("[ok] top8 + conditioned deterministic FPS24 tie rules are fixed")
    print("[locked] optimizer=none training=false dev=false selection=false")


if __name__ == "__main__":
    main()
