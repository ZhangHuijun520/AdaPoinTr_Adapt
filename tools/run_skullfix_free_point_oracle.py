#!/usr/bin/env python
"""Optimize a free 8192-point tensor from a SkullFix model prediction to GT."""

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets import build_dataset_from_cfg  # noqa: E402
from extensions.chamfer_dist import ChamferDistanceL1Stable  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.skullfix_metrics import normalized_point_surface_metrics  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--min_lr_ratio", type=float, default=0.01)
    parser.add_argument("--log_every", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260629)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--init_points")
    parser.add_argument("--squared_distance_epsilon", type=float, default=1e-12)
    parser.add_argument(
        "--out_dir",
        default="logs/skullfix/free_point_oracle",
    )
    return parser.parse_args()


def load_case(config):
    dataset_cfg = config.dataset.test
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    if len(dataset) != 1:
        raise ValueError(f"Oracle expects exactly one test sample, got {len(dataset)}")
    _, model_id, data = dataset[0]
    model_input, gt = data

    record = dataset.get_record(0)
    point_path = Path(record["point_path"])
    if not point_path.is_absolute():
        point_path = Path(dataset.data_root) / point_path
    with np.load(point_path, allow_pickle=False) as sample:
        centroid = sample["centroid"].astype(np.float64)
        scale = float(sample["scale"])
    return str(model_id), model_input, gt, centroid, scale


def metric_row(step, loss, points, gt, centroid, scale, lr):
    metrics = normalized_point_surface_metrics(
        points,
        gt,
        centroid,
        scale,
        tolerances_mm=(0.5, 1.0, 2.0),
    ).as_dict()
    return {
        "step": int(step),
        "loss_normalized": float(loss),
        "lr": float(lr),
        **metrics,
    }


def print_row(row):
    print(
        f"step={row['step']:04d} "
        f"loss={row['loss_normalized']:.8f} "
        f"CD={row['cd_l1_mm']:.6f}mm "
        f"HD95={row['hd95_mm']:.6f}mm "
        f"NSD@1={row['nsd_at_1mm']:.6f} "
        f"P->R={row['pred_to_ref_mean_mm']:.6f}mm "
        f"R->P={row['ref_to_pred_mean_mm']:.6f}mm "
        f"lr={row['lr']:.8f}"
    )


def save_progress(out_dir, rows, current_points, best_points):
    np.save(out_dir / "current_free_points.npy", current_points)
    np.save(out_dir / "best_free_points.npy", best_points)
    csv_path = out_dir / "progress.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()
    if args.steps < 1:
        raise ValueError("--steps must be >= 1")
    if args.lr <= 0:
        raise ValueError("--lr must be positive")
    if not 0 < args.min_lr_ratio <= 1:
        raise ValueError("--min_lr_ratio must be in (0, 1]")
    if args.log_every < 1:
        raise ValueError("--log_every must be >= 1")
    if args.squared_distance_epsilon <= 0:
        raise ValueError("--squared_distance_epsilon must be positive")

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    config = cfg_from_yaml_file(args.config)
    model_id, model_input, gt, centroid, scale = load_case(config)
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    target = gt.unsqueeze(0).to(device)

    if args.init_points:
        initial_array = np.load(args.init_points).astype(np.float32, copy=False)
        if initial_array.shape != tuple(gt.shape):
            raise ValueError(
                f"Initial points shape {initial_array.shape} does not match "
                f"GT shape {tuple(gt.shape)}"
            )
        initial_prediction = torch.from_numpy(initial_array).unsqueeze(0).to(device)
        initialization = str(Path(args.init_points).resolve())
    else:
        input_batch = model_input.unsqueeze(0).to(device)
        model = builder.model_builder(config.model).to(device)
        builder.load_model(model, args.ckpt)
        model.eval()
        with torch.no_grad():
            initial_prediction = model(input_batch)[-1].detach()
        initialization = "model_prediction"
        del model, input_batch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if initial_prediction.shape != target.shape:
        raise ValueError(
            f"Prediction and GT must have identical shapes, got "
            f"{tuple(initial_prediction.shape)} and {tuple(target.shape)}"
        )

    free_points = torch.nn.Parameter(initial_prediction.clone())
    optimizer = torch.optim.Adam([free_points], lr=args.lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.steps,
        eta_min=args.lr * args.min_lr_ratio,
    )
    loss_func = ChamferDistanceL1Stable(args.squared_distance_epsilon)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    initial_np = initial_prediction[0].cpu().numpy()
    gt_np = gt.numpy()
    np.save(out_dir / "initial_prediction.npy", initial_np)
    np.save(out_dir / "ground_truth.npy", gt_np)

    with torch.no_grad():
        initial_loss = loss_func(free_points, target)
    rows = [
        metric_row(
            0,
            initial_loss.item(),
            initial_np,
            gt_np,
            centroid,
            scale,
            optimizer.param_groups[0]["lr"],
        )
    ]
    print("==== SkullFix free-point oracle ====")
    print_row(rows[-1])
    best_row = rows[-1]
    best_points = initial_np.copy()
    save_progress(out_dir, rows, initial_np, best_points)

    for step in range(1, args.steps + 1):
        optimizer.zero_grad(set_to_none=True)
        loss = loss_func(free_points, target)
        if not torch.isfinite(loss):
            raise FloatingPointError(f"Non-finite loss at step {step}: {loss.item()}")
        loss.backward()
        if free_points.grad is None or not torch.isfinite(free_points.grad).all():
            raise FloatingPointError(f"Non-finite or missing gradient at step {step}")
        optimizer.step()
        scheduler.step()

        if step % args.log_every == 0 or step == args.steps:
            with torch.no_grad():
                evaluated_loss = loss_func(free_points, target).item()
                points_np = free_points[0].detach().cpu().numpy()
            row = metric_row(
                step,
                evaluated_loss,
                points_np,
                gt_np,
                centroid,
                scale,
                optimizer.param_groups[0]["lr"],
            )
            rows.append(row)
            print_row(row)
            if row["cd_l1_mm"] < best_row["cd_l1_mm"]:
                best_row = row
                best_points = points_np.copy()
            save_progress(out_dir, rows, points_np, best_points)

    final_points = free_points[0].detach().cpu().numpy()
    np.save(out_dir / "final_free_points.npy", final_points)

    csv_path = out_dir / "progress.csv"
    save_progress(out_dir, rows, final_points, best_points)

    report = {
        "config": args.config,
        "ckpt": args.ckpt,
        "case_id": model_id,
        "seed": args.seed,
        "steps": args.steps,
        "initial_lr": args.lr,
        "min_lr_ratio": args.min_lr_ratio,
        "initialization": initialization,
        "squared_distance_epsilon": args.squared_distance_epsilon,
        "scale_mm_per_normalized_unit": scale,
        "initial": rows[0],
        "best": best_row,
        "final": rows[-1],
        "passed_cd_below_0_5mm": best_row["cd_l1_mm"] < 0.5,
    }
    json_path = out_dir / "summary.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("==== oracle summary ====")
    print(
        f"initial_CD={rows[0]['cd_l1_mm']:.6f}mm "
        f"best_CD={best_row['cd_l1_mm']:.6f}mm "
        f"final_CD={rows[-1]['cd_l1_mm']:.6f}mm"
    )
    print(f"passed_cd_below_0_5mm={report['passed_cd_below_0_5mm']}")
    print(f"[saved] {csv_path}")
    print(f"[saved] {json_path}")


if __name__ == "__main__":
    main()
