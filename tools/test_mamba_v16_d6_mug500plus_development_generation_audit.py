#!/usr/bin/env python3
"""Unit tests for the D6 development400 frozen-generation audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

from audit_mamba_v16_d6_mug500plus_development_generation import (
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
    ROOT
    / "docs/mamba_v16_d6_mug500plus_development_generation_audit_protocol_v1.json"
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
    permissive["audit_effect"]["D6_gradient_calibration_authorized_on_pass"] = True
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
        "protocol_id": (
            "mamba-v16-d6-mug500plus-development-generation-fourfold-v1"
        ),
        "status": "generated_training_locked_pending_D6_generation_audit",
        "generator_sha256": (
            "793306c4b0ec9ed0079c891f4f4c1b82590fb4b77dce5f9cd7a8a8885fe99a84"
        ),
        "development100_files_manifest_sha256": (
            "ba62bbe839e044d98a1f73be2fa2d0f2973ca771ab9e0911548dd77e81376ed2"
        ),
        "development100_receipt_sha256": (
            "97e26338d4d4bff743a20e0a830ca6e34f1c64f8dfd0de5115d91f22aec93cef"
        ),
        "development100_assets_sha256": (
            "a1f06fba94158074a116033d62b37c267479c7f630a10bee94c0383980083d0c"
        ),
        "source_skulls": 100,
        "derived_cases": 400,
        "manifest_sha256": "abc",
        "D6A_R0_R1_implementation_frozen": True,
        "D6_gradient_calibration_authorized": False,
        "D6A_training_authorized": False,
        "D6_seed1_authorized": False,
        "D6B_training_authorized": False,
        "candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "official_test_accessed": False,
    }
    validate_generation_receipt(receipt, "abc")
    permissive_receipt = dict(receipt, D6_gradient_calibration_authorized=True)
    expect_failure(validate_generation_receipt, permissive_receipt, "abc")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        assert parse_relative_path("cases/sample.npz", root) == (
            root / "cases/sample.npz"
        ).resolve()
        expect_failure(parse_relative_path, str((root / "absolute.npz").resolve()), root)
        expect_failure(parse_relative_path, "C:\\absolute\\sample.npz", root)

    print("[ok] D6 audit protocol, receipt, NPZ, geometry, and path contracts")
    print(
        "[locked] calibration=false training=false seed1=false "
        "D6B=false selection=false confirmation=false"
    )


if __name__ == "__main__":
    main()
