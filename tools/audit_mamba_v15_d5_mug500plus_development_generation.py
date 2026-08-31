#!/usr/bin/env python3
"""Audit frozen D5 development400 outputs without widening permissions."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
from tqdm import tqdm

from lock_mamba_v15_d5_mug500plus_development_fourfold_protocol import (
    EXPECTED_DEVELOPMENT_ASSETS_SHA256,
    EXPECTED_DEVELOPMENT_MANIFEST_SHA256,
    EXPECTED_DEVELOPMENT_RECEIPT_SHA256,
    read_lineage,
    verify_flat_manifest,
)


AUDIT_PROTOCOL_ID = "mamba-v15-d5-mug500plus-development-generation-audit-v1"
GENERATION_PROTOCOL_ID = (
    "mamba-v15-d5-mug500plus-development-generation-fourfold-v1"
)
EXPECTED_GENERATOR_SHA256 = (
    "ef0664bf17435d7aa7c5efbba076ef4dc1cc49701483bdd29f743af1e0ac27e8"
)
EXPECTED_FOURFOLD_MANIFEST_SHA256 = (
    "eade1467f7864f041c2c9e2065936f5aa8fbd84e0999d335f1d1b0b247da18fb"
)
EXPECTED_ASSIGNMENT_SHA256 = (
    "31948e5425b17ebdc25ec2d4607fc8fbd534a144d80c5a0fe0c2828346770461"
)
EXPECTED_AUDIT_PROTOCOL_SHA256 = (
    "7cb4ceb37b47191a6102468194fe793f530e8a7107b82c8b86fd9d288a64171e"
)
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


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    ).encode("utf-8")


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def parse_relative_path(raw: str, root: Path) -> Path:
    text = str(raw)
    if not text or Path(text).is_absolute() or PureWindowsPath(text).is_absolute():
        raise RuntimeError(f"Manifest path is not portable and relative: {raw}")
    normalized = text.replace("\\", os.sep).replace("/", os.sep)
    return (root / normalized).resolve()


def portable_relative(path: Path, root: Path) -> str:
    return Path(os.path.relpath(path, root)).as_posix()


def validate_npz_arrays(
    sample: Mapping[str, np.ndarray], case_id: str
) -> Tuple[int, float]:
    if set(sample) != EXPECTED_ARRAYS:
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
    return int(rim.sum()), float(scale)


def validate_geometry(geometry: Mapping[str, Any], case_id: str) -> float:
    fraction = float(geometry["removed_surface_area_fraction"])
    if not (
        0.003 <= fraction <= 0.25
        and int(geometry["removed_triangles"]) >= 256
        and int(geometry["remaining_triangles"]) >= 4096
    ):
        raise RuntimeError(f"{case_id}: geometry hard gate failed")
    return fraction


def validate_audit_protocol(protocol: Mapping[str, Any]) -> None:
    cardinality = protocol.get("expected_cardinality", {})
    effect = protocol.get("audit_effect", {})
    if (
        protocol.get("protocol_id") != AUDIT_PROTOCOL_ID
        or protocol.get("status") != "preregistered_before_generation"
        or cardinality.get("source_skulls") != 100
        or cardinality.get("derived_cases") != 400
        or cardinality.get("cases_per_source") != 4
        or cardinality.get("sources_per_fold") != 25
        or cardinality.get("cases_per_fold") != 100
        or effect.get("D5A_model_implementation_authorized_on_pass") is not False
        or effect.get("D5A_training_authorized_on_pass") is not False
        or effect.get("D5B_training_authorized_on_pass") is not False
        or effect.get("D5_candidate_selection_authorized_on_pass") is not False
        or effect.get("proposal_confirmation_access_authorized") is not False
        or effect.get("completion_holdout_access_authorized") is not False
        or effect.get("official_test_access_authorized") is not False
    ):
        raise RuntimeError("D5 generation-audit protocol semantics are invalid")


def validate_generation_receipt(
    receipt: Mapping[str, Any], manifest_sha256: str
) -> None:
    if (
        receipt.get("protocol_id") != GENERATION_PROTOCOL_ID
        or receipt.get("status")
        != "generated_training_locked_pending_D5_generation_audit"
        or receipt.get("generator_sha256") != EXPECTED_GENERATOR_SHA256
        or receipt.get("development100_files_manifest_sha256")
        != EXPECTED_DEVELOPMENT_MANIFEST_SHA256
        or receipt.get("development100_receipt_sha256")
        != EXPECTED_DEVELOPMENT_RECEIPT_SHA256
        or receipt.get("development100_assets_sha256")
        != EXPECTED_DEVELOPMENT_ASSETS_SHA256
        or receipt.get("source_skulls") != 100
        or receipt.get("derived_cases") != 400
        or receipt.get("manifest_sha256") != manifest_sha256
        or receipt.get("D5A_model_implementation_authorized") is not False
        or receipt.get("D5A_training_authorized") is not False
        or receipt.get("D5B_training_authorized") is not False
        or receipt.get("candidate_selection_authorized") is not False
        or receipt.get("proposal_confirmation_accessed") is not False
        or receipt.get("completion_holdout_accessed") is not False
        or receipt.get("official_test_accessed") is not False
    ):
        raise RuntimeError("D5 generation receipt semantics are invalid")


def read_fold_lock(directory: Path) -> Dict[str, str]:
    if sha256_file(directory / "files.sha256") != EXPECTED_FOURFOLD_MANIFEST_SHA256:
        raise RuntimeError("Frozen D5 fourfold files.sha256 drifted")
    verify_flat_manifest(directory, EXPECTED_FOURFOLD_MANIFEST_SHA256)
    assignment = directory / "source_fold_assignments.csv"
    if sha256_file(assignment) != EXPECTED_ASSIGNMENT_SHA256:
        raise RuntimeError("Frozen D5 source-fold assignments drifted")
    with assignment.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = {row["source_id"]: row["fold"] for row in rows}
    if len(rows) != 100 or len(result) != 100 or set(result.values()) != set("ABCD"):
        raise RuntimeError("Frozen D5 source-fold assignments are invalid")
    counts = collections.Counter(result.values())
    if counts != collections.Counter({fold: 25 for fold in "ABCD"}):
        raise RuntimeError("Frozen D5 source-fold counts are invalid")
    return result


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical D5 audit")
        print(f"[locked] existing D5 generation audit is byte-identical: {output_dir}")
        return
    working = output_dir.with_name(f".{output_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Audit working directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    os.replace(working, output_dir)
    print(f"[saved] immutable D5 generation audit: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation_root", type=Path, required=True)
    parser.add_argument("--development100_qc_lock_dir", type=Path, required=True)
    parser.add_argument("--source150_acquisition_lock_dir", type=Path, required=True)
    parser.add_argument("--protocol_lock_dir", type=Path, required=True)
    parser.add_argument("--audit_protocol_json", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generation_root = args.generation_root.resolve()
    output_dir = args.output_dir.resolve()
    audit_protocol_path = args.audit_protocol_json.resolve()
    audit_protocol_bytes = audit_protocol_path.read_bytes()
    if sha256_bytes(audit_protocol_bytes) != EXPECTED_AUDIT_PROTOCOL_SHA256:
        raise RuntimeError("Frozen D5 generation-audit protocol drifted")
    audit_protocol = json.loads(audit_protocol_bytes)
    validate_audit_protocol(audit_protocol)
    if output_dir == generation_root or generation_root in output_dir.parents:
        raise RuntimeError("Audit output must be outside the generated dataset")

    manifest = generation_root / "manifest.jsonl"
    receipt_path = generation_root / "generation_receipt.json"
    verify_flat_manifest(
        generation_root, sha256_file(generation_root / "files.sha256")
    )
    rows = [
        json.loads(line)
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    validate_generation_receipt(receipt, sha256_file(manifest))
    if len(rows) != 400:
        raise RuntimeError("D5 manifest must contain exactly 400 records")

    source_rows, _ = read_lineage(
        args.development100_qc_lock_dir.resolve(),
        args.source150_acquisition_lock_dir.resolve(),
    )
    source_by_id = {row["case_id"].upper(): row for row in source_rows}
    if len(source_by_id) != 100:
        raise RuntimeError("D5 development100 lock must contain exactly 100 sources")
    fold_by_source = read_fold_lock(args.protocol_lock_dir.resolve())
    if set(source_by_id) != set(fold_by_source):
        raise RuntimeError("Source100 and fourfold locks have different membership")
    source_data_root = args.development100_qc_lock_dir.resolve().parent.parent

    case_ids = set()
    derived_hashes = set()
    source_hash_cache: Dict[Path, str] = {}
    manifest_npz_paths = set()
    by_source: Dict[str, List[Mapping[str, Any]]] = collections.defaultdict(list)
    fold_case_counts: collections.Counter[str] = collections.Counter()
    rim_counts: List[int] = []
    fractions: List[float] = []
    portable_rows = []
    audit_rows = []

    for row in tqdm(rows, desc="Audit D5 development generation"):
        case_id = str(row["case_id"])
        skull_id = str(row["skull_id"])
        defect_type = str(row["defect_type"])
        source_id = skull_id.removeprefix("mug500plus__").upper()
        expected_case_id = f"mug500plus__{source_id}__{defect_type}"
        if case_id != expected_case_id or case_id in case_ids:
            raise RuntimeError(f"Invalid or duplicate case ID: {case_id}")
        case_ids.add(case_id)
        if source_id not in source_by_id or defect_type not in EXPECTED_FAMILIES:
            raise RuntimeError(f"{case_id}: source or defect family is not frozen")
        source_lock_row = source_by_id[source_id]
        expected_fold = fold_by_source[source_id]
        if row.get("d5_fold") != expected_fold:
            raise RuntimeError(f"{case_id}: D5 fold differs from frozen assignment")
        if row.get("d5_partition") != "development":
            raise RuntimeError(f"{case_id}: non-development partition in generation")
        if row.get("generator_sha256") != EXPECTED_GENERATOR_SHA256:
            raise RuntimeError(f"{case_id}: generator SHA256 differs")
        if row.get("source_dataset") != "mug500plus-v20-d5-development100":
            raise RuntimeError(f"{case_id}: source dataset differs")
        for key in (
            "source_asset_sha256",
            "source_surface_fingerprint_sha256",
            "surface_fingerprint_algorithm_sha256",
        ):
            if str(row.get(key, "")).lower() != str(source_lock_row[key]).lower():
                raise RuntimeError(f"{case_id}: {key} differs from source lock")

        point_path = parse_relative_path(row["point_path"], generation_root)
        source_path = parse_relative_path(row["source_asset_path"], generation_root)
        expected_source_path = (
            source_data_root / source_lock_row["portable_source_path"]
        ).resolve()
        if source_path != expected_source_path or not source_path.is_file():
            raise RuntimeError(f"{case_id}: source path does not resolve to frozen asset")
        if point_path.parent != (generation_root / "cases").resolve():
            raise RuntimeError(f"{case_id}: point path escapes the cases directory")
        if point_path.name != f"{case_id}.npz" or not point_path.is_file():
            raise RuntimeError(f"{case_id}: point asset is missing or misnamed")
        manifest_npz_paths.add(point_path)

        if source_path not in source_hash_cache:
            actual_source_hash = sha256_file(source_path)
            if actual_source_hash != source_lock_row["source_asset_sha256"].lower():
                raise RuntimeError(f"{case_id}: source SHA256 mismatch")
            if source_path.stat().st_size != int(source_lock_row["file_bytes"]):
                raise RuntimeError(f"{case_id}: source byte count mismatch")
            source_hash_cache[source_path] = actual_source_hash

        actual_hash = sha256_file(point_path)
        if actual_hash != str(row["derived_case_sha256"]).lower():
            raise RuntimeError(f"{case_id}: derived SHA256 mismatch")
        if actual_hash in derived_hashes:
            raise RuntimeError(f"{case_id}: duplicate derived SHA256")
        derived_hashes.add(actual_hash)

        with np.load(point_path, allow_pickle=False) as sample:
            arrays = {name: sample[name] for name in sample.files}
        rim_count, scale = validate_npz_arrays(arrays, case_id)
        normalization = row["normalization"]
        if not np.allclose(
            arrays["centroid"], normalization["centroid"], rtol=0.0, atol=1e-10
        ) or not math.isclose(
            scale, float(normalization["scale"]), rel_tol=0.0, abs_tol=1e-10
        ):
            raise RuntimeError(f"{case_id}: normalization metadata mismatch")
        if rim_count != int(row["point_audit"]["reference_rim_points"]):
            raise RuntimeError(f"{case_id}: reference-rim count mismatch")
        if rim_count < 8:
            raise RuntimeError(f"{case_id}: reference-rim hard gate failed")
        fraction = validate_geometry(row["geometry"], case_id)

        by_source[source_id].append(row)
        fold_case_counts[expected_fold] += 1
        rim_counts.append(rim_count)
        fractions.append(fraction)
        portable = dict(row)
        portable["point_path"] = portable_relative(point_path, output_dir)
        portable["source_asset_path"] = portable_relative(source_path, output_dir)
        portable_rows.append(portable)
        audit_rows.append(
            {
                "case_id": case_id,
                "source_id": source_id,
                "defect_type": defect_type,
                "fold": expected_fold,
                "derived_case_sha256": actual_hash,
                "file_bytes": point_path.stat().st_size,
                "reference_rim_points": rim_count,
                "removed_surface_area_fraction": fraction,
                "removed_triangles": int(row["geometry"]["removed_triangles"]),
                "remaining_triangles": int(row["geometry"]["remaining_triangles"]),
                "normalization_scale_mm": scale,
            }
        )

    actual_npz_paths = {
        path.resolve() for path in (generation_root / "cases").glob("*.npz")
    }
    if actual_npz_paths != manifest_npz_paths or len(actual_npz_paths) != 400:
        raise RuntimeError("Manifest and cases directory are not bijective")
    if len(case_ids) != 400 or len(derived_hashes) != 400:
        raise RuntimeError("D5 case IDs and hashes must be unique")
    if len(by_source) != 100 or len(source_hash_cache) != 100:
        raise RuntimeError("D5 audit must bind exactly 100 source skulls")
    for source_id, items in by_source.items():
        if (
            len(items) != 4
            or {str(item["defect_type"]) for item in items} != EXPECTED_FAMILIES
            or {str(item["d5_fold"]) for item in items} != {fold_by_source[source_id]}
            or len({str(item["source_asset_sha256"]) for item in items}) != 1
        ):
            raise RuntimeError(f"{source_id}: four-family source/fold binding failed")
    expected_fold_counts = collections.Counter({fold: 100 for fold in "ABCD"})
    if fold_case_counts != expected_fold_counts:
        raise RuntimeError("D5 fold case counts are invalid")

    portable_rows.sort(key=lambda row: (row["skull_id"], row["defect_type"]))
    audit_rows.sort(key=lambda row: row["case_id"])
    source_fold_rows = [
        {
            "source_id": source_id,
            "fold": fold_by_source[source_id],
            "case_count": len(by_source[source_id]),
            "source_asset_sha256": source_by_id[source_id]["source_asset_sha256"],
            "source_rehashed": True,
            "all_four_families_present": True,
        }
        for source_id in sorted(by_source)
    ]
    portable_manifest = jsonl_bytes(portable_rows)
    summary = {
        "audit_id": AUDIT_PROTOCOL_ID,
        "status": (
            "generation_integrity_passed_model_training_selection_and_sealed_still_locked"
        ),
        "audit_protocol_sha256": EXPECTED_AUDIT_PROTOCOL_SHA256,
        "implementation_hashes": {
            "audit": sha256_file(Path(__file__).resolve()),
            "tests": sha256_file(
                Path(__file__).with_name(
                    "test_mamba_v15_d5_mug500plus_development_generation_audit.py"
                )
            ),
        },
        "source_manifest_sha256": sha256_file(manifest),
        "portable_manifest_sha256": sha256_bytes(portable_manifest),
        "generator_sha256": receipt["generator_sha256"],
        "source_skulls": 100,
        "derived_cases": 400,
        "fold_case_counts": dict(sorted(fold_case_counts.items())),
        "defect_families": sorted(EXPECTED_FAMILIES),
        "reference_rim_points": {
            "minimum": min(rim_counts),
            "mean": sum(rim_counts) / len(rim_counts),
            "maximum": max(rim_counts),
        },
        "removed_surface_area_fraction": {
            "minimum": min(fractions),
            "mean": sum(fractions) / len(fractions),
            "maximum": max(fractions),
        },
        "source_assets_rehashed": True,
        "all_derived_hashes_verified": True,
        "all_derived_hashes_unique": True,
        "manifest_cases_bijective": True,
        "all_npz_contracts_verified": True,
        "all_geometry_gates_verified": True,
        "all_four_family_bindings_verified": True,
        "all_source_fold_bindings_verified": True,
        "portable_paths": True,
        "D5A_model_implementation_authorized": False,
        "D5A_training_authorized": False,
        "D5B_training_authorized": False,
        "D5_candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "completion_holdout_accessed": False,
        "official_test_accessed": False,
        "next_step": "freeze_a_separate_D5_candidate_and_training_protocol",
    }
    report = (
        "# Mamba v1.5 D5 development400 生成完整性审计\n\n"
        "> 本审计只验证冻结派生数据，不实现或训练模型，不访问两个 sealed 分区。\n\n"
        "- source skull：100。\n"
        "- derived case：400。\n"
        "- 四折病例：A/B/C/D 各 100。\n"
        "- 每来源四种缺损族：全部完整且同折。\n"
        "- 来源与派生 SHA256：全部通过且派生哈希唯一。\n"
        "- NPZ shape/dtype/finite/normalization：全部通过。\n"
        "- 几何硬门控与 reference rim：全部通过。\n"
        f"- reference rim 点数 min/mean/max：{min(rim_counts)} / "
        f"{sum(rim_counts) / len(rim_counts):.3f} / {max(rim_counts)}。\n"
        "- manifest 与 400 个 NPZ：双射成立，无额外文件。\n"
        "- 路径：全部为可解析相对路径。\n"
        "- proposal-confirmation25、completion-holdout25 与 official test：未访问。\n"
        "- 结论：生成完整性通过；D5 模型实现、训练与候选选择继续锁定。\n"
    )
    files = {
        "manifest_portable.jsonl": portable_manifest,
        "derived_case_audit.csv": csv_bytes(
            (
                "case_id",
                "source_id",
                "defect_type",
                "fold",
                "derived_case_sha256",
                "file_bytes",
                "reference_rim_points",
                "removed_surface_area_fraction",
                "removed_triangles",
                "remaining_triangles",
                "normalization_scale_mm",
            ),
            audit_rows,
        ),
        "source_fold_audit.csv": csv_bytes(
            (
                "source_id",
                "fold",
                "case_count",
                "source_asset_sha256",
                "source_rehashed",
                "all_four_families_present",
            ),
            source_fold_rows,
        ),
        "generation_audit_summary.json": canonical_json_bytes(summary),
        "generation_audit_report_zh.md": report.encode("utf-8"),
    }
    files["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    write_locked(files, output_dir)
    print("[ok] D5 development generation integrity passed: 100 sources / 400 cases")
    print(f"[saved] portable manifest: {output_dir / 'manifest_portable.jsonl'}")
    print("[locked] model=false training=false selection=false sealed=false")
    print("[next] freeze a separate D5 candidate and training protocol")


if __name__ == "__main__":
    main()
