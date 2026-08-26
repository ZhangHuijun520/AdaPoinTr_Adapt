#!/usr/bin/env python3
"""Static contract tests for the preregistered S2 feasibility stage."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def function_node(source: str, class_name: str, function_name: str):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == function_name:
                    return item
    raise AssertionError(f"Missing {class_name}.{function_name}")


def main() -> None:
    amendment = json.loads(
        (
            ROOT
            / "docs/mamba_v13_d3_s2_head_only_feasibility_execution_amendment_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert amendment["status"] == "post_s0_pre_feasibility_preregistered_execution_amendment"
    assert amendment["timing_and_scope"]["any_s2_feasibility_output_seen"] is False
    assert amendment["timing_and_scope"]["scientific_candidate_changed"] is False
    assert amendment["training"] == {
        "epochs": 50,
        "batch_size": 8,
        "drop_last": False,
        "shuffle": "torch_randperm_seed0_per_epoch",
        "optimizer": "AdamW",
        "learning_rate": 0.001,
        "weight_decay": 0.0001,
        "scheduler": "none",
        "early_stopping": False,
        "development_evaluation_during_training": False,
        "development_evaluation_count": 1,
        "development_evaluation_time": "after_epoch_50",
        "objective": "per_case_class_balanced_binary_cross_entropy",
        "optimizer_steps_expected": 1900,
    }
    assert amendment["selection"]["selected_anchors"] == 32
    assert amendment["selection"]["candidate_pool"] == 96
    assert amendment["hard_gate"]["manual_override"] is False
    assert amendment["head"]["full_S2_reuses_feasibility_head"] is False

    model_source = (ROOT / "models/AdaPoinTr.py").read_text(encoding="utf-8")
    proxy_method = function_node(model_source, "PCTransformer", "encode_rim_proxy_tokens")
    forward_method = function_node(model_source, "PCTransformer", "forward")
    proxy_text = ast.unparse(proxy_method)
    forward_text = ast.unparse(forward_method)
    for required in (
        "self.grouper",
        "self.pos_embed",
        "self.input_proj",
        "self.encoder",
        "self.encoder_adapter",
        "torch.cat",
    ):
        assert required in proxy_text
    assert "self.encode_rim_proxy_tokens(xyz)" in forward_text
    assert "self.rim_score_head(proxy_features)" in forward_text

    runner = (
        ROOT / "tools/run_mamba_v13_d3_s2_feasibility_fold.py"
    ).read_text(encoding="utf-8")
    assert "EPOCHS = 50" in runner
    assert "BATCH_SIZE = 8" in runner
    assert "SELECTED_COUNT = 32" in runner
    assert "POOL_SIZE = 96" in runner
    assert "torch.optim.AdamW" in runner
    assert "lr=1.0e-3, weight_decay=1.0e-4" in runner
    assert runner.index("for epoch in progress") < runner.index(
        "dev_dataset = build_dataset(s2_cfg, \"val\")"
    )
    assert 'train_gt_rim_key != "reference_rim_mask"' in runner
    assert "s2_cfg.dataset.val.others.GT_RIM_KEY = train_gt_rim_key" in runner
    assert "verify_hotfix(args.hotfix_dir.resolve(), lock_dir)" in runner
    assert "full_S2_reuses_feasibility_head\": False" in runner

    sequence = (
        ROOT / "scripts/run_mamba_v13_d3_s2_feasibility.sh"
    ).read_text(encoding="utf-8")
    assert "run_mamba_v13_d3_s2_feasibility_fold.sh" in sequence
    assert "freeze_mamba_v13_d3_s2_feasibility.py" in sequence
    assert "main.py" not in sequence
    assert "--split holdout" not in sequence.lower()
    assert "holdout=false" in sequence.lower()

    hotfix = json.loads(
        (
            ROOT
            / "docs/mamba_v13_d3_s2_head_only_feasibility_hotfix1_20260825.json"
        ).read_text(encoding="utf-8")
    )
    assert hotfix["status"] == "implementation_repair_no_scientific_protocol_change"
    assert hotfix["repair"]["development_gt_use"] == "offline labels and metrics only"
    assert hotfix["repair"]["inference_graph_changed"] is False
    assert hotfix["repair"]["hard_gate_changed"] is False
    assert hotfix["recovery"]["fold_A_action"].startswith("restart deterministic")

    print("[ok] post-S0/pre-feasibility amendment is explicit")
    print("[ok] frozen proxy-token path is shared with formal S2 forward")
    print("[ok] head schedule, 32/96 selection, and one-shot dev order are frozen")
    print("[ok] sequence cannot launch full S2 training or access holdout")
    print("[ok] hotfix1 enables dev GT-rim labels for offline scoring only")


if __name__ == "__main__":
    main()
