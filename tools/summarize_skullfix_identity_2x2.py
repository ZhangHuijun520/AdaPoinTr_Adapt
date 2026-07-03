#!/usr/bin/env python
"""Evaluate the four controlled SkullFix identity-overfit variants in mm."""

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
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.skullfix_metrics import normalized_point_surface_metrics  # noqa: E402


VARIANTS = (
    {
        "group": "A",
        "query_selection": "ranking",
        "denoise_weight": 0.5,
        "config": "cfgs/SkullFix_models/AdaPoinTr_identity_overfit_controlled.yaml",
        "ckpt": (
            "experiments/AdaPoinTr_identity_overfit_controlled/SkullFix_models/"
            "skullfix_adapointr_identity_overfit/ckpt-best.pth"
        ),
    },
    {
        "group": "B",
        "query_selection": "ranking",
        "denoise_weight": 0.0,
        "config": "cfgs/SkullFix_models/AdaPoinTr_identity_B_nodenoise.yaml",
        "ckpt": (
            "experiments/AdaPoinTr_identity_B_nodenoise/SkullFix_models/"
            "skullfix_identity_B_nodenoise/ckpt-best.pth"
        ),
    },
    {
        "group": "C",
        "query_selection": "fps_preserve",
        "denoise_weight": 0.5,
        "config": (
            "cfgs/SkullFix_models/"
            "AdaPoinTr_identity_C_fpspreserve_denoise.yaml"
        ),
        "ckpt": (
            "experiments/AdaPoinTr_identity_C_fpspreserve_denoise/"
            "SkullFix_models/skullfix_identity_C_fpspreserve_denoise/"
            "ckpt-best.pth"
        ),
    },
    {
        "group": "D",
        "query_selection": "fps_preserve",
        "denoise_weight": 0.0,
        "config": (
            "cfgs/SkullFix_models/"
            "AdaPoinTr_identity_D_fpspreserve_nodenoise.yaml"
        ),
        "ckpt": (
            "experiments/AdaPoinTr_identity_D_fpspreserve_nodenoise/"
            "SkullFix_models/skullfix_identity_D_fpspreserve_nodenoise/"
            "ckpt-best.pth"
        ),
    },
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260629)
    parser.add_argument(
        "--out_json",
        default="logs/skullfix/identity_2x2/identity_2x2_summary.json",
    )
    parser.add_argument(
        "--out_csv",
        default="logs/skullfix/identity_2x2/identity_2x2_summary.csv",
    )
    return parser.parse_args()


def load_case(config):
    dataset_cfg = config.dataset.test
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    if len(dataset) != 1:
        raise ValueError(f"Expected one identity test sample, got {len(dataset)}")

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


def checkpoint_metadata(path):
    checkpoint = torch.load(path, map_location="cpu")
    return {
        "epoch": int(checkpoint.get("epoch", -1)),
        "stored_metrics": checkpoint.get("metrics"),
        "stored_best_metrics": checkpoint.get("best_metrics"),
    }


def evaluate_variant(variant, device):
    config_path = Path(variant["config"])
    ckpt_path = Path(variant["ckpt"])
    if not config_path.is_file():
        raise FileNotFoundError(config_path)
    if not ckpt_path.is_file():
        raise FileNotFoundError(ckpt_path)

    config = cfg_from_yaml_file(str(config_path))
    model_id, model_input, gt, centroid, scale = load_case(config)
    model = builder.model_builder(config.model).to(device)
    builder.load_model(model, str(ckpt_path))
    model.eval()

    with torch.no_grad():
        output = model(model_input.unsqueeze(0).to(device))
    coarse = output[0][0].detach().cpu().numpy()
    prediction = output[-1][0].detach().cpu().numpy()
    gt_np = gt.numpy()

    fine_metrics = normalized_point_surface_metrics(
        prediction,
        gt_np,
        centroid,
        scale,
        tolerances_mm=(0.5, 1.0, 2.0),
    ).as_dict()
    coarse_metrics = normalized_point_surface_metrics(
        coarse,
        gt_np,
        centroid,
        scale,
        tolerances_mm=(0.5, 1.0, 2.0),
    ).as_dict()
    result = {
        **variant,
        "case_id": model_id,
        "scale_mm_per_normalized_unit": scale,
        "checkpoint": checkpoint_metadata(ckpt_path),
        "coarse": coarse_metrics,
        "fine": fine_metrics,
    }

    del model, output
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return result


def csv_row(result):
    coarse = result["coarse"]
    fine = result["fine"]
    return {
        "group": result["group"],
        "query_selection": result["query_selection"],
        "denoise_weight": result["denoise_weight"],
        "best_epoch": result["checkpoint"]["epoch"],
        "coarse_cd_l1_mm": coarse["cd_l1_mm"],
        "coarse_hd95_mm": coarse["hd95_mm"],
        "coarse_ref_to_pred_mm": coarse["ref_to_pred_mean_mm"],
        "fine_cd_l1_mm": fine["cd_l1_mm"],
        "fine_hd95_mm": fine["hd95_mm"],
        "fine_nsd_1mm": fine["nsd_at_1mm"],
        "fine_pred_to_ref_mm": fine["pred_to_ref_mean_mm"],
        "fine_ref_to_pred_mm": fine["ref_to_pred_mean_mm"],
    }


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    results = [evaluate_variant(variant, device) for variant in VARIANTS]
    rows = [csv_row(result) for result in results]

    print("==== SkullFix identity 2x2 comparison ====")
    print(
        "group query          denoise coarse_CD coarse_R->P "
        "fine_CD fine_HD95 fine_NSD@1 fine_P->R fine_R->P"
    )
    for row in rows:
        print(
            f"{row['group']:>5s} "
            f"{row['query_selection']:<14s} "
            f"{row['denoise_weight']:>7.1f} "
            f"{row['coarse_cd_l1_mm']:>9.4f} "
            f"{row['coarse_ref_to_pred_mm']:>11.4f} "
            f"{row['fine_cd_l1_mm']:>7.4f} "
            f"{row['fine_hd95_mm']:>9.4f} "
            f"{row['fine_nsd_1mm']:>10.4f} "
            f"{row['fine_pred_to_ref_mm']:>9.4f} "
            f"{row['fine_ref_to_pred_mm']:>9.4f}"
        )

    json_path = Path(args.out_json)
    csv_path = Path(args.out_csv)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps({"seed": args.seed, "variants": results}, indent=2) + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[saved] {json_path}")
    print(f"[saved] {csv_path}")


if __name__ == "__main__":
    main()
