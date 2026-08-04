#!/usr/bin/env python
"""Lock a metadata-only strict-train panel for Mamba instrumentation."""

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402


PROTOCOL_VERSION = "mamba-v1.1-o0-multiseed-instrumentation-panel-v1"
DEFAULT_SELECTION_SEED = 20260803


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Select a deterministic, defect-balanced, skull-disjoint panel "
            "using only strict-train metadata."
        )
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--num_cases", type=int, default=20)
    parser.add_argument("--selection_seed", type=int, default=DEFAULT_SELECTION_SEED)
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ranking_key(seed, record):
    text = "|".join(
        (
            str(seed),
            str(record.get("defect_type", "")),
            str(record["skull_id"]),
            str(record["case_id"]),
        )
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def select_records(records, num_cases, selection_seed):
    if num_cases < 1:
        raise ValueError("num_cases must be positive")
    groups = defaultdict(list)
    for record in records:
        groups[str(record.get("defect_type", "unknown"))].append(record)
    defect_types = sorted(groups)
    if not defect_types:
        raise ValueError("No defect types are available for panel selection")

    base, remainder = divmod(num_cases, len(defect_types))
    targets = {
        defect: base + (index < remainder)
        for index, defect in enumerate(defect_types)
    }
    selected = []
    selected_skulls = set()
    for defect in defect_types:
        candidates = sorted(
            groups[defect], key=lambda row: ranking_key(selection_seed, row)
        )
        for record in candidates:
            skull_id = str(record["skull_id"])
            if skull_id in selected_skulls:
                continue
            selected.append(record)
            selected_skulls.add(skull_id)
            if sum(
                str(item.get("defect_type", "unknown")) == defect
                for item in selected
            ) == targets[defect]:
                break

    if len(selected) != num_cases:
        counts = Counter(
            str(item.get("defect_type", "unknown")) for item in selected
        )
        raise RuntimeError(
            "Could not build the requested skull-disjoint balanced panel: "
            f"selected={len(selected)} requested={num_cases} counts={dict(counts)}"
        )
    return sorted(selected, key=lambda row: str(row["case_id"])), targets


def comparable_payload(payload):
    result = dict(payload)
    result.pop("created_utc", None)
    return result


def write_sha256(path):
    sidecar = Path(str(path) + ".sha256")
    sidecar.write_text(
        f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
    )
    return sidecar


def main():
    args = parse_args()
    config_path = Path(args.config)
    config = cfg_from_yaml_file(str(config_path))
    dataset_cfg = config.dataset.train
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)

    records, targets = select_records(
        dataset.records,
        args.num_cases,
        args.selection_seed,
    )
    cases = [
        {
            "case_id": str(record["case_id"]),
            "skull_id": str(record["skull_id"]),
            "defect_type": str(record.get("defect_type", "")),
        }
        for record in records
    ]
    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "observation-only internal token diagnostics",
        "source_config": str(config_path.as_posix()),
        "source_config_sha256": sha256_file(config_path),
        "dataset_split": "train",
        "strict_train_required": True,
        "selection_uses_outcomes": False,
        "selection_algorithm": (
            "sha256 rank within defect type; balanced allocation; globally "
            "unique skull_id"
        ),
        "selection_seed": int(args.selection_seed),
        "num_cases": len(cases),
        "num_skulls": len({case["skull_id"] for case in cases}),
        "target_cases_by_defect_type": targets,
        "actual_cases_by_defect_type": dict(
            sorted(Counter(case["defect_type"] for case in cases).items())
        ),
        "frozen_model": "Mamba Adapter v1.1 O0 xyz out8192",
        "replication_seeds": [1, 2],
        "official_test_allowed": False,
        "catastrophe_definition": (
            "rim_contact_hd95_mm > 50.0 or non-finite; strict greater-than"
        ),
        "cases": cases,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if comparable_payload(existing) != comparable_payload(payload):
            raise RuntimeError(
                f"Refusing to replace locked instrumentation panel: {output}"
            )
        sidecar = Path(str(output) + ".sha256")
        if not sidecar.exists():
            write_sha256(output)
        print(f"[locked] existing panel is unchanged: {output}")
        print(f"[sha256] {sha256_file(output)}")
        return

    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    sidecar = write_sha256(output)
    print(
        f"[saved] {output} cases={payload['num_cases']} "
        f"skulls={payload['num_skulls']}"
    )
    print(f"[saved] {sidecar}")


if __name__ == "__main__":
    main()
