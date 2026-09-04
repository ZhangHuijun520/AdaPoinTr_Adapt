#!/usr/bin/env python3
"""Execute the authorized frozen D6-A formal-efficiency benchmark once."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.verify_mamba_v16_d6a_formal_efficiency_authorization import verify_authorization  # noqa: E402
from utils.mamba_d5a_proposal import D5V1ContextHead  # noqa: E402
from utils.mamba_d6a_efficiency import (  # noqa: E402
    LATENCY_RATIO_MAXIMUM,
    PEAK_MEMORY_RATIO_MAXIMUM,
    benchmark_candidate,
)
from utils.mamba_d6a_slot_allocator import D6R1SlotAllocator  # noqa: E402


VERSION = "mamba-v16-d6a-formal-efficiency-result-v1"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_state_hash(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def verify_preflight(root: Path, authorization_hash: str) -> dict[str, Any]:
    manifest = root / "files.sha256"
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Preflight artifact mismatch: {path}")
    receipt = json.loads((root / "authorization_preflight_receipt.json").read_text(encoding="utf-8"))
    if not (
        receipt.get("status") == "D6A_R0_R1_formal_efficiency_authorization_preflight_passed"
        and receipt.get("authorization_receipt_sha256") == authorization_hash
        and receipt.get("formal_warmup_runs") == 0
        and receipt.get("formal_timed_runs") == 0
        and receipt.get("latency_gate_evaluated") is False
        and receipt.get("peak_memory_gate_evaluated") is False
        and receipt.get("formal_efficiency_execution_authorized") is True
        and receipt.get("seed0_training_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Unsafe formal-efficiency preflight semantics")
    return receipt


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        raise RuntimeError(f"Formal-efficiency result already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            (working / name).write_bytes(payload)
        manifest = "".join(
            f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
            for name, payload in sorted(outputs.items())
        ).encode("ascii")
        (working / "files.sha256").write_bytes(manifest)
        working.replace(output_dir)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--preflight_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    authorization = verify_authorization(args.config_dir, args.authorization_dir)
    auth_receipt = args.authorization_dir / "formal_efficiency_execution_authorization_receipt.json"
    auth_hash = sha256_file(auth_receipt)
    preflight = verify_preflight(args.preflight_dir.resolve(), auth_hash)
    if not torch.cuda.is_available():
        raise RuntimeError("D6-A formal efficiency requires CUDA")

    config_path = args.config_dir / authorization["runtime_config"]["name"]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    expected_states = config["expected_initial_state_sha256"]
    device = torch.device("cuda:0")
    torch.manual_seed(160610)
    torch.cuda.manual_seed_all(160610)
    generator = torch.Generator(device="cpu").manual_seed(160610)
    descriptors = torch.randn(1, 8192, 27, generator=generator, dtype=torch.float32).to(device)

    rows = []
    constructors = {"R0": D5V1ContextHead, "R1": D6R1SlotAllocator}
    for candidate in ("R0", "R1"):
        torch.cuda.empty_cache()
        model = constructors[candidate]().to(device).eval()
        before = tensor_state_hash(model)
        if before != expected_states[candidate]:
            raise RuntimeError(f"{candidate} initial state does not match frozen zero-step")
        measured = benchmark_candidate(candidate, model, descriptors)
        after = tensor_state_hash(model)
        if before != after:
            raise RuntimeError(f"{candidate} formal benchmark changed model state")
        measured["state_sha256"] = before
        rows.append(measured)
        del model
        torch.cuda.empty_cache()

    by_candidate = {row["candidate"]: row for row in rows}
    latency_ratio = by_candidate["R1"]["latency_ms_median"] / by_candidate["R0"]["latency_ms_median"]
    memory_ratio = by_candidate["R1"]["peak_gpu_memory_bytes"] / by_candidate["R0"]["peak_gpu_memory_bytes"]
    latency_passed = latency_ratio <= LATENCY_RATIO_MAXIMUM
    memory_passed = memory_ratio <= PEAK_MEMORY_RATIO_MAXIMUM
    passed = latency_passed and memory_passed
    status = "D6A_formal_efficiency_gate_passed" if passed else "D6A_formal_efficiency_gate_failed"
    receipt = {
        "result_version": VERSION,
        "status": status,
        "authorization_receipt_sha256": auth_hash,
        "preflight_manifest_sha256": sha256_file(args.preflight_dir / "files.sha256"),
        "cuda_device_name": torch.cuda.get_device_name(device),
        "torch_version": torch.__version__,
        "candidate_order": ["R0", "R1"],
        "descriptor_seed": 160610,
        "candidate_metrics": rows,
        "R1_to_R0_latency_ratio": latency_ratio,
        "R1_to_R0_peak_memory_ratio": memory_ratio,
        "latency_ratio_maximum": LATENCY_RATIO_MAXIMUM,
        "peak_memory_ratio_maximum": PEAK_MEMORY_RATIO_MAXIMUM,
        "latency_gate_passed": latency_passed,
        "peak_memory_gate_passed": memory_passed,
        "all_efficiency_gates_passed": passed,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_accessed": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": (
            "freeze_positive_result_then_separate_seed0_training_authorization"
            if passed else "freeze_negative_result_and_stop_before_training"
        ),
    }
    report = (
        "# Mamba v1.6 D6-A formal efficiency 冻结结果\n\n"
        f"- R0 median latency：{by_candidate['R0']['latency_ms_median']:.9f} ms。\n"
        f"- R1 median latency：{by_candidate['R1']['latency_ms_median']:.9f} ms。\n"
        f"- R1/R0 latency ratio：{latency_ratio:.9f}；gate passed：`{latency_passed}`。\n"
        f"- R0 peak CUDA memory：{by_candidate['R0']['peak_gpu_memory_bytes']} bytes。\n"
        f"- R1 peak CUDA memory：{by_candidate['R1']['peak_gpu_memory_bytes']} bytes。\n"
        f"- R1/R0 peak-memory ratio：{memory_ratio:.9f}；gate passed：`{memory_passed}`。\n"
        f"- 两项效率门控同时通过：`{passed}`。\n"
        "- optimizer steps/model updates：0 / 0；D6 cases：0。\n"
        "- 本步骤不授权或启动训练、seed-1、confirmation、D6-B 或 selection。\n"
    ).encode("utf-8")
    outputs = {
        "formal_efficiency_candidate_metrics.json": canonical_json({"rows": rows}),
        "formal_efficiency_result_receipt.json": canonical_json(receipt),
        "formal_efficiency_result_report_zh.md": report,
    }
    write_locked(outputs, args.output_dir.resolve())
    print(f"[saved] immutable D6-A formal-efficiency result: {args.output_dir.resolve()}")
    print(f"[gate] latency_ratio={latency_ratio:.9f} passed={latency_passed}")
    print(f"[gate] peak_memory_ratio={memory_ratio:.9f} passed={memory_passed}")
    print(f"[gate] all_passed={passed}")
    print("[locked] training=false seed1=false confirmation=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
