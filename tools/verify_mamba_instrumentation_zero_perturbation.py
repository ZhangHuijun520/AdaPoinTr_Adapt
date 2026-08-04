#!/usr/bin/env python
"""Verify full-model output and RNG equality with instrumentation enabled."""

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
    parser.add_argument("--panel", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ckpt", default="")
    parser.add_argument("--num_cases", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260803)
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


def capture_rng_state():
    return {
        "cpu": torch.random.get_rng_state().clone(),
        "cuda": [state.clone() for state in torch.cuda.get_rng_state_all()]
        if torch.cuda.is_available()
        else [],
    }


def restore_rng_state(state):
    torch.random.set_rng_state(state["cpu"])
    if state["cuda"]:
        torch.cuda.set_rng_state_all(state["cuda"])


def rng_states_equal(left, right):
    return torch.equal(left["cpu"], right["cpu"]) and len(
        left["cuda"]
    ) == len(right["cuda"]) and all(
        torch.equal(a, b) for a, b in zip(left["cuda"], right["cuda"])
    )


def main():
    args = parse_args()
    if args.num_cases < 1:
        raise ValueError("num_cases must be positive")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    panel_path = Path(args.panel)
    panel = json.loads(panel_path.read_text(encoding="utf-8"))
    if panel["dataset_split"] != "train":
        raise RuntimeError("Zero-perturbation verification requires train panel")

    config = cfg_from_yaml_file(args.config)
    dataset_cfg = config.dataset.train
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    index_by_case = {
        str(record["case_id"]): index
        for index, record in enumerate(dataset.records)
    }
    case_ids = [
        str(item["case_id"])
        for item in panel["cases"][: args.num_cases]
    ]

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = builder.model_builder(config.model)
    if args.ckpt:
        builder.load_model(model, args.ckpt)
    model.to(device)
    model.eval()

    rows = []
    with torch.no_grad():
        for case_id in tqdm(
            case_ids,
            desc="Verify zero perturbation",
            dynamic_ncols=True,
        ):
            partial = dataset[index_by_case[case_id]][2][0]
            batch = partial.unsqueeze(0).to(device)
            model.enable_mamba_instrumentation(False)
            initial_rng = capture_rng_state()
            reference = clone_outputs(model(batch))
            reference_rng = capture_rng_state()

            restore_rng_state(initial_rng)
            model.enable_mamba_instrumentation(True)
            observed = clone_outputs(model(batch))
            observed_rng = capture_rng_state()
            records = model.pop_mamba_instrumentation()

            max_deltas = [
                float((left - right).abs().max().cpu())
                for left, right in zip(reference, observed)
            ]
            bitwise_equal = len(reference) == len(observed) and all(
                torch.equal(left, right)
                for left, right in zip(reference, observed)
            )
            rng_equal = rng_states_equal(reference_rng, observed_rng)
            if not bitwise_equal or not rng_equal or records is None:
                raise RuntimeError(
                    f"Instrumentation perturbation for {case_id}: "
                    f"bitwise_equal={bitwise_equal} rng_equal={rng_equal} "
                    f"max_deltas={max_deltas} records={records is not None}"
                )
            rows.append({
                "case_id": case_id,
                "bitwise_equal": bitwise_equal,
                "rng_state_equal": rng_equal,
                "max_abs_deltas": max_deltas,
                "ordering_rows": len(records["ordering_rows"]),
                "block_rows": len(records["block_rows"]),
            })

    model.enable_mamba_instrumentation(False)
    payload = {
        "verification_version": "mamba-instrumentation-zero-perturbation-v1",
        "passed": True,
        "full_model_verified": True,
        "bitwise_equality_required": True,
        "rng_state_equality_required": True,
        "config": args.config,
        "config_sha256": sha256_file(args.config),
        "checkpoint": args.ckpt or None,
        "checkpoint_sha256": sha256_file(args.ckpt) if args.ckpt else None,
        "panel": str(panel_path),
        "panel_sha256": sha256_file(panel_path),
        "cases": rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    sidecar = Path(str(output) + ".sha256")
    sidecar.write_text(
        f"{sha256_file(output)}  {output.name}\n", encoding="ascii"
    )
    print(f"[ok] full-model output and RNG are bitwise unchanged: {output}")
    print(f"[saved] {sidecar}")


if __name__ == "__main__":
    main()
