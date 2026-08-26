#!/usr/bin/env python3
"""Authorize the val-side GT-rim scoring repair without replacing the base lock."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "mamba-v13-d3-s2-head-feasibility-hotfix1-v1"
OLD_RUNNER_SHA256 = "4ee2d838bc890c94d89f9723d341d73ab6e245208fa6389c5489e6fb7c12a871"
REPAIR = (
    REPO_ROOT
    / "docs/mamba_v13_d3_s2_head_only_feasibility_hotfix1_20260825.json"
)
RUNNER = REPO_ROOT / "tools/run_mamba_v13_d3_s2_feasibility_fold.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_tree(root: Path) -> None:
    for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / name.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Hash-tree mismatch: {path}")


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing non-identical hotfix artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_lock_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    base = args.base_lock_dir.resolve()
    output = args.output_dir.resolve()
    verify_tree(base)
    base_receipt_path = base / "feasibility_lock_receipt.json"
    base_receipt = json.loads(base_receipt_path.read_text(encoding="utf-8"))
    if not (
        base_receipt.get("status") == "S2_head_only_feasibility_authorized"
        and base_receipt.get("S2_full_training_authorized") is False
        and base_receipt.get("holdout_authorized") is False
        and base_receipt.get("selection_started") is False
    ):
        raise RuntimeError("Base feasibility lock semantics are invalid")
    bound_runner = base_receipt.get("bound_code", {}).get(
        "tools/run_mamba_v13_d3_s2_feasibility_fold.py"
    )
    repaired_runner = sha256_file(RUNNER)
    if bound_runner not in {OLD_RUNNER_SHA256, repaired_runner}:
        raise RuntimeError(
            f"Base lock binds an unrecognized runner SHA256: {bound_runner}"
        )
    repair = json.loads(REPAIR.read_text(encoding="utf-8"))
    if not (
        repair.get("status") == "implementation_repair_no_scientific_protocol_change"
        and repair.get("old_runner_sha256") == OLD_RUNNER_SHA256
        and repair.get("repair", {}).get("inference_graph_changed") is False
        and repair.get("repair", {}).get("hard_gate_changed") is False
    ):
        raise RuntimeError("Hotfix declaration semantics are invalid")

    bound_code = {}
    for relative in (
        "tools/authorize_mamba_v13_d3_s2_feasibility_hotfix1.py",
        "tools/run_mamba_v13_d3_s2_feasibility_fold.py",
        "tools/test_mamba_v13_d3_s2_feasibility_contract.py",
        "scripts/prepare_mamba_v13_d3_s2_feasibility.sh",
        "scripts/run_mamba_v13_d3_s2_feasibility_fold.sh",
    ):
        path = REPO_ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        bound_code[relative] = sha256_file(path)
    receipt = {
        "hotfix_version": VERSION,
        "status": "development_gt_rim_scoring_repair_authorized",
        "base_lock_receipt_sha256": sha256_file(base_receipt_path),
        "base_bound_runner_sha256": bound_runner,
        "old_runner_sha256": OLD_RUNNER_SHA256,
        "repaired_runner_sha256": repaired_runner,
        "repair_declaration_sha256": sha256_file(REPAIR),
        "bound_code": bound_code,
        "scientific_protocol_changed": False,
        "fold_A_restart_from_initialization": True,
        "failed_run_development_metrics_produced": False,
        "S1_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_authorized": False,
        "holdout_accessed": False,
        "selection_started": False,
    }
    files = {
        "hotfix_declaration.json": REPAIR.read_bytes(),
        "hotfix_receipt.json": canonical_json(receipt),
    }
    files["files.sha256"] = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    if output.exists():
        extras = {path.name for path in output.iterdir()} - set(files)
        if extras:
            raise RuntimeError(f"Refusing hotfix directory extras: {sorted(extras)}")
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in files.items():
        write_identical_or_new(output / name, payload)
    verify_tree(output)
    print(f"[saved] S2 feasibility hotfix1 receipt: {output}")
    print(f"[bind] base_runner={bound_runner} repaired_runner={repaired_runner}")
    print("[repair] val GT-rim enabled for offline one-shot scoring only")
    print("[locked] scientific protocol unchanged; S2_full=false holdout=false")


if __name__ == "__main__":
    main()
