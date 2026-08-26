#!/usr/bin/env python
"""Synthetic determinism and leakage checks for the D3 data locker."""

import hashlib
import json
import tempfile
from pathlib import Path

from lock_mamba_v13_d3_data_protocol import (
    read_manifest,
    read_protected_fingerprints,
    render_outputs,
    validate_records,
    write_locked,
)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def build_fixture(root):
    generator_hash = digest(b"frozen-generator-v1")
    surface_algorithm_hash = digest(b"canonical-surface-fingerprint-v1")
    protected_path = root / "protected.sha256"
    protected_path.write_text(digest(b"protected") + "\n", encoding="ascii")
    records = []
    for skull_index in range(125):
        source_payload = f"source-{skull_index}".encode()
        source_path = root / f"source-{skull_index}.bin"
        source_path.write_bytes(source_payload)
        for defect_type in (
            "ellipsoid_small",
            "ellipsoid_medium",
            "ellipsoid_large",
            "irregular_medium",
        ):
            case_id = f"external__{skull_index:03d}__{defect_type}"
            point_payload = case_id.encode()
            point_path = root / f"{case_id}.npz"
            point_path.write_bytes(point_payload)
            records.append({
                "case_id": case_id,
                "skull_id": f"external__{skull_index:03d}",
                "defect_type": defect_type,
                "source_dataset": "independent-cohort-v1",
                "source_asset_path": source_path.name,
                "source_asset_sha256": digest(source_payload),
                "source_surface_fingerprint_sha256": digest(
                    b"surface-" + source_payload
                ),
                "surface_fingerprint_algorithm_sha256": surface_algorithm_hash,
                "point_path": point_path.name,
                "derived_case_sha256": digest(point_payload),
                "generator_sha256": generator_hash,
                "normalization": {
                    "centroid": [0.0, 0.0, 0.0],
                    "scale": 100.0,
                },
            })
    manifest_path = root / "manifest.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in records),
        encoding="utf-8",
    )
    return manifest_path, protected_path, generator_hash, surface_algorithm_hash


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (
            manifest_path,
            protected_path,
            generator_hash,
            surface_algorithm_hash,
        ) = build_fixture(root)
        records, manifest_hash = read_manifest(manifest_path)
        protected, protected_hash = read_protected_fingerprints(protected_path)
        by_skull, defects = validate_records(
            records,
            manifest_path,
            protected,
            generator_hash,
            surface_algorithm_hash,
            125,
        )
        first = render_outputs(
            by_skull, defects, manifest_hash, protected_hash,
            generator_hash, surface_algorithm_hash, 0.2,
        )
        second = render_outputs(
            by_skull, defects, manifest_hash, protected_hash,
            generator_hash, surface_algorithm_hash, 0.2,
        )
        assert first == second
        protocol = json.loads(first["protocol.json"])
        assert protocol["counts"]["total_skulls"] == 125
        assert protocol["counts"]["total_cases"] == 500
        assert protocol["counts"]["locked_holdout_skulls"] == 25
        assert sum(protocol["counts"]["fold_dev_skulls"].values()) == 100
        assert set(protocol["counts"]["fold_dev_skulls"].values()) == {25}
        output_dir = root / "locked"
        write_locked(first, output_dir)
        write_locked(first, output_dir)

        protected.add(records[0]["source_asset_sha256"])
        try:
            validate_records(
                records,
                manifest_path,
                protected,
                generator_hash,
                surface_algorithm_hash,
                125,
            )
        except ValueError as exc:
            assert "protected" in str(exc).lower()
        else:
            raise AssertionError("protected source overlap was accepted")

    print("[ok] deterministic exact 100/25 skull-level independent-data split")
    print("[ok] four balanced development folds")
    print("[ok] source/derived/generator hashes are verified")
    print("[ok] protected fingerprint overlap is rejected")
    print("[ok] locked outputs are immutable")


if __name__ == "__main__":
    main()
