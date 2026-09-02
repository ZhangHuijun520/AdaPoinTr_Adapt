#!/usr/bin/env python3
"""Freeze the metadata-only D6 terminal source125 two-partition lock."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
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
MACRO_STRATA = (
    ("S1", 1, 150),
    ("S2", 151, 250),
    ("S3", 251, 350),
    ("S4", 351, 450),
    ("S5", 451, 500),
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


def ids_bytes(values: Sequence[str]) -> bytes:
    return ("\n".join(values) + "\n").encode("ascii")


def read_ids(path: Path) -> List[str]:
    values = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip().removeprefix("mug500plus__")
        if not value:
            continue
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
        != "mamba-v16-d6-mug500plus-source125-terminal-acquisition-v1"
    ):
        raise RuntimeError("Unexpected D6 source125 protocol")

    remaining = protocol.get("remaining_pool_contract", {})
    if remaining != {
        "official_healthy_sources": 500,
        "excluded_prior_sources": 375,
        "remaining_sources": 125,
        "remaining_complete_archives": 25,
        "partial_archive_overlap_action": "hard_failure",
        "remaining_after_d6": 0,
    }:
        raise RuntimeError("D6 remaining-pool contract changed")

    rule = protocol.get("partition_rule", {})
    if (
        rule.get("expected_partition_sources")
        != {"development": 100, "proposal_confirmation": 25}
        or rule.get("expected_partition_archives")
        != {"development": 20, "proposal_confirmation": 5}
        or rule.get("manual_reassignment_allowed") is not False
        or rule.get("geometry_qc_or_model_metrics_used") is not False
    ):
        raise RuntimeError("D6 partition contract changed")

    expected_strata = [
        {"name": name, "start": start, "end": end}
        for name, start, end in MACRO_STRATA
    ]
    if rule.get("macro_strata") != expected_strata:
        raise RuntimeError("D6 macro strata changed")

    access = protocol.get("access_policy", {})
    for partition in ("development", "proposal_confirmation"):
        policy = access.get(partition, {})
        if (
            policy.get(
                "archive_download_and_checksum_authorized_after_lock"
                if partition == "development"
                else "offline_archive_download_and_checksum_authorized_after_lock"
            )
            is not True
            or policy.get("clear_stl_extraction_authorized") is not False
            or policy.get("geometry_qc_authorized") is not False
            or policy.get("model_access_authorized") is not False
        ):
            raise RuntimeError(f"D6 {partition} access policy changed")

    effect = protocol.get("lock_effect", {})
    false_keys = (
        "D6_development_extraction_authorized",
        "D6_development_QC_authorized",
        "D6_synthetic_generation_authorized",
        "D6_R0_R1_implementation_authorized",
        "D6_training_authorized",
        "D6_seed1_authorized",
        "D6_confirmation_access_authorized",
        "D6B_authorized",
        "SkullBreak_confirmation20_authorized",
        "official_test_authorized",
    )
    if (
        effect.get("development_archive_download_authorized") is not True
        or effect.get("proposal_confirmation_archive_download_authorized")
        is not True
        or effect.get("D6_mechanism_protocol_freeze_authorized_next") is not True
        or any(effect.get(key) is not False for key in false_keys)
    ):
        raise RuntimeError("D6 lock-effect boundary changed")


def verify_prior_sources(
    d3_ids: Sequence[str],
    d4_ids: Sequence[str],
    d5_ids: Sequence[str],
) -> List[str]:
    sets = [set(d3_ids), set(d4_ids), set(d5_ids)]
    expected = [125, 100, 150]
    if [len(values) for values in sets] != expected:
        raise RuntimeError("Expected exact D3/D4/D5 source counts 125/100/150")
    if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
        raise RuntimeError("D3, D4, and D5 source IDs must be pairwise disjoint")
    prior = sorted(set().union(*sets))
    if len(prior) != 375:
        raise RuntimeError("Expected exact prior-source union of 375")
    return prior


def archive_ids(item: Dict[str, Any]) -> List[str]:
    return [
        f"A{index:04d}"
        for index in range(int(item["start_index"]), int(item["end_index"]) + 1)
    ]


def partition_remaining_archives(
    healthy: Sequence[Dict[str, Any]],
    prior_ids: Sequence[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    prior = set(prior_ids)
    occupied, remaining = [], []
    for raw in healthy:
        item = dict(raw)
        ids = set(archive_ids(item))
        overlap = ids & prior
        if overlap and overlap != ids:
            raise RuntimeError(
                f"Official archive partially overlaps D3/D4/D5 sources: {item['name']}"
            )
        (occupied if overlap else remaining).append(item)

    occupied_sources = sum(int(item["skull_count"]) for item in occupied)
    remaining_sources = sum(int(item["skull_count"]) for item in remaining)
    if occupied_sources != 375 or remaining_sources != 125:
        raise RuntimeError("Expected exact occupied/remaining source counts 375/125")
    if len(remaining) != 25:
        raise RuntimeError("Expected exactly 25 complete remaining archives")
    return occupied, remaining


def macro_stratum(item: Dict[str, Any]) -> str:
    midpoint = (int(item["start_index"]) + int(item["end_index"])) // 2
    for name, start, end in MACRO_STRATA:
        if start <= midpoint <= end:
            return name
    raise RuntimeError(f"Archive midpoint outside D6 macro strata: {item['name']}")


def stable_confirmation_key(salt: str, item: Dict[str, Any]) -> Tuple[str, str]:
    payload = (
        f"{salt}|confirmation|{item['name']}|"
        f"{item['normalized_md5']}|{int(item['size'])}"
    )
    return sha256_bytes(payload.encode("utf-8")), item["name"]


def partition_source125(
    remaining: Sequence[Dict[str, Any]],
    salt: str,
) -> Dict[str, List[Dict[str, Any]]]:
    by_stratum: Dict[str, List[Dict[str, Any]]] = {
        name: [] for name, _, _ in MACRO_STRATA
    }
    for raw in remaining:
        item = dict(raw)
        item["macro_stratum"] = macro_stratum(item)
        by_stratum[item["macro_stratum"]].append(item)

    if any(not items for items in by_stratum.values()):
        missing = [name for name, items in by_stratum.items() if not items]
        raise RuntimeError(f"D6 macro strata without remaining archives: {missing}")

    confirmation = []
    for name, _, _ in MACRO_STRATA:
        items = sorted(
            by_stratum[name],
            key=lambda item: stable_confirmation_key(salt, item),
        )
        confirmation.append(items[0])

    confirmation_names = {item["name"] for item in confirmation}
    development = [
        dict(item, macro_stratum=macro_stratum(item))
        for item in remaining
        if item["name"] not in confirmation_names
    ]
    development.sort(key=lambda item: item["name"])
    confirmation.sort(key=lambda item: item["name"])

    counts = {
        "development": sum(int(item["skull_count"]) for item in development),
        "proposal_confirmation": sum(
            int(item["skull_count"]) for item in confirmation
        ),
    }
    if counts != {"development": 100, "proposal_confirmation": 25}:
        raise RuntimeError(f"Unexpected D6 partition source counts: {counts}")
    if len(development) != 20 or len(confirmation) != 5:
        raise RuntimeError("Expected exact D6 partition archive counts 20/5")
    return {
        "development": development,
        "proposal_confirmation": confirmation,
    }


def verify_lineage(
    protocol: Dict[str, Any], args: argparse.Namespace
) -> Tuple[List[Dict[str, Any]], List[str], List[str], List[str], Dict[str, str]]:
    official = protocol["official_metadata"]
    excluded = protocol["excluded_lineage"]
    parent = protocol["parent_d5_negative"]
    d3 = excluded["d3_source125"]
    d4 = excluded["d4_source100"]
    d5 = excluded["d5_source150"]

    paths = {
        "article_json": args.article_json,
        "files_json": args.files_json,
        "d3_source_ids": args.d3_lock_dir / "healthy125_case_ids.txt",
        "d3_receipt": args.d3_lock_dir / "data_lock_receipt.json",
        "d3_manifest": args.d3_lock_dir / "files.sha256",
        "d4_source_ids": args.d4_lock_dir / "d4_source100_ids.txt",
        "d4_receipt": args.d4_lock_dir / "source_acquisition_lock_receipt.json",
        "d4_manifest": args.d4_lock_dir / "files.sha256",
        "d5_source_ids": args.d5_lock_dir / "d5_source150_ids.txt",
        "d5_development_ids": args.d5_lock_dir / "d5_development100_ids.txt",
        "d5_confirmation_ids": args.d5_lock_dir
        / "d5_proposal_confirmation25_ids.txt",
        "d5_holdout_ids": args.d5_lock_dir / "d5_completion_holdout25_ids.txt",
        "d5_receipt": args.d5_lock_dir / "source_acquisition_lock_receipt.json",
        "d5_manifest": args.d5_lock_dir / "files.sha256",
        "d5_frozen_result": args.d5_frozen_result,
        "d5_complete_report": args.d5_complete_report,
    }
    expected = {
        "article_json": official["article_json_sha256"],
        "files_json": official["files_json_sha256"],
        "d3_source_ids": d3["source_ids_sha256"],
        "d3_receipt": d3["data_lock_receipt_sha256"],
        "d3_manifest": d3["files_manifest_sha256"],
        "d4_source_ids": d4["source_ids_sha256"],
        "d4_receipt": d4["acquisition_receipt_sha256"],
        "d4_manifest": d4["files_manifest_sha256"],
        "d5_source_ids": d5["source_ids_sha256"],
        "d5_development_ids": d5["development100_ids_sha256"],
        "d5_confirmation_ids": d5["proposal_confirmation25_ids_sha256"],
        "d5_holdout_ids": d5["completion_holdout25_ids_sha256"],
        "d5_receipt": d5["acquisition_receipt_sha256"],
        "d5_manifest": d5["files_manifest_sha256"],
        "d5_frozen_result": parent["frozen_result_sha256"],
        "d5_complete_report": parent["complete_report_sha256"],
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

    d3_ids = read_ids(paths["d3_source_ids"])
    d4_ids = read_ids(paths["d4_source_ids"])
    d5_ids = read_ids(paths["d5_source_ids"])
    d5_parts = (
        set(read_ids(paths["d5_development_ids"])),
        set(read_ids(paths["d5_confirmation_ids"])),
        set(read_ids(paths["d5_holdout_ids"])),
    )
    if any(d5_parts[i] & d5_parts[j] for i in range(3) for j in range(i + 1, 3)):
        raise RuntimeError("Frozen D5 partitions overlap")
    if set(d5_ids) != set().union(*d5_parts):
        raise RuntimeError("Frozen D5 source150 partition identity failed")
    verify_prior_sources(d3_ids, d4_ids, d5_ids)
    return files, d3_ids, d4_ids, d5_ids, hashes


def download_row(item: Dict[str, Any], partition: str, batch_id: str) -> Dict[str, Any]:
    return {
        "archive_name": item["name"],
        "partition": partition,
        "batch_id": batch_id,
        "macro_stratum": item["macro_stratum"],
        "skull_count": int(item["skull_count"]),
        "size_bytes": int(item["size"]),
        "md5": item["normalized_md5"],
        "file_id": int(item["id"]),
        "download_url": item["download_url"],
    }


def render_report(receipt: Dict[str, Any]) -> bytes:
    counts = receipt["counts"]
    text = f"""# Mamba v1.6 D6 source125 acquisition lock

> Metadata-only terminal source lock. No D6 geometry was accessed.

- Prior D3/D4/D5 sources: {counts['excluded_prior_sources']}.
- Remaining D6 sources: {counts['remaining_sources']}.
- Remaining complete archives: {counts['remaining_archives']}.
- Development: {counts['development_sources']} sources / {counts['development_archives']} archives.
- Proposal confirmation: {counts['proposal_confirmation_sources']} sources / {counts['proposal_confirmation_archives']} archives.
- Remaining after D6: 0 sources.
- Download bytes: {counts['download_bytes']['total']} ({counts['download_bytes']['total_gib']:.2f} GiB).
- Development extraction authorized: `False`.
- Confirmation extraction authorized: `False`.
- Next: freeze assignment-consistent D6 R0/R1 mechanism protocol.
"""
    return text.encode("utf-8")


def render_outputs(
    protocol: Dict[str, Any],
    protocol_bytes: bytes,
    files: Sequence[Dict[str, Any]],
    d3_ids: Sequence[str],
    d4_ids: Sequence[str],
    d5_ids: Sequence[str],
    lineage_hashes: Dict[str, str],
) -> Dict[str, bytes]:
    healthy, *_ = classify_archives(files)
    prior_ids = verify_prior_sources(d3_ids, d4_ids, d5_ids)
    occupied, remaining = partition_remaining_archives(healthy, prior_ids)
    partitions = partition_source125(
        remaining,
        protocol["partition_rule"]["salt"],
    )

    development = partitions["development"]
    confirmation = partitions["proposal_confirmation"]
    development_ids = [source for item in development for source in archive_ids(item)]
    confirmation_ids = [source for item in confirmation for source in archive_ids(item)]
    all_ids = sorted(development_ids + confirmation_ids)
    if set(all_ids) | set(prior_ids) != {f"A{index:04d}" for index in range(1, 501)}:
        raise RuntimeError("D6 source125 does not exhaust the healthy A-series universe")

    outputs: Dict[str, bytes] = {
        "source125_acquisition_protocol_v1.json": protocol_bytes,
        "excluded_d3_source125_ids.txt": ids_bytes(sorted(d3_ids)),
        "excluded_d4_source100_ids.txt": ids_bytes(sorted(d4_ids)),
        "excluded_d5_source150_ids.txt": ids_bytes(sorted(d5_ids)),
        "excluded_prior375_ids.txt": ids_bytes(prior_ids),
        "d6_source125_ids.txt": ids_bytes(all_ids),
        "d6_development100_ids.txt": ids_bytes(development_ids),
        "d6_proposal_confirmation25_ids.txt": ids_bytes(confirmation_ids),
    }

    archive_fields = (
        "partition",
        "batch_id",
        "macro_stratum",
        "archive_name",
        "start_index",
        "end_index",
        "skull_count",
        "size_bytes",
        "md5",
        "file_id",
        "download_url",
    )
    archive_rows = []
    for index, item in enumerate(development):
        batch_id = f"{index // 8 + 1:03d}"
        archive_rows.append(
            {
                **download_row(item, "development", batch_id),
                "start_index": int(item["start_index"]),
                "end_index": int(item["end_index"]),
            }
        )
    for item in confirmation:
        archive_rows.append(
            {
                **download_row(item, "proposal_confirmation", "sealed"),
                "start_index": int(item["start_index"]),
                "end_index": int(item["end_index"]),
            }
        )
    outputs["d6_source125_archive_plan.csv"] = csv_bytes(archive_fields, archive_rows)

    source_fields = (
        "source_id",
        "partition",
        "batch_id",
        "macro_stratum",
        "archive_name",
    )
    source_rows = []
    for row in archive_rows:
        for index in range(int(row["start_index"]), int(row["end_index"]) + 1):
            source_rows.append(
                {
                    "source_id": f"A{index:04d}",
                    "partition": row["partition"],
                    "batch_id": row["batch_id"],
                    "macro_stratum": row["macro_stratum"],
                    "archive_name": row["archive_name"],
                }
            )
    outputs["d6_source125_source_plan.csv"] = csv_bytes(source_fields, source_rows)

    download_fields = (
        "archive_name",
        "partition",
        "batch_id",
        "macro_stratum",
        "skull_count",
        "size_bytes",
        "md5",
        "file_id",
        "download_url",
    )
    for batch_id in ("001", "002", "003"):
        items = [row for row in archive_rows if row["batch_id"] == batch_id]
        ids = [
            row["source_id"]
            for row in source_rows
            if row["partition"] == "development" and row["batch_id"] == batch_id
        ]
        outputs[f"development_batch_{batch_id}_downloads.csv"] = csv_bytes(
            download_fields, items
        )
        outputs[f"development_batch_{batch_id}_expected_source_ids.txt"] = ids_bytes(ids)

    confirmation_rows = [
        row for row in archive_rows if row["partition"] == "proposal_confirmation"
    ]
    outputs["proposal_confirmation_downloads.csv"] = csv_bytes(
        download_fields, confirmation_rows
    )
    outputs["proposal_confirmation_expected_source_ids.txt"] = ids_bytes(
        confirmation_ids
    )

    partition_bytes = {
        "development": sum(int(item["size"]) for item in development),
        "proposal_confirmation": sum(int(item["size"]) for item in confirmation),
    }
    total_bytes = sum(partition_bytes.values())
    confirmation_strata = {
        item["macro_stratum"]: item["name"] for item in confirmation
    }
    audit = {
        "official_healthy_sources": 500,
        "excluded_d3_sources": len(d3_ids),
        "excluded_d4_sources": len(d4_ids),
        "excluded_d5_sources": len(d5_ids),
        "excluded_prior_union_sources": len(prior_ids),
        "prior_complete_archive_sources": sum(
            int(item["skull_count"]) for item in occupied
        ),
        "remaining_sources": len(all_ids),
        "remaining_complete_archives": len(remaining),
        "partial_prior_overlap_archives": 0,
        "development_sources": len(development_ids),
        "proposal_confirmation_sources": len(confirmation_ids),
        "development_confirmation_overlap": len(
            set(development_ids) & set(confirmation_ids)
        ),
        "selected_prior_overlap": len(set(all_ids) & set(prior_ids)),
        "healthy_unassigned_after_d6": 0,
        "confirmation_archive_by_macro_stratum": confirmation_strata,
        "all_five_macro_strata_represented": set(confirmation_strata)
        == {name for name, _, _ in MACRO_STRATA},
        "craniotomy_or_B_series_selected": False,
        "geometry_qc_or_model_metrics_used": False,
        "new_geometry_inspected": False,
    }
    outputs["source_overlap_audit.json"] = canonical_json_bytes(audit)

    receipt = {
        "protocol_id": protocol["protocol_id"],
        "status": "source125_terminal_two_partition_acquisition_locked",
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "partition_salt": protocol["partition_rule"]["salt"],
        "counts": {
            "official_healthy_sources": 500,
            "excluded_prior_sources": 375,
            "remaining_sources": 125,
            "remaining_archives": 25,
            "development_sources": 100,
            "development_archives": 20,
            "proposal_confirmation_sources": 25,
            "proposal_confirmation_archives": 5,
            "development_batches": 3,
            "remaining_after_d6": 0,
            "download_bytes": {
                **partition_bytes,
                "total": total_bytes,
                "total_gib": total_bytes / (1024**3),
            },
        },
        "lineage_hashes": lineage_hashes,
        "prior_source_identity_verified": True,
        "all_partition_boundaries_archive_complete": True,
        "partial_archive_overlap": 0,
        "source_overlap": 0,
        "new_geometry_inspected": False,
        "model_metrics_used": False,
        "protected_data_accessed": False,
        "development_archive_download_authorized_next": True,
        "development_extraction_authorized": False,
        "proposal_confirmation_archive_download_authorized_next": True,
        "proposal_confirmation_extraction_authorized": False,
        "D6_mechanism_protocol_freeze_authorized_next": True,
        "D6_implementation_authorized": False,
        "D6_training_authorized": False,
        "D6_seed1_authorized": False,
        "D6_confirmation_access_authorized": False,
        "D6B_authorized": False,
        "next_step": "freeze_assignment_consistent_R0_R1_protocol_before_geometry_extraction",
    }
    outputs["source_acquisition_lock_receipt.json"] = canonical_json_bytes(receipt)
    outputs["source_acquisition_lock_report_zh.md"] = render_report(receipt)
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(outputs.items())
    ).encode("ascii")
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
                "Refusing to overwrite non-identical D6 source125 lock: "
                f"mismatches={mismatches} extras={extras} missing={missing}"
            )
        print(f"[locked] existing D6 source125 lock is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in outputs.items():
        path = output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"[saved] D6 source125 acquisition lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article_json", type=Path, required=True)
    parser.add_argument("--files_json", type=Path, required=True)
    parser.add_argument("--d3_lock_dir", type=Path, required=True)
    parser.add_argument("--d4_lock_dir", type=Path, required=True)
    parser.add_argument("--d5_lock_dir", type=Path, required=True)
    parser.add_argument(
        "--d5_frozen_result",
        type=Path,
        default=Path(
            "docs/mamba_v15_d5a_seed0_complete_negative_result_and_csv_posthoc_zh.md"
        ),
    )
    parser.add_argument(
        "--d5_complete_report",
        type=Path,
        default=Path("docs/mamba_v15_d5_complete_experiment_report_and_next_plan_zh.md"),
    )
    parser.add_argument(
        "--test_script",
        type=Path,
        default=Path("tools/test_mamba_v16_d6_source125_acquisition.py"),
    )
    parser.add_argument(
        "--protocol_json",
        type=Path,
        default=Path("docs/mamba_v16_d6_source125_acquisition_protocol_v1.json"),
    )
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.protocol_json.read_bytes()
    protocol = json.loads(protocol_bytes.decode("utf-8"))
    verify_protocol(protocol)
    files, d3_ids, d4_ids, d5_ids, hashes = verify_lineage(protocol, args)
    outputs = render_outputs(
        protocol,
        protocol_bytes,
        files,
        d3_ids,
        d4_ids,
        d5_ids,
        hashes,
    )
    write_locked(outputs, args.out_dir)
    receipt = json.loads(outputs["source_acquisition_lock_receipt.json"])
    counts = receipt["counts"]
    print(
        "[done] remaining={remaining_sources} development={development_sources} "
        "confirmation={proposal_confirmation_sources} archives={remaining_archives} "
        "download_gib={download_bytes[total_gib]:.2f}".format(**counts)
    )
    print("[sealed] D6 proposal-confirmation25 geometry")
    print("[locked] extraction=false generation=false implementation=false training=false")
    print("[next] freeze assignment-consistent R0/R1 mechanism protocol")


if __name__ == "__main__":
    main()

