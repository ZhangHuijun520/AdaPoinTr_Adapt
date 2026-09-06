#!/usr/bin/env python3
"""Freeze the non-runnable D6-A R1 S2 certified fast-path protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_protocol_v1.json"
PROTOCOL_ID = "mamba-v16-d6a-r1-s2-certified-fast-path-feasibility-v1"

REPO_PARENTS = {
    "S1_negative_report": (
        "docs/mamba_v16_d6a_r1_s1_exact_assignment_artificial_zero_step_negative_result_zh.md",
        "71c6622787473db6ecf67e67c95618b6f97f9fdae15c5905a9707d224dfec28f",
    ),
    "S1_parent_protocol": (
        "docs/mamba_v16_d6a_r1_exact_assignment_optimization_feasibility_protocol_v1.json",
        "faededb5862c940d5198420199a7ded4de7b3d7f20aecd72212e341f539714cc",
    ),
    "production_R1": (
        "utils/mamba_d6a_slot_allocator.py",
        "2e71ff22800a8215001de6fb8963c3016b5056763b0e905a8149180578a75d43",
    ),
    "S1_shadow": (
        "utils/mamba_d6a_r1_s1_exact_assignment.py",
        "e0583751a397dfb718e47bf681437dc4265c52b8b066f28a73dc65f169e65e73",
    ),
    "S1_zero_step": (
        "tools/preflight_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py",
        "4d65e34e0ace92ca2b9ec68d43fc889765c30debd760cc57f444eb79b5aabd85",
    ),
    "S1_archive_verifier": (
        "tools/verify_mamba_v16_d6a_r1_s1_exact_assignment_negative_archive.py",
        "6a026b20f830c5aa36bda14021f1d3be3596c718742f6bc7c02ec396cede1e2e",
    ),
}

CANONICAL_PARENT = {
    "files.sha256": "4619426357e19f7f3673d2f6d793342eb1c42ecb32d62c49d228507d0beb8eff",
    "S0_S1_benchmark.template.json": "c130c86c415bc1b2d95025a8ad6cc04f13a2b30e6b164142d5731e4eec8ed4dd",
    "optimization_contract.json": "7032309e1a9103464103b5ee9530a66c45cc08422425afef137a1beba965b2a2",
    "optimization_feasibility_protocol_v1.json": "faededb5862c940d5198420199a7ded4de7b3d7f20aecd72212e341f539714cc",
    "protocol_lock_receipt.json": "a76d894734219c538082fec1b38c5e2bd5fa232ad57cd84805f9d3036ce283f0",
    "protocol_lock_report_zh.md": "b83a7fdb7e62befd6bce166e8f20827a80067894166cbe6b9f6fc7d0286f3bad",
    "synthetic_equivalence_suite.json": "d9c657af5e25be00333fccaa0a992946129391d1fa1f910b9fc0fb4131b2f7fc",
}
EXPECTED_RESTORE_MANIFEST = "89de20e88b7e2964451740393adc170cda4b7cdbc309d9b31c442265a0df444b"
EXPECTED_AUTH_MANIFEST = "3d3e7431d6916f652199d5cc6e75ec38b63f586a593eb23d036dee041a327d34"
S1_RESULT = {
    "files.sha256": "28c5ac0b265d8e6cdbc458de519b2814f356f49d346d9cf99ff7f052c8750d7c",
    "s1_artificial_equivalence_metrics.csv": "f738c0ba9e7fd5024d1c27fcf842d6ed626f58b80bd5d257f80a7306b985f929",
    "s1_union_size_summary.csv": "4b55aaef692dcc6fb75593d358e24e012420e29ebe2319ed55e047c9bc7ab8ab",
    "s1_artificial_zero_step_summary.json": "1d8fc3a2ec44d42c71593dbd06f982f47ee5224b45a8dc28bf213280565dfc66",
    "s1_artificial_zero_step_receipt.json": "7f2eab73350a3c0d5c3ecedd188da9b9fc99657fcd44991781b6d29d9051a161",
    "s1_artificial_zero_step_report_zh.md": "ed461648f3c1f79cf37895f44b5cfbbd2f2ef20cae372f1fc4d79671fd58d44e",
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


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_manifest_file(manifest: Path, root: Path) -> int:
    require(manifest.is_file(), f"Missing frozen manifest: {manifest}")
    resolved_root = root.resolve()
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        wanted, relative = line.split(maxsplit=1)
        posix = PurePosixPath(relative.lstrip("*"))
        require(not posix.is_absolute() and ".." not in posix.parts, f"Unsafe manifest path: {relative}")
        path = root.joinpath(*posix.parts).resolve()
        require(resolved_root in path.parents, f"Manifest path escaped root: {path}")
        require(path.is_file() and sha256_file(path) == wanted.lower(), f"Manifest mismatch: {path}")
        count += 1
    return count


def verify_manifest(root: Path) -> int:
    return verify_manifest_file(root / "files.sha256", root)


def verify_hashes(root: Path, expected: Mapping[str, str]) -> dict[str, str]:
    hashes = {}
    for relative, wanted in expected.items():
        path = root / relative
        require(path.is_file(), f"Missing frozen parent: {path}")
        actual = sha256_file(path)
        require(actual == wanted, f"Frozen parent drifted: {path}")
        hashes[relative] = actual
    return hashes


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    require(protocol["protocol_id"] == PROTOCOL_ID, "Protocol id drifted")
    require(
        protocol["status"]
        == "S2_certified_fast_path_feasibility_preregistered_non_runnable_after_S1_frozen_negative",
        "Protocol status drifted",
    )
    parent = protocol["frozen_parent"]
    require(parent["S1_result_status"] == "D6A_R1_S1_exact_assignment_artificial_zero_step_equivalence_failed", "S1 status drifted")
    require(parent["S1_cases"] == 168, "S1 case count drifted")
    require(parent["S1_slot_to_candidate_exact"] == parent["S1_hard_assignment_exact"] == 128, "S1 mapping result drifted")
    require(parent["S1_sorted_selected_indices_exact"] == 168, "S1 selected-set result drifted")
    require(parent["S1_adjusted_objective_exact"] == 160, "S1 objective result drifted")
    require(parent["S1_performance_benchmark_authorized"] is False, "S1 benchmark enabled")

    scope = protocol["scope"]
    require(scope["candidate"] == "R1_S2_shadow_only", "Scope is not S2-only")
    require(scope["selector_shape"] == [32, 8192], "Selector shape drifted")
    require(scope["data"] == "the_same_frozen_168_artificial_assignment_matrices_only", "Data boundary drifted")
    require(scope["full_D2H_retained"] is True, "D2H changed during feasibility")
    require(scope["D6_cases_accessed"] == 0, "D6 access enabled")
    require(scope["timing_calls"] == 0, "Timing enabled")
    require(scope["optimizer_constructed"] is False, "Optimizer enabled")
    require(scope["optimizer_steps"] == scope["model_updates"] == 0, "Updates enabled")

    candidates = protocol["candidate_definitions"]
    require(set(candidates) == {"S0", "S1", "S2"}, "Candidate set drifted")
    require(candidates["S1"]["result"] == "frozen_negative_no_rerun", "S1 rerun enabled")
    require(candidates["S2"]["fallback"] == "execute_complete_frozen_S0_and_return_only_S0_outputs", "S0 fallback drifted")
    require(candidates["S2"]["fallback_must_not_reuse_uncertified_S2_outputs"] is True, "Unsafe fallback enabled")
    require(candidates["S2"]["implementation_change_authorized"] is False, "S2 implementation enabled")
    require(candidates["S2"]["zero_step_authorized"] is False, "S2 zero-step enabled")
    require(candidates["S2"]["benchmark_authorized"] is False, "S2 benchmark enabled")

    certificate = protocol["certification_contract"]
    require(certificate["row_top_k"] == 32, "Top-k drifted")
    require(certificate["cutoff_ties"] == "include_all", "Cutoff ties dropped")
    require(certificate["union_order"] == "ascending_original_candidate_index", "Union order drifted")
    require(certificate["global_uniqueness"]["edge_exclusion_solves"] == 32, "Second-best certificate weakened")
    require("strictly_greater_than_guard" in certificate["global_uniqueness"]["certified_condition"], "Strict uniqueness gate removed")
    require(len(certificate["mandatory_fallback_conditions"]) == 5, "Fallback conditions drifted")
    require(certificate["no_posthoc_exception_rule"] is True, "Post-hoc exceptions enabled")

    suite = protocol["synthetic_equivalence_suite"]
    require(suite["binding"] == "byte_identical_to_the_frozen_S0_S1_parent_suite", "Suite binding drifted")
    require(suite["total_cases"] == 168, "Suite count drifted")
    require([item["cases"] for item in suite["families"]] == [64, 32, 8, 16, 16, 16, 16], "Family counts drifted")
    require(suite["post_result_case_search_forbidden"] is True, "Post-result search enabled")
    require(suite["case_addition_removal_or_seed_change_forbidden"] is True, "Suite mutation enabled")

    equivalence = protocol["equivalence_hard_gate"]
    for key in ("slot_to_candidate_exact", "sorted_selected_indices_exact", "hard_assignment_exact", "adjusted_objective_exact", "input_state_unchanged"):
        require(equivalence[key] == "168/168", f"Equivalence gate drifted: {key}")
    require(equivalence["comparison_reference"] == "a_separately_executed_complete_S0_for_every_case", "Independent S0 comparison removed")
    require(equivalence["failure_action"] == "freeze_S2_negative_and_stop_without_performance_benchmark", "Failure action drifted")

    routing = protocol["routing_integrity_gate"]
    require(routing["certified_fast_path_cases_minimum"] == 96, "Fast-path coverage gate drifted")
    require(routing["independent_normal_certified_fast_path_required"] == "64/64", "Normal-family gate drifted")
    require(routing["collision_heavy_certified_fast_path_required"] == "32/32", "Collision-family gate drifted")
    require(routing["false_positive_certificates_allowed"] == 0, "False-positive certificates enabled")
    require(routing["all_fallback_is_a_failure"] is True, "All-fallback loophole enabled")

    zero_step = protocol["artificial_zero_step"]
    require(zero_step["authorized_now"] is False, "Zero-step authorized as side effect")
    require(zero_step["separate_implementation_and_execution_authorization_required"] is True, "Separate authorization bypassed")
    require(zero_step["performance_timing"] is False, "Zero-step timing enabled")
    require(zero_step["warmup_runs"] == zero_step["timed_runs"] == zero_step["torch_profiler_traces"] == 0, "Performance work enabled")

    future = protocol["future_artificial_performance_benchmark"]
    require(future["authorized_now"] is False, "Performance benchmark enabled")
    require(future["separate_execution_authorization_required"] is True, "Performance authorization bypassed")
    require("certificate_and_fallback_cost" in future["comparison"], "Fallback cost excluded")
    require(future["formal_efficiency_thresholds_evaluated"] is False, "Formal gate enabled")

    permission = protocol["permission_boundary"]
    require(permission["protocol_lock_authorized"] is True, "Protocol lock disabled")
    for key, value in permission.items():
        if key != "protocol_lock_authorized":
            require(value is False, f"Forbidden permission enabled: {key}")


def verify_lineage(
    repo_root: Path,
    canonical_parent_dir: Path,
    restoration_dir: Path,
    authorization_dir: Path,
    config_dir: Path,
    result_dir: Path,
) -> tuple[dict[str, str], dict[str, str]]:
    repo_hashes = {}
    for key, (relative, wanted) in REPO_PARENTS.items():
        path = repo_root / relative
        require(path.is_file() and sha256_file(path) == wanted, f"Repository parent drifted: {relative}")
        repo_hashes[key] = wanted

    canonical_hashes = verify_hashes(canonical_parent_dir, CANONICAL_PARENT)
    require(verify_manifest(canonical_parent_dir) == 6, "Canonical parent manifest count drifted")
    require(sha256_file(restoration_dir / "files.sha256") == EXPECTED_RESTORE_MANIFEST, "Restoration manifest drifted")
    verify_manifest(restoration_dir)
    require(sha256_file(authorization_dir / "files.sha256") == EXPECTED_AUTH_MANIFEST, "S1 authorization manifest drifted")
    verify_manifest(authorization_dir)
    require(
        verify_manifest_file(authorization_dir / "runtime_config.sha256", config_dir) == 1,
        "S1 runtime-config manifest count drifted",
    )
    verify_hashes(result_dir, S1_RESULT)
    require(verify_manifest(result_dir) == 5, "S1 result manifest count drifted")

    parent_receipt = json.loads((canonical_parent_dir / "protocol_lock_receipt.json").read_text(encoding="utf-8"))
    require(parent_receipt["status"] == "D6A_R1_exact_assignment_optimization_feasibility_protocol_frozen_non_runnable", "Canonical parent status drifted")
    restore_receipt = json.loads((restoration_dir / "parent_lock_lf_restore_receipt.json").read_text(encoding="utf-8"))
    require(restore_receipt["status"] == "D6A_R1_S1_parent_lock_CRLF_transport_chain_restored_to_canonical_LF", "Restoration status drifted")
    require(restore_receipt["protocol_semantics_changed"] is False, "Restoration changed semantics")
    auth_receipt = json.loads((authorization_dir / "s1_zero_step_execution_authorization_receipt.json").read_text(encoding="utf-8"))
    require(auth_receipt["status"] == "D6A_R1_S1_exact_assignment_implementation_zero_step_authorized", "S1 authorization status drifted")
    result_receipt = json.loads((result_dir / "s1_artificial_zero_step_receipt.json").read_text(encoding="utf-8"))
    require(result_receipt["status"] == "D6A_R1_S1_exact_assignment_artificial_zero_step_equivalence_failed", "S1 result status drifted")
    require(result_receipt["cases"] == 168, "S1 result case count drifted")
    require(result_receipt["slot_to_candidate_exact"] == result_receipt["hard_assignment_exact"] == 128, "S1 mapping result drifted")
    require(result_receipt["sorted_selected_indices_exact"] == 168, "S1 selected set drifted")
    require(result_receipt["adjusted_objective_exact"] == 160, "S1 objective drifted")
    require(result_receipt["all_equivalence_gates_passed"] is False, "S1 negative result changed")
    require(result_receipt["performance_timing_calls"] == result_receipt["timed_runs"] == 0, "S1 timing occurred")
    require(result_receipt["D6_cases_accessed"] == result_receipt["optimizer_steps"] == result_receipt["model_updates"] == 0, "S1 boundary drifted")
    return repo_hashes, canonical_hashes


def build_outputs(protocol: Mapping[str, Any], repo_hashes: Mapping[str, str], parent_hashes: Mapping[str, str]) -> dict[str, bytes]:
    suite = protocol["synthetic_equivalence_suite"]
    outputs = {
        "S0_S2_zero_step.template.json": canonical_json({
            "runnable": False,
            "separate_implementation_and_execution_authorization_required": True,
            "protocol_id": PROTOCOL_ID,
            "cases": 168,
            "performance_timing": False,
            "warmup_runs": 0,
            "timed_runs": 0,
            "optimizer_constructed": False,
            "training": False,
        }),
        "certified_fast_path_contract.json": canonical_json({
            "candidate_definitions": protocol["candidate_definitions"],
            "certification_contract": protocol["certification_contract"],
            "equivalence_hard_gate": protocol["equivalence_hard_gate"],
            "routing_integrity_gate": protocol["routing_integrity_gate"],
        }),
        "protocol_v1.json": PROTOCOL.read_bytes(),
        "synthetic_equivalence_suite.json": canonical_json(suite),
    }
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "D6A_R1_S2_certified_fast_path_feasibility_protocol_frozen_non_runnable",
        "protocol_sha256": sha256_file(PROTOCOL),
        "repository_parent_sha256": dict(repo_hashes),
        "canonical_S1_parent_sha256": dict(parent_hashes),
        "S1_result_manifest_sha256": S1_RESULT["files.sha256"],
        "S1_result_status": protocol["frozen_parent"]["S1_result_status"],
        "equivalence_cases": 168,
        "equivalence_required": "168/168_for_slot_selected_hard_and_objective",
        "certified_fast_path_cases_minimum": 96,
        "edge_exclusion_solves_per_candidate_case": 32,
        "S2_implementation_runs": 0,
        "timing_calls": 0,
        "warmup_runs": 0,
        "timed_runs": 0,
        "optimizer_steps": 0,
        "model_updates": 0,
        "D6_cases_accessed": 0,
        **protocol["permission_boundary"],
    }
    outputs["protocol_lock_receipt.json"] = canonical_json(receipt)
    outputs["protocol_lock_report_zh.md"] = (
        "# Mamba v1.6 D6-A R1 S2 certified fast-path feasibility protocol lock\n\n"
        "- Parent：S1 168-case frozen negative；slot/hard=128/168，selected=168/168，objective=160/168。\n"
        "- S2：tie-safe row-top32 union + cutoff guard + 32-edge-exclusion uniqueness certificate。\n"
        "- Uncertified：必须独立执行完整 S0，并直接返回 S0 输出。\n"
        "- Semantic gate：slot、selected、hard、objective 全部 168/168。\n"
        "- Routing gate：certified fast path >= 96/168；false-positive certificate = 0。\n"
        "- 当前 timing/warmup/timed/optimizer/D6 access 均为 0。\n"
        "- 只冻结不可运行协议；implementation、zero-step 与 benchmark 均需另行授权。\n"
        "- Production、formal rerun、training、seed-1、D6-B、selection、sealed 均锁定。\n"
    ).encode("utf-8")
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    ).encode("ascii")
    return outputs


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    outputs = dict(outputs)
    if output_dir.exists():
        existing = {
            path.relative_to(output_dir).as_posix(): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        require(existing == outputs, f"Existing S2 protocol lock drifted: {output_dir}")
        print(f"[locked] existing S2 protocol lock is byte-identical: {output_dir}")
        return
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            target = working / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        working.replace(output_dir)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise
    print(f"[saved] immutable S2 certified fast-path protocol: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo_root", type=Path, default=ROOT)
    parser.add_argument("--canonical_parent_dir", type=Path, required=True)
    parser.add_argument("--restoration_dir", type=Path, required=True)
    parser.add_argument("--authorization_dir", type=Path, required=True)
    parser.add_argument("--config_dir", type=Path, required=True)
    parser.add_argument("--result_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    repo_hashes, parent_hashes = verify_lineage(
        args.repo_root.resolve(),
        args.canonical_parent_dir.resolve(),
        args.restoration_dir.resolve(),
        args.authorization_dir.resolve(),
        args.config_dir.resolve(),
        args.result_dir.resolve(),
    )
    outputs = build_outputs(protocol, repo_hashes, parent_hashes)
    write_locked(outputs, args.out_dir.resolve())
    print("[done] D6-A R1 S2 certified fast-path feasibility protocol frozen")
    print("[authorized-next] separate S2 shadow implementation and 168-case artificial zero-step only")
    print("[locked] timing=false benchmark=false production=false training=false seed1=false D6B=false sealed=false")


if __name__ == "__main__":
    main()
