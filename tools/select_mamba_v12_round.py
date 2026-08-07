#!/usr/bin/env python
"""Apply preregistered hard gates and lexicographic D2 candidate ranking."""

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


METRICS = (
    "implant_hd95_mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values, q):
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def load_record(path):
    record = json.loads(path.read_text())
    artifacts = record["artifacts"]
    for artifact in artifacts.values():
        artifact_path = Path(artifact["path"])
        if not artifact_path.is_file() or sha256_file(artifact_path) != artifact["sha256"]:
            raise RuntimeError(f"Run artifact hash mismatch: {artifact_path}")
    rows = list(csv.DictReader(open(artifacts["metrics_csv"]["path"], encoding="utf-8")))
    efficiency = json.loads(Path(artifacts["efficiency"]["path"]).read_text())
    return record, rows, efficiency


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--round", choices=("A", "B"), required=True)
    parser.add_argument("--round_a_selection", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def write_locked_receipt(output, payload):
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if output.exists() and output.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite frozen selection receipt: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    Path(str(output) + ".sha256").write_text(
        f"{sha256_file(output)}  {output.name}\n", encoding="ascii"
    )


def main():
    args = parse_args()
    protocol = json.loads(args.protocol.read_text())
    rules = protocol["selection_rules"]
    record_paths = sorted(args.records_root.glob("**/run_record.json"))
    if args.round == "B":
        if args.round_a_selection is None:
            raise ValueError("Round B requires --round_a_selection")
        round_a = json.loads(args.round_a_selection.read_text())
        allowed_candidates = set(round_a["selected"])
        if len(allowed_candidates) != 2:
            raise ValueError("Frozen Round-A receipt must contain two candidates")
    else:
        allowed_candidates = {"C0", "C1", "C2", "C3"}
    reference_candidates = allowed_candidates | {"C0"}
    grouped_rows = defaultdict(list)
    grouped_runs = defaultdict(list)
    for path in record_paths:
        record, rows, efficiency = load_record(path)
        candidate = record["candidate"]
        if candidate not in reference_candidates:
            continue
        allowed_seeds = {0}
        if args.round == "B" and candidate in allowed_candidates:
            allowed_seeds = {0, 1}
        if record["seed"] not in allowed_seeds:
            continue
        grouped_rows[candidate].extend(rows)
        grouped_runs[candidate].append((record, efficiency))
    expected_candidates = reference_candidates
    if set(grouped_rows) != expected_candidates:
        raise RuntimeError(
            f"Incomplete candidate set: expected={expected_candidates} got={set(grouped_rows)}"
        )
    for candidate, runs in grouped_runs.items():
        expected_runs = (
            8
            if args.round == "B" and candidate in allowed_candidates
            else 4
        )
        if len(runs) != expected_runs:
            raise RuntimeError(
                f"{candidate} has {len(runs)} runs; expected {expected_runs}"
            )

    summaries = {}
    for candidate, rows in grouped_rows.items():
        nonfinite_count = sum(
            not all(math.isfinite(float(row[metric])) for metric in METRICS)
            for row in rows
        )
        numeric = {}
        for metric in METRICS:
            values = []
            for row in rows:
                value = float(row[metric])
                if not math.isfinite(value):
                    value = -1.0e30 if "nsd" in metric else 1.0e30
                values.append(value)
            numeric[metric] = values
        catastrophe_count = sum(
            not all(math.isfinite(float(row[metric])) for metric in METRICS)
            or float(row["rim_contact_hd95_mm"]) > 50.0
            for row in rows
        )
        summaries[candidate] = {
            "num_case_predictions": len(rows),
            "nonfinite_case_count": nonfinite_count,
            "catastrophe_count": catastrophe_count,
            "catastrophe_rate": catastrophe_count / len(rows),
            "means": {
                metric: sum(values) / len(values)
                for metric, values in numeric.items()
            },
            "rim_contact_hd95_mm_p95": percentile(
                numeric["rim_contact_hd95_mm"], 0.95
            ),
            "rim_contact_hd95_mm_max": max(numeric["rim_contact_hd95_mm"]),
        }

    c0 = summaries["C0"]
    c0_runs = grouped_runs["C0"]
    c0_latency = sum(item[1]["latency_ms_median"] for item in c0_runs) / len(c0_runs)
    c0_memory = sum(item[1]["peak_gpu_memory_bytes"] for item in c0_runs) / len(c0_runs)
    c0_epoch = sum(item[0]["training_epoch_time_seconds_mean_excluding_first"] for item in c0_runs) / len(c0_runs)
    noninferiority = rules["final_noninferiority"]
    efficiency_limits = rules["efficiency_vs_c0"]
    for candidate, summary in summaries.items():
        runs = grouped_runs[candidate]
        latency = sum(item[1]["latency_ms_median"] for item in runs) / len(runs)
        memory = sum(item[1]["peak_gpu_memory_bytes"] for item in runs) / len(runs)
        epoch = sum(item[0]["training_epoch_time_seconds_mean_excluding_first"] for item in runs) / len(runs)
        deltas = {
            metric: summary["means"][metric] - c0["means"][metric]
            for metric in ("final_cd_l1_mm", "final_hd95_mm", "final_nsd_at_1mm")
        }
        ratios = {
            "inference_latency": latency / c0_latency,
            "peak_gpu_memory": memory / c0_memory,
            "training_epoch_time": epoch / c0_epoch,
        }
        gates = {
            "catastrophe": (
                summary["nonfinite_case_count"] == 0
                and summary["catastrophe_rate"] <= c0["catastrophe_rate"]
            ),
            "final_noninferiority": (
                deltas["final_cd_l1_mm"] <= noninferiority["final_cd_l1_mm_delta_max"]
                and deltas["final_hd95_mm"] <= noninferiority["final_hd95_mm_delta_max"]
                and deltas["final_nsd_at_1mm"] >= noninferiority["final_nsd_at_1mm_delta_min"]
            ),
            "efficiency": (
                ratios["inference_latency"] <= efficiency_limits["inference_latency_ratio_max"]
                and ratios["peak_gpu_memory"] <= efficiency_limits["peak_gpu_memory_ratio_max"]
                and ratios["training_epoch_time"] <= efficiency_limits["training_epoch_time_ratio_max"]
            ),
        }
        summary["final_deltas_vs_c0"] = deltas
        summary["efficiency_ratios_vs_c0"] = ratios
        summary["gates"] = gates
        summary["eligible"] = all(gates.values())
        summary["ranking_key"] = [
            summary["catastrophe_rate"],
            summary["rim_contact_hd95_mm_p95"],
            summary["rim_contact_hd95_mm_max"],
            summary["means"]["implant_hd95_mm"],
            summary["means"]["rim_contact_cd_l1_mm"],
            -summary["means"]["rim_contact_nsd_at_1mm"],
        ]
    eligible = sorted(
        (
            candidate
            for candidate, item in summaries.items()
            if candidate in allowed_candidates and item["eligible"]
        ),
        key=lambda candidate: summaries[candidate]["ranking_key"],
    )
    for candidate in sorted(allowed_candidates):
        item = summaries[candidate]
        print(
            f"[gate] {candidate} eligible={item['eligible']} "
            f"catastrophe={item['gates']['catastrophe']} "
            f"final_noninferiority={item['gates']['final_noninferiority']} "
            f"efficiency={item['gates']['efficiency']}"
        )
    if len(eligible) < 2 and args.round == "A":
        failure_output = args.output.with_name(
            f"{args.output.stem}_gate_failure.json"
        )
        failure_payload = {
            "selection_version": "mamba-v12-preregistered-selection-v1",
            "round": args.round,
            "status": "blocked_insufficient_eligible_candidates",
            "failure_reason": (
                "Fewer than two candidates passed preregistered hard gates"
            ),
            "protocol": str(args.protocol),
            "protocol_sha256": sha256_file(args.protocol),
            "summaries": summaries,
            "eligible_order": eligible,
            "selected": [],
            "round_b_allowed": False,
            "protocol_amendment_required": True,
            "locked": True,
            "old_monitor_used": False,
            "official_test_used": False,
        }
        write_locked_receipt(failure_output, failure_payload)
        print(f"[saved] immutable gate-failure audit: {failure_output}")
        print("[locked] Round B remains forbidden")
        raise RuntimeError(
            "Fewer than two candidates passed preregistered gates; protocol amendment "
            "is required and Round B must not start"
        )
    selected = eligible[:2] if args.round == "A" else eligible[:1]
    payload = {
        "selection_version": "mamba-v12-preregistered-selection-v1",
        "round": args.round,
        "protocol": str(args.protocol),
        "protocol_sha256": sha256_file(args.protocol),
        "summaries": summaries,
        "eligible_order": eligible,
        "selected": selected,
        "locked": True,
        "old_monitor_used": False,
        "official_test_used": False,
    }
    write_locked_receipt(args.output, payload)
    print(f"[selected] round={args.round} candidates={selected}")
    print(f"[saved] frozen selection: {args.output}")
    print("[locked] no old monitor or official-test feedback")


if __name__ == "__main__":
    main()
