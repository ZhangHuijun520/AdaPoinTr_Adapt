#!/usr/bin/env python3
"""Run the authorized 168-case artificial CUDA S2 equivalence zero-step."""

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
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VERIFY_PATH = ROOT / "tools/verify_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_authorization.py"
verify_spec = importlib.util.spec_from_file_location("d6_s2_zero_step_verify", VERIFY_PATH)
verify_module = importlib.util.module_from_spec(verify_spec)
assert verify_spec.loader is not None
verify_spec.loader.exec_module(verify_module)
verify_authorization = verify_module.verify_authorization

S1_PREFLIGHT_PATH = ROOT / "tools/preflight_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py"
s1_spec = importlib.util.spec_from_file_location("d6_s1_frozen_artificial_suite", S1_PREFLIGHT_PATH)
s1_module = importlib.util.module_from_spec(s1_spec)
assert s1_spec.loader is not None
s1_spec.loader.exec_module(s1_module)
artificial_scores = s1_module.artificial_scores

from utils.mamba_d6a_r1_s1_exact_assignment import (  # noqa: E402
    SLOT_COUNT,
    frozen_reference_diagnostics,
)
from utils.mamba_d6a_r1_s2_certified_fast_path import (  # noqa: E402
    s2_certified_fast_path_assignment,
)


VERSION = "mamba-v16-d6a-r1-s2-certified-fast-path-artificial-zero-step-v1"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


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
            raise RuntimeError(f"Existing S2 zero-step result drifted: {output_dir}")
        print(f"[locked] existing S2 artificial zero-step is byte-identical: {output_dir}")
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
        raise RuntimeError("S2 artificial zero-step requires CUDA")
    device = torch.device("cuda:0")

    equivalence_rows: list[dict[str, Any]] = []
    routing_rows: list[dict[str, Any]] = []
    family_routes: dict[str, Counter[str]] = defaultdict(Counter)
    for family_spec in suite["families"]:
        family = family_spec["name"]
        for offset in range(family_spec["cases"]):
            seed = family_spec["seed_start"] + offset
            scores = artificial_scores(family, seed)
            input_sha256 = sha256_bytes(scores.tobytes())
            logits = torch.from_numpy(scores).unsqueeze(0).to(device)
            with torch.inference_mode():
                s0_hard, s0_selected, s0_slots, s0_objective = frozen_reference_diagnostics(logits)
                s2 = s2_certified_fast_path_assignment(logits)

            slot_exact = torch.equal(s0_slots, s2.slot_to_candidate)
            selected_exact = torch.equal(s0_selected, s2.selected_indices)
            hard_exact = torch.equal(s0_hard, s2.hard_assignment)
            objective_exact = bool(s0_objective == s2.adjusted_objective)
            selected_unique = int(s2.selected_indices.unique().numel())
            input_unchanged = input_sha256 == sha256_bytes(logits.detach().cpu().numpy()[0].tobytes())
            outputs_finite = bool(
                torch.isfinite(s2.hard_assignment).all().item()
                and torch.isfinite(s2.selected_indices).all().item()
                and torch.isfinite(s2.slot_to_candidate).all().item()
                and np.isfinite(s2.adjusted_objective)
            )
            all_exact = all((slot_exact, selected_exact, hard_exact, objective_exact))
            all_case_gates = all((all_exact, selected_unique == SLOT_COUNT, input_unchanged, outputs_finite))
            fast = s2.route == "certified_fast_path"
            fallback = s2.route == "fallback_s0"
            route_valid = fast or fallback
            false_positive = fast and not all_exact
            family_routes[family][s2.route] += 1

            equivalence_rows.append(
                {
                    "case_index": len(equivalence_rows),
                    "family": family,
                    "seed": seed,
                    "slot_to_candidate_exact": slot_exact,
                    "sorted_selected_indices_exact": selected_exact,
                    "hard_assignment_exact": hard_exact,
                    "adjusted_objective_exact": objective_exact,
                    "selected_unique": selected_unique,
                    "input_unchanged": input_unchanged,
                    "outputs_finite": outputs_finite,
                    "all_case_gates_passed": all_case_gates,
                }
            )
            routing_rows.append(
                {
                    "case_index": len(routing_rows),
                    "family": family,
                    "seed": seed,
                    "route": s2.route,
                    "fallback_reason": s2.fallback_reason,
                    "union_size": int(s2.union_columns.size),
                    "cutoff_gap_minimum": float(s2.cutoff_gap_minimum),
                    "cutoff_guard_maximum": float(s2.cutoff_guard_maximum),
                    "uniqueness_gap": float(s2.uniqueness_gap),
                    "uniqueness_guard": float(s2.uniqueness_guard),
                    "edge_exclusion_solves": s2.edge_exclusion_solves,
                    "route_valid": route_valid,
                    "false_positive_certificate": false_positive,
                }
            )

    if len(equivalence_rows) != 168 or len(routing_rows) != 168:
        raise RuntimeError("S2 zero-step did not complete the frozen 168-case suite")
    if not all(row["input_unchanged"] for row in equivalence_rows):
        raise RuntimeError("S2 zero-step mutated an artificial input matrix")

    slot_exact_count = sum(row["slot_to_candidate_exact"] for row in equivalence_rows)
    selected_exact_count = sum(row["sorted_selected_indices_exact"] for row in equivalence_rows)
    hard_exact_count = sum(row["hard_assignment_exact"] for row in equivalence_rows)
    objective_exact_count = sum(row["adjusted_objective_exact"] for row in equivalence_rows)
    finite_count = sum(row["outputs_finite"] for row in equivalence_rows)
    equivalence_passed = all(row["all_case_gates_passed"] for row in equivalence_rows)
    fast_count = sum(row["route"] == "certified_fast_path" for row in routing_rows)
    fallback_count = sum(row["route"] == "fallback_s0" for row in routing_rows)
    false_positive_count = sum(row["false_positive_certificate"] for row in routing_rows)
    independent_fast = family_routes["independent_normal"]["certified_fast_path"]
    collision_fast = family_routes["collision_heavy_shared_candidate_bias"]["certified_fast_path"]
    routing_passed = all(
        (
            fast_count >= 96,
            independent_fast == 64,
            collision_fast == 32,
            false_positive_count == 0,
            fast_count + fallback_count == 168,
        )
    )
    all_passed = equivalence_passed and routing_passed

    family_rows: list[dict[str, Any]] = []
    for family_spec in suite["families"]:
        family = family_spec["name"]
        family_equivalence = [row for row in equivalence_rows if row["family"] == family]
        family_rows.append(
            {
                "family": family,
                "cases": len(family_equivalence),
                "certified_fast_path": family_routes[family]["certified_fast_path"],
                "fallback_s0": family_routes[family]["fallback_s0"],
                "all_exact": sum(row["all_case_gates_passed"] for row in family_equivalence),
            }
        )

    if not equivalence_passed:
        status = "D6A_R1_S2_certified_fast_path_artificial_zero_step_equivalence_failed"
        next_step = "freeze_S2_equivalence_negative_result_and_stop_without_benchmark"
    elif not routing_passed:
        status = "D6A_R1_S2_certified_fast_path_artificial_zero_step_routing_gate_failed"
        next_step = "freeze_S2_routing_negative_result_and_stop_without_benchmark"
    else:
        status = "D6A_R1_S2_certified_fast_path_artificial_zero_step_passed"
        next_step = "separate_S2_artificial_performance_benchmark_authorization_only"

    summary = {
        "status": status,
        "cases": 168,
        "families": 7,
        "slot_to_candidate_exact": slot_exact_count,
        "sorted_selected_indices_exact": selected_exact_count,
        "hard_assignment_exact": hard_exact_count,
        "adjusted_objective_exact": objective_exact_count,
        "outputs_finite": finite_count,
        "certified_fast_path_cases": fast_count,
        "fallback_s0_cases": fallback_count,
        "independent_normal_certified_fast_path": independent_fast,
        "collision_heavy_certified_fast_path": collision_fast,
        "false_positive_certificates": false_positive_count,
        "equivalence_gate_passed": equivalence_passed,
        "routing_integrity_gate_passed": routing_passed,
        "all_gates_passed": all_passed,
    }
    auth_path = args.authorization_dir / "s2_zero_step_execution_authorization_receipt.json"
    receipt = {
        "zero_step_version": VERSION,
        **summary,
        "authorization_receipt_sha256": sha256_bytes(auth_path.read_bytes()),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "S0_assignments": 168,
        "S2_assignments": 168,
        "state_unchanged": True,
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
        "S2_artificial_performance_benchmark_authorized": False,
        "R1_production_implementation_change_authorized": False,
        "formal_efficiency_rerun_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": next_step,
    }
    report = (
        "# Mamba v1.6 D6-A R1 S2 artificial zero-step 结果\n\n"
        "- 人工 assignment matrices：168，覆盖 7 个冻结 family。\n"
        f"- Slot / selected / hard / objective 精确一致：{slot_exact_count} / {selected_exact_count} / {hard_exact_count} / {objective_exact_count}（分母均为 168）。\n"
        f"- Certified fast path / complete S0 fallback：{fast_count} / {fallback_count}。\n"
        f"- independent-normal fast path：{independent_fast}/64；collision-heavy fast path：{collision_fast}/32。\n"
        f"- False-positive certificate：{false_positive_count}；输出有限：{finite_count}/168。\n"
        f"- 等价门控 / 路由门控 / 全部门控：{equivalence_passed} / {routing_passed} / {all_passed}。\n"
        "- Timing/warmup/timed/profiler：0 / 0 / 0 / 0。\n"
        "- D6 cases、optimizer steps、model updates：0 / 0 / 0。\n"
        "- 本结果不自动授权 benchmark、生产修改、formal rerun 或训练。\n"
    ).encode("utf-8")
    write_locked(
        {
            "s2_artificial_equivalence_metrics.csv": csv_bytes(equivalence_rows),
            "s2_certification_routing_metrics.csv": csv_bytes(routing_rows),
            "s2_family_summary.csv": csv_bytes(family_rows),
            "s2_artificial_zero_step_summary.json": canonical_json(summary),
            "s2_artificial_zero_step_receipt.json": canonical_json(receipt),
            "s2_artificial_zero_step_report_zh.md": report,
        },
        args.output_dir.resolve(),
    )
    print(f"[saved] immutable S2 artificial zero-step: {args.output_dir.resolve()}")
    print(
        f"[gate] slot={slot_exact_count}/168 selected={selected_exact_count}/168 "
        f"hard={hard_exact_count}/168 objective={objective_exact_count}/168"
    )
    print(
        f"[routing] fast={fast_count}/168 independent={independent_fast}/64 "
        f"collision={collision_fast}/32 false_positive={false_positive_count} passed={routing_passed}"
    )
    print("[done] timing=0 optimizer_steps=0 D6_cases=0")
    print("[locked] benchmark=false production=false formal_rerun=false training=false D6B=false")


if __name__ == "__main__":
    main()
