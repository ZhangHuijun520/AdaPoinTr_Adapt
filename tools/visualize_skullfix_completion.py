#!/usr/bin/env python

import argparse
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg
from tools import builder
from utils import misc
from utils.config import cfg_from_yaml_file


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--num_samples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260628)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--out_dir",
        default="experiments/visualizations/skullfix_adapointr_baseline",
    )
    return parser.parse_args()


def save_cloud_image(path, cloud):
    image = misc.get_ptcloud_img(cloud)
    Image.fromarray(image).save(path)


def load_implant(dataset, index):
    record = dataset.get_record(index)
    point_path = Path(record["point_path"])
    if not point_path.is_absolute():
        point_path = Path(dataset.data_root) / point_path
    with np.load(point_path, allow_pickle=False) as sample:
        implant = sample["implant"].astype(np.float32, copy=True)
    return record, implant


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

    output_root = Path(args.out_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    indices = list(range(len(dataset)))
    random.shuffle(indices)
    indices = indices[: min(args.num_samples, len(indices))]

    with torch.no_grad():
        for output_index, data_index in enumerate(indices):
            taxonomy_id, model_id, data = dataset[data_index]
            partial, gt = data
            partial_batch = partial.unsqueeze(0).to(device)
            prediction = model(partial_batch)[-1]

            record, implant = load_implant(dataset, data_index)
            arrays = {
                "input_defective": partial.numpy(),
                "prediction_complete": prediction.squeeze(0).cpu().numpy(),
                "ground_truth_complete": gt.numpy(),
                "ground_truth_implant": implant,
            }

            sample_dir = output_root / f"{output_index:03d}_{model_id}"
            sample_dir.mkdir(parents=True, exist_ok=True)
            for name, points in arrays.items():
                np.save(sample_dir / f"{name}.npy", points)
                save_cloud_image(sample_dir / f"{name}.png", points)

            with open(sample_dir / "meta.json", "w", encoding="utf-8") as handle:
                import json

                json.dump(
                    {
                        "taxonomy_id": taxonomy_id,
                        "model_id": model_id,
                        "split": record["split"],
                        "normalization": record["normalization"],
                        "quality": record["quality"],
                        "raw": record["raw"],
                    },
                    handle,
                    indent=2,
                    ensure_ascii=True,
                )
                handle.write("\n")
            print(f"[saved] {sample_dir}")


if __name__ == "__main__":
    main()
