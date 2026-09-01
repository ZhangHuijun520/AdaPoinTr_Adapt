#!/usr/bin/env python3
"""Run one authorized D5-A V0/V1 seed-0 head training and one-shot dev fold."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import random
import sys
from pathlib import Path, PureWindowsPath
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import torch
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.verify_mamba_v15_d5a_seed0_training_authorization import (  # noqa: E402
    verify_authorization,
)
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


VERSION = "mamba-v15-d5a-seed0-training-fold-v1"
AUTHORIZATION_VERSION = "mamba-v15-d5a-seed0-training-authorization-v1"
FOLDS = ("A", "B", "C", "D")
CANDIDATES = ("V0", "V1")
EXPECTED_ARRAYS = {
    "partial", "implant", "gt", "centroid", "scale", "reference_rim_mask"
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


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
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


def read_case_ids(path: Path) -> list[str]:
    values = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not values or len(values) != len(set(values)):
        raise RuntimeError(f"Invalid case-ID list: {path}")
    return values


def source_id(case_id: str) -> str:
    fields = case_id.split("__")
    if len(fields) != 3:
        raise RuntimeError(f"Invalid D5 case ID: {case_id}")
    return fields[1]


def parse_portable_path(raw: str, manifest_dir: Path) -> Path:
    text = str(raw)
    if not text or Path(text).is_absolute() or PureWindowsPath(text).is_absolute():
        raise RuntimeError(f"Non-portable point path: {raw}")
    return (manifest_dir / text.replace("\\", os.sep)).resolve()


def load_manifest(audit_dir: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with (audit_dir / "manifest_portable.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            case_id = str(row.get("case_id", ""))
            if not case_id or case_id in rows:
                raise RuntimeError("Portable manifest contains invalid case IDs")
            rows[case_id] = row
    if len(rows) != 400:
        raise RuntimeError("Portable manifest must contain 400 cases")
    return rows


def load_case(
    case_id: str, row: Mapping[str, Any], audit_dir: Path
) -> tuple[np.ndarray, np.ndarray]:
    point_path = parse_portable_path(str(row["point_path"]), audit_dir)
    if point_path.name != f"{case_id}.npz" or not point_path.is_file():
        raise RuntimeError(f"Missing D5 point asset: {point_path}")
    if sha256_file(point_path) != str(row["derived_case_sha256"]).lower():
        raise RuntimeError(f"D5 point hash mismatch: {case_id}")
    with np.load(point_path, allow_pickle=False) as sample:
        if set(sample.files) != EXPECTED_ARRAYS:
            raise RuntimeError(f"{case_id}: unexpected NPZ members")
        partial = sample["partial"].copy()
        labels = sample["reference_rim_mask"].copy()
    expected_positive = int(row["point_audit"]["reference_rim_points"])
    if not (
        partial.shape == (8192, 3)
        and partial.dtype == np.float32
        and np.isfinite(partial).all()
        and labels.shape == (8192,)
        and labels.dtype == np.bool_
        and int(labels.sum()) == expected_positive
        and 0 < expected_positive < 8192
    ):
        raise RuntimeError(f"{case_id}: NPZ or label contract failed")
    return partial, labels


def validate_binding(
    receipt: Mapping[str, Any], config: Mapping[str, Any], config_path: Path,
    candidate: str, fold: str,
) -> None:
    binding = receipt.get("folds", {}).get(f"{candidate}_{fold}", {})
    if not (
        receipt.get("authorization_version") == AUTHORIZATION_VERSION
        and receipt.get("D5A_seed0_training_authorized") is True
        and receipt.get("D5A_seed1_training_authorized") is False
        and receipt.get("D5B_training_authorized") is False
        and receipt.get("proposal_confirmation_access_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
        and binding.get("runtime_config", {}).get("sha256") == sha256_file(config_path)
        and config.get("status")
        == "D5A_seed0_candidate_fold_training_authorized_not_started"
        and config.get("candidate") == candidate
        and config.get("fold") == fold
        and config.get("seed") == 0
        and config.get("boundaries", {}).get("D5A_seed0_training_authorized") is True
        and config.get("boundaries", {}).get("D5A_seed1_training_authorized") is False
        and config.get("boundaries", {}).get("D5B_training_authorized") is False
        and config.get("boundaries", {}).get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("D5-A training authorization semantics are invalid")


def validate_data_bindings(
    config: Mapping[str, Any], fourfold: Path, audit: Path
) -> tuple[Path, Path]:
    verify_manifest(fourfold)
    verify_manifest(audit)
    data = config["data"]
    train_path = fourfold / data["train_case_ids_file"]
    dev_path = fourfold / data["dev_case_ids_file"]
    summary = json.loads(
        (audit / "generation_audit_summary.json").read_text(encoding="utf-8")
    )
    if not (
        sha256_file(train_path) == data["train_case_ids_sha256"]
        and sha256_file(dev_path) == data["dev_case_ids_sha256"]
        and sha256_file(audit / data["portable_manifest_file"])
        == summary["portable_manifest_sha256"]
    ):
        raise RuntimeError("D5-A runtime data binding drifted")
    return train_path, dev_path


def descriptor_for(candidate: str, partial: torch.Tensor) -> torch.Tensor:
    if candidate == "V0":
        return geometry_descriptor_13d(
            partial, knn=16, epsilon=1.0e-8, query_chunk_size=512
        )
    return geometry_descriptor_27d(
        partial, knn_small=16, knn_large=32, epsilon=1.0e-8,
        query_chunk_size=512,
    )


def build_descriptor_cache(
    candidate: str, case_ids: Sequence[str],
    manifest: Mapping[str, Mapping[str, Any]], audit_dir: Path,
    device: torch.device, label: str,
) -> tuple[torch.Tensor, torch.Tensor]:
    dimensions = 13 if candidate == "V0" else 27
    descriptors = torch.empty((len(case_ids), 8192, dimensions), dtype=torch.float32)
    labels = torch.empty((len(case_ids), 8192), dtype=torch.bool)
    with torch.inference_mode():
        for index, case_id in enumerate(tqdm(case_ids, desc=label, dynamic_ncols=True)):
            if case_id not in manifest:
                raise RuntimeError(f"Case absent from portable manifest: {case_id}")
            partial_np, labels_np = load_case(case_id, manifest[case_id], audit_dir)
            partial = torch.from_numpy(partial_np).unsqueeze(0).to(device)
            descriptor = descriptor_for(candidate, partial)
            descriptors[index].copy_(descriptor[0].cpu())
            labels[index].copy_(torch.from_numpy(labels_np))
    return descriptors, labels


def source_order_indices(case_ids: Sequence[str]) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = {}
    for index, case_id in enumerate(case_ids):
        grouped.setdefault(source_id(case_id), []).append(index)
    for source, indices in grouped.items():
        indices.sort(key=lambda value: case_ids[value])
        if len(indices) != 4:
            raise RuntimeError(f"Source {source} does not have four cases")
    if len(grouped) != 75:
        raise RuntimeError("Training fold must contain 75 sources")
    return dict(sorted(grouped.items()))


def make_head(candidate: str) -> torch.nn.Module:
    return D4AProposalHead() if candidate == "V0" else D5V1ContextHead()


def training_loss(candidate: str, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    if candidate == "V0":
        return case_balanced_binary_cross_entropy(logits, labels)
    return d5_v1_set_level_loss(logits, labels)["total"]


def rank_diagnostics(logits: torch.Tensor, labels: torch.Tensor) -> dict[str, int]:
    order = torch.argsort(logits, dim=1, descending=True, stable=True)
    ordered_positive = labels.gather(1, order)
    positions = torch.nonzero(ordered_positive[0], as_tuple=False).flatten()
    if positions.numel() == 0:
        raise RuntimeError("D5-A case has no positive candidate")
    best_rank = int(positions[0].item()) + 1
    return {
        "best_positive_rank": best_rank,
        **{
            f"recall_at_{count}": int(ordered_positive[0, :count].any().item())
            for count in (8, 16, 32, 64, 128, 256)
        },
    }


def verify_existing(output: Path, candidate: str, fold: str) -> bool:
    if not output.exists():
        return False
    verify_manifest(output)
    receipt = json.loads((output / "run_receipt.json").read_text(encoding="utf-8"))
    if not (
        receipt.get("run_version") == VERSION
        and receipt.get("candidate") == candidate
        and receipt.get("fold") == fold
        and receipt.get("status") in {"passed_fold_gate", "failed_fold_gate"}
        and receipt.get("optimizer_steps") == 1900
        and receipt.get("development_evaluation_count") == 1
        and receipt.get("D5A_seed1_training_authorized") is False
        and receipt.get("D5B_training_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError(f"Existing D5-A fold output is invalid: {output}")
    print(f"[locked] existing D5-A fold output is valid: {candidate}/fold{fold}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=CANDIDATES, required=True)
    parser.add_argument("--fold", choices=FOLDS, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    candidate, fold = args.candidate, args.fold
    config_path = args.config.resolve()
    auth_dir = args.authorization_dir.resolve()
    fourfold = args.fourfold_lock_dir.resolve()
    audit = args.generation_audit_dir.resolve()
    output = args.output_dir.resolve()
    if verify_existing(output, candidate, fold):
        return
    working = output.with_name(f".{output.name}.working")
    if output.exists() or working.exists():
        raise RuntimeError(f"D5-A fold output requires inspection: {output}")

    receipt = verify_authorization(config_path.parent, auth_dir)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_binding(receipt, config, config_path, candidate, fold)
    train_path, dev_path = validate_data_bindings(config, fourfold, audit)
    if not torch.cuda.is_available():
        raise RuntimeError("D5-A head-only training requires CUDA")
    device = torch.device("cuda:0")
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    manifest = load_manifest(audit)
    train_ids = read_case_ids(train_path)
    if len(train_ids) != 300:
        raise RuntimeError(f"{candidate}/fold{fold} requires 300 training cases")
    grouped = source_order_indices(train_ids)
    train_descriptors, train_labels = build_descriptor_cache(
        candidate, train_ids, manifest, audit, device,
        f"D5-A {candidate} fold{fold} train descriptors",
    )

    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    head = make_head(candidate).to(device).train()
    optimizer = torch.optim.AdamW(head.parameters(), lr=1.0e-3, weight_decay=1.0e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=50, eta_min=1.0e-5
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(0)
    sources = list(grouped)
    optimizer_steps = 0
    final_loss = float("nan")
    maximum_preclip_gradient_norm = 0.0
    progress = tqdm(
        range(1, 51), desc=f"D5-A {candidate} head fold{fold}", dynamic_ncols=True
    )
    for epoch in progress:
        source_permutation = torch.randperm(len(sources), generator=generator).tolist()
        order = [
            case_index
            for source_index in source_permutation
            for case_index in grouped[sources[source_index]]
        ]
        losses = []
        head.train()
        for start in range(0, 300, 8):
            indices = order[start : start + 8]
            features = train_descriptors[indices].to(device, non_blocking=True)
            labels = train_labels[indices].to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = head(features)
            loss = training_loss(candidate, logits, labels)
            if not torch.isfinite(loss):
                raise RuntimeError(f"{candidate}/fold{fold}: non-finite training loss")
            loss.backward()
            gradient_norm = torch.nn.utils.clip_grad_norm_(head.parameters(), max_norm=1.0)
            if not torch.isfinite(gradient_norm):
                raise RuntimeError(f"{candidate}/fold{fold}: non-finite gradient norm")
            maximum_preclip_gradient_norm = max(
                maximum_preclip_gradient_norm, float(gradient_norm.item())
            )
            optimizer.step()
            optimizer_steps += 1
            losses.append(float(loss.detach().item()))
        final_loss = sum(losses) / len(losses)
        scheduler.step()
        progress.set_postfix(epoch=epoch, loss=f"{final_loss:.6f}")
    if optimizer_steps != 1900:
        raise RuntimeError(f"{candidate}/fold{fold}: unexpected optimizer steps")

    working.mkdir(parents=True)
    checkpoint_path = working / "head_final_epoch.pth"
    architecture = "13-128-64-1" if candidate == "V0" else "27-64-64-context-219-128-64-1"
    torch.save(
        {
            "state_dict": {name: value.detach().cpu() for name, value in head.state_dict().items()},
            "candidate": candidate,
            "architecture": architecture,
            "fold": fold,
            "seed": 0,
            "epoch": 50,
            "optimizer_state_included": False,
            "D5A_seed1_authorized": False,
        },
        checkpoint_path,
    )

    # Dev IDs and NPZ assets remain unopened until all 1900 training steps finish.
    dev_ids = read_case_ids(dev_path)
    if len(dev_ids) != 100 or set(train_ids) & set(dev_ids):
        raise RuntimeError(f"{candidate}/fold{fold}: invalid one-shot dev partition")
    if len({source_id(value) for value in dev_ids}) != 25:
        raise RuntimeError(f"{candidate}/fold{fold}: dev must contain 25 sources")

    head.eval()
    rows = []
    with torch.inference_mode():
        for case_id in tqdm(
            dev_ids, desc=f"D5-A {candidate} fold{fold} one-shot dev",
            dynamic_ncols=True,
        ):
            partial_np, labels_np = load_case(case_id, manifest[case_id], audit)
            partial = torch.from_numpy(partial_np).unsqueeze(0).to(device)
            labels = torch.from_numpy(labels_np).unsqueeze(0).to(device)
            descriptors = descriptor_for(candidate, partial)
            logits = head(descriptors)
            selected = (
                select_top8_conditioned_fps24(logits, partial)
                if candidate == "V0"
                else select_deterministic_top32(logits)
            )
            selected_positive = int(labels[0, selected[0]].sum().item())
            logit_min, logit_max = float(logits.amin().item()), float(logits.amax().item())
            if not all(math.isfinite(value) for value in (logit_min, logit_max)):
                raise RuntimeError(f"{candidate}/fold{fold}: non-finite dev logits")
            rows.append(
                {
                    "case_id": case_id,
                    "source_skull_id": source_id(case_id),
                    "defect_type": case_id.split("__")[2],
                    "candidate": candidate,
                    "fold": fold,
                    "positive_candidate_count": int(labels.sum().item()),
                    "selected_positive_count": selected_positive,
                    "selected_hit": int(selected_positive > 0),
                    **rank_diagnostics(logits, labels),
                    "logit_min": logit_min,
                    "logit_max": logit_max,
                }
            )

    hits = sum(int(row["selected_hit"]) for row in rows)
    all_finite = all(
        math.isfinite(float(row[key]))
        for row in rows for key in ("logit_min", "logit_max")
    )
    fold_passed = len(rows) == 100 and hits == 100 and all_finite
    summary = {
        "summary_version": VERSION,
        "status": "passed_fold_gate" if fold_passed else "failed_fold_gate",
        "candidate": candidate,
        "eligibility_candidate": candidate == "V1",
        "fold": fold,
        "seed": 0,
        "train_sources": 75,
        "train_cases": 300,
        "development_sources": 25,
        "development_cases": 100,
        "epochs": 50,
        "optimizer_steps": optimizer_steps,
        "final_training_loss": final_loss,
        "final_learning_rate": float(optimizer.param_groups[0]["lr"]),
        "maximum_preclip_gradient_norm": maximum_preclip_gradient_norm,
        "parameter_count": sum(value.numel() for value in head.parameters()),
        "case_hits": hits,
        "case_hit_rate": hits / 100.0,
        "all_required_outputs_finite": all_finite,
        "fold_gate_passed": fold_passed,
        "development_evaluation_count": 1,
        "checkpoint_policy": "final_epoch_only",
        "intermediate_checkpoint_count": 0,
        "D5A_seed1_training_authorized": False,
        "proposal_confirmation_accessed": False,
        "D5B_training_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "selection_started": False,
    }
    metrics_payload = csv_bytes(list(rows[0]), rows)
    summary_payload = canonical_json(summary)
    metrics_path = working / "development_per_case.csv"
    summary_path = working / "fold_summary.json"
    metrics_path.write_bytes(metrics_payload)
    summary_path.write_bytes(summary_payload)
    receipt_payload = canonical_json(
        {
            "run_version": VERSION,
            "status": summary["status"],
            "candidate": candidate,
            "fold": fold,
            "seed": 0,
            "runtime_config_sha256": sha256_file(config_path),
            "authorization_receipt_sha256": sha256_file(
                auth_dir / "d5a_seed0_training_authorization_receipt.json"
            ),
            "artifacts": {
                "head_final_epoch": {"name": checkpoint_path.name, "sha256": sha256_file(checkpoint_path)},
                "development_per_case": {"name": metrics_path.name, "sha256": sha256_file(metrics_path)},
                "fold_summary": {"name": summary_path.name, "sha256": sha256_file(summary_path)},
            },
            "optimizer_steps": optimizer_steps,
            "development_evaluation_count": 1,
            "checkpoint_count": 1,
            "only_head_trainable": True,
            "D5A_seed1_training_authorized": False,
            "proposal_confirmation_accessed": False,
            "D5B_training_authorized": False,
            "D5_candidate_selection_authorized": False,
            "protected_or_sealed_data_accessed": False,
            "selection_started": False,
        }
    )
    receipt_path = working / "run_receipt.json"
    receipt_path.write_bytes(receipt_payload)
    artifacts = {
        path.name: path.read_bytes()
        for path in (checkpoint_path, metrics_path, summary_path, receipt_path)
    }
    (working / "files.sha256").write_bytes(
        "".join(
            f"{sha256_bytes(payload)}  {name}\n"
            for name, payload in sorted(artifacts.items())
        ).encode("ascii")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(working, output)
    print(f"[saved] immutable D5-A fold result: {output}")
    print(f"[gate] candidate={candidate} fold={fold} hits={hits}/100 passed={fold_passed}")
    print("[locked] seed1=false confirmation=false D5B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
