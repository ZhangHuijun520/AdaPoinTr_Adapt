#!/usr/bin/env python
"""Generate locked Round-B and Round-C configs from frozen receipts."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

import yaml

from generate_skullbreak_mamba_v12_dev_configs import CANDIDATES, base_config


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def dump(config):
    return yaml.safe_dump(
        config,
        sort_keys=False,
        allow_unicode=False,
        default_flow_style=False,
    ).encode("utf-8")


def write_immutable(output_dir, generated, manifest):
    generated[manifest["manifest_name"]] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    if output_dir.exists():
        mismatch = [
            name for name, payload in generated.items()
            if not (output_dir / name).is_file()
            or (output_dir / name).read_bytes() != payload
        ]
        if mismatch:
            raise RuntimeError(
                "Refusing to overwrite non-identical follow-up configs: "
                + ", ".join(mismatch)
            )
        print(f"[locked] configs are byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in generated.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] locked follow-up configs: {output_dir}")


def round_b(protocol_dir, selection_path, output_dir):
    selection = json.loads(selection_path.read_text())
    candidates = selection["selected"]
    if selection["round"] != "A" or len(candidates) != 2:
        raise ValueError("Round-B generation requires frozen Round-A top two")
    generated = {}
    for candidate in candidates:
        for fold in "ABCD":
            train_ids = str(protocol_dir / f"fold{fold}_train_case_ids.txt").replace("\\", "/")
            dev_ids = str(protocol_dir / f"fold{fold}_dev_case_ids.txt").replace("\\", "/")
            config = base_config(CANDIDATES[candidate], train_ids, dev_ids)
            config["development_protocol"] = {
                "candidate": candidate,
                "fold": fold,
                "round": "B",
                "seed": 1,
                "round_a_selection_sha256": sha256(selection_path.read_bytes()),
                "old_monitor_allowed": False,
                "official_test_allowed": False,
            }
            name = f"MambaV12Dev_{candidate}_fold{fold}_seed1.yaml"
            generated[name] = dump(config)
    manifest = {
        "manifest_name": "round_b_configs_manifest.json",
        "round": "B",
        "seed": 1,
        "candidates": candidates,
        "round_a_selection_sha256": sha256(selection_path.read_bytes()),
        "configs": {name: sha256(payload) for name, payload in sorted(generated.items())},
        "old_monitor_allowed": False,
        "official_test_allowed": False,
    }
    write_immutable(output_dir, generated, manifest)


def round_c(protocol_dir, selection_path, output_dir):
    selection = json.loads(selection_path.read_text())
    winners = selection["selected"]
    if selection["round"] != "B" or len(winners) != 1:
        raise ValueError("Round-C generation requires frozen Round-B winner")
    winner = winners[0]
    development_ids = str(protocol_dir / "development84_case_ids.txt").replace("\\", "/")
    confirmation_ids = str(protocol_dir / "confirmation20_case_ids.txt").replace("\\", "/")
    generated = {}
    for seed in (0, 1, 2):
        config = base_config(CANDIDATES[winner], development_ids, development_ids)
        config["development_protocol"] = {
            "candidate": winner,
            "round": "C_train",
            "seed": seed,
            "round_b_selection_sha256": sha256(selection_path.read_bytes()),
            "confirmation_used": False,
            "old_monitor_allowed": False,
            "official_test_allowed": False,
        }
        generated[f"MambaV12Winner_{winner}_dev84_seed{seed}.yaml"] = dump(config)

        confirmation = copy.deepcopy(config)
        for split in ("val", "test"):
            confirmation["dataset"][split]["others"]["include_case_ids_file"] = confirmation_ids
        confirmation["development_protocol"]["round"] = "C_confirmation_one_shot"
        confirmation["development_protocol"]["confirmation_used"] = True
        generated[
            f"MambaV12Winner_{winner}_confirmation20_seed{seed}.yaml"
        ] = dump(confirmation)
    manifest = {
        "manifest_name": "round_c_configs_manifest.json",
        "round": "C",
        "winner": winner,
        "seeds": [0, 1, 2],
        "round_b_selection_sha256": sha256(selection_path.read_bytes()),
        "confirmation_policy": "run all three frozen seeds once after all dev84 training completes",
        "configs": {name: sha256(payload) for name, payload in sorted(generated.items())},
        "old_monitor_allowed": False,
        "official_test_allowed": False,
    }
    write_immutable(output_dir, generated, manifest)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", choices=("B", "C"), required=True)
    parser.add_argument("--protocol_dir", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.round == "B":
        round_b(args.protocol_dir, args.selection, args.output_dir)
    else:
        round_c(args.protocol_dir, args.selection, args.output_dir)
    print("[locked] follow-up configs contain no old monitor or official test")


if __name__ == "__main__":
    main()
