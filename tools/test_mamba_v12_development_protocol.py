#!/usr/bin/env python
"""Synthetic tests for the locked Mamba v1.2 development protocol."""

import json
import tempfile
from pathlib import Path

from lock_skullbreak_mamba_v12_development_protocol import (
    EXPECTED_DEFECT_TYPES,
    render_outputs,
    strict_train_records,
    write_locked,
)


def make_records():
    records = []
    for skull_index in range(104):
        skull_id = f"train:{skull_index:03d}"
        for defect_type in sorted(EXPECTED_DEFECT_TYPES):
            records.append({
                "case_id": f"train__{skull_index:03d}__{defect_type}",
                "skull_id": skull_id,
                "defect_type": defect_type,
                "official_split": "train",
                "monitor_split": "train",
            })
    for skull_index in range(10):
        for defect_type in sorted(EXPECTED_DEFECT_TYPES):
            records.append({
                "case_id": f"monitor__{skull_index:03d}__{defect_type}",
                "skull_id": f"monitor:{skull_index:03d}",
                "defect_type": defect_type,
                "official_split": "train",
                "monitor_split": "monitor",
            })
    for skull_index in range(20):
        for defect_type in sorted(EXPECTED_DEFECT_TYPES):
            records.append({
                "case_id": f"test__{skull_index:03d}__{defect_type}",
                "skull_id": f"test:{skull_index:03d}",
                "defect_type": defect_type,
                "official_split": "test",
                "monitor_split": "official_test",
            })
    return records


def ids(files, name):
    return set(files[name].decode("utf-8").splitlines())


def main():
    records = make_records()
    strict = strict_train_records(records)
    first = render_outputs(strict, "synthetic-manifest-sha256")
    second = render_outputs(list(reversed(strict)), "synthetic-manifest-sha256")
    assert first == second
    development = ids(first, "development84_case_ids.txt")
    confirmation = ids(first, "confirmation20_case_ids.txt")
    assert len(development) == 420
    assert len(confirmation) == 100
    assert development.isdisjoint(confirmation)
    all_fold_dev = set()
    for fold_name in "ABCD":
        fold_dev = ids(first, f"fold{fold_name}_dev_case_ids.txt")
        fold_train = ids(first, f"fold{fold_name}_train_case_ids.txt")
        assert len(fold_dev) == 105
        assert len(fold_train) == 315
        assert fold_dev.isdisjoint(fold_train)
        assert fold_dev | fold_train == development
        assert all("monitor__" not in item and "test__" not in item for item in fold_dev)
        all_fold_dev.update(fold_dev)
    assert all_fold_dev == development

    protocol = json.loads(first["protocol.json"])
    assert protocol["status"] == "preregistered_before_candidate_training"
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "protocol"
        write_locked(first, output)
        write_locked(second, output)
        (output / "protocol.json").write_text("mutated", encoding="utf-8")
        try:
            write_locked(first, output)
        except RuntimeError as exc:
            assert "Refusing to overwrite" in str(exc)
        else:
            raise AssertionError("Expected immutable protocol mutation failure")

    print("[ok] deterministic 84/20 skull-level split")
    print("[ok] four disjoint 63/21 skull folds")
    print("[ok] old monitor and official test excluded")
    print("[ok] immutable protocol and preregistered rules")


if __name__ == "__main__":
    main()
