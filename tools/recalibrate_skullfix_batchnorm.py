#!/usr/bin/env python
"""Recompute BatchNorm running statistics without updating model weights."""

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.skullfix_metrics import normalized_point_surface_metrics  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--max_batches", type=int, default=32)
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260630)
    return parser.parse_args()


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_case_metadata(dataset):
    record = dataset.get_record(0)
    point_path = Path(record["point_path"])
    if not point_path.is_absolute():
        point_path = Path(dataset.data_root) / point_path
    with np.load(point_path, allow_pickle=False) as sample:
        centroid = sample["centroid"].astype(np.float64)
        scale = float(sample["scale"])
    return centroid, scale


def predict(model, points, device):
    model.eval()
    with torch.no_grad():
        return model(points.unsqueeze(0).to(device))[-1][0].cpu().numpy()


def metric_summary(prediction, reference, centroid, scale):
    metrics = normalized_point_surface_metrics(
        prediction,
        reference,
        centroid,
        scale,
        tolerances_mm=(0.5, 1.0, 2.0),
    )
    return metrics.as_dict()


def format_metrics(name, metrics):
    print(
        f"{name}: CD={metrics['cd_l1_mm']:.6f}mm "
        f"HD95={metrics['hd95_mm']:.6f}mm "
        f"NSD@1={metrics['nsd_at_1mm']:.6f} "
        f"P->R={metrics['pred_to_ref_mean_mm']:.6f}mm "
        f"R->P={metrics['ref_to_pred_mean_mm']:.6f}mm"
    )


def main():
    args = parse_args()
    if args.batch_size < 1 or args.max_batches < 1:
        raise ValueError("batch_size and max_batches must be positive")

    set_seed(args.seed)
    config = cfg_from_yaml_file(args.config)
    train_cfg = config.dataset.train
    dataset = build_dataset_from_cfg(train_cfg._base_, train_cfg.others)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        drop_last=False,
        num_workers=args.num_workers,
    )

    _, _, first_data = dataset[0]
    first_input, first_target = first_data
    centroid, scale = load_case_metadata(dataset)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = builder.model_builder(config.model).to(device)
    builder.load_model(model, args.ckpt)

    before = metric_summary(
        predict(model, first_input, device),
        first_target.numpy(),
        centroid,
        scale,
    )
    format_metrics("before", before)

    batchnorm_layers = [
        module
        for module in model.modules()
        if isinstance(module, nn.modules.batchnorm._BatchNorm)
    ]
    if not batchnorm_layers:
        raise RuntimeError("Model has no BatchNorm layers to recalibrate")

    model.eval()
    for module in batchnorm_layers:
        module.reset_running_stats()
        module.momentum = None
        module.train()

    batches_used = 0
    progress_total = min(len(loader), args.max_batches)
    with torch.no_grad():
        progress = tqdm(
            loader,
            total=progress_total,
            desc="BNCal",
            dynamic_ncols=True,
        )
        for _, _, data in progress:
            model(data[0].to(device))
            batches_used += 1
            progress.set_postfix(
                batches=f"{batches_used}/{progress_total}",
                refresh=False,
            )
            if batches_used >= args.max_batches:
                break
        progress.close()

    after = metric_summary(
        predict(model, first_input, device),
        first_target.numpy(),
        centroid,
        scale,
    )
    format_metrics("after", after)

    checkpoint = torch.load(args.ckpt, map_location="cpu")
    checkpoint["base_model"] = {
        name: tensor.detach().cpu()
        for name, tensor in model.state_dict().items()
    }
    checkpoint["bn_recalibration"] = {
        "config": args.config,
        "source_checkpoint": args.ckpt,
        "batches_used": batches_used,
        "batch_size": args.batch_size,
        "reset_running_stats": True,
        "before": before,
        "after": after,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    torch.save(checkpoint, temporary)
    temporary.replace(output)

    report_path = output.with_suffix(output.suffix + ".json")
    report_path.write_text(
        json.dumps(checkpoint["bn_recalibration"], indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[saved] {output}")
    print(f"[saved] {report_path}")
    print(
        f"[ok] recalibrated {len(batchnorm_layers)} BatchNorm layers "
        f"with {batches_used} batches"
    )


if __name__ == "__main__":
    main()
