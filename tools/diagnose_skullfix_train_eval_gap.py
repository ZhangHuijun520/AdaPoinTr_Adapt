#!/usr/bin/env python
"""Compare SkullFix predictions across AdaPoinTr train/eval branches and BN modes."""

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.skullfix_metrics import (  # noqa: E402
    normalized_point_surface_metrics,
    normalized_to_world,
)


MODES = (
    "eval_standard",
    "eval_branch_batch_bn",
    "train_branch_eval_layers",
    "train_full",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate one fixed SkullFix sample using standard inference, "
            "eval-branch with batch BN, train-branch with eval layers, and "
            "full train mode."
        )
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260629)
    parser.add_argument(
        "--out",
        default="logs/skullfix/train_eval_gap_diagnostic.json",
    )
    return parser.parse_args()


def set_batchnorm_training(module, training):
    for child in module.modules():
        if isinstance(child, nn.modules.batchnorm._BatchNorm):
            child.train(training)


def configure_mode(model, mode):
    model.eval()
    if mode == "eval_standard":
        return
    if mode == "eval_branch_batch_bn":
        set_batchnorm_training(model, True)
        return
    if mode == "train_branch_eval_layers":
        # Activate only the two flags used to select AdaPoinTr's denoising
        # branch. Child layers remain in eval mode.
        model.training = True
        model.base_model.training = True
        return
    if mode == "train_full":
        model.train()
        return
    raise ValueError(f"Unknown diagnostic mode: {mode}")


def load_case_metadata(dataset):
    record = dataset.get_record(0)
    point_path = Path(record["point_path"])
    if not point_path.is_absolute():
        point_path = Path(dataset.data_root) / point_path
    with np.load(point_path, allow_pickle=False) as sample:
        centroid = sample["centroid"].astype(np.float64)
        scale = float(sample["scale"])
    return record, centroid, scale


def batchnorm_summary(model):
    tracked = []
    invalid = []
    for name, module in model.named_modules():
        if not isinstance(module, nn.modules.batchnorm._BatchNorm):
            continue
        batches = (
            int(module.num_batches_tracked.item())
            if module.num_batches_tracked is not None
            else None
        )
        tracked.append(batches)
        if module.running_mean is not None and not torch.isfinite(module.running_mean).all():
            invalid.append(f"{name}.running_mean")
        if module.running_var is not None and not torch.isfinite(module.running_var).all():
            invalid.append(f"{name}.running_var")
    return {
        "layers": len(tracked),
        "num_batches_tracked_min": min(tracked) if tracked else None,
        "num_batches_tracked_max": max(tracked) if tracked else None,
        "nonfinite_buffers": invalid,
    }


def geometry_summary(points_normalized, centroid, scale):
    points_world = normalized_to_world(points_normalized, centroid, scale)
    center = points_world.mean(axis=0)
    radii = np.linalg.norm(points_world - center, axis=1)
    return {
        "center_mm": center.tolist(),
        "bbox_span_mm": np.ptp(points_world, axis=0).tolist(),
        "radius_p95_mm": float(np.percentile(radii, 95)),
    }


def predict(model, inputs, mode):
    configure_mode(model, mode)
    with torch.no_grad():
        output = model(inputs)
    prediction = output[-1]
    if prediction.ndim != 3 or prediction.shape[-1] != 3:
        raise RuntimeError(
            f"{mode}: expected final prediction shape (B, N, 3), "
            f"got {tuple(prediction.shape)}"
        )
    return prediction[0].detach().cpu().numpy()


def main():
    args = parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch_size must be >= 1")

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    config = cfg_from_yaml_file(args.config)
    dataset_cfg = config.dataset.test
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    if len(dataset) != 1:
        raise ValueError(f"Diagnostic expects one test sample, got {len(dataset)}")

    _, model_id, data = dataset[0]
    model_input, gt = data
    record, centroid, scale = load_case_metadata(dataset)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    inputs = model_input.unsqueeze(0).repeat(args.batch_size, 1, 1).to(device)
    gt_np = gt.numpy()

    model = builder.model_builder(config.model)
    model.to(device)

    report = {
        "config": args.config,
        "ckpt": args.ckpt,
        "case_id": str(model_id),
        "dataset_input_key": dataset.input_key,
        "batch_size": args.batch_size,
        "centroid": centroid.tolist(),
        "scale_mm_per_normalized_unit": scale,
        "reference_geometry": geometry_summary(gt_np, centroid, scale),
        "input_vs_gt": normalized_point_surface_metrics(
            model_input.numpy(),
            gt_np,
            centroid,
            scale,
            tolerances_mm=(0.5, 1.0, 2.0),
        ).as_dict(),
        "modes": {},
    }

    for mode in MODES:
        builder.load_model(model, args.ckpt)
        torch.manual_seed(args.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(args.seed)
        prediction = predict(model, inputs, mode)
        metrics = normalized_point_surface_metrics(
            prediction,
            gt_np,
            centroid,
            scale,
            tolerances_mm=(0.5, 1.0, 2.0),
        )
        report["modes"][mode] = {
            "metrics": metrics.as_dict(),
            "geometry": geometry_summary(prediction, centroid, scale),
            "batchnorm": batchnorm_summary(model),
        }
        print(
            f"{mode}: "
            f"CD={metrics.cd_l1_mm:.6f} mm "
            f"ASSD={metrics.assd_mm:.6f} mm "
            f"HD95={metrics.hd95_mm:.6f} mm "
            f"NSD@1mm={metrics.nsd[1.0]:.6f} "
            f"P->R={metrics.pred_to_ref_mean_mm:.6f} mm "
            f"R->P={metrics.ref_to_pred_mean_mm:.6f} mm"
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[saved] {out_path}")
    print("[ok] train/eval gap diagnostic completed")


if __name__ == "__main__":
    main()
