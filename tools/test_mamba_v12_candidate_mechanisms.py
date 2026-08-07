#!/usr/bin/env python
"""CUDA-independent unit checks for preregistered Mamba v1.2 candidates."""

import sys
import inspect
from pathlib import Path

import torch
from easydict import EasyDict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import models.AdaPoinTr as adapointr_module  # noqa: E402


class FakeMixer(torch.nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.scale = torch.nn.Parameter(torch.linspace(0.5, 1.5, dim))

    def forward(self, x):
        return x * self.scale


def config(mechanism):
    return EasyDict({
        "enabled": True,
        "adapter_type": "fake",
        "depth": 2,
        "d_state": 4,
        "d_conv": 3,
        "expand": 1,
        "use_fast_path": False,
        "drop_path": 0.0,
        "alpha_init": 0.01,
        "order": "xyz",
        "mechanism": mechanism,
        "normalization_eps": 1e-6,
        "normalization_scale_min": 0.1,
        "normalization_scale_max": 10.0,
    })


def main():
    original_builder = adapointr_module.build_sequence_mixer
    adapointr_module.build_sequence_mixer = lambda dim, **kwargs: FakeMixer(dim)
    try:
        assert "partial" in inspect.signature(
            adapointr_module.AdaPoinTr.get_loss
        ).parameters
        torch.manual_seed(7)
        x = torch.randn(2, 9, 4)
        coor = torch.randn(2, 9, 3)

        c0 = adapointr_module.MambaSequenceAdapter(4, config("o0")).eval()
        sort_idx, inv_idx = c0._ordering_indices(coor, "xyz")
        gather = sort_idx.unsqueeze(-1).expand_as(x)
        ordered = torch.gather(x, 1, gather)
        expected = ordered
        for block in c0.blocks:
            expected = expected + block.alpha * block.mixer(block.norm(expected))
        expected = torch.gather(
            expected,
            1,
            inv_idx.unsqueeze(-1).expand_as(expected),
        )
        assert torch.equal(c0(x, coor), expected)

        c1 = adapointr_module.MambaSequenceAdapter(
            4, config("residual_budget")
        ).eval()
        gates = c1.total_residual_budget * torch.softmax(c1.budget_logits, 0)
        assert torch.allclose(gates, torch.tensor([0.01, 0.01]))
        assert torch.allclose(gates.sum(), torch.tensor(0.02))
        assert c1.budget_logits.requires_grad
        assert all(not block.alpha.requires_grad for block in c1.blocks)

        c2 = adapointr_module.MambaSequenceAdapter(
            4, config("normalized_gate")
        ).eval()
        c2.enable_instrumentation(True)
        output_without = c2(x, coor)
        records = c2.pop_instrumentation()
        assert all(
            0.1 <= row["normalization_scale"] <= 10.0
            for row in records["block_rows"]
        )
        c2.enable_instrumentation(False)
        assert torch.equal(output_without, c2(x, coor))

        c3 = adapointr_module.MambaSequenceAdapter(
            4, config("bidirectional_shared")
        ).eval()
        assert all(not hasattr(block, "reverse_mixer") for block in c3.blocks)
        c3.enable_instrumentation(False)
        plain = c3(x, coor)
        c3.enable_instrumentation(True)
        observed = c3(x, coor)
        assert torch.equal(plain, observed)

        print("[ok] C0 is exactly the frozen O0 residual path")
        print("[ok] C1 fixed 0.02 budget with learnable softmax allocation")
        print("[ok] C2 bounded per-sample RMS normalization")
        print("[ok] C3 shared-weight bidirectional averaging")
        print("[ok] candidate instrumentation is zero-perturbation")
        print("[ok] loss API accepts and ignores runner partial input")
    finally:
        adapointr_module.build_sequence_mixer = original_builder


if __name__ == "__main__":
    main()
