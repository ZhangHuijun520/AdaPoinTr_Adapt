#!/usr/bin/env python3
"""Unit tests for D4 source100 duplicate and overlap gates."""

from lock_mamba_v14_d4_mug500plus_source100_qc import (
    duplicate_groups,
    overlap_groups,
)


def main() -> None:
    current = [
        {"case_id": "A0001", "hash": "a"},
        {"case_id": "A0002", "hash": "b"},
    ]
    prior = [{"case_id": "A0100", "hash": "c"}]
    assert duplicate_groups(current, "hash") == {}
    assert overlap_groups(current, prior, "hash") == {}

    duplicated = current + [{"case_id": "A0003", "hash": "a"}]
    assert duplicate_groups(duplicated, "hash") == {"a": ["A0001", "A0003"]}
    overlapping = prior + [{"case_id": "A0101", "hash": "b"}]
    result = overlap_groups(current, overlapping, "hash")
    assert result["b"] == {"d4": ["A0002"], "d3": ["A0101"]}
    print("[ok] D4 global duplicate and prior-source overlap gates are exact")


if __name__ == "__main__":
    main()
