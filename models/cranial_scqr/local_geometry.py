"""Raw-partial local geometry residual for Cranial-SCQR v1.1."""

import math
from typing import NamedTuple

import torch
import torch.nn as nn


class LocalGeometryOutput(NamedTuple):
    features: torch.Tensor
    knn32_indices: torch.Tensor
    knn32_radius_normalized: torch.Tensor
    local_embedding: torch.Tensor
    residual: torch.Tensor
    warmup: float


def _validate_points(points, name):
    if not torch.is_tensor(points) or points.ndim != 3 or points.shape[-1] != 3:
        raise ValueError(f"{name} must have shape (B, N, 3)")
    if points.shape[0] < 1 or points.shape[1] < 1:
        raise ValueError(f"{name} must be non-empty")
    if not points.is_floating_point() or not torch.isfinite(points).all():
        raise ValueError(f"{name} must contain finite floating-point values")


def residual_warmup(epoch, warmup_epochs=20):
    if epoch is None:
        return 1.0
    epoch = float(epoch)
    warmup_epochs = int(warmup_epochs)
    if not math.isfinite(epoch) or warmup_epochs <= 0:
        raise ValueError("epoch must be finite and warmup_epochs must be positive")
    return min(max(epoch / float(warmup_epochs), 0.0), 1.0)


def stable_knn_indices(query, reference, k=32):
    """Return distance-ordered KNN with original index as the tie breaker."""

    _validate_points(query, "query")
    _validate_points(reference, "reference")
    if query.shape[0] != reference.shape[0]:
        raise ValueError("query and reference batch sizes must match")
    if query.device != reference.device or query.dtype != reference.dtype:
        raise ValueError("query and reference must share device and dtype")
    k = int(k)
    if not 1 <= k <= reference.shape[1]:
        raise ValueError("k is outside the reference point count")
    distances = torch.cdist(query, reference, p=2)
    # Stable ascending sort retains ascending reference index for equal distances.
    indices = torch.argsort(distances, dim=-1, descending=False, stable=True)[
        ..., :k
    ]
    ordered = torch.gather(distances, dim=-1, index=indices)
    return indices, ordered


def gather_neighbors(points, indices):
    _validate_points(points, "points")
    if not torch.is_tensor(indices) or indices.ndim != 3:
        raise ValueError("indices must have shape (B, M, K)")
    if indices.shape[0] != points.shape[0]:
        raise ValueError("points and indices batch sizes must match")
    if indices.dtype != torch.long:
        indices = indices.long()
    if torch.any(indices < 0) or torch.any(indices >= points.shape[1]):
        raise ValueError("neighbor index is out of bounds")
    batch = torch.arange(points.shape[0], device=points.device)[:, None, None]
    return points[batch, indices]


def initialize_scqr_module(module):
    for child in module.modules():
        if isinstance(child, nn.Linear):
            nn.init.trunc_normal_(child.weight, std=0.02)
            if child.bias is not None:
                nn.init.zeros_(child.bias)
        elif isinstance(child, nn.LayerNorm):
            nn.init.ones_(child.weight)
            nn.init.zeros_(child.bias)


class RawLocalGeometryResidual(nn.Module):
    """Two-scale KNN16/KNN32 descriptor added to encoder proxy features."""

    def __init__(
        self,
        embed_dim=384,
        small_k=16,
        large_k=32,
        alpha_init=0.01,
        warmup_epochs=20,
    ):
        super().__init__()
        self.embed_dim = int(embed_dim)
        self.small_k = int(small_k)
        self.large_k = int(large_k)
        self.warmup_epochs = int(warmup_epochs)
        if self.embed_dim != 384:
            raise ValueError("Cranial-SCQR v1.1 requires embed_dim=384")
        if (self.small_k, self.large_k) != (16, 32):
            raise ValueError("Cranial-SCQR v1.1 requires KNN16/KNN32")
        self.point_mlp = nn.Sequential(
            nn.Linear(4, 32),
            nn.GELU(),
            nn.Linear(32, 64),
        )
        self.scale_fusion = nn.Sequential(
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Linear(128, self.embed_dim),
            nn.LayerNorm(self.embed_dim, eps=1.0e-5),
        )
        # A length-one vector is semantically scalar and enters the existing
        # optimizer's one-dimensional no-weight-decay group.
        self.alpha_l = nn.Parameter(torch.tensor([float(alpha_init)]))
        initialize_scqr_module(self)

    def _pool_scale(self, partial, proxies, indices):
        neighbors = gather_neighbors(partial, indices)
        relative = neighbors - proxies.unsqueeze(2)
        radius = torch.linalg.vector_norm(relative, dim=-1, keepdim=True)
        encoded = self.point_mlp(torch.cat([relative, radius], dim=-1))
        return torch.cat([encoded.amax(dim=2), encoded.mean(dim=2)], dim=-1)

    def forward(self, features, proxies, partial, epoch=None):
        if (
            not torch.is_tensor(features)
            or features.ndim != 3
            or features.shape[-1] != self.embed_dim
        ):
            raise ValueError("features must have shape (B, N_PROXY, 384)")
        _validate_points(proxies, "proxies")
        _validate_points(partial, "partial")
        if features.shape[:2] != proxies.shape[:2]:
            raise ValueError("features and proxies must describe the same tokens")
        if not (
            features.device == proxies.device == partial.device
            and features.dtype == proxies.dtype == partial.dtype
        ):
            raise ValueError("features, proxies, and partial must share device/dtype")
        indices, distances = stable_knn_indices(
            proxies, partial, k=self.large_k
        )
        small = self._pool_scale(partial, proxies, indices[..., : self.small_k])
        large = self._pool_scale(partial, proxies, indices)
        local_embedding = self.scale_fusion(torch.cat([small, large], dim=-1))
        warmup = residual_warmup(epoch, self.warmup_epochs)
        residual = self.alpha_l.reshape(1, 1, 1) * warmup * local_embedding
        return LocalGeometryOutput(
            features=features + residual,
            knn32_indices=indices,
            knn32_radius_normalized=distances[..., -1],
            local_embedding=local_embedding,
            residual=residual,
            warmup=warmup,
        )
