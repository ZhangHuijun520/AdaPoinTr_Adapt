#!/usr/bin/env python3
"""Freeze the four-fold S1 training-only gradient calibration completion."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-completion-v1"
FOLD_VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-fold-v1"
AUTH_VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-authorization-v1"
FOLDS = ("A", "B", "C", "D")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_tree(root: Path) -> None:
    for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, raw_name = line.split(maxsplit=1)
        path = root / raw_name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"S1 calibration tree mismatch: {path}")


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite non-identical S1 completion: {path}")
        print(f"[locked] existing S1 calibration completion is byte-identical: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs_root", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    runs_root = args.runs_root.resolve()
    authorization_dir = args.authorization_dir.resolve()
    output = args.output.resolve()
    verify_tree(authorization_dir)
    auth_path = authorization_dir / "s1_calibration_authorization_receipt.json"
    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    if not (
        auth.get("authorization_version") == AUTH_VERSION
        and auth.get("S1_calibration_authorized") is True
        and auth.get("S1_training_authorized") is False
        and auth.get("holdout_authorized") is False
        and auth.get("selection_started") is False
    ):
        raise RuntimeError("S1 calibration authorization is invalid")

    folds = {}
    all_measured = []
    for fold in FOLDS:
        run_dir = runs_root / f"fold{fold}_seed0"
        verify_tree(run_dir)
        receipt_path = run_dir / "calibration_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        weight = float(receipt.get("calibrated_weight", float("nan")))
        ratio = float(receipt.get("fold_raw_ratio_median", float("nan")))
        case_ids = [
            line.strip()
            for line in (run_dir / "batch_case_ids.txt").read_text().splitlines()
            if line.strip()
        ]
        if not (
            receipt.get("calibration_version") == FOLD_VERSION
            and receipt.get("status") == "S1_fold_calibration_frozen"
            and receipt.get("candidate") == "S1"
            and receipt.get("fold") == fold
            and receipt.get("seed") == 0
            and receipt.get("batch_count") == 8
            and receipt.get("batch_size") == 8
            and receipt.get("measured_case_slots") == 64
            and receipt.get("measured_unique_cases") == 64
            and len(case_ids) == len(set(case_ids)) == 64
            and receipt.get("optimizer_constructed") is False
            and receipt.get("optimizer_steps") == 0
            and receipt.get("checkpoint_loaded") is False
            and receipt.get("checkpoint_written") is False
            and receipt.get("model_state_restored") is True
            and receipt.get("rng_state_restored") is True
            and receipt.get("development_loader_constructed") is False
            and receipt.get("development_metrics_consumed") is False
            and receipt.get("holdout_accessed") is False
            and receipt.get("S1_training_authorized") is False
            and receipt.get("S2_calibration_authorized") is False
            and receipt.get("S2_full_training_authorized") is False
            and receipt.get("selection_started") is False
            and math.isfinite(ratio) and ratio > 0
            and math.isfinite(weight) and weight > 0
            and math.isclose(weight, 0.075 / ratio, rel_tol=1e-14, abs_tol=0.0)
        ):
            raise RuntimeError(f"S1 fold {fold} calibration semantics are invalid")
        folds[fold] = {
            "receipt": {"path": portable(receipt_path), "sha256": sha256_file(receipt_path)},
            "batch_case_ids_sha256": receipt["batch_case_ids_sha256"],
            "fold_raw_ratio_median": ratio,
            "calibrated_weight": weight,
        }
        all_measured.extend(case_ids)

    payload = {
        "completion_version": VERSION,
        "status": "S1_gradient_ratio_calibration_frozen_complete",
        "candidate": "S1",
        "seed": 0,
        "folds": folds,
        "fold_count": 4,
        "batch_count_total": 32,
        "measured_case_slots_total": 256,
        "measured_unique_case_fold_pairs": len(all_measured),
        "target_gradient_ratio": 0.075,
        "authorization_receipt": {
            "path": portable(auth_path),
            "sha256": sha256_file(auth_path),
        },
        "weights_clipped_rounded_or_manually_adjusted": False,
        "optimizer_steps": 0,
        "development_metrics_consumed": False,
        "S1_runtime_config_materialization_authorized_next": True,
        "S1_training_authorized": False,
        "S2_calibration_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_authorized": False,
        "selection_started": False,
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_identical_or_new(output, encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    write_identical_or_new(
        Path(str(output) + ".sha256"),
        f"{digest}  {output.name}\n".encode("ascii"),
    )
    print(f"[saved] S1 calibration completion receipt: {output}")
    for fold in FOLDS:
        print(f"[weight] fold{fold}={folds[fold]['calibrated_weight']:.10g}")
    print("[authorized-next] receipt-bound S1 runtime config materialization only")
    print("[locked] training=false S2=false holdout=false selection=false")


if __name__ == "__main__":
    main()
