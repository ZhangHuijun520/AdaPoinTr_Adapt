#!/usr/bin/env python3
"""Boundary tests for the D5 development generation/fourfold protocol."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from generate_mamba_v15_d5_mug500plus_development_cases import (
    build_effective_protocol,
)
from lock_mamba_v15_d5_mug500plus_development_fourfold_protocol import (
    EXPECTED_DEFECT_TYPES,
    EXPECTED_PARTITION_HASHES,
    assign_folds,
    render_outputs,
    validate_protocol,
    write_locked,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = (
    ROOT
    / "docs"
    / "mamba_v15_d5_mug500plus_development_generation_fourfold_protocol_v1.json"
)
BASE_PROTOCOL_PATH = (
    ROOT
    / "docs"
    / "mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json"
)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def expect_failure(function, text: str) -> None:
    try:
        function()
    except RuntimeError as exc:
        assert text.lower() in str(exc).lower(), (text, str(exc))
    else:
        raise AssertionError(f"Expected RuntimeError containing {text!r}")


def source_rows():
    return [
        {
            "case_id": f"A{index:04d}",
            "portable_source_path": f"development/batch_001/A{index:04d}_clear.stl",
            "source_asset_sha256": digest(f"asset-{index}"),
            "source_surface_fingerprint_sha256": digest(f"surface-{index}"),
            "surface_fingerprint_algorithm_sha256": digest("algorithm"),
            "file_bytes": "1000",
            "triangle_count": "100",
            "qc_pass": "True",
            "batch_id": "1",
        }
        for index in range(1, 101)
    ]


def partition_ids():
    return {
        "development": [f"A{index:04d}" for index in range(1, 101)],
        "proposal_confirmation": [f"A{index:04d}" for index in range(101, 126)],
        "completion_holdout": [f"A{index:04d}" for index in range(126, 151)],
    }


def main() -> None:
    protocol_bytes = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_bytes)
    base = json.loads(BASE_PROTOCOL_PATH.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    folds = assign_folds([row["case_id"] for row in source_rows()], protocol)
    assert {fold: list(folds.values()).count(fold) for fold in "ABCD"} == {
        fold: 25 for fold in "ABCD"
    }
    effective = build_effective_protocol(protocol, base)
    for section in protocol["lineage"]["m2_v1_engine"]["inherited_sections"]:
        assert effective[section] == base[section]
    assert tuple(effective["defect_families"]) == EXPECTED_DEFECT_TYPES
    assert effective["derived_dataset"]["expected_cases"] == 400
    assert effective["split_policy"]["sealed_partitions_excluded"] is True

    placeholders = {
        "base_protocol": BASE_PROTOCOL_PATH,
        "engine": ROOT / "tools" / "generate_mug500plus_m2_synthetic_defects.py",
        "generator_entry": ROOT
        / "tools"
        / "generate_mamba_v15_d5_mug500plus_development_cases.py",
        "protocol_locker": ROOT
        / "tools"
        / "lock_mamba_v15_d5_mug500plus_development_fourfold_protocol.py",
        "tests": Path(__file__),
    }
    first = render_outputs(
        source_rows(), partition_ids(), protocol, protocol_bytes, placeholders
    )
    second = render_outputs(
        source_rows(), partition_ids(), protocol, protocol_bytes, placeholders
    )
    assert first == second
    receipt = json.loads(first["d5_development_protocol_lock_receipt.json"])
    assert receipt["counts"]["planned_development_cases"] == 400
    assert receipt["D5_development_synthetic_generation_authorized_next"] is True
    assert receipt["D5A_model_implementation_authorized"] is False
    assert receipt["D5A_training_authorized"] is False
    assert receipt["proposal_confirmation_accessed"] is False
    assert receipt["completion_holdout_accessed"] is False
    sealed = json.loads(first["sealed_partition_bindings.json"])
    assert sealed["proposal_confirmation"]["ids_sha256"] == EXPECTED_PARTITION_HASHES[
        "proposal_confirmation"
    ]
    assert sealed["completion_holdout"]["ids_sha256"] == EXPECTED_PARTITION_HASHES[
        "completion_holdout"
    ]
    assert all(
        item["geometry_accessed"] is False
        and item["archive_extracted"] is False
        and item["derived_cases_generated"] is False
        for item in sealed.values()
    )
    for fold in "ABCD":
        assert len(first[f"fold{fold}_dev_source_ids.txt"].splitlines()) == 25
        assert len(first[f"fold{fold}_train_source_ids.txt"].splitlines()) == 75
        assert len(first[f"fold{fold}_dev_case_ids.txt"].splitlines()) == 100
        assert len(first[f"fold{fold}_train_case_ids.txt"].splitlines()) == 300

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "lock"
        write_locked(first, output)
        write_locked(second, output)
        changed = dict(second)
        changed["development100_ids.txt"] = b"drift\n"
        expect_failure(
            lambda: write_locked(changed, output),
            "Refusing to overwrite a non-identical",
        )

    altered = copy.deepcopy(protocol)
    altered["four_fold_rule"]["salt"] = "post-result-salt"
    expect_failure(lambda: validate_protocol(altered), "four-fold")
    permissive = copy.deepcopy(protocol)
    permissive["lock_effect"]["D5A_training_authorized"] = True
    expect_failure(lambda: validate_protocol(permissive), "authorization")
    leaky = copy.deepcopy(protocol)
    leaky["sealed_partition_contract"]["geometry_may_be_read_by_this_stage"] = True
    expect_failure(lambda: validate_protocol(leaky), "sealed-partition")
    short = [row["case_id"] for row in source_rows()][:-1]
    expect_failure(lambda: assign_folds(short, protocol), "100 unique")

    print("[ok] D5 inherits the frozen M2 v1 geometry and sampling sections")
    print("[ok] development100 maps to deterministic 25/75 source-level folds")
    print("[ok] four cases per source remain together and total 400 planned cases")
    print("[ok] sealed ID hashes bind without geometry, extraction, or generation access")
    print("[locked] model=false training=false selection=false sealed=false")


if __name__ == "__main__":
    main()
