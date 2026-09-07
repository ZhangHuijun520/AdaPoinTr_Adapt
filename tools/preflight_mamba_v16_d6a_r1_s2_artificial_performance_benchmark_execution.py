#!/usr/bin/env python3
"""Run the zero-count CUDA preflight for the authorized S2 benchmark."""

from __future__ import annotations

import os

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.verify_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_authorization import (  # noqa: E402
    verify_authorization,
)
from utils.mamba_d6a_r1_s1_exact_assignment import frozen_reference_diagnostics  # noqa: E402
from utils.mamba_d6a_r1_s2_certified_fast_path import s2_certified_fast_path_assignment  # noqa: E402


S1_PREFLIGHT = ROOT / "tools/preflight_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py"
spec = importlib.util.spec_from_file_location("d6_s2_benchmark_artificial_suite", S1_PREFLIGHT)
suite_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(suite_module)
artificial_scores = suite_module.artificial_scores

VERSION = "mamba-v16-d6a-r1-s2-artificial-performance-benchmark-authorization-preflight-v1"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    outputs = dict(outputs)
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    ).encode("ascii")
    if output_dir.exists():
        existing = {path.relative_to(output_dir).as_posix(): path.read_bytes() for path in output_dir.rglob("*") if path.is_file()}
        if existing != outputs:
            raise RuntimeError(f"Existing S2 benchmark preflight drifted: {output_dir}")
        print(f"[locked] existing S2 benchmark preflight is byte-identical: {output_dir}")
        return
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            (working / name).write_bytes(payload)
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
    authorization, config = verify_authorization(args.config_dir, args.authorization_dir)
    if not torch.cuda.is_available():
        raise RuntimeError("S2 artificial benchmark preflight requires CUDA")
    torch.set_num_threads(1)
    device = torch.device("cuda:0")
    probe_contract = config["authorization_preflight"]
    scores = artificial_scores(probe_contract["probe_family"], probe_contract["probe_seed"])
    input_sha = sha256_bytes(scores.tobytes())
    logits = torch.from_numpy(scores).unsqueeze(0).to(device)
    with torch.inference_mode():
        s0_hard, s0_selected, s0_slots, s0_objective = frozen_reference_diagnostics(logits)
        s2 = s2_certified_fast_path_assignment(logits)
    slot_exact = torch.equal(s0_slots, s2.slot_to_candidate)
    selected_exact = torch.equal(s0_selected, s2.selected_indices)
    hard_exact = torch.equal(s0_hard, s2.hard_assignment)
    objective_exact = bool(s0_objective == s2.adjusted_objective)
    input_unchanged = input_sha == sha256_bytes(logits.detach().cpu().numpy()[0].tobytes())
    outputs_finite = bool(torch.isfinite(s2.hard_assignment).all().item() and np.isfinite(s2.adjusted_objective))
    if not all((slot_exact, selected_exact, hard_exact, objective_exact, input_unchanged, outputs_finite)):
        raise RuntimeError("S2 benchmark preflight equivalence probe failed")
    if s2.route != probe_contract["expected_S2_route"] or s2.fallback_reason != "none":
        raise RuntimeError("S2 benchmark preflight route drifted")

    auth_path = args.authorization_dir / "benchmark_execution_authorization_receipt.json"
    probe = {
        "family": probe_contract["probe_family"],
        "seed": probe_contract["probe_seed"],
        "shape": list(logits.shape),
        "S0_calls": 1,
        "S2_calls": 1,
        "slot_to_candidate_exact": slot_exact,
        "sorted_selected_indices_exact": selected_exact,
        "hard_assignment_exact": hard_exact,
        "adjusted_objective_exact": objective_exact,
        "input_unchanged": input_unchanged,
        "outputs_finite": outputs_finite,
        "S2_route": s2.route,
        "selected_unique": int(s2.selected_indices.unique().numel()),
    }
    receipt = {
        "preflight_version": VERSION,
        "status": "D6A_R1_S2_artificial_performance_benchmark_authorization_preflight_passed",
        "authorization_receipt_sha256": sha256_bytes(auth_path.read_bytes()),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "probe": probe,
        "correctness_replay_cases": 0,
        "warmup_calls": 0,
        "timed_calls": 0,
        "measurement_blocks": 0,
        "torch_profiler_traces": 0,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "S2_artificial_performance_benchmark_execution_authorized": True,
        "S2_implementation_change_authorized": False,
        "R1_production_implementation_change_authorized": False,
        "formal_efficiency_rerun_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_tmux_launch_of_one_authorized_S2_artificial_performance_benchmark",
    }
    report = (
        "# Mamba v1.6 D6-A R1 S2 artificial benchmark authorization preflight\n\n"
        "- Probe：independent_normal / seed 160610；S0/S2 各 1 次。\n"
        "- Slot、selected、hard 与 objective 精确一致；S2 route=certified_fast_path。\n"
        "- Correctness replay/warmup/timed calls/blocks/profiler：0 / 0 / 0 / 0 / 0。\n"
        "- Optimizer steps/model updates/D6 cases：0 / 0 / 0。\n"
        "- 下一步仅允许单独 tmux 启动一次冻结人工 benchmark。\n"
        "- Production、formal rerun、training、seed-1、D6-B 与 sealed access 保持锁定。\n"
    ).encode("utf-8")
    write_locked(
        {
            "authorization_preflight_probe.json": canonical_json(probe),
            "authorization_preflight_receipt.json": canonical_json(receipt),
            "authorization_preflight_report_zh.md": report,
        },
        args.output_dir.resolve(),
    )
    print(f"[saved] immutable S2 benchmark authorization preflight: {args.output_dir.resolve()}")
    print("[done] S0=1 S2=1 correctness_replay=0 warmup=0 timed=0 blocks=0")
    print("[locked] benchmark not started; production=false formal_rerun=false training=false D6=false")


if __name__ == "__main__":
    main()
