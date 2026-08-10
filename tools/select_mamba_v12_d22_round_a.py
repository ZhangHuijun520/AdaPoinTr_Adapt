#!/usr/bin/env python
"""Apply the preregistered D2.2 Round-A gates and freeze one winner."""

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


CORE_METRICS = (
    "implant_cd_l1_mm",
    "implant_hd95_mm",
    "implant_nsd_at_1mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
    "coarse_gt_rim_to_pred_p95_mm",
)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_run(path):
    record = json.loads(path.read_text(encoding="utf-8"))
    artifacts = record["artifacts"]
    input_hashes = {str(path): sha256_file(path)}
    for artifact in artifacts.values():
        artifact_path = Path(artifact["path"])
        actual = sha256_file(artifact_path)
        if actual != artifact["sha256"]:
            raise RuntimeError(f"Run artifact hash mismatch: {artifact_path}")
        input_hashes[str(artifact_path)] = actual
    with open(artifacts["metrics_csv"]["path"], encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    efficiency = json.loads(
        Path(artifacts["efficiency"]["path"]).read_text(encoding="utf-8")
    )
    return record, rows, efficiency, input_hashes


def finite(row, metric):
    try:
        return math.isfinite(float(row[metric]))
    except (KeyError, TypeError, ValueError):
        return False


def is_disaster(row):
    return (
        not all(finite(row, metric) for metric in CORE_METRICS)
        or float(row["rim_contact_hd95_mm"]) > 50.0
    )


def write_locked(path, payload):
    encoded = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    if path.exists() and path.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite frozen D2.2 receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    Path(str(path) + ".sha256").write_text(
        f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
    )


def aggregate(rows, runs):
    nonfinite = sum(
        not all(finite(row, metric) for metric in CORE_METRICS)
        for row in rows
    )
    disaster_by_case = {
        row["case_id"]: is_disaster(row) for row in rows
    }
    undefined = sum(
        not finite(row, "rim_predicted_rim_points")
        or float(row["rim_predicted_rim_points"]) <= 0
        for row in rows
    )
    finite_rim_hd95 = [
        float(row["rim_contact_hd95_mm"])
        for row in rows
        if finite(row, "rim_contact_hd95_mm")
    ]
    if not finite_rim_hd95:
        finite_rim_hd95 = [1.0e30]
    means = {
        metric: float(np.mean([float(row[metric]) for row in rows]))
        if all(finite(row, metric) for row in rows)
        else None
        for metric in CORE_METRICS
    }
    catastrophic_skulls = {
        row["skull_id"] for row in rows if is_disaster(row)
    }
    return {
        "case_count": len(rows),
        "nonfinite_case_count": nonfinite,
        "disaster_count": sum(disaster_by_case.values()),
        "catastrophic_skull_count": len(catastrophic_skulls),
        "undefined_contact_count": undefined,
        "rim_hd95_p95": float(np.percentile(finite_rim_hd95, 95)),
        "rim_hd95_max": max(finite_rim_hd95),
        "means": means,
        "disaster_by_case": disaster_by_case,
        "efficiency": {
            "latency_ms_median": float(np.mean([
                item[1]["latency_ms_median"] for item in runs
            ])),
            "peak_gpu_memory_bytes": float(np.mean([
                item[1]["peak_gpu_memory_bytes"] for item in runs
            ])),
            "steady_epoch_time_seconds": float(np.mean([
                item[0]["training_epoch_time_seconds_mean_excluding_first"]
                for item in runs
            ])),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    amendment = json.loads(args.amendment.read_text(encoding="utf-8"))
    if amendment["amends"] != protocol["protocol_id"]:
        raise RuntimeError("D2.2 amendment/protocol mismatch")

    grouped_rows = defaultdict(list)
    grouped_runs = defaultdict(list)
    input_hashes = {}
    for path in sorted(args.records_root.glob("*/run_record.json")):
        record, rows, efficiency, hashes = load_run(path)
        candidate = record["candidate"]
        if candidate not in {"R0", "R1", "R2"} or record["seed"] != 0:
            continue
        grouped_rows[candidate].extend(rows)
        grouped_runs[candidate].append((record, efficiency))
        input_hashes.update(hashes)

    if set(grouped_rows) != {"R0", "R1", "R2"}:
        raise RuntimeError("D2.2 Round A requires complete R0/R1/R2 records")
    for candidate in ("R0", "R1", "R2"):
        if len(grouped_runs[candidate]) != 4:
            raise RuntimeError(f"{candidate}: expected 4 fold runs")
        case_ids = [row["case_id"] for row in grouped_rows[candidate]]
        if len(case_ids) != 420 or len(set(case_ids)) != 420:
            raise RuntimeError(f"{candidate}: expected 420 unique cases")
    reference_ids = {row["case_id"] for row in grouped_rows["R0"]}
    if any(
        {row["case_id"] for row in grouped_rows[candidate]} != reference_ids
        for candidate in ("R1", "R2")
    ):
        raise RuntimeError("D2.2 candidate/reference case sets differ")

    row_maps = {
        candidate: {row["case_id"]: row for row in rows}
        for candidate, rows in grouped_rows.items()
    }
    summaries = {
        candidate: aggregate(grouped_rows[candidate], grouped_runs[candidate])
        for candidate in ("R0", "R1", "R2")
    }
    reference = summaries["R0"]
    gates = protocol["candidate_gates"]

    for candidate in ("R1", "R2"):
        summary = summaries[candidate]
        reference_map = row_maps["R0"]
        candidate_map = row_maps[candidate]
        rescued = sum(
            is_disaster(reference_map[case_id])
            and not is_disaster(candidate_map[case_id])
            for case_id in reference_ids
        )
        induced = sum(
            not is_disaster(reference_map[case_id])
            and is_disaster(candidate_map[case_id])
            for case_id in reference_ids
        )
        direct_deltas = []
        for case_id in reference_ids:
            candidate_row = candidate_map[case_id]
            reference_row = reference_map[case_id]
            if not finite(candidate_row, "coarse_gt_rim_to_pred_p95_mm"):
                direct_deltas.append(1.0e30)
            elif not finite(reference_row, "coarse_gt_rim_to_pred_p95_mm"):
                direct_deltas.append(-1.0e30)
            else:
                direct_deltas.append(
                    float(candidate_row["coarse_gt_rim_to_pred_p95_mm"])
                    - float(reference_row["coarse_gt_rim_to_pred_p95_mm"])
                )
        improved = sum(delta < -1.0e-6 for delta in direct_deltas)
        worsened = sum(delta > 1.0e-6 for delta in direct_deltas)
        final_deltas = {}
        for metric in (
            "final_cd_l1_mm",
            "final_hd95_mm",
            "final_nsd_at_1mm",
        ):
            candidate_mean = summary["means"][metric]
            reference_mean = reference["means"][metric]
            if candidate_mean is None or reference_mean is None:
                final_deltas[metric] = (
                    -1.0e30 if "nsd" in metric else 1.0e30
                )
            else:
                final_deltas[metric] = candidate_mean - reference_mean
        efficiency_ratios = {
            key: summary["efficiency"][key] / reference["efficiency"][key]
            for key in summary["efficiency"]
        }
        gate_values = {
            "complete": summary["case_count"] == gates["complete_cases"],
            "nonfinite": summary["nonfinite_case_count"] == 0,
            "disaster": summary["disaster_count"] <= reference["disaster_count"],
            "final_noninferiority": (
                final_deltas["final_cd_l1_mm"]
                <= gates["final_cd_mean_delta_mm_le"]
                and final_deltas["final_hd95_mm"]
                <= gates["final_hd95_mean_delta_mm_le"]
                and final_deltas["final_nsd_at_1mm"]
                >= gates["final_nsd_at_1mm_mean_delta_ge"]
            ),
            "rim_tail": summary["rim_hd95_p95"] <= reference["rim_hd95_p95"],
            "transition": induced <= rescued,
            "direct_target_mean": (
                summary["means"]["coarse_gt_rim_to_pred_p95_mm"] is not None
                and reference["means"]["coarse_gt_rim_to_pred_p95_mm"] is not None
                and summary["means"]["coarse_gt_rim_to_pred_p95_mm"]
                <= reference["means"]["coarse_gt_rim_to_pred_p95_mm"]
            ),
            "direct_target_cases": improved >= worsened,
            "efficiency": (
                efficiency_ratios["latency_ms_median"]
                <= gates["inference_latency_ratio_le"]
                and efficiency_ratios["peak_gpu_memory_bytes"]
                <= gates["peak_memory_ratio_le"]
                and efficiency_ratios["steady_epoch_time_seconds"]
                <= gates["steady_epoch_time_ratio_le"]
            ),
        }
        final_margin = max(
            final_deltas["final_cd_l1_mm"] / 0.10,
            final_deltas["final_hd95_mm"] / 0.50,
            -final_deltas["final_nsd_at_1mm"] / 0.01,
        )
        rim_hd95_mean = summary["means"]["rim_contact_hd95_mm"]
        implant_hd95_mean = summary["means"]["implant_hd95_mm"]
        summary.update({
            "rescued": rescued,
            "induced": induced,
            "direct_target_improved": improved,
            "direct_target_worsened": worsened,
            "final_deltas_vs_R0": final_deltas,
            "efficiency_ratios_vs_R0": efficiency_ratios,
            "gates": gate_values,
            "eligible": all(gate_values.values()),
            "final_noninferiority_ranking_margin": final_margin,
            "ranking_vector": [
                summary["disaster_count"],
                summary["undefined_contact_count"],
                summary["rim_hd95_p95"],
                summary["rim_hd95_max"],
                induced - rescued,
                1.0e30 if rim_hd95_mean is None else rim_hd95_mean,
                1.0e30 if implant_hd95_mean is None else implant_hd95_mean,
                final_margin,
                summary["efficiency"]["latency_ms_median"],
            ],
        })

    # R0 is a reference only; it is never an improvement-eligible candidate.
    summaries["R0"]["eligible"] = False
    summaries["R0"]["role"] = "same_round_reference"
    eligible = sorted(
        [candidate for candidate in ("R1", "R2") if summaries[candidate]["eligible"]],
        key=lambda candidate: summaries[candidate]["ranking_vector"],
    )
    winner = eligible[0] if eligible else None
    payload = {
        "selection_version": "mamba-v12-d22-round-a-selection-v1",
        "protocol": str(args.protocol),
        "protocol_sha256": sha256_file(args.protocol),
        "implementation_amendment": str(args.amendment),
        "implementation_amendment_sha256": sha256_file(args.amendment),
        "input_sha256": dict(sorted(input_hashes.items())),
        "summaries": summaries,
        "eligible_order": eligible,
        "winner": winner,
        "round_b_allowed": winner is not None,
        "protected_splits_accessed": False,
        "locked": True,
    }
    write_locked(args.output, payload)
    for candidate in ("R1", "R2"):
        print(
            f"[gate] {candidate} eligible={summaries[candidate]['eligible']} "
            f"disaster={summaries[candidate]['disaster_count']}/"
            f"{reference['disaster_count']}"
        )
    print(f"[saved] immutable D2.2 Round-A receipt: {args.output}")
    if winner is None:
        print("[locked] R1/R2 ineligible; Round B forbidden")
        raise RuntimeError("D2.2 terminated: no experimental candidate passed all gates")
    print(f"[selected] frozen D2.2 winner={winner}")
    print("[locked] Round B may use only R0 plus this winner")


if __name__ == "__main__":
    main()
