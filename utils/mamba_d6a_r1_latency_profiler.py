"""Frozen observation-only R1 latency profiler for Mamba v1.6 D6-A."""

from __future__ import annotations

import gzip
import math
from pathlib import Path
import statistics
import time
from typing import Any, Callable, Dict, Iterable, Tuple

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from utils.mamba_d6a_efficiency import full_inference_once


BLOCKS = 3
WARMUP_RUNS_PER_BLOCK = 5
TIMED_RUNS_PER_BLOCK = 20
TOTAL_TIMED_OBSERVATIONS = 60
TRACE_SCHEDULE = {"wait": 1, "warmup": 1, "active": 5, "repeat": 1}
DOMINANT_SHARE_THRESHOLD = 0.5
SLOT_COUNT = 32
CANDIDATE_COUNT = 8192


def _sync(device: torch.device) -> None:
    torch.cuda.synchronize(device)


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


def _time_synchronized(device: torch.device, function: Callable[[], Any]) -> Tuple[Any, float]:
    _sync(device)
    start = time.perf_counter()
    result = function()
    _sync(device)
    return result, _elapsed_ms(start)


def validate_descriptors(descriptors: torch.Tensor) -> None:
    if not torch.is_tensor(descriptors) or descriptors.shape != (1, 8192, 27):
        raise ValueError("profiling descriptors must have shape (1, 8192, 27)")
    if descriptors.dtype != torch.float32 or descriptors.device.type != "cuda":
        raise ValueError("profiling descriptors must be CUDA float32")
    if not torch.isfinite(descriptors).all():
        raise ValueError("profiling descriptors must be finite")


def _percentile(values: Iterable[float], fraction: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("cannot summarize an empty series")
    position = (len(ordered) - 1) * fraction
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize(values: Iterable[float]) -> Dict[str, float]:
    series = [float(value) for value in values]
    if not series or not all(math.isfinite(value) and value >= 0.0 for value in series):
        raise RuntimeError("profiling metrics must be finite and non-negative")
    median = statistics.median(series)
    return {
        "minimum": min(series),
        "median": median,
        "p95": _percentile(series, 0.95),
        "maximum": max(series),
        "mad": statistics.median(abs(value - median) for value in series),
    }


def shadow_global_assignment(
    slot_logits: torch.Tensor,
    *,
    record_timings: bool,
) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, float]]:
    """Replay the frozen assignment with optional synchronized stage timing."""

    if not torch.is_tensor(slot_logits) or slot_logits.shape != (1, SLOT_COUNT, CANDIDATE_COUNT):
        raise ValueError("slot_logits must have shape (1, 32, 8192)")
    if not slot_logits.is_floating_point():
        raise ValueError("slot_logits must be floating point")
    device = slot_logits.device
    timings: Dict[str, float] = {}

    def measured(name: str, function: Callable[[], Any], *, gpu: bool = False) -> Any:
        if not record_timings:
            return function()
        if gpu:
            result, elapsed = _time_synchronized(device, function)
        else:
            start = time.perf_counter()
            result = function()
            elapsed = _elapsed_ms(start)
        timings[name] = elapsed
        return result

    def finite_validation() -> None:
        if not torch.isfinite(slot_logits).all():
            raise ValueError("slot_logits must be finite")

    measured("slot_logits_finite_validation_and_sync_ms", finite_validation, gpu=True)
    hard = measured("hard_tensor_gpu_allocation_ms", lambda: torch.zeros_like(slot_logits), gpu=True)

    def copy_to_host() -> np.ndarray:
        return slot_logits[0].detach().to("cpu", torch.float64).numpy()

    scores = measured("slot_logits_d2h_float64_numpy_ms", copy_to_host, gpu=True)
    candidate_indices = np.arange(CANDIDATE_COUNT, dtype=np.float64)
    epsilon = np.finfo(np.float64).eps
    adjusted = measured(
        "epsilon_tie_adjustment_cpu_ms",
        lambda: scores - epsilon * candidate_indices[None, :],
    )
    assignment = measured(
        "scipy_linear_sum_assignment_cpu_ms",
        lambda: linear_sum_assignment(adjusted, maximize=True),
    )
    row_indices, column_indices = assignment

    def check_assignment() -> np.ndarray:
        if row_indices.shape[0] != SLOT_COUNT or not np.array_equal(
            np.sort(row_indices), np.arange(SLOT_COUNT)
        ):
            raise RuntimeError("global assignment did not cover all slots")
        slot_to_candidate = np.empty(SLOT_COUNT, dtype=np.int64)
        slot_to_candidate[row_indices] = column_indices
        if np.unique(slot_to_candidate).size != SLOT_COUNT:
            raise RuntimeError("global assignment produced duplicate candidates")
        return slot_to_candidate

    slot_to_candidate = measured("assignment_integrity_checks_cpu_ms", check_assignment)
    columns = measured(
        "selected_indices_h2d_ms",
        lambda: torch.as_tensor(slot_to_candidate, device=device, dtype=torch.long),
        gpu=True,
    )
    rows = torch.arange(SLOT_COUNT, device=device)

    def scatter() -> None:
        hard[0, rows, columns] = 1.0

    measured("hard_scatter_gpu_ms", scatter, gpu=True)
    selected = measured(
        "selected_sort_and_stack_gpu_ms",
        lambda: torch.sort(columns).values.unsqueeze(0),
        gpu=True,
    )
    return hard, selected, timings


def _operator_rows(profiler: Any) -> list[dict[str, Any]]:
    rows = []
    for event in profiler.key_averages():
        self_device = float(
            getattr(event, "self_device_time_total", getattr(event, "self_cuda_time_total", 0.0))
        )
        device_total = float(
            getattr(event, "device_time_total", getattr(event, "cuda_time_total", 0.0))
        )
        rows.append(
            {
                "operator": str(event.key),
                "count": int(event.count),
                "self_cpu_time_total_us": float(event.self_cpu_time_total),
                "cpu_time_total_us": float(event.cpu_time_total),
                "self_cuda_time_total_us": self_device,
                "cuda_time_total_us": device_total,
                "cpu_memory_usage_bytes": int(getattr(event, "cpu_memory_usage", 0)),
                "cuda_memory_usage_bytes": int(getattr(event, "device_memory_usage", 0)),
            }
        )
    rows.sort(
        key=lambda row: (
            -row["self_cpu_time_total_us"],
            -row["self_cuda_time_total_us"],
            row["operator"],
        )
    )
    return rows


def run_torch_trace(
    model: torch.nn.Module,
    descriptors: torch.Tensor,
    trace_path: Path,
) -> Tuple[bytes, list[dict[str, Any]]]:
    schedule = torch.profiler.schedule(**TRACE_SCHEDULE)
    activities = [torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA]
    with torch.profiler.profile(
        activities=activities,
        schedule=schedule,
        record_shapes=True,
        profile_memory=True,
        with_stack=False,
    ) as profiler:
        for _ in range(sum(TRACE_SCHEDULE[key] for key in ("wait", "warmup", "active"))):
            with torch.profiler.record_function("r1_full_inference_exact"):
                full_inference_once("R1", model, descriptors)
            profiler.step()
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    profiler.export_chrome_trace(str(trace_path))
    trace_payload = gzip.compress(trace_path.read_bytes(), compresslevel=9, mtime=0)
    return trace_payload, _operator_rows(profiler)


def profile_r1(
    model: torch.nn.Module,
    descriptors: torch.Tensor,
    trace_path: Path,
) -> Dict[str, Any]:
    validate_descriptors(descriptors)
    if not isinstance(model, torch.nn.Module):
        raise TypeError("model must be a torch module")
    model.eval()
    device = descriptors.device
    exact_rows: list[dict[str, Any]] = []
    assignment_rows: list[dict[str, Any]] = []
    reference: torch.Tensor | None = None

    with torch.inference_mode():
        for block in range(1, BLOCKS + 1):
            for _ in range(WARMUP_RUNS_PER_BLOCK):
                current = full_inference_once("R1", model, descriptors).detach().cpu()
                if reference is None:
                    reference = current
                elif not torch.equal(reference, current):
                    raise RuntimeError("R1 exact-path selector changed during warmup")

            for iteration in range(1, TIMED_RUNS_PER_BLOCK + 1):
                exact_selected, exact_ms = _time_synchronized(
                    device, lambda: full_inference_once("R1", model, descriptors)
                )
                exact_cpu = exact_selected.detach().cpu()
                if reference is None or not torch.equal(reference, exact_cpu):
                    raise RuntimeError("R1 exact-path selector changed during profiling")

                _, descriptor_validation_ms = _time_synchronized(
                    device, lambda: validate_descriptors(descriptors)
                )
                outputs, model_forward_ms = _time_synchronized(
                    device, lambda: model(descriptors)
                )
                _, shadow_selected, stage_times = shadow_global_assignment(
                    outputs["slot_logits"], record_timings=True
                )
                shadow_cpu = shadow_selected.detach().cpu()
                if not torch.equal(reference, shadow_cpu):
                    raise RuntimeError("Instrumented assignment changed selected indices")
                segmented_ms = descriptor_validation_ms + model_forward_ms + sum(stage_times.values())
                exact_rows.append(
                    {
                        "block": block,
                        "iteration": iteration,
                        "exact_full_inference_ms": exact_ms,
                        "descriptor_validation_ms": descriptor_validation_ms,
                        "R1_model_forward_ms": model_forward_ms,
                        "instrumented_segment_sum_ms": segmented_ms,
                        "selected_indices_equal_reference": True,
                    }
                )
                assignment_rows.append(
                    {"block": block, "iteration": iteration, **stage_times}
                )

        trace_payload, operator_rows = run_torch_trace(model, descriptors, trace_path)

    if len(exact_rows) != TOTAL_TIMED_OBSERVATIONS:
        raise RuntimeError("R1 timed-observation count drifted")
    if len(assignment_rows) != TOTAL_TIMED_OBSERVATIONS:
        raise RuntimeError("R1 assignment-observation count drifted")

    exact_summary = {
        name: summarize(row[name] for row in exact_rows)
        for name in (
            "exact_full_inference_ms",
            "descriptor_validation_ms",
            "R1_model_forward_ms",
            "instrumented_segment_sum_ms",
        )
    }
    assignment_names = [
        "slot_logits_finite_validation_and_sync_ms",
        "hard_tensor_gpu_allocation_ms",
        "slot_logits_d2h_float64_numpy_ms",
        "epsilon_tie_adjustment_cpu_ms",
        "scipy_linear_sum_assignment_cpu_ms",
        "assignment_integrity_checks_cpu_ms",
        "selected_indices_h2d_ms",
        "hard_scatter_gpu_ms",
        "selected_sort_and_stack_gpu_ms",
    ]
    assignment_summary = {
        name: summarize(row[name] for row in assignment_rows) for name in assignment_names
    }

    categories = {
        "gpu_model_forward": exact_summary["R1_model_forward_ms"]["median"],
        "validation_or_cuda_sync": (
            exact_summary["descriptor_validation_ms"]["median"]
            + assignment_summary["slot_logits_finite_validation_and_sync_ms"]["median"]
        ),
        "device_to_host_transfer": assignment_summary["slot_logits_d2h_float64_numpy_ms"]["median"],
        "scipy_global_assignment": assignment_summary["scipy_linear_sum_assignment_cpu_ms"]["median"],
        "gpu_reconstruction": sum(
            assignment_summary[name]["median"]
            for name in (
                "hard_tensor_gpu_allocation_ms",
                "selected_indices_h2d_ms",
                "hard_scatter_gpu_ms",
                "selected_sort_and_stack_gpu_ms",
            )
        ),
        "cpu_assignment_other": sum(
            assignment_summary[name]["median"]
            for name in (
                "epsilon_tie_adjustment_cpu_ms",
                "assignment_integrity_checks_cpu_ms",
            )
        ),
    }
    denominator = sum(categories.values())
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise RuntimeError("Invalid attribution denominator")
    shares = {name: value / denominator for name, value in categories.items()}
    leading = max(shares, key=shares.get)
    label_map = {
        "gpu_model_forward": "gpu_model_forward_dominant",
        "validation_or_cuda_sync": "validation_or_cuda_sync_dominant",
        "device_to_host_transfer": "device_to_host_transfer_dominant",
        "scipy_global_assignment": "scipy_global_assignment_dominant",
        "gpu_reconstruction": "gpu_reconstruction_dominant",
        "cpu_assignment_other": "mixed_no_single_dominant_stage",
    }
    label = (
        label_map[leading]
        if shares[leading] >= DOMINANT_SHARE_THRESHOLD
        else "mixed_no_single_dominant_stage"
    )
    attribution = {
        "classification": label,
        "dominant_share_threshold": DOMINANT_SHARE_THRESHOLD,
        "leading_category": leading,
        "leading_share": shares[leading],
        "category_median_ms": categories,
        "category_shares": shares,
        "instrumented_median_denominator_ms": denominator,
        "formal_R1_latency_ms_median_frozen": 292.5087884068489,
        "formal_gate_changed": False,
        "formal_gate_rerun": False,
        "causal_claim_authorized": False,
        "optimized_alternative_benchmark_authorized": False,
    }
    return {
        "exact_rows": exact_rows,
        "assignment_rows": assignment_rows,
        "operator_rows": operator_rows,
        "trace_payload": trace_payload,
        "exact_summary": exact_summary,
        "assignment_summary": assignment_summary,
        "attribution": attribution,
        "selected_indices": reference.tolist()[0] if reference is not None else [],
    }


__all__ = [
    "BLOCKS",
    "DOMINANT_SHARE_THRESHOLD",
    "TIMED_RUNS_PER_BLOCK",
    "TOTAL_TIMED_OBSERVATIONS",
    "TRACE_SCHEDULE",
    "WARMUP_RUNS_PER_BLOCK",
    "profile_r1",
    "shadow_global_assignment",
    "summarize",
    "validate_descriptors",
]
