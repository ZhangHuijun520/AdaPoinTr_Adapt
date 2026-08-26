#!/usr/bin/env python3
"""Create the immutable, non-runnable D3 S0/S1/S2 Round-A template lock."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = REPO_ROOT / "docs" / (
    "mamba_v13_d3_round_a_candidate_execution_protocol_v1.json"
)
PARENT_PROTOCOL = REPO_ROOT / "docs" / (
    "mamba_v13_d3_contact_support_structuralization_protocol_v1.json"
)
CANDIDATES = ("S0", "S1", "S2")
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


def verify_hash_manifest(directory: Path) -> None:
    manifest = directory / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing frozen hash manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        expected, raw_name = line.split(None, 1)
        name = raw_name.lstrip("*").strip()
        if Path(name).name != name:
            raise RuntimeError(f"Unsafe source-lock manifest entry: {name}")
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen source-lock hash mismatch: {path}")


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if (
        protocol.get("protocol_id")
        != "mamba-v13-d3-round-a-candidate-execution-v1"
        or protocol.get("status")
        != "preregistered_templates_locked_training_not_authorized"
    ):
        raise RuntimeError("Unexpected D3 execution protocol")
    effect = protocol.get("template_lock_effect", {})
    if (
        effect.get("generated_configs") != 12
        or effect.get("templates_are_directly_trainable") is not False
        or effect.get("training_authorized") is not False
        or effect.get("holdout_access_authorized") is not False
        or effect.get("training_started") is not False
        or effect.get("model_selection_started") is not False
    ):
        raise RuntimeError("D3 template lock would authorize experimental use")
    calibration = protocol.get("weight_calibration", {})
    if (
        calibration.get("batches") != 8
        or calibration.get("target_ratio") != 0.075
        or calibration.get("fold_raw_ratio")
        != "median_of_8_per_batch_raw_ratios"
        or calibration.get("calibrated_weight") != "0.075/fold_raw_ratio"
        or calibration.get("dev_metrics_forbidden", True) is not True
        or calibration.get("clipping_or_manual_adjustment_allowed") is not False
        or calibration.get("recalibration_after_training_starts") is not False
    ):
        raise RuntimeError("D3 calibration algorithm is incomplete or mutable")
    candidates = protocol.get("candidates", {})
    if set(candidates) != set(CANDIDATES):
        raise RuntimeError("D3 candidate set must be exactly S0/S1/S2")
    if (
        candidates["S1"].get("threshold_mm") != 2.0
        or candidates["S1"].get("temperature_mm") != 0.25
        or candidates["S1"].get("tail_fraction") != 0.1
        or candidates["S2"].get("global_queries") != 224
        or candidates["S2"].get("rim_queries") != 32
        or candidates["S2"].get("candidate_pool") != 96
        or candidates["S2"].get("inference_target_inputs_allowed") is not False
    ):
        raise RuntimeError("D3 candidate mechanism contract changed")


def verify_lineage(protocol: Dict[str, Any], source_lock_dir: Path) -> Dict[str, str]:
    verify_hash_manifest(source_lock_dir)
    lineage = protocol["lineage"]
    parent = lineage["scientific_protocol"]
    source = lineage["source_split_lock"]
    checks = {
        "scientific_protocol": sha256_file(PARENT_PROTOCOL),
        "source_split_protocol": sha256_file(
            source_lock_dir / "source_split_protocol_v1.json"
        ),
        "source_split_receipt": sha256_file(
            source_lock_dir / "source_split_lock_receipt.json"
        ),
        "source_split_files_manifest": sha256_file(
            source_lock_dir / "files.sha256"
        ),
    }
    expected = {
        "scientific_protocol": parent["sha256"],
        "source_split_protocol": source["protocol_sha256"],
        "source_split_receipt": source["receipt_sha256"],
        "source_split_files_manifest": source["files_manifest_sha256"],
    }
    mismatches = [key for key in checks if checks[key] != expected[key]]
    if mismatches:
        raise RuntimeError(f"D3 frozen lineage mismatch: {mismatches}")
    receipt = json.loads(
        (source_lock_dir / "source_split_lock_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    counts = receipt.get("counts", {})
    if (
        receipt.get("protocol_id") != source["protocol_id"]
        or receipt.get("status") != "source_split_locked"
        or receipt.get("training_unlocked") is not False
        or receipt.get("holdout_inference_consumed") is not False
        or receipt.get("holdout_metrics_consumed") is not False
        or receipt.get("holdout_visual_review_consumed") is not False
        or counts.get("development_skulls") != 100
        or counts.get("locked_holdout_skulls") != 25
        or counts.get("development_cases") != 400
        or counts.get("locked_holdout_cases") != 100
    ):
        raise RuntimeError("Source split does not permit D3 template locking")
    return checks


def model_config(candidate: str) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "NAME": "AdaPoinTr",
        "num_query": 256,
        "num_points": 8192,
        "center_num": [512, 256],
        "global_feature_dim": 1024,
        "encoder_type": "graph",
        "decoder_type": "fc",
        "query_selection": "learned_only",
        "denoise_weight": 0.0,
        "fine_coverage_weight": 1.0,
        "fine_local_weight": 0.0,
        "mamba_adapter": {
            "enabled": True,
            "adapter_type": "mamba_ssm",
            "depth": 2,
            "d_state": 16,
            "d_conv": 4,
            "expand": 2,
            "use_fast_path": True,
            "drop_path": 0.05,
            "alpha_init": 0.01,
            "alpha_warmup_epochs": 20,
            "alpha_warmup_start": 0.0,
            "alpha_warmup_end": 1.0,
            "order": "xyz",
        },
        "encoder_config": {
            "embed_dim": 384,
            "depth": 6,
            "num_heads": 6,
            "k": 8,
            "n_group": 2,
            "mlp_ratio": 2.0,
            "block_style_list": ["attn-graph", "attn", "attn", "attn", "attn", "attn"],
            "combine_style": "concat",
        },
        "decoder_config": {
            "embed_dim": 384,
            "depth": 8,
            "num_heads": 6,
            "k": 8,
            "n_group": 2,
            "mlp_ratio": 2.0,
            "self_attn_block_style_list": ["attn-graph"] + ["attn"] * 7,
            "self_attn_combine_style": "concat",
            "cross_attn_block_style_list": ["attn-graph"] + ["attn"] * 7,
            "cross_attn_combine_style": "concat",
        },
        "dense_contact_objective": {
            "enabled": candidate == "S1",
            "weight": 1.0 if candidate == "S1" else 0.0,
            "threshold_mm": 2.0,
            "temperature_mm": 0.25,
            "tail_fraction": 0.1,
        },
        "rim_query_allocation": {
            "enabled": candidate == "S2",
            "global_queries": 224,
            "rim_queries": 32,
            "candidate_pool": 96,
            "classification_weight": 1.0 if candidate == "S2" else 0.0,
            "selection": "score_top_pool_then_deterministic_fps",
            "anchor_offset_enabled": False,
            "type_embedding_enabled": False,
        },
    }
    return config


def dataset_section(candidate: str, fold: str) -> Dict[str, Any]:
    base = "cfgs/dataset_configs/MUG500plusM2.yaml"
    common = {
        "DATA_ROOT": "data/MUG500plusM2_v1/audit_v1",
        "ASSET_ROOT": "data/MUG500plusM2_v1/audit_v1",
        "MANIFEST": "data/MUG500plusM2SourceSplitV1/manifest_with_split.jsonl",
        "split_field": "d3_partition",
        "manifest_split": "development",
        "input_key": "partial",
        "target_key": "implant",
        "N_PARTIAL": 8192,
        "N_POINTS": 8192,
    }
    train = dict(common)
    train.update({
        "subset": "train",
        "include_case_ids_file": (
            f"data/MUG500plusM2SourceSplitV1/fold{fold}_train_case_ids.txt"
        ),
    })
    if candidate in {"S1", "S2"}:
        train["GT_RIM_KEY"] = "reference_rim_mask"
    dev = dict(common)
    dev.update({
        "subset": "val",
        "include_case_ids_file": (
            f"data/MUG500plusM2SourceSplitV1/fold{fold}_dev_case_ids.txt"
        ),
    })
    test_alias = dict(dev)
    test_alias["subset"] = "test"
    return {
        "train": {"_base_": base, "others": train},
        "val": {"_base_": base, "others": dev},
        "test": {"_base_": base, "others": test_alias},
    }


def template_config(candidate: str, fold: str, protocol_sha: str) -> Dict[str, Any]:
    calibration = "not_applicable" if candidate == "S0" else "pending"
    feasibility = "pending" if candidate == "S2" else "not_applicable"
    return {
        "optimizer": {
            "type": "AdamW",
            "kwargs": {"lr": 0.0001, "weight_decay": 0.0005},
        },
        "scheduler": {
            "type": "LambdaLR",
            "kwargs": {"decay_step": 21, "lr_decay": 0.9, "lowest_decay": 0.02},
        },
        "bnmscheduler": {
            "type": "Lambda",
            "kwargs": {
                "decay_step": 21,
                "bn_decay": 0.5,
                "bn_momentum": 0.9,
                "lowest_decay": 0.01,
            },
        },
        "dataset": dataset_section(candidate, fold),
        "model": model_config(candidate),
        "d3_execution": {
            "protocol_id": "mamba-v13-d3-round-a-candidate-execution-v1",
            "protocol_sha256": protocol_sha,
            "status": "locked_template_not_runtime_config",
            "candidate": candidate,
            "fold": fold,
            "round": "A",
            "seed": 0,
            "training_authorized": False,
            "holdout_authorized": False,
            "calibration_receipt_status": calibration,
            "feasibility_receipt_status": feasibility,
            "protected_splits_accessed": False,
        },
        "total_bs": 8,
        "step_per_update": 1,
        "max_epoch": 100,
        "consider_metric": "CDL2",
        "save_freq": 10,
        "save_best_checkpoint": True,
        "save_final_epoch_checkpoints": True,
    }


def render_report(receipt: Dict[str, Any]) -> bytes:
    lines = [
        "# Mamba v1.3 D3 Round-A 候选与执行协议冻结报告",
        "",
        "> 本次只冻结候选、配置模板、校准算法、执行顺序和选择凭据；未授权训练，未访问 locked holdout。",
        "",
        "## 冻结对象",
        "",
        "- 候选：`S0`、`S1`、`S2`，定义保持父协议不变。",
        "- 模板：12 份（3 candidates x 4 folds），全部带 `training_authorized: false`。",
        "- S1：dense 8192、2 mm contact existence、0.25 mm softmin、worst 10% GT-rim tail。",
        "- S2：224 global + 32 rim queries、96 proxy pool、partial-only anchor-preserving allocation。",
        "- S1/S2 权重：每 fold 固定前 8 个训练批次，目标梯度比 0.075，禁止 dev 调权。",
        "- S2：完整训练前必须通过同 fold 冻结 S0 encoder 的 head-only feasibility。",
        "",
        "## 权限状态",
        "",
        f"- training authorized：`{receipt['training_authorized']}`。",
        f"- holdout authorized：`{receipt['holdout_authorized']}`。",
        f"- training started：`{receipt['training_started']}`。",
        f"- protected split accessed：`{receipt['protected_splits_accessed']}`。",
        "- 下一步只能先物化 receipt-bound S0 runtime configs；S1/S2 仍需各自前置凭据。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_files(protocol_path: Path, source_lock_dir: Path) -> Dict[str, bytes]:
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes)
    validate_protocol(protocol)
    lineage_checks = verify_lineage(protocol, source_lock_dir)
    protocol_sha = sha256_bytes(protocol_bytes)
    source_files = [
        "cfgs/dataset_configs/MUG500plusM2.yaml",
        "datasets/SkullBreakDataset.py",
        "models/AdaPoinTr.py",
        "tools/runner.py",
        "utils/mamba_d3_contact.py",
        "tools/lock_mamba_v13_d3_round_a_protocol.py",
    ]
    source_hashes = {
        name: sha256_file(REPO_ROOT / name) for name in source_files
    }
    files: Dict[str, bytes] = {
        "execution_protocol_v1.json": protocol_bytes,
    }
    config_hashes = {}
    for candidate in CANDIDATES:
        for fold in FOLDS:
            name = f"configs/MambaV13D3_{candidate}_fold{fold}_seed0.template.yaml"
            payload = yaml.safe_dump(
                template_config(candidate, fold, protocol_sha),
                sort_keys=False,
                allow_unicode=False,
                default_flow_style=False,
            ).encode("utf-8")
            files[name] = payload
            config_hashes[name] = sha256_bytes(payload)
    contracts = {
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": protocol_sha,
        "candidates": protocol["candidates"],
        "weight_calibration": protocol["weight_calibration"],
        "s2_feasibility": protocol["s2_feasibility"],
        "round_a_gates": protocol["round_a_gates"],
        "config_sha256": config_hashes,
        "implementation_sha256": source_hashes,
    }
    files["candidate_contracts.json"] = canonical_json(contracts)
    selection_template = {
        "protocol_id": protocol["protocol_id"],
        "status": "unconsumed_template",
        "round": "A",
        "seed": 0,
        "candidate_results": {candidate: None for candidate in CANDIDATES},
        "gate_results": {candidate: None for candidate in CANDIDATES},
        "eligible_experimental_candidates": None,
        "selection_decision": None,
        "round_b_authorized": False,
        "locked_holdout_accessed": False,
        "old_monitor_accessed": False,
        "skullbreak_confirmation20_accessed": False,
        "skullbreak_official_test_accessed": False,
        "rule_revision_after_round_a": False,
    }
    files["round_a_selection_receipt_template.json"] = canonical_json(
        selection_template
    )
    receipt = {
        "protocol_id": protocol["protocol_id"],
        "status": "candidate_templates_locked",
        "protocol_sha256": protocol_sha,
        "source_split_lock_id": protocol["lineage"]["source_split_lock"][
            "protocol_id"
        ],
        "lineage_hashes": lineage_checks,
        "implementation_sha256": source_hashes,
        "candidate_count": 3,
        "fold_count": 4,
        "config_template_count": 12,
        "training_authorized": False,
        "holdout_authorized": False,
        "training_started": False,
        "model_selection_started": False,
        "protected_splits_accessed": False,
        "next_step": "materialize_receipt_bound_S0_seed0_runtime_configs",
    }
    files["protocol_lock_receipt.json"] = canonical_json(receipt)
    files["protocol_lock_report_zh.md"] = render_report(receipt)
    hash_lines = [
        f"{sha256_bytes(payload)}  {name}"
        for name, payload in sorted(files.items())
    ]
    files["files.sha256"] = ("\n".join(hash_lines) + "\n").encode("ascii")
    return files


def write_locked(output_dir: Path, files: Dict[str, bytes]) -> None:
    expected_names = set(files)
    if output_dir.exists():
        existing_names = {
            str(path.relative_to(output_dir)).replace("\\", "/")
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        mismatches = sorted(
            name
            for name in expected_names.intersection(existing_names)
            if (output_dir / name).read_bytes() != files[name]
        )
        extras = sorted(existing_names.difference(expected_names))
        missing = sorted(expected_names.difference(existing_names))
        if mismatches or extras or missing:
            raise RuntimeError(
                "Refusing to overwrite a non-identical D3 protocol lock: "
                f"mismatches={mismatches} extras={extras} missing={missing}"
            )
        print(f"[locked] existing D3 protocol is byte-identical: {output_dir}")
        return
    for name, payload in files.items():
        path = output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"[saved] D3 S0/S1/S2 candidate protocol lock: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_split_lock_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    args = parser.parse_args()
    files = render_files(
        args.protocol.resolve(), args.source_split_lock_dir.resolve()
    )
    write_locked(args.output_dir.resolve(), files)
    print("[locked] templates are non-runnable; training_authorized=false")
    print("[locked] locked holdout was not referenced or accessed")


if __name__ == "__main__":
    main()
