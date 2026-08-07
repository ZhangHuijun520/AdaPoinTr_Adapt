#!/usr/bin/env python
"""Generate immutable D2.1 Q0-Q3 fold configs from the locked amendment."""

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from generate_skullbreak_mamba_v12_dev_configs import base_config


CANDIDATES = {
    "Q0": {"enabled": False, "mode": "none"},
    "Q1": {"enabled": True, "mode": "centroid"},
    "Q2": {"enabled": True, "mode": "centroid_radius"},
    "Q3": {"enabled": True, "mode": "coverage_cvar"},
}


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def generate(base_protocol_dir, amendment_file, output_dir):
    amendment = json.loads(amendment_file.read_text())
    if amendment["status"] != "preregistered_before_d21_candidate_training":
        raise RuntimeError("D2.1 amendment is not preregistered")
    if amendment["data_boundary"]["locked_confirmation20_allowed"]:
        raise RuntimeError("D2.1 amendment leaked locked confirmation")

    common = amendment["geometry_loss_common"]
    generated = {}
    for candidate, guard in CANDIDATES.items():
        expected_mode = amendment["candidates"][candidate]["mode"]
        if guard["mode"] != expected_mode:
            raise RuntimeError(f"Candidate mode mismatch: {candidate}")
        for fold in "ABCD":
            train_ids = str(
                base_protocol_dir / f"fold{fold}_train_case_ids.txt"
            ).replace("\\", "/")
            dev_ids = str(
                base_protocol_dir / f"fold{fold}_dev_case_ids.txt"
            ).replace("\\", "/")
            config = base_config("o0", train_ids, dev_ids)
            config["model"]["coarse_geometry_guard"] = {
                "enabled": guard["enabled"],
                "mode": guard["mode"],
                "weight": common["weight"] if guard["enabled"] else 0.0,
                "smooth_l1_beta": common["smooth_l1_beta"],
                "cvar_fraction": 0.1,
                "eps": common["eps"],
            }
            config["development_protocol"] = {
                "name": amendment["protocol_name"],
                "amends": amendment["amends"],
                "candidate": candidate,
                "fold": fold,
                "round": "A",
                "seed": 0,
                "development84_reused": True,
                "locked_confirmation_allowed": False,
                "old_monitor_allowed": False,
                "official_test_allowed": False,
            }
            name = f"MambaV12D21Geometry_{candidate}_fold{fold}_seed0.yaml"
            generated[name] = yaml.safe_dump(
                config,
                sort_keys=False,
                allow_unicode=False,
                default_flow_style=False,
            ).encode("utf-8")

    manifest = {
        "protocol_amendment": str(amendment_file),
        "protocol_amendment_sha256": sha256(amendment_file.read_bytes()),
        "round": "A",
        "seed": 0,
        "num_configs": len(generated),
        "configs": {
            name: sha256(content) for name, content in sorted(generated.items())
        },
        "protected_data": {
            "locked_confirmation_allowed": False,
            "old_monitor_allowed": False,
            "official_test_allowed": False,
        },
    }
    generated["round_a_configs_manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    if output_dir.exists():
        extras = sorted(
            path.name for path in output_dir.iterdir() if path.name not in generated
        )
        mismatches = [
            name for name, content in generated.items()
            if not (output_dir / name).is_file()
            or (output_dir / name).read_bytes() != content
        ]
        if extras or mismatches:
            raise RuntimeError(
                f"Refusing to overwrite D2.1 configs: mismatches={mismatches}, extras={extras}"
            )
        print(f"[locked] existing D2.1 configs are byte-identical: {output_dir}")
        return

    output_dir.mkdir(parents=True)
    for name, content in generated.items():
        (output_dir / name).write_bytes(content)
    print(f"[saved] 16 locked D2.1 configs: {output_dir}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_protocol_dir", type=Path, required=True)
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    generate(args.base_protocol_dir, args.amendment, args.output_dir)


if __name__ == "__main__":
    main()
