#!/usr/bin/env python3
"""CPU/static contract checks for the receipt-bound D3 S0 pipeline."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def extract_function(path: Path, name: str):
    module = ast.parse(path.read_text(encoding="utf-8"))
    node = next(
        item for item in module.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    )
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name]


def main() -> None:
    evaluator = ROOT / "tools/evaluate_skullfix_implant.py"
    split_label = extract_function(evaluator, "record_split_label")
    legacy = SimpleNamespace(split_field="official_split", manifest_split="test")
    d3 = SimpleNamespace(split_field="d3_partition", manifest_split="development")
    assert split_label(legacy, {"split": "test", "official_split": "test"}) == "test"
    assert split_label(d3, {"d3_partition": "development"}) == "development"
    assert split_label(SimpleNamespace(manifest_split="val"), {}) == "val"
    evaluator_text = evaluator.read_text(encoding="utf-8")
    assert '"coarse_predicted_rim_points"' in evaluator_text

    efficiency = (ROOT / "tools/benchmark_mamba_v12_efficiency.py").read_text(
        encoding="utf-8"
    )
    assert '"parameter_count_total"' in efficiency
    assert '"parameter_count_trainable"' in efficiency

    fold_script = (ROOT / "scripts/run_mamba_v13_d3_s0_seed0_fold.sh").read_text(
        encoding="utf-8"
    )
    assert "--split val" in fold_script
    assert "--include_coarse_rim_metrics" in fold_script
    assert "write_mamba_v13_d3_run_record.py" in fold_script
    assert "locked_holdout" not in fold_script
    assert "official" not in fold_script.lower()

    master = (ROOT / "scripts/launch_mamba_v13_d3_s0_seed0_tmux.sh").read_text(
        encoding="utf-8"
    )
    assert "tmux new-session" in master
    assert "TQDM_MININTERVAL" in master
    assert "--verify_only" in master

    sequence = (ROOT / "scripts/run_mamba_v13_d3_s0_seed0.sh").read_text(
        encoding="utf-8"
    )
    assert "for fold in A B C D" in sequence
    assert "freeze_mamba_v13_d3_s0_seed0.py" in sequence
    assert "select_mamba" not in sequence
    assert "S1_fold" not in sequence and "S2_fold" not in sequence

    print("[ok] evaluator supports legacy and D3 split labels")
    print("[ok] dense/coarse 2 mm support counts are available for frozen gates")
    print("[ok] efficiency receipt includes parameter counts")
    print("[ok] S0 sequence is tmux/tqdm-bound and selection-inert")
    print("[locked] no holdout, S1, S2 full training, or selection path")


if __name__ == "__main__":
    main()
