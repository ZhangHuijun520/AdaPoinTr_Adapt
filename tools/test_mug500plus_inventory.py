#!/usr/bin/env python3
"""Offline tests for the MUG500+ Figshare metadata inventory."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from inventory_mug500plus_figshare import (  # noqa: E402
    classify_archives,
    render_inventory,
    validate_article,
    validate_files,
)


def article_fixture():
    return {
        "id": 9616319,
        "version": 20,
        "title": "MUG500+ Repository",
        "doi": "10.6084/m9.figshare.9616319",
        "published_date": "2022-02-04T09:49:00Z",
        "modified_date": "2022-02-04T09:49:00Z",
        "license": {"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"},
    }


def file_fixture():
    files = []
    file_id = 1
    start = 1
    while start <= 500:
        end = min(start + 19, 500)
        digest = f"{file_id:032x}"
        files.append(
            {
                "id": file_id,
                "name": f"A{start:04d}-A{end:04d}.zip",
                "size": 7_800_000_000 + file_id,
                "download_url": f"https://example.invalid/files/{file_id}",
                "supplied_md5": digest,
                "computed_md5": digest,
            }
        )
        file_id += 1
        start = end + 1
    files.append(
        {
            "id": file_id,
            "name": "craniotomy skull.zip",
            "size": 500_000_000,
            "download_url": f"https://example.invalid/files/{file_id}",
            "supplied_md5": f"{file_id:032x}",
            "computed_md5": f"{file_id:032x}",
        }
    )
    return files


def expect_failure(callback, message):
    try:
        callback()
    except RuntimeError:
        return
    raise AssertionError(message)


def main():
    article = article_fixture()
    validate_article(article, 9616319, 20)
    files = validate_files(file_fixture())
    healthy, craniotomy, other = classify_archives(files)
    assert sum(item["skull_count"] for item in healthy) == 500
    assert len(craniotomy) == 1
    assert not other

    missing = [item for item in files if item["name"] != "A0001-A0020.zip"]
    expect_failure(lambda: classify_archives(missing), "Missing range was not rejected")

    duplicate = file_fixture()
    duplicate.append(dict(duplicate[0]))
    expect_failure(lambda: validate_files(duplicate), "Duplicate file was not rejected")

    mismatched = file_fixture()
    mismatched[0]["computed_md5"] = "f" * 32
    expect_failure(lambda: validate_files(mismatched), "MD5 mismatch was not rejected")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "inventory"
        summary = render_inventory(
            output,
            article,
            files,
            "https://api.figshare.com/v2/articles/9616319/versions/20",
            "https://api.figshare.com/v2/articles/9616319/versions/20#embedded-files",
            False,
            1.0,
            "offline_test_fixture",
        )
        assert summary["healthy_skull_coverage"] == 500
        assert summary["craniotomy_expected_cases"] == 29
        assert summary["no_archive_payload_downloaded"] is True
        assert summary["metadata_source"] == "offline_test_fixture"
        assert json.loads((output / "inventory_summary.json").read_text())["figshare_version"] == 20
        assert (output / "files.sha256").is_file()

    print("[ok] MUG500+ article/version/license validation")
    print("[ok] A0001-A0500 archive coverage is exact")
    print("[ok] duplicate, gap, and MD5 mismatch hard failures")
    print("[ok] deterministic metadata-only inventory rendering")


if __name__ == "__main__":
    main()
