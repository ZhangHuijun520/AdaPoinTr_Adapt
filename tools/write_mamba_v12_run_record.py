#!/usr/bin/env python
"""Write one immutable machine-readable record for a D2 training run."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser()
    for name in ("candidate", "fold", "seed", "config", "checkpoint", "metrics_csv", "metrics_summary", "efficiency", "training_log", "output"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument(
        "--extra_artifact",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Additional immutable artifact to include in the run record.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    paths = {
        name: Path(getattr(args, name))
        for name in (
            "config", "checkpoint", "metrics_csv", "metrics_summary",
            "efficiency", "training_log",
        )
    }
    for item in args.extra_artifact:
        if "=" not in item:
            raise ValueError(f"Invalid --extra_artifact value: {item!r}")
        name, value = item.split("=", 1)
        if not name or name in paths:
            raise ValueError(f"Invalid/duplicate extra artifact name: {name!r}")
        paths[name] = Path(value)
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Run record inputs missing: {missing}")
    epoch_times = [
        float(value)
        for value in re.findall(
            r"EpochTime\s*=\s*([0-9.]+)",
            paths["training_log"].read_text(encoding="utf-8", errors="replace"),
        )
    ]
    if len(epoch_times) < 2:
        raise RuntimeError("Training log has fewer than two EpochTime records")
    steady_epoch_times = epoch_times[1:]
    payload = {
        "record_version": "mamba-v12-run-record-v1",
        "candidate": args.candidate,
        "fold": args.fold,
        "seed": int(args.seed),
        "fixed_checkpoint_rule": "epoch-100 ckpt-last plus full fold-train BNCal",
        "training_epoch_time_seconds_mean_excluding_first": sum(steady_epoch_times) / len(steady_epoch_times),
        "training_epochs_recorded": len(epoch_times),
        "artifacts": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in paths.items()
        },
    }
    output = Path(args.output)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if output.exists() and output.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite non-identical run record: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    Path(str(output) + ".sha256").write_text(
        f"{sha256_file(output)}  {output.name}\n", encoding="ascii"
    )
    print(f"[saved] immutable run record: {output}")


if __name__ == "__main__":
    main()
