#!/usr/bin/env python
"""Generate an immutable R0 coarse-moment cache for D2.2 R2 training."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.mamba_d22_geometry import radial_rms  # noqa: E402


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--fold", required=True, choices=tuple("ABCD"))
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    config = cfg_from_yaml_file(args.config)
    guard = getattr(config.model, "local_rim_guard", None)
    if guard is not None and bool(getattr(guard, "enabled", False)):
        raise RuntimeError("Teacher cache config must be the unmodified R0 arm")
    if bool(getattr(config.dataset.train._base_, "CARS", False)):
        raise RuntimeError("Geometry-changing random dropping invalidates cache")

    dataset_cfg = config.dataset.train
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        drop_last=False,
    )
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = builder.model_builder(config.model)
    builder.load_model(model, args.ckpt)
    model.to(device)
    model.eval()

    entries = {}
    with torch.no_grad():
        for _, case_ids, data in tqdm(
            loader, desc="Cache R0 coarse moments", dynamic_ncols=True
        ):
            partial = data[0].to(device)
            coarse = model(partial)[0]
            centroids = coarse.mean(dim=1).cpu()
            radii = radial_rms(coarse).cpu()
            scales = dataset.get_normalization_scales(
                case_ids, dtype=torch.float64
            )
            for index, case_id in enumerate(case_ids):
                case_id = str(case_id)
                if case_id in entries:
                    raise RuntimeError(f"Duplicate teacher cache case: {case_id}")
                entries[case_id] = {
                    "normalization_scale": float(scales[index]),
                    "coarse_centroid_normalized": [
                        float(value) for value in centroids[index]
                    ],
                    "coarse_radial_rms_normalized": float(radii[index]),
                }

    expected_ids = {str(record["case_id"]) for record in dataset.records}
    if set(entries) != expected_ids:
        raise RuntimeError("Teacher cache does not cover the full fold-train set")
    entries = dict(sorted(entries.items()))
    entries_payload = canonical_bytes(entries)
    payload = {
        "protocol_version": "mamba-v12-d22-teacher-cache-v1",
        "candidate": "R0",
        "fold": args.fold,
        "seed": args.seed,
        "checkpoint_path": args.ckpt,
        "checkpoint_sha256": sha256_file(args.ckpt),
        "config_path": args.config,
        "config_sha256": sha256_file(args.config),
        "cache_sha256": hashlib.sha256(entries_payload).hexdigest(),
        "teacher_mode": "eval_no_grad_no_bn_update",
        "geometry_augmentation": False,
        "protected_splits_accessed": False,
        "entries": entries,
    }
    output = canonical_bytes(payload)
    output_hash = hashlib.sha256(output).hexdigest()
    sidecar = f"{output_hash}  {args.output.name}\n".encode("ascii")

    if args.output.exists():
        if args.output.read_bytes() != output:
            raise RuntimeError(
                f"Refusing to overwrite non-identical teacher cache: {args.output}"
            )
        sha_path = Path(str(args.output) + ".sha256")
        if not sha_path.is_file() or sha_path.read_bytes() != sidecar:
            raise RuntimeError("Existing teacher-cache sidecar differs")
        print(f"[locked] existing teacher cache is byte-identical: {args.output}")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    Path(str(args.output) + ".sha256").write_bytes(sidecar)
    print(f"[saved] immutable R0 teacher cache: {args.output}")
    print(f"[sha256] {output_hash}")
    print(f"[locked] eval/no_grad cases={len(entries)} protected_splits=false")


if __name__ == "__main__":
    main()
