#!/usr/bin/env python3
"""Bind the preregistered S1 gradient-ratio calibration to frozen inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = REPO_ROOT / "docs" / (
    "mamba_v13_d3_s1_gradient_ratio_calibration_amendment_v1.json"
)
PROTOCOL_REPORT = REPO_ROOT / "docs" / (
    "mamba_v13_d3_s1_gradient_ratio_calibration_preregistered_protocol_zh.md"
)
VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-authorization-v1"
FOLDS = ("A", "B", "C", "D")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def verify_sidecar(path: Path) -> None:
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    if (
        len(fields) < 2
        or Path(fields[1]).name != path.name
        or sha256_file(path) != fields[0].lower()
    ):
        raise RuntimeError(f"SHA256 sidecar mismatch: {path}")


def verify_tree(root: Path) -> dict[str, str]:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise FileNotFoundError(f"Missing frozen hash manifest: {manifest}")
    verified = {}
    for line in manifest.read_text(encoding="ascii").splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) != 2:
            raise RuntimeError(f"Malformed hash line: {line!r}")
        expected, raw_name = fields
        name = raw_name.lstrip("*").replace("\\", "/")
        path = root / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen tree mismatch: {path}")
        verified[name] = expected.lower()
    return verified


def write_locked(output: Path, files: dict[str, bytes]) -> None:
    expected = set(files)
    if output.exists():
        actual = {
            path.relative_to(output).as_posix()
            for path in output.rglob("*")
            if path.is_file()
        }
        mismatches = [
            name for name, payload in files.items()
            if not (output / name).is_file() or (output / name).read_bytes() != payload
        ]
        if actual != expected or mismatches:
            raise RuntimeError(
                "Refusing to overwrite non-identical S1 authorization: "
                f"extras={sorted(actual - expected)} "
                f"missing={sorted(expected - actual)} mismatches={mismatches}"
            )
        print(f"[locked] existing S1 authorization is byte-identical: {output}")
        return
    for name, payload in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent_protocol_lock", type=Path, required=True)
    parser.add_argument("--s0_completion", type=Path, required=True)
    parser.add_argument("--s2_feasibility_lock_dir", type=Path, required=True)
    parser.add_argument("--s2_negative_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    parent = args.parent_protocol_lock.resolve()
    s0_path = args.s0_completion.resolve()
    s2_lock_dir = args.s2_feasibility_lock_dir.resolve()
    s2_dir = args.s2_negative_dir.resolve()
    output = args.output_dir.resolve()

    parent_files = verify_tree(parent)
    verify_tree(s2_lock_dir)
    s2_files = verify_tree(s2_dir)
    verify_sidecar(s0_path)
    s0 = json.loads(s0_path.read_text(encoding="utf-8"))
    if not (
        s0.get("status") == "S0_seed0_frozen_ready_for_S2_feasibility"
        and s0.get("candidate") == "S0"
        and s0.get("seed") == 0
        and s0.get("development_cases") == 400
        and s0.get("S1_authorized") is False
        and s0.get("holdout_authorized") is False
        and s0.get("selection_started") is False
    ):
        raise RuntimeError("Frozen S0 completion semantics are invalid")

    s2_receipt_path = s2_dir / "negative_result_receipt.json"
    if s2_files.get(s2_receipt_path.name) != sha256_file(s2_receipt_path):
        raise RuntimeError("S2 negative receipt is not bound by its frozen tree")
    s2 = json.loads(s2_receipt_path.read_text(encoding="utf-8"))
    if not (
        s2.get("status")
        == "frozen_negative_high_hit_rate_failed_all_case_safety_gate"
        and s2.get("case_hits") == 392
        and s2.get("development_cases") == 400
        and s2.get("S2_weight_calibration_authorized") is False
        and s2.get("S2_full_training_authorized") is False
        and s2.get("S1_weight_calibration_may_be_separately_authorized") is True
        and s2.get("holdout_accessed") is False
        and s2.get("selection_started") is False
    ):
        raise RuntimeError("S2 negative receipt does not permit separate S1 calibration")

    s2_lock_receipt_path = s2_lock_dir / "feasibility_lock_receipt.json"
    s2_lock = json.loads(s2_lock_receipt_path.read_text(encoding="utf-8"))
    if not (
        s2.get("base_lock_receipt", {}).get("sha256")
        == sha256_file(s2_lock_receipt_path)
        and s2_lock.get("status") == "S2_head_only_feasibility_authorized"
        and s2_lock.get("S1_authorized") is False
        and s2_lock.get("S2_full_training_authorized") is False
        and s2_lock.get("holdout_authorized") is False
        and s2_lock.get("selection_started") is False
    ):
        raise RuntimeError("S2 feasibility base lock is not the lock frozen by the negative receipt")

    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    if not (
        amendment.get("status") == "preregistered_before_s1_calibration"
        and amendment["data_boundary"]["allowed_partition"]
        == "development fold training subset only"
        and amendment["gradient_measurement"]["target_ratio"] == 0.075
        and amendment["post_completion_permissions"]["holdout_authorized"] is False
    ):
        raise RuntimeError("S1 calibration amendment semantics are invalid")

    parent_receipt = json.loads(
        (parent / "protocol_lock_receipt.json").read_text(encoding="utf-8")
    )
    if not (
        parent_receipt.get("status") == "candidate_templates_locked"
        and parent_receipt.get("training_authorized") is False
        and parent_receipt.get("holdout_authorized") is False
        and parent_receipt.get("model_selection_started") is False
    ):
        raise RuntimeError("Parent Round-A lock semantics are invalid")

    accepted_lineage = {}
    later_bound = s2_lock.get("bound_code", {})
    allowed_later_takeover = {"models/AdaPoinTr.py", "utils/mamba_d3_contact.py"}
    for relative, expected in parent_receipt["implementation_sha256"].items():
        path = REPO_ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Missing parent-bound implementation: {relative}")
        current = sha256_file(path)
        if current == expected:
            accepted_lineage[relative] = {
                "source": "parent_round_a_protocol_lock",
                "sha256": current,
            }
        elif relative in allowed_later_takeover and later_bound.get(relative) == current:
            accepted_lineage[relative] = {
                "source": "later_s2_feasibility_base_lock_referenced_by_negative_receipt",
                "sha256": current,
                "superseded_parent_sha256": expected,
            }
        else:
            raise RuntimeError(f"Unfrozen implementation drift: {relative}")

    templates = {}
    for fold in FOLDS:
        name = f"configs/MambaV13D3_S1_fold{fold}_seed0.template.yaml"
        template = parent / name
        expected = parent_files.get(name)
        if expected is None or sha256_file(template) != expected:
            raise RuntimeError(f"Frozen S1 template mismatch: fold {fold}")
        config = yaml.safe_load(template.read_text(encoding="utf-8"))
        execution = config["d3_execution"]
        dense = config["model"]["dense_contact_objective"]
        train = config["dataset"]["train"]["others"]
        serialized = template.read_text(encoding="utf-8")
        if not (
            execution.get("candidate") == "S1"
            and execution.get("fold") == fold
            and execution.get("training_authorized") is False
            and execution.get("holdout_authorized") is False
            and dense == {
                "enabled": True,
                "weight": 1.0,
                "threshold_mm": 2.0,
                "temperature_mm": 0.25,
                "tail_fraction": 0.1,
            }
            and train.get("subset") == "train"
            and train.get("manifest_split") == "development"
            and train.get("GT_RIM_KEY") == "reference_rim_mask"
            and "locked_holdout_case_ids" not in serialized
        ):
            raise RuntimeError(f"Frozen S1 template contract invalid: fold {fold}")
        case_ids = REPO_ROOT / train["include_case_ids_file"]
        ids = [line.strip() for line in case_ids.read_text().splitlines() if line.strip()]
        if len(ids) != 300 or len(set(ids)) != 300:
            raise RuntimeError(f"Fold {fold} train case set is not exactly 300 unique cases")
        templates[fold] = {
            "template": {"path": str(template), "sha256": expected},
            "train_case_ids": {
                "path": portable(case_ids),
                "sha256": sha256_file(case_ids),
                "count": 300,
            },
        }

    bound_code = {}
    for relative in (
        "models/AdaPoinTr.py",
        "datasets/SkullBreakDataset.py",
        "utils/mamba_d3_contact.py",
        "tools/authorize_mamba_v13_d3_s1_calibration.py",
        "tools/run_mamba_v13_d3_s1_calibration_fold.py",
        "tools/freeze_mamba_v13_d3_s1_calibration.py",
        "tools/test_mamba_v13_d3_s1_calibration_contract.py",
        "scripts/prepare_mamba_v13_d3_s1_calibration.sh",
        "scripts/run_mamba_v13_d3_s1_calibration_fold.sh",
        "scripts/run_mamba_v13_d3_s1_calibration.sh",
        "scripts/launch_mamba_v13_d3_s1_calibration_tmux.sh",
    ):
        path = REPO_ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Missing S1 calibration implementation: {path}")
        bound_code[relative] = sha256_file(path)

    receipt = {
        "authorization_version": VERSION,
        "status": "S1_training_only_gradient_ratio_calibration_authorized",
        "candidate": "S1",
        "seed": 0,
        "folds": templates,
        "amendment": {"path": portable(AMENDMENT), "sha256": sha256_file(AMENDMENT)},
        "preregistered_report": {
            "path": portable(PROTOCOL_REPORT),
            "sha256": sha256_file(PROTOCOL_REPORT),
        },
        "parent_protocol_lock": {
            "path": str(parent),
            "files_sha256": sha256_file(parent / "files.sha256"),
        },
        "s0_completion": {"path": portable(s0_path), "sha256": sha256_file(s0_path)},
        "s2_negative_receipt": {
            "path": portable(s2_receipt_path),
            "sha256": sha256_file(s2_receipt_path),
        },
        "s2_feasibility_base_lock": {
            "path": portable(s2_lock_receipt_path),
            "sha256": sha256_file(s2_lock_receipt_path),
        },
        "accepted_implementation_lineage": accepted_lineage,
        "bound_code": bound_code,
        "batches_per_fold": 8,
        "batch_size": 8,
        "target_gradient_ratio": 0.075,
        "optimizer_steps_authorized": 0,
        "S1_calibration_authorized": True,
        "S1_training_authorized": False,
        "S2_calibration_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_authorized": False,
        "selection_started": False,
    }
    files = {
        "calibration_amendment_v1.json": AMENDMENT.read_bytes(),
        "s1_calibration_authorization_receipt.json": canonical_json(receipt),
    }
    files["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    write_locked(output, files)
    print(f"[saved] S1 calibration authorization: {output}")
    print("[authorized] S1 seed-0 training-fold gradient measurement only")
    print("[locked] optimizer_steps=0 dev=false holdout=false S2=false selection=false")


if __name__ == "__main__":
    main()
