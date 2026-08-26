#!/usr/bin/env python3
"""Inventory the frozen MUG500+ Figshare release without downloading payloads."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


DEFAULT_ARTICLE_ID = 9616319
DEFAULT_VERSION = 20
API_ROOT = "https://api.figshare.com/v2"
HEALTHY_ARCHIVE_RE = re.compile(r"^A(\d{4})-A(\d{4})\.zip$", re.IGNORECASE)
CRANIOTOMY_ARCHIVE_RE = re.compile(r"^craniotomy[ _-]skull\.zip$", re.IGNORECASE)
USER_AGENT = "PoinTr-MUG500plus-inventory/1.0"


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fetch_json(url: str, timeout: float, retries: int) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def normalize_md5(file_info: Dict[str, Any]) -> str:
    supplied = str(file_info.get("supplied_md5") or "").strip().lower()
    computed = str(file_info.get("computed_md5") or "").strip().lower()
    if supplied and computed and supplied != computed:
        raise RuntimeError(
            f"Figshare MD5 mismatch for {file_info.get('name')}: "
            f"supplied={supplied}, computed={computed}"
        )
    digest = computed or supplied
    if digest and not re.fullmatch(r"[0-9a-f]{32}", digest):
        raise RuntimeError(f"Invalid MD5 for {file_info.get('name')}: {digest}")
    return digest


def validate_article(article: Dict[str, Any], article_id: int, version: int) -> None:
    if int(article.get("id", -1)) != article_id:
        raise RuntimeError(f"Unexpected Figshare article id: {article.get('id')}")
    if int(article.get("version", -1)) != version:
        raise RuntimeError(f"Unexpected Figshare version: {article.get('version')}")
    if "mug500" not in str(article.get("title", "")).lower():
        raise RuntimeError(f"Unexpected article title: {article.get('title')}")
    license_info = article.get("license") or {}
    license_name = str(license_info.get("name", ""))
    if "CC BY 4.0" not in license_name.upper():
        raise RuntimeError(f"Unexpected MUG500+ license: {license_name!r}")


def validate_files(files: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not files:
        raise RuntimeError("Figshare returned no files")
    ids = set()
    names = set()
    normalized = []
    for raw in files:
        item = dict(raw)
        file_id = int(item["id"])
        name = str(item["name"]).strip()
        size = int(item["size"])
        url = str(item.get("download_url") or "").strip()
        if file_id in ids or name.casefold() in names:
            raise RuntimeError(f"Duplicate Figshare file id or name: {name}")
        if size <= 0:
            raise RuntimeError(f"Non-positive file size: {name}={size}")
        if not url.lower().startswith("https://"):
            raise RuntimeError(f"Non-HTTPS download URL for {name}: {url}")
        ids.add(file_id)
        names.add(name.casefold())
        item["normalized_md5"] = normalize_md5(item)
        normalized.append(item)
    return sorted(normalized, key=lambda item: str(item["name"]).casefold())


def classify_archives(
    files: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    healthy = []
    craniotomy = []
    other = []
    coverage: Dict[int, str] = {}
    for item in files:
        name = str(item["name"])
        match = HEALTHY_ARCHIVE_RE.fullmatch(name)
        if match:
            start, end = map(int, match.groups())
            if start < 1 or end > 500 or start > end:
                raise RuntimeError(f"Invalid healthy archive range: {name}")
            for index in range(start, end + 1):
                if index in coverage:
                    raise RuntimeError(
                        f"Healthy skull A{index:04d} appears in both "
                        f"{coverage[index]} and {name}"
                    )
                coverage[index] = name
            enriched = dict(item)
            enriched.update(start_index=start, end_index=end, skull_count=end - start + 1)
            healthy.append(enriched)
        elif CRANIOTOMY_ARCHIVE_RE.fullmatch(name):
            craniotomy.append(dict(item))
        else:
            other.append(dict(item))

    missing = [f"A{index:04d}" for index in range(1, 501) if index not in coverage]
    if missing:
        preview = ", ".join(missing[:12])
        raise RuntimeError(f"Healthy archive coverage is incomplete; missing {preview}")
    if len(craniotomy) != 1:
        raise RuntimeError(
            f"Expected exactly one craniotomy_skull.zip archive, found {len(craniotomy)}"
        )
    return (
        sorted(healthy, key=lambda item: int(item["start_index"])),
        craniotomy,
        other,
    )


def probe_http_range(url: str, timeout: float) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Range": "bytes=0-0", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            byte = response.read(1)
            status = int(getattr(response, "status", response.getcode()))
            content_range = str(response.headers.get("Content-Range", ""))
            return {
                "range_supported": status == 206 and content_range.lower().startswith("bytes 0-0/"),
                "http_status": status,
                "content_range": content_range,
                "accept_ranges": str(response.headers.get("Accept-Ranges", "")),
                "bytes_read": len(byte),
                "error": "",
            }
    except Exception as exc:  # Range support is diagnostic, not an integrity gate.
        return {
            "range_supported": False,
            "http_status": "",
            "content_range": "",
            "accept_ranges": "",
            "bytes_read": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }


def select_range_probe_files(
    healthy: Sequence[Dict[str, Any]], craniotomy: Sequence[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    indices = sorted({0, len(healthy) // 2, len(healthy) - 1})
    return [healthy[index] for index in indices] + list(craniotomy)


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_inventory(
    output_dir: Path,
    article: Dict[str, Any],
    files: Sequence[Dict[str, Any]],
    article_url: str,
    files_url: str,
    probe_range: bool,
    timeout: float,
    metadata_source: str,
) -> Dict[str, Any]:
    healthy, craniotomy, other = classify_archives(files)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_article = canonical_json_bytes(article)
    raw_files_payload = [
        {key: value for key, value in item.items() if key != "normalized_md5"}
        for item in files
    ]
    raw_files = canonical_json_bytes(raw_files_payload)
    (output_dir / "article_response.json").write_bytes(raw_article)
    (output_dir / "files_response.json").write_bytes(raw_files)

    license_info = article.get("license") or {}
    article_metadata = {
        "article_id": int(article["id"]),
        "version": int(article["version"]),
        "title": article.get("title"),
        "doi": article.get("doi"),
        "published_date": article.get("published_date"),
        "modified_date": article.get("modified_date"),
        "license_name": license_info.get("name"),
        "license_url": license_info.get("url"),
        "article_api_url": article_url,
        "files_api_url": files_url,
        "article_response_sha256": sha256_bytes(raw_article),
        "files_response_sha256": sha256_bytes(raw_files),
    }
    (output_dir / "article_metadata.json").write_bytes(canonical_json_bytes(article_metadata))

    file_rows = []
    for item in files:
        size = int(item["size"])
        file_rows.append(
            {
                "file_id": int(item["id"]),
                "name": item["name"],
                "size_bytes": size,
                "size_gb_decimal": f"{size / 1_000_000_000:.9f}",
                "size_gib": f"{size / (1024**3):.9f}",
                "md5": item["normalized_md5"],
                "download_url": item["download_url"],
            }
        )
    write_csv(
        output_dir / "figshare_files.csv",
        ("file_id", "name", "size_bytes", "size_gb_decimal", "size_gib", "md5", "download_url"),
        file_rows,
    )

    healthy_rows = []
    for item in healthy:
        healthy_rows.append(
            {
                "archive_name": item["name"],
                "start_case": f"A{int(item['start_index']):04d}",
                "end_case": f"A{int(item['end_index']):04d}",
                "skull_count": int(item["skull_count"]),
                "size_bytes": int(item["size"]),
                "md5": item["normalized_md5"],
                "download_url": item["download_url"],
            }
        )
    write_csv(
        output_dir / "healthy_archive_index.csv",
        ("archive_name", "start_case", "end_case", "skull_count", "size_bytes", "md5", "download_url"),
        healthy_rows,
    )

    probes = []
    if probe_range:
        for item in select_range_probe_files(healthy, craniotomy):
            result = probe_http_range(str(item["download_url"]), timeout)
            probes.append({"name": item["name"], "download_url": item["download_url"], **result})
    write_csv(
        output_dir / "range_probe.csv",
        (
            "name",
            "download_url",
            "range_supported",
            "http_status",
            "content_range",
            "accept_ranges",
            "bytes_read",
            "error",
        ),
        probes,
    )

    total_bytes = sum(int(item["size"]) for item in files)
    healthy_bytes = sum(int(item["size"]) for item in healthy)
    craniotomy_bytes = sum(int(item["size"]) for item in craniotomy)
    if not 150_000_000_000 <= total_bytes <= 250_000_000_000:
        raise RuntimeError(
            "Frozen MUG500+ v20 total size is outside the expected 150-250 GB "
            f"sanity range: {total_bytes} bytes"
        )
    summary = {
        "inventory_version": "mug500plus-figshare-inventory-v1",
        "article_id": int(article["id"]),
        "figshare_version": int(article["version"]),
        "file_count": len(files),
        "total_size_bytes": total_bytes,
        "total_size_gb_decimal": total_bytes / 1_000_000_000,
        "total_size_gib": total_bytes / (1024**3),
        "healthy_archive_count": len(healthy),
        "healthy_skull_coverage": 500,
        "healthy_size_bytes": healthy_bytes,
        "craniotomy_archive_count": len(craniotomy),
        "craniotomy_expected_cases": 29,
        "craniotomy_size_bytes": craniotomy_bytes,
        "other_file_count": len(other),
        "range_probe_count": len(probes),
        "range_probe_all_supported": bool(probes) and all(row["range_supported"] for row in probes),
        "no_archive_payload_downloaded": True,
        "metadata_source": metadata_source,
        "development_policy": "healthy_A_only_pending_QC",
        "craniotomy_policy": "locked_external_validation_only_after_model_freeze",
    }
    (output_dir / "inventory_summary.json").write_bytes(canonical_json_bytes(summary))

    generated = sorted(path for path in output_dir.iterdir() if path.is_file() and path.name != "files.sha256")
    with (output_dir / "files.sha256").open("w", encoding="ascii", newline="\n") as handle:
        for path in generated:
            handle.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article_id", type=int, default=DEFAULT_ARTICLE_ID)
    parser.add_argument("--version", type=int, default=DEFAULT_VERSION)
    parser.add_argument(
        "--out_dir",
        type=Path,
        default=Path("logs/mamba_v13_d3_mug500plus/inventory_figshare_v20"),
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--skip_range_probe", action="store_true")
    parser.add_argument(
        "--article_json",
        type=Path,
        help="Trusted Figshare v20 article JSON snapshot used when the API is blocked",
    )
    parser.add_argument(
        "--files_json",
        type=Path,
        help="Trusted Figshare v20 files JSON snapshot; optional when embedded in article JSON",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    article_url = f"{API_ROOT}/articles/{args.article_id}/versions/{args.version}"
    files_url = f"{article_url}/files"
    if args.files_json and not args.article_json:
        raise RuntimeError("--files_json requires --article_json")

    if args.article_json:
        article = json.loads(args.article_json.read_text(encoding="utf-8-sig"))
        metadata_source = f"offline_snapshot:{args.article_json.resolve()}"
    else:
        article = fetch_json(article_url, args.timeout, args.retries)
        metadata_source = article_url
    validate_article(article, args.article_id, args.version)

    if args.files_json:
        raw_files = json.loads(args.files_json.read_text(encoding="utf-8-sig"))
        files_url = f"offline_snapshot:{args.files_json.resolve()}"
    else:
        embedded_files = article.get("files")
        if isinstance(embedded_files, list) and embedded_files:
            raw_files = embedded_files
            files_url = article_url + "#embedded-files"
        elif args.article_json:
            raise RuntimeError(
                "Offline article snapshot contains no embedded files; provide --files_json"
            )
        else:
            raw_files = fetch_json(files_url, args.timeout, args.retries)
    files = validate_files(raw_files)
    summary = render_inventory(
        args.out_dir,
        article,
        files,
        article_url,
        files_url,
        not args.skip_range_probe,
        args.timeout,
        metadata_source,
    )
    print(f"[saved] {args.out_dir}")
    print(
        "[ok] MUG500+ Figshare "
        f"v{summary['figshare_version']} files={summary['file_count']} "
        f"healthy_archives={summary['healthy_archive_count']} "
        f"healthy_skulls={summary['healthy_skull_coverage']} "
        f"total={summary['total_size_gb_decimal']:.3f} GB"
    )
    print(f"[range] all sampled URLs support byte ranges: {summary['range_probe_all_supported']}")
    print("[locked] metadata only; no archive payload was downloaded")
    print("[locked] 29 craniotomy cases remain external-validation-only")


if __name__ == "__main__":
    main()
