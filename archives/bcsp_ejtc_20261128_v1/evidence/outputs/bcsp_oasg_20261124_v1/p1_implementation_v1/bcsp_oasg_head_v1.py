"""Observation-anchored coarse generation at the existing LQI token resolution."""

import hashlib
from pathlib import Path

import torch
from torch import nn


HEAD_SEED = 2026112402
HEAD_PARAMETERS = 1840643
INITIALIZER_BYTES = HEAD_PARAMETERS * 4


class ObservationAnchoredHead(nn.Sequential):
    def __init__(self):
        super().__init__(
            nn.Linear(1411, 1024, device="cpu", dtype=torch.float32),
            nn.GELU(),
            nn.Linear(1024, 384, device="cpu", dtype=torch.float32),
            nn.GELU(),
            nn.Linear(384, 3, device="cpu", dtype=torch.float32),
        )

    def forward(self, z, memory, coordinates):
        batch = coordinates.shape[0]
        if (coordinates.shape != (batch, 256, 3)
                or memory.shape != (batch, 256, 384)
                or z.shape != (batch, 1024)):
            raise ValueError("OASG requires paired 256-token coordinates and features")
        features = torch.cat((z.unsqueeze(1).expand(-1, 256, -1), memory, coordinates), dim=-1)
        delta = super().forward(features)
        return coordinates + delta, delta


def initializer_bytes():
    """Generate the initializer once on the designated CPU, in a private stream."""
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(HEAD_SEED)
        head = ObservationAnchoredHead()
    return b"".join(p.detach().numpy().astype("<f4", copy=False).tobytes() for p in head.parameters())


def load_head(record):
    """Use the frozen bytes; runtime PyTorch need not reproduce CPU initialization."""
    if record["seed"] != HEAD_SEED or record["bytes"] != INITIALIZER_BYTES:
        raise ValueError("OASG initializer seed or size")
    path = Path(record["path"])
    with path.open("rb") as source:
        raw = source.read(INITIALIZER_BYTES + 1)
    if len(raw) != INITIALIZER_BYTES or hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise ValueError("OASG initializer SHA256 or size mismatch")
    with torch.random.fork_rng(devices=[]):
        head = ObservationAnchoredHead()
    values = torch.frombuffer(bytearray(raw), dtype=torch.float32)
    if not torch.isfinite(values).all():
        raise ValueError("nonfinite OASG initializer")
    cursor = 0
    with torch.no_grad():
        for parameter in head.parameters():
            segment = values[cursor:cursor + parameter.numel()]
            parameter.copy_(segment.reshape_as(parameter))
            cursor += parameter.numel()
    return head
