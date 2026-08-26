#!/usr/bin/env python3
"""Run or verify the receipt-bound D3 S0 seed-0 preflight smoke test."""

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
VERSION = "mamba-v13-d3-s0-seed0-smoke-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def portable_path(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite non-identical smoke receipt: {path}")
        print(f"[locked] existing smoke receipt is byte-identical: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def verify_receipt(path: Path) -> dict:
    sidecar = Path(str(path) + ".sha256")
    expected, name = sidecar.read_text(encoding="ascii").split()[:2]
    if Path(name).name != path.name or sha256_file(path) != expected.lower():
        raise RuntimeError("S0 smoke receipt SHA256 mismatch")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if (
        receipt.get("smoke_version") != VERSION
        or receipt.get("status") != "passed_s0_seed0_training_probe"
        or receipt.get("candidate") != "S0"
        or receipt.get("seed") != 0
        or receipt.get("folds") != list(FOLDS)
        or receipt.get("S1_authorized") is not False
        or receipt.get("S2_authorized") is not False
        or receipt.get("holdout_authorized") is not False
        or receipt.get("locked_holdout_accessed") is not False
        or receipt.get("selection_started") is not False
    ):
        raise RuntimeError("S0 smoke receipt has invalid frozen semantics")
    for artifact in receipt["artifacts"].values():
        artifact_path = Path(artifact["path"])
        if not artifact_path.is_absolute():
            artifact_path = REPO_ROOT / artifact_path
        if not artifact_path.is_file() or sha256_file(artifact_path) != artifact["sha256"]:
            raise RuntimeError(f"S0 smoke artifact mismatch: {artifact_path}")
    print("[ok] S0 smoke receipt and all bound artifacts match")
    print("[authorized] S0 seed-0 folds A-D only")
    print("[locked] S1=false S2=false holdout=false selection_started=false")
    return receipt


def build_dataset(config, split):
    dataset_cfg = getattr(config.dataset, split)
    return build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)


def selected_case_ids(dataset):
    return {str(record["case_id"]) for record in dataset.records}


def audit_fold(config_path: Path, fold: str) -> tuple[dict, dict[str, Path]]:
    config = cfg_from_yaml_file(str(config_path))
    execution = config.d3_execution
    if not (
        execution.candidate == "S0"
        and execution.fold == fold
        and int(execution.seed) == 0
        and execution.training_authorized is True
        and execution.holdout_authorized is False
        and execution.S1_authorized is False
        and execution.S2_authorized is False
        and execution.selection_started is False
    ):
        raise RuntimeError(f"Fold {fold} runtime authorization is invalid")

    train = build_dataset(config, "train")
    dev = build_dataset(config, "val")
    if len(train) != 300 or len(dev) != 100:
        raise RuntimeError(
            f"Fold {fold}: expected train/dev 300/100 cases, got {len(train)}/{len(dev)}"
        )
    train_skulls = {str(record["skull_id"]) for record in train.records}
    dev_skulls = {str(record["skull_id"]) for record in dev.records}
    if len(train_skulls) != 75 or len(dev_skulls) != 25 or train_skulls & dev_skulls:
        raise RuntimeError(f"Fold {fold}: source-skull isolation failed")
    if len(train_skulls | dev_skulls) != 100:
        raise RuntimeError(f"Fold {fold}: development source-skull union is not 100")
    all_records = list(train.records) + list(dev.records)
    if any(record.get("d3_partition") != "development" for record in all_records):
        raise RuntimeError(f"Fold {fold}: protected partition leaked into selected datasets")

    train_ids = selected_case_ids(train)
    dev_ids = selected_case_ids(dev)
    if train_ids & dev_ids or len(train_ids | dev_ids) != 400:
        raise RuntimeError(f"Fold {fold}: case-level train/dev partition is invalid")

    for dataset, label in ((train, "train"), (dev, "dev")):
        for index in (0, len(dataset) - 1):
            _, _, (partial, target) = dataset[index]
            if partial.shape != (8192, 3) or target.shape != (8192, 3):
                raise RuntimeError(f"Fold {fold} {label}: invalid point tensor shape")
            if not torch.isfinite(partial).all() or not torch.isfinite(target).all():
                raise RuntimeError(f"Fold {fold} {label}: nonfinite point tensor")

    artifacts = {
        f"fold{fold}_config": config_path,
        f"fold{fold}_train_ids": Path(train.include_case_ids_file),
        f"fold{fold}_dev_ids": Path(dev.include_case_ids_file),
    }
    return {
        "train_cases": len(train),
        "dev_cases": len(dev),
        "train_source_skulls": len(train_skulls),
        "dev_source_skulls": len(dev_skulls),
        "train_dev_disjoint": True,
        "development_only": True,
    }, artifacts


def training_probe(config_path: Path) -> dict:
    if not torch.cuda.is_available():
        raise RuntimeError("S0 training smoke requires CUDA")
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    config = cfg_from_yaml_file(str(config_path))
    dataset = build_dataset(config, "train")
    loader = DataLoader(dataset, batch_size=2, shuffle=False, num_workers=0)
    _, _, data = next(iter(loader))
    partial, target = (value.cuda(non_blocking=False) for value in data)
    model = builder.model_builder(config.model).cuda().train()
    model.zero_grad(set_to_none=True)
    output = model(partial)
    sparse_loss, dense_loss = model.get_loss(output, target, epoch=0)
    total = sparse_loss + dense_loss
    if not torch.isfinite(total):
        raise RuntimeError("S0 smoke training loss is nonfinite")
    total.backward()
    gradients = [
        value.grad for value in model.parameters()
        if value.requires_grad and value.grad is not None
    ]
    if not gradients or any(not torch.isfinite(value).all() for value in gradients):
        raise RuntimeError("S0 smoke backward produced missing/nonfinite gradients")
    result = {
        "fold": "A",
        "batch_size": 2,
        "input_shape": list(partial.shape),
        "target_shape": list(target.shape),
        "forward_finite": True,
        "loss_finite": True,
        "backward_finite": True,
        "optimizer_steps": 0,
        "parameters_total": int(sum(value.numel() for value in model.parameters())),
        "parameters_trainable": int(
            sum(value.numel() for value in model.parameters() if value.requires_grad)
        ),
    }
    del output, sparse_loss, dense_loss, total, gradients, model, partial, target
    torch.cuda.empty_cache()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_receipt", type=Path, required=True)
    parser.add_argument("--deployment_receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify_only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.verify_only:
        verify_receipt(output)
        return

    config_dir = args.config_dir.resolve()
    auth = args.authorization_receipt.resolve()
    deployment = args.deployment_receipt.resolve()
    subprocess.run([
        sys.executable,
        str(REPO_ROOT / "tools/verify_mamba_v13_d3_s0_runtime_authorization.py"),
        "--config_dir", str(config_dir),
        "--receipt", str(auth),
    ], check=True, cwd=REPO_ROOT)

    fold_audits = {}
    artifact_paths = {
        "authorization_receipt": auth,
        "deployment_receipt": deployment,
        "smoke_tool": Path(__file__).resolve(),
        "evaluator": REPO_ROOT / "tools/evaluate_skullfix_implant.py",
        "efficiency_tool": REPO_ROOT / "tools/benchmark_mamba_v12_efficiency.py",
        "run_record_tool": REPO_ROOT / "tools/write_mamba_v13_d3_run_record.py",
        "completion_tool": REPO_ROOT / "tools/freeze_mamba_v13_d3_s0_seed0.py",
        "fold_runner": REPO_ROOT / "scripts/run_mamba_v13_d3_s0_seed0_fold.sh",
        "sequence_runner": REPO_ROOT / "scripts/run_mamba_v13_d3_s0_seed0.sh",
        "tmux_launcher": REPO_ROOT / "scripts/launch_mamba_v13_d3_s0_seed0_tmux.sh",
        "preflight_script": REPO_ROOT / "scripts/preflight_mamba_v13_d3_s0_seed0.sh",
    }
    for fold in tqdm(FOLDS, desc="S0 dataset/config smoke", dynamic_ncols=True):
        config_path = config_dir / f"MambaV13D3_S0_fold{fold}_seed0.yaml"
        fold_audits[fold], fold_artifacts = audit_fold(config_path, fold)
        artifact_paths.update(fold_artifacts)

    probe = training_probe(
        config_dir / "MambaV13D3_S0_foldA_seed0.yaml"
    )
    receipt = {
        "smoke_version": VERSION,
        "status": "passed_s0_seed0_training_probe",
        "candidate": "S0",
        "seed": 0,
        "folds": list(FOLDS),
        "fold_audits": fold_audits,
        "training_probe": probe,
        "artifacts": {
            name: {"path": portable_path(path), "sha256": sha256_file(path)}
            for name, path in sorted(artifact_paths.items())
        },
        "S1_authorized": False,
        "S2_authorized": False,
        "holdout_authorized": False,
        "locked_holdout_accessed": False,
        "selection_started": False,
        "next_step": "run_S0_seed0_folds_A_to_D_in_tmux",
    }
    payload = canonical_json(receipt)
    write_identical_or_new(output, payload)
    digest = hashlib.sha256(payload).hexdigest()
    write_identical_or_new(
        Path(str(output) + ".sha256"),
        f"{digest}  {output.name}\n".encode("ascii"),
    )
    verify_receipt(output)
    print(f"[saved] S0 smoke receipt: {output}")
    print("[done] dataset/config audit and zero-step CUDA training probe passed")


if __name__ == "__main__":
    main()
