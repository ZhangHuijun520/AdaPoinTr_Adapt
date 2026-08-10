#!/usr/bin/env python
"""Analyze D2.2 contact support without reopening candidate selection."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np


BANDS = (0.5, 1.0, 2.0, 3.0, 4.0, 5.0)
CANDIDATES = ("R0", "R1", "R2")
STAGES = ("coarse", "dense")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per_case", type=Path, required=True)
    parser.add_argument("--replay_summary", type=Path, required=True)
    parser.add_argument("--negative_receipt", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sidecar(path):
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    actual = sha256_file(path)
    if len(fields) < 2 or fields[0] != actual:
        raise RuntimeError(f"SHA256 mismatch: {path}")
    return actual


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_locked(path, rows):
    if not rows:
        raise RuntimeError(f"No rows for {path}")
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=list(rows[0]), lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    encoded = buffer.getvalue().encode("utf-8")
    if path.exists() and path.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite non-identical output: {path}")
    path.write_bytes(encoded)


def write_text_locked(path, text):
    encoded = text.encode("utf-8")
    if path.exists() and path.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite non-identical output: {path}")
    path.write_bytes(encoded)


def band_key(value):
    return f"{value:g}mm".replace(".", "p")


def as_int(row, key):
    return int(float(row[key]))


def finite_float(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def support_count(row, stage, band):
    return as_int(row, f"{stage}_predicted_rim_points_at_{band_key(band)}")


def summarize_bands(rows):
    output = []
    for candidate in CANDIDATES:
        candidate_rows = [row for row in rows if row["candidate"] == candidate]
        for stage in STAGES:
            for band in BANDS:
                counts = np.asarray(
                    [support_count(row, stage, band) for row in candidate_rows],
                    dtype=np.float64,
                )
                zero = int(np.count_nonzero(counts == 0))
                output.append({
                    "candidate": candidate,
                    "stage": stage,
                    "band_mm": band,
                    "cases": len(candidate_rows),
                    "zero_contact_cases": zero,
                    "contact_support_rate": float(1.0 - zero / len(counts)),
                    "support_points_mean": float(counts.mean()),
                    "support_points_p05": float(np.percentile(counts, 5)),
                    "support_points_median": float(np.median(counts)),
                    "support_points_p95": float(np.percentile(counts, 95)),
                })
    return output


def summarize_defects(rows):
    output = []
    defects = sorted({row["defect_type"] for row in rows})
    for candidate in CANDIDATES:
        for defect in defects:
            selected = [
                row for row in rows
                if row["candidate"] == candidate
                and row["defect_type"] == defect
            ]
            for stage in STAGES:
                counts = [support_count(row, stage, 2.0) for row in selected]
                output.append({
                    "candidate": candidate,
                    "defect_type": defect,
                    "stage": stage,
                    "band_mm": 2.0,
                    "cases": len(selected),
                    "zero_contact_cases": sum(count == 0 for count in counts),
                })
    return output


def paired_transitions(row_maps):
    output = []
    reference = row_maps["R0"]
    for candidate in ("R1", "R2"):
        comparison = row_maps[candidate]
        for stage in STAGES:
            for band in BANDS:
                counts = Counter()
                for case_id, reference_row in reference.items():
                    reference_support = support_count(
                        reference_row, stage, band
                    ) > 0
                    candidate_support = support_count(
                        comparison[case_id], stage, band
                    ) > 0
                    if not reference_support and candidate_support:
                        counts["resolved"] += 1
                    elif reference_support and not candidate_support:
                        counts["induced"] += 1
                    elif not reference_support and not candidate_support:
                        counts["persistent_zero"] += 1
                    else:
                        counts["stable_supported"] += 1
                output.append({
                    "candidate": candidate,
                    "reference": "R0",
                    "stage": stage,
                    "band_mm": band,
                    "resolved": counts["resolved"],
                    "induced": counts["induced"],
                    "persistent_zero": counts["persistent_zero"],
                    "stable_supported": counts["stable_supported"],
                    "net_zero_contact_change": (
                        counts["induced"] - counts["resolved"]
                    ),
                })
    return output


def zero_case_matrix(row_maps):
    union = sorted({
        case_id
        for candidate in CANDIDATES
        for case_id, row in row_maps[candidate].items()
        if support_count(row, "dense", 2.0) == 0
    })
    output = []
    for case_id in union:
        for candidate in CANDIDATES:
            row = row_maps[candidate][case_id]
            item = {
                "case_id": case_id,
                "skull_id": row["skull_id"],
                "defect_type": row["defect_type"],
                "fold": row["fold"],
                "candidate": candidate,
                "dense_zero_at_2mm": int(
                    support_count(row, "dense", 2.0) == 0
                ),
                "coarse_zero_at_2mm": int(
                    support_count(row, "coarse", 2.0) == 0
                ),
                "dense_recovery_band_mm": row["dense_recovery_band_mm"],
                "coarse_recovery_band_mm": row["coarse_recovery_band_mm"],
                "dense_nearest_defective_mm": row[
                    "dense_defective_to_stage_min_mm"
                ],
                "coarse_nearest_defective_mm": row[
                    "coarse_defective_to_stage_min_mm"
                ],
                "dense_gt_rim2_to_stage_p95_mm": row[
                    "dense_gt_rim2_to_stage_p95_mm"
                ],
                "coarse_gt_rim2_to_stage_p95_mm": row[
                    "coarse_gt_rim2_to_stage_p95_mm"
                ],
            }
            for band in BANDS:
                key = band_key(band)
                item[f"dense_points_at_{key}"] = support_count(
                    row, "dense", band
                )
                item[f"coarse_points_at_{key}"] = support_count(
                    row, "coarse", band
                )
            output.append(item)
    return output


def primary_transition(transitions, candidate, stage="dense"):
    return next(
        row for row in transitions
        if row["candidate"] == candidate
        and row["stage"] == stage
        and float(row["band_mm"]) == 2.0
    )


def main():
    args = parse_args()
    per_case_hash = verify_sidecar(args.per_case)
    replay_hash = verify_sidecar(args.replay_summary)
    negative_hash = verify_sidecar(args.negative_receipt)
    replay = json.loads(args.replay_summary.read_text(encoding="utf-8"))
    negative = json.loads(args.negative_receipt.read_text(encoding="utf-8"))
    required = {
        "post_hoc": True,
        "observation_only": True,
        "selection_inert": True,
        "winner": None,
        "round_b_allowed": False,
        "protected_splits_accessed": False,
    }
    if any(replay.get(key) != value for key, value in required.items()):
        raise RuntimeError("Replay integrity flags are invalid")
    if negative.get("round_b_allowed") is not False:
        raise RuntimeError("Negative result no longer blocks Round B")
    rows = read_csv(args.per_case)
    if len(rows) != 1260:
        raise RuntimeError(f"Expected 1260 replay rows, found {len(rows)}")
    row_maps = {
        candidate: {
            row["case_id"]: row for row in rows
            if row["candidate"] == candidate
        }
        for candidate in CANDIDATES
    }
    reference_ids = set(row_maps["R0"])
    if len(reference_ids) != 420 or any(
        set(row_maps[candidate]) != reference_ids for candidate in CANDIDATES
    ):
        raise RuntimeError("Candidate replay case sets are not paired 420-case sets")

    bands = summarize_bands(rows)
    defects = summarize_defects(rows)
    transitions = paired_transitions(row_maps)
    zero_matrix = zero_case_matrix(row_maps)
    expected_zero = negative["nonfinite_zero_contact_cases"]
    for candidate in CANDIDATES:
        actual = sorted(
            case_id for case_id, row in row_maps[candidate].items()
            if support_count(row, "dense", 2.0) == 0
        )
        if actual != expected_zero[candidate]:
            raise RuntimeError(f"{candidate}: frozen zero-contact set mismatch")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    band_path = args.output_dir / "contact_support_band_summary.csv"
    defect_path = args.output_dir / "contact_support_by_defect_2mm.csv"
    transition_path = args.output_dir / "contact_support_transitions.csv"
    zero_path = args.output_dir / "zero_contact_case_matrix.csv"
    for path, output_rows in (
        (band_path, bands),
        (defect_path, defects),
        (transition_path, transitions),
        (zero_path, zero_matrix),
    ):
        write_csv_locked(path, output_rows)

    primary = {
        candidate: primary_transition(transitions, candidate)
        for candidate in ("R1", "R2")
    }
    zero_recovery = {}
    for candidate in CANDIDATES:
        selected = [
            row_maps[candidate][case_id]
            for case_id in expected_zero[candidate]
        ]
        zero_recovery[candidate] = {
            "cases": len(selected),
            "dense_recovery_band_mm": [
                finite_float(row["dense_recovery_band_mm"]) for row in selected
            ],
            "coarse_support_at_2mm_cases": sum(
                support_count(row, "coarse", 2.0) > 0 for row in selected
            ),
        }
    summary = {
        "analysis_version": "mamba-v12-d22-contact-support-posthoc-v1",
        "post_hoc": True,
        "observation_only": True,
        "selection_inert": True,
        "winner": None,
        "round_b_allowed": False,
        "protected_splits_accessed": False,
        "confirmation20_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
        "records": len(rows),
        "unique_cases": len(reference_ids),
        "dense_2mm_zero_contact_cases": expected_zero,
        "dense_2mm_transitions_vs_R0": primary,
        "frozen_zero_case_recovery": zero_recovery,
        "input_sha256": {
            str(args.per_case): per_case_hash,
            str(args.replay_summary): replay_hash,
            str(args.negative_receipt): negative_hash,
        },
        "outputs": {
            "band_summary": band_path.name,
            "defect_summary": defect_path.name,
            "transitions": transition_path.name,
            "zero_case_matrix": zero_path.name,
        },
    }
    summary_path = args.output_dir / "contact_support_posthoc_summary.json"
    write_text_locked(
        summary_path,
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )

    report = [
        "# Mamba v1.2 D2.2 contact-support replay 事后诊断\n",
        "> 本报告是 observation-only、selection-inert 的 post-hoc 机制分析。"
        "D2.2 winner 仍为 null，Round B 仍被禁止。\n",
        "## 完整性\n",
        "- 3 个候选 × 420 个配对病例，共 1260 条 replay 记录；",
        "- coarse 与 dense 均按 0.5/1/2/3/4/5 mm 固定 band 统计；",
        "- dense 2 mm 支撑点数已逐病例严格重放冻结评估；",
        "- 未访问 confirmation20、旧 monitor 或 official test。\n",
        "## 主定义 2 mm 下的 dense 支撑转移\n",
        "| Candidate | Resolved | Induced | Persistent zero | Stable supported | Net zero change |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for candidate in ("R1", "R2"):
        item = primary[candidate]
        report.append(
            f"| {candidate} | {item['resolved']} | {item['induced']} | "
            f"{item['persistent_zero']} | {item['stable_supported']} | "
            f"{item['net_zero_contact_change']} |"
        )
    report.extend([
        "\n## 冻结零接触病例恢复\n",
        "| Candidate | Zero cases | Coarse support at 2 mm | Dense recovery bands (mm) |",
        "|---|---:|---:|---|",
    ])
    for candidate in CANDIDATES:
        item = zero_recovery[candidate]
        report.append(
            f"| {candidate} | {item['cases']} | "
            f"{item['coarse_support_at_2mm_cases']} | "
            f"`{item['dense_recovery_band_mm']}` |"
        )
    report.extend([
        "\n## 解释边界\n",
        "该 replay 可以判断零接触是接近 2 mm 阈值的边界事件、coarse 阶段"
        "已经缺失，还是 dense refinement 造成的支撑丢失。它不能用于放宽"
        "nonfinite 门控、改变主 band、选择 R1/R2 或恢复 D2.2 Round B。",
    ])
    report_path = args.output_dir / "contact_support_posthoc_report_zh.md"
    write_text_locked(report_path, "\n".join(report).rstrip() + "\n")

    output_paths = [
        band_path, defect_path, transition_path, zero_path,
        summary_path, report_path,
    ]
    for path in output_paths:
        Path(str(path) + ".sha256").write_text(
            f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
        )
    manifest_path = args.output_dir / "files.sha256"
    manifest_text = "".join(
        f"{sha256_file(path)}  {path.name}\n" for path in output_paths
    )
    write_text_locked(manifest_path, manifest_text)
    Path(str(manifest_path) + ".sha256").write_text(
        f"{sha256_file(manifest_path)}  {manifest_path.name}\n",
        encoding="ascii",
    )
    print(f"[saved] {report_path}")
    print(f"[saved] {summary_path}")
    print("[done] D2.2 contact-support post-hoc analysis")
    print("[locked] selection unchanged; Round B remains forbidden")


if __name__ == "__main__":
    main()
