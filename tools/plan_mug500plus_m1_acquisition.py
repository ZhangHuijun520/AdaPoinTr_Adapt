#!/usr/bin/env python3
"""Freeze a deterministic, metadata-only MUG500+ M1 acquisition plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from inventory_mug500plus_figshare import (  # noqa: E402
    classify_archives,
    validate_files,
)


PROTOCOL_ID = "mug500plus-m1-acquisition-qc-v1"
ORDER_SALT = "mug500plus-v20-healthy-acquisition-20260811"
EXPECTED_FILES_JSON_SHA256 = (
    "f475490611f5d17536bbf76a0f7db0693a668fd3e87e8502ec395db6b461a078"
)
STRATUM_WIDTH = 50


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_key(namespace: str, value: str) -> str:
    return sha256_bytes(f"{ORDER_SALT}|{namespace}|{value}".encode("utf-8"))


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def read_official_files(path: Path, expected_sha256: str) -> List[Dict[str, Any]]:
    actual = sha256_file(path)
    if actual != expected_sha256.lower():
        raise RuntimeError(
            f"Official files JSON SHA256 mismatch: expected={expected_sha256} actual={actual}"
        )
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        raise RuntimeError("Official files JSON must contain a list")
    return validate_files(payload)


def deterministic_archive_order(
    healthy: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    strata: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for item in healthy:
        midpoint = (int(item["start_index"]) + int(item["end_index"])) // 2
        stratum = min(9, (midpoint - 1) // STRATUM_WIDTH)
        enriched = dict(item)
        enriched["stratum"] = stratum
        strata[stratum].append(enriched)

    for stratum, items in strata.items():
        items.sort(
            key=lambda item: stable_key(
                f"stratum-{stratum}",
                f"{item['name']}|{item['normalized_md5']}|{item['size']}",
            )
        )
    stratum_order = sorted(strata, key=lambda value: stable_key("stratum", str(value)))

    ordered = []
    depth = 0
    while True:
        added = False
        for stratum in stratum_order:
            if depth < len(strata[stratum]):
                ordered.append(strata[stratum][depth])
                added = True
        if not added:
            break
        depth += 1
    if len(ordered) != len(healthy):
        raise AssertionError("Archive interleave lost records")
    return ordered


def assign_batches(
    ordered: Sequence[Dict[str, Any]], batch_target_skulls: int
) -> List[Dict[str, Any]]:
    if batch_target_skulls < 20:
        raise ValueError("batch_target_skulls must be at least 20")
    rows = []
    batch_id = 1
    batch_skulls = 0
    cumulative_skulls = 0
    for rank, item in enumerate(ordered, 1):
        if batch_skulls >= batch_target_skulls:
            batch_id += 1
            batch_skulls = 0
        skull_count = int(item["skull_count"])
        batch_skulls += skull_count
        cumulative_skulls += skull_count
        rows.append(
            {
                "archive_rank": rank,
                "batch_id": batch_id,
                "stratum": int(item["stratum"]),
                "archive_name": item["name"],
                "file_id": int(item["id"]),
                "start_case": f"A{int(item['start_index']):04d}",
                "end_case": f"A{int(item['end_index']):04d}",
                "skull_count": skull_count,
                "batch_cumulative_skulls": batch_skulls,
                "plan_cumulative_skulls": cumulative_skulls,
                "size_bytes": int(item["size"]),
                "md5": item["normalized_md5"],
                "download_url": item["download_url"],
            }
        )
    return rows


def render_plan(
    files_json_sha256: str,
    files: Sequence[Dict[str, Any]],
    batch_target_skulls: int,
    minimum_qc_pass_skulls: int,
) -> Dict[str, bytes]:
    healthy, craniotomy, other = classify_archives(files)
    ordered = deterministic_archive_order(healthy)
    rows = assign_batches(ordered, batch_target_skulls)
    if len(craniotomy) != 1:
        raise AssertionError("Craniotomy archive classification changed")
    if any("craniotomy" in str(row["archive_name"]).lower() for row in rows):
        raise AssertionError("Protected craniotomy archive leaked into the plan")

    archive_fields = (
        "archive_rank",
        "batch_id",
        "stratum",
        "archive_name",
        "file_id",
        "start_case",
        "end_case",
        "skull_count",
        "batch_cumulative_skulls",
        "plan_cumulative_skulls",
        "size_bytes",
        "md5",
        "download_url",
    )
    outputs: Dict[str, bytes] = {
        "archive_acquisition_order.csv": csv_bytes(archive_fields, rows)
    }

    skull_rows = []
    skull_rank = 0
    for row in rows:
        start = int(str(row["start_case"])[1:])
        end = int(str(row["end_case"])[1:])
        for index in range(start, end + 1):
            skull_rank += 1
            skull_rows.append(
                {
                    "skull_rank": skull_rank,
                    "batch_id": row["batch_id"],
                    "case_id": f"A{index:04d}",
                    "archive_name": row["archive_name"],
                    "expected_member_basename": f"A{index:04d}_clear.stl",
                }
            )
    outputs["skull_acquisition_order.csv"] = csv_bytes(
        (
            "skull_rank",
            "batch_id",
            "case_id",
            "archive_name",
            "expected_member_basename",
        ),
        skull_rows,
    )

    first_batch = [row for row in rows if int(row["batch_id"]) == 1]
    outputs["batch_001_downloads.csv"] = csv_bytes(archive_fields, first_batch)
    first_cases = [row["case_id"] for row in skull_rows if int(row["batch_id"]) == 1]
    outputs["batch_001_expected_case_ids.txt"] = (
        "\n".join(first_cases) + "\n"
    ).encode("ascii")

    batch_counts: Dict[str, int] = defaultdict(int)
    for row in skull_rows:
        batch_counts[str(row["batch_id"])] += 1
    protocol = {
        "protocol_id": PROTOCOL_ID,
        "status": "acquisition_order_locked_payload_not_yet_admitted",
        "figshare_article_id": 9616319,
        "figshare_version": 20,
        "official_files_json_sha256": files_json_sha256,
        "order_salt": ORDER_SALT,
        "ordering": {
            "unit": "healthy_archive",
            "strata": "ten consecutive 50-skull A-series bands",
            "within_stratum": "SHA256(order_salt, archive name, MD5, size)",
            "between_strata": "deterministic round-robin in hashed stratum order",
            "model_metrics_used": False,
            "qc_results_used_to_reorder": False,
        },
        "batch_target_skulls": batch_target_skulls,
        "minimum_qc_pass_skulls": minimum_qc_pass_skulls,
        "stop_rule": (
            "After each whole archive is QC-audited, stop at the first archive boundary "
            f"where at least {minimum_qc_pass_skulls} unique healthy skulls pass every "
            "hard QC and duplicate gate. Never discard a passing skull based on model behavior."
        ),
        "counts": {
            "healthy_archives": len(rows),
            "healthy_skulls": len(skull_rows),
            "batches": len(batch_counts),
            "batch_skulls": dict(sorted(batch_counts.items(), key=lambda item: int(item[0]))),
            "other_metadata_files": len(other),
        },
        "payload_policy": {
            "allowed": "Axxxx_clear.stl plus archive provenance",
            "forbidden": [
                "craniotomy skull.zip",
                "B-series skulls and implants",
                "NRRD payloads",
                "PNG payloads",
                "non-clear STL payloads",
            ],
            "server_full_archive_storage_allowed": False,
        },
        "qc_policy": {
            "hard_gates_frozen_before_payload_inspection": True,
            "required_tool": "tools/qc_mug500plus_clear_stl.py",
            "minimum_file_bytes": 102400,
            "minimum_triangles": 1000,
            "minimum_nondegenerate_fraction": 0.99,
            "minimum_bbox_extent_mm": 50.0,
            "maximum_bbox_extent_mm": 600.0,
            "minimum_bbox_aspect_ratio": 0.15,
            "duplicate_surface_fingerprint_allowed": False,
        },
        "protected_craniotomy_archive": {
            "name": craniotomy[0]["name"],
            "file_id": int(craniotomy[0]["id"]),
            "md5": craniotomy[0]["normalized_md5"],
            "status": "locked_external_validation_only_after_method_freeze",
            "included_in_acquisition_plan": False,
        },
        "training_unlocked": False,
    }
    outputs["protocol.json"] = (
        json.dumps(protocol, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    hashes = [
        f"{sha256_bytes(outputs[name])}  {name}" for name in sorted(outputs)
    ]
    outputs["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    return outputs


def write_locked(outputs: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != outputs:
            raise RuntimeError(
                f"Refusing to overwrite a non-identical MUG500+ M1 plan: {output_dir}"
            )
        print(f"[locked] existing M1 plan is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in outputs.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] locked MUG500+ M1 plan: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files_json", type=Path, required=True)
    parser.add_argument(
        "--files_json_sha256", default=EXPECTED_FILES_JSON_SHA256
    )
    parser.add_argument(
        "--out_dir",
        type=Path,
        default=Path("logs/mamba_v13_d3_mug500plus/protocol_m1_v1"),
    )
    parser.add_argument("--batch_target_skulls", type=int, default=40)
    parser.add_argument("--minimum_qc_pass_skulls", type=int, default=125)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.minimum_qc_pass_skulls < 125:
        raise ValueError("M1 requires at least 125 QC-passing healthy skulls")
    files = read_official_files(args.files_json, args.files_json_sha256)
    outputs = render_plan(
        args.files_json_sha256.lower(),
        files,
        args.batch_target_skulls,
        args.minimum_qc_pass_skulls,
    )
    write_locked(outputs, args.out_dir)
    protocol = json.loads(outputs["protocol.json"])
    print(
        f"[ok] archives={protocol['counts']['healthy_archives']} "
        f"skulls={protocol['counts']['healthy_skulls']} "
        f"batches={protocol['counts']['batches']}"
    )
    print("[next] acquire only the archives listed in batch_001_downloads.csv")
    print("[locked] craniotomy/B-series payloads remain forbidden")
    print("[locked] training remains disabled until QC, deduplication, and D3 data lock")


if __name__ == "__main__":
    main()
