#!/usr/bin/env python3
"""Run one immutable D6-A R1 train-only gradient-calibration fold."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import numpy as np
import torch

from tools.verify_mamba_v16_d6a_gradient_calibration_execution_authorization import verify_authorization
from utils.mamba_d5a_proposal import geometry_descriptor_27d
from utils.mamba_d6a_slot_allocator import D6R1SlotAllocator, d6a_raw_losses


VERSION = "mamba-v16-d6a-r1-gradient-calibration-fold-v1"
FOLDS = ("A", "B", "C", "D")
LOSS_NAMES = ("L_point", "L_support", "L_shape")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_manifest(root: Path) -> None:
    for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")


def state_hash(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def tensor_norm(values: Iterable[torch.Tensor | None]) -> float:
    total = torch.zeros((), dtype=torch.float64)
    for value in values:
        if value is not None:
            total += value.detach().double().square().sum().cpu()
    result = float(torch.sqrt(total).item())
    if not np.isfinite(result):
        raise RuntimeError("Non-finite diagnostic gradient norm")
    return result


def load_manifest(audit: Path) -> dict[str, dict[str, Any]]:
    path = audit / "manifest_portable.jsonl"
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        rows[row["case_id"]] = row
    if len(rows) != 400:
        raise RuntimeError("Portable manifest must contain 400 cases")
    return rows


def load_case(case_id: str, row: dict[str, Any], audit: Path) -> tuple[np.ndarray, np.ndarray]:
    path = (audit / row["point_path"]).resolve()
    if not path.is_file() or sha256_file(path) != row["derived_case_sha256"]:
        raise RuntimeError(f"Case hash mismatch: {case_id}")
    with np.load(path, allow_pickle=False) as sample:
        partial = sample["partial"].copy()
        mask = sample["reference_rim_mask"].copy()
    expected_positive = int(row["point_audit"]["reference_rim_points"])
    if not (
        partial.shape == (8192, 3) and partial.dtype == np.float32
        and np.isfinite(partial).all() and mask.shape == (8192,)
        and mask.dtype == np.bool_ and int(mask.sum()) == expected_positive
        and 0 < expected_positive < 8192
    ):
        raise RuntimeError(f"NPZ contract failed: {case_id}")
    return partial, mask


def read_schedule(path: Path) -> list[list[str]]:
    batches = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 9 or fields[0] != f"{len(batches) + 1:02d}":
            raise RuntimeError("Calibration schedule drifted")
        batches.append(fields[1:])
    if len(batches) != 8:
        raise RuntimeError("Calibration requires exactly eight batches")
    return batches


def parameter_groups(model: D6R1SlotAllocator) -> dict[str, list[torch.Tensor]]:
    point_encoder = list(model.point_encoder.parameters())
    calibration = list(model.point_calibration.parameters())
    used = {id(value) for value in point_encoder + calibration}
    slot = [value for value in model.parameters() if id(value) not in used]
    return {
        "shared_point_encoder": point_encoder,
        "point_calibration_branch": calibration,
        "slot_attention_and_pointer": slot,
    }


def write_exact(output: Path, files: dict[str, bytes]) -> None:
    if output.exists():
        verify_manifest(output)
        receipt = json.loads((output / "calibration_fold_receipt.json").read_text(encoding="utf-8"))
        if receipt.get("run_version") != VERSION:
            raise RuntimeError(f"Existing output is not reusable: {output}")
        print(f"[locked] existing calibration fold is valid: {output}")
        return
    working = output.with_name(f".{output.name}.working")
    if working.exists():
        raise RuntimeError(f"Working directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    manifest = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    (working / "files.sha256").write_bytes(manifest)
    working.rename(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fold", choices=FOLDS, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--calibration_lock_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    fold = args.fold
    output = args.output_dir.resolve()
    if output.exists():
        write_exact(output, {})
        return
    receipt = verify_authorization(args.config_dir, args.authorization_dir)
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    binding = receipt["folds"][fold]
    if not (
        sha256_file(config_path) == binding["config"]["sha256"]
        and config.get("fold") == fold
        and config.get("boundaries", {}).get("calibration_execution_authorized") is True
        and config.get("boundaries", {}).get("seed0_training_authorized") is False
        and config.get("boundaries", {}).get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Calibration runtime config binding failed")

    calibration = args.calibration_lock_dir.resolve()
    fourfold = args.fourfold_lock_dir.resolve()
    audit = args.generation_audit_dir.resolve()
    verify_manifest(calibration)
    verify_manifest(fourfold)
    verify_manifest(audit)
    schedule_path = calibration / config["schedule_file"]
    if sha256_file(schedule_path) != config["schedule_sha256"]:
        raise RuntimeError("Frozen calibration schedule hash drifted")
    batches = read_schedule(schedule_path)
    train_ids = {
        line.strip() for line in (fourfold / f"fold{fold}_train_case_ids.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    if len(train_ids) != 300 or any(case not in train_ids for batch in batches for case in batch):
        raise RuntimeError("Calibration schedule is not train-only")
    manifest = load_manifest(audit)
    if not torch.cuda.is_available():
        raise RuntimeError("D6-A gradient calibration requires CUDA")
    device = torch.device("cuda:0")

    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    cpu_rng_before = torch.get_rng_state().clone()
    cuda_rng_before = torch.cuda.get_rng_state_all()
    model = D6R1SlotAllocator().to(device).train()
    model_state_before = state_hash(model)
    groups = parameter_groups(model)
    all_parameters = [value for values in groups.values() for value in values]
    group_slices: dict[str, slice] = {}
    start = 0
    for name, values in groups.items():
        group_slices[name] = slice(start, start + len(values))
        start += len(values)

    rows = []
    for batch_index, case_ids in enumerate(batches, 1):
        partials, masks = zip(*(load_case(case, manifest[case], audit) for case in case_ids))
        partial = torch.from_numpy(np.stack(partials)).to(device)
        positive = torch.from_numpy(np.stack(masks)).to(device)
        with torch.no_grad():
            descriptors = geometry_descriptor_27d(
                partial, knn_small=16, knn_large=32, epsilon=1.0e-8,
                query_chunk_size=512,
            )
        outputs = model(descriptors)
        losses = d6a_raw_losses(outputs, positive)
        common = outputs["point_features"]
        row: dict[str, Any] = {"batch": batch_index, "case_ids": "|".join(case_ids)}
        for loss_index, loss_name in enumerate(LOSS_NAMES):
            gradients = torch.autograd.grad(
                losses[loss_name], [common, *all_parameters],
                retain_graph=loss_index < len(LOSS_NAMES) - 1,
                allow_unused=True,
            )
            if gradients[0] is None:
                raise RuntimeError(f"Missing common-F gradient: {loss_name}")
            raw_norm = tensor_norm([gradients[0]])
            if not np.isfinite(raw_norm) or raw_norm <= 0.0:
                raise RuntimeError(f"Invalid common-F norm: {loss_name}={raw_norm}")
            row[f"{loss_name}_raw_common_F_norm"] = raw_norm
            parameter_gradients = gradients[1:]
            for group_name, group_slice in group_slices.items():
                row[f"{loss_name}_{group_name}_norm"] = tensor_norm(parameter_gradients[group_slice])
        rows.append(row)
        del outputs, losses, common, descriptors, partial, positive
        torch.cuda.empty_cache()

    medians = {
        name: median(float(row[f"{name}_raw_common_F_norm"]) for row in rows)
        for name in LOSS_NAMES
    }
    lambda_support = 0.5 * medians["L_point"] / medians["L_support"]
    lambda_shape = 0.1 * medians["L_point"] / medians["L_shape"]
    if not all(np.isfinite(value) and 0.0001 <= value <= 10000.0 for value in (lambda_support, lambda_shape)):
        raise RuntimeError("Calibrated weight is non-finite, non-positive, or outside frozen bounds")
    model_state_after = state_hash(model)
    state_unchanged = model_state_before == model_state_after
    torch.set_rng_state(cpu_rng_before)
    torch.cuda.set_rng_state_all(cuda_rng_before)
    rng_restored = torch.equal(torch.get_rng_state(), cpu_rng_before) and all(
        torch.equal(left, right) for left, right in zip(torch.cuda.get_rng_state_all(), cuda_rng_before)
    )
    if not state_unchanged or not rng_restored:
        raise RuntimeError("Model state or RNG was not restored")

    fieldnames = list(rows[0])
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    fold_receipt = {
        "run_version": VERSION,
        "status": "D6A_R1_fold_gradient_calibration_complete",
        "candidate": "R1", "fold": fold, "seed": 0,
        "batches": 8, "batch_size": 8, "measured_case_slots": 64,
        "component_medians": medians,
        "lambda_support": lambda_support,
        "lambda_shape": lambda_shape,
        "target_support_ratio": 0.5,
        "target_shape_ratio": 0.1,
        "gradient_clipping_applied": False,
        "optimizer_constructed": False, "optimizer_steps": 0, "model_updates": 0,
        "checkpoint_loaded": False, "checkpoint_written": False,
        "development_dev_cases_accessed": 0,
        "model_state_unchanged": state_unchanged,
        "random_state_restored": rng_restored,
        "seed0_training_authorized": False, "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False, "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "lineage_sha256": {
            "authorization_receipt": sha256_file(args.authorization_dir / "d6a_gradient_calibration_execution_authorization_receipt.json"),
            "runtime_config": sha256_file(config_path),
            "schedule": sha256_file(schedule_path),
            "generation_audit_manifest": sha256_file(audit / "files.sha256"),
        },
    }
    files = {
        "gradient_norms.csv": stream.getvalue().encode("utf-8"),
        "calibration_fold_receipt.json": canonical_json(fold_receipt),
    }
    write_exact(output, files)
    print(f"[saved] immutable D6-A calibration fold: {output}")
    print(f"[weight] fold={fold} support={lambda_support:.12g} shape={lambda_shape:.12g}")
    print("[locked] optimizer_steps=0 training=false dev=false sealed=false")


if __name__ == "__main__":
    main()
