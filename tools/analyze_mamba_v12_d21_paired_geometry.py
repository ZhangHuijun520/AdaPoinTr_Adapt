#!/usr/bin/env python
"""Paired Q1-Q3 versus Q0 analysis for the D2.1 GT replay."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


LOWER_IS_BETTER = (
    "coarse_gt_to_stage_p95_mm",
    "coarse_centroid_offset_mm",
    "coarse_radial_log_error",
    "coarse_gt_rim_to_stage_p95_mm",
    "final_gt_to_stage_p95_mm",
    "final_centroid_offset_mm",
    "final_radial_log_error",
    "final_gt_rim_to_stage_p95_mm",
    "implant_hd95_mm",
    "rim_contact_hd95_mm",
)
HIGHER_IS_BETTER = (
    "coarse_gt_coverage_at_5mm",
    "final_gt_coverage_at_5mm",
    "rim_contact_nsd_at_1mm",
)
CANDIDATES = ("Q1", "Q2", "Q3")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        raise RuntimeError(f"No rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def enrich(row, label):
    output = dict(row)
    for prefix in ("coarse", "final"):
        ratio = finite(row[f"{prefix}_radial_rms_ratio"])
        output[f"{prefix}_radial_log_error"] = (
            abs(math.log(ratio)) if ratio is not None and ratio > 0 else float("nan")
        )
    for key in ("implant_hd95_mm", "rim_contact_hd95_mm", "rim_contact_nsd_at_1mm"):
        output[key] = label[key]
    output["catastrophe"] = label["catastrophe"]
    output["catastrophe_reason"] = label["catastrophe_reason"]
    return output


def paired_rows(candidate, q0_rows, candidate_rows, defect_type="all"):
    q0 = {row["case_id"]: row for row in q0_rows}
    current = {row["case_id"]: row for row in candidate_rows}
    if set(q0) != set(current):
        raise RuntimeError(f"Case mismatch between Q0 and {candidate}")
    output = []
    for metric in LOWER_IS_BETTER + HIGHER_IS_BETTER:
        pairs = []
        for case_id in sorted(q0):
            if defect_type != "all" and q0[case_id]["defect_type"] != defect_type:
                continue
            left = finite(current[case_id].get(metric))
            right = finite(q0[case_id].get(metric))
            if left is not None and right is not None:
                pairs.append((left, right))
        if not pairs:
            continue
        deltas = [left - right for left, right in pairs]
        higher = metric in HIGHER_IS_BETTER
        output.append({
            "candidate": candidate,
            "defect_type": defect_type,
            "metric": metric,
            "direction": "higher" if higher else "lower",
            "valid_pairs": len(pairs),
            "candidate_mean": sum(left for left, _ in pairs) / len(pairs),
            "q0_mean": sum(right for _, right in pairs) / len(pairs),
            "mean_delta_candidate_minus_q0": sum(deltas) / len(deltas),
            "better_cases": sum(delta > 0 if higher else delta < 0 for delta in deltas),
            "worse_cases": sum(delta < 0 if higher else delta > 0 for delta in deltas),
            "equal_cases": sum(delta == 0 for delta in deltas),
        })
    return output


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_labels", type=Path, required=True)
    parser.add_argument("--gt_geometry", type=Path, required=True)
    parser.add_argument("--gate_audit", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    audit = json.loads(args.gate_audit.read_text())
    if audit.get("round_b_allowed") is not False:
        raise RuntimeError("Paired analysis requires a blocked D2.1 audit")
    labels = {
        (row["candidate"], row["case_id"]): row
        for row in read_csv(args.case_labels)
    }
    geometry_source = read_csv(args.gt_geometry)
    if len(labels) != 1680 or len(geometry_source) != 1680:
        raise RuntimeError("Expected 1680 frozen label and geometry records")
    geometry = []
    for row in geometry_source:
        key = (row["candidate"], row["case_id"])
        if key not in labels:
            raise RuntimeError(f"Missing frozen label: {key}")
        geometry.append(enrich(row, labels[key]))

    by_candidate = {
        candidate: [row for row in geometry if row["candidate"] == candidate]
        for candidate in ("Q0",) + CANDIDATES
    }
    paired = []
    defect_types = sorted({row["defect_type"] for row in geometry})
    for candidate in CANDIDATES:
        paired.extend(paired_rows(
            candidate, by_candidate["Q0"], by_candidate[candidate]
        ))
        for defect_type in defect_types:
            paired.extend(paired_rows(
                candidate,
                by_candidate["Q0"],
                by_candidate[candidate],
                defect_type,
            ))

    transitions = []
    q0_by_case = {row["case_id"]: row for row in by_candidate["Q0"]}
    for candidate in CANDIDATES:
        current = {row["case_id"]: row for row in by_candidate[candidate]}
        counts = Counter()
        for case_id, q0 in q0_by_case.items():
            source = q0["catastrophe"] == "1"
            target = current[case_id]["catastrophe"] == "1"
            name = {
                (False, False): "stable_noncatastrophe",
                (True, False): "rescued",
                (False, True): "induced",
                (True, True): "shared_catastrophe",
            }[(source, target)]
            counts[name] += 1
        transitions.append({
            "candidate": candidate,
            **{key: counts[key] for key in (
                "stable_noncatastrophe", "rescued", "induced", "shared_catastrophe"
            )},
            "net_catastrophe_change": counts["induced"] - counts["rescued"],
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    paired_path = args.output_dir / "paired_q_vs_q0_metrics.csv"
    transitions_path = args.output_dir / "catastrophe_transitions.csv"
    write_csv(paired_path, paired)
    write_csv(transitions_path, transitions)

    all_rows = [row for row in paired if row["defect_type"] == "all"]
    lookup = {(row["candidate"], row["metric"]): row for row in all_rows}
    report = [
        "# Mamba v1.2 D2.1 coarse geometry guard post-hoc 配对诊断",
        "",
        "> 本报告仅用于机制诊断；不参与候选选择，不解锁 Round B，未访问 locked confirmation、旧 monitor 或 official test。",
        "",
        "## 灾难转换",
        "",
        "| Candidate | Rescued | Induced | Shared | Net change |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in transitions:
        report.append(
            f"| {row['candidate']} | {row['rescued']} | {row['induced']} | "
            f"{row['shared_catastrophe']} | {row['net_catastrophe_change']:+d} |"
        )
    report.extend(["", "## 相对 Q0 的总体配对变化", ""])
    selected_metrics = (
        "coarse_centroid_offset_mm",
        "coarse_radial_log_error",
        "coarse_gt_coverage_at_5mm",
        "coarse_gt_to_stage_p95_mm",
        "coarse_gt_rim_to_stage_p95_mm",
        "final_gt_rim_to_stage_p95_mm",
        "rim_contact_hd95_mm",
    )
    for candidate in CANDIDATES:
        report.extend([
            f"### {candidate}", "",
            "| Metric | Mean delta | Better / valid |",
            "|---|---:|---:|",
        ])
        for metric in selected_metrics:
            row = lookup[(candidate, metric)]
            report.append(
                f"| `{metric}` | {float(row['mean_delta_candidate_minus_q0']):.6g} | "
                f"{row['better_cases']} / {row['valid_pairs']} |"
            )
        report.append("")
    report.extend([
        "## 解释边界",
        "",
        "- 所有结果来自已消费的 development84，属于 post-hoc 描述；",
        "- 若候选改善其直接约束目标却诱发更多 rim 灾难，说明全局 coarse 目标与接触边缘目标不一致；",
        "- 若直接目标也未改善，才支持损失强度、优化竞争或实现有效性不足的假设；",
        "- 任何后续候选都必须形成新协议修订，不能直接更改 0.01 权重后续跑。",
    ])
    report_path = args.output_dir / "paired_posthoc_report_zh.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    summary = {
        "analysis_version": "mamba-v12-d21-paired-geometry-posthoc-v1",
        "post_hoc": True,
        "selection_inert": True,
        "round_b_allowed": False,
        "locked_confirmation_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
        "gate_audit_sha256": sha256_file(args.gate_audit),
        "case_labels_sha256": sha256_file(args.case_labels),
        "gt_geometry_sha256": sha256_file(args.gt_geometry),
        "records": len(geometry),
        "transitions": transitions,
    }
    summary_path = args.output_dir / "paired_posthoc_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for path in (paired_path, transitions_path, report_path, summary_path):
        Path(str(path) + ".sha256").write_text(
            f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
        )
        print(f"[saved] {path}")
    print("[done] D2.1 paired post-hoc analysis; Round B remains forbidden")


if __name__ == "__main__":
    main()
