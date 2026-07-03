#!/usr/bin/env python
"""Save visual samples for SkullFix implant prediction."""

import argparse
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils import misc  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.skullfix_metrics import normalized_point_surface_metrics  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--split", default="test", choices=("train", "val", "test"))
    parser.add_argument("--num_samples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260630)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--out_dir",
        default="experiments/visualizations/skullfix_implant_baseline",
    )
    return parser.parse_args()


def save_cloud_image(path, cloud):
    image = misc.get_ptcloud_img(cloud)
    Image.fromarray(image).save(path)


def load_full_sample(dataset, index):
    record = dataset.get_record(index)
    point_path = Path(record["point_path"])
    if not point_path.is_absolute():
        point_path = Path(dataset.data_root) / point_path
    with np.load(point_path, allow_pickle=False) as sample:
        arrays = {
            "partial": sample["partial"].astype(np.float32, copy=True),
            "gt": sample["gt"].astype(np.float32, copy=True),
            "implant": sample["implant"].astype(np.float32, copy=True),
        }
    return record, arrays


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    config = cfg_from_yaml_file(args.config)
    dataset_cfg = getattr(config.dataset, args.split)
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
            partial, _ = data
            prediction = model(partial.unsqueeze(0).to(device))[-1]
            pred_implant = prediction.squeeze(0).cpu().numpy()

            record, arrays = load_full_sample(dataset, data_index)
            final_reconstruction = np.concatenate(
                (arrays["partial"], pred_implant),
                axis=0,
            )
            sample_dir = output_root / f"{output_index:03d}_{model_id}"
            sample_dir.mkdir(parents=True, exist_ok=True)

            clouds = {
                "input_defective": arrays["partial"],
                "prediction_implant": pred_implant,
                "ground_truth_implant": arrays["implant"],
                "final_reconstruction": final_reconstruction,
                "ground_truth_complete": arrays["gt"],
            }
            for name, points in clouds.items():
                np.save(sample_dir / f"{name}.npy", points)
                save_cloud_image(sample_dir / f"{name}.png", points)

            norm = record["normalization"]
            implant_metrics = normalized_point_surface_metrics(
                pred_implant,
                arrays["implant"],
                norm["centroid"],
                norm["scale"],
                tolerances_mm=(0.5, 1.0, 2.0),
            )
            final_metrics = normalized_point_surface_metrics(
                final_reconstruction,
                arrays["gt"],
                norm["centroid"],
                norm["scale"],
                tolerances_mm=(0.5, 1.0, 2.0),
            )
            with open(sample_dir / "meta.json", "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "taxonomy_id": taxonomy_id,
                        "model_id": model_id,
                        "split": record["split"],
                        "input_key": dataset.input_key,
                        "target_key": dataset.target_key,
                        "normalization": norm,
                        "implant_metrics": implant_metrics.as_dict(),
                        "final_reconstruction_metrics": final_metrics.as_dict(),
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
