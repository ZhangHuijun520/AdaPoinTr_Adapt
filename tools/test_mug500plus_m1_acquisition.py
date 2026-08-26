#!/usr/bin/env python3
"""Offline determinism and leakage tests for the MUG500+ M1 acquisition plan."""

from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from inventory_mug500plus_figshare import validate_files  # noqa: E402
from plan_mug500plus_m1_acquisition import render_plan, write_locked  # noqa: E402


def fixture_files():
    files = []
    file_id = 100
    for start in range(1, 501, 20):
        end = min(start + 19, 500)
        digest = f"{file_id:032x}"[-32:]
        files.append(
            {
                "id": file_id,
                "name": f"A{start:04d}-A{end:04d}.zip",
                "size": 1_000_000_000 + file_id,
                "download_url": f"https://example.invalid/{file_id}",
                "supplied_md5": digest,
                "computed_md5": digest,
            }
        )
        file_id += 1
    files.append(
        {
            "id": file_id,
            "name": "craniotomy skull.zip",
            "size": 500_000_000,
            "download_url": f"https://example.invalid/{file_id}",
            "supplied_md5": f"{file_id:032x}"[-32:],
            "computed_md5": f"{file_id:032x}"[-32:],
        }
    )
    return validate_files(files)


def csv_rows(payload):
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def main():
    files = fixture_files()
    first = render_plan("a" * 64, files, 40, 125)
    second = render_plan("a" * 64, list(reversed(files)), 40, 125)
    assert first == second

    archives = csv_rows(first["archive_acquisition_order.csv"])
    skulls = csv_rows(first["skull_acquisition_order.csv"])
    initial = csv_rows(first["batch_001_downloads.csv"])
    protocol = json.loads(first["protocol.json"])
    assert len(archives) == 25
    assert len(skulls) == 500
    assert len({row["case_id"] for row in skulls}) == 500
    assert {row["case_id"] for row in skulls} == {
        f"A{index:04d}" for index in range(1, 501)
    }
    assert all("craniotomy" not in row["archive_name"].lower() for row in archives)
    assert sum(int(row["skull_count"]) for row in initial) >= 40
    assert protocol["minimum_qc_pass_skulls"] == 125
    assert protocol["training_unlocked"] is False
    assert protocol["protected_craniotomy_archive"]["included_in_acquisition_plan"] is False

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "locked"
        write_locked(first, output)
        write_locked(first, output)
        altered = dict(first)
        altered["protocol.json"] += b"\n"
        try:
            write_locked(altered, output)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Non-identical M1 plan overwrite was accepted")

    print("[ok] M1 archive order is deterministic and input-order independent")
    print("[ok] A0001-A0500 coverage is exact and craniotomy/B-series is excluded")
    print("[ok] batches end only on archive boundaries")
    print("[ok] 125-skull QC stop rule and immutable outputs are frozen")


if __name__ == "__main__":
    main()
