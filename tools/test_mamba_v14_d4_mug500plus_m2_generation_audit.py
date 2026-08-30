#!/usr/bin/env python3
"""Unit tests for the D4 M2 frozen-generation audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

from audit_mamba_v14_d4_mug500plus_m2_generation import (
    EXPECTED_AUDIT_PROTOCOL_SHA256,
    parse_relative_path,
    sha256_file,
    validate_audit_protocol,
    validate_generation_receipt,
    validate_geometry,
    validate_npz_arrays,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    ROOT / "docs/mamba_v14_d4_mug500plus_m2_generation_audit_protocol_v1.json"
)


def expect_failure(function, *args) -> None:
    try:
        function(*args)
    except (KeyError, RuntimeError):
        return
    raise AssertionError("Expected a hard failure")


def valid_arrays() -> dict[str, np.ndarray]:
    angles = np.linspace(0.0, 2.0 * np.pi, 8192, endpoint=False)
    partial = np.stack(
        [np.cos(angles), np.sin(angles), np.zeros_like(angles)], axis=1
    ).astype(np.float32)
    return {
        "partial": partial,
        "implant": partial.copy(),
        "gt": partial.copy(),
        "centroid": np.zeros(3, dtype=np.float64),
        "scale": np.asarray(1.0, dtype=np.float64),
        "reference_rim_mask": np.ones(8192, dtype=np.bool_),
    }


def main() -> None:
    assert sha256_file(PROTOCOL) == EXPECTED_AUDIT_PROTOCOL_SHA256
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_audit_protocol(protocol)
    permissive = json.loads(json.dumps(protocol))
    permissive["audit_effect"]["D4_training_authorized_on_pass"] = True
    expect_failure(validate_audit_protocol, permissive)

    arrays = valid_arrays()
    rim_count, scale = validate_npz_arrays(arrays, "case")
    assert rim_count == 8192 and scale == 1.0
    broken = dict(arrays)
    broken["partial"] = arrays["partial"][:32]
    expect_failure(validate_npz_arrays, broken, "case")

    geometry = {
        "removed_surface_area_fraction": 0.1,
        "removed_triangles": 256,
        "remaining_triangles": 4096,
    }
    assert validate_geometry(geometry, "case") == 0.1
    broken_geometry = dict(geometry, removed_triangles=255)
    expect_failure(validate_geometry, broken_geometry, "case")

    receipt = {
        "protocol_id": "mamba-v14-d4-mug500plus-m2-fourfold-v1",
        "status": "generated_training_locked_pending_D4_generation_audit",
        "generator_sha256": (
            "4ac9b1cb29f46e79e5dde1adfd8abf868e8a440dd366e25237bafcc5369c7e93"
        ),
        "source100_files_manifest_sha256": (
            "6103ebc8010441ad7a0c7eff4f96b3df0cae0e359de79258182b59917b5f12eb"
        ),
        "source100_receipt_sha256": (
            "c76cc14db549badb08bf2e9005b58f4825067c0af17431c989359e9697d0c98a"
        ),
        "source100_assets_sha256": (
            "0e81a5a41e1a972d5d2d66c3603fcb101b9d6f8b4878460f259e4035514c1d15"
        ),
        "source_skulls": 100,
        "derived_cases": 400,
        "manifest_sha256": "abc",
        "training_authorized": False,
        "candidate_selection_authorized": False,
        "protected_data_used": False,
    }
    validate_generation_receipt(receipt, "abc")
    permissive_receipt = dict(receipt, training_authorized=True)
    expect_failure(validate_generation_receipt, permissive_receipt, "abc")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        assert parse_relative_path("cases/sample.npz", root) == (
            root / "cases/sample.npz"
        ).resolve()
        expect_failure(parse_relative_path, str((root / "absolute.npz").resolve()), root)
        expect_failure(parse_relative_path, "C:\\absolute\\sample.npz", root)

    print("[ok] D4 audit protocol, receipt, NPZ, geometry, and path contracts")
    print("[locked] training=false selection=false protected=false")


if __name__ == "__main__":
    main()
