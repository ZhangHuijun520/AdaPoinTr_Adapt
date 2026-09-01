#!/usr/bin/env python3
"""Freeze the paired D5-A V0/V1 seed-0 all-case gate."""

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


VERSION = "mamba-v15-d5a-seed0-training-completion-v1"
FOLD_VERSION = "mamba-v15-d5a-seed0-training-fold-v1"
AUTH_VERSION = "mamba-v15-d5a-seed0-training-authorization-v1"
FOLDS = ("A", "B", "C", "D")
CANDIDATES = ("V0", "V1")


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
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
    return sha256_file(manifest)


def render_report(receipt: Mapping[str, Any]) -> bytes:
    passed = receipt["V1_seed0_all_case_gate_passed"]
    decision = (
        "V1 seed-0 通过；下一步只允许单独预注册并签发 V1 seed-1 授权。"
        if passed
        else "V1 seed-0 未通过；D5-A 冻结为负结果并停止。"
    )
    v0, v1 = receipt["candidates"]["V0"], receipt["candidates"]["V1"]
    return (
        "# Mamba v1.5 D5-A V0/V1 seed-0 四折冻结结果\n\n"
        "> 八个 head-only training 与一次性 out-of-fold dev gate；不访问 sealed 数据。\n\n"
        f"- V0 hits/misses：{v0['selected_hits']} / {v0['selected_misses']}。\n"
        f"- V1 hits/misses：{v1['selected_hits']} / {v1['selected_misses']}。\n"
        f"- paired cases：{receipt['paired_development_cases']}。\n"
        f"- V1 all-case gate passed：`{passed}`。\n"
        f"- all outputs finite：`{receipt['all_required_outputs_finite']}`。\n"
        f"- protected/sealed accessed：`{receipt['protected_or_sealed_data_accessed']}`。\n"
        f"- 结论：{decision}\n"
        "- seed-1、confirmation 与 D5-B 不会自动启动。\n"
    ).encode("utf-8")


def verify_existing(output: Path) -> bool:
    if not output.exists():
        return False
    verify_manifest(output)
    receipt = json.loads(
        (output / "d5a_seed0_training_completion_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    if not (
        receipt.get("completion_version") == VERSION
        and receipt.get("paired_development_cases") == 400
        and receipt.get("D5A_seed1_training_authorized") is False
        and receipt.get("D5B_training_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Existing D5-A completion receipt is invalid")
    print(f"[locked] existing D5-A seed-0 completion is valid: {output}")
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
        raise RuntimeError(f"D5-A completion output requires inspection: {output}")

    verify_manifest(auth_dir)
    authorization_path = auth_dir / "d5a_seed0_training_authorization_receipt.json"
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    if not (
        authorization.get("authorization_version") == AUTH_VERSION
        and authorization.get("status")
        == "D5A_V0_V1_seed0_folds_A_D_training_authorized"
        and authorization.get("D5A_seed0_training_authorized") is True
        and authorization.get("D5A_seed1_training_authorized") is False
        and authorization.get("D5B_training_authorized") is False
        and authorization.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("D5-A completion authorization is invalid")

    all_rows: list[dict[str, str]] = []
    candidate_rows: dict[str, list[dict[str, str]]] = {name: [] for name in CANDIDATES}
    candidate_receipts: dict[str, Any] = {name: {} for name in CANDIDATES}
    candidate_case_ids: dict[str, set[str]] = {name: set() for name in CANDIDATES}
    source_fold: dict[str, str] = {}
    all_finite = True
    for candidate in CANDIDATES:
        for fold in FOLDS:
            root = fold_root / f"{candidate}_fold{fold}_seed0"
            manifest_sha = verify_manifest(root)
            receipt_path = root / "run_receipt.json"
            summary_path = root / "fold_summary.json"
            metrics_path = root / "development_per_case.csv"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            with metrics_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            if not (
                receipt.get("run_version") == FOLD_VERSION
                and receipt.get("candidate") == candidate
                and receipt.get("fold") == fold
                and receipt.get("optimizer_steps") == 1900
                and receipt.get("development_evaluation_count") == 1
                and receipt.get("protected_or_sealed_data_accessed") is False
                and summary.get("candidate") == candidate
                and summary.get("fold") == fold
                and summary.get("development_cases") == 100
                and summary.get("optimizer_steps") == 1900
                and summary.get("development_evaluation_count") == 1
                and summary.get("protected_or_sealed_data_accessed") is False
                and all(
                    math.isfinite(float(summary[key]))
                    for key in (
                        "final_training_loss",
                        "final_learning_rate",
                        "maximum_preclip_gradient_norm",
                    )
                )
                and len(rows) == 100
            ):
                raise RuntimeError(f"D5-A {candidate}/fold{fold} semantics are invalid")
            for row in rows:
                case_id = row["case_id"]
                source = row["source_skull_id"]
                if not (
                    case_id not in candidate_case_ids[candidate]
                    and row["candidate"] == candidate
                    and row["fold"] == fold
                    and int(row["positive_candidate_count"]) > 0
                    and 0 <= int(row["selected_positive_count"]) <= 32
                    and int(row["selected_hit"])
                    == int(int(row["selected_positive_count"]) > 0)
                    and int(row["best_positive_rank"]) >= 1
                ):
                    raise RuntimeError(f"D5-A {candidate}/fold{fold} pairing failed")
                candidate_case_ids[candidate].add(case_id)
                if source in source_fold and source_fold[source] != fold:
                    raise RuntimeError(f"Source appears in multiple dev folds: {source}")
                source_fold[source] = fold
                all_finite = all_finite and all(
                    math.isfinite(float(row[key])) for key in ("logit_min", "logit_max")
                )
                candidate_rows[candidate].append(row)
                all_rows.append(row)
            candidate_receipts[candidate][fold] = {
                "files_manifest_sha256": manifest_sha,
                "run_receipt_sha256": sha256_file(receipt_path),
                "fold_summary_sha256": sha256_file(summary_path),
                "development_per_case_sha256": sha256_file(metrics_path),
                "head_final_epoch_sha256": sha256_file(root / "head_final_epoch.pth"),
                "hits": int(summary["case_hits"]),
                "passed": bool(summary["fold_gate_passed"]),
            }

    if candidate_case_ids["V0"] != candidate_case_ids["V1"]:
        raise RuntimeError("V0/V1 all-case pairing is not exact")
    paired_cases = len(candidate_case_ids["V1"])
    source_counts = Counter(row["source_skull_id"] for row in candidate_rows["V1"])
    candidate_summary: dict[str, Any] = {}
    for candidate in CANDIDATES:
        rows = candidate_rows[candidate]
        hits = sum(int(row["selected_hit"]) for row in rows)
        candidate_summary[candidate] = {
            "eligibility_candidate": candidate == "V1",
            "development_cases": len(rows),
            "selected_hits": hits,
            "selected_misses": len(rows) - hits,
            "folds": candidate_receipts[candidate],
            "all_four_folds_passed": all(
                item["passed"] for item in candidate_receipts[candidate].values()
            ),
        }
    v1 = candidate_summary["V1"]
    passed = (
        paired_cases == 400
        and len(source_fold) == 100
        and set(source_counts.values()) == {4}
        and v1["selected_hits"] == 400
        and v1["all_four_folds_passed"]
        and all_finite
    )
    receipt = {
        "completion_version": VERSION,
        "status": (
            "D5A_V1_seed0_all_case_gate_passed"
            if passed else "D5A_seed0_frozen_negative_V1_all_case_gate_failed"
        ),
        "seed": 0,
        "training_order": [f"{candidate}_{fold}" for candidate in CANDIDATES for fold in FOLDS],
        "authorization_receipt_sha256": sha256_file(authorization_path),
        "candidates": candidate_summary,
        "paired_development_cases": paired_cases,
        "development_sources": len(source_fold),
        "all_required_outputs_finite": all_finite,
        "exact_V0_V1_case_pairing": candidate_case_ids["V0"] == candidate_case_ids["V1"],
        "V1_seed0_all_case_gate_passed": passed,
        "V1_seed1_authorization_eligible_next": passed,
        "D5A_seed1_training_authorized": False,
        "development_all_training_authorized": False,
        "proposal_confirmation_access_authorized": False,
        "D5B_implementation_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "completion_holdout_accessed": False,
        "official_test_accessed": False,
        "protected_or_sealed_data_accessed": False,
        "selection_started": False,
        "next_step": (
            "separate_V1_seed1_training_authorization"
            if passed else "freeze_D5A_seed0_negative_and_stop"
        ),
    }
    all_rows.sort(key=lambda row: (row["case_id"], row["candidate"]))
    files = {
        "d5a_seed0_all_case_metrics.csv": csv_bytes(list(all_rows[0]), all_rows),
        "d5a_seed0_training_completion_receipt.json": canonical_json(receipt),
        "d5a_seed0_training_result_zh.md": render_report(receipt),
    }
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    (working / "files.sha256").write_bytes(
        "".join(
            f"{sha256_bytes(payload)}  {name}\n"
            for name, payload in sorted(files.items())
        ).encode("ascii")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(working, output)
    print(f"[saved] immutable D5-A seed-0 completion: {output}")
    print(
        f"[gate] V0={candidate_summary['V0']['selected_hits']}/400 "
        f"V1={candidate_summary['V1']['selected_hits']}/400 passed={passed}"
    )
    print("[locked] seed1=false confirmation=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
