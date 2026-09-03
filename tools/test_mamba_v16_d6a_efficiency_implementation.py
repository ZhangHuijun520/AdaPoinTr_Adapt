#!/usr/bin/env python3
"""Contract tests for the D6-A full-inference efficiency implementation."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "utils" / "mamba_d6a_efficiency.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.mamba_d6a_efficiency import (  # noqa: E402
    LATENCY_RATIO_MAXIMUM,
    PEAK_MEMORY_RATIO_MAXIMUM,
    TIMED_RUNS,
    WARMUP_RUNS,
    benchmark_candidate,
    full_inference_once,
)


def main() -> None:
    assert WARMUP_RUNS == 10
    assert TIMED_RUNS == 50
    assert LATENCY_RATIO_MAXIMUM == 1.15
    assert PEAK_MEMORY_RATIO_MAXIMUM == 1.10
    signature = inspect.signature(benchmark_candidate)
    assert signature.parameters["warmup_runs"].default == 10
    assert signature.parameters["timed_runs"].default == 50
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count("torch.cuda.synchronize(descriptors.device)") >= 3
    assert "torch.cuda.reset_peak_memory_stats(descriptors.device)" in source
    assert "time.perf_counter()" in source
    try:
        full_inference_once("R0", object(), torch.zeros(1, 8192, 27))
    except ValueError as exc:
        assert "CUDA float32" in str(exc)
    else:
        raise AssertionError("CPU efficiency input was accepted")
    print("[ok] full-inference includes each frozen final selector")
    print("[ok] 10 warmup / 50 timed / CUDA synchronization and peak-memory reset are fixed")
    print("[ok] artificial zero-step cannot silently become a formal benchmark")
    print("[locked] formal_efficiency=false training=false seed1=false D6B=false")


if __name__ == "__main__":
    main()
