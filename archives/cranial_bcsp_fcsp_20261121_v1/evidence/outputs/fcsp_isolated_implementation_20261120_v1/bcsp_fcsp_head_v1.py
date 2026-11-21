"""Fixed-cardinality placement head and D-only coarse descriptors."""

import math

import torch
from torch import nn


PARENTS = 256
CHILDREN = 32
INPUT_POINTS = 8192
GEOMETRY_DIM = 10


def require_fp32(name, value, shape):
    if (not isinstance(value, torch.Tensor) or value.dtype != torch.float32
            or tuple(value.shape) != shape or not bool(torch.isfinite(value).all())):
        raise ValueError(f"{name} must be finite FP32 with shape {shape}")


@torch.no_grad()
def coarse_geometry(q):
    """Return local descriptors, neighbor slots, and unregularized local scales."""
    if q.ndim != 3 or q.shape[0] == 0:
        raise ValueError("nonempty batched coarse point cloud required")
    batch = q.shape[0]
    require_fp32("Q", q, (batch, PARENTS, 3))
    relative = q[:, None, :, :] - q[:, :, None, :]
    distance2 = relative.square().sum(dim=-1)
    if not bool(torch.isfinite(distance2).all()):
        raise ValueError("coarse pairwise distance overflow")
    own_slot = torch.eye(PARENTS, dtype=torch.bool, device=q.device)[None]
    distance2 = distance2.masked_fill(own_slot, float("inf"))
    neighbors = torch.argsort(distance2, dim=-1, stable=True)[..., :8]
    vectors = relative.gather(2, neighbors[..., None].expand(-1, -1, -1, 3))
    scale = vectors.square().sum(dim=-1).mean(dim=-1).sqrt()
    unit = vectors / (scale[..., None, None] + 1e-6)
    x, y, z = unit.unbind(-1)
    moments = torch.stack((x*x, x*y, x*z, y*y, y*z, z*z), dim=-1).mean(dim=-2)
    local = torch.cat((unit.mean(dim=-2), moments, (scale + 1e-6).log()[..., None]), dim=-1)
    require_fp32("local geometry", local, (batch, PARENTS, GEOMETRY_DIM))
    return local, neighbors, scale


def geometry_condition(local, arm):
    if local.ndim != 3 or local.shape[0] == 0:
        raise ValueError("nonempty batched geometry required")
    require_fp32("local geometry", local, (local.shape[0], PARENTS, GEOMETRY_DIM))
    if arm == "B0-Global":
        return local.mean(dim=1, keepdim=True).expand_as(local)
    if arm == "B1-Local":
        return local
    raise ValueError(f"unknown FCSP arm: {arm}")


@torch.no_grad()
def fit_residual_scale(train_q, train_p0):
    """Pooled FP64 linear 95th percentile from caller-selected training cases."""
    if train_q.ndim != 3 or train_q.shape[0] == 0:
        raise ValueError("nonempty training cache required")
    cases = train_q.shape[0]
    require_fp32("training Q", train_q, (cases, PARENTS, 3))
    require_fp32("training P0", train_p0, (cases, PARENTS, CHILDREN, 3))
    q = train_q.detach().to(device="cpu", dtype=torch.float64)
    p = train_p0.detach().to(device="cpu", dtype=torch.float64)
    offsets = torch.linalg.vector_norm(p - q.unsqueeze(-2), dim=-1)
    scale = float(torch.quantile(offsets.flatten(), .95, interpolation="linear"))
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("invalid pooled native residual scale")
    return scale


class PlacementHead(nn.Module):
    def __init__(self, parent_width, b_train):
        super().__init__()
        if type(parent_width) is not int or parent_width <= 0:
            raise ValueError("positive measured parent width required")
        scale = torch.tensor(b_train, dtype=torch.float32)
        if scale.ndim != 0 or not bool(torch.isfinite(scale)) or not bool(scale > 0):
            raise ValueError("invalid FP32 residual scale")
        self.parent_width = parent_width
        self.register_buffer("b_train", scale)
        self.net = nn.Sequential(
            nn.Linear(parent_width + GEOMETRY_DIM, 128, dtype=torch.float32),
            nn.GELU(),
            nn.Linear(128, CHILDREN * 3, dtype=torch.float32),
        )
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, h, condition, p0):
        if h.ndim != 3 or h.shape[0] == 0:
            raise ValueError("nonempty batched H required")
        batch = h.shape[0]
        require_fp32("H", h, (batch, PARENTS, self.parent_width))
        require_fp32("condition", condition, (batch, PARENTS, GEOMETRY_DIM))
        require_fp32("P0", p0, (batch, PARENTS, CHILDREN, 3))
        x = torch.cat((h.detach(), condition.detach()), dim=-1)
        logits = self.net(x).reshape_as(p0)
        require_fp32("placement logits", logits, tuple(p0.shape))
        shifted = p0.detach() + self.b_train * logits.tanh()
        require_fp32("placement output", shifted, tuple(p0.shape))
        return shifted
