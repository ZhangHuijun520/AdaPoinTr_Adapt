#!/usr/bin/env python3
"""Replay frozen D4-A heads to decompose proposal-selection misses."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import torch
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.run_mamba_v14_d4a_training_fold import (  # noqa: E402
    load_case,
    load_manifest,
    sha256_file,
)
from utils.mamba_d4a_proposal import (  # noqa: E402
    D4AProposalHead,
    geometry_descriptor_13d,
    select_top8_conditioned_fps24,
)


VERSION = "mamba-v14-d4a-failure-decomposition-posthoc-v1"
FOLDS = ("A", "B", "C", "D")
PROTOCOL = REPO_ROOT / "docs/mamba_v14_d4a_failure_decomposition_posthoc_protocol_v1.json"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def csv_bytes(
    fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> bytes:
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


def load_checkpoint(path: Path, fold: str, expected: str, device: torch.device) -> D4AProposalHead:
    if sha256_file(path) != expected:
        raise RuntimeError(f"Fold {fold} checkpoint hash mismatch")
    try:
        payload = torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        payload = torch.load(path, map_location="cpu")
    if not (
        payload.get("fold") == fold
        and payload.get("seed") == 0
        and payload.get("epoch") == 50
        and payload.get("optimizer_state_included") is False
    ):
        raise RuntimeError(f"Fold {fold} checkpoint semantics are invalid")
    head = D4AProposalHead()
    head.load_state_dict(payload["state_dict"], strict=True)
    return head.to(device).eval()


def classify(selected_positive: int, pool_positive: int) -> str:
    if selected_positive > 0:
        return "selected_hit"
    if pool_positive == 0:
        return "ranking_miss_top256"
    return "selector_dropped_all_pool_positive"


def verify_existing(output: Path) -> bool:
    if not output.exists():
        return False
    verify_manifest(output)
    summary = json.loads(
        (output / "failure_decomposition_summary.json").read_text(encoding="utf-8")
    )
    if not (
        summary.get("analysis_version") == VERSION
        and summary.get("cases") == 400
        and summary.get("original_hits") == 332
        and summary.get("original_misses") == 68
        and summary.get("frozen_replay_exact") is True
        and summary.get("selection_inert") is True
        and summary.get("protected_data_accessed") is False
    ):
        raise RuntimeError("Existing D4-A post-hoc output is invalid")
    print(f"[locked] existing post-hoc output is valid: {output}")
    return True


def render_report(summary: Mapping[str, Any]) -> bytes:
    stages = summary["miss_failure_stage_counts"]
    families = summary["miss_defect_family_counts"]
    text = (
        "# Mamba v1.4 D4-A failure-decomposition post-hoc\n\n"
        "> 本分析只重放冻结 head 和冻结 selector，不训练、不改门控、不选择候选。\n\n"
        f"- cases：{summary['cases']}。\n"
        f"- original hits/misses：{summary['original_hits']} / {summary['original_misses']}。\n"
        f"- ranking miss top-256：{stages.get('ranking_miss_top256', 0)}。\n"
        f"- selector dropped all pool-positive：{stages.get('selector_dropped_all_pool_positive', 0)}。\n"
        f"- miss families：`{json.dumps(families, ensure_ascii=False, sort_keys=True)}`。\n"
        f"- miss sources：{summary['miss_sources']}；multi-miss sources：{summary['multi_miss_sources']}。\n"
        f"- frozen replay exact：`{summary['frozen_replay_exact']}`。\n"
        "- 结论：该结果只解释 D4-A 失败阶段；原 332/400 负门控保持不变。\n"
        "- T0/T1/T2、candidate selection 与 protected access 继续锁定。\n"
    )
    return text.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold_root", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--completion_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    fold_root = args.fold_root.resolve()
    authorization = args.authorization_dir.resolve()
    completion = args.completion_dir.resolve()
    audit = args.generation_audit_dir.resolve()
    output = args.output_dir.resolve()
    if verify_existing(output):
        return
    working = output.with_name(f".{output.name}.working")
    if output.exists() or working.exists():
        raise RuntimeError(f"Post-hoc output requires inspection: {working}")

    authorization_manifest = verify_manifest(authorization)
    authorization_path = authorization / "d4a_training_authorization_receipt.json"
    authorization_receipt = json.loads(
        authorization_path.read_text(encoding="utf-8")
    )
    proposal_path = REPO_ROOT / "utils/mamba_d4a_proposal.py"
    if not (
        authorization_receipt.get("status")
        == "D4A_head_only_seed0_folds_A_D_training_authorized"
        and authorization_receipt.get("implementation_sha256", {}).get(
            "utils/mamba_d4a_proposal.py"
        )
        == sha256_file(proposal_path)
        and authorization_receipt.get("protected_data_accessed") is False
    ):
        raise RuntimeError("D4-A authorization or proposal implementation drifted")

    completion_manifest = verify_manifest(completion)
    verify_manifest(audit)
    receipt_path = completion / "d4a_training_completion_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        receipt.get("status") == "D4A_frozen_negative_all_case_gate_failed"
        and receipt.get("development_cases") == 400
        and receipt.get("selected_hits") == 332
        and receipt.get("selected_misses") == 68
        and receipt.get("D4A_all_case_gate_passed") is False
        and receipt.get("T0_T1_T2_materialization_authorized_next") is False
        and receipt.get("protected_data_accessed") is False
        and receipt.get("authorization_receipt_sha256")
        == sha256_file(authorization_path)
    ):
        raise RuntimeError("D4-A completion is not the frozen negative parent")

    with (completion / "d4a_all_case_metrics.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        original_rows = list(csv.DictReader(handle))
    if len(original_rows) != 400:
        raise RuntimeError("D4-A completion must contain 400 rows")
    by_fold: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in original_rows:
        by_fold[row["fold"]].append(row)
    if set(by_fold) != set(FOLDS) or any(len(by_fold[fold]) != 100 for fold in FOLDS):
        raise RuntimeError("D4-A completion fold coverage is invalid")

    if not torch.cuda.is_available():
        raise RuntimeError("D4-A post-hoc replay requires CUDA")
    device = torch.device("cuda:0")
    manifest = load_manifest(audit)
    replay_rows: list[dict[str, Any]] = []
    fold_manifest_hashes: dict[str, str] = {}

    with torch.inference_mode():
        for fold in FOLDS:
            fold_dir = fold_root / f"fold{fold}_seed0"
            fold_manifest_hashes[fold] = verify_manifest(fold_dir)
            run_receipt = json.loads(
                (fold_dir / "run_receipt.json").read_text(encoding="utf-8")
            )
            checkpoint_info = run_receipt["artifacts"]["head_final_epoch"]
            checkpoint_path = fold_dir / checkpoint_info["name"]
            head = load_checkpoint(
                checkpoint_path, fold, checkpoint_info["sha256"], device
            )
            for original in tqdm(
                sorted(by_fold[fold], key=lambda row: row["case_id"]),
                desc=f"D4-A post-hoc fold{fold}",
                dynamic_ncols=True,
            ):
                case_id = original["case_id"]
                partial_np, labels_np = load_case(case_id, manifest[case_id], audit)
                partial = torch.from_numpy(partial_np).unsqueeze(0).to(device)
                labels = torch.from_numpy(labels_np).unsqueeze(0).to(device)
                descriptors = geometry_descriptor_13d(
                    partial, knn=16, epsilon=1.0e-8, query_chunk_size=512
                )
                logits = head(descriptors)
                order = torch.argsort(logits[0], descending=True, stable=True)
                pool = order[:256]
                top8 = pool[:8]
                selected = select_top8_conditioned_fps24(logits, partial)[0]
                fps24 = selected[8:]
                positive_count = int(labels.sum().item())
                pool_positive = int(labels[0, pool].sum().item())
                top8_positive = int(labels[0, top8].sum().item())
                fps24_positive = int(labels[0, fps24].sum().item())
                selected_positive = top8_positive + fps24_positive
                positive_ranks = torch.nonzero(labels[0, order], as_tuple=False)
                best_rank = int(positive_ranks[0, 0].item()) + 1
                logit_min = float(logits.amin().item())
                logit_max = float(logits.amax().item())
                if not all(math.isfinite(value) for value in (logit_min, logit_max)):
                    raise RuntimeError(f"Non-finite replay logits: {case_id}")
                if not (
                    positive_count == int(original["positive_candidate_count"])
                    and selected_positive == int(original["selected_positive_count"])
                    and int(selected_positive > 0) == int(original["selected_hit"])
                    and math.isclose(logit_min, float(original["logit_min"]), rel_tol=1e-6, abs_tol=1e-6)
                    and math.isclose(logit_max, float(original["logit_max"]), rel_tol=1e-6, abs_tol=1e-6)
                ):
                    raise RuntimeError(f"Frozen replay mismatch: {case_id}")
                replay_rows.append(
                    {
                        **original,
                        "best_positive_rank_1based": best_rank,
                        "top256_positive_count": pool_positive,
                        "top8_positive_count": top8_positive,
                        "fps24_positive_count": fps24_positive,
                        "failure_stage": classify(selected_positive, pool_positive),
                    }
                )
            del head
            torch.cuda.empty_cache()

    replay_rows.sort(key=lambda row: row["case_id"])
    misses = [row for row in replay_rows if int(row["selected_hit"]) == 0]
    hits = [row for row in replay_rows if int(row["selected_hit"]) == 1]
    if len(hits) != 332 or len(misses) != 68:
        raise RuntimeError("Post-hoc replay changed the frozen D4-A gate")
    source_misses = Counter(row["source_skull_id"] for row in misses)
    source_rows = [
        {
            "source_skull_id": source,
            "fold": next(row["fold"] for row in misses if row["source_skull_id"] == source),
            "miss_count": count,
            "miss_defect_types": ";".join(
                sorted(row["defect_type"] for row in misses if row["source_skull_id"] == source)
            ),
        }
        for source, count in sorted(source_misses.items())
    ]
    stage_counts = Counter(row["failure_stage"] for row in misses)
    family_counts = Counter(row["defect_type"] for row in misses)
    summary = {
        "analysis_version": VERSION,
        "status": "D4A_negative_posthoc_failure_decomposition_complete",
        "post_hoc": True,
        "selection_inert": True,
        "cases": 400,
        "original_hits": 332,
        "original_misses": 68,
        "frozen_replay_exact": True,
        "miss_failure_stage_counts": dict(sorted(stage_counts.items())),
        "miss_defect_family_counts": dict(sorted(family_counts.items())),
        "miss_sources": len(source_misses),
        "multi_miss_sources": sum(count > 1 for count in source_misses.values()),
        "maximum_misses_per_source": max(source_misses.values()),
        "miss_best_positive_rank": {
            "minimum": min(int(row["best_positive_rank_1based"]) for row in misses),
            "median": statistics.median(int(row["best_positive_rank_1based"]) for row in misses),
            "maximum": max(int(row["best_positive_rank_1based"]) for row in misses),
        },
        "completion_manifest_sha256": completion_manifest,
        "completion_receipt_sha256": sha256_file(receipt_path),
        "authorization_manifest_sha256": authorization_manifest,
        "authorization_receipt_sha256": sha256_file(authorization_path),
        "fold_manifest_sha256": fold_manifest_hashes,
        "protocol_sha256": sha256_file(PROTOCOL),
        "model_updates": 0,
        "optimizer_steps": 0,
        "D4A_gate_changed": False,
        "T0_T1_T2_materialization_authorized": False,
        "D4_candidate_selection_authorized": False,
        "protected_data_accessed": False,
        "next_step": "freeze_D4A_negative_with_posthoc_explanation_and_stop_D4_round_A",
    }

    all_payload = csv_bytes(list(replay_rows[0]), replay_rows)
    miss_payload = csv_bytes(list(misses[0]), misses)
    source_payload = csv_bytes(list(source_rows[0]), source_rows)
    summary_payload = canonical_json(summary)
    report_payload = render_report(summary)
    files = {
        "failure_decomposition_all_cases.csv": all_payload,
        "failure_decomposition_misses.csv": miss_payload,
        "failure_decomposition_source_profiles.csv": source_payload,
        "failure_decomposition_summary.json": summary_payload,
        "failure_decomposition_report_zh.md": report_payload,
    }
    files["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(working, output)
    print(f"[saved] immutable D4-A post-hoc decomposition: {output}")
    print(f"[summary] stages={dict(sorted(stage_counts.items()))}")
    print("[locked] original gate unchanged; T0/T1/T2 remain forbidden")
    print("[locked] selection=false protected=false model_updates=0")


if __name__ == "__main__":
    main()
