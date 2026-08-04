#!/usr/bin/env python
"""Lock all SkullBreak monitor cases for declared post-hoc instrumentation."""

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402


VERSION = "mamba-v1.1-o0-full-monitor-posthoc-panel-v1"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def comparable(payload):
    payload = dict(payload)
    payload.pop("created_utc", None)
    return payload


def main():
    args = parse_args()
    config_path = Path(args.config)
    config = cfg_from_yaml_file(str(config_path))
    dataset_cfg = config.dataset.val
    dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
    records = sorted(dataset.records, key=lambda row: str(row["case_id"]))
    cases = [
        {
            "case_id": str(row["case_id"]),
            "skull_id": str(row["skull_id"]),
            "defect_type": str(row.get("defect_type", "")),
        }
        for row in records
    ]
    if len(cases) != 50 or len({row["skull_id"] for row in cases}) != 10:
        raise RuntimeError(
            "Post-hoc panel must contain exactly 50 monitor cases / 10 skulls, "
            f"got {len(cases)} / {len({row['skull_id'] for row in cases})}"
        )

    payload = {
        "protocol_version": VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "declared post-hoc full-monitor internal diagnosis",
        "source_config": str(config_path.as_posix()),
        "source_config_sha256": sha256_file(config_path),
        "dataset_split": "val",
        "semantic_split": "monitor",
        "posthoc": True,
        "include_all_cases": True,
        "selection_uses_outcomes": False,
        "official_test_allowed": False,
        "num_cases": len(cases),
        "num_skulls": len({row["skull_id"] for row in cases}),
        "cases_by_defect_type": dict(
            sorted(Counter(row["defect_type"] for row in cases).items())
        ),
        "catastrophe_definition": (
            "rim_contact_hd95_mm > 50.0 or non-finite; strict greater-than"
        ),
        "cases": cases,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if comparable(existing) != comparable(payload):
            raise RuntimeError(f"Refusing to replace locked panel: {output}")
        print(f"[locked] full monitor panel unchanged: {output}")
    else:
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[saved] full monitor panel: {output}")

    sidecar = Path(str(output) + ".sha256")
    sidecar.write_text(
        f"{sha256_file(output)}  {output.name}\n", encoding="ascii"
    )
    print(f"[sha256] {sha256_file(output)}")


if __name__ == "__main__":
    main()
