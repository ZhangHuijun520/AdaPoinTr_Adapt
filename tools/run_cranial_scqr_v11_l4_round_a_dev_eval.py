#!/usr/bin/env python3
"""Fail-closed evaluator for Cranial-SCQR v1.1 L4 Round A development.

Merely importing this module performs no checkpoint, NPZ, CUDA, or model work.
Actual evaluation additionally requires a separately bound execution-
authorization JSON; the implementation authorization is intentionally
insufficient.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from analyze_cranial_scqr_v11_l4_round_a import (  # noqa: E402
    CANDIDATES,
    FOLDS,
    PROTOCOL_ID,
    ContractError,
    analyze_case_rows,
    sha256_file,
    validate_protocol,
    write_csv,
)


ALLOWED_NPZ_MEMBERS = ("partial", "implant", "gt")
EXPECTED_ORDER = tuple(f"{candidate}_fold{fold}_seed0" for candidate in CANDIDATES for fold in FOLDS)
EXPECTED_SOURCE_BINDINGS = {
    "tools/evaluate_skullfix_implant.py": "2bc216724a8ef550625eb0242fc9a733fff1091e67589ccbec2a7bc0b53a6059",
    "utils/skullfix_metrics.py": "0c4342cd19fb19a659302b0e350c3be34bd21447d2034bdc9d2e81a180174ee5",
    "utils/evaluation_statistics.py": "e9dd5dbf822407933e68fcba5412789e8bba8cc44cb987fd29c1230f2f50bc17",
    "datasets/SkullFixDataset.py": "cb26e98f22c9bbf08a6f58db8bcd26d1bf62f07d4334b818186570b1c797eb5a",
    "tools/runner.py": "07d6b9b05ada5549d8ed4781f57f31c1655e50eb5917583cd0f4e9b151b61804",
    "tools/builder.py": "8c6d2f436376e0075164413865a2ec68ea40f4f68e96a3011c07468280f6c3bf",
    "utils/config.py": "2058b26feff2e513f3f9d9d0d350ebce13f5035d94b4ef5e3ef27a8142578a91",
    "models/__init__.py": "72e5306c514605a1d05ae38c90b879d20103cd90f079286ec8988d9097fdd3d1",
    "models/AdaPoinTr.py": "62a743c4c2143b77b0f1656c59d0482563976440d841f04bae995017dbf7588f",
    "models/cranial_scqr/__init__.py": "d2d85b33cff9689dd06f2c2a0845a6aebccba03b6e706904afc8f4d97851cc5b",
    "models/cranial_scqr/contact_support.py": "358ea31017344fa4905aac7e495dc87ed7f74496954fd34d7390cd0ea579028f",
    "models/cranial_scqr/local_geometry.py": "b533efead76c38ff7bc83a5245a88c98e275a37e0523cbbfb793a63b4d645665",
    "models/cranial_scqr/query_conditioning.py": "e631f6649b3a218e63c39f15f6232607469106ae63b0c7cdf578636b110d9057",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return value


def resolve_under(root: Path, relative: str, *, must_exist: bool = True) -> Path:
    """Resolve a protocol path while rejecting absolute paths and traversal."""

    path = Path(relative)
    if path.is_absolute():
        raise ContractError(f"absolute protocol path rejected: {relative}")
    root = root.resolve()
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ContractError(f"path escapes root: {relative}") from exc
    if must_exist and not resolved.is_file():
        raise ContractError(f"bound file not found: {relative}")
    return resolved


def verify_file(path: Path, expected_sha: str, expected_bytes: int | None = None) -> None:
    if not path.is_file():
        raise ContractError(f"missing file: {path}")
    if expected_bytes is not None and path.stat().st_size != int(expected_bytes):
        raise ContractError(f"byte-size mismatch: {path}")
    actual = sha256_file(path)
    if actual != expected_sha:
        raise ContractError(f"SHA256 mismatch: {path}")


class AccessLedger:
    """Audits the exact frozen payload and execution event budget."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self._opened: set[tuple[str, str]] = set()

    def record_checkpoint_load(self, run_key: str) -> None:
        key = ("checkpoint", run_key)
        if key in self._opened:
            raise ContractError(f"duplicate checkpoint load: {run_key}")
        self._opened.add(key)
        self.counts["checkpoint_loads"] += 1

    def record_npz_open(self, run_key: str, case_id: str) -> None:
        key = (run_key, case_id)
        if key in self._opened:
            raise ContractError(f"duplicate NPZ open: {run_key}/{case_id}")
        self._opened.add(key)
        self.counts["npz_open_events"] += 1

    def record_member(self, member: str) -> None:
        if member not in ALLOWED_NPZ_MEMBERS:
            raise ContractError(f"forbidden NPZ member: {member}")
        self.counts[f"member_{member}"] += 1

    def record_forward(self) -> None:
        self.counts["model_case_forward_calls"] += 1

    def assert_final(self) -> None:
        expected = {
            "checkpoint_loads": 8,
            "npz_open_events": 840,
            "member_partial": 840,
            "member_implant": 840,
            "member_gt": 840,
            "model_case_forward_calls": 840,
            "optimizer_constructions": 0,
            "optimizer_steps": 0,
            "model_parameter_updates": 0,
            "model_buffer_updates": 0,
        }
        for key, value in expected.items():
            if self.counts[key] != value:
                raise ContractError(f"counter {key}={self.counts[key]}, expected {value}")

    def receipt_counts(self) -> dict[str, int]:
        names = (
            "checkpoint_loads", "npz_open_events", "member_partial",
            "member_implant", "member_gt", "model_case_forward_calls",
            "optimizer_constructions", "optimizer_steps",
            "model_parameter_updates", "model_buffer_updates",
        )
        return {name: int(self.counts[name]) for name in names}


def hash_tensor_mapping(mapping: Mapping[str, Any]) -> str:
    """Stable hash of names, dtype, shape, and bytes for CPU/GPU tensors/arrays."""

    digest = hashlib.sha256()
    for name, value in sorted(mapping.items()):
        if hasattr(value, "detach"):
            array = value.detach().cpu().contiguous().numpy()
        else:
            array = np.ascontiguousarray(np.asarray(value))
        digest.update(name.encode("utf-8"))
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(json.dumps(array.shape).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def model_state_hashes(model: Any) -> dict[str, str]:
    return {
        "parameters": hash_tensor_mapping(dict(model.named_parameters())),
        "buffers": hash_tensor_mapping(dict(model.named_buffers())),
    }


def assert_state_unchanged(before: Mapping[str, str], after: Mapping[str, str]) -> None:
    if before.get("parameters") != after.get("parameters"):
        raise ContractError("model parameter state changed during evaluation")
    if before.get("buffers") != after.get("buffers"):
        raise ContractError("model buffer state changed during evaluation")


def invoke_partial_only(model: Callable[[Any], Any], partial: Any) -> Any:
    """The sole prediction call site: the model receives exactly one argument."""

    return model(partial)


def forward_then_metrics(
    forward: Callable[[Any], Any],
    partial: Any,
    implant: Any,
    gt: Any,
    metric: Callable[[Any, Any, Any, Any], Any],
) -> Any:
    """Make ordering testable: metric-only targets are consumed after forward."""

    prediction = forward(partial)
    return metric(prediction, partial, implant, gt)


def validate_execution_authorization(
    authorization: Mapping[str, Any], protocol_sha256: str
) -> None:
    if authorization.get("authorization_effective") is not True:
        raise ContractError("formal execution authorization is not effective")
    if authorization.get("execution_authorized") is not True:
        raise ContractError("development evaluation is not explicitly authorized")
    if authorization.get("protocol_id") != PROTOCOL_ID:
        raise ContractError("execution authorization protocol identity mismatch")
    if authorization.get("protocol_sha256") != protocol_sha256:
        raise ContractError("execution authorization protocol SHA mismatch")
    if authorization.get("authorized_once") is not True:
        raise ContractError("execution authorization must be single-use")
    forbidden = authorization.get("protected_payload_access", {})
    if any(bool(forbidden.get(name)) for name in ("confirmation20", "official_test", "old_monitor", "MUG", "train")):
        raise ContractError("execution authorization permits a protected payload")


def _read_allowlist(path: Path) -> list[str]:
    values = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(values) != 105 or len(set(values)) != 105:
        raise ContractError(f"allowlist must contain 105 unique cases: {path}")
    return values


def preflight(
    protocol_path: Path,
    protocol_sha256: str,
    authorization_path: Path,
    authorization_sha256: str,
    manifest_path: Path,
    manifest_sha256: str,
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Verify every static binding before any checkpoint load or NPZ open."""

    verify_file(protocol_path, protocol_sha256)
    verify_file(authorization_path, authorization_sha256)
    verify_file(manifest_path, manifest_sha256)
    protocol = load_json(protocol_path)
    validate_protocol(protocol)
    validate_execution_authorization(load_json(authorization_path), protocol_sha256)
    bindings = protocol.get("implementation_bindings", {}).get("existing_read_only_sources", {})
    if bindings != EXPECTED_SOURCE_BINDINGS:
        raise ContractError("source-binding map differs from frozen implementation")
    for relative, expected_sha in EXPECTED_SOURCE_BINDINGS.items():
        verify_file(resolve_under(REPO_ROOT, relative), expected_sha)

    order = tuple(item.get("run_key") for item in protocol["checkpoint_matrix"])
    if order != EXPECTED_ORDER:
        raise ContractError("checkpoint execution order mismatch")
    allowlists: dict[str, list[str]] = {}
    for fold in FOLDS:
        item = protocol["development_allowlists"][fold]
        path = resolve_under(REPO_ROOT, item["path"])
        verify_file(path, item["sha256"], item["bytes"])
        allowlists[fold] = _read_allowlist(path)
    if set(allowlists["A"]) & set(allowlists["B"]):
        raise ContractError("Fold A/B development cases overlap")

    for item in protocol["checkpoint_matrix"]:
        run_key = item["run_key"]
        config_path = resolve_under(REPO_ROOT, item["runtime_config"])
        receipt_path = resolve_under(REPO_ROOT, item["completion_receipt"])
        checkpoint_path = resolve_under(REPO_ROOT, item["bncal_checkpoint"])
        verify_file(config_path, item["runtime_config_sha256"])
        verify_file(receipt_path, item["completion_receipt_sha256"], item["completion_receipt_bytes"])
        verify_file(checkpoint_path, item["bncal_checkpoint_sha256"], item["bncal_checkpoint_bytes"])
        receipt = load_json(receipt_path)
        if receipt.get("status") != "TRAINING_AND_BNCAL_PASS":
            raise ContractError(f"completion status failed: {run_key}")
        if receipt.get("run_key") != run_key:
            raise ContractError(f"completion run_key mismatch: {run_key}")
        if receipt.get("runtime_config_sha256") != item["runtime_config_sha256"]:
            raise ContractError(f"receipt config SHA mismatch: {run_key}")
        if receipt.get("bncal_checkpoint_sha256") != item["bncal_checkpoint_sha256"]:
            raise ContractError(f"receipt BNCal SHA mismatch: {run_key}")
        if item["development_allowlist"] != protocol["development_allowlists"][item["fold"]]["path"]:
            raise ContractError(f"wrong fold allowlist: {run_key}")
    return protocol, allowlists


def _load_manifest(path: Path, data_root: Path, allowlists: Mapping[str, Sequence[str]]) -> dict[str, dict[str, Any]]:
    allowed = set(allowlists["A"]) | set(allowlists["B"])
    records: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            record = json.loads(line)
            case_id = str(record.get("case_id", ""))
            if case_id not in allowed:
                continue
            if case_id in records:
                raise ContractError(f"duplicate manifest case: {case_id}")
            if record.get("dataset") != "SkullBreak":
                raise ContractError(f"non-SkullBreak manifest record: {case_id}")
            if record.get("official_split") != "train":
                raise ContractError(f"protected official split: {case_id}")
            if record.get("monitor_split") not in (None, ""):
                raise ContractError(f"old-monitor record rejected: {case_id}")
            required = ("skull_id", "source_skull_id", "defect_type", "gate_split", "normalization", "point_path")
            if any(name not in record for name in required):
                raise ContractError(f"manifest metadata missing at line {line_number}")
            point_path = Path(str(record["point_path"]))
            if point_path.is_absolute():
                raise ContractError(f"absolute payload path rejected: {case_id}")
            resolved = (data_root.resolve() / point_path).resolve()
            try:
                resolved.relative_to(data_root.resolve())
            except ValueError as exc:
                raise ContractError(f"payload path escapes data root: {case_id}") from exc
            record = dict(record)
            record["resolved_point_path"] = str(resolved)
            records[case_id] = record
    if set(records) != allowed:
        missing = sorted(allowed - set(records))
        raise ContractError(f"manifest does not resolve exact development allowlists: {missing[:3]}")
    return records


def _read_npz_member(sample: Any, member: str, ledger: AccessLedger, case_id: str) -> np.ndarray:
    if member not in ALLOWED_NPZ_MEMBERS:
        raise ContractError(f"forbidden NPZ member: {member}")
    if member not in sample.files:
        raise ContractError(f"missing NPZ member {member}: {case_id}")
    ledger.record_member(member)
    array = np.asarray(sample[member], dtype=np.float32).copy()
    if array.ndim != 2 or array.shape[1] != 3 or array.shape[0] == 0:
        raise ContractError(f"invalid {member} shape for {case_id}: {array.shape}")
    if not np.isfinite(array).all():
        raise ContractError(f"nonfinite {member} payload: {case_id}")
    return array


def _average_precision(scores: np.ndarray, labels: np.ndarray) -> float:
    scores = np.asarray(scores, dtype=np.float64).reshape(-1)
    labels = np.asarray(labels, dtype=bool).reshape(-1)
    if scores.shape != labels.shape or not np.isfinite(scores).all():
        raise ContractError("invalid contact AP inputs")
    positives = int(labels.sum())
    if positives == 0:
        raise ContractError("contact AP reference positives are empty")
    order = np.argsort(-scores, kind="stable")
    ranked = labels[order]
    precision = np.cumsum(ranked) / np.arange(1, ranked.size + 1)
    return float(precision[ranked].sum() / positives)


def _scalar_rms(tensor: Any) -> float:
    return float(tensor.detach().float().square().mean().sqrt().cpu().item())


def _attention_similarity(attention: Any) -> float:
    import torch

    matrix = attention.detach().float().squeeze(0)
    matrix = matrix / matrix.norm(dim=1, keepdim=True).clamp_min(1e-12)
    similarity = matrix @ matrix.transpose(0, 1)
    n = similarity.shape[0]
    if n < 2:
        raise ContractError("query attention requires at least two queries")
    return float(((similarity.sum() - similarity.diagonal().sum()) / (n * (n - 1))).cpu().item())


def _diagnostics(
    candidate: str,
    instrumentation: Mapping[str, Any],
    partial_tensor: Any,
    implant_tensor: Any,
    scale: float,
    query_residual: Any,
    coarse_rim_p95: float,
) -> dict[str, Any]:
    nulls = {
        "proxy_positive_prevalence": None,
        "contact_auprc": None,
        "contact_ap_minus_prevalence": None,
        "knn32_radius_mm_mean": None,
        "knn32_radius_mm_p95": None,
        "local_residual_rms": None,
        "alpha_local": None,
        "positive_attention_mass": None,
        "query_attention_entropy": None,
        "inter_query_attention_similarity": None,
        "query_residual_rms": None,
        "alpha_query": None,
        "coarse_rimcover_p95_mm": None,
    }
    if candidate == "B0":
        return nulls
    import torch
    from models.cranial_scqr.contact_support import build_contact_support_labels
    from models.cranial_scqr.local_geometry import stable_knn_indices

    backbone = instrumentation.get("backbone")
    if not isinstance(backbone, Mapping):
        raise ContractError("missing backbone instrumentation")
    proxies = backbone.get("encoder_coordinates")
    probability = backbone.get("scqr_contact_probability")
    local_residual = backbone.get("encoder_post_scqr") - backbone.get("encoder_post_adapter")
    if proxies is None or probability is None:
        raise ContractError("missing SCQR contact instrumentation")
    indices, distances = stable_knn_indices(proxies, partial_tensor, k=32)
    labels = build_contact_support_labels(
        partial_tensor, implant_tensor, torch.tensor([scale], device=partial_tensor.device), indices,
        rim_band_mm=2.0,
    ).proxy_labels.squeeze(0)
    probability_np = probability.squeeze(0).detach().float().cpu().numpy()
    labels_np = labels.detach().cpu().numpy()
    prevalence = float(labels_np.mean())
    ap = _average_precision(probability_np, labels_np)
    radii = (distances[..., -1] * float(scale)).detach().float().cpu().numpy().reshape(-1)
    result = dict(nulls)
    result.update({
        "proxy_positive_prevalence": prevalence,
        "contact_auprc": ap,
        "contact_ap_minus_prevalence": ap - prevalence,
        "knn32_radius_mm_mean": float(radii.mean()),
        "knn32_radius_mm_p95": float(np.percentile(radii, 95)),
        "local_residual_rms": _scalar_rms(local_residual),
    })
    base = getattr(instrumentation.get("model_object", None), "base_model", None)
    local_module = getattr(base, "scqr_local_geometry", None)
    result["alpha_local"] = float(local_module.alpha_l.detach().cpu().item())
    if candidate in ("Q0", "QC"):
        attention = backbone.get("scqr_query_attention")
        if attention is None or query_residual is None:
            raise ContractError("missing query-conditioning instrumentation")
        label_float = labels.to(dtype=attention.dtype)
        positive_mass = (attention.squeeze(0) * label_float.unsqueeze(0)).sum(dim=-1).mean()
        entropy = -(attention.float().clamp_min(1e-12) * attention.float().clamp_min(1e-12).log()).sum(dim=-1).mean()
        query_module = getattr(base, "scqr_query_conditioner", None)
        result.update({
            "positive_attention_mass": float(positive_mass.cpu().item()),
            "query_attention_entropy": float(entropy.cpu().item()),
            "inter_query_attention_similarity": _attention_similarity(attention),
            "query_residual_rms": _scalar_rms(query_residual),
            "alpha_query": float(query_module.alpha_q.detach().cpu().item()),
            "coarse_rimcover_p95_mm": float(coarse_rim_p95),
        })
    return result


def _metric_rows(
    pred_implant: np.ndarray,
    pred_coarse: np.ndarray,
    arrays: Mapping[str, np.ndarray],
    record: Mapping[str, Any],
) -> tuple[dict[str, Any], float]:
    from utils.skullfix_metrics import (
        directed_nearest_neighbor_distances,
        normalized_point_rim_metrics,
        normalized_point_surface_metrics,
        normalized_to_world,
    )

    norm = record["normalization"]
    centroid, scale = norm["centroid"], float(norm["scale"])
    tolerances = (0.5, 1.0, 2.0)
    implant = normalized_point_surface_metrics(pred_implant, arrays["implant"], centroid, scale, tolerances)
    final_pred = np.concatenate((arrays["partial"], pred_implant), axis=0)
    final = normalized_point_surface_metrics(final_pred, arrays["gt"], centroid, scale, tolerances)
    rim = normalized_point_rim_metrics(
        pred_implant, arrays["implant"], arrays["partial"], centroid, scale,
        rim_band_mm=2.0, tolerances_mm=tolerances,
    )
    coarse_rim = normalized_point_rim_metrics(
        pred_coarse, arrays["implant"], arrays["partial"], centroid, scale,
        rim_band_mm=2.0, tolerances_mm=tolerances,
    )
    partial_world = normalized_to_world(arrays["partial"], centroid, scale)
    implant_world = normalized_to_world(arrays["implant"], centroid, scale)
    pred_world = normalized_to_world(pred_implant, centroid, scale)
    reference_mask = directed_nearest_neighbor_distances(partial_world, implant_world) <= 2.0
    predicted_mask = directed_nearest_neighbor_distances(partial_world, pred_world) <= 2.0
    intersection = int(np.count_nonzero(reference_mask & predicted_mask))
    reference_count = int(np.count_nonzero(reference_mask))
    predicted_count = int(np.count_nonzero(predicted_mask))
    if reference_count == 0:
        raise ContractError("empty reference rim")
    precision = float(intersection / predicted_count) if predicted_count else float("nan")
    recall = float(intersection / reference_count)
    row = {
        "implant_cd_l1_mm": implant.cd_l1_mm,
        "implant_pred_to_ref_mean_mm": implant.pred_to_ref_mean_mm,
        "implant_ref_to_pred_mean_mm": implant.ref_to_pred_mean_mm,
        "implant_hd95_mm": implant.hd95_mm,
        "implant_nsd_at_1mm": implant.nsd[1.0],
        "final_cd_l1_mm": final.cd_l1_mm,
        "final_hd95_mm": final.hd95_mm,
        "final_nsd_at_1mm": final.nsd[1.0],
        "rim_reference_rim_points": rim.reference_rim_points,
        "rim_predicted_rim_points": rim.predicted_rim_points,
        "rim_gt_rim_to_pred_mean_mm": rim.gt_rim_to_pred_mean_mm,
        "rim_gt_rim_to_pred_p95_mm": rim.gt_rim_to_pred_p95_mm,
        "rim_contact_cd_l1_mm": rim.contact_cd_l1_mm,
        "rim_contact_hd95_mm": rim.contact_hd95_mm,
        "rim_contact_precision": precision,
        "rim_contact_recall": recall,
        "zero_contact_2mm": int(predicted_count == 0),
    }
    core = (row["implant_cd_l1_mm"], row["implant_hd95_mm"], row["final_cd_l1_mm"], row["final_hd95_mm"], row["rim_gt_rim_to_pred_p95_mm"])
    row["disaster"] = int(any(not math.isfinite(float(x)) for x in core) or (math.isfinite(float(rim.contact_hd95_mm)) and rim.contact_hd95_mm > 50.0))
    if not all(math.isfinite(float(x)) for x in core):
        raise ContractError("nonfinite core geometry metric")
    return row, float(coarse_rim.gt_rim_to_pred_p95_mm)


def _load_model(config_path: Path, checkpoint_path: Path, ledger: AccessLedger, run_key: str) -> Any:
    import torch
    from models import build_model_from_cfg
    from utils.config import cfg_from_yaml_file

    config = cfg_from_yaml_file(str(config_path))
    model = build_model_from_cfg(config.model)
    ledger.record_checkpoint_load(run_key)
    state = torch.load(str(checkpoint_path), map_location="cpu")
    raw = state.get("model") if state.get("model") is not None else state.get("base_model")
    if raw is None:
        raise ContractError(f"checkpoint lacks model state: {run_key}")
    model.load_state_dict({key.replace("module.", ""): value for key, value in raw.items()}, strict=True)
    return model.float()


def _evaluate_partition(
    item: Mapping[str, Any],
    case_ids: Sequence[str],
    manifest: Mapping[str, Mapping[str, Any]],
    data_root: Path,
    device: Any,
    ledger: AccessLedger,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    import torch

    run_key, candidate, fold = item["run_key"], item["candidate"], item["fold"]
    model = _load_model(
        resolve_under(REPO_ROOT, item["runtime_config"]),
        resolve_under(REPO_ROOT, item["bncal_checkpoint"]), ledger, run_key,
    ).to(device)
    model.eval()
    model.enable_full_instrumentation(True)
    before = model_state_hashes(model)
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    with torch.no_grad():
        for case_id in case_ids:
            record = manifest[case_id]
            ledger.record_npz_open(run_key, case_id)
            with np.load(Path(record["resolved_point_path"]), allow_pickle=False) as sample:
                if any(member not in sample.files for member in ALLOWED_NPZ_MEMBERS):
                    raise ContractError(f"NPZ lacks a required member: {case_id}")
                arrays = {"partial": _read_npz_member(sample, "partial", ledger, case_id)}
                partial = torch.from_numpy(arrays["partial"]).unsqueeze(0).to(device=device, dtype=torch.float32)
                captured: dict[str, Any] = {}
                hook = None
                query_module = getattr(getattr(model, "base_model", None), "scqr_query_conditioner", None)
                if query_module is not None:
                    hook = query_module.register_forward_hook(lambda _m, _i, output: captured.update(query_residual=output.residual.detach()))
                try:
                    output = invoke_partial_only(model, partial)
                    ledger.record_forward()
                finally:
                    if hook is not None:
                        hook.remove()
                # Metric targets are deliberately materialized only after the
                # sole model forward has completed.
                arrays["implant"] = _read_npz_member(sample, "implant", ledger, case_id)
                arrays["gt"] = _read_npz_member(sample, "gt", ledger, case_id)
            if not isinstance(output, (tuple, list)) or len(output) != 2:
                raise ContractError(f"unexpected eval output: {run_key}/{case_id}")
            coarse_tensor, implant_tensor = output
            if not torch.isfinite(coarse_tensor).all() or not torch.isfinite(implant_tensor).all():
                raise ContractError(f"nonfinite model output: {run_key}/{case_id}")
            pred_coarse = coarse_tensor.squeeze(0).detach().cpu().numpy()
            pred_implant = implant_tensor.squeeze(0).detach().cpu().numpy()
            instrumentation = model.pop_full_instrumentation()
            if not isinstance(instrumentation, dict):
                raise ContractError(f"missing full instrumentation: {run_key}/{case_id}")
            instrumentation["model_object"] = model
            metric_row, coarse_p95 = _metric_rows(pred_implant, pred_coarse, arrays, record)
            identity = {
                "run_key": run_key, "candidate": candidate, "fold": fold,
                "seed": 0, "case_id": case_id,
                "skull_id": record["skull_id"],
                "source_skull_id": record["source_skull_id"],
                "defect_type": record["defect_type"],
            }
            rows.append({**identity, **metric_row})
            diagnostics.append({
                **identity,
                **_diagnostics(
                    candidate, instrumentation, partial,
                    torch.from_numpy(arrays["implant"]).unsqueeze(0).to(device=device, dtype=torch.float32),
                    float(record["normalization"]["scale"]), captured.get("query_residual"), coarse_p95,
                ),
            })
            del instrumentation, output, coarse_tensor, implant_tensor, partial
    after = model_state_hashes(model)
    assert_state_unchanged(before, after)
    del model
    torch.cuda.empty_cache()
    return rows, diagnostics, before


def _write_json_exclusive(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def run_evaluation(args: argparse.Namespace) -> int:
    import torch

    if args.device != "cuda:0":
        raise ContractError("frozen device must be cuda:0")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ContractError("exactly one visible CUDA device is required")
    if torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 4090 D":
        raise ContractError("visible GPU is not NVIDIA GeForce RTX 4090 D")
    if args.output_dir.exists():
        raise ContractError("output directory already exists")
    protocol, allowlists = preflight(
        args.protocol, args.protocol_sha256, args.execution_authorization,
        args.execution_authorization_sha256, args.manifest, args.manifest_sha256,
    )
    manifest = _load_manifest(args.manifest, args.data_root, allowlists)
    args.output_dir.mkdir(parents=False, exist_ok=False)
    _write_json_exclusive(args.output_dir / "invocation.json", {
        "protocol_sha256": args.protocol_sha256,
        "execution_authorization_sha256": args.execution_authorization_sha256,
        "manifest_sha256": args.manifest_sha256,
        "started_at_utc": utc_now(),
    })
    ledger = AccessLedger()
    all_rows: list[dict[str, Any]] = []
    all_diagnostics: list[dict[str, Any]] = []
    state_hashes: dict[str, Any] = {}
    device = torch.device(args.device)
    try:
        for item in protocol["checkpoint_matrix"]:
            rows, diagnostics, state = _evaluate_partition(
                item, allowlists[item["fold"]], manifest, args.data_root,
                device, ledger,
            )
            all_rows.extend(rows)
            all_diagnostics.extend(diagnostics)
            state_hashes[item["run_key"]] = state
        ledger.assert_final()
        sources, deltas, summary, gate = analyze_case_rows(all_rows, protocol)
        write_csv(args.output_dir / "per_model_case_metrics.csv", all_rows)
        write_csv(args.output_dir / "per_model_source_metrics.csv", sources)
        write_csv(args.output_dir / "mechanism_diagnostics.csv", all_diagnostics)
        write_csv(args.output_dir / "paired_deltas.csv", deltas)
        _write_json_exclusive(args.output_dir / "fold_and_combined_summary.json", summary)
        _write_json_exclusive(args.output_dir / "round_a_gate_receipt.json", gate)
        receipt = {
            "protocol_id": PROTOCOL_ID,
            "status": "PASS",
            "started_at_utc": load_json(args.output_dir / "invocation.json")["started_at_utc"],
            "finished_at_utc": utc_now(),
            "counters": ledger.receipt_counts(),
            "model_state_hashes_unchanged": True,
            "state_hashes_before": state_hashes,
            "predictions_saved": False,
            "automatic_retry": False,
            "round_b_authorized": False,
            "automatic_next_run": False,
        }
        _write_json_exclusive(args.output_dir / "evaluation_execution_receipt.json", receipt)
        return 0
    except Exception as exc:
        failure = {
            "protocol_id": PROTOCOL_ID,
            "status": "FAILED_STOPPED_NO_RETRY",
            "finished_at_utc": utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "counters": ledger.receipt_counts(),
            "round_b_authorized": False,
            "automatic_next_run": False,
        }
        failure_path = args.output_dir / "evaluation_failure_receipt.json"
        if not failure_path.exists():
            _write_json_exclusive(failure_path, failure)
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
    for name in ("protocol", "execution_authorization", "manifest", "data_root", "output_dir"):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return run_evaluation(args)


if __name__ == "__main__":
    raise SystemExit(main())
