#!/usr/bin/env python
"""Rebuild voxel summary statistics from an existing per-case CSV."""

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.evaluation_statistics import (  # noqa: E402
    describe_rows,
    paired_comparisons,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--source_summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap_samples", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=20260702)
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.csv, newline="", encoding="utf-8") as handle:
        raw_rows = list(csv.DictReader(handle))

    rows = []
    for raw in raw_rows:
        row = {
            "case_id": raw["case_id"],
            "split": raw["split"],
        }
        for key, value in raw.items():
            if key not in {"case_id", "split"}:
                row[key] = float(value)
        for prefix in ("implant", "final", "input"):
            rve_key = f"{prefix}_rve"
            if rve_key in row:
                row[f"{prefix}_absolute_rve"] = abs(row[rve_key])
        rows.append(row)

    source = json.loads(
        Path(args.source_summary).read_text(encoding="utf-8")
    )
    metric_keys = [
        key for key in rows[0] if key not in {"case_id", "split"}
    ] if rows else []
    statistics = describe_rows(
        rows,
        metric_keys,
        bootstrap_samples=args.bootstrap_samples,
        confidence=args.confidence,
        seed=args.seed,
    )
    summary = {
        "protocol": source["protocol"],
        "num_samples": len(rows),
        "mean": {
            key: values.get("mean")
            for key, values in statistics.items()
        },
        "statistics": statistics,
        "paired_final_vs_input": paired_comparisons(
            rows,
            candidate_prefix="final",
            baseline_prefix="input",
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed + 10000,
        ),
        "per_sample_csv": str(Path(args.csv)),
        "rebuilt_from_existing_csv": True,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[saved] {output}")


if __name__ == "__main__":
    main()
