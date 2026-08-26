#!/usr/bin/env python3
"""Issue an immutable S1-only seed-0 training authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = REPO_ROOT / "docs/mamba_v13_d3_s1_seed0_training_authorization_protocol_v1.json"
REPORT = REPO_ROOT / "docs/mamba_v13_d3_s1_seed0_training_authorization_preregistered_protocol_zh.md"
VERSION = "mamba-v13-d3-s1-seed0-training-authorization-v1"
FOLDS = ("A", "B", "C", "D")


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


def verify_tree(root: Path) -> None:
    for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen tree mismatch: {path}")


def verify_sidecar(path: Path) -> str:
    sidecar = Path(str(path) + ".sha256")
    expected, name = sidecar.read_text(encoding="ascii").split()[:2]
    actual = sha256_file(path)
    if Path(name).name != path.name or actual != expected.lower():
        raise RuntimeError(f"SHA256 sidecar mismatch: {path}")
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
                f"Refusing non-identical S1 authorization: extras={sorted(existing-set(files))} "
                f"missing={sorted(set(files)-existing)} mismatches={mismatches}"
            )
        print(f"[locked] existing S1 authorization is byte-identical: {root}")
        return
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def load_json_sidecar(path: Path) -> tuple[dict, str]:
    digest = verify_sidecar(path)
    return json.loads(path.read_text(encoding="utf-8")), digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialization_dir", type=Path, required=True)
    parser.add_argument("--materialized_config_dir", type=Path, required=True)
    parser.add_argument("--deployment_receipt", type=Path, required=True)
    parser.add_argument("--s0_completion", type=Path, required=True)
    parser.add_argument("--s2_negative_dir", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()

    materialization_dir = args.materialization_dir.resolve()
    materialized_config_dir = args.materialized_config_dir.resolve()
    deployment_path = args.deployment_receipt.resolve()
    s0_path = args.s0_completion.resolve()
    s2_dir = args.s2_negative_dir.resolve()
    config_dir = args.config_output_dir.resolve()
    auth_dir = args.authorization_output_dir.resolve()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if not (
        protocol.get("protocol_id") == VERSION
        and protocol.get("status")
        == "preregistered_after_materialization_before_training_authorization"
        and protocol["protected_boundaries"]["locked_holdout_authorized"] is False
        and protocol["protected_boundaries"]["S2_full_training_authorized"] is False
        and protocol["protected_boundaries"]["selection_started"] is False
    ):
        raise RuntimeError("S1 training authorization protocol is invalid")

    verify_tree(materialization_dir)
    materialization_path = materialization_dir / "s1_seed0_materialization_receipt.json"
    materialization, materialization_sha = load_json_sidecar(materialization_path)
    if not (
        materialization.get("status")
        == "S1_seed0_fold_configs_materialized_training_locked"
        and materialization.get("candidate") == "S1"
        and materialization.get("seed") == 0
        and materialization.get("fold_count") == 4
        and set(materialization.get("folds", {})) == set(FOLDS)
        and materialization.get("S1_training_authorization_allowed_next") is True
        and materialization.get("S1_training_authorized") is False
        and materialization.get("S2_full_training_authorized") is False
        and materialization.get("holdout_authorized") is False
        and materialization.get("selection_started") is False
    ):
        raise RuntimeError("S1 materialization receipt is invalid")

    deployment, deployment_sha = load_json_sidecar(deployment_path)
    if not (
        deployment.get("status") == "deployment_integrity_passed_training_still_locked"
        and deployment.get("source_skulls") == 125
        and deployment.get("derived_cases") == 500
        and deployment.get("all_derived_sha256_verified") is True
        and deployment.get("all_npz_contracts_verified") is True
        and deployment.get("case_set_exact") is True
        and deployment.get("partition_counts")
        == {"development": 400, "locked_holdout": 100}
        and deployment.get("holdout_inference_consumed") is False
        and deployment.get("holdout_metrics_consumed") is False
        and deployment.get("holdout_visual_review_consumed") is False
    ):
        raise RuntimeError("MUG500+ deployment receipt is invalid")

    s0, s0_sha = load_json_sidecar(s0_path)
    if not (
        s0.get("status") == "S0_seed0_frozen_ready_for_S2_feasibility"
        and s0.get("development_cases") == 400
        and s0.get("S1_authorized") is False
        and s0.get("holdout_authorized") is False
        and s0.get("selection_started") is False
    ):
        raise RuntimeError("S0 frozen reference completion is invalid")

    verify_tree(s2_dir)
    s2_path = s2_dir / "negative_result_receipt.json"
    s2 = json.loads(s2_path.read_text(encoding="utf-8"))
    if not (
        s2.get("status") == "frozen_negative_high_hit_rate_failed_all_case_safety_gate"
        and s2.get("S2_full_training_authorized") is False
        and s2.get("holdout_accessed") is False
        and s2.get("selection_started") is False
    ):
        raise RuntimeError("S2 negative-result lock is invalid")

    auth_receipt_path = auth_dir / "s1_seed0_training_authorization_receipt.json"
    config_payloads = {}
    fold_bindings = {}
    for fold in FOLDS:
        name = f"MambaV13D3_S1_fold{fold}_seed0.materialized.yaml"
        source = materialized_config_dir / name
        binding = materialization["folds"][fold]
        if sha256_file(source) != binding["materialized_config"]["sha256"]:
            raise RuntimeError(f"Materialized S1 config mismatch: fold {fold}")
        config = yaml.safe_load(source.read_text(encoding="utf-8"))
        execution = config["d3_execution"]
        dense = config["model"]["dense_contact_objective"]
        weight = float(binding["calibrated_weight"])
        if not (
            execution.get("status") == "materialized_s1_seed0_training_not_authorized"
            and execution.get("candidate") == "S1"
            and execution.get("fold") == fold
            and execution.get("seed") == 0
            and execution.get("training_authorized") is False
            and execution.get("holdout_authorized") is False
            and execution.get("S2_authorized") is False
            and execution.get("selection_started") is False
            and dense.get("enabled") is True
            and float(dense.get("weight")) == weight
            and dense.get("threshold_mm") == 2.0
            and dense.get("temperature_mm") == 0.25
            and dense.get("tail_fraction") == 0.1
        ):
            raise RuntimeError(f"Materialized S1 config semantics invalid: fold {fold}")
        execution.update({
            "status": "runtime_authorized_s1_seed0",
            "training_authorized": True,
            "holdout_authorized": False,
            "S1_training_authorized": True,
            "S2_authorized": False,
            "selection_started": False,
            "materialized_config_sha256": sha256_file(source),
            "materialization_receipt_sha256": materialization_sha,
            "training_authorization_receipt": portable(auth_receipt_path),
        })
        output_name = f"MambaV13D3_S1_fold{fold}_seed0.yaml"
        payload = yaml.safe_dump(
            config, sort_keys=False, allow_unicode=False, default_flow_style=False
        ).encode("utf-8")
        loaded = yaml.safe_load(payload)
        if not (
            loaded["d3_execution"]["training_authorized"] is True
            and loaded["d3_execution"]["holdout_authorized"] is False
            and float(loaded["model"]["dense_contact_objective"]["weight"]) == weight
            and b"locked_holdout_case_ids" not in payload
            and b"manifest_split: locked_holdout" not in payload
        ):
            raise RuntimeError(f"Authorized S1 config is unsafe: fold {fold}")
        config_payloads[output_name] = payload
        fold_bindings[fold] = {
            "calibrated_weight": weight,
            "materialized_config": {
                "path": portable(source), "sha256": sha256_file(source)
            },
            "authorized_config": {
                "path": portable(config_dir / output_name),
                "sha256": sha256_bytes(payload),
            },
            "calibration_receipt": binding["calibration_receipt"],
        }

    write_exact_directory(config_dir, config_payloads)
    implementation_files = (
        "main.py",
        "models/AdaPoinTr.py",
        "datasets/SkullBreakDataset.py",
        "utils/mamba_d3_contact.py",
        "utils/config.py",
        "tools/builder.py",
        "tools/runner.py",
        "tools/recalibrate_skullfix_batchnorm.py",
        "tools/evaluate_skullfix_implant.py",
        "tools/benchmark_mamba_v12_efficiency.py",
        "tools/write_mamba_v13_d3_run_record.py",
        "tools/authorize_mamba_v13_d3_s1_seed0_training.py",
        "tools/verify_mamba_v13_d3_s1_seed0_training_authorization.py",
        "tools/smoke_mamba_v13_d3_s1_seed0.py",
        "tools/freeze_mamba_v13_d3_s1_seed0.py",
        "tools/test_mamba_v13_d3_s1_training_pipeline_contract.py",
        "scripts/authorize_mamba_v13_d3_s1_seed0_training.sh",
        "scripts/preflight_mamba_v13_d3_s1_seed0.sh",
        "scripts/run_mamba_v13_d3_s1_seed0_fold.sh",
        "scripts/run_mamba_v13_d3_s1_seed0.sh",
        "scripts/launch_mamba_v13_d3_s1_seed0_tmux.sh",
    )
    implementation = {
        name: sha256_file(REPO_ROOT / name) for name in implementation_files
    }
    receipt = {
        "authorization_version": VERSION,
        "status": "S1_seed0_folds_A_D_training_authorized",
        "candidate": "S1",
        "seed": 0,
        "folds": fold_bindings,
        "fold_order": list(FOLDS),
        "materialization_receipt": {
            "path": portable(materialization_path), "sha256": materialization_sha
        },
        "deployment_receipt": {
            "path": portable(deployment_path), "sha256": deployment_sha
        },
        "s0_completion": {"path": portable(s0_path), "sha256": s0_sha},
        "s2_negative_receipt": {
            "path": portable(s2_path), "sha256": sha256_file(s2_path)
        },
        "protocol": {"path": portable(PROTOCOL), "sha256": sha256_file(PROTOCOL)},
        "protocol_report": {"path": portable(REPORT), "sha256": sha256_file(REPORT)},
        "implementation_sha256": implementation,
        "epochs": 100,
        "bncal_required": True,
        "development_evaluation_authorized": True,
        "S1_training_authorized": True,
        "S2_calibration_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_authorized": False,
        "official_test_authorized": False,
        "selection_started": False,
        "training_started": False,
        "execution_order": [f"S1_fold{fold}_seed0" for fold in FOLDS],
        "next_step": "run_S1_seed0_preflight_then_launch_folds_A_D_in_tmux",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "s1_seed0_training_authorization_receipt.json"
    files = {
        "training_authorization_protocol_v1.json": PROTOCOL.read_bytes(),
        "training_authorization_report_zh.md": REPORT.read_bytes(),
        receipt_name: receipt_payload,
        receipt_name + ".sha256": (
            f"{sha256_bytes(receipt_payload)}  {receipt_name}\n"
        ).encode("ascii"),
        "runtime_configs.sha256": "".join(
            f"{sha256_bytes(payload)}  {name}\n"
            for name, payload in sorted(config_payloads.items())
        ).encode("ascii"),
    }
    files["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    write_exact_directory(auth_dir, files)
    print(f"[saved] four S1 seed-0 authorized runtime configs: {config_dir}")
    print(f"[saved] S1 seed-0 training authorization: {auth_receipt_path}")
    print("[authorized] S1 seed-0 folds A-D development-only execution")
    print("[locked] S2=false holdout=false official_test=false selection=false")
    print("[next] run S1 preflight; training was not started")


if __name__ == "__main__":
    main()
