#!/usr/bin/env python
"""CPU/static contract tests for SCQR v1.1 L4 training and BNCal guards."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.cranial_scqr_l4_audit import ScqrL4Audit, validate_l4_contract


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Dataset:
    def __len__(self):
        return 315


class Loader:
    dataset = Dataset()

    def __len__(self):
        return 39


def fixture(directory: Path, *, auto_rerun=False):
    train_ids = directory / "train_ids.txt"
    train_ids.write_text("placeholder\n", encoding="utf-8")
    calibration = directory / "calibration.json"
    write_json(
        calibration,
        {
            "status": "PASS",
            "execution_counts": {"optimizer_steps": 0},
            "training_authorized_by_this_receipt": False,
            "folds": {"A": {"lambda_scf": 0.8852418767331852}},
        },
    )
    protocol = directory / "protocol.json"
    write_json(
        protocol,
        {
            "protocol_id": "cranial-scqr-v1.1-L4-roundA-training-v1",
            "status": "FROZEN_PENDING_EXECUTION",
        },
    )
    authorization = directory / "authorization.json"
    write_json(
        authorization,
        {
            "status": "AUTHORIZED",
            "protocol_id": "cranial-scqr-v1.1-L4-roundA-training-v1",
            "authorized_run_keys": ["B0_foldA_seed0"],
            "automatic_rerun_authorized": auto_rerun,
        },
    )
    runtime = directory / "runtime.yaml"
    runtime.write_text("test fixture\n", encoding="utf-8")
    execution = NS(
        stage="L4_roundA_training",
        training_authorized=True,
        optimizer_steps_authorized=3939,
        loader_batches_expected=39,
        epoch_labels_start=0,
        epoch_labels_end=100,
        epoch_traversals_expected=101,
        seed=0,
        gpu_count=1,
        resume_authorized=False,
        checkpoint_initial_state="scratch",
        development_payload_access_authorized=False,
        bncal_authorized=True,
        seed1_authorized=False,
        checkpoint_policy="final_only",
        authorization_receipt=str(authorization),
        authorization_receipt_sha256=sha(authorization),
        calibration_receipt=str(calibration),
        calibration_receipt_sha256=sha(calibration),
        round_a_protocol=str(protocol),
        round_a_protocol_sha256=sha(protocol),
        train_case_ids=str(train_ids),
        train_case_ids_sha256=sha(train_ids),
    )
    config = NS(
        total_bs=8,
        step_per_update=1,
        max_epoch=100,
        grad_norm_clip=10,
        save_best_checkpoint=False,
        save_final_epoch_checkpoints=False,
        optimizer=NS(type="AdamW", kwargs=NS(lr=1.0e-4, weight_decay=5.0e-4)),
        model=NS(cranial_scqr=NS(auxiliary_loss_weight=None)),
        dataset=NS(train=NS(others=NS(include_case_ids_file=str(train_ids)))),
        development_protocol=NS(
            candidate="B0",
            fold="A",
            seed=0,
            confirmation_allowed=False,
            old_monitor_allowed=False,
            official_test_allowed=False,
            mug_payload_allowed=False,
        ),
        cranial_scqr_execution=execution,
    )
    args = NS(
        seed=0,
        resume=False,
        start_ckpts=None,
        config=str(runtime),
        experiment_path=str(directory / "experiment"),
    )
    Path(args.experiment_path).mkdir()
    return args, config


def expect_failure(function, fragment: str):
    try:
        function()
    except RuntimeError as error:
        assert fragment in str(error), (fragment, str(error))
    else:
        raise AssertionError(f"Expected RuntimeError containing {fragment!r}")


def main():
    with tempfile.TemporaryDirectory(prefix="scqr_l4_contract_") as raw:
        directory = Path(raw)
        args, config = fixture(directory)
        assert validate_l4_contract(args, config, Loader()) is config.cranial_scqr_execution

        drifted = copy.deepcopy(config)
        drifted.cranial_scqr_execution.optimizer_steps_authorized = 3940
        expect_failure(
            lambda: validate_l4_contract(args, drifted, Loader()),
            "optimizer_steps_authorized",
        )

        bad_dir = directory / "bad_auth"
        bad_dir.mkdir()
        bad_args, bad_config = fixture(bad_dir, auto_rerun=True)
        expect_failure(
            lambda: validate_l4_contract(bad_args, bad_config, Loader()),
            "forbid automatic reruns",
        )

        audit = ScqrL4Audit(args, config, Loader())
        audit.steps = 3939
        expect_failure(audit.authorize_next_step, "authorization exhausted")
        audit.completed_epochs = 101
        checkpoint = directory / "experiment" / "ckpt-last.pth"
        checkpoint.write_bytes(b"fixture checkpoint")
        audit.finish(checkpoint)
        state = json.loads((directory / "experiment" / "l4_execution_state.json").read_text())
        assert state["status"] == "training_complete_pending_bncal"
        assert state["optimizer_steps"] == 3939

    runner = (ROOT / "tools/runner.py").read_text(encoding="utf-8")
    step_block = runner[runner.index("l4_audit.authorize_next_step()") :]
    assert step_block.index("optimizer.step()") < step_block.index(
        "l4_audit.record_completed_step()"
    )
    assert "test_dataloader is not None and epoch % args.val_freq == 0" in runner
    assert "save_final_only = l4_audit.enabled" in runner

    bncal = (ROOT / "tools/run_cranial_scqr_v11_l4_bncal.py").read_text(
        encoding="utf-8"
    )
    assert 'payload["partial"]' in bncal
    assert 'payload["implant"]' not in bncal and 'payload["gt"]' not in bncal
    assert "drop_last=False" in bncal
    assert '"optimizer_constructions": 0' in bncal
    print("[ok] L4 binding, pre-step cap, final-only checkpoint, dev lock")
    print("[ok] BNCal partial-only, full 315/40 contract, zero optimizer")


if __name__ == "__main__":
    main()
