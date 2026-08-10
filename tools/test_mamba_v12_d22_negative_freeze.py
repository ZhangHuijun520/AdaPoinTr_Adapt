#!/usr/bin/env python
"""Synthetic immutable-freeze test for the D2.2 negative result."""

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


CORE = (
    "implant_cd_l1_mm",
    "implant_hd95_mm",
    "implant_nsd_at_1mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
    "coarse_gt_rim_to_pred_p95_mm",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def summary(nonfinite):
    return {
        "case_count": 420,
        "disaster_count": 10,
        "catastrophic_skull_count": 8,
        "nonfinite_case_count": nonfinite,
        "undefined_contact_count": nonfinite,
        "rim_hd95_p95": 20.0,
        "rim_hd95_max": 60.0,
        "means": {
            "implant_hd95_mm": 8.0,
            "coarse_gt_rim_to_pred_p95_mm": 15.0,
        },
    }


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        records_root = root / "round_a"
        protocol = root / "protocol.json"
        amendment = root / "amendment.json"
        write_json(protocol, {"protocol_id": "synthetic"})
        write_json(amendment, {"amends": "synthetic"})

        failing_folds = {
            "R0": {"A", "B"},
            "R1": {"A", "B"},
            "R2": {"A", "B", "C"},
        }
        for candidate in ("R0", "R1", "R2"):
            for fold in "ABCD":
                run_dir = records_root / f"{candidate}_fold{fold}_seed0"
                run_dir.mkdir(parents=True)
                metrics_path = run_dir / "metrics.csv"
                failed = fold in failing_folds[candidate]
                row = {
                    "case_id": f"train__{candidate[-1]}{fold}__random_1",
                    "skull_id": f"{candidate[-1]}{fold}",
                    "defect_type": "random_1",
                    "rim_predicted_rim_points": 0 if failed else 10,
                }
                row.update({metric: 1.0 for metric in CORE})
                if failed:
                    for metric in (
                        "rim_contact_cd_l1_mm",
                        "rim_contact_hd95_mm",
                        "rim_contact_nsd_at_1mm",
                    ):
                        row[metric] = "nan"
                with metrics_path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(row))
                    writer.writeheader()
                    writer.writerow(row)
                record = {
                    "candidate": candidate,
                    "fold": fold,
                    "seed": 0,
                    "artifacts": {
                        "metrics_csv": {
                            "path": str(metrics_path),
                            "sha256": sha256(metrics_path),
                        }
                    },
                }
                write_json(run_dir / "run_record.json", record)

        summaries = {
            "R0": summary(2),
            "R1": summary(2),
            "R2": summary(3),
        }
        summaries["R0"].update({"eligible": False})
        for candidate in ("R1", "R2"):
            summaries[candidate].update({
                "eligible": False,
                "gates": {
                    "complete": True,
                    "nonfinite": False,
                    "disaster": True,
                    "final_noninferiority": True,
                    "rim_tail": True,
                    "transition": True,
                    "direct_target_mean": True,
                    "direct_target_cases": True,
                    "efficiency": True,
                },
            })
        selection = root / "selection.json"
        write_json(selection, {
            "winner": None,
            "round_b_allowed": False,
            "protected_splits_accessed": False,
            "protocol_sha256": sha256(protocol),
            "implementation_amendment_sha256": sha256(amendment),
            "input_sha256": {},
            "summaries": summaries,
        })
        Path(str(selection) + ".sha256").write_text(
            f"{sha256(selection)}  {selection.name}\n", encoding="ascii"
        )
        output = root / "frozen"
        command = [
            sys.executable,
            "tools/freeze_mamba_v12_d22_negative_result.py",
            "--selection", str(selection),
            "--records_root", str(records_root),
            "--protocol", str(protocol),
            "--amendment", str(amendment),
            "--output_dir", str(output),
        ]
        subprocess.run(command, check=True)
        first_hash = sha256(output / "negative_result_receipt.json")
        subprocess.run(command, check=True)
        assert sha256(output / "negative_result_receipt.json") == first_hash
        receipt = json.loads(
            (output / "negative_result_receipt.json").read_text()
        )
        assert receipt["winner"] is None
        assert receipt["round_b_allowed"] is False
        assert receipt["failed_gate_by_candidate"] == {
            "R1": ["nonfinite"],
            "R2": ["nonfinite"],
        }
        assert len(receipt["nonfinite_zero_contact_cases"]["R2"]) == 3
        print("[ok] D2.2 negative freeze is deterministic and immutable")
        print("[ok] only the preregistered nonfinite gate blocks R1/R2")


if __name__ == "__main__":
    main()
