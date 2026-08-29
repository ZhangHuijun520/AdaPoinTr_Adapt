#!/usr/bin/env python3
"""Unit tests for the D4 MUG500+ source100 acquisition lock."""

from __future__ import annotations

import tempfile
from pathlib import Path

from lock_mamba_v14_d4_mug500plus_source100_acquisition import (
    partition_archives,
    select_archives,
    verify_prior_partition,
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


def main() -> None:
    healthy = [archive(index, index + 4) for index in range(1, 501, 5)]
    prior_archives = healthy[::4]
    old = [
        f"A{index:04d}"
        for item in prior_archives
        for index in range(item["start_index"], item["end_index"] + 1)
    ]
    development = old[:100]
    holdout = old[100:]
    verify_prior_partition(old, development, holdout)

    prior, unused = partition_archives(healthy, old)
    assert len(prior) == 25
    assert sum(item["skull_count"] for item in unused) == 375
    selected_a = select_archives(unused, "fixed-test-salt", 100)
    selected_b = select_archives(list(reversed(unused)), "fixed-test-salt", 100)
    assert [item["name"] for item in selected_a] == [item["name"] for item in selected_b]
    assert sum(item["skull_count"] for item in selected_a) == 100

    expect_failure(
        lambda: verify_prior_partition(old, development[:-1], holdout),
        "Expected exact 125 = 100 + 25",
    )
    partial_old = old[:-1]
    expect_failure(
        lambda: partition_archives(healthy, partial_old),
        "partially overlaps prior D3 sources",
    )
    expect_failure(
        lambda: select_archives(unused, "fixed-test-salt", 101),
        "cannot reach exact target",
    )

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "lock"
        files = {"a.txt": b"fixed\n", "files.sha256": b"placeholder\n"}
        write_locked(files, output)
        write_locked(files, output)
        expect_failure(
            lambda: write_locked({"a.txt": b"drift\n"}, output),
            "Refusing to overwrite non-identical source lock",
        )
    print("[ok] D4 source100 selection is deterministic and archive-complete")
    print("[ok] prior 100/25 mismatch, partial overlap, and target failure are hard errors")
    print("[ok] existing non-identical locks cannot be overwritten")


if __name__ == "__main__":
    main()
