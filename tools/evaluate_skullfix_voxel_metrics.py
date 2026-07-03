#!/usr/bin/env python
"""Evaluate exported SkullFix predictions against original NRRD masks."""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.evaluation_statistics import (  # noqa: E402
    describe_rows,
    paired_comparisons,
)
from utils.skullfix_metrics import normalized_to_world  # noqa: E402
from utils.skullfix_voxel_metrics import (  # noqa: E402
    mask_metric_dict,
    splat_world_points_to_mask,
    voxel_rim_metric_dict,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction_manifest", required=True)
    parser.add_argument("--raw_root", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--splat_radius_mm", type=float, default=1.0)
    parser.add_argument("--rim_band_mm", type=float, default=2.0)
    parser.add_argument("--tolerances_mm", default="0.5,1.0,2.0")
    parser.add_argument("--bootstrap_samples", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=20260702)
    return parser.parse_args()


def require_nrrd():
    try:
        import nrrd
    except ImportError as exc:
        raise ImportError("Install pynrrd before voxel evaluation") from exc
    return nrrd


def header_geometry(header):
    directions = np.asarray(
        header.get("space directions"), dtype=np.float64
    )
    origin = np.asarray(
        header.get("space origin", (0.0, 0.0, 0.0)),
        dtype=np.float64,
    )
    if directions.shape != (3, 3):
        raise ValueError("NRRD space directions must be 3x3")
    return directions, origin


def resolve_raw_path(raw_root, value):
    raw_root = Path(raw_root)
    path = Path(value)
    candidates = [path, raw_root / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Cannot resolve raw NRRD {value!r} below {raw_root}"
    )


def read_mask(path, threshold):
    nrrd = require_nrrd()
    volume, header = nrrd.read(str(path), index_order="F")
    return np.asarray(volume > threshold, dtype=bool), header


def prefixed(prefix, values):
    return {f"{prefix}_{key}": value for key, value in values.items()}


def main():
    args = parse_args()
    tolerances = tuple(
        float(value.strip())
        for value in args.tolerances_mm.split(",")
        if value.strip()
    )
    manifest_path = Path(args.prediction_manifest)
    prediction_root = manifest_path.parent
    records = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = []

    for record in records:
        prediction_path = prediction_root / record["prediction_path"]
        with np.load(prediction_path, allow_pickle=False) as payload:
            prediction_normalized = payload["prediction_implant"]
            centroid = payload["centroid"]
            scale = float(payload["scale"])
        prediction_world = normalized_to_world(
            prediction_normalized,
            centroid,
            scale,
        )

        masks = {}
        headers = {}
        for role in ("complete", "defective", "implant"):
            raw_path = resolve_raw_path(
                args.raw_root, record["raw"][role]
            )
            masks[role], headers[role] = read_mask(
                raw_path, args.threshold
            )

        directions, origin = header_geometry(headers["complete"])
        for role in ("defective", "implant"):
            role_directions, role_origin = header_geometry(headers[role])
            if masks[role].shape != masks["complete"].shape:
                raise ValueError(
                    f"{record['case_id']}: mismatched {role} shape"
                )
            if not np.allclose(role_directions, directions, atol=1e-5):
                raise ValueError(
                    f"{record['case_id']}: mismatched {role} directions"
                )
            if not np.allclose(role_origin, origin, atol=1e-4):
                raise ValueError(
                    f"{record['case_id']}: mismatched {role} origin"
                )

        prediction_mask = splat_world_points_to_mask(
            prediction_world,
            masks["complete"].shape,
            directions,
            origin,
            radius_mm=args.splat_radius_mm,
        )
        final_mask = masks["defective"] | prediction_mask

        row = {
            "case_id": record["case_id"],
            "split": record["split"],
        }
        row.update(
            prefixed(
                "implant",
                mask_metric_dict(
                    prediction_mask,
                    masks["implant"],
                    directions,
                    origin,
                    tolerances_mm=tolerances,
                ),
            )
        )
        row.update(
            prefixed(
                "final",
                mask_metric_dict(
                    final_mask,
                    masks["complete"],
                    directions,
                    origin,
                    tolerances_mm=tolerances,
                ),
            )
        )
        row.update(
            prefixed(
                "input",
                mask_metric_dict(
                    masks["defective"],
                    masks["complete"],
                    directions,
                    origin,
                    tolerances_mm=tolerances,
                ),
            )
        )
        row.update(
            prefixed(
                "rim",
                voxel_rim_metric_dict(
                    prediction_mask,
                    masks["implant"],
                    masks["defective"],
                    directions,
                    origin,
                    rim_band_mm=args.rim_band_mm,
                    tolerances_mm=tolerances,
                ),
            )
        )
        rows.append(row)
        print(f"[evaluated] {record['case_id']}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "skullfix_voxel_per_sample.csv"
    summary_path = out_dir / "skullfix_voxel_summary.json"

    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    metric_keys = [
        key for key in rows[0] if key not in {"case_id", "split"}
    ] if rows else []
    statistics = describe_rows(
        rows,
        metric_keys,
        bootstrap_samples=args.bootstrap_samples,
        confidence=args.confidence,
        seed=args.seed,
    )
    summary = {
        "protocol": {
            "prediction_representation": "fixed-radius surface splatting",
            "splat_radius_mm": args.splat_radius_mm,
            "rim_band_mm": args.rim_band_mm,
            "surface_dice_weighting": "surface-voxel count",
            "tolerances_mm": tolerances,
            "warning": (
                "DSC depends on point-to-voxel splatting and is not directly "
                "comparable to a native voxel-output model unless the same "
                "conversion is applied."
            ),
        },
        "num_samples": len(rows),
        "mean": {
            key: values.get("mean")
            for key, values in statistics.items()
        },
        "statistics": statistics,
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
    summary_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[saved] {csv_path}")
    print(f"[saved] {summary_path}")


if __name__ == "__main__":
    main()
