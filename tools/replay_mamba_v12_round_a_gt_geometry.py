#!/usr/bin/env python
"""GT-aware observation-only replay for blocked Mamba v1.2 Round A."""

import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from scipy.spatial import cKDTree
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.skullfix_metrics import (  # noqa: E402
    normalized_point_rim_metrics,
    normalized_point_surface_metrics,
    normalized_to_world,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--case_labels", type=Path, required=True)
    parser.add_argument("--gate_audit", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--rim_band_mm", type=float, default=2.0)
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path, expected=None):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256_file(path)
    if expected is not None and actual != expected:
        raise RuntimeError(f"SHA256 mismatch: {path}")
    return actual


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        raise RuntimeError(f"No rows for {path}")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_full_sample(dataset, index):
    record = dataset.get_record(index)
    point_path = Path(record["point_path"])
    if not point_path.is_absolute():
        point_path = Path(dataset.data_root) / point_path
    with np.load(point_path, allow_pickle=False) as sample:
        arrays = {
            "partial": sample["partial"].astype(np.float32, copy=True),
            "implant": sample["implant"].astype(np.float32, copy=True),
        }
    return record, arrays


def principal_scales(points):
    centered = points - points.mean(axis=0, keepdims=True)
    covariance = centered.T @ centered / max(1, points.shape[0] - 1)
    eigenvalues = np.linalg.eigvalsh(covariance)
    return np.sqrt(np.maximum(eigenvalues[::-1], 0.0))


def finite_ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 1e-12 else float("nan")


def stage_geometry(stage, reference, partial, centroid, scale, rim_band_mm):
    stage_world = normalized_to_world(stage, centroid, scale)
    reference_world = normalized_to_world(reference, centroid, scale)
    stage_center = stage_world.mean(axis=0)
    reference_center = reference_world.mean(axis=0)
    stage_radius = np.linalg.norm(stage_world - stage_center, axis=1)
    reference_radius = np.linalg.norm(reference_world - reference_center, axis=1)
    stage_axes = principal_scales(stage_world)
    reference_axes = principal_scales(reference_world)

    stage_to_reference = cKDTree(reference_world).query(stage_world, k=1)[0]
    reference_to_stage = cKDTree(stage_world).query(reference_world, k=1)[0]
    surface = normalized_point_surface_metrics(
        stage, reference, centroid, scale, tolerances_mm=(1.0, 2.0, 5.0)
    )
    rim = normalized_point_rim_metrics(
        stage,
        reference,
        partial,
        centroid,
        scale,
        rim_band_mm=rim_band_mm,
        tolerances_mm=(1.0, 2.0, 5.0),
    )
    output = {
        "point_count": int(stage.shape[0]),
        "surface_cd_l1_mm": surface.cd_l1_mm,
        "surface_hd95_mm": surface.hd95_mm,
        "stage_to_gt_mean_mm": float(stage_to_reference.mean()),
        "stage_to_gt_p95_mm": float(np.percentile(stage_to_reference, 95)),
        "gt_to_stage_mean_mm": float(reference_to_stage.mean()),
        "gt_to_stage_p95_mm": float(np.percentile(reference_to_stage, 95)),
        "centroid_offset_mm": float(np.linalg.norm(stage_center - reference_center)),
        "radial_rms_ratio": finite_ratio(
            float(np.sqrt(np.mean(stage_radius ** 2))),
            float(np.sqrt(np.mean(reference_radius ** 2))),
        ),
        "radial_p95_ratio": finite_ratio(
            float(np.percentile(stage_radius, 95)),
            float(np.percentile(reference_radius, 95)),
        ),
        "pca_axis1_ratio": finite_ratio(stage_axes[0], reference_axes[0]),
        "pca_axis2_ratio": finite_ratio(stage_axes[1], reference_axes[1]),
        "pca_axis3_ratio": finite_ratio(stage_axes[2], reference_axes[2]),
        "gt_coverage_at_2mm": float(np.mean(reference_to_stage <= 2.0)),
        "gt_coverage_at_5mm": float(np.mean(reference_to_stage <= 5.0)),
        "gt_coverage_at_10mm": float(np.mean(reference_to_stage <= 10.0)),
        "stage_outlier_fraction_at_10mm": float(np.mean(stage_to_reference > 10.0)),
        "reference_rim_points": rim.reference_rim_points,
        "predicted_rim_points": rim.predicted_rim_points,
        "gt_rim_to_stage_mean_mm": rim.gt_rim_to_pred_mean_mm,
        "gt_rim_to_stage_p95_mm": rim.gt_rim_to_pred_p95_mm,
    }
    return output


def prefixed(values, prefix):
    return {f"{prefix}_{key}": value for key, value in values.items()}


def finite_float(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def geometry_contrasts(rows):
    identifiers = {
        "candidate", "fold", "case_id", "skull_id", "defect_type",
        "catastrophe", "catastrophe_reason",
    }
    output = []
    for candidate in sorted({row["candidate"] for row in rows}):
        items = [row for row in rows if row["candidate"] == candidate]
        catastrophic = [row for row in items if row["catastrophe"] == "1"]
        controls = [row for row in items if row["catastrophe"] == "0"]
        for feature in rows[0]:
            if feature in identifiers:
                continue
            cat = [finite_float(row.get(feature)) for row in catastrophic]
            control = [finite_float(row.get(feature)) for row in controls]
            cat = np.asarray([value for value in cat if value is not None])
            control = np.asarray([value for value in control if value is not None])
            if cat.size < 2 or control.size < 2:
                continue
            pooled = math.sqrt((float(cat.var()) + float(control.var())) / 2.0)
            difference = float(cat.mean() - control.mean())
            output.append({
                "candidate": candidate,
                "feature": feature,
                "catastrophe_n_finite": int(cat.size),
                "control_n_finite": int(control.size),
                "catastrophe_mean": float(cat.mean()),
                "control_mean": float(control.mean()),
                "mean_difference": difference,
                "standardized_mean_difference": (
                    difference / pooled if pooled > 0.0 else 0.0
                ),
            })
    return output


def main():
    args = parse_args()
    audit = json.loads(args.gate_audit.read_text())
    if audit.get("round_b_allowed") is not False or audit.get("selected") != []:
        raise RuntimeError("Replay requires the blocked Round-A gate audit")
    verify(args.gate_audit)
    verify(args.case_labels)
    label_rows = read_csv(args.case_labels)
    labels = {(row["candidate"], row["case_id"]): row for row in label_rows}
    if len(labels) != 1680:
        raise RuntimeError(f"Expected 1680 frozen labels, found {len(labels)}")

    record_paths = sorted(args.records_root.glob("*/run_record.json"))
    if len(record_paths) != 16:
        raise RuntimeError(f"Expected 16 run records, found {len(record_paths)}")
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    rows = []
    metric_checks = []

    for record_path in record_paths:
        record = json.loads(record_path.read_text())
        candidate = record["candidate"]
        fold = record["fold"]
        seed = int(record["seed"])
        config_artifact = record["artifacts"]["config"]
        checkpoint_artifact = record["artifacts"]["checkpoint"]
        config_path = Path(config_artifact["path"])
        checkpoint_path = Path(checkpoint_artifact["path"])
        verify(config_path, config_artifact["sha256"])
        verify(checkpoint_path, checkpoint_artifact["sha256"])

        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        config = cfg_from_yaml_file(str(config_path))
        dataset_cfg = config.dataset.val
        dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
        if len(dataset) != 105:
            raise RuntimeError(f"{candidate}/{fold}: expected 105 cases")
        model = builder.model_builder(config.model)
        builder.load_model(model, str(checkpoint_path))
        model.to(device).eval()
        model.enable_full_instrumentation(True)

        with torch.no_grad():
            for index in tqdm(
                range(len(dataset)),
                desc=f"GT replay {candidate}/fold{fold}",
                dynamic_ncols=True,
            ):
                _, case_id, data = dataset[index]
                partial, target = data
                prediction = model(partial.unsqueeze(0).to(device))[-1]
                records = model.pop_full_instrumentation()
                if records is None or records.get("backbone") is None:
                    raise RuntimeError(f"Missing instrumentation for {case_id}")
                if not torch.isfinite(prediction).all():
                    raise RuntimeError(f"Non-finite prediction for {case_id}")
                coarse = records["backbone"]["coarse"][0].cpu().numpy()
                prediction_np = prediction[0].cpu().numpy()
                reference = target.numpy()
                source, arrays = load_full_sample(dataset, index)
                norm = source["normalization"]
                centroid, scale = norm["centroid"], norm["scale"]
                label = labels[(candidate, str(case_id))]

                coarse_geometry = stage_geometry(
                    coarse, reference, arrays["partial"], centroid, scale,
                    args.rim_band_mm,
                )
                final_geometry = stage_geometry(
                    prediction_np, reference, arrays["partial"], centroid, scale,
                    args.rim_band_mm,
                )
                frozen_hd95 = finite_float(label["implant_hd95_mm"])
                hd95_delta = abs(final_geometry["surface_hd95_mm"] - frozen_hd95)
                metric_checks.append(hd95_delta)
                if hd95_delta > 1e-4:
                    raise RuntimeError(
                        f"Frozen metric replay mismatch for {candidate}/{case_id}: "
                        f"delta={hd95_delta}"
                    )
                row = {
                    "candidate": candidate,
                    "fold": fold,
                    "case_id": str(case_id),
                    "skull_id": source.get("skull_id", ""),
                    "defect_type": source.get("defect_type", ""),
                    "catastrophe": label["catastrophe"],
                    "catastrophe_reason": label["catastrophe_reason"],
                    **prefixed(coarse_geometry, "coarse"),
                    **prefixed(final_geometry, "final"),
                }
                row.update({
                    "refinement_gt_to_stage_mean_delta_mm": (
                        final_geometry["gt_to_stage_mean_mm"]
                        - coarse_geometry["gt_to_stage_mean_mm"]
                    ),
                    "refinement_gt_to_stage_p95_delta_mm": (
                        final_geometry["gt_to_stage_p95_mm"]
                        - coarse_geometry["gt_to_stage_p95_mm"]
                    ),
                    "refinement_centroid_offset_delta_mm": (
                        final_geometry["centroid_offset_mm"]
                        - coarse_geometry["centroid_offset_mm"]
                    ),
                })
                rows.append(row)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if len(rows) != 1680:
        raise RuntimeError(f"Expected 1680 replay rows, found {len(rows)}")
    contrasts = geometry_contrasts(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_case_path = args.output_dir / "gt_geometry_per_case.csv"
    contrast_path = args.output_dir / "gt_geometry_contrasts.csv"
    write_csv(per_case_path, rows)
    write_csv(contrast_path, contrasts)

    summary = {
        "replay_version": "mamba-v12-round-a-gt-aware-replay-v1",
        "observation_only": True,
        "post_hoc": True,
        "selection_inert": True,
        "round_b_allowed": False,
        "old_monitor_used": False,
        "official_test_used": False,
        "locked_confirmation_used": False,
        "records": len(rows),
        "maximum_frozen_implant_hd95_replay_delta_mm": max(metric_checks),
        "gate_audit_sha256": sha256_file(args.gate_audit),
        "case_labels_sha256": sha256_file(args.case_labels),
        "outputs": {
            "per_case": per_case_path.name,
            "contrasts": contrast_path.name,
        },
    }
    summary_path = args.output_dir / "gt_geometry_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = [
        "# Mamba v1.2 Round-A GT-aware observation-only replay\n",
        "> Post-hoc only；不参与选择，不解锁 Round B，未访问 locked confirmation、旧 monitor 或 official test。\n",
        f"- records：{len(rows)}",
        f"- frozen Implant HD95 最大重放差：{max(metric_checks):.8g} mm\n",
    ]
    for candidate in ("C0", "C1", "C2", "C3"):
        selected = [row for row in contrasts if row["candidate"] == candidate]
        selected.sort(
            key=lambda row: abs(float(row["standardized_mean_difference"])),
            reverse=True,
        )
        report.extend([
            f"## {candidate}", "",
            "| Geometry feature | SMD | Cat mean | Control mean |",
            "|---|---:|---:|---:|",
        ])
        for row in selected[:15]:
            report.append(
                f"| `{row['feature']}` | "
                f"{float(row['standardized_mean_difference']):.4f} | "
                f"{float(row['catastrophe_mean']):.6g} | "
                f"{float(row['control_mean']):.6g} |"
            )
        report.append("")
    report.extend([
        "## 解释限制\n",
        "- 该重放使用训练后 checkpoint 和 development labels，所有结论均为 post-hoc；",
        "- coarse 与 final 的 GT 几何对照可定位误差是否已在 query-position/coarse 阶段出现；",
        "- 关联不能证明某个内部机制导致灾难；",
        "- 结果只能用于预注册新的 D2.1 候选，不得恢复原 Round B。",
    ])
    report_path = args.output_dir / "gt_geometry_report_zh.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    for path in (per_case_path, contrast_path, summary_path, report_path):
        Path(str(path) + ".sha256").write_text(
            f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
        )
        print(f"[saved] {path}")
    print(f"[done] GT-aware observation-only replay records={len(rows)}")
    print("[locked] Round B remains forbidden; confirmation was not accessed")


if __name__ == "__main__":
    main()
