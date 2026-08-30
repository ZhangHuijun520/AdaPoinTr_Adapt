#!/usr/bin/env python3
"""Freeze the metadata-only D5 MUG500+ source150 three-partition lock."""

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
PARTITIONS = (
    ("development", 100),
    ("proposal_confirmation", 25),
    ("completion_holdout", 25),
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def read_ids(path: Path, prefixed: bool = False) -> List[str]:
    values = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if not value:
            continue
        if prefixed:
            value = value.removeprefix("mug500plus__")
        if not SOURCE_ID_RE.fullmatch(value):
            raise RuntimeError(f"Invalid source ID in {path}: {raw!r}")
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
    if (
        protocol.get("protocol_id")
        != "mamba-v15-d5-mug500plus-source150-acquisition-v1"
    ):
        raise RuntimeError("Unexpected D5 source150 protocol")
    rule = protocol.get("selection_rule", {})
    if (
        rule.get("target_source_skulls") != 150
        or rule.get("partition_by_selected_prefix")
        != {
            "development": 100,
            "proposal_confirmation": 25,
            "completion_holdout": 25,
        }
        or rule.get("partition_boundary_failure_action") != "hard_failure"
        or rule.get("partial_prior_overlap_action") != "hard_failure"
        or rule.get("manual_reassignment_allowed") is not False
        or rule.get("geometry_qc_or_model_metrics_used") is not False
    ):
        raise RuntimeError("D5 source selection contract changed")

    access = protocol.get("access_policy", {})
    if (
        access.get("development", {}).get(
            "clear_stl_extraction_and_model_independent_qc_authorized"
        )
        is not True
        or access.get("proposal_confirmation", {}).get(
            "clear_stl_extraction_authorized"
        )
        is not False
        or access.get("completion_holdout", {}).get(
            "clear_stl_extraction_authorized"
        )
        is not False
    ):
        raise RuntimeError("D5 sealed-partition access policy changed")

    effect = protocol.get("lock_effect", {})
    forbidden_true = (
        "D5_synthetic_generation_authorized",
        "D5A_model_implementation_authorized",
        "D5A_training_authorized",
        "D5B_training_authorized",
        "D5_candidate_selection_authorized",
        "proposal_confirmation_access_authorized",
        "completion_holdout_access_authorized",
        "SkullBreak_confirmation20_access_authorized",
        "official_test_access_authorized",
    )
    if (
        effect.get("development_payload_download_authorized") is not True
        or effect.get("development_payload_qc_authorized") is not True
        or effect.get("sealed_archive_download_only_authorized") is not True
        or any(effect.get(key) is not False for key in forbidden_true)
    ):
        raise RuntimeError("D5 lock-effect boundary changed")


def verify_prior_sources(
    d3_ids: Sequence[str],
    d3_development: Sequence[str],
    d3_holdout: Sequence[str],
    d4_ids: Sequence[str],
) -> List[str]:
    d3 = set(d3_ids)
    development = set(d3_development)
    holdout = set(d3_holdout)
    d4 = set(d4_ids)
    if len(d3) != 125 or len(development) != 100 or len(holdout) != 25:
        raise RuntimeError("Expected exact D3 125 = development100 + holdout25")
    if development & holdout or d3 != development | holdout:
        raise RuntimeError("D3 source partition identity failed")
    if len(d4) != 100:
        raise RuntimeError("Expected exact D4 source100")
    if d3 & d4:
        raise RuntimeError("D3 and D4 source IDs overlap")
    prior = sorted(d3 | d4)
    if len(prior) != 225:
        raise RuntimeError("Expected exact D3/D4 prior-source union of 225")
    return prior


def verify_lineage(
    protocol: Dict[str, Any],
    args: argparse.Namespace,
) -> Tuple[List[Dict[str, Any]], List[str], List[str], Dict[str, str]]:
    official = protocol["official_metadata"]
    excluded = protocol["excluded_lineage"]
    parent = protocol["parent_d4a_negative"]
    d3 = excluded["d3_source125"]
    d4 = excluded["d4_source100"]

    paths = {
        "article_json": args.article_json,
        "files_json": args.files_json,
        "d3_source125_ids": args.d3_lock_dir / "healthy125_case_ids.txt",
        "d3_data_lock_receipt": args.d3_lock_dir / "data_lock_receipt.json",
        "d3_files_manifest": args.d3_lock_dir / "files.sha256",
        "d3_development100_ids": args.d3_split_lock_dir
        / "development_skull_ids.txt",
        "d3_holdout25_ids": args.d3_split_lock_dir
        / "locked_holdout_skull_ids.txt",
        "d3_split_receipt": args.d3_split_lock_dir
        / "source_split_lock_receipt.json",
        "d3_split_files_manifest": args.d3_split_lock_dir / "files.sha256",
        "d4_source100_ids": args.d4_lock_dir / "d4_source100_ids.txt",
        "d4_acquisition_receipt": args.d4_lock_dir
        / "source_acquisition_lock_receipt.json",
        "d4_files_manifest": args.d4_lock_dir / "files.sha256",
        "d4_frozen_result": args.d4_frozen_result,
        "d4_complete_report": args.d4_complete_report,
    }
    expected = {
        "article_json": official["article_json_sha256"],
        "files_json": official["files_json_sha256"],
        "d3_source125_ids": d3["source_ids_sha256"],
        "d3_data_lock_receipt": d3["data_lock_receipt_sha256"],
        "d3_files_manifest": d3["files_manifest_sha256"],
        "d3_development100_ids": d3["development100_ids_sha256"],
        "d3_holdout25_ids": d3["holdout25_ids_sha256"],
        "d3_split_receipt": d3["split_receipt_sha256"],
        "d3_split_files_manifest": d3["split_files_manifest_sha256"],
        "d4_source100_ids": d4["source_ids_sha256"],
        "d4_acquisition_receipt": d4["acquisition_receipt_sha256"],
        "d4_files_manifest": d4["files_manifest_sha256"],
        "d4_frozen_result": parent["frozen_result_sha256"],
        "d4_complete_report": parent["complete_report_sha256"],
    }
    hashes = {
        name: verify_hash(path, expected[name], name) for name, path in paths.items()
    }
    hashes["selection_implementation"] = sha256_file(Path(__file__).resolve())
    hashes["selection_tests"] = sha256_file(args.test_script)

    article = json.loads(args.article_json.read_text(encoding="utf-8-sig"))
    validate_article(article, int(official["article_id"]), int(official["version"]))
    raw_files = json.loads(args.files_json.read_text(encoding="utf-8-sig"))
    if not isinstance(raw_files, list):
        raise RuntimeError("Official files JSON must be a list")
    files = validate_files(raw_files)

    d3_ids = read_ids(paths["d3_source125_ids"])
    development = read_ids(paths["d3_development100_ids"], prefixed=True)
    holdout = read_ids(paths["d3_holdout25_ids"], prefixed=True)
    d4_ids = read_ids(paths["d4_source100_ids"])
    prior = verify_prior_sources(d3_ids, development, holdout, d4_ids)

    d3_receipt = json.loads(paths["d3_data_lock_receipt"].read_text())
    split_receipt = json.loads(paths["d3_split_receipt"].read_text())
    d4_receipt = json.loads(paths["d4_acquisition_receipt"].read_text())
    if (
        d3_receipt.get("status") != "locked"
        or d3_receipt.get("healthy_skulls") != 125
        or d3_receipt.get("craniotomy_or_B_series_accessed") is not False
    ):
        raise RuntimeError("Frozen D3 source125 lock is invalid")
    if (
        split_receipt.get("status") != "source_split_locked"
        or split_receipt.get("counts", {}).get("development_skulls") != 100
        or split_receipt.get("counts", {}).get("locked_holdout_skulls") != 25
        or split_receipt.get("holdout_inference_consumed") is not False
    ):
        raise RuntimeError("Frozen D3 split lock is invalid")
    if (
        d4_receipt.get("counts", {}).get("selected_sources") != 100
        or d4_receipt.get("source_overlap") != 0
        or d4_receipt.get("protected_data_accessed") is not False
    ):
        raise RuntimeError("Frozen D4 source100 lock is invalid")
    return files, d3_ids, d4_ids, hashes


def archive_ids(item: Dict[str, Any]) -> List[str]:
    return [
        f"A{index:04d}"
        for index in range(int(item["start_index"]), int(item["end_index"]) + 1)
    ]


def partition_archives(
    healthy: Sequence[Dict[str, Any]],
    prior_ids: Sequence[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    prior = set(prior_ids)
    occupied, unused = [], []
    for raw in healthy:
        item = dict(raw)
        ids = set(archive_ids(item))
        overlap = ids & prior
        if overlap and overlap != ids:
            raise RuntimeError(
                f"Official archive partially overlaps prior D3/D4 sources: "
                f"{item['name']}"
            )
        (occupied if overlap else unused).append(item)
    if sum(int(item["skull_count"]) for item in occupied) != 225:
        raise RuntimeError("Prior D3/D4 sources do not occupy exactly 225 skull slots")
    if sum(int(item["skull_count"]) for item in unused) != 275:
        raise RuntimeError("Expected exactly 275 unused healthy source skulls")
    return occupied, unused


def stable_archive_key(salt: str, item: Dict[str, Any]) -> str:
    payload = (
        f"{salt}|archive|{item['name']}|"
        f"{item['normalized_md5']}|{int(item['size'])}"
    )
    return sha256_bytes(payload.encode("utf-8"))


def select_archives(
    unused: Sequence[Dict[str, Any]],
    salt: str,
    target: int,
) -> List[Dict[str, Any]]:
    strata: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for raw in unused:
        item = dict(raw)
        midpoint = (int(item["start_index"]) + int(item["end_index"])) // 2
        stratum = min(9, (midpoint - 1) // 50)
        item["stratum"] = stratum
        strata[stratum].append(item)
    if set(strata) != set(range(10)):
        raise RuntimeError("All ten source-index strata must remain represented")
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
        raise RuntimeError(f"Cannot reach exact source target {target}; got {count}")
    return selected


def partition_selected(
    selected: Sequence[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    outputs = {name: [] for name, _ in PARTITIONS}
    boundaries = []
    cumulative = 0
    for name, count in PARTITIONS:
        cumulative += count
        boundaries.append((name, cumulative))

    cumulative = 0
    boundary_index = 0
    for raw in selected:
        if boundary_index >= len(boundaries):
            raise RuntimeError("Selected archives exceed frozen partitions")
        item = dict(raw)
        name, boundary = boundaries[boundary_index]
        next_count = cumulative + int(item["skull_count"])
        if next_count > boundary:
            raise RuntimeError(
                f"Archive {item['name']} crosses frozen {name} boundary {boundary}"
            )
        item["partition"] = name
        outputs[name].append(item)
        cumulative = next_count
        if cumulative == boundary:
            boundary_index += 1

    if boundary_index != len(boundaries) or cumulative != 150:
        raise RuntimeError("Selected archives do not fill exact 100/25/25 boundaries")
    return outputs


def assign_batches(
    archives: Sequence[Dict[str, Any]],
    target_per_batch: int,
) -> List[Dict[str, Any]]:
    rows, batch_id, batch_count = [], 1, 0
    for item in archives:
        skulls = int(item["skull_count"])
        if batch_count and batch_count + skulls > target_per_batch:
            batch_id += 1
            batch_count = 0
        batch_count += skulls
        row = dict(item)
        row["batch_id"] = batch_id
        row["batch_cumulative_skulls"] = batch_count
        rows.append(row)
    return rows


def download_row(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "archive_name": item["name"],
        "file_id": int(item["id"]),
        "start_case": f"A{int(item['start_index']):04d}",
        "end_case": f"A{int(item['end_index']):04d}",
        "skull_count": int(item["skull_count"]),
        "size_bytes": int(item["size"]),
        "md5": item["normalized_md5"],
        "download_url": item["download_url"],
    }


def render_report(receipt: Dict[str, Any]) -> bytes:
    counts = receipt["counts"]
    downloads = counts["download_bytes"]
    lines = [
        "# Mamba v1.5 D5 MUG500+ source150 三分区获取锁报告",
        "",
        "> 本锁只使用官方元数据和既有来源凭据；没有读取新几何或模型输出。",
        "",
        "## 锁定结果",
        "",
        f"- 排除 D3 来源：{counts['excluded_d3_sources']}。",
        f"- 排除 D4 来源：{counts['excluded_d4_sources']}。",
        f"- D5 development：{counts['development_sources']} 来源。",
        f"- D5 proposal confirmation：{counts['proposal_confirmation_sources']} 来源。",
        f"- D5 completion holdout：{counts['completion_holdout_sources']} 来源。",
        f"- 官方 ZIP：{counts['selected_archives']} 个。",
        f"- 全部 ZIP 预计下载：{downloads['total_gib']:.2f} GiB。",
        "- D3/D4/D5 来源交集：0。",
        "- 部分重叠 ZIP：0。",
        "- craniotomy/B-series：未纳入。",
        "",
        "## 权限边界",
        "",
        "- development：允许下载、校验、selected clear-STL 提取和模型无关 QC。",
        "- proposal confirmation：仅允许离线 ZIP 下载和校验，禁止解压。",
        "- completion holdout：仅允许离线 ZIP 下载和校验，禁止解压。",
        "- 不允许：合成生成、D5 模型实现、训练、候选选择或保护数据访问。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_outputs(
    protocol: Dict[str, Any],
    protocol_bytes: bytes,
    files: Sequence[Dict[str, Any]],
    d3_ids: Sequence[str],
    d4_ids: Sequence[str],
    lineage_hashes: Dict[str, str],
) -> Dict[str, bytes]:
    healthy, craniotomy, _ = classify_archives(files)
    if len(craniotomy) != 1:
        raise RuntimeError("Protected craniotomy archive classification changed")
    prior_ids = sorted(set(d3_ids) | set(d4_ids))
    occupied, unused = partition_archives(healthy, prior_ids)
    rule = protocol["selection_rule"]
    selected = select_archives(
        unused,
        str(rule["salt"]),
        int(rule["target_source_skulls"]),
    )
    partitions = partition_selected(selected)

    archive_rows = []
    source_rows = []
    global_source_rank = 0
    selection_rank = 0
    partition_source_ids: Dict[str, List[str]] = {
        name: [] for name, _ in PARTITIONS
    }
    for partition_name, _ in PARTITIONS:
        for partition_rank, item in enumerate(partitions[partition_name], 1):
            selection_rank += 1
            archive_rows.append(
                {
                    "selection_rank": selection_rank,
                    "partition": partition_name,
                    "partition_archive_rank": partition_rank,
                    "stratum": int(item["stratum"]),
                    **download_row(item),
                }
            )
            for source_id in archive_ids(item):
                global_source_rank += 1
                partition_source_ids[partition_name].append(source_id)
                source_rows.append(
                    {
                        "global_source_rank": global_source_rank,
                        "partition": partition_name,
                        "source_id": source_id,
                        "archive_name": item["name"],
                        "expected_member_basename": f"{source_id}_clear.stl",
                        "access_state": (
                            "development_qc_authorized"
                            if partition_name == "development"
                            else "sealed_archive_only"
                        ),
                    }
                )

    expected_counts = dict(PARTITIONS)
    for name, expected in expected_counts.items():
        if len(partition_source_ids[name]) != expected:
            raise RuntimeError(f"Partition {name} count is not {expected}")
    all_ids = [row["source_id"] for row in source_rows]
    if (
        len(all_ids) != 150
        or len(set(all_ids)) != 150
        or set(all_ids) & set(prior_ids)
    ):
        raise RuntimeError("D5 source150 cardinality or overlap failed")

    archive_fields = (
        "selection_rank",
        "partition",
        "partition_archive_rank",
        "stratum",
        "archive_name",
        "file_id",
        "start_case",
        "end_case",
        "skull_count",
        "size_bytes",
        "md5",
        "download_url",
    )
    source_fields = (
        "global_source_rank",
        "partition",
        "source_id",
        "archive_name",
        "expected_member_basename",
        "access_state",
    )
    outputs: Dict[str, bytes] = {
        "source150_acquisition_protocol_v1.json": protocol_bytes,
        "excluded_d3_source125_ids.txt": (
            "\n".join(sorted(d3_ids)) + "\n"
        ).encode(),
        "excluded_d4_source100_ids.txt": (
            "\n".join(sorted(d4_ids)) + "\n"
        ).encode(),
        "excluded_prior225_ids.txt": ("\n".join(prior_ids) + "\n").encode(),
        "d5_source150_ids.txt": ("\n".join(all_ids) + "\n").encode(),
        "d5_development100_ids.txt": (
            "\n".join(partition_source_ids["development"]) + "\n"
        ).encode(),
        "d5_proposal_confirmation25_ids.txt": (
            "\n".join(partition_source_ids["proposal_confirmation"]) + "\n"
        ).encode(),
        "d5_completion_holdout25_ids.txt": (
            "\n".join(partition_source_ids["completion_holdout"]) + "\n"
        ).encode(),
        "d5_source150_archive_plan.csv": csv_bytes(archive_fields, archive_rows),
        "d5_source150_source_plan.csv": csv_bytes(source_fields, source_rows),
    }

    download_fields = (
        "archive_name",
        "file_id",
        "start_case",
        "end_case",
        "skull_count",
        "size_bytes",
        "md5",
        "download_url",
    )
    dev_batches = assign_batches(
        partitions["development"],
        int(protocol["download_plan"]["development_target_skulls_per_batch"]),
    )
    batch_ids = sorted({int(row["batch_id"]) for row in dev_batches})
    if len(batch_ids) != int(
        protocol["download_plan"]["expected_development_batches"]
    ):
        raise RuntimeError("Unexpected development download batch count")
    for batch_id in batch_ids:
        items = [row for row in dev_batches if int(row["batch_id"]) == batch_id]
        names = {row["name"] for row in items}
        source_ids = [
            row["source_id"]
            for row in source_rows
            if row["partition"] == "development"
            and row["archive_name"] in names
        ]
        outputs[f"development_batch_{batch_id:03d}_downloads.csv"] = csv_bytes(
            download_fields,
            [download_row(item) for item in items],
        )
        outputs[
            f"development_batch_{batch_id:03d}_expected_source_ids.txt"
        ] = ("\n".join(source_ids) + "\n").encode()

    for name in ("proposal_confirmation", "completion_holdout"):
        outputs[f"{name}_downloads.csv"] = csv_bytes(
            download_fields,
            [download_row(item) for item in partitions[name]],
        )
        outputs[f"{name}_expected_source_ids.txt"] = (
            "\n".join(partition_source_ids[name]) + "\n"
        ).encode()

    selected_sets = {
        name: set(ids) for name, ids in partition_source_ids.items()
    }
    audit = {
        "official_healthy_sources": 500,
        "excluded_d3_sources": len(d3_ids),
        "excluded_d4_sources": len(d4_ids),
        "excluded_prior_union_sources": len(prior_ids),
        "prior_complete_archive_sources": sum(
            int(item["skull_count"]) for item in occupied
        ),
        "unused_sources_before_selection": sum(
            int(item["skull_count"]) for item in unused
        ),
        "selected_sources": len(all_ids),
        "selected_archives": len(selected),
        "partition_counts": {
            name: len(ids) for name, ids in partition_source_ids.items()
        },
        "selected_prior_overlap": len(set(all_ids) & set(prior_ids)),
        "development_confirmation_overlap": len(
            selected_sets["development"]
            & selected_sets["proposal_confirmation"]
        ),
        "development_completion_holdout_overlap": len(
            selected_sets["development"]
            & selected_sets["completion_holdout"]
        ),
        "confirmation_completion_holdout_overlap": len(
            selected_sets["proposal_confirmation"]
            & selected_sets["completion_holdout"]
        ),
        "partial_prior_overlap_archives": 0,
        "craniotomy_or_B_series_selected": False,
        "geometry_qc_or_model_metrics_used": False,
    }
    outputs["source_overlap_audit.json"] = canonical_json_bytes(audit)

    partition_bytes = {
        name: sum(int(item["size"]) for item in items)
        for name, items in partitions.items()
    }
    total_bytes = sum(partition_bytes.values())
    receipt = {
        "protocol_id": protocol["protocol_id"],
        "status": "source150_three_partition_acquisition_locked",
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "selection_salt": rule["salt"],
        "counts": {
            "official_healthy_sources": 500,
            "excluded_d3_sources": 125,
            "excluded_d4_sources": 100,
            "remaining_unused_sources": 275,
            "selected_sources": 150,
            "selected_archives": len(selected),
            "development_sources": 100,
            "proposal_confirmation_sources": 25,
            "completion_holdout_sources": 25,
            "development_batches": len(batch_ids),
            "download_bytes": {
                **partition_bytes,
                "total": total_bytes,
                "total_gib": total_bytes / (1024**3),
            },
        },
        "lineage_hashes": lineage_hashes,
        "prior_source_identity_verified": True,
        "all_partition_boundaries_archive_complete": True,
        "source_overlap": 0,
        "partial_archive_overlap": 0,
        "new_geometry_inspected": False,
        "geometry_qc_used_for_selection": False,
        "model_metrics_used": False,
        "protected_data_accessed": False,
        "development_download_authorized_next": True,
        "development_qc_authorized_next": True,
        "sealed_archive_download_only_authorized_next": True,
        "proposal_confirmation_extraction_authorized": False,
        "completion_holdout_extraction_authorized": False,
        "D5_synthetic_generation_authorized": False,
        "D5A_model_implementation_authorized": False,
        "D5A_training_authorized": False,
        "D5B_training_authorized": False,
        "next_step": "download_and_qc_development_only_keep_two_25_source_partitions_sealed",
    }
    outputs["source_acquisition_lock_receipt.json"] = canonical_json_bytes(receipt)
    outputs["source_acquisition_lock_report_zh.md"] = render_report(receipt)
    manifest = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(outputs.items())
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
                name
                for name in set(existing) & set(outputs)
                if existing[name] != outputs[name]
            )
            extras = sorted(set(existing) - set(outputs))
            missing = sorted(set(outputs) - set(existing))
            raise RuntimeError(
                "Refusing to overwrite non-identical source150 lock: "
                f"mismatches={mismatches} extras={extras} missing={missing}"
            )
        print(f"[locked] existing D5 source150 lock is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in outputs.items():
        path = output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"[saved] D5 source150 acquisition lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article_json", type=Path, required=True)
    parser.add_argument("--files_json", type=Path, required=True)
    parser.add_argument("--d3_lock_dir", type=Path, required=True)
    parser.add_argument("--d3_split_lock_dir", type=Path, required=True)
    parser.add_argument("--d4_lock_dir", type=Path, required=True)
    parser.add_argument(
        "--d4_frozen_result",
        type=Path,
        default=Path(
            "docs/mamba_v14_d4a_head_only_feasibility_complete_negative_result_zh.md"
        ),
    )
    parser.add_argument(
        "--d4_complete_report",
        type=Path,
        default=Path(
            "docs/mamba_v14_d4a_complete_experiment_report_and_next_plan_zh.md"
        ),
    )
    parser.add_argument(
        "--test_script",
        type=Path,
        default=Path("tools/test_mamba_v15_d5_source150_acquisition.py"),
    )
    parser.add_argument(
        "--protocol_json",
        type=Path,
        default=Path("docs/mamba_v15_d5_source150_acquisition_protocol_v1.json"),
    )
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.protocol_json.read_bytes()
    protocol = json.loads(protocol_bytes.decode("utf-8"))
    verify_protocol(protocol)
    files, d3_ids, d4_ids, hashes = verify_lineage(protocol, args)
    outputs = render_outputs(
        protocol,
        protocol_bytes,
        files,
        d3_ids,
        d4_ids,
        hashes,
    )
    write_locked(outputs, args.out_dir)
    receipt = json.loads(outputs["source_acquisition_lock_receipt.json"])
    counts = receipt["counts"]
    print(
        "[done] sources={selected_sources} development={development_sources} "
        "proposal_confirmation={proposal_confirmation_sources} "
        "completion_holdout={completion_holdout_sources} "
        "archives={selected_archives} download_gib={download_bytes[total_gib]:.2f}".format(
            **counts
        )
    )
    print("[sealed] proposal-confirmation25 and completion-holdout25")
    print("[locked] generation=false implementation=false training=false")
    print("[next] download/QC development only; sealed partitions remain archive-only")


if __name__ == "__main__":
    main()
