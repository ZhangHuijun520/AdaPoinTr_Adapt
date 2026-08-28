#!/usr/bin/env python3
"""Replay the frozen D3 S2 feasibility result for post-hoc diagnosis only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import builder  # noqa: E402
from tools.run_mamba_v13_d3_s2_feasibility_fold import (  # noqa: E402
    BATCH_SIZE,
    POOL_SIZE,
    SELECTED_COUNT,
    build_dataset,
    freeze_model,
    new_head,
    verify_hotfix,
    verify_lock,
)
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.mamba_d3_contact import (  # noqa: E402
    assign_reference_rim_to_proxies,
    diversified_topk_indices,
)
from utils.mamba_v14_pd3_diagnostics import decompose_s2_case  # noqa: E402


VERSION = "mamba-v14-pd3-s2-failure-decomposition-v1"
FOLDS = ("A", "B", "C", "D")
EXPECTED_CASES = 400
EXPECTED_MISSES = 8


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
    if not sidecar.is_file():
        raise FileNotFoundError(f"Missing SHA256 sidecar: {sidecar}")
    fields = sidecar.read_text(encoding="ascii").split()
    if len(fields) < 2 or Path(fields[1]).name != path.name:
        raise RuntimeError(f"Malformed SHA256 sidecar: {sidecar}")
    if sha256_file(path) != fields[0].lower():
        raise RuntimeError(f"SHA256 mismatch: {path}")


def verify_tree(root: Path) -> None:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise FileNotFoundError(f"Missing frozen tree manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, raw_name = line.split(maxsplit=1)
        path = root / raw_name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen tree mismatch: {path}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_checkpoint(path: Path):
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        return torch.load(path, map_location="cpu")


def verify_existing(output: Path) -> bool:
    receipt_path = output / "pd3_replay_receipt.json"
    manifest = output / "files.sha256"
    if not receipt_path.is_file() or not manifest.is_file():
        return False
    verify_tree(output)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        receipt.get("version") == VERSION
        and receipt.get("status") == "frozen_post_hoc_selection_inert"
        and receipt.get("post_hoc") is True
        and receipt.get("selection_inert") is True
        and receipt.get("holdout_accessed") is False
        and receipt.get("official_test_accessed") is False
        and receipt.get("D3_winner") is None
        and receipt.get("D4_candidate_selection_authorized") is False
    ):
        raise RuntimeError("Existing P-D3 receipt has invalid semantics")
    print(f"[locked] existing P-D3 replay is valid: {output}")
    return True


def assert_close(actual: float, expected: str, label: str, tolerance=1.0e-6) -> None:
    expected_value = float(expected)
    if not math.isclose(actual, expected_value, rel_tol=tolerance, abs_tol=tolerance):
        raise RuntimeError(
            f"Frozen feasibility replay drift for {label}: {actual} != {expected_value}"
        )


def replay_fold(
    fold: str,
    lock: dict,
    runs_root: Path,
    device: torch.device,
    num_workers: int,
) -> tuple[list[dict], dict]:
    fold_lock = lock["folds"][fold]
    config_path = resolve(fold_lock["s0_config"]["path"])
    checkpoint_path = resolve(fold_lock["s0_checkpoint"]["path"])
    for path, expected in (
        (config_path, fold_lock["s0_config"]["sha256"]),
        (checkpoint_path, fold_lock["s0_checkpoint"]["sha256"]),
    ):
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"Fold {fold} restored frozen input mismatch: {path}")

    run_dir = runs_root / f"fold{fold}_seed0"
    run_receipt_path = run_dir / "run_receipt.json"
    per_case_path = run_dir / "feasibility_per_case.csv"
    head_path = run_dir / "head_only_checkpoint.pth"
    for path in (run_receipt_path, per_case_path, head_path):
        verify_sidecar(path)
    run_receipt = json.loads(run_receipt_path.read_text(encoding="utf-8"))
    if not (
        run_receipt.get("fold") == fold
        and run_receipt.get("seed") == 0
        and run_receipt.get("development_cases") == 100
        and run_receipt.get("s0_model_frozen") is True
        and run_receipt.get("only_head_trainable") is True
        and run_receipt.get("holdout_accessed") is False
        and run_receipt.get("selection_started") is False
    ):
        raise RuntimeError(f"Fold {fold} frozen run receipt is invalid")
    frozen_rows = read_csv(per_case_path)
    frozen_by_case = {row["case_id"]: row for row in frozen_rows}
    if len(frozen_by_case) != 100:
        raise RuntimeError(f"Fold {fold} frozen case pairing is incomplete")

    cfg = cfg_from_yaml_file(str(config_path))
    cfg.dataset.val.others.GT_RIM_KEY = "reference_rim_mask"
    dataset = build_dataset(cfg, "val")
    if len(dataset) != 100:
        raise RuntimeError(f"Fold {fold}: expected exactly 100 development cases")

    model = builder.model_builder(cfg.model).to(device)
    builder.load_model(model, str(checkpoint_path))
    freeze_model(model)
    if any(parameter.requires_grad for parameter in model.parameters()):
        raise RuntimeError("P-D3 replay unexpectedly left model parameters trainable")

    head_payload = load_checkpoint(head_path)
    if not (
        head_payload.get("fold") == fold
        and head_payload.get("seed") == 0
        and head_payload.get("forbidden_for_full_S2_initialization") is True
    ):
        raise RuntimeError(f"Fold {fold} head-only checkpoint metadata is invalid")
    head = new_head(device)
    head.load_state_dict(head_payload["state_dict"], strict=True)
    head.eval()
    for parameter in head.parameters():
        parameter.requires_grad_(False)

    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        drop_last=False,
        num_workers=num_workers,
        pin_memory=True,
    )
    rows: list[dict] = []
    with torch.inference_mode():
        for _, batch_case_ids, data in tqdm(
            loader,
            desc=f"P-D3 replay fold{fold}",
            dynamic_ncols=True,
        ):
            batch_case_ids = [str(value) for value in batch_case_ids]
            partial = data[0].to(device=device, non_blocking=True)
            masks = dataset.get_gt_rim_masks(batch_case_ids, device=device)
            scales = dataset.get_normalization_scales(batch_case_ids).to(device)
            coordinates, features, _, _ = model.base_model.encode_rim_proxy_tokens(
                partial
            )
            labels = assign_reference_rim_to_proxies(
                coordinates, partial, masks
            ).labels
            scores = head(features).squeeze(-1)
            selected = diversified_topk_indices(
                scores,
                coordinates,
                selected_count=SELECTED_COUNT,
                pool_size=POOL_SIZE,
            )
            for local, case_id in enumerate(batch_case_ids):
                frozen = frozen_by_case.get(case_id)
                if frozen is None:
                    raise RuntimeError(f"Unexpected replay case: {case_id}")
                rim_points = partial[local, masks[local]]
                values = decompose_s2_case(
                    scores[local],
                    coordinates[local],
                    labels[local],
                    selected[local],
                    rim_points,
                    float(scales[local].item()),
                    pool_size=POOL_SIZE,
                )
                case_hit = int(values["selected_positive_proxy_count"] > 0)
                if case_hit != int(frozen["case_hit"]):
                    raise RuntimeError(f"Frozen case-hit replay drift: {case_id}")
                if values["positive_proxy_count"] != int(frozen["positive_proxy_count"]):
                    raise RuntimeError(f"Frozen positive-count replay drift: {case_id}")
                if values["selected_positive_proxy_count"] != int(
                    frozen["selected_positive_proxy_count"]
                ):
                    raise RuntimeError(f"Frozen selected-count replay drift: {case_id}")
                positive = int(values["positive_proxy_count"])
                selected_positive = int(values["selected_positive_proxy_count"])
                assert_close(
                    selected_positive / positive,
                    frozen["positive_proxy_recall"],
                    f"{case_id}:positive_proxy_recall",
                )
                assert_close(
                    selected_positive / SELECTED_COUNT,
                    frozen["precision"],
                    f"{case_id}:precision",
                )
                negative = int(values["proxy_count"]) - positive
                assert_close(
                    (SELECTED_COUNT - selected_positive) / negative,
                    frozen["false_positive_rate"],
                    f"{case_id}:false_positive_rate",
                )
                assert_close(
                    float(values["selected_anchor_spatial_coverage_mm"]),
                    frozen["selected_anchor_spatial_coverage_mm"],
                    f"{case_id}:selected_anchor_spatial_coverage_mm",
                    tolerance=1.0e-5,
                )
                record = dataset.get_record(len(rows))
                rows.append(
                    {
                        "case_id": case_id,
                        "source_skull_id": str(
                            record.get("source_skull_id", record.get("skull_id", ""))
                        ),
                        "defect_type": str(record.get("defect_type", "")),
                        "fold": fold,
                        "frozen_case_hit": case_hit,
                        **values,
                    }
                )

    if {row["case_id"] for row in rows} != set(frozen_by_case):
        raise RuntimeError(f"Fold {fold} replay case set differs from frozen result")
    lineage = {
        "fold": fold,
        "s0_config": {"path": portable(config_path), "sha256": sha256_file(config_path)},
        "s0_checkpoint": {
            "path": portable(checkpoint_path),
            "sha256": sha256_file(checkpoint_path),
        },
        "head_checkpoint": {"path": portable(head_path), "sha256": sha256_file(head_path)},
        "frozen_per_case": {
            "path": portable(per_case_path),
            "sha256": sha256_file(per_case_path),
        },
        "frozen_run_receipt": {
            "path": portable(run_receipt_path),
            "sha256": sha256_file(run_receipt_path),
        },
    }
    del model, head
    torch.cuda.empty_cache()
    return rows, lineage


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def report_text(summary: dict, misses: list[dict]) -> str:
    stage_counts = summary["miss_failure_stage_counts"]
    lines = [
        "# D3 S2 feasibility selection-inert post-hoc failure decomposition",
        "",
        "> 本报告为只读事后诊断。它不重开 D3、不得选择 D4 的 K/pool/scorer/selector，且未访问 holdout、confirmation 或 official test。",
        "",
        "## 冻结结果复现",
        "",
        f"- 病例：`{summary['cases']}`",
        f"- 冻结命中：`{summary['hits']}/{summary['cases']}`",
        f"- 冻结 miss：`{summary['misses']}`",
        f"- replay 与冻结 per-case 结果完全一致：`{summary['frozen_replay_exact']}`",
        "",
        "## 八个 miss 的阶段归因",
        "",
        "| Stage | Count |",
        "|---|---:|",
    ]
    for stage in (
        "oracle_absent",
        "ranking_miss_top96",
        "selector_dropped_all_positive",
    ):
        lines.append(f"| `{stage}` | {stage_counts.get(stage, 0)} |")
    lines.extend(
        [
            "",
            "| Case | Fold | Defect | Positive | Best rank | Top-96 positive | Selected positive | Stage |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in misses:
        lines.append(
            "| `{case_id}` | {fold} | {defect_type} | {positive_proxy_count} | "
            "{best_positive_rank} | {positive_in_top_pool} | "
            "{selected_positive_proxy_count} | `{failure_stage}` |".format(**row)
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "- `positive_proxy_count > 0` 只证明 frozen proxy set 中存在 Voronoi-positive proxy，不证明当前 scorer/selector 充分。",
            "- `top32/64/96/128` 仅用于描述排名，不构成旧 development 上的 pool-size sweep。",
            "- Euclidean GT-rim coverage 替代未定义拓扑的 geodesic segment coverage；当前点云不提供可审计的 rim mesh adjacency。",
            "- 结果只能检验预先写明的失败机制，不能授权 D3 rerun、seed-1 或任何受保护 split。",
            "",
            "## 下一步",
            "",
            "按已修订 D4 协议建立全新 source-skull development 数据锁。D4-A 的表示、selector 和门控必须在查看新 development 结果之前冻结。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--lock_dir", type=Path, required=True)
    parser.add_argument("--hotfix_dir", type=Path, required=True)
    parser.add_argument("--negative_freeze", type=Path, required=True)
    parser.add_argument("--runs_root", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--num_workers", type=int, default=4)
    args = parser.parse_args()

    output = resolve(args.output_dir)
    if verify_existing(output):
        return
    if output.exists():
        raise RuntimeError(f"Refusing non-final P-D3 output directory: {output}")
    working = output.parent / f".{output.name}.working"
    if working.exists():
        raise RuntimeError(f"Working directory requires inspection: {working}")
    working.mkdir(parents=True)

    protocol_path = resolve(args.protocol)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if not (
        protocol.get("protocol_version") == "mamba-v14-d4-contact-support-v1"
        and protocol["pd3"]["post_hoc"] is True
        and protocol["pd3"]["selection_inert"] is True
        and protocol["pd3"]["d3_rerun_authorized"] is False
        and protocol["protected_splits"]["all_locked"] is True
    ):
        raise RuntimeError("D4/P-D3 protocol semantics are invalid")

    lock_dir = resolve(args.lock_dir)
    hotfix_dir = resolve(args.hotfix_dir)
    negative_freeze = resolve(args.negative_freeze)
    runs_root = resolve(args.runs_root)
    verify_tree(negative_freeze)
    negative_receipt = negative_freeze / "negative_result_receipt.json"
    frozen_negative = json.loads(negative_receipt.read_text(encoding="utf-8"))
    if not (
        frozen_negative.get("status")
        == "frozen_negative_high_hit_rate_failed_all_case_safety_gate"
        and frozen_negative.get("missed_cases") == EXPECTED_MISSES
        and frozen_negative.get("holdout_accessed") is False
        and frozen_negative.get("selection_started") is False
    ):
        raise RuntimeError("Frozen S2 negative receipt has invalid semantics")

    lock, _ = verify_lock(lock_dir, "A")
    verify_hotfix(hotfix_dir, lock_dir)
    if not torch.cuda.is_available():
        raise RuntimeError("P-D3 exact replay requires CUDA")
    device = torch.device("cuda:0")
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    all_rows: list[dict] = []
    lineage = {}
    for fold in FOLDS:
        rows, fold_lineage = replay_fold(
            fold, lock, runs_root, device, args.num_workers
        )
        all_rows.extend(rows)
        lineage[fold] = fold_lineage
    if len(all_rows) != EXPECTED_CASES or len({row["case_id"] for row in all_rows}) != EXPECTED_CASES:
        raise RuntimeError("P-D3 replay did not produce exactly 400 unique cases")

    misses = [row for row in all_rows if row["frozen_case_hit"] == 0]
    if len(misses) != EXPECTED_MISSES:
        raise RuntimeError("P-D3 replay did not reproduce exactly eight misses")
    stage_counts = Counter(row["failure_stage"] for row in all_rows)
    miss_stage_counts = Counter(row["failure_stage"] for row in misses)
    summary = {
        "summary_version": VERSION,
        "status": "frozen_post_hoc_selection_inert",
        "cases": len(all_rows),
        "hits": len(all_rows) - len(misses),
        "misses": len(misses),
        "stage_counts_all_cases": dict(sorted(stage_counts.items())),
        "miss_failure_stage_counts": dict(sorted(miss_stage_counts.items())),
        "miss_positive_proxy_count_range": [
            min(int(row["positive_proxy_count"]) for row in misses),
            max(int(row["positive_proxy_count"]) for row in misses),
        ],
        "frozen_replay_exact": True,
        "optimizer_steps": 0,
        "model_updates": 0,
        "post_hoc": True,
        "selection_inert": True,
        "D3_winner": None,
        "D3_rerun_authorized": False,
        "D4_candidate_selection_authorized": False,
        "holdout_accessed": False,
        "confirmation20_accessed": False,
        "official_test_accessed": False,
    }

    per_case_path = working / "pd3_s2_failure_decomposition_per_case.csv"
    misses_path = working / "pd3_s2_miss_case_profiles.csv"
    summary_path = working / "pd3_s2_failure_decomposition_summary.json"
    report_path = working / "pd3_s2_failure_decomposition_report_zh.md"
    write_csv(per_case_path, all_rows)
    write_csv(misses_path, misses)
    summary_path.write_bytes(canonical_json(summary))
    report_path.write_text(report_text(summary, misses), encoding="utf-8", newline="\n")

    artifact_sources = {
        "per_case": per_case_path,
        "miss_cases": misses_path,
        "summary": summary_path,
        "report": report_path,
        "protocol": protocol_path,
        "negative_receipt": negative_receipt,
        "feasibility_lock": lock_dir / "feasibility_lock_receipt.json",
        "hotfix_receipt": hotfix_dir / "hotfix_receipt.json",
    }
    artifact_destinations = {
        name: (output / source.name if source.parent == working else source)
        for name, source in artifact_sources.items()
    }
    receipt = {
        "version": VERSION,
        "status": "frozen_post_hoc_selection_inert",
        "artifacts": {
            name: {
                "path": portable(artifact_destinations[name]),
                "sha256": sha256_file(source),
            }
            for name, source in artifact_sources.items()
        },
        "fold_lineage": lineage,
        "cases": EXPECTED_CASES,
        "misses": EXPECTED_MISSES,
        "optimizer_steps": 0,
        "model_updates": 0,
        "post_hoc": True,
        "selection_inert": True,
        "D3_winner": None,
        "D3_rerun_authorized": False,
        "D4_candidate_selection_authorized": False,
        "seed1_authorized": False,
        "holdout_accessed": False,
        "official_test_accessed": False,
    }
    receipt_path = working / "pd3_replay_receipt.json"
    receipt_path.write_bytes(canonical_json(receipt))

    manifest_paths = [per_case_path, misses_path, summary_path, report_path, receipt_path]
    manifest = "".join(
        f"{sha256_file(path)}  {path.name}\n" for path in sorted(manifest_paths)
    )
    (working / "files.sha256").write_text(manifest, encoding="ascii", newline="\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(working, output)
    verify_tree(output)
    print(f"[saved] P-D3 selection-inert replay: {output}")
    print(f"[summary] cases={EXPECTED_CASES} misses={EXPECTED_MISSES} stages={dict(miss_stage_counts)}")
    print("[locked] no D3 rerun, D4 selection, holdout, confirmation, or official test")


if __name__ == "__main__":
    main()
