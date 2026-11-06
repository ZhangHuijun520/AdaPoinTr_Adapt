"""Differentiable contact and non-leaky query helpers for D3."""

import math
from typing import NamedTuple

import torch
import torch.nn.functional as F

from utils.mamba_d22_geometry import directed_nearest_distances_chunked


class DenseContactLossResult(NamedTuple):
    loss: torch.Tensor
    existence_loss: torch.Tensor
    tail_loss: torch.Tensor
    soft_min_mm: torch.Tensor
    exact_min_mm: torch.Tensor
    tail_counts: torch.Tensor


class ProxyLabelResult(NamedTuple):
    labels: torch.Tensor
    positive_counts: torch.Tensor


def _validate_points(points, name):
    if not torch.is_tensor(points):
        raise TypeError(f"{name} must be a torch.Tensor")
    if points.ndim != 3 or points.shape[-1] != 3:
        raise ValueError(f"{name} must have shape (B, N, 3)")
    if points.shape[0] < 1 or points.shape[1] < 1:
        raise ValueError(f"{name} must contain points")
    if not points.is_floating_point() or not torch.isfinite(points).all():
        raise ValueError(f"{name} must contain finite floating-point values")


def _validated_scale(scale, batch_size, device, dtype):
    scale = torch.as_tensor(scale, device=device, dtype=dtype).reshape(-1)
    if scale.shape != (batch_size,):
        raise ValueError("normalization_scale must contain one value per case")
    if not torch.isfinite(scale).all() or torch.any(scale <= 0):
        raise ValueError("normalization_scale must be finite and positive")
    return scale


def normalized_softmin(distances, temperature):
    """Cardinality-invariant log-mean-exp approximation of a minimum."""

    if not torch.is_tensor(distances) or distances.ndim != 1:
        raise ValueError("distances must be a one-dimensional tensor")
    if distances.numel() < 1 or not torch.isfinite(distances).all():
        raise ValueError("distances must contain finite values")
    temperature = float(temperature)
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be finite and positive")
    count = distances.new_tensor(float(distances.numel())).log()
    return -temperature * (
        torch.logsumexp(-distances / temperature, dim=0) - count
    )


def dense_contact_safety_loss(
    pred_dense,
    partial,
    normalization_scale,
    gt_rim_mask,
    threshold_mm=2.0,
    temperature_mm=0.25,
    tail_fraction=0.1,
    query_chunk_size=1024,
    reference_chunk_size=1024,
):
    """Compute case-balanced dense contact-existence and GT-rim tail loss.

    ``gt_rim_mask`` selects the evaluator-equivalent reference rim from the
    defective partial skull. No target data are consumed by the inference
    graph; the mask is training supervision only.
    """

    _validate_points(pred_dense, "pred_dense")
    _validate_points(partial, "partial")
    if pred_dense.shape[0] != partial.shape[0]:
        raise ValueError("pred_dense and partial batch sizes must match")
    if pred_dense.device != partial.device or pred_dense.dtype != partial.dtype:
        raise ValueError("pred_dense and partial must share device and dtype")

    scale = _validated_scale(
        normalization_scale,
        pred_dense.shape[0],
        pred_dense.device,
        pred_dense.dtype,
    )
    mask = torch.as_tensor(gt_rim_mask, device=partial.device, dtype=torch.bool)
    if mask.shape != partial.shape[:2]:
        raise ValueError("gt_rim_mask must have shape (B, N_PARTIAL)")
    counts = mask.sum(dim=1)
    if torch.any(counts == 0):
        raise ValueError("gt_rim_mask must be non-empty for every case")

    threshold_mm = float(threshold_mm)
    temperature_mm = float(temperature_mm)
    tail_fraction = float(tail_fraction)
    if not math.isfinite(threshold_mm) or threshold_mm <= 0:
        raise ValueError("threshold_mm must be finite and positive")
    if not math.isfinite(temperature_mm) or temperature_mm <= 0:
        raise ValueError("temperature_mm must be finite and positive")
    if not math.isfinite(tail_fraction) or not 0 < tail_fraction <= 1:
        raise ValueError("tail_fraction must be in (0, 1]")

    existence_losses = []
    tail_losses = []
    soft_mins = []
    exact_mins = []
    tail_counts = []
    for batch_index in range(pred_dense.shape[0]):
        reference_rim = partial[batch_index, mask[batch_index]].unsqueeze(0)
        distances_mm = directed_nearest_distances_chunked(
            reference_rim,
            pred_dense[batch_index : batch_index + 1],
            query_chunk_size=query_chunk_size,
            reference_chunk_size=reference_chunk_size,
        ).squeeze(0) * scale[batch_index]
        soft_min = normalized_softmin(distances_mm, temperature_mm)
        existence = F.softplus(
            (soft_min - threshold_mm) / temperature_mm
        ) * temperature_mm
        excess = torch.relu(distances_mm - threshold_mm)
        tail_count = max(1, int(math.ceil(excess.numel() * tail_fraction)))
        tail = torch.topk(excess, k=tail_count, largest=True).values.mean()

        existence_losses.append(existence)
        tail_losses.append(tail)
        soft_mins.append(soft_min)
        exact_mins.append(distances_mm.amin())
        tail_counts.append(tail_count)

    existence_loss = torch.stack(existence_losses)
    tail_loss = torch.stack(tail_losses)
    return DenseContactLossResult(
        loss=(existence_loss + tail_loss).mean(),
        existence_loss=existence_loss,
        tail_loss=tail_loss,
        soft_min_mm=torch.stack(soft_mins),
        exact_min_mm=torch.stack(exact_mins),
        tail_counts=torch.tensor(tail_counts, device=pred_dense.device),
    )


def assign_reference_rim_to_proxies(
    proxy_coordinates,
    partial,
    gt_rim_mask,
    query_chunk_size=1024,
    reference_chunk_size=1024,
):
    """Label each proxy receiving at least one nearest reference-rim point."""

    _validate_points(proxy_coordinates, "proxy_coordinates")
    _validate_points(partial, "partial")
    if proxy_coordinates.shape[0] != partial.shape[0]:
        raise ValueError("proxy and partial batch sizes must match")
    if proxy_coordinates.device != partial.device:
        raise ValueError("proxy_coordinates and partial must share a device")
    mask = torch.as_tensor(gt_rim_mask, device=partial.device, dtype=torch.bool)
    if mask.shape != partial.shape[:2]:
        raise ValueError("gt_rim_mask must have shape (B, N_PARTIAL)")

    labels = torch.zeros(
        proxy_coordinates.shape[:2],
        device=proxy_coordinates.device,
        dtype=torch.bool,
    )
    for batch_index in range(proxy_coordinates.shape[0]):
        rim = partial[batch_index, mask[batch_index]]
        if rim.shape[0] == 0:
            raise ValueError("gt_rim_mask must be non-empty for every case")
        nearest = torch.cdist(
            rim.unsqueeze(0),
            proxy_coordinates[batch_index : batch_index + 1],
        ).squeeze(0).argmin(dim=1)
        labels[batch_index].scatter_(0, nearest, True)
    counts = labels.sum(dim=1)
    if torch.any(counts == 0):
        raise RuntimeError("nearest-proxy assignment produced an empty label set")
    return ProxyLabelResult(labels=labels, positive_counts=counts)


def case_balanced_binary_cross_entropy(logits, labels):
    """Give positive and negative proxies equal mass within every case."""

    if not torch.is_tensor(logits) or logits.ndim != 2:
        raise ValueError("logits must have shape (B, N_PROXY)")
    labels = torch.as_tensor(labels, device=logits.device, dtype=torch.bool)
    if labels.shape != logits.shape:
        raise ValueError("labels and logits must have identical shapes")
    if not torch.isfinite(logits).all():
        raise ValueError("logits must be finite")

    per_case = []
    raw = F.binary_cross_entropy_with_logits(
        logits,
        labels.to(dtype=logits.dtype),
        reduction="none",
    )
    for batch_index in range(logits.shape[0]):
        positive = labels[batch_index]
        negative = ~positive
        if not positive.any() or not negative.any():
            raise ValueError("every case must contain positive and negative proxies")
        per_case.append(
            0.5 * raw[batch_index, positive].mean()
            + 0.5 * raw[batch_index, negative].mean()
        )
    return torch.stack(per_case).mean()


def diversified_topk_indices(scores, coordinates, selected_count, pool_size):
    """Select score-filtered, spatially diverse anchors deterministically."""

    if not torch.is_tensor(scores) or scores.ndim != 2:
        raise ValueError("scores must have shape (B, N_PROXY)")
    _validate_points(coordinates, "coordinates")
    if scores.shape != coordinates.shape[:2]:
        raise ValueError("scores and coordinates must describe the same proxies")
    if not torch.isfinite(scores).all():
        raise ValueError("scores must be finite")
    selected_count = int(selected_count)
    pool_size = int(pool_size)
    proxy_count = scores.shape[1]
    if not 1 <= selected_count <= pool_size <= proxy_count:
        raise ValueError(
            "require 1 <= selected_count <= pool_size <= proxy_count"
        )

    selected_batches = []
    for batch_index in range(scores.shape[0]):
        order = torch.argsort(
            scores[batch_index], descending=True, stable=True
        )
        pool_indices = order[:pool_size]
        pool_coordinates = coordinates[batch_index, pool_indices]
        chosen_local = [0]
        minimum_squared_distance = torch.full(
            (pool_size,),
            float("inf"),
            device=coordinates.device,
            dtype=coordinates.dtype,
        )
        for _ in range(1, selected_count):
            latest = pool_coordinates[chosen_local[-1]]
            squared_distance = (pool_coordinates - latest).square().sum(dim=-1)
            minimum_squared_distance = torch.minimum(
                minimum_squared_distance, squared_distance
            )
            minimum_squared_distance[torch.tensor(
                chosen_local, device=coordinates.device
            )] = -1
            chosen_local.append(int(minimum_squared_distance.argmax().item()))
        chosen = torch.tensor(chosen_local, device=scores.device, dtype=torch.long)
        selected_batches.append(pool_indices[chosen])
    return torch.stack(selected_batches, dim=0)


def gather_points(points, indices):
    """Gather batched point or feature rows by batched indices."""

    if points.ndim != 3 or indices.ndim != 2:
        raise ValueError("points and indices must have shapes (B,N,C) and (B,K)")
    if points.shape[0] != indices.shape[0]:
        raise ValueError("points and indices batch sizes must match")
    return torch.gather(
        points,
        1,
        indices.unsqueeze(-1).expand(-1, -1, points.shape[-1]),
    )
