#!/usr/bin/env python
"""Benchmark frozen candidate inference latency and peak CUDA memory."""

import argparse
import hashlib
import json
import os
import statistics
import sys
import time
from pathlib import Path

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
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--split", choices=("train", "val", "test"), default="val")
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=50)
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    args = parse_args()
    if args.warmup < 1 or args.repeats < 1:
        raise ValueError("warmup and repeats must be positive")
    if not torch.cuda.is_available():
        raise RuntimeError("Efficiency benchmark requires CUDA")
    config = cfg_from_yaml_file(args.config)
    dataset_cfg = getattr(config.dataset, args.split)
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    batch = dataset[0][2][0].unsqueeze(0).cuda()
    model = builder.model_builder(config.model).cuda().eval()
    builder.load_model(model, args.ckpt)
    model.enable_full_instrumentation(False)

    with torch.no_grad():
        for _ in tqdm(range(args.warmup), desc="Efficiency warmup", dynamic_ncols=True):
            model(batch)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        timings = []
        for _ in tqdm(range(args.repeats), desc="Efficiency timing", dynamic_ncols=True):
            torch.cuda.synchronize()
            start = time.perf_counter()
            model(batch)
            torch.cuda.synchronize()
            timings.append((time.perf_counter() - start) * 1000.0)
    timings_sorted = sorted(timings)
    p95_index = min(len(timings_sorted) - 1, int(0.95 * len(timings_sorted)))
    payload = {
        "benchmark_version": "mamba-v12-efficiency-v1",
        "batch_size": 1,
        "warmup": args.warmup,
        "repeats": args.repeats,
        "latency_ms_mean": statistics.mean(timings),
        "latency_ms_median": statistics.median(timings),
        "latency_ms_p95": timings_sorted[p95_index],
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "gpu": torch.cuda.get_device_name(0),
        "config": args.config,
        "config_sha256": sha256_file(args.config),
        "checkpoint": args.ckpt,
        "checkpoint_sha256": sha256_file(args.ckpt),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[saved] {output}")
    print(
        f"[benchmark] median={payload['latency_ms_median']:.3f} ms "
        f"peak={payload['peak_gpu_memory_bytes'] / 2**20:.1f} MiB"
    )


if __name__ == "__main__":
    main()
