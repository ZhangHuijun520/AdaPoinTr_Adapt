#!/usr/bin/env python3
"""Run the artificial full-inference zero-step for the D6-A benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.mamba_d5a_proposal import D5V1ContextHead  # noqa: E402
from utils.mamba_d6a_efficiency import full_inference_once  # noqa: E402
from utils.mamba_d6a_slot_allocator import D6R1SlotAllocator  # noqa: E402


VERSION = "mamba-v16-d6a-full-inference-efficiency-implementation-zero-step-v1"
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_efficiency_implementation_zero_step_protocol_v1.json"
R0_IMPLEMENTATION = ROOT / "utils" / "mamba_d5a_proposal.py"
R1_IMPLEMENTATION = ROOT / "utils" / "mamba_d6a_slot_allocator.py"
EFFICIENCY_IMPLEMENTATION = ROOT / "utils" / "mamba_d6a_efficiency.py"
TESTS = ROOT / "tools" / "test_mamba_v16_d6a_efficiency_implementation.py"
EXPECTED = {
    "candidate_protocol": "5060c7700e53d42a4100ebeacf35f662accd58c585fc82af1443fafffb17fc3e",
    "R0": "6cca9c11f302da3ca202f3e33547c62e4584eeb0fd81f9e96c20f2787e04f070",
    "R1": "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43",
    "efficiency": "7a42c8fafe09ba3a98a052dd002137b4a9ab3d71ef630585cc85a269dfd8428b",
    "tests": "d086dcdee369d0c6beb68f5244402b270baee1b2f62fbc76af9506633bf32e12"
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
    zero = protocol["artificial_zero_step"]
    permission = protocol["permission_boundary"]
    if (
        protocol["protocol_id"] != VERSION
        or protocol["status"] != "preregistered_artificial_zero_step_formal_benchmark_not_authorized"
        or zero["full_inference_passes"] != {"R0": 1, "R1": 1}
        or zero["formal_warmup_runs"] != 0
        or zero["formal_timed_runs"] != 0
        or zero["latency_gate_evaluated"] is not False
        or zero["peak_memory_gate_evaluated"] is not False
        or zero["optimizer_steps"] != 0
        or zero["model_updates"] != 0
        or permission["formal_efficiency_execution_authorized"] is not False
        or permission["separate_formal_efficiency_execution_authorization_allowed_next"] is not True
        or permission["seed0_training_authorized"] is not False
        or permission["seed1_training_authorized"] is not False
        or permission["D6B_authorized"] is not False
        or permission["protected_or_sealed_data_accessed"] is not False
    ):
        raise RuntimeError("D6-A efficiency zero-step protocol drifted")


def verify_protocol_lock(directory: Path) -> dict[str, str]:
    manifest = directory / "files.sha256"
    receipt_path = directory / "protocol_lock_receipt.json"
    protocol_copy = directory / "candidate_training_efficiency_protocol_v1.json"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = directory / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"D6-A candidate protocol lock hash failure: {path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt["status"] != "D6A_candidate_training_efficiency_protocol_frozen_non_runnable"
        or receipt["optimizer_steps"] != 0
        or receipt["efficiency_execution_authorized"] is not False
        or receipt["seed0_training_authorized"] is not False
        or sha256_file(protocol_copy) != EXPECTED["candidate_protocol"]
    ):
        raise RuntimeError("D6-A candidate protocol permission boundary drifted")
    return {
        "manifest": sha256_file(manifest),
        "receipt": sha256_file(receipt_path),
        "protocol": sha256_file(protocol_copy),
    }


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {path.name: path.read_bytes() for path in output_dir.iterdir() if path.is_file()}
        if existing != dict(outputs):
            raise RuntimeError(f"Existing efficiency zero-step drifted: {output_dir}")
        print(f"[locked] existing D6-A efficiency zero-step is byte-identical: {output_dir}")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol_lock_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    for path, expected in ((R0_IMPLEMENTATION, EXPECTED["R0"]), (R1_IMPLEMENTATION, EXPECTED["R1"]), (EFFICIENCY_IMPLEMENTATION, EXPECTED["efficiency"]), (TESTS, EXPECTED["tests"])):
        if sha256_file(path) != expected:
            raise RuntimeError(f"D6-A efficiency implementation lineage drifted: {path}")
    lineage = verify_protocol_lock(args.protocol_lock_dir.resolve())
    if not torch.cuda.is_available():
        raise RuntimeError("D6-A efficiency zero-step requires CUDA")
    device = torch.device("cuda")
    torch.manual_seed(160610)
    torch.cuda.manual_seed_all(160610)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(160610)
    descriptors = torch.randn(1, 8192, 27, generator=generator, dtype=torch.float32).to(device)
    models = {"R0": D5V1ContextHead().to(device).eval(), "R1": D6R1SlotAllocator().to(device).eval()}
    before = {name: tensor_state_hash(model) for name, model in models.items()}
    rows = []
    with torch.inference_mode():
        for name, model in models.items():
            torch.cuda.synchronize(device)
            selected = full_inference_once(name, model, descriptors)
            torch.cuda.synchronize(device)
            rows.append({"candidate": name, "selected_count": int(selected.shape[1]), "selected_unique": int(selected.unique().numel()), "minimum_index": int(selected.min().item()), "maximum_index": int(selected.max().item())})
    after = {name: tensor_state_hash(model) for name, model in models.items()}
    if before != after or any(row["selected_unique"] != 32 for row in rows):
        raise RuntimeError("D6-A efficiency zero-step state/selector contract failed")
    receipt = {
        "protocol_id": VERSION,
        "status": "D6A_R0_R1_full_inference_efficiency_artificial_zero_step_passed",
        "protocol_sha256": sha256_file(PROTOCOL),
        "candidate_protocol_lineage_sha256": lineage,
        "implementation_sha256": {"R0": sha256_file(R0_IMPLEMENTATION), "R1": sha256_file(R1_IMPLEMENTATION), "efficiency": sha256_file(EFFICIENCY_IMPLEMENTATION), "tests": sha256_file(TESTS)},
        "torch_version": torch.__version__,
        "cuda_device_name": torch.cuda.get_device_name(device),
        "artificial_descriptor_seed": 160610,
        "full_inference_passes": {"R0": 1, "R1": 1},
        "selector_rows": rows,
        "state_hash_before": before,
        "state_hash_after": after,
        "formal_warmup_runs": 0,
        "formal_timed_runs": 0,
        "latency_gate_evaluated": False,
        "peak_memory_gate_evaluated": False,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "formal_efficiency_execution_authorized": False,
        "separate_formal_efficiency_execution_authorization_allowed_next": True,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
    }
    report = (
        "# Mamba v1.6 D6-A efficiency implementation artificial zero-step\n\n"
        "- 人工 descriptor：1 x 8192 x 27；D6 cases：0。\n"
        "- R0/R1 full-inference passes：各 1；均返回 32 个唯一索引。\n"
        "- 正式 warmup/timed runs：0 / 0。\n"
        "- latency 与 peak-memory gate：均未评估。\n"
        "- optimizer steps/model updates：0 / 0。\n"
        "- 下一步仅允许单独签发 formal efficiency execution authorization。\n"
    ).encode("utf-8")
    outputs = {
        "artificial_full_inference_probe.json": canonical_json({"rows": rows}),
        "efficiency_zero_step_receipt.json": canonical_json(receipt),
        "efficiency_zero_step_report_zh.md": report,
    }
    outputs["files.sha256"] = "".join(f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())).encode("ascii")
    write_locked(outputs, args.out_dir.resolve())
    print(f"[saved] immutable D6-A efficiency implementation zero-step: {args.out_dir}")
    print("[done] R0=1 R1=1 formal_warmup=0 formal_timed=0 optimizer_steps=0")
    print("[locked] formal_efficiency=false training=false seed1=false D6B=false")


if __name__ == "__main__":
    main()
