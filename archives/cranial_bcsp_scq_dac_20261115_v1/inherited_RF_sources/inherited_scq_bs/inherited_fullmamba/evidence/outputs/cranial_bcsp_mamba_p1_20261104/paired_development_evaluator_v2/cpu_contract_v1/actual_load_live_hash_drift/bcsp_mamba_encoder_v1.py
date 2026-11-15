!""P1 encoder global-branch replacement. No legacy model/package imports."""
import torch
from torch import nn


def lexicographic_order(pos):
    if pos.ndim != 3 or pos.shape[-1] != 3 or not pos.is_floating_point():
        raise ValueError('B,N,3 floating coordinates required')
    if not bool(torch.isfinite(pos).all()):
        raise ValueError('nonfinite coordinates')
    order = torch.arange(pos.shape[1], device=pos.device).expand(pos.shape[0], -1)
    # Stable z, then y, then x: exact ties retain original input index.
    for axis in (2, 1, 0):
        values = pos[..., axis].gather(1, order)
        order = order.gather(1, torch.argsort(values, dim=1, stable=True))
    inverse = torch.empty_like(order)
    inverse.scatter_(1, order, torch.arange(pos.shape[1], device=pos.device).expand_as(order))
    return order, inverse


def gather_tokens(x, order):
    return x.gather(1, order.unsqueeze(-1).expand(-1, -1, x.shape[-1]))


class BidirectionalSpatialMamba(nn.Module):
    def __init__(self, mixer):
        super().__init__()
        self.mixer = mixer  # One parameter set, two scans; no inference cache.

    def forward(self, x, pos):
        if x.ndim != 3 or x.shape[:2] != pos.shape[:2] or x.shape[-1] != 384:
            raise ValueError('matching B,N,384 features and coordinates required')
        if x.device != pos.device or x.dtype != torch.float32 or not bool(torch.isfinite(x).all()):
            raise ValueError('finite FP32 features on coordinate device required')
        order, inverse = lexicographic_order(pos)
        sorted_x = gather_tokens(x, order).contiguous()
        forward = self.mixer(sorted_x)
        reverse = self.mixer(sorted_x.flip(1).contiguous()).flip(1)
        if forward.shape != x.shape or reverse.shape != x.shape:
            raise ValueError('SSM output shape drift')
        result = gather_tokens((forward + reverse) * 0.5, inverse)
        if result.dtype != x.dtype or not bool(torch.isfinite(result).all()):
            raise ValueError('SSM nonfinite/dtype drift')
        return result


class MambaEncoderBlock(nn.Module):
    """Same residual/graph/merge/FFN computation, with xyz passed to global branch."""
    def __init__(self, legacy, branch):
        super().__init__()
        if legacy.combine_style != 'concat' or legacy.block_length not in (1, 2):
            raise ValueError('only frozen concat encoder blocks supported')
        if legacy.attn is None:
            raise ValueError('legacy global branch missing')
        self.combine_style = legacy.combine_style
        self.block_length = legacy.block_length
        # In attention-only blocks None is an ordinary attribute, not in _modules.
        self.local_attn = legacy.local_attn
        for name, module in legacy._modules.items():
            self.add_module(name, branch if name == 'attn' else module)

    def forward(self, x, pos, idx=None):
        norm_x = self.norm1(x)
        global_feature = self.attn(norm_x, pos)
        if self.block_length == 2:
            if self.local_attn is None:
                raise ValueError('frozen graph branch missing')
            local_feature = self.local_attn(norm_x, pos, idx=idx)
            feature = self.merge_map(torch.cat([global_feature, local_feature], dim=-1))
        else:
            if self.local_attn is not None:
                raise ValueError('unexpected local branch')
            feature = global_feature
        x = x + self.drop_path1(self.ls1(feature))
        return x + self.drop_path2(self.ls2(self.mlp(self.norm2(x))))
