#!/usr/bin/env python3
"""Freeze the non-runnable D6-A R1 gradient-calibration contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_gradient_ratio_calibration_protocol_v1.json"
PROTOCOL_ID = "mamba-v16-d6a-r1-training-only-gradient-ratio-calibration-v1"
FOLDS = ("A", "B", "C", "D")

REPO_PARENTS = {
    "mechanism_protocol": (
        "docs/mamba_v16_d6a_slot32_mechanism_protocol_v1.json",
        "2fff4782d429a3ea70607560bee9f464fb7b4eb7cea261376a91eb648a72f284",
    ),
    "zero_step_complete_result": (
        "docs/mamba_v16_d6a_slot32_implementation_zero_step_complete_result_zh.md",
        "7f093b50e660e4828bec85b5c0f75ce2f6dc487198c648516b933969ff267b85",
    ),
    "generation_audit_complete_result": (
        "docs/mamba_v16_d6_development400_generation_audit_complete_result_zh.md",
        "e79beea12f01cb25e3a54a1118424683a2e62bcfc9de323d73c6068f0f5590e8",
    ),
    "R1_implementation": (
        "utils/mamba_d6a_slot_allocator.py",
        "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43",
    ),
}

PARENT_FILES = {
    "mechanism_manifest": (
        "mechanism",
        "files.sha256",
        "4cbad1016851057152ad536bb69462df9a2c0b3d2440780336e3f24ac69d1a12",
    ),
    "mechanism_receipt": (
        "mechanism",
        "mechanism_lock_receipt.json",
        "acd62da63f0788ed2cbca2d48a49114c4cf8cd89b49a878d7fcba94e7ecd2a89",
    ),
    "zero_step_manifest": (
        "zero_step",
        "files.sha256",
        "8d8495a30421f143aef4f660169a0777cffcecc5e11a53f396ee1de6fccfbbf9",
    ),
    "zero_step_receipt": (
        "zero_step",
        "zero_step_preflight_receipt.json",
        "63271b3567d3ad06994e63b67eac0d7f2f006055a5b93bb2ea1e1fe23efa8c7a",
    ),
    "fourfold_manifest": (
        "fourfold",
        "files.sha256",
        "6a130df708ba006a286388cd38fb8bdd0d3fac7a028d67063357fa18bbd04036",
    ),
    "fourfold_receipt": (
        "fourfold",
        "d6_development_protocol_lock_receipt.json",
        "207ffb0c9c6f5a913ab96de23b3a5f88d17bc301d53e871b181da0a3a48a374e",
    ),
    "audit_manifest": (
        "audit",
        "files.sha256",
        "fa14e67677aa64e1f0e2cdf96aa9d37062471ea3f774ca831d05bea1c95e7e7a",
    ),
    "audit_summary": (
        "audit",
        "generation_audit_summary.json",
        "f8942d6421a524ff648639e464394bd64bfa32781f7d65a6ec8c62aa7485c390",
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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


def read_protocol(path: Path = PROTOCOL) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    require(protocol.get("protocol_id") == PROTOCOL_ID, "Protocol id drifted")
    require(
        protocol.get("status") == "preregistered_before_any_D6_gradient_measurement",
        "Protocol status drifted",
    )
    role = protocol["scientific_role"]
    require(role["candidate"] == "R1", "Only R1 may be calibrated")
    require(role["R0_new_weight_calibration"] is False, "R0 was redefined")

    data = protocol["data_boundary"]
    require(data["folds"] == list(FOLDS), "Fold order drifted")
    require(data["training_cases_per_fold"] == 300, "Train count drifted")
    require(data["training_sources_per_fold"] == 75, "Train source count drifted")
    require(data["calibration_batches_per_fold"] == 8, "Batch count drifted")
    require(data["batch_size_cases"] == 8, "Batch size drifted")
    require(data["measured_case_slots_per_fold"] == 64, "Case slots drifted")
    require(data["measured_sources_per_fold"] == 16, "Measured sources drifted")
    require(data["all_four_defect_families_per_measured_source"] is True, "Family balance drifted")
    require(data["dev_cases_accessed"] == 0, "Dev access enabled")
    for key in (
        "proposal_confirmation_accessed",
        "completion_holdout_accessed",
        "official_test_accessed",
    ):
        require(data[key] is False, f"Protected access enabled: {key}")

    model = protocol["model_state"]
    require(model["candidate"] == "R1" and model["seed"] == 0, "Model binding drifted")
    require(model["checkpoint_loaded"] is False, "Checkpoint load enabled")
    require(model["checkpoint_written"] is False, "Checkpoint write enabled")
    require(model["optimizer_constructed"] is False, "Optimizer construction enabled")
    require(model["optimizer_steps"] == 0, "Optimizer step enabled")
    require(model["model_updates"] == 0, "Model update enabled")

    measurement = protocol["gradient_measurement"]
    require(
        measurement["common_gradient_object"]
        == "shared_64D_point_features_F_before_global_pool",
        "Common gradient object drifted",
    )
    require(measurement["common_object_shape_per_case"] == [8192, 64], "F shape drifted")
    require(
        measurement["losses_measured_separately_on_the_same_forward_graph"]
        == ["L_point", "L_support", "L_shape"],
        "Measured losses drifted",
    )
    require(measurement["gradient_clipping_applied"] is False, "Calibration clipping enabled")
    require(measurement["diagnostic_group_norms_affect_weights"] is False, "Diagnostic norms affect weights")

    weights = protocol["weight_rule"]
    targets = weights["target_gradient_ratio_to_L_point"]
    require(targets["lambda_support_times_L_support"] == 0.5, "Support target drifted")
    require(targets["lambda_shape_times_L_shape"] == 0.1, "Shape target drifted")
    require(weights["weight_bounds_inclusive"] == [0.0001, 10000.0], "Weight bounds drifted")
    require(weights["clipping_rounding_or_manual_adjustment_allowed"] is False, "Weight editing enabled")
    require(weights["same_fold_weight_binding_required"] is True, "Same-fold binding disabled")
    require(weights["cross_fold_pooling_allowed"] is False, "Cross-fold pooling enabled")

    effect = protocol["protocol_lock_effect"]
    require(effect["calibration_execution_authorized"] is False, "Calibration execution enabled")
    require(effect["separate_calibration_execution_authorization_allowed_next"] is True, "Next authorization disabled")
    for key in (
        "runtime_config_materialization_authorized",
        "seed0_training_authorized",
        "seed1_training_authorized",
        "proposal_confirmation_authorized",
        "D6B_authorized",
        "candidate_selection_authorized",
        "protected_or_sealed_data_accessed",
    ):
        require(effect[key] is False, f"Forbidden permission enabled: {key}")


def verify_repo_lineage(repo_root: Path) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for key, (relative, expected) in REPO_PARENTS.items():
        path = repo_root / relative
        require(path.is_file(), f"Missing repository parent: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"Repository parent drifted: {relative}")
        hashes[key] = actual
    return hashes


def verify_parent_dirs(directories: Mapping[str, Path]) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for key, (directory_key, name, expected) in PARENT_FILES.items():
        path = directories[directory_key] / name
        require(path.is_file(), f"Missing frozen parent artifact: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"Frozen parent artifact drifted: {path}")
        hashes[key] = actual

    mechanism = json.loads((directories["mechanism"] / "mechanism_lock_receipt.json").read_text())
    require(mechanism["status"] == "D6A_slot32_mechanism_frozen_implementation_not_started", "Bad mechanism status")
    require(mechanism["training_authorized"] is False, "Mechanism authorized training")

    zero = json.loads((directories["zero_step"] / "zero_step_preflight_receipt.json").read_text())
    require(zero["status"] == "D6A_R0_R1_artificial_CUDA_zero_step_passed", "Bad zero-step status")
    require(zero["D6_cases_accessed"] == 0, "Zero-step accessed D6 cases")
    require(zero["optimizer_steps"] == 0 and zero["model_updates"] == 0, "Zero-step mutated model")

    fourfold = json.loads((directories["fourfold"] / "d6_development_protocol_lock_receipt.json").read_text())
    require(fourfold["status"] == "d6_development_generation_and_fourfold_protocol_locked", "Bad fourfold status")
    require(fourfold["counts"]["train_cases_per_fold"] == 300, "Bad fold train count")
    require(fourfold["proposal_confirmation_accessed"] is False, "Confirmation was accessed")

    audit = json.loads((directories["audit"] / "generation_audit_summary.json").read_text())
    require(
        audit["status"]
        == "generation_integrity_passed_model_training_selection_and_sealed_still_locked",
        "Bad generation audit status",
    )
    require(audit["source_skulls"] == 100 and audit["derived_cases"] == 400, "Bad audited counts")
    require(audit["D6_gradient_calibration_authorized"] is False, "Audit authorized calibration")
    return hashes


def read_nonempty_lines(path: Path) -> list[str]:
    values = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(values) == len(set(values)), f"Duplicate case id in {path}")
    return values


def source_id(case_id: str) -> str:
    fields = case_id.split("__")
    require(len(fields) == 3 and fields[1].startswith("A"), f"Unexpected case id: {case_id}")
    return fields[1]


def calibration_batches(case_ids: Iterable[str], fold: str) -> list[list[str]]:
    grouped: Dict[str, list[str]] = {}
    for case_id in case_ids:
        grouped.setdefault(source_id(case_id), []).append(case_id)
    require(len(grouped) == 75, f"Fold {fold}: expected 75 sources")
    require(all(len(values) == 4 for values in grouped.values()), f"Fold {fold}: incomplete source family")
    ranked = sorted(
        grouped,
        key=lambda value: hashlib.sha256(
            f"{PROTOCOL_ID}|fold={fold}|seed0|source={value}".encode("ascii")
        ).hexdigest(),
    )
    selected = ranked[:16]
    batches = [
        grouped[selected[index]] + grouped[selected[index + 1]]
        for index in range(0, 16, 2)
    ]
    require(len(batches) == 8 and all(len(batch) == 8 for batch in batches), "Bad batch schedule")
    return batches


def build_outputs(
    protocol: Mapping[str, Any],
    fourfold_dir: Path,
    repo_hashes: Mapping[str, str],
    parent_hashes: Mapping[str, str],
) -> Dict[str, bytes]:
    outputs: Dict[str, bytes] = {
        "calibration_protocol_v1.json": PROTOCOL.read_bytes(),
        "calibration_contract.json": canonical_json(
            {
                "data_boundary": protocol["data_boundary"],
                "model_state": protocol["model_state"],
                "gradient_measurement": protocol["gradient_measurement"],
                "weight_rule": protocol["weight_rule"],
                "receipt_contract": protocol["receipt_contract"],
            }
        ),
    }
    fold_bindings: Dict[str, Any] = {}
    for fold in FOLDS:
        path = fourfold_dir / f"fold{fold}_train_case_ids.txt"
        require(path.is_file(), f"Missing fold train IDs: {path}")
        case_ids = read_nonempty_lines(path)
        require(len(case_ids) == 300, f"Fold {fold}: expected 300 train cases")
        batches = calibration_batches(case_ids, fold)
        schedule = "".join(
            f"{index:02d}\t" + "\t".join(batch) + "\n"
            for index, batch in enumerate(batches, start=1)
        ).encode("utf-8")
        schedule_name = f"folds/fold{fold}_batch_case_ids.tsv"
        outputs[schedule_name] = schedule
        binding = {
            "candidate": "R1",
            "fold": fold,
            "seed": 0,
            "train_case_ids_file": path.name,
            "train_case_ids_sha256": sha256_file(path),
            "train_cases": 300,
            "train_sources": 75,
            "calibration_batches": 8,
            "batch_size": 8,
            "measured_case_slots": 64,
            "measured_sources": 16,
            "batch_schedule_sha256": sha256_bytes(schedule),
            "calibration_execution_authorized": False,
            "training_authorized": False,
        }
        outputs[f"folds/fold{fold}_binding.json"] = canonical_json(binding)
        fold_bindings[fold] = binding

    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "D6A_R1_gradient_calibration_protocol_frozen_execution_not_authorized",
        "protocol_sha256": sha256_file(PROTOCOL),
        "repository_parent_sha256": dict(repo_hashes),
        "frozen_parent_sha256": dict(parent_hashes),
        "folds": fold_bindings,
        "target_gradient_ratios": {"support": 0.5, "shape": 0.1},
        "optimizer_steps": 0,
        "model_updates": 0,
        "dev_cases_accessed": 0,
        "calibration_execution_authorized": False,
        "separate_calibration_execution_authorization_allowed_next": True,
        "runtime_config_materialization_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "selection_started": False,
        "protected_or_sealed_data_accessed": False,
    }
    outputs["protocol_lock_receipt.json"] = canonical_json(receipt)
    outputs["protocol_lock_report_zh.md"] = (
        "# Mamba v1.6 D6-A R1 gradient calibration protocol lock\n\n"
        "- 候选：仅 R1；R0 保持冻结 D5 V1 reference。\n"
        "- 四折：每折 300 个 train case，冻结 8 x 8 个 calibration case slots。\n"
        "- 共同梯度对象：global pooling 前 shared 64D point feature F。\n"
        "- 目标比例：support=0.5，shape=0.1，分别按 8 个 raw norm 中位数计算。\n"
        "- 当前只允许下一步单独签发 calibration execution authorization。\n"
        "- Calibration、training、seed-1、confirmation、D6-B 与 selection 均未启动。\n"
    ).encode("utf-8")
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    ).encode("ascii")
    return outputs


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        require(existing == dict(outputs), f"Existing calibration protocol lock drifted: {output_dir}")
        print(f"[locked] existing D6-A calibration protocol lock is byte-identical: {output_dir}")
        return
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            target = working / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        working.replace(output_dir)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise
    print(f"[saved] immutable D6-A gradient calibration protocol: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_root", type=Path, default=ROOT)
    parser.add_argument("--mechanism_lock_dir", type=Path, required=True)
    parser.add_argument("--zero_step_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol = read_protocol()
    validate_protocol(protocol)
    repo_hashes = verify_repo_lineage(args.repo_root.resolve())
    directories = {
        "mechanism": args.mechanism_lock_dir.resolve(),
        "zero_step": args.zero_step_dir.resolve(),
        "fourfold": args.fourfold_lock_dir.resolve(),
        "audit": args.generation_audit_dir.resolve(),
    }
    parent_hashes = verify_parent_dirs(directories)
    outputs = build_outputs(protocol, directories["fourfold"], repo_hashes, parent_hashes)
    write_locked(outputs, args.out_dir.resolve())
    print("[done] D6-A R1 gradient-ratio calibration protocol frozen")
    print("[authorized-next] separate calibration execution authorization only")
    print("[locked] calibration=false training=false seed1=false D6B=false confirmation=false")


if __name__ == "__main__":
    main()
