#!/usr/bin/env python3
"""Run the immutable same-fold calibrated weighted-loss zero-step."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.mamba_d5a_proposal import geometry_descriptor_27d
from utils.mamba_d6a_slot_allocator import D6R1SlotAllocator, d6a_raw_losses


FOLDS = ("A", "B", "C", "D")
COMPONENTS = ("point", "support", "shape")
GROUP_NAMES = (
    "shared_point_encoder",
    "point_calibration_branch",
    "slot_attention_and_pointer",
)
VERSION = "mamba-v16-d6a-calibrated-weighted-real-train-zero-step-v1"
PROTOCOL = ROOT / "docs/mamba_v16_d6a_calibrated_weighted_zero_step_protocol_v1.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_manifest(root: Path) -> None:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")


def state_hash(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def parameter_groups(model: D6R1SlotAllocator) -> dict[str, list[torch.Tensor]]:
    point = list(model.point_encoder.parameters())
    calibration = list(model.point_calibration.parameters())
    used = {id(value) for value in point + calibration}
    slot = [value for value in model.parameters() if id(value) not in used]
    return {
        "shared_point_encoder": point,
        "point_calibration_branch": calibration,
        "slot_attention_and_pointer": slot,
    }


def gradient_norm(values: Iterable[torch.Tensor | None]) -> float:
    total = torch.zeros((), dtype=torch.float64)
    for value in values:
        if value is not None:
            total += value.detach().double().square().sum().cpu()
    result = float(torch.sqrt(total).item())
    if not np.isfinite(result):
        raise RuntimeError("Non-finite gradient norm")
    return result


def gradient_cosine(
    left: Iterable[torch.Tensor | None], right: Iterable[torch.Tensor | None]
) -> float | None:
    dot = torch.zeros((), dtype=torch.float64)
    left_sq = torch.zeros((), dtype=torch.float64)
    right_sq = torch.zeros((), dtype=torch.float64)
    for lhs, rhs in zip(left, right):
        if lhs is not None:
            left_sq += lhs.detach().double().square().sum().cpu()
        if rhs is not None:
            right_sq += rhs.detach().double().square().sum().cpu()
        if lhs is not None and rhs is not None:
            dot += (lhs.detach().double() * rhs.detach().double()).sum().cpu()
    if left_sq.item() == 0.0 or right_sq.item() == 0.0:
        return None
    result = float((dot / torch.sqrt(left_sq * right_sq)).item())
    if not np.isfinite(result) or result < -1.000001 or result > 1.000001:
        raise RuntimeError("Invalid gradient cosine")
    return max(-1.0, min(1.0, result))


def load_manifest(audit: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    for line in (audit / "manifest_portable.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        rows[row["case_id"]] = row
    if len(rows) != 400:
        raise RuntimeError("Generation audit must bind exactly 400 cases")
    return rows


def load_case(case_id: str, row: dict[str, Any], audit: Path) -> tuple[np.ndarray, np.ndarray]:
    path = (audit / row["point_path"]).resolve()
    if not path.is_file() or sha256_file(path) != row["derived_case_sha256"]:
        raise RuntimeError(f"Case hash mismatch: {case_id}")
    with np.load(path, allow_pickle=False) as sample:
        partial = sample["partial"].copy()
        mask = sample["reference_rim_mask"].copy()
    if not (
        partial.shape == (8192, 3)
        and partial.dtype == np.float32
        and np.isfinite(partial).all()
        and mask.shape == (8192,)
        and mask.dtype == np.bool_
        and 0 < int(mask.sum()) < 8192
    ):
        raise RuntimeError(f"NPZ contract failed: {case_id}")
    return partial, mask


def first_frozen_batch(fold_root: Path) -> list[str]:
    with (fold_root / "gradient_norms.csv").open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    cases = row["case_ids"].split("|")
    if len(cases) != 8 or len(set(cases)) != 8:
        raise RuntimeError("Frozen first calibration batch must contain eight unique cases")
    return cases


def write_exact(output: Path, files: dict[str, bytes]) -> None:
    if output.exists():
        verify_manifest(output)
        receipt = json.loads((output / "weighted_zero_step_receipt.json").read_text(encoding="utf-8"))
        if receipt.get("run_version") != VERSION:
            raise RuntimeError(f"Existing output is not reusable: {output}")
        print(f"[locked] existing weighted zero-step is valid: {output}")
        return
    working = output.with_name(f".{output.name}.working")
    if working.exists():
        raise RuntimeError(f"Working directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    manifest = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    (working / "files.sha256").write_bytes(manifest)
    working.rename(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fourfold_lock_dir", type=Path, required=True)
    parser.add_argument("--generation_audit_dir", type=Path, required=True)
    parser.add_argument("--calibration_lock_dir", type=Path, required=True)
    parser.add_argument("--calibration_fold_root", type=Path, required=True)
    parser.add_argument("--calibration_completion_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    output = args.output_dir.resolve()
    if output.exists():
        write_exact(output, {})
        return
    fourfold = args.fourfold_lock_dir.resolve()
    audit = args.generation_audit_dir.resolve()
    calibration_lock = args.calibration_lock_dir.resolve()
    completion = args.calibration_completion_dir.resolve()
    for root in (fourfold, audit, calibration_lock, completion):
        verify_manifest(root)
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if not (
        protocol.get("protocol_id") == "mamba-v16-d6a-calibrated-weighted-real-train-zero-step-v1"
        and protocol.get("candidate") == "R1"
        and protocol.get("seed") == 0
        and protocol.get("folds") == list(FOLDS)
        and protocol.get("loss", {}).get("weight_binding") == "same_fold_only"
        and protocol.get("hard_gates", {}).get("optimizer_steps") == 0
        and protocol.get("permissions_after_pass", {}).get("D6A_seed0_training_authorized") is False
    ):
        raise RuntimeError("Weighted zero-step protocol boundary failed")
    completion_receipt = json.loads(
        (completion / "calibration_completion_receipt.json").read_text(encoding="utf-8")
    )
    if not (
        completion_receipt.get("status") == "D6A_R1_gradient_calibration_folds_A_D_complete"
        and completion_receipt.get("optimizer_steps") == 0
        and completion_receipt.get("model_updates") == 0
        and completion_receipt.get("seed0_training_authorized") is False
        and completion_receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Calibration completion boundary failed")
    if not torch.cuda.is_available():
        raise RuntimeError("Weighted zero-step requires CUDA")
    device = torch.device("cuda:0")
    manifest = load_manifest(audit)

    python_rng_before = random.getstate()
    numpy_rng_before = np.random.get_state()
    cpu_rng_before = torch.get_rng_state().clone()
    cuda_rng_before = torch.cuda.get_rng_state_all()
    rows: list[dict[str, Any]] = []
    state_unchanged = True
    for fold in FOLDS:
        fold_root = args.calibration_fold_root.resolve() / f"fold{fold}_seed0"
        verify_manifest(fold_root)
        fold_receipt = json.loads(
            (fold_root / "calibration_fold_receipt.json").read_text(encoding="utf-8")
        )
        weights = completion_receipt["fold_weights"][fold]
        if not (
            fold_receipt.get("fold") == fold
            and fold_receipt.get("lambda_support") == weights["lambda_support"]
            and fold_receipt.get("lambda_shape") == weights["lambda_shape"]
        ):
            raise RuntimeError(f"Fold weight lineage failed: {fold}")
        case_ids = first_frozen_batch(fold_root)
        train_ids = {
            line.strip()
            for line in (fourfold / f"fold{fold}_train_case_ids.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        if len(train_ids) != 300 or any(case not in train_ids for case in case_ids):
            raise RuntimeError(f"Fold {fold} zero-step input is not train-only")

        random.seed(0)
        np.random.seed(0)
        torch.manual_seed(0)
        torch.cuda.manual_seed_all(0)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        model = D6R1SlotAllocator().to(device).train()
        before = state_hash(model)
        groups = parameter_groups(model)
        all_parameters = [value for name in GROUP_NAMES for value in groups[name]]
        slices: dict[str, slice] = {}
        start = 0
        for name in GROUP_NAMES:
            slices[name] = slice(start, start + len(groups[name]))
            start += len(groups[name])

        partials, masks = zip(*(load_case(case, manifest[case], audit) for case in case_ids))
        partial = torch.from_numpy(np.stack(partials)).to(device)
        positive = torch.from_numpy(np.stack(masks)).to(device)
        with torch.no_grad():
            descriptors = geometry_descriptor_27d(
                partial, knn_small=16, knn_large=32, epsilon=1.0e-8, query_chunk_size=512
            )
        outputs = model(descriptors)
        losses = d6a_raw_losses(outputs, positive)
        selected = losses["selected_indices"]
        if selected.shape != (8, 32) or any(torch.unique(row).numel() != 32 for row in selected):
            raise RuntimeError(f"Fold {fold} assignment uniqueness failed")
        weighted = {
            "point": losses["L_point"],
            "support": float(weights["lambda_support"]) * losses["L_support"],
            "shape": float(weights["lambda_shape"]) * losses["L_shape"],
        }
        total_loss = sum(weighted.values())
        targets = [outputs["point_features"], *all_parameters]
        gradients: dict[str, tuple[torch.Tensor | None, ...]] = {}
        for name in COMPONENTS:
            gradients[name] = torch.autograd.grad(
                weighted[name], targets, retain_graph=True, allow_unused=True
            )
        gradients["total"] = torch.autograd.grad(
            total_loss, targets, retain_graph=False, allow_unused=True
        )
        if gradients["total"][0] is None or gradient_norm([gradients["total"][0]]) <= 0.0:
            raise RuntimeError(f"Fold {fold} weighted total common-F gradient is zero")

        row: dict[str, Any] = {
            "fold": fold,
            "case_ids": "|".join(case_ids),
            "lambda_support": weights["lambda_support"],
            "lambda_shape": weights["lambda_shape"],
            "L_point_raw": float(losses["L_point"].detach().cpu()),
            "L_support_raw": float(losses["L_support"].detach().cpu()),
            "L_shape_raw": float(losses["L_shape"].detach().cpu()),
            "L_point_weighted": float(weighted["point"].detach().cpu()),
            "L_support_weighted": float(weighted["support"].detach().cpu()),
            "L_shape_weighted": float(weighted["shape"].detach().cpu()),
            "L_total": float(total_loss.detach().cpu()),
        }
        for object_name, object_slice in (
            ("common_F", slice(0, 1)),
            *[(name, slice(1 + slices[name].start, 1 + slices[name].stop)) for name in GROUP_NAMES],
        ):
            total_grad = gradients["total"][object_slice]
            row[f"{object_name}_total_norm"] = gradient_norm(total_grad)
            if row[f"{object_name}_total_norm"] <= 0.0:
                raise RuntimeError(f"Fold {fold} {object_name} total gradient is zero")
            for name in COMPONENTS:
                component_grad = gradients[name][object_slice]
                row[f"{object_name}_{name}_norm"] = gradient_norm(component_grad)
                cosine = gradient_cosine(total_grad, component_grad)
                row[f"{object_name}_total_vs_{name}_cosine"] = "" if cosine is None else cosine
        if not all(
            np.isfinite(float(value))
            for key, value in row.items()
            if key not in {"fold", "case_ids"} and value != ""
        ):
            raise RuntimeError(f"Fold {fold} emitted non-finite diagnostics")
        state_unchanged &= before == state_hash(model)
        rows.append(row)
        del model, outputs, losses, gradients, descriptors, partial, positive
        torch.cuda.empty_cache()

    random.setstate(python_rng_before)
    np.random.set_state(numpy_rng_before)
    torch.set_rng_state(cpu_rng_before)
    torch.cuda.set_rng_state_all(cuda_rng_before)
    numpy_rng_after = np.random.get_state()
    rng_restored = (
        random.getstate() == python_rng_before
        and numpy_rng_after[0] == numpy_rng_before[0]
        and np.array_equal(numpy_rng_after[1], numpy_rng_before[1])
        and numpy_rng_after[2:] == numpy_rng_before[2:]
        and torch.equal(torch.get_rng_state(), cpu_rng_before)
        and all(
            torch.equal(left, right)
            for left, right in zip(torch.cuda.get_rng_state_all(), cuda_rng_before)
        )
    )
    if not state_unchanged or not rng_restored:
        raise RuntimeError("Zero-step changed model or RNG state")

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    receipt = {
        "run_version": VERSION,
        "status": "D6A_R1_calibrated_weighted_real_train_zero_step_passed",
        "candidate": "R1",
        "seed": 0,
        "folds": 4,
        "cases_per_fold": 8,
        "total_case_slots": 32,
        "forward_passes": 4,
        "gradient_queries": 16,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "checkpoint_written": False,
        "model_state_unchanged": state_unchanged,
        "random_state_restored": rng_restored,
        "development_dev_cases_accessed": 0,
        "D6A_seed0_training_authorized": False,
        "D6A_seed1_training_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "protected_or_sealed_data_accessed": False,
        "cosines_observation_only": True,
        "lineage_sha256": {
            "weighted_zero_step_protocol": sha256_file(PROTOCOL),
            "fourfold_lock_manifest": sha256_file(fourfold / "files.sha256"),
            "generation_audit_manifest": sha256_file(audit / "files.sha256"),
            "calibration_lock_manifest": sha256_file(calibration_lock / "files.sha256"),
            "calibration_completion_manifest": sha256_file(completion / "files.sha256"),
            "calibration_completion_receipt": sha256_file(
                completion / "calibration_completion_receipt.json"
            ),
        },
        "next_step": "freeze_and_review_before_separate_D6A_seed0_training_protocol",
    }
    report = (
        "# Mamba v1.6 D6-A calibrated weighted zero-step\n\n"
        "> 四折各一个冻结 train-only batch；不训练、不访问 dev 或 sealed 数据。\n\n"
        "- folds：4。\n- cases per fold：8。\n- optimizer steps：0。\n"
        "- model updates：0。\n- gradient cosines：observation-only。\n"
        "- D6-A seed-0 training authorized：`False`。\n"
        "- 下一步：冻结并人工审阅结果，再单独预注册训练协议。\n"
    ).encode("utf-8")
    files = {
        "weighted_zero_step_metrics.csv": stream.getvalue().encode("utf-8"),
        "weighted_zero_step_receipt.json": canonical_json(receipt),
        "weighted_zero_step_report_zh.md": report,
    }
    write_exact(output, files)
    print(f"[saved] immutable calibrated weighted zero-step: {output}")
    print("[done] folds=4 case_slots=32 optimizer_steps=0 model_updates=0")
    print("[locked] training=false seed1=false D6B=false selection=false sealed=false")


if __name__ == "__main__":
    main()
