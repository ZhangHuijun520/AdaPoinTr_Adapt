#!/usr/bin/env python3
"""Fail-closed runner for the frozen Q0 beta=1 reverse intervention.

Importing this module performs no checkpoint, NPZ, CUDA, model, or filesystem
work.  Real execution additionally requires a separate hashed, single-use
authorization that is deliberately not supplied by the implementation stage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import analyze_cranial_scqr_v11_l4_round_a_q0_reverse_intervention as analyzer  # noqa: E402
import run_cranial_scqr_v11_l4_round_a_dev_eval as parent_runner  # noqa: E402


PROTOCOL_ID = analyzer.PROTOCOL_ID
PROTOCOL_SHA256 = analyzer.PROTOCOL_SHA256
CONDITIONS = analyzer.CONDITIONS
FOLDS = analyzer.FOLDS
SEED = analyzer.SEED
ALLOWED_NPZ_MEMBERS = ("partial", "implant", "gt")
EXPECTED_PARENT_BINDINGS = {
    "tools/run_cranial_scqr_v11_l4_round_a_dev_eval.py": "6be1c38b46270eff278ea7a54805ba0d572e8aef81a103350308072380c38798",
    "tools/analyze_cranial_scqr_v11_l4_round_a.py": "3a54206a950c5d6825373ca6364d41feacca44bac28e62b505a7d3d35d47985d",
    "tools/test_cranial_scqr_v11_l4_round_a_dev_eval_contract.py": "d20c0f81f8b0bc49f72a90040ccdb52cb65ce475d30da9e7df989c4dc4e3b34b",
    "tools/run_cranial_scqr_v11_l4_round_a_intervention.py": "d094ade877a64d0dd27646633095ef7963475f1b8a75c266c5c9825b71bd0ff8",
    "tools/analyze_cranial_scqr_v11_l4_round_a_intervention.py": "3cd1c618cde88fbd2bfce5dd96f3f666ab22b3b2c5b78ebe1887b3efa2872a28",
    "tools/test_cranial_scqr_v11_l4_round_a_intervention_contract.py": "bf69116f38da7c231b5a409dc2a24bdc15d2772439b32e6b05e063c5688dc9b6",
    "models/cranial_scqr/query_conditioning.py": "e631f6649b3a218e63c39f15f6232607469106ae63b0c7cdf578636b110d9057",
    "models/cranial_scqr/contact_support.py": "358ea31017344fa4905aac7e495dc87ed7f74496954fd34d7390cd0ea579028f",
    "models/cranial_scqr/local_geometry.py": "b533efead76c38ff7bc83a5245a88c98e275a37e0523cbbfb793a63b4d645665",
    "models/AdaPoinTr.py": "62a743c4c2143b77b0f1656c59d0482563976440d841f04bae995017dbf7588f",
    "utils/skullfix_metrics.py": "0c4342cd19fb19a659302b0e350c3be34bd21447d2034bdc9d2e81a180174ee5",
    "utils/evaluation_statistics.py": "e9dd5dbf822407933e68fcba5412789e8bba8cc44cb987fd29c1230f2f50bc17",
    "datasets/SkullFixDataset.py": "cb26e98f22c9bbf08a6f58db8bcd26d1bf62f07d4334b818186570b1c797eb5a",
}


ContractError = analyzer.ContractError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return analyzer.load_json(path)


def resolve_under(root: Path, relative: str, *, must_exist: bool = True) -> Path:
    try:
        return parent_runner.resolve_under(root, relative, must_exist=must_exist)
    except parent_runner.ContractError as exc:
        raise ContractError(str(exc)) from exc


def verify_file(path: Path, expected_sha: str, expected_bytes: int | None = None) -> None:
    try:
        parent_runner.verify_file(path, expected_sha, expected_bytes)
    except parent_runner.ContractError as exc:
        raise ContractError(str(exc)) from exc


class AccessLedger:
    """Audit the exact future payload, forward, and beta-override budget."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self._checkpoints: set[str] = set()
        self._npz: set[tuple[str, str]] = set()

    def record_checkpoint_load(self, run_key: str) -> None:
        if run_key in self._checkpoints:
            raise ContractError(f"duplicate checkpoint load: {run_key}")
        if not run_key.startswith("Q0_fold"):
            raise ContractError(f"non-Q0 checkpoint load rejected: {run_key}")
        self._checkpoints.add(run_key)
        self.counts["checkpoint_loads"] += 1

    def record_npz_open(self, run_key: str, case_id: str) -> None:
        key = (run_key, case_id)
        if key in self._npz:
            raise ContractError(f"duplicate NPZ open: {run_key}/{case_id}")
        self._npz.add(key)
        self.counts["npz_open_events"] += 1

    def record_member(self, member: str) -> None:
        if member not in ALLOWED_NPZ_MEMBERS:
            raise ContractError(f"forbidden NPZ member: {member}")
        self.counts[f"member_{member}"] += 1

    def record_forward(self) -> None:
        self.counts["model_case_forward_calls"] += 1

    def record_beta_assignment(self) -> None:
        self.counts["temporary_beta_assignments"] += 1

    def record_beta_restoration(self) -> None:
        self.counts["temporary_beta_restorations"] += 1

    def assert_final(self) -> None:
        expected = {
            "checkpoint_loads": 2,
            "npz_open_events": 210,
            "member_partial": 210,
            "member_implant": 210,
            "member_gt": 210,
            "model_case_forward_calls": 420,
            "temporary_beta_assignments": 210,
            "temporary_beta_restorations": 210,
            "qc_checkpoint_loads": 0,
            "qc_model_forwards": 0,
            "optimizer_constructions": 0,
            "optimizer_steps": 0,
            "model_parameter_updates": 0,
            "persistent_net_buffer_updates": 0,
        }
        for name, value in expected.items():
            if self.counts[name] != value:
                raise ContractError(f"counter {name}={self.counts[name]}, expected {value}")

    def receipt_counts(self) -> dict[str, int]:
        names = (
            "checkpoint_loads",
            "npz_open_events",
            "member_partial",
            "member_implant",
            "member_gt",
            "model_case_forward_calls",
            "temporary_beta_assignments",
            "temporary_beta_restorations",
            "qc_checkpoint_loads",
            "qc_model_forwards",
            "optimizer_constructions",
            "optimizer_steps",
            "model_parameter_updates",
            "persistent_net_buffer_updates",
        )
        return {name: int(self.counts[name]) for name in names}


@contextmanager
def temporary_beta_one(module: Any, ledger: AccessLedger | None = None) -> Iterator[None]:
    """Temporarily set only a native scalar beta=0 buffer to exactly one."""

    import torch

    beta = getattr(module, "beta", None)
    if not torch.is_tensor(beta) or beta.numel() != 1 or not torch.isfinite(beta).all():
        raise ContractError("query-conditioner beta must be one finite scalar tensor")
    if float(beta.detach().cpu().item()) != 0.0:
        raise ContractError("Q0 reverse intervention requires native beta exactly 0")
    if getattr(module, "_q0_reverse_beta_override_active", False):
        raise ContractError("nested or duplicate beta override rejected")
    original = beta.detach().clone()
    original_dtype = beta.dtype
    original_device = beta.device
    setattr(module, "_q0_reverse_beta_override_active", True)
    try:
        with torch.no_grad():
            beta.fill_(1.0)
        if (
            float(beta.detach().cpu().item()) != 1.0
            or beta.dtype != original_dtype
            or beta.device != original_device
        ):
            raise ContractError("failed to establish exact temporary beta=1")
        if ledger is not None:
            ledger.record_beta_assignment()
        yield
    finally:
        with torch.no_grad():
            beta.copy_(original)
        try:
            if (
                not torch.equal(beta.detach(), original)
                or beta.dtype != original_dtype
                or beta.device != original_device
            ):
                raise ContractError("failed to restore the exact native beta buffer")
            if ledger is not None:
                ledger.record_beta_restoration()
        finally:
            delattr(module, "_q0_reverse_beta_override_active")


def max_abs_difference(left: Any, right: Any) -> float:
    import torch

    if not torch.is_tensor(left) or not torch.is_tensor(right) or left.shape != right.shape:
        raise ContractError("max-abs comparison requires same-shape tensors")
    if not torch.isfinite(left).all() or not torch.isfinite(right).all():
        raise ContractError("max-abs comparison received nonfinite tensors")
    return float((left.detach().float() - right.detach().float()).abs().max().cpu().item())


def validate_execution_authorization(
    authorization: Mapping[str, Any], protocol_sha256: str, output_dir: Path
) -> None:
    for name in ("authorization_effective", "execution_authorized", "authorized_once"):
        if authorization.get(name) is not True:
            raise ContractError("formal execution authorization is not effective and single-use")
    if authorization.get("protocol_id") != PROTOCOL_ID:
        raise ContractError("execution authorization protocol identity mismatch")
    if protocol_sha256 != PROTOCOL_SHA256 or authorization.get("protocol_sha256") != protocol_sha256:
        raise ContractError("execution authorization protocol SHA mismatch")
    expected_output = authorization.get("output_directory")
    if not isinstance(expected_output, str) or Path(expected_output).resolve() != output_dir.resolve():
        raise ContractError("execution authorization output directory mismatch")
    counts = authorization.get("authorized_counts", {})
    expected_counts = {
        "checkpoint_loads": 2,
        "npz_opens": 210,
        "model_case_forward_calls": 420,
        "conditions_per_case": 2,
        "temporary_beta_assignments": 210,
        "temporary_beta_restorations": 210,
        "qc_checkpoint_loads": 0,
        "qc_model_forwards": 0,
    }
    if any(counts.get(key) != value for key, value in expected_counts.items()):
        raise ContractError("execution authorization count mismatch")
    if authorization.get("q0_reverse_intervention") is not True:
        raise ContractError("Q0 reverse intervention is not explicitly authorized")
    protected = authorization.get("protected_payload_access", {})
    forbidden = ("confirmation20", "official_test", "old_monitor", "MUG", "train_outside_dev")
    if any(bool(protected.get(name)) for name in forbidden):
        raise ContractError("execution authorization permits a protected payload")
    if authorization.get("qc_checkpoint_rerun") is not False:
        raise ContractError("QC checkpoint rerun must remain forbidden")
    if authorization.get("training_authorized") is not False or authorization.get("bncal_authorized") is not False:
        raise ContractError("training and BNCal must remain unauthorized")
    if authorization.get("round_b_authorized") is not False:
        raise ContractError("Round B must remain unauthorized")


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
    frozen_round_a_path: Path,
    frozen_round_a_sha256: str,
    frozen_qc_path: Path,
    frozen_qc_sha256: str,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, list[str]], list[dict[str, str]], list[dict[str, str]]]:
    """Verify every binding before any checkpoint deserialization or NPZ open."""

    verify_file(protocol_path, protocol_sha256)
    verify_file(authorization_path, authorization_sha256)
    verify_file(manifest_path, manifest_sha256)
    verify_file(frozen_round_a_path, frozen_round_a_sha256)
    verify_file(frozen_qc_path, frozen_qc_sha256)
    protocol = load_json(protocol_path)
    analyzer.validate_protocol(protocol)
    validate_execution_authorization(load_json(authorization_path), protocol_sha256, output_dir)
    if protocol["data_binding"]["manifest_sha256"] != manifest_sha256:
        raise ContractError("manifest SHA differs from protocol")
    refs = protocol["frozen_reference_results"]
    if refs["round_a_development"]["per_model_case_metrics_sha256"] != frozen_round_a_sha256:
        raise ContractError("frozen Round A metric SHA differs from protocol")
    if refs["round_a_i_protocol_v2_run1"]["per_condition_case_metrics_sha256"] != frozen_qc_sha256:
        raise ContractError("frozen QC metric SHA differs from protocol")
    bindings = protocol.get("implementation_bindings_read_only_at_p1", {})
    if set(bindings) != set(EXPECTED_PARENT_BINDINGS):
        raise ContractError("parent source binding set mismatch")
    for relative, expected_sha in EXPECTED_PARENT_BINDINGS.items():
        if bindings[relative].get("sha256") != expected_sha:
            raise ContractError(f"protocol source binding mismatch: {relative}")
        verify_file(
            resolve_under(REPO_ROOT, relative), expected_sha, int(bindings[relative]["bytes"])
        )
    allowlists: dict[str, list[str]] = {}
    for fold in FOLDS:
        item = protocol["development_allowlists"][fold]
        path = resolve_under(REPO_ROOT, item["path"])
        verify_file(path, item["sha256"], int(item["bytes"]))
        allowlists[fold] = _read_allowlist(path)
    if set(allowlists["A"]) & set(allowlists["B"]):
        raise ContractError("Fold A/B development allowlists overlap")
    for item in protocol["checkpoint_matrix"]:
        for path_key, sha_key, bytes_key in (
            ("runtime_config", "runtime_config_sha256", "runtime_config_bytes"),
            ("completion_receipt", "completion_receipt_sha256", "completion_receipt_bytes"),
            ("bncal_checkpoint", "bncal_checkpoint_sha256", "bncal_checkpoint_bytes"),
        ):
            verify_file(
                resolve_under(REPO_ROOT, item[path_key]), item[sha_key], int(item[bytes_key])
            )
        receipt = load_json(resolve_under(REPO_ROOT, item["completion_receipt"]))
        if (
            receipt.get("status") != "TRAINING_AND_BNCAL_PASS"
            or receipt.get("run_key") != item["run_key"]
            or receipt.get("runtime_config_sha256") != item["runtime_config_sha256"]
            or receipt.get("bncal_checkpoint_sha256") != item["bncal_checkpoint_sha256"]
        ):
            raise ContractError(f"Q0 completion receipt mismatch: {item['run_key']}")
    frozen_round_a = analyzer.read_csv(frozen_round_a_path)
    frozen_qc = analyzer.read_csv(frozen_qc_path)
    analyzer._candidate_reference(frozen_round_a, "Q0")
    analyzer._qc_condition_reference(frozen_qc, "native_qc")
    analyzer._qc_condition_reference(frozen_qc, "bias_zero")
    return protocol, allowlists, frozen_round_a, frozen_qc


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
    model.load_state_dict(
        {key.replace("module.", ""): value for key, value in raw.items()}, strict=True
    )
    return model.float()


def _forward_condition(
    model: Any,
    partial: Any,
    condition: str,
    ledger: AccessLedger,
) -> dict[str, Any]:
    import torch

    if condition not in CONDITIONS:
        raise ContractError(f"unknown Q0 reverse condition: {condition}")
    query_module = getattr(getattr(model, "base_model", None), "scqr_query_conditioner", None)
    if query_module is None:
        raise ContractError("Q0 model lacks query conditioner")
    captured: dict[str, Any] = {}
    output_hook = query_module.register_forward_hook(
        lambda _module, _args, output: captured.update(query_residual=output.residual.detach())
    )
    context = temporary_beta_one(query_module, ledger) if condition == "q0_beta1" else nullcontext()
    try:
        with context:
            expected_beta = 1.0 if condition == "q0_beta1" else 0.0
            if float(query_module.beta.detach().cpu().item()) != expected_beta:
                raise ContractError(f"wrong beta during {condition}")
            output = parent_runner.invoke_partial_only(model, partial)
            ledger.record_forward()
    finally:
        output_hook.remove()
    if float(query_module.beta.detach().cpu().item()) != 0.0:
        raise ContractError("native beta was not restored after forward")
    if not isinstance(output, (tuple, list)) or len(output) != 2:
        raise ContractError(f"unexpected model output for {condition}")
    coarse, implant = output
    if not torch.isfinite(coarse).all() or not torch.isfinite(implant).all():
        raise ContractError(f"nonfinite model output for {condition}")
    instrumentation = model.pop_full_instrumentation()
    if not isinstance(instrumentation, dict):
        raise ContractError(f"missing instrumentation for {condition}")
    backbone = instrumentation.get("backbone")
    if not isinstance(backbone, Mapping):
        raise ContractError(f"missing backbone instrumentation for {condition}")
    attention = backbone.get("scqr_query_attention")
    if attention is None or captured.get("query_residual") is None:
        raise ContractError(f"missing query diagnostics for {condition}")
    return {
        "coarse_tensor": coarse.detach(),
        "implant_tensor": implant.detach(),
        "instrumentation": instrumentation,
        "query_residual": captured["query_residual"],
        "attention": attention.detach(),
    }


def _evaluate_partition(
    item: Mapping[str, Any],
    case_ids: Sequence[str],
    manifest: Mapping[str, Mapping[str, Any]],
    device: Any,
    ledger: AccessLedger,
    protocol: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    import torch

    run_key, fold = str(item["run_key"]), str(item["fold"])
    model = _load_model(
        resolve_under(REPO_ROOT, str(item["runtime_config"])),
        resolve_under(REPO_ROOT, str(item["bncal_checkpoint"])),
        ledger,
        run_key,
    ).to(device)
    model.eval()
    model.enable_full_instrumentation(True)
    query_module = getattr(getattr(model, "base_model", None), "scqr_query_conditioner", None)
    if query_module is None or float(query_module.beta.detach().cpu().item()) != 0.0:
        raise ContractError(f"{run_key} is not a native beta=0 Q0 checkpoint")
    before = parent_runner.model_state_hashes(model)
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    coarse_threshold = float(
        protocol["numeric_contract"]["coarse_output_condition_invariance_max_abs_normalized"]
    )
    with torch.no_grad():
        for case_id in case_ids:
            record = manifest[case_id]
            ledger.record_npz_open(run_key, case_id)
            with np.load(Path(record["resolved_point_path"]), allow_pickle=False) as sample:
                if any(member not in sample.files for member in ALLOWED_NPZ_MEMBERS):
                    raise ContractError(f"NPZ lacks a required member: {case_id}")
                partial_np = parent_runner._read_npz_member(sample, "partial", ledger, case_id)
                partial = torch.from_numpy(partial_np).unsqueeze(0).to(
                    device=device, dtype=torch.float32
                )
                outputs = {
                    condition: _forward_condition(model, partial, condition, ledger)
                    for condition in CONDITIONS
                }
                implant_np = parent_runner._read_npz_member(sample, "implant", ledger, case_id)
                gt_np = parent_runner._read_npz_member(sample, "gt", ledger, case_id)
            native_coarse = outputs["native_q0"]["coarse_tensor"]
            coarse_errors = {
                condition: max_abs_difference(value["coarse_tensor"], native_coarse)
                for condition, value in outputs.items()
            }
            if max(coarse_errors.values()) > coarse_threshold:
                raise ContractError(f"coarse output changed across conditions: {fold}/{case_id}")
            attention_error = max_abs_difference(
                outputs["q0_beta1"]["attention"], outputs["native_q0"]["attention"]
            )
            prediction_error = max_abs_difference(
                outputs["q0_beta1"]["implant_tensor"],
                outputs["native_q0"]["implant_tensor"],
            )
            arrays = {"partial": partial_np, "implant": implant_np, "gt": gt_np}
            implant_tensor = torch.from_numpy(implant_np).unsqueeze(0).to(
                device=device, dtype=torch.float32
            )
            identity = {
                "run_key": run_key,
                "candidate": "Q0",
                "fold": fold,
                "seed": SEED,
                "case_id": case_id,
                "skull_id": record["skull_id"],
                "source_skull_id": record["source_skull_id"],
                "defect_type": record["defect_type"],
            }
            for condition in CONDITIONS:
                value = outputs[condition]
                metric_row, coarse_p95 = parent_runner._metric_rows(
                    value["implant_tensor"].squeeze(0).cpu().numpy(),
                    value["coarse_tensor"].squeeze(0).cpu().numpy(),
                    arrays,
                    record,
                )
                controls = {
                    "coarse_condition_max_abs_normalized": coarse_errors[condition],
                    "q0_beta1_attention_max_abs_normalized": (
                        attention_error if condition == "q0_beta1" else 0.0
                    ),
                    "q0_beta1_prediction_max_abs_normalized": (
                        prediction_error if condition == "q0_beta1" else 0.0
                    ),
                }
                rows.append({**identity, "condition": condition, **metric_row, **controls})
                instrumentation = value["instrumentation"]
                instrumentation["model_object"] = model
                diagnostic = parent_runner._diagnostics(
                    "Q0",
                    instrumentation,
                    partial,
                    implant_tensor,
                    float(record["normalization"]["scale"]),
                    value["query_residual"],
                    coarse_p95,
                )
                diagnostics.append({**identity, "condition": condition, **diagnostic, **controls})
            del outputs, partial, implant_tensor
    after = parent_runner.model_state_hashes(model)
    parent_runner.assert_state_unchanged(before, after)
    del model
    torch.cuda.empty_cache()
    return rows, diagnostics, before


def _write_json_exclusive(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _write_text_exclusive(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(value)


def _freeze_files(output_dir: Path) -> None:
    lines = []
    for path in sorted(output_dir.iterdir(), key=lambda value: value.name):
        if path.is_file() and path.name != "files.sha256":
            lines.append(f"{analyzer.sha256_file(path)}  ./{path.name}\n")
    _write_text_exclusive(output_dir / "files.sha256", "".join(lines))


def run_intervention(args: argparse.Namespace) -> int:
    import torch

    if args.device != "cuda:0":
        raise ContractError("frozen device must be cuda:0")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ContractError("exactly one visible CUDA device is required")
    if torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 4090 D":
        raise ContractError("visible GPU is not NVIDIA GeForce RTX 4090 D")
    if args.output_dir.exists():
        raise ContractError("output directory already exists")
    authorization = load_json(args.execution_authorization)
    expected_uuid = authorization.get("resource_scope", {}).get("gpu_uuid")
    if not isinstance(expected_uuid, str) or _gpu_uuid() != expected_uuid:
        raise ContractError("visible GPU UUID differs from formal authorization")
    protocol, allowlists, frozen_round_a, frozen_qc = preflight(
        args.protocol,
        args.protocol_sha256,
        args.execution_authorization,
        args.execution_authorization_sha256,
        args.manifest,
        args.manifest_sha256,
        args.frozen_round_a_case_metrics,
        args.frozen_round_a_case_metrics_sha256,
        args.frozen_qc_case_metrics,
        args.frozen_qc_case_metrics_sha256,
        args.output_dir,
    )
    manifest = parent_runner._load_manifest(args.manifest, args.data_root, allowlists)
    args.output_dir.mkdir(parents=False, exist_ok=False)
    _write_json_exclusive(
        args.output_dir / "invocation.json",
        {
            "protocol_sha256": args.protocol_sha256,
            "execution_authorization_sha256": args.execution_authorization_sha256,
            "manifest_sha256": args.manifest_sha256,
            "frozen_round_a_case_metrics_sha256": args.frozen_round_a_case_metrics_sha256,
            "frozen_qc_case_metrics_sha256": args.frozen_qc_case_metrics_sha256,
            "started_at_utc": utc_now(),
        },
    )
    ledger = AccessLedger()
    all_rows: list[dict[str, Any]] = []
    all_diagnostics: list[dict[str, Any]] = []
    state_hashes: dict[str, Any] = {}
    device = torch.device(args.device)
    try:
        for item in protocol["checkpoint_matrix"]:
            rows, diagnostics, state = _evaluate_partition(
                item,
                allowlists[item["fold"]],
                manifest,
                device,
                ledger,
                protocol,
            )
            all_rows.extend(rows)
            all_diagnostics.extend(diagnostics)
            state_hashes[item["run_key"]] = state
        ledger.assert_final()
        sources, deltas, summary, receipt = analyzer.analyze_reverse_rows(
            all_rows, frozen_round_a, frozen_qc, protocol
        )
        analyzer.write_csv(args.output_dir / "per_condition_case_metrics.csv", all_rows)
        analyzer.write_csv(args.output_dir / "per_condition_source_metrics.csv", sources)
        analyzer.write_csv(
            args.output_dir / "reverse_intervention_diagnostics.csv", all_diagnostics
        )
        analyzer.write_csv(args.output_dir / "factorial_paired_deltas.csv", deltas)
        _write_json_exclusive(args.output_dir / "factorial_summary.json", summary)
        _write_json_exclusive(
            args.output_dir / "weight_state_classification_receipt.json", receipt
        )
        execution_receipt = {
            "protocol_id": PROTOCOL_ID,
            "status": "PASS",
            "started_at_utc": load_json(args.output_dir / "invocation.json")["started_at_utc"],
            "finished_at_utc": utc_now(),
            "counters": ledger.receipt_counts(),
            "model_state_hashes_unchanged": True,
            "state_hashes_before": state_hashes,
            "checkpoint_files_modified": False,
            "predictions_saved": False,
            "automatic_retry": False,
            "round_b_authorized": False,
            "automatic_next_run": False,
        }
        _write_json_exclusive(
            args.output_dir / "reverse_intervention_execution_receipt.json",
            execution_receipt,
        )
        _write_json_exclusive(
            args.output_dir / "environment.json",
            {
                "python": sys.version,
                "torch": torch.__version__,
                "cuda": torch.version.cuda,
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_uuid": expected_uuid,
                "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            },
        )
        _write_text_exclusive(
            args.output_dir / "formal_result_report_zh.md",
            "# Q0 反向推理干预正式结果\n\n"
            f"- 状态：PASS\n"
            f"- 总体分类：{receipt['overall_classification']}\n"
            f"- Q0 即时反向效应：{receipt['q0_reverse_effect_classification']}\n"
            f"- beta=1 权重状态结论：{receipt['weight_state_beta1_classification']}\n"
            "- 单 seed 限制：是\n"
            "- Round B 授权：否\n",
        )
        _freeze_files(args.output_dir)
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
        path = args.output_dir / "reverse_intervention_failure_receipt.json"
        if not path.exists():
            _write_json_exclusive(path, failure)
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
    parser.add_argument("--frozen-round-a-case-metrics", required=True, type=Path)
    parser.add_argument("--frozen-round-a-case-metrics-sha256", required=True)
    parser.add_argument("--frozen-qc-case-metrics", required=True, type=Path)
    parser.add_argument("--frozen-qc-case-metrics-sha256", required=True)
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
        "frozen_round_a_case_metrics",
        "frozen_qc_case_metrics",
        "output_dir",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return run_intervention(args)


if __name__ == "__main__":
    raise SystemExit(main())
