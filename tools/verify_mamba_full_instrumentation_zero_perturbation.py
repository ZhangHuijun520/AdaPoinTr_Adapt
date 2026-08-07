#!/usr/bin/env python
"""Require bitwise output and RNG equality for full-pipeline observers."""

import argparse
import hashlib
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ckpt", default="")
    parser.add_argument("--split", choices=("train", "val", "test"), default="val")
    parser.add_argument("--num_cases", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260805)
    parser.add_argument("--device", default="cuda:0")
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clone_outputs(outputs):
    if not isinstance(outputs, (list, tuple)):
        outputs = (outputs,)
    return tuple(output.detach().clone() for output in outputs)


def rng_state():
    return {
        "cpu": torch.random.get_rng_state().clone(),
        "cuda": [item.clone() for item in torch.cuda.get_rng_state_all()]
        if torch.cuda.is_available() else [],
    }


def restore_rng(state):
    torch.random.set_rng_state(state["cpu"])
    if state["cuda"]:
        torch.cuda.set_rng_state_all(state["cuda"])


def rng_equal(left, right):
    return torch.equal(left["cpu"], right["cpu"]) and len(left["cuda"]) == len(
        right["cuda"]
    ) and all(torch.equal(a, b) for a, b in zip(left["cuda"], right["cuda"]))


def main():
    args = parse_args()
    if args.num_cases < 1:
        raise ValueError("num_cases must be positive")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    config = cfg_from_yaml_file(args.config)
    dataset_cfg = getattr(config.dataset, args.split)
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = builder.model_builder(config.model)
    if args.ckpt:
        builder.load_model(model, args.ckpt)
    model.to(device).eval()

    rows = []
    with torch.no_grad():
        for index in tqdm(
            range(min(args.num_cases, len(dataset))),
            desc="Verify full instrumentation",
            dynamic_ncols=True,
        ):
            _, case_id, data = dataset[index]
            batch = data[0].unsqueeze(0).to(device)
            model.enable_full_instrumentation(False)
            initial = rng_state()
            reference = clone_outputs(model(batch))
            reference_rng = rng_state()
            restore_rng(initial)
            model.enable_full_instrumentation(True)
            observed = clone_outputs(model(batch))
            observed_rng = rng_state()
            records = model.pop_full_instrumentation()
            equal = len(reference) == len(observed) and all(
                torch.equal(a, b) for a, b in zip(reference, observed)
            )
            same_rng = rng_equal(reference_rng, observed_rng)
            if not equal or not same_rng or records is None:
                raise RuntimeError(
                    f"Observer perturbation for {case_id}: output={equal} "
                    f"rng={same_rng} records={records is not None}"
                )
            rows.append({
                "case_id": str(case_id),
                "bitwise_equal": equal,
                "rng_state_equal": same_rng,
                "decoder_layers": len(records["backbone"]["decoder_layers"]),
            })
    model.enable_full_instrumentation(False)
    payload = {
        "verification_version": "mamba-full-instrumentation-zero-perturbation-v1",
        "passed": True,
        "config": args.config,
        "config_sha256": sha256_file(args.config),
        "checkpoint": args.ckpt or None,
        "checkpoint_sha256": sha256_file(args.ckpt) if args.ckpt else None,
        "split": args.split,
        "cases": rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    Path(str(output) + ".sha256").write_text(
        f"{sha256_file(output)}  {output.name}\n", encoding="ascii"
    )
    print(f"[ok] full-pipeline observer is bitwise/RNG zero-perturbation: {output}")


if __name__ == "__main__":
    main()
