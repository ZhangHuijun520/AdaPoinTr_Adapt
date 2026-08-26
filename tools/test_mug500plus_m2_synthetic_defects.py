#!/usr/bin/env python3
"""Determinism, geometry, and protocol-boundary tests for MUG500+ M2."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import numpy as np

from generate_mug500plus_m2_synthetic_defects import (
    DEFAULT_PROTOCOL,
    choose_defect_geometry,
    deterministic_npz,
    fibonacci_directions,
    generate_point_arrays,
    sha256_file,
    stable_seed,
    triangle_areas,
)
from lock_mug500plus_m2_protocol import EXPECTED_FAMILIES, validate_protocol


def uv_sphere(radius: float = 100.0, rings: int = 80, segments: int = 160):
    vertices = [[0.0, 0.0, radius]]
    for ring in range(1, rings):
        theta = np.pi * ring / rings
        for segment in range(segments):
            phi = 2.0 * np.pi * segment / segments
            vertices.append(
                [
                    radius * np.sin(theta) * np.cos(phi),
                    radius * np.sin(theta) * np.sin(phi),
                    radius * np.cos(theta),
                ]
            )
    south = len(vertices)
    vertices.append([0.0, 0.0, -radius])
    triangles = []
    first_ring = 1
    for segment in range(segments):
        nxt = (segment + 1) % segments
        triangles.append([0, first_ring + segment, first_ring + nxt])
    for ring in range(rings - 2):
        start = 1 + ring * segments
        next_start = start + segments
        for segment in range(segments):
            nxt = (segment + 1) % segments
            triangles.append([start + segment, next_start + segment, next_start + nxt])
            triangles.append([start + segment, next_start + nxt, start + nxt])
    last_ring = 1 + (rings - 2) * segments
    for segment in range(segments):
        nxt = (segment + 1) % segments
        triangles.append([last_ring + segment, south, last_ring + nxt])
    return np.asarray(vertices, dtype=np.float64)[np.asarray(triangles)]


def main() -> None:
    protocol = json.loads(DEFAULT_PROTOCOL.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    assert tuple(protocol["defect_families"]) == EXPECTED_FAMILIES
    assert stable_seed(protocol, "A0001", "x") == stable_seed(
        protocol, "A0001", "x"
    )
    assert stable_seed(protocol, "A0001", "x") != stable_seed(
        protocol, "A0002", "x"
    )

    directions = fibonacci_directions(32)
    np.testing.assert_allclose(np.linalg.norm(directions, axis=1), 1.0, atol=1e-12)
    assert len({tuple(row) for row in directions}) == 32

    triangles = uv_sphere()
    areas = triangle_areas(triangles)
    removed_by_family = {}
    geometry_by_family = {}
    for index, family in enumerate(EXPECTED_FAMILIES):
        removed, audit = choose_defect_geometry(
            triangles, areas, "mug500plus__A0001", family, index, protocol
        )
        removed_again, audit_again = choose_defect_geometry(
            triangles, areas, "mug500plus__A0001", family, index, protocol
        )
        np.testing.assert_array_equal(removed, removed_again)
        assert audit == audit_again
        assert int(removed.sum()) >= 256
        assert int((~removed).sum()) >= 4096
        assert 0.003 <= audit["removed_surface_area_fraction"] <= 0.25
        removed_by_family[family] = removed
        geometry_by_family[family] = audit
    assert len({item["direction_slot"] for item in geometry_by_family.values()}) == 4

    reduced = copy.deepcopy(protocol)
    reduced["surface_sampling"].update(
        partial_points=2048, implant_points=2048, complete_points=2048
    )
    reduced["geometric_hard_gates"].update(
        reference_rim_band_mm=5.0, minimum_reference_rim_points=1
    )
    arrays, audit = generate_point_arrays(
        triangles,
        areas,
        removed_by_family["ellipsoid_medium"],
        "mug500plus__A0001",
        "ellipsoid_medium",
        reduced,
    )
    assert arrays["partial"].shape == (2048, 3)
    assert arrays["implant"].shape == (2048, 3)
    assert arrays["gt"].shape == (2048, 3)
    assert arrays["reference_rim_mask"].shape == (2048,)
    assert audit["reference_rim_points"] >= 1
    np.testing.assert_allclose(arrays["partial"].mean(axis=0), 0.0, atol=1e-6)
    assert np.isclose(np.linalg.norm(arrays["partial"], axis=1).max(), 1.0)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = root / "first.npz"
        second = root / "second.npz"
        deterministic_npz(first, arrays)
        deterministic_npz(second, arrays)
        assert sha256_file(first) == sha256_file(second)
        with np.load(first, allow_pickle=False) as loaded:
            assert sorted(loaded.files) == sorted(arrays)
            for key, value in arrays.items():
                np.testing.assert_array_equal(loaded[key], value)
        try:
            deterministic_npz(first, arrays)
        except RuntimeError as exc:
            assert "overwrite" in str(exc).lower()
        else:
            raise AssertionError("M2 generator overwrote an existing derived case")

    altered = copy.deepcopy(protocol)
    altered["split_policy"]["locked_holdout_skulls"] = 24
    try:
        validate_protocol(altered)
    except RuntimeError as exc:
        assert "100/25" in str(exc)
    else:
        raise AssertionError("Invalid 101/24 split was accepted")

    print("[ok] M2 protocol is exact healthy125 -> 100/25")
    print("[ok] four source-only defect families pass frozen geometry gates")
    print("[ok] point sampling and partial-only normalization are deterministic")
    print("[ok] deterministic NPZ bytes and overwrite refusal")


if __name__ == "__main__":
    main()
