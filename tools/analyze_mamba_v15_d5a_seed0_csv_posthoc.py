#!/usr/bin/env python3
"""Analyze the frozen D5-A seed-0 CSV without model or geometry access."""

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
import statistics
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = REPO_ROOT / "docs/mamba_v15_d5a_seed0_csv_posthoc_protocol_v1.json"
VERSION = "mamba-v15-d5a-seed0-csv-posthoc-v1"
TOP_K = (8, 16, 32, 64, 128, 256)


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


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
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
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
    return sha256_file(manifest)


def rank_band(rank: int) -> str:
    if rank <= 40:
        return "33-40"
    if rank <= 64:
        return "41-64"
    if rank <= 128:
        return "65-128"
    return ">128"


def transition_label(v0: int, v1: int) -> str:
    return f"{'hit' if v0 else 'miss'}_to_{'hit' if v1 else 'miss'}"


def verify_protocol() -> dict[str, Any]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    permissions = protocol.get("permissions", {})
    expected = protocol.get("expected_frozen_parent", {})
    if not (
        protocol.get("protocol_id") == VERSION
        and protocol.get("status")
        == "posthoc_csv_only_analysis_preregistered_after_frozen_negative"
        and expected
        == {
            "V0_hits": 322,
            "V0_misses": 78,
            "V1_hits": 368,
            "V1_misses": 32,
            "cases": 400,
            "sources": 100,
            "status": "D5A_seed0_frozen_negative_V1_all_case_gate_failed",
        }
        and permissions.get("post_hoc") is True
        and permissions.get("selection_inert") is True
        and permissions.get("checkpoint_access") is False
        and permissions.get("npz_access") is False
        and permissions.get("stl_access") is False
        and permissions.get("sealed_geometry_access") is False
        and permissions.get("optimizer_steps") == 0
        and permissions.get("model_updates") == 0
        and permissions.get("D5A_seed1_training_authorized") is False
        and permissions.get("D5B_training_authorized") is False
    ):
        raise RuntimeError("D5-A CSV post-hoc protocol drifted")
    return protocol


def verify_existing(output: Path) -> bool:
    if not output.exists():
        return False
    verify_manifest(output)
    summary = json.loads(
        (output / "d5a_seed0_csv_posthoc_summary.json").read_text(encoding="utf-8")
    )
    if not (
        summary.get("analysis_version") == VERSION
        and summary.get("status") == "D5A_seed0_negative_csv_posthoc_complete"
        and summary.get("V1_hits") == 368
        and summary.get("V1_misses") == 32
        and summary.get("post_hoc") is True
        and summary.get("selection_inert") is True
    ):
        raise RuntimeError("Existing D5-A CSV post-hoc output is invalid")
    print(f"[locked] existing CSV post-hoc output is valid: {output}")
    return True


def render_report(summary: Mapping[str, Any]) -> bytes:
    recall = summary["V1_counterfactual_recall_at_k"]
    transitions = summary["paired_transition_counts"]
    text = (
        "# Mamba v1.5 D5-A seed-0 CSV-only post-hoc\n\n"
        "> 本分析只消费冻结 completion CSV；不读取 checkpoint、NPZ、STL 或 sealed 数据。\n\n"
        f"- V0 hits/misses：{summary['V0_hits']} / {summary['V0_misses']}。\n"
        f"- V1 hits/misses：{summary['V1_hits']} / {summary['V1_misses']}。\n"
        f"- paired transitions：`{json.dumps(transitions, sort_keys=True)}`。\n"
        f"- V1 recall@32/64/128：{recall['32']} / {recall['64']} / {recall['128']}。\n"
        f"- V1 miss rank bands：`{json.dumps(summary['V1_miss_rank_band_counts'], sort_keys=True)}`。\n"
        f"- miss sources：{summary['V1_miss_sources']}；multi-miss sources：{summary['V1_multi_miss_sources']}。\n"
        "- 解释：V1 具有显著净增益，但 10 个新 miss 证明其并非单调安全。\n"
        "- top-64 仍为 393/400；top-128 的 400/400 仅是反事实解释，不改变冻结 top-32 门控。\n"
        "- 结论：D5-A seed-0 保持负结果；seed-1、confirmation、D5-B 和 selection 继续禁止。\n"
    )
    return text.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--completion_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    verify_protocol()
    completion = args.completion_dir.resolve()
    output = args.output_dir.resolve()
    if verify_existing(output):
        return
    working = output.with_name(f".{output.name}.working")
    if output.exists() or working.exists():
        raise RuntimeError(f"CSV post-hoc output requires inspection: {working}")

    completion_manifest = verify_manifest(completion)
    receipt_path = completion / "d5a_seed0_training_completion_receipt.json"
    metrics_path = completion / "d5a_seed0_all_case_metrics.csv"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        receipt.get("status") == "D5A_seed0_frozen_negative_V1_all_case_gate_failed"
        and receipt.get("paired_development_cases") == 400
        and receipt.get("development_sources") == 100
        and receipt.get("all_required_outputs_finite") is True
        and receipt.get("exact_V0_V1_case_pairing") is True
        and receipt.get("candidates", {}).get("V0", {}).get("selected_hits") == 322
        and receipt.get("candidates", {}).get("V1", {}).get("selected_hits") == 368
        and receipt.get("V1_seed1_authorization_eligible_next") is False
        and receipt.get("D5A_seed1_training_authorized") is False
        and receipt.get("D5B_training_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("D5-A completion is not the frozen seed-0 negative parent")

    with metrics_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 800:
        raise RuntimeError("D5-A completion CSV must contain 800 candidate-case rows")
    paired: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        case_id = row["case_id"]
        candidate = row["candidate"]
        if candidate not in ("V0", "V1") or candidate in paired.setdefault(case_id, {}):
            raise RuntimeError(f"Invalid candidate pairing: {case_id}")
        if not all(math.isfinite(float(row[key])) for key in ("logit_min", "logit_max")):
            raise RuntimeError(f"Non-finite frozen logits: {case_id}/{candidate}")
        paired[case_id][candidate] = row
    if len(paired) != 400 or any(set(pair) != {"V0", "V1"} for pair in paired.values()):
        raise RuntimeError("D5-A V0/V1 pairing is incomplete")

    transition_counts: Counter[str] = Counter()
    family_transitions: Counter[tuple[str, str]] = Counter()
    paired_rows: list[dict[str, Any]] = []
    v1_rows: list[dict[str, str]] = []
    for case_id, pair in sorted(paired.items()):
        v0, v1 = pair["V0"], pair["V1"]
        if not (
            v0["source_skull_id"] == v1["source_skull_id"]
            and v0["defect_type"] == v1["defect_type"]
            and v0["fold"] == v1["fold"]
        ):
            raise RuntimeError(f"Paired metadata mismatch: {case_id}")
        v0_hit, v1_hit = int(v0["selected_hit"]), int(v1["selected_hit"])
        transition = transition_label(v0_hit, v1_hit)
        transition_counts[transition] += 1
        family_transitions[(v1["defect_type"], transition)] += 1
        v1_rows.append(v1)
        paired_rows.append(
            {
                "case_id": case_id,
                "source_skull_id": v1["source_skull_id"],
                "defect_type": v1["defect_type"],
                "fold": v1["fold"],
                "transition": transition,
                "V0_selected_hit": v0_hit,
                "V0_best_positive_rank": int(v0["best_positive_rank"]),
                "V1_selected_hit": v1_hit,
                "V1_best_positive_rank": int(v1["best_positive_rank"]),
            }
        )

    v0_hits = sum(int(pair["V0"]["selected_hit"]) for pair in paired.values())
    v1_hits = sum(int(row["selected_hit"]) for row in v1_rows)
    misses = [row for row in v1_rows if int(row["selected_hit"]) == 0]
    recall = {str(k): sum(int(row[f"recall_at_{k}"]) for row in v1_rows) for k in TOP_K}
    expected_recall = {"8": 308, "16": 343, "32": 368, "64": 393, "128": 400, "256": 400}
    if not (
        v0_hits == 322
        and v1_hits == 368
        and len(misses) == 32
        and dict(transition_counts)
        == {"hit_to_hit": 312, "hit_to_miss": 10, "miss_to_hit": 56, "miss_to_miss": 22}
        and recall == expected_recall
        and all(int(row["positive_candidate_count"]) > 0 for row in misses)
        and all(int(row["best_positive_rank"]) >= 33 for row in misses)
        and all(row["recall_at_32"] == row["selected_hit"] for row in v1_rows)
    ):
        raise RuntimeError("Frozen D5-A observations do not match the post-hoc contract")

    miss_rows = []
    for row in sorted(misses, key=lambda item: item["case_id"]):
        rank = int(row["best_positive_rank"])
        miss_rows.append(
            {
                **row,
                "rank_band": rank_band(rank),
                "recoverable_at_64": int(row["recall_at_64"]),
                "recoverable_at_128": int(row["recall_at_128"]),
                "failure_stage": "positive_ranked_below_frozen_top32",
            }
        )
    source_counts = Counter(row["source_skull_id"] for row in miss_rows)
    source_rows = [
        {
            "source_skull_id": source,
            "miss_count": count,
            "fold": next(row["fold"] for row in miss_rows if row["source_skull_id"] == source),
            "miss_defect_types": ";".join(
                sorted(row["defect_type"] for row in miss_rows if row["source_skull_id"] == source)
            ),
        }
        for source, count in sorted(source_counts.items())
    ]
    rank_bands = Counter(row["rank_band"] for row in miss_rows)
    miss_families = Counter(row["defect_type"] for row in miss_rows)
    miss_folds = Counter(row["fold"] for row in miss_rows)
    expected_family_transitions = {
        ("ellipsoid_large", "hit_to_hit"): 83,
        ("ellipsoid_large", "hit_to_miss"): 2,
        ("ellipsoid_large", "miss_to_hit"): 13,
        ("ellipsoid_large", "miss_to_miss"): 2,
        ("ellipsoid_medium", "hit_to_hit"): 78,
        ("ellipsoid_medium", "hit_to_miss"): 2,
        ("ellipsoid_medium", "miss_to_hit"): 14,
        ("ellipsoid_medium", "miss_to_miss"): 6,
        ("ellipsoid_small", "hit_to_hit"): 72,
        ("ellipsoid_small", "hit_to_miss"): 4,
        ("ellipsoid_small", "miss_to_hit"): 15,
        ("ellipsoid_small", "miss_to_miss"): 9,
        ("irregular_medium", "hit_to_hit"): 79,
        ("irregular_medium", "hit_to_miss"): 2,
        ("irregular_medium", "miss_to_hit"): 14,
        ("irregular_medium", "miss_to_miss"): 5,
    }
    if not (
        dict(family_transitions) == expected_family_transitions
        and dict(rank_bands) == {"33-40": 9, "41-64": 16, "65-128": 7}
        and dict(miss_families)
        == {
            "ellipsoid_large": 4,
            "ellipsoid_medium": 8,
            "ellipsoid_small": 13,
            "irregular_medium": 7,
        }
        and dict(miss_folds) == {"A": 8, "B": 11, "C": 8, "D": 5}
        and sum(int(row["recall_at_64"]) for row in misses) == 25
        and sum(int(row["recall_at_128"]) for row in misses) == 32
        and len(source_counts) == 30
        and sum(count > 1 for count in source_counts.values()) == 2
        and max(source_counts.values()) == 2
    ):
        raise RuntimeError("D5-A frozen post-hoc strata drifted")
    summary = {
        "analysis_version": VERSION,
        "status": "D5A_seed0_negative_csv_posthoc_complete",
        "post_hoc": True,
        "selection_inert": True,
        "paired_cases": 400,
        "V0_hits": 322,
        "V0_misses": 78,
        "V1_hits": 368,
        "V1_misses": 32,
        "paired_transition_counts": dict(sorted(transition_counts.items())),
        "paired_transition_counts_by_family": {
            f"{family}|{transition}": count
            for (family, transition), count in sorted(family_transitions.items())
        },
        "V1_counterfactual_recall_at_k": recall,
        "V1_top32_miss_recoverable_at_64": sum(int(row["recall_at_64"]) for row in misses),
        "V1_top32_miss_recoverable_at_128": sum(int(row["recall_at_128"]) for row in misses),
        "V1_miss_rank_band_counts": dict(sorted(rank_bands.items())),
        "V1_miss_best_positive_rank": {
            "minimum": min(int(row["best_positive_rank"]) for row in misses),
            "median": statistics.median(int(row["best_positive_rank"]) for row in misses),
            "maximum": max(int(row["best_positive_rank"]) for row in misses),
        },
        "V1_miss_fold_counts": dict(sorted(miss_folds.items())),
        "V1_miss_defect_family_counts": dict(sorted(miss_families.items())),
        "V1_miss_sources": len(source_counts),
        "V1_multi_miss_sources": sum(count > 1 for count in source_counts.values()),
        "V1_maximum_misses_per_source": max(source_counts.values()),
        "completion_manifest_sha256": completion_manifest,
        "completion_receipt_sha256": sha256_file(receipt_path),
        "completion_metrics_sha256": sha256_file(metrics_path),
        "protocol_sha256": sha256_file(PROTOCOL),
        "model_updates": 0,
        "optimizer_steps": 0,
        "checkpoint_accessed": False,
        "geometry_accessed": False,
        "original_top32_gate_changed": False,
        "top128_400_of_400_is_explanatory_only": True,
        "D5A_seed1_training_authorized": False,
        "proposal_confirmation_access_authorized": False,
        "D5B_implementation_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "freeze_D5A_seed0_negative_and_preregister_a_new_fixed_budget_representation_question",
    }

    files = {
        "d5a_v0_v1_paired_transitions.csv": csv_bytes(list(paired_rows[0]), paired_rows),
        "d5a_v1_top32_misses.csv": csv_bytes(list(miss_rows[0]), miss_rows),
        "d5a_v1_miss_source_profiles.csv": csv_bytes(list(source_rows[0]), source_rows),
        "d5a_seed0_csv_posthoc_summary.json": canonical_json(summary),
        "d5a_seed0_csv_posthoc_report_zh.md": render_report(summary),
    }
    files["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())
    ).encode("ascii")
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(working, output)
    print(f"[saved] immutable D5-A seed-0 CSV post-hoc: {output}")
    print(f"[summary] transitions={dict(sorted(transition_counts.items()))}")
    print(f"[summary] recall_at_k={recall}")
    print("[locked] original 368/400 top-32 gate unchanged")
    print("[locked] seed1=false confirmation=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
