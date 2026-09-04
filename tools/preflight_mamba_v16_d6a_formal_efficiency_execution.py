#!/usr/bin/env python3
"""Run the authorized zero-count preflight for formal D6-A efficiency."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.verify_mamba_v16_d6a_formal_efficiency_authorization import verify_authorization  # noqa: E402
from utils.mamba_d5a_proposal import D5V1ContextHead  # noqa: E402
from utils.mamba_d6a_efficiency import full_inference_once  # noqa: E402
from utils.mamba_d6a_slot_allocator import D6R1SlotAllocator  # noqa: E402


VERSION = "mamba-v16-d6a-formal-efficiency-execution-preflight-v1"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def tensor_state_hash(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        raise RuntimeError(f"Preflight output already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            (working / name).write_bytes(payload)
        manifest = "".join(
            f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
            for name, payload in sorted(outputs.items())
        ).encode("ascii")
        (working / "files.sha256").write_bytes(manifest)
        working.replace(output_dir)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    authorization = verify_authorization(args.config_dir, args.authorization_dir)
    if not torch.cuda.is_available():
        raise RuntimeError("D6-A formal-efficiency preflight requires CUDA")

    config_path = args.config_dir / authorization["runtime_config"]["name"]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    expected_states = config["expected_initial_state_sha256"]
    device = torch.device("cuda:0")
    torch.manual_seed(160610)
    torch.cuda.manual_seed_all(160610)
    generator = torch.Generator(device="cpu").manual_seed(160610)
    descriptors = torch.randn(1, 8192, 27, generator=generator, dtype=torch.float32).to(device)

    rows = []
    constructors = {"R0": D5V1ContextHead, "R1": D6R1SlotAllocator}
    for candidate in ("R0", "R1"):
        model = constructors[candidate]().to(device).eval()
        before = tensor_state_hash(model)
        if before != expected_states[candidate]:
            raise RuntimeError(f"{candidate} initial state does not match frozen zero-step")
        with torch.inference_mode():
            selected = full_inference_once(candidate, model, descriptors)
        after = tensor_state_hash(model)
        if before != after:
            raise RuntimeError(f"{candidate} preflight changed model state")
        rows.append({
            "candidate": candidate,
            "full_inference_passes": 1,
            "selected_count": int(selected.shape[1]),
            "selected_unique": int(selected.unique().numel()),
            "state_sha256": before,
        })
        del selected, model
        torch.cuda.empty_cache()

    receipt_path = args.authorization_dir / "formal_efficiency_execution_authorization_receipt.json"
    receipt = {
        "preflight_version": VERSION,
        "status": "D6A_R0_R1_formal_efficiency_authorization_preflight_passed",
        "authorization_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "candidate_order": ["R0", "R1"],
        "candidate_rows": rows,
        "formal_warmup_runs": 0,
        "formal_timed_runs": 0,
        "latency_gate_evaluated": False,
        "peak_memory_gate_evaluated": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "formal_efficiency_execution_authorized": True,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_tmux_launch_of_formal_efficiency_execution",
    }
    report = (
        "# Mamba v1.6 D6-A formal efficiency 执行 preflight\n\n"
        "- R0/R1 各执行一次人工 full inference；均返回 32 个唯一索引。\n"
        "- 初始 state hash 与冻结 zero-step 完全一致，执行前后不变。\n"
        "- 正式 warmup/timed runs：0 / 0；两项效率门控均未评估。\n"
        "- optimizer steps/model updates：0 / 0；D6 cases：0。\n"
        "- 下一步仅允许单独启动正式 efficiency benchmark。\n"
        "- training、seed-1、confirmation、D6-B 与 sealed 数据继续锁定。\n"
    ).encode("utf-8")
    outputs = {
        "authorization_preflight_probe.json": canonical_json({"rows": rows}),
        "authorization_preflight_receipt.json": canonical_json(receipt),
        "authorization_preflight_report_zh.md": report,
    }
    write_locked(outputs, args.output_dir.resolve())
    print(f"[saved] immutable D6-A formal-efficiency authorization preflight: {args.output_dir.resolve()}")
    print("[done] R0=1 R1=1 formal_warmup=0 formal_timed=0 optimizer_steps=0")
    print("[locked] benchmark not started; training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
