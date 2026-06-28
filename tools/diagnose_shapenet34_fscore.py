import argparse
import sys
from collections import defaultdict
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datasets import build_dataset_from_cfg
from tools import builder
from utils import misc
from utils.config import cfg_from_yaml_file
from extensions.chamfer_dist import ChamferDistanceL2


CROP_RATIO = {
    "easy": 1 / 4,
    "median": 1 / 2,
    "hard": 3 / 4,
}

FIXED_VIEWPOINTS = [
    torch.Tensor([1, 1, 1]),
    torch.Tensor([1, 1, -1]),
    torch.Tensor([1, -1, 1]),
    torch.Tensor([-1, 1, 1]),
    torch.Tensor([-1, -1, 1]),
    torch.Tensor([-1, 1, -1]),
    torch.Tensor([1, -1, -1]),
    torch.Tensor([-1, -1, -1]),
]


def parse_thresholds(value):
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def fscore_torch(pred, gt, thresholds):
    dist = torch.cdist(pred, gt)
    pred_to_gt = dist.min(dim=2)[0]
    gt_to_pred = dist.min(dim=1)[0]

    values = []
    for th in thresholds:
        recall = (gt_to_pred < th).float().mean(dim=1)
        precision = (pred_to_gt < th).float().mean(dim=1)
        denom = recall + precision
        score = torch.where(
            denom > 0,
            2 * recall * precision / denom,
            torch.zeros_like(denom),
        )
        values.append(score.mean().item())
    return values


def mean(values):
    return sum(values) / len(values) if values else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--mode", choices=["easy", "median", "hard"], required=True)
    parser.add_argument("--max_samples", type=int, default=100)
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument(
        "--thresholds",
        default="0.008,0.009,0.010,0.011,0.012,0.013,0.014,0.015",
        help="Comma-separated F-Score distance thresholds.",
    )
    args = parser.parse_args()

    thresholds = parse_thresholds(args.thresholds)
    cfg = cfg_from_yaml_file(args.config)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = build_dataset_from_cfg(cfg.dataset.test._base_, cfg.dataset.test.others)
    loader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        drop_last=False,
        num_workers=args.num_workers,
    )

    model = builder.model_builder(cfg.model)
    builder.load_model(model, args.ckpt)
    model.to(device)
    model.eval()

    chamfer_l2 = ChamferDistanceL2(ignore_zeros=True).to(device)
    npoints = cfg.dataset.test._base_.N_POINTS
    num_crop = int(npoints * CROP_RATIO[args.mode])

    sample_scores = [[] for _ in thresholds]
    category_scores = defaultdict(lambda: [[] for _ in thresholds])
    cd_l2_values = []

    with torch.no_grad():
        iterator = tqdm(loader, total=min(len(loader), args.max_samples), dynamic_ncols=True)
        for idx, (taxonomy_ids, model_ids, data) in enumerate(iterator):
            if idx >= args.max_samples:
                break

            taxonomy_id = taxonomy_ids[0] if isinstance(taxonomy_ids[0], str) else taxonomy_ids[0].item()
            gt = data.to(device)

            for viewpoint in FIXED_VIEWPOINTS:
                partial, _ = misc.seprate_point_cloud(
                    gt,
                    npoints,
                    num_crop,
                    fixed_points=viewpoint,
                )
                partial = misc.fps(partial, 2048)
                ret = model(partial)
                dense = ret[-1]

                scores = fscore_torch(dense, gt, thresholds)
                cd_l2 = chamfer_l2(dense, gt).item() * 1000
                cd_l2_values.append(cd_l2)

                for th_idx, score in enumerate(scores):
                    sample_scores[th_idx].append(score)
                    category_scores[taxonomy_id][th_idx].append(score)

    category_mean_scores = []
    for th_idx in range(len(thresholds)):
        per_category = [
            mean(scores_by_threshold[th_idx])
            for scores_by_threshold in category_scores.values()
            if scores_by_threshold[th_idx]
        ]
        category_mean_scores.append(mean(per_category))

    print("==== ShapeNet F-Score diagnostic ====")
    print(f"config: {args.config}")
    print(f"ckpt: {args.ckpt}")
    print(f"mode: {args.mode}")
    print(f"models_used: {min(args.max_samples, len(dataset))}")
    print(f"views_per_model: {len(FIXED_VIEWPOINTS)}")
    print(f"mean_cd_l2_x1000: {mean(cd_l2_values):.4f}")
    print("")
    print("threshold,sample_weighted_fscore,category_weighted_fscore")
    for th, sample_values, category_value in zip(thresholds, sample_scores, category_mean_scores):
        print(f"{th:.4f},{mean(sample_values):.6f},{category_value:.6f}")


if __name__ == "__main__":
    main()
