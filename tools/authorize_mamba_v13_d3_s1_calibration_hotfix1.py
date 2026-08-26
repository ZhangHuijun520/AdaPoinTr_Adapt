#!/usr/bin/env python3
"""Authorize the pre-batch scalar tensor-hash repair without replacing base auth."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOTFIX = REPO_ROOT / "docs/mamba_v13_d3_s1_calibration_tensor_hash_hotfix1_20260826.json"
RUNNER = REPO_ROOT / "tools/run_mamba_v13_d3_s1_calibration_fold.py"
VERSION = "mamba-v13-d3-s1-calibration-tensor-hash-hotfix1-v1"
AUTH_VERSION = "mamba-v13-d3-s1-gradient-ratio-calibration-authorization-v1"


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


def verify_tree(root: Path) -> None:
    for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, raw_name = line.split(maxsplit=1)
        path = root / raw_name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen tree mismatch: {path}")


def write_locked(output: Path, files: dict[str, bytes]) -> None:
    if output.exists():
        actual = {path.name for path in output.iterdir() if path.is_file()}
        mismatches = [
            name for name, payload in files.items()
            if not (output / name).is_file() or (output / name).read_bytes() != payload
        ]
        if actual != set(files) or mismatches:
            raise RuntimeError(
                "Refusing to overwrite non-identical S1 calibration hotfix: "
                f"files={sorted(actual)} mismatches={mismatches}"
            )
        print(f"[locked] existing S1 calibration hotfix is byte-identical: {output}")
        return
    output.mkdir(parents=True)
    for name, payload in files.items():
        (output / name).write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_authorization_dir", type=Path, required=True)
    parser.add_argument("--failed_master_log", type=Path, required=True)
    parser.add_argument("--runs_root", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    base_dir = args.base_authorization_dir.resolve()
    failed_log = args.failed_master_log.resolve()
    runs_root = args.runs_root.resolve()
    output = args.output_dir.resolve()
    verify_tree(base_dir)
    base_path = base_dir / "s1_calibration_authorization_receipt.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    old_runner_sha = base.get("bound_code", {}).get(
        "tools/run_mamba_v13_d3_s1_calibration_fold.py"
    )
    if not (
        base.get("authorization_version") == AUTH_VERSION
        and base.get("status") == "S1_training_only_gradient_ratio_calibration_authorized"
        and isinstance(old_runner_sha, str) and len(old_runner_sha) == 64
        and base.get("S1_training_authorized") is False
        and base.get("S2_calibration_authorized") is False
        and base.get("holdout_authorized") is False
        and base.get("selection_started") is False
    ):
        raise RuntimeError("Base S1 calibration authorization is invalid")

    repaired_runner_sha = sha256_file(RUNNER)
    if old_runner_sha == repaired_runner_sha:
        raise RuntimeError("Tensor-hash hotfix is unexpectedly identical to base runner")

    if output.exists():
        verify_tree(output)
        receipt_path = output / "hotfix_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not (
            receipt.get("hotfix_version") == VERSION
            and receipt.get("status")
            == "pre_batch_scalar_tensor_hash_repair_authorized"
            and receipt.get("base_authorization", {}).get("sha256")
            == sha256_file(base_path)
            and receipt.get("base_authorized_runner_sha256") == old_runner_sha
            and receipt.get("repaired_runner", {}).get("sha256")
            == repaired_runner_sha
            and receipt.get("failed_master_log", {}).get("sha256")
            == sha256_file(failed_log)
            and receipt.get("scientific_protocol_changed") is False
            and receipt.get("S1_calibration_authorized") is True
            and receipt.get("S1_training_authorized") is False
            and receipt.get("S2_calibration_authorized") is False
            and receipt.get("S2_full_training_authorized") is False
            and receipt.get("holdout_authorized") is False
            and receipt.get("selection_started") is False
        ):
            raise RuntimeError("Existing S1 calibration hotfix semantics are invalid")
        print(f"[locked] existing S1 calibration hotfix is valid: {output}")
        return

    log_text = failed_log.read_text(encoding="utf-8", errors="replace")
    required_log_fragments = (
        "Traceback (most recent call last):",
        "run_mamba_v13_d3_s1_calibration_fold.py",
        "state_before = tensor_hash(model.state_dict().items())",
        "self.dim() cannot be 0 to view Float as Byte",
    )
    missing_fragments = [
        fragment for fragment in required_log_fragments if fragment not in log_text
    ]
    if missing_fragments:
        raise RuntimeError(
            "Master log does not prove the preregistered pre-batch failure: "
            f"missing={missing_fragments}"
        )
    if runs_root.exists() and any(runs_root.rglob("calibration_receipt.json")):
        raise RuntimeError("A fold calibration receipt already exists; hotfix is forbidden")

    hotfix = json.loads(HOTFIX.read_text(encoding="utf-8"))
    if not (
        hotfix.get("status") == "pre_batch_implementation_repair"
        and hotfix["observed_failure"]["batches_consumed"] == 0
        and hotfix["repair"]["scientific_protocol_changed"] is False
        and hotfix["permissions"]["holdout_authorized"] is False
    ):
        raise RuntimeError("Tensor-hash hotfix semantics are invalid")

    runner_text = RUNNER.read_text(encoding="utf-8")
    if not (
        "value.reshape(-1).view(torch.uint8)" in runner_text
        and runner_text.index("state_before = tensor_hash")
        < runner_text.index("iterator = iter(loader)")
    ):
        raise RuntimeError("Repaired runner does not contain the bounded pre-batch fix")

    receipt = {
        "hotfix_version": VERSION,
        "status": "pre_batch_scalar_tensor_hash_repair_authorized",
        "base_authorization": {
            "path": portable(base_path),
            "sha256": sha256_file(base_path),
        },
        "base_authorized_runner_sha256": old_runner_sha,
        "repaired_runner": {"path": portable(RUNNER), "sha256": repaired_runner_sha},
        "failed_master_log": {
            "path": portable(failed_log),
            "sha256": sha256_file(failed_log),
        },
        "hotfix_document": {"path": portable(HOTFIX), "sha256": sha256_file(HOTFIX)},
        "failure_stage": "before_data_iterator_creation",
        "calibration_batches_consumed_before_failure": 0,
        "gradients_computed_before_failure": 0,
        "fold_receipts_written_before_failure": 0,
        "scientific_protocol_changed": False,
        "S1_calibration_authorized": True,
        "S1_training_authorized": False,
        "S2_calibration_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_authorized": False,
        "selection_started": False,
    }
    files = {
        "hotfix_document.json": HOTFIX.read_bytes(),
        "hotfix_receipt.json": canonical_json(receipt),
    }
    files["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    write_locked(output, files)
    print(f"[saved] S1 calibration tensor-hash hotfix: {output}")
    print("[repaired] scalar state hashing only; zero batches were consumed")
    print("[locked] training=false S2=false holdout=false selection=false")


if __name__ == "__main__":
    main()
