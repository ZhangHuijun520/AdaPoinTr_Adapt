#!/usr/bin/env python3
"""Run or verify the receipt-bound D3 S1 seed-0 preflight smoke test."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402


FOLDS = ("A", "B", "C", "D")
VERSION = "mamba-v13-d3-s1-seed0-smoke-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing non-identical S1 smoke receipt: {path}")
        print(f"[locked] existing S1 smoke receipt is byte-identical: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def verify_receipt(path: Path) -> dict:
    expected, name = Path(str(path) + ".sha256").read_text().split()[:2]
    if Path(name).name != path.name or sha256_file(path) != expected.lower():
        raise RuntimeError("S1 smoke receipt SHA256 mismatch")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if not (
        receipt.get("smoke_version") == VERSION
        and receipt.get("status") == "passed_s1_seed0_zero_step_training_probe"
        and receipt.get("candidate") == "S1"
        and receipt.get("seed") == 0
        and receipt.get("folds") == list(FOLDS)
        and receipt.get("optimizer_steps") == 0
        and receipt.get("S2_authorized") is False
        and receipt.get("holdout_authorized") is False
        and receipt.get("selection_started") is False
    ):
        raise RuntimeError("S1 smoke receipt semantics are invalid")
    for artifact in receipt["artifacts"].values():
        artifact_path = Path(artifact["path"])
        if not artifact_path.is_absolute():
            artifact_path = REPO_ROOT / artifact_path
        if not artifact_path.is_file() or sha256_file(artifact_path) != artifact["sha256"]:
            raise RuntimeError(f"S1 smoke artifact mismatch: {artifact_path}")
    print("[ok] S1 smoke receipt and bound artifacts match")
    print("[authorized] S1 seed-0 folds A-D only")
    print("[locked] S2=false holdout=false selection=false")
    return receipt


def build_dataset(config, split):
    section = getattr(config.dataset, split)
    return build_dataset_from_cfg(section._base_, section.others)


def audit_fold(config_path: Path, fold: str, weight: float):
    config = cfg_from_yaml_file(str(config_path))
    execution = config.d3_execution
    contact = config.model.dense_contact_objective
    if not (
        execution.candidate == "S1"
        and execution.fold == fold
        and int(execution.seed) == 0
        and execution.training_authorized is True
        and execution.S1_training_authorized is True
        and execution.holdout_authorized is False
        and execution.S2_authorized is False
        and execution.selection_started is False
        and contact.enabled is True
        and float(contact.weight) == weight
        and float(contact.threshold_mm) == 2.0
        and float(contact.temperature_mm) == 0.25
        and float(contact.tail_fraction) == 0.1
    ):
        raise RuntimeError(f"Fold {fold} S1 runtime contract is invalid")
    train = build_dataset(config, "train")
    dev = build_dataset(config, "val")
    if len(train) != 300 or len(dev) != 100:
        raise RuntimeError(f"Fold {fold}: expected train/dev 300/100")
    train_skulls = {str(record["skull_id"]) for record in train.records}
    dev_skulls = {str(record["skull_id"]) for record in dev.records}
    if len(train_skulls) != 75 or len(dev_skulls) != 25 or train_skulls & dev_skulls:
        raise RuntimeError(f"Fold {fold}: source-skull isolation failed")
    all_records = list(train.records) + list(dev.records)
    if any(record.get("d3_partition") != "development" for record in all_records):
        raise RuntimeError(f"Fold {fold}: protected partition leaked")
    train_ids = {str(record["case_id"]) for record in train.records}
    dev_ids = {str(record["case_id"]) for record in dev.records}
    if train_ids & dev_ids or len(train_ids | dev_ids) != 400:
        raise RuntimeError(f"Fold {fold}: invalid train/dev case partition")
    for dataset in (train, dev):
        _, case_id, (partial, target) = dataset[0]
        if partial.shape != (8192, 3) or target.shape != (8192, 3):
            raise RuntimeError(f"Fold {fold}: invalid point tensor shape")
        if not torch.isfinite(partial).all() or not torch.isfinite(target).all():
            raise RuntimeError(f"Fold {fold}: nonfinite point tensor")
        if dataset is train:
            mask = dataset.get_gt_rim_masks([str(case_id)])
            scale = dataset.get_normalization_scales([str(case_id)])
            if mask.shape != (1, 8192) or scale.shape != (1,):
                raise RuntimeError(f"Fold {fold}: invalid S1 supervision metadata")
    return {
        "train_cases": 300,
        "dev_cases": 100,
        "train_source_skulls": 75,
        "dev_source_skulls": 25,
        "development_only": True,
        "calibrated_weight": weight,
    }, {
        f"fold{fold}_config": config_path,
        f"fold{fold}_train_ids": Path(train.include_case_ids_file),
        f"fold{fold}_dev_ids": Path(dev.include_case_ids_file),
    }


def training_probe(config_path: Path) -> dict:
    if not torch.cuda.is_available():
        raise RuntimeError("S1 training smoke requires CUDA")
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    config = cfg_from_yaml_file(str(config_path))
    dataset = build_dataset(config, "train")
    loader = DataLoader(dataset, batch_size=2, shuffle=False, num_workers=0)
    _, case_ids, data = next(iter(loader))
    case_ids = [str(value) for value in case_ids]
    partial, target = (value.cuda(non_blocking=False) for value in data)
    scales = dataset.get_normalization_scales(
        case_ids, device=partial.device, dtype=partial.dtype
    )
    masks = dataset.get_gt_rim_masks(case_ids, device=partial.device)
    model = builder.model_builder(config.model).cuda().train()
    model.zero_grad(set_to_none=True)
    output = model(partial)
    sparse, dense = model.get_loss(
        output,
        target,
        epoch=0,
        partial=partial,
        normalization_scale=scales,
        gt_rim_mask=masks,
    )
    total = sparse + dense
    if not torch.isfinite(total):
        raise RuntimeError("S1 smoke loss is nonfinite")
    total.backward()
    gradients = [
        value.grad for value in model.parameters()
        if value.requires_grad and value.grad is not None
    ]
    if not gradients or any(not torch.isfinite(value).all() for value in gradients):
        raise RuntimeError("S1 smoke backward produced missing/nonfinite gradients")
    result = {
        "fold": "A",
        "batch_size": 2,
        "input_shape": list(partial.shape),
        "target_shape": list(target.shape),
        "dense_contact_weight": float(model.dense_contact_weight),
        "loss_finite": True,
        "backward_finite": True,
        "optimizer_steps": 0,
    }
    del output, sparse, dense, total, gradients, model, partial, target
    torch.cuda.empty_cache()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--deployment_receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify_only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.verify_only:
        verify_receipt(output)
        return
    config_dir = args.config_dir.resolve()
    auth_dir = args.authorization_dir.resolve()
    deployment = args.deployment_receipt.resolve()
    subprocess.run([
        sys.executable,
        str(REPO_ROOT / "tools/verify_mamba_v13_d3_s1_seed0_training_authorization.py"),
        "--config_dir", str(config_dir),
        "--authorization_dir", str(auth_dir),
    ], check=True, cwd=REPO_ROOT)
    auth_path = auth_dir / "s1_seed0_training_authorization_receipt.json"
    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    audits = {}
    artifacts = {
        "authorization_receipt": auth_path,
        "deployment_receipt": deployment,
        "smoke_tool": Path(__file__).resolve(),
        "evaluator": REPO_ROOT / "tools/evaluate_skullfix_implant.py",
        "efficiency_tool": REPO_ROOT / "tools/benchmark_mamba_v12_efficiency.py",
        "run_record_tool": REPO_ROOT / "tools/write_mamba_v13_d3_run_record.py",
        "completion_tool": REPO_ROOT / "tools/freeze_mamba_v13_d3_s1_seed0.py",
        "fold_runner": REPO_ROOT / "scripts/run_mamba_v13_d3_s1_seed0_fold.sh",
        "sequence_runner": REPO_ROOT / "scripts/run_mamba_v13_d3_s1_seed0.sh",
        "tmux_launcher": REPO_ROOT / "scripts/launch_mamba_v13_d3_s1_seed0_tmux.sh",
        "preflight_script": REPO_ROOT / "scripts/preflight_mamba_v13_d3_s1_seed0.sh",
    }
    for fold in tqdm(FOLDS, desc="S1 dataset/config smoke", dynamic_ncols=True):
        path = config_dir / f"MambaV13D3_S1_fold{fold}_seed0.yaml"
        audits[fold], fold_artifacts = audit_fold(
            path, fold, float(auth["folds"][fold]["calibrated_weight"])
        )
        artifacts.update(fold_artifacts)
    probe = training_probe(config_dir / "MambaV13D3_S1_foldA_seed0.yaml")
    receipt = {
        "smoke_version": VERSION,
        "status": "passed_s1_seed0_zero_step_training_probe",
        "candidate": "S1",
        "seed": 0,
        "folds": list(FOLDS),
        "fold_audits": audits,
        "training_probe": probe,
        "optimizer_steps": 0,
        "artifacts": {
            name: {"path": portable(path), "sha256": sha256_file(path)}
            for name, path in sorted(artifacts.items())
        },
        "S2_authorized": False,
        "holdout_authorized": False,
        "selection_started": False,
        "next_step": "launch_S1_seed0_folds_A_D_in_tmux",
    }
    payload = canonical_json(receipt)
    write_identical_or_new(output, payload)
    digest = hashlib.sha256(payload).hexdigest()
    write_identical_or_new(
        Path(str(output) + ".sha256"),
        f"{digest}  {output.name}\n".encode("ascii"),
    )
    verify_receipt(output)
    print(f"[saved] S1 smoke receipt: {output}")
    print("[done] dataset/config audit and zero-step CUDA probe passed")


if __name__ == "__main__":
    main()
