"""Geometry primitives for the preregistered Mamba v1.2 D2.2 experiment."""

from typing import NamedTuple, Optional

import torch


class GTRimProxy(NamedTuple):
    """All-point GT-rim proxy in the normalized point-cloud frame."""

    mask: torch.Tensor
    partial_to_gt_mm: torch.Tensor
    counts: torch.Tensor


class LocalRimLossResult(NamedTuple):
    loss: torch.Tensor
    gt_rim_to_coarse_mm: torch.Tensor
    gt_radial_rms_mm: torch.Tensor
    counts: torch.Tensor


class MomentTrustLossResult(NamedTuple):
    loss: torch.Tensor
    centroid_excess_mm: torch.Tensor
    radius_log_excess: torch.Tensor


def _validate_point_batch(points, name):
    if not torch.is_tensor(points):
        raise TypeError(f"{name} must be a torch.Tensor")
    if points.ndim != 3 or points.shape[-1] != 3:
        raise ValueError(
            f"{name} must have shape (B, N, 3), got {tuple(points.shape)}"
        )
    if points.shape[0] < 1 or points.shape[1] < 1:
        raise ValueError(f"{name} must contain at least one batch and point")
    if not points.is_floating_point():
        raise TypeError(f"{name} must use a floating-point dtype")
    if not torch.isfinite(points).all():
        raise ValueError(f"{name} contains NaN or Inf")


def _chunk_size(value: Optional[int], length: int, name: str) -> int:
    if value is None:
        return length
    value = int(value)
    if value < 1:
        raise ValueError(f"{name} must be positive, got {value}")
    return min(value, length)


def directed_nearest_distances_chunked(
    query,
    reference,
    query_chunk_size=1024,
    reference_chunk_size=1024,
):
    """Compute differentiable query-to-reference distances without an NxM tensor."""

    _validate_point_batch(query, "query")
    _validate_point_batch(reference, "reference")
    if query.shape[0] != reference.shape[0]:
        raise ValueError(
            "query and reference must have the same batch size, got "
            f"{query.shape[0]} and {reference.shape[0]}"
        )
    if query.device != reference.device:
        raise ValueError("query and reference must be on the same device")
    if query.dtype != reference.dtype:
        raise ValueError("query and reference must use the same dtype")

    query_chunk_size = _chunk_size(
        query_chunk_size, query.shape[1], "query_chunk_size"
    )
    reference_chunk_size = _chunk_size(
        reference_chunk_size, reference.shape[1], "reference_chunk_size"
    )

    query_results = []
    for query_start in range(0, query.shape[1], query_chunk_size):
        query_chunk = query[
            :, query_start : query_start + query_chunk_size, :
        ]
        nearest = None
        for reference_start in range(
            0, reference.shape[1], reference_chunk_size
        ):
            reference_chunk = reference[
                :,
                reference_start : reference_start + reference_chunk_size,
                :,
            ]
            chunk_nearest = torch.cdist(
                query_chunk, reference_chunk, p=2
            ).amin(dim=-1)
            nearest = (
                chunk_nearest
                if nearest is None
                else torch.minimum(nearest, chunk_nearest)
            )
        query_results.append(nearest)

    return torch.cat(query_results, dim=1)


def build_gt_rim_proxy(
    partial,
    target_implant,
    normalization_scale,
    rim_band_mm=2.0,
    query_chunk_size=1024,
    reference_chunk_size=1024,
    require_nonempty=True,
):
    """Select defective-skull points within ``rim_band_mm`` of the GT implant.

    The stored point clouds use ``world = normalized * scale + centroid``.
    Translation cancels in pairwise distances, so normalized distances are
    converted to millimeters by multiplying by each case's manifest scale.
    """

    _validate_point_batch(partial, "partial")
    _validate_point_batch(target_implant, "target_implant")
    if partial.shape[0] != target_implant.shape[0]:
        raise ValueError("partial and target_implant batch sizes must match")

    scale = torch.as_tensor(
        normalization_scale,
        device=partial.device,
        dtype=partial.dtype,
    )
    if scale.ndim == 2 and scale.shape[1] == 1:
        scale = scale[:, 0]
    if scale.ndim != 1 or scale.shape[0] != partial.shape[0]:
        raise ValueError(
            "normalization_scale must have shape (B,) or (B, 1), got "
            f"{tuple(scale.shape)}"
        )
    if not torch.isfinite(scale).all() or torch.any(scale <= 0):
        raise ValueError("normalization_scale must contain finite positive values")

    rim_band_mm = float(rim_band_mm)
    if not torch.isfinite(torch.tensor(rim_band_mm)) or rim_band_mm <= 0:
        raise ValueError("rim_band_mm must be finite and positive")

    partial_to_gt_normalized = directed_nearest_distances_chunked(
        partial,
        target_implant,
        query_chunk_size=query_chunk_size,
        reference_chunk_size=reference_chunk_size,
    )
    partial_to_gt_mm = partial_to_gt_normalized * scale[:, None]
    mask = partial_to_gt_mm <= rim_band_mm
    counts = mask.sum(dim=1)

    if require_nonempty and torch.any(counts == 0):
        empty_batches = torch.nonzero(counts == 0, as_tuple=False).flatten()
        indices = ", ".join(str(int(index)) for index in empty_batches.cpu())
        raise ValueError(
            "GT-rim proxy is empty for batch indices "
            f"[{indices}] at rim_band_mm={rim_band_mm}"
        )

    return GTRimProxy(
        mask=mask,
        partial_to_gt_mm=partial_to_gt_mm,
        counts=counts,
    )


def radial_rms(points, eps=0.0):
    """Return per-case radial RMS around each point cloud's centroid."""

    _validate_point_batch(points, "points")
    eps = float(eps)
    if eps < 0:
        raise ValueError("eps must be non-negative")
    centroid = points.mean(dim=1, keepdim=True)
    squared_radius = (points - centroid).square().sum(dim=-1).mean(dim=1)
    return torch.sqrt(squared_radius + eps)


def local_rim_undercoverage_loss(
    pred_coarse,
    partial,
    target_implant,
    normalization_scale,
    gt_rim_mask=None,
    rim_band_mm=2.0,
    deadzone_mm=5.0,
    smooth_l1_beta=0.1,
    epsilon_mm=1.0e-6,
    query_chunk_size=1024,
    reference_chunk_size=1024,
):
    """Compute the preregistered one-sided GT-rim-to-coarse loss."""

    _validate_point_batch(pred_coarse, "pred_coarse")
    _validate_point_batch(partial, "partial")
    _validate_point_batch(target_implant, "target_implant")
    if not (
        pred_coarse.shape[0]
        == partial.shape[0]
        == target_implant.shape[0]
    ):
        raise ValueError("pred_coarse, partial, and target batch sizes must match")

    scale = torch.as_tensor(
        normalization_scale,
        device=partial.device,
        dtype=partial.dtype,
    ).reshape(-1)
    if scale.shape[0] != partial.shape[0]:
        raise ValueError("normalization_scale must contain one value per case")
    if not torch.isfinite(scale).all() or torch.any(scale <= 0):
        raise ValueError("normalization_scale must contain finite positive values")

    if gt_rim_mask is None:
        gt_rim_mask = build_gt_rim_proxy(
            partial,
            target_implant,
            scale,
            rim_band_mm=rim_band_mm,
            query_chunk_size=query_chunk_size,
            reference_chunk_size=reference_chunk_size,
            require_nonempty=True,
        ).mask
    else:
        gt_rim_mask = torch.as_tensor(gt_rim_mask, device=partial.device)
        if gt_rim_mask.shape != partial.shape[:2]:
            raise ValueError(
                "gt_rim_mask must have shape (B, N_PARTIAL), got "
                f"{tuple(gt_rim_mask.shape)}"
            )
        gt_rim_mask = gt_rim_mask.to(dtype=torch.bool)

    counts = gt_rim_mask.sum(dim=1)
    if torch.any(counts == 0):
        empty_batches = torch.nonzero(counts == 0, as_tuple=False).flatten()
        indices = ", ".join(str(int(index)) for index in empty_batches.cpu())
        raise ValueError(f"GT-rim mask is empty for batch indices [{indices}]")

    partial_to_coarse_mm = directed_nearest_distances_chunked(
        partial,
        pred_coarse,
        query_chunk_size=query_chunk_size,
        reference_chunk_size=reference_chunk_size,
    ) * scale[:, None]
    excess_mm = torch.relu(partial_to_coarse_mm - float(deadzone_mm))
    gt_radial_rms_mm = radial_rms(target_implant) * scale
    normalized_excess = excess_mm / gt_radial_rms_mm.clamp_min(
        float(epsilon_mm)
    )[:, None]
    per_point = torch.nn.functional.smooth_l1_loss(
        normalized_excess,
        torch.zeros_like(normalized_excess),
        beta=float(smooth_l1_beta),
        reduction="none",
    )
    per_case = (per_point * gt_rim_mask).sum(dim=1) / counts.to(
        dtype=per_point.dtype
    )

    return LocalRimLossResult(
        loss=per_case.mean(),
        gt_rim_to_coarse_mm=partial_to_coarse_mm,
        gt_radial_rms_mm=gt_radial_rms_mm,
        counts=counts,
    )


def global_moment_trust_loss(
    pred_coarse,
    target_implant,
    normalization_scale,
    teacher_centroid_normalized,
    teacher_radial_rms_normalized,
    centroid_tolerance_mm=3.0,
    radius_log_tolerance=0.04879016416943205,
    smooth_l1_beta=0.1,
    epsilon_mm=1.0e-6,
):
    """Compute the preregistered R0 centroid/radial-RMS trust region."""

    _validate_point_batch(pred_coarse, "pred_coarse")
    _validate_point_batch(target_implant, "target_implant")
    if pred_coarse.shape[0] != target_implant.shape[0]:
        raise ValueError("pred_coarse and target_implant batch sizes must match")

    scale = torch.as_tensor(
        normalization_scale,
        device=pred_coarse.device,
        dtype=pred_coarse.dtype,
    ).reshape(-1)
    teacher_centroid = torch.as_tensor(
        teacher_centroid_normalized,
        device=pred_coarse.device,
        dtype=pred_coarse.dtype,
    )
    teacher_radius = torch.as_tensor(
        teacher_radial_rms_normalized,
        device=pred_coarse.device,
        dtype=pred_coarse.dtype,
    ).reshape(-1)
    batch_size = pred_coarse.shape[0]
    if scale.shape != (batch_size,):
        raise ValueError("normalization_scale must have shape (B,)")
    if teacher_centroid.shape != (batch_size, 3):
        raise ValueError("teacher_centroid_normalized must have shape (B, 3)")
    if teacher_radius.shape != (batch_size,):
        raise ValueError("teacher_radial_rms_normalized must have shape (B,)")
    tensors = (scale, teacher_centroid, teacher_radius)
    if any(not torch.isfinite(value).all() for value in tensors):
        raise ValueError("trust-region metadata contains NaN or Inf")
    if torch.any(scale <= 0) or torch.any(teacher_radius <= 0):
        raise ValueError("scale and teacher radial RMS must be positive")

    candidate_centroid = pred_coarse.mean(dim=1)
    candidate_radius = radial_rms(pred_coarse)
    centroid_delta_mm = torch.linalg.vector_norm(
        candidate_centroid - teacher_centroid,
        dim=-1,
    ) * scale
    centroid_excess_mm = torch.relu(
        centroid_delta_mm - float(centroid_tolerance_mm)
    )

    epsilon_normalized = float(epsilon_mm) / scale
    radius_log_delta = torch.abs(
        torch.log(
            (candidate_radius + epsilon_normalized)
            / (teacher_radius + epsilon_normalized)
        )
    )
    radius_log_excess = torch.relu(
        radius_log_delta - float(radius_log_tolerance)
    )

    gt_radial_rms_mm = radial_rms(target_implant) * scale
    centroid_normalized = centroid_excess_mm / gt_radial_rms_mm.clamp_min(
        float(epsilon_mm)
    )
    centroid_loss = torch.nn.functional.smooth_l1_loss(
        centroid_normalized,
        torch.zeros_like(centroid_normalized),
        beta=float(smooth_l1_beta),
    )
    radius_loss = torch.nn.functional.smooth_l1_loss(
        radius_log_excess,
        torch.zeros_like(radius_log_excess),
        beta=float(smooth_l1_beta),
    )

    return MomentTrustLossResult(
        loss=centroid_loss + radius_loss,
        centroid_excess_mm=centroid_excess_mm,
        radius_log_excess=radius_log_excess,
    )
