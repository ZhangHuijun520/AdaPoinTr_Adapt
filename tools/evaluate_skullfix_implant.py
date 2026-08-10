#!/usr/bin/env python
"""Evaluate cranial implant prediction in millimeters."""

import argparse
import csv
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.evaluation_statistics import (  # noqa: E402
    aggregate_rows_by_group,
    describe_rows,
    describe_rows_by_group,
    paired_comparisons,
)
from utils.skullfix_metrics import (  # noqa: E402
    normalized_point_rim_metrics,
    normalized_point_surface_metrics,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--split", default="test", choices=("train", "val", "test"))
    parser.add_argument("--num_samples", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260630)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--out_dir", default="logs/skullfix_implant_eval")
    parser.add_argument("--rim_band_mm", type=float, default=2.0)
    parser.add_argument("--bootstrap_samples", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--dataset_label", default="SkullFix")
    parser.add_argument(
        "--include_coarse_rim_metrics",
        action="store_true",
        help="Add observation-only GT-rim-to-coarse metrics for D2.2.",
    )
    parser.add_argument(
        "--save_predictions_dir",
        default="",
        help="Optional directory for per-case prediction NPZ files.",
    )
    parser.add_argument(
        "--tolerances_mm",
        default="0.5,1.0,2.0",
        help="Comma-separated NSD tolerances in millimeters.",
    )
    return parser.parse_args()


def metric_dict(prefix, metrics):
    return {f"{prefix}_{key}": value for key, value in metrics.as_dict().items()}


def mean_dict(rows, keys):
    return {
        key: float(np.nanmean([row[key] for row in rows]))
        for key in keys
        if rows and key in rows[0]
    }


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

    tolerances = tuple(
        float(value.strip())
        for value in args.tolerances_mm.split(",")
        if value.strip()
    )
    if not tolerances:
        raise ValueError("At least one NSD tolerance is required")

    config = cfg_from_yaml_file(args.config)
    dataset_cfg = getattr(config.dataset, args.split)
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = builder.model_builder(config.model)
    builder.load_model(model, args.ckpt)
    model.to(device)
    model.eval()

    indices = list(range(len(dataset)))
    random.shuffle(indices)
    if args.num_samples > 0:
        indices = indices[: min(args.num_samples, len(indices))]

    rows = []
    prediction_records = []
    prediction_dir = (
        Path(args.save_predictions_dir)
        if args.save_predictions_dir
        else None
    )
    if prediction_dir is not None:
        prediction_dir.mkdir(parents=True, exist_ok=True)

    with torch.no_grad():
        for index in tqdm(indices, desc=f"Evaluate {args.split}", dynamic_ncols=True):
            taxonomy_id, case_id, data = dataset[index]
            partial, target = data
            model_output = model(partial.unsqueeze(0).to(device))
            pred_coarse = model_output[0].squeeze(0).cpu().numpy()
            pred_implant = model_output[-1].squeeze(0).cpu().numpy()

            record, arrays = load_full_sample(dataset, index)
            norm = record["normalization"]
            centroid = norm["centroid"]
            scale = norm["scale"]

            implant_metrics = normalized_point_surface_metrics(
                pred_implant,
                arrays["implant"],
                centroid,
                scale,
                tolerances_mm=tolerances,
            )
            final_reconstruction = np.concatenate(
                (arrays["partial"], pred_implant),
                axis=0,
            )
            final_metrics = normalized_point_surface_metrics(
                final_reconstruction,
                arrays["gt"],
                centroid,
                scale,
                tolerances_mm=tolerances,
            )
            input_metrics = normalized_point_surface_metrics(
                arrays["partial"],
                arrays["gt"],
                centroid,
                scale,
                tolerances_mm=tolerances,
            )
            rim_metrics = normalized_point_rim_metrics(
                pred_implant,
                arrays["implant"],
                arrays["partial"],
                centroid,
                scale,
                rim_band_mm=args.rim_band_mm,
                tolerances_mm=tolerances,
            )

            row = {
                "taxonomy_id": taxonomy_id,
                "case_id": case_id,
                "split": record["split"],
                "skull_id": record.get("skull_id", case_id),
                "defect_type": record.get("defect_type", ""),
            }
            row.update(metric_dict("implant", implant_metrics))
            row.update(metric_dict("final", final_metrics))
            row.update(metric_dict("input", input_metrics))
            row.update(metric_dict("rim", rim_metrics))
            if args.include_coarse_rim_metrics:
                coarse_rim_metrics = normalized_point_rim_metrics(
                    pred_coarse,
                    arrays["implant"],
                    arrays["partial"],
                    centroid,
                    scale,
                    rim_band_mm=args.rim_band_mm,
                    tolerances_mm=tolerances,
                )
                row.update({
                    "coarse_reference_rim_points": (
                        coarse_rim_metrics.reference_rim_points
                    ),
                    "coarse_gt_rim_to_pred_mean_mm": (
                        coarse_rim_metrics.gt_rim_to_pred_mean_mm
                    ),
                    "coarse_gt_rim_to_pred_p95_mm": (
                        coarse_rim_metrics.gt_rim_to_pred_p95_mm
                    ),
                })
            rows.append(row)

            if prediction_dir is not None:
                prediction_path = prediction_dir / f"{case_id}.npz"
                np.savez_compressed(
                    prediction_path,
                    prediction_implant=pred_implant.astype(np.float32),
                    centroid=np.asarray(centroid, dtype=np.float64),
                    scale=np.asarray(scale, dtype=np.float64),
                )
                prediction_records.append(
                    {
                        "case_id": str(case_id),
                        "split": record["split"],
                        "skull_id": record.get("skull_id", str(case_id)),
                        "source_skull_id": record.get(
                            "source_skull_id", str(case_id)
                        ),
                        "defect_type": record.get("defect_type", ""),
                        "official_split": record.get("official_split"),
                        "gate_split": record.get("gate_split"),
                        "prediction_path": prediction_path.name,
                        "raw": record.get("raw", {}),
                        "voxel_shape": record.get("voxel_shape"),
                        "space_directions": record.get("space_directions"),
                        "space_origin": record.get("space_origin"),
                    }
                )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{Path(args.config).stem}_{args.split}"
    csv_path = out_dir / f"{stem}_per_sample.csv"
    json_path = out_dir / f"{stem}_summary.json"

    if rows:
        fieldnames = list(rows[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    identifier_keys = {
        "taxonomy_id",
        "case_id",
        "split",
        "skull_id",
        "defect_type",
    }
    metric_keys = [
        key for key in rows[0].keys() if key not in identifier_keys
    ] if rows else []
    skull_rows = aggregate_rows_by_group(rows, "skull_id", metric_keys)
    summary = {
        "dataset": args.dataset_label,
        "config": args.config,
        "ckpt": args.ckpt,
        "split": args.split,
        "num_samples": len(rows),
        "tolerances_mm": tolerances,
        "rim_band_mm": args.rim_band_mm,
        "include_coarse_rim_metrics": args.include_coarse_rim_metrics,
        "mean": mean_dict(rows, metric_keys),
        "statistics": describe_rows(
            rows,
            metric_keys,
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed,
        ),
        "statistics_case_level": describe_rows(
            rows,
            metric_keys,
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed,
        ),
        "statistics_skull_macro": describe_rows(
            skull_rows,
            metric_keys,
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed + 20000,
        ),
        "num_skulls": len(skull_rows),
        "by_defect_type": describe_rows_by_group(
            rows,
            "defect_type",
            metric_keys,
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed + 30000,
        ),
        "paired_final_vs_input": paired_comparisons(
            rows,
            candidate_prefix="final",
            baseline_prefix="input",
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed + 10000,
        ),
        "per_sample_csv": str(csv_path),
    }
    if prediction_dir is not None:
        prediction_manifest = prediction_dir / "predictions_manifest.jsonl"
        with open(
            prediction_manifest, "w", encoding="utf-8", newline="\n"
        ) as handle:
            for record in prediction_records:
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")
        summary["predictions_manifest"] = str(prediction_manifest)
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=True)
        handle.write("\n")

    mean = summary["mean"]
    print(f"==== {args.dataset_label} implant evaluation ====")
    print(f"config: {args.config}")
    print(f"ckpt: {args.ckpt}")
    print(f"split: {args.split} samples={len(rows)}")
    if skull_rows:
        print(f"skulls: {len(skull_rows)}")
    print(
        "implant: "
        f"CD={mean.get('implant_cd_l1_mm', float('nan')):.4f}mm "
        f"HD95={mean.get('implant_hd95_mm', float('nan')):.4f}mm "
        f"NSD@1={mean.get('implant_nsd_at_1mm', float('nan')):.4f}"
    )
    print(
        "final reconstruction: "
        f"CD={mean.get('final_cd_l1_mm', float('nan')):.4f}mm "
        f"HD95={mean.get('final_hd95_mm', float('nan')):.4f}mm "
        f"NSD@1={mean.get('final_nsd_at_1mm', float('nan')):.4f}"
    )
    print(
        "input defective baseline: "
        f"CD={mean.get('input_cd_l1_mm', float('nan')):.4f}mm "
        f"HD95={mean.get('input_hd95_mm', float('nan')):.4f}mm "
        f"NSD@1={mean.get('input_nsd_at_1mm', float('nan')):.4f}"
    )
    print(
        "rim contact: "
        f"CD={mean.get('rim_contact_cd_l1_mm', float('nan')):.4f}mm "
        f"HD95={mean.get('rim_contact_hd95_mm', float('nan')):.4f}mm "
        f"NSD@1={mean.get('rim_contact_nsd_at_1mm', float('nan')):.4f} "
        f"GT-rim->pred p95="
        f"{mean.get('rim_gt_rim_to_pred_p95_mm', float('nan')):.4f}mm"
    )
    print(f"[saved] {csv_path}")
    print(f"[saved] {json_path}")
    if prediction_dir is not None:
        print(f"[saved] {summary['predictions_manifest']}")


if __name__ == "__main__":
    main()
