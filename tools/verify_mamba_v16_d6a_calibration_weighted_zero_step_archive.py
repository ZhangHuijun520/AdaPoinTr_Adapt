#!/usr/bin/env python3
"""Verify a restored D6-A calibration and weighted zero-step archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


EXPECTED = {
    "calibration_manifest": "8b848b241a7218e26551e52ab3d2922bceb826ab1784b166583edcd6712874eb",
    "calibration_receipt": "b86ad7e35f91e8d03fad6d11d2b4879e294a52f59b9836ee5e73bd300449b100",
    "weights": "077920aad2e8890ea0028718d9e56f973320f20340505c551708b13dbf224290",
    "weighted_manifest": "128e4eb9ad14fdd25474fb86ffef107db8a7b46788756d29d2f35332a41f0e0a",
    "weighted_metrics": "f65ba54bcc1727db026cef54bc78d7bea997fb76e7b47c51bfbc839f6c87f41e",
    "weighted_receipt": "33e4a9450475ef00e1df57f6f96fe1d71e89aade81dda952ca9e56edc20821db",
    "weighted_report": "96b4f90a10eef3fe2311c8be72a559c391ccb6cc73453c6539c9e49cd1ea16bc",
}
FOLDS = ("A", "B", "C", "D")
OBJECTS = (
    "common_F",
    "shared_point_encoder",
    "point_calibration_branch",
    "slot_attention_and_pointer",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path, name: str = "files.sha256") -> int:
    manifest = root / name
    if not manifest.is_file():
        raise RuntimeError(f"Missing manifest: {manifest}")
    count = 0
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, relative = line.split(maxsplit=1)
        path = root / relative.lstrip("*")
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen artifact mismatch: {path}")
        count += 1
    return count


def require_hash(path: Path, expected: str) -> None:
    if not path.is_file() or sha256_file(path) != expected:
        raise RuntimeError(f"Expected frozen hash mismatch: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore_root", type=Path, required=True)
    args = parser.parse_args()
    restore = args.restore_root.resolve()
    payload_count = verify_manifest(restore, "payload_manifest.sha256")
    repo = restore / "adapointr_work/PoinTr"
    logs = repo / "logs/mamba_v16_d6_contact_support"
    completion = logs / "d6a_gradient_calibration_completion_v1"
    weighted = logs / "d6a_calibrated_weighted_zero_step_v1"
    folds = logs / "d6a_gradient_calibration_seed0_v1"

    for root in (
        logs / "d6a_slot32_mechanism_protocol_lock_v1",
        logs / "d6a_synthetic_zero_step_v1",
        logs / "d6a_gradient_ratio_calibration_protocol_v1",
        logs / "d6a_gradient_calibration_execution_authorization_v1",
        logs / "d6a_gradient_calibration_execution_preflight_v1",
        logs / "development_generation_audit_v1",
        completion,
        weighted,
    ):
        verify_manifest(root)
    for fold in FOLDS:
        verify_manifest(folds / f"fold{fold}_seed0")

    require_hash(completion / "files.sha256", EXPECTED["calibration_manifest"])
    require_hash(
        completion / "calibration_completion_receipt.json",
        EXPECTED["calibration_receipt"],
    )
    require_hash(completion / "r1_calibrated_fold_weights.json", EXPECTED["weights"])
    require_hash(weighted / "files.sha256", EXPECTED["weighted_manifest"])
    require_hash(weighted / "weighted_zero_step_metrics.csv", EXPECTED["weighted_metrics"])
    require_hash(weighted / "weighted_zero_step_receipt.json", EXPECTED["weighted_receipt"])
    require_hash(weighted / "weighted_zero_step_report_zh.md", EXPECTED["weighted_report"])

    completion_receipt = json.loads(
        (completion / "calibration_completion_receipt.json").read_text(encoding="utf-8")
    )
    if not (
        completion_receipt.get("status") == "D6A_R1_gradient_calibration_folds_A_D_complete"
        and completion_receipt.get("optimizer_steps") == 0
        and completion_receipt.get("model_updates") == 0
        and completion_receipt.get("seed0_training_authorized") is False
        and completion_receipt.get("seed1_training_authorized") is False
        and completion_receipt.get("D6B_authorized") is False
        and completion_receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Calibration completion semantics failed")

    for fold in FOLDS:
        fold_root = folds / f"fold{fold}_seed0"
        fold_receipt_path = fold_root / "calibration_fold_receipt.json"
        fold_receipt = json.loads(fold_receipt_path.read_text(encoding="utf-8"))
        lineage = completion_receipt["fold_lineage_sha256"][fold]
        if not (
            sha256_file(fold_root / "files.sha256") == lineage["manifest"]
            and sha256_file(fold_receipt_path) == lineage["receipt"]
            and fold_receipt.get("fold") == fold
            and fold_receipt.get("optimizer_steps") == 0
            and fold_receipt.get("model_updates") == 0
            and fold_receipt.get("model_state_unchanged") is True
        ):
            raise RuntimeError(f"Calibration fold lineage failed: {fold}")

    weighted_receipt = json.loads(
        (weighted / "weighted_zero_step_receipt.json").read_text(encoding="utf-8")
    )
    if not (
        weighted_receipt.get("status")
        == "D6A_R1_calibrated_weighted_real_train_zero_step_passed"
        and weighted_receipt.get("folds") == 4
        and weighted_receipt.get("total_case_slots") == 32
        and weighted_receipt.get("optimizer_constructed") is False
        and weighted_receipt.get("optimizer_steps") == 0
        and weighted_receipt.get("model_updates") == 0
        and weighted_receipt.get("model_state_unchanged") is True
        and weighted_receipt.get("random_state_restored") is True
        and weighted_receipt.get("development_dev_cases_accessed") == 0
        and weighted_receipt.get("D6A_seed0_training_authorized") is False
        and weighted_receipt.get("D6A_seed1_training_authorized") is False
        and weighted_receipt.get("D6B_authorized") is False
        and weighted_receipt.get("proposal_confirmation_accessed") is False
        and weighted_receipt.get("protected_or_sealed_data_accessed") is False
    ):
        raise RuntimeError("Weighted zero-step semantics failed")
    if weighted_receipt["lineage_sha256"]["calibration_completion_manifest"] != EXPECTED[
        "calibration_manifest"
    ]:
        raise RuntimeError("Weighted zero-step calibration lineage failed")

    with (weighted / "weighted_zero_step_metrics.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    if [row["fold"] for row in rows] != list(FOLDS):
        raise RuntimeError("Weighted zero-step fold rows drifted")
    for row in rows:
        for object_name in OBJECTS:
            total = float(row[f"{object_name}_total_norm"])
            if not math.isfinite(total) or total <= 0.0:
                raise RuntimeError(f"Invalid total gradient: {row['fold']} {object_name}")

    forbidden_suffixes = {".pth", ".pt", ".ckpt", ".npz", ".stl"}
    forbidden = [
        path
        for path in restore.rglob("*")
        if path.is_file() and path.suffix.lower() in forbidden_suffixes
    ]
    if forbidden:
        raise RuntimeError(f"Archive contains excluded model/data payload: {forbidden[0]}")

    print(f"[ok] payload manifest verified: {payload_count} files")
    print("[ok] four calibration folds and completion lineage match")
    print("[ok] calibrated weighted zero-step frozen semantics match")
    print("[excluded] checkpoints, NPZ, STL and sealed data")
    print("[locked] training=false seed1=false D6B=false selection=false sealed=false")


if __name__ == "__main__":
    main()

