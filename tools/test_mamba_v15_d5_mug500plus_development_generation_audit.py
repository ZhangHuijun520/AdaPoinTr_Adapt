#!/usr/bin/env python3
"""Unit tests for the D5 development400 frozen-generation audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

from audit_mamba_v15_d5_mug500plus_development_generation import (
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
    / "docs/mamba_v15_d5_mug500plus_development_generation_audit_protocol_v1.json"
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
    permissive["audit_effect"]["D5A_training_authorized_on_pass"] = True
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
            "mamba-v15-d5-mug500plus-development-generation-fourfold-v1"
        ),
        "status": "generated_training_locked_pending_D5_generation_audit",
        "generator_sha256": (
            "ef0664bf17435d7aa7c5efbba076ef4dc1cc49701483bdd29f743af1e0ac27e8"
        ),
        "development100_files_manifest_sha256": (
            "cb2ec987d4f5e4259464a8083bb4ca3bb632d4212bf8f1cdb140f5b404d534b4"
        ),
        "development100_receipt_sha256": (
            "c9985f0c323edb0c0bfac3b02141cda2b371844804b215450f45f17494476e56"
        ),
        "development100_assets_sha256": (
            "a60775feb127a6ca3ba33d22f877b4c4d64d532c0bb5b4bae735cdb47ab6702f"
        ),
        "source_skulls": 100,
        "derived_cases": 400,
        "manifest_sha256": "abc",
        "D5A_model_implementation_authorized": False,
        "D5A_training_authorized": False,
        "D5B_training_authorized": False,
        "candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "completion_holdout_accessed": False,
        "official_test_accessed": False,
    }
    validate_generation_receipt(receipt, "abc")
    permissive_receipt = dict(receipt, D5A_training_authorized=True)
    expect_failure(validate_generation_receipt, permissive_receipt, "abc")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        assert parse_relative_path("cases/sample.npz", root) == (
            root / "cases/sample.npz"
        ).resolve()
        expect_failure(parse_relative_path, str((root / "absolute.npz").resolve()), root)
        expect_failure(parse_relative_path, "C:\\absolute\\sample.npz", root)

    print("[ok] D5 audit protocol, receipt, NPZ, geometry, and path contracts")
    print("[locked] model=false training=false selection=false sealed=false")


if __name__ == "__main__":
    main()
