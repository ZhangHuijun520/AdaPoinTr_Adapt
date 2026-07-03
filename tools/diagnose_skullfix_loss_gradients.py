#!/usr/bin/env python
"""Decompose AdaPoinTr losses, gradients, and output coverage on one SkullFix case."""

import argparse
import json
import random
import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np
import torch
from scipy.spatial import cKDTree

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets import build_dataset_from_cfg  # noqa: E402
from extensions.chamfer_dist import ChamferDistanceL1  # noqa: E402
from models.Transformer_utils import index_points, knn_point  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.skullfix_metrics import (  # noqa: E402
    normalized_point_surface_metrics,
    normalized_to_world,
)


GRADIENT_GROUPS = OrderedDict(
    [
        ("grouper", ("base_model.grouper.",)),
        ("encoder", ("base_model.encoder.",)),
        ("coarse_pred", ("base_model.coarse_pred.",)),
        ("query_ranking", ("base_model.query_ranking.",)),
        ("transformer_decoder", ("base_model.decoder.",)),
        ("outer_increase_dim", ("increase_dim.",)),
        ("reduce_map", ("reduce_map.",)),
        ("decode_head", ("decode_head.",)),
    ]
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run one train-mode forward pass on a fixed SkullFix sample, "
            "decompose AdaPoinTr losses, and report per-loss module gradients."
        )
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260629)
    parser.add_argument(
        "--out",
        default="logs/skullfix/identity_loss_gradient_diagnostic.json",
    )
    return parser.parse_args()


def load_case_metadata(dataset):
    record = dataset.get_record(0)
    point_path = Path(record["point_path"])
    if not point_path.is_absolute():
        point_path = Path(dataset.data_root) / point_path
    with np.load(point_path, allow_pickle=False) as sample:
        centroid = sample["centroid"].astype(np.float64)
        scale = float(sample["scale"])
    return record, centroid, scale


def metric_dict(points, reference, centroid, scale):
    return normalized_point_surface_metrics(
        points,
        reference,
        centroid,
        scale,
        tolerances_mm=(0.5, 1.0, 2.0),
    ).as_dict()


def geometry_summary(points, centroid, scale):
    world = normalized_to_world(points, centroid, scale)
    center = world.mean(axis=0)
    radii = np.linalg.norm(world - center, axis=1)
    nearest = cKDTree(world).query(world, k=2)[0][:, 1]
    return {
        "bbox_span_mm": np.ptp(world, axis=0).tolist(),
        "radius_p95_mm": float(np.percentile(radii, 95)),
        "internal_nn_mean_mm": float(nearest.mean()),
        "internal_nn_p05_mm": float(np.percentile(nearest, 5)),
        "near_duplicate_fraction_0_1mm": float(np.mean(nearest <= 0.1)),
    }


def patch_summary(pred_fine, pred_coarse, scale, factor):
    patches = pred_fine.reshape(pred_coarse.shape[0], factor, 3)
    distances = np.linalg.norm(patches - pred_coarse[:, None, :], axis=2) * scale
    patch_radius = distances.max(axis=1)
    return {
        "factor": int(factor),
        "point_to_parent_mean_mm": float(distances.mean()),
        "point_to_parent_p95_mm": float(np.percentile(distances, 95)),
        "patch_radius_mean_mm": float(patch_radius.mean()),
        "patch_radius_p95_mm": float(np.percentile(patch_radius, 95)),
        "patch_radius_max_mm": float(patch_radius.max()),
    }


def gradient_group(name):
    for group, prefixes in GRADIENT_GROUPS.items():
        if name.startswith(prefixes):
            return group
    return "other"


def gradient_summary(model):
    report = {}
    for group in list(GRADIENT_GROUPS) + ["other"]:
        report[group] = {
            "parameter_tensors": 0,
            "tensors_with_grad": 0,
            "gradient_elements": 0,
            "grad_l2_sq": 0.0,
            "grad_abs_sum": 0.0,
            "grad_max_abs": 0.0,
            "nonfinite_gradients": 0,
        }

    for name, parameter in model.named_parameters():
        group = gradient_group(name)
        values = report[group]
        values["parameter_tensors"] += 1
        if parameter.grad is None:
            continue
        gradient = parameter.grad.detach()
        values["tensors_with_grad"] += 1
        values["gradient_elements"] += gradient.numel()
        finite = torch.isfinite(gradient)
        values["nonfinite_gradients"] += int((~finite).sum().item())
        if not finite.all():
            gradient = torch.where(finite, gradient, torch.zeros_like(gradient))
        values["grad_l2_sq"] += float(torch.sum(gradient.double() ** 2).item())
        values["grad_abs_sum"] += float(torch.sum(torch.abs(gradient)).item())
        values["grad_max_abs"] = max(
            values["grad_max_abs"],
            float(torch.max(torch.abs(gradient)).item()),
        )

    for values in report.values():
        values["grad_l2"] = float(np.sqrt(values.pop("grad_l2_sq")))
        count = values["gradient_elements"]
        values["grad_abs_mean"] = (
            values.pop("grad_abs_sum") / count if count else 0.0
        )
    return report


def print_gradient_table(loss_name, report):
    print(f"---- gradients from {loss_name} ----")
    for group, values in report.items():
        print(
            f"{group:20s} "
            f"tensors={values['tensors_with_grad']:3d}/"
            f"{values['parameter_tensors']:3d} "
            f"L2={values['grad_l2']:.6e} "
            f"mean_abs={values['grad_abs_mean']:.6e} "
            f"max_abs={values['grad_max_abs']:.6e} "
            f"nonfinite={values['nonfinite_gradients']}"
        )


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
    _, centroid, scale = load_case_metadata(dataset)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    inputs = model_input.unsqueeze(0).repeat(args.batch_size, 1, 1).to(device)
    targets = gt.unsqueeze(0).repeat(args.batch_size, 1, 1).to(device)

    model = builder.model_builder(config.model)
    builder.load_model(model, args.ckpt)
    model.to(device)
    model.train()

    ret = model(inputs)
    pred_coarse, denoised_coarse, denoised_fine, pred_fine = ret
    loss_func = ChamferDistanceL1()

    neighbor_index = knn_point(model.factor, targets, denoised_coarse)
    denoised_target = index_points(targets, neighbor_index).reshape(
        targets.size(0), -1, 3
    )
    loss_denoise = model.denoise_weight * loss_func(
        denoised_fine,
        denoised_target,
    )
    loss_coarse = loss_func(pred_coarse, targets)
    loss_fine_global, loss_fine_local, loss_fine = (
        model.get_fine_loss_components(
            pred_coarse,
            pred_fine,
            targets,
        )
    )
    loss_reconstruction = loss_coarse + loss_fine
    loss_total = loss_denoise + loss_reconstruction

    official_sparse, official_dense = model.get_loss(ret, targets, 0)
    if not torch.allclose(loss_denoise, official_sparse, atol=1e-7, rtol=1e-6):
        raise AssertionError("Recomputed denoise loss does not match model.get_loss")
    if not torch.allclose(
        loss_reconstruction, official_dense, atol=1e-7, rtol=1e-6
    ):
        raise AssertionError("Recomputed reconstruction loss does not match model.get_loss")

    losses = OrderedDict(
        [
            ("denoise", loss_denoise),
            ("coarse", loss_coarse),
            ("fine_global", loss_fine_global),
            ("fine_local", loss_fine_local),
            ("fine", loss_fine),
            ("reconstruction", loss_reconstruction),
            ("total", loss_total),
        ]
    )
    print("==== loss decomposition ====")
    for name, loss in losses.items():
        print(f"{name:16s} raw={loss.item():.9f} x1000={loss.item() * 1000:.6f}")

    gt_np = targets[0].detach().cpu().numpy()
    coarse_np = pred_coarse[0].detach().cpu().numpy()
    fine_np = pred_fine[0].detach().cpu().numpy()
    denoised_target_np = denoised_target[0].detach().cpu().numpy()
    denoised_fine_np = denoised_fine[0].detach().cpu().numpy()

    report = {
        "config": args.config,
        "ckpt": args.ckpt,
        "case_id": str(model_id),
        "dataset_input_key": dataset.input_key,
        "batch_size": args.batch_size,
        "scale_mm_per_normalized_unit": scale,
        "losses": {
            name: {"raw": float(loss.item()), "x1000": float(loss.item() * 1000)}
            for name, loss in losses.items()
        },
        "coverage": {
            "coarse_vs_gt": metric_dict(coarse_np, gt_np, centroid, scale),
            "fine_vs_gt": metric_dict(fine_np, gt_np, centroid, scale),
            "denoised_fine_vs_target": metric_dict(
                denoised_fine_np,
                denoised_target_np,
                centroid,
                scale,
            ),
        },
        "geometry": {
            "gt": geometry_summary(gt_np, centroid, scale),
            "coarse": geometry_summary(coarse_np, centroid, scale),
            "fine": geometry_summary(fine_np, centroid, scale),
            "fine_patches": patch_summary(
                fine_np,
                coarse_np,
                scale,
                model.factor,
            ),
        },
        "gradients": {},
    }

    backward_losses = OrderedDict(
        [
            ("denoise", loss_denoise),
            ("coarse", loss_coarse),
            ("fine", loss_fine),
            ("total", loss_total),
        ]
    )
    for index, (name, loss) in enumerate(backward_losses.items()):
        model.zero_grad(set_to_none=True)
        loss.backward(retain_graph=index < len(backward_losses) - 1)
        gradients = gradient_summary(model)
        report["gradients"][name] = gradients
        print_gradient_table(name, gradients)

    print("==== coverage summary ====")
    for name, metrics in report["coverage"].items():
        print(
            f"{name:28s} "
            f"CD={metrics['cd_l1_mm']:.6f} mm "
            f"HD95={metrics['hd95_mm']:.6f} mm "
            f"NSD@1mm={metrics['nsd_at_1mm']:.6f} "
            f"P->R={metrics['pred_to_ref_mean_mm']:.6f} mm "
            f"R->P={metrics['ref_to_pred_mean_mm']:.6f} mm"
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[saved] {out_path}")
    print("[ok] loss and gradient diagnostic completed without an optimizer step")


if __name__ == "__main__":
    main()
