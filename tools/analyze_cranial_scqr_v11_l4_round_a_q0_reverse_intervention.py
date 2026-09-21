#!/usr/bin/env python3
"""Pure analyzer for the frozen Q0 reverse inference intervention.

Importing this module performs no checkpoint, NPZ, CUDA, model, or filesystem
work.  The functions are intentionally usable by the synthetic CPU contract
suite and require separately frozen real inputs for any future execution.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


PROTOCOL_ID = "cranial-scqr-v1.1-L4-roundA-I-Q0-reverse-inference-intervention-v1"
PROTOCOL_STATUS = "FROZEN_PENDING_IMPLEMENTATION_AND_SEPARATE_EXECUTION_AUTHORIZATION"
PROTOCOL_SHA256 = "bf447b2585aa799f00bd0f942033971a567eb2ebc527a6ef3d28664facfd3de0"
FOLDS = ("A", "B")
SEED = 0
CONDITIONS = ("native_q0", "q0_beta1")
COMPARISONS = (
    "q0_beta1_minus_native_q0",
    "native_q0_minus_qc_bias_zero",
    "q0_beta1_minus_native_qc",
    "factorial_interaction",
)
PRIMARY = "rim_gt_rim_to_pred_p95_mm"
DISTANCE_METRICS = (
    "implant_cd_l1_mm",
    "implant_pred_to_ref_mean_mm",
    "implant_ref_to_pred_mean_mm",
    "implant_hd95_mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "rim_gt_rim_to_pred_mean_mm",
    PRIMARY,
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
)
UNIT_INTERVAL_METRICS = (
    "implant_nsd_at_1mm",
    "final_nsd_at_1mm",
    "rim_contact_precision",
    "rim_contact_recall",
)
OPTIONAL_FIELDS = (
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_precision",
)
INTEGER_FIELDS = (
    "rim_reference_rim_points",
    "rim_predicted_rim_points",
    "zero_contact_2mm",
    "disaster",
)
SUMMARY_METRICS = (
    PRIMARY,
    "implant_cd_l1_mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
)


class ContractError(RuntimeError):
    """Raised whenever a frozen Q0 reverse-intervention contract is violated."""


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ContractError(f"refusing to write empty CSV: {path}")
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name} is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        raise ContractError(f"{name} is nonfinite: {value!r}")
    return number


def _optional(value: Any, name: str) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name} is not numeric: {value!r}") from exc
    if math.isnan(number):
        return None
    if not math.isfinite(number):
        raise ContractError(f"{name} is nonfinite: {value!r}")
    return number


def _integer(value: Any, name: str) -> int:
    number = _finite(value, name)
    integer = int(number)
    if number != integer:
        raise ContractError(f"{name} is not an integer: {value!r}")
    return integer


def _assert_close(left: Any, right: Any, tolerance: float, name: str) -> float:
    left_number = _optional(left, f"{name} left")
    right_number = _optional(right, f"{name} right")
    if left_number is None or right_number is None:
        if left_number is right_number:
            return 0.0
        raise ContractError(f"{name}: optional-NA mismatch")
    difference = abs(left_number - right_number)
    if difference > tolerance:
        raise ContractError(f"{name}: abs difference {difference} exceeds {tolerance}")
    return difference


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    if protocol.get("protocol_id") != PROTOCOL_ID:
        raise ContractError("protocol identity mismatch")
    if protocol.get("status") != PROTOCOL_STATUS:
        raise ContractError("protocol status mismatch")
    matrix = protocol.get("checkpoint_matrix")
    expected = [("Q0", fold, SEED, 0.0) for fold in FOLDS]
    if not isinstance(matrix, list) or [
        (
            row.get("candidate"),
            row.get("fold"),
            row.get("seed"),
            row.get("native_inference_beta"),
        )
        for row in matrix
    ] != expected:
        raise ContractError("checkpoint matrix must be exactly Q0 Fold A/B seed 0 beta 0")
    conditions = protocol.get("factorial_design", {}).get("q0_conditions", {})
    if conditions.get("order") != list(CONDITIONS):
        raise ContractError("Q0 condition order mismatch")
    dev = protocol.get("development_allowlists", {})
    for fold in FOLDS:
        item = dev.get(fold, {})
        if (
            item.get("cases") != 105
            or item.get("sources") != 21
            or item.get("cases_per_source") != 5
        ):
            raise ContractError(f"Fold {fold} development cardinality mismatch")
    numeric = protocol.get("numeric_contract", {})
    reproduction = numeric.get("native_q0_reproduction_against_frozen_round_a", {})
    if (
        reproduction.get("distance_metrics_max_abs_mm") != 1e-5
        or reproduction.get("unit_interval_metrics_max_abs") != 1e-8
        or numeric.get("coarse_output_condition_invariance_max_abs_normalized") != 1e-7
        or numeric.get("inference_effect_practical_inactivity_threshold_mm") != 0.01
    ):
        raise ContractError("numeric contract mismatch")
    analysis = protocol.get("analysis_contract", {})
    if analysis.get("comparison_order") != list(COMPARISONS):
        raise ContractError("comparison order mismatch")
    if analysis.get("bootstrap_seed") != 20260910 or analysis.get("bootstrap_samples") != 10000:
        raise ContractError("bootstrap contract mismatch")
    if analysis.get("round_b_authorized_by_any_result") is not False:
        raise ContractError("Round B must remain unauthorized")
    execution = protocol.get("future_execution_contract", {})
    expected_counts = {
        "checkpoint_loads_expected": 2,
        "model_case_forward_calls_expected": 420,
        "npz_opens_expected": 210,
        "partial_reads_expected": 210,
        "implant_reads_expected": 210,
        "gt_reads_expected": 210,
        "temporary_beta_assignments_expected": 210,
        "temporary_beta_restorations_expected": 210,
        "qc_checkpoint_loads_expected": 0,
        "qc_model_forwards_expected": 0,
    }
    if any(execution.get(key) != value for key, value in expected_counts.items()):
        raise ContractError("future execution count mismatch")
    if execution.get("execution_authorized_by_this_protocol") is not False:
        raise ContractError("protocol cannot authorize formal execution")
    boundary = protocol.get("authorization_boundary", {})
    locked = (
        "implementation_authorized_by_this_protocol",
        "syntax_or_synthetic_tests_authorized_by_this_protocol",
        "real_checkpoint_loads_authorized",
        "real_npz_opens_authorized",
        "gpu_use_authorized",
        "development_execution_authorized",
        "real_result_statistics_authorized",
        "launcher_creation_authorized",
        "formal_output_directory_creation_authorized",
        "training_or_bncal_authorized",
        "threshold_tuning_authorized",
        "automatic_retry_authorized",
        "round_b_authorized",
        "automatic_next_stage",
    )
    if any(boundary.get(name) is not False for name in locked):
        raise ContractError("protocol crosses an authorization boundary")


def validate_reverse_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    if len(rows) != 420:
        raise ContractError(f"expected 420 reverse-intervention rows, found {len(rows)}")
    partitions: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    identities: set[tuple[str, str, str]] = set()
    metadata: dict[tuple[str, str], tuple[str, str, str]] = {}
    for index, row in enumerate(rows):
        condition = str(row.get("condition", ""))
        fold = str(row.get("fold", ""))
        case_id = str(row.get("case_id", ""))
        if (
            condition not in CONDITIONS
            or fold not in FOLDS
            or not case_id
            or str(row.get("candidate")) != "Q0"
            or int(row.get("seed", -1)) != SEED
        ):
            raise ContractError(f"row {index}: invalid condition/Q0/fold/seed/case identity")
        identity = (condition, fold, case_id)
        if identity in identities:
            raise ContractError(f"duplicate row: {identity}")
        identities.add(identity)
        source = str(row.get("source_skull_id", ""))
        skull = str(row.get("skull_id", ""))
        defect = str(row.get("defect_type", ""))
        if not source or not skull or not defect:
            raise ContractError(f"row {index}: missing case metadata")
        case_key = (fold, case_id)
        previous = metadata.setdefault(case_key, (source, skull, defect))
        if previous != (source, skull, defect):
            raise ContractError(f"condition metadata mismatch: {fold}/{case_id}")
        for field in DISTANCE_METRICS:
            if field not in row:
                raise ContractError(f"row {index}: missing {field}")
            (_optional if field in OPTIONAL_FIELDS else _finite)(row[field], field)
        for field in UNIT_INTERVAL_METRICS:
            if field not in row:
                raise ContractError(f"row {index}: missing {field}")
            (_optional if field in OPTIONAL_FIELDS else _finite)(row[field], field)
        for field in INTEGER_FIELDS:
            value = _integer(row.get(field), field)
            if field in ("zero_contact_2mm", "disaster") and value not in (0, 1):
                raise ContractError(f"row {index}: {field} must be binary")
        coarse = _finite(
            row.get("coarse_condition_max_abs_normalized"),
            "coarse_condition_max_abs_normalized",
        )
        if coarse < 0:
            raise ContractError("coarse-condition error cannot be negative")
        partitions[(condition, fold)].append(row)
    for condition in CONDITIONS:
        for fold in FOLDS:
            part = partitions[(condition, fold)]
            if len(part) != 105:
                raise ContractError(f"{condition}/{fold} requires 105 cases")
            sources: dict[str, set[str]] = defaultdict(set)
            defects: dict[str, set[str]] = defaultdict(set)
            for row in part:
                source = str(row["source_skull_id"])
                sources[source].add(str(row["case_id"]))
                defects[source].add(str(row["defect_type"]))
            if len(sources) != 21 or any(len(value) != 5 for value in sources.values()):
                raise ContractError(f"{condition}/{fold} violates 21 x 5 structure")
            if any(len(value) != 5 for value in defects.values()):
                raise ContractError(f"{condition}/{fold} lacks five unique defects per source")
        if {
            str(row["case_id"]) for row in partitions[(condition, "A")]
        } & {
            str(row["case_id"]) for row in partitions[(condition, "B")]
        }:
            raise ContractError("Fold A/B case IDs overlap")
    for fold in FOLDS:
        native = {str(row["case_id"]) for row in partitions[("native_q0", fold)]}
        reverse = {str(row["case_id"]) for row in partitions[("q0_beta1", fold)]}
        if native != reverse:
            raise ContractError(f"unpaired Q0 conditions in Fold {fold}")


def _candidate_reference(
    rows: Sequence[Mapping[str, Any]], candidate: str
) -> dict[tuple[str, str], Mapping[str, Any]]:
    output: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        if str(row.get("candidate")) != candidate:
            continue
        fold, case_id = str(row.get("fold", "")), str(row.get("case_id", ""))
        if fold not in FOLDS or not case_id or int(row.get("seed", -1)) != SEED:
            raise ContractError(f"invalid frozen {candidate} identity")
        key = (fold, case_id)
        if key in output:
            raise ContractError(f"duplicate frozen {candidate} row: {key}")
        output[key] = row
    if len(output) != 210:
        raise ContractError(f"frozen {candidate} reference requires 210 rows")
    return output


def _qc_condition_reference(
    rows: Sequence[Mapping[str, Any]], condition: str
) -> dict[tuple[str, str], Mapping[str, Any]]:
    output: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        if str(row.get("condition")) != condition:
            continue
        fold, case_id = str(row.get("fold", "")), str(row.get("case_id", ""))
        if fold not in FOLDS or not case_id or str(row.get("candidate")) != "QC":
            raise ContractError(f"invalid frozen QC/{condition} identity")
        key = (fold, case_id)
        if key in output:
            raise ContractError(f"duplicate frozen QC/{condition} row: {key}")
        output[key] = row
    if len(output) != 210:
        raise ContractError(f"frozen QC/{condition} reference requires 210 rows")
    return output


def validate_execution_controls(
    rows: Sequence[Mapping[str, Any]],
    frozen_round_a_rows: Sequence[Mapping[str, Any]],
    frozen_qc_rows: Sequence[Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    validate_protocol(protocol)
    validate_reverse_rows(rows)
    frozen_q0 = _candidate_reference(frozen_round_a_rows, "Q0")
    frozen_qc_native = _qc_condition_reference(frozen_qc_rows, "native_qc")
    frozen_qc_zero = _qc_condition_reference(frozen_qc_rows, "bias_zero")
    if set(frozen_q0) != set(frozen_qc_native) or set(frozen_q0) != set(frozen_qc_zero):
        raise ContractError("frozen Q0/QC case identities differ")
    by_key = {
        (str(row["condition"]), str(row["fold"]), str(row["case_id"])): row
        for row in rows
    }
    numeric = protocol["numeric_contract"]
    reproduction = numeric["native_q0_reproduction_against_frozen_round_a"]
    maxima = {
        "native_distance_metric_max_abs_mm": 0.0,
        "native_unit_interval_metric_max_abs": 0.0,
        "coarse_condition_max_abs_normalized": 0.0,
    }
    for fold, case_id in sorted(frozen_q0):
        native = by_key[("native_q0", fold, case_id)]
        reverse = by_key[("q0_beta1", fold, case_id)]
        reference = frozen_q0[(fold, case_id)]
        for field in DISTANCE_METRICS:
            difference = _assert_close(
                native[field], reference[field],
                float(reproduction["distance_metrics_max_abs_mm"]),
                f"native Q0 reproduction {fold}/{case_id}/{field}",
            )
            maxima["native_distance_metric_max_abs_mm"] = max(
                maxima["native_distance_metric_max_abs_mm"], difference
            )
        for field in UNIT_INTERVAL_METRICS:
            difference = _assert_close(
                native[field], reference[field],
                float(reproduction["unit_interval_metrics_max_abs"]),
                f"native Q0 reproduction {fold}/{case_id}/{field}",
            )
            maxima["native_unit_interval_metric_max_abs"] = max(
                maxima["native_unit_interval_metric_max_abs"], difference
            )
        for field in INTEGER_FIELDS:
            if _integer(native[field], field) != _integer(reference[field], field):
                raise ContractError(f"native Q0 integer mismatch: {fold}/{case_id}/{field}")
        for row in (native, reverse):
            maxima["coarse_condition_max_abs_normalized"] = max(
                maxima["coarse_condition_max_abs_normalized"],
                _finite(row["coarse_condition_max_abs_normalized"], "coarse error"),
            )
    threshold = float(numeric["coarse_output_condition_invariance_max_abs_normalized"])
    if maxima["coarse_condition_max_abs_normalized"] > threshold:
        raise ContractError("coarse output changed across Q0 beta conditions")
    return {
        "status": "PASS",
        "native_q0_reproduction_pass": True,
        "coarse_condition_invariance_pass": True,
        "frozen_qc_cells_reused_without_checkpoint_load": True,
        "maxima": maxima,
    }


def _aggregate_cell(
    rows: Sequence[Mapping[str, Any]],
    *,
    cell: str,
    condition: str | None = None,
    candidate: str | None = None,
) -> list[dict[str, Any]]:
    selected = [
        row for row in rows
        if (condition is None or str(row.get("condition")) == condition)
        and (candidate is None or str(row.get("candidate")) == candidate)
    ]
    if len(selected) != 210:
        raise ContractError(f"cell {cell} requires 210 case rows, found {len(selected)}")
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in selected:
        groups[(str(row["fold"]), str(row["source_skull_id"]))].append(row)
    output: list[dict[str, Any]] = []
    for (fold, source), group in sorted(groups.items()):
        if fold not in FOLDS or len(group) != 5 or len({str(r["defect_type"]) for r in group}) != 5:
            raise ContractError(f"cell {cell} source group is incomplete: {fold}/{source}")
        result: dict[str, Any] = {
            "cell": cell,
            "fold": fold,
            "seed": SEED,
            "source_skull_id": source,
            "case_count": 5,
        }
        for metric in SUMMARY_METRICS:
            result[metric] = float(np.mean([_finite(row[metric], metric) for row in group]))
        output.append(result)
    if len(output) != 42:
        raise ContractError(f"cell {cell} requires 42 source rows, found {len(output)}")
    return output


def aggregate_factorial_sources(
    rows: Sequence[Mapping[str, Any]],
    frozen_round_a_rows: Sequence[Mapping[str, Any]],
    frozen_qc_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    cells = []
    cells.extend(_aggregate_cell(rows, cell="Q0_beta0", condition="native_q0"))
    cells.extend(_aggregate_cell(rows, cell="Q0_beta1", condition="q0_beta1"))
    cells.extend(_aggregate_cell(frozen_qc_rows, cell="QC_beta0", condition="bias_zero"))
    cells.extend(_aggregate_cell(frozen_qc_rows, cell="QC_beta1", condition="native_qc"))
    # The frozen Q0 rows are not added as a fifth cell; they are a reproduction
    # gate for the same-run native Q0 cell.
    _candidate_reference(frozen_round_a_rows, "Q0")
    if len(cells) != 168:
        raise ContractError("factorial aggregation must produce 168 source rows")
    return cells


def paired_factorial_deltas(source_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    index = {
        (str(row["cell"]), str(row["fold"]), str(row["source_skull_id"])): row
        for row in source_rows
    }
    if len(index) != 168:
        raise ContractError("factorial source rows are duplicated or incomplete")
    output: list[dict[str, Any]] = []
    for fold in FOLDS:
        sources = sorted(key[2] for key in index if key[:2] == ("Q0_beta0", fold))
        if len(sources) != 21:
            raise ContractError(f"Fold {fold} requires 21 paired sources")
        for source in sources:
            cells = {
                name: index.get((name, fold, source))
                for name in ("Q0_beta0", "Q0_beta1", "QC_beta0", "QC_beta1")
            }
            if any(value is None for value in cells.values()):
                raise ContractError(f"unpaired factorial source: {fold}/{source}")
            for comparison in COMPARISONS:
                row: dict[str, Any] = {
                    "comparison": comparison,
                    "fold": fold,
                    "seed": SEED,
                    "source_skull_id": source,
                }
                for metric in SUMMARY_METRICS:
                    q00 = _finite(cells["Q0_beta0"][metric], metric)  # type: ignore[index]
                    q01 = _finite(cells["Q0_beta1"][metric], metric)  # type: ignore[index]
                    qc0 = _finite(cells["QC_beta0"][metric], metric)  # type: ignore[index]
                    qc1 = _finite(cells["QC_beta1"][metric], metric)  # type: ignore[index]
                    values = {
                        "q0_beta1_minus_native_q0": q01 - q00,
                        "native_q0_minus_qc_bias_zero": q00 - qc0,
                        "q0_beta1_minus_native_qc": q01 - qc1,
                        "factorial_interaction": (q01 - q00) - (qc1 - qc0),
                    }
                    row[metric] = values[comparison]
                output.append(row)
    if len(output) != 168:
        raise ContractError("paired factorial deltas must produce 168 rows")
    return output


def stratified_cluster_bootstrap(
    rows: Sequence[Mapping[str, Any]],
    metric: str,
    *,
    seed: int = 20260910,
    samples: int = 10000,
) -> dict[str, float]:
    if seed != 20260910 or samples != 10000:
        raise ContractError("bootstrap seed/sample count must remain frozen")
    by_fold: dict[str, np.ndarray] = {}
    for fold in FOLDS:
        values = np.asarray(
            [_finite(row[metric], metric) for row in rows if row["fold"] == fold],
            dtype=np.float64,
        )
        if values.shape != (21,):
            raise ContractError(f"bootstrap Fold {fold} requires 21 sources")
        by_fold[fold] = values
    rng = np.random.default_rng(seed)
    draws = np.empty(samples, dtype=np.float64)
    for start in range(0, samples, 1000):
        count = min(1000, samples - start)
        fold_means = []
        for fold in FOLDS:
            indices = rng.integers(0, 21, size=(count, 21))
            fold_means.append(by_fold[fold][indices].mean(axis=1))
        draws[start : start + count] = 0.5 * (fold_means[0] + fold_means[1])
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
    summary: dict[str, Any] = {"cells": {}, "comparisons": {}}
    for cell in ("Q0_beta0", "Q0_beta1", "QC_beta0", "QC_beta1"):
        summary["cells"][cell] = {}
        for metric in SUMMARY_METRICS:
            means = {
                fold: float(np.mean([
                    _finite(row[metric], metric)
                    for row in source_rows
                    if row["cell"] == cell and row["fold"] == fold
                ]))
                for fold in FOLDS
            }
            means["combined"] = 0.5 * (means["A"] + means["B"])
            summary["cells"][cell][metric] = means
    for comparison in COMPARISONS:
        selected = [row for row in delta_rows if row["comparison"] == comparison]
        if len(selected) != 42:
            raise ContractError(f"comparison {comparison} requires 42 source rows")
        summary["comparisons"][comparison] = {}
        for metric in SUMMARY_METRICS:
            means = {
                fold: float(np.mean([
                    _finite(row[metric], metric) for row in selected if row["fold"] == fold
                ]))
                for fold in FOLDS
            }
            means["combined"] = 0.5 * (means["A"] + means["B"])
            means["bootstrap"] = stratified_cluster_bootstrap(selected, metric)
            summary["comparisons"][comparison][metric] = means
    return summary


def classify_weight_state(
    summary: Mapping[str, Any], controls: Mapping[str, Any], threshold: float = 0.01
) -> dict[str, Any]:
    if controls.get("status") != "PASS":
        raise ContractError("execution controls must pass before classification")
    comparisons = summary.get("comparisons", {})
    immediate = comparisons["q0_beta1_minus_native_q0"][PRIMARY]
    beta0 = comparisons["native_q0_minus_qc_bias_zero"][PRIMARY]
    beta1 = comparisons["q0_beta1_minus_native_qc"][PRIMARY]
    inactive = all(
        abs(_finite(immediate[scope], f"immediate {scope}")) <= threshold
        for scope in (*FOLDS, "combined")
    )
    material = not inactive
    beta0_point = _finite(beta0["combined"], "beta0 weight contrast")
    beta1_point = _finite(beta1["combined"], "beta1 weight contrast")
    beta0_high = _finite(beta0["bootstrap"]["ci95_high"], "beta0 CI high")
    beta1_high = _finite(beta1["bootstrap"]["ci95_high"], "beta1 CI high")
    robust = (
        inactive
        and beta0_point <= -threshold
        and beta1_point <= -threshold
        and beta0_high < 0
        and beta1_high < 0
    )
    directional = (
        inactive
        and beta0_point <= -threshold
        and beta1_point <= -threshold
        and not robust
    )
    if robust:
        overall = "WEIGHT_STATE_DOMINANT_ROBUST"
    elif directional:
        overall = "WEIGHT_STATE_DOMINANT_DIRECTIONAL"
    elif material:
        overall = "INFERENCE_BETA_MATERIAL_OR_MIXED"
    else:
        overall = "MIXED_OR_INCONCLUSIVE"
    if beta1_high < 0:
        beta1_class = "WEIGHT_STATE_ADVANTAGE_AT_BETA1_ROBUST"
    elif beta1_point < 0:
        beta1_class = "WEIGHT_STATE_ADVANTAGE_AT_BETA1_DIRECTIONAL"
    else:
        beta1_class = "NO_Q0_WEIGHT_STATE_ADVANTAGE_AT_BETA1"
    return {
        "protocol_id": PROTOCOL_ID,
        "execution_controls": dict(controls),
        "q0_reverse_effect_classification": (
            "Q0_REVERSE_EFFECT_INACTIVE" if inactive else "Q0_REVERSE_EFFECT_MATERIAL"
        ),
        "weight_state_beta1_classification": beta1_class,
        "overall_classification": overall,
        "factorial_interaction_role": "REQUIRED_DESCRIPTIVE_NO_EQUIVALENCE_GATE",
        "practical_inactivity_threshold_mm": threshold,
        "single_seed_limitation": True,
        "formal_confirmation_claim": False,
        "round_b_authorized": False,
        "automatic_beta_tuning": False,
        "automatic_retry": False,
        "automatic_next_run": False,
    }


def analyze_reverse_rows(
    rows: Sequence[Mapping[str, Any]],
    frozen_round_a_rows: Sequence[Mapping[str, Any]],
    frozen_qc_rows: Sequence[Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    controls = validate_execution_controls(
        rows, frozen_round_a_rows, frozen_qc_rows, protocol
    )
    sources = aggregate_factorial_sources(rows, frozen_round_a_rows, frozen_qc_rows)
    deltas = paired_factorial_deltas(sources)
    summary = build_summary(sources, deltas)
    receipt = classify_weight_state(
        summary,
        controls,
        float(protocol["numeric_contract"]["inference_effect_practical_inactivity_threshold_mm"]),
    )
    return sources, deltas, summary, receipt


def _write_json_exclusive(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--reverse-case-metrics", required=True, type=Path)
    parser.add_argument("--frozen-round-a-case-metrics", required=True, type=Path)
    parser.add_argument("--frozen-round-a-case-metrics-sha256", required=True)
    parser.add_argument("--frozen-qc-case-metrics", required=True, type=Path)
    parser.add_argument("--frozen-qc-case-metrics-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if sha256_file(args.protocol) != args.protocol_sha256 or args.protocol_sha256 != PROTOCOL_SHA256:
        raise ContractError("protocol SHA256 mismatch")
    if sha256_file(args.frozen_round_a_case_metrics) != args.frozen_round_a_case_metrics_sha256:
        raise ContractError("frozen Round A case-metrics SHA256 mismatch")
    if sha256_file(args.frozen_qc_case_metrics) != args.frozen_qc_case_metrics_sha256:
        raise ContractError("frozen QC case-metrics SHA256 mismatch")
    protocol = load_json(args.protocol)
    rows = read_csv(args.reverse_case_metrics)
    frozen_round_a = read_csv(args.frozen_round_a_case_metrics)
    frozen_qc = read_csv(args.frozen_qc_case_metrics)
    sources, deltas, summary, receipt = analyze_reverse_rows(
        rows, frozen_round_a, frozen_qc, protocol
    )
    args.output_dir.mkdir(parents=False, exist_ok=False)
    write_csv(args.output_dir / "per_condition_source_metrics.csv", sources)
    write_csv(args.output_dir / "factorial_paired_deltas.csv", deltas)
    _write_json_exclusive(args.output_dir / "factorial_summary.json", summary)
    _write_json_exclusive(args.output_dir / "weight_state_classification_receipt.json", receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
