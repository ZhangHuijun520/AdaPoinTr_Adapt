#!/usr/bin/env python
"""Audit the held-out SkullBreak monitor protocol for ordering ablation."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


DEFECT_TYPES = {
    "bilateral",
    "frontoorbital",
    "parietotemporal",
    "random_1",
    "random_2",
}
PROTOCOL_VERSION = "skullbreak-ordering-monitor-v1"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_values(values):
    payload = "\n".join(sorted(str(value) for value in values)) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_manifest(path):
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            record["_line_number"] = line_number
            records.append(record)
    return records


def _case_ids(records):
    return {str(record["case_id"]) for record in records}


def _skull_ids(records):
    return {str(record["skull_id"]) for record in records}


def _hashes(records):
    return {
        str(record["complete_mask_sha256"])
        for record in records
        if record.get("complete_mask_sha256")
    }


def _validate_five_defects(records, label, errors):
    defects_by_skull = defaultdict(list)
    for record in records:
        defects_by_skull[str(record["skull_id"])].append(
            str(record.get("defect_type", ""))
        )
    for skull_id, defects in sorted(defects_by_skull.items()):
        if len(defects) != 5 or set(defects) != DEFECT_TYPES:
            errors.append(
                f"{label} skull {skull_id!r} must contain exactly "
                f"{sorted(DEFECT_TYPES)}, got {sorted(defects)}"
            )


def audit_manifest(
    manifest_path,
    expected_official_train_cases=570,
    expected_official_test_cases=100,
    expected_monitor_cases=50,
):
    manifest_path = Path(manifest_path)
    records = load_manifest(manifest_path)
    errors = []

    required = {
        "case_id",
        "skull_id",
        "defect_type",
        "official_split",
        "monitor_split",
        "complete_mask_sha256",
    }
    for record in records:
        missing = required.difference(record)
        if missing:
            errors.append(
                f"manifest line {record['_line_number']} missing "
                f"{sorted(missing)}"
            )

    case_counts = Counter(
        str(record.get("case_id", "")) for record in records
    )
    duplicates = sorted(
        case_id for case_id, count in case_counts.items() if count != 1
    )
    if duplicates:
        errors.append(f"duplicate case_id values: {duplicates[:10]}")

    official_train = [
        record
        for record in records
        if record.get("official_split") == "train"
    ]
    official_test = [
        record
        for record in records
        if record.get("official_split") == "test"
    ]
    monitor = [
        record
        for record in records
        if record.get("monitor_split") == "monitor"
    ]
    strict_train = [
        record
        for record in official_train
        if record.get("monitor_split") != "monitor"
    ]

    expected_strict_train_cases = (
        expected_official_train_cases - expected_monitor_cases
    )
    count_expectations = (
        ("official train", official_train, expected_official_train_cases),
        ("strict train", strict_train, expected_strict_train_cases),
        ("monitor", monitor, expected_monitor_cases),
        ("official test", official_test, expected_official_test_cases),
    )
    for label, subset, expected in count_expectations:
        if len(subset) != expected:
            errors.append(
                f"{label} expected {expected} cases, got {len(subset)}"
            )

    invalid_monitor = [
        str(record.get("case_id"))
        for record in monitor
        if record.get("official_split") != "train"
    ]
    if invalid_monitor:
        errors.append(
            "monitor must be drawn only from official train; invalid cases: "
            f"{invalid_monitor[:10]}"
        )

    for label, subset in (
        ("official train", official_train),
        ("strict train", strict_train),
        ("monitor", monitor),
        ("official test", official_test),
    ):
        _validate_five_defects(subset, label, errors)

    split_sets = {
        "strict_train": _skull_ids(strict_train),
        "monitor": _skull_ids(monitor),
        "official_test": _skull_ids(official_test),
    }
    split_hashes = {
        "strict_train": _hashes(strict_train),
        "monitor": _hashes(monitor),
        "official_test": _hashes(official_test),
    }
    pairs = (
        ("strict_train", "monitor"),
        ("strict_train", "official_test"),
        ("monitor", "official_test"),
    )
    for left, right in pairs:
        skull_overlap = split_sets[left].intersection(split_sets[right])
        if skull_overlap:
            errors.append(
                f"{left}/{right} skull overlap: {sorted(skull_overlap)}"
            )
        hash_overlap = split_hashes[left].intersection(split_hashes[right])
        if hash_overlap:
            errors.append(
                f"{left}/{right} complete-skull hash overlap: "
                f"{sorted(hash_overlap)}"
            )

    defect_counts = Counter(
        str(record.get("defect_type", "")) for record in monitor
    )
    expected_per_defect = expected_monitor_cases // len(DEFECT_TYPES)
    if defect_counts != Counter(
        {defect: expected_per_defect for defect in DEFECT_TYPES}
    ):
        errors.append(
            "monitor defect counts must be balanced at "
            f"{expected_per_defect} each, got {dict(defect_counts)}"
        )

    if errors:
        raise ValueError(
            "SkullBreak ordering protocol audit failed:\n- "
            + "\n- ".join(errors)
        )

    subsets = {
        "official_train": official_train,
        "strict_train": strict_train,
        "monitor": monitor,
        "official_test": official_test,
    }
    report = {
        "protocol_version": PROTOCOL_VERSION,
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "status": "pass",
        "counts": {
            label: {
                "cases": len(subset),
                "skulls": len(_skull_ids(subset)),
            }
            for label, subset in subsets.items()
        },
        "monitor_defect_counts": dict(sorted(defect_counts.items())),
        "case_id_sha256": {
            label: sha256_values(_case_ids(subset))
            for label, subset in subsets.items()
        },
        "skull_id_sha256": {
            label: sha256_values(_skull_ids(subset))
            for label, subset in subsets.items()
        },
        "disjoint_checks": {
            f"{left}_vs_{right}": True for left, right in pairs
        },
    }
    return report


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="data/SkullBreakPC_out8192/manifest.jsonl",
    )
    parser.add_argument("--output", default="")
    parser.add_argument("--expected_official_train_cases", type=int, default=570)
    parser.add_argument("--expected_official_test_cases", type=int, default=100)
    parser.add_argument("--expected_monitor_cases", type=int, default=50)
    return parser.parse_args()


def main():
    args = parse_args()
    report = audit_manifest(
        args.manifest,
        expected_official_train_cases=args.expected_official_train_cases,
        expected_official_test_cases=args.expected_official_test_cases,
        expected_monitor_cases=args.expected_monitor_cases,
    )
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
        print(f"[saved] {output}")
    print(payload, end="")


if __name__ == "__main__":
    main()
