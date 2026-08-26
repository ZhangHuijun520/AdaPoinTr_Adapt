#!/usr/bin/env python3
"""Boundary tests for the MUG500+ M2 100/25 source-skull data lock."""

from __future__ import annotations

import copy
import hashlib
import json

from lock_mug500plus_m2_source_split_v1 import (
    DEFAULT_PROTOCOL,
    make_partitions,
    read_and_validate_manifest,
    render_outputs,
    validate_protocol,
)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_records(protocol):
    records = []
    for index in range(125):
        skull_id = f"mug500plus__A{index + 1:04d}"
        for defect in protocol["input_contract"]["defect_types"]:
            case_id = f"{skull_id}__{defect}"
            records.append({
                "case_id": case_id,
                "skull_id": skull_id,
                "defect_type": defect,
                "source_dataset": protocol["input_contract"]["source_dataset"],
                "source_asset_path": f"../../raw/{skull_id}.stl",
                "source_asset_sha256": digest(f"source-{skull_id}"),
                "source_surface_fingerprint_sha256": digest(f"surface-{skull_id}"),
                "surface_fingerprint_algorithm_sha256": protocol["input_contract"]["surface_fingerprint_algorithm_sha256"],
                "point_path": f"../cases/{case_id}.npz",
                "derived_case_sha256": digest(case_id),
                "generator_sha256": protocol["input_contract"]["generator_sha256"],
            })
    return records


def expect_failure(function, text):
    try:
        function()
    except RuntimeError as exc:
        assert text.lower() in str(exc).lower(), (text, str(exc))
    else:
        raise AssertionError(f"Expected rejection containing: {text}")


def main():
    protocol = json.loads(DEFAULT_PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    records = build_records(protocol)

    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "manifest.jsonl"
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in records),
            encoding="utf-8",
        )
        parsed, by_skull = read_and_validate_manifest(path, protocol)
        holdout, folds = make_partitions(sorted(by_skull), protocol)
        assert len(holdout) == 25
        assert len(folds) == 100
        assert sorted(folds.values()).count("A") == 25
        assert sorted(folds.values()).count("B") == 25
        assert sorted(folds.values()).count("C") == 25
        assert sorted(folds.values()).count("D") == 25
        upstream = {"m2_portable_manifest": digest("manifest")}
        first = render_outputs(
            parsed, by_skull, protocol, b"protocol", upstream
        )
        second = render_outputs(
            parsed, by_skull, protocol, b"protocol", upstream
        )
        assert first == second
        receipt = json.loads(first["source_split_lock_receipt.json"])
        assert receipt["training_unlocked"] is False
        assert receipt["holdout_metrics_consumed"] is False

        broken = copy.deepcopy(records)
        broken.pop()
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in broken),
            encoding="utf-8",
        )
        expect_failure(
            lambda: read_and_validate_manifest(path, protocol), "500 manifest"
        )

    altered = copy.deepcopy(protocol)
    altered["split_rule"]["salt"] = "post-outcome-salt"
    expect_failure(lambda: validate_protocol(altered), "split rule")
    short_hash = copy.deepcopy(protocol)
    short_hash["lineage"]["m2_generation_audit"][
        "files_manifest_sha256"
    ] = "0" * 63
    expect_failure(lambda: validate_protocol(short_hash), "lineage sha256")
    permissive = copy.deepcopy(protocol)
    permissive["holdout_policy"][
        "holdout_metrics_allowed_before_method_freeze"
    ] = True
    expect_failure(lambda: validate_protocol(permissive), "holdout")

    print("[ok] exact deterministic 100/25 source-skull split")
    print("[ok] four development folds contain exactly 25 skulls each")
    print("[ok] all four cases from one skull remain in one partition/fold")
    print("[ok] salt mutation and early holdout access are rejected")
    print("[ok] data-lock generation does not unlock training")


if __name__ == "__main__":
    main()
