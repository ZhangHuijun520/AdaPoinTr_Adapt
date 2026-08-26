#!/usr/bin/env python3
"""Diagnose a frozen MUG500+ M2 overlap audit without changing its gate."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


POSTHOC_ID = "mug500plus-m2-protected-overlap-posthoc-v1"
EXPECTED_AUDIT_ID = "mug500plus-m2-protected-overlap-audit-v1"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def percentile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return math.nan
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def csv_bytes(rows: Sequence[Sequence[Any]]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode("utf-8")


def verify_frozen_audit(audit_dir: Path) -> None:
    manifest = audit_dir / "files.sha256"
    if not manifest.is_file():
        raise FileNotFoundError(manifest)
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        path = audit_dir / name.strip().lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen v1 hash mismatch: {path}")


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical post-hoc diagnosis")
        print(f"[locked] existing post-hoc diagnosis is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] immutable post-hoc diagnosis: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audit_dir = args.audit_dir.resolve()
    output_dir = args.output_dir.resolve()
    verify_frozen_audit(audit_dir)

    summary_path = audit_dir / "overlap_audit_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (
        summary.get("audit_id") != EXPECTED_AUDIT_ID
        or summary.get("automatic_gate_passed") is not False
        or summary.get("training_unlocked") is not False
    ):
        raise RuntimeError("Expected a frozen, failed, training-locked v1 audit")

    candidates = read_csv(audit_dir / "near_duplicate_candidates.csv")
    calibration = read_csv(audit_dir / "within_source_calibration.csv")
    cd_threshold = float(summary["thresholds"]["symmetric_cd_l1_normalized"])
    hd_threshold = float(summary["thresholds"]["symmetric_hd95_normalized"])

    dataset_rows: List[List[Any]] = [[
        "protected_dataset", "candidate_pairs", "suspect_pairs",
        "suspect_fraction", "flagged_mug_skulls", "flagged_protected_skulls",
        "cd_q01", "cd_q50", "cd_q99", "hd95_q01", "hd95_q50", "hd95_q99",
    ]]
    dataset_stats: Dict[str, Dict[str, Any]] = {}
    for dataset in sorted({row["protected_dataset"] for row in candidates}):
        rows = [row for row in candidates if row["protected_dataset"] == dataset]
        suspects = [row for row in rows if row["suspect_near_duplicate"] == "1"]
        stats = {
            "candidate_pairs": len(rows),
            "suspect_pairs": len(suspects),
            "suspect_fraction": len(suspects) / len(rows),
            "flagged_mug_skulls": len({row["mug_skull_id"] for row in suspects}),
            "flagged_protected_skulls": len({row["protected_skull_id"] for row in suspects}),
            "cd_q01": percentile(
                (float(row["symmetric_cd_l1_normalized"]) for row in rows), 0.01
            ),
            "cd_q50": percentile(
                (float(row["symmetric_cd_l1_normalized"]) for row in rows), 0.50
            ),
            "cd_q99": percentile(
                (float(row["symmetric_cd_l1_normalized"]) for row in rows), 0.99
            ),
            "hd95_q01": percentile(
                (float(row["symmetric_hd95_normalized"]) for row in rows), 0.01
            ),
            "hd95_q50": percentile(
                (float(row["symmetric_hd95_normalized"]) for row in rows), 0.50
            ),
            "hd95_q99": percentile(
                (float(row["symmetric_hd95_normalized"]) for row in rows), 0.99
            ),
        }
        dataset_stats[dataset] = stats
        dataset_rows.append([dataset, *stats.values()])

    best_rows: List[List[Any]] = [[
        "mug_skull_id", "best_protected_skull_id", "best_score",
        "second_best_score", "score_gap", "score_ratio",
        "symmetric_cd_l1_normalized", "symmetric_hd95_normalized",
    ]]
    skullfix = [
        row for row in candidates if row["protected_dataset"] == "skullfix"
    ]
    by_mug: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for row in skullfix:
        item: Dict[str, Any] = dict(row)
        item["score"] = max(
            float(row["symmetric_cd_l1_normalized"]) / cd_threshold,
            float(row["symmetric_hd95_normalized"]) / hd_threshold,
        )
        by_mug[row["mug_skull_id"]].append(item)

    gaps: List[float] = []
    best_protected = collections.Counter()
    best_score_by_mug: Dict[str, float] = {}
    for mug_skull_id, rows in sorted(by_mug.items()):
        ordered = sorted(rows, key=lambda row: row["score"])
        first, second = ordered[:2]
        gap = float(second["score"] - first["score"])
        ratio = float(second["score"] / first["score"])
        gaps.append(gap)
        best_protected[first["protected_skull_id"]] += 1
        best_score_by_mug[mug_skull_id] = float(first["score"])
        best_rows.append([
            mug_skull_id,
            first["protected_skull_id"],
            first["score"],
            second["score"],
            gap,
            ratio,
            first["symmetric_cd_l1_normalized"],
            first["symmetric_hd95_normalized"],
        ])

    suspect_rows = [row for row in skullfix if row["suspect_near_duplicate"] == "1"]
    rank_counts = collections.Counter(int(row["descriptor_rank"]) for row in suspect_rows)
    top_best = best_protected.most_common(5)
    top_best_fraction = sum(count for _, count in top_best) / len(by_mug)

    calibration_stats = {}
    for dataset in sorted({row["dataset"] for row in calibration}):
        rows = [row for row in calibration if row["dataset"] == dataset]
        calibration_stats[dataset] = {
            "pairs": len(rows),
            "cd_q50": percentile(
                (float(row["symmetric_cd_l1_normalized"]) for row in rows), 0.50
            ),
            "cd_q99": percentile(
                (float(row["symmetric_cd_l1_normalized"]) for row in rows), 0.99
            ),
            "hd95_q50": percentile(
                (float(row["symmetric_hd95_normalized"]) for row in rows), 0.50
            ),
            "hd95_q99": percentile(
                (float(row["symmetric_hd95_normalized"]) for row in rows), 0.99
            ),
        }

    diagnostic = {
        "posthoc_id": POSTHOC_ID,
        "source_audit_id": EXPECTED_AUDIT_ID,
        "source_audit_summary_sha256": sha256_file(summary_path),
        "source_audit_tree_verified": True,
        "post_hoc": True,
        "selection_inert": True,
        "automatic_gate_changed": False,
        "automatic_gate_passed": False,
        "training_unlocked": False,
        "model_predictions_used": False,
        "model_metrics_used": False,
        "protected_defect_or_implant_arrays_used": False,
        "dataset_stats": dataset_stats,
        "calibration_stats": calibration_stats,
        "skullfix_match_structure": {
            "unique_mug_skulls": len(by_mug),
            "flagged_mug_skulls": len({row["mug_skull_id"] for row in suspect_rows}),
            "flagged_protected_skulls": len(
                {row["protected_skull_id"] for row in suspect_rows}
            ),
            "best_match_distinct_protected_skulls": len(best_protected),
            "top5_best_match_frequency": top_best,
            "top5_best_match_fraction": top_best_fraction,
            "best_second_score_gap_q50": percentile(gaps, 0.50),
            "best_second_score_gap_q95": percentile(gaps, 0.95),
            "best_second_score_gap_max": max(gaps),
            "strong_gap_gt_0_1_count": sum(gap > 0.1 for gap in gaps),
            "suspect_descriptor_rank_counts": dict(sorted(rank_counts.items())),
        },
        "provenance": {
            "mug500plus": "Medical University of Graz clinical-routine head CT scans",
            "skullfix": "CQ500 public head CT collection",
            "independent_reported_sources": True,
            "mug500plus_reference": "https://doi.org/10.1016/j.dib.2021.107524",
            "skullfix_reference": "https://doi.org/10.1016/j.dib.2021.106902",
        },
        "interpretation": {
            "v1_outcome": "failed_as_preregistered",
            "evidence_of_exact_overlap": False,
            "near_duplicate_labels_establish_patient_overlap": False,
            "diagnostic_assessment": "v1_geometry_gate_has_low_specificity_for_skullfix",
            "required_next_step": "preregister_independent_high_resolution_overlap_audit_v2",
        },
    }

    report = f"""# MUG500+ M2 protected-overlap v1 post-hoc 诊断

> 本报告为冻结 v1 门控之后的事后诊断。它不能修改 v1 结论、删除疑似病例、调整阈值或解锁 D3 training。

## 冻结结论

- exact hash intersection：`{summary['counts']['exact_hash_intersections']}`；
- near-duplicate suspect：`{summary['counts']['near_duplicate_suspects']}`；
- v1 automatic gate：**未通过**；
- D3 training：**继续锁定**。

## 命中构成

| Protected dataset | 候选对 | 疑似对 | 疑似比例 | 涉及 MUG skull | 涉及 protected skull |
|---|---:|---:|---:|---:|---:|
| SkullBreak | {dataset_stats['skullbreak']['candidate_pairs']} | {dataset_stats['skullbreak']['suspect_pairs']} | {dataset_stats['skullbreak']['suspect_fraction']:.1%} | {dataset_stats['skullbreak']['flagged_mug_skulls']} | {dataset_stats['skullbreak']['flagged_protected_skulls']} |
| SkullFix | {dataset_stats['skullfix']['candidate_pairs']} | {dataset_stats['skullfix']['suspect_pairs']} | {dataset_stats['skullfix']['suspect_fraction']:.1%} | {dataset_stats['skullfix']['flagged_mug_skulls']} | {dataset_stats['skullfix']['flagged_protected_skulls']} |

全部疑似项来自 SkullFix；SkullBreak 为 0。SkullFix 命中覆盖 119/125 个 MUG source skull，因此该标签在当前表示与阈值下不是稀疏的近重复信号。

## 匹配结构

- 125 个 MUG skull 的最佳 SkullFix 匹配只落在 `{len(best_protected)}` 个 SkullFix ID 上；
- 最常见 5 个 ID 占全部最佳匹配的 `{top_best_fraction:.1%}`；
- 最佳与次佳归一化联合分数间隔中位数：`{percentile(gaps, 0.50):.6f}`；
- 间隔大于 0.1 的病例：`{sum(gap > 0.1 for gap in gaps)}/125`；
- descriptor rank 1--10 均有大量疑似项：`{dict(sorted(rank_counts.items()))}`。

上述模式缺少清晰的一对一对应、显著匹配间隔和 rank-1 富集，不能把 769 个标签解释为 769 个患者级重复。

## 来源证据

- MUG500+ 论文说明 500 个健康颅骨来自 Medical University of Graz 临床常规 head CT；
- SkullFix/SkullBreak 论文说明两者来自 CQ500；
- 两个已报告来源相互独立，但来源证据不能代替几何复核。

参考：

- MUG500+: https://doi.org/10.1016/j.dib.2021.107524
- SkullBreak/SkullFix: https://doi.org/10.1016/j.dib.2021.106902

## 诊断结论

v1 按预注册规则正确地失败并阻止了训练。事后结果表明，当前 `1024-point PCA + pooled q99 x 1.5` 规则对 SkullFix 的特异度不足；它适合作为高灵敏度初筛，不能独立证明数据重叠。

下一步必须另行预注册 high-resolution overlap audit v2，使用独立实现、源级高分辨率几何、明确的阳性/阴性校准和人工复核边界。v2 冻结并通过之前，不生成 100/25 split，不训练 D3。
"""

    files = {
        "dataset_statistics.csv": csv_bytes(dataset_rows),
        "skullfix_best_match_per_mug.csv": csv_bytes(best_rows),
        "posthoc_diagnosis_summary.json": (
            json.dumps(diagnostic, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
        "posthoc_diagnosis_report_zh.md": report.encode("utf-8"),
    }
    hashes = [f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    write_locked(files, output_dir)

    print("[done] post-hoc overlap-gate diagnosis")
    print("[locked] v1 gate unchanged; D3 training remains disabled")
    print(f"[summary] SkullFix suspects={len(suspect_rows)}/1250")
    print(f"[summary] flagged MUG skulls={len(set(row['mug_skull_id'] for row in suspect_rows))}/125")


if __name__ == "__main__":
    main()
