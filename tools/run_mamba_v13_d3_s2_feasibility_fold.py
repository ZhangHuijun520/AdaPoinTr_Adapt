#!/usr/bin/env python3
"""Train and score one frozen-S0 S2 rim-head feasibility fold."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import shutil
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.mamba_d3_contact import (  # noqa: E402
    assign_reference_rim_to_proxies,
    case_balanced_binary_cross_entropy,
    diversified_topk_indices,
)


VERSION = "mamba-v13-d3-s2-head-feasibility-fold-v1"
LOCK_VERSION = "mamba-v13-d3-s2-head-feasibility-lock-v1"
HOTFIX_VERSION = "mamba-v13-d3-s2-head-feasibility-hotfix1-v1"
FOLDS = ("A", "B", "C", "D")
EPOCHS = 50
BATCH_SIZE = 8
SELECTED_COUNT = 32
POOL_SIZE = 96


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def resolve(path: str | Path) -> Path:
    result = Path(path)
    if not result.is_absolute():
        result = REPO_ROOT / result
    return result.resolve()


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def verify_sidecar(path: Path) -> None:
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    if (
        len(fields) < 2
        or Path(fields[1]).name != path.name
        or sha256_file(path) != fields[0].lower()
    ):
        raise RuntimeError(f"SHA256 sidecar mismatch: {path}")


def verify_lock(lock_dir: Path, fold: str) -> tuple[dict, dict]:
    manifest = lock_dir / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = lock_dir / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Feasibility lock mismatch: {path}")
    receipt_path = lock_dir / "feasibility_lock_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    amendment = json.loads(
        (lock_dir / "execution_amendment.json").read_text(encoding="utf-8")
    )
    if not (
        receipt.get("lock_version") == LOCK_VERSION
        and receipt.get("status") == "S2_head_only_feasibility_authorized"
        and receipt.get("seed") == 0
        and receipt.get("S2_full_training_authorized") is False
        and receipt.get("holdout_authorized") is False
        and receipt.get("selection_started") is False
        and fold in receipt.get("folds", {})
        and amendment.get("training", {}).get("epochs") == EPOCHS
        and amendment.get("selection", {}).get("candidate_pool") == POOL_SIZE
        and amendment.get("selection", {}).get("selected_anchors") == SELECTED_COUNT
    ):
        raise RuntimeError("Feasibility lock semantics are invalid")
    return receipt, amendment


def verify_hotfix(hotfix_dir: Path, lock_dir: Path) -> dict:
    manifest = hotfix_dir / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = hotfix_dir / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Feasibility hotfix mismatch: {path}")
    receipt = json.loads(
        (hotfix_dir / "hotfix_receipt.json").read_text(encoding="utf-8")
    )
    base_receipt = lock_dir / "feasibility_lock_receipt.json"
    current_runner = Path(__file__).resolve()
    if not (
        receipt.get("hotfix_version") == HOTFIX_VERSION
        and receipt.get("status") == "development_gt_rim_scoring_repair_authorized"
        and receipt.get("base_lock_receipt_sha256") == sha256_file(base_receipt)
        and receipt.get("repaired_runner_sha256") == sha256_file(current_runner)
        and receipt.get("scientific_protocol_changed") is False
        and receipt.get("S2_full_training_authorized") is False
        and receipt.get("holdout_authorized") is False
        and receipt.get("selection_started") is False
    ):
        raise RuntimeError("Feasibility hotfix receipt semantics are invalid")
    return receipt


def build_dataset(config, split):
    dataset_cfg = getattr(config.dataset, split)
    return build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)


def freeze_model(model: nn.Module) -> None:
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    if hasattr(model, "set_mamba_adapter_scale"):
        model.set_mamba_adapter_scale(1.0)


def new_head(device: torch.device) -> nn.Sequential:
    head = nn.Sequential(nn.Linear(768, 128), nn.GELU(), nn.Linear(128, 1))
    for module in head.modules():
        if isinstance(module, nn.Linear):
            nn.init.trunc_normal_(module.weight, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
    return head.to(device)


def extract_cache(model, dataset, device, num_workers, label):
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        drop_last=False,
        num_workers=num_workers,
        pin_memory=True,
    )
    features = []
    coordinates = []
    labels = []
    case_ids = []
    scales = []
    with torch.inference_mode():
        for _, batch_case_ids, data in tqdm(
            loader, desc=label, dynamic_ncols=True
        ):
            batch_case_ids = [str(value) for value in batch_case_ids]
            partial = data[0].to(device=device, non_blocking=True)
            masks = dataset.get_gt_rim_masks(batch_case_ids, device=device)
            coor, proxy_features, _, _ = model.base_model.encode_rim_proxy_tokens(
                partial
            )
            proxy_labels = assign_reference_rim_to_proxies(
                coor, partial, masks
            ).labels
            features.append(proxy_features.float().cpu())
            coordinates.append(coor.float().cpu())
            labels.append(proxy_labels.cpu())
            case_ids.extend(batch_case_ids)
            scales.append(dataset.get_normalization_scales(batch_case_ids))
    return {
        "features": torch.cat(features, dim=0),
        "coordinates": torch.cat(coordinates, dim=0),
        "labels": torch.cat(labels, dim=0),
        "case_ids": case_ids,
        "scales": torch.cat(scales, dim=0),
    }


def selected_anchor_metrics(selected, labels, coordinates, scale):
    selected_labels = labels[selected]
    selected_positive = int(selected_labels.sum().item())
    positive = int(labels.sum().item())
    negative = int((~labels).sum().item())
    selected_coordinates = coordinates[selected]
    pairwise = torch.cdist(
        selected_coordinates.unsqueeze(0), selected_coordinates.unsqueeze(0)
    ).squeeze(0)
    pairwise.fill_diagonal_(float("inf"))
    coverage = float(pairwise.amin(dim=1).mean().item() * float(scale))
    return {
        "case_hit": int(selected_positive > 0),
        "positive_proxy_count": positive,
        "selected_positive_proxy_count": selected_positive,
        "positive_proxy_recall": selected_positive / positive,
        "precision": selected_positive / SELECTED_COUNT,
        "false_positive_rate": (SELECTED_COUNT - selected_positive) / negative,
        "selected_anchor_spatial_coverage_mm": coverage,
    }


def verify_existing(output: Path, fold: str) -> bool:
    receipt_path = output / "run_receipt.json"
    if not receipt_path.is_file():
        return False
    verify_sidecar(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        receipt.get("run_version") == VERSION
        and receipt.get("fold") == fold
        and receipt.get("status") in {"passed_hard_gate", "failed_hard_gate"}
        and receipt.get("holdout_accessed") is False
        and receipt.get("selection_started") is False
    ):
        raise RuntimeError(f"Existing feasibility receipt is invalid: {receipt_path}")
    for artifact in receipt["artifacts"].values():
        path = resolve(artifact["path"])
        if not path.is_file() or sha256_file(path) != artifact["sha256"]:
            raise RuntimeError(f"Existing feasibility artifact mismatch: {path}")
    print(f"[locked] existing S2 feasibility fold is valid: {fold}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold", choices=FOLDS, required=True)
    parser.add_argument("--lock_dir", type=Path, required=True)
    parser.add_argument("--hotfix_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--num_workers", type=int, default=4)
    args = parser.parse_args()
    fold = args.fold
    output = args.output_dir.resolve()
    if verify_existing(output, fold):
        return
    if output.exists():
        raise RuntimeError(f"Refusing non-final feasibility output directory: {output}")
    working = output.parent / f".{output.name}.working"
    if working.exists():
        if any(working.iterdir()):
            raise RuntimeError(
                f"Non-empty working directory requires inspection: {working}"
            )
        working.rmdir()
        print(f"[recovery] removed verified-empty working directory: {working}")
    working.mkdir(parents=True)

    if not torch.cuda.is_available():
        raise RuntimeError("S2 feasibility requires CUDA")
    device = torch.device("cuda:0")
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    lock_dir = args.lock_dir.resolve()
    lock, amendment = verify_lock(lock_dir, fold)
    verify_hotfix(args.hotfix_dir.resolve(), lock_dir)
    fold_lock = lock["folds"][fold]
    s0_config = resolve(fold_lock["s0_config"]["path"])
    s0_checkpoint = resolve(fold_lock["s0_checkpoint"]["path"])
    s2_template = resolve(fold_lock["s2_template"]["path"])
    for path, expected in (
        (s0_config, fold_lock["s0_config"]["sha256"]),
        (s0_checkpoint, fold_lock["s0_checkpoint"]["sha256"]),
        (s2_template, fold_lock["s2_template"]["sha256"]),
    ):
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"Fold {fold} frozen input mismatch: {path}")

    s0_cfg = cfg_from_yaml_file(str(s0_config))
    s2_cfg = cfg_from_yaml_file(str(s2_template))
    train_dataset = build_dataset(s2_cfg, "train")
    if len(train_dataset) != 300:
        raise RuntimeError(f"Fold {fold}: expected 300 training cases")

    model = builder.model_builder(s0_cfg.model).to(device)
    builder.load_model(model, str(s0_checkpoint))
    freeze_model(model)
    if any(parameter.requires_grad for parameter in model.parameters()):
        raise RuntimeError("S0 model was not fully frozen")

    train_cache = extract_cache(
        model,
        train_dataset,
        device,
        args.num_workers,
        f"S2 feasibility fold{fold} train features",
    )
    if len(set(train_cache["case_ids"])) != 300:
        raise RuntimeError("Training cache case IDs are not unique")

    head = new_head(device)
    optimizer = torch.optim.AdamW(
        head.parameters(), lr=1.0e-3, weight_decay=1.0e-4
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(0)
    optimizer_steps = 0
    final_loss = None
    progress = tqdm(range(1, EPOCHS + 1), desc=f"S2 head fold{fold}", dynamic_ncols=True)
    for epoch in progress:
        order = torch.randperm(300, generator=generator)
        losses = []
        head.train()
        for start in range(0, 300, BATCH_SIZE):
            indices = order[start : start + BATCH_SIZE]
            features = train_cache["features"][indices].to(
                device=device, non_blocking=True
            )
            labels = train_cache["labels"][indices].to(
                device=device, non_blocking=True
            )
            optimizer.zero_grad(set_to_none=True)
            logits = head(features).squeeze(-1)
            loss = case_balanced_binary_cross_entropy(logits, labels)
            if not torch.isfinite(loss):
                raise RuntimeError(f"Fold {fold}: nonfinite head loss")
            loss.backward()
            optimizer.step()
            optimizer_steps += 1
            losses.append(float(loss.detach().cpu()))
        final_loss = sum(losses) / len(losses)
        progress.set_postfix(epoch=epoch, loss=f"{final_loss:.6f}")
    if optimizer_steps != int(amendment["training"]["optimizer_steps_expected"]):
        raise RuntimeError(f"Unexpected optimizer step count: {optimizer_steps}")

    # The development dataset is materialized only after all head updates finish.
    train_gt_rim_key = getattr(
        s2_cfg.dataset.train.others, "GT_RIM_KEY", None
    )
    if train_gt_rim_key != "reference_rim_mask":
        raise RuntimeError("Frozen S2 train template has an unexpected GT_RIM_KEY")
    existing_dev_gt_rim_key = getattr(
        s2_cfg.dataset.val.others, "GT_RIM_KEY", None
    )
    if existing_dev_gt_rim_key not in (None, train_gt_rim_key):
        raise RuntimeError("Frozen S2 val template has a conflicting GT_RIM_KEY")
    s2_cfg.dataset.val.others.GT_RIM_KEY = train_gt_rim_key
    dev_dataset = build_dataset(s2_cfg, "val")
    if len(dev_dataset) != 100:
        raise RuntimeError(f"Fold {fold}: expected 100 development cases")
    dev_cache = extract_cache(
        model,
        dev_dataset,
        device,
        args.num_workers,
        f"S2 feasibility fold{fold} one-shot dev",
    )
    head.eval()
    rows = []
    with torch.inference_mode():
        for start in tqdm(
            range(0, 100, BATCH_SIZE),
            desc=f"S2 feasibility fold{fold} score",
            dynamic_ncols=True,
        ):
            end = min(start + BATCH_SIZE, 100)
            features = dev_cache["features"][start:end].to(device)
            coordinates = dev_cache["coordinates"][start:end].to(device)
            labels = dev_cache["labels"][start:end].to(device)
            logits = head(features).squeeze(-1)
            selected = diversified_topk_indices(
                logits,
                coordinates,
                selected_count=SELECTED_COUNT,
                pool_size=POOL_SIZE,
            )
            for local in range(end - start):
                case_index = start + local
                values = selected_anchor_metrics(
                    selected[local],
                    labels[local],
                    coordinates[local],
                    dev_cache["scales"][case_index],
                )
                record = dev_dataset.get_record(case_index)
                rows.append({
                    "case_id": dev_cache["case_ids"][case_index],
                    "source_skull_id": str(record.get("source_skull_id", record.get("skull_id", ""))),
                    "defect_type": str(record.get("defect_type", "")),
                    "fold": fold,
                    **values,
                })

    hits = sum(row["case_hit"] for row in rows)
    metric_names = (
        "positive_proxy_recall",
        "precision",
        "false_positive_rate",
        "selected_anchor_spatial_coverage_mm",
    )
    summary = {
        "summary_version": VERSION,
        "fold": fold,
        "seed": 0,
        "train_cases": 300,
        "development_cases": 100,
        "optimizer_steps": optimizer_steps,
        "final_training_loss": final_loss,
        "case_hits": hits,
        "case_hit_rate": hits / 100.0,
        "hard_gate_passed": hits == 100,
        "means": {
            key: float(np.mean([row[key] for row in rows])) for key in metric_names
        },
        "development_evaluation_count": 1,
        "full_S2_reuses_feasibility_head": False,
        "holdout_accessed": False,
        "selection_started": False,
    }
    csv_path = working / "feasibility_per_case.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary_path = working / "feasibility_summary.json"
    summary_path.write_bytes(canonical_json(summary))
    checkpoint_path = working / "head_only_checkpoint.pth"
    torch.save({
        "state_dict": head.state_dict(),
        "fold": fold,
        "seed": 0,
        "forbidden_for_full_S2_initialization": True,
        "architecture": "Linear(768,128)-GELU-Linear(128,1)",
    }, checkpoint_path)

    final_artifacts = {
        "head_only_checkpoint": output / checkpoint_path.name,
        "per_case_csv": output / csv_path.name,
        "summary": output / summary_path.name,
        "feasibility_lock_receipt": lock_dir / "feasibility_lock_receipt.json",
        "hotfix_receipt": args.hotfix_dir.resolve() / "hotfix_receipt.json",
    }
    source_paths = {
        "head_only_checkpoint": checkpoint_path,
        "per_case_csv": csv_path,
        "summary": summary_path,
        "feasibility_lock_receipt": lock_dir / "feasibility_lock_receipt.json",
        "hotfix_receipt": args.hotfix_dir.resolve() / "hotfix_receipt.json",
    }
    receipt = {
        "run_version": VERSION,
        "status": "passed_hard_gate" if hits == 100 else "failed_hard_gate",
        "fold": fold,
        "seed": 0,
        "artifacts": {
            name: {"path": portable(final_artifacts[name]), "sha256": sha256_file(path)}
            for name, path in source_paths.items()
        },
        "s0_checkpoint": fold_lock["s0_checkpoint"],
        "s0_model_frozen": True,
        "batchnorm_updates": False,
        "only_head_trainable": True,
        "full_S2_reuses_feasibility_head": False,
        "development_evaluation_count": 1,
        "case_hits": hits,
        "development_cases": 100,
        "hard_gate_passed": hits == 100,
        "S1_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_accessed": False,
        "selection_started": False,
    }
    receipt_path = working / "run_receipt.json"
    receipt_path.write_bytes(canonical_json(receipt))
    for path in (checkpoint_path, csv_path, summary_path, receipt_path):
        sidecar = Path(str(path) + ".sha256")
        sidecar.write_text(f"{sha256_file(path)}  {path.name}\n", encoding="ascii")

    os.replace(working, output)
    print(f"[saved] S2 feasibility fold {fold}: {output}")
    print(f"[gate] fold={fold} hits={hits}/100 passed={hits == 100}")
    print("[locked] S2_full=false holdout=false selection_started=false")


if __name__ == "__main__":
    main()
