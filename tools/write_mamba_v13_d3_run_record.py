#!/usr/bin/env python3
"""Write one immutable, receipt-bound D3 candidate run record."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

import yaml


VERSION = "mamba-v13-d3-run-record-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite non-identical run record: {path}")
        print(f"[locked] existing run record is byte-identical: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in (
        "candidate", "fold", "seed", "config", "checkpoint",
        "metrics_csv", "metrics_summary", "efficiency", "training_log",
        "authorization_receipt", "smoke_receipt", "expected_case_ids",
        "output",
    ):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--extra_artifact", action="append", default=[])
    args = parser.parse_args()
    if args.candidate not in {"S0", "S1", "S2"}:
        raise ValueError("candidate must be S0, S1, or S2")
    if args.fold not in "ABCD" or int(args.seed) < 0:
        raise ValueError("invalid fold or seed")

    raw_paths = {
        name: Path(getattr(args, name))
        for name in (
            "config", "checkpoint", "metrics_csv", "metrics_summary",
            "efficiency", "training_log", "authorization_receipt",
            "smoke_receipt", "expected_case_ids",
        )
    }
    for item in args.extra_artifact:
        if "=" not in item:
            raise ValueError(f"Invalid --extra_artifact: {item!r}")
        name, value = item.split("=", 1)
        if not name or name in raw_paths:
            raise ValueError(f"Invalid/duplicate artifact name: {name!r}")
        raw_paths[name] = Path(value)
    paths = {
        name: (path if path.is_absolute() else Path.cwd() / path).resolve()
        for name, path in raw_paths.items()
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Run-record artifacts missing: {missing}")

    config = yaml.safe_load(paths["config"].read_text(encoding="utf-8"))
    execution = config["d3_execution"]
    if not (
        execution["candidate"] == args.candidate
        and execution["fold"] == args.fold
        and int(execution["seed"]) == int(args.seed)
        and execution["training_authorized"] is True
        and execution["holdout_authorized"] is False
        and execution["selection_started"] is False
    ):
        raise RuntimeError("Config execution authorization does not match this run")

    expected_ids = {
        line.strip()
        for line in paths["expected_case_ids"].read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    with paths["metrics_csv"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    observed_ids = [str(row["case_id"]) for row in rows]
    if (
        len(rows) != 100
        or len(observed_ids) != len(set(observed_ids))
        or set(observed_ids) != expected_ids
    ):
        raise RuntimeError("D3 dev metrics do not exactly match the frozen fold case set")
    required_columns = {
        "final_cd_l1_mm", "final_hd95_mm", "final_nsd_at_1mm",
        "rim_contact_hd95_mm", "rim_predicted_rim_points",
        "coarse_predicted_rim_points",
    }
    if not required_columns.issubset(rows[0]):
        raise RuntimeError(
            f"D3 metrics omit required columns: {sorted(required_columns - set(rows[0]))}"
        )

    efficiency = json.loads(paths["efficiency"].read_text(encoding="utf-8"))
    for key in (
        "latency_ms_median", "peak_gpu_memory_bytes", "parameter_count_total",
    ):
        try:
            value = float(efficiency[key])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Efficiency artifact omits {key}") from exc
        if not math.isfinite(value) or value <= 0:
            raise RuntimeError(f"Efficiency field {key} is invalid")

    epoch_times = [
        float(value)
        for value in re.findall(
            r"EpochTime\s*=\s*([0-9.]+)",
            paths["training_log"].read_text(encoding="utf-8", errors="replace"),
        )
    ]
    if len(epoch_times) < 100:
        raise RuntimeError(
            f"Training log has {len(epoch_times)} EpochTime records; expected at least 100"
        )
    steady = epoch_times[1:]
    payload = {
        "record_version": VERSION,
        "candidate": args.candidate,
        "fold": args.fold,
        "seed": int(args.seed),
        "status": "frozen_complete_development_fold",
        "fixed_checkpoint_rule": "epoch-100 ckpt-last plus full fold-train BNCal",
        "dev_cases": len(rows),
        "dev_case_set_exact": True,
        "training_epochs_recorded": len(epoch_times),
        "training_epoch_time_seconds_mean_excluding_first": sum(steady) / len(steady),
        "artifacts": {
            name: {
                "path": str(raw_paths[name]).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for name, path in sorted(paths.items())
        },
        "holdout_inference_consumed": False,
        "holdout_metrics_consumed": False,
        "holdout_visual_review_consumed": False,
        "selection_started": False,
    }
    encoded = (
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    output = Path(args.output).resolve()
    write_identical_or_new(output, encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    write_identical_or_new(
        Path(str(output) + ".sha256"),
        f"{digest}  {output.name}\n".encode("ascii"),
    )
    print(f"[saved] immutable D3 run record: {output}")
    print("[locked] no holdout access and no selection")


if __name__ == "__main__":
    main()
