#!/usr/bin/env python
"""Frozen train-fold-only SCQR auxiliary gradient-ratio calibration."""

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch

from datasets import build_dataset_from_cfg
from models import build_model_from_cfg
from models.cranial_scqr import (
    build_contact_support_labels,
    case_balanced_binary_cross_entropy,
)
from tools.run_cranial_scqr_v11_l2_preflight import (
    MODEL_SEED,
    state_sha256,
    tensor_sha256,
)
from tools.run_cranial_scqr_v11_l3_benchmark import model_dense_output
from utils.config import cfg_from_yaml_file


ROOT = PROJECT_ROOT
FOLDS = ("A", "B")
BATCHES_PER_FOLD = 5
BATCH_SIZE = 4
CASES_PER_FOLD = 20
FORWARD_WARMUP_EPOCH = 20
TARGET_GRADIENT_RATIO = 0.1
WEIGHT_MIN = 1.0e-6
WEIGHT_MAX = 1.0


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lines(values):
    payload = "".join(f"{value}\n" for value in values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def gradient_rms(loss, encoder_features, retain_graph):
    gradient = torch.autograd.grad(
        loss,
        encoder_features,
        retain_graph=retain_graph,
        create_graph=False,
        allow_unused=False,
    )[0]
    value = float(torch.sqrt(torch.mean(gradient.detach().double().square())).cpu())
    if not math.isfinite(value) or value <= 0.0:
        raise RuntimeError("nonfinite or zero encoder-feature gradient RMS")
    return value


def validate_protocol(protocol, output_dir):
    payload = json.loads(protocol.read_text(encoding="utf-8"))
    if payload.get("protocol_id") != "cranial-scqr-v1.1-L4-gradient-calibration-v1":
        raise RuntimeError("unexpected L4 calibration protocol_id")
    if payload.get("status") != "frozen_before_execution":
        raise RuntimeError("L4 calibration protocol is not frozen")
    execution = payload.get("execution", {})
    if execution.get("allowed_runs") != 1:
        raise RuntimeError("protocol must authorize exactly one calibration run")
    if execution.get("output_dir") != str(output_dir.relative_to(ROOT)):
        raise RuntimeError("output directory differs from frozen protocol")
    expected = {
        "folds": list(FOLDS),
        "candidate": "A1",
        "model_seed": MODEL_SEED,
        "skulls_per_fold": 4,
        "cases_per_fold": CASES_PER_FOLD,
        "batches_per_fold": BATCHES_PER_FOLD,
        "batch_size": BATCH_SIZE,
        "full_model_forward_calls": 10,
        "autograd_calls": 20,
        "optimizer_constructions": 0,
        "optimizer_steps": 0,
        "bncal_runs": 0,
        "forward_mode": "eval_with_autograd",
        "temporary_residual_warmup_factor": 1.0,
        "target_gradient_ratio": TARGET_GRADIENT_RATIO,
        "weight_clip": [WEIGHT_MIN, WEIGHT_MAX],
    }
    if payload.get("calibration_contract") != expected:
        raise RuntimeError("calibration contract differs from runner constants")
    bindings = payload.get("sha256_bindings", [])
    if not bindings:
        raise RuntimeError("calibration protocol has no SHA256 bindings")
    for item in bindings:
        path = ROOT / item["path"]
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"SHA256 binding mismatch: {item['path']}")
    p0 = json.loads((ROOT / payload["prerequisites"]["p0_receipt"]).read_text())
    l2 = json.loads((ROOT / payload["prerequisites"]["l2_receipt"]).read_text())
    l3 = json.loads((ROOT / payload["prerequisites"]["l3_receipt"]).read_text())
    if p0.get("result") != "PASS":
        raise RuntimeError("bound P0 prerequisite is not PASS")
    if l2.get("status") != "PASS":
        raise RuntimeError("bound L2 prerequisite is not PASS")
    if l3.get("status") != "GATE_PASS":
        raise RuntimeError("bound L3 prerequisite is not GATE_PASS")
    return payload


def load_case_ids_unbounded(path):
    case_ids = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return case_ids


def load_case_ids(path):
    case_ids = load_case_ids_unbounded(path)
    if len(case_ids) != CASES_PER_FOLD or len(set(case_ids)) != CASES_PER_FOLD:
        raise RuntimeError(f"invalid calibration case list: {path}")
    return case_ids


def build_fold_dataset_and_model(fold, case_ids_path):
    config_path = (
        ROOT
        / "cfgs/SkullBreak_models/cranial_scqr_v11"
        / f"CranialSCQRV11_A1_fold{fold}_seed0.yaml"
    )
    config = cfg_from_yaml_file(str(config_path))
    execution = config.cranial_scqr_execution
    if execution.training_authorized is not False or execution.bncal_authorized is not False:
        raise RuntimeError("calibration must consume a training-locked L1 template")
    config.model.cranial_scqr.auxiliary_loss_weight = 1.0
    config.dataset.train.others.include_case_ids_file = str(case_ids_path)
    dataset = build_dataset_from_cfg(
        config.dataset.train._base_, config.dataset.train.others
    )
    if len(dataset) != CASES_PER_FOLD:
        raise RuntimeError(f"fold {fold}: expected exactly 20 calibration cases")
    requested = load_case_ids(case_ids_path)
    actual = {str(record["case_id"]) for record in dataset.records}
    if actual != set(requested):
        raise RuntimeError(f"fold {fold}: selected dataset differs from case list")
    torch.manual_seed(MODEL_SEED)
    torch.cuda.manual_seed_all(MODEL_SEED)
    model = build_model_from_cfg(config.model).eval()
    return dataset, model, config_path, requested


def fetch_batch(dataset, ordered_case_ids, device):
    index_by_id = {
        str(record["case_id"]): index
        for index, record in enumerate(dataset.records)
    }
    samples = [dataset[index_by_id[case_id]] for case_id in ordered_case_ids]
    partial = torch.stack([sample[2][0] for sample in samples]).to(device)
    target = torch.stack([sample[2][1] for sample in samples]).to(device)
    scale = dataset.get_normalization_scales(
        ordered_case_ids, device=device, dtype=partial.dtype
    )
    return partial, target, scale


def run_fold(fold, case_ids_path, device, log, row_sink):
    log(f"fold {fold}: construct A1 seed0 initial copy on CPU")
    dataset, model, config_path, case_ids = build_fold_dataset_and_model(
        fold, case_ids_path
    )
    state_before = state_sha256(model)
    model = model.to(device).eval()
    captured = {}

    def capture_encoder_features(_module, _inputs, output):
        captured["features"] = output

    hook = model.base_model.encoder.register_forward_hook(capture_encoder_features)
    rows = []
    try:
        for batch_index in range(BATCHES_PER_FOLD):
            batch_case_ids = case_ids[
                batch_index * BATCH_SIZE : (batch_index + 1) * BATCH_SIZE
            ]
            log(f"fold {fold}: batch {batch_index + 1}/5 load 4 authorized cases")
            partial, target, scale = fetch_batch(dataset, batch_case_ids, device)
            captured.clear()
            query_features, coarse, denoise_length, auxiliary = model.base_model(
                partial, epoch=FORWARD_WARMUP_EPOCH
            )
            if denoise_length != 0 or auxiliary is None:
                raise RuntimeError("A1 calibration forward contract failed")
            fine = model_dense_output(model, query_features, coarse)
            reconstruction_loss = model.loss_func(coarse, target)
            reconstruction_loss = reconstruction_loss + model.get_fine_loss_components(
                coarse, fine, target
            )[2]
            labels = build_contact_support_labels(
                partial,
                target,
                scale,
                auxiliary["knn32_indices"],
                rim_band_mm=2.0,
            )
            auxiliary_loss = case_balanced_binary_cross_entropy(
                auxiliary["contact_logits"], labels.proxy_labels
            )
            encoder_features = captured.get("features")
            if encoder_features is None:
                raise RuntimeError("public encoder output F was not captured")
            g_rec = gradient_rms(
                reconstruction_loss, encoder_features, retain_graph=True
            )
            g_scf = gradient_rms(
                auxiliary_loss, encoder_features, retain_graph=False
            )
            ratio = g_rec / g_scf
            values = [
                float(reconstruction_loss.detach().cpu()),
                float(auxiliary_loss.detach().cpu()),
                g_rec,
                g_scf,
                ratio,
            ]
            if not all(math.isfinite(value) and value > 0.0 for value in values):
                raise RuntimeError(f"fold {fold} batch {batch_index}: invalid value")
            row = {
                "fold": fold,
                "batch_index": batch_index,
                "case_ids": "|".join(batch_case_ids),
                "case_ids_sha256": sha256_lines(batch_case_ids),
                "partial_sha256": tensor_sha256(partial),
                "implant_sha256": tensor_sha256(target),
                "scale_sha256": tensor_sha256(scale),
                "reconstruction_loss": values[0],
                "scf_loss": values[1],
                "g_rec_rms_at_encoder_F": g_rec,
                "g_scf_rms_at_encoder_F": g_scf,
                "g_rec_over_g_scf": ratio,
                "raw_positive_count": int(labels.raw_positive_counts.sum().item()),
                "positive_proxy_count": int(labels.positive_proxy_counts.sum().item()),
            }
            rows.append(row)
            row_sink(row)
            log(
                f"fold {fold}: batch {batch_index + 1} complete "
                f"g_rec/g_scf={ratio:.9g}"
            )
            del (
                partial,
                target,
                scale,
                query_features,
                coarse,
                auxiliary,
                fine,
                reconstruction_loss,
                labels,
                auxiliary_loss,
                encoder_features,
            )
    finally:
        hook.remove()
    if any(parameter.grad is not None for parameter in model.parameters()):
        raise RuntimeError("autograd calibration unexpectedly populated parameter.grad")
    model = model.cpu()
    torch.cuda.synchronize()
    torch.cuda.empty_cache()
    state_after = state_sha256(model)
    if state_before != state_after:
        raise RuntimeError(f"fold {fold}: model parameters or buffers changed")
    ratios = [row["g_rec_over_g_scf"] for row in rows]
    median_ratio = float(statistics.median(ratios))
    unclipped = TARGET_GRADIENT_RATIO * median_ratio
    calibrated = min(max(unclipped, WEIGHT_MIN), WEIGHT_MAX)
    if not math.isfinite(calibrated) or calibrated <= 0.0:
        raise RuntimeError(f"fold {fold}: invalid calibrated lambda")
    return {
        "fold": fold,
        "candidate": "A1",
        "template": str(config_path.relative_to(ROOT)),
        "template_sha256": sha256_file(config_path),
        "selection_file": str(case_ids_path.relative_to(ROOT)),
        "selection_sha256": sha256_file(case_ids_path),
        "selected_case_ids": case_ids,
        "selected_case_ids_sha256": sha256_lines(case_ids),
        "selected_skulls": sorted({case_id.split("__")[1] for case_id in case_ids}),
        "gradient_ratios": ratios,
        "median_g_rec_over_g_scf": median_ratio,
        "lambda_unclipped": unclipped,
        "lambda_scf": calibrated,
        "lambda_clipped": calibrated != unclipped,
        "model_state_sha256_before": state_before,
        "model_state_sha256_after": state_after,
        "model_state_unchanged": True,
        "parameter_grad_tensors_after": 0,
        "payload_open_events": CASES_PER_FOLD,
        "full_model_forward_calls": BATCHES_PER_FOLD,
        "autograd_calls": 2 * BATCHES_PER_FOLD,
    }


def write_json(path, payload):
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_report(path, receipt):
    lines = [
        "# Cranial-SCQR v1.1 L4 train-only 梯度量级校准",
        "",
        f"- 状态：**{receipt['status']}**",
        f"- run ID：`{receipt['run_id']}`",
        "- optimizer 构造/step：0/0；checkpoint：0；BNCal：0。",
        "- 仅访问 fold-train 入选的 partial/implant 与 normalization scale。",
        "- eval+autograd，临时残差 warmup factor=1；不是训练。",
        "",
        "## 每折结果",
        "",
        "| fold | median g_rec/g_scf | unclipped λ | final λ | clipped |",
        "|---|---:|---:|---:|---:|",
    ]
    for fold in FOLDS:
        value = receipt.get("folds", {}).get(fold)
        if value is not None:
            lines.append(
                f"| {fold} | {value['median_g_rec_over_g_scf']:.9g} | "
                f"{value['lambda_unclipped']:.9g} | {value['lambda_scf']:.9g} | "
                f"{value['lambda_clipped']} |"
            )
    if receipt["status"] == "ERROR":
        lines.extend(["", "## 错误", "", "```text", receipt["error"], "```"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    protocol = args.protocol.resolve()
    output_dir = args.output_dir.resolve()
    payload = validate_protocol(protocol, output_dir)
    if output_dir.exists():
        raise FileExistsError(f"refusing to reuse calibration output: {output_dir}")
    output_dir.mkdir(parents=True)
    progress_path = output_dir / "progress.log"
    csv_path = output_dir / "batch_gradient_metrics.csv"
    fieldnames = (
        "fold",
        "batch_index",
        "case_ids",
        "case_ids_sha256",
        "partial_sha256",
        "implant_sha256",
        "scale_sha256",
        "reconstruction_loss",
        "scf_loss",
        "g_rec_rms_at_encoder_F",
        "g_scf_rms_at_encoder_F",
        "g_rec_over_g_scf",
        "raw_positive_count",
        "positive_proxy_count",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=fieldnames).writeheader()

    def log(message):
        line = f"[{utc_now()}] {message}"
        print(line, flush=True)
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def row_sink(row):
        with csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writerow(row)

    receipt = {
        "protocol_id": payload["protocol_id"],
        "protocol": str(protocol.relative_to(ROOT)),
        "protocol_sha256": sha256_file(protocol),
        "run_id": output_dir.name,
        "started_at_utc": utc_now(),
        "optimizer_constructions": 0,
        "optimizer_steps": 0,
        "checkpoints_loaded": 0,
        "checkpoints_written": 0,
        "bncal_runs": 0,
        "confirmation20_payload_opened": 0,
        "official_test_payload_opened": 0,
        "old_monitor_payload_opened": 0,
        "mug_payload_opened": 0,
    }
    try:
        if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
            raise RuntimeError("CUBLAS_WORKSPACE_CONFIG=:4096:8 is required")
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required")
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.benchmark = False
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        device = torch.device("cuda:0")
        fold_results = {}
        for fold in FOLDS:
            selection = ROOT / payload["folds"][fold]["selection_file"]
            fold_results[fold] = run_fold(
                fold, selection, device, log, row_sink
            )
        receipt.update(
            {
                "status": "PASS",
                "finished_at_utc": utc_now(),
                "folds": fold_results,
                "execution_counts": {
                    "folds": 2,
                    "payload_open_events": 40,
                    "selected_unique_cases": len(
                        set(fold_results["A"]["selected_case_ids"])
                        | set(fold_results["B"]["selected_case_ids"])
                    ),
                    "full_model_forward_calls": 10,
                    "autograd_calls": 20,
                    "optimizer_constructions": 0,
                    "optimizer_steps": 0,
                    "bncal_runs": 0,
                },
                "training_authorized_by_this_receipt": False,
            }
        )
    except Exception as exc:
        receipt.update(
            {
                "status": "ERROR",
                "finished_at_utc": utc_now(),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "training_authorized_by_this_receipt": False,
            }
        )
    write_json(output_dir / "calibration_receipt.json", receipt)
    write_json(
        output_dir / "calibration_summary.json",
        {
            "status": receipt["status"],
            "folds": receipt.get("folds", {}),
            "training_authorized": False,
        },
    )
    write_report(output_dir / "calibration_report_zh.md", receipt)
    files = [
        progress_path,
        csv_path,
        output_dir / "calibration_summary.json",
        output_dir / "calibration_receipt.json",
        output_dir / "calibration_report_zh.md",
    ]
    with (output_dir / "files.sha256").open("w", encoding="ascii") as handle:
        for path in files:
            handle.write(f"{sha256_file(path)}  {path.name}\n")
    print(f"[{receipt['status']}] {output_dir}", flush=True)
    if receipt["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
