#!/usr/bin/env python3
"""Issue the frozen D6-A R1 gradient-calibration execution authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = REPO_ROOT / "docs/mamba_v16_d6a_gradient_calibration_execution_authorization_protocol_v1.json"
REPORT = REPO_ROOT / "docs/mamba_v16_d6a_gradient_calibration_execution_authorization_preregistered_protocol_zh.md"
VERSION = "mamba-v16-d6a-gradient-calibration-execution-authorization-v1"
FOLDS = ("A", "B", "C", "D")
EXPECTED = {
    "calibration_lock_manifest": "fa41d44ccac1738f2437330d30dac61ebbd66d9df5f90decde1e873edd8f30c3",
    "calibration_protocol": "85d44b759ac12be1ec3be1f94e378f87b80076b7b602553b92c1801a1151f70b",
    "calibration_contract": "1b012285cc8c9a06350639f3d312e1523069fcb070dcbfe9945991a5f5db3a63",
    "calibration_lock_receipt": "2425b5869004e0e9fd9849dff1ac6b608023329f1bd06a3e0cc771c597ae8d6c",
    "fourfold_manifest": "6a130df708ba006a286388cd38fb8bdd0d3fac7a028d67063357fa18bbd04036",
    "audit_manifest": "fa14e67677aa64e1f0e2cdf96aa9d37062471ea3f774ca831d05bea1c95e7e7a",
    "audit_summary": "f8942d6421a524ff648639e464394bd64bfa32781f7d65a6ec8c62aa7485c390",
    "portable_manifest": "f39e44d0836545980840db2dad8969899be00b631f070fe535b8f09bbba9c682",
    "R1_implementation": "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43",
}


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


def verify_manifest(root: Path) -> str:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing files.sha256: {root}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
    return sha256_file(manifest)


def read_schedule(path: Path) -> list[list[str]]:
    batches: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 9 or fields[0] != f"{len(batches) + 1:02d}":
            raise RuntimeError(f"Invalid frozen schedule: {path}")
        batches.append(fields[1:])
    if len(batches) != 8 or any(len(batch) != 8 for batch in batches):
        raise RuntimeError(f"Expected 8 x 8 schedule: {path}")
    return batches


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    scope = protocol.get("scope", {})
    measurement = protocol.get("measurement", {})
    preflight = protocol.get("cuda_preflight", {})
    effect = protocol.get("execution_effect", {})
    if not (
        protocol.get("protocol_id") == VERSION
        and protocol.get("status") == "preregistered_after_protocol_lock_before_calibration_execution"
        and scope.get("candidate") == "R1"
        and scope.get("folds") == list(FOLDS)
        and scope.get("seed") == 0
        and scope.get("calibration_execution_authorized") is True
        and scope.get("completed_fold_rerun_authorized") is False
        and measurement.get("batches_per_fold") == 8
        and measurement.get("cases_per_batch") == 8
        and measurement.get("common_gradient_object") == "shared_64D_point_features_F_before_global_pool"
        and measurement.get("target_support_ratio") == 0.5
        and measurement.get("target_shape_ratio") == 0.1
        and measurement.get("gradient_clipping") is False
        and preflight.get("D6_cases_accessed") == 0
        and preflight.get("optimizer_steps") == 0
        and effect.get("seed0_training_authorized") is False
        and effect.get("seed1_training_authorized") is False
        and effect.get("proposal_confirmation_authorized") is False
        and effect.get("D6B_authorized") is False
        and effect.get("candidate_selection_authorized") is False
        and effect.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("D6-A calibration execution authorization protocol drifted")


def implementation_hashes() -> dict[str, str]:
    names = (
        "utils/mamba_d6a_slot_allocator.py",
        "tools/authorize_mamba_v16_d6a_gradient_calibration_execution.py",
        "tools/verify_mamba_v16_d6a_gradient_calibration_execution_authorization.py",
        "tools/preflight_mamba_v16_d6a_gradient_calibration_execution.py",
        "tools/run_mamba_v16_d6a_gradient_calibration_fold.py",
        "tools/freeze_mamba_v16_d6a_gradient_calibration.py",
        "tools/test_mamba_v16_d6a_gradient_calibration_execution_contract.py",
        "scripts/authorize_mamba_v16_d6a_gradient_calibration_execution.sh",
        "scripts/preflight_mamba_v16_d6a_gradient_calibration_execution.sh",
        "scripts/run_mamba_v16_d6a_gradient_calibration_fold.sh",
        "scripts/run_mamba_v16_d6a_gradient_calibration.sh",
        "scripts/launch_mamba_v16_d6a_gradient_calibration_tmux.sh",
    )
    hashes = {}
    for name in names:
        path = REPO_ROOT / name
        if not path.is_file():
            raise RuntimeError(f"Missing authorized implementation: {name}")
        hashes[name] = sha256_file(path)
    if hashes["utils/mamba_d6a_slot_allocator.py"] != EXPECTED["R1_implementation"]:
        raise RuntimeError("Frozen R1 implementation drifted")
    return hashes


def write_exact(root: Path, files: Mapping[str, bytes]) -> None:
    if root.exists():
        existing = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
        mismatches = [name for name, payload in files.items() if not (root / name).is_file() or (root / name).read_bytes() != payload]
        if existing != set(files) or mismatches:
            raise RuntimeError(f"Refusing non-identical authorization: {mismatches}")
        print(f"[locked] existing authorization is byte-identical: {root}")
        return
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def manifest_bytes(files: Mapping[str, bytes]) -> bytes:
    return "".join(f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())).encode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration_lock_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    calibration = args.calibration_lock_dir.resolve()
    fourfold = args.fourfold_lock_dir.resolve()
    audit = args.generation_audit_dir.resolve()
    if verify_manifest(calibration) != EXPECTED["calibration_lock_manifest"]:
        raise RuntimeError("Calibration protocol-lock manifest drifted")
    if verify_manifest(fourfold) != EXPECTED["fourfold_manifest"]:
        raise RuntimeError("D6 fourfold lock drifted")
    if verify_manifest(audit) != EXPECTED["audit_manifest"]:
        raise RuntimeError("D6 generation audit drifted")

    lock_receipt_path = calibration / "protocol_lock_receipt.json"
    lock_receipt = json.loads(lock_receipt_path.read_text(encoding="utf-8"))
    if not (
        sha256_file(calibration / "calibration_protocol_v1.json") == EXPECTED["calibration_protocol"]
        and sha256_file(calibration / "calibration_contract.json") == EXPECTED["calibration_contract"]
        and sha256_file(lock_receipt_path) == EXPECTED["calibration_lock_receipt"]
        and lock_receipt.get("status") == "D6A_R1_gradient_calibration_protocol_frozen_execution_not_authorized"
        and lock_receipt.get("separate_calibration_execution_authorization_allowed_next") is True
        and lock_receipt.get("seed0_training_authorized") is False
        and lock_receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Calibration protocol lock does not authorize this transition")

    summary_path = audit / "generation_audit_summary.json"
    portable_path = audit / "manifest_portable.jsonl"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not (
        sha256_file(summary_path) == EXPECTED["audit_summary"]
        and sha256_file(portable_path) == EXPECTED["portable_manifest"]
        and summary.get("derived_cases") == 400
        and summary.get("D6_gradient_calibration_authorized") is False
        and summary.get("proposal_confirmation_accessed") is False
        and summary.get("official_test_accessed") is False
    ):
        raise RuntimeError("D6 generation audit semantics drifted")

    configs: dict[str, bytes] = {}
    fold_bindings: dict[str, Any] = {}
    for fold in FOLDS:
        schedule = calibration / "folds" / f"fold{fold}_batch_case_ids.tsv"
        binding = calibration / "folds" / f"fold{fold}_binding.json"
        batches = read_schedule(schedule)
        config = {
            "authorization_version": VERSION,
            "status": "D6A_R1_fold_gradient_calibration_authorized_not_started",
            "candidate": "R1",
            "fold": fold,
            "seed": 0,
            "schedule_file": schedule.relative_to(calibration).as_posix(),
            "schedule_sha256": sha256_file(schedule),
            "binding_sha256": sha256_file(binding),
            "batches": 8,
            "batch_size": 8,
            "target_support_ratio": 0.5,
            "target_shape_ratio": 0.1,
            "weight_bounds_inclusive": [0.0001, 10000.0],
            "boundaries": {
                "calibration_execution_authorized": True,
                "seed0_training_authorized": False,
                "seed1_training_authorized": False,
                "proposal_confirmation_authorized": False,
                "D6B_authorized": False,
                "candidate_selection_authorized": False,
                "protected_or_sealed_data_accessed": False
            }
        }
        name = f"MambaV16D6A_R1_gradient_calibration_fold{fold}_seed0.json"
        payload = canonical_json(config)
        configs[name] = payload
        fold_bindings[fold] = {
            "config": {"name": name, "sha256": sha256_bytes(payload)},
            "schedule_sha256": sha256_file(schedule),
            "binding_sha256": sha256_file(binding),
            "probe_case_ids": batches[0],
        }

    write_exact(args.config_output_dir.resolve(), configs)
    receipt = {
        "authorization_version": VERSION,
        "status": "D6A_R1_seed0_folds_A_D_gradient_calibration_authorized",
        "candidate": "R1",
        "fold_order": list(FOLDS),
        "seed": 0,
        "folds": fold_bindings,
        "lineage_sha256": {
            "calibration_lock_manifest": EXPECTED["calibration_lock_manifest"],
            "calibration_lock_receipt": EXPECTED["calibration_lock_receipt"],
            "fourfold_manifest": EXPECTED["fourfold_manifest"],
            "generation_audit_manifest": EXPECTED["audit_manifest"],
            "generation_audit_summary": EXPECTED["audit_summary"],
            "portable_manifest": EXPECTED["portable_manifest"],
            "authorization_protocol": sha256_file(PROTOCOL),
            "authorization_report": sha256_file(REPORT),
        },
        "implementation_sha256": implementation_hashes(),
        "calibration_execution_authorized": True,
        "calibration_started": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_artificial_CUDA_preflight_before_calibration_launch",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "d6a_gradient_calibration_execution_authorization_receipt.json"
    files = {
        receipt_name: receipt_payload,
        f"{receipt_name}.sha256": f"{sha256_bytes(receipt_payload)}  {receipt_name}\n".encode("ascii"),
        "runtime_configs.sha256": manifest_bytes(configs),
        "execution_authorization_protocol_v1.json": canonical_json(protocol),
        "execution_authorization_report_zh.md": REPORT.read_bytes(),
    }
    files["files.sha256"] = manifest_bytes(files)
    write_exact(args.authorization_output_dir.resolve(), files)
    print("[authorized] D6-A R1 seed-0 gradient calibration folds A-D only")
    print("[locked] training=false seed1=false confirmation=false D6B=false sealed=false")
    print("[next] run artificial CUDA execution preflight; calibration was not started")


if __name__ == "__main__":
    main()
