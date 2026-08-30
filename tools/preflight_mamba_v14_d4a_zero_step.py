#!/usr/bin/env python3
"""Run the authorized Mamba v1.4 D4-A implementation zero-step preflight."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import sys
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, Iterable, Mapping, Sequence

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.mamba_d4a_proposal import (  # noqa: E402
    D4AProposalHead,
    case_balanced_binary_cross_entropy,
    geometry_descriptor_13d,
    select_top8_conditioned_fps24,
)


VERSION = "mamba-v14-d4a-zero-step-preflight-v1"
FOLDS = ("A", "B", "C", "D")
EXPECTED_PARENT_PROTOCOL_SHA256 = (
    "1fd3d6dff2876d4dbaec92b6dc34e61ba833ddee0ff7bbe4cd0abf64488eb24a"
)
EXPECTED_ARRAYS = {
    "partial",
    "implant",
    "gt",
    "centroid",
    "scale",
    "reference_rim_mask",
}


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


def validate_preflight_protocol(protocol: Dict[str, Any]) -> None:
    scope = protocol.get("scope", {})
    probe = protocol.get("probe_cases", {})
    descriptor = protocol.get("descriptor", {})
    head = protocol.get("proposal_head", {})
    selector = protocol.get("selector", {})
    zero = protocol.get("zero_step_contract", {})
    if (
        protocol.get("protocol_id") != VERSION
        or protocol.get("lineage", {}).get(
            "candidate_training_protocol_sha256"
        )
        != EXPECTED_PARENT_PROTOCOL_SHA256
        or scope.get("implementation_allowed") is not True
        or scope.get("zero_step_preflight_allowed") is not True
        or any(
            scope.get(key) is not False
            for key in (
                "D4A_training_allowed",
                "D4_full_training_allowed",
                "development_evaluation_allowed",
                "candidate_selection_allowed",
                "protected_data_access_allowed",
            )
        )
        or probe.get("folds") != list(FOLDS)
        or probe.get("total_cases") != 4
        or probe.get("dev_case_access") != 0
        or descriptor.get("candidate_count") != 8192
        or descriptor.get("dimensions") != 13
        or descriptor.get("knn") != 16
        or descriptor.get("query_chunk_size") != 512
        or head.get("layers") != [13, 128, 64, 1]
        or head.get("seed") != 0
        or selector.get("mandatory_top_score_count") != 8
        or selector.get("ranked_pool_size") != 256
        or selector.get("diversified_count") != 24
        or selector.get("selected_count") != 32
        or zero.get("device") != "CUDA_required"
        or zero.get("optimizer_constructed") is not False
        or zero.get("optimizer_steps") != 0
        or zero.get("model_updates") != 0
        or zero.get("checkpoint_loaded") is not False
        or zero.get("checkpoint_written") is not False
    ):
        raise RuntimeError("D4-A zero-step preflight protocol drifted")


def verify_lineage(
    candidate_lock: Path, fourfold_lock: Path, audit_dir: Path
) -> Dict[str, str]:
    candidate_manifest = verify_manifest(candidate_lock)
    fourfold_manifest = verify_manifest(fourfold_lock)
    audit_manifest = verify_manifest(audit_dir)

    candidate_receipt_path = candidate_lock / "protocol_lock_receipt.json"
    candidate_protocol_path = candidate_lock / "candidate_training_protocol_v1.json"
    fourfold_receipt_path = fourfold_lock / "d4_m2_protocol_lock_receipt.json"
    audit_summary_path = audit_dir / "generation_audit_summary.json"
    portable_manifest_path = audit_dir / "manifest_portable.jsonl"
    candidate_receipt = json.loads(
        candidate_receipt_path.read_text(encoding="utf-8")
    )
    fourfold_receipt = json.loads(
        fourfold_receipt_path.read_text(encoding="utf-8")
    )
    audit_summary = json.loads(audit_summary_path.read_text(encoding="utf-8"))
    lineage = candidate_receipt.get("lineage_sha256", {})
    if (
        sha256_file(candidate_protocol_path) != EXPECTED_PARENT_PROTOCOL_SHA256
        or candidate_receipt.get("status")
        != "candidate_training_protocol_locked_non_runnable"
        or candidate_receipt.get(
            "implementation_and_zero_step_preflight_authorized_next"
        )
        is not True
        or any(
            candidate_receipt.get(key) is not False
            for key in (
                "D4A_execution_authorized",
                "D4_training_authorized",
                "D4_candidate_selection_authorized",
                "training_started",
                "selection_started",
                "protected_data_accessed",
            )
        )
        or lineage.get("fourfold_manifest") != fourfold_manifest
        or lineage.get("generation_audit_manifest") != audit_manifest
        or lineage.get("portable_manifest") != sha256_file(portable_manifest_path)
        or fourfold_receipt.get("status")
        != "d4_m2_generation_and_fourfold_protocol_locked"
        or fourfold_receipt.get("D4_training_authorized") is not False
        or fourfold_receipt.get("protected_data_accessed") is not False
        or audit_summary.get("status")
        != "generation_integrity_passed_training_and_selection_still_locked"
        or audit_summary.get("source_skulls") != 100
        or audit_summary.get("derived_cases") != 400
        or audit_summary.get("D4_training_authorized") is not False
        or audit_summary.get("D4_candidate_selection_authorized") is not False
        or audit_summary.get("protected_data_used") is not False
    ):
        raise RuntimeError("D4-A preflight lineage semantics are invalid")

    return {
        "candidate_lock_manifest": candidate_manifest,
        "candidate_lock_receipt": sha256_file(candidate_receipt_path),
        "fourfold_lock_manifest": fourfold_manifest,
        "fourfold_lock_receipt": sha256_file(fourfold_receipt_path),
        "generation_audit_manifest": audit_manifest,
        "generation_audit_summary": sha256_file(audit_summary_path),
        "portable_manifest": sha256_file(portable_manifest_path),
    }


def read_case_ids(path: Path) -> list[str]:
    values = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not values or len(values) != len(set(values)):
        raise RuntimeError(f"Invalid case-ID list: {path}")
    return values


def choose_probe_cases(fourfold_lock: Path) -> Dict[str, str]:
    chosen: Dict[str, str] = {}
    already_used = set()
    for fold in FOLDS:
        train = set(
            read_case_ids(fourfold_lock / f"fold{fold}_train_case_ids.txt")
        )
        dev = set(read_case_ids(fourfold_lock / f"fold{fold}_dev_case_ids.txt"))
        if train & dev:
            raise RuntimeError(f"Fold {fold} train/dev case leakage")
        candidates = sorted(train - already_used)
        if not candidates:
            raise RuntimeError(f"Fold {fold} has no unused training probe case")
        chosen[fold] = candidates[0]
        already_used.add(candidates[0])
    if len(set(chosen.values())) != len(FOLDS):
        raise RuntimeError("D4-A probe cases are not distinct")
    return chosen


def parse_portable_path(raw: str, manifest_dir: Path) -> Path:
    text = str(raw)
    if not text or Path(text).is_absolute() or PureWindowsPath(text).is_absolute():
        raise RuntimeError(f"Non-portable point path: {raw}")
    return (manifest_dir / text.replace("\\", os.sep)).resolve()


def load_manifest(audit_dir: Path) -> Dict[str, Dict[str, Any]]:
    manifest = audit_dir / "manifest_portable.jsonl"
    records: Dict[str, Dict[str, Any]] = {}
    with manifest.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            case_id = str(row.get("case_id", ""))
            if not case_id or case_id in records:
                raise RuntimeError(
                    f"Invalid portable manifest case at line {line_number}"
                )
            records[case_id] = row
    if len(records) != 400:
        raise RuntimeError("D4 portable manifest must contain 400 cases")
    return records


def load_case(
    row: Mapping[str, Any], manifest_dir: Path
) -> tuple[np.ndarray, np.ndarray, Path]:
    case_id = str(row["case_id"])
    point_path = parse_portable_path(str(row["point_path"]), manifest_dir)
    if point_path.name != f"{case_id}.npz" or not point_path.is_file():
        raise RuntimeError(f"D4 probe point asset is missing: {point_path}")
    if sha256_file(point_path) != str(row["derived_case_sha256"]).lower():
        raise RuntimeError(f"D4 probe point hash mismatch: {case_id}")
    with np.load(point_path, allow_pickle=False) as sample:
        if set(sample.files) != EXPECTED_ARRAYS:
            raise RuntimeError(f"{case_id}: unexpected NPZ members")
        partial = sample["partial"].copy()
        rim = sample["reference_rim_mask"].copy()
    expected_rim = int(row["point_audit"]["reference_rim_points"])
    if not (
        partial.shape == (8192, 3)
        and partial.dtype == np.float32
        and np.isfinite(partial).all()
        and rim.shape == (8192,)
        and rim.dtype == np.bool_
        and int(rim.sum()) == expected_rim
        and 0 < expected_rim < 8192
        and np.allclose(partial.mean(axis=0), 0.0, atol=2.0e-6)
        and math.isclose(
            float(np.linalg.norm(partial, axis=1).max()),
            1.0,
            rel_tol=0.0,
            abs_tol=2.0e-6,
        )
    ):
        raise RuntimeError(f"{case_id}: D4 probe NPZ contract failed")
    return partial, rim, point_path


def module_state_hash(module: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(module.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(tensor.dtype).encode("ascii") + b"\0")
        digest.update(str(tuple(tensor.shape)).encode("ascii") + b"\0")
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def implementation_hashes(
    protocol_path: Path, test_script: Path, launcher_script: Path
) -> Dict[str, str]:
    return {
        "preflight_protocol": sha256_file(protocol_path),
        "proposal_module": sha256_file(
            REPO_ROOT / "utils/mamba_d4a_proposal.py"
        ),
        "preflight_runner": sha256_file(Path(__file__).resolve()),
        "tests": sha256_file(test_script.resolve()),
        "launcher": sha256_file(launcher_script.resolve()),
    }


def render_report(receipt: Mapping[str, Any]) -> bytes:
    return (
        "# Mamba v1.4 D4-A zero-step preflight\n\n"
        "> 本结果只验证实现路径，不训练、不评估 dev、不选择候选。\n\n"
        f"- folds：{receipt['folds']}。\n"
        f"- train probe cases：{receipt['train_probe_cases']}。\n"
        f"- optimizer steps：{receipt['optimizer_steps']}。\n"
        f"- model updates：{receipt['model_updates']}。\n"
        f"- dev cases accessed：{receipt['dev_cases_accessed']}。\n"
        f"- protected data accessed：`{receipt['protected_data_accessed']}`。\n"
        "- selected-hit 仅为随机初始化下的路径观测，不构成 gate。\n"
        "- 下一步：单独冻结 D4-A training execution authorization。\n"
    ).encode("utf-8")


def verify_existing(
    output: Path, expected_implementation: Mapping[str, str]
) -> bool:
    if not output.exists():
        return False
    verify_manifest(output)
    receipt = json.loads(
        (output / "zero_step_preflight_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    if not (
        receipt.get("preflight_version") == VERSION
        and receipt.get("status") == "implementation_zero_step_preflight_passed"
        and receipt.get("implementation_sha256") == expected_implementation
        and receipt.get("folds") == 4
        and receipt.get("train_probe_cases") == 4
        and receipt.get("dev_cases_accessed") == 0
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("checkpoint_loaded") is False
        and receipt.get("checkpoint_written") is False
        and receipt.get("D4A_training_authorized") is False
        and receipt.get("D4_training_authorized") is False
        and receipt.get("selection_started") is False
        and receipt.get("protected_data_accessed") is False
    ):
        raise RuntimeError("Existing D4-A preflight receipt is invalid")
    print(f"[locked] existing D4-A zero-step preflight is valid: {output}")
    return True


def write_locked(output: Path, files: Mapping[str, bytes]) -> None:
    working = output.with_name(f".{output.name}.working")
    if output.exists() or working.exists():
        raise RuntimeError(f"D4-A preflight output requires inspection: {output}")
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    manifest_payload = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    (working / "files.sha256").write_bytes(manifest_payload)
    os.replace(working, output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_lock_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument(
        "--protocol",
        type=Path,
        default=REPO_ROOT
        / "docs/mamba_v14_d4a_zero_step_preflight_protocol_v1.json",
    )
    parser.add_argument("--test_script", type=Path, required=True)
    parser.add_argument("--launcher_script", type=Path, required=True)
    args = parser.parse_args()

    protocol_path = args.protocol.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    validate_preflight_protocol(protocol)
    candidate_lock = args.candidate_lock_dir.resolve()
    fourfold_lock = args.fourfold_lock_dir.resolve()
    audit_dir = args.generation_audit_dir.resolve()
    output = args.output_dir.resolve()
    lineage = verify_lineage(candidate_lock, fourfold_lock, audit_dir)
    current_implementation = implementation_hashes(
        protocol_path, args.test_script, args.launcher_script
    )
    if verify_existing(output, current_implementation):
        return

    if not torch.cuda.is_available():
        raise RuntimeError("D4-A zero-step preflight requires CUDA")
    device = torch.device("cuda")
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)

    manifest_rows = load_manifest(audit_dir)
    probes = choose_probe_cases(fourfold_lock)
    metrics = []
    for fold_index, fold in enumerate(FOLDS):
        case_id = probes[fold]
        if case_id not in manifest_rows:
            raise RuntimeError(f"Probe case is absent from manifest: {case_id}")
        manifest_row = manifest_rows[case_id]
        partial_np, rim_np, point_path = load_case(manifest_row, audit_dir)
        partial = torch.from_numpy(partial_np).unsqueeze(0).to(device)
        labels = torch.from_numpy(rim_np).unsqueeze(0).to(device)

        with torch.no_grad():
            descriptors = geometry_descriptor_13d(
                partial, knn=16, epsilon=1.0e-8, query_chunk_size=512
            )
        torch.manual_seed(0)
        torch.cuda.manual_seed_all(0)
        head = D4AProposalHead().to(device).train()
        state_before = module_state_hash(head)
        head.zero_grad(set_to_none=True)
        logits = head(descriptors)
        loss = case_balanced_binary_cross_entropy(logits, labels)
        loss.backward()

        gradients = [
            parameter.grad
            for parameter in head.parameters()
            if parameter.requires_grad
        ]
        if not gradients or any(gradient is None for gradient in gradients):
            raise RuntimeError(f"Fold {fold} proposal gradients are missing")
        gradient_norm = torch.linalg.vector_norm(
            torch.cat([gradient.detach().reshape(-1) for gradient in gradients])
        )
        if not torch.isfinite(gradient_norm) or gradient_norm <= 0:
            raise RuntimeError(f"Fold {fold} proposal gradients are invalid")

        selected = select_top8_conditioned_fps24(
            logits.detach(),
            partial,
            mandatory_top_score_count=8,
            ranked_pool_size=256,
            diversified_count=24,
        )
        score_order = torch.argsort(
            logits.detach()[0], descending=True, stable=True
        )
        ranked_pool = set(score_order[:256].cpu().tolist())
        selected_list = selected[0].cpu().tolist()
        if (
            selected.shape != (1, 32)
            or len(set(selected_list)) != 32
            or not set(selected_list).issubset(ranked_pool)
            or selected_list[:8] != score_order[:8].cpu().tolist()
        ):
            raise RuntimeError(f"Fold {fold} selector contract failed")
        state_after = module_state_hash(head)
        if state_after != state_before:
            raise RuntimeError(f"Fold {fold} head changed without an optimizer step")

        selected_positive = int(labels[0, selected[0]].sum().item())
        metrics.append(
            {
                "fold": fold,
                "case_id": case_id,
                "point_path": str(manifest_row["point_path"]),
                "candidate_count": partial.shape[1],
                "positive_count": int(labels.sum().item()),
                "descriptor_dimensions": descriptors.shape[-1],
                "descriptor_abs_max": float(descriptors.abs().amax().item()),
                "logit_abs_max": float(logits.detach().abs().amax().item()),
                "loss": float(loss.detach().item()),
                "gradient_norm": float(gradient_norm.item()),
                "selected_count": len(selected_list),
                "selected_positive_count_observation_only": selected_positive,
                "selected_hit_observation_only": int(selected_positive > 0),
                "parameter_hash_unchanged": int(state_before == state_after),
                "optimizer_steps": 0,
                "dev_cases_accessed": 0,
            }
        )
        del head, logits, loss, descriptors, partial, labels, gradients
        torch.cuda.empty_cache()

    if len(metrics) != 4 or not all(
        all(
            math.isfinite(float(row[key]))
            for key in (
                "descriptor_abs_max",
                "logit_abs_max",
                "loss",
                "gradient_norm",
            )
        )
        for row in metrics
    ):
        raise RuntimeError("D4-A zero-step metrics are incomplete or non-finite")

    receipt = {
        "preflight_version": VERSION,
        "status": "implementation_zero_step_preflight_passed",
        "lineage_sha256": lineage,
        "implementation_sha256": current_implementation,
        "device": str(device),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "folds": 4,
        "train_probe_cases": 4,
        "probe_case_ids": probes,
        "dev_cases_accessed": 0,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "backward_passes": 4,
        "model_updates": 0,
        "checkpoint_loaded": False,
        "checkpoint_written": False,
        "selected_hit_is_observation_only_not_a_gate": True,
        "D4A_training_authorized": False,
        "D4_training_authorized": False,
        "D4_candidate_selection_authorized": False,
        "selection_started": False,
        "holdout_accessed": False,
        "protected_data_accessed": False,
        "next_step": "separate_D4A_training_execution_authorization",
    }
    fieldnames = list(metrics[0])
    files = {
        "fold_probe_metrics.csv": csv_bytes(fieldnames, metrics),
        "zero_step_preflight_receipt.json": canonical_json(receipt),
        "zero_step_preflight_report_zh.md": render_report(receipt),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    write_locked(output, files)
    verify_manifest(output)
    print(f"[saved] immutable D4-A zero-step preflight: {output}")
    print("[done] folds=4 train_probes=4 optimizer_steps=0 model_updates=0")
    print("[locked] D4A_training=false D4_training=false selection=false protected=false")
    print("[next] separate D4-A training execution authorization")


if __name__ == "__main__":
    main()
