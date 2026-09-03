#!/usr/bin/env python3
"""Contract tests for the D6-A R1 gradient-calibration preregistration."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "lock_mamba_v16_d6a_gradient_ratio_calibration_protocol.py"
SPEC = importlib.util.spec_from_file_location("d6_calibration_lock", MODULE_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

FAMILIES = (
    "ellipsoid_large",
    "ellipsoid_medium",
    "ellipsoid_small",
    "irregular_medium",
)


def must_fail(protocol, label: str) -> None:
    try:
        MOD.validate_protocol(protocol)
    except RuntimeError:
        return
    raise AssertionError(f"Expected hard failure: {label}")


def write_fold_files(directory: Path) -> None:
    directory.mkdir(parents=True)
    for fold in MOD.FOLDS:
        rows = [
            f"mug500plus__A{index:04d}__{family}"
            for index in range(1, 76)
            for family in FAMILIES
        ]
        (directory / f"fold{fold}_train_case_ids.txt").write_bytes(
            ("\n".join(rows) + "\n").encode("utf-8")
        )


def main() -> None:
    protocol = MOD.read_protocol()
    MOD.validate_protocol(protocol)

    tampered = copy.deepcopy(protocol)
    tampered["scientific_role"]["R0_new_weight_calibration"] = True
    must_fail(tampered, "R0 redefinition")

    tampered = copy.deepcopy(protocol)
    tampered["data_boundary"]["dev_cases_accessed"] = 1
    must_fail(tampered, "dev access")

    tampered = copy.deepcopy(protocol)
    tampered["gradient_measurement"]["common_gradient_object"] = "all_parameters"
    must_fail(tampered, "disjoint gradient object")

    tampered = copy.deepcopy(protocol)
    tampered["weight_rule"]["target_gradient_ratio_to_L_point"][
        "lambda_support_times_L_support"
    ] = 0.4
    must_fail(tampered, "support target drift")

    tampered = copy.deepcopy(protocol)
    tampered["weight_rule"]["cross_fold_pooling_allowed"] = True
    must_fail(tampered, "cross-fold pooling")

    tampered = copy.deepcopy(protocol)
    tampered["protocol_lock_effect"]["calibration_execution_authorized"] = True
    must_fail(tampered, "calibration side effect")

    with tempfile.TemporaryDirectory() as temporary:
        fourfold = Path(temporary) / "fourfold"
        write_fold_files(fourfold)
        repo_hashes = {key: expected for key, (_, expected) in MOD.REPO_PARENTS.items()}
        parent_hashes = {
            key: expected for key, (_, _, expected) in MOD.PARENT_FILES.items()
        }
        first = MOD.build_outputs(protocol, fourfold, repo_hashes, parent_hashes)
        second = MOD.build_outputs(protocol, fourfold, repo_hashes, parent_hashes)
        assert first == second
        assert "files.sha256" in first

        receipt = json.loads(first["protocol_lock_receipt.json"])
        assert receipt["status"] == (
            "D6A_R1_gradient_calibration_protocol_frozen_execution_not_authorized"
        )
        assert receipt["optimizer_steps"] == 0
        assert receipt["calibration_execution_authorized"] is False
        assert receipt["seed0_training_authorized"] is False
        assert set(receipt["folds"]) == set(MOD.FOLDS)

        for fold in MOD.FOLDS:
            schedule = first[f"folds/fold{fold}_batch_case_ids.tsv"].decode().splitlines()
            assert len(schedule) == 8
            measured = []
            for row in schedule:
                fields = row.split("\t")
                assert len(fields) == 9
                cases = fields[1:]
                assert len({MOD.source_id(case_id) for case_id in cases}) == 2
                for source in {MOD.source_id(case_id) for case_id in cases}:
                    families = {
                        case_id.split("__")[2]
                        for case_id in cases
                        if MOD.source_id(case_id) == source
                    }
                    assert families == set(FAMILIES)
                measured.extend(cases)
            assert len(measured) == 64 and len(set(measured)) == 64
            assert len({MOD.source_id(case_id) for case_id in measured}) == 16

    print("[ok] R1-only common-F gradient and 0.5/0.1 target contracts are fixed")
    print("[ok] four deterministic fold schedules contain 8 x 8 train-only case slots")
    print("[ok] dev access, cross-fold pooling, R0 redefinition and permission escalation fail")
    print("[locked] calibration=false training=false seed1=false D6B=false confirmation=false")


if __name__ == "__main__":
    main()
