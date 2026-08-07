#!/usr/bin/env python
"""Post-hoc, selection-inert analysis of Mamba v1.2 Round-A failures."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


CORE_METRICS = (
    "implant_hd95_mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
)
IDENTIFIERS = {
    "candidate", "fold", "case_id", "skull_id", "defect_type", "split",
    "mechanism", "catastrophe", "catastrophe_reason", "sample_index",
    "layer_index", "block_index",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--gate_audit", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path, expected=None):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256_file(path)
    if expected is not None and actual != expected:
        raise RuntimeError(f"SHA256 mismatch: {path}")
    sidecar = Path(str(path) + ".sha256")
    if sidecar.is_file() and sidecar.read_text().split()[0] != actual:
        raise RuntimeError(f"Sidecar SHA256 mismatch: {path}")
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


def finite_float(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def classify(row):
    invalid = [metric for metric in CORE_METRICS if finite_float(row.get(metric)) is None]
    rim_hd95 = finite_float(row.get("rim_contact_hd95_mm"))
    if invalid:
        return True, "nonfinite:" + ",".join(invalid)
    if rim_hd95 > 50.0:
        return True, "rim_contact_hd95_mm>50"
    return False, "none"


def numeric_keys(rows, group_keys):
    excluded = IDENTIFIERS | set(group_keys)
    keys = []
    for key in rows[0]:
        if key in excluded:
            continue
        values = [finite_float(row.get(key)) for row in rows]
        if all(value is not None for value in values):
            keys.append(key)
    return keys


def contrast_rows(rows, group_keys):
    grouped = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    output = []
    for group, items in sorted(grouped.items()):
        features = numeric_keys(items, group_keys)
        catastrophic = [row for row in items if row["catastrophe"] == "1"]
        controls = [row for row in items if row["catastrophe"] == "0"]
        if not catastrophic or not controls:
            continue
        for feature in features:
            cat = np.asarray([float(row[feature]) for row in catastrophic], dtype=np.float64)
            control = np.asarray([float(row[feature]) for row in controls], dtype=np.float64)
            pooled = math.sqrt((float(cat.var()) + float(control.var())) / 2.0)
            difference = float(cat.mean() - control.mean())
            result = {key: value for key, value in zip(group_keys, group)}
            result.update({
                "feature": feature,
                "catastrophe_n": len(cat),
                "control_n": len(control),
                "catastrophe_mean": float(cat.mean()),
                "control_mean": float(control.mean()),
                "mean_difference": difference,
                "standardized_mean_difference": (
                    difference / pooled if pooled > 0.0 else 0.0
                ),
            })
            output.append(result)
    return output


def attach_labels(rows, labels, candidate, fold):
    output = []
    for source in rows:
        key = (candidate, source["case_id"])
        if key not in labels:
            raise RuntimeError(f"Instrumentation case is absent from metrics: {key}")
        row = dict(source)
        row["candidate"] = candidate
        row["fold"] = fold
        row["catastrophe"] = "1" if labels[key]["catastrophe"] else "0"
        row["catastrophe_reason"] = labels[key]["catastrophe_reason"]
        output.append(row)
    return output


def top_features(rows, candidate, limit=8):
    selected = [row for row in rows if row["candidate"] == candidate]
    selected.sort(
        key=lambda row: abs(float(row["standardized_mean_difference"])),
        reverse=True,
    )
    return selected[:limit]


def main():
    args = parse_args()
    verify_file(args.gate_audit)
    audit = json.loads(args.gate_audit.read_text())
    if audit.get("round_b_allowed") is not False or audit.get("selected") != []:
        raise RuntimeError("Post-hoc analysis requires a blocked Round-A audit")

    labels = {}
    label_rows = []
    pipeline_rows = []
    decoder_rows = []
    adapter_rows = []
    record_paths = sorted(args.records_root.glob("*/run_record.json"))
    if len(record_paths) != 16:
        raise RuntimeError(f"Expected 16 Round-A run records, found {len(record_paths)}")

    for record_path in record_paths:
        record = json.loads(record_path.read_text())
        candidate = record["candidate"]
        fold = record["fold"]
        metrics_artifact = record["artifacts"]["metrics_csv"]
        metrics_path = Path(metrics_artifact["path"])
        verify_file(metrics_path, metrics_artifact["sha256"])
        for row in read_csv(metrics_path):
            catastrophe, reason = classify(row)
            key = (candidate, row["case_id"])
            if key in labels:
                raise RuntimeError(f"Duplicate candidate/case prediction: {key}")
            label = {
                "candidate": candidate,
                "fold": fold,
                "case_id": row["case_id"],
                "skull_id": row.get("skull_id", ""),
                "defect_type": row.get("defect_type", ""),
                "catastrophe": catastrophe,
                "catastrophe_reason": reason,
                **{metric: row.get(metric, "") for metric in CORE_METRICS},
            }
            labels[key] = label
            label_rows.append({
                **label,
                "catastrophe": "1" if catastrophe else "0",
            })

        instrument_dir = record_path.parent / "instrumentation"
        paths = {
            "pipeline": instrument_dir / "pipeline_per_case.csv",
            "decoder": instrument_dir / "decoder_layer_per_case.csv",
            "adapter": instrument_dir / "adapter_block_per_case.csv",
        }
        for path in paths.values():
            verify_file(path)
        pipeline_rows.extend(attach_labels(
            read_csv(paths["pipeline"]), labels, candidate, fold
        ))
        decoder_rows.extend(attach_labels(
            read_csv(paths["decoder"]), labels, candidate, fold
        ))
        adapter_rows.extend(attach_labels(
            read_csv(paths["adapter"]), labels, candidate, fold
        ))

    expected = {"C0", "C1", "C2", "C3"}
    if {row["candidate"] for row in label_rows} != expected:
        raise RuntimeError("Incomplete candidate set")
    if len(label_rows) != 1680:
        raise RuntimeError(f"Expected 1680 candidate/case rows, found {len(label_rows)}")

    by_case = defaultdict(list)
    for row in label_rows:
        if row["catastrophe"] == "1":
            by_case[row["case_id"]].append(row)
    recurrence_rows = []
    for case_id, items in sorted(by_case.items()):
        recurrence_rows.append({
            "case_id": case_id,
            "skull_id": items[0]["skull_id"],
            "defect_type": items[0]["defect_type"],
            "candidate_count": len(items),
            "candidates": ",".join(sorted(row["candidate"] for row in items)),
            "nonfinite_candidate_count": sum(
                row["catastrophe_reason"].startswith("nonfinite:") for row in items
            ),
        })

    candidate_summary = {}
    for candidate in sorted(expected):
        items = [row for row in label_rows if row["candidate"] == candidate]
        catastrophic = [row for row in items if row["catastrophe"] == "1"]
        candidate_summary[candidate] = {
            "records": len(items),
            "catastrophes": len(catastrophic),
            "catastrophe_rate": len(catastrophic) / len(items),
            "nonfinite": sum(
                row["catastrophe_reason"].startswith("nonfinite:")
                for row in catastrophic
            ),
            "by_defect_type": dict(Counter(
                row["defect_type"] for row in catastrophic
            )),
        }

    pipeline_contrasts = contrast_rows(pipeline_rows, ("candidate",))
    decoder_contrasts = contrast_rows(
        decoder_rows, ("candidate", "layer_index")
    )
    adapter_contrasts = contrast_rows(
        adapter_rows, ("candidate", "block_index")
    )
    recurrence_histogram = dict(sorted(Counter(
        int(row["candidate_count"]) for row in recurrence_rows
    ).items()))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "case_labels": args.output_dir / "round_a_case_labels.csv",
        "recurrence": args.output_dir / "catastrophe_recurrence.csv",
        "pipeline": args.output_dir / "pipeline_feature_contrasts.csv",
        "decoder": args.output_dir / "decoder_feature_contrasts.csv",
        "adapter": args.output_dir / "adapter_feature_contrasts.csv",
    }
    write_csv(outputs["case_labels"], label_rows)
    write_csv(outputs["recurrence"], recurrence_rows)
    write_csv(outputs["pipeline"], pipeline_contrasts)
    write_csv(outputs["decoder"], decoder_contrasts)
    write_csv(outputs["adapter"], adapter_contrasts)

    summary = {
        "analysis_version": "mamba-v12-round-a-posthoc-v1",
        "post_hoc": True,
        "selection_inert": True,
        "round_b_allowed": False,
        "old_monitor_used": False,
        "official_test_used": False,
        "locked_confirmation_used": False,
        "gate_audit": str(args.gate_audit),
        "gate_audit_sha256": sha256_file(args.gate_audit),
        "run_records": len(record_paths),
        "candidate_case_records": len(label_rows),
        "unique_catastrophic_cases": len(recurrence_rows),
        "recurrence_histogram": recurrence_histogram,
        "candidate_summary": candidate_summary,
        "outputs": {key: path.name for key, path in outputs.items()},
    }
    summary_path = args.output_dir / "posthoc_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = [
        "# Mamba v1.2 Round-A 灾难失败 post-hoc 诊断\n",
        "> 本分析不参与候选选择，不解锁 Round B，未访问旧 monitor、official test 或 locked confirmation。\n",
        "## 灾难概况\n",
        f"- 候选-病例记录：{len(label_rows)}",
        f"- 独立灾难病例：{len(recurrence_rows)}",
        f"- 跨候选复现直方图：`{recurrence_histogram}`\n",
        "| 候选 | 灾难数 | 灾难率 | Nonfinite |",
        "|---|---:|---:|---:|",
    ]
    for candidate in sorted(expected):
        item = candidate_summary[candidate]
        report.append(
            f"| {candidate} | {item['catastrophes']} | "
            f"{100.0 * item['catastrophe_rate']:.2f}% | {item['nonfinite']} |"
        )
    report.extend(["\n## 内部特征对照", ""])
    for candidate in sorted(expected):
        report.append(f"### {candidate}")
        report.append("\nPipeline 中绝对标准化差异最大的特征：\n")
        report.append("| Feature | SMD | Cat mean | Control mean |")
        report.append("|---|---:|---:|---:|")
        for row in top_features(pipeline_contrasts, candidate):
            report.append(
                f"| `{row['feature']}` | "
                f"{float(row['standardized_mean_difference']):.4f} | "
                f"{float(row['catastrophe_mean']):.6g} | "
                f"{float(row['control_mean']):.6g} |"
            )
        report.append("")
    report.extend([
        "## 解释限制\n",
        "- 全部关系均为 development84 上的 post-hoc 描述，不能重新选择候选；",
        "- 特征对照包含病例几何与机制响应的混合影响，不证明因果；",
        "- 当前 coarse/query 仅记录张量统计，未计算相对 GT implant 的阶段几何误差；",
        "- 因此本报告可定位内部异常关联，但不能单独证明几何错误首次出现在哪一阶段；",
        "- 若要决定 geometry guard 或 decoder/rebuild 修复，需预注册并运行 GT-aware observation-only replay。",
    ])
    report_path = args.output_dir / "posthoc_report_zh.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    all_outputs = list(outputs.values()) + [summary_path, report_path]
    for path in all_outputs:
        Path(str(path) + ".sha256").write_text(
            f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
        )
        print(f"[saved] {path}")
    print(
        f"[done] post-hoc records={len(label_rows)} "
        f"unique_catastrophes={len(recurrence_rows)}"
    )
    print("[locked] selection remains closed; Round B is forbidden")


if __name__ == "__main__":
    main()
