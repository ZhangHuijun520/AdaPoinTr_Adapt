#!/usr/bin/env python3
"""Bind the S2 head-only feasibility amendment to frozen S0 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FOLDS = ("A", "B", "C", "D")
VERSION = "mamba-v13-d3-s2-head-feasibility-lock-v1"
AMENDMENT = (
    REPO_ROOT
    / "docs/mamba_v13_d3_s2_head_only_feasibility_execution_amendment_v1.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def resolve(path: str | Path) -> Path:
    result = Path(path)
    if not result.is_absolute():
        result = REPO_ROOT / result
    return result.resolve()


def portable(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def verify_sidecar(path: Path) -> None:
    sidecar = Path(str(path) + ".sha256")
    if not sidecar.is_file():
        raise FileNotFoundError(f"Missing SHA256 sidecar: {sidecar}")
    fields = sidecar.read_text(encoding="ascii").split()
    if len(fields) < 2 or Path(fields[1]).name != path.name:
        raise RuntimeError(f"Invalid SHA256 sidecar: {sidecar}")
    if sha256_file(path) != fields[0].lower():
        raise RuntimeError(f"SHA256 mismatch: {path}")


def verify_tree(root: Path) -> dict[str, str]:
    manifest = root / "files.sha256"
    if not manifest.is_file():
        raise FileNotFoundError(f"Parent protocol lock omits files.sha256: {root}")
    verified = {}
    for line in manifest.read_text(encoding="ascii").splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) != 2:
            raise RuntimeError(f"Malformed parent hash line: {line!r}")
        expected, raw_name = fields
        name = raw_name.lstrip("*").replace("\\", "/")
        path = root / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Parent protocol artifact mismatch: {path}")
        verified[name] = expected.lower()
    return verified


def write_identical_or_new(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite non-identical lock file: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s0_completion", type=Path, required=True)
    parser.add_argument("--parent_protocol_lock", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()

    s0_completion = args.s0_completion.resolve()
    parent_lock = args.parent_protocol_lock.resolve()
    output = args.output_dir.resolve()
    verify_sidecar(s0_completion)
    parent_files = verify_tree(parent_lock)
    completion = json.loads(s0_completion.read_text(encoding="utf-8"))
    if not (
        completion.get("status") == "S0_seed0_frozen_ready_for_S2_feasibility"
        and completion.get("candidate") == "S0"
        and completion.get("seed") == 0
        and completion.get("folds") == list(FOLDS)
        and completion.get("development_cases") == 400
        and completion.get("S2_head_only_feasibility_authorized_next") is True
        and completion.get("S2_full_training_authorized") is False
        and completion.get("holdout_authorized") is False
        and completion.get("selection_started") is False
    ):
        raise RuntimeError("S0 completion receipt does not authorize feasibility")

    s2_templates = {
        name: digest
        for name, digest in parent_files.items()
        if "S2" in Path(name).name and Path(name).suffix in {".yaml", ".yml"}
    }
    if len(s2_templates) != 4:
        raise RuntimeError(
            f"Expected four frozen S2 templates, found {sorted(s2_templates)}"
        )

    folds = {}
    for fold in FOLDS:
        run_item = completion["run_records"][fold]
        run_path = resolve(run_item["path"])
        verify_sidecar(run_path)
        if sha256_file(run_path) != run_item["sha256"]:
            raise RuntimeError(f"S0 fold {fold} run-record hash mismatch")
        run = json.loads(run_path.read_text(encoding="utf-8"))
        if not (
            run.get("candidate") == "S0"
            and run.get("fold") == fold
            and run.get("seed") == 0
            and run.get("status") == "frozen_complete_development_fold"
        ):
            raise RuntimeError(f"Invalid S0 fold {fold} run record")
        checkpoint = resolve(run["artifacts"]["checkpoint"]["path"])
        config = resolve(run["artifacts"]["config"]["path"])
        for label, path, expected in (
            ("checkpoint", checkpoint, run["artifacts"]["checkpoint"]["sha256"]),
            ("config", config, run["artifacts"]["config"]["sha256"]),
        ):
            if not path.is_file() or sha256_file(path) != expected:
                raise RuntimeError(f"S0 fold {fold} {label} mismatch: {path}")
        template_matches = [
            name for name in s2_templates if f"fold{fold}" in Path(name).stem
        ]
        if len(template_matches) != 1:
            raise RuntimeError(f"Cannot identify S2 template for fold {fold}")
        template_name = template_matches[0]
        folds[fold] = {
            "s0_run_record": {
                "path": portable(run_path),
                "sha256": sha256_file(run_path),
            },
            "s0_config": {"path": portable(config), "sha256": sha256_file(config)},
            "s0_checkpoint": {
                "path": portable(checkpoint),
                "sha256": sha256_file(checkpoint),
            },
            "s2_template": {
                "path": str(parent_lock / template_name),
                "sha256": s2_templates[template_name],
            },
        }

    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    if amendment.get("status") != "post_s0_pre_feasibility_preregistered_execution_amendment":
        raise RuntimeError("Feasibility amendment status is invalid")

    bound_code = {}
    for relative in (
        "models/AdaPoinTr.py",
        "utils/mamba_d3_contact.py",
        "tools/lock_mamba_v13_d3_s2_feasibility_protocol.py",
        "tools/run_mamba_v13_d3_s2_feasibility_fold.py",
        "tools/freeze_mamba_v13_d3_s2_feasibility.py",
        "tools/test_mamba_v13_d3_s2_feasibility_contract.py",
        "scripts/prepare_mamba_v13_d3_s2_feasibility.sh",
        "scripts/run_mamba_v13_d3_s2_feasibility_fold.sh",
        "scripts/run_mamba_v13_d3_s2_feasibility.sh",
        "scripts/launch_mamba_v13_d3_s2_feasibility_tmux.sh",
    ):
        path = REPO_ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Missing feasibility implementation: {path}")
        bound_code[relative] = sha256_file(path)

    receipt = {
        "lock_version": VERSION,
        "status": "S2_head_only_feasibility_authorized",
        "seed": 0,
        "folds": folds,
        "amendment": {
            "path": AMENDMENT.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_file(AMENDMENT),
        },
        "s0_completion": {
            "path": portable(s0_completion),
            "sha256": sha256_file(s0_completion),
        },
        "parent_protocol_lock": {
            "path": str(parent_lock),
            "files_sha256": sha256_file(parent_lock / "files.sha256"),
        },
        "bound_code": bound_code,
        "S1_authorized": False,
        "S2_full_training_authorized": False,
        "holdout_authorized": False,
        "holdout_accessed": False,
        "selection_started": False,
    }
    receipt_bytes = canonical_json(receipt)
    files = {
        "execution_amendment.json": AMENDMENT.read_bytes(),
        "feasibility_lock_receipt.json": receipt_bytes,
    }
    manifest_lines = []
    for name, payload in sorted(files.items()):
        manifest_lines.append(f"{hashlib.sha256(payload).hexdigest()}  {name}\n")
    files["files.sha256"] = "".join(manifest_lines).encode("ascii")

    if output.exists():
        extras = {path.name for path in output.iterdir()} - set(files)
        if extras:
            raise RuntimeError(f"Refusing existing feasibility lock extras: {sorted(extras)}")
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in files.items():
        write_identical_or_new(output / name, payload)

    for name, expected in (
        line.split()[:2] for line in (output / "files.sha256").read_text().splitlines()
    ):
        if sha256_file(output / expected) != name:
            raise RuntimeError("Generated feasibility lock verification failed")
    print(f"[saved] S2 head-only feasibility lock: {output}")
    print("[authorized] frozen-S0 head-only folds A-D, seed=0")
    print("[locked] S1=false S2_full=false holdout=false selection_started=false")


if __name__ == "__main__":
    main()
