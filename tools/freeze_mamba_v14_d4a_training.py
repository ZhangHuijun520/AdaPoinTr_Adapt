#!/usr/bin/env python3
"""Freeze the all-case D4-A gate after all four authorized folds finish."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence


VERSION = "mamba-v14-d4a-training-completion-v1"
FOLD_VERSION = "mamba-v14-d4a-head-only-training-fold-v1"
FOLDS = ("A", "B", "C", "D")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def csv_bytes(fieldnames: Sequence[str], rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def verify_manifest(root: Path) -> str:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing files.sha256: {root}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen fold artifact mismatch: {path}")
    return sha256_file(manifest)


def render_report(receipt: Mapping[str, Any]) -> bytes:
    passed = receipt["D4A_all_case_gate_passed"]
    decision = (
        "D4-A 通过；下一步仅允许单独物化 T0/T1/T2 Round-A 配置。"
        if passed
        else "D4-A 未通过；T0/T1/T2 Round A 被禁止。"
    )
    return (
        "# Mamba v1.4 D4-A head-only feasibility 冻结结果\n\n"
        "> 四折 head-only 训练和一次性 out-of-fold dev gate；不访问保护数据。\n\n"
        f"- cases：{receipt['development_cases']}。\n"
        f"- selected hits：{receipt['selected_hits']}。\n"
        f"- misses：{receipt['selected_misses']}。\n"
        f"- all outputs finite：`{receipt['all_required_outputs_finite']}`。\n"
        f"- all-case gate passed：`{passed}`。\n"
        f"- protected data accessed：`{receipt['protected_data_accessed']}`。\n"
        f"- 结论：{decision}\n"
    ).encode("utf-8")


def verify_existing(output: Path) -> bool:
    if not output.exists():
        return False
    verify_manifest(output)
    receipt = json.loads(
        (output / "d4a_training_completion_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    if not (
        receipt.get("completion_version") == VERSION
        and receipt.get("development_cases") == 400
        and receipt.get("D4_candidate_selection_authorized") is False
        and receipt.get("protected_data_accessed") is False
    ):
        raise RuntimeError("Existing D4-A completion receipt is invalid")
    print(f"[locked] existing D4-A completion is valid: {output}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fold_root", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    fold_root = args.fold_root.resolve()
    auth_dir = args.authorization_dir.resolve()
    output = args.output_dir.resolve()
    if verify_existing(output):
        return
    working = output.with_name(f".{output.name}.working")
    if output.exists() or working.exists():
        raise RuntimeError(f"D4-A completion output requires inspection: {output}")

    verify_manifest(auth_dir)
    authorization_path = auth_dir / "d4a_training_authorization_receipt.json"
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    if not (
        authorization.get("status")
        == "D4A_head_only_seed0_folds_A_D_training_authorized"
        and authorization.get("D4A_training_authorized") is True
        and authorization.get("T0_training_authorized") is False
        and authorization.get("T1_training_authorized") is False
        and authorization.get("T2_training_authorized") is False
        and authorization.get("protected_data_accessed") is False
    ):
        raise RuntimeError("D4-A completion authorization is invalid")

    rows: list[dict[str, str]] = []
    fold_receipts: dict[str, Any] = {}
    case_ids: set[str] = set()
    source_fold: dict[str, str] = {}
    all_finite = True
    for fold in FOLDS:
        root = fold_root / f"fold{fold}_seed0"
        manifest_sha = verify_manifest(root)
        receipt_path = root / "run_receipt.json"
        summary_path = root / "fold_summary.json"
        metrics_path = root / "development_per_case.csv"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        with metrics_path.open(encoding="utf-8", newline="") as handle:
            fold_rows = list(csv.DictReader(handle))
        if not (
            receipt.get("run_version") == FOLD_VERSION
            and receipt.get("fold") == fold
            and receipt.get("optimizer_steps") == 1900
            and receipt.get("development_evaluation_count") == 1
            and receipt.get("protected_data_accessed") is False
            and summary.get("fold") == fold
            and summary.get("development_cases") == 100
            and summary.get("optimizer_steps") == 1900
            and summary.get("development_evaluation_count") == 1
            and summary.get("protected_data_accessed") is False
            and all(
                math.isfinite(float(summary[key]))
                for key in (
                    "final_training_loss",
                    "final_learning_rate",
                    "maximum_preclip_gradient_norm",
                )
            )
            and len(fold_rows) == 100
        ):
            raise RuntimeError(f"D4-A fold {fold} result semantics are invalid")
        for row in fold_rows:
            case_id = row["case_id"]
            source = row["source_skull_id"]
            if (
                case_id in case_ids
                or row["fold"] != fold
                or int(row["positive_candidate_count"]) <= 0
                or not 0 <= int(row["selected_positive_count"]) <= 32
                or int(row["selected_hit"])
                != int(int(row["selected_positive_count"]) > 0)
            ):
                raise RuntimeError(f"D4-A fold {fold} case pairing failed")
            case_ids.add(case_id)
            if source in source_fold and source_fold[source] != fold:
                raise RuntimeError(f"Source appears in multiple dev folds: {source}")
            source_fold[source] = fold
            finite = all(
                math.isfinite(float(row[key]))
                for key in ("logit_min", "logit_max")
            )
            all_finite = all_finite and finite
            rows.append(row)
        fold_receipts[fold] = {
            "files_manifest_sha256": manifest_sha,
            "run_receipt_sha256": sha256_file(receipt_path),
            "fold_summary_sha256": sha256_file(summary_path),
            "development_per_case_sha256": sha256_file(metrics_path),
            "head_final_epoch_sha256": sha256_file(root / "head_final_epoch.pth"),
            "hits": int(summary["case_hits"]),
            "passed": bool(summary["fold_gate_passed"]),
        }

    rows.sort(key=lambda row: row["case_id"])
    source_counts = Counter(row["source_skull_id"] for row in rows)
    hits = sum(int(row["selected_hit"]) for row in rows)
    passed = (
        len(rows) == 400
        and len(case_ids) == 400
        and len(source_fold) == 100
        and set(source_counts.values()) == {4}
        and hits == 400
        and all_finite
        and all(item["passed"] for item in fold_receipts.values())
    )
    receipt = {
        "completion_version": VERSION,
        "status": (
            "D4A_all_case_gate_passed"
            if passed
            else "D4A_frozen_negative_all_case_gate_failed"
        ),
        "candidate": "D4A",
        "seed": 0,
        "folds": fold_receipts,
        "authorization_receipt_sha256": sha256_file(authorization_path),
        "development_cases": len(rows),
        "development_sources": len(source_fold),
        "selected_hits": hits,
        "selected_misses": len(rows) - hits,
        "all_required_outputs_finite": all_finite,
        "exact_case_pairing": len(case_ids) == 400,
        "D4A_all_case_gate_passed": passed,
        "T0_T1_T2_materialization_authorized_next": passed,
        "T0_training_authorized": False,
        "T1_training_authorized": False,
        "T2_training_authorized": False,
        "D4_candidate_selection_authorized": False,
        "protected_data_accessed": False,
        "selection_started": False,
        "next_step": (
            "separate_T0_T1_T2_round_A_materialization"
            if passed
            else "freeze_D4A_negative_and_stop_D4_round_A"
        ),
    }
    files = {
        "d4a_all_case_metrics.csv": csv_bytes(list(rows[0]), rows),
        "d4a_training_completion_receipt.json": canonical_json(receipt),
        "d4a_training_result_zh.md": render_report(receipt),
    }
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    manifest_payload = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    (working / "files.sha256").write_bytes(manifest_payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(working, output)
    print(f"[saved] immutable D4-A completion: {output}")
    print(f"[gate] hits={hits}/400 passed={passed}")
    if passed:
        print("[authorized-next] separate T0/T1/T2 materialization only")
    else:
        print("[negative] T0/T1/T2 Round A remains forbidden")
    print("[locked] selection=false protected=false no automatic full training")


if __name__ == "__main__":
    main()
