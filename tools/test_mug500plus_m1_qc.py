#!/usr/bin/env python3
"""Synthetic tests for MUG500+ M1 STL QC and canonical fingerprints."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

import numpy as np


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from qc_mug500plus_clear_stl import (  # noqa: E402
    apply_duplicate_gate,
    canonical_surface_fingerprint,
    evaluate_stl,
)


def synthetic_triangles(count=2400):
    rng = np.random.default_rng(20260811)
    p0 = rng.uniform([-100.0, -80.0, -70.0], [100.0, 80.0, 70.0], (count, 3))
    u = rng.normal(size=(count, 3))
    v = rng.normal(size=(count, 3))
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    v -= np.sum(u * v, axis=1, keepdims=True) * u
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return np.stack((p0, p0 + 1.5 * u, p0 + 1.5 * v), axis=1)


def write_binary_stl(path, triangles):
    dtype = np.dtype(
        [("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attr", "<u2")]
    )
    rows = np.zeros(len(triangles), dtype=dtype)
    rows["vertices"] = triangles.astype("<f4")
    with path.open("wb") as handle:
        handle.write(b"MUG500+ synthetic QC".ljust(80, b"\0"))
        handle.write(struct.pack("<I", len(rows)))
        rows.tofile(handle)


def main():
    triangles = synthetic_triangles()
    bbox_min = triangles.reshape(-1, 3).min(axis=0)
    bbox_max = triangles.reshape(-1, 3).max(axis=0)
    reference = canonical_surface_fingerprint(triangles, bbox_min, bbox_max)

    transformed = triangles[::-1, ::-1] * 2.5 + np.array([17.0, -23.0, 41.0])
    transformed_min = transformed.reshape(-1, 3).min(axis=0)
    transformed_max = transformed.reshape(-1, 3).max(axis=0)
    assert canonical_surface_fingerprint(
        transformed, transformed_min, transformed_max
    ) == reference

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        valid_path = root / "A0001_clear.stl"
        duplicate_path = root / "A0002_clear.stl"
        invalid_path = root / "A0003_clear.stl"
        write_binary_stl(valid_path, triangles)
        write_binary_stl(duplicate_path, triangles[::-1, ::-1])
        write_binary_stl(invalid_path, np.zeros_like(triangles))

        valid = evaluate_stl(valid_path)
        duplicate = evaluate_stl(duplicate_path)
        invalid = evaluate_stl(invalid_path)
        assert valid["qc_pass"] is True
        assert duplicate["qc_pass"] is True
        assert invalid["qc_pass"] is False
        disk_triangles = triangles.astype(np.float32).astype(np.float64)
        disk_min = disk_triangles.reshape(-1, 3).min(axis=0)
        disk_max = disk_triangles.reshape(-1, 3).max(axis=0)
        disk_reference = canonical_surface_fingerprint(
            disk_triangles, disk_min, disk_max
        )
        assert valid["source_surface_fingerprint_sha256"] == disk_reference
        rows = [valid, duplicate]
        apply_duplicate_gate(rows)
        assert all(row["qc_pass"] is False for row in rows)
        assert all("duplicate_surface" in row["failure_reasons"] for row in rows)

    print("[ok] binary STL structural QC accepts valid geometry")
    print("[ok] degenerate geometry is rejected")
    print("[ok] fingerprint is invariant to triangle order, winding, translation, and scale")
    print("[ok] duplicate fingerprints are a hard QC failure")


if __name__ == "__main__":
    main()
