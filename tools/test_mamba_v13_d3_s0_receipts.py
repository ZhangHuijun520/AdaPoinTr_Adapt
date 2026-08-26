#!/usr/bin/env python3
"""Synthetic end-to-end checks for D3 run and S0 completion receipts."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_hashed(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    Path(str(path) + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="ascii"
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "yaml.py").write_text(
            "import json\n"
            "def safe_load(value):\n"
            "    return json.loads(value)\n",
            encoding="utf-8",
        )
        subprocess_env = os.environ.copy()
        existing_pythonpath = subprocess_env.get("PYTHONPATH", "")
        subprocess_env["PYTHONPATH"] = str(root) + (
            os.pathsep + existing_pythonpath if existing_pythonpath else ""
        )
        records = root / "records"
        auth = root / "authorization.json"
        smoke = root / "smoke.json"
        write_hashed(auth, b"{}\n")
        write_hashed(smoke, b"{}\n")

        for fold in "ABCD":
            run = records / f"S0_fold{fold}_seed0"
            run.mkdir(parents=True)
            config = run / "config.yaml"
            config.write_text(json.dumps({
                "d3_execution": {
                    "candidate": "S0", "fold": fold, "seed": 0,
                    "training_authorized": True,
                    "holdout_authorized": False,
                    "selection_started": False,
                }
            }) + "\n", encoding="utf-8")
            checkpoint = run / "checkpoint.pth"
            checkpoint.write_bytes(b"synthetic checkpoint")
            summary = run / "summary.json"
            summary.write_text("{}\n", encoding="utf-8")
            efficiency = run / "efficiency.json"
            efficiency.write_text(json.dumps({
                "latency_ms_median": 40.0,
                "peak_gpu_memory_bytes": 600_000_000,
                "parameter_count_total": 10_000,
                "parameter_count_trainable": 10_000,
            }) + "\n", encoding="utf-8")
            training = run / "training.log"
            training.write_text(
                "".join(f"EpochTime = {1 + index / 1000:.3f}\n" for index in range(100)),
                encoding="utf-8",
            )
            expected = run / "expected.txt"
            case_ids = [f"case_{fold}_{index:03d}" for index in range(100)]
            expected.write_text("\n".join(case_ids) + "\n", encoding="utf-8")
            metrics = run / "metrics.csv"
            rows = [{
                "case_id": case_id,
                "final_cd_l1_mm": 1.0,
                "final_hd95_mm": 2.0,
                "final_nsd_at_1mm": 0.9,
                "rim_contact_hd95_mm": 10.0,
                "rim_predicted_rim_points": 5,
                "coarse_predicted_rim_points": 2,
            } for case_id in case_ids]
            with metrics.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            subprocess.run([
                sys.executable,
                str(ROOT / "tools/write_mamba_v13_d3_run_record.py"),
                "--candidate", "S0", "--fold", fold, "--seed", "0",
                "--config", str(config), "--checkpoint", str(checkpoint),
                "--metrics_csv", str(metrics), "--metrics_summary", str(summary),
                "--efficiency", str(efficiency), "--training_log", str(training),
                "--authorization_receipt", str(auth),
                "--smoke_receipt", str(smoke),
                "--expected_case_ids", str(expected),
                "--output", str(run / "run_record.json"),
            ], check=True, cwd=ROOT, env=subprocess_env)

        completion = root / "completion.json"
        subprocess.run([
            sys.executable,
            str(ROOT / "tools/freeze_mamba_v13_d3_s0_seed0.py"),
            "--records_root", str(records),
            "--authorization_receipt", str(auth),
            "--smoke_receipt", str(smoke),
            "--output", str(completion),
        ], check=True, cwd=ROOT)
        receipt = json.loads(completion.read_text(encoding="utf-8"))
        assert receipt["development_cases"] == 400
        assert receipt["reference_summary"]["disaster_count"] == 0
        assert receipt["reference_summary"]["dense_zero_contact_at_2mm_count"] == 0
        assert receipt["reference_summary"]["coarse_zero_support_at_2mm_count"] == 0
        assert receipt["S2_head_only_feasibility_authorized_next"] is True
        assert receipt["S2_full_training_authorized"] is False
        assert receipt["holdout_authorized"] is False

    print("[ok] four immutable D3 fold records validate exact 100-case sets")
    print("[ok] S0 completion receipt validates 400 unique development cases")
    print("[locked] only S2 head-only feasibility is authorized next")


if __name__ == "__main__":
    main()
