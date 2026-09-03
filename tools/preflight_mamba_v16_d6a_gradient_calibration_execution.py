#!/usr/bin/env python3
"""Run the authorized artificial CUDA preflight for D6-A calibration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import torch

from tools.verify_mamba_v16_d6a_gradient_calibration_execution_authorization import verify_authorization
from utils.mamba_d6a_slot_allocator import D6R1SlotAllocator, d6a_raw_losses


VERSION = "mamba-v16-d6a-gradient-calibration-execution-preflight-v1"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def model_hash(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode() + b"\0")
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def write_immutable(output: Path, files: dict[str, bytes]) -> None:
    if output.exists():
        raise RuntimeError(f"Preflight output already exists: {output}")
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
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    receipt = verify_authorization(args.config_dir, args.authorization_dir)
    if not torch.cuda.is_available():
        raise RuntimeError("D6-A calibration preflight requires CUDA")
    device = torch.device("cuda:0")
    torch.manual_seed(20260903)
    torch.cuda.manual_seed_all(20260903)
    model = D6R1SlotAllocator().to(device).train()
    before = model_hash(model)
    generator = torch.Generator(device=device).manual_seed(20260903)
    descriptors = torch.randn((2, 8192, 27), generator=generator, device=device)
    masks = torch.zeros((2, 8192), dtype=torch.bool, device=device)
    masks[0, torch.arange(0, 8192, 257, device=device)] = True
    masks[1, torch.arange(31, 8192, 263, device=device)] = True
    outputs = model(descriptors)
    losses = d6a_raw_losses(outputs, masks)
    common = outputs["point_features"]
    rows = []
    for index, name in enumerate(("L_point", "L_support", "L_shape")):
        gradient = torch.autograd.grad(
            losses[name], common, retain_graph=index < 2, allow_unused=False
        )[0]
        norm = float(torch.linalg.vector_norm(gradient.detach().double()).item())
        if not torch.isfinite(gradient).all() or not (norm > 0.0):
            raise RuntimeError(f"Artificial common-F gradient failed: {name}")
        rows.append({"loss": name, "raw_common_F_norm": format(norm, ".17g"), "finite": True})
    after = model_hash(model)
    if before != after:
        raise RuntimeError("Artificial preflight changed model state")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    result = {
        "preflight_version": VERSION,
        "status": "D6A_R1_gradient_calibration_artificial_CUDA_preflight_passed",
        "authorization_receipt_sha256": hashlib.sha256(
            (args.authorization_dir / "d6a_gradient_calibration_execution_authorization_receipt.json").read_bytes()
        ).hexdigest(),
        "cuda_device_name": torch.cuda.get_device_name(0),
        "artificial_cases": 2,
        "forward_passes": 1,
        "backward_gradient_queries": 3,
        "D6_cases_accessed": 0,
        "calibration_batches_executed": 0,
        "calibration_weights_computed": False,
        "calibration_receipt_written": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "model_state_unchanged": True,
        "calibration_execution_authorized": receipt["calibration_execution_authorized"],
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_tmux_launch_of_four_frozen_calibration_folds",
    }
    report = (
        "# Mamba v1.6 D6-A 梯度校准执行 preflight\n\n"
        "- 仅使用 2 例确定性人工 27D descriptor；D6 病例访问数为 0。\n"
        "- 三项损失的公共 F 梯度均为有限正数。\n"
        "- optimizer steps：0；model updates：0；未计算校准权重。\n"
        "- 下一步仅允许单独启动 A-D 四折冻结校准。\n"
        "- seed-0 训练、seed-1、confirmation、D6-B 与 sealed 数据继续锁定。\n"
    ).encode("utf-8")
    write_immutable(args.output_dir.resolve(), {
        "artificial_gradient_probe_metrics.csv": stream.getvalue().encode("utf-8"),
        "execution_preflight_receipt.json": canonical_json(result),
        "execution_preflight_report_zh.md": report,
    })
    print(f"[saved] immutable D6-A calibration execution preflight: {args.output_dir.resolve()}")
    print("[done] artificial_cases=2 gradient_queries=3 optimizer_steps=0 model_updates=0")
    print("[locked] D6_cases=0 calibration=false training=false sealed=false")


if __name__ == "__main__":
    main()
