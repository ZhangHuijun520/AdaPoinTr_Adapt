#!/usr/bin/env python
"""Build immutable all-point GT-rim masks for one D2.2 training fold."""

import argparse
import hashlib
import io
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def npy_bytes(array):
    output = io.BytesIO()
    np.save(output, array, allow_pickle=False)
    return output.getvalue()


def write_immutable(output_dir, generated):
    if output_dir.exists():
        existing = {
            path.relative_to(output_dir).as_posix(): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        mismatches = sorted(
            name
            for name in set(existing).union(generated)
            if existing.get(name) != generated.get(name)
        )
        if mismatches:
            raise RuntimeError(
                "Refusing to overwrite non-identical GT-rim cache: "
                + ", ".join(mismatches[:10])
            )
        print(f"[locked] existing GT-rim cache is byte-identical: {output_dir}")
        return

    for name, payload in generated.items():
        path = output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"[saved] immutable GT-rim cache: {output_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--split", default="train", choices=("train",))
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--rim_band_mm", type=float, default=2.0)
    args = parser.parse_args()

    config = cfg_from_yaml_file(args.config)
    dataset_cfg = config.dataset.train
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    case_ids = [str(record["case_id"]) for record in dataset.records]
    if len(case_ids) != len(set(case_ids)):
        raise RuntimeError("D2.2 GT-rim cache input contains duplicate cases")

    generated = {}
    records = []
    counts = []
    maximum_conversion_delta_mm = 0.0
    for index, case_id in tqdm(
        enumerate(case_ids),
        total=len(case_ids),
        desc="Cache D2.2 GT-rim",
        dynamic_ncols=True,
    ):
        record = dataset.get_record(index)
        point_path = Path(record["point_path"])
        if not point_path.is_absolute():
            point_path = Path(dataset.data_root) / point_path
        with np.load(point_path, allow_pickle=False) as sample:
            partial = sample["partial"].astype(np.float64, copy=True)
            implant = sample["implant"].astype(np.float64, copy=True)

        normalization = dataset.get_case_normalization(case_id)
        centroid = normalization["centroid"]
        scale = normalization["scale"]
        normalized_distances_mm = cKDTree(implant).query(
            partial, k=1
        )[0] * scale
        world_partial = partial * scale + centroid
        world_implant = implant * scale + centroid
        world_distances_mm = cKDTree(world_implant).query(
            world_partial, k=1
        )[0]
        delta = float(
            np.max(np.abs(normalized_distances_mm - world_distances_mm))
        )
        maximum_conversion_delta_mm = max(maximum_conversion_delta_mm, delta)
        if delta > 1.0e-6:
            raise RuntimeError(
                f"{case_id}: normalized/world distance delta {delta} exceeds 1e-6 mm"
            )

        normalized_mask = normalized_distances_mm <= args.rim_band_mm
        evaluator_mask = world_distances_mm <= args.rim_band_mm
        if not np.array_equal(normalized_mask, evaluator_mask):
            raise RuntimeError(
                f"{case_id}: normalized proxy differs from evaluator reference rim"
            )
        mask = evaluator_mask.astype(np.bool_, copy=False)
        rim_points = int(mask.sum())
        if rim_points == 0:
            raise RuntimeError(f"{case_id}: GT-rim proxy is empty")

        name = f"masks/{case_id}.npy"
        payload = npy_bytes(mask)
        generated[name] = payload
        records.append({
            "case_id": case_id,
            "mask_path": name,
            "mask_sha256": sha256(payload),
            "normalization_scale": scale,
            "rim_band_mm": float(args.rim_band_mm),
            "rim_points": rim_points,
        })
        counts.append(rim_points)

    manifest = "".join(
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        for record in sorted(records, key=lambda item: item["case_id"])
    ).encode("utf-8")
    generated["gt_rim_manifest.jsonl"] = manifest

    counts_array = np.asarray(counts, dtype=np.float64)
    summary = {
        "protocol_version": "mamba-v12-d22-gt-rim-cache-v1",
        "config": args.config,
        "config_sha256": sha256(Path(args.config).read_bytes()),
        "cases": len(records),
        "empty_cases": 0,
        "rim_band_mm": float(args.rim_band_mm),
        "reference_rim_exact_index_equivalence": True,
        "maximum_normalized_world_delta_mm": maximum_conversion_delta_mm,
        "point_count": {
            "min": float(np.min(counts_array)),
            "p1": float(np.percentile(counts_array, 1)),
            "p5": float(np.percentile(counts_array, 5)),
            "median": float(np.median(counts_array)),
            "p95": float(np.percentile(counts_array, 95)),
            "max": float(np.max(counts_array)),
        },
        "protected_splits_accessed": False,
    }
    generated["validity_summary.json"] = (
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    hashes = "".join(
        f"{sha256(payload)}  {name}\n"
        for name, payload in sorted(generated.items())
    ).encode("utf-8")
    generated["files.sha256"] = hashes
    write_immutable(args.output_dir, generated)
    print(
        "[ok] reference-rim exact equivalence; "
        f"cases={len(records)} empty=0 max_delta_mm={maximum_conversion_delta_mm:.3g}"
    )


if __name__ == "__main__":
    main()
