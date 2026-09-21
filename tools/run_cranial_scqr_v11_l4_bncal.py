#!/usr/bin/env python
"""Train-only full-allowlist BatchNorm calibration for SCQR v1.1 L4."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import builder  # noqa: E402
from tools.cranial_scqr_l4_audit import sha256_file  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402


VERSION = "cranial-scqr-v1.1-l4-bncal-v1"
EXPECTED_CASES = 315
EXPECTED_BATCHES = 40
EXPECTED_SOURCES = 63
EXPECTED_DEFECTS = {
    "bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"
}


def canonical_json(payload: dict) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def tensor_map_sha256(items) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(items):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(value.dtype).encode("ascii") + b"\0")
        digest.update(str(tuple(value.shape)).encode("ascii") + b"\0")
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def read_ids(path: Path) -> list[str]:
    values = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(values) != EXPECTED_CASES or len(set(values)) != EXPECTED_CASES:
        raise RuntimeError("BNCal train allowlist must contain 315 unique cases")
    return values


def source_id(case_id: str) -> str:
    parts = case_id.split("__")
    if len(parts) != 3 or parts[0] != "train":
        raise RuntimeError(f"Invalid development84 train case ID: {case_id}")
    return parts[1]


class PartialOnlyDataset(Dataset):
    """Open only the NPZ partial member; no implant/GT member is indexed."""

    def __init__(self, config):
        others = config.dataset.train.others
        data_root = Path(str(others.DATA_ROOT)).expanduser()
        if not data_root.is_absolute():
            data_root = REPO_ROOT / data_root
        self.data_root = data_root.resolve()
        manifest_name = str(config.dataset.train._base_.MANIFEST)
        manifest = Path(manifest_name).expanduser()
        if not manifest.is_absolute():
            manifest = self.data_root / manifest
        self.manifest_path = manifest.resolve()
        allowlist = Path(str(others.include_case_ids_file)).expanduser()
        if not allowlist.is_absolute():
            allowlist = REPO_ROOT / allowlist
        self.allowlist_path = allowlist.resolve()
        self.case_ids = read_ids(self.allowlist_path)
        allowed = set(self.case_ids)

        records = {}
        with self.manifest_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                case_id = str(record.get("case_id", ""))
                if case_id not in allowed:
                    continue
                if record.get("official_split") != "train":
                    raise RuntimeError(f"BNCal case is outside official train: {case_id}")
                if record.get("monitor_split") == "monitor":
                    raise RuntimeError(f"BNCal case is in old monitor: {case_id}")
                if case_id in records:
                    raise RuntimeError(f"Duplicate BNCal manifest case: {case_id}")
                records[case_id] = record
        if set(records) != allowed:
            raise RuntimeError("BNCal manifest and train allowlist case sets differ")
        sources = {source_id(value) for value in self.case_ids}
        defects = {value.split("__")[2] for value in self.case_ids}
        if len(sources) != EXPECTED_SOURCES or defects != EXPECTED_DEFECTS:
            raise RuntimeError("BNCal source/defect identity drifted")
        self.records = [records[value] for value in self.case_ids]
        self.opened_case_ids: list[str] = []

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        record = self.records[index]
        point_path = Path(str(record["point_path"])).expanduser()
        if not point_path.is_absolute():
            point_path = self.data_root / point_path
        with np.load(point_path.resolve(), allow_pickle=False) as payload:
            if "partial" not in payload.files:
                raise RuntimeError(f"partial missing: {record['case_id']}")
            partial = payload["partial"].astype(np.float32, copy=True)
        if partial.shape != (8192, 3) or not np.isfinite(partial).all():
            raise RuntimeError(f"Invalid partial array: {record['case_id']}")
        self.opened_case_ids.append(str(record["case_id"]))
        return str(record["case_id"]), torch.from_numpy(partial)


def validate_execution(config, config_path: Path, experiment_dir: Path):
    execution = config.cranial_scqr_execution
    development = config.development_protocol
    if (
        str(execution.stage) != "L4_roundA_training"
        or not bool(execution.training_authorized)
        or not bool(execution.bncal_authorized)
        or bool(execution.development_payload_access_authorized)
        or bool(execution.resume_authorized)
        or int(execution.optimizer_steps_authorized) != 3939
        or int(development.seed) != 0
    ):
        raise RuntimeError("BNCal runtime authorization contract is invalid")
    state_path = experiment_dir / "l4_execution_state.json"
    checkpoint_path = experiment_dir / "ckpt-last.pth"
    if not state_path.is_file() or not checkpoint_path.is_file():
        raise RuntimeError("BNCal requires completed training state and ckpt-last")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if (
        state.get("status") != "training_complete_pending_bncal"
        or state.get("optimizer_steps") != 3939
        or state.get("model_updates") != 3939
        or state.get("epoch_traversals_completed") != 101
        or state.get("development_payload_accessed") is not False
        or state.get("bncal_updates") != 0
        or state.get("runtime_config_sha256") != sha256_file(config_path)
        or state.get("checkpoint_sha256") != sha256_file(checkpoint_path)
        or state.get("candidate") != str(development.candidate)
        or state.get("fold") != str(development.fold)
    ):
        raise RuntimeError("BNCal source training receipt is invalid")
    return state_path, checkpoint_path, state


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--experiment_dir", type=Path, required=True)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = args.config.resolve()
    experiment_dir = args.experiment_dir.resolve()
    if args.batch_size != 8 or args.num_workers != 0 or args.seed != 0:
        raise RuntimeError("SCQR L4 BNCal requires batch=8, workers=0, seed=0")
    output_checkpoint = experiment_dir / "ckpt-last-bncal.pth"
    receipt_path = experiment_dir / "l4_bncal_receipt.json"
    files_path = experiment_dir / "l4_bncal_files.sha256"
    for path in (output_checkpoint, receipt_path, files_path):
        if path.exists():
            raise RuntimeError(f"BNCal output already exists; rerun forbidden: {path}")

    config = cfg_from_yaml_file(str(config_path))
    state_path, checkpoint_path, training_state = validate_execution(
        config, config_path, experiment_dir
    )
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("SCQR L4 BNCal requires exactly one visible CUDA GPU")

    dataset = PartialOnlyDataset(config)
    loader = DataLoader(
        dataset,
        batch_size=8,
        shuffle=False,
        drop_last=False,
        num_workers=0,
    )
    if len(loader) != EXPECTED_BATCHES:
        raise RuntimeError(f"BNCal requires 40 batches, got {len(loader)}")

    device = torch.device("cuda:0")
    model = builder.model_builder(config.model).to(device)
    builder.load_model(model, str(checkpoint_path))
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    parameter_sha_before = tensor_map_sha256(model.named_parameters())
    state_before = {
        name: value.detach().cpu().clone() for name, value in model.state_dict().items()
    }
    batchnorm = {
        name: module
        for name, module in model.named_modules()
        if isinstance(module, nn.modules.batchnorm._BatchNorm)
    }
    if not batchnorm:
        raise RuntimeError("SCQR model has no BatchNorm layers")
    model.eval()
    for module in batchnorm.values():
        module.reset_running_stats()
        module.momentum = None
        module.train()

    started = datetime.now(timezone.utc).isoformat()
    torch.cuda.reset_peak_memory_stats()
    batches = 0
    with torch.inference_mode():
        for _, partial in tqdm(loader, total=EXPECTED_BATCHES, desc="SCQR L4 BNCal"):
            model(partial.to(device, non_blocking=False), epoch=None)
            batches += 1
    if batches != EXPECTED_BATCHES:
        raise RuntimeError(f"BNCal batch count mismatch: {batches}")
    if len(dataset.opened_case_ids) != EXPECTED_CASES:
        raise RuntimeError("BNCal payload-open count mismatch")
    if dataset.opened_case_ids != dataset.case_ids:
        raise RuntimeError("BNCal payload order differs from frozen allowlist")

    parameter_sha_after = tensor_map_sha256(model.named_parameters())
    if parameter_sha_after != parameter_sha_before:
        raise RuntimeError("BNCal changed model parameters")
    changed = []
    for name, after in model.state_dict().items():
        if not torch.equal(state_before[name], after.detach().cpu()):
            changed.append(name)
    allowed = {
        f"{name}.{suffix}"
        for name in batchnorm
        for suffix in ("running_mean", "running_var", "num_batches_tracked")
    }
    unexpected = sorted(set(changed).difference(allowed))
    if unexpected:
        raise RuntimeError(f"BNCal changed non-BN state: {unexpected[:10]}")

    source_checkpoint = torch.load(checkpoint_path, map_location="cpu")
    source_checkpoint["base_model"] = {
        name: value.detach().cpu() for name, value in model.state_dict().items()
    }
    metadata = {
        "version": VERSION,
        "source_checkpoint_sha256": sha256_file(checkpoint_path),
        "train_case_ids_sha256": sha256_file(dataset.allowlist_path),
        "partial_only": True,
        "implant_or_gt_members_opened": 0,
        "batches": batches,
        "cases": len(dataset.opened_case_ids),
        "reset_running_stats": True,
    }
    source_checkpoint["bn_recalibration"] = metadata
    temporary = output_checkpoint.with_suffix(".pth.tmp")
    torch.save(source_checkpoint, temporary)
    os.replace(temporary, output_checkpoint)

    receipt = {
        "receipt_version": VERSION,
        "status": "PASS",
        "candidate": str(config.development_protocol.candidate),
        "fold": str(config.development_protocol.fold),
        "seed": 0,
        "started_at_utc": started,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_config_sha256": sha256_file(config_path),
        "training_state_sha256": sha256_file(state_path),
        "source_checkpoint_sha256": sha256_file(checkpoint_path),
        "bncal_checkpoint_sha256": sha256_file(output_checkpoint),
        "train_case_ids_sha256": sha256_file(dataset.allowlist_path),
        "train_cases": EXPECTED_CASES,
        "train_sources": EXPECTED_SOURCES,
        "bncal_batches": batches,
        "bncal_forward_calls": batches,
        "bncal_buffer_update_batches": batches,
        "optimizer_constructions": 0,
        "optimizer_steps": 0,
        "model_parameter_updates": 0,
        "parameter_sha256_before": parameter_sha_before,
        "parameter_sha256_after": parameter_sha_after,
        "parameters_unchanged": True,
        "batchnorm_layer_count": len(batchnorm),
        "changed_bn_buffer_count": len(changed),
        "changed_bn_buffers": sorted(changed),
        "non_bn_state_changes": [],
        "payload_open_events": len(dataset.opened_case_ids),
        "npz_members_opened": ["partial"],
        "implant_or_gt_members_opened": 0,
        "development_payload_opened": 0,
        "confirmation20_payload_opened": 0,
        "official_test_payload_opened": 0,
        "old_monitor_payload_opened": 0,
        "mug_payload_opened": 0,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "development_evaluation_authorized_by_this_receipt": False,
        "next_run_authorized_by_this_receipt": False,
    }
    receipt_path.write_bytes(canonical_json(receipt))
    files_path.write_text(
        f"{sha256_file(output_checkpoint)}  {output_checkpoint.name}\n"
        f"{sha256_file(receipt_path)}  {receipt_path.name}\n",
        encoding="ascii",
    )
    print(f"[done] BNCal PASS candidate={receipt['candidate']} fold={receipt['fold']}")
    print(f"[count] cases={EXPECTED_CASES} batches={batches} optimizer_steps=0")
    print(f"[saved] {output_checkpoint}")
    print(f"[saved] {receipt_path}")


if __name__ == "__main__":
    main()
