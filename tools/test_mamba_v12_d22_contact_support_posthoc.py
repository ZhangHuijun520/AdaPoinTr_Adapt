#!/usr/bin/env python
"""CPU-only invariants for the D2.2 contact-support post-hoc tools."""

import json
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from utils.mamba_d22_contact_support import (  # noqa: E402
    DEFAULT_BANDS,
    distance_profile,
)

ANALYSIS_PATH = Path(BASE_DIR) / "analyze_mamba_v12_d22_contact_support_posthoc.py"
SPEC = importlib.util.spec_from_file_location("d22_contact_analysis", ANALYSIS_PATH)
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)
BANDS = ANALYSIS.BANDS
paired_transitions = ANALYSIS.paired_transitions


def synthetic_row(candidate, case_id, support):
    row = {
        "candidate": candidate,
        "case_id": case_id,
        "skull_id": case_id.split("__")[1],
        "defect_type": "random_1",
        "fold": "A",
    }
    for stage in ("coarse", "dense"):
        for band in BANDS:
            key = f"{band:g}mm".replace(".", "p")
            row[f"{stage}_predicted_rim_points_at_{key}"] = (
                1 if support else 0
            )
    return row


def main():
    profile = distance_profile(
        stage_normalized=np.asarray([[0.0, 0.0, 0.0]]),
        partial_world=np.asarray([
            [1.0, 0.0, 0.0],
            [2.5, 0.0, 0.0],
            [6.0, 0.0, 0.0],
        ]),
        reference_rim_2mm_world=np.asarray([
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
        ]),
        centroid=np.zeros(3),
        scale=1.0,
    )
    expected_counts = {
        "0p5mm": 0,
        "1mm": 1,
        "2mm": 1,
        "3mm": 2,
        "4mm": 2,
        "5mm": 2,
    }
    for key, expected in expected_counts.items():
        assert profile[f"predicted_rim_points_at_{key}"] == expected
    assert profile["recovery_band_mm"] == 1.0
    assert profile["defective_to_stage_min_mm"] == 1.0
    assert profile["zero_contact_margin_at_2mm"] == -1.0

    try:
        distance_profile(
            np.asarray([[0.0, 0.0, 0.0]]),
            np.asarray([[1.0, 0.0, 0.0]]),
            np.asarray([[1.0, 0.0, 0.0]]),
            np.zeros(3),
            1.0,
            bands=(2.0,),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Contact bands must remain immutable")

    row_maps = {
        "R0": {
            "train__000__random_1": synthetic_row(
                "R0", "train__000__random_1", False
            ),
            "train__001__random_1": synthetic_row(
                "R0", "train__001__random_1", False
            ),
            "train__002__random_1": synthetic_row(
                "R0", "train__002__random_1", True
            ),
            "train__003__random_1": synthetic_row(
                "R0", "train__003__random_1", True
            ),
        },
        "R1": {},
        "R2": {},
    }
    row_maps["R1"] = {
        case_id: synthetic_row(
            "R1",
            case_id,
            case_id in {
                "train__000__random_1",
                "train__003__random_1",
            },
        )
        for case_id in row_maps["R0"]
    }
    row_maps["R2"] = {
        case_id: synthetic_row("R2", case_id, True)
        for case_id in row_maps["R0"]
    }
    transitions = paired_transitions(row_maps)
    primary_r1 = next(
        row for row in transitions
        if row["candidate"] == "R1"
        and row["stage"] == "dense"
        and row["band_mm"] == 2.0
    )
    assert primary_r1["resolved"] == 1
    assert primary_r1["induced"] == 1
    assert primary_r1["persistent_zero"] == 1
    assert primary_r1["stable_supported"] == 1

    protocol_path = Path(
        "docs/mamba_v12_d22_contact_support_posthoc_v1.json"
    )
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    assert tuple(protocol["scope"]["contact_bands_mm"]) == DEFAULT_BANDS
    integrity = protocol["integrity"]
    assert integrity["post_hoc"] is True
    assert integrity["selection_inert"] is True
    assert integrity["may_change_d22_winner"] is False
    assert integrity["may_unlock_round_b"] is False
    assert integrity["confirmation20_used"] is False
    assert integrity["old_monitor_used"] is False
    assert integrity["official_test_used"] is False
    print("[ok] D2.2 contact-support geometry and transition accounting")
    print("[ok] immutable bands and selection-inert post-hoc declaration")


if __name__ == "__main__":
    main()
