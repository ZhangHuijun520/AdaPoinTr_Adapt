#!/usr/bin/env python3
"""Verify a restored D6-A formal-efficiency frozen-negative archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


EXPECTED = {
    "candidate_manifest": "79aad71cc9da046b1e87fbe102ec0c454a0118890b3f93dd00fe2bc82c2d1285",
    "candidate_receipt": "372fb304305e85e6cf0c63ea08b5c7f62ee2a026492daf34f6d045ee957c71bf",
    "zero_manifest": "4e85572b1dd6cd044d6ce199623ab2583326a0c6916b4d3c01cdc641acb5f6b4",
    "zero_receipt": "60644275e58407e3b6b4e13abad2ef6c1490984ba31b782678f6963aded7408c",
    "result_manifest": "a448a65b1f83a9bde232395a18c491bc33b192ebd091a5a08b1a15be18cd35d3",
    "candidate_metrics": "452a31019ec528991543dc33e31c6d30cb28b56873309f8303d45020af559e94",
    "result_receipt": "3ef41b0e0c211935d2e0f900732dbf4d30b792e86c5144115d8850671a3d3303",
    "result_report": "dd6758baa8bc780397d315831978b7b5e085c44418d97a659e7ba75aca8f26d1",
}
EXPECTED_STATE = {
    "R0": "d65faa30fdb4e648c8dfc6f7fd2112fc2b01bd18a16a9ea7f84e5fd9f1d43642",
    "R1": "d3eedd80617538c1fa0278d8d87427c27b242fd38fe2950bd8bba6cd5455cd78",
}
EXPECTED_METRICS = {
    "R0": {
        "latency_ms_minimum": 0.3751087933778763,
        "latency_ms_median": 0.3978973254561424,
        "latency_ms_maximum": 0.6335880607366562,
        "peak_gpu_memory_bytes": 27304960,
    },
    "R1": {
        "latency_ms_minimum": 8.82061943411827,
        "latency_ms_median": 292.5087884068489,
        "latency_ms_maximum": 492.14704521000385,
        "peak_gpu_memory_bytes": 30400512,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path, name: str = "files.sha256") -> int:
    manifest = root / name
    if not manifest.is_file():
        raise RuntimeError(f"Missing manifest: {manifest}")
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, relative = line.split(maxsplit=1)
        path = root / relative.lstrip("*").replace("\\", "/")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
        count += 1
    return count


def require_hash(path: Path, expected: str) -> None:
    if not path.is_file() or sha256_file(path) != expected:
        raise RuntimeError(f"Frozen lineage mismatch: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()
    restore = args.restore_root.resolve()
    payload_count = verify_manifest(restore, "payload_manifest.sha256")
    repo = restore / "adapointr_work" / "PoinTr"
    logs = repo / "logs" / "mamba_v16_d6_contact_support"
    candidate = logs / "d6a_candidate_training_efficiency_protocol_v1"
    zero = logs / "d6a_efficiency_implementation_zero_step_v1"
    auth = logs / "d6a_formal_efficiency_execution_authorization_v1"
    preflight = logs / "d6a_formal_efficiency_execution_preflight_v1"
    result = logs / "d6a_formal_efficiency_result_v1"

    for root in (candidate, zero, auth, preflight, result):
        verify_manifest(root)
    require_hash(candidate / "files.sha256", EXPECTED["candidate_manifest"])
    require_hash(candidate / "protocol_lock_receipt.json", EXPECTED["candidate_receipt"])
    require_hash(zero / "files.sha256", EXPECTED["zero_manifest"])
    require_hash(zero / "efficiency_zero_step_receipt.json", EXPECTED["zero_receipt"])
    require_hash(result / "files.sha256", EXPECTED["result_manifest"])
    require_hash(result / "formal_efficiency_candidate_metrics.json", EXPECTED["candidate_metrics"])
    require_hash(result / "formal_efficiency_result_receipt.json", EXPECTED["result_receipt"])
    require_hash(result / "formal_efficiency_result_report_zh.md", EXPECTED["result_report"])

    auth_receipt_path = auth / "formal_efficiency_execution_authorization_receipt.json"
    auth_receipt = json.loads(auth_receipt_path.read_text(encoding="utf-8"))
    preflight_receipt = json.loads(
        (preflight / "authorization_preflight_receipt.json").read_text(encoding="utf-8")
    )
    receipt = json.loads(
        (result / "formal_efficiency_result_receipt.json").read_text(encoding="utf-8")
    )
    metrics_payload = json.loads(
        (result / "formal_efficiency_candidate_metrics.json").read_text(encoding="utf-8")
    )

    if not (
        auth_receipt.get("status") == "D6A_R0_R1_formal_efficiency_execution_authorized"
        and auth_receipt.get("execution_started") is False
        and auth_receipt.get("seed0_training_authorized") is False
        and auth_receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Formal-efficiency authorization semantics drifted")
    if not (
        preflight_receipt.get("status")
        == "D6A_R0_R1_formal_efficiency_authorization_preflight_passed"
        and preflight_receipt.get("authorization_receipt_sha256")
        == sha256_file(auth_receipt_path)
        and preflight_receipt.get("formal_warmup_runs") == 0
        and preflight_receipt.get("formal_timed_runs") == 0
        and preflight_receipt.get("optimizer_steps") == 0
        and preflight_receipt.get("model_updates") == 0
    ):
        raise RuntimeError("Formal-efficiency preflight semantics drifted")
    if not (
        receipt.get("status") == "D6A_formal_efficiency_gate_failed"
        and receipt.get("candidate_order") == ["R0", "R1"]
        and receipt.get("latency_gate_passed") is False
        and receipt.get("peak_memory_gate_passed") is False
        and receipt.get("all_efficiency_gates_passed") is False
        and receipt.get("optimizer_constructed") is False
        and receipt.get("optimizer_steps") == 0
        and receipt.get("model_updates") == 0
        and receipt.get("D6_cases_accessed") == 0
        and receipt.get("seed0_training_authorized") is False
        and receipt.get("seed1_training_authorized") is False
        and receipt.get("proposal_confirmation_accessed") is False
        and receipt.get("D6B_authorized") is False
        and receipt.get("candidate_selection_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
        and receipt.get("next_step") == "freeze_negative_result_and_stop_before_training"
        and receipt.get("authorization_receipt_sha256") == sha256_file(auth_receipt_path)
        and receipt.get("preflight_manifest_sha256") == sha256_file(preflight / "files.sha256")
    ):
        raise RuntimeError("Formal-efficiency frozen-negative semantics drifted")

    if not (
        math.isclose(receipt["R1_to_R0_latency_ratio"], 735.1363522524863, rel_tol=0, abs_tol=1e-12)
        and math.isclose(receipt["R1_to_R0_peak_memory_ratio"], 1.1133695855991, rel_tol=0, abs_tol=1e-12)
        and receipt["latency_ratio_maximum"] == 1.15
        and receipt["peak_memory_ratio_maximum"] == 1.10
    ):
        raise RuntimeError("Formal-efficiency ratio or threshold drifted")

    rows = metrics_payload.get("rows", [])
    if [row.get("candidate") for row in rows] != ["R0", "R1"]:
        raise RuntimeError("Candidate result ordering drifted")
    for row in rows:
        candidate_name = row["candidate"]
        expected = EXPECTED_METRICS[candidate_name]
        selected = row.get("selected_indices", [])
        if not (
            row.get("warmup_runs") == 10
            and row.get("timed_runs") == 50
            and len(selected) == 32
            and len(set(selected)) == 32
            and all(isinstance(index, int) and 0 <= index < 8192 for index in selected)
            and row.get("state_sha256") == EXPECTED_STATE[candidate_name]
            and row.get("peak_gpu_memory_bytes") == expected["peak_gpu_memory_bytes"]
            and all(
                math.isclose(row[key], value, rel_tol=0, abs_tol=1e-12)
                for key, value in expected.items()
                if key != "peak_gpu_memory_bytes"
            )
        ):
            raise RuntimeError(f"Frozen candidate metrics drifted: {candidate_name}")

    forbidden_suffixes = {".pth", ".pt", ".ckpt", ".npz", ".stl"}
    for path in restore.rglob("*"):
        if path.is_file() and path.suffix.lower() in forbidden_suffixes:
            raise RuntimeError(f"Archive contains forbidden model/data payload: {path}")

    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] authorization, zero-count preflight and formal result lineage match")
    print("[ok] R0/R1 latency, memory and frozen-negative gates match")
    print("[excluded] checkpoints, NPZ, STL and sealed data")
    print("[locked] rerun=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
