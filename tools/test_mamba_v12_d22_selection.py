#!/usr/bin/env python
"""Synthetic test of D2.2 gates, transitions, and reference-only R0."""

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_run(root, candidate, fold, rows):
    run = root / f"{candidate}_fold{fold}_seed0"
    run.mkdir(parents=True)
    artifacts = {}
    files = {
        "config": ("config.yaml", b"model: synthetic\n"),
        "checkpoint": ("ckpt.pth", b"synthetic checkpoint"),
        "metrics_summary": ("summary.json", b"{}\n"),
        "training_log": (
            "train.log",
            b"EpochTime = 1.0\nEpochTime = 1.0\n",
        ),
    }
    for key, (name, payload) in files.items():
        path = run / name
        path.write_bytes(payload)
        artifacts[key] = {"path": str(path), "sha256": sha256_file(path)}

    csv_path = run / "metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    artifacts["metrics_csv"] = {
        "path": str(csv_path),
        "sha256": sha256_file(csv_path),
    }

    efficiency_path = run / "efficiency.json"
    efficiency_path.write_text(json.dumps({
        "latency_ms_median": 40.0,
        "peak_gpu_memory_bytes": 600_000_000,
    }))
    artifacts["efficiency"] = {
        "path": str(efficiency_path),
        "sha256": sha256_file(efficiency_path),
    }
    record = {
        "candidate": candidate,
        "fold": fold,
        "seed": 0,
        "training_epoch_time_seconds_mean_excluding_first": 1.0,
        "artifacts": artifacts,
    }
    record_path = run / "run_record.json"
    record_path.write_text(json.dumps(record, sort_keys=True) + "\n")


def make_row(index, candidate):
    rim_hd95 = {"R0": 20.0, "R1": 18.0, "R2": 19.0}[candidate]
    if candidate == "R0" and index < 2:
        rim_hd95 = 60.0
    if candidate == "R1" and index < 1:
        rim_hd95 = 60.0
    if candidate == "R2" and index < 2:
        rim_hd95 = 60.0
    direct = {"R0": 8.0, "R1": 7.0, "R2": 7.5}[candidate]
    return {
        "case_id": f"case_{index:03d}",
        "skull_id": f"skull_{index // 5:03d}",
        "implant_cd_l1_mm": 2.0,
        "implant_hd95_mm": 7.0,
        "implant_nsd_at_1mm": 0.3,
        "final_cd_l1_mm": 2.0,
        "final_hd95_mm": 5.0,
        "final_nsd_at_1mm": 0.2,
        "rim_contact_cd_l1_mm": 4.0,
        "rim_contact_hd95_mm": rim_hd95,
        "rim_contact_nsd_at_1mm": 0.5,
        "rim_predicted_rim_points": 100,
        "coarse_gt_rim_to_pred_p95_mm": direct,
    }


def main():
    with tempfile.TemporaryDirectory() as temporary:
        temporary = Path(temporary)
        records = temporary / "records"
        for candidate in ("R0", "R1", "R2"):
            all_rows = [make_row(index, candidate) for index in range(420)]
            for fold_index, fold in enumerate("ABCD"):
                start = fold_index * 105
                write_run(
                    records,
                    candidate,
                    fold,
                    all_rows[start : start + 105],
                )

        output = temporary / "selection.json"
        subprocess.run([
            sys.executable,
            str(ROOT / "tools/select_mamba_v12_d22_round_a.py"),
            "--records_root", str(records),
            "--protocol", str(
                ROOT / "docs/mamba_v12_d22_local_rim_trust_protocol_v1.json"
            ),
            "--amendment", str(
                ROOT / "docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1.json"
            ),
            "--output", str(output),
        ], check=True)
        selection = json.loads(output.read_text())
        assert selection["winner"] == "R1"
        assert selection["round_b_allowed"] is True
        assert selection["summaries"]["R0"]["eligible"] is False
        assert selection["summaries"]["R1"]["rescued"] == 1
        assert selection["summaries"]["R1"]["induced"] == 0
        assert selection["summaries"]["R1"]["eligible"] is True

    print("[ok] R0 remains reference-only and cannot win")
    print("[ok] D2.2 hard gates, transitions, and lexicographic winner are frozen")


if __name__ == "__main__":
    main()
