"""Frozen full-inference efficiency helpers for Mamba v1.6 D6-A."""

from __future__ import annotations

import statistics
import time
from typing import Any, Dict

import torch

from utils.mamba_d5a_proposal import select_deterministic_top32


WARMUP_RUNS = 10
TIMED_RUNS = 50
LATENCY_RATIO_MAXIMUM = 1.15
PEAK_MEMORY_RATIO_MAXIMUM = 1.10


def _validate_input(descriptors: torch.Tensor) -> None:
    if not torch.is_tensor(descriptors) or descriptors.shape != (1, 8192, 27):
        raise ValueError("efficiency descriptors must have shape (1, 8192, 27)")
    if descriptors.dtype != torch.float32 or descriptors.device.type != "cuda":
        raise ValueError("efficiency descriptors must be CUDA float32")
    if not torch.isfinite(descriptors).all():
        raise ValueError("efficiency descriptors must be finite")


def full_inference_once(
    candidate: str,
    model: torch.nn.Module,
    descriptors: torch.Tensor,
) -> torch.Tensor:
    """Run the candidate head and its frozen final selector exactly once."""

    _validate_input(descriptors)
    if candidate == "R0":
        selected = select_deterministic_top32(model(descriptors))
    elif candidate == "R1":
        selected = model.infer_indices(descriptors)
    else:
        raise ValueError(f"unsupported D6-A candidate: {candidate}")
    if selected.shape != (1, 32) or selected.unique().numel() != 32:
        raise RuntimeError(f"{candidate} full inference did not return 32 unique indices")
    if selected.dtype != torch.long:
        raise RuntimeError(f"{candidate} selector index dtype drifted")
    return selected


def benchmark_candidate(
    candidate: str,
    model: torch.nn.Module,
    descriptors: torch.Tensor,
    *,
    warmup_runs: int = WARMUP_RUNS,
    timed_runs: int = TIMED_RUNS,
) -> Dict[str, Any]:
    """Measure frozen batch-1 full-inference latency and peak CUDA memory."""

    _validate_input(descriptors)
    if int(warmup_runs) != WARMUP_RUNS or int(timed_runs) != TIMED_RUNS:
        raise ValueError("formal efficiency requires exactly 10 warmup and 50 timed runs")
    model.eval()
    reference = None
    timings = []
    with torch.inference_mode():
        for _ in range(WARMUP_RUNS):
            current = full_inference_once(candidate, model, descriptors)
            if reference is None:
                reference = current.detach().cpu()
            elif not torch.equal(reference, current.detach().cpu()):
                raise RuntimeError(f"{candidate} selector is not deterministic")
        torch.cuda.synchronize(descriptors.device)
        torch.cuda.reset_peak_memory_stats(descriptors.device)
        for _ in range(TIMED_RUNS):
            torch.cuda.synchronize(descriptors.device)
            start = time.perf_counter()
            current = full_inference_once(candidate, model, descriptors)
            torch.cuda.synchronize(descriptors.device)
            timings.append((time.perf_counter() - start) * 1000.0)
            if not torch.equal(reference, current.detach().cpu()):
                raise RuntimeError(f"{candidate} selector changed during timing")
        peak = int(torch.cuda.max_memory_allocated(descriptors.device))
    if len(timings) != TIMED_RUNS or not all(value > 0 for value in timings):
        raise RuntimeError("formal efficiency timing contract failed")
    return {
        "candidate": candidate,
        "warmup_runs": WARMUP_RUNS,
        "timed_runs": TIMED_RUNS,
        "batch_size": 1,
        "dtype": "float32",
        "latency_ms_median": statistics.median(timings),
        "latency_ms_minimum": min(timings),
        "latency_ms_maximum": max(timings),
        "peak_gpu_memory_bytes": peak,
        "selected_indices": reference.tolist()[0],
    }


__all__ = [
    "LATENCY_RATIO_MAXIMUM",
    "PEAK_MEMORY_RATIO_MAXIMUM",
    "TIMED_RUNS",
    "WARMUP_RUNS",
    "benchmark_candidate",
    "full_inference_once",
]
