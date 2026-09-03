#!/usr/bin/env python3
"""Freeze the non-runnable D6-A efficiency-before-training contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_candidate_training_efficiency_protocol_v1.json"
PROTOCOL_ID = "mamba-v16-d6a-r0-r1-candidate-training-efficiency-v1"
FOLDS = ("A", "B", "C", "D")
CANDIDATES = ("R0", "R1")

REPO_PARENTS = {
    "mechanism_protocol": ("docs/mamba_v16_d6a_slot32_mechanism_protocol_v1.json", "2fff4782d429a3ea70607560bee9f464fb7b4eb7cea261376a91eb648a72f284"),
    "complete_result": ("docs/mamba_v16_d6a_gradient_calibration_weighted_zero_step_complete_result_zh.md", "cc3eedba7fd3b9c574e8b796e683dfbbfd69820609d10f3d3fcf98f047019ab6"),
    "R0_implementation": ("utils/mamba_d5a_proposal.py", "6cca9c11f302da3ca202f3e33547c62e4584eeb0fd81f9e96c20f2787e04f070"),
    "R1_implementation": ("utils/mamba_d6a_slot_allocator.py", "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43"),
}

PARENT_FILES = {
    "fourfold_manifest": ("fourfold", "files.sha256", "6a130df708ba006a286388cd38fb8bdd0d3fac7a028d67063357fa18bbd04036"),
    "fourfold_receipt": ("fourfold", "d6_development_protocol_lock_receipt.json", "207ffb0c9c6f5a913ab96de23b3a5f88d17bc301d53e871b181da0a3a48a374e"),
    "audit_manifest": ("audit", "files.sha256", "fa14e67677aa64e1f0e2cdf96aa9d37062471ea3f774ca831d05bea1c95e7e7a"),
    "audit_summary": ("audit", "generation_audit_summary.json", "f8942d6421a524ff648639e464394bd64bfa32781f7d65a6ec8c62aa7485c390"),
    "calibration_manifest": ("calibration", "files.sha256", "8b848b241a7218e26551e52ab3d2922bceb826ab1784b166583edcd6712874eb"),
    "calibration_receipt": ("calibration", "calibration_completion_receipt.json", "b86ad7e35f91e8d03fad6d11d2b4879e294a52f59b9836ee5e73bd300449b100"),
    "calibration_weights": ("calibration", "r1_calibrated_fold_weights.json", "077920aad2e8890ea0028718d9e56f973320f20340505c551708b13dbf224290"),
    "weighted_manifest": ("weighted", "files.sha256", "128e4eb9ad14fdd25474fb86ffef107db8a7b46788756d29d2f35332a41f0e0a"),
    "weighted_receipt": ("weighted", "weighted_zero_step_receipt.json", "33e4a9450475ef00e1df57f6f96fe1d71e89aade81dda952ca9e56edc20821db"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    require(protocol["protocol_id"] == PROTOCOL_ID, "Protocol id drifted")
    require(protocol["status"] == "preregistered_non_runnable_efficiency_before_training", "Status drifted")
    gate = protocol["efficiency_gate"]
    require(gate["warmup_runs"] == 10 and gate["timed_runs"] == 50, "Benchmark repetitions drifted")
    require(gate["R1_to_R0_latency_ratio_maximum"] == 1.15, "Latency threshold drifted")
    require(gate["R1_to_R0_peak_memory_ratio_maximum"] == 1.10, "Memory threshold drifted")
    require(gate["development_cases_accessed"] == 0, "Benchmark accesses development")
    budget = protocol["seed0_training_budget"]
    require(budget["authorized_now"] is False, "Training was authorized")
    require(budget["runs"] == 8 and budget["optimizer_steps_total_maximum"] == 15200, "Training budget drifted")
    require(budget["optimizer_steps_per_run"] == 1900 and budget["epochs_per_run"] == 50, "Per-run budget drifted")
    require(budget["early_stopping"] is False and budget["checkpoint_policy"] == "final_epoch_only", "Checkpoint policy drifted")
    loss = protocol["loss_contract"]["R1"]
    require(loss["cross_fold_mean_weight_forbidden"] is True, "Cross-fold calibration enabled")
    require(loss["scalar_total_loss_for_early_stopping_scheduler_checkpoint_or_candidate_comparison_forbidden"] is True, "Scalar total loss controls training")
    permission = protocol["permission_boundary"]
    require(permission["efficiency_implementation_and_artificial_zero_step_authorized_next"] is True, "Next step drifted")
    for key in ("efficiency_execution_authorized", "runtime_training_configs_authorized", "seed0_training_authorized", "seed1_training_authorized", "proposal_confirmation_authorized", "D6B_authorized", "candidate_selection_authorized", "protected_or_sealed_data_accessed"):
        require(permission[key] is False, f"Forbidden permission enabled: {key}")


def verify_lineage(repo_root: Path, directories: Mapping[str, Path]) -> tuple[dict[str, str], dict[str, str]]:
    repo_hashes = {}
    for key, (relative, expected) in REPO_PARENTS.items():
        path = repo_root / relative
        require(path.is_file(), f"Missing repository parent: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"Repository parent drifted: {relative}")
        repo_hashes[key] = actual
    parent_hashes = {}
    for key, (directory_key, name, expected) in PARENT_FILES.items():
        path = directories[directory_key] / name
        require(path.is_file(), f"Missing frozen parent: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"Frozen parent drifted: {path}")
        parent_hashes[key] = actual
    return repo_hashes, parent_hashes


def read_ids(path: Path, expected: int) -> list[str]:
    values = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(values) == expected and len(set(values)) == expected, f"Bad membership file: {path}")
    return values


def build_outputs(protocol: Mapping[str, Any], fourfold: Path, repo_hashes: Mapping[str, str], parent_hashes: Mapping[str, str]) -> dict[str, bytes]:
    outputs = {
        "candidate_training_efficiency_protocol_v1.json": PROTOCOL.read_bytes(),
        "efficiency_gate_contract.json": canonical_json(protocol["efficiency_gate"]),
        "training_contract.json": canonical_json({"budget": protocol["seed0_training_budget"], "loss": protocol["loss_contract"], "hard_gate": protocol["seed0_hard_gate_after_training"]}),
        "efficiency_benchmark.template.json": canonical_json({"runnable": False, "authorization_required": True, **protocol["efficiency_gate"]}),
    }
    bindings = {}
    for candidate in CANDIDATES:
        for fold in FOLDS:
            train = fourfold / f"fold{fold}_train_case_ids.txt"
            dev = fourfold / f"fold{fold}_dev_case_ids.txt"
            read_ids(train, 300)
            read_ids(dev, 100)
            config = {
                "runnable": False,
                "authorization_required": True,
                "candidate": candidate,
                "fold": fold,
                "seed": 0,
                "train_case_ids": train.name,
                "train_case_ids_sha256": sha256_file(train),
                "dev_case_ids": dev.name,
                "dev_case_ids_sha256": sha256_file(dev),
                "training": protocol["seed0_training_budget"],
                "loss": protocol["loss_contract"][candidate],
            }
            name = f"configs/{candidate}_fold{fold}_seed0.template.json"
            outputs[name] = canonical_json(config)
            bindings[f"{candidate}_fold{fold}"] = {"config": name, "config_sha256": sha256_bytes(outputs[name])}
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "D6A_candidate_training_efficiency_protocol_frozen_non_runnable",
        "protocol_sha256": sha256_file(PROTOCOL),
        "repository_parent_sha256": dict(repo_hashes),
        "frozen_parent_sha256": dict(parent_hashes),
        "bindings": bindings,
        "planned_training_runs": 8,
        "planned_optimizer_steps_maximum": 15200,
        "optimizer_steps": 0,
        "model_updates": 0,
        "development_cases_accessed": 0,
        **protocol["permission_boundary"],
    }
    outputs["protocol_lock_receipt.json"] = canonical_json(receipt)
    outputs["protocol_lock_report_zh.md"] = (
        "# Mamba v1.6 D6-A candidate/training/efficiency protocol lock\n\n"
        "- R0/R1 seed-0：4 folds x 2 candidates；训练预算上限 15,200 optimizer steps。\n"
        "- 训练前必须先通过 artificial full-inference efficiency gate。\n"
        "- 门控：R1/R0 median latency <= 1.15，peak CUDA memory <= 1.10。\n"
        "- R1 只使用同折校准权重；scalar total loss 不控制调度、停止或选择。\n"
        "- 当前仅授权 efficiency implementation + artificial zero-step。\n"
        "- Efficiency execution、training、seed-1、confirmation、D6-B、selection 均未授权。\n"
    ).encode("utf-8")
    outputs["files.sha256"] = "".join(f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())).encode("ascii")
    return outputs


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes() for path in output_dir.rglob("*") if path.is_file()}
        require(existing == dict(outputs), f"Existing protocol lock drifted: {output_dir}")
        print(f"[locked] existing D6-A candidate/training/efficiency lock is byte-identical: {output_dir}")
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
    print(f"[saved] immutable D6-A candidate/training/efficiency protocol: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_root", type=Path, default=ROOT)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--calibration_completion_dir", type=Path, required=True)
    parser.add_argument("--weighted_zero_step_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    directories = {"fourfold": args.fourfold_lock_dir.resolve(), "audit": args.generation_audit_dir.resolve(), "calibration": args.calibration_completion_dir.resolve(), "weighted": args.weighted_zero_step_dir.resolve()}
    repo_hashes, parent_hashes = verify_lineage(args.repo_root.resolve(), directories)
    outputs = build_outputs(protocol, directories["fourfold"], repo_hashes, parent_hashes)
    write_locked(outputs, args.out_dir.resolve())
    print("[done] D6-A candidate/training/efficiency protocol frozen")
    print("[authorized-next] efficiency implementation and artificial zero-step only")
    print("[locked] efficiency_execution=false training=false seed1=false D6B=false confirmation=false")


if __name__ == "__main__":
    main()
