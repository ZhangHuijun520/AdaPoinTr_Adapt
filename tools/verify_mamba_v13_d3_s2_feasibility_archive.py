#!/usr/bin/env python3
"""Verify a restored D3 S2 feasibility negative-result archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


FOLDS = ("A", "B", "C", "D")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path, manifest: Path) -> None:
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Archive hash mismatch: {path}")


def verify_sidecar(path: Path) -> None:
    fields = Path(str(path) + ".sha256").read_text(encoding="ascii").split()
    if (
        len(fields) < 2
        or Path(fields[1]).name != path.name
        or sha256_file(path) != fields[0].lower()
    ):
        raise RuntimeError(f"Sidecar mismatch: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    metadata = root / "metadata"
    for name in (
        "README.txt",
        "ARCHIVE_PATHS.txt",
        "MANIFEST.sha256",
        "HEAD_CHECKPOINTS.sha256",
        "runtime_environment.txt",
        "python_runtime.txt",
        "pip_freeze.txt",
        "conda_list.txt",
    ):
        if not (metadata / name).is_file() or (metadata / name).stat().st_size == 0:
            raise RuntimeError(f"Missing archive metadata: {metadata / name}")
    verify_manifest(root, metadata / "MANIFEST.sha256")
    verify_manifest(root, metadata / "HEAD_CHECKPOINTS.sha256")
    parent_lock = metadata / "parent_round_a_protocol_lock"
    verify_manifest(parent_lock, parent_lock / "files.sha256")

    completion_path = root / (
        "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_completion_v1/"
        "s2_head_feasibility_completion_receipt.json"
    )
    verify_sidecar(completion_path)
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    if not (
        completion.get("status") == "failed_preregistered_hard_gate"
        and completion.get("pooled_case_hits") == 392
        and completion.get("S2_full_training_authorized") is False
        and completion.get("holdout_accessed") is False
        and completion.get("selection_started") is False
    ):
        raise RuntimeError("Archived completion semantics are invalid")

    all_rows = []
    checkpoints = []
    for fold in FOLDS:
        fold_root = root / (
            "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_v1/"
            f"fold{fold}_seed0"
        )
        run_path = fold_root / "run_receipt.json"
        verify_sidecar(run_path)
        run = json.loads(run_path.read_text(encoding="utf-8"))
        if not (
            run.get("fold") == fold
            and run.get("development_cases") == 100
            and run.get("S2_full_training_authorized") is False
            and run.get("holdout_accessed") is False
        ):
            raise RuntimeError(f"Archived fold {fold} semantics are invalid")
        for artifact_name in ("head_only_checkpoint", "per_case_csv", "summary"):
            artifact = run["artifacts"][artifact_name]
            path = root / artifact["path"]
            if not path.is_file() or sha256_file(path) != artifact["sha256"]:
                raise RuntimeError(f"Fold {fold} artifact mismatch: {path}")
        checkpoints.append(root / run["artifacts"]["head_only_checkpoint"]["path"])
        csv_path = root / run["artifacts"]["per_case_csv"]["path"]
        with csv_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 100:
            raise RuntimeError(f"Fold {fold} does not contain 100 cases")
        all_rows.extend(rows)

    if len(checkpoints) != 4 or len({path.as_posix() for path in checkpoints}) != 4:
        raise RuntimeError("Archive must contain four unique head checkpoints")
    pth_files = list(root.rglob("*.pth"))
    if set(pth_files) != set(checkpoints):
        raise RuntimeError("Archive contains unexpected model checkpoints")
    case_ids = [row["case_id"] for row in all_rows]
    hits = sum(int(row["case_hit"]) for row in all_rows)
    if len(all_rows) != 400 or len(set(case_ids)) != 400 or hits != 392:
        raise RuntimeError("Archived per-case universe or hit count is invalid")

    for tree in (
        root / "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1",
        root / "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_hotfix1",
        root / "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_negative_freeze_v1",
    ):
        verify_manifest(tree, tree / "files.sha256")
    freeze = json.loads(
        (
            root
            / "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_negative_freeze_v1/negative_result_receipt.json"
        ).read_text(encoding="utf-8")
    )
    if not (
        freeze.get("status") == "frozen_negative_high_hit_rate_failed_all_case_safety_gate"
        and freeze.get("S2_weight_calibration_authorized") is False
        and freeze.get("S1_weight_calibration_authorized") is False
        and freeze.get("holdout_accessed") is False
    ):
        raise RuntimeError("Archived negative freeze semantics are invalid")

    print("[ok] archive manifests and four head checkpoints match")
    print("[ok] 400 unique cases, 392 hits, and eight misses are frozen")
    print("[ok] base lock, hotfix1, completion, and negative receipt are valid")
    print("[locked] S2 calibration=false S2 full=false holdout=false selection=false")


if __name__ == "__main__":
    main()
