#!/usr/bin/env python3
"""Fail-closed one-case scalar numerical diagnostic for Round A-I.

Importing this module performs no checkpoint, NPZ, model, CUDA, or filesystem
work.  Real execution requires a separately hashed, single-use execution
authorization.  The implementation-only authorization is deliberately
insufficient.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter, OrderedDict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, MutableMapping, Sequence

import numpy as np


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import analyze_cranial_scqr_v11_l4_round_a_i_negative_control_numeric_diagnostic as analyzer  # noqa: E402
import run_cranial_scqr_v11_l4_round_a_dev_eval as parent_runner  # noqa: E402


PROTOCOL_ID = analyzer.PROTOCOL_ID
PROTOCOL_SHA256 = analyzer.PROTOCOL_SHA256
FOLD = analyzer.FOLD
CASE_ID = analyzer.CASE_ID
RUN_KEY = analyzer.RUN_KEY
SEED = analyzer.SEED
CONDITIONS = analyzer.CONDITIONS
FORWARD_ORDER = analyzer.FORWARD_ORDER
STAGES = analyzer.STAGES
PAIR_SPECS = analyzer.PAIR_SPECS
NORMALIZATION_SCALE_MM = analyzer.NORMALIZATION_SCALE_MM
ALLOWED_NPZ_MEMBERS = ("partial",)
FORBIDDEN_NPZ_MEMBERS = ("implant", "gt")
EXPECTED_SOURCE_BINDINGS = {
    "tools/run_cranial_scqr_v11_l4_round_a_intervention.py": {
        "sha256": "bff73650017164043230c810f2eca0397b54a852dd6bbd96e8ca085992f3234b",
        "bytes": 29715,
    },
    "tools/analyze_cranial_scqr_v11_l4_round_a_intervention.py": {
        "sha256": "180bc58b644d6042b50c6828cbf87df151110ae27f5fac5110a05b0fcdd0b012",
        "bytes": 33138,
    },
    "tools/test_cranial_scqr_v11_l4_round_a_intervention_contract.py": {
        "sha256": "3e52c2d679eca490ec98d8d0f35b4898ef2631dca817cc84e874fa2b9d144fea",
        "bytes": 23853,
    },
    "models/AdaPoinTr.py": {
        "sha256": "62a743c4c2143b77b0f1656c59d0482563976440d841f04bae995017dbf7588f",
        "bytes": None,
    },
    "models/cranial_scqr/query_conditioning.py": {
        "sha256": "e631f6649b3a218e63c39f15f6232607469106ae63b0c7cdf578636b110d9057",
        "bytes": None,
    },
}


ContractError = analyzer.ContractError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return analyzer.sha256_file(path)


def load_json(path: Path) -> dict[str, Any]:
    return analyzer.load_json(path)


def resolve_under(root: Path, relative: str, *, must_exist: bool = True) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ContractError(f"absolute path rejected: {relative}")
    resolved = (root.resolve() / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ContractError(f"path escapes bound root: {relative}") from exc
    if must_exist and not resolved.exists():
        raise ContractError(f"bound path does not exist: {relative}")
    return resolved


def verify_file(path: Path, expected_sha256: str, expected_bytes: int | None = None) -> None:
    if not path.is_file():
        raise ContractError(f"bound file missing: {path}")
    if expected_bytes is not None and path.stat().st_size != expected_bytes:
        raise ContractError(f"bound file size mismatch: {path}")
    if sha256_file(path) != expected_sha256:
        raise ContractError(f"bound file SHA256 mismatch: {path}")


def _write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    analyzer.write_json_exclusive(path, value)


class AccessLedger:
    """Fail closed on the exact one-load, one-open, partial-only, four-forward budget."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self._checkpoint_loaded = False
        self._npz_opened = False
        self._forward_index = 0

    def record_checkpoint_load(self, run_key: str) -> None:
        if run_key != RUN_KEY or self._checkpoint_loaded:
            raise ContractError(f"unexpected or duplicate checkpoint load: {run_key}")
        self._checkpoint_loaded = True
        self.counts["checkpoint_loads"] += 1

    def record_npz_open(self, fold: str, case_id: str) -> None:
        if fold != FOLD or case_id != CASE_ID or self._npz_opened:
            raise ContractError(f"unexpected or duplicate NPZ open: {fold}/{case_id}")
        self._npz_opened = True
        self.counts["npz_open_events"] += 1

    def record_member(self, member: str) -> None:
        if member not in ALLOWED_NPZ_MEMBERS:
            raise ContractError(f"forbidden NPZ member: {member}")
        if self.counts[f"member_{member}"]:
            raise ContractError(f"duplicate NPZ member read: {member}")
        self.counts[f"member_{member}"] += 1

    def record_forward(self, label: str) -> None:
        if self._forward_index >= len(FORWARD_ORDER):
            raise ContractError(f"extra model forward: {label}")
        expected = FORWARD_ORDER[self._forward_index]
        if label != expected:
            raise ContractError(f"forward order mismatch: {label}, expected {expected}")
        self._forward_index += 1
        self.counts["model_case_forward_calls"] += 1

    def record_probability_hook_registered(self) -> None:
        self.counts["probability_hooks_registered"] += 1

    def record_probability_hook_removed(self) -> None:
        self.counts["probability_hooks_removed"] += 1

    def receipt_counts(self) -> dict[str, int]:
        names = (
            "checkpoint_loads",
            "npz_open_events",
            "member_partial",
            "member_implant",
            "member_gt",
            "model_case_forward_calls",
            "probability_hooks_registered",
            "probability_hooks_removed",
            "optimizer_constructions",
            "optimizer_steps",
            "model_parameter_updates",
            "model_buffer_updates",
        )
        return {name: int(self.counts[name]) for name in names}

    def assert_final(self) -> None:
        expected = {
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
        if self.receipt_counts() != expected:
            raise ContractError(
                f"execution ledger mismatch: {self.receipt_counts()} != {expected}"
            )


def _condition_from_label(label: str) -> tuple[str, int]:
    if label not in FORWARD_ORDER:
        raise ContractError(f"unfrozen forward label: {label}")
    condition = "bias_zero" if label.startswith("bias_zero_") else "case_mean_probability"
    replicate = int(label.rsplit("rep", 1)[1])
    return condition, replicate


def intervene_probability(probability: Any, condition: str, *, fold: str, case_id: str) -> Any:
    """Return a transient two-condition probability without mutating the input."""

    import torch

    if fold != FOLD or case_id != CASE_ID:
        raise ContractError(f"unauthorized case: {fold}/{case_id}")
    if condition not in CONDITIONS:
        raise ContractError(f"unauthorized diagnostic condition: {condition}")
    if (
        not torch.is_tensor(probability)
        or probability.ndim != 2
        or probability.shape[0] != 1
        or probability.shape[1] < 2
        or not torch.isfinite(probability).all()
    ):
        raise ContractError("contact probability must be finite with shape (1, N_PROXY)")
    if condition == "bias_zero":
        return torch.ones_like(probability)
    return probability.mean(dim=-1, keepdim=True).expand_as(probability)


@contextmanager
def temporary_probability_intervention(
    module: Any,
    condition: str,
    *,
    fold: str,
    case_id: str,
    ledger: AccessLedger | None = None,
) -> Iterator[MutableMapping[str, Any]]:
    """Temporarily replace only the conditioner contact-probability argument."""

    captured: MutableMapping[str, Any] = {}

    def hook(_module: Any, args: tuple[Any, ...]) -> tuple[Any, ...]:
        if len(args) < 4:
            raise ContractError("conditioner call lacks contact_probability argument")
        original = args[3]
        replaced = intervene_probability(original, condition, fold=fold, case_id=case_id)
        captured["original_contact_probability"] = original.detach()
        captured["intervened_contact_probability"] = replaced.detach()
        return (*args[:3], replaced, *args[4:])

    handle = module.register_forward_pre_hook(hook)
    if ledger is not None:
        ledger.record_probability_hook_registered()
    try:
        yield captured
    finally:
        handle.remove()
        if ledger is not None:
            ledger.record_probability_hook_removed()


def tensor_sha256(tensor: Any) -> str:
    """Hash dtype, shape, and contiguous tensor bytes without retaining values."""

    import torch

    if not torch.is_tensor(tensor):
        raise ContractError("tensor SHA256 requires a torch tensor")
    value = tensor.detach().cpu().contiguous()
    array = value.numpy()
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode("ascii"))
    digest.update(json.dumps(list(value.shape), separators=(",", ":")).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def scalar_summary(tensor: Any) -> dict[str, Any]:
    """Reduce a finite nonempty tensor to metadata and scalar statistics only."""

    import torch

    if not torch.is_tensor(tensor) or tensor.numel() == 0:
        raise ContractError("scalar summary requires a nonempty torch tensor")
    if not torch.isfinite(tensor).all():
        raise ContractError("scalar summary received a nonfinite tensor")
    value = tensor.detach().double()
    return {
        "finite": True,
        "element_count": int(value.numel()),
        "dtype": str(tensor.dtype).replace("torch.", "", 1),
        "shape": [int(dimension) for dimension in tensor.shape],
        "min": float(value.min().cpu().item()),
        "max": float(value.max().cpu().item()),
        "mean": float(value.mean().cpu().item()),
        "std_population": float(value.std(unbiased=False).cpu().item()),
        "rms": float(value.square().mean().sqrt().cpu().item()),
        "tensor_sha256": tensor_sha256(tensor),
    }


def row_center_logits(logits: Any) -> Any:
    import torch

    if not torch.is_tensor(logits) or logits.ndim < 2 or logits.shape[-1] < 2:
        raise ContractError("query logits must have a proxy dimension")
    if not torch.isfinite(logits).all():
        raise ContractError("query logits are nonfinite")
    return logits - logits.mean(dim=-1, keepdim=True)


def pairwise_error(left: Any, right: Any) -> dict[str, Any]:
    import torch

    if (
        not torch.is_tensor(left)
        or not torch.is_tensor(right)
        or left.shape != right.shape
        or left.dtype != right.dtype
        or left.numel() == 0
    ):
        raise ContractError("pairwise comparison requires same-shape, same-dtype tensors")
    if not torch.isfinite(left).all() or not torch.isfinite(right).all():
        raise ContractError("pairwise comparison received nonfinite tensors")
    left_digest = tensor_sha256(left)
    right_digest = tensor_sha256(right)
    difference = (left.detach().double() - right.detach().double()).abs().reshape(-1)
    return {
        "bitwise_equal": left_digest == right_digest,
        "max_abs": float(difference.max().cpu().item()),
        "mean_abs": float(difference.mean().cpu().item()),
        "rms": float(difference.square().mean().sqrt().cpu().item()),
        "p95_abs": float(torch.quantile(difference, 0.95).cpu().item()),
        "left_tensor_sha256": left_digest,
        "right_tensor_sha256": right_digest,
    }


def prediction_error(left: Any, right: Any, scale_mm: float) -> dict[str, float]:
    import torch

    base = pairwise_error(left, right)
    if left.ndim < 2 or left.shape[-1] != 3:
        raise ContractError("predicted implant must end in XYZ coordinates")
    if not math.isfinite(scale_mm) or scale_mm <= 0:
        raise ContractError("normalization scale must be finite and positive")
    coordinate = (left.detach().double() - right.detach().double()).abs().reshape(-1)
    point_delta = left.detach().double() - right.detach().double()
    point_l2 = torch.sqrt(point_delta.square().sum(dim=-1)).reshape(-1)
    coordinate_max = float(coordinate.max().cpu().item())
    coordinate_mean = float(coordinate.mean().cpu().item())
    coordinate_rms = float(coordinate.square().mean().sqrt().cpu().item())
    coordinate_p95 = float(torch.quantile(coordinate, 0.95).cpu().item())
    point_max = float(point_l2.max().cpu().item())
    point_mean = float(point_l2.mean().cpu().item())
    point_p95 = float(torch.quantile(point_l2, 0.95).cpu().item())
    if coordinate_max != base["max_abs"] or coordinate_mean != base["mean_abs"]:
        raise ContractError("prediction scalar calculation mismatch")
    return {
        "coordinate_max_abs_normalized": coordinate_max,
        "coordinate_mean_abs_normalized": coordinate_mean,
        "coordinate_rms_normalized": coordinate_rms,
        "coordinate_p95_abs_normalized": coordinate_p95,
        "point_l2_max_normalized": point_max,
        "point_l2_mean_normalized": point_mean,
        "point_l2_p95_normalized": point_p95,
        "coordinate_max_abs_mm": coordinate_max * scale_mm,
        "coordinate_rms_mm": coordinate_rms * scale_mm,
        "point_l2_max_mm": point_max * scale_mm,
        "point_l2_mean_mm": point_mean * scale_mm,
        "point_l2_p95_mm": point_p95 * scale_mm,
    }


def logit_shift_scalars(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, float]:
    import torch

    raw_left = left["query_logits_raw"]
    raw_right = right["query_logits_raw"]
    if raw_left.shape != raw_right.shape:
        raise ContractError("logit shapes differ")
    delta = (raw_right.detach().double() - raw_left.detach().double()).reshape(-1)
    delta_mean = delta.mean()
    left_condition = str(left["condition"])
    right_condition = str(right["condition"])
    if left_condition == right_condition:
        expected = 0.0
    elif (left_condition, right_condition) == CONDITIONS:
        probability_mean = float(
            right["original_contact_probability"].detach().double().mean().cpu().item()
        )
        if probability_mean <= 0.0 or not math.isfinite(probability_mean):
            raise ContractError("case mean probability must be finite and positive")
        expected = math.log(probability_mean)
    else:
        raise ContractError("unfrozen logit comparison direction")
    centered = pairwise_error(
        left["query_logits_row_centered"], right["query_logits_row_centered"]
    )
    return {
        "raw_logit_delta_mean": float(delta_mean.cpu().item()),
        "raw_logit_delta_std_population": float(delta.std(unbiased=False).cpu().item()),
        "raw_logit_delta_max_deviation_from_its_mean": float(
            (delta - delta_mean).abs().max().cpu().item()
        ),
        "expected_log_case_mean_probability": expected,
        "raw_delta_mean_minus_expected_shift": float(delta_mean.cpu().item()) - expected,
        "row_centered_logit_max_abs": centered["max_abs"],
    }


def _state_mapping_digest(mapping: Mapping[str, str]) -> str:
    required = {"parameters", "buffers"}
    if set(mapping) != required:
        raise ContractError("model state hash mapping fields mismatch")
    for name, value in mapping.items():
        if not isinstance(value, str) or len(value) != 64:
            raise ContractError(f"invalid model-state digest: {name}")
    payload = json.dumps(dict(sorted(mapping.items())), separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def compile_scalar_result(
    records: Mapping[str, Mapping[str, Any]],
    ledger: AccessLedger,
    state_before: Mapping[str, str],
    state_after: Mapping[str, str],
) -> dict[str, Any]:
    """Reduce four in-memory forward records to the frozen scalar-only schema."""

    if tuple(records) != FORWARD_ORDER:
        raise ContractError("forward record order mismatch")
    ledger.assert_final()
    before_digest = _state_mapping_digest(state_before)
    after_digest = _state_mapping_digest(state_after)
    if state_before != state_after or before_digest != after_digest:
        raise ContractError("model parameter or buffer state changed")
    per_forward: OrderedDict[str, Any] = OrderedDict()
    for label in FORWARD_ORDER:
        condition, replicate = _condition_from_label(label)
        record = records[label]
        if record.get("condition") != condition:
            raise ContractError(f"record condition mismatch: {label}")
        tensors = record.get("stage_tensors")
        if not isinstance(tensors, Mapping) or tuple(tensors) != STAGES:
            raise ContractError(f"record stages mismatch: {label}")
        per_forward[label] = {
            "condition": condition,
            "replicate": replicate,
            "stages": OrderedDict(
                (stage, scalar_summary(tensors[stage])) for stage in STAGES
            ),
        }
    pairwise: OrderedDict[str, Any] = OrderedDict()
    for name, (left_label, right_label, role) in PAIR_SPECS.items():
        left_record = records[left_label]
        right_record = records[right_label]
        left = left_record["stage_tensors"]
        right = right_record["stage_tensors"]
        pairwise[name] = {
            "left": left_label,
            "right": right_label,
            "role": role,
            "stage_errors": OrderedDict(
                (stage, pairwise_error(left[stage], right[stage])) for stage in STAGES
            ),
            "prediction_errors": prediction_error(
                left["predicted_implant"],
                right["predicted_implant"],
                NORMALIZATION_SCALE_MM,
            ),
            "logit_shift_scalars": logit_shift_scalars(
                {"condition": left_record["condition"], **left},
                {"condition": right_record["condition"], **right},
            ),
        }
    result = {
        "protocol_id": PROTOCOL_ID,
        "status": "PASS_DIAGNOSTIC_ONLY",
        "identity": {
            "run_key": RUN_KEY,
            "candidate": "QC",
            "fold": FOLD,
            "seed": SEED,
            "case_id": CASE_ID,
            "source_skull_id": "000",
            "defect_type": "frontoorbital",
        },
        "counters": ledger.receipt_counts(),
        "forward_order": list(FORWARD_ORDER),
        "per_forward": per_forward,
        "pairwise": pairwise,
        "model_state": {
            "before_sha256": before_digest,
            "after_sha256": after_digest,
            "unchanged": True,
        },
        "parent_threshold_reference": {
            "attention_max_abs": analyzer.ATTENTION_REFERENCE,
            "predicted_points_normalized_max_abs": analyzer.PREDICTION_REFERENCE,
            "reference_only": True,
        },
        "safeguards": {
            "raw_tensors_saved": False,
            "point_coordinates_saved": False,
            "implant_member_read": False,
            "gt_member_read": False,
            "threshold_changed": False,
            "automatic_retry": False,
            "round_a_i_retry_authorized": False,
            "round_b_authorized": False,
            "automatic_next_run": False,
        },
    }
    analyzer.validate_scalar_result(result)
    return result


def build_failure_receipt(
    error: BaseException,
    ledger: AccessLedger,
    completed_scalar_summaries: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a scalar-only fail-closed receipt without tensor or coordinate data."""

    summaries = dict(completed_scalar_summaries or {})
    for label, value in summaries.items():
        if label not in FORWARD_ORDER or not isinstance(value, Mapping):
            raise ContractError("failure receipt contains an invalid scalar summary")
        for stage, summary in value.items():
            if stage not in STAGES:
                raise ContractError("failure receipt contains an invalid stage")
            analyzer._validate_summary(summary, f"failure.{label}.{stage}")
    return {
        "protocol_id": PROTOCOL_ID,
        "status": "FAILED_STOPPED_NO_RETRY",
        "finished_at_utc": utc_now(),
        "error_type": type(error).__name__,
        "error": str(error),
        "counters": ledger.receipt_counts(),
        "completed_forward_scalar_summaries": summaries,
        "raw_tensors_saved": False,
        "point_coordinates_saved": False,
        "automatic_retry": False,
        "round_a_i_retry_authorized": False,
        "threshold_change_authorized": False,
        "round_b_authorized": False,
        "automatic_next_run": False,
    }


def validate_execution_authorization(
    authorization: Mapping[str, Any], protocol_sha256: str, output_dir: Path
) -> None:
    required_true = ("authorization_effective", "execution_authorized", "authorized_once")
    if any(authorization.get(name) is not True for name in required_true):
        raise ContractError("formal numeric-diagnostic authorization is not effective and single-use")
    if authorization.get("protocol_id") != PROTOCOL_ID:
        raise ContractError("execution authorization protocol identity mismatch")
    if authorization.get("protocol_sha256") != protocol_sha256:
        raise ContractError("execution authorization protocol SHA mismatch")
    expected_output = authorization.get("output_directory")
    if not isinstance(expected_output, str) or Path(expected_output).resolve() != output_dir.resolve():
        raise ContractError("execution authorization output directory mismatch")
    if authorization.get("fold") != FOLD or authorization.get("case_id") != CASE_ID:
        raise ContractError("execution authorization case mismatch")
    if authorization.get("forward_order") != list(FORWARD_ORDER):
        raise ContractError("execution authorization forward order mismatch")
    if authorization.get("conditions") != list(CONDITIONS):
        raise ContractError("execution authorization condition mismatch")
    if authorization.get("allowed_npz_members") != ["partial"]:
        raise ContractError("execution authorization member mismatch")
    counts = authorization.get("authorized_counts", {})
    expected_counts = {
        "checkpoint_loads": 1,
        "npz_opens": 1,
        "partial_reads": 1,
        "model_case_forward_calls": 4,
        "conditions": 2,
        "replicates_per_condition": 2,
    }
    if counts != expected_counts:
        raise ContractError("execution authorization count mismatch")
    forbidden = authorization.get("protected_payload_access", {})
    required_false = (
        "implant",
        "gt",
        "Fold_B",
        "Q0",
        "native_qc",
        "fixed_permutation",
        "confirmation20",
        "official_test",
        "old_monitor",
        "MUG",
    )
    if any(forbidden.get(name) is not False for name in required_false):
        raise ContractError("execution authorization permits a forbidden resource")
    boundary = (
        "automatic_retry",
        "formal_round_a_i_retry",
        "threshold_change_authorized",
        "training_authorized",
        "bncal_authorized",
        "round_b_authorized",
        "automatic_next_run",
    )
    if any(authorization.get(name) is not False for name in boundary):
        raise ContractError("execution authorization crosses a frozen boundary")


def _read_exact_allowlist_case(path: Path, expected_line: int) -> None:
    cases = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(cases) != 105 or len(set(cases)) != 105:
        raise ContractError("Fold A development allowlist cardinality mismatch")
    if expected_line < 1 or cases[expected_line - 1] != CASE_ID or cases.count(CASE_ID) != 1:
        raise ContractError("exact diagnostic case is not at its frozen allowlist line")


def _read_exact_manifest_record(path: Path, data_root: Path, expected_line: int) -> dict[str, Any]:
    selected: dict[str, Any] | None = None
    selected_line = 0
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("case_id") == CASE_ID:
                if selected is not None:
                    raise ContractError("duplicate diagnostic case in manifest")
                selected = record
                selected_line = line_number
    if selected is None or selected_line != expected_line:
        raise ContractError("diagnostic case manifest line mismatch")
    expected_fields = {
        "dataset": "SkullBreak",
        "official_split": "train",
        "gate_split": "train",
        "monitor_split": None,
        "source_skull_id": "000",
        "defect_type": "frontoorbital",
    }
    if any(selected.get(key) != value for key, value in expected_fields.items()):
        raise ContractError("diagnostic manifest metadata mismatch")
    normalization = selected.get("normalization", {})
    if float(normalization.get("scale")) != NORMALIZATION_SCALE_MM:
        raise ContractError("diagnostic normalization scale mismatch")
    relative = selected.get("point_path")
    if relative != "points/train__000__frontoorbital.npz":
        raise ContractError("diagnostic payload path mismatch")
    payload = resolve_under(data_root, relative)
    selected = dict(selected)
    selected["resolved_point_path"] = str(payload)
    return selected


def preflight(
    protocol_path: Path,
    protocol_sha256: str,
    authorization_path: Path,
    authorization_sha256: str,
    manifest_path: Path,
    manifest_sha256: str,
    data_root: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate every binding before GPU query, model construction, or NPZ open."""

    if protocol_sha256 != PROTOCOL_SHA256:
        raise ContractError("command-line protocol SHA is not frozen")
    verify_file(protocol_path, protocol_sha256, 15114)
    verify_file(authorization_path, authorization_sha256)
    verify_file(manifest_path, manifest_sha256, 734982)
    protocol = load_json(protocol_path)
    analyzer.validate_protocol(protocol)
    validate_execution_authorization(load_json(authorization_path), protocol_sha256, output_dir)
    if protocol["exact_case"]["manifest_sha256"] != manifest_sha256:
        raise ContractError("manifest SHA differs from frozen protocol")
    for relative, binding in EXPECTED_SOURCE_BINDINGS.items():
        verify_file(
            resolve_under(REPO_ROOT, relative),
            str(binding["sha256"]),
            binding["bytes"],
        )
    allowlist = protocol["exact_case"]
    allowlist_path = resolve_under(REPO_ROOT, str(allowlist["allowlist_path"]))
    verify_file(
        allowlist_path,
        str(allowlist["allowlist_sha256"]),
        int(allowlist["allowlist_bytes"]),
    )
    _read_exact_allowlist_case(
        allowlist_path, int(allowlist["allowlist_line_number_one_based"])
    )
    checkpoint = protocol["exact_checkpoint"]
    for item_name in ("runtime_config", "completion_receipt", "bncal_checkpoint"):
        item = checkpoint[item_name]
        verify_file(
            resolve_under(REPO_ROOT, str(item["path"])),
            str(item["sha256"]),
            int(item["bytes"]),
        )
    receipt = load_json(resolve_under(REPO_ROOT, checkpoint["completion_receipt"]["path"]))
    if receipt.get("status") != "TRAINING_AND_BNCAL_PASS" or receipt.get("run_key") != RUN_KEY:
        raise ContractError("QC Fold A completion receipt mismatch")
    if output_dir.exists():
        raise ContractError("formal diagnostic output directory already exists")
    record = _read_exact_manifest_record(
        manifest_path,
        data_root,
        int(protocol["exact_case"]["manifest_line_number_one_based"]),
    )
    return protocol, record


def _gpu_uuid() -> str:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=uuid", "--format=csv,noheader"],
        check=True,
        capture_output=True,
        text=True,
    )
    values = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(values) != 1:
        raise ContractError("exactly one visible GPU UUID is required")
    return values[0]


def _verify_gpu(authorization: Mapping[str, Any], device_name: str) -> Any:
    import torch

    if device_name != "cuda:0":
        raise ContractError("formal diagnostic device must be cuda:0")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ContractError("exactly one visible CUDA device is required")
    if torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 4090 D":
        raise ContractError("visible GPU is not NVIDIA GeForce RTX 4090 D")
    expected_uuid = authorization.get("resource_scope", {}).get("gpu_uuid")
    if not isinstance(expected_uuid, str) or _gpu_uuid() != expected_uuid:
        raise ContractError("visible GPU UUID differs from formal authorization")
    return torch.device(device_name)


def _load_model(protocol: Mapping[str, Any], ledger: AccessLedger) -> Any:
    import torch
    from models import build_model_from_cfg
    from utils.config import cfg_from_yaml_file

    checkpoint = protocol["exact_checkpoint"]
    config_path = resolve_under(REPO_ROOT, checkpoint["runtime_config"]["path"])
    checkpoint_path = resolve_under(REPO_ROOT, checkpoint["bncal_checkpoint"]["path"])
    config = cfg_from_yaml_file(str(config_path))
    model = build_model_from_cfg(config.model)
    ledger.record_checkpoint_load(RUN_KEY)
    state = torch.load(str(checkpoint_path), map_location="cpu")
    raw = state.get("model") if state.get("model") is not None else state.get("base_model")
    if raw is None:
        raise ContractError("QC Fold A checkpoint lacks model state")
    model.load_state_dict(
        {key.replace("module.", ""): value for key, value in raw.items()}, strict=True
    )
    return model.float()


def _capture_forward(
    model: Any,
    partial: Any,
    label: str,
    ledger: AccessLedger,
) -> dict[str, Any]:
    import torch

    condition, _ = _condition_from_label(label)
    query_module = getattr(getattr(model, "base_model", None), "scqr_query_conditioner", None)
    if query_module is None:
        raise ContractError("QC model lacks query conditioner")
    query_capture: dict[str, Any] = {}

    def output_hook(_module: Any, _args: tuple[Any, ...], output: Any) -> None:
        for name in ("logits", "attention", "residual"):
            value = getattr(output, name, None)
            if value is None:
                raise ContractError(f"query conditioner output lacks {name}")
            query_capture[name] = value.detach()

    output_handle = query_module.register_forward_hook(output_hook)
    try:
        with temporary_probability_intervention(
            query_module,
            condition,
            fold=FOLD,
            case_id=CASE_ID,
            ledger=ledger,
        ) as probability_capture:
            output = parent_runner.invoke_partial_only(model, partial)
            ledger.record_forward(label)
    finally:
        output_handle.remove()
    if not isinstance(output, (tuple, list)) or len(output) != 2:
        raise ContractError("unexpected model output")
    coarse, predicted_implant = output
    instrumentation = model.pop_full_instrumentation()
    if not isinstance(instrumentation, Mapping):
        raise ContractError("full-model instrumentation is missing")
    backbone = instrumentation.get("backbone")
    if not isinstance(backbone, Mapping):
        raise ContractError("wrapped backbone instrumentation is missing")
    required = (
        "original_contact_probability",
        "intervened_contact_probability",
    )
    if any(name not in probability_capture for name in required):
        raise ContractError("probability intervention capture is incomplete")
    if any(name not in query_capture for name in ("logits", "attention", "residual")):
        raise ContractError("query conditioner capture is incomplete")
    tensors: OrderedDict[str, Any] = OrderedDict(
        (
            ("original_contact_probability", probability_capture["original_contact_probability"]),
            ("intervened_contact_probability", probability_capture["intervened_contact_probability"]),
            ("coarse", coarse.detach()),
            ("query_logits_raw", query_capture["logits"]),
            ("query_logits_row_centered", row_center_logits(query_capture["logits"])),
            ("query_attention", query_capture["attention"]),
            ("query_residual", query_capture["residual"]),
            ("query_pre_decoder", backbone.get("query_pre_decoder")),
            ("query_post_decoder", backbone.get("query_post_decoder")),
            ("predicted_implant", predicted_implant.detach()),
        )
    )
    if tuple(tensors) != STAGES or any(value is None for value in tensors.values()):
        raise ContractError("frozen instrumentation stage is unavailable")
    for stage, tensor in tensors.items():
        if not torch.is_tensor(tensor) or tensor.numel() == 0 or not torch.isfinite(tensor).all():
            raise ContractError(f"invalid stage tensor: {stage}")
    return {"condition": condition, "stage_tensors": tensors}


def _read_partial(record: Mapping[str, Any], ledger: AccessLedger, device: Any) -> Any:
    import torch

    path = Path(str(record["resolved_point_path"]))
    ledger.record_npz_open(FOLD, CASE_ID)
    with np.load(path, allow_pickle=False) as sample:
        if "partial" not in sample.files:
            raise ContractError("diagnostic NPZ lacks partial")
        ledger.record_member("partial")
        partial_np = np.asarray(sample["partial"], dtype=np.float32).copy()
    if partial_np.ndim != 2 or partial_np.shape[1] != 3 or partial_np.shape[0] == 0:
        raise ContractError("partial must be a nonempty Nx3 array")
    if not np.isfinite(partial_np).all():
        raise ContractError("partial contains nonfinite values")
    return torch.from_numpy(partial_np).unsqueeze(0).to(device=device, dtype=torch.float32)


def _completed_summaries(records: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        label: {
            stage: scalar_summary(tensor)
            for stage, tensor in record.get("stage_tensors", {}).items()
            if stage in STAGES
        }
        for label, record in records.items()
        if label in FORWARD_ORDER
    }


def _write_files_manifest(output_dir: Path, names: Sequence[str]) -> None:
    lines = []
    for name in names:
        path = output_dir / name
        lines.append(f"{sha256_file(path)}  {name}\n")
    manifest = output_dir / "files.sha256"
    with manifest.open("x", encoding="utf-8") as stream:
        stream.writelines(lines)


def run_diagnostic(args: argparse.Namespace) -> int:
    protocol, record = preflight(
        args.protocol,
        args.protocol_sha256,
        args.execution_authorization,
        args.execution_authorization_sha256,
        args.manifest,
        args.manifest_sha256,
        args.data_root,
        args.output_dir,
    )
    authorization = load_json(args.execution_authorization)
    device = _verify_gpu(authorization, args.device)
    args.output_dir.mkdir(parents=False, exist_ok=False)
    ledger = AccessLedger()
    records: OrderedDict[str, Any] = OrderedDict()
    started_at = utc_now()
    try:
        import torch

        model = _load_model(protocol, ledger).to(device)
        model.eval()
        model.enable_full_instrumentation(True)
        query_module = getattr(getattr(model, "base_model", None), "scqr_query_conditioner", None)
        if query_module is None or float(query_module.beta.detach().cpu().item()) != 1.0:
            raise ContractError("bound checkpoint is not a native beta=1 QC model")
        state_before = parent_runner.model_state_hashes(model)
        partial = _read_partial(record, ledger, device)
        partial_digest = tensor_sha256(partial)
        with torch.no_grad():
            for label in FORWARD_ORDER:
                if tensor_sha256(partial) != partial_digest:
                    raise ContractError("in-memory partial tensor changed between forwards")
                records[label] = _capture_forward(model, partial, label, ledger)
        if tensor_sha256(partial) != partial_digest:
            raise ContractError("in-memory partial tensor changed after forwards")
        state_after = parent_runner.model_state_hashes(model)
        parent_runner.assert_state_unchanged(state_before, state_after)
        result = compile_scalar_result(records, ledger, state_before, state_after)
        analysis = analyzer.analyze_scalar_result(result)
        _write_json_exclusive(args.output_dir / "numeric_diagnostic_scalars.json", result)
        _write_json_exclusive(
            args.output_dir / "diagnostic_completion_receipt.json",
            {
                "protocol_id": PROTOCOL_ID,
                "status": "PASS_DIAGNOSTIC_ONLY",
                "started_at_utc": started_at,
                "finished_at_utc": utc_now(),
                "counters": ledger.receipt_counts(),
                "analysis": analysis,
                "model_state_unchanged": True,
                "raw_tensors_saved": False,
                "point_coordinates_saved": False,
                "threshold_change_authorized": False,
                "formal_round_a_i_retry_authorized": False,
                "round_b_authorized": False,
                "automatic_retry": False,
                "automatic_next_run": False,
            },
        )
        _write_files_manifest(
            args.output_dir,
            ("numeric_diagnostic_scalars.json", "diagnostic_completion_receipt.json"),
        )
        del records, partial, model
        torch.cuda.empty_cache()
        return 0
    except Exception as exc:
        failure = build_failure_receipt(exc, ledger, _completed_summaries(records))
        failure_path = args.output_dir / "numeric_diagnostic_failure_receipt.json"
        if not failure_path.exists():
            _write_json_exclusive(failure_path, failure)
        if not (args.output_dir / "files.sha256").exists():
            _write_files_manifest(args.output_dir, (failure_path.name,))
        raise


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--execution-authorization", required=True, type=Path)
    parser.add_argument("--execution-authorization-sha256", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--device", default="cuda:0")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    for name in (
        "protocol",
        "execution_authorization",
        "manifest",
        "data_root",
        "output_dir",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return run_diagnostic(args)


if __name__ == "__main__":
    raise SystemExit(main())
