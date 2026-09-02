#!/usr/bin/env python3
"""Run the preregistered artificial CUDA zero-step for D6-A R0/R1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import scipy
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.mamba_d5a_proposal import (  # noqa: E402
    D5V1ContextHead,
    d5_v1_set_level_loss,
    select_deterministic_top32,
)
from utils.mamba_d6a_slot_allocator import (  # noqa: E402
    CANDIDATE_COUNT,
    D6R1SlotAllocator,
    d6a_raw_losses,
)


VERSION = "mamba-v16-d6a-synthetic-zero-step-v1"
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_synthetic_zero_step_protocol_v1.json"
AMENDMENT = ROOT / "docs" / "mamba_v16_d6a_scipy_compatibility_amendment_v1.json"
IMPLEMENTATION = ROOT / "utils" / "mamba_d6a_slot_allocator.py"
TESTS = ROOT / "tools" / "test_mamba_v16_d6a_slot_allocator.py"
EXPECTED = {
    "mechanism_protocol": "2fff4782d429a3ea70607560bee9f464fb7b4eb7cea261376a91eb648a72f284",
    "mechanism_receipt": "acd62da63f0788ed2cbca2d48a49114c4cf8cd89b49a878d7fcba94e7ecd2a89",
    "mechanism_manifest": "4cbad1016851057152ad536bb69462df9a2c0b3d2440780336e3f24ac69d1a12",
    "implementation": "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43",
    "tests": "94e8933fd45b80864e62f009afdf3043d35529f7f62f7a5f6c0870f5b1c86a00",
    "scipy_amendment": "5c5cd38d7dd2386c9886a007f4318be5328bac014c50f94b31dd713bb9890914",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def tensor_state_hash(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    lineage = protocol["lineage"]
    environment = protocol["environment"]
    artificial = protocol["artificial_input"]
    execution = protocol["execution"]
    access = protocol["access_boundary"]
    if (
        protocol["protocol_id"] != VERSION
        or protocol["status"] != "preregistered_artificial_CUDA_zero_step_only"
        or lineage["mechanism_protocol_sha256"] != EXPECTED["mechanism_protocol"]
        or lineage["mechanism_lock_receipt_sha256"] != EXPECTED["mechanism_receipt"]
        or lineage["mechanism_lock_manifest_sha256"] != EXPECTED["mechanism_manifest"]
        or lineage["implementation_sha256"] != EXPECTED["implementation"]
        or lineage["implementation_tests_sha256"] != EXPECTED["tests"]
        or lineage["scipy_compatibility_amendment_sha256"]
        != EXPECTED["scipy_amendment"]
        or environment["device"] != "CUDA_required"
        or environment["dtype"] != "float32"
        or environment["scipy_version_specifier"] != ">=1.11,<2.0"
        or environment["scipy_semantic_runtime_tests_required"] is not True
        or artificial["cases"] != 4
        or artificial["candidate_points_per_case"] != 8192
        or artificial["descriptor_dimensions"] != 27
        or artificial["positive_points_per_case"] != 16
        or artificial["contains_D6_identity_or_geometry"] is not False
        or execution["candidates"] != ["R0", "R1"]
        or execution["forward_passes"] != 8
        or execution["backward_passes"] != 8
        or execution["optimizer_constructed"] is not False
        or execution["optimizer_steps"] != 0
        or execution["model_updates"] != 0
        or execution["checkpoint_loaded"] is not False
        or execution["checkpoint_written"] is not False
        or access["D6_cases_accessed"] != 0
        or access["D6_geometry_accessed"] is not False
        or access["D6_confirmation_accessed"] is not False
        or access["training_authorized"] is not False
        or access["selection_started"] is not False
    ):
        raise RuntimeError("D6-A synthetic zero-step protocol drifted")


def verify_mechanism_lock(directory: Path) -> Dict[str, str]:
    manifest = directory / "files.sha256"
    receipt = directory / "mechanism_lock_receipt.json"
    protocol = directory / "mechanism_protocol_v1.json"
    if (
        sha256_file(manifest) != EXPECTED["mechanism_manifest"]
        or sha256_file(receipt) != EXPECTED["mechanism_receipt"]
        or sha256_file(protocol) != EXPECTED["mechanism_protocol"]
    ):
        raise RuntimeError("D6-A mechanism lock drifted")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = directory / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"D6-A mechanism lock hash failure: {path}")
    frozen = json.loads(receipt.read_text(encoding="utf-8"))
    if (
        frozen["status"] != "D6A_slot32_mechanism_frozen_implementation_not_started"
        or frozen["implementation_authorized_next"] is not True
        or frozen["training_authorized"] is not False
        or frozen["proposal_confirmation_authorized"] is not False
    ):
        raise RuntimeError("D6-A mechanism permission boundary drifted")
    return {
        "mechanism_protocol": sha256_file(protocol),
        "mechanism_receipt": sha256_file(receipt),
        "mechanism_manifest": sha256_file(manifest),
    }


def ensure_environment() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError("D6-A formal zero-step requires CUDA")
    version_parts = scipy.__version__.split(".")
    try:
        scipy_major_minor = (int(version_parts[0]), int(version_parts[1]))
    except (IndexError, ValueError) as exc:
        raise RuntimeError(f"Cannot parse SciPy version: {scipy.__version__}") from exc
    if not ((1, 11) <= scipy_major_minor < (2, 0)):
        raise RuntimeError(
            f"D6-A formal zero-step requires SciPy >=1.11,<2.0, found {scipy.__version__}"
        )
    return torch.device("cuda")


def artificial_case(case_index: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(160600 + case_index)
    descriptors = torch.randn(
        1, CANDIDATE_COUNT, 27, generator=generator, dtype=torch.float32
    ).to(device)
    positive = torch.zeros(1, CANDIDATE_COUNT, dtype=torch.bool)
    start = 17 + case_index * 97
    positive_indices = (start + torch.arange(16) * 431) % CANDIDATE_COUNT
    positive[0, positive_indices] = True
    return descriptors, positive.to(device)


def run_zero_step(device: torch.device) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    torch.manual_seed(160600)
    torch.cuda.manual_seed_all(160600)
    r0 = D5V1ContextHead().to(device)
    r1 = D6R1SlotAllocator().to(device)
    before = {"R0": tensor_state_hash(r0), "R1": tensor_state_hash(r1)}
    rows = []
    backward_passes = 0
    for case_index in range(4):
        descriptors, positive = artificial_case(case_index, device)

        r0.zero_grad(set_to_none=True)
        r0_logits = r0(descriptors)
        r0_losses = d5_v1_set_level_loss(r0_logits, positive)
        r0_losses["total"].backward()
        backward_passes += 1
        r0_selected = select_deterministic_top32(r0_logits.detach())
        r0_hit = bool(positive[0, r0_selected[0]].any().item())
        r0_grad_finite = all(
            parameter.grad is None or torch.isfinite(parameter.grad).all()
            for parameter in r0.parameters()
        )
        rows.append(
            {
                "artificial_case": case_index,
                "candidate": "R0",
                "loss": f"{r0_losses['total'].item():.12g}",
                "selected_unique": int(r0_selected[0].unique().numel()),
                "selected_hit_observation_only": str(r0_hit).lower(),
                "gradients_finite": str(r0_grad_finite).lower(),
            }
        )

        r1.zero_grad(set_to_none=True)
        r1_outputs = r1(descriptors)
        r1_losses = d6a_raw_losses(r1_outputs, positive)
        r1_probe = r1_losses["L_point"] + r1_losses["L_support"] + r1_losses["L_shape"]
        r1_probe.backward()
        backward_passes += 1
        r1_selected = r1_losses["selected_indices"]
        r1_hit = bool(positive[0, r1_selected[0]].any().item())
        r1_grad_finite = all(
            parameter.grad is None or torch.isfinite(parameter.grad).all()
            for parameter in r1.parameters()
        )
        rows.append(
            {
                "artificial_case": case_index,
                "candidate": "R1",
                "loss": f"{r1_probe.item():.12g}",
                "selected_unique": int(r1_selected[0].unique().numel()),
                "selected_hit_observation_only": str(r1_hit).lower(),
                "gradients_finite": str(r1_grad_finite).lower(),
            }
        )
        del descriptors, positive, r0_logits, r1_outputs

    after = {"R0": tensor_state_hash(r0), "R1": tensor_state_hash(r1)}
    if before != after:
        raise RuntimeError("D6-A zero-step changed model parameters")
    if backward_passes != 8:
        raise RuntimeError("D6-A zero-step backward count drifted")
    if any(row["selected_unique"] != 32 or row["gradients_finite"] != "true" for row in rows):
        raise RuntimeError("D6-A zero-step finite/unique contract failed")
    return rows, {
        "state_hash_before": before,
        "state_hash_after": after,
        "backward_passes": backward_passes,
        "R0_trainable_parameters": sum(p.numel() for p in r0.parameters()),
        "R1_trainable_parameters": r1.trainable_parameter_count(),
    }


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            path.name: path.read_bytes() for path in output_dir.iterdir() if path.is_file()
        }
        if existing != dict(outputs):
            raise RuntimeError(f"Existing D6-A zero-step result drifted: {output_dir}")
        print(f"[locked] existing D6-A zero-step is byte-identical: {output_dir}")
        return
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            (working / name).write_bytes(payload)
        working.replace(output_dir)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mechanism_lock_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    if sha256_file(AMENDMENT) != EXPECTED["scipy_amendment"]:
        raise RuntimeError("D6-A SciPy compatibility amendment drifted")
    if sha256_file(IMPLEMENTATION) != EXPECTED["implementation"]:
        raise RuntimeError("D6-A implementation drifted")
    if sha256_file(TESTS) != EXPECTED["tests"]:
        raise RuntimeError("D6-A implementation tests drifted")
    lineage = verify_mechanism_lock(args.mechanism_lock_dir)
    device = ensure_environment()
    rows, execution = run_zero_step(device)
    metrics = csv_bytes(
        [
            "artificial_case",
            "candidate",
            "loss",
            "selected_unique",
            "selected_hit_observation_only",
            "gradients_finite",
        ],
        rows,
    )
    receipt = {
        "protocol_id": VERSION,
        "status": "D6A_R0_R1_artificial_CUDA_zero_step_passed",
        "lineage_sha256": lineage,
        "protocol_sha256": sha256_file(PROTOCOL),
        "implementation_sha256": sha256_file(IMPLEMENTATION),
        "implementation_tests_sha256": sha256_file(TESTS),
        "scipy_compatibility_amendment_sha256": sha256_file(AMENDMENT),
        "torch_version": torch.__version__,
        "scipy_version": scipy.__version__,
        "cuda_device_name": torch.cuda.get_device_name(device),
        "artificial_cases": 4,
        "forward_passes": 8,
        "backward_passes": execution["backward_passes"],
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "checkpoint_loaded": False,
        "checkpoint_written": False,
        "state_hash_before": execution["state_hash_before"],
        "state_hash_after": execution["state_hash_after"],
        "R0_trainable_parameters": execution["R0_trainable_parameters"],
        "R1_trainable_parameters": execution["R1_trainable_parameters"],
        "selected_hit_is_observation_only_not_a_gate": True,
        "D6_cases_accessed": 0,
        "D6_geometry_accessed": False,
        "D6_generation_authorized": False,
        "gradient_calibration_authorized": False,
        "training_authorized": False,
        "seed1_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "selection_started": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "freeze_implementation_and_zero_step_then_authorize_development_download_and_QC_only",
    }
    report = (
        "# Mamba v1.6 D6-A artificial CUDA zero-step\n\n"
        "- artificial cases：4；D6 cases：0。\n"
        "- R0/R1 forward：8；backward：8。\n"
        "- optimizer steps：0；model updates：0。\n"
        f"- R1 trainable parameters：{execution['R1_trainable_parameters']}。\n"
        "- selected-hit 只记录随机初始化路径，不构成 gate。\n"
        "- generation、calibration、training、seed-1、confirmation 与 D6-B 继续锁定。\n"
    ).encode("utf-8")
    outputs: Dict[str, bytes] = {
        "artificial_probe_metrics.csv": metrics,
        "zero_step_preflight_receipt.json": canonical_json(receipt),
        "zero_step_preflight_report_zh.md": report,
    }
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    ).encode("ascii")
    write_locked(outputs, args.out_dir)
    print(f"[saved] immutable D6-A synthetic zero-step: {args.out_dir}")
    print("[done] artificial_cases=4 forward=8 backward=8 optimizer_steps=0 model_updates=0")
    print("[locked] D6=0 generation=false calibration=false training=false sealed=false")


if __name__ == "__main__":
    main()
