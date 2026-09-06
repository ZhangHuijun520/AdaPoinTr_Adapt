#!/usr/bin/env python3
"""Verify a restored D6-A R1 S2 certified-fast-path positive archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


EXPECTED_PARENT = {
    "files.sha256": "abc72d3d05637d1a19d028425a693d775728843447ea16301c2b1484dbd67494",
    "protocol_v1.json": "360b2e8ed87371d84bb0be4d4c9170ff9b10f1fb8a5ed0a2b20cbf3133a14281",
    "certified_fast_path_contract.json": "4c8e0c8395596a314caafc8734a37d63702d95dbc6710fee159472d93cfb4594",
    "protocol_lock_receipt.json": "21d622cfcce240fc050c6751970dc162abe02e6998df106d387ab16590a3013b",
    "synthetic_equivalence_suite.json": "864e11ab4edf3164963bcb68123499c2b52f02429a566e95cd2303322d14ebc0",
}
EXPECTED_BACKUP = {
    "files.sha256": "a34adc235272b025417df47a01795cfb54b285ac94af5afd2d4da7782982c460",
    "protocol_v1.json": "ba8b78b8542c1cd29a50c258bd6fc35c8558efbaf5daa814a5002dfa356a62dd",
    "protocol_lock_receipt.json": "4d614dfa9645ffd390d0d31ff33063d4b8d1b95aff66fdc26de41cd9b66b3a6c",
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
EXPECTED_R1 = "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43"
EXPECTED_S1 = "e0583751a397dfb718e47bf681437dc4265c52b8b066f28a73dc65f169e65e73"
SERVER_REPO_PREFIX = "/home/jovyan/adapointr_work/PoinTr/"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def verify_server_repo_manifest(manifest: Path, restored_repo: Path) -> int:
    """Verify a frozen server-absolute manifest against a restored repo."""

    require(manifest.is_file(), f"Missing manifest: {manifest}")
    resolved_repo = restored_repo.resolve()
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        wanted, original = line.split(maxsplit=1)
        original = original.lstrip("*").replace("\\", "/")
        require(original.startswith(SERVER_REPO_PREFIX), f"Unexpected server path: {original}")
        relative = original[len(SERVER_REPO_PREFIX):]
        posix = PurePosixPath(relative)
        require(not posix.is_absolute() and ".." not in posix.parts, f"Unsafe server path: {original}")
        path = restored_repo.joinpath(*posix.parts).resolve()
        require(path == resolved_repo or resolved_repo in path.parents, f"Escaped server path: {path}")
        require(path.is_file() and sha256_file(path) == wanted.lower(), f"Manifest mismatch: {path}")
        count += 1
    return count


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def flag(row: dict[str, str], key: str) -> bool:
    return row[key].lower() == "true"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()
    restore = args.restore_root.resolve()
    payload_count = verify_manifest(restore / "payload_manifest.sha256", restore)
    repo = restore / "adapointr_work" / "PoinTr"
    logs = repo / "logs" / "mamba_v16_d6_contact_support"
    parent = logs / "d6a_r1_s2_certified_fast_path_feasibility_protocol_v1"
    backup = logs / "d6a_r1_s2_certified_fast_path_feasibility_protocol_crlf_backup_v1"
    normalization = logs / "d6a_r1_s2_parent_repo_normalization_v1"
    restoration = logs / "d6a_r1_s2_parent_lock_lf_restore_v1"
    auth = logs / "d6a_r1_s2_certified_fast_path_zero_step_authorization_v1"
    prelaunch = logs / "d6a_r1_s2_certified_fast_path_zero_step_prelaunch_lock_v1"
    result = logs / "d6a_r1_s2_certified_fast_path_artificial_zero_step_v1"
    config = repo / "cfgs" / "MUG500plus_models" / "generated_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_authorized_v1"

    for directory in (parent, backup, normalization, restoration, auth, prelaunch, result, config):
        require(directory.is_dir(), f"Missing frozen directory: {directory}")
    require_hashes(parent, EXPECTED_PARENT)
    require_hashes(backup, EXPECTED_BACKUP)
    require_hashes(result, EXPECTED_RESULT)
    for directory in (parent, backup, auth, result):
        verify_manifest(directory / "files.sha256", directory)
    verify_manifest(normalization / "files.sha256", normalization)
    verify_manifest(restoration / "files.sha256", restoration)
    verify_manifest(auth / "runtime_config.sha256", config)
    verify_manifest(prelaunch / "files.sha256", prelaunch)
    prelaunch_count = verify_server_repo_manifest(prelaunch / "key_artifacts.sha256", repo)
    require(prelaunch_count == 9, f"Unexpected prelaunch key-artifact count: {prelaunch_count}")

    require(sha256_file(repo / "utils/mamba_d6a_slot_allocator.py") == EXPECTED_R1, "Production R1 drifted")
    require(sha256_file(repo / "utils/mamba_d6a_r1_s1_exact_assignment.py") == EXPECTED_S1, "Frozen S1 shadow drifted")

    restore_receipt = json.loads((restoration / "parent_lock_lf_restore_receipt.json").read_text())
    require(
        restore_receipt.get("status") == "D6A_R1_S2_parent_lock_CRLF_transport_chain_restored_to_canonical_LF"
        and restore_receipt.get("protocol_semantics_changed") is False
        and restore_receipt.get("suite_changed") is False
        and restore_receipt.get("permission_boundary_changed") is False
        and restore_receipt.get("authorization_or_execution_started") is False,
        "S2 parent restoration semantics drifted",
    )
    auth_receipt = json.loads((auth / "s2_zero_step_execution_authorization_receipt.json").read_text())
    require(
        auth_receipt.get("status") == "D6A_R1_S2_certified_fast_path_implementation_zero_step_authorized"
        and auth_receipt.get("execution_started") is False
        and auth_receipt.get("S2_artificial_performance_benchmark_authorized") is False
        and auth_receipt.get("optimizer_steps") == auth_receipt.get("model_updates") == 0
        and auth_receipt.get("D6_cases_accessed") == 0,
        "S2 authorization semantics drifted",
    )
    prelaunch_receipt = json.loads((prelaunch / "prelaunch_receipt.json").read_text())
    require(
        prelaunch_receipt.get("status") == "D6A_R1_S2_certified_fast_path_zero_step_prelaunch_frozen"
        and prelaunch_receipt.get("execution_started") is False
        and prelaunch_receipt.get("performance_timing_calls") == 0
        and prelaunch_receipt.get("training_authorized") is False,
        "S2 prelaunch semantics drifted",
    )

    receipt = json.loads((result / "s2_artificial_zero_step_receipt.json").read_text())
    summary = json.loads((result / "s2_artificial_zero_step_summary.json").read_text())
    required_result = (
        receipt.get("status") == "D6A_R1_S2_certified_fast_path_artificial_zero_step_passed"
        and receipt.get("cases") == receipt.get("S0_assignments") == receipt.get("S2_assignments") == 168
        and receipt.get("slot_to_candidate_exact") == 168
        and receipt.get("sorted_selected_indices_exact") == 168
        and receipt.get("hard_assignment_exact") == 168
        and receipt.get("adjusted_objective_exact") == 168
        and receipt.get("outputs_finite") == 168
        and receipt.get("certified_fast_path_cases") == 96
        and receipt.get("fallback_s0_cases") == 72
        and receipt.get("independent_normal_certified_fast_path") == 64
        and receipt.get("collision_heavy_certified_fast_path") == 32
        and receipt.get("false_positive_certificates") == 0
        and receipt.get("equivalence_gate_passed") is True
        and receipt.get("routing_integrity_gate_passed") is True
        and receipt.get("all_gates_passed") is True
        and receipt.get("state_unchanged") is True
        and receipt.get("performance_timing_calls") == receipt.get("warmup_runs") == receipt.get("timed_runs") == 0
        and receipt.get("torch_profiler_traces") == 0
        and receipt.get("optimizer_steps") == receipt.get("model_updates") == receipt.get("D6_cases_accessed") == 0
        and receipt.get("S2_artificial_performance_benchmark_authorized") is False
        and receipt.get("formal_efficiency_rerun_authorized") is False
        and receipt.get("seed0_training_authorized") is False
        and receipt.get("seed1_training_authorized") is False
        and receipt.get("D6B_authorized") is False
        and receipt.get("protected_or_sealed_data_accessed") is False
        and receipt.get("next_step") == "separate_S2_artificial_performance_benchmark_authorization_only"
    )
    require(required_result and summary.get("all_gates_passed") is True, "S2 positive-result semantics drifted")

    equivalence = read_csv(result / "s2_artificial_equivalence_metrics.csv")
    routing = read_csv(result / "s2_certification_routing_metrics.csv")
    families = read_csv(result / "s2_family_summary.csv")
    require(len(equivalence) == len(routing) == 168 and len(families) == 7, "S2 CSV row counts drifted")
    for row in equivalence:
        require(
            all(flag(row, key) for key in (
                "slot_to_candidate_exact", "sorted_selected_indices_exact", "hard_assignment_exact",
                "adjusted_objective_exact", "input_unchanged", "outputs_finite", "all_case_gates_passed",
            )) and int(row["selected_unique"]) == 32,
            f"S2 equivalence row drifted: {row['case_index']}",
        )

    expected_routes = {
        "independent_normal": (64, 64, 0),
        "collision_heavy_shared_candidate_bias": (32, 32, 0),
        "identical_rows": (8, 0, 8),
        "exact_tie_groups": (16, 0, 16),
        "near_ties_float32": (16, 0, 16),
        "shared_top32_adversarial": (16, 0, 16),
        "top32_cutoff_ties": (16, 0, 16),
    }
    observed: dict[str, Counter[str]] = defaultdict(Counter)
    reasons: Counter[str] = Counter()
    for row in routing:
        observed[row["family"]][row["route"]] += 1
        require(flag(row, "route_valid") and not flag(row, "false_positive_certificate"), "Invalid S2 route")
        if row["route"] == "fallback_s0":
            reasons[row["fallback_reason"]] += 1
    for family, (cases, fast, fallback) in expected_routes.items():
        require(sum(observed[family].values()) == cases, f"Family count drifted: {family}")
        require(observed[family]["certified_fast_path"] == fast, f"Fast routing drifted: {family}")
        require(observed[family]["fallback_s0"] == fallback, f"Fallback routing drifted: {family}")
    require(reasons == Counter({"cutoff_tie_or_near_tie": 32, "global_optimum_not_certified_unique": 40}), "Fallback reasons drifted")
    family_rows = {row["family"]: row for row in families}
    require(set(family_rows) == set(expected_routes), "Family-summary membership drifted")
    for family, (cases, fast, fallback) in expected_routes.items():
        row = family_rows[family]
        require(
            int(row["cases"]) == cases
            and int(row["certified_fast_path"]) == fast
            and int(row["fallback_s0"]) == fallback
            and int(row["all_exact"]) == cases,
            f"Family-summary values drifted: {family}",
        )

    forbidden = {".pth", ".pt", ".ckpt", ".npz", ".stl"}
    for path in restore.rglob("*"):
        if path.is_file() and path.suffix.lower() in forbidden:
            raise RuntimeError(f"Archive contains forbidden model/data payload: {path}")
    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] canonical/CRLF parent locks and restoration lineage match")
    print("[ok] S2=168/168 exact, fast=96, fallback=72, false-positive=0")
    print("[excluded] checkpoints, NPZ, STL, D6 cases and sealed data")
    print("[locked] benchmark=false production=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
