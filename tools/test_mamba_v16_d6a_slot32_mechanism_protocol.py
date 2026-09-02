#!/usr/bin/env python3
"""Contract tests for the D6-A slot32 mechanism preregistration."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "lock_mamba_v16_d6a_slot32_mechanism_protocol.py"
SPEC = importlib.util.spec_from_file_location("d6a_lock", MODULE_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def must_fail(protocol, label: str) -> None:
    try:
        MOD.validate_protocol(protocol)
    except RuntimeError:
        return
    raise AssertionError(f"Expected hard failure: {label}")


def main() -> None:
    protocol = MOD.read_protocol()
    MOD.validate_protocol(protocol)

    tampered = copy.deepcopy(protocol)
    tampered["candidates"]["R1"]["support_slots"] = 31
    must_fail(tampered, "slot budget drift")

    tampered = copy.deepcopy(protocol)
    tampered["hard_assignment"]["algorithm"] = "slot_order_greedy"
    must_fail(tampered, "assignment drift")

    tampered = copy.deepcopy(protocol)
    tampered["candidate_universe_and_label"]["ground_truth_is_never_an_inference_input"] = False
    must_fail(tampered, "GT leakage")

    tampered = copy.deepcopy(protocol)
    tampered["straight_through_training_assignment"]["softmax_temperature"] = 0.5
    must_fail(tampered, "temperature scan")

    tampered = copy.deepcopy(protocol)
    tampered["lock_effect"]["D6_generation_authorized"] = True
    must_fail(tampered, "generation side effect")

    tampered = copy.deepcopy(protocol)
    tampered["training_only_gradient_calibration"]["optimizer_steps"] = 1
    must_fail(tampered, "calibration optimizer step")

    source_hashes = dict(MOD.SOURCE_LOCK_HASHES)
    parent_hashes = {key: expected for key, (_, expected) in MOD.PARENTS.items()}
    outputs_a = MOD.build_outputs(protocol, source_hashes, parent_hashes)
    outputs_b = MOD.build_outputs(protocol, source_hashes, parent_hashes)
    assert outputs_a == outputs_b
    assert "files.sha256" in outputs_a
    assert b"training_authorized\": false" in outputs_a["mechanism_lock_receipt.json"]

    print("[ok] R0/R1, slot32, assignment, STE, loss and parameter contracts are fixed")
    print("[ok] GT leakage, temperature scan and permission escalation hard-fail")
    print("[ok] immutable non-runnable lock outputs are deterministic")
    print("[locked] extraction=false generation=false calibration=false training=false sealed=false")


if __name__ == "__main__":
    main()
