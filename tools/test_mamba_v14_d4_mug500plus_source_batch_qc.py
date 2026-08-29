#!/usr/bin/env python3
"""Synthetic archive-contract tests for D4 source-batch extraction and QC."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from qc_mamba_v14_d4_mug500plus_source_batch import (
    FROZEN_MEMBER_ALIASES,
    index_clear_members,
)


def expect_failure(fn, text: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError(f"Expected RuntimeError containing {text!r}")


def make_zip(path: Path, names: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, b"x" * 102400)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        valid = root / "valid.zip"
        make_zip(
            valid,
            ["nested/A0001_clear.stl", "nested/A0002_clear.stl", "A0001.png"],
        )
        with zipfile.ZipFile(valid) as archive:
            selected = index_clear_members(archive, ["A0001", "A0002"])
            assert set(selected) == {"A0001", "A0002"}

        extra = root / "extra.zip"
        make_zip(extra, ["A0001_clear.stl", "A0002_clear.stl"])
        with zipfile.ZipFile(extra) as archive:
            expect_failure(
                lambda: index_clear_members(archive, ["A0001"]),
                "membership differs from lock",
            )

        duplicate = root / "duplicate.zip"
        make_zip(duplicate, ["x/A0001_clear.stl", "y/A0001_clear.stl"])
        with zipfile.ZipFile(duplicate) as archive:
            expect_failure(
                lambda: index_clear_members(archive, ["A0001"]),
                "duplicate clear-STL members",
            )

        alias = root / "alias.zip"
        payload = b"x" * 102400
        with zipfile.ZipFile(alias, "w") as archive:
            info = zipfile.ZipInfo("A0191-A0195/A0192/A192_clear.stl")
            archive.writestr(info, payload)
        with zipfile.ZipFile(alias) as archive:
            info = archive.getinfo("A0191-A0195/A0192/A192_clear.stl")
            contract = FROZEN_MEMBER_ALIASES["A0191-A0195.zip"]["A0192"]
            frozen = dict(contract)
            try:
                contract.update(file_size=info.file_size, crc32=f"{info.CRC:08x}")
                selected = index_clear_members(
                    archive, ["A0192"], "A0191-A0195.zip"
                )
                assert set(selected) == {"A0192"}
                contract["crc32"] = "00000000"
                expect_failure(
                    lambda: index_clear_members(
                        archive, ["A0192"], "A0191-A0195.zip"
                    ),
                    "size/CRC mismatch",
                )
            finally:
                contract.clear()
                contract.update(frozen)

    print("[ok] D4 extraction accepts exactly one frozen clear STL per source")
    print("[ok] unexpected and duplicate clear-STL members are hard failures")
    print("[ok] the single frozen alias requires exact archive, source, size, and CRC")


if __name__ == "__main__":
    main()
