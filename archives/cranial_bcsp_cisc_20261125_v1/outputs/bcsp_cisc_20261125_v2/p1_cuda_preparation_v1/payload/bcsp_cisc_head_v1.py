"""CISC spatial and uniform support on the existing OASG coarse head."""

import math
from typing import NamedTuple

import torch
from torch import nn
from torch.nn import functional as F


N_INPUT = 8192
N_TOKEN = 256
CHUNK = 1024
EPS = 1e-4
AUX_WEIGHT = 0.05
EXTRA_PARAMETERS = 61057


class Condition(NamedTuple):
    descriptor: torch.Tensor
    logits: torch.Tensor
    index: torch.Tensor
    counts: torch.Tensor


def assign(points, anchors):
    """Nearest native token in FP32; argmin resolves exact ties by index."""
    with torch.no_grad():
        indices = []
        for part in points.split(CHUNK, dim=1):
            difference = part[:, :, None] - anchors[:, None]
            indices.append(difference.square().sum(dim=-1).argmin(dim=-1))
        index = torch.cat(indices, dim=1)
        counts = index.new_zeros((len(points), anchors.shape[1]))
        counts.scatter_add_(1, index, torch.ones_like(index))
    return index, counts


def describe(points, anchors, index, counts, logits, arm):
    support = logits.sigmoid().clamp(EPS, 1 - EPS)
    mass = (support * (counts / points.shape[1])).sum(dim=1, keepdim=True)
    uniform = mass.expand_as(support)
    r = torch.where(counts > 0, support, uniform) if arm == "I" else uniform
    weights = r.gather(1, index)
    alpha = weights / weights.sum(dim=1, keepdim=True)
    center = (alpha[..., None] * points).sum(dim=1)
    diff = points - center[:, None]
    cov = (diff * alpha[..., None]).transpose(1, 2) @ diff
    cov6 = torch.stack((cov[:, 0, 0], cov[:, 1, 1], cov[:, 2, 2],
                        cov[:, 0, 1], cov[:, 0, 2], cov[:, 1, 2]), dim=-1)
    return torch.cat((r[..., None], uniform[..., None], anchors - center[:, None],
                      cov6[:, None].expand(-1, anchors.shape[1], -1)), dim=-1)


class CutConditioner(nn.Module):
    def __init__(self, arm, prior, seed):
        super().__init__()
        if arm not in ("U", "I") or type(seed) is not int or not 0 <= prior <= 1:
            raise ValueError("invalid CISC arm, seed or Fold prior")
        self.arm = arm
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(seed)
            self.first = nn.Linear(387, 128, device="cpu", dtype=torch.float32)
            self.last = nn.Linear(128, 1, device="cpu", dtype=torch.float32)
        prior = min(max(prior, EPS), 1 - EPS)
        nn.init.zeros_(self.last.weight)
        nn.init.constant_(self.last.bias, math.log(prior / (1 - prior)))

    def forward(self, points, anchors, features):
        batch = points.shape[0]
        inputs = (points, anchors, features)
        if (tuple(x.shape for x in inputs) != ((batch, N_INPUT, 3), (batch, N_TOKEN, 3), (batch, N_TOKEN, 384))
                or any(x.dtype != torch.float32 or x.device != points.device for x in inputs)):
            raise ValueError("CISC requires paired FP32 input, anchors and Memory")
        index, counts = assign(points, anchors)
        reference = torch.cat((F.layer_norm(features, (384,), eps=1e-5), anchors), dim=-1)
        logits = self.last(F.gelu(self.first(reference))).squeeze(-1)
        return Condition(describe(points, anchors, index, counts, logits, self.arm),
                         logits, index, counts)


class CiscObservationHead(nn.Sequential):
    def __init__(self, original, arm, prior, seed):
        # Reuse the original tensors and their state_dict names.
        super().__init__(*original.children())
        self.conditioner = CutConditioner(arm, prior, seed)
        with torch.random.fork_rng(devices=[]):
            self.condition_map = nn.Linear(11, 1024, bias=False, device="cpu", dtype=torch.float32)
        nn.init.zeros_(self.condition_map.weight)

    def forward(self, z, features, anchors, points):
        if z.shape != (points.shape[0], 1024) or z.dtype != torch.float32 or z.device != points.device:
            raise ValueError("CISC requires the original FP32 global summary")
        condition = self.conditioner(points, anchors, features)
        u = torch.cat((z[:, None].expand(-1, N_TOKEN, -1), features, anchors), dim=-1)
        hidden = self[1](self[0](u) + self.condition_map(condition.descriptor))
        delta = self[4](self[3](self[2](hidden)))
        return anchors + delta, delta


def auxiliary_loss(condition, labels):
    """The source-face labels enter here, after the model forward."""
    if (labels.dtype != torch.bool or labels.shape != condition.index.shape
            or labels.device != condition.logits.device):
        raise ValueError("CISC labels must be aligned Boolean input rows")
    positives = condition.counts.new_zeros(condition.counts.shape)
    positives.scatter_add_(1, condition.index, labels.to(dtype=positives.dtype))
    target = positives / condition.counts.clamp_min(1)
    weights = condition.counts / labels.shape[1]
    per_cell = F.binary_cross_entropy_with_logits(condition.logits, target, reduction="none")
    return (weights * per_cell).sum(dim=1).mean()
