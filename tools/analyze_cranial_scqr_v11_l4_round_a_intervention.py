#!/usr/bin/env python3
"""Pure, fail-closed analyzer for the Cranial-SCQR Round A-I intervention.

Importing this module performs no checkpoint, dataset, CUDA, or filesystem
work.  Its public functions are intentionally usable by synthetic CPU tests.
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


PROTOCOL_ID = "cranial-scqr-v1.1-L4-roundA-I-same-QC-checkpoint-intervention-v2"
PROTOCOL_STATUS = "FROZEN_REVISED_PROTOCOL_IMPLEMENTATION_AND_EXECUTION_NOT_AUTHORIZED"
PERMUTATION_SEED_NAMESPACE_PROTOCOL_ID = (
    "cranial-scqr-v1.1-L4-roundA-I-same-QC-checkpoint-intervention-v1"
)
FOLDS = ("A", "B")
SEED = 0
CONDITIONS = (
    "native_qc",
    "bias_zero",
    "case_mean_probability",
    "fixed_seed_within_case_probability_permutation",
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
OPTIONAL_DISTANCE_METRICS = ("rim_contact_cd_l1_mm", "rim_contact_hd95_mm")
OPTIONAL_UNIT_INTERVAL_METRICS = ("rim_contact_precision",)
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
COMPARISONS = (
    "bias_zero_minus_native_qc",
    "fixed_permutation_minus_native_qc",
    "case_mean_probability_minus_bias_zero",
    "bias_zero_minus_frozen_Q0",
)
COMPARISON_SIDES = {
    "bias_zero_minus_native_qc": ("bias_zero", "native_qc"),
    "fixed_permutation_minus_native_qc": (
        "fixed_seed_within_case_probability_permutation",
        "native_qc",
    ),
    "case_mean_probability_minus_bias_zero": (
        "case_mean_probability",
        "bias_zero",
    ),
}
COMPARISON_ROLES = {
    "bias_zero_minus_native_qc": "SCIENTIFIC_MECHANISM_COMPARISON",
    "fixed_permutation_minus_native_qc": "SCIENTIFIC_MECHANISM_COMPARISON",
    "case_mean_probability_minus_bias_zero": (
        "DIAGNOSTIC_ONLY_NOT_USED_FOR_SCIENTIFIC_CLASSIFICATION"
    ),
    "bias_zero_minus_frozen_Q0": "SCIENTIFIC_MECHANISM_COMPARISON",
}
SCIENTIFIC_CLASSIFICATION_COMPARISONS = (
    "bias_zero_minus_native_qc",
    "fixed_permutation_minus_native_qc",
    "bias_zero_minus_frozen_Q0",
)
DIAGNOSTIC_ONLY_COMPARISONS = ("case_mean_probability_minus_bias_zero",)


class ContractError(RuntimeError):
    """Raised whenever a frozen intervention contract is violated."""


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


def _integer(value: Any, name: str) -> int:
    number = _finite(value, name)
    integer = int(number)
    if number != integer:
        raise ContractError(f"{name} is not an integer: {value!r}")
    return integer


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    """Validate all analysis-critical constants without touching bound files."""

    if protocol.get("protocol_id") != PROTOCOL_ID:
        raise ContractError("intervention protocol identity mismatch")
    if protocol.get("status") != PROTOCOL_STATUS:
        raise ContractError("intervention protocol status mismatch")
    matrix = protocol.get("checkpoint_matrix")
    expected_matrix = [("QC", fold, SEED) for fold in FOLDS]
    if not isinstance(matrix, list) or [
        (row.get("candidate"), row.get("fold"), row.get("seed")) for row in matrix
    ] != expected_matrix:
        raise ContractError("checkpoint matrix must be exactly QC Fold A/B seed 0")
    if protocol.get("conditions", {}).get("order") != list(CONDITIONS):
        raise ContractError("intervention condition order mismatch")
    if protocol.get("conditions", {}).get(
        "case_mean_probability_is_bias_zero_softmax_negative_control"
    ) is not True:
        raise ContractError("negative-control identity is not frozen")
    if (
        protocol.get("conditions", {}).get("permutation_seed_namespace_protocol_id")
        != PERMUTATION_SEED_NAMESPACE_PROTOCOL_ID
    ):
        raise ContractError("fixed permutation namespace mismatch")
    dev = protocol.get("development_allowlists", {})
    for fold in FOLDS:
        item = dev.get(fold, {})
        if (
            item.get("cases") != 105
            or item.get("sources") != 21
            or item.get("cases_per_source") != 5
        ):
            raise ContractError(f"Fold {fold} development cardinality mismatch")
    analysis = protocol.get("analysis_contract", {})
    if analysis.get("comparison_order") != list(COMPARISONS):
        raise ContractError("comparison order mismatch")
    if analysis.get("comparison_roles") != COMPARISON_ROLES:
        raise ContractError("comparison roles mismatch")
    if analysis.get("scientific_classification_comparisons") != list(
        SCIENTIFIC_CLASSIFICATION_COMPARISONS
    ):
        raise ContractError("scientific classification comparison set mismatch")
    if analysis.get("bootstrap_seed") != 20260910:
        raise ContractError("bootstrap seed mismatch")
    if analysis.get("bootstrap_samples") != 10000:
        raise ContractError("bootstrap sample count mismatch")
    if analysis.get("round_b_authorized_by_any_result") is not False:
        raise ContractError("protocol must never authorize Round B")
    negative = protocol.get("numeric_contract", {}).get("case_mean_vs_bias_zero", {})
    if (
        negative.get("acceptance_layer") != "query_attention"
        or negative.get("attention_max_abs") != 1e-6
        or negative.get("attention_comparison") != "less_than_or_equal"
        or negative.get("gate_scope") != "every evaluated case independently"
        or negative.get("acceptance_receipt_field")
        != "case_mean_probability_attention_equivalence_pass"
        or negative.get("output_level_equality_claim") is not False
        or negative.get("downstream_equality_acceptance_gates") is not False
    ):
        raise ContractError("v2 attention-only negative-control contract mismatch")
    prediction = negative.get("prediction_diagnostics", {})
    derived = negative.get("derived_metric_diagnostics", {})
    logits = negative.get("logit_diagnostics", {})
    if (
        prediction.get("role") != "NON_GATING_DIAGNOSTIC"
        or prediction.get("required_scalar")
        != "negative_control_prediction_max_abs_normalized"
        or prediction.get("acceptance_threshold") is not None
        or prediction.get("scale_aware_tolerance_introduced") is not False
        or derived.get("acceptance_threshold") is not None
        or logits.get("role") != "OPTIONAL_NON_GATING_DIAGNOSTIC"
        or logits.get("acceptance_threshold") is not None
        or logits.get("additional_forwards") != 0
    ):
        raise ContractError("v2 non-gating diagnostic schema mismatch")
    execution = protocol.get("future_execution_contract", {})
    expected_counts = {
        "checkpoint_loads_expected": 2,
        "model_case_forward_calls_expected": 840,
        "npz_opens_expected": 210,
        "partial_reads_expected": 210,
        "implant_reads_expected": 210,
        "gt_reads_expected": 210,
        "temporary_probability_hooks_expected": 630,
        "temporary_probability_hooks_removed_expected": 630,
    }
    if any(execution.get(key) != value for key, value in expected_counts.items()):
        raise ContractError("future execution counter contract mismatch")
    if execution.get("execution_authorized_by_this_protocol") is not False:
        raise ContractError("implementation protocol cannot authorize execution")
    boundary = protocol.get("authorization_boundary", {})
    forbidden = (
        "real_checkpoint_loads_authorized",
        "real_npz_opens_authorized",
        "gpu_use_authorized",
        "development_evaluation_authorized",
        "training_or_bncal_authorized",
        "round_b_authorized",
    )
    if any(boundary.get(name) is not False for name in forbidden):
        raise ContractError("implementation protocol crosses an authorization boundary")


def _row_identity(row: Mapping[str, Any]) -> tuple[str, str, int, str]:
    condition = str(row.get("condition", ""))
    fold = str(row.get("fold", ""))
    try:
        seed = int(row.get("seed"))
    except (TypeError, ValueError) as exc:
        raise ContractError("invalid seed") from exc
    case_id = str(row.get("case_id", ""))
    if condition not in CONDITIONS or fold not in FOLDS or seed != SEED or not case_id:
        raise ContractError("invalid condition/fold/seed/case identity")
    return condition, fold, seed, case_id


def validate_intervention_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Require the exact 4-condition x 2-fold x 105-case matrix."""

    if len(rows) != 840:
        raise ContractError(f"expected 840 intervention rows, found {len(rows)}")
    by_partition: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    identities: set[tuple[str, str, int, str]] = set()
    metadata_by_case: dict[tuple[str, str], tuple[str, str, str]] = {}
    for index, row in enumerate(rows):
        identity = _row_identity(row)
        if identity in identities:
            raise ContractError(f"duplicate intervention row: {identity}")
        identities.add(identity)
        condition, fold, _, case_id = identity
        if str(row.get("candidate")) != "QC":
            raise ContractError(f"row {index}: only QC is allowed")
        source = str(row.get("source_skull_id", ""))
        skull = str(row.get("skull_id", ""))
        defect = str(row.get("defect_type", ""))
        if not source or not skull or not defect:
            raise ContractError(f"row {index}: missing case metadata")
        metadata = (source, skull, defect)
        case_key = (fold, case_id)
        previous = metadata_by_case.setdefault(case_key, metadata)
        if previous != metadata:
            raise ContractError(f"condition metadata mismatch: {fold}/{case_id}")
        for field in DISTANCE_METRICS:
            if field not in row:
                raise ContractError(f"row {index}: missing {field}")
            if field in OPTIONAL_DISTANCE_METRICS:
                _optional_number(row[field], f"row {index} {field}")
            else:
                _finite(row[field], f"row {index} {field}")
        for field in UNIT_INTERVAL_METRICS:
            if field not in row:
                raise ContractError(f"row {index}: missing {field}")
            if field in OPTIONAL_UNIT_INTERVAL_METRICS:
                _optional_number(row[field], f"row {index} {field}")
            else:
                _finite(row[field], f"row {index} {field}")
        for field in INTEGER_FIELDS:
            if field not in row:
                raise ContractError(f"row {index}: missing {field}")
            value = _integer(row[field], f"row {index} {field}")
            if field in ("zero_contact_2mm", "disaster") and value not in (0, 1):
                raise ContractError(f"row {index}: {field} must be binary")
        coarse_error = _finite(
            row.get("coarse_condition_max_abs_normalized"),
            f"row {index} coarse_condition_max_abs_normalized",
        )
        if coarse_error < 0:
            raise ContractError("coarse invariance error cannot be negative")
        if condition == "case_mean_probability":
            for field in (
                "negative_control_attention_max_abs",
                "negative_control_prediction_max_abs_normalized",
            ):
                if _finite(row.get(field), f"row {index} {field}") < 0:
                    raise ContractError(f"row {index}: negative control error below zero")
        by_partition[(condition, fold)].append(row)

    for condition in CONDITIONS:
        for fold in FOLDS:
            part = by_partition[(condition, fold)]
            if len(part) != 105:
                raise ContractError(f"{condition}/{fold} requires 105 cases")
            sources: dict[str, set[str]] = defaultdict(set)
            defects: dict[str, set[str]] = defaultdict(set)
            for row in part:
                source = str(row["source_skull_id"])
                sources[source].add(str(row["case_id"]))
                defects[source].add(str(row["defect_type"]))
            if len(sources) != 21 or any(len(values) != 5 for values in sources.values()):
                raise ContractError(f"{condition}/{fold} violates 21 x 5 structure")
            if any(len(values) != 5 for values in defects.values()):
                raise ContractError(f"{condition}/{fold} lacks five unique defects per source")
        cases_a = {str(row["case_id"]) for row in by_partition[(condition, "A")]}
        cases_b = {str(row["case_id"]) for row in by_partition[(condition, "B")]}
        if cases_a & cases_b:
            raise ContractError("Fold A/B case IDs overlap")
    for fold in FOLDS:
        reference = {str(row["case_id"]) for row in by_partition[(CONDITIONS[0], fold)]}
        for condition in CONDITIONS[1:]:
            observed = {str(row["case_id"]) for row in by_partition[(condition, fold)]}
            if observed != reference:
                raise ContractError(f"unpaired condition cases: {condition}/{fold}")
    sources_a = {
        str(row["source_skull_id"])
        for row in by_partition[(CONDITIONS[0], "A")]
    }
    sources_b = {
        str(row["source_skull_id"])
        for row in by_partition[(CONDITIONS[0], "B")]
    }
    if sources_a & sources_b:
        raise ContractError("Fold A/B source skulls overlap")


def _reference_rows(
    rows: Sequence[Mapping[str, Any]], candidate: str
) -> dict[tuple[str, str], Mapping[str, Any]]:
    output: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        if str(row.get("candidate")) != candidate:
            continue
        fold = str(row.get("fold", ""))
        case_id = str(row.get("case_id", ""))
        if fold not in FOLDS or not case_id or int(row.get("seed", -1)) != SEED:
            raise ContractError(f"invalid frozen {candidate} reference identity")
        key = (fold, case_id)
        if key in output:
            raise ContractError(f"duplicate frozen {candidate} reference: {key}")
        output[key] = row
    if len(output) != 210:
        raise ContractError(f"frozen {candidate} reference requires 210 rows")
    return output


def _optional_number(value: Any, name: str) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name} is not numeric: {value!r}") from exc
    if math.isnan(number):
        return None
    if not math.isfinite(number):
        raise ContractError(f"{name} is nonfinite: {value!r}")
    return number


def _assert_close(left: Any, right: Any, tolerance: float, name: str) -> float:
    left_number = _optional_number(left, f"{name} left")
    right_number = _optional_number(right, f"{name} right")
    if left_number is None or right_number is None:
        if left_number is right_number:
            return 0.0
        raise ContractError(f"{name}: NA mismatch")
    difference = abs(left_number - right_number)
    if difference > tolerance:
        raise ContractError(
            f"{name}: abs difference {difference} exceeds {tolerance}"
        )
    return difference


def _diagnostic_abs_difference(
    left: Any, right: Any, name: str
) -> tuple[float | None, bool]:
    """Return a finite absolute difference and whether optional NA status differs."""

    left_number = _optional_number(left, f"{name} left")
    right_number = _optional_number(right, f"{name} right")
    if left_number is None or right_number is None:
        return None, left_number is not right_number
    return abs(left_number - right_number), False


def validate_execution_controls(
    rows: Sequence[Mapping[str, Any]],
    frozen_v2_rows: Sequence[Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate native reproduction, the softmax negative control and coarse invariance."""

    validate_protocol(protocol)
    validate_intervention_rows(rows)
    frozen_qc = _reference_rows(frozen_v2_rows, "QC")
    _reference_rows(frozen_v2_rows, "Q0")
    by_key = {
        (str(row["condition"]), str(row["fold"]), str(row["case_id"])): row
        for row in rows
    }
    numeric = protocol["numeric_contract"]
    reproduction = numeric["native_reproduction"]
    negative = numeric["case_mean_vs_bias_zero"]
    maxima: dict[str, Any] = {
        "native_distance_metric_max_abs_mm": 0.0,
        "native_unit_interval_metric_max_abs": 0.0,
        "negative_control_distance_metric_max_abs_mm": 0.0,
        "negative_control_unit_interval_metric_max_abs": 0.0,
        "negative_control_attention_max_abs": 0.0,
        "negative_control_prediction_max_abs_normalized": 0.0,
        "coarse_condition_max_abs_normalized": 0.0,
    }
    distance_maxima = {field: 0.0 for field in DISTANCE_METRICS}
    unit_interval_maxima = {field: 0.0 for field in UNIT_INTERVAL_METRICS}
    optional_na_mismatches = {
        field: 0
        for field in (*OPTIONAL_DISTANCE_METRICS, *OPTIONAL_UNIT_INTERVAL_METRICS)
    }
    integer_mismatches = {field: 0 for field in INTEGER_FIELDS}
    for fold, case_id in sorted(frozen_qc):
        native = by_key[("native_qc", fold, case_id)]
        zero = by_key[("bias_zero", fold, case_id)]
        mean = by_key[("case_mean_probability", fold, case_id)]
        reference = frozen_qc[(fold, case_id)]
        for field in DISTANCE_METRICS:
            difference = _assert_close(
                native[field], reference[field],
                float(reproduction["distance_metrics_max_abs_mm"]),
                f"native reproduction {fold}/{case_id}/{field}",
            )
            maxima["native_distance_metric_max_abs_mm"] = max(
                maxima["native_distance_metric_max_abs_mm"], difference
            )
            difference, na_mismatch = _diagnostic_abs_difference(
                mean[field], zero[field],
                f"negative-control diagnostic {fold}/{case_id}/{field}",
            )
            if na_mismatch:
                optional_na_mismatches[field] += 1
            if difference is not None:
                distance_maxima[field] = max(distance_maxima[field], difference)
                maxima["negative_control_distance_metric_max_abs_mm"] = max(
                    maxima["negative_control_distance_metric_max_abs_mm"], difference
                )
        for field in UNIT_INTERVAL_METRICS:
            difference = _assert_close(
                native[field], reference[field],
                float(reproduction["unit_interval_metrics_max_abs"]),
                f"native reproduction {fold}/{case_id}/{field}",
            )
            maxima["native_unit_interval_metric_max_abs"] = max(
                maxima["native_unit_interval_metric_max_abs"], difference
            )
            difference, na_mismatch = _diagnostic_abs_difference(
                mean[field], zero[field],
                f"negative-control diagnostic {fold}/{case_id}/{field}",
            )
            if na_mismatch:
                optional_na_mismatches[field] += 1
            if difference is not None:
                unit_interval_maxima[field] = max(
                    unit_interval_maxima[field], difference
                )
                maxima["negative_control_unit_interval_metric_max_abs"] = max(
                    maxima["negative_control_unit_interval_metric_max_abs"], difference
                )
        for field in INTEGER_FIELDS:
            if _integer(native[field], field) != _integer(reference[field], field):
                raise ContractError(f"native integer mismatch: {fold}/{case_id}/{field}")
            if _integer(mean[field], field) != _integer(zero[field], field):
                integer_mismatches[field] += 1
        attention_error = _finite(
            mean["negative_control_attention_max_abs"],
            "negative_control_attention_max_abs",
        )
        prediction_error = _finite(
            mean["negative_control_prediction_max_abs_normalized"],
            "negative_control_prediction_max_abs_normalized",
        )
        maxima["negative_control_attention_max_abs"] = max(
            maxima["negative_control_attention_max_abs"], attention_error
        )
        maxima["negative_control_prediction_max_abs_normalized"] = max(
            maxima["negative_control_prediction_max_abs_normalized"], prediction_error
        )
        for condition in CONDITIONS:
            coarse_error = _finite(
                by_key[(condition, fold, case_id)]["coarse_condition_max_abs_normalized"],
                "coarse_condition_max_abs_normalized",
            )
            maxima["coarse_condition_max_abs_normalized"] = max(
                maxima["coarse_condition_max_abs_normalized"], coarse_error
            )

    thresholds = {
        "negative_control_attention_max_abs": float(negative["attention_max_abs"]),
        "coarse_condition_max_abs_normalized": float(
            numeric["coarse_condition_invariance_max_abs_normalized"]
        ),
    }
    for key, threshold in thresholds.items():
        if maxima[key] > threshold:
            raise ContractError(f"{key}={maxima[key]} exceeds {threshold}")
    return {
        "status": "PASS",
        "native_reproduction_pass": True,
        "case_mean_probability_attention_equivalence_pass": True,
        "downstream_negative_control_diagnostics_non_gating": True,
        "coarse_condition_invariance_pass": True,
        "maxima": maxima,
        "negative_control_downstream_diagnostics": {
            "prediction_max_abs_normalized": maxima[
                "negative_control_prediction_max_abs_normalized"
            ],
            "distance_metric_max_abs_mm_by_field": distance_maxima,
            "unit_interval_metric_max_abs_by_field": unit_interval_maxima,
            "optional_na_mismatch_count_by_field": optional_na_mismatches,
            "integer_and_boolean_mismatch_count_by_field": integer_mismatches,
        },
    }


def aggregate_intervention_sources(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    validate_intervention_rows(rows)
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["condition"]), str(row["fold"]), str(row["source_skull_id"]))].append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(groups, key=lambda x: (CONDITIONS.index(x[0]), FOLDS.index(x[1]), x[2])):
        group = groups[key]
        if len(group) != 5 or len({str(row["defect_type"]) for row in group}) != 5:
            raise ContractError(f"source group {key} is not five unique defects")
        result: dict[str, Any] = {
            "condition": key[0],
            "fold": key[1],
            "seed": SEED,
            "source_skull_id": key[2],
            "case_count": 5,
            "zero_contact_2mm_count": sum(_integer(row["zero_contact_2mm"], "zero") for row in group),
            "disaster_count": sum(_integer(row["disaster"], "disaster") for row in group),
        }
        for metric in SUMMARY_METRICS:
            result[metric] = float(np.mean([_finite(row[metric], metric) for row in group]))
        output.append(result)
    if len(output) != 168:
        raise ContractError("intervention source aggregation must produce 168 rows")
    return output


def aggregate_frozen_q0_sources(
    frozen_v2_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = _reference_rows(frozen_v2_rows, "Q0")
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for (fold, _), row in rows.items():
        groups[(fold, str(row["source_skull_id"]))].append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        if len(group) != 5 or len({str(row["defect_type"]) for row in group}) != 5:
            raise ContractError(f"frozen Q0 source group {key} is incomplete")
        result: dict[str, Any] = {
            "condition": "frozen_Q0",
            "fold": key[0],
            "seed": SEED,
            "source_skull_id": key[1],
            "case_count": 5,
        }
        for metric in SUMMARY_METRICS:
            result[metric] = float(np.mean([_finite(row[metric], metric) for row in group]))
        output.append(result)
    if len(output) != 42:
        raise ContractError("frozen Q0 source aggregation must produce 42 rows")
    return output


def paired_source_deltas(
    source_rows: Sequence[Mapping[str, Any]],
    frozen_q0_sources: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_condition = {
        (str(row["condition"]), str(row["fold"]), str(row["source_skull_id"])): row
        for row in source_rows
    }
    q0 = {
        (str(row["fold"]), str(row["source_skull_id"])): row
        for row in frozen_q0_sources
    }
    output: list[dict[str, Any]] = []
    native_keys = sorted(
        (fold, source)
        for condition, fold, source in by_condition
        if condition == "native_qc"
    )
    if len(native_keys) != 42 or set(native_keys) != set(q0):
        raise ContractError("intervention and frozen Q0 source identities differ")
    for comparison in COMPARISONS:
        for fold, source in native_keys:
            if comparison == "bias_zero_minus_frozen_Q0":
                left = by_condition[("bias_zero", fold, source)]
                right = q0[(fold, source)]
            else:
                left_name, right_name = COMPARISON_SIDES[comparison]
                left = by_condition[(left_name, fold, source)]
                right = by_condition[(right_name, fold, source)]
            result: dict[str, Any] = {
                "comparison": comparison,
                "comparison_role": COMPARISON_ROLES[comparison],
                "fold": fold,
                "seed": SEED,
                "source_skull_id": source,
            }
            for metric in SUMMARY_METRICS:
                result[metric] = _finite(left[metric], metric) - _finite(right[metric], metric)
            output.append(result)
    if len(output) != 168:
        raise ContractError("paired comparison table must contain 168 rows")
    return output


def stratified_cluster_bootstrap(
    deltas: Sequence[Mapping[str, Any]],
    metric: str,
    *,
    seed: int = 20260910,
    samples: int = 10000,
) -> dict[str, float | int]:
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


def _case_win_counts(
    rows: Sequence[Mapping[str, Any]],
    frozen_v2_rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, int]]:
    by_key = {
        (str(row["condition"]), str(row["fold"]), str(row["case_id"])): row
        for row in rows
    }
    q0 = _reference_rows(frozen_v2_rows, "Q0")
    identities = sorted(q0)
    output: dict[str, dict[str, int]] = {}
    for comparison in COMPARISONS:
        deltas = []
        for fold, case_id in identities:
            if comparison == "bias_zero_minus_frozen_Q0":
                left = by_key[("bias_zero", fold, case_id)]
                right = q0[(fold, case_id)]
            else:
                left_name, right_name = COMPARISON_SIDES[comparison]
                left = by_key[(left_name, fold, case_id)]
                right = by_key[(right_name, fold, case_id)]
            deltas.append(_finite(left[PRIMARY], PRIMARY) - _finite(right[PRIMARY], PRIMARY))
        output[comparison] = {
            "left_better": sum(value < 0 for value in deltas),
            "tied": sum(value == 0 for value in deltas),
            "left_worse": sum(value > 0 for value in deltas),
        }
    return output


def build_summary(
    source_rows: Sequence[Mapping[str, Any]],
    delta_rows: Sequence[Mapping[str, Any]],
    case_rows: Sequence[Mapping[str, Any]],
    frozen_v2_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    summary: dict[str, Any] = {"conditions": {}, "comparisons": {}}
    for condition in CONDITIONS:
        summary["conditions"][condition] = {}
        for metric in SUMMARY_METRICS:
            folds = {}
            for fold in FOLDS:
                values = [
                    _finite(row[metric], metric)
                    for row in source_rows
                    if row["condition"] == condition and row["fold"] == fold
                ]
                if len(values) != 21:
                    raise ContractError(f"missing source means: {condition}/{fold}/{metric}")
                folds[fold] = float(np.mean(values))
            folds["combined"] = 0.5 * (folds["A"] + folds["B"])
            summary["conditions"][condition][metric] = folds
    case_counts = _case_win_counts(case_rows, frozen_v2_rows)
    for comparison in COMPARISONS:
        selected = [row for row in delta_rows if row["comparison"] == comparison]
        if len(selected) != 42:
            raise ContractError(f"comparison {comparison} requires 42 sources")
        summary["comparisons"][comparison] = {
            "comparison_role": COMPARISON_ROLES[comparison],
            "case_primary_win_tie_loss": case_counts[comparison],
            "source_primary_win_tie_loss": {
                "left_better": sum(_finite(row[PRIMARY], PRIMARY) < 0 for row in selected),
                "tied": sum(_finite(row[PRIMARY], PRIMARY) == 0 for row in selected),
                "left_worse": sum(_finite(row[PRIMARY], PRIMARY) > 0 for row in selected),
            },
        }
        for metric in SUMMARY_METRICS:
            folds = {
                fold: float(np.mean([
                    _finite(row[metric], metric)
                    for row in selected if row["fold"] == fold
                ]))
                for fold in FOLDS
            }
            folds["combined"] = 0.5 * (folds["A"] + folds["B"])
            folds["bootstrap"] = stratified_cluster_bootstrap(selected, metric)
            summary["comparisons"][comparison][metric] = folds
    return summary


def classify_mechanism(
    summary: Mapping[str, Any], controls: Mapping[str, Any], *, inactive_threshold: float = 0.01
) -> dict[str, Any]:
    if controls.get("status") != "PASS":
        raise ContractError("execution controls did not pass")
    if controls.get("case_mean_probability_attention_equivalence_pass") is not True:
        raise ContractError("attention negative control did not pass")
    if controls.get("downstream_negative_control_diagnostics_non_gating") is not True:
        raise ContractError("downstream negative-control diagnostics are not non-gating")
    comparisons = summary.get("comparisons", {})
    bias = comparisons["bias_zero_minus_native_qc"][PRIMARY]
    permutation = comparisons["fixed_permutation_minus_native_qc"][PRIMARY]
    training = comparisons["bias_zero_minus_frozen_Q0"][PRIMARY]
    robust_harm = (
        _finite(bias["A"], "bias A") <= 0
        and _finite(bias["B"], "bias B") <= 0
        and _finite(bias["bootstrap"]["ci95_high"], "bias CI high") < 0
    )
    robust_alignment_benefit = (
        _finite(bias["bootstrap"]["ci95_low"], "bias CI low") > 0
        and _finite(permutation["bootstrap"]["ci95_low"], "permutation CI low") > 0
    )
    inactive = all(
        abs(_finite(item[scope], f"inactive {scope}")) <= inactive_threshold
        for item in (bias, permutation)
        for scope in (*FOLDS, "combined")
    )
    directional_harm = _finite(bias["combined"], "bias combined") < 0
    if robust_harm:
        classification = "IMMEDIATE_BIAS_HARM_ROBUST"
    elif robust_alignment_benefit:
        classification = "SPATIAL_ALIGNMENT_BENEFIT_ROBUST"
    elif inactive:
        classification = "CONDITIONING_EFFECT_INACTIVE"
    elif directional_harm:
        classification = "IMMEDIATE_BIAS_HARM_DIRECTIONAL"
    else:
        classification = "MIXED_OR_INCONCLUSIVE"
    training_ci_low = _finite(training["bootstrap"]["ci95_low"], "training CI low")
    training_combined = _finite(training["combined"], "training combined")
    if training_ci_low > 0:
        training_gap = "TRAINING_PATH_RESIDUAL_GAP_ROBUST"
    elif training_combined > 0:
        training_gap = "TRAINING_PATH_RESIDUAL_GAP_DIRECTIONAL"
    else:
        training_gap = "NO_POSITIVE_TRAINING_PATH_RESIDUAL_GAP"
    return {
        "protocol_id": PROTOCOL_ID,
        "execution_controls": dict(controls),
        "scientific_classification_comparisons": list(
            SCIENTIFIC_CLASSIFICATION_COMPARISONS
        ),
        "diagnostic_only_comparisons": list(DIAGNOSTIC_ONLY_COMPARISONS),
        "mechanism_classification": classification,
        "training_path_classification": training_gap,
        "round_b_authorized": False,
        "automatic_next_run": False,
        "automatic_beta_tuning": False,
        "formal_confirmation_claim": False,
    }


def analyze_intervention_rows(
    rows: Sequence[Mapping[str, Any]],
    frozen_v2_rows: Sequence[Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    controls = validate_execution_controls(rows, frozen_v2_rows, protocol)
    sources = aggregate_intervention_sources(rows)
    q0_sources = aggregate_frozen_q0_sources(frozen_v2_rows)
    deltas = paired_source_deltas(sources, q0_sources)
    summary = build_summary(sources, deltas, rows, frozen_v2_rows)
    receipt = classify_mechanism(
        summary,
        controls,
        inactive_threshold=float(
            protocol["numeric_contract"]["conditioning_inactive_primary_max_abs_mm"]
        ),
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
    parser.add_argument("--intervention-case-metrics", required=True, type=Path)
    parser.add_argument("--frozen-v2-case-metrics", required=True, type=Path)
    parser.add_argument("--frozen-v2-case-metrics-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if sha256_file(args.protocol) != args.protocol_sha256:
        raise ContractError("protocol SHA256 mismatch")
    if sha256_file(args.frozen_v2_case_metrics) != args.frozen_v2_case_metrics_sha256:
        raise ContractError("frozen v2 case-metrics SHA256 mismatch")
    protocol = load_json(args.protocol)
    rows = read_csv(args.intervention_case_metrics)
    frozen = read_csv(args.frozen_v2_case_metrics)
    sources, deltas, summary, receipt = analyze_intervention_rows(rows, frozen, protocol)
    args.output_dir.mkdir(parents=False, exist_ok=False)
    write_csv(args.output_dir / "per_condition_source_metrics.csv", sources)
    write_csv(args.output_dir / "paired_intervention_deltas.csv", deltas)
    _write_json_exclusive(args.output_dir / "intervention_summary.json", summary)
    _write_json_exclusive(args.output_dir / "mechanism_classification_receipt.json", receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
