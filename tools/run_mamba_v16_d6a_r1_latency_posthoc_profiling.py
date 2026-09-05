#!/usr/bin/env python3
"""Run the authorized one-shot D6-A R1 latency post-hoc profiling."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping, Sequence

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.verify_mamba_v16_d6a_r1_latency_posthoc_profiling_authorization import (  # noqa: E402
    verify_authorization,
)
from utils.mamba_d5a_proposal import D5V1ContextHead  # noqa: E402
from utils.mamba_d6a_r1_latency_profiler import profile_r1  # noqa: E402
from utils.mamba_d6a_slot_allocator import D6R1SlotAllocator  # noqa: E402


VERSION = "mamba-v16-d6a-r1-latency-posthoc-profiling-result-v1"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_state_hash(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    if not rows:
        raise RuntimeError("Cannot freeze empty profiling CSV")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().replace("\r\n", "\n").encode("utf-8")


def verify_preflight(preflight_dir: Path, authorization_hash: str) -> dict[str, Any]:
    manifest = preflight_dir / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = preflight_dir / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Profiling preflight artifact mismatch: {path}")
    receipt = json.loads(
        (preflight_dir / "authorization_preflight_receipt.json").read_text(encoding="utf-8")
    )
    if not (
        receipt.get("status") == "D6A_R1_latency_posthoc_profiling_authorization_preflight_passed"
        and receipt.get("authorization_receipt_sha256") == authorization_hash
        and receipt.get("profiling_blocks") == 0
        and receipt.get("timed_observations") == 0
        and receipt.get("torch_profiler_traces") == 0
        and receipt.get("formal_gate_evaluated") is False
        and receipt.get("formal_gate_changed") is False
        and receipt.get("formal_gate_rerun") is False
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("D6_cases_accessed") == 0
        and receipt.get("posthoc_profiling_execution_authorized") is True
        and receipt.get("seed0_training_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Unsafe R1 profiling preflight semantics")
    return receipt


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        raise RuntimeError(f"R1 profiling result already exists: {output_dir}")
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
    parser.add_argument("--preflight_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    authorization = verify_authorization(args.config_dir, args.authorization_dir)
    auth_path = args.authorization_dir / "profiling_execution_authorization_receipt.json"
    auth_hash = sha256_file(auth_path)
    preflight = verify_preflight(args.preflight_dir.resolve(), auth_hash)
    if not torch.cuda.is_available():
        raise RuntimeError("R1 latency post-hoc profiling requires CUDA")

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
        raise RuntimeError("R1 profiling state does not match frozen formal result")

    trace_fd, trace_name = tempfile.mkstemp(prefix="d6a_r1_trace_", suffix=".json")
    os.close(trace_fd)
    trace_tmp = Path(trace_name)
    try:
        profiled = profile_r1(model, descriptors, trace_tmp)
    finally:
        trace_tmp.unlink(missing_ok=True)
    after = tensor_state_hash(model)
    if before != after:
        raise RuntimeError("R1 post-hoc profiling changed model state")

    exact_summary = profiled["exact_summary"]
    attribution = profiled["attribution"]
    if not all(
        math.isfinite(value)
        for summary in exact_summary.values()
        for value in summary.values()
    ):
        raise RuntimeError("R1 profiling produced non-finite exact-path metrics")

    receipt = {
        "result_version": VERSION,
        "status": "D6A_R1_latency_posthoc_profiling_complete_observation_only",
        "authorization_receipt_sha256": auth_hash,
        "preflight_manifest_sha256": sha256_file(args.preflight_dir / "files.sha256"),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "torch_version": torch.__version__,
        "candidate": "R1",
        "descriptor_seed": 160610,
        "blocks": 3,
        "warmup_runs_per_block": 5,
        "timed_runs_per_block": 20,
        "timed_observations": len(profiled["exact_rows"]),
        "torch_profiler_traces": 1,
        "selected_indices": profiled["selected_indices"],
        "selected_indices_equal_reference": True,
        "state_hash_before": before,
        "state_hash_after": after,
        "exact_path_summary": exact_summary,
        "assignment_stage_summary": profiled["assignment_summary"],
        "attribution": attribution,
        "frozen_formal_R1_latency_ms_median": 292.5087884068489,
        "formal_gate_evaluated": False,
        "formal_gate_changed": False,
        "formal_gate_rerun": False,
        "causal_claim_authorized": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "R1_implementation_change_authorized": False,
        "optimized_alternative_benchmark_authorized": False,
        "R2_implementation_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "freeze_profiling_result_and_review_without_implementation_or_training",
    }
    report = (
        "# Mamba v1.6 D6-A R1 latency post-hoc profiling 冻结结果\n\n"
        f"- Frozen formal R1 median：292.508788407 ms；formal gate 未重跑或改变。\n"
        f"- Instrumented exact-path median：{exact_summary['exact_full_inference_ms']['median']:.9f} ms。\n"
        f"- Instrumented segment-sum median：{exact_summary['instrumented_segment_sum_ms']['median']:.9f} ms。\n"
        f"- Descriptive attribution：`{attribution['classification']}`。\n"
        f"- Leading category/share：`{attribution['leading_category']}` / {attribution['leading_share']:.6f}。\n"
        "- Timed observations/trace：60 / 1；全部索引与冻结路径一致。\n"
        "- Model state 前后不变；optimizer steps/model updates：0 / 0；D6 cases：0。\n"
        "- 本结果只描述冻结实现的时间归属，不构成因果证明或优化、R2、训练授权。\n"
        "- Training、seed-1、confirmation、D6-B、selection 与 sealed 数据继续锁定。\n"
    ).encode("utf-8")
    outputs = {
        "r1_exact_path_stage_metrics.csv": csv_bytes(profiled["exact_rows"]),
        "r1_assignment_stage_metrics.csv": csv_bytes(profiled["assignment_rows"]),
        "r1_operator_summary.csv": csv_bytes(profiled["operator_rows"]),
        "r1_torch_profiler_trace.json.gz": profiled["trace_payload"],
        "r1_latency_attribution_summary.json": canonical_json(
            {
                "exact_path_summary": exact_summary,
                "assignment_stage_summary": profiled["assignment_summary"],
                "attribution": attribution,
            }
        ),
        "posthoc_profiling_receipt.json": canonical_json(receipt),
        "posthoc_profiling_report_zh.md": report,
    }
    write_locked(outputs, args.output_dir.resolve())
    print(f"[saved] immutable R1 latency post-hoc profiling: {args.output_dir.resolve()}")
    print(f"[summary] attribution={attribution['classification']}")
    print(f"[summary] leading={attribution['leading_category']} share={attribution['leading_share']:.6f}")
    print("[locked] formal gate unchanged; training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
