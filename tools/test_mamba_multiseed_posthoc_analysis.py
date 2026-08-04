#!/usr/bin/env python
"""Synthetic end-to-end test for multiseed post-hoc analysis."""

import csv
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

import analyze_skullbreak_mamba_multiseed_posthoc as analysis


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        cases = [f"case_{index}" for index in range(4)]
        panel = {
            "posthoc": True,
            "include_all_cases": True,
            "cases": [
                {
                    "case_id": case_id,
                    "skull_id": f"skull_{index}",
                    "defect_type": "random_1",
                }
                for index, case_id in enumerate(cases)
            ],
        }
        panel_path = root / "panel.json"
        panel_path.write_text(json.dumps(panel), encoding="utf-8")

        metric_args = []
        instrumentation_args = []
        for seed in (0, 1, 2):
            metric_rows = []
            ordering_rows = []
            block_rows = []
            instrumentation_dir = root / f"instrumentation_seed{seed}"
            token_dir = instrumentation_dir / "token_arrays"
            token_dir.mkdir(parents=True)
            manifest_rows = []
            for index, case_id in enumerate(cases):
                base = float(index + seed + 1)
                rim_hd95 = 55.0 if seed == 2 and index == 3 else 10.0 + base
                metric_row = {
                    "case_id": case_id,
                    "skull_id": f"skull_{index}",
                    "defect_type": "random_1",
                }
                for metric in analysis.METRICS:
                    metric_row[metric] = rim_hd95 if metric == "rim_contact_hd95_mm" else base
                metric_rows.append(metric_row)

                ordering_row = {"case_id": case_id}
                for feature in analysis.ORDERING_FEATURES:
                    ordering_row[feature] = base
                ordering_rows.append(ordering_row)

                for block_index in (0, 1):
                    block_row = {
                        "case_id": case_id,
                        "block_index": block_index,
                    }
                    for feature_index, feature in enumerate(analysis.BLOCK_FEATURES):
                        block_row[feature] = (
                            base + block_index + feature_index / 100.0
                        )
                    block_rows.append(block_row)

                token_path = token_dir / f"{case_id}.npz"
                coor = np.arange(24, dtype=np.float32).reshape(8, 3) + index
                sort_idx = np.arange(8, dtype=np.int64)
                np.savez_compressed(
                    token_path,
                    coor_original=coor,
                    sort_idx=sort_idx,
                    coor_ordered=coor,
                )
                manifest_rows.append({
                    "case_id": case_id,
                    "path": str(token_path.relative_to(instrumentation_dir).as_posix()),
                })

            metric_path = root / f"metrics_seed{seed}.csv"
            write_csv(metric_path, metric_rows)
            write_csv(
                instrumentation_dir / "ordering_geometry_per_case.csv",
                ordering_rows,
            )
            write_csv(
                instrumentation_dir / "adapter_block_per_case.csv",
                block_rows,
            )
            with open(
                instrumentation_dir / "token_arrays_manifest.jsonl",
                "w",
                encoding="utf-8",
            ) as handle:
                for row in manifest_rows:
                    handle.write(json.dumps(row) + "\n")
            metric_args.extend(["--metrics", f"{seed}={metric_path}"])
            instrumentation_args.extend([
                "--instrumentation", f"{seed}={instrumentation_dir}"
            ])

        out_dir = root / "analysis"
        previous_argv = sys.argv
        try:
            sys.argv = [
                "analyze_skullbreak_mamba_multiseed_posthoc.py",
                *metric_args,
                *instrumentation_args,
                "--panel", str(panel_path),
                "--out_dir", str(out_dir),
            ]
            analysis.main()
        finally:
            sys.argv = previous_argv

        summary = json.loads(
            (out_dir / "posthoc_summary.json").read_text(encoding="utf-8")
        )
        assert summary["num_records"] == 12
        assert summary["num_cases"] == 4
        assert summary["catastrophes_by_seed"] == {"0": 0, "1": 0, "2": 1}
        assert summary["token_equality"]["all_equal"] is True
        assert (out_dir / "posthoc_report_zh.md").is_file()
        assert (out_dir / "instrumentation_correlations.csv").is_file()
        print("[ok] synthetic multiseed post-hoc analysis")
        print("[ok] catastrophe, correlation, token equality, report, checksums")


if __name__ == "__main__":
    main()
