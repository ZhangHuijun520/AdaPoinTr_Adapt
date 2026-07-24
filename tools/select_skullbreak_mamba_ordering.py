#!/usr/bin/env python
"""Select a SkullBreak ordering using only the held-out monitor split."""

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from audit_skullbreak_ordering_protocol import (
    PROTOCOL_VERSION,
    audit_manifest,
    load_manifest,
    sha256_file,
    sha256_values,
)


SELECTION_VERSION = "mamba-v1.1-ordering-selection-v1"
RIM_CD_DISASTER_MM = 50.0
RIM_HD95_DISASTER_MM = 50.0
FINAL_NONINFERIORITY = {
    "final_cd_l1_mm_max_increase": 0.10,
    "final_hd95_mm_max_increase": 0.50,
    "final_nsd_at_1mm_max_decrease": 0.01,
}
REQUIRED_METRICS = (
    "implant_cd_l1_mm",
    "implant_hd95_mm",
    "implant_nsd_at_1mm",
    "final_cd_l1_mm",
    "final_hd95_mm",
    "final_nsd_at_1mm",
    "rim_contact_cd_l1_mm",
    "rim_contact_hd95_mm",
    "rim_contact_nsd_at_1mm",
)
CANDIDATES = {
    "O0": {
        "order": "xyz",
        "config": (
            "cfgs/SkullBreak_models/"
            "MambaAdapterV11OrderingO0_xyz_out8192_monitor.yaml"
        ),
        "exp_name": "skullbreak_mamba_v11_ordering_o0_xyz_seed0",
        "eval_name": "O0_xyz_monitor",
    },
    "O1": {
        "order": "identity",
        "config": (
            "cfgs/SkullBreak_models/"
            "MambaAdapterV11OrderingO1_identity_out8192_monitor.yaml"
        ),
        "exp_name": "skullbreak_mamba_v11_ordering_o1_identity_seed0",
        "eval_name": "O1_identity_monitor",
    },
    "O2": {
        "order": "zyx",
        "config": (
            "cfgs/SkullBreak_models/"
            "MambaAdapterV11OrderingO2_zyx_out8192_monitor.yaml"
        ),
        "exp_name": "skullbreak_mamba_v11_ordering_o2_zyx_seed0",
        "eval_name": "O2_zyx_monitor",
    },
    "O3": {
        "order": "xzy",
        "config": (
            "cfgs/SkullBreak_models/"
            "MambaAdapterV11OrderingO3_xzy_out8192_monitor.yaml"
        ),
        "exp_name": "skullbreak_mamba_v11_ordering_o3_xzy_seed0",
        "eval_name": "O3_xzy_monitor",
    },
}


def candidate_paths(repo_root, candidate_id):
    spec = dict(CANDIDATES[candidate_id])
    config = repo_root / spec["config"]
    config_stem = config.stem
    experiment = (
        repo_root
        / "experiments"
        / config_stem
        / "SkullBreak_models"
        / spec["exp_name"]
    )
    evaluation = (
        repo_root
        / "logs"
        / "skullbreak_mamba_ordering_v11_out8192_eval"
        / spec["eval_name"]
    )
    spec.update(
        {
            "config_path": config,
            "checkpoint_path": experiment / "ckpt-last-bncal.pth",
            "monitor_csv_path": (
                evaluation / f"{config_stem}_val_per_sample.csv"
            ),
        }
    )
    return spec


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"empty monitor CSV: {path}")
    return rows


def finite_value(row, key):
    try:
        value = float(row[key])
    except (KeyError, TypeError, ValueError):
        return math.nan
    return value if math.isfinite(value) else math.nan


def mean_metric(rows, key):
    values = [finite_value(row, key) for row in rows]
    values = [value for value in values if math.isfinite(value)]
    return sum(values) / len(values) if values else math.nan


def disaster(row):
    rim_cd = finite_value(row, "rim_contact_cd_l1_mm")
    rim_hd95 = finite_value(row, "rim_contact_hd95_mm")
    rim_nsd = finite_value(row, "rim_contact_nsd_at_1mm")
    if not all(math.isfinite(value) for value in (rim_cd, rim_hd95, rim_nsd)):
        return True
    return (
        rim_cd > RIM_CD_DISASTER_MM
        or rim_hd95 > RIM_HD95_DISASTER_MM
    )


def summarize_rows(rows):
    frontoorbital = [
        row for row in rows if row.get("defect_type") == "frontoorbital"
    ]
    return {
        "num_cases": len(rows),
        "num_skulls": len({row.get("skull_id") for row in rows}),
        "disaster_count": sum(disaster(row) for row in rows),
        "frontoorbital_disaster_count": sum(
            disaster(row) for row in frontoorbital
        ),
        "mean": {
            metric: mean_metric(rows, metric)
            for metric in REQUIRED_METRICS
        },
        "frontoorbital_mean": {
            metric: mean_metric(frontoorbital, metric)
            for metric in REQUIRED_METRICS
        },
    }


def validate_config_set(specs):
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to validate ordering configs"
        ) from exc
    canonical = None
    for candidate_id, spec in specs.items():
        with open(spec["config_path"], "r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        order = config["model"]["mamba_adapter"]["order"]
        if order != spec["order"]:
            raise ValueError(
                f"{candidate_id} expected order={spec['order']!r}, "
                f"got {order!r}"
            )
        train = config["dataset"]["train"]["others"]
        expected_filter = {
            "split_field": "official_split",
            "manifest_split": "train",
            "exclude_split_field": "monitor_split",
            "exclude_manifest_split": "monitor",
        }
        actual_filter = {
            key: train.get(key) for key in expected_filter
        }
        if actual_filter != expected_filter:
            raise ValueError(
                f"{candidate_id} is not strict-monitor training: "
                f"{actual_filter}"
            )
        val = config["dataset"]["val"]["others"]
        if (
            val.get("split_field") != "monitor_split"
            or val.get("manifest_split") != "monitor"
        ):
            raise ValueError(
                f"{candidate_id} validation is not monitor-only"
            )
        config["model"]["mamba_adapter"]["order"] = "__ORDER__"
        serialized = json.dumps(config, sort_keys=True, separators=(",", ":"))
        if canonical is None:
            canonical = serialized
        elif serialized != canonical:
            raise ValueError(
                f"{candidate_id} differs from O0 beyond ordering"
            )


def validate_monitor_rows(rows, monitor_case_ids, candidate_id):
    if len(rows) != len(monitor_case_ids):
        raise ValueError(
            f"{candidate_id} expected {len(monitor_case_ids)} monitor rows, "
            f"got {len(rows)}"
        )
    case_ids = [str(row.get("case_id", "")) for row in rows]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError(f"{candidate_id} contains duplicate case_id rows")
    if set(case_ids) != monitor_case_ids:
        missing = sorted(monitor_case_ids.difference(case_ids))
        extra = sorted(set(case_ids).difference(monitor_case_ids))
        raise ValueError(
            f"{candidate_id} monitor cases mismatch; "
            f"missing={missing[:5]} extra={extra[:5]}"
        )
    missing_columns = [
        metric for metric in REQUIRED_METRICS if metric not in rows[0]
    ]
    if missing_columns:
        raise ValueError(
            f"{candidate_id} missing metrics: {missing_columns}"
        )
    defect_counts = {}
    for row in rows:
        defect = str(row.get("defect_type", ""))
        defect_counts[defect] = defect_counts.get(defect, 0) + 1
    if defect_counts.get("frontoorbital") != 10:
        raise ValueError(
            f"{candidate_id} expected 10 frontoorbital cases, "
            f"got {defect_counts.get('frontoorbital', 0)}"
        )


def noninferiority(summary, baseline):
    epsilon = 1e-12
    candidate_mean = summary["mean"]
    baseline_mean = baseline["mean"]
    deltas = {
        metric: candidate_mean[metric] - baseline_mean[metric]
        for metric in (
            "final_cd_l1_mm",
            "final_hd95_mm",
            "final_nsd_at_1mm",
        )
    }
    passed = (
        deltas["final_cd_l1_mm"]
        <= FINAL_NONINFERIORITY["final_cd_l1_mm_max_increase"] + epsilon
        and deltas["final_hd95_mm"]
        <= FINAL_NONINFERIORITY["final_hd95_mm_max_increase"] + epsilon
        and deltas["final_nsd_at_1mm"]
        >= (
            -FINAL_NONINFERIORITY["final_nsd_at_1mm_max_decrease"]
            - epsilon
        )
    )
    return passed, deltas


def rank_key(item):
    summary = item["summary"]
    overall = summary["mean"]
    front = summary["frontoorbital_mean"]

    def ascending(value):
        return round(value, 6) if math.isfinite(value) else math.inf

    def descending(value):
        return -round(value, 6) if math.isfinite(value) else math.inf

    return (
        summary["disaster_count"],
        summary["frontoorbital_disaster_count"],
        ascending(overall["rim_contact_hd95_mm"]),
        ascending(overall["rim_contact_cd_l1_mm"]),
        descending(overall["rim_contact_nsd_at_1mm"]),
        ascending(front["implant_hd95_mm"]),
        ascending(front["implant_cd_l1_mm"]),
        ascending(front["rim_contact_hd95_mm"]),
        ascending(front["rim_contact_cd_l1_mm"]),
        descending(front["rim_contact_nsd_at_1mm"]),
        ascending(overall["implant_hd95_mm"]),
        ascending(overall["implant_cd_l1_mm"]),
        descending(overall["implant_nsd_at_1mm"]),
        ascending(overall["final_hd95_mm"]),
        ascending(overall["final_cd_l1_mm"]),
        descending(overall["final_nsd_at_1mm"]),
        item["candidate_id"],
    )


def write_checksum(path):
    checksum_path = Path(str(path) + ".sha256")
    checksum_path.write_text(
        f"{sha256_file(path)}  {Path(path).name}\n",
        encoding="ascii",
    )
    return checksum_path


def build_decision(repo_root, manifest_path):
    protocol_audit = audit_manifest(manifest_path)
    records = load_manifest(manifest_path)
    monitor_case_ids = {
        str(record["case_id"])
        for record in records
        if record.get("monitor_split") == "monitor"
    }
    specs = {
        candidate_id: candidate_paths(repo_root, candidate_id)
        for candidate_id in CANDIDATES
    }
    for candidate_id, spec in specs.items():
        for key in ("config_path", "checkpoint_path", "monitor_csv_path"):
            if not spec[key].is_file():
                raise FileNotFoundError(
                    f"{candidate_id} missing {key}: {spec[key]}"
                )
    validate_config_set(specs)

    candidates = []
    for candidate_id, spec in specs.items():
        rows = load_csv(spec["monitor_csv_path"])
        validate_monitor_rows(rows, monitor_case_ids, candidate_id)
        candidates.append(
            {
                "candidate_id": candidate_id,
                "order": spec["order"],
                "config": str(spec["config_path"].relative_to(repo_root)),
                "checkpoint": str(
                    spec["checkpoint_path"].relative_to(repo_root)
                ),
                "monitor_csv": str(
                    spec["monitor_csv_path"].relative_to(repo_root)
                ),
                "sha256": {
                    "config": sha256_file(spec["config_path"]),
                    "checkpoint": sha256_file(spec["checkpoint_path"]),
                    "monitor_csv": sha256_file(spec["monitor_csv_path"]),
                },
                "summary": summarize_rows(rows),
            }
        )

    baseline = next(
        item["summary"]
        for item in candidates
        if item["candidate_id"] == "O0"
    )
    for item in candidates:
        if item["candidate_id"] == "O0":
            passed = True
            deltas = {
                "final_cd_l1_mm": 0.0,
                "final_hd95_mm": 0.0,
                "final_nsd_at_1mm": 0.0,
            }
        else:
            passed, deltas = noninferiority(item["summary"], baseline)
        item["final_noninferiority"] = {
            "passed": passed,
            "delta_vs_O0": deltas,
        }

    eligible = [
        item
        for item in candidates
        if item["final_noninferiority"]["passed"]
    ]
    ranked = sorted(eligible, key=rank_key)
    winner = ranked[0]
    return {
        "selection_version": SELECTION_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ordering_frozen",
        "seed": 0,
        "protocol_audit": protocol_audit,
        "disaster_definition": {
            "nonfinite_any_core_rim_metric": True,
            "rim_contact_cd_l1_mm_gt": RIM_CD_DISASTER_MM,
            "rim_contact_hd95_mm_gt": RIM_HD95_DISASTER_MM,
        },
        "final_noninferiority_vs_O0": FINAL_NONINFERIORITY,
        "ranking_priority": [
            "total disaster count ascending",
            "frontoorbital disaster count ascending",
            "overall Rim HD95 ascending",
            "overall Rim CD ascending",
            "overall Rim NSD@1 descending",
            "frontoorbital Implant HD95 ascending",
            "frontoorbital Implant CD ascending",
            "frontoorbital Rim HD95 ascending",
            "frontoorbital Rim CD ascending",
            "frontoorbital Rim NSD@1 descending",
            "overall Implant HD95 ascending",
            "overall Implant CD ascending",
            "overall Implant NSD@1 descending",
            "overall Final HD95 ascending",
            "overall Final CD ascending",
            "overall Final NSD@1 descending",
            "candidate ID ascending",
        ],
        "candidates": candidates,
        "eligible_ranking": [
            item["candidate_id"] for item in ranked
        ],
        "selected": {
            "candidate_id": winner["candidate_id"],
            "order": winner["order"],
            "config": winner["config"],
            "checkpoint": winner["checkpoint"],
            "monitor_csv": winner["monitor_csv"],
            "config_sha256": winner["sha256"]["config"],
            "checkpoint_sha256": winner["sha256"]["checkpoint"],
        },
        "official_test_policy": {
            "allowed_runs": 1,
            "official_test_used_for_selection": False,
            "return_to_candidate_selection_after_official_test": False,
        },
    }


def verify_decision(repo_root, manifest_path, decision_path):
    decision_path = Path(decision_path)
    checksum_path = Path(str(decision_path) + ".sha256")
    if not decision_path.is_file() or not checksum_path.is_file():
        raise FileNotFoundError(
            f"decision or checksum missing: {decision_path}"
        )
    expected = checksum_path.read_text(encoding="ascii").split()[0].lower()
    actual = sha256_file(decision_path).lower()
    if actual != expected:
        raise ValueError("ordering decision SHA256 mismatch")
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    if decision.get("selection_version") != SELECTION_VERSION:
        raise ValueError("unsupported ordering decision version")
    audit = audit_manifest(manifest_path)
    frozen_audit = decision["protocol_audit"]
    if (
        audit["manifest_sha256"] != frozen_audit["manifest_sha256"]
        or audit["case_id_sha256"] != frozen_audit["case_id_sha256"]
    ):
        raise ValueError("current manifest differs from frozen protocol")
    selected = decision["selected"]
    config_path = repo_root / selected["config"]
    checkpoint_path = repo_root / selected["checkpoint"]
    if sha256_file(config_path) != selected["config_sha256"]:
        raise ValueError("selected config differs from frozen decision")
    if sha256_file(checkpoint_path) != selected["checkpoint_sha256"]:
        raise ValueError("selected checkpoint differs from frozen decision")
    return decision


def command_select(args):
    repo_root = Path(args.repo_root).resolve()
    decision_path = Path(args.decision)
    if decision_path.exists() or Path(str(decision_path) + ".sha256").exists():
        raise FileExistsError(
            f"refusing to overwrite frozen decision: {decision_path}"
        )
    decision = build_decision(repo_root, Path(args.manifest))
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    checksum_path = write_checksum(decision_path)
    print(
        f"[selected] {decision['selected']['candidate_id']} "
        f"order={decision['selected']['order']}"
    )
    print(f"[saved] {decision_path}")
    print(f"[saved] {checksum_path}")


def command_verify(args):
    decision = verify_decision(
        Path(args.repo_root).resolve(),
        Path(args.manifest),
        Path(args.decision),
    )
    print(
        f"[ok] frozen winner {decision['selected']['candidate_id']} "
        f"order={decision['selected']['order']}"
    )


def command_winner(args):
    decision = verify_decision(
        Path(args.repo_root).resolve(),
        Path(args.manifest),
        Path(args.decision),
    )
    selected = decision["selected"]
    for key in ("candidate_id", "order", "config", "checkpoint"):
        print(selected[key])


def command_record_official(args):
    repo_root = Path(args.repo_root).resolve()
    decision = verify_decision(
        repo_root, Path(args.manifest), Path(args.decision)
    )
    receipt_path = Path(args.receipt)
    if receipt_path.exists():
        raise FileExistsError(
            f"official-test receipt already exists: {receipt_path}"
        )
    attempt_path = Path(args.attempt)
    if not attempt_path.is_file():
        raise FileNotFoundError(
            f"official-test attempt lock is missing: {attempt_path}"
        )
    attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
    if attempt.get("decision_sha256") != sha256_file(args.decision):
        raise ValueError("official-test attempt does not match decision")
    official_csv = Path(args.official_csv)
    predictions_manifest = Path(args.predictions_manifest)
    if not official_csv.is_file() or not predictions_manifest.is_file():
        raise FileNotFoundError(
            "official CSV or predictions manifest is missing"
        )
    receipt = {
        "selection_version": SELECTION_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "decision": str(Path(args.decision)),
        "decision_sha256": sha256_file(args.decision),
        "attempt": str(attempt_path),
        "attempt_sha256": sha256_file(attempt_path),
        "selected": decision["selected"],
        "official_csv": str(official_csv),
        "official_csv_sha256": sha256_file(official_csv),
        "predictions_manifest": str(predictions_manifest),
        "predictions_manifest_sha256": sha256_file(predictions_manifest),
        "official_test_runs_consumed": 1,
        "selection_reopening_permitted": False,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_checksum(receipt_path)
    print(f"[saved] {receipt_path}")


def command_start_official(args):
    repo_root = Path(args.repo_root).resolve()
    decision = verify_decision(
        repo_root, Path(args.manifest), Path(args.decision)
    )
    attempt_path = Path(args.attempt)
    receipt_path = Path(args.receipt)
    if (
        attempt_path.exists()
        or Path(str(attempt_path) + ".sha256").exists()
        or receipt_path.exists()
        or Path(str(receipt_path) + ".sha256").exists()
    ):
        raise FileExistsError(
            "official-test attempt or receipt already exists"
        )
    attempt = {
        "selection_version": SELECTION_VERSION,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "decision": str(Path(args.decision)),
        "decision_sha256": sha256_file(args.decision),
        "selected": decision["selected"],
        "official_test_attempts_started": 1,
        "automatic_retry_permitted": False,
    }
    attempt_path.parent.mkdir(parents=True, exist_ok=True)
    attempt_path.write_text(
        json.dumps(attempt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_checksum(attempt_path)
    print(f"[started] {attempt_path}")


def build_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser):
        subparser.add_argument("--repo_root", default=".")
        subparser.add_argument(
            "--manifest",
            default="data/SkullBreakPC_out8192/manifest.jsonl",
        )
        subparser.add_argument(
            "--decision",
            default=(
                "logs/skullbreak_mamba_ordering_v11_out8192/"
                "ordering_decision_seed0.json"
            ),
        )

    select_parser = subparsers.add_parser("select")
    add_common(select_parser)
    select_parser.set_defaults(func=command_select)

    verify_parser = subparsers.add_parser("verify")
    add_common(verify_parser)
    verify_parser.set_defaults(func=command_verify)

    winner_parser = subparsers.add_parser("winner")
    add_common(winner_parser)
    winner_parser.set_defaults(func=command_winner)

    start_parser = subparsers.add_parser("start-official")
    add_common(start_parser)
    start_parser.add_argument("--attempt", required=True)
    start_parser.add_argument("--receipt", required=True)
    start_parser.set_defaults(func=command_start_official)

    receipt_parser = subparsers.add_parser("record-official")
    add_common(receipt_parser)
    receipt_parser.add_argument("--attempt", required=True)
    receipt_parser.add_argument("--official_csv", required=True)
    receipt_parser.add_argument("--predictions_manifest", required=True)
    receipt_parser.add_argument("--receipt", required=True)
    receipt_parser.set_defaults(func=command_record_official)
    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
