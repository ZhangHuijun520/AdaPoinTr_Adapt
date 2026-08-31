#!/usr/bin/env python3
"""Run the authorized Mamba v1.5 D5-A implementation zero-step preflight."""

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

from utils.mamba_d5a_proposal import (  # noqa: E402
    D4AProposalHead,
    D5V1ContextHead,
    case_balanced_binary_cross_entropy,
    d5_v1_set_level_loss,
    geometry_descriptor_13d,
    geometry_descriptor_27d,
    select_deterministic_top32,
    select_top8_conditioned_fps24,
)


VERSION = "mamba-v15-d5a-zero-step-preflight-v1"
FOLDS = ("A", "B", "C", "D")
EXPECTED_PARENT_PROTOCOL_SHA256 = (
    "135cd7a99da57b36d94220fc8b6ed0ec73b87bb35443ddbd898e1216edba03ed"
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
    v0 = protocol.get("V0", {})
    v1 = protocol.get("V1", {})
    zero = protocol.get("zero_step_contract", {})
    if (
        protocol.get("protocol_id") != VERSION
        or protocol.get("lineage", {}).get("candidate_training_protocol_sha256")
        != EXPECTED_PARENT_PROTOCOL_SHA256
        or scope.get("V0_V1_implementation_allowed") is not True
        or scope.get("zero_step_preflight_allowed") is not True
        or any(
            scope.get(key) is not False
            for key in (
                "D5A_seed0_training_allowed",
                "D5A_seed1_training_allowed",
                "development_evaluation_allowed",
                "proposal_confirmation_access_allowed",
                "D5B_implementation_allowed",
                "candidate_selection_allowed",
                "protected_or_sealed_data_access_allowed",
            )
        )
        or probe.get("folds") != list(FOLDS)
        or probe.get("total_cases") != 4
        or probe.get("candidates_per_case") != ["V0", "V1"]
        or probe.get("dev_case_access") != 0
        or probe.get("sealed_case_access") != 0
        or v0.get("candidate_count") != 8192
        or v0.get("descriptor_dimensions") != 13
        or v0.get("head_layers") != [13, 128, 64, 1]
        or v0.get("selected_count") != 32
        or v1.get("candidate_count") != 8192
        or v1.get("descriptor_dimensions") != 27
        or v1.get("knn_scales") != [16, 32]
        or v1.get("point_encoder_layers") != [27, 64, 64]
        or v1.get("classifier_layers") != [219, 128, 64, 1]
        or v1.get("selector") != "deterministic_score_top32"
        or v1.get("selected_count") != 32
        or v1.get("positive_mass_softmax_temperature") != 1.0
        or v1.get("top32_margin") != 1.0
        or v1.get("loss_weights")
        != {
            "case_balanced_binary_cross_entropy": 1.0,
            "positive_mass_nll": 1.0,
            "top32_margin": 1.0,
        }
        or zero.get("device") != "CUDA_required"
        or zero.get("optimizer_constructed") is not False
        or zero.get("optimizer_steps") != 0
        or zero.get("backward_passes") != 8
        or zero.get("model_updates") != 0
        or zero.get("checkpoint_loaded") is not False
        or zero.get("checkpoint_written") is not False
        or zero.get("dev_cases_accessed") != 0
        or zero.get("proposal_confirmation_accessed") is not False
    ):
        raise RuntimeError("D5-A zero-step preflight protocol drifted")


def verify_lineage(
    candidate_lock: Path, fourfold_lock: Path, audit_dir: Path
) -> Dict[str, str]:
    candidate_manifest = verify_manifest(candidate_lock)
    fourfold_manifest = verify_manifest(fourfold_lock)
    audit_manifest = verify_manifest(audit_dir)
    candidate_receipt_path = candidate_lock / "protocol_lock_receipt.json"
    candidate_protocol_path = candidate_lock / "candidate_training_protocol_v1.json"
    fourfold_receipt_path = fourfold_lock / "d5_development_protocol_lock_receipt.json"
    audit_summary_path = audit_dir / "generation_audit_summary.json"
    portable_manifest_path = audit_dir / "manifest_portable.jsonl"
    candidate_receipt = json.loads(candidate_receipt_path.read_text(encoding="utf-8"))
    fourfold_receipt = json.loads(fourfold_receipt_path.read_text(encoding="utf-8"))
    audit_summary = json.loads(audit_summary_path.read_text(encoding="utf-8"))
    lineage = candidate_receipt.get("lineage_sha256", {})
    if (
        sha256_file(candidate_protocol_path) != EXPECTED_PARENT_PROTOCOL_SHA256
        or candidate_receipt.get("status")
        != "D5_candidate_training_protocol_locked_non_runnable"
        or candidate_receipt.get(
            "V0_V1_implementation_and_zero_step_preflight_authorized_next"
        )
        is not True
        or any(
            candidate_receipt.get(key) is not False
            for key in (
                "D5A_seed0_training_authorized",
                "D5A_seed1_training_authorized",
                "development_all_training_authorized",
                "proposal_confirmation_access_authorized",
                "D5B_implementation_authorized",
                "D5B_training_authorized",
                "D5_candidate_selection_authorized",
                "training_started",
                "selection_started",
                "protected_or_sealed_data_accessed",
            )
        )
        or lineage.get("fourfold_manifest") != fourfold_manifest
        or lineage.get("audit_manifest") != audit_manifest
        or lineage.get("portable_manifest") != sha256_file(portable_manifest_path)
        or fourfold_receipt.get("status")
        != "d5_development_generation_and_fourfold_protocol_locked"
        or fourfold_receipt.get("source_fold_leakage") != 0
        or fourfold_receipt.get("proposal_confirmation_accessed") is not False
        or fourfold_receipt.get("completion_holdout_accessed") is not False
        or fourfold_receipt.get("official_test_accessed") is not False
        or audit_summary.get("status")
        != "generation_integrity_passed_model_training_selection_and_sealed_still_locked"
        or audit_summary.get("source_skulls") != 100
        or audit_summary.get("derived_cases") != 400
        or audit_summary.get("D5A_model_implementation_authorized") is not False
        or audit_summary.get("D5A_training_authorized") is not False
        or audit_summary.get("D5B_training_authorized") is not False
        or audit_summary.get("D5_candidate_selection_authorized") is not False
        or audit_summary.get("proposal_confirmation_accessed") is not False
        or audit_summary.get("completion_holdout_accessed") is not False
        or audit_summary.get("official_test_accessed") is not False
    ):
        raise RuntimeError("D5-A preflight lineage semantics are invalid")
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
        train = set(read_case_ids(fourfold_lock / f"fold{fold}_train_case_ids.txt"))
        dev = set(read_case_ids(fourfold_lock / f"fold{fold}_dev_case_ids.txt"))
        if train & dev:
            raise RuntimeError(f"Fold {fold} train/dev case leakage")
        candidates = sorted(train - already_used)
        if not candidates:
            raise RuntimeError(f"Fold {fold} has no unused training probe case")
        chosen[fold] = candidates[0]
        already_used.add(candidates[0])
    if len(set(chosen.values())) != len(FOLDS):
        raise RuntimeError("D5-A probe cases are not distinct")
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
                raise RuntimeError(f"Invalid portable manifest case at line {line_number}")
            records[case_id] = row
    if len(records) != 400:
        raise RuntimeError("D5 portable manifest must contain 400 cases")
    return records


def load_case(
    row: Mapping[str, Any], manifest_dir: Path
) -> tuple[np.ndarray, np.ndarray]:
    case_id = str(row["case_id"])
    point_path = parse_portable_path(str(row["point_path"]), manifest_dir)
    if point_path.name != f"{case_id}.npz" or not point_path.is_file():
        raise RuntimeError(f"D5 probe point asset is missing: {point_path}")
    if sha256_file(point_path) != str(row["derived_case_sha256"]).lower():
        raise RuntimeError(f"D5 probe point hash mismatch: {case_id}")
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
        raise RuntimeError(f"{case_id}: D5 probe NPZ contract failed")
    return partial, rim


def module_state_hash(module: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(module.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(tensor.dtype).encode("ascii") + b"\0")
        digest.update(str(tuple(tensor.shape)).encode("ascii") + b"\0")
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def gradient_norm(module: torch.nn.Module) -> torch.Tensor:
    gradients = [
        parameter.grad for parameter in module.parameters() if parameter.requires_grad
    ]
    if not gradients or any(gradient is None for gradient in gradients):
        raise RuntimeError("D5-A proposal gradients are missing")
    value = torch.linalg.vector_norm(
        torch.cat([gradient.detach().reshape(-1) for gradient in gradients])
    )
    if not torch.isfinite(value) or value <= 0:
        raise RuntimeError("D5-A proposal gradients are invalid")
    return value


def implementation_hashes(
    protocol_path: Path, test_script: Path, launcher_script: Path
) -> Dict[str, str]:
    return {
        "preflight_protocol": sha256_file(protocol_path),
        "d4a_reference_module": sha256_file(REPO_ROOT / "utils/mamba_d4a_proposal.py"),
        "d5a_proposal_module": sha256_file(REPO_ROOT / "utils/mamba_d5a_proposal.py"),
        "preflight_runner": sha256_file(Path(__file__).resolve()),
        "tests": sha256_file(test_script.resolve()),
        "launcher": sha256_file(launcher_script.resolve()),
    }


def render_report(receipt: Mapping[str, Any]) -> bytes:
    return (
        "# Mamba v1.5 D5-A V0/V1 zero-step preflight\n\n"
        "> 本结果只验证冻结实现路径，不训练、不访问 dev 或 sealed 数据。\n\n"
        f"- folds / train probes：{receipt['folds']} / {receipt['train_probe_cases']}。\n"
        f"- candidates per probe：{receipt['candidates_per_probe']}。\n"
        f"- backward passes：{receipt['backward_passes']}。\n"
        f"- optimizer steps / model updates：{receipt['optimizer_steps']} / {receipt['model_updates']}。\n"
        f"- dev cases accessed：{receipt['dev_cases_accessed']}。\n"
        f"- proposal confirmation accessed：`{receipt['proposal_confirmation_accessed']}`。\n"
        "- 随机初始化下 selected-hit 只验证执行路径，不构成 gate。\n"
        "- 下一步：单独冻结 D5-A seed-0 training execution authorization。\n"
    ).encode("utf-8")


def verify_existing(output: Path, expected_implementation: Mapping[str, str]) -> bool:
    if not output.exists():
        return False
    verify_manifest(output)
    receipt = json.loads(
        (output / "zero_step_preflight_receipt.json").read_text(encoding="utf-8")
    )
    if not (
        receipt.get("preflight_version") == VERSION
        and receipt.get("status") == "V0_V1_implementation_zero_step_preflight_passed"
        and receipt.get("implementation_sha256") == expected_implementation
        and receipt.get("folds") == 4
        and receipt.get("train_probe_cases") == 4
        and receipt.get("candidates_per_probe") == 2
        and receipt.get("backward_passes") == 8
        and receipt.get("dev_cases_accessed") == 0
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("checkpoint_loaded") is False
        and receipt.get("checkpoint_written") is False
        and receipt.get("D5A_seed0_training_authorized") is False
        and receipt.get("D5A_seed1_training_authorized") is False
        and receipt.get("D5B_implementation_authorized") is False
        and receipt.get("selection_started") is False
        and receipt.get("proposal_confirmation_accessed") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Existing D5-A preflight receipt is invalid")
    print(f"[locked] existing D5-A zero-step preflight is valid: {output}")
    return True


def write_locked(output: Path, files: Mapping[str, bytes]) -> None:
    working = output.with_name(f".{output.name}.working")
    if output.exists() or working.exists():
        raise RuntimeError(f"D5-A preflight output requires inspection: {output}")
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    manifest_payload = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())
    ).encode("ascii")
    (working / "files.sha256").write_bytes(manifest_payload)
    os.replace(working, output)


def candidate_row(
    *,
    fold: str,
    case_id: str,
    candidate: str,
    descriptors: torch.Tensor,
    logits: torch.Tensor,
    loss_values: Mapping[str, torch.Tensor],
    gradient: torch.Tensor,
    selected: torch.Tensor,
    labels: torch.Tensor,
    state_unchanged: bool,
) -> Dict[str, Any]:
    selected_positive = int(labels[0, selected[0]].sum().item())
    return {
        "fold": fold,
        "case_id": case_id,
        "candidate": candidate,
        "candidate_count": descriptors.shape[1],
        "positive_count": int(labels.sum().item()),
        "descriptor_dimensions": descriptors.shape[-1],
        "descriptor_abs_max": float(descriptors.abs().amax().item()),
        "logit_abs_max": float(logits.detach().abs().amax().item()),
        "total_loss": float(loss_values["total"].detach().item()),
        "case_balanced_bce": float(
            loss_values["case_balanced_bce"].detach().item()
        ),
        "positive_mass_nll": float(loss_values["positive_mass_nll"].detach().item()),
        "top32_margin": float(loss_values["top32_margin"].detach().item()),
        "gradient_norm": float(gradient.item()),
        "selected_count": selected.shape[1],
        "selected_positive_count_observation_only": selected_positive,
        "selected_hit_observation_only": int(selected_positive > 0),
        "parameter_hash_unchanged": int(state_unchanged),
        "optimizer_steps": 0,
        "dev_cases_accessed": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_lock_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument(
        "--protocol",
        type=Path,
        default=REPO_ROOT / "docs/mamba_v15_d5a_zero_step_preflight_protocol_v1.json",
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
        raise RuntimeError("D5-A zero-step preflight requires CUDA")
    device = torch.device("cuda")
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)

    manifest_rows = load_manifest(audit_dir)
    probes = choose_probe_cases(fourfold_lock)
    metrics = []
    for fold in FOLDS:
        case_id = probes[fold]
        if case_id not in manifest_rows:
            raise RuntimeError(f"Probe case is absent from manifest: {case_id}")
        partial_np, rim_np = load_case(manifest_rows[case_id], audit_dir)
        partial = torch.from_numpy(partial_np).unsqueeze(0).to(device)
        labels = torch.from_numpy(rim_np).unsqueeze(0).to(device)
        with torch.no_grad():
            descriptor_v0 = geometry_descriptor_13d(
                partial, knn=16, epsilon=1.0e-8, query_chunk_size=512
            )
            descriptor_v1 = geometry_descriptor_27d(
                partial,
                knn_small=16,
                knn_large=32,
                epsilon=1.0e-8,
                query_chunk_size=512,
            )

        torch.manual_seed(0)
        torch.cuda.manual_seed_all(0)
        v0 = D4AProposalHead().to(device).train()
        v0_before = module_state_hash(v0)
        v0.zero_grad(set_to_none=True)
        v0_logits = v0(descriptor_v0)
        v0_bce = case_balanced_binary_cross_entropy(v0_logits, labels)
        v0_bce.backward()
        v0_gradient = gradient_norm(v0)
        v0_selected = select_top8_conditioned_fps24(v0_logits.detach(), partial)
        v0_after = module_state_hash(v0)
        metrics.append(
            candidate_row(
                fold=fold,
                case_id=case_id,
                candidate="V0",
                descriptors=descriptor_v0,
                logits=v0_logits,
                loss_values={
                    "total": v0_bce,
                    "case_balanced_bce": v0_bce,
                    "positive_mass_nll": torch.zeros_like(v0_bce),
                    "top32_margin": torch.zeros_like(v0_bce),
                },
                gradient=v0_gradient,
                selected=v0_selected,
                labels=labels,
                state_unchanged=v0_before == v0_after,
            )
        )

        torch.manual_seed(0)
        torch.cuda.manual_seed_all(0)
        v1 = D5V1ContextHead().to(device).train()
        v1_before = module_state_hash(v1)
        v1.zero_grad(set_to_none=True)
        v1_logits = v1(descriptor_v1)
        v1_losses = d5_v1_set_level_loss(v1_logits, labels)
        v1_losses["total"].backward()
        v1_gradient = gradient_norm(v1)
        v1_selected = select_deterministic_top32(v1_logits.detach())
        v1_after = module_state_hash(v1)
        metrics.append(
            candidate_row(
                fold=fold,
                case_id=case_id,
                candidate="V1",
                descriptors=descriptor_v1,
                logits=v1_logits,
                loss_values=v1_losses,
                gradient=v1_gradient,
                selected=v1_selected,
                labels=labels,
                state_unchanged=v1_before == v1_after,
            )
        )
        if v0_before != v0_after or v1_before != v1_after:
            raise RuntimeError(f"Fold {fold} head changed without optimizer step")
        del (
            v0,
            v1,
            v0_logits,
            v1_logits,
            v0_bce,
            v1_losses,
            descriptor_v0,
            descriptor_v1,
            partial,
            labels,
        )
        torch.cuda.empty_cache()

    numeric_fields = (
        "descriptor_abs_max",
        "logit_abs_max",
        "total_loss",
        "case_balanced_bce",
        "positive_mass_nll",
        "top32_margin",
        "gradient_norm",
    )
    if len(metrics) != 8 or not all(
        all(math.isfinite(float(row[key])) for key in numeric_fields) for row in metrics
    ):
        raise RuntimeError("D5-A zero-step metrics are incomplete or non-finite")

    receipt = {
        "preflight_version": VERSION,
        "status": "V0_V1_implementation_zero_step_preflight_passed",
        "lineage_sha256": lineage,
        "implementation_sha256": current_implementation,
        "device": str(device),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "folds": 4,
        "train_probe_cases": 4,
        "candidates_per_probe": 2,
        "probe_case_ids": probes,
        "dev_cases_accessed": 0,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "backward_passes": 8,
        "model_updates": 0,
        "checkpoint_loaded": False,
        "checkpoint_written": False,
        "selected_hit_is_observation_only_not_a_gate": True,
        "D5A_seed0_training_authorized": False,
        "D5A_seed1_training_authorized": False,
        "development_all_training_authorized": False,
        "proposal_confirmation_access_authorized": False,
        "D5B_implementation_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "selection_started": False,
        "proposal_confirmation_accessed": False,
        "completion_holdout_accessed": False,
        "official_test_accessed": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "separate_D5A_seed0_training_execution_authorization",
    }
    files = {
        "fold_candidate_probe_metrics.csv": csv_bytes(list(metrics[0]), metrics),
        "zero_step_preflight_receipt.json": canonical_json(receipt),
        "zero_step_preflight_report_zh.md": render_report(receipt),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    write_locked(output, files)
    verify_manifest(output)
    print(f"[saved] immutable D5-A zero-step preflight: {output}")
    print("[done] folds=4 train_probes=4 candidates=2 backward=8 optimizer_steps=0")
    print("[locked] D5A_training=false D5B=false selection=false sealed=false")
    print("[next] separate D5-A seed-0 training execution authorization")


if __name__ == "__main__":
    main()
