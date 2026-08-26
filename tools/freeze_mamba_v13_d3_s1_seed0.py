#!/usr/bin/env python3
"""Freeze four S1 seed-0 development-fold records without selection."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


FOLDS = ("A", "B", "C", "D")
VERSION = "mamba-v13-d3-s1-seed0-completion-v1"
METRICS = (
    "final_cd_l1_mm", "final_hd95_mm", "final_nsd_at_1mm",
    "rim_contact_hd95_mm",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sidecar(path: Path) -> None:
    expected, name = Path(str(path) + ".sha256").read_text().split()[:2]
    if Path(name).name != path.name or sha256_file(path) != expected.lower():
        raise RuntimeError(f"SHA256 sidecar mismatch: {path}")


def resolve(path: str, root: Path) -> Path:
    result = Path(path)
    return (result if result.is_absolute() else root / result).resolve()


def portable(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing non-identical S1 completion: {path}")
        print(f"[locked] existing S1 completion is byte-identical: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--authorization_receipt", type=Path, required=True)
    parser.add_argument("--smoke_receipt", type=Path, required=True)
    parser.add_argument("--s0_completion", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path.cwd().resolve()
    auth = args.authorization_receipt.resolve()
    smoke = args.smoke_receipt.resolve()
    s0 = args.s0_completion.resolve()
    for path in (auth, smoke, s0):
        verify_sidecar(path)
    auth_receipt = json.loads(auth.read_text(encoding="utf-8"))
    smoke_receipt = json.loads(smoke.read_text(encoding="utf-8"))
    s0_receipt = json.loads(s0.read_text(encoding="utf-8"))
    if not (
        auth_receipt.get("status") == "S1_seed0_folds_A_D_training_authorized"
        and auth_receipt.get("candidate") == "S1"
        and auth_receipt.get("seed") == 0
        and auth_receipt.get("S1_training_authorized") is True
        and auth_receipt.get("S2_full_training_authorized") is False
        and auth_receipt.get("holdout_authorized") is False
        and auth_receipt.get("selection_started") is False
    ):
        raise RuntimeError("S1 training authorization semantics are invalid")
    if not (
        smoke_receipt.get("status") == "passed_s1_seed0_zero_step_training_probe"
        and smoke_receipt.get("candidate") == "S1"
        and smoke_receipt.get("seed") == 0
        and smoke_receipt.get("folds") == list(FOLDS)
        and smoke_receipt.get("optimizer_steps") == 0
        and smoke_receipt.get("S2_authorized") is False
        and smoke_receipt.get("holdout_authorized") is False
        and smoke_receipt.get("selection_started") is False
    ):
        raise RuntimeError("S1 smoke-test semantics are invalid")
    if not (
        s0_receipt.get("status") == "S0_seed0_frozen_ready_for_S2_feasibility"
        and s0_receipt.get("candidate") == "S0"
        and s0_receipt.get("seed") == 0
        and s0_receipt.get("development_cases") == 400
        and s0_receipt.get("holdout_authorized") is False
        and s0_receipt.get("selection_started") is False
    ):
        raise RuntimeError("S0 reference completion semantics are invalid")
    rows = []
    records = {}
    efficiency = {}
    for fold in FOLDS:
        path = args.records_root.resolve() / f"S1_fold{fold}_seed0" / "run_record.json"
        verify_sidecar(path)
        record = json.loads(path.read_text(encoding="utf-8"))
        if not (
            record.get("status") == "frozen_complete_development_fold"
            and record.get("candidate") == "S1"
            and record.get("fold") == fold
            and record.get("seed") == 0
            and record.get("dev_cases") == 100
            and record.get("holdout_inference_consumed") is False
            and record.get("holdout_metrics_consumed") is False
            and record.get("selection_started") is False
        ):
            raise RuntimeError(f"Invalid S1 run record: fold {fold}")
        for name, artifact in record["artifacts"].items():
            artifact_path = resolve(artifact["path"], repo)
            if not artifact_path.is_file() or sha256_file(artifact_path) != artifact["sha256"]:
                raise RuntimeError(f"Fold {fold} artifact mismatch: {name}")
        metrics_path = resolve(record["artifacts"]["metrics_csv"]["path"], repo)
        with metrics_path.open(newline="", encoding="utf-8") as handle:
            fold_rows = list(csv.DictReader(handle))
        if len(fold_rows) != 100:
            raise RuntimeError(f"Fold {fold}: expected 100 metric rows")
        for row in fold_rows:
            row["fold"] = fold
        rows.extend(fold_rows)
        records[fold] = {"path": portable(path, repo), "sha256": sha256_file(path)}
        eff_path = resolve(record["artifacts"]["efficiency"]["path"], repo)
        eff = json.loads(eff_path.read_text(encoding="utf-8"))
        efficiency[fold] = {
            "parameter_count_total": int(eff["parameter_count_total"]),
            "parameter_count_trainable": int(eff["parameter_count_trainable"]),
            "latency_ms_median": float(eff["latency_ms_median"]),
            "peak_gpu_memory_bytes": int(eff["peak_gpu_memory_bytes"]),
        }
    ids = [(row["case_id"], row["fold"]) for row in rows]
    case_ids = [row["case_id"] for row in rows]
    if len(rows) != 400 or len(ids) != len(set(ids)) or len(case_ids) != len(set(case_ids)):
        raise RuntimeError("S1 completion does not contain 400 unique development cases")
    def value(row, key):
        try:
            return float(row[key])
        except (KeyError, TypeError, ValueError):
            return float("nan")
    disasters = 0
    dense_zero = 0
    coarse_zero = 0
    finite_counts = {key: 0 for key in METRICS}
    for row in rows:
        values = {key: value(row, key) for key in METRICS}
        finite = all(math.isfinite(item) for item in values.values())
        disasters += int(not finite or values["rim_contact_hd95_mm"] > 50.0)
        dense_zero += int(value(row, "rim_predicted_rim_points") <= 0)
        coarse_zero += int(value(row, "coarse_predicted_rim_points") <= 0)
        for key, item in values.items():
            finite_counts[key] += int(math.isfinite(item))
    means = {}
    for key in METRICS:
        array = np.asarray([value(row, key) for row in rows], dtype=np.float64)
        means[key] = float(array.mean()) if np.isfinite(array).all() else None
    rim = np.asarray([value(row, "rim_contact_hd95_mm") for row in rows])
    rim_p95 = float(np.percentile(rim, 95, method="linear")) if np.isfinite(rim).all() else None
    payload = {
        "completion_version": VERSION,
        "status": "S1_seed0_frozen_ready_for_preregistered_gate_analysis",
        "candidate": "S1",
        "seed": 0,
        "folds": list(FOLDS),
        "development_cases": 400,
        "run_records": records,
        "authorization_receipt": {"path": portable(auth, repo), "sha256": sha256_file(auth)},
        "smoke_receipt": {"path": portable(smoke, repo), "sha256": sha256_file(smoke)},
        "s0_reference_completion": {"path": portable(s0, repo), "sha256": sha256_file(s0)},
        "summary": {
            "means": means,
            "finite_counts": finite_counts,
            "disaster_count": disasters,
            "dense_zero_contact_at_2mm_count": dense_zero,
            "coarse_zero_support_at_2mm_count": coarse_zero,
            "rim_contact_hd95_p95_mm_linear": rim_p95,
        },
        "fold_efficiency": efficiency,
        "preregistered_S1_vs_S0_gate_analysis_authorized_next": True,
        "automatic_selection_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_authorized": False,
        "selection_started": False,
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    output = args.output.resolve()
    write_identical_or_new(output, encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    write_identical_or_new(
        Path(str(output) + ".sha256"),
        f"{digest}  {output.name}\n".encode("ascii"),
    )
    print(f"[saved] S1 seed-0 completion receipt: {output}")
    print(f"[summary] cases=400 disasters={disasters} dense_zero={dense_zero} coarse_zero={coarse_zero}")
    print("[authorized-next] preregistered S1-vs-S0 gate analysis only")
    print("[locked] selection=false S2=false holdout=false")


if __name__ == "__main__":
    main()
