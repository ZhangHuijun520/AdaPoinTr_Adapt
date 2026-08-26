#!/usr/bin/env python3
"""Measure the preregistered S1 auxiliary/reconstruction gradient ratio."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import pickle
import random
import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils import misc  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.mamba_d3_contact import dense_contact_safety_loss  # noqa: E402


VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-fold-v1"
AUTH_VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-authorization-v1"
HOTFIX_VERSION = "mamba-v13-d3-s1-calibration-tensor-hash-hotfix1-v1"
FOLDS = ("A", "B", "C", "D")
BATCHES = 8
BATCH_SIZE = 8
TARGET_RATIO = 0.075


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def verify_tree(root: Path) -> None:
    manifest = root / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, raw_name = line.split(maxsplit=1)
        path = root / raw_name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen S1 authorization mismatch: {path}")


def resolve(path: str | Path) -> Path:
    result = Path(path)
    if not result.is_absolute():
        result = REPO_ROOT / result
    return result.resolve()


def tensor_hash(items) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(items, key=lambda item: item[0]):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(value.dtype).encode("ascii") + b"\0")
        digest.update(str(tuple(value.shape)).encode("ascii") + b"\0")
        digest.update(value.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def capture_rng_state() -> dict:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state().clone(),
        "torch_cuda": [state.clone() for state in torch.cuda.get_rng_state_all()],
    }


def restore_rng_state(state: dict) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"])
    torch.cuda.set_rng_state_all(state["torch_cuda"])


def rng_fingerprint(state: dict) -> str:
    payload = {
        "python": state["python"],
        "numpy_name": state["numpy"][0],
        "numpy_keys": state["numpy"][1].tolist(),
        "numpy_position": int(state["numpy"][2]),
        "numpy_has_gauss": int(state["numpy"][3]),
        "numpy_cached_gaussian": float(state["numpy"][4]),
        "torch_cpu": state["torch_cpu"].tolist(),
        "torch_cuda": [value.tolist() for value in state["torch_cuda"]],
    }
    return sha256_bytes(pickle.dumps(payload, protocol=4))


def rng_states_equal(left: dict, right: dict) -> bool:
    numpy_equal = (
        left["numpy"][0] == right["numpy"][0]
        and np.array_equal(left["numpy"][1], right["numpy"][1])
        and left["numpy"][2:] == right["numpy"][2:]
    )
    return (
        left["python"] == right["python"]
        and numpy_equal
        and torch.equal(left["torch_cpu"], right["torch_cpu"])
        and len(left["torch_cuda"]) == len(right["torch_cuda"])
        and all(
            torch.equal(a, b)
            for a, b in zip(left["torch_cuda"], right["torch_cuda"])
        )
    )


def global_gradient_l2(loss, parameters, retain_graph=False) -> float:
    gradients = torch.autograd.grad(
        loss,
        parameters,
        retain_graph=retain_graph,
        create_graph=False,
        allow_unused=True,
    )
    squared = loss.new_zeros((), dtype=torch.float64)
    for gradient in gradients:
        if gradient is not None:
            squared = squared + gradient.detach().double().square().sum()
    result = float(torch.sqrt(squared).cpu())
    del gradients
    return result


def csv_bytes(rows: list[dict]) -> bytes:
    fields = (
        "batch_index",
        "case_ids",
        "case_ids_sha256",
        "reconstruction_loss",
        "auxiliary_loss",
        "reconstruction_gradient_l2",
        "auxiliary_gradient_l2",
        "raw_ratio",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def verify_existing(output: Path, fold: str) -> bool:
    receipt_path = output / "calibration_receipt.json"
    manifest = output / "files.sha256"
    if not receipt_path.is_file() or not manifest.is_file():
        return False
    verify_tree(output)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        receipt.get("calibration_version") == VERSION
        and receipt.get("status") == "S1_fold_calibration_frozen"
        and receipt.get("fold") == fold
        and receipt.get("batch_count") == BATCHES
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_state_restored") is True
        and receipt.get("rng_state_restored") is True
        and receipt.get("holdout_accessed") is False
        and receipt.get("selection_started") is False
    ):
        raise RuntimeError(f"Existing S1 fold {fold} receipt semantics are invalid")
    print(f"[locked] existing S1 fold {fold} calibration is valid: {output}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold", choices=FOLDS, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--hotfix_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--num_workers", type=int, default=4)
    args = parser.parse_args()

    fold = args.fold
    authorization_dir = args.authorization_dir.resolve()
    hotfix_dir = args.hotfix_dir.resolve()
    output = args.output_dir.resolve()
    verify_tree(authorization_dir)
    authorization_path = authorization_dir / "s1_calibration_authorization_receipt.json"
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    bound_runner = authorization.get("bound_code", {}).get(
        "tools/run_mamba_v13_d3_s1_calibration_fold.py"
    )
    if not (
        authorization.get("authorization_version") == AUTH_VERSION
        and authorization.get("status")
        == "S1_training_only_gradient_ratio_calibration_authorized"
        and authorization.get("S1_calibration_authorized") is True
        and authorization.get("S1_training_authorized") is False
        and authorization.get("S2_calibration_authorized") is False
        and authorization.get("S2_full_training_authorized") is False
        and authorization.get("holdout_authorized") is False
        and authorization.get("selection_started") is False
        and authorization.get("batches_per_fold") == BATCHES
        and authorization.get("batch_size") == BATCH_SIZE
        and authorization.get("target_gradient_ratio") == TARGET_RATIO
        and isinstance(bound_runner, str)
        and len(bound_runner) == 64
    ):
        raise RuntimeError("S1 calibration authorization semantics are invalid")

    verify_tree(hotfix_dir)
    hotfix_path = hotfix_dir / "hotfix_receipt.json"
    hotfix = json.loads(hotfix_path.read_text(encoding="utf-8"))
    if not (
        hotfix.get("hotfix_version") == HOTFIX_VERSION
        and hotfix.get("status") == "pre_batch_scalar_tensor_hash_repair_authorized"
        and hotfix.get("base_authorization", {}).get("sha256")
        == sha256_file(authorization_path)
        and hotfix.get("base_authorized_runner_sha256") == bound_runner
        and hotfix.get("repaired_runner", {}).get("sha256")
        == sha256_file(Path(__file__).resolve())
        and hotfix.get("failure_stage") == "before_data_iterator_creation"
        and hotfix.get("calibration_batches_consumed_before_failure") == 0
        and hotfix.get("gradients_computed_before_failure") == 0
        and hotfix.get("fold_receipts_written_before_failure") == 0
        and hotfix.get("scientific_protocol_changed") is False
        and hotfix.get("S1_calibration_authorized") is True
        and hotfix.get("S1_training_authorized") is False
        and hotfix.get("S2_calibration_authorized") is False
        and hotfix.get("S2_full_training_authorized") is False
        and hotfix.get("holdout_authorized") is False
        and hotfix.get("selection_started") is False
    ):
        raise RuntimeError("S1 calibration tensor-hash hotfix is invalid")
    if verify_existing(output, fold):
        return
    if output.exists():
        raise RuntimeError(f"Refusing incomplete S1 calibration directory: {output}")
    if not torch.cuda.is_available():
        raise RuntimeError("S1 gradient-ratio calibration requires CUDA")

    fold_lock = authorization["folds"][fold]
    template = Path(fold_lock["template"]["path"]).resolve()
    train_ids_path = resolve(fold_lock["train_case_ids"]["path"])
    if (
        sha256_file(template) != fold_lock["template"]["sha256"]
        or sha256_file(train_ids_path) != fold_lock["train_case_ids"]["sha256"]
    ):
        raise RuntimeError(f"Fold {fold} frozen input mismatch")

    external_rng = capture_rng_state()
    model = None
    buffer_snapshot = None
    try:
        misc.set_random_seed(0, deterministic=True)
        config = cfg_from_yaml_file(str(template))
        if not (
            config.d3_execution.candidate == "S1"
            and config.d3_execution.fold == fold
            and config.d3_execution.training_authorized is False
            and config.d3_execution.holdout_authorized is False
            and config.dataset.train.others.subset == "train"
            and config.dataset.train.others.manifest_split == "development"
            and config.dataset.train.others.GT_RIM_KEY == "reference_rim_mask"
        ):
            raise RuntimeError(f"Fold {fold} S1 template semantics changed")
        contact = config.model.dense_contact_objective
        if not (
            contact.enabled is True
            and float(contact.weight) == 1.0
            and float(contact.threshold_mm) == 2.0
            and float(contact.temperature_mm) == 0.25
            and float(contact.tail_fraction) == 0.1
        ):
            raise RuntimeError("S1 auxiliary objective differs from preregistration")

        config.dataset.train.others.bs = BATCH_SIZE
        dataset = build_dataset_from_cfg(
            config.dataset.train._base_, config.dataset.train.others
        )
        if len(dataset) != 300:
            raise RuntimeError(f"Fold {fold}: expected exactly 300 training cases")
        dataset_ids = [str(dataset.get_record(index)["case_id"]) for index in range(len(dataset))]
        frozen_ids = [line.strip() for line in train_ids_path.read_text().splitlines() if line.strip()]
        if set(dataset_ids) != set(frozen_ids) or len(dataset_ids) != len(set(dataset_ids)):
            raise RuntimeError(f"Fold {fold}: dataset differs from frozen train case set")
        loader = DataLoader(
            dataset,
            batch_size=BATCH_SIZE,
            shuffle=True,
            drop_last=True,
            num_workers=int(args.num_workers),
            worker_init_fn=builder.worker_init_fn,
            pin_memory=True,
        )

        model = builder.model_builder(config.model).cuda()
        # Build the exact S1 template, then disable only its scalar loss addition
        # so the first gradient measurement is reconstruction-only.
        if not model.dense_contact_enabled or model.dense_contact_weight != 1.0:
            raise RuntimeError("Constructed model does not match the frozen S1 objective")
        model.dense_contact_enabled = False
        model.dense_contact_weight = 0.0
        model.train()
        if hasattr(model, "set_mamba_adapter_scale"):
            model.set_mamba_adapter_scale(0.0)
        parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
        if not parameters:
            raise RuntimeError("S1 model has no trainable parameters")

        state_before = tensor_hash(model.state_dict().items())
        buffer_snapshot = {
            name: buffer.detach().cpu().clone()
            for name, buffer in model.named_buffers()
        }
        measurement_rng = capture_rng_state()
        measurement_rng_sha = rng_fingerprint(measurement_rng)

        rows = []
        all_case_ids = []
        iterator = iter(loader)
        for batch_index in tqdm(
            range(BATCHES),
            desc=f"S1 gradient calibration fold{fold}",
            dynamic_ncols=True,
        ):
            _, case_ids, data = next(iterator)
            case_ids = [str(value) for value in case_ids]
            if len(case_ids) != BATCH_SIZE:
                raise RuntimeError("Calibration encountered a non-full batch")
            partial = data[0].cuda(non_blocking=True)
            gt = data[1].cuda(non_blocking=True)
            scales = dataset.get_normalization_scales(
                case_ids, device=partial.device, dtype=partial.dtype
            )
            masks = dataset.get_gt_rim_masks(case_ids, device=partial.device)
            prediction = model(partial)
            sparse, reconstruction = model.get_loss(prediction, gt, epoch=0)
            reconstruction_loss = sparse + reconstruction
            auxiliary = dense_contact_safety_loss(
                prediction[3],
                partial,
                scales,
                masks,
                threshold_mm=2.0,
                temperature_mm=0.25,
                tail_fraction=0.1,
            ).loss
            reconstruction_norm = global_gradient_l2(
                reconstruction_loss, parameters, retain_graph=True
            )
            auxiliary_norm = global_gradient_l2(auxiliary, parameters)
            ratio = auxiliary_norm / max(reconstruction_norm, 1.0e-12)
            values = (
                float(reconstruction_loss.detach().cpu()),
                float(auxiliary.detach().cpu()),
                reconstruction_norm,
                auxiliary_norm,
                ratio,
            )
            if not all(math.isfinite(value) and value > 0 for value in values):
                raise RuntimeError(
                    f"Fold {fold} batch {batch_index}: nonfinite/zero calibration value"
                )
            case_payload = "".join(f"{case_id}\n" for case_id in case_ids).encode()
            rows.append({
                "batch_index": batch_index,
                "case_ids": "|".join(case_ids),
                "case_ids_sha256": sha256_bytes(case_payload),
                "reconstruction_loss": format(values[0], ".17g"),
                "auxiliary_loss": format(values[1], ".17g"),
                "reconstruction_gradient_l2": format(reconstruction_norm, ".17g"),
                "auxiliary_gradient_l2": format(auxiliary_norm, ".17g"),
                "raw_ratio": format(ratio, ".17g"),
            })
            all_case_ids.extend(case_ids)
            del prediction, sparse, reconstruction, reconstruction_loss, auxiliary
        del iterator

        ratios = np.asarray([float(row["raw_ratio"]) for row in rows], dtype=np.float64)
        fold_ratio = float(np.median(ratios))
        calibrated_weight = TARGET_RATIO / fold_ratio
        if not (
            math.isfinite(fold_ratio) and fold_ratio > 0
            and math.isfinite(calibrated_weight) and calibrated_weight > 0
        ):
            raise RuntimeError(f"Fold {fold}: invalid calibrated weight")

        with torch.no_grad():
            for name, buffer in model.named_buffers():
                buffer.copy_(buffer_snapshot[name].to(device=buffer.device, dtype=buffer.dtype))
        state_after = tensor_hash(model.state_dict().items())
        model_state_restored = state_after == state_before
        restore_rng_state(measurement_rng)
        restored_measurement_rng = capture_rng_state()
        rng_state_restored = rng_states_equal(measurement_rng, restored_measurement_rng)
        if not model_state_restored or not rng_state_restored:
            raise RuntimeError("Model or RNG state was not restored after calibration")

        case_list = "".join(f"{case_id}\n" for case_id in all_case_ids).encode("utf-8")
        metrics = csv_bytes(rows)
        receipt = {
            "calibration_version": VERSION,
            "status": "S1_fold_calibration_frozen",
            "candidate": "S1",
            "fold": fold,
            "seed": 0,
            "authorization_receipt": {
                "path": portable(authorization_path),
                "sha256": sha256_file(authorization_path),
            },
            "tensor_hash_hotfix_receipt": {
                "path": portable(hotfix_path),
                "sha256": sha256_file(hotfix_path),
            },
            "template": {"path": str(template), "sha256": sha256_file(template)},
            "training_case_universe": {
                "path": portable(train_ids_path),
                "sha256": sha256_file(train_ids_path),
                "count": 300,
            },
            "batch_count": BATCHES,
            "batch_size": BATCH_SIZE,
            "measured_case_slots": len(all_case_ids),
            "measured_unique_cases": len(set(all_case_ids)),
            "batch_case_ids_sha256": sha256_bytes(case_list),
            "batch_metrics_sha256": sha256_bytes(metrics),
            "raw_ratios": [float(value) for value in ratios],
            "fold_raw_ratio_median": fold_ratio,
            "target_gradient_ratio": TARGET_RATIO,
            "calibrated_weight": calibrated_weight,
            "weight_clipped_or_adjusted": False,
            "optimizer_constructed": False,
            "optimizer_steps": 0,
            "checkpoint_loaded": False,
            "checkpoint_written": False,
            "exact_s1_template_constructed": True,
            "auxiliary_temporarily_disabled_for_reconstruction_measurement": True,
            "mamba_adapter_alpha_scale": 0.0,
            "model_state_sha256_before": state_before,
            "model_state_sha256_after_restore": state_after,
            "model_state_restored": model_state_restored,
            "measurement_rng_sha256": measurement_rng_sha,
            "rng_state_restored": rng_state_restored,
            "development_loader_constructed": False,
            "development_metrics_consumed": False,
            "holdout_accessed": False,
            "S1_training_authorized": False,
            "S2_calibration_authorized": False,
            "S2_full_training_authorized": False,
            "selection_started": False,
        }
        files = {
            "batch_case_ids.txt": case_list,
            "batch_gradient_metrics.csv": metrics,
            "calibration_receipt.json": canonical_json(receipt),
        }
        files["files.sha256"] = "".join(
            f"{sha256_bytes(payload)}  {name}\n"
            for name, payload in sorted(files.items())
        ).encode("ascii")
        output.parent.mkdir(parents=True, exist_ok=True)
        working = output.parent / f".{output.name}.working"
        if working.exists():
            raise RuntimeError(f"Stale S1 calibration working directory: {working}")
        working.mkdir(parents=True)
        for name, payload in files.items():
            (working / name).write_bytes(payload)
        working.rename(output)
        print(f"[saved] S1 fold {fold} calibration: {output}")
        print(f"[weight] raw_median={fold_ratio:.10g} calibrated={calibrated_weight:.10g}")
        print("[locked] optimizer_steps=0 dev=false holdout=false training=false")
    finally:
        if buffer_snapshot is not None and model is not None:
            with torch.no_grad():
                for name, buffer in model.named_buffers():
                    buffer.copy_(
                        buffer_snapshot[name].to(device=buffer.device, dtype=buffer.dtype)
                    )
        restore_rng_state(external_rng)


if __name__ == "__main__":
    main()
