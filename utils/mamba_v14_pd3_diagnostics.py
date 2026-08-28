"""Selection-inert diagnostics for the frozen D3 S2 feasibility result."""

from __future__ import annotations

import math

import torch


RANK_CUTOFFS = (32, 64, 96, 128)
COVERAGE_THRESHOLDS_MM = (2.0, 5.0, 10.0)


def _quantile(values: torch.Tensor, q: float) -> float:
    if values.numel() == 0:
        return float("nan")
    return float(torch.quantile(values.float(), q).item())


def decompose_s2_case(
    scores: torch.Tensor,
    coordinates: torch.Tensor,
    labels: torch.Tensor,
    selected_indices: torch.Tensor,
    rim_points: torch.Tensor,
    normalization_scale: float,
    pool_size: int = 96,
) -> dict[str, float | int | str]:
    """Describe ranking, pool retention, selector retention, and coverage.

    The function does not choose a threshold, candidate pool, or selector. It
    only evaluates the already-frozen S2 score order and selected indices.
    """

    scores = torch.as_tensor(scores).detach().float().cpu()
    coordinates = torch.as_tensor(coordinates).detach().float().cpu()
    labels = torch.as_tensor(labels).detach().bool().cpu()
    selected_indices = torch.as_tensor(selected_indices).detach().long().cpu()
    rim_points = torch.as_tensor(rim_points).detach().float().cpu()
    scale = float(normalization_scale)

    if scores.ndim != 1:
        raise ValueError("scores must have shape (N,)")
    if coordinates.shape != (scores.numel(), 3):
        raise ValueError("coordinates must have shape (N, 3)")
    if labels.shape != scores.shape:
        raise ValueError("labels must match scores")
    if selected_indices.ndim != 1 or selected_indices.numel() < 1:
        raise ValueError("selected_indices must be a non-empty vector")
    if rim_points.ndim != 2 or rim_points.shape[1] != 3 or rim_points.shape[0] < 1:
        raise ValueError("rim_points must have shape (R, 3) with R > 0")
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("normalization_scale must be finite and positive")
    if not torch.isfinite(scores).all() or not torch.isfinite(coordinates).all():
        raise ValueError("scores and coordinates must be finite")
    if not torch.isfinite(rim_points).all():
        raise ValueError("rim_points must be finite")
    if selected_indices.min() < 0 or selected_indices.max() >= scores.numel():
        raise ValueError("selected index is out of bounds")
    if selected_indices.unique().numel() != selected_indices.numel():
        raise ValueError("selected indices must be unique")
    pool_size = int(pool_size)
    if not 1 <= pool_size <= scores.numel():
        raise ValueError("pool_size is out of bounds")

    order = torch.argsort(scores, descending=True, stable=True)
    positive_indices = torch.nonzero(labels, as_tuple=False).flatten()
    positive_count = int(positive_indices.numel())
    rank_by_index = torch.empty_like(order)
    rank_by_index[order] = torch.arange(1, order.numel() + 1)
    positive_ranks = rank_by_index[positive_indices]

    pool_indices = order[:pool_size]
    positive_in_pool = int(labels[pool_indices].sum().item())
    selected_positive = int(labels[selected_indices].sum().item())

    if positive_count == 0:
        stage = "oracle_absent"
    elif positive_in_pool == 0:
        stage = "ranking_miss_top96"
    elif selected_positive == 0:
        stage = "selector_dropped_all_positive"
    else:
        stage = "selected_hit"

    all_distances_mm = torch.cdist(rim_points, coordinates) * scale
    rim_to_all = all_distances_mm.amin(dim=1)
    selected_coordinates = coordinates[selected_indices]
    selected_pairwise = torch.cdist(selected_coordinates, selected_coordinates)
    selected_pairwise.fill_diagonal_(float("inf"))
    selected_spatial_coverage = float(
        selected_pairwise.amin(dim=1).mean().item() * scale
    )
    rim_to_selected = torch.cdist(rim_points, selected_coordinates).amin(dim=1)
    rim_to_selected = rim_to_selected * scale

    result: dict[str, float | int | str] = {
        "failure_stage": stage,
        "proxy_count": int(scores.numel()),
        "positive_proxy_count": positive_count,
        "positive_proxy_fraction": positive_count / float(scores.numel()),
        "best_positive_rank": int(positive_ranks.min().item()) if positive_count else 0,
        "positive_in_top_pool": positive_in_pool,
        "selected_positive_proxy_count": selected_positive,
        "selected_anchor_spatial_coverage_mm": selected_spatial_coverage,
        "nearest_proxy_to_gt_rim_mm": float(rim_to_all.min().item()),
        "gt_rim_to_all_proxy_p50_mm": _quantile(rim_to_all, 0.50),
        "gt_rim_to_all_proxy_p95_mm": _quantile(rim_to_all, 0.95),
        "gt_rim_to_selected_anchor_p50_mm": _quantile(rim_to_selected, 0.50),
        "gt_rim_to_selected_anchor_p95_mm": _quantile(rim_to_selected, 0.95),
    }
    for cutoff in RANK_CUTOFFS:
        effective = min(cutoff, scores.numel())
        result[f"positive_in_top{cutoff}"] = int(labels[order[:effective]].sum().item())
    for threshold in COVERAGE_THRESHOLDS_MM:
        name = str(int(threshold)) if threshold.is_integer() else str(threshold)
        result[f"gt_rim_coverage_at_{name}mm"] = float(
            (rim_to_selected <= threshold).float().mean().item()
        )

    if selected_positive >= 2:
        positive_coordinates = coordinates[selected_indices[labels[selected_indices]]]
        pairwise = torch.pdist(positive_coordinates) * scale
        result["selected_positive_pairwise_mean_mm"] = float(pairwise.mean().item())
    else:
        result["selected_positive_pairwise_mean_mm"] = float("nan")
    return result
