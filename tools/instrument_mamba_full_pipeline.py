#!/usr/bin/env python
"""Collect observation-only summaries across the Mamba/AdaPoinTr pipeline."""

import argparse
import csv
import hashlib
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402


VERSION = "mamba-adapointr-full-pipeline-instrumentation-v1"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--split", choices=("train", "val", "test"), default="val")
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max_cases", type=int, default=0)
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_stats(tensor, prefix):
    value = tensor.float()
    flat = value.reshape(value.size(0), -1)
    rms = torch.sqrt(torch.mean(flat.square(), dim=1))
    norm = torch.linalg.vector_norm(flat, dim=1)
    return {
        f"{prefix}_rms": float(rms[0].cpu()),
        f"{prefix}_l2": float(norm[0].cpu()),
        f"{prefix}_abs_max": float(flat[0].abs().amax().cpu()),
        f"{prefix}_nonfinite": int((~torch.isfinite(flat[0])).sum().cpu()),
    }


def delta_stats(before, after, prefix):
    delta = after.float() - before.float()
    before_rms = torch.sqrt(torch.mean(before.float().square())).clamp_min(1e-12)
    delta_rms = torch.sqrt(torch.mean(delta.square()))
    cosine = torch.nn.functional.cosine_similarity(
        before.float().reshape(1, -1),
        delta.reshape(1, -1),
        dim=1,
        eps=1e-12,
    )
    return {
        f"{prefix}_delta_rms": float(delta_rms.cpu()),
        f"{prefix}_delta_to_input_rms": float((delta_rms / before_rms).cpu()),
        f"{prefix}_input_delta_cosine": float(cosine[0].cpu()),
    }


def write_csv(path, rows):
    if not rows:
        raise RuntimeError(f"No rows produced for {path}")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows, ignored):
    output = {}
    for key in rows[0]:
        if key in ignored or isinstance(rows[0][key], str):
            continue
        values = np.asarray([row[key] for row in rows], dtype=np.float64)
        output[key] = {
            "count": int(values.size),
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)) if values.size > 1 else 0.0,
            "min": float(values.min()),
            "max": float(values.max()),
        }
    return output


def main():
    args = parse_args()
    if args.max_cases < 0:
        raise ValueError("max_cases must be non-negative")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    config = cfg_from_yaml_file(args.config)
    dataset_cfg = getattr(config.dataset, args.split)
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    indices = list(range(len(dataset)))
    if args.max_cases:
        indices = indices[: args.max_cases]

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = builder.model_builder(config.model)
    builder.load_model(model, args.ckpt)
    model.to(device).eval()
    if not hasattr(model, "enable_full_instrumentation"):
        raise RuntimeError("Model does not expose full-pipeline instrumentation")
    model.enable_full_instrumentation(True)

    pipeline_rows = []
    decoder_rows = []
    adapter_rows = []
    with torch.no_grad():
        for index in tqdm(
            indices,
            desc="Instrument full pipeline",
            dynamic_ncols=True,
        ):
            _, case_id, data = dataset[index]
            partial, _ = data
            model.pop_full_instrumentation()
            prediction = model(partial.unsqueeze(0).to(device))[-1]
            records = model.pop_full_instrumentation()
            if records is None or records.get("backbone") is None:
                raise RuntimeError(f"No full instrumentation for {case_id}")
            if not torch.isfinite(prediction).all():
                raise RuntimeError(f"Non-finite prediction for {case_id}")
            backbone = records["backbone"]
            source = dataset.get_record(index)
            metadata = {
                "case_id": str(case_id),
                "skull_id": str(source.get("skull_id", "")),
                "defect_type": str(source.get("defect_type", "")),
                "split": args.split,
            }
            row = dict(metadata)
            tensors = {
                "encoder_pre_adapter": backbone["encoder_pre_adapter"],
                "encoder_post_adapter": backbone["encoder_post_adapter"],
                "query_pre_decoder": backbone["query_pre_decoder"],
                "query_post_decoder": backbone["query_post_decoder"],
                "coarse": backbone["coarse"],
                "rebuild_feature": records["rebuild_feature"],
                "relative_xyz": records["relative_xyz"],
                "prediction": prediction,
            }
            for name, tensor in tensors.items():
                row.update(tensor_stats(tensor, name))
            row.update(delta_stats(
                backbone["encoder_pre_adapter"],
                backbone["encoder_post_adapter"],
                "encoder_adapter",
            ))
            row.update(delta_stats(
                backbone["query_pre_decoder"],
                backbone["query_post_decoder"],
                "decoder_total",
            ))
            pipeline_rows.append(row)

            for layer in backbone["decoder_layers"]:
                layer_row = {
                    **metadata,
                    "layer_index": int(layer["layer_index"]),
                }
                layer_row.update(delta_stats(
                    layer["input"], layer["after_self"], "self_attention"
                ))
                layer_row.update(delta_stats(
                    layer["after_self"], layer["after_cross"], "cross_attention"
                ))
                layer_row.update(delta_stats(
                    layer["after_cross"], layer["output"], "mlp"
                ))
                layer_row.update(delta_stats(
                    layer["input"], layer["output"], "layer_total"
                ))
                decoder_rows.append(layer_row)

            adapter = backbone.get("adapter")
            if adapter is None:
                raise RuntimeError(f"No adapter instrumentation for {case_id}")
            for adapter_row in adapter["block_rows"]:
                adapter_row.update(metadata)
                adapter_rows.append(adapter_row)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pipeline_path = out_dir / "pipeline_per_case.csv"
    decoder_path = out_dir / "decoder_layer_per_case.csv"
    adapter_path = out_dir / "adapter_block_per_case.csv"
    summary_path = out_dir / "instrumentation_summary.json"
    write_csv(pipeline_path, pipeline_rows)
    write_csv(decoder_path, decoder_rows)
    write_csv(adapter_path, adapter_rows)
    summary = {
        "instrumentation_version": VERSION,
        "observation_only": True,
        "zero_perturbation_verification_required": True,
        "config": args.config,
        "config_sha256": sha256_file(args.config),
        "checkpoint": args.ckpt,
        "checkpoint_sha256": sha256_file(args.ckpt),
        "split": args.split,
        "num_cases": len(indices),
        "pipeline": summarize(
            pipeline_rows, {"case_id", "skull_id", "defect_type", "split"}
        ),
        "decoder_by_layer": {
            str(layer): summarize(
                [row for row in decoder_rows if row["layer_index"] == layer],
                {"case_id", "skull_id", "defect_type", "split", "layer_index"},
            )
            for layer in sorted({row["layer_index"] for row in decoder_rows})
        },
        "outputs": {
            "pipeline_csv": pipeline_path.name,
            "decoder_csv": decoder_path.name,
            "adapter_csv": adapter_path.name,
        },
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for path in (pipeline_path, decoder_path, adapter_path, summary_path):
        Path(str(path) + ".sha256").write_text(
            f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
        )
        print(f"[saved] {path}")
    print(f"[done] observation-only full pipeline cases={len(indices)}")


if __name__ == "__main__":
    main()
