#!/usr/bin/env python
"""Verify that disabled D2.2 leaves the frozen O0 inference graph unchanged."""

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from tools import builder
from utils.config import cfg_from_yaml_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    config = cfg_from_yaml_file(args.config)
    candidate_config = copy.deepcopy(config.model)
    reference_config = copy.deepcopy(config.model)
    reference_config.pop("local_rim_guard", None)
    if bool(candidate_config.local_rim_guard.enabled):
        raise RuntimeError("R0 zero-perturbation config unexpectedly enables D2.2")

    torch.manual_seed(args.seed)
    candidate = builder.model_builder(candidate_config)
    torch.manual_seed(args.seed)
    reference = builder.model_builder(reference_config)
    reference.load_state_dict(candidate.state_dict(), strict=True)
    if tuple(candidate.state_dict()) != tuple(reference.state_dict()):
        raise RuntimeError("Disabled D2.2 changed model state-dict keys")

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    candidate.to(device).eval()
    reference.to(device).eval()
    torch.manual_seed(args.seed + 1)
    partial = torch.randn(1, 8192, 3, device=device)
    with torch.no_grad():
        candidate_output = candidate(partial)
        reference_output = reference(partial)
    exact = all(
        torch.equal(candidate_value, reference_value)
        for candidate_value, reference_value in zip(
            candidate_output, reference_output
        )
    )
    maximum_delta = max(
        float((candidate_value - reference_value).abs().max().cpu())
        for candidate_value, reference_value in zip(
            candidate_output, reference_output
        )
    )
    if not exact:
        raise RuntimeError(
            f"Disabled D2.2 changed R0 output; max_delta={maximum_delta}"
        )

    payload = {
        "verification": "mamba-v12-d22-r0-zero-perturbation-v1",
        "config": args.config,
        "config_sha256": hashlib.sha256(
            Path(args.config).read_bytes()
        ).hexdigest(),
        "state_dict_keys_equal": True,
        "outputs_exactly_equal": True,
        "maximum_output_delta": maximum_delta,
        "synthetic_input_only": True,
        "protected_splits_accessed": False,
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    if args.output.exists() and args.output.read_bytes() != encoded:
        raise RuntimeError("Refusing to overwrite non-identical R0 receipt")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    Path(str(args.output) + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="ascii"
    )
    print("[ok] disabled D2.2 is exactly zero-perturbation on R0 inference")
    print(f"[saved] {args.output}")


if __name__ == "__main__":
    main()
