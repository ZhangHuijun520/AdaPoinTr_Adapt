#!/usr/bin/env python3
"""Audit MUG500+ M2 outputs and emit an immutable portable manifest."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
from tqdm import tqdm


PROTOCOL_ID = "mug500plus-m2-synthetic-defect-v1"
EXPECTED_FAMILIES = {
    "ellipsoid_small",
    "ellipsoid_medium",
    "ellipsoid_large",
    "irregular_medium",
}
EXPECTED_ARRAYS = {
    "partial",
    "implant",
    "gt",
    "centroid",
    "scale",
    "reference_rim_mask",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_windows_relative(root: Path, raw: str) -> Path:
    normalized = str(raw).replace("\\", os.sep).replace("/", os.sep)
    path = Path(normalized)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def portable_relative(path: Path, root: Path) -> str:
    return Path(os.path.relpath(path, root)).as_posix()


def jsonl_bytes(rows: Iterable[Dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    ).encode("utf-8")


def csv_bytes(rows: List[List[Any]]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode("utf-8")


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical M2 audit")
        print(f"[locked] existing M2 audit is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] immutable M2 generation audit: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = args.manifest.resolve()
    source_root = manifest.parent
    output_dir = args.output_dir.resolve()
    if output_dir == source_root:
        raise RuntimeError("Audit output must be a dedicated child directory")
    rows = [
        json.loads(line)
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    receipt_path = source_root / "generation_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("protocol_id") != PROTOCOL_ID
        or receipt.get("status")
        != "generated_training_still_locked_pending_D3_data_audit"
        or int(receipt.get("source_skulls", 0)) != 125
        or int(receipt.get("derived_cases", 0)) != 500
        or sha256_file(manifest) != receipt.get("manifest_sha256")
    ):
        raise RuntimeError("M2 generation receipt is invalid")

    case_ids = set()
    derived_hashes = set()
    by_skull = collections.defaultdict(list)
    portable_rows = []
    audit_rows: List[List[Any]] = [[
        "case_id",
        "skull_id",
        "defect_type",
        "derived_case_sha256",
        "file_bytes",
        "reference_rim_points",
        "removed_surface_area_fraction",
        "normalization_scale_mm",
    ]]
    rim_counts = []
    for row in tqdm(rows, desc="Audit M2 generation"):
        case_id = str(row["case_id"])
        skull_id = str(row["skull_id"])
        defect_type = str(row["defect_type"])
        if case_id in case_ids:
            raise RuntimeError(f"Duplicate case ID: {case_id}")
        case_ids.add(case_id)
        by_skull[skull_id].append(row)
        point_path = resolve_windows_relative(source_root, row["point_path"])
        source_path = resolve_windows_relative(source_root, row["source_asset_path"])
        if not point_path.is_file() or not source_path.is_file():
            raise FileNotFoundError(f"{case_id}: source or point asset is missing")
        actual_hash = sha256_file(point_path)
        if actual_hash != str(row["derived_case_sha256"]).lower():
            raise RuntimeError(f"{case_id}: derived SHA256 mismatch")
        if actual_hash in derived_hashes:
            raise RuntimeError(f"{case_id}: duplicate derived SHA256")
        derived_hashes.add(actual_hash)
        with np.load(point_path, allow_pickle=False) as sample:
            if set(sample.files) != EXPECTED_ARRAYS:
                raise RuntimeError(f"{case_id}: unexpected NPZ members")
            partial = sample["partial"]
            implant = sample["implant"]
            complete = sample["gt"]
            centroid = sample["centroid"]
            scale = sample["scale"]
            rim = sample["reference_rim_mask"]
            if not (
                partial.shape == implant.shape == complete.shape == (8192, 3)
                and partial.dtype == implant.dtype == complete.dtype == np.float32
                and centroid.shape == (3,)
                and centroid.dtype == np.float64
                and scale.shape == ()
                and scale.dtype == np.float64
                and rim.shape == (8192,)
                and rim.dtype == np.bool_
            ):
                raise RuntimeError(f"{case_id}: NPZ shape or dtype contract failed")
            if not all(
                np.isfinite(array).all()
                for array in (partial, implant, complete, centroid, scale)
            ):
                raise RuntimeError(f"{case_id}: NPZ contains NaN or Inf")
            if not np.allclose(partial.mean(axis=0), 0.0, atol=2e-6):
                raise RuntimeError(f"{case_id}: partial is not centered")
            radius = float(np.linalg.norm(partial, axis=1).max())
            if not math.isclose(radius, 1.0, rel_tol=0.0, abs_tol=2e-6):
                raise RuntimeError(f"{case_id}: partial radius is not one")
            normalization = row["normalization"]
            if not np.allclose(
                centroid, normalization["centroid"], rtol=0.0, atol=1e-10
            ) or not math.isclose(
                float(scale),
                float(normalization["scale"]),
                rel_tol=0.0,
                abs_tol=1e-10,
            ):
                raise RuntimeError(f"{case_id}: normalization metadata mismatch")
            rim_count = int(rim.sum())
        if rim_count != int(row["point_audit"]["reference_rim_points"]):
            raise RuntimeError(f"{case_id}: reference-rim count mismatch")
        if rim_count < 8:
            raise RuntimeError(f"{case_id}: reference-rim hard gate failed")
        geometry = row["geometry"]
        fraction = float(geometry["removed_surface_area_fraction"])
        if not (
            0.003 <= fraction <= 0.25
            and int(geometry["removed_triangles"]) >= 256
            and int(geometry["remaining_triangles"]) >= 4096
        ):
            raise RuntimeError(f"{case_id}: geometry hard gate failed")
        portable = dict(row)
        portable["point_path"] = portable_relative(point_path, output_dir)
        portable["source_asset_path"] = portable_relative(source_path, output_dir)
        portable_rows.append(portable)
        rim_counts.append(rim_count)
        audit_rows.append([
            case_id,
            skull_id,
            defect_type,
            actual_hash,
            point_path.stat().st_size,
            rim_count,
            fraction,
            float(row["normalization"]["scale"]),
        ])

    if len(rows) != 500 or len(by_skull) != 125:
        raise RuntimeError("M2 cardinality must be exactly 125 skulls / 500 cases")
    for skull_id, items in by_skull.items():
        if (
            len(items) != 4
            or {str(item["defect_type"]) for item in items} != EXPECTED_FAMILIES
            or len({item["source_asset_sha256"] for item in items}) != 1
            or len({item["source_surface_fingerprint_sha256"] for item in items})
            != 1
        ):
            raise RuntimeError(f"{skull_id}: four-family source binding failed")

    portable_rows.sort(key=lambda item: (item["skull_id"], item["defect_type"]))
    portable_manifest = jsonl_bytes(portable_rows)
    summary = {
        "audit_id": "mug500plus-m2-generation-audit-v1",
        "status": "generation_integrity_passed_training_still_locked",
        "source_manifest_sha256": sha256_file(manifest),
        "portable_manifest_sha256": sha256_bytes(portable_manifest),
        "generator_sha256": receipt["generator_sha256"],
        "source_skulls": len(by_skull),
        "derived_cases": len(rows),
        "defect_families": sorted(EXPECTED_FAMILIES),
        "reference_rim_points": {
            "minimum": min(rim_counts),
            "mean": sum(rim_counts) / len(rim_counts),
            "maximum": max(rim_counts),
        },
        "all_derived_hashes_verified": True,
        "all_npz_contracts_verified": True,
        "all_geometry_gates_verified": True,
        "portable_paths": True,
        "protected_overlap_audit_passed": False,
        "training_unlocked": False,
        "protected_data_used": False,
    }
    report = f"""# MUG500+ M2 派生数据完整性审计\n\n- source skull：125\n- derived case：500\n- 四种缺损族：完整\n- derived SHA256：全部通过\n- NPZ shape/dtype/finite：全部通过\n- partial-only 归一化：全部通过\n- reference rim 点数：{min(rim_counts)} / {sum(rim_counts) / len(rim_counts):.3f} / {max(rim_counts)}（min/mean/max）\n- portable manifest：已生成\n- protected overlap audit：尚未通过\n- D3 training：保持锁定\n"""
    files = {
        "manifest_portable.jsonl": portable_manifest,
        "derived_case_audit.csv": csv_bytes(audit_rows),
        "generation_audit_summary.json": (
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
        "generation_audit_report_zh.md": report.encode("utf-8"),
    }
    hashes = [
        f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)
    ]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    write_locked(files, output_dir)
    print("[ok] M2 generation integrity passed: 125 skulls / 500 cases")
    print(f"[saved] portable manifest: {output_dir / 'manifest_portable.jsonl'}")
    print("[locked] protected overlap audit and D3 data lock are still pending")


if __name__ == "__main__":
    main()
