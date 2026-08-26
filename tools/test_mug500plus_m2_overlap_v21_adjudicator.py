#!/usr/bin/env python3
"""Boundary tests for the frozen-table-only MUG500+ v2.1 adjudicator."""

from __future__ import annotations

import copy
import json

from adjudicate_mug500plus_m2_overlap_v21 import (
    CANDIDATE_FIELDS,
    METRICS,
    adjudicate_geometry,
    summarize_calibration,
)
from lock_mug500plus_m2_overlap_v21_protocol import DEFAULT_PROTOCOL


def calibration_row(dataset: str, label: str, index: int, value: float):
    return {
        "label": label,
        "dataset": dataset,
        "pair_id": f"{dataset}-{label}-{index}",
        "first_case_id": f"{dataset}-first-{label}-{index}",
        "second_case_id": f"{dataset}-second-{label}-{index}",
        METRICS[0]: str(value),
        METRICS[1]: str(value * 2.0),
    }


def make_calibration(protocol):
    values = {
        ("mug500plus", "positive"): 0.050,
        ("mug500plus", "negative"): 0.060,
        ("skullbreak", "positive"): 0.040,
        ("skullbreak", "negative"): 0.045,
        ("skullfix", "negative"): 0.055,
    }
    rows = []
    for domain, item in protocol["source_stratified_calibration"]["domains"].items():
        for label, key in (
            ("positive", "positive_pairs_required"),
            ("negative", "negative_pairs_required"),
        ):
            for index in range(int(item[key])):
                rows.append(calibration_row(domain, label, index, values[(domain, label)]))
    return rows


def make_candidates(protocol):
    rows = []
    for dataset in ("skullbreak", "skullfix"):
        for skull_index in range(125):
            for rank in protocol["geometry_adjudication"]["expected_descriptor_ranks"]:
                row = dict(zip(CANDIDATE_FIELDS, [""] * len(CANDIDATE_FIELDS)))
                row.update({
                    "protected_dataset": dataset,
                    "mug_skull_id": f"mug-{skull_index:03d}",
                    "mug_case_id": f"mug-case-{skull_index:03d}",
                    "protected_skull_id": f"{dataset}-skull-{skull_index:03d}-{rank}",
                    "protected_case_id": f"{dataset}-case-{skull_index:03d}-{rank}",
                    "descriptor_rank": str(rank),
                    "descriptor_distance": "1.0",
                    METRICS[0]: "0.070",
                    METRICS[1]: "0.130",
                    "suspect_near_duplicate": "0",
                })
                rows.append(row)
    return rows


def expect_failure(function, text: str):
    try:
        function()
    except RuntimeError as exc:
        assert text.lower() in str(exc).lower(), (text, str(exc))
    else:
        raise AssertionError(f"Expected rejection containing: {text}")


def main():
    protocol = json.loads(DEFAULT_PROTOCOL.read_text(encoding="utf-8"))
    calibration_rows = make_calibration(protocol)
    _, summary = summarize_calibration(calibration_rows, protocol)
    assert summary["mug500plus"]["domain_separated"] is True
    assert summary["skullbreak"]["domain_separated"] is True
    assert summary["skullfix"]["domain_separated"] is None
    assert (
        summary["mug500plus"]["metrics"][METRICS[0]]["positive_q99"]
        > summary["skullbreak"]["metrics"][METRICS[0]]["negative_q01"]
    ), "Synthetic pooled extrema should overlap while source domains separate"

    invented = calibration_rows + [
        calibration_row("skullfix", "positive", 0, 0.01)
    ]
    expect_failure(
        lambda: summarize_calibration(invented, protocol), "unexpected calibration"
    )
    missing = calibration_rows[:-1]
    expect_failure(
        lambda: summarize_calibration(missing, protocol), "count mismatch"
    )

    candidates = make_candidates(protocol)
    _, geometry = adjudicate_geometry(candidates, protocol, 0.050, 0.100)
    assert geometry["duplicate_like_candidates"] == 0
    duplicate = copy.deepcopy(candidates)
    duplicate[0][METRICS[0]] = "0.049"
    duplicate[0][METRICS[1]] = "0.099"
    _, duplicate_geometry = adjudicate_geometry(
        duplicate, protocol, 0.050, 0.100
    )
    assert duplicate_geometry["duplicate_like_candidates"] == 1
    malformed = candidates[:-1]
    expect_failure(
        lambda: adjudicate_geometry(malformed, protocol, 0.050, 0.100),
        "candidate count",
    )

    print("[ok] source-stratified calibration passes despite pooled-domain overlap")
    print("[ok] SkullFix positive controls remain forbidden")
    print("[ok] frozen calibration counts are enforced")
    print("[ok] MUG-positive q99 envelope is conjunctive and deterministic")
    print("[ok] fixed 1,250-pair candidate panel is enforced")


if __name__ == "__main__":
    main()
