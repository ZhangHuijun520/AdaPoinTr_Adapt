#!/usr/bin/env python3
"""Issue the receipt-bound D5-A V0/V1 seed-0 training authorization."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = REPO_ROOT / "docs/mamba_v15_d5a_seed0_training_authorization_protocol_v1.json"
REPORT_PATH = REPO_ROOT / "docs/mamba_v15_d5a_seed0_training_authorization_preregistered_protocol_zh.md"
PARENT_PROTOCOL_PATH = REPO_ROOT / "docs/mamba_v15_d5_candidate_training_protocol_v1.json"
ZERO_RESULT_REPORT_PATH = REPO_ROOT / "docs/mamba_v15_d5a_v0_v1_zero_step_complete_result_zh.md"
VERSION = "mamba-v15-d5a-seed0-training-authorization-v1"
FOLDS = ("A", "B", "C", "D")
CANDIDATES = ("V0", "V1")
ORDER = tuple(f"{candidate}_{fold}" for candidate in CANDIDATES for fold in FOLDS)
EXPECTED = {
    "parent_protocol": "135cd7a99da57b36d94220fc8b6ed0ec73b87bb35443ddbd898e1216edba03ed",
    "zero_result_report": "0988705914ad6dce6604ffec6bde60f23efb8faab0282d9308d945c99e3ac357",
    "candidate_manifest": "0bf9ae52e3f94e3043b17b97a29046fcce8d20af4e84025bae30a6a81ea263f0",
    "candidate_receipt": "9f367a67737b565e34776b098260f89c5d177cb4753c88331c2981f2ac0d905b",
    "fourfold_manifest": "eade1467f7864f041c2c9e2065936f5aa8fbd84e0999d335f1d1b0b247da18fb",
    "fourfold_receipt": "ed9173f50f70bf835fb5173e03a0eb16b110476b45a2deade9afbafbddbaeafc",
    "audit_manifest": "6232d046f87ee8548d29580a635c41e3ab316d96920fcc6a9fd8ab27a78e55ed",
    "audit_summary": "a760c09eacff95841c5443155f11328a6b6a0cc6d646455e8a2d5ef35aad2840",
    "portable_manifest": "f653a82ac29c98909d987ad0b6bb618841d006ddf3144ba732d4911cff32bf8d",
    "zero_receipt": "ff3ac1dfdede66781815dce0bdd420d6f3a38145c1601e2405aa5f42493c45b0",
    "zero_metrics": "c80042f1e01cc259ef24caa51fe72aefba4caf06ad7f9cd5a2ec3d17b861b9bb",
    "zero_report": "984e66fe3ddda30790f83029c0f6b0a24521ff8a89eaca8ac6a97ab6ca2f50cf",
    "zero_manifest": "8643213bc1e0698445daaf0a0ae1dfa5d2feaa6d073be37de3eb0e6be4cfa58c",
    "result_summary": "83044d35b441b06d42025a79122cf9fe3637c68fcd9fdbc7c27d296b1c6b0262",
    "result_report": "0988705914ad6dce6604ffec6bde60f23efb8faab0282d9308d945c99e3ac357",
    "result_manifest": "87c38656e57f7066f4401dfcd391c3496635e8e3423be9d1c4e4793cbe52f12b",
    "transport_receipt": "bb84a21e5894712ba9cce9a7d800d264fa6760dff4c013ad94b8e0e0f32e8de4",
    "parent_hotfix_receipt": "e6cdb5c5c8668e68c4674015dc8a0b1f375180a0b7887329be1b6f984fde2c44",
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


def read_case_ids(path: Path) -> list[str]:
    values = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not values or len(values) != len(set(values)):
        raise RuntimeError(f"Invalid case-ID list: {path}")
    return values


def source_id(case_id: str) -> str:
    fields = case_id.split("__")
    if len(fields) != 3 or not fields[1].startswith("A"):
        raise RuntimeError(f"Invalid D5 case ID: {case_id}")
    return fields[1]


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            case_id = str(row.get("case_id", ""))
            if not case_id or case_id in rows:
                raise RuntimeError("Portable manifest contains invalid case IDs")
            rows[case_id] = row
    if len(rows) != 400:
        raise RuntimeError("Portable manifest must contain exactly 400 cases")
    return rows


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    scope = protocol.get("authorization_scope", {})
    data = protocol.get("data", {})
    training = protocol.get("training", {})
    gate = protocol.get("hard_gate", {})
    preflight = protocol.get("preflight", {})
    if not (
        protocol.get("protocol_id") == VERSION
        and protocol.get("status")
        == "preregistered_after_zero_step_result_freeze_before_seed0_training"
        and scope.get("candidates") == list(CANDIDATES)
        and scope.get("folds") == list(FOLDS)
        and scope.get("training_order") == list(ORDER)
        and scope.get("maximum_head_trainings") == 8
        and scope.get("D5A_seed0_training_authorized") is True
        and scope.get("one_shot_development_evaluation_authorized") is True
        and all(
            scope.get(key) is False
            for key in (
                "D5A_seed1_training_authorized",
                "development_all_training_authorized",
                "proposal_confirmation_access_authorized",
                "D5B_implementation_authorized",
                "D5B_training_authorized",
                "D5_candidate_selection_authorized",
                "completion_holdout_access_authorized",
                "official_test_access_authorized",
                "training_started_by_authorization",
            )
        )
        and data.get("development_cases") == 400
        and data.get("train_cases_per_fold") == 300
        and data.get("dev_cases_per_fold") == 100
        and data.get("dev_assets_may_be_opened")
        == "only_after_all_50_training_epochs_finish"
        and training.get("epochs") == 50
        and training.get("batch_size") == 8
        and training.get("optimizer_steps_per_candidate_fold") == 1900
        and training.get("maximum_optimizer_steps_total") == 15200
        and training.get("checkpoint_policy") == "final_epoch_only"
        and training.get("dev_evaluation_count_after_training") == 1
        and gate.get("V0_is_reference_and_not_eligible") is True
        and gate.get("V1_selected32_contains_positive_400_of_400") is True
        and gate.get("automatic_seed1_execution") is False
        and gate.get("automatic_confirmation_or_D5B_execution") is False
        and preflight.get("optimizer_steps") == 0
        and preflight.get("model_updates") == 0
        and preflight.get("dev_cases_accessed") == 0
    ):
        raise RuntimeError("D5-A seed-0 authorization protocol drifted")


def verify_candidate_lock(root: Path) -> dict[str, str]:
    manifest_hash = verify_manifest(root)
    receipt_path = root / "protocol_lock_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        manifest_hash == EXPECTED["candidate_manifest"]
        and sha256_file(receipt_path) == EXPECTED["candidate_receipt"]
        and receipt.get("status") == "D5_candidate_training_protocol_locked_non_runnable"
        and receipt.get("V0_V1_implementation_and_zero_step_preflight_authorized_next") is True
        and receipt.get("D5A_seed0_training_authorized") is False
        and receipt.get("D5A_seed1_training_authorized") is False
        and receipt.get("D5B_training_authorized") is False
        and receipt.get("proposal_confirmation_access_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("D5 candidate lock does not authorize this transition")
    return {
        "candidate_lock_manifest": manifest_hash,
        "candidate_lock_receipt": sha256_file(receipt_path),
    }


def verify_zero_step(zero: Path, result: Path) -> dict[str, str]:
    zero_manifest = verify_manifest(zero)
    result_manifest = verify_manifest(result)
    zero_receipt_path = zero / "zero_step_preflight_receipt.json"
    zero_metrics_path = zero / "fold_candidate_probe_metrics.csv"
    zero_report_path = zero / "zero_step_preflight_report_zh.md"
    result_summary_path = result / "d5a_v0_v1_zero_step_result_summary.json"
    result_report_path = result / "d5a_v0_v1_zero_step_complete_result_zh.md"
    actual = {
        "zero_receipt": sha256_file(zero_receipt_path),
        "zero_metrics": sha256_file(zero_metrics_path),
        "zero_report": sha256_file(zero_report_path),
        "zero_manifest": zero_manifest,
        "result_summary": sha256_file(result_summary_path),
        "result_report": sha256_file(result_report_path),
        "result_manifest": result_manifest,
    }
    if any(actual[key] != EXPECTED[key] for key in actual):
        raise RuntimeError("D5-A zero-step/result hashes do not match authorization")
    zero_receipt = json.loads(zero_receipt_path.read_text(encoding="utf-8"))
    summary = json.loads(result_summary_path.read_text(encoding="utf-8"))
    if not (
        zero_receipt.get("status") == "V0_V1_implementation_zero_step_preflight_passed"
        and zero_receipt.get("backward_passes") == 8
        and zero_receipt.get("optimizer_steps") == 0
        and zero_receipt.get("model_updates") == 0
        and zero_receipt.get("dev_cases_accessed") == 0
        and zero_receipt.get("D5A_seed0_training_authorized") is False
        and summary.get("status")
        == "D5A_V0_V1_zero_step_frozen_complete_training_still_locked"
        and summary.get("metric_rows") == 8
        and summary.get("D5A_seed0_training_authorized") is False
        and summary.get("D5A_seed1_training_authorized") is False
        and summary.get("D5B_training_authorized") is False
        and summary.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("D5-A zero-step/result semantics are invalid")
    return actual


def verify_data(fourfold: Path, audit: Path) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    fourfold_manifest = verify_manifest(fourfold)
    audit_manifest = verify_manifest(audit)
    fourfold_receipt_path = fourfold / "d5_development_protocol_lock_receipt.json"
    audit_summary_path = audit / "generation_audit_summary.json"
    portable_path = audit / "manifest_portable.jsonl"
    fourfold_receipt = json.loads(fourfold_receipt_path.read_text(encoding="utf-8"))
    audit_summary = json.loads(audit_summary_path.read_text(encoding="utf-8"))
    rows = load_manifest(portable_path)
    lineage = {
        "fourfold_manifest": fourfold_manifest,
        "fourfold_receipt": sha256_file(fourfold_receipt_path),
        "audit_manifest": audit_manifest,
        "audit_summary": sha256_file(audit_summary_path),
        "portable_manifest": sha256_file(portable_path),
    }
    if not (
        lineage["fourfold_manifest"] == EXPECTED["fourfold_manifest"]
        and lineage["fourfold_receipt"] == EXPECTED["fourfold_receipt"]
        and lineage["audit_manifest"] == EXPECTED["audit_manifest"]
        and lineage["audit_summary"] == EXPECTED["audit_summary"]
        and lineage["portable_manifest"] == EXPECTED["portable_manifest"]
        and fourfold_receipt.get("status")
        == "d5_development_generation_and_fourfold_protocol_locked"
        and fourfold_receipt.get("source_fold_leakage") == 0
        and fourfold_receipt.get("proposal_confirmation_accessed") is False
        and fourfold_receipt.get("completion_holdout_accessed") is False
        and audit_summary.get("status")
        == "generation_integrity_passed_model_training_selection_and_sealed_still_locked"
        and audit_summary.get("source_skulls") == 100
        and audit_summary.get("derived_cases") == 400
        and audit_summary.get("proposal_confirmation_accessed") is False
        and audit_summary.get("completion_holdout_accessed") is False
        and audit_summary.get("official_test_accessed") is False
    ):
        raise RuntimeError("D5 data lineage is invalid")
    return lineage, rows


def candidate_config(candidate: str) -> dict[str, Any]:
    if candidate == "V0":
        return {
            "descriptor": {"dimensions": 13, "knn": [16], "query_chunk_size": 512},
            "head": {"architecture": "13-128-64-1", "seed": 0},
            "loss": {"case_balanced_bce": 1.0, "positive_mass_nll": 0.0, "top32_margin": 0.0},
            "selector": {"algorithm": "top8_plus_conditioned_FPS24_over_top256", "selected_count": 32},
        }
    if candidate == "V1":
        return {
            "descriptor": {"dimensions": 27, "knn": [16, 32], "query_chunk_size": 512},
            "head": {"architecture": "27-64-64-context-219-128-64-1", "seed": 0},
            "loss": {"case_balanced_bce": 1.0, "positive_mass_nll": 1.0, "top32_margin": 1.0, "temperature": 1.0, "margin": 1.0},
            "selector": {"algorithm": "stable_score_top32", "selected_count": 32},
        }
    raise RuntimeError(f"Unknown D5-A candidate: {candidate}")


def runtime_configs(
    fourfold: Path, rows: Mapping[str, Mapping[str, Any]]
) -> tuple[dict[str, bytes], dict[str, Any]]:
    all_cases = set(rows)
    all_dev: set[str] = set()
    fold_data: dict[str, dict[str, Any]] = {}
    for fold in FOLDS:
        train_path = fourfold / f"fold{fold}_train_case_ids.txt"
        dev_path = fourfold / f"fold{fold}_dev_case_ids.txt"
        train = read_case_ids(train_path)
        dev = read_case_ids(dev_path)
        train_set, dev_set = set(train), set(dev)
        train_sources = {source_id(value) for value in train}
        dev_sources = {source_id(value) for value in dev}
        dev_fold_counts = Counter(str(rows[value].get("d5_fold")) for value in dev)
        if not (
            len(train) == 300
            and len(dev) == 100
            and len(train_sources) == 75
            and len(dev_sources) == 25
            and not train_set & dev_set
            and not train_sources & dev_sources
            and train_set | dev_set == all_cases
            and dev_fold_counts == Counter({fold: 100})
        ):
            raise RuntimeError(f"Fold {fold} data contract failed")
        all_dev.update(dev_set)
        fold_data[fold] = {
            "train_case_ids_file": train_path.name,
            "train_case_ids_sha256": sha256_file(train_path),
            "dev_case_ids_file": dev_path.name,
            "dev_case_ids_sha256": sha256_file(dev_path),
            "portable_manifest_file": "manifest_portable.jsonl",
            "train_cases": 300,
            "dev_cases": 100,
            "train_sources": 75,
            "dev_sources": 25,
        }
    if all_dev != all_cases:
        raise RuntimeError("Four D5-A dev folds do not cover all 400 cases")

    payloads: dict[str, bytes] = {}
    bindings: dict[str, Any] = {}
    for candidate in CANDIDATES:
        for fold in FOLDS:
            config = {
                "authorization_version": VERSION,
                "status": "D5A_seed0_candidate_fold_training_authorized_not_started",
                "candidate": candidate,
                "eligibility_candidate": candidate == "V1",
                "fold": fold,
                "seed": 0,
                "data": fold_data[fold],
                **candidate_config(candidate),
                "training": {
                    "epochs": 50,
                    "batch_size": 8,
                    "optimizer": "AdamW",
                    "learning_rate": 0.001,
                    "weight_decay": 0.0001,
                    "scheduler": "CosineAnnealingLR",
                    "scheduler_t_max_epochs": 50,
                    "minimum_learning_rate": 0.00001,
                    "gradient_clip_norm": 1.0,
                    "optimizer_steps_expected": 1900,
                    "checkpoint_policy": "final_epoch_only",
                    "dev_evaluation_count": 1,
                },
                "boundaries": {
                    "D5A_seed0_training_authorized": True,
                    "D5A_seed1_training_authorized": False,
                    "development_all_training_authorized": False,
                    "proposal_confirmation_access_authorized": False,
                    "D5B_implementation_authorized": False,
                    "D5B_training_authorized": False,
                    "D5_candidate_selection_authorized": False,
                    "selection_started": False,
                    "protected_or_sealed_data_accessed": False,
                },
            }
            name = f"MambaV15D5A_{candidate}_fold{fold}_seed0.json"
            payload = canonical_json(config)
            payloads[name] = payload
            bindings[f"{candidate}_{fold}"] = {
                "runtime_config": {"name": name, "sha256": sha256_bytes(payload)},
                "train_case_ids_sha256": fold_data[fold]["train_case_ids_sha256"],
                "dev_case_ids_sha256": fold_data[fold]["dev_case_ids_sha256"],
            }
    return payloads, bindings


def implementation_hashes() -> dict[str, str]:
    files = (
        "utils/mamba_d4a_proposal.py",
        "utils/mamba_d5a_proposal.py",
        "tools/authorize_mamba_v15_d5a_seed0_training.py",
        "tools/verify_mamba_v15_d5a_seed0_training_authorization.py",
        "tools/run_mamba_v15_d5a_seed0_training_fold.py",
        "tools/freeze_mamba_v15_d5a_seed0_training.py",
        "tools/test_mamba_v15_d5a_seed0_training_pipeline_contract.py",
        "scripts/authorize_mamba_v15_d5a_seed0_training.sh",
        "scripts/preflight_mamba_v15_d5a_seed0_training.sh",
        "scripts/run_mamba_v15_d5a_seed0_training_fold.sh",
        "scripts/run_mamba_v15_d5a_seed0_training.sh",
        "scripts/launch_mamba_v15_d5a_seed0_training_tmux.sh",
    )
    return {name: sha256_file(REPO_ROOT / name) for name in files}


def write_exact(root: Path, files: Mapping[str, bytes]) -> None:
    if root.exists():
        existing = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
        mismatches = [
            name for name, payload in files.items()
            if not (root / name).is_file() or (root / name).read_bytes() != payload
        ]
        if existing != set(files) or mismatches:
            raise RuntimeError(f"Refusing non-identical D5-A authorization: mismatches={mismatches}")
        print(f"[locked] existing authorization is byte-identical: {root}")
        return
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def manifest_bytes(files: Mapping[str, bytes]) -> bytes:
    return "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())
    ).encode("ascii")


def verify_repair_receipts(transport: Path, parent_hotfix: Path) -> dict[str, str]:
    if not (
        sha256_file(transport) == EXPECTED["transport_receipt"]
        and sha256_file(parent_hotfix) == EXPECTED["parent_hotfix_receipt"]
    ):
        raise RuntimeError("D5-A transport/lineage repair receipts drifted")
    transport_data = json.loads(transport.read_text(encoding="utf-8"))
    hotfix_data = json.loads(parent_hotfix.read_text(encoding="utf-8"))
    if not (
        transport_data.get("status") == "transport_crlf_normalized_to_canonical_lf"
        and transport_data.get("semantic_drift_detected") is False
        and hotfix_data.get("status") == "exact_frozen_parent_report_restored"
        and hotfix_data.get("report_content_changed") is False
        and hotfix_data.get("sealed_data_accessed") is False
    ):
        raise RuntimeError("D5-A repair receipt semantics are invalid")
    return {
        "transport_normalization_receipt": sha256_file(transport),
        "parent_lineage_hotfix_receipt": sha256_file(parent_hotfix),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_lock_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--zero_step_dir", type=Path, required=True)
    parser.add_argument("--zero_step_result_dir", type=Path, required=True)
    parser.add_argument("--transport_receipt", type=Path, required=True)
    parser.add_argument("--parent_hotfix_receipt", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    if (
        sha256_file(PARENT_PROTOCOL_PATH) != EXPECTED["parent_protocol"]
        or sha256_file(ZERO_RESULT_REPORT_PATH) != EXPECTED["zero_result_report"]
    ):
        raise RuntimeError("D5-A authorization parent report/protocol drifted")

    candidate_hashes = verify_candidate_lock(args.candidate_lock_dir.resolve())
    zero_hashes = verify_zero_step(
        args.zero_step_dir.resolve(), args.zero_step_result_dir.resolve()
    )
    data_hashes, rows = verify_data(
        args.fourfold_lock_dir.resolve(), args.generation_audit_dir.resolve()
    )
    repair_hashes = verify_repair_receipts(
        args.transport_receipt.resolve(), args.parent_hotfix_receipt.resolve()
    )
    configs, bindings = runtime_configs(args.fourfold_lock_dir.resolve(), rows)
    config_dir = args.config_output_dir.resolve()
    auth_dir = args.authorization_output_dir.resolve()
    write_exact(config_dir, configs)

    receipt = {
        "authorization_version": VERSION,
        "status": "D5A_V0_V1_seed0_folds_A_D_training_authorized",
        "candidates": list(CANDIDATES),
        "seed": 0,
        "training_order": list(ORDER),
        "folds": bindings,
        "lineage_sha256": {
            **candidate_hashes,
            **data_hashes,
            **zero_hashes,
            **repair_hashes,
            "authorization_protocol": sha256_file(PROTOCOL_PATH),
            "authorization_report": sha256_file(REPORT_PATH),
        },
        "implementation_sha256": implementation_hashes(),
        "epochs": 50,
        "batch_size": 8,
        "optimizer_steps_per_candidate_fold": 1900,
        "maximum_optimizer_steps_total": 15200,
        "checkpoint_policy": "final_epoch_only",
        "development_evaluation_count_per_candidate_fold": 1,
        "D5A_seed0_training_authorized": True,
        "D5A_seed1_training_authorized": False,
        "development_all_training_authorized": False,
        "proposal_confirmation_access_authorized": False,
        "D5B_implementation_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "completion_holdout_access_authorized": False,
        "official_test_access_authorized": False,
        "training_started": False,
        "selection_started": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_training_preflight_without_optimizer_or_training",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "d5a_seed0_training_authorization_receipt.json"
    auth_files = {
        receipt_name: receipt_payload,
        f"{receipt_name}.sha256": (
            f"{sha256_bytes(receipt_payload)}  {receipt_name}\n"
        ).encode("ascii"),
        "runtime_configs.sha256": manifest_bytes(configs),
        "training_authorization_protocol_v1.json": canonical_json(protocol),
        "training_authorization_report_zh.md": REPORT_PATH.read_bytes(),
    }
    auth_files["files.sha256"] = manifest_bytes(auth_files)
    write_exact(auth_dir, auth_files)
    print(f"[saved] eight authorized D5-A runtime configs: {config_dir}")
    print(f"[saved] D5-A seed-0 training authorization: {auth_dir / receipt_name}")
    print("[authorized] V0/V1 seed-0 folds A-D only; training not started")
    print("[locked] seed1=false confirmation=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
