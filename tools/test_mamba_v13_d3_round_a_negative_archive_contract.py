#!/usr/bin/env python3
"""Static safety checks for the D3 Round-A negative archive scripts."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    archive = (ROOT / "scripts/archive_mamba_v13_d3_round_a_negative_seed0.sh").read_text(
        encoding="utf-8"
    )
    verify = (ROOT / "tools/verify_mamba_v13_d3_round_a_negative_archive.py").read_text(
        encoding="utf-8"
    )
    restore = (ROOT / "scripts/verify_mamba_v13_d3_round_a_negative_archive.sh").read_text(
        encoding="utf-8"
    )
    assert 'PART_SIZE="${PART_SIZE:-256M}"' in archive
    assert 'tar -cf -' in archive and '| split -b "$PART_SIZE"' in archive
    assert 'cat "${parts[@]}" | tar -xf -' in archive
    assert "expected exactly eight" in verify.lower()
    assert "round_a_frozen_negative_no_experimental_candidate_passed" in verify
    assert "seed1_authorized=false" in archive
    assert "holdout_accessed=false" in archive
    assert "official_test_accessed=false" in archive
    assert "candidate_or_rule_revision_authorized=false" in archive
    assert "verify_mamba_v13_d3_round_a_negative_archive.py" in archive
    assert 'tar -tf -' in restore
    assert "MUG500plusM2_v1/audit_v1" not in archive
    print("[ok] D3 archive is split-only, restore-verified, and checkpoint-bounded")
    print("[ok] protected data assets and prohibited continuations are excluded")
    print("[locked] seed1=false holdout=false official_test=false rule_revision=false")


if __name__ == "__main__":
    main()
