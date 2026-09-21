"""Contact-support labels, head, and auxiliary loss for SCQR v1.1."""

import math
from typing import NamedTuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .local_geometry import initialize_scqr_module


class ContactLabelOutput(NamedTuple):
    proxy_labels: torch.Tensor
    raw_positive_mask: torch.Tensor
    raw_positive_counts: torch.Tensor
    positive_proxy_counts: torch.Tensor


def _validate_points(points, name):
    if not torch.is_tensor(points) or points.ndim != 3 or points.shape[-1] != 3:
        raise ValueError(f"{name} must have shape (B, N, 3)")
    if points.shape[0] < 1 or points.shape[1] < 1:
        raise ValueError(f"{name} must be non-empty")
    if not points.is_floating_point() or not torch.isfinite(points).all():
        raise ValueError(f"{name} must contain finite floating-point values")


def _validated_scale(scale, batch_size, device, dtype):
    scale = torch.as_tensor(scale, device=device, dtype=dtype).reshape(-1)
    if scale.shape != (batch_size,):
        raise ValueError("normalization_scale must contain one value per case")
    if not torch.isfinite(scale).all() or torch.any(scale <= 0):
        raise ValueError("normalization_scale must be finite and positive")
    return scale


def directed_nearest_distance(
    query,
    reference,
    query_chunk_size=1024,
    reference_chunk_size=1024,
):
    _validate_points(query, "query")
    _validate_points(reference, "reference")
    if query.shape[0] != reference.shape[0]:
        raise ValueError("query and reference batch sizes must match")
    if query.device != reference.device or query.dtype != reference.dtype:
        raise ValueError("query and reference must share device and dtype")
    outputs = []
    for query_start in range(0, query.shape[1], int(query_chunk_size)):
        query_chunk = query[:, query_start : query_start + int(query_chunk_size)]
        nearest = None
        for reference_start in range(
            0, reference.shape[1], int(reference_chunk_size)
        ):
            reference_chunk = reference[
                :, reference_start : reference_start + int(reference_chunk_size)
            ]
            candidate = torch.cdist(query_chunk, reference_chunk, p=2).amin(-1)
            nearest = candidate if nearest is None else torch.minimum(nearest, candidate)
        outputs.append(nearest)
    return torch.cat(outputs, dim=1)


def build_contact_support_labels(
    partial,
    target_implant,
    normalization_scale,
    knn32_indices,
    rim_band_mm=2.0,
):
    """Build training-only raw and KNN32 proxy contact labels."""

    _validate_points(partial, "partial")
    _validate_points(target_implant, "target_implant")
    if partial.shape[0] != target_implant.shape[0]:
        raise ValueError("partial and target batch sizes must match")
    if partial.device != target_implant.device or partial.dtype != target_implant.dtype:
        raise ValueError("partial and target must share device and dtype")
    if not torch.is_tensor(knn32_indices) or knn32_indices.ndim != 3:
        raise ValueError("knn32_indices must have shape (B, N_PROXY, 32)")
    if knn32_indices.shape[0] != partial.shape[0] or knn32_indices.shape[-1] != 32:
        raise ValueError("knn32_indices violates the frozen batch/K contract")
    if knn32_indices.device != partial.device:
        raise ValueError("knn32_indices and partial must share a device")
    scale = _validated_scale(
        normalization_scale,
        partial.shape[0],
        partial.device,
        partial.dtype,
    )
    rim_band_mm = float(rim_band_mm)
    if not math.isfinite(rim_band_mm) or rim_band_mm <= 0:
        raise ValueError("rim_band_mm must be finite and positive")
    with torch.no_grad():
        distance_mm = directed_nearest_distance(partial, target_implant) * scale[:, None]
        raw_positive_mask = distance_mm <= rim_band_mm
        batch = torch.arange(partial.shape[0], device=partial.device)[:, None, None]
        proxy_labels = raw_positive_mask[batch, knn32_indices.long()].any(dim=-1)
        raw_counts = raw_positive_mask.sum(dim=1)
        proxy_counts = proxy_labels.sum(dim=1)
    if torch.any(raw_counts == 0):
        raise ValueError("SCQR raw GT-rim label is empty")
    return ContactLabelOutput(
        proxy_labels=proxy_labels,
        raw_positive_mask=raw_positive_mask,
        raw_positive_counts=raw_counts,
        positive_proxy_counts=proxy_counts,
    )


def case_balanced_binary_cross_entropy(logits, labels):
    """Average present classes per case, then average cases."""

    if not torch.is_tensor(logits) or logits.ndim != 2:
        raise ValueError("logits must have shape (B, N_PROXY)")
    labels = torch.as_tensor(labels, device=logits.device, dtype=torch.bool)
    if labels.shape != logits.shape:
        raise ValueError("labels and logits must have identical shapes")
    if not torch.isfinite(logits).all():
        raise ValueError("logits must be finite")
    raw = F.binary_cross_entropy_with_logits(
        logits,
        labels.to(dtype=logits.dtype),
        reduction="none",
    )
    case_losses = []
    for batch_index in range(logits.shape[0]):
        class_losses = []
        positive = labels[batch_index]
        negative = ~positive
        if positive.any():
            class_losses.append(raw[batch_index, positive].mean())
        if negative.any():
            class_losses.append(raw[batch_index, negative].mean())
        if not class_losses:
            raise RuntimeError("a proxy case cannot contain zero labels")
        case_losses.append(torch.stack(class_losses).mean())
    return torch.stack(case_losses).mean()


class ContactSupportHead(nn.Module):
    """Predict neighborhood contact support from [H, PE(V)]."""

    def __init__(self, embed_dim=384, hidden_dim=128):
        super().__init__()
        if int(embed_dim) != 384 or int(hidden_dim) != 128:
            raise ValueError("Cranial-SCQR v1.1 requires 768->128->1 SCF head")
        self.network = nn.Sequential(
            nn.Linear(2 * int(embed_dim), int(hidden_dim)),
            nn.GELU(),
            nn.Linear(int(hidden_dim), 1),
        )
        initialize_scqr_module(self)

    def forward(self, features, position_embedding):
        if features.shape != position_embedding.shape or features.shape[-1] != 384:
            raise ValueError("features and position_embedding must match at dim=384")
        logits = self.network(torch.cat([features, position_embedding], dim=-1)).squeeze(-1)
        return logits, torch.sigmoid(logits)
