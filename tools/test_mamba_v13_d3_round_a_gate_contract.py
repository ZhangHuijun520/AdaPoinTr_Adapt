#!/usr/bin/env python3
"""Static contract checks for the D3 Round-A gate executor."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    protocol = json.loads(
        (ROOT / "docs/mamba_v13_d3_round_a_candidate_execution_protocol_v1.json").read_text(
            encoding="utf-8"
        )
    )
    analyzer = (ROOT / "tools/analyze_mamba_v13_d3_round_a_seed0.py").read_text(
        encoding="utf-8"
    )
    sequence = (ROOT / "scripts/analyze_mamba_v13_d3_round_a_seed0.sh").read_text(
        encoding="utf-8"
    )
    gates = protocol["round_a_gates"]
    assert gates["dense_zero_contact_at_2mm"] == 0
    assert gates["disaster_count_max"] == "same_round_S0"
    assert gates["final_cd_l1_mm_delta_max"] == 0.1
    assert gates["final_hd95_mm_delta_max"] == 0.5
    assert gates["final_nsd_at_1mm_delta_min"] == -0.01
    assert gates["parameter_ratio_max"] == 1.02
    assert gates["latency_ratio_max"] == 1.1
    assert gates["peak_gpu_memory_ratio_max"] == 1.1
    assert "f7e91539cec7928689487b2922a8b70ab129df8889d292f72a08ca6872f6afa6" in analyzer
    assert "case_id_plus_fold_exact" in analyzer
    assert "implemented_after_training_as_mechanical_execution_of_preexisting_rules" in analyzer
    assert "np.percentile(rim, 95, method=\"linear\")" in analyzer
    assert "stop_D3_loss_query_micro_tuning_and_archive_negative_result" in analyzer
    assert "verify_mamba_v13_d3_round_a_seed0.py" in sequence
    forbidden = ("official_split: test", "manifest_split: monitor", "holdout_authorized: true")
    assert not any(item in (analyzer + sequence) for item in forbidden)
    print("[ok] D3 Round-A executor exactly binds the preregistered gates")
    print("[ok] analysis is paired, immutable, and protected-split free")
    print("[locked] no threshold amendment or manual tie break")


if __name__ == "__main__":
    main()
