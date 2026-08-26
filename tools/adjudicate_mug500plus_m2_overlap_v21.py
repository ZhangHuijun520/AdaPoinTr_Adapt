#!/usr/bin/env python3
"""Adjudicate the frozen MUG500+ overlap-audit v2 tables under v2.1."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from lock_mug500plus_m2_overlap_v21_protocol import (
    PROTOCOL_ID,
    sha256_file,
    validate_frozen_inputs,
    validate_protocol,
    validate_provenance,
)


CALIBRATION_FIELDS = [
    "label",
    "dataset",
    "pair_id",
    "first_case_id",
    "second_case_id",
    "symmetric_cd_l1_normalized",
    "symmetric_hd95_normalized",
]
CANDIDATE_FIELDS = [
    "protected_dataset",
    "mug_skull_id",
    "mug_case_id",
    "protected_skull_id",
    "protected_case_id",
    "descriptor_rank",
    "descriptor_distance",
    "symmetric_cd_l1_normalized",
    "symmetric_hd95_normalized",
    "suspect_near_duplicate",
]
EXACT_HASH_FIELDS = ["sha256", "mug_labels", "protected_labels"]
METRICS = [
    "symmetric_cd_l1_normalized",
    "symmetric_hd95_normalized",
]
DOMAIN_ORDER = ["mug500plus", "skullbreak", "skullfix"]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def csv_bytes(rows: Sequence[Sequence[Any]]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode("utf-8")


def percentile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise RuntimeError("Cannot compute a quantile from an empty group")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def finite_nonnegative(raw: str, label: str) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Invalid numeric value for {label}: {raw!r}") from exc
    if not math.isfinite(value) or value < 0:
        raise RuntimeError(f"Non-finite or negative value for {label}: {raw!r}")
    return value


def read_csv_exact(path: Path, expected_fields: Sequence[str]) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(expected_fields):
            raise RuntimeError(
                f"Unexpected CSV schema for {path.name}: {reader.fieldnames}"
            )
        return list(reader)


def verify_hash_manifest(directory: Path) -> None:
    manifest = directory / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing frozen hash manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise RuntimeError(f"Malformed hash-manifest line: {line!r}")
        expected, raw_name = parts
        name = raw_name.lstrip("*").strip()
        if Path(name).name != name:
            raise RuntimeError(f"Nested or absolute hash-manifest path: {name}")
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen hash mismatch: {path}")


def validate_protocol_lock(lock_dir: Path, v2_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    expected_names = {
        "files.sha256",
        "overlap_audit_protocol_v21.json",
        "protocol_lock_receipt.json",
        "source_provenance_v1.json",
    }
    actual_names = {path.name for path in lock_dir.iterdir() if path.is_file()}
    if actual_names != expected_names:
        raise RuntimeError(
            f"Unexpected v2.1 protocol-lock contents: {sorted(actual_names)}"
        )
    verify_hash_manifest(lock_dir)
    protocol_path = lock_dir / "overlap_audit_protocol_v21.json"
    provenance_path = lock_dir / "source_provenance_v1.json"
    receipt_path = lock_dir / "protocol_lock_receipt.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    validate_provenance(provenance)
    if receipt.get("status") != "protocol_locked_not_adjudicated":
        raise RuntimeError("v2.1 protocol-lock receipt has an unexpected status")
    if receipt.get("adjudication_started") is not False:
        raise RuntimeError("v2.1 protocol lock was already marked as adjudicated")
    if receipt.get("protocol_sha256") != sha256_file(protocol_path):
        raise RuntimeError("v2.1 protocol hash does not match its lock receipt")
    if receipt.get("source_provenance_sha256") != sha256_file(provenance_path):
        raise RuntimeError("Source-provenance hash does not match its lock receipt")
    if (
        sha256_file(provenance_path)
        != protocol["frozen_inputs"]["source_provenance_sha256"]
    ):
        raise RuntimeError("Source provenance does not match the preregistration")
    validate_frozen_inputs(protocol, v2_dir)
    if (
        sha256_file(v2_dir / "files.sha256")
        != protocol["lineage"]["v2"]["files_manifest_sha256"]
    ):
        raise RuntimeError("Frozen v2 files manifest does not match the lineage")
    if receipt.get("source_v2_files_manifest_sha256") != sha256_file(
        v2_dir / "files.sha256"
    ):
        raise RuntimeError("Protocol lock and frozen v2 manifest disagree")
    return protocol, provenance, receipt


def summarize_calibration(
    rows: Sequence[Dict[str, str]], protocol: Dict[str, Any]
) -> Tuple[List[List[Any]], Dict[str, Any]]:
    domains = protocol["source_stratified_calibration"]["domains"]
    allowed = {
        (domain, label)
        for domain in DOMAIN_ORDER
        for label, key in (
            ("positive", "positive_pairs_required"),
            ("negative", "negative_pairs_required"),
        )
        if int(domains[domain][key]) > 0
    }
    groups: Dict[Tuple[str, str], List[Dict[str, str]]] = collections.defaultdict(list)
    seen = set()
    for row in rows:
        key = (row["dataset"], row["label"])
        if key not in allowed:
            raise RuntimeError(f"Unexpected calibration group: {key}")
        identity = (row["dataset"], row["label"], row["pair_id"])
        if identity in seen:
            raise RuntimeError(f"Duplicate calibration pair: {identity}")
        seen.add(identity)
        if not row["first_case_id"] or not row["second_case_id"]:
            raise RuntimeError("Calibration pair contains an empty case identifier")
        if row["first_case_id"] == row["second_case_id"]:
            raise RuntimeError(f"Self-pair in calibration: {identity}")
        for metric in METRICS:
            finite_nonnegative(row[metric], metric)
        groups[key].append(row)

    for domain in DOMAIN_ORDER:
        for label, key in (
            ("positive", "positive_pairs_required"),
            ("negative", "negative_pairs_required"),
        ):
            required = int(domains[domain][key])
            actual = len(groups.get((domain, label), []))
            if actual != required:
                raise RuntimeError(
                    f"Calibration count mismatch for {domain}/{label}: "
                    f"expected {required}, got {actual}"
                )

    output = [[
        "dataset",
        "metric",
        "positive_count",
        "negative_count",
        "positive_q99",
        "negative_q01",
        "separation_applicable",
        "separated",
        "decision_rule",
    ]]
    summary: Dict[str, Any] = {}
    for domain in DOMAIN_ORDER:
        positive = groups.get((domain, "positive"), [])
        negative = groups[(domain, "negative")]
        metric_results = {}
        for metric in METRICS:
            positive_q99 = (
                percentile((row[metric] for row in positive), 0.99)
                if positive
                else None
            )
            negative_q01 = percentile((row[metric] for row in negative), 0.01)
            applicable = positive_q99 is not None
            separated = applicable and positive_q99 < negative_q01
            metric_results[metric] = {
                "positive_q99": positive_q99,
                "negative_q01": negative_q01,
                "separation_applicable": applicable,
                "separated": separated if applicable else None,
            }
            output.append([
                domain,
                metric,
                len(positive),
                len(negative),
                "" if positive_q99 is None else positive_q99,
                negative_q01,
                int(applicable),
                "" if not applicable else int(separated),
                (
                    "positive_q99_lt_negative_q01"
                    if applicable
                    else "not_applicable_no_positive_pairs"
                ),
            ])
        summary[domain] = {
            "positive_pairs": len(positive),
            "negative_pairs": len(negative),
            "metrics": metric_results,
            "domain_separated": (
                all(item["separated"] for item in metric_results.values())
                if positive
                else None
            ),
        }
    return output, summary


def adjudicate_geometry(
    rows: Sequence[Dict[str, str]],
    protocol: Dict[str, Any],
    cd_limit: float,
    hd95_limit: float,
) -> Tuple[List[List[Any]], Dict[str, Any]]:
    geometry = protocol["geometry_adjudication"]
    expected_total = int(geometry["expected_candidate_pairs"])
    expected_per_dataset = int(geometry["expected_pairs_per_protected_dataset"])
    expected_ranks = {int(value) for value in geometry["expected_descriptor_ranks"]}
    if len(rows) != expected_total:
        raise RuntimeError(
            f"Candidate count mismatch: expected {expected_total}, got {len(rows)}"
        )

    counts = collections.Counter()
    rank_counts = collections.Counter()
    per_mug_ranks: Dict[Tuple[str, str], set] = collections.defaultdict(set)
    identities = set()
    duplicate_counts = collections.Counter()
    output = [CANDIDATE_FIELDS + [
        "mug_positive_cd_q99_limit",
        "mug_positive_hd95_q99_limit",
        "duplicate_like_v21",
    ]]
    for row in rows:
        dataset = row["protected_dataset"]
        if dataset not in {"skullbreak", "skullfix"}:
            raise RuntimeError(f"Unexpected protected dataset: {dataset}")
        try:
            rank = int(row["descriptor_rank"])
        except ValueError as exc:
            raise RuntimeError(f"Invalid descriptor rank: {row['descriptor_rank']}") from exc
        if rank not in expected_ranks:
            raise RuntimeError(f"Unexpected descriptor rank: {rank}")
        identity = (dataset, row["mug_skull_id"], rank)
        if identity in identities:
            raise RuntimeError(f"Duplicate candidate identity: {identity}")
        identities.add(identity)
        if not all(row[field] for field in CANDIDATE_FIELDS[:5]):
            raise RuntimeError("Candidate contains an empty identifier")
        descriptor_distance = finite_nonnegative(
            row["descriptor_distance"], "descriptor_distance"
        )
        cd_value = finite_nonnegative(
            row["symmetric_cd_l1_normalized"], METRICS[0]
        )
        hd95_value = finite_nonnegative(
            row["symmetric_hd95_normalized"], METRICS[1]
        )
        if row["suspect_near_duplicate"] not in {"0", "1"}:
            raise RuntimeError("Invalid frozen v2 suspect flag")
        duplicate_like = cd_value <= cd_limit and hd95_value <= hd95_limit
        counts[dataset] += 1
        rank_counts[rank] += 1
        per_mug_ranks[(dataset, row["mug_skull_id"])].add(rank)
        duplicate_counts[dataset] += int(duplicate_like)
        output.append([
            row[field] for field in CANDIDATE_FIELDS[:6]
        ] + [
            descriptor_distance,
            cd_value,
            hd95_value,
            row["suspect_near_duplicate"],
            cd_limit,
            hd95_limit,
            int(duplicate_like),
        ])

    for dataset in ("skullbreak", "skullfix"):
        if counts[dataset] != expected_per_dataset:
            raise RuntimeError(
                f"Candidate count mismatch for {dataset}: {counts[dataset]}"
            )
    expected_per_rank = expected_total // len(expected_ranks)
    if any(rank_counts[rank] != expected_per_rank for rank in expected_ranks):
        raise RuntimeError(f"Descriptor-rank counts are invalid: {rank_counts}")
    expected_mug_skulls = expected_per_dataset // len(expected_ranks)
    for dataset in ("skullbreak", "skullfix"):
        keys = [key for key in per_mug_ranks if key[0] == dataset]
        if len(keys) != expected_mug_skulls:
            raise RuntimeError(f"Unexpected MUG skull coverage for {dataset}")
        if any(per_mug_ranks[key] != expected_ranks for key in keys):
            raise RuntimeError(f"Incomplete descriptor ranks for {dataset}")

    total_duplicates = sum(duplicate_counts.values())
    return output, {
        "candidate_pairs": len(rows),
        "pairs_by_protected_dataset": dict(sorted(counts.items())),
        "duplicate_like_by_protected_dataset": {
            dataset: duplicate_counts[dataset]
            for dataset in ("skullbreak", "skullfix")
        },
        "duplicate_like_candidates": total_duplicates,
        "required_duplicate_like_candidates": int(
            geometry["required_duplicate_like_candidates"]
        ),
        "mug_positive_cd_q99_limit": cd_limit,
        "mug_positive_hd95_q99_limit": hd95_limit,
    }


def render_report(receipt: Dict[str, Any]) -> bytes:
    calibration = receipt["source_stratified_calibration"]
    geometry = receipt["geometry_adjudication"]
    lines = [
        "# MUG500+ M2 protected-overlap audit v2.1 裁决报告",
        "",
        "> 本裁决只消费冻结的 v2 CSV/JSON、v2.1 协议锁和来源凭据；未重新打开受保护数组，也未访问模型预测或指标。",
        "",
        "## 冻结谱系",
        "",
        f"- protocol：`{receipt['protocol_id']}`",
        f"- protocol SHA256：`{receipt['protocol_sha256']}`",
        f"- v2 summary SHA256：`{receipt['inputs']['overlap_audit_v2_summary.json']}`",
        f"- provenance SHA256：`{receipt['source_provenance_sha256']}`",
        "- v1 与 v2 的失败结论保持不变；v2.1 是透明的事后统计修订。",
        "",
        "## 按来源校准",
        "",
        "| 来源域 | 正对 | 负对 | CD q99 / q01 | HD95 q99 / q01 | 域内分离 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for domain in DOMAIN_ORDER:
        item = calibration[domain]
        cd = item["metrics"][METRICS[0]]
        hd = item["metrics"][METRICS[1]]
        cd_text = (
            f"{cd['positive_q99']:.12g} / {cd['negative_q01']:.12g}"
            if cd["positive_q99"] is not None
            else f"N/A / {cd['negative_q01']:.12g}"
        )
        hd_text = (
            f"{hd['positive_q99']:.12g} / {hd['negative_q01']:.12g}"
            if hd["positive_q99"] is not None
            else f"N/A / {hd['negative_q01']:.12g}"
        )
        status = (
            "通过"
            if item["domain_separated"] is True
            else "不适用" if item["domain_separated"] is None else "未通过"
        )
        lines.append(
            f"| `{domain}` | {item['positive_pairs']} | {item['negative_pairs']} | "
            f"{cd_text} | {hd_text} | {status} |"
        )
    lines.extend([
        "",
        "SkullFix 每个来源颅骨只有一个点采样，因此不构造正对，也不参与重复包络定义。跨来源 pooled extrema 未被使用。",
        "",
        "## 几何裁决",
        "",
        f"- 固定候选对：{geometry['candidate_pairs']}。",
        f"- MUG 正对 CD q99 上限：{geometry['mug_positive_cd_q99_limit']:.12g}。",
        f"- MUG 正对 HD95 q99 上限：{geometry['mug_positive_hd95_q99_limit']:.12g}。",
        f"- duplicate-like 候选：{geometry['duplicate_like_candidates']}（要求为 {geometry['required_duplicate_like_candidates']}）。",
        f"- SkullBreak / SkullFix 分项：{geometry['duplicate_like_by_protected_dataset']}。",
        f"- 精确哈希交集：{receipt['exact_hash_intersections']}。",
        "",
        "## 自动门控",
        "",
        f"- 来源凭据：{'通过' if receipt['gates']['provenance'] else '未通过'}。",
        f"- 精确哈希：{'通过' if receipt['gates']['exact_hash'] else '未通过'}。",
        f"- MUG 校准：{'通过' if receipt['gates']['mug500plus_calibration'] else '未通过'}。",
        f"- SkullBreak 校准：{'通过' if receipt['gates']['skullbreak_calibration'] else '未通过'}。",
        f"- 几何重复包络：{'通过' if receipt['gates']['geometry'] else '未通过'}。",
        f"- 总体结果：`{receipt['status']}`。",
        "",
        "## 权限边界",
        "",
        f"- 允许创建独立的 100/25 source-skull 数据锁：`{receipt['data_split_lock_allowed']}`。",
        f"- 自动开始 D3 训练：`{receipt['training_unlocked']}`。",
        "- 本裁决不选择模型、loss、ordering、seed 或 query 机制，也不删除任何 MUG 病例。",
    ])
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical v2.1 adjudication")
        print(f"[locked] existing v2.1 adjudication is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] immutable v2.1 adjudication: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2_audit_dir", type=Path, required=True)
    parser.add_argument("--protocol_lock_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    v2_dir = args.v2_audit_dir.resolve()
    lock_dir = args.protocol_lock_dir.resolve()
    output_dir = args.output_dir.resolve()
    protocol, _, lock_receipt = validate_protocol_lock(lock_dir, v2_dir)

    calibration_rows = read_csv_exact(
        v2_dir / "calibration_pairs.csv", CALIBRATION_FIELDS
    )
    calibration_csv, calibration = summarize_calibration(
        calibration_rows, protocol
    )
    exact_rows = read_csv_exact(
        v2_dir / "exact_hash_intersections.csv", EXACT_HASH_FIELDS
    )
    candidate_rows = read_csv_exact(
        v2_dir / "high_resolution_candidates.csv", CANDIDATE_FIELDS
    )
    mug_metrics = calibration["mug500plus"]["metrics"]
    cd_limit = mug_metrics[METRICS[0]]["positive_q99"]
    hd95_limit = mug_metrics[METRICS[1]]["positive_q99"]
    if cd_limit is None or hd95_limit is None:
        raise RuntimeError("MUG positive calibration cannot define the envelope")
    geometry_csv, geometry = adjudicate_geometry(
        candidate_rows, protocol, cd_limit, hd95_limit
    )

    gates = {
        "lineage_hashes": True,
        "provenance": True,
        "exact_hash": len(exact_rows) == int(
            protocol["exact_hash_gate"]["required_intersections"]
        ),
        "mug500plus_calibration": calibration["mug500plus"][
            "domain_separated"
        ]
        is True,
        "skullbreak_calibration": calibration["skullbreak"][
            "domain_separated"
        ]
        is True,
        "geometry": geometry["duplicate_like_candidates"]
        == geometry["required_duplicate_like_candidates"],
    }
    passed = all(gates.values())
    status = (
        "passed_permit_100_25_source_skull_data_lock"
        if passed
        else "failed_keep_D3_locked"
    )
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": status,
        "protocol_sha256": lock_receipt["protocol_sha256"],
        "source_provenance_sha256": lock_receipt[
            "source_provenance_sha256"
        ],
        "inputs": {
            name: sha256_file(v2_dir / name)
            for name in sorted(protocol["frozen_inputs"]["v2_files"])
        },
        "source_stratified_calibration": calibration,
        "geometry_adjudication": geometry,
        "exact_hash_intersections": len(exact_rows),
        "gates": gates,
        "automatic_gate_passed": passed,
        "data_split_lock_allowed": passed,
        "training_unlocked": False,
        "raw_protected_arrays_reopened": False,
        "model_predictions_used": False,
        "model_metrics_used": False,
        "cross_dataset_thresholds_fitted": False,
        "manual_case_exclusions": [],
        "next_step": (
            "create_separate_100_25_source_skull_data_lock"
            if passed
            else "manual_source_level_review_or_new_explicit_amendment"
        ),
    }
    receipt_bytes = (
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    files = {
        "source_stratified_calibration.csv": csv_bytes(calibration_csv),
        "geometry_adjudication.csv": csv_bytes(geometry_csv),
        "overlap_v21_adjudication_receipt.json": receipt_bytes,
        "overlap_v21_adjudication_report_zh.md": render_report(receipt),
    }
    hashes = [f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    write_locked(files, output_dir)
    print(f"[gate] source-stratified calibration MUG={gates['mug500plus_calibration']} SkullBreak={gates['skullbreak_calibration']}")
    print(f"[gate] exact_hash={len(exact_rows)} duplicate_like={geometry['duplicate_like_candidates']}")
    print(f"[result] {status}")
    print(f"[next] {receipt['next_step']}")
    print("[locked] D3 training was not started")


if __name__ == "__main__":
    main()
