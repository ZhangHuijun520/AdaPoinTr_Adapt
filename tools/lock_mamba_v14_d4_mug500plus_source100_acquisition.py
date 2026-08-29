#!/usr/bin/env python3
"""Freeze the metadata-only D4 MUG500+ 100-source acquisition lock."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from inventory_mug500plus_figshare import (  # noqa: E402
    classify_archives,
    validate_article,
    validate_files,
)


SOURCE_ID_RE = re.compile(r"A\d{4}")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def read_ids(path: Path, prefixed: bool) -> List[str]:
    values = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if not value:
            continue
        if prefixed:
            value = value.removeprefix("mug500plus__")
        if not SOURCE_ID_RE.fullmatch(value):
            raise RuntimeError(f"Invalid MUG500+ source ID in {path}: {raw!r}")
        values.append(value)
    if len(values) != len(set(values)):
        raise RuntimeError(f"Duplicate source IDs in {path}")
    return values


def verify_hash(path: Path, expected: str, label: str) -> str:
    actual = sha256_file(path)
    if actual != expected.lower():
        raise RuntimeError(
            f"{label} SHA256 mismatch: expected={expected.lower()} actual={actual}"
        )
    return actual


def verify_protocol(protocol: Dict[str, Any]) -> None:
    if protocol.get("protocol_id") != "mamba-v14-d4-mug500plus-source100-acquisition-v1":
        raise RuntimeError("Unexpected D4 source-acquisition protocol")
    selection = protocol.get("selection_rule", {})
    if (
        selection.get("target_source_skulls") != 100
        or selection.get("partial_prior_overlap_action") != "hard_failure"
        or selection.get("manual_reassignment_allowed") is not False
        or selection.get("geometry_qc_or_model_metrics_used") is not False
    ):
        raise RuntimeError("D4 selection contract is not frozen")
    effect = protocol.get("lock_effect", {})
    if (
        effect.get("payload_download_authorized") is not True
        or effect.get("payload_qc_authorized") is not True
        or effect.get("synthetic_defect_generation_authorized") is not False
        or effect.get("D4_training_authorized") is not False
        or effect.get("D4_candidate_selection_authorized") is not False
        or any(
            effect.get(key) is not False
            for key in (
                "D3_holdout_access_authorized",
                "SkullBreak_confirmation20_access_authorized",
                "official_test_access_authorized",
            )
        )
    ):
        raise RuntimeError("D4 lock-effect boundary changed")


def verify_lineage(
    protocol: Dict[str, Any],
    article_json: Path,
    files_json: Path,
    m1_lock_dir: Path,
    d3_split_lock_dir: Path,
    parent_protocol_json: Path,
    parent_protocol_report: Path,
    test_script: Path,
) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, str]]:
    official = protocol["official_metadata"]
    excluded = protocol["excluded_d3_lineage"]
    parent = protocol["parent_d4_protocol"]
    paths = {
        "article_json": article_json,
        "files_json": files_json,
        "m1_healthy125_ids": m1_lock_dir / "healthy125_case_ids.txt",
        "m1_receipt": m1_lock_dir / "data_lock_receipt.json",
        "m1_files_manifest": m1_lock_dir / "files.sha256",
        "d3_development100_ids": d3_split_lock_dir / "development_skull_ids.txt",
        "d3_holdout25_ids": d3_split_lock_dir / "locked_holdout_skull_ids.txt",
        "d3_split_receipt": d3_split_lock_dir / "source_split_lock_receipt.json",
        "d3_split_files_manifest": d3_split_lock_dir / "files.sha256",
        "parent_d4_protocol_json": parent_protocol_json,
        "parent_d4_protocol_report": parent_protocol_report,
    }
    expected = {
        "article_json": official["article_json_sha256"],
        "files_json": official["files_json_sha256"],
        "m1_healthy125_ids": excluded["m1_healthy125_ids_sha256"],
        "m1_receipt": excluded["m1_receipt_sha256"],
        "m1_files_manifest": excluded["m1_files_manifest_sha256"],
        "d3_development100_ids": excluded["d3_development100_ids_sha256"],
        "d3_holdout25_ids": excluded["d3_holdout25_ids_sha256"],
        "d3_split_receipt": excluded["d3_split_receipt_sha256"],
        "d3_split_files_manifest": excluded["d3_split_files_manifest_sha256"],
        "parent_d4_protocol_json": parent["protocol_json_sha256"],
        "parent_d4_protocol_report": parent["protocol_report_sha256"],
    }
    hashes = {
        name: verify_hash(path, expected[name], name) for name, path in paths.items()
    }
    hashes["selection_implementation"] = sha256_file(Path(__file__).resolve())
    hashes["selection_tests"] = sha256_file(test_script)

    article = json.loads(article_json.read_text(encoding="utf-8-sig"))
    validate_article(article, int(official["article_id"]), int(official["version"]))
    raw_files = json.loads(files_json.read_text(encoding="utf-8-sig"))
    if not isinstance(raw_files, list):
        raise RuntimeError("Official files JSON must be a list")
    files = validate_files(raw_files)

    old_ids = read_ids(paths["m1_healthy125_ids"], prefixed=False)
    development = read_ids(paths["d3_development100_ids"], prefixed=True)
    holdout = read_ids(paths["d3_holdout25_ids"], prefixed=True)
    verify_prior_partition(old_ids, development, holdout)

    m1_receipt = json.loads(paths["m1_receipt"].read_text(encoding="utf-8"))
    split_receipt = json.loads(paths["d3_split_receipt"].read_text(encoding="utf-8"))
    if (
        m1_receipt.get("data_lock_id") != excluded["m1_lock_id"]
        or m1_receipt.get("status") != "locked"
        or m1_receipt.get("healthy_skulls") != 125
        or m1_receipt.get("craniotomy_or_B_series_accessed") is not False
    ):
        raise RuntimeError("Frozen M1 source lock is invalid")
    if (
        split_receipt.get("protocol_id") != excluded["d3_split_protocol_id"]
        or split_receipt.get("status") != "source_split_locked"
        or split_receipt.get("counts", {}).get("development_skulls") != 100
        or split_receipt.get("counts", {}).get("locked_holdout_skulls") != 25
        or split_receipt.get("holdout_inference_consumed") is not False
        or split_receipt.get("holdout_metrics_consumed") is not False
        or split_receipt.get("holdout_visual_review_consumed") is not False
    ):
        raise RuntimeError("Frozen D3 100/25 source split is invalid")
    return files, old_ids, hashes


def verify_prior_partition(
    old_ids: Sequence[str], development: Sequence[str], holdout: Sequence[str]
) -> None:
    old, dev, locked = set(old_ids), set(development), set(holdout)
    if len(old) != 125 or len(dev) != 100 or len(locked) != 25:
        raise RuntimeError("Expected exact 125 = 100 + 25 prior-source counts")
    if dev & locked:
        raise RuntimeError("D3 development and holdout source IDs overlap")
    if old != dev | locked:
        raise RuntimeError("M1 healthy125 does not equal D3 development100 plus holdout25")


def archive_ids(item: Dict[str, Any]) -> List[str]:
    return [
        f"A{index:04d}"
        for index in range(int(item["start_index"]), int(item["end_index"]) + 1)
    ]


def partition_archives(
    healthy: Sequence[Dict[str, Any]], old_ids: Sequence[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    old = set(old_ids)
    prior, unused = [], []
    for item in healthy:
        ids = set(archive_ids(item))
        overlap = ids & old
        if overlap and overlap != ids:
            raise RuntimeError(
                f"Official archive partially overlaps prior D3 sources: {item['name']}"
            )
        (prior if overlap else unused).append(dict(item))
    if sum(int(item["skull_count"]) for item in prior) != 125:
        raise RuntimeError("Prior D3 sources do not occupy exactly 125 archived skull slots")
    if sum(int(item["skull_count"]) for item in unused) != 375:
        raise RuntimeError("Expected exactly 375 unused healthy source skulls")
    return prior, unused


def stable_archive_key(salt: str, item: Dict[str, Any]) -> str:
    payload = (
        f"{salt}|archive|{item['name']}|{item['normalized_md5']}|{int(item['size'])}"
    )
    return sha256_bytes(payload.encode("utf-8"))


def select_archives(
    unused: Sequence[Dict[str, Any]], salt: str, target: int
) -> List[Dict[str, Any]]:
    strata: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for raw in unused:
        item = dict(raw)
        midpoint = (int(item["start_index"]) + int(item["end_index"])) // 2
        stratum = min(9, (midpoint - 1) // 50)
        item["stratum"] = stratum
        strata[stratum].append(item)
    if set(strata) != set(range(10)):
        raise RuntimeError("All ten fixed source-index strata must remain represented")
    for items in strata.values():
        items.sort(key=lambda item: (stable_archive_key(salt, item), item["name"]))
    ordered = []
    depth = 0
    while True:
        added = False
        for stratum in range(10):
            if depth < len(strata[stratum]):
                ordered.append(strata[stratum][depth])
                added = True
        if not added:
            break
        depth += 1

    selected, count = [], 0
    for item in ordered:
        skulls = int(item["skull_count"])
        if count + skulls <= target:
            selected.append(item)
            count += skulls
        if count == target:
            break
    if count != target:
        raise RuntimeError(f"Archive-level rule cannot reach exact target {target}; got {count}")
    return selected


def assign_batches(
    selected: Sequence[Dict[str, Any]], target_per_batch: int
) -> List[Dict[str, Any]]:
    rows, batch_id, batch_count, total = [], 1, 0, 0
    for rank, item in enumerate(selected, 1):
        skulls = int(item["skull_count"])
        if batch_count and batch_count + skulls > target_per_batch:
            batch_id += 1
            batch_count = 0
        batch_count += skulls
        total += skulls
        rows.append(
            {
                "archive_rank": rank,
                "batch_id": batch_id,
                "stratum": int(item["stratum"]),
                "archive_name": item["name"],
                "file_id": int(item["id"]),
                "start_case": f"A{int(item['start_index']):04d}",
                "end_case": f"A{int(item['end_index']):04d}",
                "skull_count": skulls,
                "batch_cumulative_skulls": batch_count,
                "plan_cumulative_skulls": total,
                "size_bytes": int(item["size"]),
                "md5": item["normalized_md5"],
                "download_url": item["download_url"],
            }
        )
    return rows


def render_report(receipt: Dict[str, Any]) -> bytes:
    batches = receipt["counts"]["batch_source_skulls"]
    lines = [
        "# Mamba v1.4 D4 MUG500+ 新来源 100 例获取锁报告",
        "",
        "> 本锁在载荷下载前生成；未读取新 STL、几何 QC、模型输出或保护集。",
        "",
        "## 锁定结果",
        "",
        f"- 旧 D3 来源排除：{receipt['counts']['excluded_prior_sources']} skull。",
        f"- 新 D4 来源：{receipt['counts']['selected_sources']} skull。",
        f"- 官方 ZIP：{receipt['counts']['selected_archives']} 个。",
        f"- 预计下载量：{receipt['counts']['download_bytes']} bytes（{receipt['counts']['download_gib']:.2f} GiB）。",
        f"- 批次来源数：{batches}。",
        "- 新旧来源交集：0。",
        "- 部分重叠 ZIP：0。",
        "- craniotomy/B-series：未纳入。",
        "",
        "## 权限边界",
        "",
        "- 允许：下载、MD5/字节数验证、selected clear STL 提取、模型无关 QC。",
        "- 不允许：synthetic defect 生成、D4 训练、候选选择、D3 holdout 或其他保护集访问。",
        "- QC 失败必须冻结并修订协议，不得自动替补来源。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_outputs(
    protocol: Dict[str, Any],
    protocol_bytes: bytes,
    files: Sequence[Dict[str, Any]],
    old_ids: Sequence[str],
    lineage_hashes: Dict[str, str],
) -> Dict[str, bytes]:
    healthy, craniotomy, _ = classify_archives(files)
    if len(craniotomy) != 1:
        raise RuntimeError("Protected craniotomy archive classification changed")
    prior, unused = partition_archives(healthy, old_ids)
    rule = protocol["selection_rule"]
    selected = select_archives(unused, rule["salt"], int(rule["target_source_skulls"]))
    rows = assign_batches(
        selected, int(protocol["download_plan"]["target_skulls_per_batch"])
    )
    if max(int(row["batch_id"]) for row in rows) != int(
        protocol["download_plan"]["expected_batches"]
    ):
        raise RuntimeError("Selected archives do not produce the preregistered batch count")

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
    source_rows = []
    source_rank = 0
    for row in rows:
        for index in range(int(row["start_case"][1:]), int(row["end_case"][1:]) + 1):
            source_rank += 1
            source_rows.append(
                {
                    "source_rank": source_rank,
                    "batch_id": row["batch_id"],
                    "source_id": f"A{index:04d}",
                    "archive_name": row["archive_name"],
                    "expected_member_basename": f"A{index:04d}_clear.stl",
                }
            )
    source_ids = [row["source_id"] for row in source_rows]
    if len(source_ids) != 100 or set(source_ids) & set(old_ids):
        raise RuntimeError("D4 source100 cardinality or disjointness failed")

    outputs: Dict[str, bytes] = {
        "source_acquisition_protocol_v1.json": protocol_bytes,
        "excluded_d3_source125_ids.txt": ("\n".join(sorted(old_ids)) + "\n").encode(),
        "d4_source100_ids.txt": ("\n".join(source_ids) + "\n").encode(),
        "d4_source100_archive_plan.csv": csv_bytes(archive_fields, rows),
        "d4_source100_source_plan.csv": csv_bytes(
            ("source_rank", "batch_id", "source_id", "archive_name", "expected_member_basename"),
            source_rows,
        ),
    }
    batch_counts = {}
    for batch_id in sorted({int(row["batch_id"]) for row in rows}):
        batch_rows = [row for row in rows if int(row["batch_id"]) == batch_id]
        batch_sources = [
            row["source_id"]
            for row in source_rows
            if int(row["batch_id"]) == batch_id
        ]
        batch_counts[str(batch_id)] = len(batch_sources)
        outputs[f"batch_{batch_id:03d}_downloads.csv"] = csv_bytes(
            ("archive_name", "file_id", "start_case", "end_case", "skull_count", "size_bytes", "md5", "download_url"),
            batch_rows,
        )
        outputs[f"batch_{batch_id:03d}_expected_source_ids.txt"] = (
            "\n".join(batch_sources) + "\n"
        ).encode()

    audit = {
        "official_healthy_sources": 500,
        "prior_d3_sources": len(old_ids),
        "prior_complete_archives": len(prior),
        "unused_sources_before_selection": sum(int(x["skull_count"]) for x in unused),
        "selected_sources": len(source_ids),
        "selected_archives": len(selected),
        "selected_prior_overlap": len(set(source_ids) & set(old_ids)),
        "partial_prior_overlap_archives": 0,
        "craniotomy_or_B_series_selected": False,
        "geometry_qc_or_model_metrics_used": False,
    }
    outputs["source_overlap_audit.json"] = canonical_json_bytes(audit)
    receipt = {
        "protocol_id": protocol["protocol_id"],
        "status": "source100_acquisition_locked_payload_not_downloaded",
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "selection_salt": rule["salt"],
        "counts": {
            "official_healthy_sources": 500,
            "excluded_prior_sources": 125,
            "remaining_unused_sources": 375,
            "selected_sources": 100,
            "selected_archives": len(selected),
            "selected_batches": len(batch_counts),
            "batch_source_skulls": batch_counts,
            "download_bytes": sum(int(row["size_bytes"]) for row in rows),
            "download_gib": sum(int(row["size_bytes"]) for row in rows) / (1024**3),
        },
        "lineage_hashes": lineage_hashes,
        "prior_source_identity_verified": True,
        "source_overlap": 0,
        "partial_archive_overlap": 0,
        "payload_downloaded": False,
        "new_geometry_inspected": False,
        "geometry_qc_used_for_selection": False,
        "model_metrics_used": False,
        "protected_data_accessed": False,
        "payload_download_authorized_next": True,
        "payload_qc_authorized_next": True,
        "synthetic_generation_authorized": False,
        "D4_training_authorized": False,
        "D4_candidate_selection_authorized": False,
        "next_step": "download_three_frozen_batches_then_run_model_independent_QC",
    }
    outputs["source_acquisition_lock_receipt.json"] = canonical_json_bytes(receipt)
    outputs["source_acquisition_lock_report_zh.md"] = render_report(receipt)
    manifest = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in sorted(outputs.items())
    )
    outputs["files.sha256"] = manifest.encode("ascii")
    return outputs


def write_locked(outputs: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != outputs:
            mismatches = sorted(
                name for name in set(existing) & set(outputs) if existing[name] != outputs[name]
            )
            extras = sorted(set(existing) - set(outputs))
            missing = sorted(set(outputs) - set(existing))
            raise RuntimeError(
                "Refusing to overwrite non-identical source lock: "
                f"mismatches={mismatches} extras={extras} missing={missing}"
            )
        print(f"[locked] existing source100 acquisition lock is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in outputs.items():
        path = output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"[saved] D4 source100 acquisition lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article_json", type=Path, required=True)
    parser.add_argument("--files_json", type=Path, required=True)
    parser.add_argument("--m1_lock_dir", type=Path, required=True)
    parser.add_argument("--d3_split_lock_dir", type=Path, required=True)
    parser.add_argument(
        "--parent_protocol_json",
        type=Path,
        default=Path("docs/mamba_v14_d4_contact_support_representation_protocol_v1.json"),
    )
    parser.add_argument(
        "--parent_protocol_report",
        type=Path,
        default=Path("docs/mamba_v14_d4_contact_support_representation_preregistered_protocol_zh.md"),
    )
    parser.add_argument(
        "--test_script",
        type=Path,
        default=Path("tools/test_mamba_v14_d4_mug500plus_source100_acquisition.py"),
    )
    parser.add_argument(
        "--protocol_json",
        type=Path,
        default=Path("docs/mamba_v14_d4_mug500plus_source100_acquisition_protocol_v1.json"),
    )
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.protocol_json.read_bytes()
    protocol = json.loads(protocol_bytes.decode("utf-8"))
    verify_protocol(protocol)
    files, old_ids, hashes = verify_lineage(
        protocol,
        args.article_json,
        args.files_json,
        args.m1_lock_dir,
        args.d3_split_lock_dir,
        args.parent_protocol_json,
        args.parent_protocol_report,
        args.test_script,
    )
    outputs = render_outputs(protocol, protocol_bytes, files, old_ids, hashes)
    write_locked(outputs, args.out_dir)
    receipt = json.loads(outputs["source_acquisition_lock_receipt.json"])
    print(
        "[done] sources={selected_sources} archives={selected_archives} "
        "batches={selected_batches} download_gib={download_gib:.2f}".format(
            **receipt["counts"]
        )
    )
    print("[locked] D3 development100 and holdout25 excluded; protected data untouched")
    print("[next] download the three frozen batches and run model-independent QC")


if __name__ == "__main__":
    main()
