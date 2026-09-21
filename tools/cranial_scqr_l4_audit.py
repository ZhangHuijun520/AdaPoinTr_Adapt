"""Fail-closed accounting for authorized Cranial-SCQR v1.1 L4 training."""

from __future__ import annotations

import atexit
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "cranial-scqr-v1.1-l4-execution-state-v1"
EXPECTED_STEPS = 3939
EXPECTED_BATCHES = 39
EXPECTED_CASES = 315
EXPECTED_TRAVERSALS = 101


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_repo_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _require_hash_binding(execution, path_key: str, hash_key: str) -> Path:
    path = resolve_repo_path(str(getattr(execution, path_key, "")))
    if not path.is_file():
        raise RuntimeError(f"SCQR L4 binding is missing: {path_key}={path}")
    expected = str(getattr(execution, hash_key, ""))
    actual = sha256_file(path)
    if not expected or actual != expected:
        raise RuntimeError(f"SCQR L4 binding hash mismatch: {path_key}")
    return path


def _validate_external_bindings(config, execution) -> None:
    authorization = _require_hash_binding(
        execution, "authorization_receipt", "authorization_receipt_sha256"
    )
    calibration = _require_hash_binding(
        execution, "calibration_receipt", "calibration_receipt_sha256"
    )
    protocol = _require_hash_binding(
        execution, "round_a_protocol", "round_a_protocol_sha256"
    )
    train_ids = _require_hash_binding(
        execution, "train_case_ids", "train_case_ids_sha256"
    )

    authorization_payload = json.loads(authorization.read_text(encoding="utf-8"))
    development = config.development_protocol
    run_key = f"{development.candidate}_fold{development.fold}_seed0"
    if (
        authorization_payload.get("status") != "AUTHORIZED"
        or authorization_payload.get("protocol_id")
        != "cranial-scqr-v1.1-L4-roundA-training-v1"
        or run_key not in authorization_payload.get("authorized_run_keys", [])
    ):
        raise RuntimeError(f"SCQR L4 run is not in the authorization receipt: {run_key}")
    if authorization_payload.get("automatic_rerun_authorized") is not False:
        raise RuntimeError("SCQR L4 authorization must forbid automatic reruns")

    calibration_payload = json.loads(calibration.read_text(encoding="utf-8"))
    if (
        calibration_payload.get("status") != "PASS"
        or calibration_payload.get("execution_counts", {}).get("optimizer_steps") != 0
        or calibration_payload.get("training_authorized_by_this_receipt") is not False
    ):
        raise RuntimeError("SCQR L4 calibration receipt is invalid")
    fold = str(development.fold)
    calibrated = float(calibration_payload["folds"][fold]["lambda_scf"])
    variant = str(development.candidate)
    configured = getattr(config.model.cranial_scqr, "auxiliary_loss_weight", None)
    if variant == "B0":
        if configured is not None:
            raise RuntimeError("SCQR B0 must not have an auxiliary loss weight")
    elif configured is None or not math.isclose(
        float(configured), calibrated, rel_tol=0.0, abs_tol=1.0e-15
    ):
        raise RuntimeError("SCQR L4 auxiliary loss weight does not match calibration")

    protocol_payload = json.loads(protocol.read_text(encoding="utf-8"))
    if (
        protocol_payload.get("protocol_id")
        != "cranial-scqr-v1.1-L4-roundA-training-v1"
        or protocol_payload.get("status") != "FROZEN_PENDING_EXECUTION"
    ):
        raise RuntimeError("SCQR L4 Round A protocol is not frozen")

    configured_ids = resolve_repo_path(
        str(config.dataset.train.others.include_case_ids_file)
    )
    if configured_ids != train_ids:
        raise RuntimeError("SCQR L4 train allowlist path differs from bound path")


def validate_l4_contract(args, config, train_dataloader):
    execution = getattr(config, "cranial_scqr_execution", None)
    if execution is None or str(getattr(execution, "stage", "")) != "L4_roundA_training":
        return None

    development = config.development_protocol
    expected = {
        "optimizer_steps_authorized": EXPECTED_STEPS,
        "loader_batches_expected": EXPECTED_BATCHES,
        "epoch_labels_start": 0,
        "epoch_labels_end": 100,
        "epoch_traversals_expected": EXPECTED_TRAVERSALS,
        "seed": 0,
        "gpu_count": 1,
    }
    for key, value in expected.items():
        if int(getattr(execution, key, -1)) != value:
            raise RuntimeError(f"SCQR L4 {key} must equal {value}")
    if not bool(getattr(execution, "training_authorized", False)):
        raise RuntimeError("SCQR L4 training is not authorized")
    if int(args.seed) != 0 or bool(args.resume) or args.start_ckpts is not None:
        raise RuntimeError("SCQR L4 Round A requires seed=0, scratch, no resume")
    if bool(getattr(execution, "resume_authorized", True)):
        raise RuntimeError("SCQR L4 Round A resume must remain unauthorized")
    if str(getattr(execution, "checkpoint_initial_state", "")) != "scratch":
        raise RuntimeError("SCQR L4 Round A must initialize from scratch")
    if bool(getattr(execution, "development_payload_access_authorized", True)):
        raise RuntimeError("SCQR L4 training must not access dev payload")
    if not bool(getattr(execution, "bncal_authorized", False)):
        raise RuntimeError("SCQR L4 runtime must authorize train-only BNCal")
    if bool(getattr(execution, "seed1_authorized", True)):
        raise RuntimeError("SCQR L4 Round A must not authorize seed 1")
    for key in (
        "confirmation_allowed",
        "old_monitor_allowed",
        "official_test_allowed",
        "mug_payload_allowed",
    ):
        if bool(getattr(development, key, True)):
            raise RuntimeError(f"SCQR L4 protected boundary drift: {key}")
    if config.total_bs != 8 or config.step_per_update != 1 or config.max_epoch != 100:
        raise RuntimeError("SCQR L4 batch/accumulation/epoch contract drifted")
    if str(config.optimizer.type) != "AdamW":
        raise RuntimeError("SCQR L4 optimizer must be AdamW")
    if not math.isclose(float(config.optimizer.kwargs.lr), 1.0e-4):
        raise RuntimeError("SCQR L4 learning rate drifted")
    if not math.isclose(float(config.optimizer.kwargs.weight_decay), 5.0e-4):
        raise RuntimeError("SCQR L4 weight decay drifted")
    if int(getattr(config, "grad_norm_clip", 10)) != 10:
        raise RuntimeError("SCQR L4 gradient clipping drifted")
    if bool(getattr(config, "save_best_checkpoint", True)):
        raise RuntimeError("SCQR L4 best-checkpoint selection is forbidden")
    if bool(getattr(config, "save_final_epoch_checkpoints", True)):
        raise RuntimeError("SCQR L4 duplicate final checkpoints are forbidden")
    if str(getattr(execution, "checkpoint_policy", "")) != "final_only":
        raise RuntimeError("SCQR L4 checkpoint policy must be final_only")
    if len(train_dataloader) != EXPECTED_BATCHES or len(train_dataloader.dataset) != EXPECTED_CASES:
        raise RuntimeError(
            "SCQR L4 loader identity drifted: "
            f"cases={len(train_dataloader.dataset)} batches={len(train_dataloader)}"
        )
    _validate_external_bindings(config, execution)
    return execution


class ScqrL4Audit:
    def __init__(self, args, config, train_dataloader):
        self.execution = validate_l4_contract(args, config, train_dataloader)
        self.enabled = self.execution is not None
        self.finished = False
        if not self.enabled:
            return
        development = config.development_protocol
        self.steps = 0
        self.completed_epochs = 0
        self.current_epoch = None
        self.path = Path(args.experiment_path) / "l4_execution_state.json"
        self.payload = {
            "receipt_version": VERSION,
            "status": "running",
            "runtime_config_sha256": sha256_file(args.config),
            "authorization_receipt_sha256": str(
                self.execution.authorization_receipt_sha256
            ),
            "round_a_protocol_sha256": str(self.execution.round_a_protocol_sha256),
            "train_case_ids_sha256": str(self.execution.train_case_ids_sha256),
            "candidate": str(development.candidate),
            "fold": str(development.fold),
            "seed": 0,
            "start_time_utc": datetime.now(timezone.utc).isoformat(),
            "end_time_utc": None,
            "train_cases": EXPECTED_CASES,
            "loader_batches_actual": len(train_dataloader),
            "epoch_traversals_completed": 0,
            "optimizer_steps": 0,
            "optimizer_steps_authorized": EXPECTED_STEPS,
            "model_updates": 0,
            "development_payload_accessed": False,
            "bncal_updates": 0,
            "checkpoint_sha256": None,
            "peak_allocated_bytes": 0,
            "failure_or_interruption_requires_new_authorization": True,
            "resume_authorized": False,
            "seed1_authorized": False,
            "confirmation_authorized": False,
        }
        atomic_json(self.path, self.payload)
        atexit.register(self._write_exit_state)

    def begin_epoch(self, epoch: int) -> None:
        if self.enabled:
            self.current_epoch = int(epoch)

    def authorize_next_step(self) -> None:
        if self.enabled and self.steps >= EXPECTED_STEPS:
            raise RuntimeError("SCQR L4 optimizer-step authorization exhausted")

    def record_completed_step(self) -> None:
        if not self.enabled:
            return
        self.steps += 1
        if self.steps > EXPECTED_STEPS:
            raise AssertionError("SCQR L4 recorded an unauthorized optimizer step")

    def end_epoch(self) -> None:
        if not self.enabled:
            return
        self.completed_epochs += 1
        self.payload.update(
            current_epoch_label=self.current_epoch,
            epoch_traversals_completed=self.completed_epochs,
            optimizer_steps=self.steps,
            model_updates=self.steps,
            peak_allocated_bytes=int(torch.cuda.max_memory_allocated()),
        )
        atomic_json(self.path, self.payload)

    def finish(self, checkpoint_path: str | Path) -> None:
        if not self.enabled:
            return
        checkpoint_path = Path(checkpoint_path)
        if self.steps != EXPECTED_STEPS or self.completed_epochs != EXPECTED_TRAVERSALS:
            raise RuntimeError(
                f"SCQR L4 completion mismatch: steps={self.steps} epochs={self.completed_epochs}"
            )
        if not checkpoint_path.is_file():
            raise RuntimeError("SCQR L4 final checkpoint is missing")
        self.payload.update(
            status="training_complete_pending_bncal",
            end_time_utc=datetime.now(timezone.utc).isoformat(),
            optimizer_steps=self.steps,
            model_updates=self.steps,
            epoch_traversals_completed=self.completed_epochs,
            checkpoint_sha256=sha256_file(checkpoint_path),
            peak_allocated_bytes=int(torch.cuda.max_memory_allocated()),
        )
        atomic_json(self.path, self.payload)
        self.finished = True

    def _write_exit_state(self) -> None:
        if not self.enabled or self.finished:
            return
        self.payload.update(
            status="terminated_before_training_completion",
            end_time_utc=datetime.now(timezone.utc).isoformat(),
            current_epoch_label=self.current_epoch,
            epoch_traversals_completed=self.completed_epochs,
            optimizer_steps=self.steps,
            model_updates=self.steps,
            peak_allocated_bytes=int(torch.cuda.max_memory_allocated()),
        )
        try:
            atomic_json(self.path, self.payload)
        except Exception:
            pass
