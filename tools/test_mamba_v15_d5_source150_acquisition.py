#!/usr/bin/env python3
"""Unit tests for the D5 MUG500+ source150 three-partition lock."""

from __future__ import annotations

import tempfile
from pathlib import Path

from lock_mamba_v15_d5_source150_acquisition import (
    partition_archives,
    partition_selected,
    select_archives,
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


def expect_failure(fn, text: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError(f"Expected RuntimeError containing {text!r}")


def source_ids(items: list[dict]) -> list[str]:
    return [
        f"A{index:04d}"
        for item in items
        for index in range(item["start_index"], item["end_index"] + 1)
    ]


def main() -> None:
    healthy = [archive(index, index + 4) for index in range(1, 501, 5)]
    by_stratum = {
        stratum: healthy[stratum * 10 : (stratum + 1) * 10]
        for stratum in range(10)
    }
    d3_archives = [
        item
        for stratum, items in by_stratum.items()
        for item in items[: (3 if stratum < 5 else 2)]
    ]
    d3 = source_ids(d3_archives)
    assert len(d3) == 125
    development, holdout = d3[:100], d3[100:]

    d3_names = {item["name"] for item in d3_archives}
    d4_archives = []
    for items in by_stratum.values():
        available = [item for item in items if item["name"] not in d3_names]
        d4_archives.extend(available[:2])
    d4 = source_ids(d4_archives)
    prior = verify_prior_sources(d3, development, holdout, d4)
    assert len(prior) == 225

    occupied, unused = partition_archives(healthy, prior)
    assert sum(item["skull_count"] for item in occupied) == 225
    assert sum(item["skull_count"] for item in unused) == 275

    selected_a = select_archives(unused, "fixed-d5-test-salt", 150)
    selected_b = select_archives(list(reversed(unused)), "fixed-d5-test-salt", 150)
    assert [item["name"] for item in selected_a] == [
        item["name"] for item in selected_b
    ]
    assert sum(item["skull_count"] for item in selected_a) == 150

    partitions = partition_selected(selected_a)
    assert {name: len(source_ids(items)) for name, items in partitions.items()} == {
        "development": 100,
        "proposal_confirmation": 25,
        "completion_holdout": 25,
    }
    sets = {name: set(source_ids(items)) for name, items in partitions.items()}
    assert not sets["development"] & sets["proposal_confirmation"]
    assert not sets["development"] & sets["completion_holdout"]
    assert not sets["proposal_confirmation"] & sets["completion_holdout"]
    assert not set().union(*sets.values()) & set(prior)

    expect_failure(
        lambda: verify_prior_sources(
            d3,
            development[:-1],
            holdout,
            d4,
        ),
        "Expected exact D3 125",
    )
    expect_failure(
        lambda: verify_prior_sources(
            d3,
            development,
            holdout,
            d4[:-1] + [d3[0]],
        ),
        "D3 and D4 source IDs overlap",
    )
    expect_failure(
        lambda: partition_archives(healthy, prior[:-1]),
        "partially overlaps prior D3/D4 sources",
    )
    expect_failure(
        lambda: select_archives(unused, "fixed-d5-test-salt", 151),
        "Cannot reach exact source target",
    )

    crossing = [archive(index, index + 4) for index in range(1, 96, 5)]
    crossing.append(archive(96, 105))
    crossing.extend(archive(index, index + 4) for index in range(106, 146, 5))
    expect_failure(
        lambda: partition_selected(crossing),
        "crosses frozen development boundary",
    )

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "lock"
        files = {"a.txt": b"fixed\n", "files.sha256": b"placeholder\n"}
        write_locked(files, output)
        write_locked(files, output)
        expect_failure(
            lambda: write_locked({"a.txt": b"drift\n"}, output),
            "Refusing to overwrite non-identical source150 lock",
        )

    print("[ok] D5 selection is deterministic, archive-complete, and 150 exact")
    print("[ok] source partitions are exact 100/25/25 and pairwise disjoint")
    print("[ok] D3/D4 overlap, partial ZIPs, boundary crossing, and drift fail hard")
    print("[sealed] confirmation25 and completion-holdout25 remain archive-only")


if __name__ == "__main__":
    main()
