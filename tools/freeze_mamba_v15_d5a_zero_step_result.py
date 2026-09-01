#!/usr/bin/env python3
"""Freeze the complete D5-A V0/V1 zero-step result and permission boundary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = (
    REPO_ROOT / "docs/mamba_v15_d5a_zero_step_result_freeze_protocol_v1.json"
)
VERSION = "mamba-v15-d5a-v0-v1-zero-step-result-freeze-v1"
FOLDS = ("A", "B", "C", "D")
CANDIDATES = ("V0", "V1")
EXPECTED_SOURCE_COMMIT = "1480a9bc0957528182c11bfddd722b53517b5388"
EXPECTED_SOURCE_TAG = "mamba-adapter-v15-d5a-zero-step-preflight-v1"
EXPECTED_D4_RESULT_SHA256 = (
    "2f9f061f8649d06b6c45006510a0a2e3a64e2ba1496f03a3e05dc24053bb325d"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


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


def read_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    facts = protocol.get("required_execution_facts", {})
    boundary = protocol.get("permission_boundary", {})
    archive = protocol.get("archive_boundary", {})
    if (
        protocol.get("protocol_id") != VERSION
        or protocol.get("status")
        != "preregistered_result_freeze_after_zero_step_before_training_authorization"
        or facts
        != {
            "folds": 4,
            "training_probe_cases": 4,
            "candidates_per_probe": 2,
            "metric_rows": 8,
            "backward_passes": 8,
            "optimizer_constructed": False,
            "optimizer_steps": 0,
            "model_updates": 0,
            "checkpoint_loaded": False,
            "checkpoint_written": False,
            "dev_cases_accessed": 0,
        }
        or any(value is not False for value in boundary.values())
        or archive.get("include_checkpoints") is not False
        or archive.get("include_npz") is not False
        or archive.get("include_stl") is not False
        or archive.get("include_sealed_geometry") is not False
    ):
        raise RuntimeError("D5-A zero-step result-freeze protocol drifted")


def validate_zero_receipt(receipt: Mapping[str, Any]) -> None:
    false_keys = (
        "optimizer_constructed",
        "checkpoint_loaded",
        "checkpoint_written",
        "D5A_seed0_training_authorized",
        "D5A_seed1_training_authorized",
        "development_all_training_authorized",
        "proposal_confirmation_access_authorized",
        "D5B_implementation_authorized",
        "D5B_training_authorized",
        "D5_candidate_selection_authorized",
        "selection_started",
        "proposal_confirmation_accessed",
        "completion_holdout_accessed",
        "official_test_accessed",
        "protected_or_sealed_data_accessed",
    )
    if not (
        receipt.get("status") == "V0_V1_implementation_zero_step_preflight_passed"
        and receipt.get("folds") == 4
        and receipt.get("train_probe_cases") == 4
        and receipt.get("candidates_per_probe") == 2
        and receipt.get("backward_passes") == 8
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("dev_cases_accessed") == 0
        and receipt.get("selected_hit_is_observation_only_not_a_gate") is True
        and all(receipt.get(key) is False for key in false_keys)
        and set(receipt.get("probe_case_ids", {})) == set(FOLDS)
        and len(set(receipt["probe_case_ids"].values())) == 4
    ):
        raise RuntimeError("D5-A zero-step receipt semantics are invalid")


def load_and_validate_metrics(path: Path, receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 8:
        raise RuntimeError(f"Expected eight zero-step metric rows, found {len(rows)}")

    expected_pairs = {(fold, candidate) for fold in FOLDS for candidate in CANDIDATES}
    actual_pairs = {(row["fold"], row["candidate"]) for row in rows}
    if actual_pairs != expected_pairs:
        raise RuntimeError("Fold/candidate metric pairing is incomplete")

    numeric = (
        "descriptor_abs_max",
        "logit_abs_max",
        "total_loss",
        "case_balanced_bce",
        "positive_mass_nll",
        "top32_margin",
        "gradient_norm",
    )
    integer = (
        "candidate_count",
        "positive_count",
        "descriptor_dimensions",
        "selected_count",
        "selected_positive_count_observation_only",
        "selected_hit_observation_only",
        "parameter_hash_unchanged",
        "optimizer_steps",
        "dev_cases_accessed",
    )
    converted: list[dict[str, Any]] = []
    for row in rows:
        item: dict[str, Any] = dict(row)
        for key in numeric:
            item[key] = float(row[key])
            if not math.isfinite(item[key]):
                raise RuntimeError(f"Non-finite {key}: {row}")
        for key in integer:
            item[key] = int(row[key])
        fold = str(item["fold"])
        candidate = str(item["candidate"])
        expected_dimensions = 13 if candidate == "V0" else 27
        if not (
            item["case_id"] == receipt["probe_case_ids"][fold]
            and item["candidate_count"] == 8192
            and item["positive_count"] > 0
            and item["descriptor_dimensions"] == expected_dimensions
            and item["gradient_norm"] > 0.0
            and item["selected_count"] == 32
            and item["selected_positive_count_observation_only"] >= 0
            and item["selected_hit_observation_only"] in (0, 1)
            and item["parameter_hash_unchanged"] == 1
            and item["optimizer_steps"] == 0
            and item["dev_cases_accessed"] == 0
        ):
            raise RuntimeError(f"Unsafe zero-step metric row: {row}")
        if candidate == "V0" and not (
            item["positive_mass_nll"] == 0.0 and item["top32_margin"] == 0.0
        ):
            raise RuntimeError("V0 unexpectedly used V1-only set losses")
        converted.append(item)
    return sorted(converted, key=lambda row: (FOLDS.index(row["fold"]), row["candidate"]))


def validate_transport_receipts(
    transport_path: Path, lineage_path: Path
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    transport = read_json(transport_path)
    lineage = read_json(lineage_path)
    if not (
        transport.get("status") == "transport_crlf_normalized_to_canonical_lf"
        and transport.get("source_commit") == EXPECTED_SOURCE_COMMIT
        and transport.get("source_tag") == EXPECTED_SOURCE_TAG
        and transport.get("entry_count") == 13
        and transport.get("semantic_drift_detected") is False
        and transport.get("training_started") is False
        and transport.get("sealed_data_accessed") is False
    ):
        raise RuntimeError("Overlay transport-normalization receipt is invalid")
    if not (
        lineage.get("status") == "exact_frozen_parent_report_restored"
        and lineage.get("source_commit") == EXPECTED_SOURCE_COMMIT
        and lineage.get("source_tag") == EXPECTED_SOURCE_TAG
        and lineage.get("post_hotfix_sha256") == EXPECTED_D4_RESULT_SHA256
        and lineage.get("report_content_changed") is False
        and lineage.get("transport_bytes_repaired_only") is True
        and lineage.get("training_started") is False
        and lineage.get("model_updates") == 0
        and lineage.get("sealed_data_accessed") is False
    ):
        raise RuntimeError("D4-A parent-lineage hotfix receipt is invalid")
    return transport, lineage


def aggregate_metrics(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["candidate"])].append(row)
    result: dict[str, Any] = {}
    for candidate in CANDIDATES:
        values = grouped[candidate]
        result[candidate] = {
            "rows": len(values),
            "descriptor_dimensions": int(values[0]["descriptor_dimensions"]),
            "gradient_norm_min": min(float(row["gradient_norm"]) for row in values),
            "gradient_norm_median": statistics.median(
                float(row["gradient_norm"]) for row in values
            ),
            "gradient_norm_max": max(float(row["gradient_norm"]) for row in values),
            "total_loss_min": min(float(row["total_loss"]) for row in values),
            "total_loss_median": statistics.median(
                float(row["total_loss"]) for row in values
            ),
            "total_loss_max": max(float(row["total_loss"]) for row in values),
            "selected_hit_observation_count": sum(
                int(row["selected_hit_observation_only"]) for row in values
            ),
        }
    return result


def render_report(summary: Mapping[str, Any], rows: Iterable[Mapping[str, Any]]) -> bytes:
    aggregate = summary["candidate_aggregates"]
    lines = [
        "# Mamba v1.5 D5-A V0/V1 zero-step 完整冻结结果",
        "",
        "> 本报告只证明实现、loss、selector 与 CUDA backward 路径可执行；不构成训练、候选比较、开发集评估或 sealed 数据访问。",
        "",
        "## 1. 执行结论",
        "",
        f"- 状态：`{summary['status']}`。",
        f"- GPU：`{summary['cuda_device_name']}`。",
        "- 四折各使用一个冻结 training probe，V0/V1 各执行一次 backward。",
        "- metric rows：8；backward passes：8。",
        "- optimizer constructed：`False`；optimizer steps：0；model updates：0。",
        "- checkpoint loaded/written：`False / False`。",
        "- dev、proposal confirmation、completion holdout、official test：均未访问。",
        "",
        "## 2. 候选实现",
        "",
        "- V0：冻结 D4-A 13D 描述符、`13-128-64-1` head、case-balanced BCE、top8 + conditioned FPS24。",
        "- V1：27D 双尺度局部几何描述符、共享点编码与全局 mean/max context、`219-128-64-1` head。",
        "- V1 loss：case-balanced BCE、positive-mass NLL、top32 margin，冻结权重均为 1。",
        "- V1 selector：稳定 score top32；分数相同时按 candidate index。",
        "",
        "## 3. 八条 probe 记录",
        "",
        "| Fold | Candidate | Case | Positive | Dim | Total loss | Gradient norm | Selected positive* | Hit* |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {fold} | {candidate} | `{case_id}` | {positive_count} | "
            "{descriptor_dimensions} | {total_loss:.9g} | {gradient_norm:.9g} | "
            "{selected_positive_count_observation_only} | "
            "{selected_hit_observation_only} |".format(**row)
        )
    lines.extend(
        [
            "",
            "\\* 随机初始化下的 selected-positive/hit 仅用于确认 selector 路径，不是 gate，也不得用于 V0/V1 选择。",
            "",
            "## 4. 候选聚合（非比较性）",
            "",
            "| Candidate | Rows | Dim | Loss min/median/max | Gradient min/median/max | Observed hits* |",
            "| --- | ---: | ---: | --- | --- | ---: |",
        ]
    )
    for candidate in CANDIDATES:
        item = aggregate[candidate]
        lines.append(
            f"| {candidate} | {item['rows']} | {item['descriptor_dimensions']} | "
            f"{item['total_loss_min']:.9g} / {item['total_loss_median']:.9g} / "
            f"{item['total_loss_max']:.9g} | {item['gradient_norm_min']:.9g} / "
            f"{item['gradient_norm_median']:.9g} / {item['gradient_norm_max']:.9g} | "
            f"{item['selected_hit_observation_count']} / 4 |"
        )
    lines.extend(
        [
            "",
            "## 5. 完整性与传输修复",
            "",
            "- 原始 overlay、13 文件内容清单及规范 LF 安装均有 SHA256 绑定。",
            "- D4-A 父报告按预注册 lineage 精确恢复；只修复传输字节，不更改报告内容。",
            "- candidate lock、zero-step 三件套和两份修复凭据均进入最终归档。",
            "",
            "## 6. 可解释范围",
            "",
            "本结果证明 V0/V1 在四个 training probe 上输出有限、梯度非零、backward 后参数哈希不变。它不证明训练收敛、out-of-fold 泛化、V1 优于 V0，也不授权 seed-1、全 development 训练、proposal confirmation 或 D5-B。",
            "",
            "## 7. 权限边界与下一步",
            "",
            "- `D5A_seed0_training_authorized=false`。",
            "- `D5A_seed1_training_authorized=false`。",
            "- `D5B_implementation_authorized=false`。",
            "- `D5_candidate_selection_authorized=false`。",
            "- `protected_or_sealed_data_accessed=false`。",
            "- 下一步仅可单独预注册 D5-A seed-0 training execution authorization，并先运行不启动训练的 training preflight。",
            "",
        ]
    )
    return ("\n".join(lines)).encode("utf-8")


def write_locked(output: Path, files: Mapping[str, bytes]) -> None:
    expected = dict(files)
    expected["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(expected.items())
    ).encode("ascii")
    if output.exists():
        existing = {
            path.relative_to(output).as_posix(): path.read_bytes()
            for path in output.rglob("*")
            if path.is_file()
        }
        if existing != expected:
            raise RuntimeError(f"Refusing non-identical result freeze: {output}")
        print(f"[locked] existing D5-A zero-step result is byte-identical: {output}")
        return
    working = output.with_name(f".{output.name}.working")
    if working.exists():
        raise RuntimeError(f"Working result directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in expected.items():
        path = working / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    os.replace(working, output)
    print(f"[saved] immutable D5-A zero-step result: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_lock_dir", type=Path, required=True)
    parser.add_argument("--zero_step_dir", type=Path, required=True)
    parser.add_argument("--transport_receipt", type=Path, required=True)
    parser.add_argument("--lineage_receipt", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL_PATH)
    args = parser.parse_args()

    protocol = read_json(args.protocol.resolve())
    validate_protocol(protocol)
    candidate = args.candidate_lock_dir.resolve()
    zero = args.zero_step_dir.resolve()
    candidate_manifest = verify_manifest(candidate)
    zero_manifest = verify_manifest(zero)

    candidate_receipt_path = candidate / "protocol_lock_receipt.json"
    candidate_receipt = read_json(candidate_receipt_path)
    if not (
        candidate_receipt.get("status")
        == "D5_candidate_training_protocol_locked_non_runnable"
        and candidate_receipt.get("D5A_seed0_training_authorized") is False
        and candidate_receipt.get("D5A_seed1_training_authorized") is False
        and candidate_receipt.get("D5B_implementation_authorized") is False
        and candidate_receipt.get("D5_candidate_selection_authorized") is False
        and candidate_receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Candidate protocol lock is not safely frozen")

    zero_receipt_path = zero / "zero_step_preflight_receipt.json"
    zero_metrics_path = zero / "fold_candidate_probe_metrics.csv"
    zero_report_path = zero / "zero_step_preflight_report_zh.md"
    zero_receipt = read_json(zero_receipt_path)
    validate_zero_receipt(zero_receipt)
    rows = load_and_validate_metrics(zero_metrics_path, zero_receipt)
    transport, lineage = validate_transport_receipts(
        args.transport_receipt.resolve(), args.lineage_receipt.resolve()
    )

    summary = {
        "result_version": VERSION,
        "status": "D5A_V0_V1_zero_step_frozen_complete_training_still_locked",
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "source_tag": EXPECTED_SOURCE_TAG,
        "cuda_device_name": zero_receipt["cuda_device_name"],
        "folds": 4,
        "training_probe_cases": 4,
        "candidates_per_probe": 2,
        "metric_rows": 8,
        "backward_passes": 8,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "checkpoint_loaded": False,
        "checkpoint_written": False,
        "dev_cases_accessed": 0,
        "selected_hit_observation_only_not_a_gate": True,
        "candidate_aggregates": aggregate_metrics(rows),
        "input_sha256": {
            "freeze_protocol": sha256_file(args.protocol.resolve()),
            "candidate_lock_manifest": candidate_manifest,
            "candidate_lock_receipt": sha256_file(candidate_receipt_path),
            "zero_step_manifest": zero_manifest,
            "zero_step_receipt": sha256_file(zero_receipt_path),
            "zero_step_metrics": sha256_file(zero_metrics_path),
            "zero_step_report": sha256_file(zero_report_path),
            "transport_normalization_receipt": sha256_file(
                args.transport_receipt.resolve()
            ),
            "parent_lineage_hotfix_receipt": sha256_file(
                args.lineage_receipt.resolve()
            ),
        },
        "implementation_sha256": zero_receipt["implementation_sha256"],
        "transport_normalization": {
            "entry_count": transport["entry_count"],
            "normalized_entry_count": transport["normalized_entry_count"],
            "semantic_drift_detected": False,
        },
        "parent_lineage": {
            "post_hotfix_sha256": lineage["post_hotfix_sha256"],
            "report_content_changed": False,
        },
        "D5A_seed0_training_authorized": False,
        "D5A_seed1_training_authorized": False,
        "development_all_training_authorized": False,
        "proposal_confirmation_access_authorized": False,
        "D5B_implementation_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "completion_holdout_accessed": False,
        "official_test_accessed": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_D5A_seed0_training_execution_authorization_and_preflight_only",
    }
    files = {
        "d5a_v0_v1_zero_step_complete_result_zh.md": render_report(summary, rows),
        "d5a_v0_v1_zero_step_result_summary.json": canonical_json(summary),
    }
    write_locked(args.output_dir.resolve(), files)
    verify_manifest(args.output_dir.resolve())
    print("[done] D5-A V0/V1 zero-step complete result frozen")
    print("[locked] training=false seed1=false D5B=false selection=false sealed=false")
    print("[next] archive and restore-verify this zero-step milestone")


if __name__ == "__main__":
    main()
