"""Frozen V0/V1 proposal helpers for Mamba v1.5 D5-A."""

from __future__ import annotations

import math
from typing import Dict

import torch
import torch.nn.functional as F
from torch import nn

from utils.mamba_d4a_proposal import (
    D4AProposalHead,
    _validate_points,
    case_balanced_binary_cross_entropy,
    geometry_descriptor_13d,
    select_top8_conditioned_fps24,
)


V0_DESCRIPTOR_DIMENSIONS = 13
V1_DESCRIPTOR_DIMENSIONS = 27
V1_SELECTED_COUNT = 32


def _knn_context_9d(
    points: torch.Tensor,
    *,
    knn: int,
    epsilon: float,
    query_chunk_size: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return centroid offset, distance statistics, eigenvalues, and mean distance."""

    _validate_points(points, "points")
    knn = int(knn)
    query_chunk_size = int(query_chunk_size)
    epsilon = float(epsilon)
    if not 1 <= knn < points.shape[1]:
        raise ValueError("knn must satisfy 1 <= knn < point count")
    if query_chunk_size < 1:
        raise ValueError("query_chunk_size must be positive")
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")

    batch_size, point_count, _ = points.shape
    batch_indices = torch.arange(
        batch_size, device=points.device, dtype=torch.long
    ).view(batch_size, 1, 1)
    contexts = []
    means = []
    for start in range(0, point_count, query_chunk_size):
        end = min(start + query_chunk_size, point_count)
        query = points[:, start:end, :]
        distances = torch.cdist(query, points, p=2)
        local_indices = torch.arange(end - start, device=points.device)
        global_indices = torch.arange(start, end, device=points.device)
        distances[:, local_indices, global_indices] = float("inf")
        neighbor_distances, neighbor_indices = torch.topk(
            distances, k=knn, dim=-1, largest=False, sorted=True
        )
        neighbors = points[
            batch_indices.expand(-1, end - start, knn), neighbor_indices
        ]
        centroid = neighbors.mean(dim=2)
        offset = centroid - query
        mean_distance = neighbor_distances.mean(dim=-1)
        statistics = torch.stack(
            (
                mean_distance,
                neighbor_distances.std(dim=-1, unbiased=False),
                neighbor_distances.amax(dim=-1),
            ),
            dim=-1,
        )
        centered = neighbors - centroid.unsqueeze(2)
        covariance = torch.einsum(
            "bqki,bqkj->bqij", centered, centered
        ) / float(knn)
        eigenvalues = torch.linalg.eigvalsh(covariance).clamp_min(0.0)
        trace = eigenvalues.sum(dim=-1, keepdim=True).clamp_min(epsilon)
        normalized_eigenvalues = eigenvalues / trace
        contexts.append(torch.cat((offset, statistics, normalized_eigenvalues), dim=-1))
        means.append(mean_distance)

    context = torch.cat(contexts, dim=1)
    mean = torch.cat(means, dim=1)
    if context.shape != (batch_size, point_count, 9):
        raise RuntimeError("D5-A kNN context shape drifted")
    if not torch.isfinite(context).all() or not torch.isfinite(mean).all():
        raise RuntimeError("D5-A kNN context contains non-finite values")
    return context, mean


def geometry_descriptor_27d(
    points: torch.Tensor,
    *,
    knn_small: int = 16,
    knn_large: int = 32,
    epsilon: float = 1.0e-8,
    query_chunk_size: int = 512,
) -> torch.Tensor:
    """Compute the preregistered 27D partial-only D5-A descriptor."""

    _validate_points(points, "points")
    if int(knn_small) != 16 or int(knn_large) != 32:
        raise ValueError("D5-A V1 requires frozen kNN scales 16 and 32")
    base = geometry_descriptor_13d(
        points,
        knn=knn_small,
        epsilon=epsilon,
        query_chunk_size=query_chunk_size,
    )
    large_context, large_mean = _knn_context_9d(
        points,
        knn=knn_large,
        epsilon=epsilon,
        query_chunk_size=query_chunk_size,
    )
    partial_centroid = points.mean(dim=1, keepdim=True)
    offset_to_partial_centroid = partial_centroid - points
    centered = points - partial_centroid
    rms_radius = centered.square().sum(dim=-1).mean(dim=1, keepdim=True).sqrt()
    rms_radius = rms_radius.clamp_min(float(epsilon))
    radial_by_rms = (
        torch.linalg.vector_norm(centered, dim=-1) / rms_radius
    ).unsqueeze(-1)
    small_mean = base[..., 6]
    log_scale_ratio = torch.log(
        (small_mean + float(epsilon)) / (large_mean + float(epsilon))
    ).unsqueeze(-1)
    descriptor = torch.cat(
        (
            base,
            large_context,
            offset_to_partial_centroid,
            radial_by_rms,
            log_scale_ratio,
        ),
        dim=-1,
    )
    expected_shape = (points.shape[0], points.shape[1], V1_DESCRIPTOR_DIMENSIONS)
    if descriptor.shape != expected_shape:
        raise RuntimeError("D5-A V1 descriptor dimension drifted")
    if not torch.isfinite(descriptor).all():
        raise RuntimeError("D5-A V1 descriptor contains non-finite values")
    return descriptor


class D5V1ContextHead(nn.Module):
    """Frozen 27D point encoder plus mean/max global context classifier."""

    def __init__(self) -> None:
        super().__init__()
        self.point_encoder = nn.Sequential(
            nn.Linear(27, 64),
            nn.GELU(),
            nn.Linear(64, 64),
            nn.GELU(),
        )
        self.classifier = nn.Sequential(
            nn.Linear(219, 128),
            nn.GELU(),
            nn.Linear(128, 64),
            nn.GELU(),
            nn.Linear(64, 1),
        )
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.trunc_normal_(module.weight, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, descriptors: torch.Tensor) -> torch.Tensor:
        if descriptors.ndim != 3 or descriptors.shape[-1] != 27:
            raise ValueError("descriptors must have shape (B, N, 27)")
        if not descriptors.is_floating_point() or not torch.isfinite(
            descriptors
        ).all():
            raise ValueError("descriptors must contain finite floats")
        point_features = self.point_encoder(descriptors)
        mean_context = point_features.mean(dim=1)
        max_context = point_features.amax(dim=1)
        global_context = torch.cat((mean_context, max_context), dim=-1)
        expanded_context = global_context.unsqueeze(1).expand(
            -1, descriptors.shape[1], -1
        )
        classifier_input = torch.cat(
            (point_features, expanded_context, descriptors), dim=-1
        )
        if classifier_input.shape[-1] != 219:
            raise RuntimeError("D5-A V1 classifier input dimension drifted")
        logits = self.classifier(classifier_input).squeeze(-1)
        if not torch.isfinite(logits).all():
            raise RuntimeError("D5-A V1 logits are non-finite")
        return logits


def d5_v1_set_level_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    *,
    selected_count: int = 32,
    softmax_temperature: float = 1.0,
    margin: float = 1.0,
) -> Dict[str, torch.Tensor]:
    """Compute the fixed BCE, positive-mass NLL, and top-32 margin loss."""

    if not torch.is_tensor(logits) or logits.ndim != 2:
        raise ValueError("logits must have shape (B, N)")
    labels = torch.as_tensor(labels, device=logits.device, dtype=torch.bool)
    if labels.shape != logits.shape or not torch.isfinite(logits).all():
        raise ValueError("labels must match finite logits")
    selected_count = int(selected_count)
    temperature = float(softmax_temperature)
    margin = float(margin)
    if selected_count != V1_SELECTED_COUNT:
        raise ValueError("D5-A V1 selected_count is frozen at 32")
    if not math.isfinite(temperature) or temperature != 1.0:
        raise ValueError("D5-A V1 softmax temperature is frozen at 1.0")
    if not math.isfinite(margin) or margin != 1.0:
        raise ValueError("D5-A V1 margin is frozen at 1.0")

    bce = case_balanced_binary_cross_entropy(logits, labels)
    mass_losses = []
    margin_losses = []
    for batch_index in range(logits.shape[0]):
        positive_scores = logits[batch_index, labels[batch_index]]
        negative_scores = logits[batch_index, ~labels[batch_index]]
        if positive_scores.numel() == 0 or negative_scores.numel() < selected_count:
            raise ValueError("each case requires positives and at least 32 negatives")
        scaled = logits[batch_index] / temperature
        positive_scaled = positive_scores / temperature
        positive_mass_nll = -(
            torch.logsumexp(positive_scaled, dim=0)
            - torch.logsumexp(scaled, dim=0)
        )
        negative_rank32 = torch.topk(
            negative_scores, k=selected_count, largest=True, sorted=True
        ).values[-1]
        best_positive = positive_scores.amax()
        top32_margin = F.softplus(margin + negative_rank32 - best_positive)
        mass_losses.append(positive_mass_nll)
        margin_losses.append(top32_margin)
    positive_mass = torch.stack(mass_losses).mean()
    top32_margin = torch.stack(margin_losses).mean()
    total = bce + positive_mass + top32_margin
    if not torch.isfinite(total):
        raise RuntimeError("D5-A V1 set-level loss is non-finite")
    return {
        "total": total,
        "case_balanced_bce": bce,
        "positive_mass_nll": positive_mass,
        "top32_margin": top32_margin,
    }


def select_deterministic_top32(scores: torch.Tensor) -> torch.Tensor:
    """Select score top-32 with stable candidate-index tie breaking."""

    if not torch.is_tensor(scores) or scores.ndim != 2:
        raise ValueError("scores must have shape (B, N)")
    if scores.shape[1] < V1_SELECTED_COUNT or not torch.isfinite(scores).all():
        raise ValueError("scores must contain at least 32 finite candidates")
    order = torch.argsort(scores, dim=1, descending=True, stable=True)
    selected = order[:, :V1_SELECTED_COUNT]
    if any(row.unique().numel() != V1_SELECTED_COUNT for row in selected):
        raise RuntimeError("D5-A V1 selector produced duplicate indices")
    return selected


__all__ = [
    "D4AProposalHead",
    "D5V1ContextHead",
    "case_balanced_binary_cross_entropy",
    "d5_v1_set_level_loss",
    "geometry_descriptor_13d",
    "geometry_descriptor_27d",
    "select_deterministic_top32",
    "select_top8_conditioned_fps24",
]
