#!/usr/bin/env python3
"""Validate and immutably lock the MUG500+ overlap audit v2.1 amendment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict


PROTOCOL_ID = (
    "mug500plus-m2-protected-overlap-audit-v2.1-source-stratified-provenance"
)
EVIDENCE_ID = "mug500plus-skullbreak-skullfix-source-provenance-v1"
REQUIRED_DOIS = {
    "10.1016/j.dib.2021.107524",
    "10.1016/j.dib.2021.106902",
}
DEFAULT_PROTOCOL = Path(__file__).resolve().parents[1] / "docs" / (
    "mamba_v13_d3_mug500plus_phase_m2_overlap_audit_protocol_v21.json"
)
DEFAULT_PROVENANCE = Path(__file__).resolve().parents[1] / "docs" / (
    "mug500plus_skullbreak_skullfix_source_provenance_v1.json"
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_provenance(evidence: Dict[str, Any]) -> None:
    if (
        evidence.get("evidence_id") != EVIDENCE_ID
        or evidence.get("status") != "frozen_primary_source_metadata"
    ):
        raise RuntimeError("Unexpected source-provenance evidence")
    assertions = evidence.get("assertions", {})
    required_true = {
        "reported_acquisition_cohorts_are_distinct",
        "reported_institutions_are_distinct",
        "reported_countries_are_distinct",
        "provenance_must_be_combined_with_exact_hash_and_geometry_audits",
    }
    if any(assertions.get(name) is not True for name in required_true):
        raise RuntimeError("Independent-source assertions are incomplete")
    if assertions.get("provenance_alone_proves_zero_duplicate_geometry") is not False:
        raise RuntimeError("Provenance must not be treated as geometric proof")
    dois = {
        item["primary_reference"]["doi"]
        for item in evidence.get("datasets", {}).values()
    }
    if dois != REQUIRED_DOIS:
        raise RuntimeError(f"Unexpected provenance references: {dois}")
    datasets = evidence["datasets"]
    if (
        datasets["mug500plus"]["cohort"]
        == datasets["skullbreak_skullfix"]["cohort"]
        or datasets["mug500plus"]["institution"]
        == datasets["skullbreak_skullfix"]["institution"]
    ):
        raise RuntimeError("Reported source cohorts are not independent")


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if (
        protocol.get("protocol_id") != PROTOCOL_ID
        or protocol.get("status") != "preregistered_not_adjudicated"
        or protocol.get("lineage", {}).get("amendment_is_post_v2") is not True
        or protocol.get("lineage", {}).get("prior_results_remain_immutable")
        is not True
    ):
        raise RuntimeError("v2.1 protocol is not a transparent post-v2 amendment")

    access = protocol.get("access_boundary", {})
    if (
        access.get("raw_protected_arrays_reopened") is not False
        or access.get("model_predictions_allowed") is not False
        or access.get("model_metrics_allowed") is not False
        or access.get("defect_or_implant_arrays_allowed") is not False
        or access.get("MUG500plus_B_series_or_craniotomy_allowed") is not False
    ):
        raise RuntimeError("v2.1 access boundary is invalid")

    calibration = protocol.get("source_stratified_calibration", {})
    domains = calibration.get("domains", {})
    expected_counts = {
        "mug500plus": (125, 125),
        "skullbreak": (134, 134),
        "skullfix": (0, 100),
    }
    for domain, (positive, negative) in expected_counts.items():
        item = domains.get(domain, {})
        if (
            int(item.get("positive_pairs_required", -1)) != positive
            or int(item.get("negative_pairs_required", -1)) != negative
        ):
            raise RuntimeError(f"Unexpected calibration counts for {domain}")
    if calibration.get("pooled_cross_domain_extrema_forbidden") is not True:
        raise RuntimeError("Pooled cross-domain extrema must remain forbidden")

    geometry = protocol.get("geometry_adjudication", {})
    envelope = geometry.get("duplicate_like_envelope", {})
    if (
        int(geometry.get("expected_candidate_pairs", 0)) != 1250
        or int(geometry.get("expected_pairs_per_protected_dataset", 0)) != 625
        or geometry.get("expected_descriptor_ranks") != [1, 2, 3, 4, 5]
        or envelope.get("source")
        != "mug500plus positive calibration pairs only"
        or geometry.get("required_duplicate_like_candidates") != 0
        or geometry.get("manual_case_exclusion_allowed") is not False
    ):
        raise RuntimeError("v2.1 geometry adjudication is not frozen")

    gate = protocol.get("automatic_gate", {})
    if (
        gate.get("training_starts_automatically") is not False
        or gate.get("pass_effect")
        != "permit_only_the_100_25_source_skull_data_lock_step"
    ):
        raise RuntimeError("v2.1 must not directly unlock training")

    forbidden = set(protocol.get("forbidden", []))
    required_forbidden = {
        "rewrite_or_delete_v1_or_v2_results",
        "recompute_thresholds_from_cross_dataset_candidate_pairs",
        "pool_calibration_extrema_across_source_domains",
        "invent_skullfix_positive_pairs",
        "remove_individual_MUG_cases_after_adjudication",
        "start_D3_training_before_a_separate_100_25_data_lock",
    }
    if not required_forbidden.issubset(forbidden):
        raise RuntimeError("v2.1 forbidden-action list is incomplete")


def validate_frozen_inputs(protocol: Dict[str, Any], v2_dir: Path) -> None:
    expected = protocol["frozen_inputs"]["v2_files"]
    actual_names = {path.name for path in v2_dir.iterdir() if path.is_file()}
    for name, expected_hash in expected.items():
        path = v2_dir / name
        if name not in actual_names or sha256_file(path) != expected_hash:
            raise RuntimeError(f"Frozen v2 input mismatch: {path}")
    summary = json.loads((v2_dir / "overlap_audit_v2_summary.json").read_text())
    if (
        summary.get("status") != "blocked_calibration_not_separated"
        or summary.get("automatic_gate_passed") is not False
        or summary.get("training_unlocked") is not False
    ):
        raise RuntimeError("v2 frozen outcome was altered")


def render_outputs(
    protocol_path: Path,
    provenance_path: Path,
    protocol: Dict[str, Any],
    v2_dir: Path,
) -> Dict[str, bytes]:
    protocol_bytes = protocol_path.read_bytes()
    provenance_bytes = provenance_path.read_bytes()
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "protocol_locked_not_adjudicated",
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "source_provenance_sha256": sha256_bytes(provenance_bytes),
        "source_v1_summary_sha256": protocol["lineage"]["v1"][
            "summary_sha256"
        ],
        "source_v2_summary_sha256": sha256_file(
            v2_dir / "overlap_audit_v2_summary.json"
        ),
        "source_v2_files_manifest_sha256": sha256_file(
            v2_dir / "files.sha256"
        ),
        "calibration_mode": "source_stratified",
        "cross_dataset_threshold_fitting_allowed": False,
        "adjudication_started": False,
        "data_split_lock_allowed": False,
        "training_unlocked": False,
        "model_predictions_used": False,
        "model_metrics_used": False,
    }
    files = {
        "overlap_audit_protocol_v21.json": protocol_bytes,
        "source_provenance_v1.json": provenance_bytes,
        "protocol_lock_receipt.json": (
            json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }
    hashes = [f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    return files


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical v2.1 lock")
        print(f"[locked] existing v2.1 protocol is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] immutable v2.1 protocol lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--provenance_json", type=Path, default=DEFAULT_PROVENANCE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol_json.resolve()
    provenance_path = args.provenance_json.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    validate_provenance(provenance)
    if (
        sha256_file(provenance_path)
        != protocol["frozen_inputs"]["source_provenance_sha256"]
    ):
        raise RuntimeError("Source-provenance hash does not match v2.1 protocol")
    v2_dir = args.v2_audit_dir.resolve()
    validate_frozen_inputs(protocol, v2_dir)
    files = render_outputs(protocol_path, provenance_path, protocol, v2_dir)
    write_locked(files, args.output_dir.resolve())
    receipt = json.loads(files["protocol_lock_receipt.json"])
    print(f"[sha256] protocol={receipt['protocol_sha256']}")
    print(f"[sha256] provenance={receipt['source_provenance_sha256']}")
    print("[locked] adjudication has not started")
    print("[locked] 100/25 data lock and D3 training remain disabled")


if __name__ == "__main__":
    main()
