#!/usr/bin/env python
"""Synthetic regression test for preregistered Round-A selection."""

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        records_root = root / "records"
        protocol = root / "protocol.json"
        protocol.write_text(json.dumps({
            "selection_rules": {
                "final_noninferiority": {
                    "final_cd_l1_mm_delta_max": 0.10,
                    "final_hd95_mm_delta_max": 0.50,
                    "final_nsd_at_1mm_delta_min": -0.01,
                },
                "efficiency_vs_c0": {
                    "peak_gpu_memory_ratio_max": 1.25,
                    "inference_latency_ratio_max": 1.75,
                    "training_epoch_time_ratio_max": 1.75,
                },
            }
        }))
        settings = {
            "C0": {"rim": 20.0, "final_cd": 2.0, "final_hd": 5.0, "nsd": 0.2},
            "C1": {"rim": 15.0, "final_cd": 2.02, "final_hd": 5.1, "nsd": 0.2},
            "C2": {"rim": 60.0, "final_cd": 2.0, "final_hd": 5.0, "nsd": 0.2},
            "C3": {"rim": 18.0, "final_cd": 2.2, "final_hd": 5.0, "nsd": 0.2},
        }
        for candidate, values in settings.items():
            for fold in "ABCD":
                run = records_root / f"{candidate}_fold{fold}_seed0"
                run.mkdir(parents=True)
                metrics = run / "metrics.csv"
                with open(metrics, "w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=[
                        "case_id", "implant_hd95_mm", "final_cd_l1_mm",
                        "final_hd95_mm", "final_nsd_at_1mm",
                        "rim_contact_cd_l1_mm", "rim_contact_hd95_mm",
                        "rim_contact_nsd_at_1mm",
                    ])
                    writer.writeheader()
                    writer.writerow({
                        "case_id": f"{fold}",
                        "implant_hd95_mm": 7.0,
                        "final_cd_l1_mm": values["final_cd"],
                        "final_hd95_mm": values["final_hd"],
                        "final_nsd_at_1mm": values["nsd"],
                        "rim_contact_cd_l1_mm": 4.0,
                        "rim_contact_hd95_mm": values["rim"],
                        "rim_contact_nsd_at_1mm": 0.5,
                    })
                summary = run / "summary.json"
                summary.write_text("{}")
                efficiency = run / "efficiency.json"
                efficiency.write_text(json.dumps({
                    "latency_ms_median": 10.0,
                    "peak_gpu_memory_bytes": 1000,
                }))
                config = run / "config.yaml"
                config.write_text("candidate: test\n")
                checkpoint = run / "checkpoint.pth"
                checkpoint.write_bytes(b"checkpoint")
                training_log = run / "training.log"
                training_log.write_text("EpochTime = 1.0\nEpochTime = 1.0\n")
                artifacts = {
                    "config": config,
                    "checkpoint": checkpoint,
                    "metrics_csv": metrics,
                    "metrics_summary": summary,
                    "efficiency": efficiency,
                    "training_log": training_log,
                }
                record = {
                    "candidate": candidate,
                    "fold": fold,
                    "seed": 0,
                    "training_epoch_time_seconds_mean_excluding_first": 1.0,
                    "artifacts": {
                        name: {"path": str(path), "sha256": digest(path)}
                        for name, path in artifacts.items()
                    },
                }
                (run / "run_record.json").write_text(json.dumps(record))
        output = root / "selection.json"
        subprocess.run([
            sys.executable,
            str(Path(__file__).with_name("select_mamba_v12_round.py")),
            "--records_root", str(records_root),
            "--protocol", str(protocol),
            "--round", "A",
            "--output", str(output),
        ], check=True)
        selected = json.loads(output.read_text())
        assert selected["selected"] == ["C1", "C0"]
        assert not selected["summaries"]["C2"]["gates"]["catastrophe"]
        assert not selected["summaries"]["C3"]["gates"]["final_noninferiority"]

        for fold in "ABCD":
            run = records_root / f"C1_fold{fold}_seed0"
            metrics = run / "metrics.csv"
            rows = list(csv.DictReader(metrics.open()))
            rows[0]["final_cd_l1_mm"] = "3.0"
            with metrics.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            record_path = run / "run_record.json"
            record = json.loads(record_path.read_text())
            record["artifacts"]["metrics_csv"]["sha256"] = digest(metrics)
            record_path.write_text(json.dumps(record))

        blocked_output = root / "blocked_selection.json"
        blocked = subprocess.run([
            sys.executable,
            str(Path(__file__).with_name("select_mamba_v12_round.py")),
            "--records_root", str(records_root),
            "--protocol", str(protocol),
            "--round", "A",
            "--output", str(blocked_output),
        ])
        assert blocked.returncode != 0
        assert not blocked_output.exists()
        failure_path = root / "blocked_selection_gate_failure.json"
        failure = json.loads(failure_path.read_text())
        assert failure["eligible_order"] == ["C0"]
        assert failure["selected"] == []
        assert failure["round_b_allowed"] is False
        assert Path(str(failure_path) + ".sha256").is_file()
    print("[ok] hard gates precede lexicographic ranking")
    print("[ok] catastrophe and final non-inferiority failures are rejected")
    print("[ok] expected frozen top two are C1 then C0")
    print("[ok] insufficient eligibility writes an audit and blocks Round B")


if __name__ == "__main__":
    main()
