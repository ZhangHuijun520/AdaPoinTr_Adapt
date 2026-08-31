#!/usr/bin/env python3
"""Contract tests for D5 development-only extraction and QC."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from qc_mamba_v15_d5_development_batch import index_clear_members, verify_sealed_empty


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
    protocol = json.loads(
        Path("docs/mamba_v15_d5_development_batch_qc_protocol_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert protocol["scope"]["partition"] == "development"
    assert (
        protocol["sealed_partition_contract"]
        ["proposal_confirmation_files_before_and_after"]
        == 0
    )
    assert (
        protocol["sealed_partition_contract"]
        ["completion_holdout_files_before_and_after"]
        == 0
    )
    assert protocol["lock_effect"]["D5_synthetic_generation_authorized"] is False

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        valid = root / "valid.zip"
        make_zip(
            valid,
            ["nested/A0001_clear.stl", "nested/A0002_clear.stl", "A0001.png"],
        )
        with zipfile.ZipFile(valid) as archive:
            assert set(index_clear_members(archive, ["A0001", "A0002"])) == {
                "A0001",
                "A0002",
            }

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

        sealed = root / "sealed"
        sealed.mkdir()
        verify_sealed_empty([sealed])
        (sealed / "forbidden.zip").write_bytes(b"x")
        expect_failure(lambda: verify_sealed_empty([sealed]), "not empty")

    print("[ok] D5 accepts exactly one canonical clear STL per development source")
    print("[ok] unexpected or duplicate clear STL members are hard failures")
    print("[ok] both sealed partitions must remain empty")
    print("[locked] model=false generation=false training=false protected=false")


if __name__ == "__main__":
    main()
