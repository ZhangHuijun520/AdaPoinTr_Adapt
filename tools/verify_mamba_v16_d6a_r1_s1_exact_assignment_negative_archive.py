#!/usr/bin/env python3
"""Verify a restored D6-A R1 S1 exact-assignment frozen-negative archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path, PurePosixPath


EXPECTED_R1 = "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43"
EXPECTED_S1 = "e0583751a397dfb718e47bf681437dc4265c52b8b066f28a73dc65f169e65e73"
EXPECTED_PARENT = {
    "files.sha256": "4619426357e19f7f3673d2f6d793342eb1c42ecb32d62c49d228507d0beb8eff",
    "optimization_feasibility_protocol_v1.json": "faededb5862c940d5198420199a7ded4de7b3d7f20aecd72212e341f539714cc",
    "optimization_contract.json": "7032309e1a9103464103b5ee9530a66c45cc08422425afef137a1beba965b2a2",
    "protocol_lock_receipt.json": "a76d894734219c538082fec1b38c5e2bd5fa232ad57cd84805f9d3036ce283f0",
    "synthetic_equivalence_suite.json": "d9c657af5e25be00333fccaa0a992946129391d1fa1f910b9fc0fb4131b2f7fc",
}
EXPECTED_BACKUP = {
    "files.sha256": "6342a34147e87f63623fdd6865e941ef8e4daa3dd399bf68b0af8cca3c5813a4",
    "optimization_feasibility_protocol_v1.json": "7e0983d657b802f847f3cbce6643a6792cc4cdf8b6a530947a9bcaf06ddcfb88",
    "protocol_lock_receipt.json": "328cadd45631849cb1d4a14ae15a4f893fea9077846f83005bbd1ca0e89b4a0b",
}
EXPECTED_RESULT = {
    "files.sha256": "28c5ac0b265d8e6cdbc458de519b2814f356f49d346d9cf99ff7f052c8750d7c",
    "s1_artificial_equivalence_metrics.csv": "f738c0ba9e7fd5024d1c27fcf842d6ed626f58b80bd5d257f80a7306b985f929",
    "s1_union_size_summary.csv": "4b55aaef692dcc6fb75593d358e24e012420e29ebe2319ed55e047c9bc7ab8ab",
    "s1_artificial_zero_step_summary.json": "1d8fc3a2ec44d42c71593dbd06f982f47ee5224b45a8dc28bf213280565dfc66",
    "s1_artificial_zero_step_receipt.json": "7f2eab73350a3c0d5c3ecedd188da9b9fc99657fcd44991781b6d29d9051a161",
    "s1_artificial_zero_step_report_zh.md": "ed461648f3c1f79cf37895f44b5cfbbd2f2ef20cae372f1fc4d79671fd58d44e",
}
EXPECTED_AUTH_MANIFEST = "3d3e7431d6916f652199d5cc6e75ec38b63f586a593eb23d036dee041a327d34"
EXPECTED_RESTORE_MANIFEST = "89de20e88b7e2964451740393adc170cda4b7cdbc309d9b31c442265a0df444b"


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def flag(row: dict[str, str], name: str) -> bool:
    return row[name].lower() == "true"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()
    restore = args.restore_root.resolve()
    payload_count = verify_manifest(restore / "payload_manifest.sha256", restore)
    repo = restore / "adapointr_work" / "PoinTr"
    logs = repo / "logs" / "mamba_v16_d6_contact_support"
    parent = logs / "d6a_r1_exact_assignment_optimization_feasibility_protocol_v1"
    backup = logs / "d6a_r1_exact_assignment_optimization_feasibility_protocol_v1.crlf_transport_backup_20260906"
    normalization = logs / "d6a_r1_s1_parent_lock_lf_restore_v1"
    auth = logs / "d6a_r1_s1_exact_assignment_zero_step_authorization_v1"
    result = logs / "d6a_r1_s1_exact_assignment_artificial_zero_step_v1"
    config = repo / "cfgs" / "MUG500plus_models" / "generated_mamba_v16_d6a_r1_s1_exact_assignment_zero_step_authorized_v1"

    for directory in (parent, backup, normalization, auth, result, config):
        require(directory.is_dir(), f"Missing frozen directory: {directory}")
    require_hashes(parent, EXPECTED_PARENT)
    require_hashes(backup, EXPECTED_BACKUP)
    require_hashes(result, EXPECTED_RESULT)
    require(sha256_file(auth / "files.sha256") == EXPECTED_AUTH_MANIFEST, "Authorization manifest drifted")
    require(sha256_file(normalization / "files.sha256") == EXPECTED_RESTORE_MANIFEST, "Restoration manifest drifted")
    verify_manifest(parent / "files.sha256", parent)
    verify_manifest(backup / "files.sha256", backup)
    verify_manifest(normalization / "files.sha256", normalization)
    verify_manifest(auth / "files.sha256", auth)
    verify_manifest(auth / "runtime_config.sha256", config)
    verify_manifest(result / "files.sha256", result)

    require(sha256_file(repo / "utils/mamba_d6a_slot_allocator.py") == EXPECTED_R1, "Production R1 drifted")
    require(sha256_file(repo / "utils/mamba_d6a_r1_s1_exact_assignment.py") == EXPECTED_S1, "S1 shadow drifted")
    restore_receipt = json.loads((normalization / "parent_lock_lf_restore_receipt.json").read_text())
    require(
        restore_receipt.get("status") == "D6A_R1_S1_parent_lock_CRLF_transport_chain_restored_to_canonical_LF"
        and restore_receipt.get("protocol_semantics_changed") is False
        and restore_receipt.get("authorization_started_before_restore") is False
        and restore_receipt.get("zero_step_started_before_restore") is False
        and restore_receipt.get("training_authorized") is False,
        "Parent restoration semantics drifted",
    )

    auth_receipt = json.loads((auth / "s1_zero_step_execution_authorization_receipt.json").read_text())
    require(
        auth_receipt.get("status") == "D6A_R1_S1_exact_assignment_implementation_zero_step_authorized"
        and auth_receipt.get("execution_started") is False
        and auth_receipt.get("S1_artificial_performance_benchmark_authorized") is False
        and auth_receipt.get("optimizer_steps") == auth_receipt.get("model_updates") == 0
        and auth_receipt.get("D6_cases_accessed") == 0,
        "S1 authorization semantics drifted",
    )

    receipt = json.loads((result / "s1_artificial_zero_step_receipt.json").read_text())
    summary = json.loads((result / "s1_artificial_zero_step_summary.json").read_text())
    require(
        receipt.get("status") == "D6A_R1_S1_exact_assignment_artificial_zero_step_equivalence_failed"
        and receipt.get("cases") == 168
        and receipt.get("slot_to_candidate_exact") == receipt.get("hard_assignment_exact") == 128
        and receipt.get("sorted_selected_indices_exact") == 168
        and receipt.get("adjusted_objective_exact") == 160
        and receipt.get("baseline_columns_contained_in_union") == 168
        and receipt.get("all_equivalence_gates_passed") is False
        and receipt.get("state_unchanged") is True
        and receipt.get("performance_timing_calls") == receipt.get("warmup_runs") == receipt.get("timed_runs") == 0
        and receipt.get("torch_profiler_traces") == 0
        and receipt.get("formal_gate_evaluated") is False
        and receipt.get("optimizer_steps") == receipt.get("model_updates") == 0
        and receipt.get("D6_cases_accessed") == 0
        and receipt.get("S1_artificial_performance_benchmark_authorized") is False
        and receipt.get("seed0_training_authorized") is False
        and receipt.get("seed1_training_authorized") is False
        and receipt.get("D6B_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
        and receipt.get("next_step") == "archive_S1_equivalence_negative_result_and_stop_S1",
        "S1 frozen-negative semantics drifted",
    )
    require(summary.get("union_size_minimum") == 32 and summary.get("union_size_maximum") == 981, "Union bounds drifted")

    rows = read_csv(result / "s1_artificial_equivalence_metrics.csv")
    require(len(rows) == 168, "S1 case count drifted")
    expected = {
        "collision_heavy_shared_candidate_bias": (32, 32, 32),
        "exact_tie_groups": (16, 16, 16),
        "identical_rows": (8, 0, 7),
        "independent_normal": (64, 64, 64),
        "near_ties_float32": (16, 0, 12),
        "shared_top32_adversarial": (16, 0, 13),
        "top32_cutoff_ties": (16, 16, 16),
    }
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["family"]].append(row)
        require(flag(row, "sorted_selected_indices_exact"), "Selected set drifted")
        require(flag(row, "baseline_columns_contained_in_union"), "S0 column escaped S1 union")
        require(flag(row, "input_unchanged") and int(row["selected_unique"]) == 32, "State/uniqueness drifted")
    for family, (cases, slots, objectives) in expected.items():
        family_rows = grouped.get(family, [])
        require(len(family_rows) == cases, f"Family count drifted: {family}")
        require(sum(flag(row, "slot_to_candidate_exact") for row in family_rows) == slots, f"Slot result drifted: {family}")
        require(sum(flag(row, "hard_assignment_exact") for row in family_rows) == slots, f"Hard result drifted: {family}")
        require(sum(flag(row, "adjusted_objective_exact") for row in family_rows) == objectives, f"Objective drifted: {family}")

    forbidden = {".pth", ".pt", ".ckpt", ".npz", ".stl"}
    for path in restore.rglob("*"):
        if path.is_file() and path.suffix.lower() in forbidden:
            raise RuntimeError(f"Archive contains forbidden model/data payload: {path}")
    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] canonical and CRLF parent locks plus restoration lineage match")
    print("[ok] S1=128/168 slot, 168/168 selected, 160/168 objective negative semantics match")
    print("[excluded] checkpoints, NPZ, STL, D6 cases and sealed data")
    print("[locked] benchmark=false production=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
