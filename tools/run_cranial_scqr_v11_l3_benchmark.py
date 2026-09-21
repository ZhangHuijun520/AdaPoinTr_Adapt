#!/usr/bin/env python
"""Cranial-SCQR v1.1 L3 synthetic whole-network performance benchmark."""

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from models.cranial_scqr import (
    build_contact_support_labels,
    case_balanced_binary_cross_entropy,
)
from tools.run_cranial_scqr_v11_l2_preflight import (
    MODEL_SEED,
    SYNTHETIC_SEED,
    build_variant,
    state_sha256,
    synthetic_case,
    tensor_sha256,
)


ROOT = PROJECT_ROOT
CANDIDATES = ("B0", "QC")
MODES = ("inference_b1", "forward_backward_b8")
BLOCK_ORDERS = (
    ("B0", "QC"),
    ("QC", "B0"),
    ("B0", "QC"),
    ("QC", "B0"),
)
WARMUP_ITERATIONS = 20
TIMED_ITERATIONS = 50
BLOCKS = 4
DIAGNOSTIC_AUXILIARY_WEIGHT = 1.0
GIB = 1024 ** 3


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values, percentile_value):
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile_value))


def model_dense_output(model, query_features, coarse):
    batch, queries, _ = query_features.shape
    global_feature = model.increase_dim(
        query_features.transpose(1, 2)
    ).transpose(1, 2)
    global_feature = torch.max(global_feature, dim=1)[0]
    rebuild_feature = torch.cat(
        [
            global_feature.unsqueeze(-2).expand(-1, queries, -1),
            query_features,
            coarse,
        ],
        dim=-1,
    )
    if model.decoder_type != "fc":
        raise AssertionError("L3 frozen configuration requires the fc dense head")
    rebuild_feature = model.reduce_map(rebuild_feature)
    relative_xyz = model.decode_head(rebuild_feature)
    fine = relative_xyz + coarse.unsqueeze(-2)
    return fine.reshape(batch, -1, 3).contiguous()


def eval_forward_with_training_loss(model, variant, partial, target, scale):
    query_features, coarse, denoise_length, auxiliary = model.base_model(
        partial,
        epoch=20,
    )
    if denoise_length != 0:
        raise AssertionError("L3 eval-mode proxy must not create denoise queries")
    fine = model_dense_output(model, query_features, coarse)
    loss_coarse = model.loss_func(coarse, target)
    _, _, loss_fine = model.get_fine_loss_components(coarse, fine, target)
    loss = loss_coarse + loss_fine
    if variant == "QC":
        if auxiliary is None:
            raise AssertionError("QC did not expose auxiliary data from base_model")
        labels = build_contact_support_labels(
            partial,
            target,
            scale,
            auxiliary["knn32_indices"],
            rim_band_mm=2.0,
        )
        contact_loss = case_balanced_binary_cross_entropy(
            auxiliary["contact_logits"], labels.proxy_labels
        )
        loss = loss + DIAGNOSTIC_AUXILIARY_WEIGHT * contact_loss
    elif auxiliary is not None:
        raise AssertionError("B0 unexpectedly emitted SCQR auxiliary data")
    return loss, coarse, fine


def prepare_inputs(mode, device):
    partial, target, scale = synthetic_case(device)
    if mode == "forward_backward_b8":
        partial = partial.repeat(8, 1, 1).contiguous()
        target = target.repeat(8, 1, 1).contiguous()
        scale = scale.repeat(8).contiguous()
    return partial, target, scale


def execute_once(model, variant, mode, partial, target, scale):
    if mode == "inference_b1":
        with torch.no_grad():
            coarse, fine = model(partial)
        if tuple(coarse.shape) != (1, 256, 3):
            raise AssertionError("inference coarse shape mismatch")
        if tuple(fine.shape) != (1, 8192, 3):
            raise AssertionError("inference fine shape mismatch")
        return coarse, fine
    loss, coarse, fine = eval_forward_with_training_loss(
        model, variant, partial, target, scale
    )
    loss.backward()
    if not torch.isfinite(loss):
        raise AssertionError("nonfinite forward/backward proxy loss")
    return loss, coarse, fine


def validate_gradients(model):
    count = 0
    nonfinite = []
    for name, parameter in model.named_parameters():
        if parameter.grad is not None:
            count += 1
            if not torch.isfinite(parameter.grad).all():
                nonfinite.append(name)
    if nonfinite:
        raise AssertionError(f"nonfinite gradients: {nonfinite}")
    return count


def timed_block(model, variant, mode, block_index, partial, target, scale):
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    latencies_ms = []
    last_payload = None
    for iteration in range(TIMED_ITERATIONS):
        if mode == "forward_backward_b8":
            model.zero_grad(set_to_none=True)
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        last_payload = execute_once(model, variant, mode, partial, target, scale)
        end.record()
        end.synchronize()
        latencies_ms.append(float(start.elapsed_time(end)))
    gradient_count = (
        validate_gradients(model) if mode == "forward_backward_b8" else 0
    )
    allocated = int(torch.cuda.max_memory_allocated())
    reserved = int(torch.cuda.max_memory_reserved())
    for value in last_payload:
        if torch.is_tensor(value) and not torch.isfinite(value).all():
            raise AssertionError("timed block produced a nonfinite output")
    model.zero_grad(set_to_none=True)
    return {
        "candidate": variant,
        "mode": mode,
        "block": block_index,
        "iterations": TIMED_ITERATIONS,
        "latencies_ms": latencies_ms,
        "median_ms": float(statistics.median(latencies_ms)),
        "p95_ms": percentile(latencies_ms, 95),
        "peak_allocated_bytes": allocated,
        "peak_reserved_bytes": reserved,
        "peak_allocated_gib": allocated / GIB,
        "peak_reserved_gib": reserved / GIB,
        "gradient_tensor_count": gradient_count,
    }


def warmup(model, variant, mode, partial, target, scale):
    for _ in range(WARMUP_ITERATIONS):
        if mode == "forward_backward_b8":
            model.zero_grad(set_to_none=True)
        execute_once(model, variant, mode, partial, target, scale)
    torch.cuda.synchronize()
    model.zero_grad(set_to_none=True)


def aggregate(blocks):
    summary = {}
    for mode in MODES:
        summary[mode] = {}
        for candidate in CANDIDATES:
            selected = [
                item
                for item in blocks
                if item["mode"] == mode and item["candidate"] == candidate
            ]
            if len(selected) != BLOCKS:
                raise AssertionError(
                    f"{mode}/{candidate}: expected {BLOCKS} completed blocks"
                )
            values = [value for item in selected for value in item["latencies_ms"]]
            summary[mode][candidate] = {
                "samples": len(values),
                "overall_median_ms": float(statistics.median(values)),
                "overall_p95_ms": percentile(values, 95),
                "block_median_ms": [item["median_ms"] for item in selected],
                "block_p95_ms": [item["p95_ms"] for item in selected],
                "peak_allocated_bytes_max": max(
                    item["peak_allocated_bytes"] for item in selected
                ),
                "peak_reserved_bytes_max": max(
                    item["peak_reserved_bytes"] for item in selected
                ),
                "peak_allocated_gib_max": max(
                    item["peak_allocated_gib"] for item in selected
                ),
                "peak_reserved_gib_max": max(
                    item["peak_reserved_gib"] for item in selected
                ),
            }
    return summary


def evaluate_gates(summary):
    modes = {}
    for mode in MODES:
        baseline = summary[mode]["B0"]
        candidate = summary[mode]["QC"]
        latency_ratio = (
            candidate["overall_median_ms"] / baseline["overall_median_ms"]
        )
        allocated_ratio = (
            candidate["peak_allocated_bytes_max"]
            / baseline["peak_allocated_bytes_max"]
        )
        absolute_peak = max(
            candidate["peak_allocated_gib_max"],
            baseline["peak_allocated_gib_max"],
        )
        checks = {
            "median_latency_ratio_le_1_50": latency_ratio <= 1.50,
            "peak_allocated_ratio_le_1_30": allocated_ratio <= 1.30,
            "absolute_peak_allocated_le_20_gib": absolute_peak <= 20.0,
        }
        modes[mode] = {
            "QC_over_B0_median_latency_ratio": latency_ratio,
            "QC_over_B0_peak_allocated_ratio": allocated_ratio,
            "absolute_peak_allocated_gib": absolute_peak,
            "checks": checks,
            "pass": all(checks.values()),
        }
    return {
        "thresholds": {
            "median_latency_ratio_max": 1.50,
            "peak_allocated_ratio_max": 1.30,
            "absolute_peak_allocated_gib_max": 20.0,
        },
        "modes": modes,
        "pass": all(value["pass"] for value in modes.values()),
    }


def run_benchmark(log, block_sink):
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("L3 requires CUBLAS_WORKSPACE_CONFIG=:4096:8")
    if not torch.cuda.is_available():
        raise RuntimeError("L3 requires CUDA")
    device = torch.device("cuda:0")
    torch.manual_seed(SYNTHETIC_SEED)
    torch.cuda.manual_seed_all(SYNTHETIC_SEED)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False

    models = {}
    initial_state = {}
    common_state = {}
    config_hashes = {}
    log("constructing B0 and QC on CPU with matched seeds")
    for candidate in CANDIDATES:
        auxiliary_weight = (
            DIAGNOSTIC_AUXILIARY_WEIGHT if candidate == "QC" else None
        )
        model, _, config_path = build_variant(
            candidate,
            torch.device("cpu"),
            auxiliary_loss_weight=auxiliary_weight,
        )
        model.eval()
        models[candidate] = model
        initial_state[candidate] = state_sha256(model)
        common_state[candidate] = state_sha256(model, exclude_scqr=True)
        config_hashes[candidate] = sha256_file(config_path)
    if common_state["B0"] != common_state["QC"]:
        raise AssertionError("B0/QC public initialization mismatch")

    blocks = []
    warmup_completed = {(mode, candidate): False for mode in MODES for candidate in CANDIDATES}
    input_hashes = {}
    for mode in MODES:
        partial, target, scale = prepare_inputs(mode, device)
        input_hashes[mode] = {
            "partial_sha256": tensor_sha256(partial),
            "target_sha256": tensor_sha256(target),
            "scale_sha256": tensor_sha256(scale),
            "partial_shape": list(partial.shape),
            "target_shape": list(target.shape),
        }
        for block_index, order in enumerate(BLOCK_ORDERS):
            for candidate in order:
                torch.cuda.empty_cache()
                model = models[candidate].to(device).eval()
                key = (mode, candidate)
                if not warmup_completed[key]:
                    log(
                        f"warmup {mode} {candidate}: "
                        f"{WARMUP_ITERATIONS} iterations"
                    )
                    warmup(model, candidate, mode, partial, target, scale)
                    warmup_completed[key] = True
                log(
                    f"timed block {block_index + 1}/{BLOCKS} "
                    f"{mode} {candidate}: {TIMED_ITERATIONS} iterations"
                )
                result = timed_block(
                    model,
                    candidate,
                    mode,
                    block_index,
                    partial,
                    target,
                    scale,
                )
                blocks.append(result)
                block_sink(result)
                log(
                    f"completed {mode} {candidate} block {block_index + 1}: "
                    f"median_ms={result['median_ms']:.6f} "
                    f"peak_allocated_gib={result['peak_allocated_gib']:.6f}"
                )
                model.zero_grad(set_to_none=True)
                models[candidate] = model.cpu()
                torch.cuda.synchronize()
                torch.cuda.empty_cache()
        del partial, target, scale
        torch.cuda.empty_cache()

    final_state = {candidate: state_sha256(model) for candidate, model in models.items()}
    state_unchanged = {
        candidate: initial_state[candidate] == final_state[candidate]
        for candidate in CANDIDATES
    }
    if not all(state_unchanged.values()):
        raise AssertionError(f"benchmark changed model state: {state_unchanged}")
    summary = aggregate(blocks)
    gates = evaluate_gates(summary)
    return {
        "device": {
            "type": str(device),
            "name": torch.cuda.get_device_name(device),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "dtype": "float32",
            "CUBLAS_WORKSPACE_CONFIG": os.environ["CUBLAS_WORKSPACE_CONFIG"],
        },
        "benchmark_contract": {
            "candidates": list(CANDIDATES),
            "modes": list(MODES),
            "block_orders": [list(order) for order in BLOCK_ORDERS],
            "warmup_iterations_per_candidate_mode": WARMUP_ITERATIONS,
            "timed_iterations_per_block": TIMED_ITERATIONS,
            "blocks_per_candidate_mode": BLOCKS,
            "total_full_model_forward_calls": 880,
            "total_full_model_backward_calls": 440,
            "optimizer_constructions": 0,
            "optimizer_steps": 0,
            "bncal_runs": 0,
            "dataset_payload_files_opened": 0,
            "formal_metric": "CUDA event elapsed time",
        },
        "synthetic_input": {
            "seed": SYNTHETIC_SEED,
            "model_seed": MODEL_SEED,
            "generator": "deterministic_fibonacci_sphere_plus_northern_cap",
            "hashes": input_hashes,
        },
        "configuration_sha256": config_hashes,
        "public_initialization_sha256": common_state,
        "state_sha256_before": initial_state,
        "state_sha256_after": final_state,
        "state_unchanged": state_unchanged,
        "blocks": [
            {key: value for key, value in item.items() if key != "latencies_ms"}
            for item in blocks
        ],
        "summary": summary,
        "resource_gates": gates,
        "interpretation": (
            "forward_backward_b8 is an eval-mode training-compute proxy, "
            "not a train-mode optimizer step"
        ),
        "diagnostic_auxiliary_loss_weight": DIAGNOSTIC_AUXILIARY_WEIGHT,
        "diagnostic_weight_is_calibration": False,
    }


def write_json(path, payload):
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def validate_frozen_protocol(protocol, output_dir):
    payload = json.loads(protocol.read_text(encoding="utf-8"))
    if payload.get("protocol_id") != "cranial-scqr-v1.1-L3-synthetic-performance-v1":
        raise AssertionError("unexpected L3 protocol_id")
    if payload.get("status") != "frozen_before_execution":
        raise AssertionError("L3 protocol is not frozen_before_execution")
    execution = payload.get("execution", {})
    if execution.get("allowed_runs") != 1:
        raise AssertionError("L3 protocol must authorize exactly one run")
    if execution.get("output_dir") != str(output_dir.relative_to(ROOT)):
        raise AssertionError("L3 output directory does not match frozen protocol")
    expected_contract = {
        "candidates": list(CANDIDATES),
        "modes": list(MODES),
        "block_orders": [list(order) for order in BLOCK_ORDERS],
        "warmup_iterations_per_candidate_mode": WARMUP_ITERATIONS,
        "timed_iterations_per_block": TIMED_ITERATIONS,
        "blocks_per_candidate_mode": BLOCKS,
        "total_full_model_forward_calls": 880,
        "total_full_model_backward_calls": 440,
        "optimizer_constructions": 0,
        "optimizer_steps": 0,
        "bncal_runs": 0,
        "dataset_manifest_files_opened": 0,
        "dataset_payload_files_opened": 0,
    }
    if payload.get("benchmark_contract") != expected_contract:
        raise AssertionError("L3 benchmark contract differs from runner constants")
    for item in payload.get("sha256_bindings", []):
        bound_path = ROOT / item["path"]
        if sha256_file(bound_path) != item["sha256"]:
            raise AssertionError(f"SHA256 binding mismatch: {item['path']}")
    prerequisite = payload.get("prerequisite_l2", {})
    receipt_path = ROOT / prerequisite["receipt"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "PASS":
        raise AssertionError("bound L2 prerequisite receipt is not PASS")
    return payload


def write_report(path, receipt):
    result = receipt.get("result", {})
    gates = result.get("resource_gates", {})
    summary = result.get("summary", {})
    lines = [
        "# Cranial-SCQR v1.1 L3 人工输入性能 benchmark",
        "",
        f"- 状态：**{receipt['status']}**",
        f"- run ID：`{receipt['run_id']}`",
        f"- protocol/amendment SHA256：`{receipt['protocol_sha256']}`",
        "- 数据 payload：0；optimizer 构造/step：0/0；BNCal：0。",
        "",
        "## 完整网络结果",
        "",
        "| 模式 | 候选 | overall median ms | overall P95 ms | peak allocated GiB |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        for candidate in CANDIDATES:
            value = summary.get(mode, {}).get(candidate)
            if value is not None:
                lines.append(
                    f"| {mode} | {candidate} | "
                    f"{value['overall_median_ms']:.6f} | "
                    f"{value['overall_p95_ms']:.6f} | "
                    f"{value['peak_allocated_gib_max']:.6f} |"
                )
    lines.extend(
        [
            "",
            "## 资源门槛",
            "",
            f"- 总门槛：`{gates.get('pass', 'NOT_EVALUATED')}`",
        ]
    )
    for mode, value in gates.get("modes", {}).items():
        lines.append(
            f"- {mode}：latency ratio="
            f"{value['QC_over_B0_median_latency_ratio']:.6f}，"
            f"allocated ratio={value['QC_over_B0_peak_allocated_ratio']:.6f}，"
            f"absolute peak={value['absolute_peak_allocated_gib']:.6f} GiB，"
            f"pass={value['pass']}。"
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "B=8 forward+backward 在 eval 模式下测量，是训练计算代理，"
            "不是 train-mode optimizer step。诊断 λ=1 不是校准结果。",
        ]
    )
    if receipt["status"] == "ERROR":
        lines.extend(["", "## 错误", "", "```text", receipt["error"], "```"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    protocol = args.protocol.resolve()
    output_dir = args.output_dir.resolve()
    validate_frozen_protocol(protocol, output_dir)
    if output_dir.exists():
        raise FileExistsError(f"refusing to reuse L3 output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    progress_path = output_dir / "progress.log"
    iterations_path = output_dir / "benchmark_iterations.csv"
    fieldnames = (
        "mode",
        "candidate",
        "block",
        "iteration",
        "latency_ms",
    )
    with iterations_path.open("w", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=fieldnames).writeheader()

    def log(message):
        line = f"[{utc_now()}] {message}"
        print(line, flush=True)
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def block_sink(block):
        with iterations_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            for iteration, latency in enumerate(block["latencies_ms"]):
                writer.writerow(
                    {
                        "mode": block["mode"],
                        "candidate": block["candidate"],
                        "block": block["block"],
                        "iteration": iteration,
                        "latency_ms": f"{latency:.9f}",
                    }
                )

    receipt = {
        "protocol_id": "cranial-scqr-v1.1-L3-synthetic-performance-v1",
        "protocol": str(protocol.relative_to(ROOT)),
        "protocol_sha256": sha256_file(protocol),
        "run_id": output_dir.name,
        "started_at_utc": utc_now(),
        "optimizer_constructions": 0,
        "optimizer_steps": 0,
        "bncal_runs": 0,
        "dataset_payload_files_opened": 0,
    }
    try:
        log("L3 synthetic performance benchmark started")
        result = run_benchmark(log, block_sink)
        status = "GATE_PASS" if result["resource_gates"]["pass"] else "GATE_FAIL"
        receipt.update(
            {
                "status": status,
                "finished_at_utc": utc_now(),
                "result": result,
            }
        )
    except Exception as exc:
        receipt.update(
            {
                "status": "ERROR",
                "finished_at_utc": utc_now(),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
        )
    write_json(output_dir / "l3_benchmark_receipt.json", receipt)
    if "result" in receipt:
        write_json(output_dir / "benchmark_summary.json", receipt["result"])
    else:
        write_json(
            output_dir / "benchmark_summary.json",
            {"status": "ERROR", "error": receipt["error"]},
        )
    write_report(output_dir / "l3_benchmark_report_zh.md", receipt)
    files = [
        progress_path,
        iterations_path,
        output_dir / "benchmark_summary.json",
        output_dir / "l3_benchmark_receipt.json",
        output_dir / "l3_benchmark_report_zh.md",
    ]
    with (output_dir / "files.sha256").open("w", encoding="ascii") as handle:
        for path in files:
            handle.write(f"{sha256_file(path)}  {path.name}\n")
    print(f"[{receipt['status']}] {output_dir}", flush=True)
    if receipt["status"] != "GATE_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
