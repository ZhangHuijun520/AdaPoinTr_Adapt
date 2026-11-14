"""F0-P-v2 isolated decoder. Native mixers are supplied by the frozen factory."""
import torch
from torch import nn
from bcsp_mamba_encoder_v1 import lexicographic_order, gather_tokens


def require(ok, message):
    if not ok:
        raise ValueError(message)


def tensor_input(x, n, width):
    require(x.ndim == 3 and x.shape[1:] == (n, width), 'fixed tensor shape')
    require(x.dtype == torch.float32 and bool(torch.isfinite(x).all()), 'finite FP32')


class F0Block(nn.Module):
    def __init__(self, old, index, mixer_builder):
        super().__init__()
        require(index in range(8), 'eight blocks')
        require(old.self_attn_combine_style == old.cross_attn_combine_style == 'concat', 'concat')
        require(old.self_attn_block_length == old.cross_attn_block_length == (2 if index == 0 else 1), 'graph placement')
        for name in ['norm1', 'norm_q', 'norm_v', 'norm2']:
            norm = getattr(old, name)
            require(tuple(norm.normalized_shape) == (384,) and norm.eps == 1e-6, 'frozen norm')
        require(old.mlp.fc1.in_features == 384 and old.mlp.fc1.out_features == 768, 'FFN width')
        for name in ['norm1', 'norm_q', 'norm_v', 'norm2', 'mlp', 'drop_path1', 'ls1', 'drop_path4', 'ls4', 'drop_path2', 'ls2']:
            self.add_module(name, getattr(old, name))
        for name in ['drop_path1', 'ls1', 'drop_path4', 'ls4', 'drop_path2', 'ls2']:
            require(isinstance(getattr(self, name), nn.Identity), 'frozen residual identity')
        require(all(not isinstance(m, nn.Dropout) or m.p == 0 for m in self.mlp.modules()), 'no dropout')
        self.local_self_attn = old.local_self_attn
        self.local_cross_attn = old.local_cross_attn
        require((self.local_self_attn is not None) == (index == 0), 'local self placement')
        require((self.local_cross_attn is not None) == (index == 0), 'local cross placement')
        if index == 0:
            require(type(self.local_self_attn).__name__ == type(self.local_cross_attn).__name__ == 'DynamicGraphAttention', 'audited local graph only')
            self.self_attn_merge_map = old.self_attn_merge_map
            self.cross_attn_merge_map = old.cross_attn_merge_map
            for m in [self.self_attn_merge_map, self.cross_attn_merge_map]:
                require(m.in_features == 768 and m.out_features == 384, 'merge width')
        self.self_ssm = mixer_builder()
        self.cond_ssm = mixer_builder()

    def forward(self, x, memory, q_pos, m_pos, q_pe, m_pe, order_q, inverse_q, order_m, self_idx, cross_idx, trace=False):
        original = x
        ns = self.norm1(x)
        u = gather_tokens(ns + q_pe, order_q).contiguous()
        y = (self.self_ssm(u) + self.self_ssm(u.flip(1).contiguous()).flip(1)) * .5
        bq = gather_tokens(y, inverse_q)
        if self.local_self_attn is not None:
            bq = self.self_attn_merge_map(torch.cat([bq, self.local_self_attn(ns, q_pos, idx=self_idx)], -1))
        x1 = x + self.drop_path1(self.ls1(bq))
        nq, nv = self.norm_q(x1), self.norm_v(memory)
        prefix = gather_tokens(nv + m_pe, order_m)
        suffix = gather_tokens(nq + q_pe, order_q)
        c = self.cond_ssm(torch.cat([prefix, suffix], 1).contiguous())
        require(c.shape == (x.shape[0], 512, 384), 'conditional output shape')
        cq = gather_tokens(c[:, 256:], inverse_q)
        f = cq
        if self.local_cross_attn is not None:
            local = self.local_cross_attn(q=nq, v=nv, q_pos=q_pos, v_pos=m_pos, idx=cross_idx)
            f = self.cross_attn_merge_map(torch.cat([cq, local], -1))
        x2 = x1 + self.drop_path4(self.ls4(f))
        result = x2 + self.drop_path2(self.ls2(self.mlp(self.norm2(x2))))
        require(bool(torch.isfinite(result).all()), 'decoder nonfinite')
        if not trace:
            return result
        return result, dict(input=original.detach(), after_self=x1.detach(), prefix_suffix=cq.detach(), after_cross=x2.detach(), output=result.detach())


class F0Decoder(nn.Module):
    """Compatible mother decoder entry; no cache, token roles or GT argument."""
    def __init__(self, old, mixer_builder):
        super().__init__()
        require(len(old.blocks.blocks) == 8 and old.blocks.k == 8, 'eight layers/k8')
        self.knn = type(old.blocks).forward.__globals__['knn_point']
        self.coordinate_pe = nn.Linear(3, 384, bias=False)
        self.blocks = nn.ModuleList([F0Block(block, i, mixer_builder) for i, block in enumerate(old.blocks.blocks)])

    def forward(self, q, v, q_pos, v_pos, denoise_length=None, return_instrumentation=False):
        require(denoise_length is None, 'denoise disabled')
        require(not return_instrumentation or not self.training, 'full trace inference only')
        for t, width in [(q, 384), (v, 384), (q_pos, 3), (v_pos, 3)]:
            tensor_input(t, 256, width)
            require(t.shape[0] == q.shape[0] and t.device == q.device, 'batch/device consistency')
        pq, iq = lexicographic_order(q_pos.detach())
        pm, _ = lexicographic_order(v_pos.detach())
        self_idx = self.knn(8, q_pos, q_pos)
        cross_idx = self.knn(8, v_pos, q_pos)
        qp, mp = self.coordinate_pe(q_pos), self.coordinate_pe(v_pos)
        records = []
        for i, block in enumerate(self.blocks):
            result = block(q, v, q_pos, v_pos, qp, mp, pq, iq, pm, self_idx, cross_idx, return_instrumentation)
            if return_instrumentation:
                q, record = result
                records.append(dict(layer_index=i, **record))
            else:
                q = result
        return (q, records) if return_instrumentation else q
