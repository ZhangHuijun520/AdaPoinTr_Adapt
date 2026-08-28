#!/usr/bin/env python3
"""CPU contract tests for the P-D3 S2 decomposition helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.mamba_v14_pd3_diagnostics import decompose_s2_case  # noqa: E402


def run(scores, labels, selected):
    coordinates = torch.tensor(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]
    )
    return decompose_s2_case(
        torch.tensor(scores),
        coordinates,
        torch.tensor(labels),
        torch.tensor(selected),
        torch.tensor([[0.9, 0.0, 0.0], [1.1, 0.0, 0.0]]),
        normalization_scale=1.0,
        pool_size=2,
    )


def main() -> None:
    ranking = run([4.0, 1.0, 3.0, 2.0], [False, True, False, False], [0, 2])
    assert ranking["failure_stage"] == "ranking_miss_top96"
    assert ranking["best_positive_rank"] == 4

    selector = run([4.0, 3.0, 2.0, 1.0], [False, True, False, False], [0, 2])
    assert selector["failure_stage"] == "selector_dropped_all_positive"
    assert selector["positive_in_top_pool"] == 1

    hit = run([4.0, 3.0, 2.0, 1.0], [False, True, False, False], [0, 1])
    assert hit["failure_stage"] == "selected_hit"
    assert hit["selected_positive_proxy_count"] == 1
    assert hit["gt_rim_coverage_at_2mm"] == 1.0

    absent = run([4.0, 3.0, 2.0, 1.0], [False, False, False, False], [0, 1])
    assert absent["failure_stage"] == "oracle_absent"
    assert absent["best_positive_rank"] == 0
    print("[ok] P-D3 ranking, pool, selector, and coverage contracts")


if __name__ == "__main__":
    main()
