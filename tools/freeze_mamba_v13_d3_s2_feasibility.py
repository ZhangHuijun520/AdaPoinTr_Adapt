#!/usr/bin/env python3
"""Freeze the four-fold D3 S2 head-only feasibility decision."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
FOLDS = ("A", "B", "C", "D")
VERSION = "mamba-v13-d3-s2-head-feasibility-completion-v1"
RUN_VERSION = "mamba-v13-d3-s2-head-feasibility-fold-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def resolve(path: str | Path) -> Path:
    result = Path(path)
    if not result.is_absolute():
        result = REPO_ROOT / result
    return result.resolve()


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def verify_sidecar(path: Path) -> None:
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    if (
        len(fields) < 2
        or Path(fields[1]).name != path.name
        or sha256_file(path) != fields[0].lower()
    ):
        raise RuntimeError(f"SHA256 sidecar mismatch: {path}")


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing non-identical completion receipt: {path}")
        print(f"[locked] existing completion receipt is byte-identical: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs_root", type=Path, required=True)
    parser.add_argument("--lock_dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runs_root = args.runs_root.resolve()
    lock_dir = args.lock_dir.resolve()

    rows = []
    fold_results = {}
    run_records = {}
    for fold in FOLDS:
        receipt_path = runs_root / f"fold{fold}_seed0" / "run_receipt.json"
        verify_sidecar(receipt_path)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not (
            receipt.get("run_version") == RUN_VERSION
            and receipt.get("fold") == fold
            and receipt.get("seed") == 0
            and receipt.get("development_cases") == 100
            and receipt.get("development_evaluation_count") == 1
            and receipt.get("s0_model_frozen") is True
            and receipt.get("only_head_trainable") is True
            and receipt.get("full_S2_reuses_feasibility_head") is False
            and receipt.get("S2_full_training_authorized") is False
            and receipt.get("holdout_accessed") is False
            and receipt.get("selection_started") is False
        ):
            raise RuntimeError(f"Invalid feasibility fold receipt: {receipt_path}")
        for artifact in receipt["artifacts"].values():
            path = resolve(artifact["path"])
            if not path.is_file() or sha256_file(path) != artifact["sha256"]:
                raise RuntimeError(f"Feasibility artifact mismatch: {path}")
        csv_path = resolve(receipt["artifacts"]["per_case_csv"]["path"])
        with csv_path.open(newline="", encoding="utf-8") as handle:
            fold_rows = list(csv.DictReader(handle))
        if len(fold_rows) != 100 or any(row["fold"] != fold for row in fold_rows):
            raise RuntimeError(f"Fold {fold} per-case records are incomplete")
        hits = sum(int(row["case_hit"]) for row in fold_rows)
        if hits != int(receipt["case_hits"]):
            raise RuntimeError(f"Fold {fold} hit count differs from receipt")
        passed = hits == 100
        if passed != bool(receipt["hard_gate_passed"]):
            raise RuntimeError(f"Fold {fold} hard-gate status is inconsistent")
        rows.extend(fold_rows)
        fold_results[fold] = {
            "case_hits": hits,
            "development_cases": 100,
            "case_hit_rate": hits / 100.0,
            "hard_gate_passed": passed,
        }
        run_records[fold] = {
            "path": portable(receipt_path),
            "sha256": sha256_file(receipt_path),
        }

    case_ids = [row["case_id"] for row in rows]
    if len(rows) != 400 or len(set(case_ids)) != 400:
        raise RuntimeError("Feasibility completion requires 400 unique dev cases")
    all_passed = all(value["hard_gate_passed"] for value in fold_results.values())
    metric_names = (
        "positive_proxy_recall",
        "precision",
        "false_positive_rate",
        "selected_anchor_spatial_coverage_mm",
    )
    pooled_means = {
        key: float(np.mean([float(row[key]) for row in rows]))
        for key in metric_names
    }
    payload = {
        "completion_version": VERSION,
        "status": "passed_all_folds" if all_passed else "failed_preregistered_hard_gate",
        "seed": 0,
        "development_cases": 400,
        "case_ids_unique": True,
        "fold_results": fold_results,
        "pooled_case_hits": sum(value["case_hits"] for value in fold_results.values()),
        "pooled_case_hit_rate": sum(value["case_hits"] for value in fold_results.values()) / 400.0,
        "pooled_means": pooled_means,
        "run_records": run_records,
        "feasibility_lock": {
            "path": portable(lock_dir / "feasibility_lock_receipt.json"),
            "sha256": sha256_file(lock_dir / "feasibility_lock_receipt.json"),
        },
        "hard_gate": "all_four_folds_100_of_100_case_hits",
        "manual_override": False,
        "rerun_or_hyperparameter_tuning_allowed": False,
        "S1_weight_calibration_may_be_separately_authorized": True,
        "S2_full_weight_calibration_may_be_authorized": all_passed,
        "S2_full_training_authorized": False,
        "full_S2_reuses_feasibility_head": False,
        "holdout_authorized": False,
        "holdout_accessed": False,
        "selection_started": False,
        "next_step": (
            "issue_separate_training_only_weight_calibration_authorization_for_S1_and_S2"
            if all_passed
            else "freeze_S2_feasibility_negative_and_consider_S1_training_only_calibration"
        ),
    }
    encoded = canonical_json(payload)
    output = args.output.resolve()
    write_identical_or_new(output, encoded)
    write_identical_or_new(
        Path(str(output) + ".sha256"),
        f"{hashlib.sha256(encoded).hexdigest()}  {output.name}\n".encode("ascii"),
    )
    print(f"[saved] S2 feasibility completion receipt: {output}")
    print(
        f"[gate] pooled_hits={payload['pooled_case_hits']}/400 "
        f"all_folds_passed={all_passed}"
    )
    if all_passed:
        print("[authorized-next] separate S1/S2 training-only weight calibration receipt")
    else:
        print("[negative] S2 full route remains locked; no feasibility rerun or tuning")
    print("[locked] S2_full=false holdout=false selection_started=false")


if __name__ == "__main__":
    main()
