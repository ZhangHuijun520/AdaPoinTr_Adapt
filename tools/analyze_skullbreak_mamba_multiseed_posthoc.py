#!/usr/bin/env python
"""Analyze full-monitor Mamba instrumentation across frozen seeds."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


VERSION = "mamba-v1.1-o0-multiseed-monitor-posthoc-analysis-v1"
SEEDS = (0, 1, 2)
METRICS = (
    "implant_cd_l1_mm",
    "implant_hd95_mm",
    "implant_nsd_at_1mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
)
CORRELATION_TARGETS = (
    "implant_hd95_mm",
    "final_hd95_mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
)
BLOCK_FEATURES = (
    "alpha",
    "effective_alpha",
    "input_rms",
    "mixed_rms",
    "residual_rms",
    "output_rms",
    "residual_to_input_rms",
    "residual_to_input_token_ratio_p95",
    "residual_to_input_token_ratio_max",
    "input_residual_cosine",
    "output_delta_rms",
    "residual_head_token_norm_mean",
    "residual_tail_token_norm_mean",
    "residual_tail_to_head_ratio",
    "residual_max_position_fraction",
    "output_nonfinite_count",
)
ORDERING_FEATURES = (
    "jump_mean",
    "jump_p95",
    "jump_max",
    "path_length",
    "endpoint_distance",
    "path_efficiency",
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metrics",
        action="append",
        required=True,
        help="SEED=per_sample.csv; provide exactly seed 0, 1, and 2",
    )
    parser.add_argument(
        "--instrumentation",
        action="append",
        required=True,
        help="SEED=instrumentation_dir; provide exactly seed 0, 1, and 2",
    )
    parser.add_argument("--panel", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--catastrophe_threshold_mm", type=float, default=50.0)
    return parser.parse_args()


def parse_seed_paths(values, label):
    output = {}
    for value in values:
        seed_text, separator, path_text = value.partition("=")
        if not separator:
            raise ValueError(f"Invalid {label} mapping: {value}")
        seed = int(seed_text)
        if seed in output:
            raise ValueError(f"Duplicate {label} seed: {seed}")
        output[seed] = Path(path_text)
    if set(output) != set(SEEDS):
        raise ValueError(
            f"{label} must provide seeds {SEEDS}, got {sorted(output)}"
        )
    return output


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def finite_float(value):
    result = float(value)
    return result if math.isfinite(result) else math.nan


def safe_number(value):
    value = float(value)
    return value if math.isfinite(value) else None


def pearson(left, right):
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    valid = np.isfinite(left) & np.isfinite(right)
    left = left[valid]
    right = right[valid]
    if left.size < 3 or np.std(left) == 0 or np.std(right) == 0:
        return math.nan, int(left.size)
    return float(np.corrcoef(left, right)[0, 1]), int(left.size)


def rankdata(values):
    values = np.asarray(values, dtype=np.float64)
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.size, dtype=np.float64)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + end - 1) / 2.0 + 1.0
        start = end
    return ranks


def spearman(left, right):
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    valid = np.isfinite(left) & np.isfinite(right)
    left = left[valid]
    right = right[valid]
    if left.size < 3:
        return math.nan, int(left.size)
    return pearson(rankdata(left), rankdata(right))[0], int(left.size)


def centered_values(rows, key):
    by_case = defaultdict(list)
    for row in rows:
        by_case[row["case_id"]].append(row[key])
    means = {
        case_id: float(np.nanmean(values))
        for case_id, values in by_case.items()
    }
    return [row[key] - means[row["case_id"]] for row in rows]


def load_token_manifest(directory):
    path = directory / "token_arrays_manifest.jsonl"
    result = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            result[str(row["case_id"])] = directory / row["path"]
    return result


def verify_token_equality(instrumentation_paths, case_ids):
    manifests = {
        seed: load_token_manifest(path)
        for seed, path in instrumentation_paths.items()
    }
    rows = []
    all_equal = True
    maximum_delta = 0.0
    for case_id in sorted(case_ids):
        with np.load(manifests[0][case_id], allow_pickle=False) as archive:
            reference = {key: archive[key].copy() for key in archive.files}
        row = {"case_id": case_id}
        for seed in (1, 2):
            with np.load(manifests[seed][case_id], allow_pickle=False) as archive:
                coordinate_delta = max(
                    float(np.max(np.abs(reference[key] - archive[key])))
                    for key in ("coor_original", "coor_ordered")
                )
                sort_equal = bool(
                    np.array_equal(reference["sort_idx"], archive["sort_idx"])
                )
            coordinates_equal = coordinate_delta == 0.0
            equal = coordinates_equal and sort_equal
            row[f"seed0_seed{seed}_coordinates_equal"] = coordinates_equal
            row[f"seed0_seed{seed}_sort_idx_equal"] = sort_equal
            row[f"seed0_seed{seed}_max_coordinate_delta"] = coordinate_delta
            all_equal = all_equal and equal
            maximum_delta = max(maximum_delta, coordinate_delta)
        rows.append(row)
    return rows, all_equal, maximum_delta


def build_long_rows(metric_paths, instrumentation_paths, panel):
    panel_cases = {str(row["case_id"]) for row in panel["cases"]}
    all_rows = []
    source_hashes = {"metrics": {}, "instrumentation": {}}
    for seed in SEEDS:
        metric_path = metric_paths[seed]
        metric_rows = read_csv(metric_path)
        metric_by_case = {str(row["case_id"]): row for row in metric_rows}
        ordering_path = instrumentation_paths[seed] / "ordering_geometry_per_case.csv"
        block_path = instrumentation_paths[seed] / "adapter_block_per_case.csv"
        ordering_by_case = {
            str(row["case_id"]): row for row in read_csv(ordering_path)
        }
        block_by_case = defaultdict(dict)
        for row in read_csv(block_path):
            block_by_case[str(row["case_id"])][int(row["block_index"])] = row

        case_sets = (
            set(metric_by_case), set(ordering_by_case), set(block_by_case)
        )
        if any(case_set != panel_cases for case_set in case_sets):
            raise RuntimeError(
                f"seed-{seed} case set differs from the locked 50-case panel"
            )
        source_hashes["metrics"][str(seed)] = sha256_file(metric_path)
        source_hashes["instrumentation"][str(seed)] = {
            "ordering_csv": sha256_file(ordering_path),
            "block_csv": sha256_file(block_path),
        }

        for case_id in sorted(panel_cases):
            metric_row = metric_by_case[case_id]
            rim_hd95 = finite_float(metric_row["rim_contact_hd95_mm"])
            row = {
                "seed": seed,
                "case_id": case_id,
                "skull_id": metric_row.get("skull_id", ""),
                "defect_type": metric_row.get("defect_type", ""),
                "catastrophe": (
                    not math.isfinite(rim_hd95) or rim_hd95 > 50.0
                ),
            }
            for metric in METRICS:
                row[metric] = finite_float(metric_row[metric])
            for feature in ORDERING_FEATURES:
                row[f"ordering_{feature}"] = finite_float(
                    ordering_by_case[case_id][feature]
                )
            for block_index in (0, 1):
                block = block_by_case[case_id][block_index]
                for feature in BLOCK_FEATURES:
                    row[f"block{block_index}_{feature}"] = finite_float(
                        block[feature]
                    )
            all_rows.append(row)
    return all_rows, source_hashes


def correlation_rows(rows, features):
    output = []
    scopes = [(f"seed-{seed}", [row for row in rows if row["seed"] == seed]) for seed in SEEDS]
    scopes.append(("pooled-descriptive", rows))
    for scope, scope_rows in scopes:
        for target in CORRELATION_TARGETS:
            for feature in features:
                p, count = pearson(
                    [row[feature] for row in scope_rows],
                    [row[target] for row in scope_rows],
                )
                s, _ = spearman(
                    [row[feature] for row in scope_rows],
                    [row[target] for row in scope_rows],
                )
                output.append({
                    "scope": scope,
                    "target": target,
                    "feature": feature,
                    "count": count,
                    "pearson": safe_number(p),
                    "spearman": safe_number(s),
                })

    for target in CORRELATION_TARGETS:
        centered_target = centered_values(rows, target)
        for feature in features:
            centered_feature = centered_values(rows, feature)
            p, count = pearson(centered_feature, centered_target)
            s, _ = spearman(centered_feature, centered_target)
            output.append({
                "scope": "case-centered-cross-seed",
                "target": target,
                "feature": feature,
                "count": count,
                "pearson": safe_number(p),
                "spearman": safe_number(s),
            })
    return output


def catastrophe_contrasts(rows, features):
    output = []
    for scope, scope_rows in [("pooled", rows)] + [
        (f"seed-{seed}", [row for row in rows if row["seed"] == seed])
        for seed in SEEDS
    ]:
        catastrophic = [row for row in scope_rows if row["catastrophe"]]
        controls = [row for row in scope_rows if not row["catastrophe"]]
        for feature in features:
            cat_values = np.asarray(
                [row[feature] for row in catastrophic], dtype=np.float64
            )
            control_values = np.asarray(
                [row[feature] for row in controls], dtype=np.float64
            )
            cat_mean = float(np.nanmean(cat_values)) if cat_values.size else math.nan
            control_mean = (
                float(np.nanmean(control_values)) if control_values.size else math.nan
            )
            ratio = (
                cat_mean / control_mean
                if math.isfinite(cat_mean)
                and math.isfinite(control_mean)
                and control_mean != 0
                else math.nan
            )
            output.append({
                "scope": scope,
                "feature": feature,
                "catastrophe_count": len(catastrophic),
                "control_count": len(controls),
                "catastrophe_mean": safe_number(cat_mean),
                "control_mean": safe_number(control_mean),
                "mean_delta": safe_number(cat_mean - control_mean),
                "mean_ratio": safe_number(ratio),
            })
    return output


def disaster_profiles(rows, features):
    bad_cases = {
        row["case_id"] for row in rows if row["catastrophe"]
    }
    output = []
    for row in rows:
        if row["case_id"] not in bad_cases:
            continue
        output.append({
            key: row[key]
            for key in (
                "seed", "case_id", "skull_id", "defect_type", "catastrophe",
                *METRICS, *features,
            )
        })
    return output


def mean_by_seed(rows, key):
    return {
        str(seed): float(np.nanmean([
            row[key] for row in rows if row["seed"] == seed
        ]))
        for seed in SEEDS
    }


def render_report(summary, correlations, contrasts):
    lines = [
        "# Mamba Adapter v1.1 O0-xyz 多 seed 完整 monitor post-hoc 内部诊断",
        "",
        "> 本报告为事后机制分析，不用于重新选择 seed、ordering 或模型；未运行 official test。",
        "",
        "## 数据完整性",
        "",
        f"- records：{summary['num_records']}（3 seeds x 50 cases）",
        f"- unique cases：{summary['num_cases']}",
        f"- token 坐标与排序跨 seed 完全一致：`{summary['token_equality']['all_equal']}`",
        f"- 最大 token 坐标差：`{summary['token_equality']['maximum_coordinate_delta']}`",
        "",
        "## 灾难复现",
        "",
        "| Seed | 灾难数 | 灾难率 |",
        "|---:|---:|---:|",
    ]
    for seed in SEEDS:
        count = summary["catastrophes_by_seed"][str(seed)]
        lines.append(f"| {seed} | {count} | {count / 50:.1%} |")
    lines.extend([
        "",
        f"独立灾难病例共 `{summary['unique_catastrophe_cases']}` 个；复现直方图：`{summary['catastrophe_recurrence_histogram']}`。",
        "",
        "## Block 残差分配",
        "",
        "| Seed | B0 residual/input | B1 residual/input | B0 tail/head | B1 tail/head |",
        "|---:|---:|---:|---:|---:|",
    ])
    for seed in SEEDS:
        lines.append(
            "| {seed} | {b0:.6f} | {b1:.6f} | {t0:.6f} | {t1:.6f} |".format(
                seed=seed,
                b0=summary["feature_means"]["block0_residual_to_input_rms"][str(seed)],
                b1=summary["feature_means"]["block1_residual_to_input_rms"][str(seed)],
                t0=summary["feature_means"]["block0_residual_tail_to_head_ratio"][str(seed)],
                t1=summary["feature_means"]["block1_residual_tail_to_head_ratio"][str(seed)],
            )
        )

    centered = [
        row for row in correlations
        if row["scope"] == "case-centered-cross-seed"
        and row["target"] == "rim_contact_hd95_mm"
        and row["pearson"] is not None
    ]
    centered.sort(key=lambda row: abs(row["pearson"]), reverse=True)
    lines.extend([
        "",
        "## Rim HD95 的病例内跨 seed 相关",
        "",
        "| Feature | Pearson | Spearman | N |",
        "|---|---:|---:|---:|",
    ])
    for row in centered[:12]:
        lines.append(
            f"| `{row['feature']}` | {row['pearson']:.4f} | "
            f"{row['spearman']:.4f} | {row['count']} |"
        )

    pooled = [
        row for row in contrasts
        if row["scope"] == "pooled" and row["catastrophe_count"] > 0
    ]
    pooled.sort(
        key=lambda row: abs(row["mean_ratio"] - 1.0)
        if row["mean_ratio"] is not None else -1,
        reverse=True,
    )
    lines.extend([
        "",
        "## 灾难与非灾难内部特征对照",
        "",
        "| Feature | 灾难均值 | 对照均值 | 比值 |",
        "|---|---:|---:|---:|",
    ])
    for row in pooled[:12]:
        lines.append(
            f"| `{row['feature']}` | {row['catastrophe_mean']:.6g} | "
            f"{row['control_mean']:.6g} | {row['mean_ratio']:.4f} |"
        )

    lines.extend([
        "",
        "## 解释限制",
        "",
        "- monitor 已被消费，所有关系均为 post-hoc 描述性结果；",
        "- pooled 记录不独立，case-centered 结果用于控制固定病例难度，但只有 3 个 seed；",
        "- 相关不证明 Mamba residual 导致几何失败；",
        "- 本报告只能为新的 skull-level development folds 提出假设。",
        "",
    ])
    return "\n".join(lines)


def main():
    args = parse_args()
    metric_paths = parse_seed_paths(args.metrics, "metrics")
    instrumentation_paths = parse_seed_paths(
        args.instrumentation, "instrumentation"
    )
    panel_path = Path(args.panel)
    panel = json.loads(panel_path.read_text(encoding="utf-8"))
    if not panel.get("posthoc") or not panel.get("include_all_cases"):
        raise RuntimeError("Panel is not a declared full-monitor post-hoc panel")
    if args.catastrophe_threshold_mm != 50.0:
        raise RuntimeError("Frozen catastrophe threshold must remain 50.0 mm")

    rows, source_hashes = build_long_rows(
        metric_paths, instrumentation_paths, panel
    )
    features = tuple(
        f"block{block}_{feature}"
        for block in (0, 1)
        for feature in BLOCK_FEATURES
    )
    correlations = correlation_rows(rows, features)
    contrasts = catastrophe_contrasts(rows, features)
    profiles = disaster_profiles(rows, features)
    token_rows, tokens_equal, maximum_delta = verify_token_equality(
        instrumentation_paths,
        {str(row["case_id"]) for row in panel["cases"]},
    )

    catastrophes_by_seed = {
        str(seed): sum(row["catastrophe"] for row in rows if row["seed"] == seed)
        for seed in SEEDS
    }
    bad_seeds_by_case = defaultdict(set)
    for row in rows:
        if row["catastrophe"]:
            bad_seeds_by_case[row["case_id"]].add(row["seed"])
    recurrence = Counter(len(seeds) for seeds in bad_seeds_by_case.values())
    feature_means = {
        feature: mean_by_seed(rows, feature) for feature in features
    }
    summary = {
        "analysis_version": VERSION,
        "posthoc": True,
        "selection_allowed": False,
        "official_test_used": False,
        "catastrophe_threshold_mm": 50.0,
        "num_records": len(rows),
        "num_cases": len({row["case_id"] for row in rows}),
        "catastrophes_by_seed": catastrophes_by_seed,
        "unique_catastrophe_cases": len(bad_seeds_by_case),
        "catastrophe_recurrence_histogram": {
            str(key): value for key, value in sorted(recurrence.items())
        },
        "catastrophe_cases": {
            case_id: sorted(seeds)
            for case_id, seeds in sorted(bad_seeds_by_case.items())
        },
        "token_equality": {
            "all_equal": tokens_equal,
            "maximum_coordinate_delta": maximum_delta,
        },
        "feature_means": feature_means,
        "source_hashes": source_hashes,
        "panel_sha256": sha256_file(panel_path),
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "merged": out_dir / "monitor_seed_case_instrumentation.csv",
        "correlations": out_dir / "instrumentation_correlations.csv",
        "contrasts": out_dir / "catastrophe_feature_contrasts.csv",
        "profiles": out_dir / "catastrophe_case_profiles.csv",
        "tokens": out_dir / "token_equality_per_case.csv",
        "summary": out_dir / "posthoc_summary.json",
        "report": out_dir / "posthoc_report_zh.md",
    }
    write_csv(outputs["merged"], rows)
    write_csv(outputs["correlations"], correlations)
    write_csv(outputs["contrasts"], contrasts)
    write_csv(outputs["profiles"], profiles)
    write_csv(outputs["tokens"], token_rows)
    outputs["summary"].write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    outputs["report"].write_text(
        render_report(summary, correlations, contrasts),
        encoding="utf-8",
    )
    for path in outputs.values():
        sidecar = Path(str(path) + ".sha256")
        sidecar.write_text(
            f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
        )
        print(f"[saved] {path}")
    print(
        f"[done] post-hoc records={len(rows)} cases={summary['num_cases']} "
        f"tokens_equal={tokens_equal} official_test=False"
    )


if __name__ == "__main__":
    main()
