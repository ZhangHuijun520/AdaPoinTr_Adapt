#!/usr/bin/env python
"""Generate immutable Round-A configs from the locked D2 protocol."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

import yaml


CANDIDATES = {
    "C0": "o0",
    "C1": "residual_budget",
    "C2": "normalized_gate",
    "C3": "bidirectional_shared",
}


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def dataset_entry(subset, case_file):
    return {
        "_base_": "cfgs/dataset_configs/SkullBreak.yaml",
        "others": {
            "DATA_ROOT": "data/SkullBreakPC_out8192",
            "subset": subset,
            "split_field": "official_split",
            "manifest_split": "train",
            "exclude_split_field": "monitor_split",
            "exclude_manifest_split": "monitor",
            "include_case_ids_file": case_file,
            "input_key": "partial",
            "target_key": "implant",
            "N_PARTIAL": 8192,
            "N_POINTS": 8192,
        },
    }


def base_config(mechanism, train_ids, dev_ids):
    return {
        "optimizer": {
            "type": "AdamW",
            "kwargs": {"lr": 0.0001, "weight_decay": 0.0005},
        },
        "scheduler": {
            "type": "LambdaLR",
            "kwargs": {
                "decay_step": 21,
                "lr_decay": 0.9,
                "lowest_decay": 0.02,
            },
        },
        "bnmscheduler": {
            "type": "Lambda",
            "kwargs": {
                "decay_step": 21,
                "bn_decay": 0.5,
                "bn_momentum": 0.9,
                "lowest_decay": 0.01,
            },
        },
        "dataset": {
            "train": dataset_entry("train", train_ids),
            "val": dataset_entry("val", dev_ids),
            "test": dataset_entry("test", dev_ids),
        },
        "model": {
            "NAME": "AdaPoinTr",
            "num_query": 256,
            "num_points": 8192,
            "center_num": [512, 256],
            "global_feature_dim": 1024,
            "encoder_type": "graph",
            "decoder_type": "fc",
            "query_selection": "learned_only",
            "denoise_weight": 0.0,
            "fine_coverage_weight": 1.0,
            "fine_local_weight": 0.0,
            "mamba_adapter": {
                "enabled": True,
                "adapter_type": "mamba_ssm",
                "depth": 2,
                "d_state": 16,
                "d_conv": 4,
                "expand": 2,
                "use_fast_path": True,
                "drop_path": 0.05,
                "alpha_init": 0.01,
                "alpha_warmup_epochs": 20,
                "alpha_warmup_start": 0.0,
                "alpha_warmup_end": 1.0,
                "order": "xyz",
                "mechanism": mechanism,
                "normalization_eps": 1.0e-6,
                "normalization_scale_min": 0.1,
                "normalization_scale_max": 10.0,
            },
            "encoder_config": {
                "embed_dim": 384,
                "depth": 6,
                "num_heads": 6,
                "k": 8,
                "n_group": 2,
                "mlp_ratio": 2.0,
                "block_style_list": [
                    "attn-graph", "attn", "attn", "attn", "attn", "attn"
                ],
                "combine_style": "concat",
            },
            "decoder_config": {
                "embed_dim": 384,
                "depth": 8,
                "num_heads": 6,
                "k": 8,
                "n_group": 2,
                "mlp_ratio": 2.0,
                "self_attn_block_style_list": [
                    "attn-graph", "attn", "attn", "attn",
                    "attn", "attn", "attn", "attn",
                ],
                "self_attn_combine_style": "concat",
                "cross_attn_block_style_list": [
                    "attn-graph", "attn", "attn", "attn",
                    "attn", "attn", "attn", "attn",
                ],
                "cross_attn_combine_style": "concat",
            },
        },
        "total_bs": 8,
        "step_per_update": 1,
        "max_epoch": 100,
        "consider_metric": "CDL2",
        "save_freq": 100,
        "save_best_checkpoint": False,
        "save_final_epoch_checkpoints": False,
    }


def generate(protocol_dir, output_dir):
    protocol = json.loads((protocol_dir / "protocol.json").read_text())
    if protocol["status"] != "preregistered_before_candidate_training":
        raise ValueError("Protocol is not in preregistered state")
    generated = {}
    for candidate, mechanism in CANDIDATES.items():
        for fold_name in "ABCD":
            train_ids = str(
                protocol_dir / f"fold{fold_name}_train_case_ids.txt"
            ).replace("\\", "/")
            dev_ids = str(
                protocol_dir / f"fold{fold_name}_dev_case_ids.txt"
            ).replace("\\", "/")
            config = base_config(mechanism, train_ids, dev_ids)
            config["development_protocol"] = {
                "name": protocol["protocol_name"],
                "candidate": candidate,
                "fold": fold_name,
                "round": "A",
                "seed": 0,
                "selection_data": "new_development_fold_only",
                "old_monitor_allowed": False,
                "official_test_allowed": False,
            }
            name = f"MambaV12Dev_{candidate}_fold{fold_name}_seed0.yaml"
            payload = yaml.safe_dump(
                config,
                sort_keys=False,
                allow_unicode=False,
                default_flow_style=False,
            ).encode("utf-8")
            generated[name] = payload

    manifest = {
        "protocol_sha256": sha256((protocol_dir / "protocol.json").read_bytes()),
        "round": "A",
        "seed": 0,
        "num_configs": len(generated),
        "configs": {
            name: sha256(payload) for name, payload in sorted(generated.items())
        },
        "locked_constraints": {
            "old_monitor_allowed": False,
            "official_test_allowed": False,
            "checkpoint": "ckpt-last at epoch 100",
            "bn_recalibration": "all fold-train batches only",
        },
    }
    generated["round_a_configs_manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    if output_dir.exists():
        mismatches = [
            name
            for name, payload in generated.items()
            if not (output_dir / name).is_file()
            or (output_dir / name).read_bytes() != payload
        ]
        if mismatches:
            raise RuntimeError(
                "Refusing to overwrite non-identical generated configs: "
                + ", ".join(mismatches)
            )
        print(f"[locked] existing Round-A configs are byte-identical: {output_dir}")
        return generated

    output_dir.mkdir(parents=True)
    for name, payload in generated.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] {len(generated) - 1} locked Round-A configs: {output_dir}")
    return generated


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    generated = generate(args.protocol_dir, args.output_dir)
    for name, payload in generated.items():
        if not name.endswith(".yaml"):
            continue
        config = yaml.safe_load(payload.decode("utf-8"))
        for split in ("train", "val", "test"):
            others = config["dataset"][split]["others"]
            if (
                others.get("split_field") != "official_split"
                or others.get("manifest_split") != "train"
                or others.get("exclude_split_field") != "monitor_split"
                or others.get("exclude_manifest_split") != "monitor"
            ):
                raise RuntimeError(
                    "Generated config escaped the strict-train boundary: "
                    f"config={name} split={split}"
                )
    print("[locked] all configs use only strict-train case-ID lists")


if __name__ == "__main__":
    main()
