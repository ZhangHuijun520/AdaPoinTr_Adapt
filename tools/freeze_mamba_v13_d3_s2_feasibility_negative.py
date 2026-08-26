#!/usr/bin/env python3
"""Freeze the failed D3 S2 head-only feasibility result and its provenance."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
FOLDS = ("A", "B", "C", "D")
VERSION = "mamba-v13-d3-s2-head-feasibility-negative-freeze-v1"


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


def verify_tree(root: Path) -> None:
    manifest = root / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Hash-tree mismatch: {path}")


def verify_artifacts(record: dict) -> None:
    for artifact in record["artifacts"].values():
        path = resolve(artifact["path"])
        if not path.is_file() or sha256_file(path) != artifact["sha256"]:
            raise RuntimeError(f"Frozen artifact mismatch: {path}")


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing non-identical freeze artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs_root", type=Path, required=True)
    parser.add_argument("--completion", type=Path, required=True)
    parser.add_argument("--base_lock_dir", type=Path, required=True)
    parser.add_argument("--hotfix_dir", type=Path, required=True)
    parser.add_argument("--s0_completion", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    runs_root = args.runs_root.resolve()
    completion_path = args.completion.resolve()
    base_lock = args.base_lock_dir.resolve()
    hotfix = args.hotfix_dir.resolve()
    s0_completion_path = args.s0_completion.resolve()
    report_path = args.report.resolve()
    output = args.output_dir.resolve()

    verify_sidecar(completion_path)
    verify_sidecar(s0_completion_path)
    verify_tree(base_lock)
    verify_tree(hotfix)
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    if not (
        completion.get("status") == "failed_preregistered_hard_gate"
        and completion.get("development_cases") == 400
        and completion.get("pooled_case_hits") == 392
        and math.isclose(completion.get("pooled_case_hit_rate"), 0.98)
        and completion.get("S2_full_training_authorized") is False
        and completion.get("holdout_accessed") is False
        and completion.get("selection_started") is False
    ):
        raise RuntimeError("Completion receipt is not the frozen S2 negative result")

    s0_completion = json.loads(s0_completion_path.read_text(encoding="utf-8"))
    if not (
        s0_completion.get("status") == "S0_seed0_frozen_ready_for_S2_feasibility"
        and s0_completion.get("S2_full_training_authorized") is False
        and s0_completion.get("holdout_authorized") is False
    ):
        raise RuntimeError("S0 completion lineage is invalid")
    s0_checkpoint_hashes = {}
    for fold in FOLDS:
        run_path = resolve(s0_completion["run_records"][fold]["path"])
        verify_sidecar(run_path)
        run = json.loads(run_path.read_text(encoding="utf-8"))
        verify_artifacts(run)
        checkpoint = run["artifacts"]["checkpoint"]
        s0_checkpoint_hashes[fold] = checkpoint

    all_rows = []
    run_receipts = {}
    head_checkpoints = {}
    for fold in FOLDS:
        run_path = runs_root / f"fold{fold}_seed0" / "run_receipt.json"
        verify_sidecar(run_path)
        run = json.loads(run_path.read_text(encoding="utf-8"))
        if not (
            run.get("fold") == fold
            and run.get("development_cases") == 100
            and run.get("full_S2_reuses_feasibility_head") is False
            and run.get("S2_full_training_authorized") is False
            and run.get("holdout_accessed") is False
            and run.get("selection_started") is False
        ):
            raise RuntimeError(f"Invalid fold receipt: {run_path}")
        verify_artifacts(run)
        csv_path = resolve(run["artifacts"]["per_case_csv"]["path"])
        with csv_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 100 or any(row["fold"] != fold for row in rows):
            raise RuntimeError(f"Fold {fold} per-case records are invalid")
        all_rows.extend(rows)
        run_receipts[fold] = {"path": portable(run_path), "sha256": sha256_file(run_path)}
        head_checkpoints[fold] = run["artifacts"]["head_only_checkpoint"]

    case_ids = [row["case_id"] for row in all_rows]
    if len(all_rows) != 400 or len(set(case_ids)) != 400:
        raise RuntimeError("Expected 400 unique development cases")
    misses = [row for row in all_rows if int(row["case_hit"]) == 0]
    if len(misses) != 8:
        raise RuntimeError(f"Expected eight missed cases, found {len(misses)}")
    fold_hits = {
        fold: sum(int(row["case_hit"]) for row in all_rows if row["fold"] == fold)
        for fold in FOLDS
    }
    expected_fold_hits = {"A": 98, "B": 96, "C": 98, "D": 100}
    if fold_hits != expected_fold_hits:
        raise RuntimeError(f"Unexpected fold hit counts: {fold_hits}")

    metric_names = (
        "positive_proxy_recall",
        "precision",
        "false_positive_rate",
        "selected_anchor_spatial_coverage_mm",
    )
    means = {
        key: float(np.mean([float(row[key]) for row in all_rows]))
        for key in metric_names
    }
    for key, expected in completion["pooled_means"].items():
        if not math.isclose(means[key], float(expected), rel_tol=0.0, abs_tol=1e-12):
            raise RuntimeError(f"Pooled metric differs from completion receipt: {key}")

    missed_fields = list(misses[0])
    from io import StringIO
    missed_buffer = StringIO(newline="")
    writer = csv.DictWriter(missed_buffer, fieldnames=missed_fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(misses)
    missed_bytes = missed_buffer.getvalue().encode("utf-8")
    summary = {
        "freeze_version": VERSION,
        "status": "frozen_negative_high_hit_rate_failed_all_case_safety_gate",
        "development_cases": 400,
        "case_hits": 392,
        "case_hit_rate": 0.98,
        "fold_hits": fold_hits,
        "pooled_means": means,
        "missed_cases": 8,
        "missed_source_skulls": len({row["source_skull_id"] for row in misses}),
        "missed_defect_counts": dict(sorted(Counter(row["defect_type"] for row in misses).items())),
        "missed_positive_proxy_count_range": [
            min(int(row["positive_proxy_count"]) for row in misses),
            max(int(row["positive_proxy_count"]) for row in misses),
        ],
        "S2_full_training_authorized": False,
        "S2_weight_calibration_authorized": False,
        "S1_weight_calibration_authorized": False,
        "S1_weight_calibration_may_be_separately_authorized": True,
        "holdout_accessed": False,
        "selection_started": False,
    }
    summary_bytes = canonical_json(summary)
    receipt = {
        **summary,
        "completion_receipt": {"path": portable(completion_path), "sha256": sha256_file(completion_path)},
        "base_lock_receipt": {
            "path": portable(base_lock / "feasibility_lock_receipt.json"),
            "sha256": sha256_file(base_lock / "feasibility_lock_receipt.json"),
        },
        "hotfix_receipt": {
            "path": portable(hotfix / "hotfix_receipt.json"),
            "sha256": sha256_file(hotfix / "hotfix_receipt.json"),
        },
        "s0_completion_receipt": {
            "path": portable(s0_completion_path),
            "sha256": sha256_file(s0_completion_path),
        },
        "s0_checkpoint_hashes": s0_checkpoint_hashes,
        "feasibility_run_receipts": run_receipts,
        "head_only_checkpoints": head_checkpoints,
        "report": {"path": portable(report_path), "sha256": sha256_file(report_path)},
        "head_checkpoint_reuse_for_full_S2": "forbidden",
        "S2_rerun_or_parameter_revision": "forbidden",
        "next_step": "create_separate_S1_training_only_weight_calibration_authorization",
    }
    receipt_bytes = canonical_json(receipt)
    files = {
        "aggregate_summary.json": summary_bytes,
        "missed_cases.csv": missed_bytes,
        "negative_result_receipt.json": receipt_bytes,
    }
    files["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    if output.exists():
        extras = {path.name for path in output.iterdir()} - set(files)
        if extras:
            raise RuntimeError(f"Refusing freeze directory extras: {sorted(extras)}")
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in files.items():
        write_identical_or_new(output / name, payload)
    verify_tree(output)
    print(f"[saved] S2 feasibility negative freeze: {output}")
    print("[result] hits=392/400; folds=A98 B96 C98 D100; hard gate failed")
    print("[locked] S2 calibration=false S2 full=false holdout=false selection=false")
    print("[next] S1 calibration requires a separate future authorization receipt")


if __name__ == "__main__":
    main()
