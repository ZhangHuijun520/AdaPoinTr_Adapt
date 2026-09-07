#!/usr/bin/env python3
"""Verify a restored D6-A R1 S2 artificial-benchmark negative archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


EXPECTED_PARENT = {
    "files.sha256": "1887c591137aacb67615510defa2be816cf5c71f4637d12f390121c328b03f9a",
    "benchmark_contract.json": "841dfcea14b41c68294526080b6bf13ab311ddabaa1311b8739315e9fda52ecd",
    "benchmark_execution.template.json": "74ca7f0a03c32b9adfff2008db4958807064ea5f4f2eac34fcc8bdc895149a58",
    "protocol_lock_receipt.json": "c553795d6c4f3995b062e755c7dde7a53c646266c3f07c72d2cc5ac4de24088b",
    "protocol_lock_report_zh.md": "81e07348c7f41e7d8ef759d8d2432f12361c0d7634f1e747cd8feca41af97b3a",
    "protocol_v1.json": "0542199bf2b05a82c3197bd156e5bc3269a118acf676e356ebdc306effa9ea04",
    "synthetic_suite_binding.json": "6da4e2100f9a682c7364bdc01b680b2d796644d2c7a4ccc3f41be22f9f9118f3",
}
EXPECTED_PARENT_BACKUP = {
    "files.sha256": "1ea36a58bf4655fc0fd3228b800fc7fb079a3b6e96dce5c7e44e4721e1a49e67",
    "protocol_lock_receipt.json": "e63cf55bf95332acd691d16a809d3861234fd5c66be2789b3547cdba9b87a214",
    "protocol_v1.json": "918043aafa4b13d6836285177dfdf74e0a01fba6ada140d82bde2c87f40404ce",
}
EXPECTED_S2_RESULT = {
    "files.sha256": "5713a4fa4307cd0a68c8d429848b6055e2b0d888c2eea0c5e39cd9d965fcbeb6",
    "s2_artificial_equivalence_metrics.csv": "be1ea8643a169293cf258bd39473557f8a40f72da31427b84cfc5fcc85677244",
    "s2_artificial_zero_step_receipt.json": "85d8a0946504bb02d471b0087df7d6a8ccb929c01dc40df031088c6143a9c061",
    "s2_artificial_zero_step_report_zh.md": "a166d0fb514716d2e71477dc064243a3e0623a85c93477127f7f0d1d50e4df7b",
    "s2_artificial_zero_step_summary.json": "a3b9c5ede525f3b29e638abdc55f97c7367d8b760fb34d829d0472b3093813d1",
    "s2_certification_routing_metrics.csv": "182654d18b1c428f80f4f796449c35eafe17d782e11238fa7856811a302a4cc1",
    "s2_family_summary.csv": "102a7c4d3b5c0dff5410f17a3f6d88c14b2d755267d9dde2eacb0ed2c7c79fd0",
}
EXPECTED_BLOCKS = [
    (0, 1094.0110349999993, 1620.397318, 1.4811526265820536),
    (1, 1083.2697139999993, 1615.9052529999992, 1.4916924493653851),
    (2, 1088.142639, 1617.464545, 1.4864453308129213),
]
EXPECTED_GATE = {
    "median_overall_block_ratio": 1.4864453308129213,
    "aggregate_fast_path_ratio": 1.3882236452516563,
    "aggregate_fallback_ratio": 1.5778733949761603,
}
EXPECTED_ROUTES = {
    "certified_fast_path": (96, 288, 1.3882236452516563),
    "fallback_s0": (72, 216, 1.5778733949761603),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def close(actual: float, expected: float, *, tolerance: float = 1e-12) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def require_hashes(root: Path, expected: dict[str, str]) -> None:
    for name, wanted in expected.items():
        path = root / name
        require(path.is_file() and sha256_file(path) == wanted, f"Frozen hash mismatch: {path}")


def verify_manifest(manifest: Path, root: Path) -> int:
    require(manifest.is_file(), f"Missing manifest: {manifest}")
    resolved_root = root.resolve()
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        wanted, relative = line.split(maxsplit=1)
        posix = PurePosixPath(relative.lstrip("*"))
        require(not posix.is_absolute() and ".." not in posix.parts, f"Unsafe manifest path: {relative}")
        path = root.joinpath(*posix.parts).resolve()
        require(path == resolved_root or resolved_root in path.parents, f"Escaped manifest path: {path}")
        require(path.is_file() and sha256_file(path) == wanted.lower(), f"Manifest mismatch: {path}")
        count += 1
    return count


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def flag(value: str) -> bool:
    return value.lower() == "true"


def verify_result(result: Path) -> None:
    verify_manifest(result / "files.sha256", result)
    expected_names = {
        "files.sha256",
        "s2_artificial_performance_block_summary.csv",
        "s2_artificial_performance_environment.json",
        "s2_artificial_performance_observations.csv",
        "s2_artificial_performance_receipt.json",
        "s2_artificial_performance_report_zh.md",
        "s2_artificial_performance_stratum_summary.csv",
    }
    require({path.name for path in result.iterdir() if path.is_file()} == expected_names, "Result file set drifted")

    receipt = read_json(result / "s2_artificial_performance_receipt.json")
    correctness = receipt.get("correctness_replay", {})
    gate = receipt.get("performance_gate", {})
    require(
        receipt.get("status") == "D6A_R1_S2_artificial_performance_benchmark_failed"
        and correctness == {
            "all_exact": 168,
            "cases": 168,
            "certified_fast_path": 96,
            "fallback_s0": 72,
            "passed": True,
        }
        and receipt.get("warmup_calls") == 28
        and receipt.get("timed_observation_rows") == 1008
        and receipt.get("measurement_blocks") == 3
        and receipt.get("implementation_state_unchanged") is True
        and receipt.get("outliers_removed") == receipt.get("slow_observations_retried") == 0
        and receipt.get("torch_profiler_traces") == 0
        and receipt.get("formal_R0_denominator_used") is False
        and receipt.get("formal_efficiency_thresholds_evaluated") is False
        and receipt.get("formal_efficiency_rerun") is False
        and receipt.get("optimizer_constructed") is False
        and receipt.get("optimizer_steps") == receipt.get("model_updates") == receipt.get("D6_cases_accessed") == 0
        and receipt.get("R1_production_implementation_change_authorized") is False
        and receipt.get("seed0_training_authorized") is False
        and receipt.get("seed1_training_authorized") is False
        and receipt.get("proposal_confirmation_accessed") is False
        and receipt.get("D6B_authorized") is False
        and receipt.get("candidate_selection_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
        and receipt.get("next_step") == "freeze_archive_and_stop_S2_while_retaining_S0",
        "Frozen benchmark receipt semantics drifted",
    )
    require(
        gate.get("all_performance_gates_passed") is False
        and gate.get("median_overall_block_ratio_passed") is False
        and gate.get("every_block_ratio_passed") is False
        and gate.get("fast_path_ratio_passed") is False
        and gate.get("fallback_ratio_passed") is False
        and gate.get("finite_positive_and_count_passed") is True
        and all(close(float(gate[name]), value) for name, value in EXPECTED_GATE.items())
        and all(close(float(actual), expected) for actual, expected in zip(gate.get("individual_block_ratios", []), [row[3] for row in EXPECTED_BLOCKS]))
        and len(gate.get("individual_block_ratios", [])) == 3,
        "Frozen performance gate drifted",
    )

    blocks = read_csv(result / "s2_artificial_performance_block_summary.csv")
    require(len(blocks) == 3, "Block count drifted")
    for row, (block, s0, s2, ratio) in zip(blocks, EXPECTED_BLOCKS):
        require(
            int(row["block"]) == block
            and int(row["cases"]) == 168
            and close(float(row["S0_total_ms"]), s0)
            and close(float(row["S2_total_ms"]), s2)
            and close(float(row["S2_over_S0_ratio"]), ratio)
            and not flag(row["strictly_below_1"]),
            f"Block summary drifted: {block}",
        )

    observations = read_csv(result / "s2_artificial_performance_observations.csv")
    require(len(observations) == 1008, "Timed observation count drifted")
    candidates: Counter[str] = Counter()
    routes: dict[str, Counter[str]] = defaultdict(Counter)
    by_block: dict[int, list[dict[str, str]]] = defaultdict(list)
    pairs: dict[tuple[int, int], set[str]] = defaultdict(set)
    first: dict[int, Counter[str]] = defaultdict(Counter)
    for row in observations:
        block = int(row["block"])
        case = int(row["case_index"])
        candidate = row["candidate"]
        route = row["expected_route"]
        latency_ns = int(row["latency_ns"])
        latency_ms = float(row["latency_ms"])
        require(block in (0, 1, 2) and 0 <= case < 168, "Observation index drifted")
        require(candidate in ("S0", "S2") and route in EXPECTED_ROUTES, "Observation label drifted")
        require(latency_ns > 0 and math.isfinite(latency_ms) and latency_ms > 0, "Non-positive timing")
        require(close(latency_ms, latency_ns / 1_000_000.0, tolerance=1e-9), "ns/ms timing mismatch")
        candidates[candidate] += 1
        routes[candidate][route] += 1
        by_block[block].append(row)
        pairs[(block, case)].add(candidate)
        if int(row["order_position"]) == 0:
            first[block][candidate] += 1
    require(candidates == Counter({"S0": 504, "S2": 504}), "Candidate timing counts drifted")
    require(len(pairs) == 504 and all(value == {"S0", "S2"} for value in pairs.values()), "Pairing drifted")
    for block, s0_expected, s2_expected, _ in EXPECTED_BLOCKS:
        rows = by_block[block]
        require(len(rows) == 336 and first[block] == Counter({"S0": 84, "S2": 84}), f"Block order drifted: {block}")
        s0_actual = sum(float(row["latency_ms"]) for row in rows if row["candidate"] == "S0")
        s2_actual = sum(float(row["latency_ms"]) for row in rows if row["candidate"] == "S2")
        require(close(s0_actual, s0_expected, tolerance=1e-10) and close(s2_actual, s2_expected, tolerance=1e-10), f"Block totals drifted: {block}")
    for candidate in ("S0", "S2"):
        require(routes[candidate] == Counter({"certified_fast_path": 288, "fallback_s0": 216}), f"Route counts drifted: {candidate}")

    strata = read_csv(result / "s2_artificial_performance_stratum_summary.csv")
    require(len(strata) == 10, "Stratum count drifted")
    lookup = {(row["stratum_type"], row["stratum"]): row for row in strata}
    require(len(lookup) == 10 and ("overall", "all") in lookup, "Stratum membership drifted")
    overall = lookup[("overall", "all")]
    require(
        int(overall["cases"]) == 168
        and int(overall["paired_observations"]) == 504
        and close(float(overall["aggregate_S2_over_S0_ratio"]), 1.4864127983638977),
        "Overall stratum drifted",
    )
    for route, (cases, paired, ratio) in EXPECTED_ROUTES.items():
        row = lookup[("route", route)]
        require(
            int(row["cases"]) == cases
            and int(row["paired_observations"]) == paired
            and close(float(row["aggregate_S2_over_S0_ratio"]), ratio),
            f"Route stratum drifted: {route}",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()
    restore = args.restore_root.resolve()
    payload_count = verify_manifest(restore / "payload_manifest.sha256", restore)
    repo = restore / "adapointr_work" / "PoinTr"
    logs = repo / "logs" / "mamba_v16_d6_contact_support"
    parent = logs / "d6a_r1_s2_artificial_performance_benchmark_protocol_v1"
    backup = logs / "d6a_r1_s2_artificial_performance_benchmark_protocol_crlf_backup_v1"
    restoration = logs / "d6a_r1_s2_artificial_performance_benchmark_parent_lf_restore_v1"
    auth = logs / "d6a_r1_s2_artificial_performance_benchmark_execution_authorization_v1"
    preflight = logs / "d6a_r1_s2_artificial_performance_benchmark_execution_preflight_v1"
    result = logs / "d6a_r1_s2_artificial_performance_benchmark_result_v1"
    s2_result = logs / "d6a_r1_s2_certified_fast_path_artificial_zero_step_v1"
    config = repo / "cfgs" / "MUG500plus_models" / "generated_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_authorized_v1"

    for directory in (parent, backup, restoration, auth, preflight, result, s2_result, config):
        require(directory.is_dir(), f"Missing frozen directory: {directory}")
    require_hashes(parent, EXPECTED_PARENT)
    require_hashes(backup, EXPECTED_PARENT_BACKUP)
    require_hashes(s2_result, EXPECTED_S2_RESULT)
    for directory in (parent, backup, restoration, auth, preflight, s2_result):
        verify_manifest(directory / "files.sha256", directory)
    verify_manifest(auth / "runtime_config.sha256", config)
    verify_result(result)

    restore_receipt = read_json(restoration / "parent_lf_restore_receipt.json")
    require(
        restore_receipt.get("status") == "D6A_R1_S2_artificial_benchmark_parent_LF_restored"
        and restore_receipt.get("semantic_change") is False
        and restore_receipt.get("authorization_started") is False
        and restore_receipt.get("preflight_started") is False
        and restore_receipt.get("benchmark_started") is False
        and restore_receipt.get("optimizer_steps") == restore_receipt.get("D6_cases_accessed") == 0,
        "Parent restoration semantics drifted",
    )
    auth_receipt = read_json(auth / "benchmark_execution_authorization_receipt.json")
    require(
        auth_receipt.get("status") == "D6A_R1_S2_artificial_performance_benchmark_execution_authorized"
        and auth_receipt.get("execution_started") is False
        and auth_receipt.get("S2_artificial_performance_benchmark_execution_authorized") is True
        and auth_receipt.get("optimizer_steps") == auth_receipt.get("model_updates") == auth_receipt.get("D6_cases_accessed") == 0,
        "Benchmark authorization semantics drifted",
    )
    preflight_receipt = read_json(preflight / "authorization_preflight_receipt.json")
    require(
        preflight_receipt.get("status") == "D6A_R1_S2_artificial_performance_benchmark_authorization_preflight_passed"
        and preflight_receipt.get("correctness_replay_cases") == 0
        and preflight_receipt.get("warmup_calls") == preflight_receipt.get("timed_calls") == 0
        and preflight_receipt.get("measurement_blocks") == preflight_receipt.get("torch_profiler_traces") == 0
        and preflight_receipt.get("optimizer_steps") == preflight_receipt.get("model_updates") == preflight_receipt.get("D6_cases_accessed") == 0,
        "Authorization preflight semantics drifted",
    )
    s2_receipt = read_json(s2_result / "s2_artificial_zero_step_receipt.json")
    require(
        s2_receipt.get("status") == "D6A_R1_S2_certified_fast_path_artificial_zero_step_passed"
        and s2_receipt.get("slot_to_candidate_exact") == s2_receipt.get("sorted_selected_indices_exact") == 168
        and s2_receipt.get("hard_assignment_exact") == s2_receipt.get("adjusted_objective_exact") == 168
        and s2_receipt.get("certified_fast_path_cases") == 96
        and s2_receipt.get("fallback_s0_cases") == 72,
        "S2 positive input semantics drifted",
    )

    forbidden = {".pth", ".pt", ".ckpt", ".npz", ".stl"}
    for path in restore.rglob("*"):
        if path.is_file() and path.suffix.lower() in forbidden:
            raise RuntimeError(f"Archive contains forbidden model/data payload: {path}")
    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] canonical/CRLF parent and LF-restoration lineage match")
    print("[ok] S2 correctness=168/168 and frozen 1008-observation negative result match")
    print("[ok] block median=1.486445, fast=1.388224, fallback=1.577873; all performance gates failed")
    print("[excluded] checkpoints, NPZ, STL, D6 cases, tmux logs and sealed data")
    print("[locked] rerun=false production=false formal_rerun=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
