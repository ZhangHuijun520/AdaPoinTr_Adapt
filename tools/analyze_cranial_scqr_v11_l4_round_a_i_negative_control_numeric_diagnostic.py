#!/usr/bin/env python3
"""Pure scalar-only analyzer for the Round A-I negative-control diagnostic.

Importing this module performs no checkpoint, NPZ, model, CUDA, or filesystem
work.  The one-case result is descriptive evidence only: it cannot change a
threshold, rank a model, authorize a retry, or authorize Round B.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


PROTOCOL_ID = (
    "cranial-scqr-v1.1-L4-roundA-I-negative-control-numeric-diagnostic-v1"
)
PROTOCOL_STATUS = "FROZEN_DESIGN_IMPLEMENTATION_AND_EXECUTION_NOT_AUTHORIZED"
PROTOCOL_SHA256 = "10e7c777974f27fd92e55115942660910d18a21230a5699d244b9b3fffc2806f"
FOLD = "A"
CASE_ID = "train__000__frontoorbital"
RUN_KEY = "QC_foldA_seed0"
SEED = 0
CONDITIONS = ("bias_zero", "case_mean_probability")
FORWARD_ORDER = (
    "bias_zero_rep0",
    "case_mean_probability_rep0",
    "bias_zero_rep1",
    "case_mean_probability_rep1",
)
STAGES = (
    "original_contact_probability",
    "intervened_contact_probability",
    "coarse",
    "query_logits_raw",
    "query_logits_row_centered",
    "query_attention",
    "query_residual",
    "query_pre_decoder",
    "query_post_decoder",
    "predicted_implant",
)
PROPAGATION_STAGES = (
    "query_logits_row_centered",
    "query_attention",
    "query_residual",
    "query_pre_decoder",
    "query_post_decoder",
    "predicted_implant",
)
PAIR_SPECS = {
    "bias_zero_repeat": (
        "bias_zero_rep0",
        "bias_zero_rep1",
        "within-condition repeat control",
    ),
    "case_mean_probability_repeat": (
        "case_mean_probability_rep0",
        "case_mean_probability_rep1",
        "within-condition repeat control",
    ),
    "cross_condition_rep0": (
        "bias_zero_rep0",
        "case_mean_probability_rep0",
        "paired cross-condition comparison",
    ),
    "cross_condition_rep1": (
        "bias_zero_rep1",
        "case_mean_probability_rep1",
        "paired cross-condition comparison",
    ),
}
NORMALIZATION_SCALE_MM = 95.31487479704157
ATTENTION_REFERENCE = 1e-6
PREDICTION_REFERENCE = 1e-6
HEX = frozenset("0123456789abcdef")

SUMMARY_FLOATS = ("min", "max", "mean", "std_population", "rms")
ERROR_FLOATS = ("max_abs", "mean_abs", "rms", "p95_abs")
PREDICTION_ERROR_FLOATS = (
    "coordinate_max_abs_normalized",
    "coordinate_mean_abs_normalized",
    "coordinate_rms_normalized",
    "coordinate_p95_abs_normalized",
    "point_l2_max_normalized",
    "point_l2_mean_normalized",
    "point_l2_p95_normalized",
    "coordinate_max_abs_mm",
    "coordinate_rms_mm",
    "point_l2_max_mm",
    "point_l2_mean_mm",
    "point_l2_p95_mm",
)
LOGIT_SHIFT_FLOATS = (
    "raw_logit_delta_mean",
    "raw_logit_delta_std_population",
    "raw_logit_delta_max_deviation_from_its_mean",
    "expected_log_case_mean_probability",
    "raw_delta_mean_minus_expected_shift",
    "row_centered_logit_max_abs",
)


class ContractError(RuntimeError):
    """Raised whenever a frozen diagnostic contract is violated."""


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


def write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ContractError(f"{name} must be numeric, not boolean")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name} is not numeric") from exc
    if not math.isfinite(number):
        raise ContractError(f"{name} is nonfinite")
    return number


def _nonnegative_integer(value: Any, name: str) -> int:
    number = _finite(value, name)
    integer = int(number)
    if number != integer or integer < 0:
        raise ContractError(f"{name} must be a nonnegative integer")
    return integer


def _digest(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in HEX for character in value)
    ):
        raise ContractError(f"{name} must be a lowercase SHA256 digest")
    return value


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    """Validate every analysis-critical constant without touching bound files."""

    if protocol.get("protocol_id") != PROTOCOL_ID:
        raise ContractError("diagnostic protocol identity mismatch")
    if protocol.get("status") != PROTOCOL_STATUS:
        raise ContractError("diagnostic protocol status mismatch")
    boundary = protocol.get("authorization_boundary", {})
    if not isinstance(boundary, Mapping) or any(value is not False for value in boundary.values()):
        raise ContractError("diagnostic protocol crosses an authorization boundary")
    case = protocol.get("exact_case", {})
    if case.get("fold") != FOLD or case.get("case_id") != CASE_ID:
        raise ContractError("diagnostic case identity mismatch")
    if case.get("p4_design_audit_npz_open_count") != 0:
        raise ContractError("P4 design audit NPZ count mismatch")
    scale = case.get("normalization", {}).get("scale_mm_per_normalized_unit")
    if _finite(scale, "normalization scale") != NORMALIZATION_SCALE_MM:
        raise ContractError("normalization scale mismatch")
    checkpoint = protocol.get("exact_checkpoint", {})
    if (
        checkpoint.get("run_key") != RUN_KEY
        or checkpoint.get("candidate") != "QC"
        or checkpoint.get("seed") != SEED
        or checkpoint.get("contact_bias_beta") != 1.0
        or checkpoint.get("bncal_checkpoint", {}).get(
            "p4_design_audit_deserialization_count"
        )
        != 0
    ):
        raise ContractError("diagnostic checkpoint binding mismatch")
    execution = protocol.get("future_real_execution_contract", {})
    expected = {
        "checkpoint_loads": 1,
        "npz_open_events": 1,
        "partial_member_reads": 1,
        "forward_count": 4,
        "batch_size": 1,
        "workers": 0,
    }
    if any(execution.get(key) != value for key, value in expected.items()):
        raise ContractError("future execution count mismatch")
    if execution.get("allowed_npz_members") != ["partial"]:
        raise ContractError("only partial may be read")
    if execution.get("forbidden_npz_members") != ["implant", "gt"]:
        raise ContractError("implant/gt prohibition mismatch")
    if tuple(execution.get("forward_order", ())) != FORWARD_ORDER:
        raise ContractError("forward order mismatch")
    if tuple(execution.get("intervention_definitions", {}).keys()) != CONDITIONS:
        raise ContractError("condition set or order mismatch")
    if execution.get("forbidden_conditions") != [
        "native_qc",
        "fixed_probability_permutation",
    ]:
        raise ContractError("forbidden condition binding mismatch")
    measurement = protocol.get("scalar_only_measurement_contract", {})
    if measurement.get("raw_tensor_or_point_cloud_persistence_forbidden") is not True:
        raise ContractError("raw tensor persistence must be forbidden")
    if tuple(measurement.get("captured_stages", ())) != STAGES:
        raise ContractError("captured stage order mismatch")
    pairs = measurement.get("pairwise_comparisons", ())
    actual_pairs = {
        item.get("name"): (item.get("left"), item.get("right"), item.get("role"))
        for item in pairs
        if isinstance(item, Mapping)
    }
    if actual_pairs != PAIR_SPECS or len(pairs) != len(PAIR_SPECS):
        raise ContractError("pairwise comparison contract mismatch")
    reference = measurement.get("frozen_parent_threshold_reference_only", {})
    if (
        _finite(reference.get("attention_max_abs"), "attention reference")
        != ATTENTION_REFERENCE
        or _finite(
            reference.get("predicted_points_normalized_max_abs"),
            "prediction reference",
        )
        != PREDICTION_REFERENCE
    ):
        raise ContractError("parent threshold reference mismatch")
    interpretation = protocol.get("diagnostic_interpretation_contract", {})
    required_true = (
        "classification_is_descriptive_not_acceptance_gate",
        "one_case_generalization_forbidden",
        "model_ranking_forbidden",
        "scientific_significance_claim_forbidden",
        "threshold_relaxation_recommendation_forbidden_without_separate_evidence_and_authorization",
    )
    if any(interpretation.get(key) is not True for key in required_true):
        raise ContractError("diagnostic non-claim boundary mismatch")


def _validate_summary(value: Any, name: str) -> None:
    if not isinstance(value, Mapping):
        raise ContractError(f"{name} must be a scalar summary")
    expected = {
        "finite",
        "element_count",
        "dtype",
        "shape",
        *SUMMARY_FLOATS,
        "tensor_sha256",
    }
    if set(value) != expected:
        raise ContractError(f"{name} scalar summary fields mismatch")
    if value.get("finite") is not True:
        raise ContractError(f"{name} must be finite")
    count = _nonnegative_integer(value.get("element_count"), f"{name}.element_count")
    if count == 0:
        raise ContractError(f"{name} cannot be empty")
    if not isinstance(value.get("dtype"), str) or not value["dtype"]:
        raise ContractError(f"{name}.dtype is invalid")
    shape = value.get("shape")
    if not isinstance(shape, list) or not shape:
        raise ContractError(f"{name}.shape is invalid")
    product = 1
    for index, dimension in enumerate(shape):
        product *= _nonnegative_integer(dimension, f"{name}.shape[{index}]")
    if product != count:
        raise ContractError(f"{name} shape/count mismatch")
    numbers = {key: _finite(value.get(key), f"{name}.{key}") for key in SUMMARY_FLOATS}
    if numbers["min"] > numbers["max"] or numbers["std_population"] < 0 or numbers["rms"] < 0:
        raise ContractError(f"{name} summary range mismatch")
    _digest(value.get("tensor_sha256"), f"{name}.tensor_sha256")


def _validate_error(value: Any, name: str) -> None:
    if not isinstance(value, Mapping):
        raise ContractError(f"{name} must be an error object")
    expected = {"bitwise_equal", *ERROR_FLOATS, "left_tensor_sha256", "right_tensor_sha256"}
    if set(value) != expected or not isinstance(value.get("bitwise_equal"), bool):
        raise ContractError(f"{name} error fields mismatch")
    numbers = {key: _finite(value.get(key), f"{name}.{key}") for key in ERROR_FLOATS}
    if any(number < 0 for number in numbers.values()):
        raise ContractError(f"{name} errors must be nonnegative")
    if value["bitwise_equal"] and numbers["max_abs"] != 0.0:
        raise ContractError(f"{name} bitwise equality/max-abs mismatch")
    _digest(value.get("left_tensor_sha256"), f"{name}.left_tensor_sha256")
    _digest(value.get("right_tensor_sha256"), f"{name}.right_tensor_sha256")


def _condition_and_replicate(label: str) -> tuple[str, int]:
    if label.startswith("bias_zero_rep"):
        condition = "bias_zero"
    elif label.startswith("case_mean_probability_rep"):
        condition = "case_mean_probability"
    else:
        raise ContractError(f"invalid forward label: {label}")
    try:
        replicate = int(label.rsplit("rep", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ContractError(f"invalid forward replicate: {label}") from exc
    if replicate not in (0, 1):
        raise ContractError(f"invalid forward replicate: {label}")
    return condition, replicate


def validate_scalar_result(result: Mapping[str, Any]) -> None:
    """Validate the exact scalar-only result schema and reject payload leakage."""

    top = {
        "protocol_id",
        "status",
        "identity",
        "counters",
        "forward_order",
        "per_forward",
        "pairwise",
        "model_state",
        "parent_threshold_reference",
        "safeguards",
    }
    if set(result) != top:
        raise ContractError("scalar result top-level fields mismatch")
    if result.get("protocol_id") != PROTOCOL_ID or result.get("status") != "PASS_DIAGNOSTIC_ONLY":
        raise ContractError("scalar result identity/status mismatch")
    identity = result.get("identity", {})
    expected_identity = {
        "run_key": RUN_KEY,
        "candidate": "QC",
        "fold": FOLD,
        "seed": SEED,
        "case_id": CASE_ID,
        "source_skull_id": "000",
        "defect_type": "frontoorbital",
    }
    if identity != expected_identity:
        raise ContractError("case identity mismatch")
    counters = result.get("counters", {})
    expected_counts = {
        "checkpoint_loads": 1,
        "npz_open_events": 1,
        "member_partial": 1,
        "member_implant": 0,
        "member_gt": 0,
        "model_case_forward_calls": 4,
        "probability_hooks_registered": 4,
        "probability_hooks_removed": 4,
        "optimizer_constructions": 0,
        "optimizer_steps": 0,
        "model_parameter_updates": 0,
        "model_buffer_updates": 0,
    }
    if counters != expected_counts:
        raise ContractError("execution counter mismatch")
    if tuple(result.get("forward_order", ())) != FORWARD_ORDER:
        raise ContractError("result forward order mismatch")
    forwards = result.get("per_forward")
    if not isinstance(forwards, Mapping) or tuple(forwards) != FORWARD_ORDER:
        raise ContractError("per-forward key order mismatch")
    for label in FORWARD_ORDER:
        item = forwards[label]
        if not isinstance(item, Mapping) or set(item) != {"condition", "replicate", "stages"}:
            raise ContractError(f"{label} fields mismatch")
        condition, replicate = _condition_and_replicate(label)
        if item.get("condition") != condition or item.get("replicate") != replicate:
            raise ContractError(f"{label} condition/replicate mismatch")
        stages = item.get("stages")
        if not isinstance(stages, Mapping) or tuple(stages) != STAGES:
            raise ContractError(f"{label} stage order mismatch")
        for stage in STAGES:
            _validate_summary(stages[stage], f"{label}.{stage}")
    pairs = result.get("pairwise")
    if not isinstance(pairs, Mapping) or tuple(pairs) != tuple(PAIR_SPECS):
        raise ContractError("pairwise key order mismatch")
    for name, (left, right, role) in PAIR_SPECS.items():
        item = pairs[name]
        expected_pair_keys = {
            "left",
            "right",
            "role",
            "stage_errors",
            "prediction_errors",
            "logit_shift_scalars",
        }
        if not isinstance(item, Mapping) or set(item) != expected_pair_keys:
            raise ContractError(f"{name} fields mismatch")
        if (item.get("left"), item.get("right"), item.get("role")) != (left, right, role):
            raise ContractError(f"{name} identity mismatch")
        stage_errors = item.get("stage_errors")
        if not isinstance(stage_errors, Mapping) or tuple(stage_errors) != STAGES:
            raise ContractError(f"{name} stage-error order mismatch")
        for stage in STAGES:
            _validate_error(stage_errors[stage], f"{name}.{stage}")
        prediction = item.get("prediction_errors")
        if not isinstance(prediction, Mapping) or set(prediction) != set(PREDICTION_ERROR_FLOATS):
            raise ContractError(f"{name} prediction-error fields mismatch")
        if any(_finite(prediction[key], f"{name}.{key}") < 0 for key in PREDICTION_ERROR_FLOATS):
            raise ContractError(f"{name} prediction errors must be nonnegative")
        logit = item.get("logit_shift_scalars")
        if not isinstance(logit, Mapping) or set(logit) != set(LOGIT_SHIFT_FLOATS):
            raise ContractError(f"{name} logit-shift fields mismatch")
        for key in LOGIT_SHIFT_FLOATS:
            _finite(logit[key], f"{name}.{key}")
    state = result.get("model_state", {})
    if set(state) != {"before_sha256", "after_sha256", "unchanged"}:
        raise ContractError("model-state fields mismatch")
    before = _digest(state.get("before_sha256"), "model_state.before_sha256")
    after = _digest(state.get("after_sha256"), "model_state.after_sha256")
    if state.get("unchanged") is not True or before != after:
        raise ContractError("model state changed")
    reference = result.get("parent_threshold_reference", {})
    if set(reference) != {"attention_max_abs", "predicted_points_normalized_max_abs", "reference_only"}:
        raise ContractError("threshold reference fields mismatch")
    if (
        _finite(reference.get("attention_max_abs"), "attention reference") != ATTENTION_REFERENCE
        or _finite(reference.get("predicted_points_normalized_max_abs"), "prediction reference")
        != PREDICTION_REFERENCE
        or reference.get("reference_only") is not True
    ):
        raise ContractError("threshold reference mismatch")
    safeguards = result.get("safeguards", {})
    required_safeguards = {
        "raw_tensors_saved": False,
        "point_coordinates_saved": False,
        "implant_member_read": False,
        "gt_member_read": False,
        "threshold_changed": False,
        "automatic_retry": False,
        "round_a_i_retry_authorized": False,
        "round_b_authorized": False,
        "automatic_next_run": False,
    }
    if safeguards != required_safeguards:
        raise ContractError("scalar-only safeguard mismatch")


def _stage_max(result: Mapping[str, Any], pairs: Sequence[str], stage: str) -> float:
    return max(
        _finite(
            result["pairwise"][pair]["stage_errors"][stage]["max_abs"],
            f"{pair}.{stage}.max_abs",
        )
        for pair in pairs
    )


def analyze_scalar_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Return a threshold-free, descriptive diagnosis from a validated result."""

    validate_scalar_result(result)
    within_pairs = ("bias_zero_repeat", "case_mean_probability_repeat")
    cross_pairs = ("cross_condition_rep0", "cross_condition_rep1")
    within_by_stage = {stage: _stage_max(result, within_pairs, stage) for stage in STAGES}
    cross_by_stage = {stage: _stage_max(result, cross_pairs, stage) for stage in STAGES}
    repeat_present = any(value > 0.0 for value in within_by_stage.values())
    earliest = next(
        (stage for stage in PROPAGATION_STAGES if cross_by_stage[stage] > 0.0),
        "none",
    )
    stable_through_centered_logits = all(
        within_by_stage[stage] == 0.0
        for stage in (
            "original_contact_probability",
            "coarse",
            "query_logits_raw",
            "query_logits_row_centered",
        )
    )
    centered_roundoff = (
        stable_through_centered_logits
        and cross_by_stage["query_logits_row_centered"] > 0.0
    )
    softmax_first = (
        stable_through_centered_logits
        and cross_by_stage["query_logits_row_centered"] == 0.0
        and cross_by_stage["query_attention"] > 0.0
    )
    upstream = max(
        cross_by_stage["query_logits_row_centered"],
        cross_by_stage["query_attention"],
        cross_by_stage["query_residual"],
    )
    downstream = max(
        cross_by_stage["query_post_decoder"],
        cross_by_stage["predicted_implant"],
    )
    downstream_amplification = upstream > 0.0 and downstream > upstream
    repeat_prediction = within_by_stage["predicted_implant"]
    cross_prediction = cross_by_stage["predicted_implant"]
    inconclusive = repeat_present and repeat_prediction >= cross_prediction
    if inconclusive:
        diagnosis = "INCONCLUSIVE_REPEAT_VARIABILITY"
    elif centered_roundoff:
        diagnosis = "CONSTANT_SHIFT_ROUNDOFF_BEFORE_SOFTMAX"
    elif softmax_first:
        diagnosis = "SOFTMAX_ROUNDOFF_FIRST_VISIBLE"
    elif earliest == "none":
        diagnosis = "EXACT_NEGATIVE_CONTROL_REPRODUCED"
    elif downstream_amplification:
        diagnosis = "DOWNSTREAM_AMPLIFICATION_OF_NUMERIC_DIFFERENCE"
    else:
        diagnosis = "NUMERIC_DIFFERENCE_LOCALIZED_DESCRIPTIVELY"
    ratios: dict[str, Any] = {}
    for stage in STAGES:
        denominator = within_by_stage[stage]
        entry: dict[str, Any] = {
            "max_within_condition": denominator,
            "max_cross_condition": cross_by_stage[stage],
            "cross_to_max_within_ratio_defined": denominator > 0.0,
        }
        if denominator > 0.0:
            entry["cross_to_max_within_ratio"] = cross_by_stage[stage] / denominator
        ratios[stage] = entry
    attention = cross_by_stage["query_attention"]
    prediction = cross_prediction
    return {
        "protocol_id": PROTOCOL_ID,
        "status": "DESCRIPTIVE_DIAGNOSIS_ONLY",
        "diagnosis": diagnosis,
        "earliest_nonzero_cross_condition_stage": earliest,
        "evidence_flags": {
            "repeat_nondeterminism_present": repeat_present,
            "cross_condition_roundoff_before_softmax": centered_roundoff,
            "softmax_roundoff_first_visible": softmax_first,
            "downstream_amplification_present": downstream_amplification,
            "inconclusive": inconclusive,
        },
        "stage_error_context": ratios,
        "parent_threshold_observation": {
            "attention_max_abs": attention,
            "attention_reference": ATTENTION_REFERENCE,
            "attention_exceeds_reference": attention > ATTENTION_REFERENCE,
            "attention_to_reference_ratio": attention / ATTENTION_REFERENCE,
            "prediction_max_abs_normalized": prediction,
            "prediction_reference": PREDICTION_REFERENCE,
            "prediction_exceeds_reference": prediction > PREDICTION_REFERENCE,
            "prediction_to_reference_ratio": prediction / PREDICTION_REFERENCE,
            "reference_only_no_threshold_change": True,
        },
        "limitations": [
            "single-case numerical diagnostic only",
            "not a model-quality estimate or model ranking",
            "not generalizable to Fold A, Fold B, development84, or held-out data",
            "does not authorize a threshold change, Round A-I retry, Round B, or a later run",
        ],
        "round_a_i_retry_authorized": False,
        "threshold_change_authorized": False,
        "round_b_authorized": False,
        "automatic_next_run": False,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = load_json(args.input.expanduser().resolve())
    analysis = analyze_scalar_result(result)
    write_json_exclusive(args.output.expanduser().resolve(), analysis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
