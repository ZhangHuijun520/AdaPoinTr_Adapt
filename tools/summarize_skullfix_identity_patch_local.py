#!/usr/bin/env python
"""Compare identity overfit with patch-local weights 0, 0.5, and 1."""

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

from tools.summarize_skullfix_identity_2x2 import evaluate_variant  # noqa: E402


VARIANTS = (
    {
        "group": "D",
        "query_selection": "fps_preserve",
        "denoise_weight": 0.0,
        "fine_coverage_weight": 1.0,
        "fine_local_weight": 0.0,
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
    {
        "group": "G",
        "query_selection": "fps_preserve",
        "denoise_weight": 0.0,
        "fine_coverage_weight": 1.0,
        "fine_local_weight": 0.5,
        "config": "cfgs/SkullFix_models/AdaPoinTr_identity_G_local05.yaml",
        "ckpt": (
            "experiments/AdaPoinTr_identity_G_local05/SkullFix_models/"
            "skullfix_identity_G_local05/ckpt-best.pth"
        ),
    },
    {
        "group": "H",
        "query_selection": "fps_preserve",
        "denoise_weight": 0.0,
        "fine_coverage_weight": 1.0,
        "fine_local_weight": 1.0,
        "config": "cfgs/SkullFix_models/AdaPoinTr_identity_H_local10.yaml",
        "ckpt": (
            "experiments/AdaPoinTr_identity_H_local10/SkullFix_models/"
            "skullfix_identity_H_local10/ckpt-best.pth"
        ),
    },
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260629)
    parser.add_argument(
        "--out_json",
        default=(
            "logs/skullfix/identity_patch_local/"
            "identity_patch_local_summary.json"
        ),
    )
    parser.add_argument(
        "--out_csv",
        default=(
            "logs/skullfix/identity_patch_local/"
            "identity_patch_local_summary.csv"
        ),
    )
    return parser.parse_args()


def make_row(result):
    coarse = result["coarse"]
    fine = result["fine"]
    return {
        "group": result["group"],
        "fine_local_weight": result["fine_local_weight"],
        "best_epoch": result["checkpoint"]["epoch"],
        "coarse_cd_l1_mm": coarse["cd_l1_mm"],
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
    rows = [make_row(result) for result in results]

    print("==== SkullFix identity patch-local comparison ====")
    print(
        "group local_w coarse_CD coarse_R->P fine_CD fine_HD95 "
        "fine_NSD@1 fine_P->R fine_R->P"
    )
    for row in rows:
        print(
            f"{row['group']:>5s} "
            f"{row['fine_local_weight']:>7.1f} "
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
