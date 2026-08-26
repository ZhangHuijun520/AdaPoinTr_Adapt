#!/usr/bin/env python3
"""Synthetic end-to-end test for the D3 Round-A gate executor."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDS = ("A", "B", "C", "D")


def canonical(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_sidecar(path: Path) -> None:
    Path(str(path) + ".sha256").write_text(
        f"{sha256(path)}  {path.name}\n", encoding="ascii"
    )


def write_json(path: Path, value: dict, sidecar: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))
    if sidecar:
        write_sidecar(path)


def make_candidate(root: Path, candidate: str, disasters: int, dense_zero: int) -> Path:
    records = {}
    remaining_disasters = disasters
    remaining_zero = dense_zero
    fold_efficiency = {}
    for fold_index, fold in enumerate(FOLDS):
        run_dir = root / candidate / f"{candidate}_fold{fold}_seed0"
        run_dir.mkdir(parents=True)
        metrics = run_dir / "metrics.csv"
        fieldnames = [
            "case_id", "final_cd_l1_mm", "final_hd95_mm", "final_nsd_at_1mm",
            "rim_contact_hd95_mm", "rim_predicted_rim_points",
            "coarse_predicted_rim_points",
        ]
        with metrics.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for index in range(100):
                zero = remaining_zero > 0
                disaster = remaining_disasters > 0
                if zero:
                    remaining_zero -= 1
                if disaster:
                    remaining_disasters -= 1
                writer.writerow({
                    "case_id": f"case_{fold}_{index:03d}",
                    "final_cd_l1_mm": 2.0 + (0.02 if candidate == "S1" else 0.0),
                    "final_hd95_mm": 5.0 + (0.1 if candidate == "S1" else 0.0),
                    "final_nsd_at_1mm": 0.2 + (-0.001 if candidate == "S1" else 0.0),
                    "rim_contact_hd95_mm": "nan" if zero else (60.0 if disaster else 10.0),
                    "rim_predicted_rim_points": 0 if zero else 8,
                    "coarse_predicted_rim_points": 0 if index < 30 else 4,
                })
        efficiency = run_dir / "efficiency.json"
        write_json(efficiency, {
            "parameter_count_total": 1000,
            "parameter_count_trainable": 1000,
            "latency_ms_median": 10.0 + (0.2 if candidate == "S1" else 0.0),
            "peak_gpu_memory_bytes": 1000000,
        })
        record_path = run_dir / "run_record.json"
        record = {
            "record_version": "mamba-v13-d3-run-record-v1",
            "status": "frozen_complete_development_fold",
            "candidate": candidate,
            "fold": fold,
            "seed": 0,
            "dev_cases": 100,
            "artifacts": {
                "metrics_csv": {"path": str(metrics), "sha256": sha256(metrics)},
                "efficiency": {"path": str(efficiency), "sha256": sha256(efficiency)},
            },
            "holdout_inference_consumed": False,
            "holdout_metrics_consumed": False,
            "holdout_visual_review_consumed": False,
            "selection_started": False,
        }
        write_json(record_path, record, sidecar=True)
        records[fold] = {"path": str(record_path), "sha256": sha256(record_path)}
        fold_efficiency[fold] = json.loads(efficiency.read_text())
    assert remaining_disasters == 0 and remaining_zero == 0
    summary = {
        "disaster_count": disasters,
        "dense_zero_contact_at_2mm_count": dense_zero,
        "coarse_zero_support_at_2mm_count": 120,
    }
    status = {
        "S0": "S0_seed0_frozen_ready_for_S2_feasibility",
        "S1": "S1_seed0_frozen_ready_for_preregistered_gate_analysis",
    }[candidate]
    completion = {
        "status": status,
        "candidate": candidate,
        "seed": 0,
        "folds": list(FOLDS),
        "development_cases": 400,
        "run_records": records,
        "fold_efficiency": fold_efficiency,
        "holdout_authorized": False,
        "selection_started": False,
        "reference_summary" if candidate == "S0" else "summary": summary,
    }
    path = root / candidate / "completion.json"
    write_json(path, completion, sidecar=True)
    return path


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="mamba_d3_gate_e2e_") as temp:
        root = Path(temp)
        s0 = make_candidate(root, "S0", disasters=248, dense_zero=33)
        s1 = make_candidate(root, "S1", disasters=233, dense_zero=25)
        s2_dir = root / "S2_negative"
        s2_receipt = s2_dir / "negative_result_receipt.json"
        write_json(s2_receipt, {
            "status": "frozen_negative_high_hit_rate_failed_all_case_safety_gate",
            "S2_full_training_authorized": False,
            "holdout_accessed": False,
            "selection_started": False,
        })
        (s2_dir / "files.sha256").write_text(
            f"{sha256(s2_receipt)}  {s2_receipt.name}\n", encoding="ascii"
        )
        output = root / "output"
        subprocess.run([
            sys.executable, str(ROOT / "tools/analyze_mamba_v13_d3_round_a_seed0.py"),
            "--s0_completion", str(s0), "--s1_completion", str(s1),
            "--s2_negative_dir", str(s2_dir), "--output_dir", str(output),
        ], cwd=ROOT, check=True)
        subprocess.run([
            sys.executable, str(ROOT / "tools/verify_mamba_v13_d3_round_a_seed0.py"),
            "--result_dir", str(output),
        ], cwd=ROOT, check=True)
        receipt = json.loads((output / "round_a_selection_receipt.json").read_text())
        assert receipt["status"] == "round_a_frozen_negative_no_experimental_candidate_passed"
        assert receipt["S1_gates"]["disaster_count_not_above_S0"] is True
        assert receipt["S1_gates"]["dense_zero_contact_at_2mm_equals_zero"] is False
        print("[e2e] synthetic 400-case D3 Round-A negative freeze passed")


if __name__ == "__main__":
    main()
