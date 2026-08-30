"""Frozen high-resolution geometry proposal helpers for Mamba v1.4 D4-A."""

from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import nn


DESCRIPTOR_DIMENSIONS = 13


def _validate_points(points: torch.Tensor, name: str) -> None:
    if not torch.is_tensor(points):
        raise TypeError(f"{name} must be a torch.Tensor")
    if points.ndim != 3 or points.shape[-1] != 3:
        raise ValueError(f"{name} must have shape (B, N, 3)")
    if points.shape[0] < 1 or points.shape[1] < 2:
        raise ValueError(f"{name} must contain at least two points per case")
    if points.dtype not in (torch.float32, torch.float64):
        raise ValueError(f"{name} must use float32 or float64")
    if not torch.isfinite(points).all():
        raise ValueError(f"{name} must contain finite values")


def geometry_descriptor_13d(
    points: torch.Tensor,
    *,
    knn: int = 16,
    epsilon: float = 1.0e-8,
    query_chunk_size: int = 512,
) -> torch.Tensor:
    """Compute the preregistered 13D descriptor for every partial point.

    The component order is normalized xyz, vector from the point to its kNN
    centroid, kNN distance mean/population-std/max, covariance eigenvalues
    divided by trace in ascending order, and radial norm. Self-neighbors are
    excluded by index rather than by assuming the first zero distance is self.
    """

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
    descriptors = []
    for start in range(0, point_count, query_chunk_size):
        end = min(start + query_chunk_size, point_count)
        query = points[:, start:end, :]
        distances = torch.cdist(query, points, p=2)
        local_indices = torch.arange(end - start, device=points.device)
        global_indices = torch.arange(start, end, device=points.device)
        distances[:, local_indices, global_indices] = float("inf")
        neighbor_distances, neighbor_indices = torch.topk(
            distances,
            k=knn,
            dim=-1,
            largest=False,
            sorted=True,
        )
        neighbors = points[
            batch_indices.expand(-1, end - start, knn), neighbor_indices
        ]

        centroid = neighbors.mean(dim=2)
        offset_to_centroid = centroid - query
        distance_statistics = torch.stack(
            (
                neighbor_distances.mean(dim=-1),
                neighbor_distances.std(dim=-1, unbiased=False),
                neighbor_distances.amax(dim=-1),
            ),
            dim=-1,
        )

        centered = neighbors - centroid.unsqueeze(2)
        covariance = torch.einsum(
            "bqki,bqkj->bqij", centered, centered
        ) / float(knn)
        eigenvalues = torch.linalg.eigvalsh(covariance)
        trace = eigenvalues.sum(dim=-1, keepdim=True).clamp_min(epsilon)
        normalized_eigenvalues = eigenvalues.clamp_min(0.0) / trace
        radial_norm = torch.linalg.vector_norm(query, dim=-1, keepdim=True)

        descriptor = torch.cat(
            (
                query,
                offset_to_centroid,
                distance_statistics,
                normalized_eigenvalues,
                radial_norm,
            ),
            dim=-1,
        )
        if descriptor.shape[-1] != DESCRIPTOR_DIMENSIONS:
            raise RuntimeError("D4-A descriptor dimension drifted")
        descriptors.append(descriptor)

    result = torch.cat(descriptors, dim=1)
    if result.shape != (batch_size, point_count, DESCRIPTOR_DIMENSIONS):
        raise RuntimeError("D4-A descriptor shape is invalid")
    if not torch.isfinite(result).all():
        raise RuntimeError("D4-A descriptor contains non-finite values")
    return result


class D4AProposalHead(nn.Module):
    """Frozen D4-A 13 -> 128 -> 64 -> 1 proposal head architecture."""

    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(13, 128),
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
        if descriptors.ndim != 3 or descriptors.shape[-1] != 13:
            raise ValueError("descriptors must have shape (B, N, 13)")
        if not descriptors.is_floating_point() or not torch.isfinite(
            descriptors
        ).all():
            raise ValueError("descriptors must contain finite floats")
        logits = self.layers(descriptors).squeeze(-1)
        if not torch.isfinite(logits).all():
            raise RuntimeError("D4-A proposal logits are non-finite")
        return logits


def case_balanced_binary_cross_entropy(
    logits: torch.Tensor, labels: torch.Tensor
) -> torch.Tensor:
    """Give positive and negative candidate points equal mass in each case."""

    if not torch.is_tensor(logits) or logits.ndim != 2:
        raise ValueError("logits must have shape (B, N)")
    labels = torch.as_tensor(labels, device=logits.device, dtype=torch.bool)
    if labels.shape != logits.shape:
        raise ValueError("labels and logits must have identical shapes")
    if not torch.isfinite(logits).all():
        raise ValueError("logits must be finite")

    raw = F.binary_cross_entropy_with_logits(
        logits, labels.to(dtype=logits.dtype), reduction="none"
    )
    losses = []
    for batch_index in range(logits.shape[0]):
        positive = labels[batch_index]
        negative = ~positive
        if not positive.any() or not negative.any():
            raise ValueError("every case must contain positive and negative labels")
        losses.append(
            0.5 * raw[batch_index, positive].mean()
            + 0.5 * raw[batch_index, negative].mean()
        )
    return torch.stack(losses).mean()


def select_top8_conditioned_fps24(
    scores: torch.Tensor,
    coordinates: torch.Tensor,
    *,
    mandatory_top_score_count: int = 8,
    ranked_pool_size: int = 256,
    diversified_count: int = 24,
) -> torch.Tensor:
    """Apply the fixed top-8 plus conditioned deterministic FPS-24 selector."""

    if not torch.is_tensor(scores) or scores.ndim != 2:
        raise ValueError("scores must have shape (B, N)")
    _validate_points(coordinates, "coordinates")
    if scores.shape != coordinates.shape[:2]:
        raise ValueError("scores and coordinates must describe the same points")
    if not torch.isfinite(scores).all():
        raise ValueError("scores must be finite")

    mandatory = int(mandatory_top_score_count)
    pool_size = int(ranked_pool_size)
    diversified = int(diversified_count)
    point_count = scores.shape[1]
    if not (
        mandatory >= 1
        and diversified >= 1
        and mandatory + diversified <= pool_size <= point_count
    ):
        raise ValueError("invalid D4-A selector counts")

    selected_batches = []
    for batch_index in range(scores.shape[0]):
        order = torch.argsort(
            scores[batch_index], descending=True, stable=True
        )
        pool_indices = order[:pool_size]
        pool_coordinates = coordinates[batch_index, pool_indices]
        chosen_local = list(range(mandatory))

        mandatory_coordinates = pool_coordinates[:mandatory]
        squared_distances = (
            pool_coordinates[:, None, :] - mandatory_coordinates[None, :, :]
        ).square().sum(dim=-1)
        minimum_squared_distance = squared_distances.amin(dim=1)
        minimum_squared_distance[:mandatory] = -1.0

        for _ in range(diversified):
            next_local = int(minimum_squared_distance.argmax().item())
            chosen_local.append(next_local)
            latest = pool_coordinates[next_local]
            latest_distance = (pool_coordinates - latest).square().sum(dim=-1)
            minimum_squared_distance = torch.minimum(
                minimum_squared_distance, latest_distance
            )
            minimum_squared_distance[
                torch.tensor(chosen_local, device=scores.device)
            ] = -1.0

        chosen = torch.tensor(
            chosen_local, device=scores.device, dtype=torch.long
        )
        selected = pool_indices[chosen]
        if selected.unique().numel() != mandatory + diversified:
            raise RuntimeError("D4-A selector produced duplicate indices")
        selected_batches.append(selected)

    return torch.stack(selected_batches, dim=0)


def gather_batched(values: torch.Tensor, indices: torch.Tensor) -> torch.Tensor:
    """Gather batched rows from a (B, N, C) tensor."""

    if values.ndim != 3 or indices.ndim != 2:
        raise ValueError("values and indices must have shapes (B,N,C) and (B,K)")
    if values.shape[0] != indices.shape[0]:
        raise ValueError("values and indices batch sizes must match")
    return torch.gather(
        values,
        1,
        indices.unsqueeze(-1).expand(-1, -1, values.shape[-1]),
    )
