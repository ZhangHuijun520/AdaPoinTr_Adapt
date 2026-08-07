#!/usr/bin/env python
"""Apply the preregistered D2.1 Round-A gates and ranking."""

import argparse
import math
from collections import defaultdict
from pathlib import Path

from select_mamba_v12_round import (
    METRICS,
    load_record,
    percentile,
    sha256_file,
    write_locked_receipt,
)


CANDIDATES = {"Q0", "Q1", "Q2", "Q3"}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def summarize(rows):
    numeric = {}
    nonfinite_count = sum(
        not all(math.isfinite(float(row[metric])) for metric in METRICS)
        for row in rows
    )
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
    return {
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


def main():
    args = parse_args()
    import json

    protocol = json.loads(args.protocol.read_text())
    if protocol["status"] != "preregistered_before_d21_candidate_training":
        raise RuntimeError("D2.1 protocol is not in preregistered state")
    rules = protocol["selection_rules"]

    grouped_rows = defaultdict(list)
    grouped_runs = defaultdict(list)
    for path in sorted(args.records_root.glob("**/run_record.json")):
        record, rows, efficiency = load_record(path)
        candidate = record["candidate"]
        if candidate not in CANDIDATES or record["seed"] != 0:
            continue
        grouped_rows[candidate].extend(rows)
        grouped_runs[candidate].append((record, efficiency))
    if set(grouped_rows) != CANDIDATES:
        raise RuntimeError(
            f"Incomplete D2.1 candidates: expected={CANDIDATES}, got={set(grouped_rows)}"
        )
    for candidate, runs in grouped_runs.items():
        if len(runs) != 4:
            raise RuntimeError(f"{candidate} has {len(runs)} runs; expected 4")

    summaries = {
        candidate: summarize(rows) for candidate, rows in grouped_rows.items()
    }
    q0 = summaries["Q0"]
    q0_runs = grouped_runs["Q0"]

    def run_mean(runs, record_key=None, efficiency_key=None):
        if record_key is not None:
            values = [record[record_key] for record, _ in runs]
        else:
            values = [efficiency[efficiency_key] for _, efficiency in runs]
        return sum(values) / len(values)

    q0_latency = run_mean(q0_runs, efficiency_key="latency_ms_median")
    q0_memory = run_mean(q0_runs, efficiency_key="peak_gpu_memory_bytes")
    q0_epoch = run_mean(
        q0_runs, record_key="training_epoch_time_seconds_mean_excluding_first"
    )
    noninferiority = rules["final_noninferiority"]
    efficiency_limits = rules["efficiency_vs_q0"]

    for candidate, summary in summaries.items():
        runs = grouped_runs[candidate]
        deltas = {
            metric: summary["means"][metric] - q0["means"][metric]
            for metric in ("final_cd_l1_mm", "final_hd95_mm", "final_nsd_at_1mm")
        }
        ratios = {
            "inference_latency": run_mean(
                runs, efficiency_key="latency_ms_median"
            ) / q0_latency,
            "peak_gpu_memory": run_mean(
                runs, efficiency_key="peak_gpu_memory_bytes"
            ) / q0_memory,
            "training_epoch_time": run_mean(
                runs,
                record_key="training_epoch_time_seconds_mean_excluding_first",
            ) / q0_epoch,
        }
        gates = {
            "catastrophe": (
                summary["nonfinite_case_count"] == 0
                and summary["catastrophe_rate"] <= q0["catastrophe_rate"]
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
        summary["final_deltas_vs_q0"] = deltas
        summary["efficiency_ratios_vs_q0"] = ratios
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
        (candidate for candidate in CANDIDATES if summaries[candidate]["eligible"]),
        key=lambda candidate: summaries[candidate]["ranking_key"],
    )
    for candidate in sorted(CANDIDATES):
        item = summaries[candidate]
        print(
            f"[gate] {candidate} eligible={item['eligible']} "
            f"catastrophe={item['catastrophe_count']}/{item['num_case_predictions']} "
            f"final={item['gates']['final_noninferiority']} "
            f"efficiency={item['gates']['efficiency']}"
        )

    allowed = len(eligible) >= 2
    output = args.output if allowed else args.output.with_name(
        f"{args.output.stem}_gate_failure.json"
    )
    receipt = {
        "selection_version": "mamba-v12-d21-geometry-selection-v1",
        "round": "A",
        "status": "top_two_frozen" if allowed else "blocked_insufficient_eligible_candidates",
        "protocol": str(args.protocol),
        "protocol_sha256": sha256_file(args.protocol),
        "summaries": summaries,
        "eligible_order": eligible,
        "selected": eligible[:2] if allowed else [],
        "round_b_allowed": allowed,
        "locked": True,
        "locked_confirmation_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
    }
    write_locked_receipt(output, receipt)
    print(f"[saved] immutable D2.1 Round-A receipt: {output}")
    if not allowed:
        raise RuntimeError(
            "D2.1 Round B forbidden: fewer than two candidates passed all gates"
        )
    print(f"[selected] D2.1 Round-A top two: {eligible[:2]}")
    print("[locked] do not alter candidates or rules before Round B")


if __name__ == "__main__":
    main()
