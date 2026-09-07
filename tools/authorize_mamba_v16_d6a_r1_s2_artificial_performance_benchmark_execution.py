#!/usr/bin/env python3
"""Authorize one frozen-suite D6-A R1 S2 artificial performance benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_r1_s2_artificial_performance_benchmark_execution_authorization_protocol_v1.json"
REPORT = ROOT / "docs" / "mamba_v16_d6a_r1_s2_artificial_performance_benchmark_execution_authorization_preregistered_protocol_zh.md"
VERSION = "mamba-v16-d6a-r1-s2-artificial-performance-benchmark-execution-authorization-v1"

EXPECTED_LOCK = {
    "files.sha256": "1887c591137aacb67615510defa2be816cf5c71f4637d12f390121c328b03f9a",
    "benchmark_contract.json": "841dfcea14b41c68294526080b6bf13ab311ddabaa1311b8739315e9fda52ecd",
    "benchmark_execution.template.json": "74ca7f0a03c32b9adfff2008db4958807064ea5f4f2eac34fcc8bdc895149a58",
    "protocol_lock_receipt.json": "c553795d6c4f3995b062e755c7dde7a53c646266c3f07c72d2cc5ac4de24088b",
    "protocol_lock_report_zh.md": "81e07348c7f41e7d8ef759d8d2432f12361c0d7634f1e747cd8feca41af97b3a",
    "protocol_v1.json": "0542199bf2b05a82c3197bd156e5bc3269a118acf676e356ebdc306effa9ea04",
    "synthetic_suite_binding.json": "6da4e2100f9a682c7364bdc01b680b2d796644d2c7a4ccc3f41be22f9f9118f3",
}
EXPECTED_RESULT = {
    "files.sha256": "5713a4fa4307cd0a68c8d429848b6055e2b0d888c2eea0c5e39cd9d965fcbeb6",
    "s2_artificial_equivalence_metrics.csv": "be1ea8643a169293cf258bd39473557f8a40f72da31427b84cfc5fcc85677244",
    "s2_certification_routing_metrics.csv": "182654d18b1c428f80f4f796449c35eafe17d782e11238fa7856811a302a4cc1",
    "s2_family_summary.csv": "102a7c4d3b5c0dff5410f17a3f6d88c14b2d755267d9dde2eacb0ed2c7c79fd0",
    "s2_artificial_zero_step_summary.json": "a3b9c5ede525f3b29e638abdc55f97c7367d8b760fb34d829d0472b3093813d1",
    "s2_artificial_zero_step_receipt.json": "85d8a0946504bb02d471b0087df7d6a8ccb929c01dc40df031088c6143a9c061",
    "s2_artificial_zero_step_report_zh.md": "a166d0fb514716d2e71477dc064243a3e0623a85c93477127f7f0d1d50e4df7b",
}
SOURCE_PATHS = {
    "S2_shadow": "utils/mamba_d6a_r1_s2_certified_fast_path.py",
    "S1_support": "utils/mamba_d6a_r1_s1_exact_assignment.py",
    "S1_artificial_suite": "tools/preflight_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py",
    "S2_zero_step_reference": "tools/preflight_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py",
}
EXPECTED_SOURCE_LF = {
    "S2_shadow": "4cb4e5bd2c8c9cb7ce8a4e2b1d501e85631553b6b27ecc10079788fcd0189bb6",
    "S1_support": "ba4072e5ac23679c9cf6c186eb7aded5d761b59160e2c9c406ddd052516550cd",
    "S1_artificial_suite": "4d65e34e0ace92ca2b9ec68d43fc889765c30debd760cc57f444eb79b5aabd85",
    "S2_zero_step_reference": "b89ddad702d9828ebfab7dabdce952a4fbb4fd19f823ed5c0422bb58473aa4f1",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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


def manifest_bytes(files: Mapping[str, bytes]) -> bytes:
    return "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(files.items())
    ).encode("ascii")


def verify_manifest(root: Path) -> int:
    manifest = root / "files.sha256"
    require(manifest.is_file(), f"Missing manifest: {manifest}")
    resolved = root.resolve()
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        wanted, relative = line.split(maxsplit=1)
        posix = PurePosixPath(relative.lstrip("*"))
        require(not posix.is_absolute() and ".." not in posix.parts, f"Unsafe manifest path: {relative}")
        path = root.joinpath(*posix.parts).resolve()
        require(path == resolved or resolved in path.parents, f"Manifest escaped root: {path}")
        require(path.is_file() and sha256_file(path) == wanted.lower(), f"Manifest mismatch: {path}")
        count += 1
    return count


def verify_hashes(root: Path, expected: Mapping[str, str]) -> None:
    for name, wanted in expected.items():
        path = root / name
        require(path.is_file() and sha256_file(path) == wanted, f"Frozen lineage drifted: {path}")


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    require(protocol["protocol_id"] == VERSION, "Authorization protocol id drifted")
    require(protocol["status"] == "preregistered_after_frozen_benchmark_protocol_before_authorization_preflight_or_execution", "Authorization status drifted")
    parent = protocol["frozen_parent"]
    require(parent["protocol_lock_status"] == "D6A_R1_S2_artificial_performance_benchmark_protocol_frozen_non_runnable", "Parent status drifted")
    require(parent["protocol_lock_hashes"] == EXPECTED_LOCK, "Parent lock hashes drifted")
    require(parent["S2_result_status"] == "D6A_R1_S2_certified_fast_path_artificial_zero_step_passed", "S2 result status drifted")
    require(parent["S2_result_manifest_sha256"] == EXPECTED_RESULT["files.sha256"], "S2 result manifest drifted")
    require(parent["cases"] == 168 and parent["certified_fast_path_cases"] == 96 and parent["fallback_s0_cases"] == 72, "S2 result counts drifted")
    require(parent["false_positive_certificates"] == 0, "False-positive result drifted")

    binding = protocol["implementation_binding"]
    require(binding["LF_normalized_sha256"] == EXPECTED_SOURCE_LF, "Implementation binding drifted")
    require(binding["S0_or_S2_change_authorized"] is False and binding["full_D2H_retained"] is True, "Implementation change enabled")
    require(binding["source_hashes_recorded_in_authorization_receipt"] is True, "Raw source binding removed")

    runtime = protocol["runtime"]
    require(runtime["candidates"] == ["S0", "S2"], "Candidate order drifted")
    require(runtime["data"] == "same_frozen_168_artificial_assignment_matrices_only", "Data boundary drifted")
    require(runtime["pre_timing_correctness_replay_cases"] == runtime["cases_per_block"] == 168, "Case count drifted")
    require(runtime["expected_routes"] == {"certified_fast_path": 96, "fallback_s0": 72}, "Route counts drifted")
    require(runtime["expected_fallback_reasons"] == {"cutoff_tie_or_near_tie": 32, "global_optimum_not_certified_unique": 40}, "Fallback reasons drifted")
    require(runtime["warmup_anchor_families"] == 7 and runtime["warmup_rounds"] == 2, "Warmup design drifted")
    require(runtime["warmup_calls_per_candidate"] == 14 and runtime["warmup_calls_total"] == 28, "Warmup count drifted")
    require(runtime["measurement_blocks"] == 3 and runtime["timed_calls_per_candidate"] == 504 and runtime["timed_observation_rows"] == 1008, "Measurement count drifted")
    require("mod_2" in runtime["paired_order_rule"], "Paired ordering drifted")
    require(runtime["CUDA_sync_before_and_after_each_timed_call"] is True, "CUDA synchronization removed")
    require(runtime["clock"] == "time.perf_counter_ns", "Clock drifted")
    require(runtime["outlier_removal"] == "none" and runtime["retry_on_slow_observation"] is False, "Observation filtering enabled")
    require(runtime["torch_profiler_traces"] == 0 and set(runtime["CPU_threads"].values()) == {1}, "Runtime controls drifted")

    preflight = protocol["authorization_preflight"]
    require(preflight["CUDA_required"] is True and preflight["probe_family"] == "independent_normal" and preflight["probe_seed"] == 160610, "Preflight probe drifted")
    require(preflight["S0_calls"] == preflight["S2_calls"] == 1 and preflight["exact_outputs_required"] is True, "Preflight equivalence drifted")
    require(preflight["expected_S2_route"] == "certified_fast_path", "Preflight route drifted")
    for key in ("warmup_calls", "timed_calls", "measurement_blocks", "torch_profiler_traces", "D6_cases_accessed"):
        require(preflight[key] == 0, f"Preflight zero-count boundary drifted: {key}")

    gate = protocol["performance_gate"]
    require(gate["timed_observation_rows_required"] == 1008, "Gate row count drifted")
    require(gate["median_of_3_overall_block_ratios_maximum"] == 0.9, "Overall gate drifted")
    require(gate["each_overall_block_ratio_must_be_strictly_less_than"] == 1.0, "Block gate drifted")
    require(gate["aggregate_fast_path_ratio_maximum"] == 0.5 and gate["aggregate_fallback_ratio_maximum"] == 1.25, "Route gates drifted")
    require(gate["all_conditions_required"] is True and gate["formal_R0_denominator_used"] is False and gate["formal_efficiency_thresholds_evaluated"] is False, "Formal gate imported")

    result = protocol["result_contract"]
    require(result["negative_result_frozen_on_any_failure"] is True, "Negative freeze removed")
    for key in ("result_can_authorize_production_change", "result_can_authorize_formal_efficiency_rerun", "result_can_authorize_training"):
        require(result[key] is False, f"Result permission enabled: {key}")

    boundary = protocol["permission_boundary"]
    require(boundary["S2_artificial_performance_benchmark_execution_authorized"] is True, "Benchmark authorization missing")
    require(boundary["authorization_preflight_authorized"] is True and boundary["execution_started"] is False, "Authorization state drifted")
    for key, value in boundary.items():
        if key not in {"S2_artificial_performance_benchmark_execution_authorized", "authorization_preflight_authorized"}:
            require(value is False, f"Forbidden permission enabled: {key}")


def read_cases(result_dir: Path) -> list[dict[str, Any]]:
    with (result_dir / "s2_certification_routing_metrics.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 168, "Frozen routing table row count drifted")
    cases = []
    for expected_index, row in enumerate(rows):
        require(int(row["case_index"]) == expected_index, "Frozen case order drifted")
        require(row["route_valid"].lower() == "true" and row["false_positive_certificate"].lower() == "false", "Frozen route validity drifted")
        cases.append({
            "case_index": expected_index,
            "family": row["family"],
            "seed": int(row["seed"]),
            "expected_route": row["route"],
            "expected_fallback_reason": row["fallback_reason"],
        })
    require(Counter(case["expected_route"] for case in cases) == Counter({"certified_fast_path": 96, "fallback_s0": 72}), "Frozen route counts drifted")
    require(Counter(case["expected_fallback_reason"] for case in cases if case["expected_route"] == "fallback_s0") == Counter({"cutoff_tie_or_near_tie": 32, "global_optimum_not_certified_unique": 40}), "Frozen fallback reasons drifted")
    return cases


def verify_lineage(lock_dir: Path, result_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    verify_hashes(lock_dir, EXPECTED_LOCK)
    require(verify_manifest(lock_dir) == 6, "Benchmark lock manifest count drifted")
    verify_hashes(result_dir, EXPECTED_RESULT)
    require(verify_manifest(result_dir) == 6, "S2 result manifest count drifted")
    lock_receipt = json.loads((lock_dir / "protocol_lock_receipt.json").read_text(encoding="utf-8"))
    result_receipt = json.loads((result_dir / "s2_artificial_zero_step_receipt.json").read_text(encoding="utf-8"))
    require(lock_receipt["status"] == "D6A_R1_S2_artificial_performance_benchmark_protocol_frozen_non_runnable", "Benchmark lock status drifted")
    require(lock_receipt["warmup_calls_executed"] == lock_receipt["timed_calls_executed"] == 0, "Benchmark lock executed work")
    require(lock_receipt["S2_artificial_performance_benchmark_execution_authorized"] is False, "Parent lock already authorized execution")
    require(result_receipt["status"] == "D6A_R1_S2_certified_fast_path_artificial_zero_step_passed", "S2 result status drifted")
    require(result_receipt["all_gates_passed"] is True and result_receipt["certified_fast_path_cases"] == 96 and result_receipt["fallback_s0_cases"] == 72, "S2 positive result drifted")
    require(result_receipt["performance_timing_calls"] == 0 and result_receipt["D6_cases_accessed"] == 0, "S2 result boundary drifted")
    return lock_receipt, read_cases(result_dir)


def source_hashes() -> dict[str, dict[str, Any]]:
    observed = {}
    for name, relative in SOURCE_PATHS.items():
        path = ROOT / relative
        require(path.is_file(), f"Missing frozen implementation source: {path}")
        payload = path.read_bytes()
        require(b"\r" not in payload.replace(b"\r\n", b""), f"Lone CR byte in source: {path}")
        lf_payload = payload.replace(b"\r\n", b"\n")
        lf_sha = sha256_bytes(lf_payload)
        require(lf_sha == EXPECTED_SOURCE_LF[name], f"Frozen implementation source drifted: {path}")
        observed[name] = {
            "path": relative,
            "raw_sha256": sha256_bytes(payload),
            "LF_normalized_sha256": lf_sha,
            "CRLF_sequences": payload.count(b"\r\n"),
        }
    return observed


def write_exact(root: Path, files: Mapping[str, bytes]) -> None:
    files = dict(files)
    if root.exists():
        existing = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}
        require(existing == files, f"Existing authorization drifted: {root}")
        print(f"[locked] existing S2 benchmark authorization is byte-identical: {root}")
        return
    root.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{root.name}.", dir=root.parent))
    try:
        for name, payload in files.items():
            target = working / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        working.replace(root)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol_lock_dir", type=Path, required=True)
    parser.add_argument("--s2_result_dir", type=Path, required=True)
    parser.add_argument("--config_output_dir", type=Path, required=True)
    parser.add_argument("--authorization_output_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    parent_receipt, cases = verify_lineage(args.protocol_lock_dir.resolve(), args.s2_result_dir.resolve())
    implementations = source_hashes()
    config_name = "MambaV16D6A_R1_S2_artificial_performance_benchmark_v1.json"
    config = {
        "authorization_version": VERSION,
        "status": "D6A_R1_S2_artificial_performance_benchmark_authorized_not_started",
        "cases": cases,
        "runtime": protocol["runtime"],
        "authorization_preflight": protocol["authorization_preflight"],
        "performance_gate": protocol["performance_gate"],
        "result_contract": protocol["result_contract"],
        "permission_boundary": protocol["permission_boundary"],
        "implementation_sha256": implementations,
    }
    config_payload = canonical_json(config)
    configs = {config_name: config_payload}
    write_exact(args.config_output_dir.resolve(), configs)

    receipt = {
        "authorization_version": VERSION,
        "status": "D6A_R1_S2_artificial_performance_benchmark_execution_authorized",
        "runtime_config": {"name": config_name, "sha256": sha256_bytes(config_payload)},
        "parent_lock_status": parent_receipt["status"],
        "parent_lock_sha256": dict(EXPECTED_LOCK),
        "S2_positive_result_sha256": dict(EXPECTED_RESULT),
        "authorization_protocol_sha256": sha256_file(PROTOCOL),
        "authorization_report_sha256": sha256_file(REPORT),
        "implementation_sha256": implementations,
        "S2_artificial_performance_benchmark_execution_authorized": True,
        "authorization_preflight_authorized": True,
        "execution_started": False,
        "correctness_replay_cases_completed": 0,
        "warmup_calls_completed": 0,
        "timed_calls_completed": 0,
        "measurement_blocks_completed": 0,
        "torch_profiler_traces": 0,
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        "S2_implementation_change_authorized": False,
        "R1_production_implementation_change_authorized": False,
        "formal_efficiency_rerun_authorized": False,
        "seed0_training_authorized": False,
        "seed1_training_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "candidate_selection_authorized": False,
        "protected_or_sealed_data_accessed": False,
        "next_step": "run_zero_count_CUDA_authorization_preflight",
    }
    receipt_payload = canonical_json(receipt)
    receipt_name = "benchmark_execution_authorization_receipt.json"
    files = {
        receipt_name: receipt_payload,
        f"{receipt_name}.sha256": f"{sha256_bytes(receipt_payload)}  {receipt_name}\n".encode("ascii"),
        "runtime_config.sha256": manifest_bytes(configs),
        "execution_authorization_protocol_v1.json": canonical_json(protocol),
        "execution_authorization_report_zh.md": REPORT.read_bytes(),
    }
    files["files.sha256"] = manifest_bytes(files)
    write_exact(args.authorization_output_dir.resolve(), files)
    print("[authorized] one fixed 168-case S0-versus-S2 artificial performance benchmark")
    print("[next] run separate zero-count CUDA authorization preflight")
    print("[locked] execution not started; production=false formal_rerun=false training=false D6=false")


if __name__ == "__main__":
    main()
