#!/usr/bin/env python
"""Estimate implant representation limits from GT point sampling density."""

import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.evaluation_statistics import describe_rows  # noqa: E402
from utils.skullfix_metrics import point_surface_metrics  # noqa: E402
from utils.skullfix_voxel_metrics import (  # noqa: E402
    mask_metric_dict,
    splat_world_points_to_mask,
)

_PREPARE_PATH = REPO_ROOT / "tools" / "prepare_skullfix_pointcloud.py"
_SPEC = importlib.util.spec_from_file_location(
    "prepare_skullfix_pointcloud_module", _PREPARE_PATH
)
_PREPARE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_PREPARE)

flat_indices_to_world = _PREPARE.flat_indices_to_world
header_geometry = _PREPARE.header_geometry
read_binary_volume = _PREPARE.read_binary_volume
stable_rng = _PREPARE.stable_rng
surface_flat_indices = _PREPARE.surface_flat_indices


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Sample GT implant surfaces at several point counts and compare "
            "them with the original implant surface/mask. This estimates the "
            "best possible representation quality for a point-only implant."
        )
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--data_root", default="")
    parser.add_argument("--raw_root", required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--counts", default="1024,2048,4096,8192,16384")
    parser.add_argument("--max_samples", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260708)
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--splat_radius_mm", type=float, default=1.0)
    parser.add_argument("--tolerances_mm", default="0.5,1.0,2.0")
    parser.add_argument("--bootstrap_samples", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument(
        "--out_dir",
        default="logs/skullfix_implant_point_count/gt_sampling_upper_bound",
    )
    return parser.parse_args()


def resolve_path(root, value):
    path = Path(value)
    candidates = [path]
    if root:
        candidates.append(Path(root) / path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Cannot resolve {value!r} below {root!r}")


def load_manifest(path, split):
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("split") == split:
                records.append(record)
    records.sort(key=lambda item: str(item["case_id"]))
    return records


def sample_world_points(surface_indices, shape, directions, origin, count, rng):
    chosen = rng.choice(
        surface_indices,
        size=int(count),
        replace=surface_indices.size < int(count),
    )
    return flat_indices_to_world(chosen, shape, directions, origin)


def prefixed(prefix, values):
    return {f"{prefix}_{key}": value for key, value in values.items()}


def main():
    args = parse_args()
    counts = [int(value.strip()) for value in args.counts.split(",") if value.strip()]
    if not counts or min(counts) <= 0:
        raise ValueError("--counts must contain positive integers")
    tolerances = tuple(
        float(value.strip())
        for value in args.tolerances_mm.split(",")
        if value.strip()
    )

    manifest = Path(args.manifest)
    data_root = args.data_root or str(manifest.parent)
    records = load_manifest(manifest, args.split)
    if args.max_samples > 0:
        records = records[: min(args.max_samples, len(records))]
    if not records:
        raise ValueError(f"No records found for split {args.split!r}")

    rows = []
    for record in records:
        implant_path = resolve_path(args.raw_root, record["raw"]["implant"])
        implant_mask, implant_header = read_binary_volume(
            implant_path, args.threshold
        )
        directions, origin = header_geometry(implant_header)
        surface_indices = surface_flat_indices(implant_mask)
        reference_world = flat_indices_to_world(
            surface_indices, implant_mask.shape, directions, origin
        )

        for count in counts:
            sampled_world = sample_world_points(
                surface_indices,
                implant_mask.shape,
                directions,
                origin,
                count,
                stable_rng(args.seed, str(record["case_id"]), f"implant_gt_{count}"),
            )
            point_metrics = point_surface_metrics(
                sampled_world, reference_world, tolerances_mm=tolerances
            )
            sampled_mask = splat_world_points_to_mask(
                sampled_world,
                implant_mask.shape,
                directions,
                origin,
                radius_mm=args.splat_radius_mm,
            )
            voxel_metrics = mask_metric_dict(
                sampled_mask,
                implant_mask,
                directions,
                origin,
                tolerances_mm=tolerances,
            )
            row = {
                "case_id": record["case_id"],
                "split": record["split"],
                "sample_count": count,
                "surface_reference_points": int(surface_indices.size),
                "splat_radius_mm": float(args.splat_radius_mm),
            }
            row.update(prefixed("point", point_metrics.as_dict()))
            row.update(prefixed("voxel", voxel_metrics))
            rows.append(row)
        print(f"[evaluated] {record['case_id']}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"skullfix_gt_sampling_{args.split}.csv"
    summary_path = out_dir / f"skullfix_gt_sampling_{args.split}_summary.json"
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    metric_keys = [
        key
        for key in rows[0]
        if key
        not in {
            "case_id",
            "split",
            "sample_count",
            "surface_reference_points",
            "splat_radius_mm",
        }
    ]
    summary = {
        "dataset": "SkullFix",
        "manifest": str(manifest),
        "data_root": data_root,
        "raw_root": args.raw_root,
        "split": args.split,
        "num_cases": len(records),
        "counts": counts,
        "splat_radius_mm": args.splat_radius_mm,
        "statistics_by_count": {},
        "per_sample_csv": str(csv_path),
    }
    for count in counts:
        count_rows = [row for row in rows if row["sample_count"] == count]
        summary["statistics_by_count"][str(count)] = describe_rows(
            count_rows,
            metric_keys,
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed + count,
        )

    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=True)
        handle.write("\n")

    print("==== SkullFix GT implant sampling upper bound ====")
    for count in counts:
        stats = summary["statistics_by_count"][str(count)]
        print(
            f"{count:5d} points | "
            f"point CD={stats['point_cd_l1_mm']['mean']:.4f}mm "
            f"point HD95={stats['point_hd95_mm']['mean']:.4f}mm "
            f"voxel DSC={stats['voxel_dsc']['mean']:.4f} "
            f"voxel SurfaceDice@1="
            f"{stats['voxel_surface_dice_at_1mm']['mean']:.4f} "
            f"RVE={stats['voxel_rve']['mean']:.4f}"
        )
    print(f"[saved] {csv_path}")
    print(f"[saved] {summary_path}")


if __name__ == "__main__":
    main()
