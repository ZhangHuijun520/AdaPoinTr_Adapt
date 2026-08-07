#!/usr/bin/env python
"""Lock the skull-level development protocol for Mamba mechanism studies."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


PROTOCOL_NAME = "mamba-v12-mechanism-development-v1"
PROTOCOL_SALT = "mamba-v12-mechanism-development-v1-20260805"
BASE_TAG = "mamba-adapter-v11-o0-xyz-out8192-multiseed-r1-p1-seed012"
BASE_COMMIT = "82b07550b4457b34b06be834565a306265fe3f35"
EXPECTED_DEFECT_TYPES = {
    "bilateral",
    "frontoorbital",
    "parietotemporal",
    "random_1",
    "random_2",
}


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def stable_key(namespace, value):
    payload = f"{PROTOCOL_SALT}|{namespace}|{value}".encode("utf-8")
    return sha256_bytes(payload)


def read_manifest(path):
    raw = path.read_bytes()
    records = [
        json.loads(line)
        for line in raw.decode("utf-8").splitlines()
        if line.strip()
    ]
    return records, sha256_bytes(raw)


def strict_train_records(records):
    return [
        record
        for record in records
        if record.get("official_split") == "train"
        and record.get("monitor_split") != "monitor"
    ]


def validate_strict_train(records, expected_skulls=104):
    expected_cases = expected_skulls * len(EXPECTED_DEFECT_TYPES)
    if len(records) != expected_cases:
        raise ValueError(
            f"Expected {expected_cases} strict-train cases, got {len(records)}"
        )
    case_ids = [str(record["case_id"]) for record in records]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Strict-train case IDs are not unique")
    by_skull = defaultdict(list)
    for record in records:
        by_skull[str(record["skull_id"])].append(record)
    if len(by_skull) != expected_skulls:
        raise ValueError(
            f"Expected {expected_skulls} strict-train skulls, got {len(by_skull)}"
        )
    for skull_id, skull_records in by_skull.items():
        defect_types = {str(item.get("defect_type")) for item in skull_records}
        if defect_types != EXPECTED_DEFECT_TYPES or len(skull_records) != 5:
            raise ValueError(
                f"Skull {skull_id} does not have exactly the five defect types"
            )
    return by_skull


def make_assignments(by_skull):
    skull_ids = sorted(by_skull)
    confirmation = set(
        sorted(
            skull_ids,
            key=lambda item: stable_key("confirmation", item),
        )[:20]
    )
    development = [item for item in skull_ids if item not in confirmation]
    development.sort(key=lambda item: stable_key("fold", item))
    if len(development) != 84:
        raise ValueError(f"Expected 84 development skulls, got {len(development)}")
    fold_by_skull = {}
    for fold_index, fold_name in enumerate("ABCD"):
        start = fold_index * 21
        for skull_id in development[start : start + 21]:
            fold_by_skull[skull_id] = fold_name
    return confirmation, fold_by_skull


def case_ids_for_skulls(by_skull, skull_ids):
    rows = []
    for skull_id in sorted(skull_ids):
        rows.extend(by_skull[skull_id])
    rows.sort(key=lambda item: str(item["case_id"]))
    return [str(item["case_id"]) for item in rows]


def render_outputs(records, manifest_sha256):
    by_skull = validate_strict_train(records)
    confirmation, fold_by_skull = make_assignments(by_skull)
    development = set(fold_by_skull)
    files = {}

    def add_ids(name, ids):
        files[name] = ("\n".join(ids) + "\n").encode("utf-8")

    add_ids(
        "development84_case_ids.txt",
        case_ids_for_skulls(by_skull, development),
    )
    add_ids(
        "confirmation20_case_ids.txt",
        case_ids_for_skulls(by_skull, confirmation),
    )
    for fold_name in "ABCD":
        dev_skulls = {
            skull_id
            for skull_id, assigned_fold in fold_by_skull.items()
            if assigned_fold == fold_name
        }
        train_skulls = development.difference(dev_skulls)
        add_ids(
            f"fold{fold_name}_dev_case_ids.txt",
            case_ids_for_skulls(by_skull, dev_skulls),
        )
        add_ids(
            f"fold{fold_name}_train_case_ids.txt",
            case_ids_for_skulls(by_skull, train_skulls),
        )

    skull_rows = [["skull_id", "partition", "fold"]]
    for skull_id in sorted(by_skull):
        if skull_id in confirmation:
            skull_rows.append([skull_id, "locked_confirmation", ""])
        else:
            skull_rows.append([skull_id, "development", fold_by_skull[skull_id]])
    case_rows = [["case_id", "skull_id", "defect_type", "partition", "fold"]]
    for skull_id in sorted(by_skull):
        partition = (
            "locked_confirmation" if skull_id in confirmation else "development"
        )
        fold_name = "" if skull_id in confirmation else fold_by_skull[skull_id]
        for record in sorted(by_skull[skull_id], key=lambda item: item["case_id"]):
            case_rows.append([
                str(record["case_id"]),
                skull_id,
                str(record["defect_type"]),
                partition,
                fold_name,
            ])

    def csv_bytes(rows):
        import io
        output = io.StringIO(newline="")
        csv.writer(output, lineterminator="\n").writerows(rows)
        return output.getvalue().encode("utf-8")

    files["skull_assignments.csv"] = csv_bytes(skull_rows)
    files["case_assignments.csv"] = csv_bytes(case_rows)

    protocol = {
        "protocol_name": PROTOCOL_NAME,
        "protocol_salt": PROTOCOL_SALT,
        "status": "preregistered_before_candidate_training",
        "base_git_tag": BASE_TAG,
        "base_git_commit": BASE_COMMIT,
        "source_manifest_sha256": manifest_sha256,
        "source_filter": {
            "official_split": "train",
            "exclude_monitor_split": "monitor",
        },
        "counts": {
            "strict_train_skulls": 104,
            "strict_train_cases": 520,
            "development_skulls": 84,
            "development_cases": 420,
            "confirmation_skulls": 20,
            "confirmation_cases": 100,
            "fold_dev_skulls": 21,
            "fold_dev_cases": 105,
            "fold_train_skulls": 63,
            "fold_train_cases": 315,
        },
        "candidates": {
            "C0": "frozen O0 xyz single-direction adapter",
            "C1": "fixed total inter-block residual budget",
            "C2": "per-block RMS-normalized residual gate",
            "C3": "shared-weight bidirectional xyz adapter",
        },
        "rounds": {
            "A": "C0-C3 x folds A-D x seed 0",
            "B": "frozen top two x folds A-D x seed 1",
            "C": "frozen winner on development84 x seeds 0,1,2; one-shot confirmation20",
        },
        "selection_rules": {
            "catastrophe": "nonfinite metric or rim_contact_hd95_mm > 50.0",
            "round_a_catastrophe_gate": "candidate total catastrophes <= C0 total catastrophes",
            "final_noninferiority": {
                "final_cd_l1_mm_delta_max": 0.10,
                "final_hd95_mm_delta_max": 0.50,
                "final_nsd_at_1mm_delta_min": -0.01,
            },
            "efficiency_vs_c0": {
                "peak_gpu_memory_ratio_max": 1.25,
                "inference_latency_ratio_max": 1.75,
                "training_epoch_time_ratio_max": 1.75,
            },
            "eligible_ranking": [
                "catastrophe_count",
                "rim_contact_hd95_mm_p95",
                "rim_contact_hd95_mm_max",
                "implant_hd95_mm_mean",
                "rim_contact_cd_l1_mm_mean",
                "negative_rim_contact_nsd_at_1mm_mean",
            ],
            "checkpoint": "epoch-100 ckpt-last, followed by train-only full BN recalibration",
        },
        "prohibitions": [
            "No old monitor split is used for training, selection, or feedback",
            "No official test is used before the winner is frozen",
            "No candidate or rule changes after Round A starts",
        ],
    }
    files["protocol.json"] = (
        json.dumps(protocol, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    hashes = []
    for name in sorted(files):
        hashes.append(f"{sha256_bytes(files[name])}  {name}")
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("utf-8")
    return files


def write_locked(files, output_dir):
    if output_dir.exists():
        mismatches = []
        for name, payload in files.items():
            path = output_dir / name
            if not path.is_file() or path.read_bytes() != payload:
                mismatches.append(name)
        extras = sorted(
            str(path.relative_to(output_dir))
            for path in output_dir.rglob("*")
            if path.is_file() and path.name not in files
        )
        if mismatches or extras:
            raise RuntimeError(
                "Refusing to overwrite an existing non-identical protocol: "
                f"mismatches={mismatches}, extras={extras}"
            )
        print(f"[locked] existing protocol is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] locked protocol: {output_dir}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    records, manifest_sha256 = read_manifest(args.manifest)
    strict_records = strict_train_records(records)
    files = render_outputs(strict_records, manifest_sha256)
    write_locked(files, args.output_dir)
    counts = Counter(
        row.split(",")[1]
        for row in files["skull_assignments.csv"].decode().splitlines()[1:]
    )
    print(f"[ok] partitions={dict(counts)}")
    print(f"[sha256] source_manifest={manifest_sha256}")
    print("[locked] no old monitor or official-test records were admitted")


if __name__ == "__main__":
    main()
