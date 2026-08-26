#!/usr/bin/env python3
"""Test portable M2 asset resolution and NPZ-native GT-rim supervision."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from easydict import EasyDict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets.SkullBreakDataset import SkullBreak  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        asset_root = root / "audit_v1"
        case_dir = root / "cases"
        lock_dir = root / "lock"
        asset_root.mkdir()
        case_dir.mkdir()
        lock_dir.mkdir()
        case_id = "A0001__ellipsoid_small"
        partial = np.arange(24, dtype=np.float32).reshape(8, 3) / 24
        implant = partial[::-1].copy()
        mask = np.array([True, False, True, False, False, True, False, False])
        np.savez_compressed(
            case_dir / f"{case_id}.npz",
            partial=partial,
            implant=implant,
            reference_rim_mask=mask,
        )
        record = {
            "case_id": case_id,
            "skull_id": "A0001",
            "defect_type": "ellipsoid_small",
            "d3_partition": "development",
            "point_path": f"../cases/{case_id}.npz",
            "normalization": {"centroid": [0.0, 0.0, 0.0], "scale": 100.0},
            "point_audit": {"reference_rim_points": 3},
        }
        manifest = lock_dir / "manifest_with_split.jsonl"
        manifest.write_text(json.dumps(record) + "\n", encoding="utf-8")
        ids = lock_dir / "foldA_train_case_ids.txt"
        ids.write_text(case_id + "\n", encoding="utf-8")
        config = EasyDict({
            "DATA_ROOT": str(asset_root),
            "ASSET_ROOT": str(asset_root),
            "MANIFEST": str(manifest),
            "subset": "train",
            "split_field": "d3_partition",
            "manifest_split": "development",
            "include_case_ids_file": str(ids),
            "input_key": "partial",
            "target_key": "implant",
            "GT_RIM_KEY": "reference_rim_mask",
            "N_PARTIAL": 8,
            "N_POINTS": 8,
            "TAXONOMY_ID": "mug500plus_m2",
        })
        dataset = SkullBreak(config)
        _, loaded_id, (loaded_partial, loaded_implant) = dataset[0]
        assert loaded_id == case_id
        assert np.array_equal(loaded_partial.numpy(), partial)
        assert np.array_equal(loaded_implant.numpy(), implant)
        loaded_mask = dataset.get_gt_rim_masks([case_id]).numpy()[0]
        assert np.array_equal(loaded_mask, mask)
        assert dataset.get_normalization_scales([case_id]).item() == 100.0
        conflicting = EasyDict(dict(config))
        conflicting.GT_RIM_CACHE_MANIFEST = "forbidden.jsonl"
        try:
            SkullBreak(conflicting)
        except ValueError as exc:
            assert "exactly one GT-rim source" in str(exc)
        else:
            raise AssertionError("Conflicting GT-rim sources were accepted")
    print("[ok] portable M2 point paths resolve through ASSET_ROOT")
    print("[ok] reference_rim_mask loads directly from frozen NPZ")
    print("[ok] conflicting GT-rim sources are rejected")


if __name__ == "__main__":
    main()
