"""Isolated second SCQ head. Inputs are D-derived Memory and graph-bearing Q1 only."""
import hashlib
import math
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as functional

SHAPES = {'V1.weight': (128, 1802), 'V1.bias': (128,),
          'V2.weight': (3, 128), 'V2.bias': (3,)}
SEED = 2026111402


def require(ok, message):
    if not ok:
        raise ValueError(message)


def initialization_values():
    """Linear-default equivalent initialization using a private CPU random stream."""
    g = torch.Generator(device='cpu').manual_seed(SEED)
    weight = torch.empty(128, 1802).uniform_(-1 / math.sqrt(1802), 1 / math.sqrt(1802), generator=g)
    bias = torch.empty(128).uniform_(-1 / math.sqrt(1802), 1 / math.sqrt(1802), generator=g)
    return {'V1.weight': weight, 'V1.bias': bias,
            'V2.weight': torch.zeros(3, 128), 'V2.bias': torch.zeros(3)}


def load_initialization(record):
    """Frozen little-endian FP32 bytes are authoritative; seed is provenance only."""
    import sys
    require(sys.byteorder == 'little', 'RF initialization byte order')
    require(tuple(SHAPES.items()) == (('V1.weight', (128, 1802)), ('V1.bias', (128,)),
                                     ('V2.weight', (3, 128)), ('V2.bias', (3,))), 'RF fixed layout')
    raw = Path(record['path']).read_bytes()
    require(len(raw) == record['bytes'] == 231171 * 4, 'RF initialization size')
    require(hashlib.sha256(raw).hexdigest() == record['sha256'], 'RF initialization SHA256')
    flat = torch.frombuffer(bytearray(raw), dtype=torch.float32)
    values, offset = {}, 0
    for name, shape in SHAPES.items():
        count = math.prod(shape)
        values[name] = flat[offset:offset + count].reshape(shape).clone()
        offset += count
    require(offset == flat.numel() and all(t.dtype == torch.float32 and t.device.type == 'cpu'
                                          and tuple(t.shape) == SHAPES[k] for k, t in values.items()), 'RF decoded structure')
    require(all(bool(torch.isfinite(x).all()) for x in values.values()), 'RF initialization finite')
    require(bool((values['V2.weight'] == 0).all()) and bool((values['V2.bias'] == 0).all()), 'RF zero output')
    return values


class RFResidual(nn.Module):
    def __init__(self, variant, knn, initialization):
        super().__init__()
        require(variant in ('RF-Static', 'RF-Requery'), 'RF variant')
        self.variant, self.knn = variant, knn
        with torch.random.fork_rng(devices=[]):
            self.V1 = nn.Linear(1802, 128)
            self.V2 = nn.Linear(128, 3)
        self.load_state_dict(load_initialization(initialization), strict=True)

    def describe(self, M, F, z, Q1, N0):
        b = Q1.shape[0]
        require(b > 0 and Q1.shape == M.shape == (b, 256, 3)
                and F.shape == (b, 256, 384) and z.shape == (b, 1024), 'RF shapes')
        require(all(x.dtype == torch.float32 and x.device == Q1.device
                    and bool(torch.isfinite(x).all()) for x in (M, F, z, Q1)), 'RF finite FP32 device')
        require(N0.shape == (b, 256, 8) and N0.dtype == torch.int64 and N0.device == M.device
                and bool((N0 >= 0).all()) and bool((N0 < 256).all()), 'RF N0')
        # The sole arm-dependent computational branch. Integer selection has no gradient.
        with torch.no_grad():
            idx = N0 if self.variant == 'RF-Static' else self.knn(8, M, Q1)
        require(idx.shape == N0.shape and idx.dtype == N0.dtype and idx.device == M.device
                and bool((idx >= 0).all()) and bool((idx < 256).all()), 'RF selected indices')
        batch = torch.arange(b, device=M.device)[:, None, None]
        nf = functional.layer_norm(F, (384,), eps=1e-5)[batch, idx]
        fa, fm = nf.mean(2), nf.max(2).values
        d = M[batch, idx] - Q1[:, :, None, :]
        mean = d.mean(2)
        sigma = ((d - mean[:, :, None, :]).square().mean(2) + 1e-6).sqrt()
        rho = torch.linalg.vector_norm(d, dim=-1).mean(2, keepdim=True)
        geometry = torch.cat((mean, sigma, rho), -1)
        h = torch.cat((z[:, None, :].expand(-1, 256, -1), fa, fm, Q1, geometry), -1)
        return h, dict(indices=idx, fa=fa, fm=fm, geometry=geometry)

    def forward(self, M, F, z, Q1, N0):
        h, info = self.describe(M, F, z, Q1, N0)
        delta1 = self.V2(functional.gelu(self.V1(h), approximate='none'))
        Q2 = Q1 + delta1
        require(bool(torch.isfinite(Q2).all()), 'RF nonfinite Q2')
        record = {k: v.detach() for k, v in dict(Q1=Q1, Q2=Q2, delta1=delta1, **info).items()}
        return Q2, record
