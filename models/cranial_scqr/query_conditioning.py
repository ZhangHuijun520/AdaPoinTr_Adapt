"""Ordinary/contact-biased query attention for SCQR Q0 and QC."""

import math
from typing import NamedTuple

import torch
import torch.nn as nn

from .local_geometry import initialize_scqr_module, residual_warmup


class QueryConditioningOutput(NamedTuple):
    queries: torch.Tensor
    attention: torch.Tensor
    logits: torch.Tensor
    residual: torch.Tensor
    warmup: float


class ContactConditionedQueryAttention(nn.Module):
    """Single-head query-to-proxy attention with fixed beta log support bias."""

    def __init__(
        self,
        embed_dim=384,
        attention_dim=128,
        beta=0.0,
        alpha_init=0.01,
        warmup_epochs=20,
        probability_floor=1.0e-4,
    ):
        super().__init__()
        self.embed_dim = int(embed_dim)
        self.attention_dim = int(attention_dim)
        self.warmup_epochs = int(warmup_epochs)
        self.probability_floor = float(probability_floor)
        beta = float(beta)
        if self.embed_dim != 384 or self.attention_dim != 128:
            raise ValueError("Cranial-SCQR v1.1 requires d=384 and d_attn=128")
        if beta not in (0.0, 1.0):
            raise ValueError("contact bias beta must be exactly 0 or 1")
        if self.probability_floor != 1.0e-4:
            raise ValueError("Cranial-SCQR v1.1 fixes probability_floor=1e-4")
        self.register_buffer("beta", torch.tensor(beta), persistent=True)
        self.query_norm = nn.LayerNorm(self.embed_dim, eps=1.0e-5)
        self.key_norm = nn.LayerNorm(self.embed_dim, eps=1.0e-5)
        self.value_norm = nn.LayerNorm(self.embed_dim, eps=1.0e-5)
        self.query_projection = nn.Linear(self.embed_dim, self.attention_dim)
        self.key_projection = nn.Linear(self.embed_dim, self.attention_dim)
        self.value_projection = nn.Linear(self.embed_dim, self.attention_dim)
        self.output_mlp = nn.Sequential(
            nn.Linear(self.embed_dim + self.attention_dim, self.embed_dim),
            nn.GELU(),
            nn.Linear(self.embed_dim, self.embed_dim),
        )
        self.output_norm = nn.LayerNorm(self.embed_dim, eps=1.0e-5)
        self.alpha_q = nn.Parameter(torch.tensor([float(alpha_init)]))
        initialize_scqr_module(self)

    def forward(
        self,
        queries,
        proxy_features,
        position_embedding,
        contact_probability,
        epoch=None,
    ):
        if not torch.is_tensor(queries) or queries.ndim != 3:
            raise ValueError("queries must have shape (B, N_QUERY, 384)")
        if queries.shape[-1] != self.embed_dim:
            raise ValueError("query feature dimension mismatch")
        if proxy_features.shape != position_embedding.shape:
            raise ValueError("proxy_features and position_embedding must match")
        if proxy_features.shape[0] != queries.shape[0] or proxy_features.shape[-1] != self.embed_dim:
            raise ValueError("query/proxy batch or feature dimension mismatch")
        if contact_probability.shape != proxy_features.shape[:2]:
            raise ValueError("contact_probability must have shape (B, N_PROXY)")
        tensors = (queries, proxy_features, position_embedding, contact_probability)
        if len({tensor.device for tensor in tensors}) != 1:
            raise ValueError("all query conditioning tensors must share a device")
        if not all(torch.isfinite(tensor).all() for tensor in tensors):
            raise ValueError("query conditioning tensors must be finite")

        q = self.query_projection(self.query_norm(queries)).float()
        k = self.key_projection(
            self.key_norm(proxy_features + position_embedding)
        ).float()
        value = self.value_projection(self.value_norm(proxy_features)).float()
        logits = torch.matmul(q, k.transpose(-1, -2)) / math.sqrt(
            float(self.attention_dim)
        )
        log_bias = self.beta.float() * torch.log(
            contact_probability.detach().float().clamp_min(self.probability_floor)
        )
        logits = logits + log_bias.unsqueeze(1)
        attention = torch.softmax(logits, dim=-1)
        attended = torch.matmul(attention, value).to(dtype=queries.dtype)
        update = self.output_norm(
            self.output_mlp(torch.cat([queries, attended], dim=-1))
        )
        warmup = residual_warmup(epoch, self.warmup_epochs)
        residual = self.alpha_q.reshape(1, 1, 1) * warmup * update
        return QueryConditioningOutput(
            queries=queries + residual,
            attention=attention,
            logits=logits,
            residual=residual,
            warmup=warmup,
        )
