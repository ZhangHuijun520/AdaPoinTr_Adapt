#!/usr/bin/env python3
"""Unit tests for the D6 terminal source125 acquisition lock."""

from __future__ import annotations

import tempfile
from pathlib import Path

from lock_mamba_v16_d6_source125_acquisition import (
    partition_remaining_archives,
    partition_source125,
    verify_prior_sources,
    write_locked,
)


def archive(start: int, end: int) -> dict:
    return {
        "id": start,
        "name": f"A{start:04d}-A{end:04d}.zip",
        "start_index": start,
        "end_index": end,
        "skull_count": end - start + 1,
        "size": 1000 + start,
        "normalized_md5": f"{start:032x}",
        "download_url": f"https://example.invalid/{start}",
    }


def archive_ids(items: list[dict]) -> list[str]:
    return [
        f"A{index:04d}"
        for item in items
        for index in range(item["start_index"], item["end_index"] + 1)
    ]


def expect_failure(fn, text: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError(f"Expected RuntimeError containing {text!r}")


def main() -> None:
    healthy = [archive(index, index + 4) for index in range(1, 501, 5)]

    remaining_names = {
        "A0051-A0055.zip",
        "A0101-A0105.zip",
        "A0151-A0155.zip",
        "A0201-A0205.zip",
        "A0251-A0255.zip",
        "A0301-A0305.zip",
        "A0351-A0355.zip",
        "A0401-A0405.zip",
        "A0451-A0455.zip",
        "A0061-A0065.zip",
        "A0111-A0115.zip",
        "A0161-A0165.zip",
        "A0211-A0215.zip",
        "A0261-A0265.zip",
        "A0311-A0315.zip",
        "A0361-A0365.zip",
        "A0411-A0415.zip",
        "A0461-A0465.zip",
        "A0071-A0075.zip",
        "A0171-A0175.zip",
        "A0271-A0275.zip",
        "A0371-A0375.zip",
        "A0421-A0425.zip",
        "A0471-A0475.zip",
        "A0481-A0485.zip",
    }
    remaining = [item for item in healthy if item["name"] in remaining_names]
    assert len(remaining) == 25
    prior_archives = [item for item in healthy if item["name"] not in remaining_names]
    prior = archive_ids(prior_archives)
    assert len(prior) == 375

    d3, d4, d5 = prior[:125], prior[125:225], prior[225:]
    verified = verify_prior_sources(d3, d4, d5)
    assert verified == sorted(prior)

    occupied, residual = partition_remaining_archives(healthy, verified)
    assert len(occupied) == 75
    assert len(residual) == 25
    assert len(archive_ids(residual)) == 125

    parts_a = partition_source125(residual, "fixed-d6-test-salt")
    parts_b = partition_source125(list(reversed(residual)), "fixed-d6-test-salt")
    assert [item["name"] for item in parts_a["development"]] == [
        item["name"] for item in parts_b["development"]
    ]
    assert [item["name"] for item in parts_a["proposal_confirmation"]] == [
        item["name"] for item in parts_b["proposal_confirmation"]
    ]
    assert len(parts_a["development"]) == 20
    assert len(parts_a["proposal_confirmation"]) == 5
    assert len(archive_ids(parts_a["development"])) == 100
    assert len(archive_ids(parts_a["proposal_confirmation"])) == 25
    assert {
        item["macro_stratum"] for item in parts_a["proposal_confirmation"]
    } == {"S1", "S2", "S3", "S4", "S5"}

    expect_failure(
        lambda: verify_prior_sources(d3[:-1], d4, d5),
        "Expected exact D3/D4/D5 source counts",
    )
    expect_failure(
        lambda: verify_prior_sources(d3, d4[:-1] + [d3[0]], d5),
        "pairwise disjoint",
    )
    expect_failure(
        lambda: partition_remaining_archives(healthy, verified[:-1]),
        "partially overlaps D3/D4/D5 sources",
    )
    expect_failure(
        lambda: partition_source125(
            [item for item in residual if item["start_index"] > 150],
            "fixed-d6-test-salt",
        ),
        "without remaining archives",
    )

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "lock"
        files = {"a.txt": b"fixed\n", "files.sha256": b"placeholder\n"}
        write_locked(files, output)
        write_locked(files, output)
        expect_failure(
            lambda: write_locked({"a.txt": b"drift\n"}, output),
            "Refusing to overwrite non-identical D6 source125 lock",
        )

    print("[ok] D6 prior union is exact 125/100/150 = 375 and pairwise disjoint")
    print("[ok] remaining pool is exact 125 sources in 25 complete archives")
    print("[ok] blind macro-stratified partition is deterministic 100/25")
    print("[locked] geometry=false extraction=false training=false confirmation=false")


if __name__ == "__main__":
    main()

