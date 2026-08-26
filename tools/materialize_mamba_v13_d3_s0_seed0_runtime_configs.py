#!/usr/bin/env python3
"""Materialize receipt-bound S0 seed-0 configs from frozen D3 templates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import yaml


PROTOCOL_ID = "mamba-v13-d3-round-a-candidate-execution-v1"
DEPLOYMENT_RECEIPT_ID = "mug500plus-m2-server-deployment-v1"
FOLDS = ("A", "B", "C", "D")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_sidecar(path: Path) -> str:
    sidecar = Path(str(path) + ".sha256")
    if not sidecar.is_file():
        raise RuntimeError(f"Missing SHA256 sidecar: {sidecar}")
    fields = sidecar.read_text(encoding="ascii").split()
    if len(fields) < 2 or Path(fields[1]).name != path.name:
        raise RuntimeError(f"Malformed SHA256 sidecar: {sidecar}")
    actual = sha256_file(path)
    if actual != fields[0].lower():
        raise RuntimeError(f"SHA256 mismatch: {path}")
    return actual


def verify_hash_manifest(directory: Path) -> None:
    manifest = directory / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing protocol hash manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        expected, raw_name = line.split(None, 1)
        name = raw_name.lstrip("*").strip()
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen protocol-lock mismatch: {path}")


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite non-identical file: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def validate_deployment_receipt(path: Path) -> Dict[str, Any]:
    receipt_hash = verify_sidecar(path)
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if (
        receipt.get("receipt_id") != DEPLOYMENT_RECEIPT_ID
        or receipt.get("status")
        != "deployment_integrity_passed_training_still_locked"
        or receipt.get("source_skulls") != 125
        or receipt.get("derived_cases") != 500
        or receipt.get("npz_files") != 500
        or receipt.get("partition_counts")
        != {"development": 400, "locked_holdout": 100}
        or receipt.get("development_fold_counts")
        != {fold: 100 for fold in FOLDS}
        or receipt.get("all_derived_sha256_verified") is not True
        or receipt.get("all_npz_contracts_verified") is not True
        or receipt.get("case_set_exact") is not True
        or receipt.get("holdout_inference_consumed") is not False
        or receipt.get("holdout_metrics_consumed") is not False
        or receipt.get("holdout_visual_review_consumed") is not False
        or receipt.get("training_authorized") is not False
    ):
        raise RuntimeError("Deployment receipt does not authorize S0 materialization")
    return {"receipt": receipt, "sha256": receipt_hash}


def validate_protocol_lock(directory: Path) -> Dict[str, Any]:
    verify_hash_manifest(directory)
    receipt_path = directory / "protocol_lock_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("protocol_id") != PROTOCOL_ID
        or receipt.get("status") != "candidate_templates_locked"
        or receipt.get("config_template_count") != 12
        or receipt.get("training_authorized") is not False
        or receipt.get("training_started") is not False
        or receipt.get("holdout_authorized") is not False
        or receipt.get("protected_splits_accessed") is not False
    ):
        raise RuntimeError("Frozen D3 protocol lock is not in the expected state")
    return {
        "receipt": receipt,
        "receipt_sha256": sha256_file(receipt_path),
        "files_sha256": sha256_file(directory / "files.sha256"),
    }


def materialize(
    protocol_lock_dir: Path,
    deployment_receipt_path: Path,
    config_output_dir: Path,
    authorization_output_dir: Path,
) -> Dict[str, bytes]:
    protocol = validate_protocol_lock(protocol_lock_dir)
    deployment = validate_deployment_receipt(deployment_receipt_path)
    expected_source_receipt = protocol["receipt"]["lineage_hashes"][
        "source_split_receipt"
    ]
    expected_source_files = protocol["receipt"]["lineage_hashes"][
        "source_split_files_manifest"
    ]
    if (
        deployment["receipt"].get("source_split_receipt_sha256")
        != expected_source_receipt
        or deployment["receipt"].get("source_split_files_sha256")
        != expected_source_files
    ):
        raise RuntimeError("Deployment receipt and D3 protocol lineage differ")

    authorization_receipt_path = (
        "logs/mamba_v13_d3_mug500plus/s0_seed0_authorization_v1/"
        "s0_seed0_authorization_receipt.json"
    )
    runtime_payloads: Dict[str, bytes] = {}
    template_hashes: Dict[str, str] = {}
    for fold in FOLDS:
        template_name = f"MambaV13D3_S0_fold{fold}_seed0.template.yaml"
        template_path = protocol_lock_dir / "configs" / template_name
        template_payload = template_path.read_bytes()
        config = yaml.safe_load(template_payload)
        execution = config.get("d3_execution", {})
        dense = config.get("model", {}).get("dense_contact_objective", {})
        rim = config.get("model", {}).get("rim_query_allocation", {})
        serialized = template_payload.decode("utf-8")
        if (
            execution.get("candidate") != "S0"
            or execution.get("fold") != fold
            or execution.get("seed") != 0
            or execution.get("training_authorized") is not False
            or execution.get("holdout_authorized") is not False
            or dense.get("enabled") is not False
            or rim.get("enabled") is not False
            or "locked_holdout_case_ids" in serialized
            or "manifest_split: locked_holdout" in serialized
        ):
            raise RuntimeError(f"Invalid frozen S0 template: {template_path}")

        template_hash = sha256_bytes(template_payload)
        execution.update({
            "status": "runtime_authorized_s0_seed0",
            "training_authorized": True,
            "holdout_authorized": False,
            "template_sha256": template_hash,
            "protocol_lock_receipt_sha256": protocol["receipt_sha256"],
            "deployment_receipt_sha256": deployment["sha256"],
            "authorization_receipt": authorization_receipt_path,
            "selection_started": False,
            "S1_authorized": False,
            "S2_authorized": False,
        })
        runtime_name = f"MambaV13D3_S0_fold{fold}_seed0.yaml"
        runtime_payload = yaml.safe_dump(
            config,
            sort_keys=False,
            allow_unicode=False,
            default_flow_style=False,
        ).encode("utf-8")
        if (
            b"locked_holdout_case_ids" in runtime_payload
            or b"manifest_split: locked_holdout" in runtime_payload
        ):
            raise RuntimeError(f"Runtime config leaked locked holdout: {runtime_name}")
        runtime_payloads[runtime_name] = runtime_payload
        template_hashes[template_name] = template_hash

    for name, payload in runtime_payloads.items():
        write_identical_or_new(config_output_dir / name, payload)
    existing_configs = {
        path.name for path in config_output_dir.glob("*.yaml") if path.is_file()
    }
    if existing_configs != set(runtime_payloads):
        raise RuntimeError(
            "Runtime config directory contains missing or extra YAML files: "
            f"{sorted(existing_configs)}"
        )

    runtime_hashes = {
        name: sha256_bytes(payload)
        for name, payload in sorted(runtime_payloads.items())
    }
    tool_dir = Path(__file__).resolve().parent
    receipt = {
        "authorization_id": "mamba-v13-d3-s0-seed0-runtime-v1",
        "status": "S0_seed0_runtime_configs_authorized",
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": protocol["receipt"]["protocol_sha256"],
        "protocol_lock_receipt_sha256": protocol["receipt_sha256"],
        "protocol_lock_files_sha256": protocol["files_sha256"],
        "deployment_receipt_sha256": deployment["sha256"],
        "source_split_receipt_sha256": expected_source_receipt,
        "candidate": "S0",
        "round": "A",
        "seed": 0,
        "folds": list(FOLDS),
        "runtime_config_sha256": runtime_hashes,
        "template_config_sha256": template_hashes,
        "authorization_tool_sha256": sha256_file(Path(__file__).resolve()),
        "verification_tool_sha256": sha256_file(
            tool_dir / "verify_mamba_v13_d3_s0_runtime_authorization.py"
        ),
        "training_authorized": True,
        "S1_authorized": False,
        "S2_authorized": False,
        "holdout_authorized": False,
        "holdout_inference_consumed": False,
        "holdout_metrics_consumed": False,
        "holdout_visual_review_consumed": False,
        "selection_started": False,
        "training_started": False,
        "execution_order": [f"S0_fold{fold}_seed0" for fold in FOLDS],
        "next_step": "run_S0_seed0_folds_A_to_D_in_tmux",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "s0_seed0_authorization_receipt.json"
    receipt_hash = sha256_bytes(receipt_payload)
    output_files = {
        receipt_name: receipt_payload,
        receipt_name + ".sha256": (
            f"{receipt_hash}  {receipt_name}\n"
        ).encode("ascii"),
        "runtime_configs.sha256": (
            "\n".join(
                f"{digest}  {name}" for name, digest in runtime_hashes.items()
            ) + "\n"
        ).encode("ascii"),
    }
    for name, payload in output_files.items():
        write_identical_or_new(authorization_output_dir / name, payload)
    existing_receipts = {
        path.name
        for path in authorization_output_dir.iterdir()
        if path.is_file()
    }
    if existing_receipts != set(output_files):
        raise RuntimeError(
            "Authorization directory contains missing or extra files: "
            f"{sorted(existing_receipts)}"
        )
    print(f"[saved] four receipt-bound S0 runtime configs: {config_output_dir}")
    print(f"[saved] S0 authorization receipt: {authorization_output_dir / receipt_name}")
    print(f"[sha256] {receipt_hash}")
    print("[authorized] S0 seed-0 folds A-D only")
    print("[locked] S1=false S2=false holdout=false selection_started=false")
    return runtime_payloads


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol_lock_dir", type=Path, required=True)
    parser.add_argument("--deployment_receipt", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()
    materialize(
        args.protocol_lock_dir.resolve(),
        args.deployment_receipt.resolve(),
        args.config_output_dir.resolve(),
        args.authorization_output_dir.resolve(),
    )


if __name__ == "__main__":
    main()
