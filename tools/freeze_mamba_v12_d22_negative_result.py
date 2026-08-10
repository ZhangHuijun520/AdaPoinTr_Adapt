#!/usr/bin/env python
"""Freeze the blocked D2.2 Round-A outcome before post-hoc replay."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


CORE_METRICS = (
    "implant_cd_l1_mm",
    "implant_hd95_mm",
    "implant_nsd_at_1mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
    "coarse_gt_rim_to_pred_p95_mm",
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument(
        "--verify_all_inputs",
        action="store_true",
        help="Rehash every input captured by the frozen selection receipt.",
    )
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


def verify_sidecar(path):
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    if len(fields) < 2 or Path(fields[1]).name != Path(path).name:
        raise RuntimeError(f"Invalid SHA256 sidecar: {sidecar}")
    return verify(path, fields[0])


def finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_locked(path, rows, fieldnames):
    lines = []
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    encoded = buffer.getvalue().encode("utf-8")
    if path.exists() and path.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite non-identical file: {path}")
    path.write_bytes(encoded)
    lines.append(f"{sha256_file(path)}  {path.name}\n")
    Path(str(path) + ".sha256").write_text("".join(lines), encoding="ascii")


def write_text_locked(path, text):
    encoded = text.encode("utf-8")
    if path.exists() and path.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite non-identical file: {path}")
    path.write_bytes(encoded)
    Path(str(path) + ".sha256").write_text(
        f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
    )


def find_nonfinite_cases(record_paths):
    rows = []
    case_sets = {candidate: set() for candidate in ("R0", "R1", "R2")}
    run_manifest = []
    for record_path in record_paths:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        candidate = record["candidate"]
        fold = record["fold"]
        metrics_artifact = record["artifacts"]["metrics_csv"]
        metrics_path = Path(metrics_artifact["path"])
        verify(metrics_path, metrics_artifact["sha256"])
        run_manifest.append({
            "candidate": candidate,
            "fold": fold,
            "seed": int(record["seed"]),
            "run_record": str(record_path),
            "run_record_sha256": sha256_file(record_path),
            "metrics_csv": str(metrics_path),
            "metrics_csv_sha256": metrics_artifact["sha256"],
        })
        for metric_row in read_csv(metrics_path):
            invalid = [
                metric for metric in CORE_METRICS
                if not finite(metric_row.get(metric))
            ]
            if not invalid:
                continue
            case_id = str(metric_row["case_id"])
            case_sets[candidate].add(case_id)
            rows.append({
                "candidate": candidate,
                "fold": fold,
                "case_id": case_id,
                "skull_id": metric_row.get("skull_id", ""),
                "defect_type": metric_row.get("defect_type", ""),
                "predicted_rim_points": metric_row.get(
                    "rim_predicted_rim_points", ""
                ),
                "nonfinite_metrics": ";".join(invalid),
            })
    rows.sort(key=lambda row: (row["candidate"], row["fold"], row["case_id"]))
    run_manifest.sort(key=lambda row: (row["candidate"], row["fold"]))
    return rows, case_sets, run_manifest


def metric_table(selection):
    lines = [
        "| Candidate | Disasters | Catastrophic skulls | Nonfinite | "
        "Implant HD95 | Rim HD95 P95 | GT-rim->coarse P95 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for candidate in ("R0", "R1", "R2"):
        item = selection["summaries"][candidate]
        means = item["means"]
        lines.append(
            f"| {candidate} | {item['disaster_count']}/420 | "
            f"{item['catastrophic_skull_count']} | "
            f"{item['nonfinite_case_count']} | "
            f"{means['implant_hd95_mm']:.6f} | "
            f"{item['rim_hd95_p95']:.6f} | "
            f"{means['coarse_gt_rim_to_pred_p95_mm']:.6f} |"
        )
    return lines


def main():
    args = parse_args()
    selection_hash = verify_sidecar(args.selection)
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    protocol_hash = verify(args.protocol, selection["protocol_sha256"])
    amendment_hash = verify(
        args.amendment, selection["implementation_amendment_sha256"]
    )

    if selection.get("winner") is not None:
        raise RuntimeError("D2.2 negative freeze requires winner=None")
    if selection.get("round_b_allowed") is not False:
        raise RuntimeError("D2.2 negative freeze requires Round B to be blocked")
    if selection.get("protected_splits_accessed") is not False:
        raise RuntimeError("Protected split access was reported")
    if args.verify_all_inputs:
        for input_path, expected in selection["input_sha256"].items():
            verify(Path(input_path), expected)

    record_paths = sorted(args.records_root.glob("*/run_record.json"))
    if len(record_paths) != 12:
        raise RuntimeError(f"Expected 12 D2.2 run records, found {len(record_paths)}")
    nonfinite_rows, case_sets, run_manifest = find_nonfinite_cases(record_paths)
    if len(run_manifest) != 12:
        raise RuntimeError("Incomplete D2.2 run manifest")

    expected_candidates = {"R0", "R1", "R2"}
    if {row["candidate"] for row in run_manifest} != expected_candidates:
        raise RuntimeError("Unexpected D2.2 candidate set")
    for candidate in expected_candidates:
        if sum(row["candidate"] == candidate for row in run_manifest) != 4:
            raise RuntimeError(f"{candidate}: expected four fold records")
        expected_count = selection["summaries"][candidate][
            "nonfinite_case_count"
        ]
        if len(case_sets[candidate]) != expected_count:
            raise RuntimeError(f"{candidate}: nonfinite count mismatch")
        if any(
            float(row["predicted_rim_points"]) != 0.0
            for row in nonfinite_rows if row["candidate"] == candidate
        ):
            raise RuntimeError(
                f"{candidate}: nonfinite failure was not zero rim support"
            )

    for candidate in ("R1", "R2"):
        failed_gates = sorted(
            gate for gate, passed
            in selection["summaries"][candidate]["gates"].items()
            if not passed
        )
        if failed_gates != ["nonfinite"]:
            raise RuntimeError(
                f"{candidate}: unexpected failed gates {failed_gates}"
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    nonfinite_path = args.output_dir / "nonfinite_zero_contact_cases.csv"
    write_csv_locked(
        nonfinite_path,
        nonfinite_rows,
        (
            "candidate", "fold", "case_id", "skull_id", "defect_type",
            "predicted_rim_points", "nonfinite_metrics",
        ),
    )
    run_manifest_path = args.output_dir / "run_records_manifest.csv"
    write_csv_locked(
        run_manifest_path,
        run_manifest,
        (
            "candidate", "fold", "seed", "run_record",
            "run_record_sha256", "metrics_csv", "metrics_csv_sha256",
        ),
    )

    transitions = {}
    for candidate in ("R1", "R2"):
        transitions[candidate] = {
            "persistent_from_R0": sorted(case_sets["R0"] & case_sets[candidate]),
            "resolved_from_R0": sorted(case_sets["R0"] - case_sets[candidate]),
            "newly_induced": sorted(case_sets[candidate] - case_sets["R0"]),
        }
    receipt = {
        "freeze_version": "mamba-v12-d22-negative-result-freeze-v1",
        "status": "negative_with_positive_mechanism_signal_but_safety_gate_failed",
        "selection_sha256": selection_hash,
        "protocol_sha256": protocol_hash,
        "implementation_amendment_sha256": amendment_hash,
        "run_records": 12,
        "case_records_per_candidate": 420,
        "winner": None,
        "round_b_allowed": False,
        "failed_gate_by_candidate": {"R1": ["nonfinite"], "R2": ["nonfinite"]},
        "nonfinite_zero_contact_cases": {
            candidate: sorted(case_sets[candidate])
            for candidate in ("R0", "R1", "R2")
        },
        "zero_contact_transitions": transitions,
        "protected_splits_accessed": False,
        "confirmation20_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
        "post_hoc_replay_may_change_selection": False,
        "selection_locked": True,
    }
    receipt_path = args.output_dir / "negative_result_receipt.json"
    write_text_locked(
        receipt_path,
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )

    report = [
        "# Mamba v1.2 D2.2 Round A 冻结负结果\n",
        "> 状态：有积极机制信号，但未通过预注册安全门控。该结果已冻结，"
        "不得通过 post-hoc replay 改写候选资格或解锁 Round B。\n",
        "## 冻结判定\n",
        "- 12/12 个 Round-A 运行及其输入哈希已纳入冻结凭据。",
        "- `winner = null`，`round_b_allowed = false`。",
        "- R1、R2 唯一失败门控均为 `nonfinite`。",
        "- 所有 nonfinite 均由 2 mm 定义下 `predicted_rim_points = 0` 引起；"
        "网络的其余核心几何指标保持有限。",
        "- confirmation20、旧 monitor、official test 均未访问。\n",
        "## Round-A 汇总\n",
        *metric_table(selection),
        "\n## 零接触失败迁移\n",
        f"- R0：`{sorted(case_sets['R0'])}`",
        f"- R1：`{sorted(case_sets['R1'])}`",
        f"- R2：`{sorted(case_sets['R2'])}`",
        f"- R1 修复 R0 病例：`{transitions['R1']['resolved_from_R0']}`",
        f"- R1 新诱发病例：`{transitions['R1']['newly_induced']}`",
        f"- R2 修复 R0 病例：`{transitions['R2']['resolved_from_R0']}`",
        f"- R2 新诱发病例：`{transitions['R2']['newly_induced']}`\n",
        "## 解释边界\n",
        "D2.2 改善了灾难数、Implant HD95、Rim HD95 尾部和直接覆盖目标，"
        "但没有建立病例级接触存在性保证。后续 contact-support replay 明确属于"
        "事后机制诊断，只能为新实验提出假设。",
    ]
    report_path = args.output_dir / "negative_result_report_zh.md"
    write_text_locked(report_path, "\n".join(report).rstrip() + "\n")

    manifest_targets = sorted(
        path for path in args.output_dir.iterdir()
        if path.is_file()
        and path.name not in {"files.sha256", "files.sha256.sha256"}
        and not path.name.endswith(".sha256")
    )
    manifest_path = args.output_dir / "files.sha256"
    manifest_text = "".join(
        f"{sha256_file(path)}  {path.name}\n" for path in manifest_targets
    )
    write_text_locked(manifest_path, manifest_text)
    print(f"[saved] frozen D2.2 negative result: {args.output_dir}")
    print("[locked] winner=None; Round B forbidden")
    print("[locked] post-hoc replay is observation-only and selection-inert")


if __name__ == "__main__":
    main()
