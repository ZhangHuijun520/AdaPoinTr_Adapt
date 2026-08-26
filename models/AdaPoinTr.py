##############################################################
# % Author: Castle
# % Date:01/12/2022
###############################################################

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from functools import partial, reduce
from timm.models.layers import DropPath, trunc_normal_
from extensions.chamfer_dist import ChamferDistanceL1, ChamferDistanceL1Directional
from .build import MODELS, build_model_from_cfg
from models.Transformer_utils import *
from utils import misc
from utils.mamba_d22_geometry import (
    global_moment_trust_loss,
    local_rim_undercoverage_loss,
)
from utils.mamba_d3_contact import (
    assign_reference_rim_to_proxies,
    case_balanced_binary_cross_entropy,
    dense_contact_safety_loss,
    diversified_topk_indices,
    gather_points,
)


def coarse_geometry_guard_components(
        pred_coarse,
        gt,
        smooth_l1_beta=0.1,
        cvar_fraction=0.1,
        eps=1.0e-6,
        requested_mode=None):
    """Return scale-normalized coarse geometry losses for training only."""
    if pred_coarse.ndim != 3 or gt.ndim != 3:
        raise ValueError('pred_coarse and gt must have shape [B, N, 3]')
    if pred_coarse.size(0) != gt.size(0) or pred_coarse.size(-1) != 3:
        raise ValueError('pred_coarse and gt batch/coordinate dimensions differ')
    if not 0.0 < cvar_fraction <= 1.0:
        raise ValueError('cvar_fraction must be in (0, 1]')
    if smooth_l1_beta <= 0 or eps <= 0:
        raise ValueError('smooth_l1_beta and eps must be positive')
    allowed_modes = {None, 'centroid', 'centroid_radius', 'coverage_cvar'}
    if requested_mode not in allowed_modes:
        raise ValueError(f'Unsupported requested_mode={requested_mode!r}')

    gt_centroid = gt.mean(dim=1)
    pred_centroid = pred_coarse.mean(dim=1)
    gt_radius = torch.sqrt(
        torch.mean(torch.sum((gt - gt_centroid.unsqueeze(1)) ** 2, dim=-1), dim=1)
        + eps
    )
    pred_radius = torch.sqrt(
        torch.mean(
            torch.sum(
                (pred_coarse - pred_centroid.unsqueeze(1)) ** 2,
                dim=-1,
            ),
            dim=1,
        )
        + eps
    )

    centroid_offset = torch.linalg.vector_norm(
        pred_centroid - gt_centroid,
        dim=-1,
    ) / gt_radius
    radius_log_ratio = torch.log((pred_radius + eps) / (gt_radius + eps))
    centroid = F.smooth_l1_loss(
        centroid_offset,
        torch.zeros_like(centroid_offset),
        beta=smooth_l1_beta,
    )
    radius = F.smooth_l1_loss(
        radius_log_ratio,
        torch.zeros_like(radius_log_ratio),
        beta=smooth_l1_beta,
    )

    components = {
        'centroid': centroid,
        'radius': radius,
        'centroid_radius': 0.5 * (centroid + radius),
    }
    if requested_mode in (None, 'coverage_cvar'):
        gt_to_coarse = (
            torch.cdist(gt, pred_coarse).amin(dim=-1)
            / gt_radius.unsqueeze(1)
        )
        tail_count = max(1, int(math.ceil(gt.size(1) * cvar_fraction)))
        components['coverage_cvar'] = torch.topk(
            gt_to_coarse,
            k=tail_count,
            dim=1,
            largest=True,
            sorted=False,
        ).values.mean()
    return components


def patch_local_chamfer(pred_coarse, pred_fine, gt, factor, loss_func):
    """Match each query's fine patch to the factor nearest GT points."""
    batch_size, num_queries, _ = pred_coarse.shape
    if pred_fine.size(1) != num_queries * factor:
        raise ValueError(
            'pred_fine cannot be reshaped into query-local patches: '
            f'{pred_fine.size(1)} != {num_queries} * {factor}'
        )
    target_index = knn_point(factor, gt, pred_coarse)
    target_patches = index_points(gt, target_index)
    pred_patches = pred_fine.reshape(batch_size * num_queries, factor, 3)
    target_patches = target_patches.reshape(
        batch_size * num_queries,
        factor,
        3,
    )
    return loss_func(pred_patches, target_patches)


class GatedConvSequenceMixer(nn.Module):
    """Small dependency-free mixer for adapter smoke tests.

    The real Mamba adapter uses mamba_ssm when available. This mixer keeps the
    same BNC interface so configs can be debugged without the CUDA extension.
    """

    def __init__(self, dim, d_conv=4, expand=2):
        super().__init__()
        hidden_dim = int(dim * expand)
        padding = max(int(d_conv) - 1, 0)
        self.in_proj = nn.Linear(dim, hidden_dim * 2)
        self.dwconv = nn.Conv1d(
            hidden_dim,
            hidden_dim,
            kernel_size=int(d_conv),
            padding=padding,
            groups=hidden_dim,
        )
        self.act = nn.SiLU()
        self.out_proj = nn.Linear(hidden_dim, dim)

    def forward(self, x):
        value, gate = self.in_proj(x).chunk(2, dim=-1)
        value = self.dwconv(value.transpose(1, 2)).transpose(1, 2)
        if value.size(1) != x.size(1):
            value = value[:, :x.size(1)]
        return self.out_proj(self.act(value) * torch.sigmoid(gate))


def build_sequence_mixer(dim, adapter_type, d_state, d_conv, expand, use_fast_path):
    if adapter_type == 'mamba_ssm':
        try:
            try:
                from mamba_ssm import Mamba
            except ImportError:
                from mamba_ssm.modules.mamba_simple import Mamba
        except ImportError as exc:
            raise ImportError(
                "mamba_ssm is required when mamba_adapter.adapter_type="
                "'mamba_ssm'. Install mamba-ssm in the training environment "
                "or set adapter_type: gated_conv for a dependency-free smoke "
                "test."
            ) from exc
        try:
            return Mamba(
                d_model=dim,
                d_state=int(d_state),
                d_conv=int(d_conv),
                expand=int(expand),
                use_fast_path=bool(use_fast_path),
            )
        except TypeError:
            if not bool(use_fast_path):
                raise TypeError(
                    "The installed mamba_ssm Mamba class does not support "
                    "use_fast_path=False. Install a compatible mamba-ssm "
                    "version or enable fast path with a working "
                    "causal-conv1d CUDA extension."
                )
            return Mamba(
                d_model=dim,
                d_state=int(d_state),
                d_conv=int(d_conv),
                expand=int(expand),
            )
    if adapter_type == 'gated_conv':
        return GatedConvSequenceMixer(dim, d_conv=d_conv, expand=expand)
    raise ValueError(
        f"Unsupported mamba_adapter.adapter_type={adapter_type!r}; "
        "expected 'mamba_ssm' or 'gated_conv'"
    )


class MambaAdapterBlock(nn.Module):
    def __init__(
        self,
        dim,
        adapter_type='mamba_ssm',
        d_state=16,
        d_conv=4,
        expand=2,
        use_fast_path=True,
        drop_path=0.0,
        alpha_init=0.1,
        mechanism='o0',
        normalization_eps=1e-6,
        normalization_scale_min=0.1,
        normalization_scale_max=10.0,
        alpha_trainable=True,
    ):
        super().__init__()
        if mechanism not in {'o0', 'residual_budget', 'normalized_gate', 'bidirectional_shared'}:
            raise ValueError(f'Unsupported Mamba adapter mechanism: {mechanism!r}')
        if normalization_eps <= 0:
            raise ValueError('normalization_eps must be positive')
        if not 0 < normalization_scale_min <= normalization_scale_max:
            raise ValueError('Invalid residual normalization scale bounds')
        self.mechanism = mechanism
        self.normalization_eps = float(normalization_eps)
        self.normalization_scale_min = float(normalization_scale_min)
        self.normalization_scale_max = float(normalization_scale_max)
        self.norm = nn.LayerNorm(dim)
        self.mixer = build_sequence_mixer(
            dim=dim,
            adapter_type=adapter_type,
            d_state=d_state,
            d_conv=d_conv,
            expand=expand,
            use_fast_path=use_fast_path,
        )
        self.drop_path = DropPath(drop_path) if drop_path > 0. else nn.Identity()
        self.alpha = nn.Parameter(
            torch.tensor(float(alpha_init)),
            requires_grad=bool(alpha_trainable),
        )
        self.register_buffer('alpha_scale', torch.tensor(1.0), persistent=False)

    def set_alpha_scale(self, scale):
        self.alpha_scale.fill_(float(scale))

    def forward(self, x, return_instrumentation=False, external_alpha=None):
        normalized = self.norm(x)
        if self.mechanism == 'bidirectional_shared':
            mixed_forward = self.mixer(normalized)
            mixed_reverse = torch.flip(
                self.mixer(
                    torch.flip(normalized, dims=(1,)).contiguous()
                ),
                dims=(1,),
            ).contiguous()
            mixed = 0.5 * (mixed_forward + mixed_reverse)
        else:
            mixed = self.mixer(normalized)

        normalization_scale = mixed.new_ones((mixed.size(0), 1, 1))
        if self.mechanism == 'normalized_gate':
            input_rms = torch.sqrt(
                torch.mean(x.float().square(), dim=(1, 2), keepdim=True)
            )
            mixed_rms = torch.sqrt(
                torch.mean(mixed.float().square(), dim=(1, 2), keepdim=True)
            )
            normalization_scale = (
                input_rms / mixed_rms.clamp_min(self.normalization_eps)
            ).clamp(
                min=self.normalization_scale_min,
                max=self.normalization_scale_max,
            ).to(dtype=mixed.dtype)
            mixed = mixed * normalization_scale

        alpha = self.alpha if external_alpha is None else external_alpha
        residual = self.alpha_scale * alpha * self.drop_path(mixed)
        output = x + residual
        if not return_instrumentation:
            return output
        return output, {
            'input': x.detach(),
            'normalized': normalized.detach(),
            'mixed': mixed.detach(),
            'residual': residual.detach(),
            'output': output.detach(),
            'alpha': alpha.detach(),
            'alpha_scale': self.alpha_scale.detach(),
            'normalization_scale': normalization_scale.detach(),
            'mechanism': self.mechanism,
        }


class MambaSequenceAdapter(nn.Module):
    def __init__(self, dim, config):
        super().__init__()
        self.enabled = bool(getattr(config, 'enabled', False)) if config else False
        self.order = getattr(config, 'order', 'xyz') if config else 'xyz'
        self.mechanism = getattr(config, 'mechanism', 'o0') if config else 'o0'
        self.instrumentation_enabled = False
        self._last_instrumentation = None
        if not self.enabled:
            self.blocks = nn.ModuleList()
            return

        adapter_type = getattr(config, 'adapter_type', 'mamba_ssm')
        depth = int(getattr(config, 'depth', 1))
        d_state = int(getattr(config, 'd_state', 16))
        d_conv = int(getattr(config, 'd_conv', 4))
        expand = int(getattr(config, 'expand', 2))
        use_fast_path = bool(getattr(config, 'use_fast_path', True))
        drop_path = float(getattr(config, 'drop_path', 0.0))
        alpha_init = float(getattr(config, 'alpha_init', 0.1))
        normalization_eps = float(getattr(config, 'normalization_eps', 1e-6))
        normalization_scale_min = float(
            getattr(config, 'normalization_scale_min', 0.1)
        )
        normalization_scale_max = float(
            getattr(config, 'normalization_scale_max', 10.0)
        )

        if self.mechanism not in {
            'o0', 'residual_budget', 'normalized_gate', 'bidirectional_shared'
        }:
            raise ValueError(
                f'Unsupported mamba_adapter.mechanism={self.mechanism!r}'
            )
        if self.mechanism == 'residual_budget':
            self.budget_logits = nn.Parameter(torch.zeros(depth))
            self.register_buffer(
                'total_residual_budget',
                torch.tensor(float(depth) * alpha_init),
            )
        else:
            self.register_parameter('budget_logits', None)
            self.register_buffer(
                'total_residual_budget',
                torch.tensor(0.0),
                persistent=False,
            )

        self.blocks = nn.ModuleList([
            MambaAdapterBlock(
                dim=dim,
                adapter_type=adapter_type,
                d_state=d_state,
                d_conv=d_conv,
                expand=expand,
                use_fast_path=use_fast_path,
                drop_path=drop_path,
                alpha_init=alpha_init,
                mechanism=self.mechanism,
                normalization_eps=normalization_eps,
                normalization_scale_min=normalization_scale_min,
                normalization_scale_max=normalization_scale_max,
                alpha_trainable=self.mechanism != 'residual_budget',
            )
            for _ in range(depth)
        ])

    @staticmethod
    def _ordering_indices(coor, order):
        if order in [None, 'none', 'identity']:
            return None, None
        axes_by_order = {
            'x': [0],
            'y': [1],
            'z': [2],
            'xy': [0, 1],
            'xz': [0, 2],
            'yz': [1, 2],
            'xyz': [0, 1, 2],
            'xzy': [0, 2, 1],
            'zyx': [2, 1, 0],
        }
        if order not in axes_by_order:
            raise ValueError(
                f"Unsupported mamba_adapter.order={order!r}; expected one of "
                f"{sorted(axes_by_order) + ['none', 'identity']}"
            )
        axes = axes_by_order[order]
        values = coor.detach()[..., axes]
        min_values = values.amin(dim=1, keepdim=True)
        max_values = values.amax(dim=1, keepdim=True)
        values = (values - min_values) / (max_values - min_values + 1e-6)

        key = values.new_zeros(values.shape[:2])
        weight = 1.0
        for axis_id in range(values.size(-1)):
            key = key + values[..., axis_id] * weight
            weight *= 1e-3

        sort_idx = torch.argsort(key, dim=1)
        inv_idx = torch.empty_like(sort_idx)
        arange = torch.arange(
            sort_idx.size(1),
            device=sort_idx.device,
            dtype=sort_idx.dtype,
        ).unsqueeze(0).expand_as(sort_idx)
        inv_idx.scatter_(1, sort_idx, arange)
        return sort_idx, inv_idx

    def set_alpha_scale(self, scale):
        if not self.enabled:
            return
        for block in self.blocks:
            block.set_alpha_scale(scale)

    def enable_instrumentation(self, enabled=True):
        self.instrumentation_enabled = bool(enabled)
        self._last_instrumentation = None

    def pop_instrumentation(self):
        records = self._last_instrumentation
        self._last_instrumentation = None
        return records

    @staticmethod
    def _tensor_summary(tensor, eps=1e-12):
        token_norm = torch.linalg.vector_norm(tensor.float(), dim=-1)
        rms = torch.sqrt(torch.mean(tensor.float().square(), dim=(1, 2)))
        return {
            'rms': rms,
            'token_norm_mean': token_norm.mean(dim=1),
            'token_norm_p95': torch.quantile(token_norm, 0.95, dim=1),
            'token_norm_max': token_norm.amax(dim=1),
            'token_norm_min': token_norm.amin(dim=1),
            'nonfinite_count': (~torch.isfinite(tensor)).sum(dim=(1, 2)),
            'eps': tensor.new_full((tensor.size(0),), float(eps)),
        }

    @classmethod
    def _block_instrumentation_rows(cls, block_index, tensors):
        eps = 1e-12
        input_tensor = tensors['input'].float()
        residual = tensors['residual'].float()
        input_norm = torch.linalg.vector_norm(input_tensor, dim=-1)
        residual_norm = torch.linalg.vector_norm(residual, dim=-1)
        output_delta = tensors['output'].float() - input_tensor
        ratio = residual_norm / input_norm.clamp_min(eps)
        token_count = input_tensor.size(1)
        head_count = max(1, token_count // 10)
        tail_start = token_count - head_count
        max_position = residual_norm.argmax(dim=1).float()
        if token_count > 1:
            max_position = max_position / float(token_count - 1)

        input_residual_cosine = torch.nn.functional.cosine_similarity(
            input_tensor.reshape(input_tensor.size(0), -1),
            residual.reshape(residual.size(0), -1),
            dim=1,
            eps=eps,
        )
        summaries = {
            name: cls._tensor_summary(tensor)
            for name, tensor in (
                ('input', tensors['input']),
                ('normalized', tensors['normalized']),
                ('mixed', tensors['mixed']),
                ('residual', tensors['residual']),
                ('output', tensors['output']),
            )
        }
        output_delta_rms = torch.sqrt(
            torch.mean(output_delta.square(), dim=(1, 2))
        )
        alpha = float(tensors['alpha'].float().cpu().item())
        alpha_scale = float(tensors['alpha_scale'].float().cpu().item())
        normalization_scale = tensors['normalization_scale'].float().reshape(
            input_tensor.size(0), -1
        ).mean(dim=1)

        rows = []
        for sample_index in range(input_tensor.size(0)):
            row = {
                'sample_index': sample_index,
                'block_index': int(block_index),
                'mechanism': tensors['mechanism'],
                'token_count': int(token_count),
                'feature_dim': int(input_tensor.size(2)),
                'alpha': alpha,
                'alpha_scale': alpha_scale,
                'effective_alpha': alpha * alpha_scale,
                'normalization_scale': float(
                    normalization_scale[sample_index].cpu()
                ),
                'residual_to_input_rms': float(
                    summaries['residual']['rms'][sample_index].cpu()
                    / summaries['input']['rms'][sample_index].clamp_min(eps).cpu()
                ),
                'residual_to_input_token_ratio_mean': float(
                    ratio[sample_index].mean().cpu()
                ),
                'residual_to_input_token_ratio_p95': float(
                    torch.quantile(ratio[sample_index], 0.95).cpu()
                ),
                'residual_to_input_token_ratio_max': float(
                    ratio[sample_index].amax().cpu()
                ),
                'input_residual_cosine': float(
                    input_residual_cosine[sample_index].cpu()
                ),
                'output_delta_rms': float(output_delta_rms[sample_index].cpu()),
                'residual_head_token_norm_mean': float(
                    residual_norm[sample_index, :head_count].mean().cpu()
                ),
                'residual_tail_token_norm_mean': float(
                    residual_norm[sample_index, tail_start:].mean().cpu()
                ),
                'residual_tail_to_head_ratio': float(
                    (
                        residual_norm[sample_index, tail_start:].mean()
                        / residual_norm[
                            sample_index, :head_count
                        ].mean().clamp_min(eps)
                    ).cpu()
                ),
                'residual_max_position_fraction': float(
                    max_position[sample_index].cpu()
                ),
            }
            for name, summary in summaries.items():
                for metric_name, values in summary.items():
                    if metric_name == 'eps':
                        continue
                    value = values[sample_index]
                    if metric_name == 'nonfinite_count':
                        row[f'{name}_{metric_name}'] = int(value.cpu())
                    else:
                        row[f'{name}_{metric_name}'] = float(value.cpu())
            rows.append(row)
        return rows

    @staticmethod
    def _ordering_instrumentation_rows(ordered_coor):
        coor = ordered_coor.float()
        jumps = torch.linalg.vector_norm(coor[:, 1:] - coor[:, :-1], dim=-1)
        endpoint = torch.linalg.vector_norm(coor[:, -1] - coor[:, 0], dim=-1)
        path_length = jumps.sum(dim=1)
        rows = []
        for sample_index in range(coor.size(0)):
            sample_jumps = jumps[sample_index]
            rows.append({
                'sample_index': sample_index,
                'token_count': int(coor.size(1)),
                'order': None,
                'jump_mean': float(sample_jumps.mean().cpu()),
                'jump_p95': float(
                    torch.quantile(sample_jumps, 0.95).cpu()
                ),
                'jump_max': float(sample_jumps.amax().cpu()),
                'path_length': float(path_length[sample_index].cpu()),
                'endpoint_distance': float(endpoint[sample_index].cpu()),
                'path_efficiency': float(
                    (
                        endpoint[sample_index]
                        / path_length[sample_index].clamp_min(1e-12)
                    ).cpu()
                ),
                'coordinate_nonfinite_count': int(
                    (~torch.isfinite(coor[sample_index])).sum().cpu()
                ),
            })
        return rows

    def forward(self, x, coor):
        if not self.enabled:
            return x
        if self.instrumentation_enabled and self.training:
            raise RuntimeError(
                'Mamba instrumentation is inference-only; call model.eval() '
                'before enabling it'
            )

        sort_idx, inv_idx = self._ordering_indices(coor, self.order)
        original_coor = coor
        if sort_idx is not None:
            feature_sort_idx = sort_idx.unsqueeze(-1).expand(-1, -1, x.size(-1))
            x = torch.gather(x, 1, feature_sort_idx)
            coor_sort_idx = sort_idx.unsqueeze(-1).expand(-1, -1, coor.size(-1))
            ordered_coor = torch.gather(coor, 1, coor_sort_idx)
        else:
            ordered_coor = coor

        block_rows = []
        if self.mechanism == 'residual_budget':
            block_alphas = self.total_residual_budget * torch.softmax(
                self.budget_logits, dim=0
            )
        else:
            block_alphas = [None] * len(self.blocks)
        for block_index, block in enumerate(self.blocks):
            if self.instrumentation_enabled:
                x, tensors = block(
                    x,
                    return_instrumentation=True,
                    external_alpha=block_alphas[block_index],
                )
                block_rows.extend(
                    self._block_instrumentation_rows(block_index, tensors)
                )
            else:
                x = block(x, external_alpha=block_alphas[block_index])

        if self.instrumentation_enabled:
            ordering_rows = self._ordering_instrumentation_rows(ordered_coor)
            for row in ordering_rows:
                row['order'] = self.order
            if sort_idx is None:
                sort_idx_to_save = torch.arange(
                    coor.size(1), device=coor.device
                ).unsqueeze(0).expand(coor.size(0), -1)
            else:
                sort_idx_to_save = sort_idx
            self._last_instrumentation = {
                'order': self.order,
                'mechanism': self.mechanism,
                'ordering_rows': ordering_rows,
                'block_rows': block_rows,
                'coor_original': original_coor.detach().cpu(),
                'sort_idx': sort_idx_to_save.detach().cpu(),
                'coor_ordered': ordered_coor.detach().cpu(),
            }

        if inv_idx is not None:
            inv_idx = inv_idx.unsqueeze(-1).expand(-1, -1, x.size(-1))
            x = torch.gather(x, 1, inv_idx)
        return x


class SelfAttnBlockApi(nn.Module):
    r'''
        1. Norm Encoder Block 
            block_style = 'attn'
        2. Concatenation Fused Encoder Block
            block_style = 'attn-deform'  
            combine_style = 'concat'
        3. Three-layer Fused Encoder Block
            block_style = 'attn-deform'  
            combine_style = 'onebyone'        
    '''
    def __init__(
            self, dim, num_heads, mlp_ratio=4., qkv_bias=False, drop=0., attn_drop=0., init_values=None,
            drop_path=0., act_layer=nn.GELU, norm_layer=nn.LayerNorm, block_style='attn-deform', combine_style='concat',
            k=10, n_group=2
        ):

        super().__init__()
        self.combine_style = combine_style
        assert combine_style in ['concat', 'onebyone'], f'got unexpect combine_style {combine_style} for local and global attn'
        self.norm1 = norm_layer(dim)
        self.ls1 = LayerScale(dim, init_values=init_values) if init_values else nn.Identity()
        self.drop_path1 = DropPath(drop_path) if drop_path > 0. else nn.Identity()

        self.norm2 = norm_layer(dim)
        self.ls2 = LayerScale(dim, init_values=init_values) if init_values else nn.Identity()
        self.mlp = Mlp(in_features=dim, hidden_features=int(dim * mlp_ratio), act_layer=act_layer, drop=drop)
        self.drop_path2 = DropPath(drop_path) if drop_path > 0. else nn.Identity()        

        # Api desigin
        block_tokens = block_style.split('-')
        assert len(block_tokens) > 0 and len(block_tokens) <= 2, f'invalid block_style {block_style}'
        self.block_length = len(block_tokens)
        self.attn = None
        self.local_attn = None
        for block_token in block_tokens:
            assert block_token in ['attn', 'rw_deform', 'deform', 'graph', 'deform_graph'], f'got unexpect block_token {block_token} for Block component'
            if block_token == 'attn':
                self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
            elif block_token == 'rw_deform':
                self.local_attn = DeformableLocalAttention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop, k=k, n_group=n_group)
            elif block_token == 'deform':
                self.local_attn = DeformableLocalCrossAttention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop, k=k, n_group=n_group)
            elif block_token == 'graph':
                self.local_attn = DynamicGraphAttention(dim, k=k)
            elif block_token == 'deform_graph':
                self.local_attn = improvedDeformableLocalGraphAttention(dim, k=k)
        if self.attn is not None and self.local_attn is not None:
            if combine_style == 'concat':
                self.merge_map = nn.Linear(dim*2, dim)
            else:
                self.norm3 = norm_layer(dim)
                self.ls3 = LayerScale(dim, init_values=init_values) if init_values else nn.Identity()
                self.drop_path3 = DropPath(drop_path) if drop_path > 0. else nn.Identity()

    def forward(self, x, pos, idx=None):
        feature_list = []
        if self.block_length == 2:
            if self.combine_style == 'concat':
                norm_x = self.norm1(x)
                if self.attn is not None:
                    global_attn_feat = self.attn(norm_x)
                    feature_list.append(global_attn_feat)
                if self.local_attn is not None:
                    local_attn_feat = self.local_attn(norm_x, pos, idx=idx)
                    feature_list.append(local_attn_feat)
                # combine
                if len(feature_list) == 2:
                    f = torch.cat(feature_list, dim=-1)
                    f = self.merge_map(f)
                    x = x + self.drop_path1(self.ls1(f))
                else:
                    raise RuntimeError()
            else: # onebyone
                x = x + self.drop_path1(self.ls1(self.attn(self.norm1(x))))
                x = x + self.drop_path3(self.ls3(self.local_attn(self.norm3(x), pos, idx=idx)))

        elif self.block_length == 1:
            norm_x = self.norm1(x)
            if self.attn is not None:
                global_attn_feat = self.attn(norm_x)
                feature_list.append(global_attn_feat)
            if self.local_attn is not None:
                local_attn_feat = self.local_attn(norm_x, pos, idx=idx)
                feature_list.append(local_attn_feat)
            # combine
            if len(feature_list) == 1:
                f = feature_list[0]
                x = x + self.drop_path1(self.ls1(f))
            else:
                raise RuntimeError()

        x = x + self.drop_path2(self.ls2(self.mlp(self.norm2(x))))
        return x
   
class CrossAttnBlockApi(nn.Module):
    r'''
        1. Norm Decoder Block 
            self_attn_block_style = 'attn'
            cross_attn_block_style = 'attn'
        2. Concatenation Fused Decoder Block
            self_attn_block_style = 'attn-deform'  
            self_attn_combine_style = 'concat'
            cross_attn_block_style = 'attn-deform'  
            cross_attn_combine_style = 'concat'
        3. Three-layer Fused Decoder Block
            self_attn_block_style = 'attn-deform'  
            self_attn_combine_style = 'onebyone'
            cross_attn_block_style = 'attn-deform'  
            cross_attn_combine_style = 'onebyone'    
        4. Design by yourself
            #  only deform the cross attn
            self_attn_block_style = 'attn'  
            cross_attn_block_style = 'attn-deform'  
            cross_attn_combine_style = 'concat'    
            #  perform graph conv on self attn
            self_attn_block_style = 'attn-graph'  
            self_attn_combine_style = 'concat'    
            cross_attn_block_style = 'attn-deform'  
            cross_attn_combine_style = 'concat'    
    '''
    def __init__(
            self, dim, num_heads, mlp_ratio=4., qkv_bias=False, drop=0., attn_drop=0., init_values=None,
            drop_path=0., act_layer=nn.GELU, norm_layer=nn.LayerNorm, 
            self_attn_block_style='attn-deform', self_attn_combine_style='concat',
            cross_attn_block_style='attn-deform', cross_attn_combine_style='concat',
            k=10, n_group=2
        ):
        super().__init__()        
        self.norm2 = norm_layer(dim)
        self.ls2 = LayerScale(dim, init_values=init_values) if init_values else nn.Identity()
        self.mlp = Mlp(in_features=dim, hidden_features=int(dim * mlp_ratio), act_layer=act_layer, drop=drop)
        self.drop_path2 = DropPath(drop_path) if drop_path > 0. else nn.Identity()      

        # Api desigin
        # first we deal with self-attn
        self.norm1 = norm_layer(dim)
        self.ls1 = LayerScale(dim, init_values=init_values) if init_values else nn.Identity()
        self.drop_path1 = DropPath(drop_path) if drop_path > 0. else nn.Identity()

        self.self_attn_combine_style = self_attn_combine_style
        assert self_attn_combine_style in ['concat', 'onebyone'], f'got unexpect self_attn_combine_style {self_attn_combine_style} for local and global attn'
  
        self_attn_block_tokens = self_attn_block_style.split('-')
        assert len(self_attn_block_tokens) > 0 and len(self_attn_block_tokens) <= 2, f'invalid self_attn_block_style {self_attn_block_style}'
        self.self_attn_block_length = len(self_attn_block_tokens)
        self.self_attn = None
        self.local_self_attn = None
        for self_attn_block_token in self_attn_block_tokens:
            assert self_attn_block_token in ['attn', 'rw_deform', 'deform', 'graph', 'deform_graph'], f'got unexpect self_attn_block_token {self_attn_block_token} for Block component'
            if self_attn_block_token == 'attn':
                self.self_attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
            elif self_attn_block_token == 'rw_deform':
                self.local_self_attn = DeformableLocalAttention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop, k=k, n_group=n_group)
            elif self_attn_block_token == 'deform':
                self.local_self_attn = DeformableLocalCrossAttention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop, k=k, n_group=n_group)
            elif self_attn_block_token == 'graph':
                self.local_self_attn = DynamicGraphAttention(dim, k=k)
            elif self_attn_block_token == 'deform_graph':
                self.local_self_attn = improvedDeformableLocalGraphAttention(dim, k=k)
        if self.self_attn is not None and self.local_self_attn is not None:
            if self_attn_combine_style == 'concat':
                self.self_attn_merge_map = nn.Linear(dim*2, dim)
            else:
                self.norm3 = norm_layer(dim)
                self.ls3 = LayerScale(dim, init_values=init_values) if init_values else nn.Identity()
                self.drop_path3 = DropPath(drop_path) if drop_path > 0. else nn.Identity()

        # Then we deal with cross-attn
        self.norm_q = norm_layer(dim)
        self.norm_v = norm_layer(dim)
        self.ls4 = LayerScale(dim, init_values=init_values) if init_values else nn.Identity()
        self.drop_path4 = DropPath(drop_path) if drop_path > 0. else nn.Identity()  

        self.cross_attn_combine_style = cross_attn_combine_style
        assert cross_attn_combine_style in ['concat', 'onebyone'], f'got unexpect cross_attn_combine_style {cross_attn_combine_style} for local and global attn'
        
        # Api desigin
        cross_attn_block_tokens = cross_attn_block_style.split('-')
        assert len(cross_attn_block_tokens) > 0 and len(cross_attn_block_tokens) <= 2, f'invalid cross_attn_block_style {cross_attn_block_style}'
        self.cross_attn_block_length = len(cross_attn_block_tokens)
        self.cross_attn = None
        self.local_cross_attn = None
        for cross_attn_block_token in cross_attn_block_tokens:
            assert cross_attn_block_token in ['attn', 'deform', 'graph', 'deform_graph'], f'got unexpect cross_attn_block_token {cross_attn_block_token} for Block component'
            if cross_attn_block_token == 'attn':
                self.cross_attn = CrossAttention(dim, dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
            elif cross_attn_block_token == 'deform':
                self.local_cross_attn = DeformableLocalCrossAttention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop, k=k, n_group=n_group)
            elif cross_attn_block_token == 'graph':
                self.local_cross_attn = DynamicGraphAttention(dim, k=k)
            elif cross_attn_block_token == 'deform_graph':
                self.local_cross_attn = improvedDeformableLocalGraphAttention(dim, k=k)
        if self.cross_attn is not None and self.local_cross_attn is not None:
            if cross_attn_combine_style == 'concat':
                self.cross_attn_merge_map = nn.Linear(dim*2, dim)
            else:
                self.norm_q_2 = norm_layer(dim)
                self.norm_v_2 = norm_layer(dim)
                self.ls5 = LayerScale(dim, init_values=init_values) if init_values else nn.Identity()
                self.drop_path5 = DropPath(drop_path) if drop_path > 0. else nn.Identity()

    def forward(
        self,
        q,
        v,
        q_pos,
        v_pos,
        self_attn_idx=None,
        cross_attn_idx=None,
        denoise_length=None,
        return_instrumentation=False,
    ):
        q_input = q
        # q = q + self.drop_path(self.self_attn(self.norm1(q)))

        # calculate mask, shape N,N
        # 1 for mask, 0 for not mask
        # mask shape N, N
        # q: [ true_query; denoise_token ]
        if denoise_length is None:
            mask = None
        else:
            query_len = q.size(1)
            mask = torch.zeros(query_len, query_len).to(q.device)
            mask[:-denoise_length, -denoise_length:] = 1.

        # Self attn
        feature_list = []
        if self.self_attn_block_length == 2:
            if self.self_attn_combine_style == 'concat':
                norm_q = self.norm1(q)
                if self.self_attn is not None:
                    global_attn_feat = self.self_attn(norm_q, mask=mask)
                    feature_list.append(global_attn_feat)
                if self.local_self_attn is not None:
                    local_attn_feat = self.local_self_attn(norm_q, q_pos, idx=self_attn_idx, denoise_length=denoise_length)
                    feature_list.append(local_attn_feat)
                # combine
                if len(feature_list) == 2:
                    f = torch.cat(feature_list, dim=-1)
                    f = self.self_attn_merge_map(f)
                    q = q + self.drop_path1(self.ls1(f))
                else:
                    raise RuntimeError()
            else: # onebyone
                q = q + self.drop_path1(self.ls1(self.self_attn(self.norm1(q), mask=mask)))
                q = q + self.drop_path3(self.ls3(self.local_self_attn(self.norm3(q), q_pos, idx=self_attn_idx, denoise_length=denoise_length)))

        elif self.self_attn_block_length == 1:
            norm_q = self.norm1(q)
            if self.self_attn is not None:
                global_attn_feat = self.self_attn(norm_q, mask=mask)
                feature_list.append(global_attn_feat)
            if self.local_self_attn is not None:
                local_attn_feat = self.local_self_attn(norm_q, q_pos, idx=self_attn_idx, denoise_length=denoise_length)
                feature_list.append(local_attn_feat)
            # combine
            if len(feature_list) == 1:
                f = feature_list[0]
                q = q + self.drop_path1(self.ls1(f))
            else:
                raise RuntimeError()

        q_after_self = q
        # q = q + self.drop_path(self.attn(self.norm_q(q), self.norm_v(v)))
        # Cross attn
        feature_list = []
        if self.cross_attn_block_length == 2:
            if self.cross_attn_combine_style == 'concat':
                norm_q = self.norm_q(q)
                norm_v = self.norm_v(v)
                if self.cross_attn is not None:
                    global_attn_feat = self.cross_attn(norm_q, norm_v)
                    feature_list.append(global_attn_feat)
                if self.local_cross_attn is not None:
                    local_attn_feat = self.local_cross_attn(q=norm_q, v=norm_v, q_pos=q_pos, v_pos=v_pos, idx=cross_attn_idx)
                    feature_list.append(local_attn_feat)
                # combine
                if len(feature_list) == 2:
                    f = torch.cat(feature_list, dim=-1)
                    f = self.cross_attn_merge_map(f)
                    q = q + self.drop_path4(self.ls4(f))
                else:
                    raise RuntimeError()
            else: # onebyone
                q = q + self.drop_path4(self.ls4(self.cross_attn(self.norm_q(q), self.norm_v(v))))
                q = q + self.drop_path5(self.ls5(self.local_cross_attn(q=self.norm_q_2(q), v=self.norm_v_2(v), q_pos=q_pos, v_pos=v_pos, idx=cross_attn_idx)))

        elif self.cross_attn_block_length == 1:
            norm_q = self.norm_q(q)
            norm_v = self.norm_v(v)
            if self.cross_attn is not None:
                global_attn_feat = self.cross_attn(norm_q, norm_v)
                feature_list.append(global_attn_feat)
            if self.local_cross_attn is not None:
                local_attn_feat = self.local_cross_attn(q=norm_q, v=norm_v, q_pos=q_pos, v_pos=v_pos, idx=cross_attn_idx)
                feature_list.append(local_attn_feat)
            # combine
            if len(feature_list) == 1:
                f = feature_list[0]
                q = q + self.drop_path4(self.ls4(f))
            else:
                raise RuntimeError()

        q_after_cross = q
        q = q + self.drop_path2(self.ls2(self.mlp(self.norm2(q))))
        if not return_instrumentation:
            return q
        return q, {
            'input': q_input.detach(),
            'after_self': q_after_self.detach(),
            'after_cross': q_after_cross.detach(),
            'output': q.detach(),
        }
######################################## Entry ########################################  

class TransformerEncoder(nn.Module):
    """ Transformer Encoder without hierarchical structure
    """
    def __init__(self, embed_dim=256, depth=4, num_heads=4, mlp_ratio=4., qkv_bias=False, init_values=None,
        drop_rate=0., attn_drop_rate=0., drop_path_rate=0., act_layer=nn.GELU, norm_layer=nn.LayerNorm,
        block_style_list=['attn-deform'], combine_style='concat', k=10, n_group=2):
        super().__init__()
        self.k = k
        self.blocks = nn.ModuleList()
        for i in range(depth):
            self.blocks.append(SelfAttnBlockApi(
                dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, init_values=init_values,
                drop=drop_rate, attn_drop=attn_drop_rate, 
                drop_path = drop_path_rate[i] if isinstance(drop_path_rate, list) else drop_path_rate,
                act_layer=act_layer, norm_layer=norm_layer,
                block_style=block_style_list[i], combine_style=combine_style, k=k, n_group=n_group
            ))

    def forward(self, x, pos):
        idx = idx = knn_point(self.k, pos, pos)
        for _, block in enumerate(self.blocks):
            x = block(x, pos, idx=idx) 
        return x

class TransformerDecoder(nn.Module):
    """ Transformer Decoder without hierarchical structure
    """
    def __init__(self, embed_dim=256, depth=4, num_heads=4, mlp_ratio=4., qkv_bias=False, init_values=None,
        drop_rate=0., attn_drop_rate=0., drop_path_rate=0., act_layer=nn.GELU, norm_layer=nn.LayerNorm,
        self_attn_block_style_list=['attn-deform'], self_attn_combine_style='concat',
        cross_attn_block_style_list=['attn-deform'], cross_attn_combine_style='concat',
        k=10, n_group=2):
        super().__init__()
        self.k = k
        self.blocks = nn.ModuleList()
        for i in range(depth):
            self.blocks.append(CrossAttnBlockApi(
                dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, init_values=init_values,
                drop=drop_rate, attn_drop=attn_drop_rate, 
                drop_path = drop_path_rate[i] if isinstance(drop_path_rate, list) else drop_path_rate,
                act_layer=act_layer, norm_layer=norm_layer,
                self_attn_block_style=self_attn_block_style_list[i], self_attn_combine_style=self_attn_combine_style,
                cross_attn_block_style=cross_attn_block_style_list[i], cross_attn_combine_style=cross_attn_combine_style,
                k=k, n_group=n_group
            ))

    def forward(
        self,
        q,
        v,
        q_pos,
        v_pos,
        denoise_length=None,
        return_instrumentation=False,
    ):
        if denoise_length is None:
            self_attn_idx = knn_point(self.k, q_pos, q_pos)
        else:
            self_attn_idx = None
        cross_attn_idx = knn_point(self.k, v_pos, q_pos)
        layer_records = []
        for layer_index, block in enumerate(self.blocks):
            if return_instrumentation:
                q, record = block(
                    q, v, q_pos, v_pos,
                    self_attn_idx=self_attn_idx,
                    cross_attn_idx=cross_attn_idx,
                    denoise_length=denoise_length,
                    return_instrumentation=True,
                )
                record['layer_index'] = layer_index
                layer_records.append(record)
            else:
                q = block(
                    q, v, q_pos, v_pos,
                    self_attn_idx=self_attn_idx,
                    cross_attn_idx=cross_attn_idx,
                    denoise_length=denoise_length,
                )
        if return_instrumentation:
            return q, layer_records
        return q

class PointTransformerEncoder(nn.Module):
    """ Vision Transformer for point cloud encoder/decoder
    A PyTorch impl of : `An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale`
        - https://arxiv.org/abs/2010.11929
    Args:
        embed_dim (int): embedding dimension
        depth (int): depth of transformer
        num_heads (int): number of attention heads
        mlp_ratio (int): ratio of mlp hidden dim to embedding dim
        qkv_bias (bool): enable bias for qkv if True
        init_values: (float): layer-scale init values
        drop_rate (float): dropout rate
        attn_drop_rate (float): attention dropout rate
        drop_path_rate (float): stochastic depth rate
        norm_layer: (nn.Module): normalization layer
        act_layer: (nn.Module): MLP activation layer
    """
    def __init__(
            self, embed_dim=256, depth=12, num_heads=4, mlp_ratio=4., qkv_bias=True, init_values=None,
            drop_rate=0., attn_drop_rate=0., drop_path_rate=0.,
            norm_layer=None, act_layer=None,
            block_style_list=['attn-deform'], combine_style='concat',
            k=10, n_group=2
        ):
        super().__init__()
        norm_layer = norm_layer or partial(nn.LayerNorm, eps=1e-6)
        act_layer = act_layer or nn.GELU
        self.num_features = self.embed_dim = embed_dim  # num_features for consistency with other models
        self.pos_drop = nn.Dropout(p=drop_rate)

        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]  # stochastic depth decay rule
        assert len(block_style_list) == depth
        self.blocks = TransformerEncoder(
            embed_dim=embed_dim,
            num_heads=num_heads,
            depth = depth,
            mlp_ratio=mlp_ratio,
            qkv_bias=qkv_bias,
            init_values=init_values,
            drop_rate=drop_rate, 
            attn_drop_rate=attn_drop_rate,
            drop_path_rate = dpr,
            norm_layer=norm_layer, 
            act_layer=act_layer,
            block_style_list=block_style_list,
            combine_style=combine_style,
            k=k,
            n_group=n_group)
        self.norm = norm_layer(embed_dim) 
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def forward(self, x, pos):
        x = self.blocks(x, pos)
        return x

class PointTransformerDecoder(nn.Module):
    """ Vision Transformer for point cloud encoder/decoder
    A PyTorch impl of : `An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale`
        - https://arxiv.org/abs/2010.11929
    """
    def __init__(
            self, embed_dim=256, depth=12, num_heads=4, mlp_ratio=4., qkv_bias=True, init_values=None,
            drop_rate=0., attn_drop_rate=0., drop_path_rate=0.,
            norm_layer=None, act_layer=None,
            self_attn_block_style_list=['attn-deform'], self_attn_combine_style='concat',
            cross_attn_block_style_list=['attn-deform'], cross_attn_combine_style='concat',
            k=10, n_group=2
        ):
        """
        Args:
            embed_dim (int): embedding dimension
            depth (int): depth of transformer
            num_heads (int): number of attention heads
            mlp_ratio (int): ratio of mlp hidden dim to embedding dim
            qkv_bias (bool): enable bias for qkv if True
            init_values: (float): layer-scale init values
            drop_rate (float): dropout rate
            attn_drop_rate (float): attention dropout rate
            drop_path_rate (float): stochastic depth rate
            norm_layer: (nn.Module): normalization layer
            act_layer: (nn.Module): MLP activation layer
        """
        super().__init__()
        norm_layer = norm_layer or partial(nn.LayerNorm, eps=1e-6)
        act_layer = act_layer or nn.GELU
        self.num_features = self.embed_dim = embed_dim  # num_features for consistency with other models
        self.pos_drop = nn.Dropout(p=drop_rate)

        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]  # stochastic depth decay rule
        assert len(self_attn_block_style_list) == len(cross_attn_block_style_list) == depth
        self.blocks = TransformerDecoder(
            embed_dim=embed_dim,
            num_heads=num_heads,
            depth = depth,
            mlp_ratio=mlp_ratio,
            qkv_bias=qkv_bias,
            init_values=init_values,
            drop_rate=drop_rate, 
            attn_drop_rate=attn_drop_rate,
            drop_path_rate = dpr,
            norm_layer=norm_layer, 
            act_layer=act_layer,
            self_attn_block_style_list=self_attn_block_style_list, 
            self_attn_combine_style=self_attn_combine_style,
            cross_attn_block_style_list=cross_attn_block_style_list, 
            cross_attn_combine_style=cross_attn_combine_style,
            k=k, 
            n_group=n_group
        )
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def forward(
        self,
        q,
        v,
        q_pos,
        v_pos,
        denoise_length=None,
        return_instrumentation=False,
    ):
        return self.blocks(
            q,
            v,
            q_pos,
            v_pos,
            denoise_length=denoise_length,
            return_instrumentation=return_instrumentation,
        )

class PointTransformerEncoderEntry(PointTransformerEncoder):
    def __init__(self, config, **kwargs):
        super().__init__(**dict(config))

class PointTransformerDecoderEntry(PointTransformerDecoder):
    def __init__(self, config, **kwargs):
        super().__init__(**dict(config))

######################################## Grouper ########################################  
class DGCNN_Grouper(nn.Module):
    def __init__(self, k = 16):
        super().__init__()
        '''
        K has to be 16
        '''
        print('using group version 2')
        self.k = k
        # self.knn = KNN(k=k, transpose_mode=False)
        self.input_trans = nn.Conv1d(3, 8, 1)

        self.layer1 = nn.Sequential(nn.Conv2d(16, 32, kernel_size=1, bias=False),
                                   nn.GroupNorm(4, 32),
                                   nn.LeakyReLU(negative_slope=0.2)
                                   )

        self.layer2 = nn.Sequential(nn.Conv2d(64, 64, kernel_size=1, bias=False),
                                   nn.GroupNorm(4, 64),
                                   nn.LeakyReLU(negative_slope=0.2)
                                   )

        self.layer3 = nn.Sequential(nn.Conv2d(128, 64, kernel_size=1, bias=False),
                                   nn.GroupNorm(4, 64),
                                   nn.LeakyReLU(negative_slope=0.2)
                                   )

        self.layer4 = nn.Sequential(nn.Conv2d(128, 128, kernel_size=1, bias=False),
                                   nn.GroupNorm(4, 128),
                                   nn.LeakyReLU(negative_slope=0.2)
                                   )
        self.num_features = 128
    @staticmethod
    def fps_downsample(coor, x, num_group):
        xyz = coor.transpose(1, 2).contiguous() # b, n, 3
        fps_idx = pointnet2_utils.furthest_point_sample(xyz, num_group)

        combined_x = torch.cat([coor, x], dim=1)

        new_combined_x = (
            pointnet2_utils.gather_operation(
                combined_x, fps_idx
            )
        )

        new_coor = new_combined_x[:, :3]
        new_x = new_combined_x[:, 3:]

        return new_coor, new_x

    def get_graph_feature(self, coor_q, x_q, coor_k, x_k):

        # coor: bs, 3, np, x: bs, c, np

        k = self.k
        batch_size = x_k.size(0)
        num_points_k = x_k.size(2)
        num_points_q = x_q.size(2)

        with torch.no_grad():
            # _, idx = self.knn(coor_k, coor_q)  # bs k np
            idx = knn_point(k, coor_k.transpose(-1, -2).contiguous(), coor_q.transpose(-1, -2).contiguous()) # B G M
            idx = idx.transpose(-1, -2).contiguous()
            assert idx.shape[1] == k
            idx_base = torch.arange(0, batch_size, device=x_q.device).view(-1, 1, 1) * num_points_k
            idx = idx + idx_base
            idx = idx.view(-1)
        num_dims = x_k.size(1)
        x_k = x_k.transpose(2, 1).contiguous()
        feature = x_k.view(batch_size * num_points_k, -1)[idx, :]
        feature = feature.view(batch_size, k, num_points_q, num_dims).permute(0, 3, 2, 1).contiguous()
        x_q = x_q.view(batch_size, num_dims, num_points_q, 1).expand(-1, -1, -1, k)
        feature = torch.cat((feature - x_q, x_q), dim=1)
        return feature

    def forward(self, x, num):
        '''
            INPUT:
                x : bs N 3
                num : list e.g.[1024, 512]
            ----------------------
            OUTPUT:

                coor bs N 3
                f    bs N C(128) 
        '''
        x = x.transpose(-1, -2).contiguous()

        coor = x
        f = self.input_trans(x)

        f = self.get_graph_feature(coor, f, coor, f)
        f = self.layer1(f)
        f = f.max(dim=-1, keepdim=False)[0]

        coor_q, f_q = self.fps_downsample(coor, f, num[0])
        f = self.get_graph_feature(coor_q, f_q, coor, f)
        f = self.layer2(f)
        f = f.max(dim=-1, keepdim=False)[0]
        coor = coor_q

        f = self.get_graph_feature(coor, f, coor, f)
        f = self.layer3(f)
        f = f.max(dim=-1, keepdim=False)[0]

        coor_q, f_q = self.fps_downsample(coor, f, num[1])
        f = self.get_graph_feature(coor_q, f_q, coor, f)
        f = self.layer4(f)
        f = f.max(dim=-1, keepdim=False)[0]
        coor = coor_q

        coor = coor.transpose(-1, -2).contiguous()
        f = f.transpose(-1, -2).contiguous()

        return coor, f

class Encoder(nn.Module):
    def __init__(self, encoder_channel):
        super().__init__()
        self.encoder_channel = encoder_channel
        self.first_conv = nn.Sequential(
            nn.Conv1d(3, 128, 1),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Conv1d(128, 256, 1)
        )
        self.second_conv = nn.Sequential(
            nn.Conv1d(512, 512, 1),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Conv1d(512, self.encoder_channel, 1)
        )
    def forward(self, point_groups):
        '''
            point_groups : B G N 3
            -----------------
            feature_global : B G C
        '''
        bs, g, n , _ = point_groups.shape
        point_groups = point_groups.reshape(bs * g, n, 3)
        # encoder
        feature = self.first_conv(point_groups.transpose(2,1))  # BG 256 n
        feature_global = torch.max(feature,dim=2,keepdim=True)[0]  # BG 256 1
        feature = torch.cat([feature_global.expand(-1,-1,n), feature], dim=1)# BG 512 n
        feature = self.second_conv(feature) # BG 1024 n
        feature_global = torch.max(feature, dim=2, keepdim=False)[0] # BG 1024
        return feature_global.reshape(bs, g, self.encoder_channel)

class SimpleEncoder(nn.Module):
    def __init__(self, k = 32, embed_dims=128):
        super().__init__()
        self.embedding = Encoder(embed_dims)
        self.group_size = k

        self.num_features = embed_dims

    def forward(self, xyz, n_group):
        # 2048 divide into 128 * 32, overlap is needed
        if isinstance(n_group, list):
            n_group = n_group[-1] 

        center = misc.fps(xyz, n_group) # B G 3
            
        assert center.size(1) == n_group, f'expect center to be B {n_group} 3, but got shape {center.shape}'
        
        batch_size, num_points, _ = xyz.shape
        # knn to get the neighborhood
        idx = knn_point(self.group_size, xyz, center)
        assert idx.size(1) == n_group
        assert idx.size(2) == self.group_size
        idx_base = torch.arange(0, batch_size, device=xyz.device).view(-1, 1, 1) * num_points
        idx = idx + idx_base
        idx = idx.view(-1)
        neighborhood = xyz.view(batch_size * num_points, -1)[idx, :]
        neighborhood = neighborhood.view(batch_size, n_group, self.group_size, 3).contiguous()
            
        assert neighborhood.size(1) == n_group
        assert neighborhood.size(2) == self.group_size
            
        features = self.embedding(neighborhood) # B G C
        
        return center, features

######################################## Fold ########################################    
class Fold(nn.Module):
    def __init__(self, in_channel, step , hidden_dim=512):
        super().__init__()

        self.in_channel = in_channel
        self.step = step

        a = torch.linspace(-1., 1., steps=step, dtype=torch.float).view(1, step).expand(step, step).reshape(1, -1)
        b = torch.linspace(-1., 1., steps=step, dtype=torch.float).view(step, 1).expand(step, step).reshape(1, -1)
        self.folding_seed = torch.cat([a, b], dim=0).cuda()

        self.folding1 = nn.Sequential(
            nn.Conv1d(in_channel + 2, hidden_dim, 1),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Conv1d(hidden_dim, hidden_dim//2, 1),
            nn.BatchNorm1d(hidden_dim//2),
            nn.ReLU(inplace=True),
            nn.Conv1d(hidden_dim//2, 3, 1),
        )

        self.folding2 = nn.Sequential(
            nn.Conv1d(in_channel + 3, hidden_dim, 1),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Conv1d(hidden_dim, hidden_dim//2, 1),
            nn.BatchNorm1d(hidden_dim//2),
            nn.ReLU(inplace=True),
            nn.Conv1d(hidden_dim//2, 3, 1),
        )

    def forward(self, x):
        num_sample = self.step * self.step
        bs = x.size(0)
        features = x.view(bs, self.in_channel, 1).expand(bs, self.in_channel, num_sample)
        seed = self.folding_seed.view(1, 2, num_sample).expand(bs, 2, num_sample).to(x.device)

        x = torch.cat([seed, features], dim=1)
        fd1 = self.folding1(x)
        x = torch.cat([fd1, features], dim=1)
        fd2 = self.folding2(x)

        return fd2

class SimpleRebuildFCLayer(nn.Module):
    def __init__(self, input_dims, step, hidden_dim=512):
        super().__init__()
        self.input_dims = input_dims
        self.step = step
        self.layer = Mlp(self.input_dims, hidden_dim, step * 3)

    def forward(self, rec_feature):
        '''
        Input BNC
        '''
        batch_size = rec_feature.size(0)
        g_feature = rec_feature.max(1)[0]
        token_feature = rec_feature
            
        patch_feature = torch.cat([
                g_feature.unsqueeze(1).expand(-1, token_feature.size(1), -1),
                token_feature
            ], dim = -1)
        rebuild_pc = self.layer(patch_feature).reshape(batch_size, -1, self.step , 3)
        assert rebuild_pc.size(1) == rec_feature.size(1)
        return rebuild_pc

######################################## PCTransformer ########################################   
class PCTransformer(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.full_instrumentation_enabled = False
        self._last_full_instrumentation = None
        encoder_config = config.encoder_config
        decoder_config = config.decoder_config
        self.center_num  = getattr(config, 'center_num', [512, 128])
        self.encoder_type = config.encoder_type
        assert self.encoder_type in ['graph', 'pn'], f'unexpected encoder_type {self.encoder_type}'

        in_chans = 3
        self.num_query = query_num = config.num_query
        self.query_selection = getattr(config, 'query_selection', 'ranking')
        if self.query_selection not in [
            'ranking', 'fps_preserve', 'fps_only', 'learned_only'
        ]:
            raise ValueError(
                f'Unsupported query_selection={self.query_selection!r}; '
                "expected 'ranking', 'fps_preserve', 'fps_only', or "
                "'learned_only'"
            )
        rim_query_config = getattr(config, 'rim_query_allocation', None)
        self.rim_query_enabled = bool(
            getattr(rim_query_config, 'enabled', False)
        ) if rim_query_config is not None else False
        self.rim_query_count = int(
            getattr(rim_query_config, 'rim_queries', 32)
        ) if rim_query_config is not None else 32
        self.rim_query_pool_size = int(
            getattr(rim_query_config, 'candidate_pool', 96)
        ) if rim_query_config is not None else 96
        if self.rim_query_enabled:
            if self.query_selection != 'learned_only':
                raise ValueError(
                    'Rim query allocation requires query_selection=learned_only'
                )
            if not 0 < self.rim_query_count < self.num_query:
                raise ValueError(
                    'rim_queries must be positive and smaller than num_query'
                )
            proxy_count = int(self.center_num[-1])
            if not (
                self.rim_query_count
                <= self.rim_query_pool_size
                <= proxy_count
            ):
                raise ValueError(
                    'Rim allocation requires rim_queries <= candidate_pool '
                    '<= final encoder proxy count'
                )
        self.use_denoise = float(getattr(config, 'denoise_weight', 0.5)) > 0
        global_feature_dim = config.global_feature_dim

        print_log(f'Transformer with config {config}', logger='MODEL')
        # base encoder
        if self.encoder_type == 'graph':
            self.grouper = DGCNN_Grouper(k = 16)
        else:
            self.grouper = SimpleEncoder(k = 32, embed_dims=512)
        self.pos_embed = nn.Sequential(
            nn.Linear(in_chans, 128),
            nn.GELU(),
            nn.Linear(128, encoder_config.embed_dim)
        )  
        self.input_proj = nn.Sequential(
            nn.Linear(self.grouper.num_features, 512),
            nn.GELU(),
            nn.Linear(512, encoder_config.embed_dim)
        )
        # Coarse Level 1 : Encoder
        self.encoder = PointTransformerEncoderEntry(encoder_config)
        self.encoder_adapter = MambaSequenceAdapter(
            encoder_config.embed_dim,
            getattr(config, 'mamba_adapter', None),
        )
        if self.rim_query_enabled:
            proxy_feature_dim = 2 * encoder_config.embed_dim
            self.rim_score_head = nn.Sequential(
                nn.Linear(proxy_feature_dim, 128),
                nn.GELU(),
                nn.Linear(128, 1),
            )
        else:
            self.rim_score_head = None

        self.increase_dim = nn.Sequential(
            nn.Linear(encoder_config.embed_dim, 1024),
            nn.GELU(),
            nn.Linear(1024, global_feature_dim))
        # query generator
        self.coarse_pred = nn.Sequential(
            nn.Linear(global_feature_dim, 1024),
            nn.GELU(),
            nn.Linear(1024, 3 * query_num)
        )
        self.mlp_query = nn.Sequential(
            nn.Linear(global_feature_dim + 3, 1024),
            nn.GELU(),
            nn.Linear(1024, 1024),
            nn.GELU(),
            nn.Linear(1024, decoder_config.embed_dim)
        )
        # assert decoder_config.embed_dim == encoder_config.embed_dim
        if decoder_config.embed_dim == encoder_config.embed_dim:
            self.mem_link = nn.Identity()
        else:
            self.mem_link = nn.Linear(encoder_config.embed_dim, decoder_config.embed_dim)
        # Coarse Level 2 : Decoder
        self.decoder = PointTransformerDecoderEntry(decoder_config)
 
        self.query_ranking = nn.Sequential(
            nn.Linear(3, 256),
            nn.GELU(),
            nn.Linear(256, 256),
            nn.GELU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def set_mamba_adapter_scale(self, scale):
        self.encoder_adapter.set_alpha_scale(scale)

    def enable_mamba_instrumentation(self, enabled=True):
        self.encoder_adapter.enable_instrumentation(enabled)

    def pop_mamba_instrumentation(self):
        return self.encoder_adapter.pop_instrumentation()

    def enable_full_instrumentation(self, enabled=True):
        self.full_instrumentation_enabled = bool(enabled)
        self._last_full_instrumentation = None
        self.encoder_adapter.enable_instrumentation(enabled)

    def pop_full_instrumentation(self):
        records = self._last_full_instrumentation
        self._last_full_instrumentation = None
        if records is not None:
            records['adapter'] = self.encoder_adapter.pop_instrumentation()
        return records

    def encode_rim_proxy_tokens(self, xyz):
        """Return the exact coordinates and features consumed by the rim head."""

        coor, features = self.grouper(xyz, self.center_num)
        position = self.pos_embed(coor)
        encoded = self.input_proj(features)
        encoded = self.encoder(encoded + position, coor)
        encoder_pre_adapter = encoded
        encoded = self.encoder_adapter(encoded, coor)
        proxy_features = torch.cat([encoded, position], dim=-1)
        return coor, proxy_features, encoder_pre_adapter, encoded

    def forward(self, xyz):
        if self.full_instrumentation_enabled and self.training:
            raise RuntimeError(
                'Full-model instrumentation is inference-only; call eval() first'
        )
        bs = xyz.size(0)
        coor, proxy_features, encoder_pre_adapter, x = (
            self.encode_rim_proxy_tokens(xyz)
        )
        pe = proxy_features[..., x.shape[-1]:]
        encoder_post_adapter = x
        global_feature = self.increase_dim(x) # B 1024 N 
        global_feature = torch.max(global_feature, dim=1)[0] # B 1024

        learned_coarse = self.coarse_pred(global_feature).reshape(bs, -1, 3)

        fps_count = (
            self.num_query
            if self.query_selection == 'fps_only'
            else self.num_query // 2
        )
        coarse_inp = misc.fps(xyz, fps_count)
        mem = self.mem_link(x)
        coarse_candidates = None
        query_ranking = None
        selected_query_indices = None
        rim_aux = None

        if self.query_selection == 'ranking':
            coarse_candidates = torch.cat([learned_coarse, coarse_inp], dim=1)
            query_ranking = self.query_ranking(coarse_candidates) # b n 1
            idx = torch.argsort(query_ranking, dim=1, descending=True) # b n 1
            selected_query_indices = idx[:, :self.num_query]
            coarse = torch.gather(
                coarse_candidates,
                1,
                idx[:, :self.num_query].expand(-1, -1, coarse_candidates.size(-1))
            )
        elif self.query_selection == 'fps_preserve':
            # Keep every input FPS anchor so the coarse queries retain global
            # coverage. The remaining half are differentiable learned queries.
            learned_count = self.num_query - coarse_inp.size(1)
            coarse = torch.cat([learned_coarse[:, :learned_count], coarse_inp], dim=1)
        elif self.query_selection == 'fps_only':
            coarse = coarse_inp
        elif self.rim_query_enabled:
            rim_logits = self.rim_score_head(proxy_features).squeeze(-1)
            selected_rim_indices = diversified_topk_indices(
                rim_logits,
                coor,
                selected_count=self.rim_query_count,
                pool_size=self.rim_query_pool_size,
            )
            rim_coarse = gather_points(coor, selected_rim_indices)
            learned_count = self.num_query - self.rim_query_count
            coarse = torch.cat(
                [learned_coarse[:, :learned_count], rim_coarse], dim=1
            )
            rim_aux = {
                'proxy_coordinates': coor,
                'rim_logits': rim_logits,
                'selected_proxy_indices': selected_rim_indices,
                'selected_proxy_coordinates': rim_coarse,
            }
        else:
            # Implant prediction should not anchor query points on the defective
            # skull surface; all coarse queries are generated from global context.
            coarse = learned_coarse[:, :self.num_query]

        if self.training and self.use_denoise:
            # add denoise task
            # first pick some point : 64?
            picked_points = misc.fps(xyz, 64)
            picked_points = misc.jitter_points(picked_points)
            coarse = torch.cat([coarse, picked_points], dim=1) # B 256+64 3?
            denoise_length = 64     

            # produce query
            q = self.mlp_query(
            torch.cat([
                global_feature.unsqueeze(1).expand(-1, coarse.size(1), -1),
                coarse], dim = -1)) # b n c
            query_pre_decoder = q

            # forward decoder
            if self.full_instrumentation_enabled:
                q, decoder_layers = self.decoder(
                    q=q, v=mem, q_pos=coarse, v_pos=coor,
                    denoise_length=denoise_length,
                    return_instrumentation=True,
                )
            else:
                q = self.decoder(q=q, v=mem, q_pos=coarse, v_pos=coor, denoise_length=denoise_length)
                decoder_layers = None

            if self.full_instrumentation_enabled:
                self._last_full_instrumentation = {
                    'input_xyz': xyz.detach(),
                    'encoder_coordinates': coor.detach(),
                    'encoder_pre_adapter': encoder_pre_adapter.detach(),
                    'encoder_post_adapter': encoder_post_adapter.detach(),
                    'encoder_memory': mem.detach(),
                    'global_feature': global_feature.detach(),
                    'learned_coarse': learned_coarse.detach(),
                    'fps_coarse': coarse_inp.detach(),
                    'coarse_candidates': None if coarse_candidates is None else coarse_candidates.detach(),
                    'query_ranking': None if query_ranking is None else query_ranking.detach(),
                    'selected_query_indices': None if selected_query_indices is None else selected_query_indices.detach(),
                    'rim_logits': None if rim_aux is None else rim_aux['rim_logits'].detach(),
                    'selected_rim_indices': None if rim_aux is None else rim_aux['selected_proxy_indices'].detach(),
                    'coarse': coarse.detach(),
                    'query_pre_decoder': query_pre_decoder.detach(),
                    'query_post_decoder': q.detach(),
                    'decoder_layers': decoder_layers,
                }

            return q, coarse, denoise_length, rim_aux

        else:
            # produce query
            q = self.mlp_query(
            torch.cat([
                global_feature.unsqueeze(1).expand(-1, coarse.size(1), -1),
                coarse], dim = -1)) # b n c
            query_pre_decoder = q
            
            # forward decoder
            if self.full_instrumentation_enabled:
                q, decoder_layers = self.decoder(
                    q=q, v=mem, q_pos=coarse, v_pos=coor,
                    return_instrumentation=True,
                )
            else:
                q = self.decoder(q=q, v=mem, q_pos=coarse, v_pos=coor)
                decoder_layers = None

            if self.full_instrumentation_enabled:
                self._last_full_instrumentation = {
                    'input_xyz': xyz.detach(),
                    'encoder_coordinates': coor.detach(),
                    'encoder_pre_adapter': encoder_pre_adapter.detach(),
                    'encoder_post_adapter': encoder_post_adapter.detach(),
                    'encoder_memory': mem.detach(),
                    'global_feature': global_feature.detach(),
                    'learned_coarse': learned_coarse.detach(),
                    'fps_coarse': coarse_inp.detach(),
                    'coarse_candidates': None if coarse_candidates is None else coarse_candidates.detach(),
                    'query_ranking': None if query_ranking is None else query_ranking.detach(),
                    'selected_query_indices': None if selected_query_indices is None else selected_query_indices.detach(),
                    'rim_logits': None if rim_aux is None else rim_aux['rim_logits'].detach(),
                    'selected_rim_indices': None if rim_aux is None else rim_aux['selected_proxy_indices'].detach(),
                    'coarse': coarse.detach(),
                    'query_pre_decoder': query_pre_decoder.detach(),
                    'query_post_decoder': q.detach(),
                    'decoder_layers': decoder_layers,
                }

            return q, coarse, 0, rim_aux

######################################## PoinTr ########################################  

@MODELS.register_module()
class AdaPoinTr(nn.Module):
    def __init__(self, config, **kwargs):
        super().__init__()
        self.full_instrumentation_enabled = False
        self._last_full_instrumentation = None
        self.trans_dim = config.decoder_config.embed_dim
        self.num_query = config.num_query
        self.num_points = getattr(config, 'num_points', None)

        self.decoder_type = config.decoder_type
        assert self.decoder_type in ['fold', 'fc'], f'unexpected decoder_type {self.decoder_type}'
        self.denoise_weight = float(getattr(config, 'denoise_weight', 0.5))
        if self.denoise_weight < 0:
            raise ValueError('denoise_weight must be non-negative')
        self.fine_coverage_weight = float(
            getattr(config, 'fine_coverage_weight', 1.0)
        )
        if self.fine_coverage_weight <= 0:
            raise ValueError('fine_coverage_weight must be positive')
        self.fine_local_weight = float(
            getattr(config, 'fine_local_weight', 0.0)
        )
        if self.fine_local_weight < 0:
            raise ValueError('fine_local_weight must be non-negative')

        geometry_config = getattr(config, 'coarse_geometry_guard', None)
        self.coarse_geometry_guard_enabled = bool(
            getattr(geometry_config, 'enabled', False)
        ) if geometry_config is not None else False
        self.coarse_geometry_guard_mode = str(
            getattr(geometry_config, 'mode', 'none')
        ) if geometry_config is not None else 'none'
        self.coarse_geometry_guard_weight = float(
            getattr(geometry_config, 'weight', 0.0)
        ) if geometry_config is not None else 0.0
        self.coarse_geometry_guard_beta = float(
            getattr(geometry_config, 'smooth_l1_beta', 0.1)
        ) if geometry_config is not None else 0.1
        self.coarse_geometry_guard_cvar_fraction = float(
            getattr(geometry_config, 'cvar_fraction', 0.1)
        ) if geometry_config is not None else 0.1
        self.coarse_geometry_guard_eps = float(
            getattr(geometry_config, 'eps', 1.0e-6)
        ) if geometry_config is not None else 1.0e-6
        allowed_geometry_modes = {
            'none', 'centroid', 'centroid_radius', 'coverage_cvar'
        }
        if self.coarse_geometry_guard_mode not in allowed_geometry_modes:
            raise ValueError(
                'Unsupported coarse_geometry_guard mode: '
                f'{self.coarse_geometry_guard_mode!r}'
            )
        if self.coarse_geometry_guard_enabled:
            if self.coarse_geometry_guard_mode == 'none':
                raise ValueError('Enabled coarse geometry guard requires a mode')
            if self.coarse_geometry_guard_weight <= 0:
                raise ValueError('Enabled coarse geometry guard requires positive weight')

        local_rim_config = getattr(config, 'local_rim_guard', None)
        self.local_rim_guard_enabled = bool(
            getattr(local_rim_config, 'enabled', False)
        ) if local_rim_config is not None else False
        self.local_rim_guard_weight = float(
            getattr(local_rim_config, 'weight', 0.01)
        ) if local_rim_config is not None else 0.01
        self.local_rim_band_mm = float(
            getattr(local_rim_config, 'rim_band_mm', 2.0)
        ) if local_rim_config is not None else 2.0
        self.local_rim_deadzone_mm = float(
            getattr(local_rim_config, 'deadzone_mm', 5.0)
        ) if local_rim_config is not None else 5.0
        self.local_rim_beta = float(
            getattr(local_rim_config, 'smooth_l1_beta', 0.1)
        ) if local_rim_config is not None else 0.1
        self.local_rim_epsilon_mm = float(
            getattr(local_rim_config, 'epsilon_mm', 1.0e-6)
        ) if local_rim_config is not None else 1.0e-6
        self.moment_trust_enabled = bool(
            getattr(local_rim_config, 'trust_enabled', False)
        ) if local_rim_config is not None else False
        self.moment_trust_weight = float(
            getattr(local_rim_config, 'trust_weight', 0.01)
        ) if local_rim_config is not None else 0.01
        self.moment_trust_centroid_tolerance_mm = float(
            getattr(local_rim_config, 'centroid_tolerance_mm', 3.0)
        ) if local_rim_config is not None else 3.0
        self.moment_trust_radius_log_tolerance = float(
            getattr(
                local_rim_config,
                'radius_log_tolerance',
                math.log(1.05),
            )
        ) if local_rim_config is not None else math.log(1.05)
        if self.moment_trust_enabled and not self.local_rim_guard_enabled:
            raise ValueError('Moment trust requires the local rim guard')
        if self.local_rim_guard_enabled and self.local_rim_guard_weight <= 0:
            raise ValueError('Enabled local rim guard requires positive weight')
        if self.moment_trust_enabled and self.moment_trust_weight <= 0:
            raise ValueError('Enabled moment trust requires positive weight')

        dense_contact_config = getattr(config, 'dense_contact_objective', None)
        self.dense_contact_enabled = bool(
            getattr(dense_contact_config, 'enabled', False)
        ) if dense_contact_config is not None else False
        self.dense_contact_weight = float(
            getattr(dense_contact_config, 'weight', 0.0)
        ) if dense_contact_config is not None else 0.0
        self.dense_contact_threshold_mm = float(
            getattr(dense_contact_config, 'threshold_mm', 2.0)
        ) if dense_contact_config is not None else 2.0
        self.dense_contact_temperature_mm = float(
            getattr(dense_contact_config, 'temperature_mm', 0.25)
        ) if dense_contact_config is not None else 0.25
        self.dense_contact_tail_fraction = float(
            getattr(dense_contact_config, 'tail_fraction', 0.1)
        ) if dense_contact_config is not None else 0.1
        if self.dense_contact_enabled and self.dense_contact_weight <= 0:
            raise ValueError(
                'Enabled dense contact objective requires a calibrated weight'
            )

        rim_query_config = getattr(config, 'rim_query_allocation', None)
        self.rim_query_enabled = bool(
            getattr(rim_query_config, 'enabled', False)
        ) if rim_query_config is not None else False
        self.rim_query_classification_weight = float(
            getattr(rim_query_config, 'classification_weight', 0.0)
        ) if rim_query_config is not None else 0.0
        if (
            self.rim_query_enabled
            and self.rim_query_classification_weight <= 0
        ):
            raise ValueError(
                'Enabled rim query allocation requires a calibrated '
                'classification_weight'
            )

        self.fold_step = 8
        self.base_model = PCTransformer(config)
        
        if self.decoder_type == 'fold':
            self.factor = self.fold_step**2
            self.decode_head = Fold(self.trans_dim, step=self.fold_step, hidden_dim=256)  # rebuild a cluster point
        else:
            if self.num_points is not None:
                self.factor = self.num_points // self.num_query
                assert self.num_points % self.num_query == 0
                self.decode_head = SimpleRebuildFCLayer(self.trans_dim * 2, step=self.num_points // self.num_query)  # rebuild a cluster point
            else:
                self.factor = self.fold_step**2
                self.decode_head = SimpleRebuildFCLayer(self.trans_dim * 2, step=self.fold_step**2)
        self.increase_dim = nn.Sequential(
            nn.Conv1d(self.trans_dim, 1024, 1),
            nn.BatchNorm1d(1024),
            nn.LeakyReLU(negative_slope=0.2),
            nn.Conv1d(1024, 1024, 1)
        )
        self.reduce_map = nn.Linear(self.trans_dim + 1027, self.trans_dim)
        self.build_loss_func()

    def set_mamba_adapter_scale(self, scale):
        if hasattr(self.base_model, 'set_mamba_adapter_scale'):
            self.base_model.set_mamba_adapter_scale(scale)

    def enable_mamba_instrumentation(self, enabled=True):
        if not hasattr(self.base_model, 'enable_mamba_instrumentation'):
            raise RuntimeError('Mamba instrumentation is unavailable')
        self.base_model.enable_mamba_instrumentation(enabled)

    def pop_mamba_instrumentation(self):
        if not hasattr(self.base_model, 'pop_mamba_instrumentation'):
            return None
        return self.base_model.pop_mamba_instrumentation()

    def enable_full_instrumentation(self, enabled=True):
        self.full_instrumentation_enabled = bool(enabled)
        self._last_full_instrumentation = None
        self.base_model.enable_full_instrumentation(enabled)

    def pop_full_instrumentation(self):
        records = self._last_full_instrumentation
        self._last_full_instrumentation = None
        backbone = self.base_model.pop_full_instrumentation()
        if records is not None:
            records['backbone'] = backbone
        return records

    def build_loss_func(self):
        self.loss_func = ChamferDistanceL1()
        self.fine_loss_func = ChamferDistanceL1Directional(
            pred_to_ref_weight=1.0,
            ref_to_pred_weight=self.fine_coverage_weight,
        )

    def get_fine_loss_components(self, pred_coarse, pred_fine, gt):
        loss_global = self.fine_loss_func(pred_fine, gt)
        if self.fine_local_weight == 0:
            loss_local = pred_fine.new_zeros(())
            return loss_global, loss_local, loss_global

        loss_local = patch_local_chamfer(
            pred_coarse,
            pred_fine,
            gt,
            self.factor,
            self.loss_func,
        )
        loss_combined = (
            loss_global + self.fine_local_weight * loss_local
        ) / (1.0 + self.fine_local_weight)
        return loss_global, loss_local, loss_combined

    def get_loss(
        self,
        ret,
        gt,
        epoch=1,
        partial=None,
        normalization_scale=None,
        gt_rim_mask=None,
        teacher_coarse_centroid=None,
        teacher_coarse_radius=None,
    ):
        if len(ret) not in (4, 5):
            raise ValueError('AdaPoinTr training output must contain 4 or 5 items')
        pred_coarse, denoised_coarse, denoised_fine, pred_fine = ret[:4]
        rim_aux = ret[4] if len(ret) == 5 else None
        
        assert pred_fine.size(1) == gt.size(1)

        if self.denoise_weight > 0 and denoised_coarse.size(1) > 0:
            idx = knn_point(self.factor, gt, denoised_coarse) # B n k
            denoised_target = index_points(gt, idx) # B n k 3
            denoised_target = denoised_target.reshape(gt.size(0), -1, 3)
            assert denoised_target.size(1) == denoised_fine.size(1)
            loss_denoised = self.loss_func(denoised_fine, denoised_target)
            loss_denoised = loss_denoised * self.denoise_weight
        else:
            loss_denoised = pred_fine.new_zeros(())

        # recon loss
        loss_coarse = self.loss_func(pred_coarse, gt)
        _, _, loss_fine = self.get_fine_loss_components(
            pred_coarse,
            pred_fine,
            gt,
        )
        loss_recon = loss_coarse + loss_fine
        if self.coarse_geometry_guard_enabled:
            geometry_components = coarse_geometry_guard_components(
                pred_coarse,
                gt,
                smooth_l1_beta=self.coarse_geometry_guard_beta,
                cvar_fraction=self.coarse_geometry_guard_cvar_fraction,
                eps=self.coarse_geometry_guard_eps,
                requested_mode=self.coarse_geometry_guard_mode,
            )
            loss_recon = loss_recon + (
                self.coarse_geometry_guard_weight
                * geometry_components[self.coarse_geometry_guard_mode]
            )

        if self.local_rim_guard_enabled:
            if partial is None or normalization_scale is None:
                raise ValueError(
                    'Local rim guard requires partial and normalization_scale'
                )
            rim_result = local_rim_undercoverage_loss(
                pred_coarse,
                partial,
                gt,
                normalization_scale,
                gt_rim_mask=gt_rim_mask,
                rim_band_mm=self.local_rim_band_mm,
                deadzone_mm=self.local_rim_deadzone_mm,
                smooth_l1_beta=self.local_rim_beta,
                epsilon_mm=self.local_rim_epsilon_mm,
            )
            loss_recon = loss_recon + self.local_rim_guard_weight * rim_result.loss

        if self.moment_trust_enabled:
            if teacher_coarse_centroid is None or teacher_coarse_radius is None:
                raise ValueError('Moment trust requires frozen R0 teacher moments')
            trust_result = global_moment_trust_loss(
                pred_coarse,
                gt,
                normalization_scale,
                teacher_coarse_centroid,
                teacher_coarse_radius,
                centroid_tolerance_mm=(
                    self.moment_trust_centroid_tolerance_mm
                ),
                radius_log_tolerance=(
                    self.moment_trust_radius_log_tolerance
                ),
                smooth_l1_beta=self.local_rim_beta,
                epsilon_mm=self.local_rim_epsilon_mm,
            )
            loss_recon = (
                loss_recon + self.moment_trust_weight * trust_result.loss
            )

        if self.dense_contact_enabled:
            if (
                partial is None
                or normalization_scale is None
                or gt_rim_mask is None
            ):
                raise ValueError(
                    'Dense contact objective requires partial, '
                    'normalization_scale, and gt_rim_mask'
                )
            contact_result = dense_contact_safety_loss(
                pred_fine,
                partial,
                normalization_scale,
                gt_rim_mask,
                threshold_mm=self.dense_contact_threshold_mm,
                temperature_mm=self.dense_contact_temperature_mm,
                tail_fraction=self.dense_contact_tail_fraction,
            )
            loss_recon = (
                loss_recon + self.dense_contact_weight * contact_result.loss
            )

        if self.rim_query_enabled:
            if partial is None or gt_rim_mask is None or rim_aux is None:
                raise ValueError(
                    'Rim query supervision requires partial, gt_rim_mask, '
                    'and rim query auxiliary output'
                )
            proxy_labels = assign_reference_rim_to_proxies(
                rim_aux['proxy_coordinates'],
                partial,
                gt_rim_mask,
            )
            classification_loss = case_balanced_binary_cross_entropy(
                rim_aux['rim_logits'],
                proxy_labels.labels,
            )
            loss_recon = loss_recon + (
                self.rim_query_classification_weight * classification_loss
            )

        return loss_denoised, loss_recon

    def forward(self, xyz):
        if self.full_instrumentation_enabled and self.training:
            raise RuntimeError(
                'Full-model instrumentation is inference-only; call eval() first'
            )
        q, coarse_point_cloud, denoise_length, rim_aux = self.base_model(xyz)
    
        B, M ,C = q.shape

        global_feature = self.increase_dim(q.transpose(1,2)).transpose(1,2) # B M 1024
        global_feature = torch.max(global_feature, dim=1)[0] # B 1024

        rebuild_feature = torch.cat([
            global_feature.unsqueeze(-2).expand(-1, M, -1),
            q,
            coarse_point_cloud], dim=-1)  # B M 1027 + C

        
        # NOTE: foldingNet
        if self.decoder_type == 'fold':
            rebuild_feature = self.reduce_map(rebuild_feature.reshape(B*M, -1)) # BM C
            relative_xyz = self.decode_head(rebuild_feature).reshape(B, M, 3, -1)    # B M 3 S
            rebuild_points = (relative_xyz + coarse_point_cloud.unsqueeze(-1)).transpose(2,3)  # B M S 3

        else:
            rebuild_feature = self.reduce_map(rebuild_feature) # B M C
            relative_xyz = self.decode_head(rebuild_feature)   # B M S 3
            rebuild_points = (relative_xyz + coarse_point_cloud.unsqueeze(-2))  # B M S 3

        if self.full_instrumentation_enabled:
            self._last_full_instrumentation = {
                'decoder_query': q.detach(),
                'coarse_point_cloud': coarse_point_cloud.detach(),
                'rebuild_global_feature': global_feature.detach(),
                'rebuild_feature': rebuild_feature.detach(),
                'relative_xyz': relative_xyz.detach(),
                'rebuild_points_grouped': rebuild_points.detach(),
            }

        if self.training and denoise_length > 0:
            # split the reconstruction and denoise task
            pred_fine = rebuild_points[:, :-denoise_length].reshape(B, -1, 3).contiguous()
            pred_coarse = coarse_point_cloud[:, :-denoise_length].contiguous()

            denoised_fine = rebuild_points[:, -denoise_length:].reshape(B, -1, 3).contiguous()
            denoised_coarse = coarse_point_cloud[:, -denoise_length:].contiguous()

            assert pred_fine.size(1) == self.num_query * self.factor
            assert pred_coarse.size(1) == self.num_query

            ret = (pred_coarse, denoised_coarse, denoised_fine, pred_fine)
            if rim_aux is not None:
                ret = ret + (rim_aux,)
            return ret
        elif self.training:
            pred_fine = rebuild_points.reshape(B, -1, 3).contiguous()
            pred_coarse = coarse_point_cloud.contiguous()

            assert pred_fine.size(1) == self.num_query * self.factor
            assert pred_coarse.size(1) == self.num_query

            ret = (
                pred_coarse,
                pred_coarse[:, :0],
                pred_fine[:, :0],
                pred_fine,
            )
            if rim_aux is not None:
                ret = ret + (rim_aux,)
            return ret

        else:
            assert denoise_length == 0
            rebuild_points = rebuild_points.reshape(B, -1, 3).contiguous()  # B N 3

            assert rebuild_points.size(1) == self.num_query * self.factor
            assert coarse_point_cloud.size(1) == self.num_query

            ret = (coarse_point_cloud, rebuild_points)
            return ret
