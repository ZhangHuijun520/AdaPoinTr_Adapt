#!/usr/bin/env python3
"""Create the immutable, non-runnable D4 candidate and training protocol lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ID = "mamba-v14-d4-candidate-training-v1"
PROTOCOL_PATH = ROOT / "docs" / "mamba_v14_d4_candidate_training_protocol_v1.json"
SCIENTIFIC_PATH = ROOT / "docs" / "mamba_v14_d4_contact_support_representation_protocol_v1.json"
PD3_PATH = ROOT / "docs" / "mamba_v14_pd3_s2_failure_decomposition_result_zh.md"
FOLDS = ("A", "B", "C", "D")
CANDIDATES = ("T0", "T1", "T2")

EXPECTED = {
    "scientific_protocol": "7dff6bd80f62aef273960e1d6546f67c97745ae3e3fa64c6e5ba26d2054ce4e3",
    "pd3_result": "629344497e16dee56991d9ed45e31faa1a3f0e3da623287fb3fc4f075602b356",
    "fourfold_protocol": "505f7e510447cdb7b3be8016fafcf8126f9f6e093536d4aba1587d672183b324",
    "fourfold_receipt": "84c92aacc7a3bf7bac1d84f5ff1eb1b63a241705f07e930b99ded7ae7a1a5885",
    "fourfold_manifest": "3b431cfddc3c9575f9269e1535bd3c4ba66c1220b64a77b14256fea152aa1b7b",
    "audit_summary": "829a74d2eccd6bedd61bd2c1041e6120394c00ee6f645922beadeb61a45a565f",
    "audit_manifest": "0b51735e0af8ef14fddca8e378155b0d9b60ff818fe163813287f7935c731929",
    "portable_manifest": "709759f5a32fe8862668b5a457f9f7be60489fcabb63fa83093fd6627278e781",
}


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


def verify_flat_manifest(directory: Path, expected_hash: str) -> None:
    manifest = directory / "files.sha256"
    if not manifest.is_file() or sha256_file(manifest) != expected_hash:
        raise RuntimeError(f"Frozen files.sha256 drifted: {manifest}")
    for raw in manifest.read_text(encoding="ascii").splitlines():
        if not raw.strip():
            continue
        expected, name = raw.split(maxsplit=1)
        name = name.lstrip("*").strip()
        if Path(name).name != name:
            raise RuntimeError(f"Unsafe nested manifest entry: {name}")
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen hash-chain failure: {path}")


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if (
        protocol.get("protocol_id") != PROTOCOL_ID
        or protocol.get("status")
        != "preregistered_candidates_and_budgets_locked_training_not_authorized"
    ):
        raise RuntimeError("Unexpected D4 candidate protocol identity")

    lineage = protocol.get("lineage", {})
    scientific = lineage.get("scientific_protocol", {})
    pd3 = lineage.get("pd3_result", {})
    fourfold = lineage.get("fourfold_lock", {})
    audit = lineage.get("generation_audit", {})
    if (
        lineage.get("parent_git_commit")
        != "7d30d8519474fac4566e92e38599ce006c7e4180"
        or lineage.get("parent_git_tag")
        != "mamba-adapter-v14-d4-m2-generation-audit-v1"
        or scientific.get("sha256") != EXPECTED["scientific_protocol"]
        or pd3.get("sha256") != EXPECTED["pd3_result"]
        or pd3.get("ranking_miss_top96") != 2
        or pd3.get("selector_dropped_all_positive") != 6
        or pd3.get("candidate_or_threshold_selection_authorized") is not False
        or fourfold.get("protocol_sha256") != EXPECTED["fourfold_protocol"]
        or fourfold.get("receipt_sha256") != EXPECTED["fourfold_receipt"]
        or fourfold.get("files_manifest_sha256") != EXPECTED["fourfold_manifest"]
        or audit.get("summary_sha256") != EXPECTED["audit_summary"]
        or audit.get("files_manifest_sha256") != EXPECTED["audit_manifest"]
        or audit.get("portable_manifest_sha256") != EXPECTED["portable_manifest"]
        or audit.get("required_status")
        != "generation_integrity_passed_training_and_selection_still_locked"
    ):
        raise RuntimeError("D4 frozen lineage contract changed")

    data = protocol.get("data_and_folds", {})
    if (
        data.get("source_skulls") != 100
        or data.get("cases") != 400
        or data.get("folds") != list(FOLDS)
        or data.get("train_sources_per_fold") != 75
        or data.get("dev_sources_per_fold") != 25
        or data.get("train_cases_per_fold") != 300
        or data.get("dev_cases_per_fold") != 100
        or data.get("development_evaluations_per_run") != 1
        or data.get("holdout_or_protected_data_allowed") is not False
    ):
        raise RuntimeError("D4 source-fourfold execution contract changed")

    feasibility = protocol.get("d4a_feasibility", {})
    descriptor = feasibility.get("descriptor", {})
    selector = feasibility.get("selector", {})
    head_training = feasibility.get("training", {})
    gate = feasibility.get("hard_gate", {})
    if (
        feasibility.get("candidate_count") != 8192
        or descriptor.get("knn") != 16
        or descriptor.get("total_dimensions") != 13
        or feasibility.get("proposal_head", {}).get("layers") != [13, 128, 64, 1]
        or selector.get("rim_query_budget") != 32
        or selector.get("mandatory_top_score_count") != 8
        or selector.get("ranked_pool_size") != 256
        or selector.get("diversified_count") != 24
        or selector.get("candidate_count_or_selector_scan_allowed") is not False
        or head_training.get("epochs") != 50
        or head_training.get("batch_size") != 8
        or head_training.get("seed") != 0
        or head_training.get("dev_evaluation_during_training") is not False
        or head_training.get("one_shot_dev_evaluation_after_final_epoch") is not True
        or gate.get("selected_32_contains_positive_for_all_400_out_of_fold_cases") is not True
        or gate.get("all_folds_must_pass") is not True
    ):
        raise RuntimeError("D4-A feasibility contract changed")

    candidates = protocol.get("candidates", {})
    if set(candidates) != set(CANDIDATES):
        raise RuntimeError("D4 candidate set must be exactly T0/T1/T2")
    if (
        candidates["T0"].get("global_learned_queries") != 256
        or candidates["T1"].get("global_learned_queries") != 224
        or candidates["T1"].get("rim_queries") != 32
        or candidates["T1"].get("proposal_head")
        != "same_fold_frozen_D4A_final_head"
        or candidates["T2"].get("support_offset")
        != "0.02_times_tanh_raw_offset_in_normalized_space"
        or candidates["T2"].get("support_points") != 32
        or candidates["T2"].get("ordinary_generated_points") != 8160
        or candidates["T2"].get("total_output_points") != 8192
    ):
        raise RuntimeError("D4 candidate mechanism contract changed")

    budget = protocol.get("round_a_training_budget", {})
    if (
        budget.get("maximum_full_trainings_after_D4A_pass") != 12
        or budget.get("epochs_per_training") != 100
        or budget.get("total_batch_size") != 8
        or budget.get("seed") != 0
        or budget.get("dev_evaluation_during_training") is not False
        or budget.get("dev_evaluation_count_per_candidate_fold") != 1
        or budget.get("best_checkpoint_selection_from_dev_forbidden") is not True
        or budget.get("S1_or_other_contact_loss_allowed") is not False
    ):
        raise RuntimeError("D4 Round-A training budget changed")

    gates = protocol.get("round_a_hard_gates", {})
    expected_order = [
        "complete_exact_case_pairing",
        "all_required_metrics_finite",
        "dense_zero_contact_at_2mm_equals_zero",
        "T2_generated_only_zero_contact_at_2mm_equals_zero",
        "disaster_count_not_above_same_seed_same_fold_T0",
        "induced_disasters_not_above_rescued_disasters",
        "contact_relevance_event_vectors_componentwise_not_above_T0",
        "final_noninferiority",
        "efficiency",
    ]
    relevance = gates.get("contact_relevance", {})
    if (
        gates.get("order") != expected_order
        or relevance.get("thresholds_mm") != [2.0, 5.0, 10.0, 20.0, 50.0]
        or relevance.get("nonfinite_counts_as_event") is not True
        or relevance.get("finite_only_p95_as_primary_gate_forbidden") is not True
        or gates.get("bootstrap_unit") != "source_skull"
        or gates.get("bootstrap_samples") != 2000
    ):
        raise RuntimeError("D4 safety gates changed")

    effect = protocol.get("lock_effect", {})
    if (
        effect.get("non_runnable_templates_generated") != 12
        or effect.get("D4_implementation_and_zero_step_preflight_authorized_next") is not True
        or any(
            effect.get(key) is not False
            for key in (
                "D4A_execution_authorized",
                "D4_training_authorized",
                "D4_candidate_selection_authorized",
                "round_b_authorized",
                "holdout_access_authorized",
                "protected_data_accessed",
                "training_started",
                "selection_started",
            )
        )
    ):
        raise RuntimeError("D4 protocol lock would authorize experimental execution")


def verify_lineage(
    protocol: Dict[str, Any], fourfold_dir: Path, audit_dir: Path
) -> Dict[str, str]:
    if sha256_file(SCIENTIFIC_PATH) != EXPECTED["scientific_protocol"]:
        raise RuntimeError("D4 scientific protocol drifted")
    if sha256_file(PD3_PATH) != EXPECTED["pd3_result"]:
        raise RuntimeError("P-D3 frozen result drifted")

    verify_flat_manifest(fourfold_dir, EXPECTED["fourfold_manifest"])
    fourfold_protocol = fourfold_dir / "d4_m2_fourfold_protocol_v1.json"
    fourfold_receipt = fourfold_dir / "d4_m2_protocol_lock_receipt.json"
    if (
        sha256_file(fourfold_protocol) != EXPECTED["fourfold_protocol"]
        or sha256_file(fourfold_receipt) != EXPECTED["fourfold_receipt"]
    ):
        raise RuntimeError("D4 fourfold lock lineage drifted")
    receipt = json.loads(fourfold_receipt.read_text(encoding="utf-8"))
    if (
        receipt.get("status") != "d4_m2_generation_and_fourfold_protocol_locked"
        or receipt.get("counts", {}).get("sources") != 100
        or receipt.get("counts", {}).get("planned_cases") != 400
        or receipt.get("source_fold_leakage") != 0
        or receipt.get("D4_training_authorized") is not False
        or receipt.get("protected_data_accessed") is not False
    ):
        raise RuntimeError("D4 fourfold receipt semantics are invalid")

    verify_flat_manifest(audit_dir, EXPECTED["audit_manifest"])
    summary_path = audit_dir / "generation_audit_summary.json"
    portable_path = audit_dir / "manifest_portable.jsonl"
    if (
        sha256_file(summary_path) != EXPECTED["audit_summary"]
        or sha256_file(portable_path) != EXPECTED["portable_manifest"]
    ):
        raise RuntimeError("D4 generation audit lineage drifted")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (
        summary.get("status")
        != "generation_integrity_passed_training_and_selection_still_locked"
        or summary.get("source_skulls") != 100
        or summary.get("derived_cases") != 400
        or summary.get("fold_case_counts")
        != {"A": 100, "B": 100, "C": 100, "D": 100}
        or summary.get("all_geometry_gates_verified") is not True
        or summary.get("manifest_cases_bijective") is not True
        or summary.get("D4_training_authorized") is not False
        or summary.get("D4_candidate_selection_authorized") is not False
        or summary.get("protected_data_used") is not False
    ):
        raise RuntimeError("D4 generation audit semantics are invalid")

    return {
        "scientific_protocol": sha256_file(SCIENTIFIC_PATH),
        "pd3_result": sha256_file(PD3_PATH),
        "fourfold_protocol": sha256_file(fourfold_protocol),
        "fourfold_receipt": sha256_file(fourfold_receipt),
        "fourfold_manifest": sha256_file(fourfold_dir / "files.sha256"),
        "generation_audit_summary": sha256_file(summary_path),
        "generation_audit_manifest": sha256_file(audit_dir / "files.sha256"),
        "portable_manifest": sha256_file(portable_path),
    }


def dataset_section(fold: str, candidate: str) -> Dict[str, Any]:
    common = {
        "DATA_ROOT": "data/MUG500plusD4M2_v1",
        "ASSET_ROOT": "data/MUG500plusD4M2_v1",
        "MANIFEST": "data/MUG500plusD4M2_v1/manifest_portable.jsonl",
        "input_key": "partial",
        "target_key": "implant",
        "N_PARTIAL": 8192,
        "N_POINTS": 8192,
    }
    train = dict(common)
    train.update(
        subset="train",
        include_case_ids_file=(
            f"data/MUG500plusD4M2FourfoldV1/fold{fold}_train_case_ids.txt"
        ),
    )
    dev = dict(common)
    dev.update(
        subset="val",
        include_case_ids_file=(
            f"data/MUG500plusD4M2FourfoldV1/fold{fold}_dev_case_ids.txt"
        ),
    )
    if candidate in {"T1", "T2"}:
        train["FROZEN_D4A_HEAD_REQUIRED"] = True
        train["GT_RIM_KEY"] = None
    return {
        "train": {"_base_": "cfgs/dataset_configs/MUG500plusM2.yaml", "others": train},
        "val": {"_base_": "cfgs/dataset_configs/MUG500plusM2.yaml", "others": dev},
    }


def model_section(protocol: Dict[str, Any], candidate: str, fold: str) -> Dict[str, Any]:
    common = protocol["common_model"]
    selected = protocol["candidates"][candidate]
    enabled = candidate in {"T1", "T2"}
    return {
        "NAME": "AdaPoinTr",
        "num_query": common["num_queries"],
        "num_points": common["output_points"],
        "center_num": [512, 256],
        "global_feature_dim": 1024,
        "encoder_type": "graph",
        "decoder_type": "fc",
        "query_selection": common["query_selection"],
        "denoise_weight": common["denoise_weight"],
        "fine_coverage_weight": 1.0,
        "fine_local_weight": 0.0,
        "mamba_adapter": {
            "enabled": True,
            "adapter_type": "mamba_ssm",
            "depth": common["mamba_depth"],
            "d_state": common["mamba_d_state"],
            "d_conv": common["mamba_d_conv"],
            "expand": common["mamba_expand"],
            "use_fast_path": True,
            "drop_path": common["mamba_drop_path"],
            "alpha_init": common["alpha_init"],
            "alpha_warmup_epochs": common["alpha_warmup_epochs"],
            "alpha_warmup_start": 0.0,
            "alpha_warmup_end": 1.0,
            "order": common["mamba_order"],
        },
        "dense_contact_objective": {"enabled": False, "weight": 0.0},
        "high_resolution_rim_proposal": {
            "enabled": enabled,
            "descriptor_dimensions": 13,
            "knn": 16,
            "head_layers": [13, 128, 64, 1],
            "head_checkpoint": (
                f"pending_D4A_receipt/fold{fold}_final_head.pth" if enabled else None
            ),
            "head_trainable": False,
            "rim_queries": selected.get("rim_queries", 0),
            "mandatory_top_score_count": 8,
            "ranked_pool_size": 256,
            "diversified_count": 24,
            "selector": "top8_then_conditioned_deterministic_fps24",
            "type_embedding_enabled": enabled,
        },
        "contact_support_preservation": {
            "enabled": candidate == "T2",
            "normalized_offset_radius": 0.02,
            "support_points": 32 if candidate == "T2" else 0,
            "ordinary_generated_points": 8160 if candidate == "T2" else 8192,
            "replacement_index_per_rim_group": 0 if candidate == "T2" else None,
        },
    }


def template_config(
    protocol: Dict[str, Any], protocol_sha: str, candidate: str, fold: str
) -> Dict[str, Any]:
    budget = protocol["round_a_training_budget"]
    return {
        "optimizer": {
            "type": budget["optimizer"],
            "kwargs": {
                "lr": budget["learning_rate"],
                "weight_decay": budget["weight_decay"],
            },
        },
        "scheduler": {"type": "LambdaLR", "kwargs": budget["scheduler"]},
        "bnmscheduler": {"type": "Lambda", "kwargs": budget["bn_scheduler"]},
        "dataset": dataset_section(fold, candidate),
        "model": model_section(protocol, candidate, fold),
        "d4_execution": {
            "protocol_id": PROTOCOL_ID,
            "protocol_sha256": protocol_sha,
            "status": "locked_non_runnable_template",
            "candidate": candidate,
            "fold": fold,
            "round": "A",
            "seed": budget["seed"],
            "D4A_receipt": "not_applicable" if candidate == "T0" else "pending",
            "training_authorized": False,
            "dev_evaluation_authorized": False,
            "selection_authorized": False,
            "protected_data_accessed": False,
        },
        "total_bs": budget["total_batch_size"],
        "step_per_update": budget["step_per_update"],
        "max_epoch": budget["epochs_per_training"],
        "consider_metric": "CDL2",
        "save_freq": 10,
        "save_best_checkpoint": False,
        "save_final_epoch_checkpoints": True,
    }


def render_report(receipt: Dict[str, Any]) -> bytes:
    return (
        "# Mamba v1.4 D4 候选与训练协议锁报告\n\n"
        "> 本锁只生成不可运行模板；未训练、未评估、未选择、未访问保护数据。\n\n"
        "- D4-A：8192 candidates，13D descriptor，top8 + conditioned FPS24。\n"
        "- D4-A：4 folds，50 epochs，source-skull out-of-fold，400/400 hard gate。\n"
        "- Round-A：T0/T1/T2 x 4 folds x seed0，最多 12 次 full training。\n"
        "- Full run：100 epochs、batch 8、final epoch + train-fold BNCal。\n"
        "- T2：32 support + 8160 generated = 8192，并执行 generated-only gate。\n"
        "- S1/contact loss：Round-A 禁止。\n"
        f"- training authorized：`{receipt['D4_training_authorized']}`。\n"
        f"- selection authorized：`{receipt['D4_candidate_selection_authorized']}`。\n"
        "- 下一步：实现所有路径并执行零步 preflight；另立 D4-A execution receipt。\n"
    ).encode("utf-8")


def render_files(
    protocol: Dict[str, Any],
    protocol_bytes: bytes,
    lineage_hashes: Dict[str, str],
    implementation_paths: Dict[str, Path],
) -> Dict[str, bytes]:
    protocol_sha = sha256_bytes(protocol_bytes)
    files: Dict[str, bytes] = {"candidate_training_protocol_v1.json": protocol_bytes}
    config_hashes: Dict[str, str] = {}
    for candidate in CANDIDATES:
        for fold in FOLDS:
            name = f"configs/MambaV14D4_{candidate}_fold{fold}_seed0.template.json"
            payload = canonical_json(
                template_config(protocol, protocol_sha, candidate, fold)
            )
            files[name] = payload
            config_hashes[name] = sha256_bytes(payload)

    files["d4a_feasibility_contract.json"] = canonical_json(
        {
            "protocol_id": PROTOCOL_ID,
            "protocol_sha256": protocol_sha,
            "d4a_feasibility": protocol["d4a_feasibility"],
            "D4A_execution_authorized": False,
            "T0_T1_T2_round_A_authorized": False,
            "protected_data_accessed": False,
        }
    )
    files["round_a_candidate_contracts.json"] = canonical_json(
        {
            "protocol_id": PROTOCOL_ID,
            "protocol_sha256": protocol_sha,
            "common_model": protocol["common_model"],
            "candidates": protocol["candidates"],
            "training_budget": protocol["round_a_training_budget"],
            "hard_gates": protocol["round_a_hard_gates"],
            "config_sha256": config_hashes,
        }
    )
    files["round_a_selection_receipt_template.json"] = canonical_json(
        {
            "protocol_id": PROTOCOL_ID,
            "status": "unconsumed_template",
            "round": "A",
            "seed": 0,
            "candidate_results": {candidate: None for candidate in CANDIDATES},
            "gate_results": {candidate: None for candidate in CANDIDATES},
            "eligible_experimental_candidates": None,
            "selection_decision": None,
            "round_b_authorized": False,
            "rule_revision_after_results": False,
            "holdout_accessed": False,
            "confirmation20_accessed": False,
            "official_test_accessed": False,
        }
    )
    implementation_hashes = {
        name: sha256_file(path) for name, path in sorted(implementation_paths.items())
    }
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "candidate_training_protocol_locked_non_runnable",
        "protocol_sha256": protocol_sha,
        "lineage_sha256": lineage_hashes,
        "lock_implementation_sha256": implementation_hashes,
        "candidate_count": 3,
        "fold_count": 4,
        "non_runnable_template_count": 12,
        "D4A_execution_authorized": False,
        "D4_training_authorized": False,
        "D4_candidate_selection_authorized": False,
        "round_b_authorized": False,
        "holdout_authorized": False,
        "protected_data_accessed": False,
        "training_started": False,
        "selection_started": False,
        "implementation_and_zero_step_preflight_authorized_next": True,
        "next_step": "implement_D4A_T0_T1_T2_and_freeze_zero_step_preflight",
    }
    files["protocol_lock_receipt.json"] = canonical_json(receipt)
    files["protocol_lock_report_zh.md"] = render_report(receipt)
    files["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    return files


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical D4 candidate lock")
        print(f"[locked] existing D4 candidate lock is byte-identical: {output_dir}")
        return
    working = output_dir.with_name(f".{output_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Working lock directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in files.items():
        path = working / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    os.replace(working, output_dir)
    print(f"[saved] immutable D4 candidate/training protocol: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL_PATH)
    parser.add_argument("--test_script", type=Path, required=True)
    args = parser.parse_args()

    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    validate_protocol(protocol)
    lineage = verify_lineage(protocol, args.fourfold_lock_dir, args.generation_audit_dir)
    files = render_files(
        protocol,
        protocol_bytes,
        lineage,
        {
            "protocol_locker": Path(__file__).resolve(),
            "tests": args.test_script.resolve(),
        },
    )
    write_locked(files, args.output_dir.resolve())
    print("[done] D4-A and T0/T1/T2 definitions, budgets, folds, and gates frozen")
    print("[authorized-next] implementation and zero-step preflight only")
    print("[locked] D4A=false training=false selection=false protected=false")


if __name__ == "__main__":
    main()
