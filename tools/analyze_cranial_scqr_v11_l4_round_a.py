#!/usr/bin/env python3
"""Frozen paired analyzer for Cranial-SCQR v1.1 L4 Round A.

This module is deliberately usable with synthetic rows and NumPy only.  It
never loads a model or a dataset payload.  The evaluation runner imports its
pure functions after all eight evaluation partitions have completed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


PROTOCOL_ID = "cranial-scqr-v1.1-L4-roundA-development-evaluation-v1"
CANDIDATES = ("B0", "A1", "Q0", "QC")
FOLDS = ("A", "B")
SEED = 0
PRIMARY = "rim_gt_rim_to_pred_p95_mm"
GUARDRAILS = (
    "implant_cd_l1_mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
)
REQUIRED_CASE_METRICS = (
    PRIMARY,
    "implant_cd_l1_mm",
    "implant_pred_to_ref_mean_mm",
    "implant_ref_to_pred_mean_mm",
    "implant_hd95_mm",
    "implant_nsd_at_1mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_reference_rim_points",
    "rim_predicted_rim_points",
    "rim_gt_rim_to_pred_mean_mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_precision",
    "rim_contact_recall",
    "zero_contact_2mm",
    "disaster",
)


class ContractError(RuntimeError):
    """Raised when frozen analysis inputs fail closed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return value


def _finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name} is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        raise ContractError(f"{name} is nonfinite: {value!r}")
    return number


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    """Validate analysis-critical frozen structure without touching bound files."""

    if protocol.get("protocol_id") != PROTOCOL_ID:
        raise ContractError("protocol identity mismatch")
    matrix = protocol.get("checkpoint_matrix")
    if not isinstance(matrix, list) or len(matrix) != 8:
        raise ContractError("checkpoint matrix must contain exactly eight entries")
    actual = []
    run_keys = set()
    for entry in matrix:
        if not isinstance(entry, dict):
            raise ContractError("checkpoint matrix entry must be an object")
        key = (entry.get("candidate"), entry.get("fold"), entry.get("seed"))
        actual.append(key)
        run_keys.add(entry.get("run_key"))
    expected = [(c, f, SEED) for c in CANDIDATES for f in FOLDS]
    if actual != expected:
        raise ContractError(f"checkpoint order/matrix mismatch: {actual!r}")
    if len(run_keys) != 8:
        raise ContractError("run_key values must be unique")
    dev = protocol.get("development_allowlists", {})
    for fold in FOLDS:
        item = dev.get(fold, {})
        if (
            item.get("cases") != 105
            or item.get("sources") != 21
            or item.get("cases_per_source") != 5
        ):
            raise ContractError(f"Fold {fold} allowlist cardinality mismatch")
    analysis = protocol.get("round_a_analysis_contract", {})
    if analysis.get("bootstrap_seed") != 20260910:
        raise ContractError("bootstrap seed mismatch")
    if analysis.get("bootstrap_samples") != 10000:
        raise ContractError("bootstrap sample count mismatch")
    if analysis.get("round_b_authorized_by_gate_result") is not False:
        raise ContractError("protocol must not authorize Round B")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ContractError(f"refusing to write empty CSV: {path}")
    fields: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def validate_case_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Require the complete 4 x 2 x 105 matrix and strict pair identities."""

    if len(rows) != 840:
        raise ContractError(f"expected 840 case rows, found {len(rows)}")
    by_partition: dict[tuple[str, str, int], list[Mapping[str, Any]]] = defaultdict(list)
    identities = set()
    for index, row in enumerate(rows):
        candidate = str(row.get("candidate", ""))
        fold = str(row.get("fold", ""))
        try:
            seed = int(row.get("seed"))
        except (TypeError, ValueError) as exc:
            raise ContractError(f"row {index}: invalid seed") from exc
        if candidate not in CANDIDATES or fold not in FOLDS or seed != SEED:
            raise ContractError(f"row {index}: invalid candidate/fold/seed")
        case_id = str(row.get("case_id", ""))
        source = str(row.get("source_skull_id", ""))
        defect = str(row.get("defect_type", ""))
        if not case_id or not source or not defect:
            raise ContractError(f"row {index}: missing case/source/defect identity")
        identity = (candidate, fold, seed, case_id)
        if identity in identities:
            raise ContractError(f"duplicate case identity: {identity}")
        identities.add(identity)
        for metric in REQUIRED_CASE_METRICS:
            if metric not in row:
                raise ContractError(f"row {index}: missing {metric}")
        # Primary and gate guardrails can never be silently filtered.
        for metric in (PRIMARY, *GUARDRAILS):
            _finite(row[metric], f"row {index} {metric}")
        zero = _finite(row["zero_contact_2mm"], "zero_contact_2mm")
        disaster = _finite(row["disaster"], "disaster")
        if zero not in (0.0, 1.0) or disaster not in (0.0, 1.0):
            raise ContractError("event counters must be binary per case")
        by_partition[(candidate, fold, seed)].append(row)

    for key in [(c, f, SEED) for c in CANDIDATES for f in FOLDS]:
        part = by_partition.get(key, [])
        if len(part) != 105:
            raise ContractError(f"partition {key} has {len(part)} cases, expected 105")
        sources: dict[str, set[str]] = defaultdict(set)
        for row in part:
            sources[str(row["source_skull_id"])].add(str(row["case_id"]))
        if len(sources) != 21 or any(len(cases) != 5 for cases in sources.values()):
            raise ContractError(f"partition {key} violates 21 x 5 source structure")

    for fold in FOLDS:
        reference = {
            str(row["case_id"]) for row in by_partition[("B0", fold, SEED)]
        }
        for candidate in CANDIDATES[1:]:
            observed = {
                str(row["case_id"])
                for row in by_partition[(candidate, fold, SEED)]
            }
            if observed != reference:
                raise ContractError(f"unpaired case IDs for {candidate} Fold {fold}")
    fold_sources = {
        fold: {
            str(row["source_skull_id"])
            for row in by_partition[("B0", fold, SEED)]
        }
        for fold in FOLDS
    }
    if fold_sources["A"] & fold_sources["B"]:
        raise ContractError("Fold A/B source skulls must be disjoint")


def aggregate_source_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Average five defects equally within each source skull."""

    validate_case_rows(rows)
    groups: dict[tuple[str, str, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["candidate"]),
            str(row["fold"]),
            int(row["seed"]),
            str(row["source_skull_id"]),
        )
        groups[key].append(row)

    output: list[dict[str, Any]] = []
    numeric = set(REQUIRED_CASE_METRICS) - {"zero_contact_2mm", "disaster"}
    for key in sorted(groups, key=lambda x: (CANDIDATES.index(x[0]), FOLDS.index(x[1]), x[3])):
        group = groups[key]
        if len(group) != 5 or len({str(row["defect_type"]) for row in group}) != 5:
            raise ContractError(f"source {key} does not contain five unique defects")
        result: dict[str, Any] = {
            "candidate": key[0],
            "fold": key[1],
            "seed": key[2],
            "source_skull_id": key[3],
            "case_count": 5,
            "zero_contact_2mm_count": int(sum(int(float(r["zero_contact_2mm"])) for r in group)),
            "disaster_count": int(sum(int(float(r["disaster"])) for r in group)),
        }
        for metric in sorted(numeric):
            raw_values = [row[metric] for row in group]
            try:
                values = [_finite(value, f"{key} {metric}") for value in raw_values]
            except ContractError:
                if metric in (PRIMARY, *GUARDRAILS):
                    raise
                result[metric] = None
            else:
                result[metric] = float(np.mean(values))
        output.append(result)
    if len(output) != 168:
        raise ContractError(f"expected 168 source rows, found {len(output)}")
    return output


def paired_source_deltas(
    source_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    index: dict[tuple[str, str, int, str], Mapping[str, Any]] = {}
    for row in source_rows:
        key = (
            str(row["candidate"]), str(row["fold"]), int(row["seed"]),
            str(row["source_skull_id"]),
        )
        if key in index:
            raise ContractError(f"duplicate source row: {key}")
        index[key] = row
    output: list[dict[str, Any]] = []
    comparisons = (("QC", "B0"), ("QC", "Q0"), ("A1", "B0"), ("Q0", "B0"))
    metrics = (PRIMARY, *GUARDRAILS)
    for candidate, comparator in comparisons:
        for fold in FOLDS:
            sources = sorted(
                key[3] for key in index if key[:3] == (comparator, fold, SEED)
            )
            if len(sources) != 21:
                raise ContractError(f"{comparator} Fold {fold} lacks 21 sources")
            for source in sources:
                left = index.get((candidate, fold, SEED, source))
                right = index.get((comparator, fold, SEED, source))
                if left is None or right is None:
                    raise ContractError(f"unpaired source: {candidate}/{comparator}/{fold}/{source}")
                row: dict[str, Any] = {
                    "comparison": f"{candidate}_minus_{comparator}",
                    "candidate": candidate,
                    "comparator": comparator,
                    "fold": fold,
                    "seed": SEED,
                    "source_skull_id": source,
                }
                for metric in metrics:
                    row[metric] = _finite(left[metric], metric) - _finite(right[metric], metric)
                output.append(row)
    return output


def stratified_cluster_bootstrap(
    deltas: Sequence[Mapping[str, Any]],
    metric: str,
    *,
    seed: int = 20260910,
    samples: int = 10000,
) -> dict[str, float]:
    """Resample 21 sources in each fold and combine folds with equal weight."""

    if seed != 20260910 or samples != 10000:
        raise ContractError("bootstrap seed/sample count must remain frozen")
    by_fold: dict[str, np.ndarray] = {}
    for fold in FOLDS:
        values = np.asarray(
            [_finite(row[metric], metric) for row in deltas if row["fold"] == fold],
            dtype=np.float64,
        )
        if values.shape != (21,):
            raise ContractError(f"bootstrap Fold {fold} requires 21 source deltas")
        by_fold[fold] = values
    rng = np.random.default_rng(seed)
    draws = np.empty(samples, dtype=np.float64)
    for start in range(0, samples, 1000):
        count = min(1000, samples - start)
        means = []
        for fold in FOLDS:
            indices = rng.integers(0, 21, size=(count, 21))
            means.append(by_fold[fold][indices].mean(axis=1))
        draws[start : start + count] = 0.5 * (means[0] + means[1])
    return {
        "point_estimate": float(0.5 * (by_fold["A"].mean() + by_fold["B"].mean())),
        "ci95_low": float(np.percentile(draws, 2.5)),
        "ci95_high": float(np.percentile(draws, 97.5)),
        "seed": seed,
        "samples": samples,
    }


def build_summary(
    source_rows: Sequence[Mapping[str, Any]],
    delta_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    metrics = (PRIMARY, *GUARDRAILS)
    summary: dict[str, Any] = {"candidates": {}, "comparisons": {}}
    for candidate in CANDIDATES:
        summary["candidates"][candidate] = {}
        for metric in metrics:
            fold_means = {}
            for fold in FOLDS:
                values = [
                    _finite(r[metric], metric)
                    for r in source_rows
                    if r["candidate"] == candidate and r["fold"] == fold
                ]
                if len(values) != 21:
                    raise ContractError(f"missing source values for {candidate}/{fold}/{metric}")
                fold_means[fold] = float(np.mean(values))
            fold_means["combined"] = 0.5 * (fold_means["A"] + fold_means["B"])
            summary["candidates"][candidate][metric] = fold_means

    for comparison in ("QC_minus_B0", "QC_minus_Q0", "A1_minus_B0", "Q0_minus_B0"):
        selected = [r for r in delta_rows if r["comparison"] == comparison]
        if len(selected) != 42:
            raise ContractError(f"comparison {comparison} requires 42 source rows")
        summary["comparisons"][comparison] = {}
        for metric in metrics:
            fold_means = {
                fold: float(np.mean([_finite(r[metric], metric) for r in selected if r["fold"] == fold]))
                for fold in FOLDS
            }
            fold_means["combined"] = 0.5 * (fold_means["A"] + fold_means["B"])
            fold_means["bootstrap"] = stratified_cluster_bootstrap(selected, metric)
            summary["comparisons"][comparison][metric] = fold_means
    return summary


def event_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for candidate in CANDIDATES:
        result[candidate] = {}
        for fold in FOLDS:
            selected = [r for r in rows if r["candidate"] == candidate and r["fold"] == fold]
            if len(selected) != 105:
                raise ContractError(f"event count partition incomplete: {candidate}/{fold}")
            result[candidate][fold] = {
                "zero_contact": int(sum(int(float(r["zero_contact_2mm"])) for r in selected)),
                "disaster": int(sum(int(float(r["disaster"])) for r in selected)),
            }
    return result


def build_tail_reports(
    rows: Sequence[Mapping[str, Any]],
    source_deltas: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Produce the frozen case tails and paired improved/worsened counts."""

    reports: dict[str, Any] = {"candidates": {}, "comparisons": {}}
    for candidate in CANDIDATES:
        selected = [row for row in rows if row["candidate"] == candidate]
        values = np.asarray([_finite(row[PRIMARY], PRIMARY) for row in selected])
        by_defect: dict[str, float] = {}
        for defect in sorted({str(row["defect_type"]) for row in selected}):
            defect_values = [
                _finite(row[PRIMARY], PRIMARY)
                for row in selected if str(row["defect_type"]) == defect
            ]
            by_defect[defect] = float(np.mean(defect_values))
        reports["candidates"][candidate] = {
            "case_median": float(np.median(values)),
            "case_p90": float(np.percentile(values, 90)),
            "case_p95": float(np.percentile(values, 95)),
            "by_defect_type": by_defect,
        }

    case_index = {
        (str(row["candidate"]), str(row["fold"]), int(row["seed"]), str(row["case_id"])): row
        for row in rows
    }
    for candidate, comparator in (("QC", "B0"), ("QC", "Q0"), ("A1", "B0"), ("Q0", "B0")):
        comparison = f"{candidate}_minus_{comparator}"
        cases: list[float] = []
        for key, left in case_index.items():
            if key[0] != candidate:
                continue
            right = case_index.get((comparator, key[1], key[2], key[3]))
            if right is None:
                raise ContractError(f"missing paired case for {comparison}: {key[3]}")
            cases.append(_finite(left[PRIMARY], PRIMARY) - _finite(right[PRIMARY], PRIMARY))
        sources = [
            _finite(row[PRIMARY], PRIMARY)
            for row in source_deltas if row["comparison"] == comparison
        ]
        if len(cases) != 210 or len(sources) != 42:
            raise ContractError(f"tail pairing incomplete for {comparison}")
        reports["comparisons"][comparison] = {
            "per_source_delta_distribution": {
                "mean": float(np.mean(sources)),
                "median": float(np.median(sources)),
                "p05": float(np.percentile(sources, 5)),
                "p95": float(np.percentile(sources, 95)),
            },
            "paired_improved_case_count": int(np.count_nonzero(np.asarray(cases) < 0)),
            "paired_worsened_case_count": int(np.count_nonzero(np.asarray(cases) > 0)),
            "paired_tied_case_count": int(np.count_nonzero(np.asarray(cases) == 0)),
            "paired_improved_source_count": int(np.count_nonzero(np.asarray(sources) < 0)),
            "paired_worsened_source_count": int(np.count_nonzero(np.asarray(sources) > 0)),
            "paired_tied_source_count": int(np.count_nonzero(np.asarray(sources) == 0)),
        }
    return reports


def evaluate_gate(
    summary: Mapping[str, Any],
    counts: Mapping[str, Any],
    *,
    numeric_complete: bool = True,
    execution_ok: bool = True,
    resource_ok: bool = True,
) -> dict[str, Any]:
    """Apply exact point-estimate thresholds; a PASS is never authorization."""

    qcb0 = summary["comparisons"]["QC_minus_B0"]
    qcq0 = summary["comparisons"]["QC_minus_Q0"]
    checks: list[dict[str, Any]] = []

    def add(name: str, actual: Any, operator: str, threshold: Any, passed: bool) -> None:
        checks.append({
            "name": name, "actual": actual, "operator": operator,
            "threshold": threshold, "passed": bool(passed),
        })

    add("primary_fold_A_nonworsening", qcb0[PRIMARY]["A"], "<=", 0.0, qcb0[PRIMARY]["A"] <= 0.0)
    add("primary_fold_B_nonworsening", qcb0[PRIMARY]["B"], "<=", 0.0, qcb0[PRIMARY]["B"] <= 0.0)
    add("primary_combined_improvement", qcb0[PRIMARY]["combined"], "<=", -0.10, qcb0[PRIMARY]["combined"] <= -0.10)
    add("contact_increment_over_Q0", qcq0[PRIMARY]["combined"], "<", 0.0, qcq0[PRIMARY]["combined"] < 0.0)

    upper = {
        "implant_cd_l1_mm": 0.10,
        "final_cd_l1_mm": 0.10,
        "final_hd95_mm": 0.50,
    }
    for metric, threshold in upper.items():
        for scope in (*FOLDS, "combined"):
            actual = qcb0[metric][scope]
            add(f"{metric}_{scope}", actual, "<=", threshold, actual <= threshold)
    for scope in (*FOLDS, "combined"):
        actual = qcb0["final_nsd_at_1mm"][scope]
        add(f"final_nsd_at_1mm_{scope}", actual, ">=", -0.01, actual >= -0.01)
    for fold in FOLDS:
        qc_zero = int(counts["QC"][fold]["zero_contact"])
        b0_zero = int(counts["B0"][fold]["zero_contact"])
        add(f"zero_contact_fold_{fold}", qc_zero, "<=", b0_zero, qc_zero <= b0_zero)
        qc_disaster = int(counts["QC"][fold]["disaster"])
        b0_disaster = int(counts["B0"][fold]["disaster"])
        add(f"disaster_fold_{fold}", qc_disaster, "<=", b0_disaster, qc_disaster <= b0_disaster)
    add("all_required_numeric", numeric_complete, "is", True, numeric_complete is True)
    add("execution_gate", execution_ok, "is", True, execution_ok is True)
    add("resource_gate", resource_ok, "is", True, resource_ok is True)

    all_pass = all(item["passed"] for item in checks)
    primary_a = qcb0[PRIMARY]["A"]
    primary_b = qcb0[PRIMARY]["B"]
    guardrail_names = {
        item["name"] for item in checks
        if item["name"].startswith(("implant_", "final_", "zero_", "disaster_"))
    }
    guardrail_failure = any(not item["passed"] for item in checks if item["name"] in guardrail_names)
    if all_pass:
        classification = "PASS"
    elif not numeric_complete or not execution_ok or not resource_ok or guardrail_failure:
        classification = "NO_GO"
    elif (primary_a < 0 < primary_b) or (primary_b < 0 < primary_a):
        classification = "INCONCLUSIVE"
    elif qcb0[PRIMARY]["combined"] >= 0:
        classification = "NEGATIVE"
    else:
        classification = "NO_GO"
    return {
        "protocol_id": PROTOCOL_ID,
        "classification": classification,
        "all_gate_requirements_pass": all_pass,
        "checks": checks,
        "round_b_authorized": False,
        "automatic_next_run": False,
        "automatic_beta_adjustment": False,
        "automatic_candidate_exclusion": False,
    }


def analyze_case_rows(
    rows: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    validate_protocol(protocol)
    sources = aggregate_source_rows(rows)
    deltas = paired_source_deltas(sources)
    summary = build_summary(sources, deltas)
    summary["tail_reports"] = build_tail_reports(rows, deltas)
    gate = evaluate_gate(summary, event_counts(rows))
    return sources, deltas, summary, gate


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--case-metrics", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if sha256_file(args.protocol) != args.protocol_sha256:
        raise ContractError("protocol SHA256 mismatch")
    protocol = load_json(args.protocol)
    rows = read_csv(args.case_metrics)
    sources, deltas, summary, gate = analyze_case_rows(rows, protocol)
    args.output_dir.mkdir(parents=False, exist_ok=False)
    write_csv(args.output_dir / "per_model_source_metrics.csv", sources)
    write_csv(args.output_dir / "paired_deltas.csv", deltas)
    with (args.output_dir / "fold_and_combined_summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    with (args.output_dir / "round_a_gate_receipt.json").open("x", encoding="utf-8") as stream:
        json.dump(gate, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
