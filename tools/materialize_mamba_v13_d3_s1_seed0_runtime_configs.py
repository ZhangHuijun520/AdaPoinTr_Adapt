#!/usr/bin/env python3
"""Materialize non-runnable S1 configs from frozen fold calibration receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = REPO_ROOT / "docs/mamba_v13_d3_s1_runtime_config_materialization_protocol_v1.json"
REPORT = REPO_ROOT / "docs/mamba_v13_d3_s1_runtime_config_materialization_preregistered_protocol_zh.md"
PROTOCOL_ID = "mamba-v13-d3-s1-seed0-runtime-config-materialization-v1"
ROUND_PROTOCOL_ID = "mamba-v13-d3-round-a-candidate-execution-v1"
COMPLETION_VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-completion-v1"
FOLD_VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-fold-v1"
FOLDS = ("A", "B", "C", "D")
TARGET_RATIO = 0.075


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve(path: str | Path) -> Path:
    result = Path(path)
    if not result.is_absolute():
        result = REPO_ROOT / result
    return result.resolve()


def verify_tree(root: Path) -> None:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing frozen files manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        expected, raw_name = line.split(maxsplit=1)
        path = root / raw_name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen tree mismatch: {path}")


def verify_sidecar(path: Path) -> str:
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    if len(fields) < 2 or Path(fields[1]).name != path.name:
        raise RuntimeError(f"Malformed SHA256 sidecar: {sidecar}")
    actual = sha256_file(path)
    if actual != fields[0].lower():
        raise RuntimeError(f"SHA256 mismatch: {path}")
    return actual


def write_exact_directory(root: Path, files: dict[str, bytes]) -> None:
    if root.exists():
        existing = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*") if path.is_file()
        }
        mismatches = [
            name for name, payload in files.items()
            if not (root / name).is_file() or (root / name).read_bytes() != payload
        ]
        if existing != set(files) or mismatches:
            raise RuntimeError(
                f"Refusing non-identical S1 materialization: extras={sorted(existing - set(files))} "
                f"missing={sorted(set(files) - existing)} mismatches={mismatches}"
            )
        print(f"[locked] existing S1 materialization is byte-identical: {root}")
        return
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol_lock_dir", type=Path, required=True)
    parser.add_argument("--completion_receipt", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--receipt_output_dir", type=Path, required=True)
    args = parser.parse_args()

    lock_dir = args.protocol_lock_dir.resolve()
    completion_path = args.completion_receipt.resolve()
    config_dir = args.config_output_dir.resolve()
    receipt_dir = args.receipt_output_dir.resolve()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if not (
        protocol.get("protocol_id") == PROTOCOL_ID
        and protocol.get("status")
        == "preregistered_after_calibration_before_materialization"
        and protocol["materialized_config_state"]["training_authorized"] is False
        and protocol["materialized_config_state"]["holdout_authorized"] is False
    ):
        raise RuntimeError("S1 materialization protocol is invalid")

    verify_tree(lock_dir)
    lock_receipt_path = lock_dir / "protocol_lock_receipt.json"
    lock_receipt = json.loads(lock_receipt_path.read_text(encoding="utf-8"))
    if not (
        lock_receipt.get("protocol_id") == ROUND_PROTOCOL_ID
        and lock_receipt.get("status") == "candidate_templates_locked"
        and lock_receipt.get("config_template_count") == 12
        and lock_receipt.get("training_authorized") is False
        and lock_receipt.get("holdout_authorized") is False
        and lock_receipt.get("model_selection_started") is False
    ):
        raise RuntimeError("Round-A template lock is invalid")
    lock_hashes = {}
    for line in (lock_dir / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        lock_hashes[name.lstrip("*")] = expected.lower()

    completion_sha = verify_sidecar(completion_path)
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    if not (
        completion.get("completion_version") == COMPLETION_VERSION
        and completion.get("status") == "S1_gradient_ratio_calibration_frozen_complete"
        and completion.get("candidate") == "S1"
        and completion.get("seed") == 0
        and completion.get("fold_count") == 4
        and completion.get("batch_count_total") == 32
        and completion.get("measured_case_slots_total") == 256
        and completion.get("target_gradient_ratio") == TARGET_RATIO
        and completion.get("optimizer_steps") == 0
        and completion.get("development_metrics_consumed") is False
        and completion.get("S1_runtime_config_materialization_authorized_next") is True
        and completion.get("S1_training_authorized") is False
        and completion.get("S2_calibration_authorized") is False
        and completion.get("S2_full_training_authorized") is False
        and completion.get("holdout_authorized") is False
        and completion.get("selection_started") is False
        and set(completion.get("folds", {})) == set(FOLDS)
    ):
        raise RuntimeError("S1 calibration completion receipt is invalid")

    config_payloads: dict[str, bytes] = {}
    fold_bindings = {}
    materialization_receipt_path = receipt_dir / "s1_seed0_materialization_receipt.json"
    for fold in FOLDS:
        template_name = f"configs/MambaV13D3_S1_fold{fold}_seed0.template.yaml"
        template_path = lock_dir / template_name
        expected_template_sha = lock_hashes.get(template_name)
        if expected_template_sha is None or sha256_file(template_path) != expected_template_sha:
            raise RuntimeError(f"Frozen S1 template mismatch: fold {fold}")
        config = yaml.safe_load(template_path.read_text(encoding="utf-8"))
        execution = config["d3_execution"]
        dense = config["model"]["dense_contact_objective"]
        serialized = template_path.read_text(encoding="utf-8")
        if not (
            execution.get("candidate") == "S1"
            and execution.get("fold") == fold
            and execution.get("seed") == 0
            and execution.get("training_authorized") is False
            and execution.get("holdout_authorized") is False
            and dense == {
                "enabled": True,
                "weight": 1.0,
                "threshold_mm": 2.0,
                "temperature_mm": 0.25,
                "tail_fraction": 0.1,
            }
            and "locked_holdout_case_ids" not in serialized
            and "manifest_split: locked_holdout" not in serialized
        ):
            raise RuntimeError(f"Frozen S1 template contract changed: fold {fold}")

        completion_fold = completion["folds"][fold]
        fold_receipt_path = resolve(completion_fold["receipt"]["path"])
        if sha256_file(fold_receipt_path) != completion_fold["receipt"]["sha256"]:
            raise RuntimeError(f"Completion-bound fold receipt mismatch: fold {fold}")
        verify_tree(fold_receipt_path.parent)
        fold_receipt = json.loads(fold_receipt_path.read_text(encoding="utf-8"))
        ratio = float(completion_fold["fold_raw_ratio_median"])
        weight = float(completion_fold["calibrated_weight"])
        if not (
            fold_receipt.get("calibration_version") == FOLD_VERSION
            and fold_receipt.get("status") == "S1_fold_calibration_frozen"
            and fold_receipt.get("fold") == fold
            and fold_receipt.get("optimizer_steps") == 0
            and fold_receipt.get("development_metrics_consumed") is False
            and fold_receipt.get("holdout_accessed") is False
            and fold_receipt.get("S1_training_authorized") is False
            and fold_receipt.get("selection_started") is False
            and fold_receipt.get("template", {}).get("sha256") == expected_template_sha
            and float(fold_receipt.get("fold_raw_ratio_median")) == ratio
            and float(fold_receipt.get("calibrated_weight")) == weight
            and math.isfinite(ratio) and ratio > 0
            and math.isfinite(weight) and weight > 0
            and math.isclose(weight, TARGET_RATIO / ratio, rel_tol=1e-14, abs_tol=0.0)
            and isinstance(fold_receipt.get("tensor_hash_hotfix_receipt", {}).get("sha256"), str)
        ):
            raise RuntimeError(f"Fold calibration semantics are invalid: fold {fold}")

        dense["weight"] = weight
        execution.update({
            "status": "materialized_s1_seed0_training_not_authorized",
            "training_authorized": False,
            "holdout_authorized": False,
            "calibration_receipt_status": "frozen_complete",
            "calibrated_dense_contact_weight": weight,
            "template_sha256": expected_template_sha,
            "fold_calibration_receipt_sha256": completion_fold["receipt"]["sha256"],
            "calibration_completion_receipt_sha256": completion_sha,
            "materialization_receipt": portable(materialization_receipt_path),
            "S1_training_authorized": False,
            "S2_authorized": False,
            "selection_started": False,
        })
        runtime_name = f"MambaV13D3_S1_fold{fold}_seed0.materialized.yaml"
        payload = yaml.safe_dump(
            config, sort_keys=False, allow_unicode=False, default_flow_style=False
        ).encode("utf-8")
        loaded = yaml.safe_load(payload)
        if not (
            float(loaded["model"]["dense_contact_objective"]["weight"]) == weight
            and loaded["d3_execution"]["training_authorized"] is False
            and loaded["d3_execution"]["holdout_authorized"] is False
            and b"locked_holdout_case_ids" not in payload
            and b"manifest_split: locked_holdout" not in payload
        ):
            raise RuntimeError(f"Materialized S1 config is unsafe: fold {fold}")
        config_payloads[runtime_name] = payload
        fold_bindings[fold] = {
            "template": {"path": str(template_path), "sha256": expected_template_sha},
            "calibration_receipt": completion_fold["receipt"],
            "fold_raw_ratio_median": ratio,
            "calibrated_weight": weight,
            "materialized_config": {
                "path": portable(config_dir / runtime_name),
                "sha256": sha256_bytes(payload),
            },
        }

    write_exact_directory(config_dir, config_payloads)
    implementation_files = (
        "tools/materialize_mamba_v13_d3_s1_seed0_runtime_configs.py",
        "tools/verify_mamba_v13_d3_s1_seed0_materialization.py",
        "tools/test_mamba_v13_d3_s1_materialization_contract.py",
        "scripts/materialize_mamba_v13_d3_s1_seed0_configs.sh",
    )
    receipt = {
        "materialization_version": PROTOCOL_ID,
        "status": "S1_seed0_fold_configs_materialized_training_locked",
        "candidate": "S1",
        "seed": 0,
        "folds": fold_bindings,
        "fold_count": 4,
        "protocol": {"path": portable(PROTOCOL), "sha256": sha256_file(PROTOCOL)},
        "protocol_report": {"path": portable(REPORT), "sha256": sha256_file(REPORT)},
        "round_a_protocol_lock": {
            "path": str(lock_dir),
            "receipt_sha256": sha256_file(lock_receipt_path),
            "files_sha256": sha256_file(lock_dir / "files.sha256"),
        },
        "calibration_completion_receipt": {
            "path": portable(completion_path),
            "sha256": completion_sha,
        },
        "implementation_sha256": {
            name: sha256_file(REPO_ROOT / name) for name in implementation_files
        },
        "weights_pooled_rounded_clipped_or_manually_adjusted": False,
        "development_metrics_consumed": False,
        "optimizer_steps": 0,
        "S1_training_authorization_allowed_next": True,
        "S1_training_authorized": False,
        "S2_calibration_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_authorized": False,
        "selection_started": False,
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "s1_seed0_materialization_receipt.json"
    receipt_files = {
        "materialization_protocol_v1.json": PROTOCOL.read_bytes(),
        "materialization_report_zh.md": REPORT.read_bytes(),
        receipt_name: receipt_payload,
        receipt_name + ".sha256": (
            f"{sha256_bytes(receipt_payload)}  {receipt_name}\n"
        ).encode("ascii"),
        "materialized_configs.sha256": "".join(
            f"{sha256_bytes(payload)}  {name}\n"
            for name, payload in sorted(config_payloads.items())
        ).encode("ascii"),
    }
    receipt_files["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(receipt_files.items())
    ).encode("ascii")
    write_exact_directory(receipt_dir, receipt_files)
    print(f"[saved] four receipt-bound non-runnable S1 configs: {config_dir}")
    print(f"[saved] S1 materialization receipt: {materialization_receipt_path}")
    for fold in FOLDS:
        print(f"[weight] fold{fold}={fold_bindings[fold]['calibrated_weight']:.17g}")
    print("[locked] training=false S2=false holdout=false selection=false")
    print("[next] independent S1 seed-0 training authorization only")


if __name__ == "__main__":
    main()
