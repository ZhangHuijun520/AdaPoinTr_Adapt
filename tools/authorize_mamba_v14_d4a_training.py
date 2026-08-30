#!/usr/bin/env python3
"""Issue the receipt-bound D4-A head-only training authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = (
    REPO_ROOT / "docs/mamba_v14_d4a_training_authorization_protocol_v1.json"
)
REPORT_PATH = (
    REPO_ROOT
    / "docs/mamba_v14_d4a_training_authorization_preregistered_protocol_zh.md"
)
PARENT_PROTOCOL_PATH = (
    REPO_ROOT / "docs/mamba_v14_d4_candidate_training_protocol_v1.json"
)
ZERO_RESULT_PATH = (
    REPO_ROOT
    / "docs/mamba_v14_d4a_implementation_zero_step_preflight_result_zh.md"
)
HOTFIX_PATH = (
    REPO_ROOT
    / "docs/mamba_v14_d4a_training_authorization_fold_binding_hotfix1_v1.json"
)
VERSION = "mamba-v14-d4a-training-authorization-v1"
FOLDS = ("A", "B", "C", "D")
EXPECTED = {
    "hotfix": "d605b93c365a067e78bc9a75440dd5fadb2aa34f2a6df8d24959b822b35816a9",
    "parent_protocol": "1fd3d6dff2876d4dbaec92b6dc34e61ba833ddee0ff7bbe4cd0abf64488eb24a",
    "zero_result": "77b311f1a14a6534e23cf31cf29b22964108c3527878785b830bc389214f97b6",
    "candidate_manifest": "baf0daca2594d8afa6c8cf47cd1efc76be3cda02f4e17ed193abea61237882f1",
    "candidate_receipt": "c515a89231145d9b081e60b92233edcacb2016c3d95726b9fd7b679adf292dde",
    "fourfold_manifest": "3b431cfddc3c9575f9269e1535bd3c4ba66c1220b64a77b14256fea152aa1b7b",
    "fourfold_receipt": "84c92aacc7a3bf7bac1d84f5ff1eb1b63a241705f07e930b99ded7ae7a1a5885",
    "generation_audit_manifest": "0b51735e0af8ef14fddca8e378155b0d9b60ff818fe163813287f7935c731929",
    "generation_audit_summary": "829a74d2eccd6bedd61bd2c1041e6120394c00ee6f645922beadeb61a45a565f",
    "portable_manifest": "709759f5a32fe8862668b5a457f9f7be60489fcabb63fa83093fd6627278e781",
    "zero_receipt": "20b728a1760d906bf89076c5991730275557065c98762c2e6d2ac0d673b91dfc",
    "zero_metrics": "b3fff3299b8e3f4354a09f9aa552e88386ca57f3ebef8163a42d357e5916cde2",
    "zero_report": "68d177bbf52c98b7a6b06a478786790b5150916e5a94d93aa0dba18fee623dfc",
    "zero_manifest": "85c9f8a322b975a8a79b31ed2ef9f1b3421c635bdf2de75bc335153df7d16a74",
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
        raise RuntimeError(f"Invalid D4 case ID: {case_id}")
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
    if (
        protocol.get("protocol_id") != VERSION
        or protocol.get("status")
        != "preregistered_after_zero_step_before_head_only_training"
        or scope.get("candidate") != "D4A_head_only"
        or scope.get("folds") != list(FOLDS)
        or scope.get("seed") != 0
        or scope.get("D4A_head_only_training_authorized") is not True
        or scope.get("one_shot_development_evaluation_authorized") is not True
        or any(
            scope.get(key) is not False
            for key in (
                "T0_training_authorized",
                "T1_training_authorized",
                "T2_training_authorized",
                "D4_candidate_selection_authorized",
                "protected_data_access_authorized",
                "training_started_by_authorization",
            )
        )
        or data.get("source_skulls") != 100
        or data.get("cases") != 400
        or data.get("train_cases_per_fold") != 300
        or data.get("dev_cases_per_fold") != 100
        or data.get("dev_assets_may_be_opened")
        != "only_after_all_50_training_epochs_finish"
        or training.get("epochs") != 50
        or training.get("batch_size") != 8
        or training.get("optimizer") != "AdamW"
        or training.get("optimizer_steps_per_fold") != 1900
        or training.get("checkpoint_policy") != "final_epoch_only"
        or training.get("dev_evaluation_count_after_training") != 1
        or gate.get("selected_32_contains_positive_for_all_400_out_of_fold_cases")
        is not True
        or gate.get("automatic_T0_T1_T2_execution") is not False
    ):
        raise RuntimeError("D4-A training authorization protocol drifted")


def verify_zero_step(root: Path) -> dict[str, Any]:
    manifest_hash = verify_manifest(root)
    receipt_path = root / "zero_step_preflight_receipt.json"
    metrics_path = root / "fold_probe_metrics.csv"
    report_path = root / "zero_step_preflight_report_zh.md"
    actual = {
        "zero_receipt": sha256_file(receipt_path),
        "zero_metrics": sha256_file(metrics_path),
        "zero_report": sha256_file(report_path),
        "zero_manifest": manifest_hash,
    }
    if any(actual[key] != EXPECTED[key] for key in actual):
        raise RuntimeError("D4-A zero-step frozen hashes do not match authorization")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        receipt.get("status") == "implementation_zero_step_preflight_passed"
        and receipt.get("folds") == 4
        and receipt.get("train_probe_cases") == 4
        and receipt.get("backward_passes") == 4
        and receipt.get("optimizer_constructed") is False
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("checkpoint_loaded") is False
        and receipt.get("checkpoint_written") is False
        and receipt.get("dev_cases_accessed") == 0
        and receipt.get("D4A_training_authorized") is False
        and receipt.get("D4_training_authorized") is False
        and receipt.get("D4_candidate_selection_authorized") is False
        and receipt.get("protected_data_accessed") is False
        and receipt.get("selection_started") is False
    ):
        raise RuntimeError("D4-A zero-step receipt semantics are invalid")
    return actual


def verify_data(
    fourfold: Path, audit: Path
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    fourfold_manifest = verify_manifest(fourfold)
    audit_manifest = verify_manifest(audit)
    fourfold_receipt = json.loads(
        (fourfold / "d4_m2_protocol_lock_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    audit_summary = json.loads(
        (audit / "generation_audit_summary.json").read_text(encoding="utf-8")
    )
    portable_path = audit / "manifest_portable.jsonl"
    rows = load_manifest(portable_path)
    if not (
        fourfold_receipt.get("status")
        == "d4_m2_generation_and_fourfold_protocol_locked"
        and fourfold_receipt.get("counts", {}).get("sources") == 100
        and fourfold_receipt.get("counts", {}).get("planned_cases") == 400
        and fourfold_receipt.get("D4_training_authorized") is False
        and fourfold_receipt.get("protected_data_accessed") is False
        and audit_summary.get("status")
        == "generation_integrity_passed_training_and_selection_still_locked"
        and audit_summary.get("source_skulls") == 100
        and audit_summary.get("derived_cases") == 400
        and audit_summary.get("D4_training_authorized") is False
        and audit_summary.get("D4_candidate_selection_authorized") is False
        and audit_summary.get("protected_data_used") is False
    ):
        raise RuntimeError("D4 data lineage is invalid")
    lineage = {
        "fourfold_manifest": fourfold_manifest,
        "fourfold_receipt": sha256_file(
            fourfold / "d4_m2_protocol_lock_receipt.json"
        ),
        "generation_audit_manifest": audit_manifest,
        "generation_audit_summary": sha256_file(
            audit / "generation_audit_summary.json"
        ),
        "portable_manifest": sha256_file(portable_path),
    }
    return lineage, rows


def runtime_configs(
    fourfold: Path, rows: Mapping[str, Mapping[str, Any]]
) -> tuple[dict[str, bytes], dict[str, Any]]:
    all_cases = set(rows)
    all_dev: set[str] = set()
    payloads: dict[str, bytes] = {}
    bindings: dict[str, Any] = {}
    for fold in FOLDS:
        train_path = fourfold / f"fold{fold}_train_case_ids.txt"
        dev_path = fourfold / f"fold{fold}_dev_case_ids.txt"
        train = read_case_ids(train_path)
        dev = read_case_ids(dev_path)
        train_set, dev_set = set(train), set(dev)
        train_sources = {source_id(value) for value in train}
        dev_sources = {source_id(value) for value in dev}
        dev_fold_counts = Counter(
            str(rows[value].get("d4_fold")) for value in dev
        )
        diagnostics = {
            "train_cases": len(train),
            "dev_cases": len(dev),
            "train_sources": len(train_sources),
            "dev_sources": len(dev_sources),
            "case_overlap": len(train_set & dev_set),
            "source_overlap": len(train_sources & dev_sources),
            "combined_cases": len(train_set | dev_set),
            "manifest_cases": len(all_cases),
            "dev_d4_fold_counts": dict(sorted(dev_fold_counts.items())),
        }
        valid = (
            diagnostics["train_cases"] == 300
            and diagnostics["dev_cases"] == 100
            and diagnostics["train_sources"] == 75
            and diagnostics["dev_sources"] == 25
            and diagnostics["case_overlap"] == 0
            and diagnostics["source_overlap"] == 0
            and train_set | dev_set == all_cases
            and dev_fold_counts == Counter({fold: 100})
        )
        if not valid:
            raise RuntimeError(
                f"Fold {fold} data contract failed: {diagnostics}"
            )
        all_dev.update(dev_set)
        config = {
            "authorization_version": VERSION,
            "status": "D4A_head_only_fold_training_authorized_not_started",
            "candidate": "D4A",
            "fold": fold,
            "seed": 0,
            "data": {
                "train_case_ids_file": train_path.name,
                "train_case_ids_sha256": sha256_file(train_path),
                "dev_case_ids_file": dev_path.name,
                "dev_case_ids_sha256": sha256_file(dev_path),
                "portable_manifest_file": "manifest_portable.jsonl",
                "train_cases": 300,
                "dev_cases": 100,
                "train_sources": 75,
                "dev_sources": 25,
            },
            "descriptor": {
                "candidate_count": 8192,
                "dimensions": 13,
                "knn": 16,
                "query_chunk_size": 512,
            },
            "head": {"layers": [13, 128, 64, 1], "seed": 0},
            "selector": {
                "mandatory_top_score_count": 8,
                "ranked_pool_size": 256,
                "diversified_count": 24,
                "selected_count": 32,
            },
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
                "D4A_training_authorized": True,
                "T0_training_authorized": False,
                "T1_training_authorized": False,
                "T2_training_authorized": False,
                "selection_started": False,
                "protected_data_accessed": False,
            },
        }
        name = f"MambaV14D4A_fold{fold}_seed0.json"
        payload = canonical_json(config)
        payloads[name] = payload
        bindings[fold] = {
            "runtime_config": {"name": name, "sha256": sha256_bytes(payload)},
            "train_case_ids_sha256": sha256_file(train_path),
            "dev_case_ids_sha256": sha256_file(dev_path),
        }
    if all_dev != all_cases:
        raise RuntimeError("Four D4-A dev folds do not cover all 400 cases")
    return payloads, bindings


def implementation_hashes() -> dict[str, str]:
    files = (
        "utils/mamba_d4a_proposal.py",
        "tools/authorize_mamba_v14_d4a_training.py",
        "tools/verify_mamba_v14_d4a_training_authorization.py",
        "tools/run_mamba_v14_d4a_training_fold.py",
        "tools/freeze_mamba_v14_d4a_training.py",
        "tools/test_mamba_v14_d4a_training_pipeline_contract.py",
        "docs/mamba_v14_d4a_training_authorization_fold_binding_hotfix1_v1.json",
        "scripts/authorize_mamba_v14_d4a_training.sh",
        "scripts/preflight_mamba_v14_d4a_training.sh",
        "scripts/run_mamba_v14_d4a_training_fold.sh",
        "scripts/run_mamba_v14_d4a_training.sh",
        "scripts/launch_mamba_v14_d4a_training_tmux.sh",
    )
    return {name: sha256_file(REPO_ROOT / name) for name in files}


def write_exact(root: Path, files: Mapping[str, bytes]) -> None:
    if root.exists():
        existing = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        }
        mismatches = [
            name
            for name, payload in files.items()
            if not (root / name).is_file() or (root / name).read_bytes() != payload
        ]
        if existing != set(files) or mismatches:
            raise RuntimeError(
                f"Refusing non-identical D4-A authorization: "
                f"extras={sorted(existing-set(files))} "
                f"missing={sorted(set(files)-existing)} "
                f"mismatches={mismatches}"
            )
        print(f"[locked] existing authorization is byte-identical: {root}")
        return
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def config_manifest(payloads: Mapping[str, bytes]) -> bytes:
    return "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(payloads.items())
    ).encode("ascii")


def output_manifest(files: Mapping[str, bytes]) -> bytes:
    return "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_lock_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--zero_step_dir", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    if (
        sha256_file(HOTFIX_PATH) != EXPECTED["hotfix"]
        or sha256_file(PARENT_PROTOCOL_PATH) != EXPECTED["parent_protocol"]
        or sha256_file(ZERO_RESULT_PATH) != EXPECTED["zero_result"]
    ):
        raise RuntimeError("D4-A authorization parent implementation drifted")

    candidate_lock = args.candidate_lock_dir.resolve()
    fourfold = args.fourfold_lock_dir.resolve()
    audit = args.generation_audit_dir.resolve()
    zero_step = args.zero_step_dir.resolve()
    config_dir = args.config_output_dir.resolve()
    auth_dir = args.authorization_output_dir.resolve()

    candidate_manifest = verify_manifest(candidate_lock)
    candidate_receipt_path = candidate_lock / "protocol_lock_receipt.json"
    candidate_receipt = json.loads(
        candidate_receipt_path.read_text(encoding="utf-8")
    )
    if not (
        candidate_receipt.get("status")
        == "candidate_training_protocol_locked_non_runnable"
        and candidate_receipt.get(
            "implementation_and_zero_step_preflight_authorized_next"
        )
        is True
        and candidate_receipt.get("D4A_execution_authorized") is False
        and candidate_receipt.get("D4_training_authorized") is False
        and candidate_receipt.get("protected_data_accessed") is False
    ):
        raise RuntimeError("D4 candidate lock does not authorize this transition")

    zero_hashes = verify_zero_step(zero_step)
    data_hashes, rows = verify_data(fourfold, audit)
    if (
        candidate_manifest != EXPECTED["candidate_manifest"]
        or sha256_file(candidate_receipt_path) != EXPECTED["candidate_receipt"]
        or any(data_hashes[key] != EXPECTED[key] for key in data_hashes)
    ):
        raise RuntimeError("D4-A authorization lineage hashes are not exact")
    configs, fold_bindings = runtime_configs(fourfold, rows)
    write_exact(config_dir, configs)

    receipt = {
        "authorization_version": VERSION,
        "status": "D4A_head_only_seed0_folds_A_D_training_authorized",
        "candidate": "D4A",
        "seed": 0,
        "fold_order": list(FOLDS),
        "folds": fold_bindings,
        "lineage_sha256": {
            "candidate_lock_manifest": candidate_manifest,
            "candidate_lock_receipt": sha256_file(candidate_receipt_path),
            **data_hashes,
            **zero_hashes,
            "authorization_protocol": sha256_file(PROTOCOL_PATH),
            "authorization_report": sha256_file(REPORT_PATH),
        },
        "implementation_sha256": implementation_hashes(),
        "epochs": 50,
        "batch_size": 8,
        "optimizer_steps_per_fold": 1900,
        "checkpoint_policy": "final_epoch_only",
        "development_evaluation_count_per_fold": 1,
        "D4A_training_authorized": True,
        "T0_training_authorized": False,
        "T1_training_authorized": False,
        "T2_training_authorized": False,
        "D4_candidate_selection_authorized": False,
        "protected_data_accessed": False,
        "training_started": False,
        "selection_started": False,
        "execution_order": [f"D4A_fold{fold}_seed0" for fold in FOLDS],
        "next_step": "run_separate_D4A_training_preflight_then_tmux_launch",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "d4a_training_authorization_receipt.json"
    files = {
        "training_authorization_protocol_v1.json": PROTOCOL_PATH.read_bytes(),
        "training_authorization_report_zh.md": REPORT_PATH.read_bytes(),
        receipt_name: receipt_payload,
        receipt_name + ".sha256": (
            f"{sha256_bytes(receipt_payload)}  {receipt_name}\n"
        ).encode("ascii"),
        "runtime_configs.sha256": config_manifest(configs),
    }
    files["files.sha256"] = output_manifest(files)
    write_exact(auth_dir, files)
    print(f"[saved] four authorized D4-A runtime configs: {config_dir}")
    print(f"[saved] D4-A training authorization: {auth_dir / receipt_name}")
    print("[authorized] D4-A head-only seed-0 folds A-D only")
    print("[locked] T0=false T1=false T2=false selection=false protected=false")
    print("[next] run separate preflight; training was not started")


if __name__ == "__main__":
    main()
