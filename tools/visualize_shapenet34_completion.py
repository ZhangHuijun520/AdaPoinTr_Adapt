import argparse
import os
import random
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg
from tools import builder
from utils import misc
from utils.config import cfg_from_yaml_file


CROP_RATIO = {
    "easy": 1 / 4,
    "median": 1 / 2,
    "hard": 3 / 4,
}

FIXED_POINTS = [
    torch.Tensor([1, 1, 1]),
    torch.Tensor([1, 1, -1]),
    torch.Tensor([1, -1, 1]),
    torch.Tensor([-1, 1, 1]),
    torch.Tensor([-1, -1, 1]),
    torch.Tensor([-1, 1, -1]),
    torch.Tensor([1, -1, -1]),
    torch.Tensor([-1, -1, -1]),
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--split", choices=["seen", "unseen"], default="seen")
    parser.add_argument("--mode", choices=["easy", "median", "hard"], default="hard")
    parser.add_argument("--num_samples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--out_dir", default="")
    return parser.parse_args()


def save_cloud_image(path, cloud):
    img = misc.get_ptcloud_img(cloud)
    cv2.imwrite(str(path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    config = cfg_from_yaml_file(args.config)
    dataset_cfg = config.dataset.test
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = builder.model_builder(config.model)
    builder.load_model(model, args.ckpt)
    model.to(device)
    model.eval()

    out_dir = args.out_dir
    if out_dir == "":
        out_dir = os.path.join(
            "experiments",
            "visualizations",
            "shapenet34_adapointr_1gpu_full",
            f"{args.split}_{args.mode}",
        )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    indices = list(range(len(dataset)))
    random.shuffle(indices)
    indices = indices[: args.num_samples]
    npoints = config.dataset.test._base_.N_POINTS
    num_crop = int(npoints * CROP_RATIO[args.mode])

    with torch.no_grad():
        for out_idx, data_idx in enumerate(indices):
            taxonomy_id, model_id, gt = dataset[data_idx]
            gt = gt.unsqueeze(0).to(device)
            fixed_point = FIXED_POINTS[out_idx % len(FIXED_POINTS)]

            partial, crop = misc.seprate_point_cloud(
                gt, npoints, num_crop, fixed_points=fixed_point
            )
            partial = misc.fps(partial, 2048)
            ret = model(partial)
            pred = ret[-1]

            sample_dir = out_dir / f"{out_idx:03d}_{taxonomy_id}_{model_id}"
            sample_dir.mkdir(parents=True, exist_ok=True)

            partial_np = partial.squeeze(0).detach().cpu().numpy()
            crop_np = crop.squeeze(0).detach().cpu().numpy()
            pred_np = pred.squeeze(0).detach().cpu().numpy()
            gt_np = gt.squeeze(0).detach().cpu().numpy()

            np.save(sample_dir / "input_partial.npy", partial_np)
            np.save(sample_dir / "missing_crop.npy", crop_np)
            np.save(sample_dir / "pred.npy", pred_np)
            np.save(sample_dir / "gt.npy", gt_np)

            save_cloud_image(sample_dir / "input_partial.png", partial_np)
            save_cloud_image(sample_dir / "pred.png", pred_np)
            save_cloud_image(sample_dir / "gt.png", gt_np)

            with open(sample_dir / "meta.txt", "w", encoding="utf-8") as f:
                f.write(f"split: {args.split}\n")
                f.write(f"mode: {args.mode}\n")
                f.write(f"taxonomy_id: {taxonomy_id}\n")
                f.write(f"model_id: {model_id}\n")
                f.write(f"num_crop: {num_crop}\n")

            print(f"[saved] {sample_dir}")


if __name__ == "__main__":
    main()
