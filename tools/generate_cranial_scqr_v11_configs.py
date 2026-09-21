#!/usr/bin/env python
"""Generate immutable, training-locked Cranial-SCQR v1.1 L1 configs."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = ROOT / (
    "cfgs/SkullBreak_models/AdaPoinTr_implant_full100_out8192_bncal.yaml"
)
PROTOCOL_DIR = ROOT / "logs/skullbreak_mamba_v12_development/protocol_v1"
PLAN = ROOT / "docs/cranial_scqr_v1_research_2026_09_10/experiment_plan_zh.md"
P0_RECEIPT = ROOT / (
    "logs/cranial_scqr_v11/p0_data_audit/"
    "p0_data_audit_v1_20260910T115759Z/p0_data_audit_receipt.json"
)
OUTPUT_DIR = ROOT / "cfgs/SkullBreak_models/cranial_scqr_v11"
VARIANTS = {
    "B0": (False, False, False, False, 0.0),
    "A1": (True, True, True, False, 0.0),
    "Q0": (True, True, True, True, 0.0),
    "QC": (True, True, True, True, 1.0),
}


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def _relative(path):
    return path.relative_to(ROOT).as_posix()


def _dataset_entry(subset, case_ids_file):
    return {
        "_base_": "cfgs/dataset_configs/SkullBreak.yaml",
        "others": {
            "DATA_ROOT": "data/SkullBreakPC_out8192",
            "subset": subset,
            "split_field": "official_split",
            "manifest_split": "train",
            "exclude_split_field": "monitor_split",
            "exclude_manifest_split": "monitor",
            "include_case_ids_file": _relative(case_ids_file),
            "input_key": "partial",
            "target_key": "implant",
            "N_PARTIAL": 8192,
            "N_POINTS": 8192,
        },
    }


def _scqr_block(variant):
    enabled, local, contact, query, beta = VARIANTS[variant]
    return {
        "variant": variant,
        "enabled": enabled,
        "local_geometry_enabled": local,
        "contact_supervision_enabled": contact,
        "query_conditioning_enabled": query,
        "contact_bias_beta": beta,
        "local_knn_small": 16,
        "local_knn_large": 32,
        "attention_dim": 128,
        "warmup_epochs": 20,
        "rim_band_mm": 2.0,
        "alpha_local_init": 0.01,
        "alpha_query_init": 0.01,
        "attention_dropout": 0.0,
        "probability_floor": 1.0e-4,
        "initialization_seed": 31001,
        # Filled only by the separately authorized train-only calibration.
        "auxiliary_loss_weight": None,
    }


def _base_for_fold(base, fold):
    config = copy.deepcopy(base)
    train_ids = PROTOCOL_DIR / f"fold{fold}_train_case_ids.txt"
    dev_ids = PROTOCOL_DIR / f"fold{fold}_dev_case_ids.txt"
    expected_counts = ((train_ids, 315), (dev_ids, 105))
    for path, expected in expected_counts:
        if not path.is_file():
            raise FileNotFoundError(path)
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count != expected:
            raise RuntimeError(f"{path}: expected {expected} IDs, found {count}")
    config["dataset"] = {
        "train": _dataset_entry("train", train_ids),
        "val": _dataset_entry("val", dev_ids),
        "test": _dataset_entry("test", dev_ids),
    }
    model = config["model"]
    model["mamba_adapter"] = {"enabled": False}
    model["coarse_geometry_guard"] = {
        "enabled": False,
        "mode": "none",
        "weight": 0.0,
    }
    model["local_rim_guard"] = {
        "enabled": False,
        "trust_enabled": False,
    }
    model["dense_contact_objective"] = {"enabled": False, "weight": 0.0}
    model["rim_query_allocation"] = {
        "enabled": False,
        "classification_weight": 0.0,
    }
    return config, train_ids, dev_ids


def generate(output_dir=OUTPUT_DIR):
    if not BASE_CONFIG.is_file() or not PLAN.is_file() or not P0_RECEIPT.is_file():
        raise FileNotFoundError("SCQR base, plan, or P0 receipt is missing")
    base = yaml.safe_load(BASE_CONFIG.read_text(encoding="utf-8"))
    generated = {}
    id_hashes = {}
    for fold in "AB":
        fold_base, train_ids, dev_ids = _base_for_fold(base, fold)
        id_hashes[f"fold{fold}_train"] = sha256(train_ids.read_bytes())
        id_hashes[f"fold{fold}_dev"] = sha256(dev_ids.read_bytes())
        for variant in VARIANTS:
            config = copy.deepcopy(fold_base)
            config["model"]["cranial_scqr"] = _scqr_block(variant)
            config["cranial_scqr_execution"] = {
                "stage": "L1_static_template",
                "status": "training_locked_pending_L2_L3_and_calibration",
                "training_authorized": False,
                "optimizer_steps_authorized": 0,
                "bncal_authorized": False,
                "formal_timing_authorized": False,
            }
            config["development_protocol"] = {
                "name": "cranial-scqr-v1.1",
                "candidate": variant,
                "fold": fold,
                "round": "A",
                "seed": 0,
                "development84_reused": True,
                "protected_splits_accessed": False,
                "confirmation_allowed": False,
                "old_monitor_allowed": False,
                "official_test_allowed": False,
                "mug_payload_allowed": False,
            }
            name = f"CranialSCQRV11_{variant}_fold{fold}_seed0.yaml"
            generated[name] = yaml.safe_dump(
                config,
                sort_keys=False,
                allow_unicode=False,
                default_flow_style=False,
            ).encode("utf-8")

    manifest = {
        "protocol_id": "cranial-scqr-v1.1-L1-static-configs",
        "experiment_plan": _relative(PLAN),
        "experiment_plan_sha256": sha256(PLAN.read_bytes()),
        "p0_receipt": _relative(P0_RECEIPT),
        "p0_receipt_sha256": sha256(P0_RECEIPT.read_bytes()),
        "base_config": _relative(BASE_CONFIG),
        "base_config_sha256": sha256(BASE_CONFIG.read_bytes()),
        "round": "A",
        "folds": ["A", "B"],
        "variants": list(VARIANTS),
        "seed": 0,
        "num_configs": len(generated),
        "id_list_sha256": id_hashes,
        "configs": {
            name: sha256(payload) for name, payload in sorted(generated.items())
        },
        "execution_lock": {
            "training_authorized": False,
            "optimizer_steps_authorized": 0,
            "bncal_authorized": False,
            "formal_timing_authorized": False,
            "auxiliary_loss_weight": "pending_separate_train_only_calibration",
        },
        "protected_payload_accessed": False,
    }
    generated["l1_configs_manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    output_dir = Path(output_dir)
    if output_dir.exists():
        existing = {
            path.name: path.read_bytes()
            for path in output_dir.iterdir()
            if path.is_file()
        }
        mismatches = sorted(
            name
            for name in set(existing).union(generated)
            if existing.get(name) != generated.get(name)
        )
        if mismatches:
            raise RuntimeError(
                "Refusing to overwrite non-identical SCQR L1 configs: "
                + ", ".join(mismatches)
            )
        print(f"[locked] existing SCQR L1 configs are byte-identical: {output_dir}")
        return generated

    output_dir.mkdir(parents=True)
    for name, payload in generated.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] 8 training-locked SCQR L1 configs: {output_dir}")
    return generated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    generate(args.output_dir)


if __name__ == "__main__":
    main()
