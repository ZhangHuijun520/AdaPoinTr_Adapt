#!/usr/bin/env python3
"""Apply the preregistered D3 Round-A gates to frozen S0/S1 seed-0 runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
FOLDS = ("A", "B", "C", "D")
VERSION = "mamba-v13-d3-round-a-seed0-gate-analysis-v1"
PROTOCOL = REPO_ROOT / "docs/mamba_v13_d3_round_a_candidate_execution_protocol_v1.json"
PROTOCOL_SHA256 = "f7e91539cec7928689487b2922a8b70ab129df8889d292f72a08ca6872f6afa6"
FINAL_METRICS = ("final_cd_l1_mm", "final_hd95_mm", "final_nsd_at_1mm")
FINITE_METRICS = FINAL_METRICS + ("rim_contact_hd95_mm",)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def resolve(path: str | Path) -> Path:
    result = Path(path)
    if not result.is_absolute():
        result = REPO_ROOT / result
    return result.resolve()


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing non-identical Round-A artifact: {path}")
        print(f"[locked] existing artifact is byte-identical: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def verify_sidecar(path: Path) -> None:
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    if (
        len(fields) < 2
        or Path(fields[1]).name != path.name
        or sha256_file(path) != fields[0].lower()
    ):
        raise RuntimeError(f"SHA256 sidecar mismatch: {path}")


def verify_tree(root: Path) -> None:
    manifest = root / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Hash-tree mismatch: {path}")


def as_float(row: dict, key: str) -> float:
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return float("nan")


def load_completion(path: Path, candidate: str) -> dict:
    verify_sidecar(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    expected_status = {
        "S0": "S0_seed0_frozen_ready_for_S2_feasibility",
        "S1": "S1_seed0_frozen_ready_for_preregistered_gate_analysis",
    }[candidate]
    if not (
        value.get("status") == expected_status
        and value.get("candidate") == candidate
        and value.get("seed") == 0
        and value.get("folds") == list(FOLDS)
        and value.get("development_cases") == 400
        and value.get("holdout_authorized") is False
        and value.get("selection_started") is False
    ):
        raise RuntimeError(f"Invalid {candidate} completion receipt")
    return value


def load_candidate(completion: dict, candidate: str) -> tuple[dict, dict]:
    rows = {}
    efficiency = {}
    for fold in FOLDS:
        record_path = resolve(completion["run_records"][fold]["path"])
        verify_sidecar(record_path)
        if sha256_file(record_path) != completion["run_records"][fold]["sha256"]:
            raise RuntimeError(f"{candidate} fold {fold} record hash mismatch")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if not (
            record.get("record_version") == "mamba-v13-d3-run-record-v1"
            and record.get("status") == "frozen_complete_development_fold"
            and record.get("candidate") == candidate
            and record.get("fold") == fold
            and record.get("seed") == 0
            and record.get("dev_cases") == 100
            and record.get("holdout_inference_consumed") is False
            and record.get("holdout_metrics_consumed") is False
            and record.get("holdout_visual_review_consumed") is False
            and record.get("selection_started") is False
        ):
            raise RuntimeError(f"Invalid {candidate} fold {fold} run record")
        for name, artifact in record["artifacts"].items():
            artifact_path = resolve(artifact["path"])
            if not artifact_path.is_file() or sha256_file(artifact_path) != artifact["sha256"]:
                raise RuntimeError(f"{candidate} fold {fold} artifact mismatch: {name}")
        metrics_path = resolve(record["artifacts"]["metrics_csv"]["path"])
        with metrics_path.open(newline="", encoding="utf-8") as handle:
            fold_rows = list(csv.DictReader(handle))
        if len(fold_rows) != 100:
            raise RuntimeError(f"{candidate} fold {fold} does not contain 100 cases")
        for row in fold_rows:
            key = (row["case_id"], fold)
            if key in rows:
                raise RuntimeError(f"Duplicate {candidate} case/fold: {key}")
            rows[key] = row
        efficiency[fold] = completion["fold_efficiency"][fold]
    case_ids = [key[0] for key in rows]
    if len(rows) != 400 or len(case_ids) != len(set(case_ids)):
        raise RuntimeError(f"{candidate} does not contain 400 unique development cases")
    return rows, efficiency


def validate_protocol() -> dict:
    if sha256_file(PROTOCOL) != PROTOCOL_SHA256:
        raise RuntimeError("The preregistered Round-A protocol hash has drifted")
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    gates = protocol["round_a_gates"]
    aggregation = protocol["selection_aggregation"]
    selection = protocol["selection"]
    if not (
        protocol.get("protocol_id") == "mamba-v13-d3-round-a-candidate-execution-v1"
        and gates == {
            "complete_case_records": True,
            "all_required_metrics_finite": True,
            "disaster": "nonfinite_or_rim_contact_hd95_mm_gt_50",
            "disaster_count_max": "same_round_S0",
            "dense_zero_contact_at_2mm": 0,
            "S2_coarse_zero_support_at_2mm": 0,
            "rim_contact_hd95_p95_max": "same_round_S0",
            "final_cd_l1_mm_delta_max": 0.1,
            "final_hd95_mm_delta_max": 0.5,
            "final_nsd_at_1mm_delta_min": -0.01,
            "parameter_ratio_max": 1.02,
            "latency_ratio_max": 1.1,
            "peak_gpu_memory_ratio_max": 1.1,
        }
        and aggregation["pairing"] == "candidate_to_S0_by_case_id_and_fold"
        and aggregation["pooled_percentile_method"] == "numpy_percentile_linear"
        and aggregation["final_metric_delta"]
        == "mean_of_400_paired_candidate_minus_S0_case_deltas"
        and selection["no_experimental_passes"]
        == "freeze_negative_and_stop_loss_query_micro_tuning"
    ):
        raise RuntimeError("The preregistered Round-A gate protocol has drifted")
    return protocol


def metric_summary(rows: dict) -> dict:
    finite = {
        key: sum(math.isfinite(as_float(row, key)) for row in rows.values())
        for key in FINITE_METRICS
    }
    disasters = sum(
        not all(math.isfinite(as_float(row, key)) for key in FINITE_METRICS)
        or as_float(row, "rim_contact_hd95_mm") > 50.0
        for row in rows.values()
    )
    dense_zero = sum(as_float(row, "rim_predicted_rim_points") <= 0 for row in rows.values())
    coarse_zero = sum(as_float(row, "coarse_predicted_rim_points") <= 0 for row in rows.values())
    rim = np.asarray([as_float(row, "rim_contact_hd95_mm") for row in rows.values()])
    return {
        "finite_counts": finite,
        "all_required_metrics_finite": all(value == 400 for value in finite.values()),
        "disaster_count": int(disasters),
        "dense_zero_contact_at_2mm_count": int(dense_zero),
        "coarse_zero_support_at_2mm_count": int(coarse_zero),
        "rim_contact_hd95_p95_mm_linear": (
            float(np.percentile(rim, 95, method="linear"))
            if np.isfinite(rim).all()
            else None
        ),
    }


def csv_bytes(rows: list[dict]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s0_completion", type=Path, required=True)
    parser.add_argument("--s1_completion", type=Path, required=True)
    parser.add_argument("--s2_negative_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = validate_protocol()
    s0_path = args.s0_completion.resolve()
    s1_path = args.s1_completion.resolve()
    s2_dir = args.s2_negative_dir.resolve()
    output = args.output_dir.resolve()
    s0_completion = load_completion(s0_path, "S0")
    s1_completion = load_completion(s1_path, "S1")
    verify_tree(s2_dir)
    s2_path = s2_dir / "negative_result_receipt.json"
    s2 = json.loads(s2_path.read_text(encoding="utf-8"))
    if not (
        s2.get("status") == "frozen_negative_high_hit_rate_failed_all_case_safety_gate"
        and s2.get("S2_full_training_authorized") is False
        and s2.get("holdout_accessed") is False
        and s2.get("selection_started") is False
    ):
        raise RuntimeError("S2 negative-result lineage is invalid")

    s0_rows, s0_efficiency = load_candidate(s0_completion, "S0")
    s1_rows, s1_efficiency = load_candidate(s1_completion, "S1")
    if set(s0_rows) != set(s1_rows):
        raise RuntimeError("S0/S1 case_id+fold universes differ")

    paired = []
    deltas = {key: [] for key in FINAL_METRICS}
    for case_id, fold in sorted(s0_rows, key=lambda item: (item[1], item[0])):
        left = s0_rows[(case_id, fold)]
        right = s1_rows[(case_id, fold)]
        row = {"case_id": case_id, "fold": fold}
        for key in FINITE_METRICS:
            s0_value = as_float(left, key)
            s1_value = as_float(right, key)
            row[f"S0_{key}"] = s0_value
            row[f"S1_{key}"] = s1_value
            if key in FINAL_METRICS:
                delta = s1_value - s0_value
                row[f"delta_{key}"] = delta
                deltas[key].append(delta)
        for key in ("rim_predicted_rim_points", "coarse_predicted_rim_points"):
            row[f"S0_{key}"] = as_float(left, key)
            row[f"S1_{key}"] = as_float(right, key)
        paired.append(row)

    s0_summary = metric_summary(s0_rows)
    s1_summary = metric_summary(s1_rows)
    for completion, key, recalculated, candidate in (
        (s0_completion, "reference_summary", s0_summary, "S0"),
        (s1_completion, "summary", s1_summary, "S1"),
    ):
        frozen = completion[key]
        for field in (
            "disaster_count",
            "dense_zero_contact_at_2mm_count",
            "coarse_zero_support_at_2mm_count",
        ):
            if int(frozen[field]) != recalculated[field]:
                raise RuntimeError(f"{candidate} completion summary mismatch: {field}")
    delta_means = {
        key: float(np.mean(np.asarray(values, dtype=np.float64)))
        for key, values in deltas.items()
    }
    max_ratios = {"parameter": 0.0, "latency": 0.0, "peak_gpu_memory": 0.0}
    fold_ratios = {}
    for fold in FOLDS:
        ratios = {
            "parameter": float(s1_efficiency[fold]["parameter_count_total"])
            / float(s0_efficiency[fold]["parameter_count_total"]),
            "latency": float(s1_efficiency[fold]["latency_ms_median"])
            / float(s0_efficiency[fold]["latency_ms_median"]),
            "peak_gpu_memory": float(s1_efficiency[fold]["peak_gpu_memory_bytes"])
            / float(s0_efficiency[fold]["peak_gpu_memory_bytes"]),
        }
        fold_ratios[fold] = ratios
        for key, value in ratios.items():
            max_ratios[key] = max(max_ratios[key], value)

    p95_comparable = (
        s0_summary["rim_contact_hd95_p95_mm_linear"] is not None
        and s1_summary["rim_contact_hd95_p95_mm_linear"] is not None
    )
    gates = {
        "complete_case_records": True,
        "case_pairing_exact": True,
        "all_required_metrics_finite": s1_summary["all_required_metrics_finite"],
        "disaster_count_not_above_S0":
            s1_summary["disaster_count"] <= s0_summary["disaster_count"],
        "dense_zero_contact_at_2mm_equals_zero":
            s1_summary["dense_zero_contact_at_2mm_count"] == 0,
        "rim_contact_hd95_p95_not_above_S0": (
            p95_comparable
            and s1_summary["rim_contact_hd95_p95_mm_linear"]
            <= s0_summary["rim_contact_hd95_p95_mm_linear"]
        ),
        "final_cd_l1_noninferior": delta_means["final_cd_l1_mm"] <= 0.1,
        "final_hd95_noninferior": delta_means["final_hd95_mm"] <= 0.5,
        "final_nsd_at_1mm_noninferior": delta_means["final_nsd_at_1mm"] >= -0.01,
        "parameter_ratio_within_limit": max_ratios["parameter"] <= 1.02,
        "latency_ratio_within_limit": max_ratios["latency"] <= 1.1,
        "peak_gpu_memory_ratio_within_limit": max_ratios["peak_gpu_memory"] <= 1.1,
    }
    s1_passed = all(gates.values())
    if s1_passed:
        status = "round_a_S1_passed_advance_S0_and_S1_to_seed1"
        next_step = "preregister_and_authorize_S0_S1_seed1"
    else:
        status = "round_a_frozen_negative_no_experimental_candidate_passed"
        next_step = "stop_D3_loss_query_micro_tuning_and_archive_negative_result"

    paired_path = output / "s1_vs_s0_paired_metrics.csv"
    receipt_path = output / "round_a_selection_receipt.json"
    report_path = output / "round_a_gate_report_zh.md"
    paired_payload = csv_bytes(paired)
    report = f"""# Mamba v1.3 D3 Round-A seed-0 门控结果

> 本分析机械执行训练前已冻结的 Round-A 规则；未修改候选、阈值或配对方法，未访问 locked holdout。

## 冻结结论

- S1 是否通过全部硬门控：`{s1_passed}`
- S2 是否具备完整训练资格：`False`
- Round-A 状态：`{status}`
- 下一步：`{next_step}`

## 核心计数

| 指标 | S0 | S1 | 门控 |
|---|---:|---:|---|
| 灾难病例 | {s0_summary['disaster_count']} | {s1_summary['disaster_count']} | S1 <= S0：`{gates['disaster_count_not_above_S0']}` |
| dense 2 mm zero-contact | {s0_summary['dense_zero_contact_at_2mm_count']} | {s1_summary['dense_zero_contact_at_2mm_count']} | S1 = 0：`{gates['dense_zero_contact_at_2mm_equals_zero']}` |
| coarse 2 mm zero-support | {s0_summary['coarse_zero_support_at_2mm_count']} | {s1_summary['coarse_zero_support_at_2mm_count']} | S1 不以此项门控 |

S1 虽然降低了灾难数和 zero-contact 数，但仍有 `{s1_summary['dense_zero_contact_at_2mm_count']}` 个 dense zero-contact 病例，因此未通过预注册硬门控。非有限 rim 指标也使完整有限性门控失败，P95 不得改用有限子集事后重算。

## Final 配对均值差（S1 - S0）

- final CD-L1：`{delta_means['final_cd_l1_mm']}` mm，门控 `{gates['final_cd_l1_noninferior']}`
- final HD95：`{delta_means['final_hd95_mm']}` mm，门控 `{gates['final_hd95_noninferior']}`
- final NSD@1 mm：`{delta_means['final_nsd_at_1mm']}`，门控 `{gates['final_nsd_at_1mm_noninferior']}`

## 边界

- S1 不进入 seed-1；S2 已在 head-only feasibility 阶段冻结为负结果。
- 不运行 locked holdout，不根据本结果调整 loss 权重、2 mm 阈值或 query 规则。
- 后续只允许冻结归档和撰写负结果报告；新方法必须建立新的独立协议与数据边界。
""".encode("utf-8")
    receipt = {
        "analysis_version": VERSION,
        "status": status,
        "protocol": {"path": portable(PROTOCOL), "sha256": sha256_file(PROTOCOL)},
        "implementation_timing": "implemented_after_training_as_mechanical_execution_of_preexisting_rules",
        "case_universe": 400,
        "pairing": "case_id_plus_fold_exact",
        "S0": s0_summary,
        "S1": s1_summary,
        "S1_minus_S0_final_metric_mean_deltas": delta_means,
        "fold_efficiency_ratios": fold_ratios,
        "maximum_efficiency_ratios": max_ratios,
        "S1_gates": gates,
        "S1_passed_all_gates": s1_passed,
        "S2_full_training_eligible": False,
        "S2_negative_receipt": {"path": portable(s2_path), "sha256": sha256_file(s2_path)},
        "lineage": {
            "S0_completion": {"path": portable(s0_path), "sha256": sha256_file(s0_path)},
            "S1_completion": {"path": portable(s1_path), "sha256": sha256_file(s1_path)},
        },
        "artifacts": {
            "paired_metrics": {"path": paired_path.name, "sha256": hashlib.sha256(paired_payload).hexdigest()},
            "report": {"path": report_path.name, "sha256": hashlib.sha256(report).hexdigest()},
        },
        "round_a_gate_selection_completed": True,
        "seed1_authorized": s1_passed,
        "holdout_accessed": False,
        "holdout_authorized": False,
        "official_test_accessed": False,
        "candidate_or_rule_revision_authorized": False,
        "next_step": next_step,
    }
    receipt_payload = canonical_json(receipt)
    write_identical_or_new(paired_path, paired_payload)
    write_identical_or_new(report_path, report)
    write_identical_or_new(receipt_path, receipt_payload)
    manifest_lines = []
    for path in (paired_path, report_path, receipt_path):
        manifest_lines.append(f"{sha256_file(path)}  {path.name}\n")
    manifest_payload = "".join(manifest_lines).encode("ascii")
    manifest_path = output / "files.sha256"
    write_identical_or_new(manifest_path, manifest_payload)
    write_identical_or_new(
        output / "files.sha256.sha256",
        f"{hashlib.sha256(manifest_payload).hexdigest()}  files.sha256\n".encode("ascii"),
    )
    print(f"[saved] D3 Round-A gate receipt: {receipt_path}")
    print(
        f"[gate] S1 passed={s1_passed} disasters={s1_summary['disaster_count']}/"
        f"{s0_summary['disaster_count']} dense_zero="
        f"{s1_summary['dense_zero_contact_at_2mm_count']}"
    )
    print("[negative] no experimental candidate advances to seed-1" if not s1_passed else "[advance] S1 and S0 may enter seed-1")
    print("[locked] holdout=false official_test=false rule_revision=false")


if __name__ == "__main__":
    main()
