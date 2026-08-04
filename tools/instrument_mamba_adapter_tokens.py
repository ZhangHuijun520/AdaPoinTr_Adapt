#!/usr/bin/env python
"""Collect observation-only internal token statistics from a Mamba adapter."""

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


INSTRUMENTATION_VERSION = "mamba-adapter-token-instrumentation-v1"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ckpt", required=True)
    parser.add_argument("--panel", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--allow_nontrain",
        action="store_true",
        help="Explicit opt-in for post-hoc val/test diagnostics.",
    )
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_panel(panel_path):
    sidecar = Path(str(panel_path) + ".sha256")
    if not sidecar.exists():
        raise FileNotFoundError(f"Panel checksum is missing: {sidecar}")
    expected = sidecar.read_text(encoding="ascii").split()[0].lower()
    actual = sha256_file(panel_path)
    if actual.lower() != expected:
        raise RuntimeError(
            f"Panel checksum mismatch: expected={expected} actual={actual}"
        )
    return actual


def write_csv(path, rows):
    if not rows:
        raise RuntimeError(f"No rows were produced for {path.name}")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def numeric_summary(rows, group_key=None):
    groups = defaultdict(list)
    for row in rows:
        groups[row[group_key] if group_key else "all"].append(row)
    output = {}
    ignored = {"sample_index", "block_index", "token_count", "feature_dim"}
    for group, group_rows in groups.items():
        metrics = {}
        for key in group_rows[0]:
            if key in ignored or isinstance(group_rows[0][key], str):
                continue
            values = np.asarray([row[key] for row in group_rows], dtype=np.float64)
            metrics[key] = {
                "count": int(values.size),
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }
        output[str(group)] = metrics
    return output


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    panel_path = Path(args.panel)
    panel_sha256 = verify_panel(panel_path)
    panel = json.loads(panel_path.read_text(encoding="utf-8"))
    split = str(panel["dataset_split"])
    if split != "train" and not args.allow_nontrain:
        raise RuntimeError(
            "Non-train instrumentation requires --allow_nontrain and must "
            "remain post-hoc only"
        )

    config = cfg_from_yaml_file(args.config)
    dataset_cfg = getattr(config.dataset, split)
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    index_by_case = {
        str(record["case_id"]): index
        for index, record in enumerate(dataset.records)
    }
    requested_cases = [str(item["case_id"]) for item in panel["cases"]]
    missing = sorted(set(requested_cases).difference(index_by_case))
    if missing:
        raise RuntimeError(f"Panel cases are absent from {split}: {missing}")

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = builder.model_builder(config.model)
    builder.load_model(model, args.ckpt)
    model.to(device)
    model.eval()
    if not hasattr(model, "enable_mamba_instrumentation"):
        raise RuntimeError("Model does not expose Mamba instrumentation")
    model.enable_mamba_instrumentation(True)

    out_dir = Path(args.out_dir)
    token_dir = out_dir / "token_arrays"
    token_dir.mkdir(parents=True, exist_ok=True)
    ordering_rows = []
    block_rows = []
    array_manifest = []

    with torch.no_grad():
        for case_id in tqdm(
            requested_cases,
            desc="Instrument Mamba tokens",
            dynamic_ncols=True,
        ):
            index = index_by_case[case_id]
            _, loaded_case_id, data = dataset[index]
            if str(loaded_case_id) != case_id:
                raise RuntimeError(
                    f"Dataset index mismatch: expected={case_id} got={loaded_case_id}"
                )
            partial, _ = data
            model.pop_mamba_instrumentation()
            prediction = model(partial.unsqueeze(0).to(device))[-1]
            instrumentation = model.pop_mamba_instrumentation()
            if instrumentation is None:
                raise RuntimeError(f"No instrumentation captured for {case_id}")
            if not torch.isfinite(prediction).all():
                raise RuntimeError(f"Non-finite prediction for {case_id}")

            record = dataset.get_record(index)
            metadata = {
                "case_id": case_id,
                "skull_id": str(record.get("skull_id", "")),
                "defect_type": str(record.get("defect_type", "")),
                "split": split,
            }
            for row in instrumentation["ordering_rows"]:
                row.update(metadata)
                ordering_rows.append(row)
            for row in instrumentation["block_rows"]:
                row.update(metadata)
                block_rows.append(row)

            array_path = token_dir / f"{case_id}.npz"
            np.savez_compressed(
                array_path,
                coor_original=instrumentation["coor_original"][0].numpy(),
                sort_idx=instrumentation["sort_idx"][0].numpy(),
                coor_ordered=instrumentation["coor_ordered"][0].numpy(),
            )
            array_manifest.append({
                **metadata,
                "path": str(array_path.relative_to(out_dir).as_posix()),
                "sha256": sha256_file(array_path),
            })

    ordering_path = out_dir / "ordering_geometry_per_case.csv"
    block_path = out_dir / "adapter_block_per_case.csv"
    manifest_path = out_dir / "token_arrays_manifest.jsonl"
    summary_path = out_dir / "instrumentation_summary.json"
    write_csv(ordering_path, ordering_rows)
    write_csv(block_path, block_rows)
    with open(manifest_path, "w", encoding="utf-8") as handle:
        for row in array_manifest:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "instrumentation_version": INSTRUMENTATION_VERSION,
        "observation_only": True,
        "config": args.config,
        "config_sha256": sha256_file(args.config),
        "checkpoint": args.ckpt,
        "checkpoint_sha256": sha256_file(args.ckpt),
        "panel": str(panel_path),
        "panel_sha256": panel_sha256,
        "split": split,
        "num_cases": len(requested_cases),
        "order": instrumentation["order"],
        "ordering_statistics": numeric_summary(ordering_rows),
        "block_statistics": numeric_summary(block_rows, "block_index"),
        "outputs": {
            "ordering_csv": ordering_path.name,
            "block_csv": block_path.name,
            "token_manifest": manifest_path.name,
        },
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for path in (ordering_path, block_path, manifest_path, summary_path):
        Path(str(path) + ".sha256").write_text(
            f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
        )
        print(f"[saved] {path}")
    print(
        f"[done] observation-only cases={len(requested_cases)} "
        f"split={split} order={instrumentation['order']}"
    )


if __name__ == "__main__":
    main()
