#!/usr/bin/env python3
"""Verify a restored D6-A efficiency implementation zero-step archive."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "lock_manifest": "79aad71cc9da046b1e87fbe102ec0c454a0118890b3f93dd00fe2bc82c2d1285",
    "lock_receipt": "372fb304305e85e6cf0c63ea08b5c7f62ee2a026492daf34f6d045ee957c71bf",
    "zero_manifest": "4e85572b1dd6cd044d6ce199623ab2583326a0c6916b4d3c01cdc641acb5f6b4",
    "zero_receipt": "60644275e58407e3b6b4e13abad2ef6c1490984ba31b782678f6963aded7408c",
    "probe": "85eebf33b7c6d26c106e421f97ab231940834c16659cdd08a7f496ad95454bc5",
    "zero_report": "5f2df5f94e5559dcb1784587899c8eef2a2d609c3851c735e78ed4d3d2c6814c",
    "parent_normalization": "e190c96ed46073e075cf092897576a10851cfee9b6fc66e85d7c367726244576",
    "lock_repair": "4edc1161f3c8ba1e28bac764364146eec7faea13a46c4939babb65ff73cb136c",
    "overlay_normalization": "3e4309a29b65a8bad287a81d702e49690e42b2691d1057ee921d37b040f57663",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path, manifest_name: str) -> int:
    manifest = root / manifest_name
    if not manifest.is_file():
        raise RuntimeError(f"Missing manifest: {manifest}")
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        relative = name.lstrip("*").replace("\\", "/")
        path = root / relative
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()
    restore = args.restore_root.resolve()
    repo = restore / "adapointr_work" / "PoinTr"
    logs = repo / "logs" / "mamba_v16_d6_contact_support"
    lock = logs / "d6a_candidate_training_efficiency_protocol_v1"
    zero = logs / "d6a_efficiency_implementation_zero_step_v1"

    payload_count = verify_manifest(restore, "payload_manifest.sha256")
    verify_manifest(lock, "files.sha256")
    verify_manifest(zero, "files.sha256")

    paths = {
        "lock_manifest": lock / "files.sha256",
        "lock_receipt": lock / "protocol_lock_receipt.json",
        "zero_manifest": zero / "files.sha256",
        "zero_receipt": zero / "efficiency_zero_step_receipt.json",
        "probe": zero / "artificial_full_inference_probe.json",
        "zero_report": zero / "efficiency_zero_step_report_zh.md",
        "parent_normalization": logs / "d6a_candidate_training_parent_normalization_v1" / "normalization_receipt.json",
        "lock_repair": logs / "d6a_candidate_protocol_lock_lf_repair_v1" / "lock_lf_repair_receipt.json",
        "overlay_normalization": logs / "d6a_efficiency_zero_step_overlay_normalization_v1" / "normalization_receipt.json",
    }
    for key, path in paths.items():
        if not path.is_file() or sha256_file(path) != EXPECTED[key]:
            raise RuntimeError(f"Frozen lineage mismatch: {path}")

    lock_receipt = json.loads(paths["lock_receipt"].read_text(encoding="utf-8"))
    zero_receipt = json.loads(paths["zero_receipt"].read_text(encoding="utf-8"))
    if (
        lock_receipt["status"] != "D6A_candidate_training_efficiency_protocol_frozen_non_runnable"
        or lock_receipt["protocol_sha256"] != "5060c7700e53d42a4100ebeacf35f662accd58c585fc82af1443fafffb17fc3e"
        or lock_receipt["optimizer_steps"] != 0
        or lock_receipt["efficiency_execution_authorized"] is not False
    ):
        raise RuntimeError("Candidate protocol lock semantics drifted")
    if (
        zero_receipt["status"] != "D6A_R0_R1_full_inference_efficiency_artificial_zero_step_passed"
        or zero_receipt["full_inference_passes"] != {"R0": 1, "R1": 1}
        or zero_receipt["formal_warmup_runs"] != 0
        or zero_receipt["formal_timed_runs"] != 0
        or zero_receipt["latency_gate_evaluated"] is not False
        or zero_receipt["peak_memory_gate_evaluated"] is not False
        or zero_receipt["optimizer_steps"] != 0
        or zero_receipt["model_updates"] != 0
        or zero_receipt["state_hash_before"] != zero_receipt["state_hash_after"]
        or zero_receipt["formal_efficiency_execution_authorized"] is not False
        or zero_receipt["seed0_training_authorized"] is not False
        or zero_receipt["protected_or_sealed_data_accessed"] is not False
    ):
        raise RuntimeError("Efficiency zero-step semantics drifted")
    rows = zero_receipt.get("selector_rows", [])
    if len(rows) != 2 or {row["candidate"] for row in rows} != {"R0", "R1"}:
        raise RuntimeError("Artificial probe candidate pairing drifted")
    if any(row["selected_count"] != 32 or row["selected_unique"] != 32 for row in rows):
        raise RuntimeError("Artificial probe selector contract drifted")

    forbidden_suffixes = {".npz", ".stl", ".pth", ".pt", ".ckpt"}
    for line in (restore / "payload_manifest.sha256").read_text(encoding="ascii").splitlines():
        _, name = line.split(maxsplit=1)
        relative = name.lstrip("*").replace("\\", "/").lower()
        if Path(relative).suffix in forbidden_suffixes or "/cases/" in relative:
            raise RuntimeError(f"Forbidden model/data payload: {relative}")

    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] canonical candidate lock and artificial full-inference zero-step match")
    print("[excluded] NPZ, STL, checkpoints and sealed data")
    print("[locked] formal_efficiency=false training=false seed1=false D6B=false")


if __name__ == "__main__":
    main()
