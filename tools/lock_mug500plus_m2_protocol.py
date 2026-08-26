#!/usr/bin/env python3
"""Validate and immutably lock the MUG500+ M2 synthetic-defect protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from generate_mug500plus_m2_synthetic_defects import (
    DEFAULT_PROTOCOL,
    audit_locked_sources,
    generator_bundle_sha256,
    locate_sources,
    read_data_lock,
    sha256_bytes,
    sha256_file,
)


PROTOCOL_ID = "mug500plus-m2-synthetic-defect-v1"
EXPECTED_FAMILIES = (
    "ellipsoid_small",
    "ellipsoid_medium",
    "ellipsoid_large",
    "irregular_medium",
)


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if protocol.get("protocol_id") != PROTOCOL_ID:
        raise RuntimeError("Unexpected M2 protocol ID")
    if protocol.get("status") != "preregistered_generator_not_run":
        raise RuntimeError("M2 protocol is not in its preregistered state")
    source = protocol.get("source_data_lock", {})
    if (
        source.get("data_lock_id") != "mug500plus-m1-healthy125-v1"
        or int(source.get("healthy_skulls", 0)) != 125
        or int(source.get("qc_pass_required", 0)) != 125
        or int(source.get("duplicate_surface_groups_required", -1)) != 0
        or source.get("protected_external_validation_unlocked") is not False
    ):
        raise RuntimeError("M2 source-data boundary is not healthy125-only")

    families = tuple(protocol.get("defect_families", {}))
    if families != EXPECTED_FAMILIES:
        raise RuntimeError(f"Unexpected or reordered defect families: {families}")
    derived = protocol.get("derived_dataset", {})
    if (
        int(derived.get("defects_per_skull", 0)) != 4
        or int(derived.get("expected_cases", 0)) != 500
        or derived.get("source_dataset") != "mug500plus-v20-healthy125"
    ):
        raise RuntimeError("M2 derived-dataset cardinality is not 125 x 4")
    sampling = protocol.get("surface_sampling", {})
    if any(
        int(sampling.get(field, 0)) != 8192
        for field in ("partial_points", "implant_points", "complete_points")
    ):
        raise RuntimeError("M2 point-count contract must remain 8192/8192/8192")
    normalization = protocol.get("normalization", {})
    if normalization.get("uses_partial_only") is not True:
        raise RuntimeError("M2 normalization must use defective partial only")
    split = protocol.get("split_policy", {})
    if (
        split.get("unit") != "source_skull"
        or int(split.get("development_skulls", 0)) != 100
        or int(split.get("locked_holdout_skulls", 0)) != 25
        or int(split.get("development_folds", 0)) != 4
        or int(split.get("fold_dev_skulls", 0)) != 25
    ):
        raise RuntimeError("M2 split policy must be exact 100/25 with four folds")
    forbidden = set(protocol.get("forbidden", []))
    required_forbidden = {
        "derive_generator_parameters_from_D2_or_D2.2_failure_cases",
        "use_skullbreak_confirmation20_old_monitor_or_official_test",
        "inspect_locked_holdout_metrics during development",
    }
    if not required_forbidden.issubset(forbidden):
        raise RuntimeError("M2 forbidden-action list is incomplete")


def source_inventory_sha256(rows: Iterable[Dict[str, str]]) -> str:
    payload = "".join(
        "|".join(
            (
                row["case_id"].upper(),
                row["source_asset_sha256"].lower(),
                row["source_surface_fingerprint_sha256"].lower(),
                row["surface_fingerprint_algorithm_sha256"].lower(),
                str(int(row["file_bytes"])),
                str(int(row["triangle_count"])),
            )
        )
        + "\n"
        for row in sorted(rows, key=lambda item: item["case_id"])
    ).encode("ascii")
    return sha256_bytes(payload)


def render_outputs(
    protocol_path: Path,
    protocol: Dict[str, Any],
    data_lock_dir: Path,
    lock_rows: Iterable[Dict[str, str]],
) -> Dict[str, bytes]:
    rows = list(lock_rows)
    generator_path = Path(__file__).resolve().with_name(
        "generate_mug500plus_m2_synthetic_defects.py"
    )
    protocol_bytes = protocol_path.read_bytes()
    data_lock_files = (data_lock_dir / "files.sha256").read_bytes()
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "protocol_locked_generation_not_run",
        "healthy_source_skulls": len(rows),
        "expected_derived_cases": int(
            protocol["derived_dataset"]["expected_cases"]
        ),
        "defect_families": list(protocol["defect_families"]),
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "generator_sha256": sha256_file(generator_path),
        "generator_bundle_sha256": generator_bundle_sha256(protocol_path),
        "healthy125_files_manifest_sha256": sha256_bytes(data_lock_files),
        "healthy125_source_inventory_sha256": source_inventory_sha256(rows),
        "development_skulls_after_generation": 100,
        "locked_holdout_skulls_after_generation": 25,
        "training_unlocked": False,
        "derived_generation_started": False,
        "protected_data_used": False,
        "protected_external_validation_unlocked": False,
    }
    files = {
        "synthetic_defect_protocol.json": protocol_bytes,
        "m2_protocol_receipt.json": (
            json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }
    hashes = [
        f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)
    ]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    return files


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError(
                "Refusing to overwrite a non-identical M2 protocol lock"
            )
        print(f"[locked] existing M2 protocol is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] immutable M2 protocol lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data_lock_dir", type=Path, required=True)
    parser.add_argument("--source_root", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, default=DEFAULT_PROTOCOL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol_json.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    data_lock_dir = args.data_lock_dir.resolve()
    rows = read_data_lock(data_lock_dir)
    if len(rows) != 125:
        raise RuntimeError("M2 requires exactly 125 locked healthy skulls")
    sources = locate_sources(args.source_root.resolve(), rows)
    audit_locked_sources(sources, rows)
    files = render_outputs(protocol_path, protocol, data_lock_dir, rows)
    write_locked(files, args.output_dir.resolve())
    receipt = json.loads(files["m2_protocol_receipt.json"])
    print(f"[ok] healthy125 source inventory={len(rows)}")
    print(f"[sha256] generator={receipt['generator_sha256']}")
    print(f"[sha256] bundle={receipt['generator_bundle_sha256']}")
    print("[locked] generation and D3 training have not started")
    print("[locked] MUG500+ B-series/craniotomy data remain inaccessible")


if __name__ == "__main__":
    main()
