#!/usr/bin/env python
"""Zero-perturbation tests for Mamba adapter instrumentation."""

import os
import sys

import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from models.AdaPoinTr import MambaSequenceAdapter


class Config:
    enabled = True
    adapter_type = "gated_conv"
    depth = 2
    d_state = 8
    d_conv = 3
    expand = 2
    use_fast_path = False
    drop_path = 0.0
    alpha_init = 0.01
    order = "xyz"


def main():
    torch.manual_seed(20260803)
    adapter = MambaSequenceAdapter(dim=16, config=Config()).eval()
    x = torch.randn(2, 32, 16)
    coor = torch.randn(2, 32, 3)

    with torch.no_grad():
        reference = adapter(x.clone(), coor.clone())
        adapter.enable_instrumentation(True)
        observed = adapter(x.clone(), coor.clone())

    if not torch.equal(reference, observed):
        max_delta = (reference - observed).abs().max().item()
        raise AssertionError(
            f"Instrumentation perturbed output; max_abs_delta={max_delta}"
        )
    records = adapter.pop_instrumentation()
    if records is None:
        raise AssertionError("Instrumentation did not produce records")
    if len(records["ordering_rows"]) != x.size(0):
        raise AssertionError("Unexpected ordering row count")
    if len(records["block_rows"]) != x.size(0) * len(adapter.blocks):
        raise AssertionError("Unexpected block row count")
    if records["sort_idx"].shape != (x.size(0), x.size(1)):
        raise AssertionError("Unexpected sort index shape")
    if adapter.pop_instrumentation() is not None:
        raise AssertionError("pop_instrumentation must clear records")

    adapter.train()
    try:
        adapter(x, coor)
    except RuntimeError as exc:
        if "inference-only" not in str(exc):
            raise
    else:
        raise AssertionError("Training-time instrumentation was not rejected")

    print("[ok] instrumentation is bitwise zero-perturbation in eval mode")
    print("[ok] records, token arrays, and inference-only guard validated")


if __name__ == "__main__":
    main()
