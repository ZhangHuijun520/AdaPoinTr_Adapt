import os
import sys

import torch
from easydict import EasyDict as edict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import models
from models.build import build_model_from_cfg


def build_toy_config():
    return edict(
        NAME="AdaPoinTr",
        num_query=16,
        num_points=64,
        center_num=[16, 8],
        global_feature_dim=128,
        encoder_type="graph",
        decoder_type="fc",
        encoder_config=edict(
            embed_dim=64,
            depth=1,
            num_heads=4,
            k=4,
            n_group=1,
            mlp_ratio=2.0,
            block_style_list=["attn"],
            combine_style="concat",
        ),
        decoder_config=edict(
            embed_dim=64,
            depth=1,
            num_heads=4,
            k=4,
            n_group=1,
            mlp_ratio=2.0,
            self_attn_block_style_list=["attn"],
            self_attn_combine_style="concat",
            cross_attn_block_style_list=["attn"],
            cross_attn_combine_style="concat",
        ),
    )


def main():
    if not torch.cuda.is_available():
        raise RuntimeError("AdaPoinTr uses CUDA paths; no CUDA device was found.")

    torch.manual_seed(0)
    model = build_model_from_cfg(build_toy_config()).cuda().train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    partial = torch.rand(1, 128, 3, device="cuda")
    gt = torch.rand(1, 64, 3, device="cuda")

    ret = model(partial)
    loss_denoised, loss_recon = model.get_loss(ret, gt, epoch=1)
    loss = loss_denoised + loss_recon

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    max_mem = torch.cuda.max_memory_allocated() / 1024 / 1024
    print(f"toy smoke ok | loss={loss.item():.6f} | max_cuda_mem={max_mem:.1f} MB")


if __name__ == "__main__":
    main()
