#!/usr/bin/env python
"""Generate immutable D2.2 Round-A R0/R1/R2 fold configurations."""

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from generate_skullbreak_mamba_v12_dev_configs import base_config


CANDIDATES = ("R0", "R1", "R2")


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def generate(protocol_file, amendment_file, base_protocol_dir, output_dir):
    protocol = json.loads(protocol_file.read_text(encoding="utf-8"))
    if protocol["protocol_id"] != "mamba-v12-d22-local-rim-trust-v1":
        raise RuntimeError("Unexpected D2.2 protocol ID")
    if protocol["status"] != "preregistered_before_implementation":
        raise RuntimeError("D2.2 protocol is not preregistered")
    amendment = json.loads(amendment_file.read_text(encoding="utf-8"))
    if amendment["amends"] != protocol["protocol_id"]:
        raise RuntimeError("D2.2 implementation amendment targets another protocol")
    if amendment["status"] != "preregistered_before_any_d22_candidate_training":
        raise RuntimeError("D2.2 implementation amendment is not preregistered")

    generated = {}
    for candidate in CANDIDATES:
        for fold in "ABCD":
            train_ids = str(
                base_protocol_dir / f"fold{fold}_train_case_ids.txt"
            ).replace("\\", "/")
            dev_ids = str(
                base_protocol_dir / f"fold{fold}_dev_case_ids.txt"
            ).replace("\\", "/")
            config = base_config("o0", train_ids, dev_ids)
            rim_cache = (
                "logs/skullbreak_mamba_v12_d22_local_rim/"
                f"gt_rim_cache/fold{fold}/gt_rim_manifest.jsonl"
            )
            teacher_cache = (
                "logs/skullbreak_mamba_v12_d22_local_rim/"
                f"teacher_cache/seed0/fold{fold}/teacher_cache.json"
            )
            enabled = candidate in {"R1", "R2"}
            trust_enabled = candidate == "R2"
            if enabled:
                config["dataset"]["train"]["others"][
                    "GT_RIM_CACHE_MANIFEST"
                ] = rim_cache
            config["model"]["local_rim_guard"] = {
                "enabled": enabled,
                "weight": protocol["local_rim"]["lambda"],
                "rim_band_mm": protocol["local_rim"]["rim_band_mm"],
                "deadzone_mm": protocol["local_rim"]["deadzone_mm"],
                "smooth_l1_beta": protocol["local_rim"][
                    "smooth_l1_beta"
                ],
                "epsilon_mm": protocol["local_rim"]["epsilon_mm"],
                "trust_enabled": trust_enabled,
                "trust_weight": protocol["trust_region"]["lambda"],
                "centroid_tolerance_mm": protocol["trust_region"][
                    "centroid_tolerance_mm"
                ],
                "radius_log_tolerance": protocol["trust_region"][
                    "radius_log_tolerance"
                ],
                "teacher_cache": teacher_cache if trust_enabled else "",
            }
            config["development_protocol"] = {
                "name": protocol["protocol_id"],
                "candidate": candidate,
                "fold": fold,
                "round": "A",
                "seed": 0,
                "reference": "same_fold_same_seed_R0",
                "protected_splits_accessed": False,
                "confirmation_allowed": False,
                "old_monitor_allowed": False,
                "official_test_allowed": False,
            }
            name = f"MambaV12D22LocalRim_{candidate}_fold{fold}_seed0.yaml"
            generated[name] = yaml.safe_dump(
                config,
                sort_keys=False,
                allow_unicode=False,
                default_flow_style=False,
            ).encode("utf-8")

    manifest = {
        "protocol": str(protocol_file).replace("\\", "/"),
        "protocol_sha256": sha256(protocol_file.read_bytes()),
        "implementation_amendment": str(amendment_file).replace("\\", "/"),
        "implementation_amendment_sha256": sha256(
            amendment_file.read_bytes()
        ),
        "round": "A",
        "seed": 0,
        "num_configs": len(generated),
        "configs": {
            name: sha256(payload)
            for name, payload in sorted(generated.items())
        },
        "execution_order": "R0_then_teacher_cache_then_R1_then_R2_per_fold",
        "protected_splits_accessed": False,
    }
    generated["round_a_configs_manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    if output_dir.exists():
        existing = {
            path.name: path.read_bytes()
            for path in output_dir.iterdir()
            if path.is_file()
        }
        mismatches = sorted(
            name
            for name in set(existing).union(generated)
            if existing.get(name) != generated.get(name)
        )
        if mismatches:
            raise RuntimeError(
                "Refusing to overwrite non-identical D2.2 configs: "
                + ", ".join(mismatches)
            )
        print(f"[locked] existing D2.2 configs are byte-identical: {output_dir}")
        return generated

    output_dir.mkdir(parents=True)
    for name, payload in generated.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] 12 immutable D2.2 Round-A configs: {output_dir}")
    return generated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--base_protocol_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    generate(
        args.protocol,
        args.amendment,
        args.base_protocol_dir,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
