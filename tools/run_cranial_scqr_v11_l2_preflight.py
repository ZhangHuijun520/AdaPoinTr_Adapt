#!/usr/bin/env python
"""Cranial-SCQR v1.1 L2 synthetic zero-update preflight.

This runner never opens a dataset, constructs an optimizer, calls optimizer.step,
performs BN calibration, or records latency measurements.
"""

import argparse
import hashlib
import json
import math
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Running a file under tools/ makes tools/ sys.path[0]. Bind the known project
# root before importing project-local packages.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
import torch.nn as nn
import yaml
from easydict import EasyDict
from scipy.spatial import cKDTree

from models import build_model_from_cfg
from models.cranial_scqr import (
    ContactConditionedQueryAttention,
    build_contact_support_labels,
    case_balanced_binary_cross_entropy,
    stable_knn_indices,
)
from tools.runner import _enforce_scqr_execution_guard
from utils.skullfix_metrics import point_rim_metrics


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "cfgs/SkullBreak_models/cranial_scqr_v11"
MODEL_SEED = 31002
SYNTHETIC_SEED = 20260911
COMPONENT_SEED = 31003
INPUT_POINTS = 8192
OUTPUT_POINTS = 8192
FULL_MODEL_FORWARD_CALLS = 7
FULL_MODEL_BACKWARD_CALLS = 1
OPTIMIZER_STEPS = 0


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_sha256(tensor):
    value = tensor.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode("ascii"))
    digest.update(str(tuple(value.shape)).encode("ascii"))
    digest.update(value.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def state_sha256(module, exclude_scqr=False):
    digest = hashlib.sha256()
    for name, value in sorted(module.state_dict().items()):
        if exclude_scqr and name.startswith("base_model.scqr_"):
            continue
        digest.update(name.encode("utf-8"))
        digest.update(tensor_sha256(value).encode("ascii"))
    return digest.hexdigest()


def state_snapshot(module):
    return {
        name: value.detach().cpu().clone()
        for name, value in module.state_dict().items()
    }


def changed_state_names(module, before):
    after = module.state_dict()
    if set(after) != set(before):
        raise AssertionError("state_dict key set changed")
    return sorted(
        name
        for name, old in before.items()
        if not torch.equal(old, after[name].detach().cpu())
    )


def assert_finite_tensor(value, name):
    if not torch.is_tensor(value) or not torch.isfinite(value).all():
        raise AssertionError(f"{name} is not a finite tensor")


def max_abs_difference(left, right):
    return float((left.detach().float() - right.detach().float()).abs().max().cpu())


def load_config(variant, auxiliary_loss_weight=None):
    path = CONFIG_DIR / f"CranialSCQRV11_{variant}_foldA_seed0.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload["cranial_scqr_execution"]["training_authorized"] is not False:
        raise AssertionError("L2 must consume a training-locked L1 template")
    payload["model"]["cranial_scqr"][
        "auxiliary_loss_weight"
    ] = auxiliary_loss_weight
    return EasyDict(payload), path


def build_variant(variant, device, auxiliary_loss_weight=None):
    config, path = load_config(variant, auxiliary_loss_weight)
    torch.manual_seed(MODEL_SEED)
    torch.cuda.manual_seed_all(MODEL_SEED)
    model = build_model_from_cfg(config.model).to(device)
    return model, config, path


def synthetic_case(device):
    index = torch.arange(INPUT_POINTS, dtype=torch.float64)
    z = 1.0 - 2.0 * (index + 0.5) / float(INPUT_POINTS)
    azimuth = index * (math.pi * (3.0 - math.sqrt(5.0)))
    radius = torch.sqrt(torch.clamp(1.0 - z.square(), min=0.0))
    partial = torch.stack(
        (radius * torch.cos(azimuth), radius * torch.sin(azimuth), z),
        dim=-1,
    ).float()
    # A deterministic northern cap, repeated only to match the locked 8192 target
    # count. It is synthetic geometry, not a dataset-derived implant.
    implant = partial[:2048].repeat(4, 1).contiguous()
    return (
        partial.unsqueeze(0).to(device),
        implant.unsqueeze(0).to(device),
        torch.tensor([100.0], device=device, dtype=torch.float32),
    )


def component_contracts(device):
    results = {}

    query = torch.zeros((1, 1, 3), device=device)
    reference = torch.tensor(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
        ]
        + [[float(index + 2), 0.0, 0.0] for index in range(28)],
        device=device,
    ).unsqueeze(0)
    indices, distances = stable_knn_indices(query, reference, k=4)
    if indices[0, 0].tolist() != [0, 1, 2, 3]:
        raise AssertionError("stable KNN tie order is not original-index order")
    results["stable_knn_tie_indices"] = indices[0, 0].tolist()
    results["stable_knn_tie_distances"] = distances[0, 0].cpu().tolist()

    partial = torch.full((1, 64, 3), 5.0, device=device)
    partial[0, 0] = torch.tensor([0.199, 0.0, 0.0], device=device)
    target = torch.zeros((1, 1, 3), device=device)
    knn = torch.stack(
        (torch.arange(0, 32, device=device), torch.arange(32, 64, device=device)),
        dim=0,
    ).unsqueeze(0)
    labels = build_contact_support_labels(
        partial,
        target,
        normalization_scale=torch.tensor([10.0], device=device),
        knn32_indices=knn,
        rim_band_mm=2.0,
    )
    if labels.proxy_labels.tolist() != [[True, False]]:
        raise AssertionError("millimetre-scale contact label contract failed")
    results["mm_label_raw_positive_count"] = int(labels.raw_positive_counts.item())
    results["mm_label_proxy_labels"] = labels.proxy_labels.cpu().tolist()

    logits = torch.tensor([[0.2, -0.4, 1.1]], device=device, requires_grad=True)
    empty_class = {}
    for label_name, label_value in (("all_positive", True), ("all_negative", False)):
        class_labels = torch.full_like(logits, label_value, dtype=torch.bool)
        loss = case_balanced_binary_cross_entropy(logits, class_labels)
        assert_finite_tensor(loss, f"{label_name} BCE")
        empty_class[label_name] = float(loss.detach().cpu())
    results["empty_class_bce"] = empty_class

    torch.manual_seed(COMPONENT_SEED)
    q0 = ContactConditionedQueryAttention(beta=0.0).to(device).eval()
    torch.manual_seed(COMPONENT_SEED)
    qc = ContactConditionedQueryAttention(beta=1.0).to(device).eval()
    for (name0, parameter0), (name1, parameter1) in zip(
        q0.named_parameters(), qc.named_parameters()
    ):
        if name0 != name1 or not torch.equal(parameter0, parameter1):
            raise AssertionError("Q0/QC query module parameters are not identical")
    generator = torch.Generator(device=device).manual_seed(SYNTHETIC_SEED)
    queries = torch.randn((2, 7, 384), generator=generator, device=device)
    proxies = torch.randn((2, 11, 384), generator=generator, device=device)
    position = torch.randn((2, 11, 384), generator=generator, device=device)
    probability = torch.rand((2, 11), generator=generator, device=device) * 0.8 + 0.1
    with torch.no_grad():
        q0_output = q0(queries, proxies, position, probability, epoch=20)
        projected_q = q0.query_projection(q0.query_norm(queries)).float()
        projected_k = q0.key_projection(q0.key_norm(proxies + position)).float()
        ordinary_logits = torch.matmul(
            projected_q, projected_k.transpose(-1, -2)
        ) / math.sqrt(128.0)
        ordinary_attention = torch.softmax(ordinary_logits, dim=-1)
        ordinary_difference = max_abs_difference(
            q0_output.attention, ordinary_attention
        )
        if ordinary_difference > 1.0e-7:
            raise AssertionError("beta=0 does not equal ordinary attention")

        constant_probability = torch.full((2, 11), 0.37, device=device)
        constant_q0 = q0(
            queries, proxies, position, constant_probability, epoch=20
        )
        constant_qc = qc(
            queries, proxies, position, constant_probability, epoch=20
        )
        constant_difference = max_abs_difference(
            constant_q0.attention, constant_qc.attention
        )
        if constant_difference > 1.0e-6:
            raise AssertionError("constant contact bias did not cancel in softmax")

        saved_alpha = qc.alpha_q.detach().clone()
        qc.alpha_q.zero_()
        alpha_zero = qc(queries, proxies, position, probability, epoch=20)
        alpha_zero_difference = max_abs_difference(alpha_zero.queries, queries)
        qc.alpha_q.copy_(saved_alpha)
        if alpha_zero_difference != 0.0:
            raise AssertionError("alpha_Q=0 did not recover uncoupled queries")

    detached_probability = probability.detach().clone().requires_grad_(True)
    detached_query = queries.detach().clone().requires_grad_(True)
    detached_output = qc(
        detached_query,
        proxies.detach(),
        position.detach(),
        detached_probability,
        epoch=20,
    )
    detached_output.queries.sum().backward()
    if detached_probability.grad is not None:
        raise AssertionError("contact probability bias path is not detached")
    results["query_attention"] = {
        "beta0_vs_ordinary_max_abs": ordinary_difference,
        "constant_probability_q0_vs_qc_max_abs": constant_difference,
        "alpha_q_zero_output_max_abs": alpha_zero_difference,
        "contact_probability_grad_is_none": True,
    }
    return results


def rimcover_contracts():
    cases = []
    for offset in (0.0, 0.25):
        defective = np.asarray(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
            dtype=np.float64,
        )
        reference = defective + np.asarray([0.0, 0.0, 1.0 + offset])
        prediction = defective + np.asarray([0.0, 0.0, 1.5 + offset])
        metric = point_rim_metrics(
            prediction,
            reference,
            defective,
            rim_band_mm=2.0,
        )
        reference_distance, _ = cKDTree(reference).query(defective, k=1)
        reference_rim = defective[reference_distance <= 2.0]
        manual_distance, _ = cKDTree(prediction).query(reference_rim, k=1)
        manual = float(np.percentile(manual_distance, 95))
        if metric.gt_rim_to_pred_p95_mm != manual:
            raise AssertionError("RimCover-P95 differs from the existing field")
        cases.append(
            {
                "offset": offset,
                "existing_field": metric.gt_rim_to_pred_p95_mm,
                "manual_rimcover_p95_mm": manual,
            }
        )

    defective = np.asarray([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    reference = defective + np.asarray([0.0, 0.0, 1.0])
    far_prediction = defective + np.asarray([0.0, 0.0, 20.0])
    no_contact = point_rim_metrics(
        far_prediction,
        reference,
        defective,
        rim_band_mm=2.0,
    )
    if no_contact.predicted_rim_points != 0:
        raise AssertionError("artificial no-contact case unexpectedly has contact")
    if not np.isfinite(no_contact.gt_rim_to_pred_p95_mm):
        raise AssertionError("primary RimCover is unavailable without predicted contact")
    return {
        "per_case_equivalence": cases,
        "no_predicted_contact": {
            "predicted_rim_points": no_contact.predicted_rim_points,
            "primary_rimcover_p95_mm": no_contact.gt_rim_to_pred_p95_mm,
            "contact_cd_is_nan": bool(np.isnan(no_contact.contact_cd_l1_mm)),
        },
    }


def summarize_instrumentation(records, variant):
    backbone = records["backbone"]
    summary = {
        "encoder_coordinates_shape": list(backbone["encoder_coordinates"].shape),
        "encoder_post_scqr_shape": list(backbone["encoder_post_scqr"].shape),
        "decoder_query_shape": list(records["decoder_query"].shape),
    }
    contact_logits = backbone["scqr_contact_logits"]
    attention = backbone["scqr_query_attention"]
    if variant == "B0":
        if contact_logits is not None or attention is not None:
            raise AssertionError("B0 unexpectedly produced SCQR instrumentation")
        return summary
    assert_finite_tensor(contact_logits, f"{variant} contact logits")
    if tuple(contact_logits.shape) != (1, 256):
        raise AssertionError(f"{variant} contact logit shape mismatch")
    probability = backbone["scqr_contact_probability"]
    assert_finite_tensor(probability, f"{variant} contact probability")
    summary.update(
        {
            "contact_logits_shape": list(contact_logits.shape),
            "contact_probability_min": float(probability.min().cpu()),
            "contact_probability_max": float(probability.max().cpu()),
        }
    )
    if variant == "A1":
        if attention is not None:
            raise AssertionError("A1 unexpectedly used query conditioning")
    else:
        assert_finite_tensor(attention, f"{variant} query attention")
        if tuple(attention.shape) != (1, 256, 256):
            raise AssertionError(f"{variant} query attention shape mismatch")
        summary["query_attention_shape"] = list(attention.shape)
        summary["attention_row_sum_max_error"] = float(
            (attention.sum(-1) - 1.0).abs().max().cpu()
        )
    return summary


def full_model_forward_contracts(device, partial, shuffled_gt_hashes):
    results = {}
    common_hashes = {}
    q0_coarse = None
    for variant in ("B0", "A1", "Q0", "QC"):
        model, _, config_path = build_variant(variant, device)
        model.eval()
        before = state_sha256(model)
        common_hashes[variant] = state_sha256(model, exclude_scqr=True)
        if variant == "QC":
            with torch.no_grad():
                output_without_instrumentation = model(partial)
            model.enable_full_instrumentation(True)
            with torch.no_grad():
                output = model(partial)
            records = model.pop_full_instrumentation()
            model.enable_full_instrumentation(False)
            toggle_differences = [
                max_abs_difference(left, right)
                for left, right in zip(output_without_instrumentation, output)
            ]
            if max(toggle_differences) > 1.0e-7:
                raise AssertionError("instrumentation changed QC inference output")
            gt_free = {
                "external_gt_original_sha256": shuffled_gt_hashes[0],
                "external_gt_shuffled_sha256": shuffled_gt_hashes[1],
                "gt_was_passed_to_forward": False,
                "output_max_abs_after_external_gt_shuffle": max(toggle_differences),
            }
        else:
            model.enable_full_instrumentation(True)
            with torch.no_grad():
                output = model(partial)
            records = model.pop_full_instrumentation()
            model.enable_full_instrumentation(False)
            toggle_differences = None
            gt_free = None

        if len(output) != 2:
            raise AssertionError(f"{variant} eval output must contain coarse and fine")
        coarse, fine = output
        assert_finite_tensor(coarse, f"{variant} coarse")
        assert_finite_tensor(fine, f"{variant} fine")
        if tuple(coarse.shape) != (1, 256, 3):
            raise AssertionError(f"{variant} coarse shape mismatch")
        if tuple(fine.shape) != (1, OUTPUT_POINTS, 3):
            raise AssertionError(f"{variant} fine shape mismatch")
        if state_sha256(model) != before:
            raise AssertionError(f"{variant} eval forward changed model state")
        result = {
            "config": str(config_path.relative_to(ROOT)),
            "config_sha256": sha256_file(config_path),
            "coarse_shape": list(coarse.shape),
            "fine_shape": list(fine.shape),
            "coarse_sha256": tensor_sha256(coarse),
            "fine_sha256": tensor_sha256(fine),
            "state_unchanged": True,
            "instrumentation": summarize_instrumentation(records, variant),
        }
        if toggle_differences is not None:
            result["instrumentation_toggle_max_abs"] = toggle_differences
            result["gt_free_inference"] = gt_free
        if variant == "Q0":
            q0_coarse = coarse.detach().cpu()
        if variant == "QC":
            coarse_difference = max_abs_difference(q0_coarse, coarse.cpu())
            if coarse_difference != 0.0:
                raise AssertionError("Q0/QC coarse changed under fixed upstream state")
            result["q0_qc_coarse_max_abs"] = coarse_difference
        results[variant] = result
        del records, output, coarse, fine, model
        torch.cuda.empty_cache()
    if len(set(common_hashes.values())) != 1:
        raise AssertionError("public initialization differs across B0/A1/Q0/QC")
    return results, common_hashes


def full_model_backward_contract(device, partial, implant, scale):
    # lambda=1 is an in-memory synthetic diagnostic value only. It is neither
    # calibrated nor written into any runtime configuration.
    model, _, _ = build_variant("QC", device, auxiliary_loss_weight=1.0)
    model.train()
    frozen_bn = []
    for name, module in model.named_modules():
        if isinstance(module, nn.modules.batchnorm._BatchNorm):
            module.eval()
            frozen_bn.append(name)
    before = state_snapshot(model)
    output = model(partial, epoch=10)
    if len(output) != 5:
        raise AssertionError("QC training output must include SCQR auxiliary data")
    sparse_loss, dense_loss = model.get_loss(
        output,
        implant,
        epoch=10,
        partial=partial,
        normalization_scale=scale,
    )
    total_loss = sparse_loss + dense_loss
    assert_finite_tensor(total_loss, "QC total loss")
    total_loss.backward()
    nonfinite_gradients = []
    gradient_names = []
    for name, parameter in model.named_parameters():
        if parameter.grad is not None:
            gradient_names.append(name)
            if not torch.isfinite(parameter.grad).all():
                nonfinite_gradients.append(name)
    if nonfinite_gradients:
        raise AssertionError(f"nonfinite gradients: {nonfinite_gradients}")
    required_gradient_fragments = (
        "scqr_local_geometry.alpha_l",
        "scqr_contact_head.network.0.weight",
        "scqr_query_conditioner.alpha_q",
    )
    for fragment in required_gradient_fragments:
        if not any(fragment in name for name in gradient_names):
            raise AssertionError(f"missing SCQR gradient: {fragment}")
    changed = changed_state_names(model, before)
    if changed:
        raise AssertionError(f"zero-update backward changed state: {changed}")
    auxiliary = output[4]
    positive_counts = auxiliary["positive_proxy_counts"].detach().cpu().tolist()
    if not all(0 < count < 256 for count in positive_counts):
        raise AssertionError("synthetic QC proxy labels do not contain both classes")
    result = {
        "mode": "train_return_path_with_all_batchnorm_layers_forced_eval",
        "epoch": 10,
        "diagnostic_auxiliary_loss_weight": 1.0,
        "diagnostic_weight_is_calibration": False,
        "sparse_loss": float(sparse_loss.detach().cpu()),
        "dense_loss": float(dense_loss.detach().cpu()),
        "total_loss": float(total_loss.detach().cpu()),
        "gradient_tensor_count": len(gradient_names),
        "nonfinite_gradient_count": 0,
        "positive_proxy_counts": positive_counts,
        "frozen_batchnorm_modules": frozen_bn,
        "changed_state_names": changed,
        "parameters_unchanged": True,
        "buffers_unchanged": True,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
    }
    model.zero_grad(set_to_none=True)
    del output, total_loss, sparse_loss, dense_loss, model
    torch.cuda.empty_cache()
    return result


def disposable_train_mode_bn_audit(device, partial):
    model, _, _ = build_variant("B0", device)
    model.train()
    before = state_snapshot(model)
    parameter_names = set(dict(model.named_parameters()))
    expected_bn_buffers = set()
    for module_name, module in model.named_modules():
        if isinstance(module, nn.modules.batchnorm._BatchNorm):
            for buffer_name, _ in module.named_buffers(recurse=False):
                expected_bn_buffers.add(
                    f"{module_name}.{buffer_name}" if module_name else buffer_name
                )
    with torch.no_grad():
        output = model(partial)
    changed = changed_state_names(model, before)
    changed_parameters = sorted(set(changed).intersection(parameter_names))
    unexpected = sorted(set(changed).difference(expected_bn_buffers))
    if changed_parameters or unexpected or not changed:
        raise AssertionError(
            "disposable train-mode mutation audit did not isolate BN buffers: "
            f"parameters={changed_parameters}, unexpected={unexpected}, changed={changed}"
        )
    result = {
        "disposable_clone": True,
        "purpose": "explain why formal zero-update autograd freezes BN modules",
        "forward_output_items": len(output),
        "changed_parameter_names": changed_parameters,
        "changed_buffer_names": changed,
        "all_changes_are_batchnorm_buffers": True,
        "clone_destroyed_after_audit": True,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
    }
    del output, model
    torch.cuda.empty_cache()
    return result


def execution_guard_contract():
    config, _ = load_config("B0")
    try:
        _enforce_scqr_execution_guard(config)
    except RuntimeError as exc:
        message = str(exc)
        if "training is locked" not in message:
            raise
        return {"blocked": True, "message": message}
    raise AssertionError("training-locked L1 config passed the execution guard")


def run_preflight(log):
    if not torch.cuda.is_available():
        raise RuntimeError("L2 requires the locked CUDA environment")
    device = torch.device("cuda:0")
    torch.manual_seed(SYNTHETIC_SEED)
    torch.cuda.manual_seed_all(SYNTHETIC_SEED)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    partial, implant, scale = synthetic_case(device)
    original_gt_hash = tensor_sha256(implant)
    permutation = torch.arange(INPUT_POINTS - 1, -1, -1, device=device)
    shuffled_gt_hash = tensor_sha256(implant[:, permutation])
    if original_gt_hash == shuffled_gt_hash:
        raise AssertionError("external GT shuffle did not change its content hash")

    log("component contracts")
    components = component_contracts(device)
    log("RimCover contracts")
    rimcover = rimcover_contracts()
    log("execution lock contract")
    guard = execution_guard_contract()
    log("B0/A1/Q0/QC full-model forward contracts")
    forward, common_hashes = full_model_forward_contracts(
        device,
        partial,
        (original_gt_hash, shuffled_gt_hash),
    )
    log("QC finite backward with zero state updates")
    backward = full_model_backward_contract(device, partial, implant, scale)
    log("disposable train-mode BN mutation audit")
    bn_audit = disposable_train_mode_bn_audit(device, partial)
    return {
        "status": "PASS",
        "device": {
            "type": str(device),
            "name": torch.cuda.get_device_name(device),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "dtype": "float32",
        },
        "synthetic_input": {
            "generator": "deterministic_fibonacci_sphere_plus_northern_cap",
            "seed": SYNTHETIC_SEED,
            "batch_size": 1,
            "partial_shape": list(partial.shape),
            "implant_shape": list(implant.shape),
            "normalization_scale_mm": scale.cpu().tolist(),
            "partial_sha256": tensor_sha256(partial),
            "implant_sha256": original_gt_hash,
        },
        "determinism": {
            "torch_deterministic_algorithms": True,
            "cudnn_benchmark": False,
            "allow_tf32": False,
        },
        "component_contracts": components,
        "rimcover_contracts": rimcover,
        "execution_guard": guard,
        "full_model_forward": forward,
        "public_initialization_sha256": common_hashes,
        "full_model_backward": backward,
        "disposable_train_mode_bn_audit": bn_audit,
        "execution_counts": {
            "full_model_forward_calls": FULL_MODEL_FORWARD_CALLS,
            "full_model_backward_calls": FULL_MODEL_BACKWARD_CALLS,
            "optimizer_constructions": 0,
            "optimizer_steps": OPTIMIZER_STEPS,
            "formal_timing_iterations": 0,
            "bncal_runs": 0,
            "dataset_payload_files_opened": 0,
        },
    }


def write_json(path, payload):
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_report(path, receipt):
    result = receipt.get("result", {})
    status = receipt["status"]
    counts = result.get("execution_counts", {})
    backward = result.get("full_model_backward", {})
    bn_audit = result.get("disposable_train_mode_bn_audit", {})
    text = f"""# Cranial-SCQR v1.1 L2 零更新 preflight

- 状态：**{status}**
- run ID：`{receipt['run_id']}`
- 开始：`{receipt['started_at_utc']}`
- 结束：`{receipt['finished_at_utc']}`
- protocol SHA256：`{receipt['protocol_sha256']}`

## 权限与执行计数

- 整网 forward：{counts.get('full_model_forward_calls', 0)}
- 整网 backward：{counts.get('full_model_backward_calls', 0)}
- optimizer 构造/step：{counts.get('optimizer_constructions', 0)} / {counts.get('optimizer_steps', 0)}
- 正式计时循环：{counts.get('formal_timing_iterations', 0)}
- BNCal：{counts.get('bncal_runs', 0)}
- 数据 payload：{counts.get('dataset_payload_files_opened', 0)}

## 核心结论

- B0/A1/Q0/QC 形状、有限性与公共初始化：`{status}`。
- QC backward 非有限梯度数：{backward.get('nonfinite_gradient_count', 'NA')}。
- 正式 backward 参数/buffer 更新：{backward.get('model_updates', 'NA')}。
- 一次性 train-mode clone 只变化 BN buffers：{bn_audit.get('all_changes_are_batchnorm_buffers', 'NA')}。
- L1 runtime 配置训练锁保持有效；本次没有生成授权训练配置。

## 边界

本结果只证明固定人工输入下的零更新执行契约，不是训练、BNCal、辅助损失校准或性能 benchmark，也不提供真实病例效果证据。
"""
    if status != "PASS":
        text += f"\n## 失败\n\n```text\n{receipt.get('error', '')}\n```\n"
    path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    protocol = args.protocol.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"refusing to reuse L2 output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    progress_path = output_dir / "progress.log"

    def log(message):
        line = f"[{utc_now()}] {message}"
        print(line, flush=True)
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    started = utc_now()
    protocol_hash = sha256_file(protocol)
    receipt = {
        "protocol_id": "cranial-scqr-v1.1-L2-zero-update-preflight-v1",
        "protocol": str(protocol.relative_to(ROOT)),
        "protocol_sha256": protocol_hash,
        "run_id": output_dir.name,
        "started_at_utc": started,
        "optimizer_steps": 0,
        "bncal_runs": 0,
        "dataset_payload_files_opened": 0,
        "formal_timing_iterations": 0,
    }
    try:
        log("L2 synthetic zero-update preflight started")
        result = run_preflight(log)
        receipt.update(
            {
                "status": "PASS",
                "finished_at_utc": utc_now(),
                "result": result,
            }
        )
    except Exception as exc:
        receipt.update(
            {
                "status": "FAIL",
                "finished_at_utc": utc_now(),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
        )
    write_json(output_dir / "l2_preflight_receipt.json", receipt)
    write_report(output_dir / "l2_preflight_report_zh.md", receipt)
    files = [
        progress_path,
        output_dir / "l2_preflight_receipt.json",
        output_dir / "l2_preflight_report_zh.md",
    ]
    with (output_dir / "files.sha256").open("w", encoding="ascii") as handle:
        for path in files:
            handle.write(f"{sha256_file(path)}  {path.name}\n")
    print(f"[{receipt['status']}] {output_dir}", flush=True)
    if receipt["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
