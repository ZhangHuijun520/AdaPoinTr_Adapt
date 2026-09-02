#!/usr/bin/env python3
"""Freeze the non-runnable D6-A R0/R1 slot32 mechanism contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "mamba_v16_d6a_slot32_mechanism_protocol_v1.json"
PROTOCOL_ID = "mamba-v16-d6a-slot32-assignment-consistent-mechanism-v1"

PARENTS = {
    "negative_result": (
        ROOT / "docs" / "mamba_v15_d5a_seed0_complete_negative_result_and_csv_posthoc_zh.md",
        "6b4eceafa24e29077fa48dae086df36bec3e6faea597793c388e05cf658f5932",
    ),
    "complete_report": (
        ROOT / "docs" / "mamba_v15_d5_complete_experiment_report_and_next_plan_zh.md",
        "f69bc137bc0d57ee43cd2ee1f4e8edad667ceabacc14875ca04180582152bfd6",
    ),
    "candidate_protocol": (
        ROOT / "docs" / "mamba_v15_d5_candidate_training_protocol_v1.json",
        "135cd7a99da57b36d94220fc8b6ed0ec73b87bb35443ddbd898e1216edba03ed",
    ),
    "v1_implementation": (
        ROOT / "utils" / "mamba_d5a_proposal.py",
        "6cca9c11f302da3ca202f3e33547c62e4584eeb0fd81f9e96c20f2787e04f070",
    ),
}

SOURCE_LOCK_HASHES = {
    "files.sha256": "d8509c44dd36575d46784972f70ec8f808754d3ffa84f390655ef3e5467c0fc1",
    "source_acquisition_lock_receipt.json": "865b9fb30ef52c532ae5dd4c5ff18405833dee0570144ee94957cf5c460dab71",
    "d6_source125_ids.txt": "f84e13b0f260beefe9308bd5bd56d18fc5d95055c24033eaad0f2d1a74c3d658",
    "d6_development100_ids.txt": "833595b000732cb56a3d729fcb1121a0c70018bf030505aa9584020498a2cc68",
    "d6_proposal_confirmation25_ids.txt": "7adb4a0dcf6eb7897d66110f32f425fa36a5c5561f729bd173200bcd1386d632",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_protocol(path: Path = PROTOCOL) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_protocol(p: Mapping[str, Any]) -> None:
    require(p.get("protocol_id") == PROTOCOL_ID, "Unexpected D6-A protocol id")
    require(
        p.get("status") == "preregistered_mechanism_locked_implementation_not_started",
        "Unexpected D6-A protocol status",
    )

    lineage = p["lineage"]
    require(
        lineage["source125_acquisition_commit"]
        == "c3b4671b263b56d2132343b88fc5842e400ad43a",
        "D6 acquisition commit drifted",
    )
    require(
        lineage["source125_acquisition_tag"]
        == "mamba-adapter-v16-d6-source125-acquisition-v1",
        "D6 acquisition tag drifted",
    )
    for key, expected in {
        "receipt_sha256": SOURCE_LOCK_HASHES["source_acquisition_lock_receipt.json"],
        "files_manifest_sha256": SOURCE_LOCK_HASHES["files.sha256"],
        "source125_ids_sha256": SOURCE_LOCK_HASHES["d6_source125_ids.txt"],
        "development100_ids_sha256": SOURCE_LOCK_HASHES["d6_development100_ids.txt"],
        "confirmation25_ids_sha256": SOURCE_LOCK_HASHES[
            "d6_proposal_confirmation25_ids.txt"
        ],
    }.items():
        require(lineage["source125_lock"][key] == expected, f"D6 source lock {key} drifted")

    parent = lineage["d5_parent"]
    require(parent["frozen_V0_hits"] == 322, "D5 V0 result drifted")
    require(parent["frozen_V1_hits"] == 368, "D5 V1 result drifted")
    require(parent["frozen_cases"] == 400, "D5 case count drifted")
    require(
        parent["D5_rerun_seed1_confirmation_D5B_authorized"] is False,
        "D5 forbidden boundary drifted",
    )

    boundary = p["data_access_boundary"]
    require(boundary["D6_source_partition_frozen"] is True, "D6 partition is not frozen")
    require(boundary["D6_geometry_extracted"] is False, "D6 geometry was opened")
    require(boundary["D6_geometry_QC_authorized"] is False, "D6 QC was authorized")
    require(boundary["D6_generation_authorized"] is False, "D6 generation was authorized")

    label = p["candidate_universe_and_label"]
    require(label["candidate_count"] == 8192, "Candidate count drifted")
    require(label["positive_mask_key"] == "reference_rim_mask", "GT key drifted")
    require(label["positive_mask_dtype"] == "bool", "GT dtype drifted")
    require(label["positive_mask_shape"] == [8192], "GT shape drifted")
    require(label["ground_truth_is_never_an_inference_input"] is True, "GT leakage")

    candidates = p["candidates"]
    require(set(candidates) == {"R0", "R1"}, "Candidate set drifted")
    r0, r1 = candidates["R0"], candidates["R1"]
    require(r0["eligibility_candidate"] is False, "R0 became eligible")
    require(r0["descriptor_dimensions"] == 27, "R0 descriptor drifted")
    require(r0["point_encoder_layers"] == [27, 64, 64], "R0 encoder drifted")
    require(r0["classifier_layers"] == [219, 128, 64, 1], "R0 head drifted")
    require(r0["selected_count"] == 32, "R0 budget drifted")
    require(r1["eligibility_candidate"] is True, "R1 eligibility drifted")
    require(r1["point_encoder_layers"] == [27, 64, 64], "R1 encoder drifted")
    require(r1["support_slots"] == 32, "Slot count drifted")
    require(r1["slot_dimensions"] == 64, "Slot dimensions drifted")
    require(r1["pointer"]["logit_shape"] == [32, 8192], "Pointer shape drifted")
    require(
        r1["parameter_gate"]["trainable_parameters_maximum"] == 100000,
        "Parameter gate drifted",
    )

    assignment = p["hard_assignment"]
    require(
        assignment["algorithm"] == "maximum_weight_rectangular_linear_sum_assignment",
        "Hard assignment changed",
    )
    require(assignment["slots"] == 32, "Assignment slots drifted")
    require(assignment["candidates"] == 8192, "Assignment candidates drifted")
    require(assignment["output_unique_indices"] == 32, "Unique budget drifted")
    require(assignment["slot_order_greedy_forbidden"] is True, "Greedy was enabled")
    require(
        assignment["random_sampling_gumbel_or_stochastic_assignment_forbidden"] is True,
        "Stochastic assignment was enabled",
    )

    ste = p["straight_through_training_assignment"]
    require(ste["softmax_temperature"] == 1.0, "STE temperature drifted")
    require(ste["temperature_scan_allowed"] is False, "Temperature scan was enabled")
    require(
        ste["hard_forward_selected_set_must_equal_inference_selected_set"] is True,
        "Training/inference assignment diverged",
    )

    loss = p["raw_loss_components"]
    require(loss["L_support"]["target_mass"] == 0.5, "Support target drifted")
    require(loss["L_support"]["beta"] == 8.0, "Support beta drifted")
    require(loss["L_shape"]["epsilon"] == 1e-8, "Shape epsilon drifted")

    calibration = p["training_only_gradient_calibration"]
    require(calibration["authorized_now"] is False, "Calibration was authorized")
    require(calibration["fixed_complete_training_batches_per_fold"] == 8, "Calibration batches drifted")
    require(calibration["batch_size_cases"] == 8, "Calibration batch size drifted")
    require(calibration["optimizer_steps"] == 0, "Calibration optimizer step allowed")
    require(calibration["dev_access"] == 0, "Calibration dev access allowed")
    require(calibration["weight_bounds"] == [0.0001, 10000.0], "Weight bounds drifted")

    zero = p["synthetic_zero_step"]
    require(zero["artificial_cases"] == 4, "Synthetic cases drifted")
    require(zero["forward_passes"] == 8, "Forward count drifted")
    require(zero["backward_passes"] == 8, "Backward count drifted")
    require(zero["optimizer_steps"] == 0, "Zero-step optimizer changed")
    require(zero["model_updates"] == 0, "Zero-step updates changed")

    lock = p["lock_effect"]
    require(lock["R0_R1_implementation_authorized_next"] is True, "Implementation not authorized")
    require(lock["toy_case_learning_test_authorized_next"] is True, "Toy test not authorized")
    for key in (
        "D6_development_extraction_authorized",
        "D6_generation_authorized",
        "gradient_calibration_authorized",
        "seed0_training_authorized",
        "seed1_training_authorized",
        "proposal_confirmation_access_authorized",
        "D6B_authorized",
        "candidate_selection_authorized",
        "protected_or_sealed_data_accessed",
    ):
        require(lock[key] is False, f"Forbidden authorization enabled: {key}")


def verify_source_lock(directory: Path) -> Dict[str, str]:
    require(directory.is_dir(), f"Missing D6 source lock: {directory}")
    for name, expected in SOURCE_LOCK_HASHES.items():
        path = directory / name
        require(path.is_file(), f"Missing source lock file: {path}")
        require(sha256_file(path) == expected, f"D6 source lock drifted: {name}")

    receipt = json.loads((directory / "source_acquisition_lock_receipt.json").read_text())
    require(receipt["status"] == "source125_terminal_two_partition_acquisition_locked", "Bad source lock status")
    require(receipt["counts"]["remaining_sources"] == 125, "Bad source125 count")
    require(receipt["counts"]["development_sources"] == 100, "Bad development100 count")
    require(receipt["counts"]["proposal_confirmation_sources"] == 25, "Bad confirmation25 count")
    require(receipt["development_extraction_authorized"] is False, "Extraction already authorized")
    require(receipt["proposal_confirmation_extraction_authorized"] is False, "Confirmation opened")
    return dict(SOURCE_LOCK_HASHES)


def verify_parent_files() -> Dict[str, str]:
    hashes = {}
    for key, (path, expected) in PARENTS.items():
        require(path.is_file(), f"Missing frozen parent: {path}")
        actual = sha256_file(path)
        require(actual == expected, f"Frozen parent drifted: {path.name}")
        hashes[key] = actual
    return hashes


def build_outputs(protocol: Mapping[str, Any], source_hashes: Mapping[str, str], parent_hashes: Mapping[str, str]) -> Dict[str, bytes]:
    outputs: Dict[str, bytes] = {}
    outputs["mechanism_protocol_v1.json"] = PROTOCOL.read_bytes()
    outputs["r0_r1_contract.json"] = canonical_json(
        {
            "candidates": protocol["candidates"],
            "candidate_universe_and_label": protocol["candidate_universe_and_label"],
            "hard_assignment": protocol["hard_assignment"],
            "straight_through_training_assignment": protocol["straight_through_training_assignment"],
            "raw_loss_components": protocol["raw_loss_components"],
            "parameter_gate": protocol["candidates"]["R1"]["parameter_gate"],
        }
    )
    outputs["zero_step_contract.json"] = canonical_json(protocol["synthetic_zero_step"])
    for candidate in ("R0", "R1"):
        outputs[f"configs/{candidate}_seed0.template.json"] = canonical_json(
            {
                "candidate": candidate,
                "non_runnable_template": True,
                "protocol_id": PROTOCOL_ID,
                "seed": 0,
                "candidate_contract": protocol["candidates"][candidate],
                "development_data_bound": False,
                "training_authorized": False,
            }
        )

    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "D6A_slot32_mechanism_frozen_implementation_not_started",
        "protocol_sha256": sha256_file(PROTOCOL),
        "source_lock_sha256": dict(source_hashes),
        "parent_sha256": dict(parent_hashes),
        "candidates": ["R0", "R1"],
        "eligible_candidate": "R1",
        "slots": 32,
        "candidate_points": 8192,
        "trainable_parameters_maximum": 100000,
        "implementation_authorized_next": True,
        "toy_tests_authorized_next": True,
        "synthetic_zero_step_authorized_after_tests": True,
        "D6_development_extraction_authorized": False,
        "D6_generation_authorized": False,
        "gradient_calibration_authorized": False,
        "training_authorized": False,
        "seed1_authorized": False,
        "proposal_confirmation_authorized": False,
        "D6B_authorized": False,
        "selection_started": False,
        "protected_or_sealed_data_accessed": False,
    }
    outputs["mechanism_lock_receipt.json"] = canonical_json(receipt)
    outputs["mechanism_lock_report_zh.md"] = (
        "# Mamba v1.6 D6-A slot32 mechanism lock\n\n"
        "- R0：精确 D5 V1 reference，仅用于新来源基线。\n"
        "- R1：32-slot、32x8192 pointer、deterministic global unique assignment。\n"
        "- 参数门控：R1 trainable parameters <= 100,000。\n"
        "- 当前只授权 implementation、toy tests，以及测试后的 artificial zero-step。\n"
        "- D6 geometry extraction、generation、calibration、training、seed-1、confirmation 与 D6-B 均未授权。\n"
    ).encode("utf-8")
    outputs["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(outputs.items())
    ).encode("ascii")
    return outputs


def write_locked(outputs: Mapping[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        require(existing == dict(outputs), f"Existing D6-A mechanism lock drifted: {output_dir}")
        print(f"[locked] existing D6-A mechanism lock is byte-identical: {output_dir}")
        return

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        for name, payload in outputs.items():
            target = working / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        working.replace(output_dir)
    except Exception:
        shutil.rmtree(working, ignore_errors=True)
        raise
    print(f"[saved] immutable D6-A slot32 mechanism lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_lock_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol = read_protocol()
    validate_protocol(protocol)
    source_hashes = verify_source_lock(args.source_lock_dir)
    parent_hashes = verify_parent_files()
    outputs = build_outputs(protocol, source_hashes, parent_hashes)
    write_locked(outputs, args.out_dir)
    print("[done] D6-A R0/R1 assignment-consistent mechanism frozen")
    print("[authorized-next] implementation, toy tests, then artificial zero-step only")
    print("[locked] extraction=false generation=false calibration=false training=false sealed=false")


if __name__ == "__main__":
    main()
