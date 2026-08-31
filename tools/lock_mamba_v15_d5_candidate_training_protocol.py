#!/usr/bin/env python3
"""Create the immutable, non-runnable D5 candidate/training protocol lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ID = "mamba-v15-d5-candidate-training-v1"
PROTOCOL_PATH = ROOT / "docs" / "mamba_v15_d5_candidate_training_protocol_v1.json"
D4_RESULT_PATH = ROOT / "docs" / "mamba_v14_d4a_complete_experiment_report_and_next_plan_zh.md"
D5_RESULT_PATH = ROOT / "docs" / "mamba_v15_d5_development400_generation_audit_complete_result_zh.md"
FOLDS = ("A", "B", "C", "D")
CANDIDATES = ("V0", "V1")

EXPECTED = {
    "d4_result": "2f9f061f8649d06b6c45006510a0a2e3a64e2ba1496f03a3e05dc24053bb325d",
    "d5_result": "eca7c9d01a02db12e84f72d831f85e70624a3d605c8c583d57dedf926477a1c4",
    "qc_receipt": "c9985f0c323edb0c0bfac3b02141cda2b371844804b215450f45f17494476e56",
    "qc_manifest": "cb2ec987d4f5e4259464a8083bb4ca3bb632d4212bf8f1cdb140f5b404d534b4",
    "fourfold_protocol": "aa6a1d44bc99cdeec2a5edd3271c07e60daf6f9aae17fb0f1141dfbaaab80eaa",
    "fourfold_receipt": "ed9173f50f70bf835fb5173e03a0eb16b110476b45a2deade9afbafbddbaeafc",
    "fourfold_manifest": "eade1467f7864f041c2c9e2065936f5aa8fbd84e0999d335f1d1b0b247da18fb",
    "audit_summary": "a760c09eacff95841c5443155f11328a6b6a0cc6d646455e8a2d5ef35aad2840",
    "audit_manifest": "6232d046f87ee8548d29580a635c41e3ab316d96920fcc6a9fd8ab27a78e55ed",
    "portable_manifest": "f653a82ac29c98909d987ad0b6bb618841d006ddf3144ba732d4911cff32bf8d",
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


def read_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        != "preregistered_D5A_candidates_budgets_and_progression_locked_training_not_authorized"
    ):
        raise RuntimeError("Unexpected D5 candidate protocol identity")

    lineage = protocol.get("lineage", {})
    if (
        lineage.get("parent_git_commit")
        != "fa2f4223a90728b65f9a0182c6dc7aa6bcc62037"
        or lineage.get("parent_git_tag")
        != "mamba-adapter-v15-d5-development400-generation-audit-v1"
        or lineage.get("d4a_complete_result", {}).get("sha256")
        != EXPECTED["d4_result"]
        or lineage.get("d4a_complete_result", {}).get("ranking_miss_top256") != 2
        or lineage.get("d4a_complete_result", {}).get(
            "selector_dropped_all_pool_positive"
        )
        != 66
        or lineage.get("d4a_complete_result", {}).get("D4_rerun_authorized")
        is not False
        or lineage.get("d5_generation_result", {}).get("sha256")
        != EXPECTED["d5_result"]
        or lineage.get("development100_qc_lock", {}).get("receipt_sha256")
        != EXPECTED["qc_receipt"]
        or lineage.get("development100_qc_lock", {}).get("files_manifest_sha256")
        != EXPECTED["qc_manifest"]
        or lineage.get("development400_fourfold_lock", {}).get("protocol_sha256")
        != EXPECTED["fourfold_protocol"]
        or lineage.get("development400_fourfold_lock", {}).get("receipt_sha256")
        != EXPECTED["fourfold_receipt"]
        or lineage.get("development400_fourfold_lock", {}).get(
            "files_manifest_sha256"
        )
        != EXPECTED["fourfold_manifest"]
        or lineage.get("generation_audit", {}).get("summary_sha256")
        != EXPECTED["audit_summary"]
        or lineage.get("generation_audit", {}).get("files_manifest_sha256")
        != EXPECTED["audit_manifest"]
        or lineage.get("generation_audit", {}).get("portable_manifest_sha256")
        != EXPECTED["portable_manifest"]
    ):
        raise RuntimeError("D5 frozen lineage contract changed")

    data = protocol.get("data_and_folds", {})
    if (
        data.get("development_source_skulls") != 100
        or data.get("development_cases") != 400
        or data.get("folds") != list(FOLDS)
        or data.get("train_sources_per_fold") != 75
        or data.get("dev_sources_per_fold") != 25
        or data.get("train_cases_per_fold") != 300
        or data.get("dev_cases_per_fold") != 100
        or data.get("development_evaluations_per_run") != 1
        or data.get("proposal_confirmation_currently_sealed") is not True
        or data.get("completion_holdout_currently_sealed") is not True
        or data.get("official_test_currently_sealed") is not True
    ):
        raise RuntimeError("D5 source-fourfold data contract changed")

    candidates = protocol.get("candidates", {})
    if set(candidates) != set(CANDIDATES):
        raise RuntimeError("D5 candidate set must be exactly V0 and V1")
    v0 = candidates["V0"]
    v1 = candidates["V1"]
    if (
        v0.get("eligibility_candidate") is not False
        or v0.get("descriptor", {}).get("total_dimensions") != 13
        or v0.get("head_layers") != [13, 128, 64, 1]
        or v0.get("selector", {}).get("selected_count") != 32
        or v0.get("selector", {}).get("mandatory_top_score_count") != 8
        or v0.get("selector", {}).get("ranked_pool_size") != 256
        or v0.get("selector", {}).get("diversified_count") != 24
    ):
        raise RuntimeError("D5 V0 reference contract changed")
    descriptor = v1.get("descriptor", {})
    context = v1.get("context_head", {})
    loss = v1.get("loss", {})
    selector = v1.get("selector", {})
    if (
        v1.get("eligibility_candidate") is not True
        or descriptor.get("total_dimensions") != 27
        or descriptor.get("knn_scales") != [16, 32]
        or context.get("point_encoder_layers") != [27, 64, 64]
        or context.get("global_pool") != ["mean", "max"]
        or context.get("classifier_input_dimensions") != 219
        or context.get("classifier_layers") != [219, 128, 64, 1]
        or loss.get("case_balanced_binary_cross_entropy_weight") != 1.0
        or loss.get("positive_mass_nll_weight") != 1.0
        or loss.get("positive_mass_softmax_temperature") != 1.0
        or loss.get("top32_margin_weight") != 1.0
        or loss.get("top32_margin") != 1.0
        or selector.get("algorithm") != "deterministic_score_top32"
        or selector.get("selected_count") != 32
        or selector.get("score_tie_break") != "candidate_index_ascending"
        or selector.get("fps_or_post_rank_diversification") is not False
    ):
        raise RuntimeError("D5 V1 mechanism contract changed")

    training = protocol.get("common_head_training", {})
    if (
        training.get("epochs") != 50
        or training.get("batch_size_cases") != 8
        or training.get("optimizer") != "AdamW"
        or training.get("learning_rate") != 0.001
        or training.get("dev_evaluation_during_training") is not False
        or training.get("one_shot_dev_evaluation_after_final_epoch") is not True
        or training.get("checkpoint_selection") != "final_epoch_only"
        or training.get("completion_backbone_loaded") is not False
    ):
        raise RuntimeError("D5 head training budget changed")

    seed0 = protocol.get("seed0_budget", {})
    seed1 = protocol.get("seed1_stability_budget", {})
    confirmation = protocol.get("development_all_confirmation_budget", {})
    if (
        seed0.get("candidates") != list(CANDIDATES)
        or seed0.get("folds") != list(FOLDS)
        or seed0.get("seed") != 0
        or seed0.get("maximum_head_trainings") != 8
        or seed1.get("candidate") != "V1"
        or seed1.get("seed") != 1
        or seed1.get("maximum_head_trainings") != 4
        or seed1.get("authorized_only_after_seed0_all_case_gate") is not True
        or seed1.get("V0_seed1_training") is not False
        or confirmation.get("proposal_confirmation_evaluations") != 1
        or confirmation.get("currently_authorized") is not False
    ):
        raise RuntimeError("D5 staged training budget changed")

    gates = protocol.get("hard_gates", {})
    for stage, cases in (("development_seed0", 400), ("development_seed1", 400)):
        gate = gates.get(stage, {})
        if (
            gate.get(f"V1_exact_case_pairing_{cases}") is not True
            or gate.get(f"V1_oracle_positive_exists_{cases}_of_{cases}") is not True
            or gate.get(f"V1_selected32_contains_positive_{cases}_of_{cases}")
            is not True
            or gate.get("all_required_outputs_finite") is not True
            or gate.get("all_four_folds_pass") is not True
            or gate.get("protected_or_sealed_accessed") is not False
        ):
            raise RuntimeError("D5 all-case safety gate changed")
    confirm_gate = gates.get("proposal_confirmation", {})
    if (
        confirm_gate.get("exact_case_pairing_100") is not True
        or confirm_gate.get("oracle_positive_exists_100_of_100") is not True
        or confirm_gate.get("selected32_contains_positive_100_of_100") is not True
        or confirm_gate.get("single_access_only") is not True
    ):
        raise RuntimeError("D5 confirmation safety gate changed")

    d5b = protocol.get("D5B_full_model_boundary", {})
    if (
        d5b.get("candidate_definition_frozen_here") is not False
        or d5b.get("implementation_authorized") is not False
        or d5b.get("training_authorized") is not False
        or d5b.get("selection_authorized") is not False
        or d5b.get("separate_protocol_required_after_D5A_confirmation_pass")
        is not True
    ):
        raise RuntimeError("D5-B boundary changed")

    effect = protocol.get("lock_effect", {})
    if (
        effect.get("non_runnable_templates_generated") != 13
        or effect.get("V0_V1_implementation_and_zero_step_preflight_authorized_next")
        is not True
        or any(
            effect.get(key) is not False
            for key in (
                "D5A_seed0_training_authorized",
                "D5A_seed1_training_authorized",
                "development_all_training_authorized",
                "proposal_confirmation_access_authorized",
                "D5B_implementation_authorized",
                "D5B_training_authorized",
                "D5_candidate_selection_authorized",
                "completion_holdout_access_authorized",
                "official_test_access_authorized",
                "training_started",
                "selection_started",
                "protected_or_sealed_data_accessed",
            )
        )
    ):
        raise RuntimeError("D5 protocol lock would authorize experimental execution")


def verify_lineage(
    protocol: Dict[str, Any], qc_dir: Path, fourfold_dir: Path, audit_dir: Path
) -> Dict[str, str]:
    if sha256_file(D4_RESULT_PATH) != EXPECTED["d4_result"]:
        raise RuntimeError("D4-A frozen result drifted")
    if sha256_file(D5_RESULT_PATH) != EXPECTED["d5_result"]:
        raise RuntimeError("D5 generation result drifted")

    verify_flat_manifest(qc_dir, EXPECTED["qc_manifest"])
    qc_receipt_path = qc_dir / "development100_qc_lock_receipt.json"
    if sha256_file(qc_receipt_path) != EXPECTED["qc_receipt"]:
        raise RuntimeError("D5 development100 receipt drifted")
    qc_receipt = read_json(qc_receipt_path)
    if (
        qc_receipt.get("status") != "development100_qc_locked_complete"
        or qc_receipt.get("counts", {}).get("sources") != 100
        or qc_receipt.get("counts", {}).get("qc_fail") != 0
        or qc_receipt.get("global_duplicate_and_overlap_gates_passed") is not True
        or qc_receipt.get("proposal_confirmation_accessed") is not False
        or qc_receipt.get("completion_holdout_accessed") is not False
    ):
        raise RuntimeError("D5 development100 QC semantics are invalid")

    verify_flat_manifest(fourfold_dir, EXPECTED["fourfold_manifest"])
    fourfold_protocol = fourfold_dir / "d5_development_generation_fourfold_protocol_v1.json"
    fourfold_receipt_path = fourfold_dir / "d5_development_protocol_lock_receipt.json"
    if (
        sha256_file(fourfold_protocol) != EXPECTED["fourfold_protocol"]
        or sha256_file(fourfold_receipt_path) != EXPECTED["fourfold_receipt"]
    ):
        raise RuntimeError("D5 fourfold lock lineage drifted")
    fourfold_receipt = read_json(fourfold_receipt_path)
    if (
        fourfold_receipt.get("status")
        != "d5_development_generation_and_fourfold_protocol_locked"
        or fourfold_receipt.get("counts", {}).get("development_sources") != 100
        or fourfold_receipt.get("counts", {}).get("planned_development_cases")
        != 400
        or fourfold_receipt.get("source_fold_leakage") != 0
        or fourfold_receipt.get("proposal_confirmation_accessed") is not False
        or fourfold_receipt.get("completion_holdout_accessed") is not False
        or fourfold_receipt.get("official_test_accessed") is not False
    ):
        raise RuntimeError("D5 fourfold receipt semantics are invalid")

    verify_flat_manifest(audit_dir, EXPECTED["audit_manifest"])
    summary_path = audit_dir / "generation_audit_summary.json"
    portable_path = audit_dir / "manifest_portable.jsonl"
    if (
        sha256_file(summary_path) != EXPECTED["audit_summary"]
        or sha256_file(portable_path) != EXPECTED["portable_manifest"]
    ):
        raise RuntimeError("D5 generation audit lineage drifted")
    summary = read_json(summary_path)
    if (
        summary.get("status")
        != "generation_integrity_passed_model_training_selection_and_sealed_still_locked"
        or summary.get("source_skulls") != 100
        or summary.get("derived_cases") != 400
        or summary.get("fold_case_counts")
        != {"A": 100, "B": 100, "C": 100, "D": 100}
        or summary.get("all_geometry_gates_verified") is not True
        or summary.get("manifest_cases_bijective") is not True
        or summary.get("D5A_model_implementation_authorized") is not False
        or summary.get("D5A_training_authorized") is not False
        or summary.get("D5B_training_authorized") is not False
        or summary.get("D5_candidate_selection_authorized") is not False
        or summary.get("proposal_confirmation_accessed") is not False
        or summary.get("completion_holdout_accessed") is not False
        or summary.get("official_test_accessed") is not False
    ):
        raise RuntimeError("D5 generation audit semantics are invalid")

    return {
        "d4_result": sha256_file(D4_RESULT_PATH),
        "d5_result": sha256_file(D5_RESULT_PATH),
        "qc_receipt": sha256_file(qc_receipt_path),
        "qc_manifest": sha256_file(qc_dir / "files.sha256"),
        "fourfold_protocol": sha256_file(fourfold_protocol),
        "fourfold_receipt": sha256_file(fourfold_receipt_path),
        "fourfold_manifest": sha256_file(fourfold_dir / "files.sha256"),
        "audit_summary": sha256_file(summary_path),
        "audit_manifest": sha256_file(audit_dir / "files.sha256"),
        "portable_manifest": sha256_file(portable_path),
    }


def data_binding(fold: str | None, split: str) -> Dict[str, Any]:
    binding: Dict[str, Any] = {
        "dataset_root": "data/MUG500plusD5Development400_v1",
        "manifest": "data/MUG500plusD5Development400_v1/manifest_portable.jsonl",
        "input_key": "partial",
        "label_key": "reference_rim_mask",
        "candidate_count": 8192,
        "sealed_data_allowed": False,
    }
    if fold is None:
        binding["case_ids"] = "all_400_frozen_development_cases"
    else:
        binding["case_ids"] = (
            "data/MUG500plusD5Development100_v1/data_locks/"
            "mug500plus_d5_development400_fourfold_protocol_lock_v1/"
            f"fold{fold}_{split}_case_ids.txt"
        )
    return binding


def template_config(
    protocol: Dict[str, Any], protocol_sha: str, candidate: str, fold: str | None, seed: int
) -> Dict[str, Any]:
    training = protocol["common_head_training"]
    candidate_spec = protocol["candidates"][candidate]
    stage = "development_all_confirmation_preparation" if fold is None else "out_of_fold"
    return {
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": protocol_sha,
        "status": "locked_non_runnable_template",
        "candidate": candidate,
        "fold": fold,
        "stage": stage,
        "seed": seed,
        "train_data": data_binding(fold, "train") if fold else data_binding(None, "train"),
        "dev_data": None if fold is None else data_binding(fold, "dev"),
        "candidate_contract": candidate_spec,
        "training": training,
        "authorization": {
            "implementation_authorized": False,
            "training_authorized": False,
            "dev_evaluation_authorized": False,
            "proposal_confirmation_access_authorized": False,
            "selection_authorized": False,
            "protected_or_sealed_data_accessed": False,
        },
    }


def render_report(receipt: Mapping[str, Any]) -> bytes:
    return (
        "# Mamba v1.5 D5 候选与训练协议锁报告\n\n"
        "> 本锁只生成不可运行模板；未实现模型、未训练、未评估、未选择、未访问 sealed 数据。\n\n"
        "- V0：D4-A 13D + top8/FPS24 参考机制，仅 seed 0。\n"
        "- V1：27D multiscale partial-only context + global pooling + direct top32。\n"
        "- V1 loss：case-balanced BCE + positive-mass NLL + top32 margin，固定等权。\n"
        "- Seed 0：V0/V1 x A-D，最多 8 个 head；V1 必须 400/400。\n"
        "- Seed 1：仅 V1 x A-D，只有 seed 0 通过后才能授权，仍须 400/400。\n"
        "- Proposal confirmation：一次性 100/100，当前 sealed。\n"
        "- D5-B：本协议不定义、不实现、不训练。\n"
        f"- D5-A training authorized：`{receipt['D5A_seed0_training_authorized']}`。\n"
        f"- sealed access authorized：`{receipt['proposal_confirmation_access_authorized']}`。\n"
        "- 下一步：实现 V0/V1 并执行 zero-step preflight；训练需单独授权。\n"
    ).encode("utf-8")


def render_files(
    protocol: Dict[str, Any],
    protocol_bytes: bytes,
    lineage_hashes: Dict[str, str],
    implementation_paths: Dict[str, Path],
) -> Dict[str, bytes]:
    protocol_sha = sha256_bytes(protocol_bytes)
    files: Dict[str, bytes] = {"candidate_training_protocol_v1.json": protocol_bytes}
    template_hashes: Dict[str, str] = {}
    for candidate in CANDIDATES:
        for fold in FOLDS:
            name = f"configs/MambaV15D5_{candidate}_fold{fold}_seed0.template.json"
            payload = canonical_json(
                template_config(protocol, protocol_sha, candidate, fold, 0)
            )
            files[name] = payload
            template_hashes[name] = sha256_bytes(payload)
    for fold in FOLDS:
        name = f"configs/MambaV15D5_V1_fold{fold}_seed1.template.json"
        payload = canonical_json(template_config(protocol, protocol_sha, "V1", fold, 1))
        files[name] = payload
        template_hashes[name] = sha256_bytes(payload)
    all_name = "configs/MambaV15D5_V1_development_all_seed0.template.json"
    all_payload = canonical_json(
        template_config(protocol, protocol_sha, "V1", None, 0)
    )
    files[all_name] = all_payload
    template_hashes[all_name] = sha256_bytes(all_payload)

    files["d5a_candidate_contracts.json"] = canonical_json(
        {
            "protocol_id": PROTOCOL_ID,
            "protocol_sha256": protocol_sha,
            "candidate_coordinates": protocol["candidate_coordinates"],
            "candidates": protocol["candidates"],
            "common_head_training": protocol["common_head_training"],
            "hard_gates": protocol["hard_gates"],
            "template_sha256": template_hashes,
        }
    )
    files["d5a_progression_receipt_template.json"] = canonical_json(
        {
            "protocol_id": PROTOCOL_ID,
            "status": "unconsumed_progression_template",
            "seed0_V0": None,
            "seed0_V1": None,
            "seed1_V1": None,
            "proposal_confirmation": None,
            "D5A_seed1_training_authorized": False,
            "development_all_training_authorized": False,
            "proposal_confirmation_access_authorized": False,
            "D5B_protocol_authorized": False,
            "selection_started": False,
            "protected_or_sealed_data_accessed": False,
            "rule_revision_after_results": False,
        }
    )
    implementation_hashes = {
        name: sha256_file(path) for name, path in sorted(implementation_paths.items())
    }
    receipt: Dict[str, Any] = {
        "protocol_id": PROTOCOL_ID,
        "status": "D5_candidate_training_protocol_locked_non_runnable",
        "protocol_sha256": protocol_sha,
        "lineage_sha256": lineage_hashes,
        "lock_implementation_sha256": implementation_hashes,
        "candidate_count": 2,
        "fold_count": 4,
        "non_runnable_template_count": 13,
        "V0_V1_implementation_and_zero_step_preflight_authorized_next": True,
        "D5A_seed0_training_authorized": False,
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
        "next_step": "implement_V0_V1_and_freeze_zero_step_preflight",
    }
    files["protocol_lock_receipt.json"] = canonical_json(receipt)
    files["protocol_lock_report_zh.md"] = render_report(receipt)
    files["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())
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
            raise RuntimeError("Refusing to overwrite a non-identical D5 candidate lock")
        print(f"[locked] existing D5 candidate lock is byte-identical: {output_dir}")
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
    print(f"[saved] immutable D5 candidate/training protocol: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development100_qc_lock_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL_PATH)
    parser.add_argument("--test_script", type=Path, required=True)
    args = parser.parse_args()

    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    validate_protocol(protocol)
    lineage = verify_lineage(
        protocol,
        args.development100_qc_lock_dir.resolve(),
        args.fourfold_lock_dir.resolve(),
        args.generation_audit_dir.resolve(),
    )
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
    print("[done] D5 V0/V1 definitions, budgets, gates, and progression frozen")
    print("[authorized-next] V0/V1 implementation and zero-step preflight only")
    print("[locked] training=false selection=false sealed=false D5B=false")


if __name__ == "__main__":
    main()
