#!/usr/bin/env python3
"""Run the zero-count CUDA preflight for authorized R1 latency profiling."""

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

from tools.verify_mamba_v16_d6a_r1_latency_posthoc_profiling_authorization import (  # noqa: E402
    verify_authorization,
)
from utils.mamba_d5a_proposal import D5V1ContextHead  # noqa: E402
from utils.mamba_d6a_r1_latency_profiler import shadow_global_assignment  # noqa: E402
from utils.mamba_d6a_slot_allocator import (  # noqa: E402
    D6R1SlotAllocator,
    deterministic_global_assignment,
)


VERSION = "mamba-v16-d6a-r1-latency-posthoc-profiling-execution-preflight-v1"


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
        raise RuntimeError(f"Profiling preflight output already exists: {output_dir}")
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
        raise RuntimeError("R1 profiling preflight requires CUDA")

    config_path = args.config_dir / authorization["runtime_config"]["name"]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    device = torch.device("cuda:0")
    torch.manual_seed(160610)
    torch.cuda.manual_seed_all(160610)
    generator = torch.Generator(device="cpu").manual_seed(160610)
    descriptors = torch.randn(1, 8192, 27, generator=generator, dtype=torch.float32).to(device)

    reference_model = D5V1ContextHead().to(device).eval()
    del reference_model
    torch.cuda.empty_cache()
    model = D6R1SlotAllocator().to(device).eval()
    before = tensor_state_hash(model)
    if before != config["expected_R1_state_sha256"]:
        raise RuntimeError("R1 preflight state does not match frozen formal result")

    with torch.inference_mode():
        outputs = model(descriptors)
        _, frozen_selected = deterministic_global_assignment(outputs["slot_logits"])
        _, shadow_selected, timings = shadow_global_assignment(
            outputs["slot_logits"], record_timings=False
        )
    if timings:
        raise RuntimeError("Zero-count preflight unexpectedly recorded timings")
    if not torch.equal(frozen_selected, shadow_selected):
        raise RuntimeError("Instrumented assignment is not equivalent to frozen assignment")
    selected_cpu = frozen_selected.detach().cpu()
    after = tensor_state_hash(model)
    if before != after:
        raise RuntimeError("R1 profiling preflight changed model state")

    auth_path = args.authorization_dir / "profiling_execution_authorization_receipt.json"
    probe = {
        "candidate": "R1",
        "descriptor_shape": list(descriptors.shape),
        "R1_forward_probes": 1,
        "assignment_equivalence_probes": 1,
        "selected_count": int(selected_cpu.shape[1]),
        "selected_unique": int(selected_cpu.unique().numel()),
        "selected_indices_equal": True,
        "state_sha256": before,
    }
    receipt = {
        "preflight_version": VERSION,
        "status": "D6A_R1_latency_posthoc_profiling_authorization_preflight_passed",
        "authorization_receipt_sha256": hashlib.sha256(auth_path.read_bytes()).hexdigest(),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "probe": probe,
        "profiling_blocks": 0,
        "timed_observations": 0,
        "torch_profiler_traces": 0,
        "formal_gate_evaluated": False,
        "formal_gate_changed": False,
        "formal_gate_rerun": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "posthoc_profiling_execution_authorized": True,
        "R1_implementation_change_authorized": False,
        "R2_implementation_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_tmux_launch_of_R1_posthoc_profiling",
    }
    report = (
        "# Mamba v1.6 D6-A R1 latency profiling 执行 preflight\n\n"
        "- R1 人工 descriptor forward：1；assignment 等价性探针：1。\n"
        "- Frozen assignment 与 instrumented shadow assignment 返回相同 32 个唯一索引。\n"
        "- Profiling blocks/timed observations/traces：0 / 0 / 0。\n"
        "- Model state 前后不变；optimizer steps/model updates：0 / 0。\n"
        "- Formal gate 未评估、未改变、未重跑；D6 cases：0。\n"
        "- 下一步仅允许单独 tmux 启动 R1 profiling。\n"
        "- Training、R1 修改、R2、seed-1、confirmation、D6-B 与 sealed 数据继续锁定。\n"
    ).encode("utf-8")
    write_locked(
        {
            "authorization_preflight_probe.json": canonical_json(probe),
            "authorization_preflight_receipt.json": canonical_json(receipt),
            "authorization_preflight_report_zh.md": report,
        },
        args.output_dir.resolve(),
    )
    print(f"[saved] immutable R1 profiling authorization preflight: {args.output_dir.resolve()}")
    print("[done] forward=1 equivalence=1 profiling_blocks=0 timed=0 traces=0")
    print("[locked] profiling not started; training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
