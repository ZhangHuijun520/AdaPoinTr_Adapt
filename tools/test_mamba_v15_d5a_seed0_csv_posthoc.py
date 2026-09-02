#!/usr/bin/env python3
"""Contract tests for the D5-A seed-0 CSV-only post-hoc analysis."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/mamba_v15_d5a_seed0_csv_posthoc_protocol_v1.json"
RUNNER = ROOT / "tools/analyze_mamba_v15_d5a_seed0_csv_posthoc.py"
SCRIPT = ROOT / "scripts/run_mamba_v15_d5a_seed0_csv_posthoc.sh"
REPORT = ROOT / "docs/mamba_v15_d5a_seed0_complete_negative_result_and_csv_posthoc_zh.md"
ARCHIVE_VERIFIER = ROOT / "tools/verify_mamba_v15_d5a_seed0_negative_archive.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("d5a_csv_posthoc", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load D5-A CSV post-hoc runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    permissions = protocol["permissions"]
    assert protocol["protocol_id"] == "mamba-v15-d5a-seed0-csv-posthoc-v1"
    assert permissions["post_hoc"] is True
    assert permissions["selection_inert"] is True
    assert permissions["checkpoint_access"] is False
    assert permissions["npz_access"] is False
    assert permissions["sealed_geometry_access"] is False
    assert permissions["optimizer_steps"] == 0
    assert permissions["D5A_seed1_training_authorized"] is False
    assert permissions["D5B_training_authorized"] is False

    runner = load_runner()
    assert runner.rank_band(33) == "33-40"
    assert runner.rank_band(41) == "41-64"
    assert runner.rank_band(65) == "65-128"
    assert runner.rank_band(129) == ">128"
    assert runner.transition_label(1, 0) == "hit_to_miss"
    runner.verify_protocol()

    text = RUNNER.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for forbidden in ("torch.load", "optimizer.step", ".npz", ".stl", "subprocess"):
        assert forbidden not in text
    assert "launch_mamba" not in script
    assert "368/400" in report
    assert "393/400" in report
    assert "selection-inert" in report

    verifier_spec = importlib.util.spec_from_file_location(
        "d5a_negative_archive_verifier", ARCHIVE_VERIFIER
    )
    if verifier_spec is None or verifier_spec.loader is None:
        raise RuntimeError("Unable to load D5-A archive verifier")
    verifier = importlib.util.module_from_spec(verifier_spec)
    verifier_spec.loader.exec_module(verifier)
    assert verifier.EXPECTED_TRANSITIONS == {
        "hit_to_hit": 312,
        "hit_to_miss": 10,
        "miss_to_hit": 56,
        "miss_to_miss": 22,
    }
    print("[ok] D5-A CSV post-hoc consumes frozen completion artifacts only")
    print("[ok] paired transitions, rank bands, and recall@K contracts are fixed")
    print("[locked] checkpoint=false geometry=false training=false sealed=false")


if __name__ == "__main__":
    main()
