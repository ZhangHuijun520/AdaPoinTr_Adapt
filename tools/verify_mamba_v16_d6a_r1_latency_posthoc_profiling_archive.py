#!/usr/bin/env python3
"""Verify a restored D6-A R1 latency profiling frozen-result archive."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path, PurePosixPath


EXPECTED_RESULT = {
    "files.sha256": "8c0fb421188abe6efdd0081013eb451cb87bf5a3768f9279b7bf16678709f385",
    "posthoc_profiling_receipt.json": "ba4382e9af597189ec75ff3ea12175d3a4add8ec9894e02ccab3301d6469a0d9",
    "posthoc_profiling_report_zh.md": "772e080e644d377a865e6cd40628a5a82550a639c8d01a3f2514c9c2fe7b173d",
    "r1_assignment_stage_metrics.csv": "99d6601c0994d8966412f0b23f29f4bf80f393ec569f663c67830c670c3dfe12",
    "r1_exact_path_stage_metrics.csv": "2cd82f348c910d6b699b759661c1fcf99a064802aba4d02917d0e2880a40f327",
    "r1_latency_attribution_summary.json": "b5f1ca7f37fde4c06a8564700799b2e32ae05b01842dd399047415f7d0607c37",
    "r1_operator_summary.csv": "90e9d7f75032e3f170b89d05af5f03e3756546f4ea49e06f35d4715631b8fc4e",
    "r1_torch_profiler_trace.json.gz": "98503b3721e6973dc921ad54f70942442a97f423461210a68a6065d2823ef03e",
}
EXPECTED_FREEZE = {
    "files.sha256": "c2fbcc4c6b894201cd5111877b9df6d66d0b0050f99365fb1751cedab633e2a4",
    "artifact_inventory.tsv": "698551249e7983fb98a42ad7fd7bc146b229c612013dded274d6a97e3d6d4c1f",
    "profiling_result_freeze_receipt.json": "4156c7a0fb75c7d4f4108bf2d3e14b9483a415ba21e8c56ff2b11c8a66f02501",
}
EXPECTED_PROTOCOL_LOCK = {
    "files.sha256": "259bc0e1dcbffda71d2a343ae090240f4a07ba40c2b2138a5cc6bb31ebc871b7",
    "profiling_protocol_v1.json": "b93200400b48dc62f03c7703f3434d28fa76e3c88e4975e6562e28e340fdcea1",
    "protocol_lock_receipt.json": "b074c94acb0b1e73228c030c7e8f50562d48d929f919dad5dfb6e3a35ad9af05",
}
EXPECTED_STATE = "d3eedd80617538c1fa0278d8d87427c27b242fd38fe2950bd8bba6cd5455cd78"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_hashes(root: Path, expected: dict[str, str]) -> None:
    for name, wanted in expected.items():
        path = root / name
        require(path.is_file() and sha256_file(path) == wanted, f"Frozen hash mismatch: {path}")


def manifest_entries(manifest: Path, root: Path) -> int:
    require(manifest.is_file(), f"Missing manifest: {manifest}")
    count = 0
    resolved_root = root.resolve()
    for line in manifest.read_text(encoding="ascii").splitlines():
        wanted, relative = line.split(maxsplit=1)
        path = (root / relative.lstrip("*").replace("\\", "/")).resolve()
        require(path == resolved_root or resolved_root in path.parents, f"Unsafe manifest path: {path}")
        require(path.is_file() and sha256_file(path) == wanted.lower(), f"Manifest mismatch: {path}")
        count += 1
    return count


def verify_inventory(repo: Path, freeze: Path) -> int:
    rows = freeze.joinpath("artifact_inventory.tsv").read_text(encoding="ascii").splitlines()
    require(len(rows) == 57, f"Unexpected inventory row count: {len(rows)}")
    seen: set[str] = set()
    for line in rows:
        wanted, size_text, relative = line.split("\t", 2)
        posix = PurePosixPath(relative)
        require(not posix.is_absolute() and ".." not in posix.parts, f"Unsafe inventory path: {relative}")
        require(relative not in seen, f"Duplicate inventory path: {relative}")
        seen.add(relative)
        path = repo.joinpath(*posix.parts)
        require(path.is_file(), f"Missing inventoried artifact: {path}")
        require(path.stat().st_size == int(size_text), f"Inventory size mismatch: {path}")
        require(sha256_file(path) == wanted, f"Inventory hash mismatch: {path}")
    return len(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()
    restore = args.restore_root.resolve()
    payload_count = manifest_entries(restore / "payload_manifest.sha256", restore)
    repo = restore / "adapointr_work" / "PoinTr"
    logs = repo / "logs" / "mamba_v16_d6_contact_support"
    protocol = logs / "d6a_r1_latency_bottleneck_posthoc_profiling_protocol_v1"
    auth = logs / "d6a_r1_latency_posthoc_profiling_execution_authorization_v1"
    preflight = logs / "d6a_r1_latency_posthoc_profiling_execution_preflight_v1"
    prelaunch = logs / "d6a_r1_latency_posthoc_profiling_prelaunch_lock_v1"
    result = logs / "d6a_r1_latency_posthoc_profiling_result_v1"
    freeze = logs / "d6a_r1_latency_posthoc_profiling_result_freeze_v1"
    normalization = logs / "d6a_r1_latency_bottleneck_posthoc_profiling_parent_lf_normalization_v1"
    backup = logs / "d6a_r1_latency_bottleneck_posthoc_profiling_protocol_crlf_transport_backup_v1"

    for root in (protocol, auth, preflight, prelaunch, result, freeze, normalization, backup):
        require(root.is_dir(), f"Missing frozen directory: {root}")

    manifest_entries(protocol / "files.sha256", protocol)
    manifest_entries(auth / "files.sha256", auth)
    manifest_entries(preflight / "files.sha256", preflight)
    manifest_entries(result / "files.sha256", result)
    manifest_entries(freeze / "files.sha256", freeze)
    manifest_entries(normalization / "normalization_receipt.json.sha256", normalization)
    manifest_entries(prelaunch / "key_artifacts.sha256", repo)
    manifest_entries(prelaunch / "files.sha256", repo)

    require_hashes(protocol, EXPECTED_PROTOCOL_LOCK)
    require_hashes(result, EXPECTED_RESULT)
    require_hashes(freeze, EXPECTED_FREEZE)
    inventory_count = verify_inventory(repo, freeze)

    auth_receipt_path = auth / "profiling_execution_authorization_receipt.json"
    auth_receipt = json.loads(auth_receipt_path.read_text(encoding="utf-8"))
    preflight_receipt = json.loads((preflight / "authorization_preflight_receipt.json").read_text(encoding="utf-8"))
    prelaunch_receipt = json.loads((prelaunch / "prelaunch_receipt.json").read_text(encoding="utf-8"))
    receipt = json.loads((result / "posthoc_profiling_receipt.json").read_text(encoding="utf-8"))
    attribution = json.loads((result / "r1_latency_attribution_summary.json").read_text(encoding="utf-8"))
    freeze_receipt = json.loads((freeze / "profiling_result_freeze_receipt.json").read_text(encoding="utf-8"))

    require(
        auth_receipt.get("status") == "D6A_R1_latency_posthoc_profiling_execution_authorized"
        and auth_receipt.get("execution_started") is False
        and auth_receipt.get("optimizer_steps") == auth_receipt.get("model_updates") == 0
        and auth_receipt.get("D6_cases_accessed") == 0,
        "Profiling authorization semantics drifted",
    )
    require(
        preflight_receipt.get("status") == "D6A_R1_latency_posthoc_profiling_authorization_preflight_passed"
        and preflight_receipt.get("profiling_blocks") == 0
        and preflight_receipt.get("timed_observations") == 0
        and preflight_receipt.get("torch_profiler_traces") == 0
        and preflight_receipt.get("optimizer_steps") == preflight_receipt.get("model_updates") == 0
        and preflight_receipt.get("D6_cases_accessed") == 0,
        "Profiling preflight semantics drifted",
    )
    require(
        prelaunch_receipt.get("status") == "D6A_R1_latency_posthoc_profiling_prelaunch_frozen"
        and prelaunch_receipt.get("profiling_started") is False
        and prelaunch_receipt.get("training_authorized") is False
        and prelaunch_receipt.get("D6_cases_accessed") == 0,
        "Prelaunch freeze semantics drifted",
    )
    require(
        receipt.get("status") == "D6A_R1_latency_posthoc_profiling_complete_observation_only"
        and receipt.get("candidate") == "R1"
        and receipt.get("blocks") == 3
        and receipt.get("timed_runs_per_block") == 20
        and receipt.get("timed_observations") == 60
        and receipt.get("torch_profiler_traces") == 1
        and receipt.get("selected_indices_equal_reference") is True
        and receipt.get("state_hash_before") == receipt.get("state_hash_after") == EXPECTED_STATE
        and receipt.get("formal_gate_evaluated") is False
        and receipt.get("formal_gate_changed") is False
        and receipt.get("formal_gate_rerun") is False
        and receipt.get("optimizer_constructed") is False
        and receipt.get("optimizer_steps") == receipt.get("model_updates") == 0
        and receipt.get("D6_cases_accessed") == 0
        and receipt.get("seed0_training_authorized") is False
        and receipt.get("seed1_training_authorized") is False
        and receipt.get("D6B_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
        and receipt.get("authorization_receipt_sha256") == sha256_file(auth_receipt_path)
        and receipt.get("preflight_manifest_sha256") == sha256_file(preflight / "files.sha256"),
        "Frozen profiling result semantics drifted",
    )

    selected = receipt.get("selected_indices", [])
    require(len(selected) == len(set(selected)) == 32, "Selected-index contract drifted")
    require(all(isinstance(index, int) and 0 <= index < 8192 for index in selected), "Invalid selected index")
    observed = receipt["attribution"]
    require(
        observed.get("classification") == "scipy_global_assignment_dominant"
        and observed.get("leading_category") == "scipy_global_assignment"
        and math.isclose(observed.get("leading_share"), 0.7087436968007994, rel_tol=0, abs_tol=1e-15)
        and observed.get("causal_claim_authorized") is False
        and observed.get("optimized_alternative_benchmark_authorized") is False,
        "Latency attribution drifted",
    )
    require(attribution.get("attribution") == observed, "Attribution summary and receipt disagree")

    require(
        freeze_receipt.get("status") == "D6A_R1_latency_posthoc_profiling_result_frozen"
        and freeze_receipt.get("artifact_count") == 57
        and freeze_receipt.get("artifact_inventory_sha256") == EXPECTED_FREEZE["artifact_inventory.tsv"]
        and freeze_receipt.get("state_unchanged") is True
        and freeze_receipt.get("formal_gate_changed") is False
        and freeze_receipt.get("training_authorized") is False
        and freeze_receipt.get("D6_cases_accessed") == 0,
        "Result-freeze receipt drifted",
    )

    require(len(read_csv(result / "r1_exact_path_stage_metrics.csv")) == 60, "Exact-path row count drifted")
    require(len(read_csv(result / "r1_assignment_stage_metrics.csv")) == 60, "Assignment row count drifted")
    require(len(read_csv(result / "r1_operator_summary.csv")) > 0, "Operator summary is empty")
    with gzip.open(result / "r1_torch_profiler_trace.json.gz", "rt", encoding="utf-8") as handle:
        trace = json.load(handle)
    require(isinstance(trace.get("traceEvents"), list) and trace["traceEvents"], "Profiler trace is empty")

    forbidden_suffixes = {".pth", ".pt", ".ckpt", ".npz", ".stl"}
    for path in restore.rglob("*"):
        if path.is_file() and path.suffix.lower() in forbidden_suffixes:
            raise RuntimeError(f"Archive contains forbidden model/data payload: {path}")

    print(f"[ok] payload manifest verified: {payload_count} files")
    print(f"[ok] frozen server inventory verified: {inventory_count} artifacts")
    print("[ok] R1 60-run metrics, trace, state and selected indices match")
    print("[ok] SciPy assignment 70.8744% descriptive attribution matches")
    print("[excluded] checkpoints, NPZ, STL and sealed data")
    print("[locked] optimization=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
