#!/usr/bin/env python3
"""Run the authorized 168-case artificial CUDA S1 equivalence zero-step."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VERIFY_PATH = ROOT / "tools/verify_mamba_v16_d6a_r1_s1_exact_assignment_zero_step_authorization.py"
verify_spec = importlib.util.spec_from_file_location("d6_s1_zero_step_verify", VERIFY_PATH)
verify_module = importlib.util.module_from_spec(verify_spec)
assert verify_spec.loader is not None
verify_spec.loader.exec_module(verify_module)
verify_authorization = verify_module.verify_authorization
from utils.mamba_d6a_r1_s1_exact_assignment import (  # noqa: E402
    CANDIDATE_COUNT,
    SLOT_COUNT,
    frozen_reference_diagnostics,
    s1_exact_reduced_assignment,
)


VERSION = "mamba-v16-d6a-r1-s1-exact-assignment-artificial-zero-step-v1"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def artificial_scores(family: str, seed: int) -> np.ndarray:
    """Generate one preregistered finite float32 assignment matrix."""

    rng = np.random.default_rng(seed)
    shape = (SLOT_COUNT, CANDIDATE_COUNT)
    if family == "independent_normal":
        scores = rng.standard_normal(shape).astype(np.float32)
    elif family == "collision_heavy_shared_candidate_bias":
        shared = rng.standard_normal(CANDIDATE_COUNT).astype(np.float32)
        scores = shared[None, :] + 0.05 * rng.standard_normal(shape).astype(np.float32)
        scores[:, :96] += np.float32(5.0)
    elif family == "identical_rows":
        row = rng.standard_normal(CANDIDATE_COUNT).astype(np.float32)
        scores = np.repeat(row[None, :], SLOT_COUNT, axis=0)
    elif family == "exact_tie_groups":
        scores = rng.integers(-8, 9, size=shape, dtype=np.int16).astype(np.float32)
    elif family == "near_ties_float32":
        shared = rng.standard_normal(CANDIDATE_COUNT).astype(np.float32)
        perturbation = rng.choice(
            np.asarray([-2, -1, 0, 1, 2], dtype=np.float32), size=shape
        ) * np.float32(2.0**-20)
        scores = shared[None, :] + perturbation
    elif family == "shared_top32_adversarial":
        scores = 0.01 * rng.standard_normal(shape).astype(np.float32)
        shared_columns = rng.choice(CANDIDATE_COUNT, size=32, replace=False)
        scores[:, shared_columns] = np.float32(20.0)
        remaining = np.setdiff1d(
            np.arange(CANDIDATE_COUNT, dtype=np.int64), shared_columns
        )
        unique_columns = rng.choice(remaining, size=SLOT_COUNT, replace=False)
        scores[np.arange(SLOT_COUNT), unique_columns] = np.float32(19.999)
    elif family == "top32_cutoff_ties":
        scores = np.full(shape, np.float32(-1.0e8), dtype=np.float32)
        tied_columns = rng.choice(CANDIDATE_COUNT, size=64, replace=False)
        scores[:, tied_columns] = np.float32(1.0e8)
    else:
        raise ValueError(f"Unknown artificial family: {family}")
    scores = np.ascontiguousarray(scores, dtype=np.float32)
    if scores.shape != shape or not np.isfinite(scores).all():
        raise RuntimeError(f"Invalid artificial matrix for {family}/{seed}")
    return scores


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    outputs = dict(outputs)
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    ).encode("ascii")
    if output_dir.exists():
        existing = {
            path.relative_to(output_dir).as_posix(): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != outputs:
            raise RuntimeError(f"Existing S1 zero-step result drifted: {output_dir}")
        print(f"[locked] existing S1 artificial zero-step is byte-identical: {output_dir}")
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

    authorization = verify_authorization(args.config_dir, args.authorization_dir)
    config_path = args.config_dir / authorization["runtime_config"]["name"]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    suite = config["synthetic_equivalence_suite"]
    if not torch.cuda.is_available():
        raise RuntimeError("S1 artificial zero-step requires CUDA")
    device = torch.device("cuda:0")

    rows: list[dict[str, Any]] = []
    unions: dict[str, list[int]] = defaultdict(list)
    for family_spec in suite["families"]:
        family = family_spec["name"]
        for offset in range(family_spec["cases"]):
            seed = family_spec["seed_start"] + offset
            scores = artificial_scores(family, seed)
            input_sha256 = sha256_bytes(scores.tobytes())
            logits = torch.from_numpy(scores).unsqueeze(0).to(device)
            with torch.inference_mode():
                s0_hard, s0_selected, s0_slots, s0_objective = frozen_reference_diagnostics(logits)
                s1 = s1_exact_reduced_assignment(logits)

            slot_exact = torch.equal(s0_slots, s1.slot_to_candidate)
            selected_exact = torch.equal(s0_selected, s1.selected_indices)
            hard_exact = torch.equal(s0_hard, s1.hard_assignment)
            objective_exact = bool(s0_objective == s1.adjusted_objective)
            baseline_columns = s0_slots[0].detach().cpu().numpy()
            baseline_contained = bool(np.isin(baseline_columns, s1.union_columns).all())
            selected_unique = int(s1.selected_indices.unique().numel())
            output_input_sha256 = sha256_bytes(logits.detach().cpu().numpy()[0].tobytes())
            input_unchanged = input_sha256 == output_input_sha256
            passed = all(
                (
                    slot_exact,
                    selected_exact,
                    hard_exact,
                    objective_exact,
                    baseline_contained,
                    selected_unique == SLOT_COUNT,
                    input_unchanged,
                )
            )
            union_size = int(s1.union_columns.size)
            unions[family].append(union_size)
            rows.append(
                {
                    "case_index": len(rows),
                    "family": family,
                    "seed": seed,
                    "union_size": union_size,
                    "slot_to_candidate_exact": slot_exact,
                    "sorted_selected_indices_exact": selected_exact,
                    "hard_assignment_exact": hard_exact,
                    "adjusted_objective_exact": objective_exact,
                    "baseline_columns_contained_in_union": baseline_contained,
                    "selected_unique": selected_unique,
                    "input_unchanged": input_unchanged,
                    "all_case_gates_passed": passed,
                }
            )

    if len(rows) != 168:
        raise RuntimeError(f"S1 zero-step case count drifted: {len(rows)}")
    all_inputs_unchanged = all(row["input_unchanged"] for row in rows)
    if not all_inputs_unchanged:
        raise RuntimeError("S1 zero-step mutated an artificial input matrix")
    metrics_buffer = io.StringIO(newline="")
    fieldnames = list(rows[0])
    writer = csv.DictWriter(metrics_buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

    union_rows = []
    for family_spec in suite["families"]:
        family = family_spec["name"]
        values = unions[family]
        union_rows.append(
            {
                "family": family,
                "cases": len(values),
                "minimum": min(values),
                "mean": float(np.mean(values, dtype=np.float64)),
                "maximum": max(values),
                "slot_to_candidate_exact": sum(
                    row["slot_to_candidate_exact"]
                    for row in rows
                    if row["family"] == family
                ),
                "adjusted_objective_exact": sum(
                    row["adjusted_objective_exact"]
                    for row in rows
                    if row["family"] == family
                ),
            }
        )
    union_buffer = io.StringIO(newline="")
    union_writer = csv.DictWriter(
        union_buffer, fieldnames=list(union_rows[0]), lineterminator="\n"
    )
    union_writer.writeheader()
    union_writer.writerows(union_rows)

    all_union_sizes = [row["union_size"] for row in rows]
    slot_exact_count = sum(row["slot_to_candidate_exact"] for row in rows)
    selected_exact_count = sum(row["sorted_selected_indices_exact"] for row in rows)
    hard_exact_count = sum(row["hard_assignment_exact"] for row in rows)
    objective_exact_count = sum(row["adjusted_objective_exact"] for row in rows)
    contained_count = sum(row["baseline_columns_contained_in_union"] for row in rows)
    all_passed = all(row["all_case_gates_passed"] for row in rows)
    summary = {
        "status": (
            "S1_equivalence_passed_performance_not_evaluated"
            if all_passed
            else "S1_equivalence_failed_performance_forbidden"
        ),
        "cases": 168,
        "families": 7,
        "slot_to_candidate_exact": slot_exact_count,
        "sorted_selected_indices_exact": selected_exact_count,
        "hard_assignment_exact": hard_exact_count,
        "adjusted_objective_exact": objective_exact_count,
        "baseline_columns_contained_in_union": contained_count,
        "union_size_minimum": min(all_union_sizes),
        "union_size_mean": float(np.mean(all_union_sizes, dtype=np.float64)),
        "union_size_maximum": max(all_union_sizes),
    }
    auth_path = args.authorization_dir / "s1_zero_step_execution_authorization_receipt.json"
    receipt = {
        "zero_step_version": VERSION,
        "status": (
            "D6A_R1_S1_exact_assignment_artificial_zero_step_passed"
            if all_passed
            else "D6A_R1_S1_exact_assignment_artificial_zero_step_equivalence_failed"
        ),
        "authorization_receipt_sha256": sha256_bytes(auth_path.read_bytes()),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "cases": 168,
        "families": 7,
        "S0_assignments": 168,
        "S1_assignments": 168,
        "slot_to_candidate_exact": slot_exact_count,
        "sorted_selected_indices_exact": selected_exact_count,
        "hard_assignment_exact": hard_exact_count,
        "adjusted_objective_exact": objective_exact_count,
        "baseline_columns_contained_in_union": contained_count,
        "all_equivalence_gates_passed": all_passed,
        "state_unchanged": all_inputs_unchanged,
        "performance_timing_calls": 0,
        "warmup_runs": 0,
        "timed_runs": 0,
        "torch_profiler_traces": 0,
        "formal_gate_evaluated": False,
        "formal_gate_changed": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "S1_artificial_performance_benchmark_authorized": False,
        "S2_implementation_authorized": False,
        "R1_production_implementation_change_authorized": False,
        "formal_efficiency_rerun_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": (
            "separate_S1_artificial_performance_benchmark_execution_authorization_only"
            if all_passed
            else "archive_S1_equivalence_negative_result_and_stop_S1"
        ),
    }
    report = (
        "# Mamba v1.6 D6-A R1 S1 artificial zero-step 结果\n\n"
        "- 人工 assignment matrices：168，覆盖 7 个预注册 family。\n"
        f"- S0/S1 slot mapping：{slot_exact_count}/168；selected indices：{selected_exact_count}/168。\n"
        f"- Hard assignment：{hard_exact_count}/168；adjusted objective：{objective_exact_count}/168。\n"
        f"- S0 选择列包含于 S1 union：{contained_count}/168；每例 selected unique：32/32。\n"
        f"- Union size min/mean/max：{summary['union_size_minimum']} / {summary['union_size_mean']:.6f} / {summary['union_size_maximum']}。\n"
        "- Timing calls/warmup/timed/profiler traces：0 / 0 / 0 / 0。\n"
        "- D6 cases、optimizer steps、model updates：0 / 0 / 0。\n"
        f"- 全部等价门控通过：{all_passed}。\n"
        "- 本结果不授权 performance benchmark、生产 R1 修改、formal rerun 或训练。\n"
    ).encode("utf-8")
    write_locked(
        {
            "s1_artificial_equivalence_metrics.csv": metrics_buffer.getvalue().encode("utf-8"),
            "s1_union_size_summary.csv": union_buffer.getvalue().encode("utf-8"),
            "s1_artificial_zero_step_summary.json": canonical_json(summary),
            "s1_artificial_zero_step_receipt.json": canonical_json(receipt),
            "s1_artificial_zero_step_report_zh.md": report,
        },
        args.output_dir.resolve(),
    )
    print(f"[saved] immutable S1 artificial zero-step: {args.output_dir.resolve()}")
    print(
        f"[gate] slot={slot_exact_count}/168 selected={selected_exact_count}/168 "
        f"hard={hard_exact_count}/168 objective={objective_exact_count}/168 passed={all_passed}"
    )
    print("[done] timing=0 optimizer_steps=0 D6_cases=0")
    print("[locked] benchmark=false production=false formal_rerun=false training=false D6B=false")


if __name__ == "__main__":
    main()
