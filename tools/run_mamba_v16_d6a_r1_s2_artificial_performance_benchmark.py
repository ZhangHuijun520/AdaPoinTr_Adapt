#!/usr/bin/env python3
"""Run one authorized frozen-suite S0-versus-S2 artificial benchmark."""

from __future__ import annotations

import os

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import csv
import gc
import hashlib
import importlib.util
import io
import json
import platform
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping

import numpy as np
import scipy
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.verify_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_authorization import (  # noqa: E402
    sha256_file,
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

VERSION = "mamba-v16-d6a-r1-s2-artificial-performance-benchmark-v1"
OBS_FIELDS = ["block", "case_index", "family", "seed", "expected_route", "candidate", "order_position", "latency_ns", "latency_ms"]
BLOCK_FIELDS = ["block", "cases", "S0_total_ms", "S2_total_ms", "S2_over_S0_ratio", "strictly_below_1"]
STRATUM_FIELDS = [
    "stratum_type", "stratum", "cases", "paired_observations", "S0_min_ms", "S0_median_ms", "S0_mean_ms", "S0_p95_ms", "S0_max_ms",
    "S2_min_ms", "S2_median_ms", "S2_mean_ms", "S2_p95_ms", "S2_max_ms", "aggregate_S2_over_S0_ratio",
    "paired_ratio_median", "paired_ratio_p95", "paired_difference_ms_mean",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def csv_bytes(rows: list[dict[str, Any]], fieldnames: list[str]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def verify_manifest(manifest: Path, root: Path) -> int:
    require(manifest.is_file(), f"Missing preflight manifest: {manifest}")
    resolved = root.resolve()
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        wanted, relative = line.split(maxsplit=1)
        posix = PurePosixPath(relative.lstrip("*"))
        require(not posix.is_absolute() and ".." not in posix.parts, f"Unsafe preflight path: {relative}")
        path = root.joinpath(*posix.parts).resolve()
        require(path == resolved or resolved in path.parents, f"Preflight path escaped root: {path}")
        require(path.is_file() and sha256_file(path) == wanted.lower(), f"Preflight artifact drifted: {path}")
        count += 1
    return count


def verify_preflight(preflight_dir: Path, authorization_dir: Path) -> dict[str, Any]:
    require(verify_manifest(preflight_dir / "files.sha256", preflight_dir) == 3, "Preflight manifest count drifted")
    receipt = json.loads((preflight_dir / "authorization_preflight_receipt.json").read_text(encoding="utf-8"))
    auth_path = authorization_dir / "benchmark_execution_authorization_receipt.json"
    require(receipt["status"] == "D6A_R1_S2_artificial_performance_benchmark_authorization_preflight_passed", "Preflight status drifted")
    require(receipt["authorization_receipt_sha256"] == sha256_file(auth_path), "Preflight authorization lineage drifted")
    probe = receipt["probe"]
    for key in ("slot_to_candidate_exact", "sorted_selected_indices_exact", "hard_assignment_exact", "adjusted_objective_exact", "input_unchanged", "outputs_finite"):
        require(probe[key] is True, f"Preflight probe drifted: {key}")
    require(probe["S2_route"] == "certified_fast_path" and probe["selected_unique"] == 32, "Preflight route drifted")
    for key in ("correctness_replay_cases", "warmup_calls", "timed_calls", "measurement_blocks", "torch_profiler_traces", "optimizer_steps", "model_updates", "D6_cases_accessed"):
        require(receipt[key] == 0, f"Preflight zero-count boundary drifted: {key}")
    require(receipt["formal_efficiency_rerun_authorized"] is False and receipt["seed0_training_authorized"] is False, "Preflight escalated permission")
    return receipt


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    outputs = dict(outputs)
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    ).encode("ascii")
    require(not output_dir.exists(), f"S2 benchmark result already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            (working / name).write_bytes(payload)
        working.replace(output_dir)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise


def make_logits(case: Mapping[str, Any], device: torch.device) -> tuple[np.ndarray, torch.Tensor]:
    scores = artificial_scores(case["family"], int(case["seed"]))
    return scores, torch.from_numpy(scores).unsqueeze(0).to(device)


def run_s0(logits: torch.Tensor) -> Any:
    return frozen_reference_diagnostics(logits)


def run_s2(logits: torch.Tensor) -> Any:
    return s2_certified_fast_path_assignment(logits)


def correctness_replay(cases: list[dict[str, Any]], device: torch.device) -> tuple[list[dict[str, Any]], bool]:
    rows = []
    for case in cases:
        scores, logits = make_logits(case, device)
        before = sha256_bytes(scores.tobytes())
        with torch.inference_mode():
            s0_hard, s0_selected, s0_slots, s0_objective = run_s0(logits)
            s2 = run_s2(logits)
        row = {
            **case,
            "slot_to_candidate_exact": torch.equal(s0_slots, s2.slot_to_candidate),
            "sorted_selected_indices_exact": torch.equal(s0_selected, s2.selected_indices),
            "hard_assignment_exact": torch.equal(s0_hard, s2.hard_assignment),
            "adjusted_objective_exact": bool(s0_objective == s2.adjusted_objective),
            "input_unchanged": before == sha256_bytes(logits.detach().cpu().numpy()[0].tobytes()),
            "route_exact": s2.route == case["expected_route"],
            "fallback_reason_exact": s2.fallback_reason == case["expected_fallback_reason"],
            "selected_unique": int(s2.selected_indices.unique().numel()),
        }
        row["all_exact"] = all(row[key] for key in (
            "slot_to_candidate_exact", "sorted_selected_indices_exact", "hard_assignment_exact", "adjusted_objective_exact",
            "input_unchanged", "route_exact", "fallback_reason_exact",
        )) and row["selected_unique"] == 32
        rows.append(row)
    routes = Counter(row["expected_route"] for row in rows if row["route_exact"])
    reasons = Counter(row["expected_fallback_reason"] for row in rows if row["expected_route"] == "fallback_s0" and row["fallback_reason_exact"])
    passed = (
        len(rows) == 168
        and all(row["all_exact"] for row in rows)
        and routes == Counter({"certified_fast_path": 96, "fallback_s0": 72})
        and reasons == Counter({"cutoff_tie_or_near_tie": 32, "global_optimum_not_certified_unique": 40})
    )
    return rows, passed


def candidate_order(block: int, case_index: int) -> tuple[str, str]:
    return ("S0", "S2") if (block + case_index) % 2 == 0 else ("S2", "S0")


def timed_call(function: Callable[[torch.Tensor], Any], logits: torch.Tensor) -> tuple[Any, int]:
    torch.cuda.synchronize(logits.device)
    start = time.perf_counter_ns()
    output = function(logits)
    torch.cuda.synchronize(logits.device)
    elapsed = time.perf_counter_ns() - start
    require(elapsed > 0, "Non-positive timed observation")
    return output, elapsed


def percentile(values: np.ndarray, quantile: float) -> float:
    return float(np.percentile(values, quantile, method="linear"))


def summarize_stratum(name_type: str, name: str, cases: list[dict[str, Any]], observations: list[dict[str, Any]]) -> dict[str, Any]:
    allowed = {case["case_index"] for case in cases}
    selected = [row for row in observations if row["case_index"] in allowed]
    pairs: dict[tuple[int, int], dict[str, float]] = {}
    for row in selected:
        pairs.setdefault((row["block"], row["case_index"]), {})[row["candidate"]] = float(row["latency_ms"])
    require(all(set(pair) == {"S0", "S2"} for pair in pairs.values()), f"Incomplete timing pair: {name_type}/{name}")
    s0 = np.asarray([pair["S0"] for pair in pairs.values()], dtype=np.float64)
    s2 = np.asarray([pair["S2"] for pair in pairs.values()], dtype=np.float64)
    ratio = s2 / s0
    difference = s2 - s0
    return {
        "stratum_type": name_type,
        "stratum": name,
        "cases": len(allowed),
        "paired_observations": len(pairs),
        "S0_min_ms": float(np.min(s0)), "S0_median_ms": float(np.median(s0)), "S0_mean_ms": float(np.mean(s0)), "S0_p95_ms": percentile(s0, 95), "S0_max_ms": float(np.max(s0)),
        "S2_min_ms": float(np.min(s2)), "S2_median_ms": float(np.median(s2)), "S2_mean_ms": float(np.mean(s2)), "S2_p95_ms": percentile(s2, 95), "S2_max_ms": float(np.max(s2)),
        "aggregate_S2_over_S0_ratio": float(np.sum(s2) / np.sum(s0)),
        "paired_ratio_median": float(np.median(ratio)),
        "paired_ratio_p95": percentile(ratio, 95),
        "paired_difference_ms_mean": float(np.mean(difference)),
    }


def evaluate_gate(block_rows: list[dict[str, Any]], stratum_rows: list[dict[str, Any]], observations: list[dict[str, Any]], gate: Mapping[str, Any]) -> dict[str, Any]:
    block_ratios = [float(row["S2_over_S0_ratio"]) for row in block_rows]
    lookup = {(row["stratum_type"], row["stratum"]): row for row in stratum_rows}
    fast_ratio = float(lookup[("route", "certified_fast_path")]["aggregate_S2_over_S0_ratio"])
    fallback_ratio = float(lookup[("route", "fallback_s0")]["aggregate_S2_over_S0_ratio"])
    finite_positive = len(observations) == gate["timed_observation_rows_required"] and all(
        np.isfinite(float(row["latency_ms"])) and float(row["latency_ms"]) > 0 for row in observations
    )
    median_block_ratio = float(np.median(np.asarray(block_ratios, dtype=np.float64)))
    checks = {
        "finite_positive_and_count_passed": finite_positive,
        "median_overall_block_ratio_passed": median_block_ratio <= gate["median_of_3_overall_block_ratios_maximum"],
        "every_block_ratio_passed": all(value < gate["each_overall_block_ratio_must_be_strictly_less_than"] for value in block_ratios),
        "fast_path_ratio_passed": fast_ratio <= gate["aggregate_fast_path_ratio_maximum"],
        "fallback_ratio_passed": fallback_ratio <= gate["aggregate_fallback_ratio_maximum"],
    }
    return {
        "median_overall_block_ratio": median_block_ratio,
        "individual_block_ratios": block_ratios,
        "aggregate_fast_path_ratio": fast_ratio,
        "aggregate_fallback_ratio": fallback_ratio,
        **checks,
        "all_performance_gates_passed": all(checks.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--preflight_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    authorization, config = verify_authorization(args.config_dir, args.authorization_dir)
    preflight = verify_preflight(args.preflight_dir.resolve(), args.authorization_dir.resolve())
    require(not args.output_dir.exists(), f"Immutable benchmark result already exists: {args.output_dir}")
    require(torch.cuda.is_available(), "S2 artificial benchmark requires CUDA")
    torch.set_num_threads(1)
    require(torch.get_num_threads() == 1, "PyTorch CPU thread count drifted")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        require(os.environ.get(name) == "1", f"CPU thread environment drifted: {name}")
    device = torch.device("cuda:0")
    cases = config["cases"]
    runtime = config["runtime"]
    gate = config["performance_gate"]
    torch.cuda.synchronize(device)
    memory_before = {"allocated": torch.cuda.memory_allocated(device), "reserved": torch.cuda.memory_reserved(device)}

    replay_rows, replay_passed = correctness_replay(cases, device)
    observations: list[dict[str, Any]] = []
    block_rows: list[dict[str, Any]] = []
    stratum_rows: list[dict[str, Any]] = []
    warmup_calls = 0
    gate_result: dict[str, Any] = {"all_performance_gates_passed": False}

    if replay_passed:
        first_by_family = {}
        for case in cases:
            first_by_family.setdefault(case["family"], case)
        anchors = list(first_by_family.values())
        require(len(anchors) == runtime["warmup_anchor_families"] == 7, "Warmup anchor count drifted")
        functions = {"S0": run_s0, "S2": run_s2}
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            with torch.inference_mode():
                for warmup_round in range(runtime["warmup_rounds"]):
                    for family_index, case in enumerate(anchors):
                        _, logits = make_logits(case, device)
                        order = ("S0", "S2") if (warmup_round + family_index) % 2 == 0 else ("S2", "S0")
                        for candidate in order:
                            torch.cuda.synchronize(device)
                            output = functions[candidate](logits)
                            torch.cuda.synchronize(device)
                            if candidate == "S2":
                                require(output.route == case["expected_route"], "Warmup S2 route drifted")
                            warmup_calls += 1
                            del output
                require(warmup_calls == runtime["warmup_calls_total"] == 28, "Warmup call count drifted")

                torch.cuda.reset_peak_memory_stats(device)
                for block in range(runtime["measurement_blocks"]):
                    for case in cases:
                        _, logits = make_logits(case, device)
                        for order_position, candidate in enumerate(candidate_order(block, case["case_index"])):
                            output, elapsed_ns = timed_call(functions[candidate], logits)
                            if candidate == "S2":
                                require(output.route == case["expected_route"] and output.fallback_reason == case["expected_fallback_reason"], "Timed S2 route drifted")
                            observations.append({
                                "block": block,
                                "case_index": case["case_index"],
                                "family": case["family"],
                                "seed": case["seed"],
                                "expected_route": case["expected_route"],
                                "candidate": candidate,
                                "order_position": order_position,
                                "latency_ns": elapsed_ns,
                                "latency_ms": elapsed_ns / 1_000_000.0,
                            })
                            del output
        finally:
            if gc_was_enabled:
                gc.enable()

        require(len(observations) == runtime["timed_observation_rows"] == 1008, "Timed observation count drifted")
        for block in range(runtime["measurement_blocks"]):
            block_obs = [row for row in observations if row["block"] == block]
            s0_total = sum(float(row["latency_ms"]) for row in block_obs if row["candidate"] == "S0")
            s2_total = sum(float(row["latency_ms"]) for row in block_obs if row["candidate"] == "S2")
            ratio = s2_total / s0_total
            block_rows.append({"block": block, "cases": 168, "S0_total_ms": s0_total, "S2_total_ms": s2_total, "S2_over_S0_ratio": ratio, "strictly_below_1": ratio < 1.0})
        stratum_rows.append(summarize_stratum("overall", "all", cases, observations))
        for route in ("certified_fast_path", "fallback_s0"):
            stratum_rows.append(summarize_stratum("route", route, [case for case in cases if case["expected_route"] == route], observations))
        for family in dict.fromkeys(case["family"] for case in cases):
            stratum_rows.append(summarize_stratum("family", family, [case for case in cases if case["family"] == family], observations))
        gate_result = evaluate_gate(block_rows, stratum_rows, observations, gate)

    torch.cuda.synchronize(device)
    memory_after = {
        "allocated": torch.cuda.memory_allocated(device),
        "reserved": torch.cuda.memory_reserved(device),
        "peak_allocated_during_measurement": torch.cuda.max_memory_allocated(device) if replay_passed else None,
        "peak_reserved_during_measurement": torch.cuda.max_memory_reserved(device) if replay_passed else None,
    }
    verify_authorization(args.config_dir, args.authorization_dir)

    if not replay_passed:
        status = config["result_contract"]["correctness_replay_failure_status"]
        next_step = "freeze_archive_and_stop_S2_while_retaining_S0"
    elif gate_result["all_performance_gates_passed"]:
        status = config["result_contract"]["performance_positive_status"]
        next_step = config["result_contract"]["positive_next_step"]
    else:
        status = config["result_contract"]["performance_negative_status"]
        next_step = config["result_contract"]["negative_next_step"]

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "scipy": scipy.__version__,
        "numpy": np.__version__,
        "CUDA_device": torch.cuda.get_device_name(device),
        "CPU_threads": {name: os.environ[name] for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
        "torch_num_threads": torch.get_num_threads(),
        "CUDA_memory_before": memory_before,
        "CUDA_memory_after": memory_after,
    }
    replay_summary = {
        "cases": len(replay_rows),
        "all_exact": sum(row["all_exact"] for row in replay_rows),
        "certified_fast_path": sum(row["expected_route"] == "certified_fast_path" and row["route_exact"] for row in replay_rows),
        "fallback_s0": sum(row["expected_route"] == "fallback_s0" and row["route_exact"] for row in replay_rows),
        "passed": replay_passed,
    }
    auth_path = args.authorization_dir / "benchmark_execution_authorization_receipt.json"
    preflight_path = args.preflight_dir / "authorization_preflight_receipt.json"
    receipt = {
        "benchmark_version": VERSION,
        "status": status,
        "authorization_receipt_sha256": sha256_file(auth_path),
        "preflight_receipt_sha256": sha256_file(preflight_path),
        "correctness_replay": replay_summary,
        "warmup_calls": warmup_calls,
        "timed_observation_rows": len(observations),
        "measurement_blocks": len(block_rows),
        "performance_gate": gate_result,
        "implementation_state_unchanged": True,
        "outliers_removed": 0,
        "slow_observations_retried": 0,
        "torch_profiler_traces": 0,
        "formal_R0_denominator_used": False,
        "formal_efficiency_thresholds_evaluated": False,
        "formal_efficiency_rerun": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "R1_production_implementation_change_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": next_step,
    }
    report = (
        "# Mamba v1.6 D6-A R1 S2 artificial performance benchmark 结果\n\n"
        f"- Status：`{status}`。\n"
        f"- Pre-timing correctness replay：{replay_summary['all_exact']}/168；passed={replay_passed}。\n"
        f"- Warmup/timed observations/blocks：{warmup_calls} / {len(observations)} / {len(block_rows)}。\n"
        f"- Median overall block ratio：{gate_result.get('median_overall_block_ratio', 'not-run')}。\n"
        f"- Fast/fallback aggregate ratio：{gate_result.get('aggregate_fast_path_ratio', 'not-run')} / {gate_result.get('aggregate_fallback_ratio', 'not-run')}。\n"
        f"- All performance gates passed：{gate_result['all_performance_gates_passed']}。\n"
        "- Outlier removal/retry/profiler：0 / 0 / 0。\n"
        "- Formal gate 未评估、未重跑；optimizer/model updates/D6 cases：0 / 0 / 0。\n"
        f"- Next：`{next_step}`。\n"
    ).encode("utf-8")
    write_locked(
        {
            "s2_artificial_performance_observations.csv": csv_bytes(observations, OBS_FIELDS),
            "s2_artificial_performance_block_summary.csv": csv_bytes(block_rows, BLOCK_FIELDS),
            "s2_artificial_performance_stratum_summary.csv": csv_bytes(stratum_rows, STRATUM_FIELDS),
            "s2_artificial_performance_environment.json": canonical_json(environment),
            "s2_artificial_performance_receipt.json": canonical_json(receipt),
            "s2_artificial_performance_report_zh.md": report,
        },
        args.output_dir.resolve(),
    )
    print(f"[saved] immutable S2 artificial benchmark result: {args.output_dir.resolve()}")
    print(f"[correctness] exact={replay_summary['all_exact']}/168 passed={replay_passed}")
    print(f"[benchmark] warmup={warmup_calls} timed={len(observations)} blocks={len(block_rows)}")
    print(f"[gate] all_passed={gate_result['all_performance_gates_passed']} status={status}")
    print("[locked] production=false formal_rerun=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
