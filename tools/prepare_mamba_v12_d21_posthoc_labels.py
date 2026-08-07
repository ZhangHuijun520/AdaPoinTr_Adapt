#!/usr/bin/env python
"""Freeze D2.1 catastrophe labels for selection-inert post-hoc replay."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


CORE_METRICS = (
    "implant_hd95_mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
)
CANDIDATES = {"Q0", "Q1", "Q2", "Q3"}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def write_locked(path, content):
    if path.exists() and path.read_bytes() != content:
        raise RuntimeError(f"Refusing to overwrite non-identical post-hoc label artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    Path(str(path) + ".sha256").write_text(
        f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--gate_audit", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    audit = json.loads(args.gate_audit.read_text())
    if audit.get("round_b_allowed") is not False or audit.get("selected") != []:
        raise RuntimeError("D2.1 post-hoc labels require the frozen gate-failure audit")
    if set(audit.get("summaries", {})) != CANDIDATES:
        raise RuntimeError("Gate audit does not contain Q0-Q3")

    rows = []
    recurrence = defaultdict(set)
    record_paths = sorted(args.records_root.glob("*/run_record.json"))
    if len(record_paths) != 16:
        raise RuntimeError(f"Expected 16 D2.1 run records, found {len(record_paths)}")
    for record_path in record_paths:
        record = json.loads(record_path.read_text())
        candidate = record["candidate"]
        fold = record["fold"]
        if candidate not in CANDIDATES or int(record["seed"]) != 0:
            raise RuntimeError(f"Unexpected D2.1 run record: {record_path}")
        artifact = record["artifacts"]["metrics_csv"]
        metrics_path = Path(artifact["path"])
        if sha256_file(metrics_path) != artifact["sha256"]:
            raise RuntimeError(f"Metrics hash mismatch: {metrics_path}")
        with metrics_path.open(newline="", encoding="utf-8") as handle:
            for source in csv.DictReader(handle):
                invalid = [metric for metric in CORE_METRICS if not finite(source.get(metric))]
                rim_hd95 = float(source["rim_contact_hd95_mm"])
                catastrophe = bool(invalid) or rim_hd95 > 50.0
                reason = (
                    "nonfinite:" + ",".join(invalid)
                    if invalid else
                    "rim_contact_hd95_mm>50" if catastrophe else "none"
                )
                row = {
                    "candidate": candidate,
                    "fold": fold,
                    "case_id": source["case_id"],
                    "skull_id": source.get("skull_id", ""),
                    "defect_type": source.get("defect_type", ""),
                    "catastrophe": "1" if catastrophe else "0",
                    "catastrophe_reason": reason,
                    **{metric: source.get(metric, "") for metric in CORE_METRICS},
                }
                rows.append(row)
                if catastrophe:
                    recurrence[row["case_id"]].add(candidate)

    if len(rows) != 1680:
        raise RuntimeError(f"Expected 1680 labels, found {len(rows)}")
    if len({(row["candidate"], row["case_id"]) for row in rows}) != 1680:
        raise RuntimeError("Duplicate candidate/case labels")

    fieldnames = list(rows[0])
    lines = []
    import io
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    label_path = args.output_dir / "round_a_case_labels.csv"
    write_locked(label_path, buffer.getvalue().encode("utf-8"))

    counts = Counter(len(candidates) for candidates in recurrence.values())
    summary = {
        "analysis_version": "mamba-v12-d21-posthoc-labels-v1",
        "post_hoc": True,
        "selection_inert": True,
        "round_b_allowed": False,
        "locked_confirmation_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
        "gate_audit_sha256": sha256_file(args.gate_audit),
        "records": len(rows),
        "unique_catastrophic_cases": len(recurrence),
        "recurrence_histogram": dict(sorted(counts.items())),
        "universal_catastrophes": sorted(
            case_id for case_id, candidates in recurrence.items()
            if candidates == CANDIDATES
        ),
    }
    summary_path = args.output_dir / "label_summary.json"
    write_locked(
        summary_path,
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    print(f"[saved] {label_path}")
    print(f"[saved] {summary_path}")
    print("[locked] labels are post-hoc and cannot reopen D2.1 Round B")


if __name__ == "__main__":
    main()
