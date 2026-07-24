#!/usr/bin/env python
"""Synthetic tests for the strict SkullBreak ordering protocol."""

import json
import math
import tempfile
from pathlib import Path

from audit_skullbreak_ordering_protocol import (
    DEFECT_TYPES,
    audit_manifest,
)
from select_skullbreak_mamba_ordering import (
    FINAL_NONINFERIORITY,
    disaster,
    noninferiority,
    rank_key,
    summarize_rows,
)


def make_manifest(path):
    records = []
    for index in range(114):
        skull_id = f"train:{index:03d}"
        monitor_split = "monitor" if index < 10 else None
        for defect in sorted(DEFECT_TYPES):
            records.append(
                {
                    "case_id": f"train__{index:03d}__{defect}",
                    "skull_id": skull_id,
                    "defect_type": defect,
                    "official_split": "train",
                    "monitor_split": monitor_split,
                    "complete_mask_sha256": f"train-hash-{index:03d}",
                }
            )
    for index in range(20):
        skull_id = f"test:{index:03d}"
        for defect in sorted(DEFECT_TYPES):
            records.append(
                {
                    "case_id": f"test__{index:03d}__{defect}",
                    "skull_id": skull_id,
                    "defect_type": defect,
                    "official_split": "test",
                    "monitor_split": None,
                    "complete_mask_sha256": f"test-hash-{index:03d}",
                }
            )
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    return records


def metric_row(index, defect="random_1"):
    return {
        "case_id": f"case-{index}",
        "skull_id": f"skull-{index // 5}",
        "defect_type": defect,
        "implant_cd_l1_mm": "2.0",
        "implant_hd95_mm": "6.0",
        "implant_nsd_at_1mm": "0.25",
        "final_cd_l1_mm": "2.2",
        "final_hd95_mm": "5.0",
        "final_nsd_at_1mm": "0.15",
        "rim_contact_cd_l1_mm": "3.0",
        "rim_contact_hd95_mm": "12.0",
        "rim_contact_nsd_at_1mm": "0.55",
    }


def main():
    with tempfile.TemporaryDirectory() as temporary:
        manifest = Path(temporary) / "manifest.jsonl"
        records = make_manifest(manifest)
        report = audit_manifest(manifest)
        assert report["status"] == "pass"
        assert report["counts"]["strict_train"] == {
            "cases": 520,
            "skulls": 104,
        }
        assert report["counts"]["monitor"] == {
            "cases": 50,
            "skulls": 10,
        }
        assert report["counts"]["official_test"] == {
            "cases": 100,
            "skulls": 20,
        }

        leaking = [dict(record) for record in records]
        leaking[-1]["complete_mask_sha256"] = "train-hash-010"
        manifest.write_text(
            "".join(json.dumps(record) + "\n" for record in leaking),
            encoding="utf-8",
        )
        try:
            audit_manifest(manifest)
        except ValueError as exc:
            assert "hash overlap" in str(exc)
        else:
            raise AssertionError("expected strict/test hash overlap failure")

    normal = metric_row(0)
    assert not disaster(normal)
    nonfinite = dict(normal, rim_contact_cd_l1_mm="nan")
    assert disaster(nonfinite)
    high_cd = dict(normal, rim_contact_cd_l1_mm="50.0001")
    assert disaster(high_cd)
    boundary_cd = dict(normal, rim_contact_cd_l1_mm="50.0")
    assert not disaster(boundary_cd)
    high_hd95 = dict(normal, rim_contact_hd95_mm="50.0001")
    assert disaster(high_hd95)

    baseline_rows = [metric_row(index) for index in range(50)]
    candidate_rows = [dict(row) for row in baseline_rows]
    for row in candidate_rows:
        row["final_cd_l1_mm"] = str(
            2.2 + FINAL_NONINFERIORITY[
                "final_cd_l1_mm_max_increase"
            ]
        )
        row["final_hd95_mm"] = str(
            5.0 + FINAL_NONINFERIORITY[
                "final_hd95_mm_max_increase"
            ]
        )
        row["final_nsd_at_1mm"] = str(
            0.15 - FINAL_NONINFERIORITY[
                "final_nsd_at_1mm_max_decrease"
            ]
        )
    baseline = summarize_rows(baseline_rows)
    candidate = summarize_rows(candidate_rows)
    passed, _ = noninferiority(candidate, baseline)
    assert passed

    candidate_rows[0]["final_cd_l1_mm"] = "100.0"
    candidate = summarize_rows(candidate_rows)
    passed, _ = noninferiority(candidate, baseline)
    assert not passed

    clean_item = {
        "candidate_id": "O1",
        "summary": summarize_rows(baseline_rows),
    }
    bad_rows = [dict(row) for row in baseline_rows]
    bad_rows[0]["rim_contact_hd95_mm"] = "51.0"
    bad_item = {
        "candidate_id": "O2",
        "summary": summarize_rows(bad_rows),
    }
    assert rank_key(clean_item) < rank_key(bad_item)
    assert math.isfinite(clean_item["summary"]["mean"]["final_cd_l1_mm"])

    print("[ok] strict train/monitor/official-test isolation")
    print("[ok] pre-registered disaster thresholds")
    print("[ok] final non-inferiority boundary")
    print("[ok] deterministic disaster-first ranking")


if __name__ == "__main__":
    main()
