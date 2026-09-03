#!/usr/bin/env python3
"""Contract tests for the D6 development100 final QC lock."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from lock_mamba_v16_d6_development100_qc import (
    duplicate_groups,
    overlap_groups,
    verify_protocol,
    verify_sealed_empty,
    write_locked,
)


def expect_failure(fn, text: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError(f"Expected RuntimeError containing {text!r}")


def row(source_id: str, asset: str, surface: str) -> dict[str, str]:
    return {
        "case_id": source_id,
        "source_asset_sha256": asset,
        "source_surface_fingerprint_sha256": surface,
    }


def main() -> None:
    protocol_path = Path(
        "docs/mamba_v16_d6_development100_final_qc_lock_protocol_v1.json"
    )
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    verify_protocol(protocol)

    clean = [row("A0001", "asset-1", "surface-1"), row("A0002", "asset-2", "surface-2")]
    assert duplicate_groups(clean, "source_asset_sha256") == {}
    duplicated = clean + [row("A0003", "asset-1", "surface-3")]
    assert duplicate_groups(duplicated, "source_asset_sha256") == {
        "asset-1": ["A0001", "A0003"]
    }
    prior = [row("A9999", "asset-2", "surface-x")]
    assert "asset-2" in overlap_groups(clean, prior, "source_asset_sha256")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        sealed = root / "sealed"
        sealed.mkdir()
        verify_sealed_empty([sealed])
        (sealed / "forbidden.zip").write_bytes(b"x")
        expect_failure(lambda: verify_sealed_empty([sealed]), "not empty")

        output = root / "lock"
        payloads = {"receipt.json": b"{}\n", "files.sha256": b""}
        write_locked(payloads, output)
        write_locked(payloads, output)
        (output / "receipt.json").write_bytes(b"drift")
        expect_failure(lambda: write_locked(payloads, output), "non-identical")

    changed = json.loads(json.dumps(protocol))
    changed["success_effect"]["synthetic_generation_authorized"] = True
    expect_failure(lambda: verify_protocol(changed), "permission boundary")

    print("[ok] D6 final-lock protocol and permission boundary are fixed")
    print("[ok] duplicate and prior-overlap hard gates are explicit")
    print("[ok] confirmation25 and immutable output behavior are enforced")
    print("[locked] generation=false calibration=false training=false confirmation=false")


if __name__ == "__main__":
    main()
