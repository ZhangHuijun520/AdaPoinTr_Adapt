#!/usr/bin/env python3
"""Validate D3 template generation, access boundaries, and runner guard."""

from __future__ import annotations

import argparse
import ast
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import yaml

from lock_mamba_v13_d3_round_a_protocol import (
    CANDIDATES,
    FOLDS,
    DEFAULT_PROTOCOL,
    render_files,
    sha256_bytes,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_runner_guard():
    source = (REPO_ROOT / "tools/runner.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    node = next(
        item
        for item in module.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "_enforce_d3_execution_guard"
    )
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "runner_guard", "exec"), namespace)
    return namespace["_enforce_d3_execution_guard"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_split_lock_dir", type=Path, required=True)
    args = parser.parse_args()
    files = render_files(DEFAULT_PROTOCOL, args.source_split_lock_dir.resolve())
    names = sorted(name for name in files if name.endswith(".template.yaml"))
    assert len(names) == 12
    assert len(set(names)) == 12
    for name in names:
        config = yaml.safe_load(files[name])
        execution = config["d3_execution"]
        candidate = execution["candidate"]
        fold = execution["fold"]
        assert candidate in CANDIDATES and fold in FOLDS
        assert execution["training_authorized"] is False
        assert execution["holdout_authorized"] is False
        assert execution["status"] == "locked_template_not_runtime_config"
        serialized = files[name].decode("utf-8")
        assert "locked_holdout_case_ids" not in serialized
        assert "manifest_split: locked_holdout" not in serialized
        train = config["dataset"]["train"]["others"]
        dev = config["dataset"]["val"]["others"]
        assert f"fold{fold}_train_case_ids.txt" in train["include_case_ids_file"]
        assert f"fold{fold}_dev_case_ids.txt" in dev["include_case_ids_file"]
        assert train["manifest_split"] == dev["manifest_split"] == "development"
        dense = config["model"]["dense_contact_objective"]
        rim = config["model"]["rim_query_allocation"]
        assert dense["enabled"] is (candidate == "S1")
        assert rim["enabled"] is (candidate == "S2")
        assert ("GT_RIM_KEY" in train) is (candidate in {"S1", "S2"})
        if candidate == "S1":
            assert (dense["threshold_mm"], dense["temperature_mm"], dense["tail_fraction"]) == (2.0, 0.25, 0.1)
        if candidate == "S2":
            assert (rim["global_queries"], rim["rim_queries"], rim["candidate_pool"]) == (224, 32, 96)
    selection = json.loads(files["round_a_selection_receipt_template.json"])
    assert selection["candidate_results"] == {name: None for name in CANDIDATES}
    assert selection["eligible_experimental_candidates"] is None
    assert selection["round_b_authorized"] is False
    assert selection["locked_holdout_accessed"] is False
    guard = load_runner_guard()
    locked = SimpleNamespace(d3_execution=SimpleNamespace(
        candidate="S1", fold="A", status="locked_template_not_runtime_config",
        training_authorized=False,
    ))
    try:
        guard(locked)
    except RuntimeError as exc:
        assert "D3 training is locked" in str(exc)
    else:
        raise AssertionError("Runner accepted a locked D3 template")
    guard(SimpleNamespace(d3_execution=SimpleNamespace(training_authorized=True)))
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name, payload in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
            expected, filename = line.split(None, 1)
            assert sha256_bytes((root / filename.strip()).read_bytes()) == expected
    print("[ok] generated exactly 12 immutable S0/S1/S2 x A-D templates")
    print("[ok] no template references the locked holdout")
    print("[ok] candidate loss/query contracts match the preregistration")
    print("[ok] runner rejects direct training from locked templates")
    print("[ok] selection receipt is unconsumed and Round B remains locked")


if __name__ == "__main__":
    main()
