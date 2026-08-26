#!/usr/bin/env python3
"""Protocol-boundary tests for the MUG500+ overlap audit v2.1 amendment."""

from __future__ import annotations

import copy
import json

from lock_mug500plus_m2_overlap_v21_protocol import (
    DEFAULT_PROTOCOL,
    DEFAULT_PROVENANCE,
    validate_protocol,
    validate_provenance,
)


def expect_failure(function, value, text: str) -> None:
    try:
        function(value)
    except RuntimeError as exc:
        assert text.lower() in str(exc).lower(), (text, str(exc))
    else:
        raise AssertionError(f"Expected rejection containing: {text}")


def main() -> None:
    protocol = json.loads(DEFAULT_PROTOCOL.read_text(encoding="utf-8"))
    provenance = json.loads(DEFAULT_PROVENANCE.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    validate_provenance(provenance)

    pooled = copy.deepcopy(protocol)
    pooled["source_stratified_calibration"][
        "pooled_cross_domain_extrema_forbidden"
    ] = False
    expect_failure(validate_protocol, pooled, "pooled")

    invented = copy.deepcopy(protocol)
    invented["source_stratified_calibration"]["domains"]["skullfix"][
        "positive_pairs_required"
    ] = 100
    expect_failure(validate_protocol, invented, "skullfix")

    direct_training = copy.deepcopy(protocol)
    direct_training["automatic_gate"]["training_starts_automatically"] = True
    expect_failure(validate_protocol, direct_training, "training")

    case_removal = copy.deepcopy(protocol)
    case_removal["geometry_adjudication"]["manual_case_exclusion_allowed"] = True
    expect_failure(validate_protocol, case_removal, "geometry")

    same_cohort = copy.deepcopy(provenance)
    same_cohort["datasets"]["skullbreak_skullfix"]["cohort"] = same_cohort[
        "datasets"
    ]["mug500plus"]["cohort"]
    expect_failure(validate_provenance, same_cohort, "independent")

    provenance_only = copy.deepcopy(provenance)
    provenance_only["assertions"][
        "provenance_alone_proves_zero_duplicate_geometry"
    ] = True
    expect_failure(validate_provenance, provenance_only, "geometric")

    print("[ok] v1/v2 failure lineage remains immutable")
    print("[ok] source-stratified calibration forbids pooled extrema")
    print("[ok] SkullFix positive controls cannot be invented")
    print("[ok] provenance cannot replace exact-hash and geometry evidence")
    print("[ok] protocol can permit only a later 100/25 data-lock step")


if __name__ == "__main__":
    main()
