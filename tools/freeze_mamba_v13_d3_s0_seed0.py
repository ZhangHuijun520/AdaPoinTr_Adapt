#!/usr/bin/env python3
"""Freeze the four-fold D3 S0 seed-0 reference completion receipt."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


FOLDS = ("A", "B", "C", "D")
VERSION = "mamba-v13-d3-s0-seed0-completion-v1"
GATE_METRICS = (
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_hd95_mm",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_artifact(path: str, repo_root: Path) -> Path:
    result = Path(path)
    if not result.is_absolute():
        result = repo_root / result
    return result.resolve()


def portable_path(path: Path, repo_root: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def verify_sidecar(path: Path) -> None:
    sidecar = Path(str(path) + ".sha256")
    expected, name = sidecar.read_text(encoding="ascii").split()[:2]
    if Path(name).name != path.name or sha256_file(path) != expected.lower():
        raise RuntimeError(f"SHA256 sidecar mismatch: {path}")


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite non-identical completion receipt: {path}")
        print(f"[locked] existing completion receipt is byte-identical: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def load_fold(record_path: Path, fold: str, repo_root: Path):
    verify_sidecar(record_path)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if not (
        record.get("record_version") == "mamba-v13-d3-run-record-v1"
        and record.get("status") == "frozen_complete_development_fold"
        and record.get("candidate") == "S0"
        and record.get("fold") == fold
        and record.get("seed") == 0
        and record.get("dev_cases") == 100
        and record.get("holdout_inference_consumed") is False
        and record.get("holdout_metrics_consumed") is False
        and record.get("holdout_visual_review_consumed") is False
        and record.get("selection_started") is False
    ):
        raise RuntimeError(f"Invalid frozen S0 run record: {record_path}")
    for name, artifact in record["artifacts"].items():
        path = resolve_artifact(artifact["path"], repo_root)
        if not path.is_file() or sha256_file(path) != artifact["sha256"]:
            raise RuntimeError(f"Fold {fold} artifact mismatch ({name}): {path}")

    metrics_path = resolve_artifact(
        record["artifacts"]["metrics_csv"]["path"], repo_root
    )
    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 100:
        raise RuntimeError(f"Fold {fold}: expected 100 metric rows")
    for row in rows:
        row["fold"] = fold

    efficiency_path = resolve_artifact(
        record["artifacts"]["efficiency"]["path"], repo_root
    )
    efficiency = json.loads(efficiency_path.read_text(encoding="utf-8"))
    return record, rows, efficiency


def as_float(row, key):
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return float("nan")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--authorization_receipt", type=Path, required=True)
    parser.add_argument("--smoke_receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo_root = Path.cwd().resolve()
    records_root = args.records_root.resolve()
    auth = args.authorization_receipt.resolve()
    smoke = args.smoke_receipt.resolve()
    verify_sidecar(auth)
    verify_sidecar(smoke)

    all_rows = []
    run_records = {}
    fold_efficiency = {}
    for fold in FOLDS:
        path = records_root / f"S0_fold{fold}_seed0" / "run_record.json"
        record, rows, efficiency = load_fold(path, fold, repo_root)
        run_records[fold] = {
            "path": portable_path(path, repo_root),
            "sha256": sha256_file(path),
        }
        all_rows.extend(rows)
        fold_efficiency[fold] = {
            "parameter_count_total": int(efficiency["parameter_count_total"]),
            "parameter_count_trainable": int(
                efficiency["parameter_count_trainable"]
            ),
            "latency_ms_median": float(efficiency["latency_ms_median"]),
            "peak_gpu_memory_bytes": int(efficiency["peak_gpu_memory_bytes"]),
        }

    identities = [(row["case_id"], row["fold"]) for row in all_rows]
    case_ids = [row["case_id"] for row in all_rows]
    if len(all_rows) != 400 or len(identities) != len(set(identities)):
        raise RuntimeError("S0 completion does not contain 400 unique case+fold rows")
    if len(case_ids) != len(set(case_ids)):
        raise RuntimeError("D3 cross-validation case IDs must appear in exactly one dev fold")

    disasters = 0
    zero_dense = 0
    zero_coarse = 0
    finite_counts = {key: 0 for key in GATE_METRICS}
    for row in all_rows:
        values = {key: as_float(row, key) for key in GATE_METRICS}
        finite = all(math.isfinite(value) for value in values.values())
        if not finite or values["rim_contact_hd95_mm"] > 50.0:
            disasters += 1
        zero_dense += int(as_float(row, "rim_predicted_rim_points") <= 0)
        zero_coarse += int(as_float(row, "coarse_predicted_rim_points") <= 0)
        for key, value in values.items():
            finite_counts[key] += int(math.isfinite(value))

    means = {}
    for key in GATE_METRICS:
        values = np.asarray([as_float(row, key) for row in all_rows], dtype=np.float64)
        means[key] = float(np.mean(values)) if np.isfinite(values).all() else None
    rim_hd95 = np.asarray(
        [as_float(row, "rim_contact_hd95_mm") for row in all_rows],
        dtype=np.float64,
    )
    rim_p95 = (
        float(np.percentile(rim_hd95, 95, method="linear"))
        if np.isfinite(rim_hd95).all()
        else None
    )

    payload = {
        "completion_version": VERSION,
        "status": "S0_seed0_frozen_ready_for_S2_feasibility",
        "candidate": "S0",
        "seed": 0,
        "folds": list(FOLDS),
        "development_cases": 400,
        "case_fold_records_unique": True,
        "cross_fold_case_ids_unique": True,
        "run_records": run_records,
        "authorization_receipt": {
            "path": portable_path(auth, repo_root),
            "sha256": sha256_file(auth),
        },
        "smoke_receipt": {
            "path": portable_path(smoke, repo_root),
            "sha256": sha256_file(smoke),
        },
        "reference_summary": {
            "means": means,
            "finite_counts": finite_counts,
            "disaster_count": disasters,
            "dense_zero_contact_at_2mm_count": zero_dense,
            "coarse_zero_support_at_2mm_count": zero_coarse,
            "rim_contact_hd95_p95_mm_linear": rim_p95,
        },
        "fold_efficiency": fold_efficiency,
        "S1_authorized": False,
        "S2_full_training_authorized": False,
        "S2_head_only_feasibility_authorized_next": True,
        "holdout_authorized": False,
        "holdout_inference_consumed": False,
        "holdout_metrics_consumed": False,
        "holdout_visual_review_consumed": False,
        "selection_started": False,
        "next_step": "run_same_fold_frozen_S0_BNCal_encoder_S2_head_only_feasibility",
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output = args.output.resolve()
    write_identical_or_new(output, encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    write_identical_or_new(
        Path(str(output) + ".sha256"),
        f"{digest}  {output.name}\n".encode("ascii"),
    )
    print(f"[saved] S0 completion receipt: {output}")
    print(f"[summary] cases=400 disasters={disasters} dense_zero={zero_dense} coarse_zero={zero_coarse}")
    print("[authorized-next] S2 head-only feasibility only")
    print("[locked] S1=false S2_full=false holdout=false selection_started=false")


if __name__ == "__main__":
    main()
