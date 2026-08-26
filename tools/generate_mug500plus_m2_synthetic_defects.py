#!/usr/bin/env python3
"""Generate the preregistered MUG500+ M2 synthetic implant point pairs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import struct
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from scipy.spatial import cKDTree
from tqdm import tqdm


DEFAULT_PROTOCOL = Path(__file__).resolve().parents[1] / "docs" / (
    "mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json"
)
LOCK_FIELDS = {
    "case_id",
    "source_path",
    "source_asset_sha256",
    "source_surface_fingerprint_sha256",
    "surface_fingerprint_algorithm_sha256",
    "file_bytes",
    "triangle_count",
    "qc_pass",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generator_bundle_sha256(protocol_path: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((Path(__file__).resolve(), protocol_path.resolve()), key=str):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def stable_seed(protocol: Dict[str, Any], *parts: object) -> int:
    fields = [
        protocol["protocol_id"],
        str(protocol["determinism"]["master_seed"]),
        *(str(part) for part in parts),
    ]
    digest = hashlib.sha256("|".join(fields).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def binary_triangle_count(path: Path) -> int | None:
    size = path.stat().st_size
    if size < 84:
        return None
    with path.open("rb") as handle:
        handle.seek(80)
        count = struct.unpack("<I", handle.read(4))[0]
    return count if 84 + 50 * count == size else None


def read_stl_triangles(path: Path) -> np.ndarray:
    count = binary_triangle_count(path)
    if count is not None:
        dtype = np.dtype(
            [("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attr", "<u2")]
        )
        records = np.fromfile(path, dtype=dtype, count=count, offset=84)
        triangles = np.asarray(records["vertices"], dtype=np.float64)
    else:
        vertices: List[List[float]] = []
        with path.open("r", encoding="ascii", errors="strict") as handle:
            for line in handle:
                fields = line.strip().split()
                if len(fields) == 4 and fields[0].lower() == "vertex":
                    vertices.append([float(value) for value in fields[1:]])
        if len(vertices) % 3:
            raise RuntimeError("ASCII STL vertex count is not divisible by three")
        triangles = np.asarray(vertices, dtype=np.float64).reshape(-1, 3, 3)
    if triangles.size == 0 or not np.isfinite(triangles).all():
        raise RuntimeError(f"Invalid STL geometry: {path}")
    return triangles


def triangle_areas(triangles: np.ndarray) -> np.ndarray:
    cross = np.cross(
        triangles[:, 1] - triangles[:, 0],
        triangles[:, 2] - triangles[:, 0],
    )
    areas = np.linalg.norm(cross, axis=1) * 0.5
    if not np.isfinite(areas).all() or float(areas.sum()) <= 0:
        raise RuntimeError("Mesh has invalid triangle areas")
    return areas


def sample_surface_points(
    triangles: np.ndarray,
    areas: np.ndarray,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    positive = areas > 0
    triangles = triangles[positive]
    areas = areas[positive]
    cumulative = np.cumsum(areas, dtype=np.float64)
    draws = rng.random(count) * cumulative[-1]
    indices = np.searchsorted(cumulative, draws, side="right")
    chosen = triangles[indices]
    uv = rng.random((count, 2))
    root_u = np.sqrt(uv[:, 0])
    weights = np.column_stack(
        (1.0 - root_u, root_u * (1.0 - uv[:, 1]), root_u * uv[:, 1])
    )
    return np.einsum("ni,nij->nj", weights, chosen, optimize=True)


def fibonacci_directions(count: int) -> np.ndarray:
    index = np.arange(count, dtype=np.float64)
    z = 1.0 - 2.0 * (index + 0.5) / count
    radius = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    angle = index * (math.pi * (3.0 - math.sqrt(5.0)))
    return np.column_stack((radius * np.cos(angle), radius * np.sin(angle), z))


def local_frame(normal: np.ndarray, angle: float) -> np.ndarray:
    normal = np.asarray(normal, dtype=np.float64)
    normal /= np.linalg.norm(normal)
    axes = np.eye(3, dtype=np.float64)
    reference = axes[int(np.argmin(np.abs(axes @ normal)))]
    tangent_u = np.cross(normal, reference)
    tangent_u /= np.linalg.norm(tangent_u)
    tangent_v = np.cross(normal, tangent_u)
    rotated_u = math.cos(angle) * tangent_u + math.sin(angle) * tangent_v
    rotated_v = -math.sin(angle) * tangent_u + math.cos(angle) * tangent_v
    return np.column_stack((rotated_u, rotated_v, normal))


def ellipsoid_membership(
    points: np.ndarray,
    center: np.ndarray,
    frame: np.ndarray,
    radii: np.ndarray,
) -> np.ndarray:
    local = (points - center) @ frame
    return np.sum(np.square(local / radii), axis=1) <= 1.0


def defect_membership(
    points: np.ndarray,
    center: np.ndarray,
    frame: np.ndarray,
    radii: np.ndarray,
    family: Dict[str, Any],
) -> np.ndarray:
    inside = ellipsoid_membership(points, center, frame, radii)
    for lobe in family.get("irregular_lobes", []):
        lobe_center = (
            center
            + frame[:, 0] * radii[0] * float(lobe["offset_u"])
            + frame[:, 1] * radii[1] * float(lobe["offset_v"])
        )
        lobe_radii = radii * float(lobe["radius_scale"])
        inside |= ellipsoid_membership(points, lobe_center, frame, lobe_radii)
    return inside


def choose_defect_geometry(
    triangles: np.ndarray,
    areas: np.ndarray,
    skull_id: str,
    defect_type: str,
    family_index: int,
    protocol: Dict[str, Any],
) -> Tuple[np.ndarray, Dict[str, Any]]:
    centroids = triangles.mean(axis=1)
    bbox_min = triangles.reshape(-1, 3).min(axis=0)
    bbox_max = triangles.reshape(-1, 3).max(axis=0)
    scale = float(np.max(bbox_max - bbox_min))
    family = protocol["defect_families"][defect_type]
    radii = scale * np.asarray(
        [
            family["tangent_radius_u_scale"],
            family["tangent_radius_v_scale"],
            family["normal_radius_scale"],
        ],
        dtype=np.float64,
    )
    location = protocol["location"]
    gates = protocol["geometric_hard_gates"]
    directions = fibonacci_directions(int(location["candidate_directions"]))
    base_slot = stable_seed(protocol, skull_id, "location") % len(directions)
    rotation_rng = np.random.default_rng(
        stable_seed(protocol, skull_id, defect_type, "rotation")
    )
    rotation = float(rotation_rng.uniform(0.0, math.pi))
    total_area = float(areas.sum())

    for attempt in range(int(location["maximum_geometry_attempts"])):
        slot = (
            base_slot
            + family_index * int(location["family_stride"])
            + attempt * int(location["retry_stride"])
        ) % len(directions)
        normal = directions[slot]
        anchor = centroids[int(np.argmax(centroids @ normal))]
        frame = local_frame(normal, rotation)
        center = anchor - (
            normal
            * radii[2]
            * float(family["inward_center_offset_fraction"])
        )
        removed = defect_membership(centroids, center, frame, radii, family)
        removed_count = int(removed.sum())
        remaining_count = int((~removed).sum())
        fraction = float(areas[removed].sum() / total_area)
        if (
            int(gates["minimum_removed_triangles"]) <= removed_count
            and int(gates["minimum_remaining_triangles"]) <= remaining_count
            and float(gates["removed_surface_area_fraction_min"])
            <= fraction
            <= float(gates["removed_surface_area_fraction_max"])
        ):
            return removed, {
                "geometry_attempt": attempt,
                "direction_slot": int(slot),
                "direction": normal.tolist(),
                "surface_anchor_mm": anchor.tolist(),
                "cut_center_mm": center.tolist(),
                "frame": frame.tolist(),
                "radii_mm": radii.tolist(),
                "rotation_rad": rotation,
                "removed_triangles": removed_count,
                "remaining_triangles": remaining_count,
                "removed_surface_area_fraction": fraction,
            }
    raise RuntimeError(f"{skull_id}/{defect_type}: no geometry attempt passed gates")


def generate_point_arrays(
    triangles: np.ndarray,
    areas: np.ndarray,
    removed: np.ndarray,
    skull_id: str,
    defect_type: str,
    protocol: Dict[str, Any],
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    sampling = protocol["surface_sampling"]
    gates = protocol["geometric_hard_gates"]
    partial_count = int(sampling["partial_points"])
    implant_count = int(sampling["implant_points"])
    complete_count = int(sampling["complete_points"])
    rim_band = float(gates["reference_rim_band_mm"])
    minimum_rim = int(gates["minimum_reference_rim_points"])

    for attempt in range(int(gates["maximum_point_sampling_attempts"])):
        partial = sample_surface_points(
            triangles[~removed],
            areas[~removed],
            partial_count,
            np.random.default_rng(
                stable_seed(protocol, skull_id, defect_type, "partial", attempt)
            ),
        )
        implant = sample_surface_points(
            triangles[removed],
            areas[removed],
            implant_count,
            np.random.default_rng(
                stable_seed(protocol, skull_id, defect_type, "implant", attempt)
            ),
        )
        complete = sample_surface_points(
            triangles,
            areas,
            complete_count,
            np.random.default_rng(
                stable_seed(protocol, skull_id, defect_type, "complete", attempt)
            ),
        )
        distances = cKDTree(implant).query(partial, k=1, workers=1)[0]
        rim_mask = distances <= rim_band
        rim_count = int(rim_mask.sum())
        if rim_count < minimum_rim:
            continue
        centroid = partial.mean(axis=0)
        scale = float(np.linalg.norm(partial - centroid, axis=1).max())
        if not math.isfinite(scale) or scale <= 0:
            raise RuntimeError(f"{skull_id}/{defect_type}: invalid normalization")
        arrays = {
            "partial": ((partial - centroid) / scale).astype(np.float32),
            "implant": ((implant - centroid) / scale).astype(np.float32),
            "gt": ((complete - centroid) / scale).astype(np.float32),
            "centroid": centroid.astype(np.float64),
            "scale": np.asarray(scale, dtype=np.float64),
            "reference_rim_mask": rim_mask.astype(np.bool_),
        }
        if not all(np.isfinite(value).all() for value in arrays.values()):
            raise RuntimeError(f"{skull_id}/{defect_type}: non-finite output")
        return arrays, {
            "point_sampling_attempt": attempt,
            "reference_rim_band_mm": rim_band,
            "reference_rim_points": rim_count,
            "normalization": {
                "source": "defective_partial_only",
                "centroid": centroid.tolist(),
                "scale": scale,
            },
        }
    raise RuntimeError(f"{skull_id}/{defect_type}: reference-rim gate failed")


def deterministic_npz(path: Path, arrays: Dict[str, np.ndarray]) -> None:
    temporary = path.with_suffix(path.suffix + ".partial")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"Refusing to overwrite derived case: {path}")
    try:
        with zipfile.ZipFile(
            temporary, mode="x", compression=zipfile.ZIP_DEFLATED, compresslevel=6
        ) as archive:
            for key in sorted(arrays):
                payload = io.BytesIO()
                np.lib.format.write_array(
                    payload, np.asarray(arrays[key]), allow_pickle=False
                )
                info = zipfile.ZipInfo(f"{key}.npy", (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, payload.getvalue(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_hash_manifest(directory: Path) -> None:
    for raw in (directory / "files.sha256").read_text(encoding="ascii").splitlines():
        expected, name = raw.split(maxsplit=1)
        path = directory / Path(name.lstrip("*")).name
        if sha256_file(path) != expected.lower():
            raise RuntimeError(f"Data-lock SHA256 mismatch: {path}")


def read_data_lock(directory: Path) -> List[Dict[str, str]]:
    verify_hash_manifest(directory)
    receipt = json.loads((directory / "data_lock_receipt.json").read_text(encoding="utf-8-sig"))
    if (
        receipt.get("data_lock_id") != "mug500plus-m1-healthy125-v1"
        or receipt.get("status") != "locked"
        or int(receipt.get("healthy_skulls", 0)) != 125
        or not receipt.get("development_use_unlocked")
        or receipt.get("protected_external_validation_unlocked")
    ):
        raise RuntimeError("M1 healthy125 data-lock semantics are invalid")
    with (directory / "healthy125_source_assets.csv").open(
        newline="", encoding="utf-8-sig"
    ) as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if not LOCK_FIELDS.issubset(reader.fieldnames or []):
            raise RuntimeError("Healthy125 asset manifest schema is incomplete")
    if len(rows) != 125 or len({row["case_id"] for row in rows}) != 125:
        raise RuntimeError("Healthy125 asset manifest is not exactly 125 unique skulls")
    if any(row["qc_pass"].lower() != "true" for row in rows):
        raise RuntimeError("Healthy125 asset manifest contains a QC failure")
    return rows


def locate_sources(source_root: Path, lock_rows: Sequence[Dict[str, str]]) -> Dict[str, Path]:
    found: Dict[str, List[Path]] = {}
    for path in source_root.rglob("A????_clear.stl"):
        found.setdefault(path.stem[:5].upper(), []).append(path.resolve())
    expected = {row["case_id"].upper() for row in lock_rows}
    unexpected = sorted(set(found).difference(expected))
    if unexpected:
        raise RuntimeError(f"Source root contains unlocked skulls: {unexpected[:10]}")
    result = {}
    for case_id in sorted(expected):
        paths = found.get(case_id, [])
        if len(paths) != 1:
            raise RuntimeError(f"{case_id}: expected one source STL, found {len(paths)}")
        result[case_id] = paths[0]
    return result


def audit_locked_sources(
    source_paths: Dict[str, Path], lock_rows: Sequence[Dict[str, str]]
) -> None:
    lock_by_case = {row["case_id"].upper(): row for row in lock_rows}
    for case_id in tqdm(sorted(source_paths), desc="Audit healthy125 STL"):
        path = source_paths[case_id]
        row = lock_by_case[case_id]
        if path.stat().st_size != int(row["file_bytes"]):
            raise RuntimeError(f"{case_id}: source byte count differs from data lock")
        if sha256_file(path) != row["source_asset_sha256"].lower():
            raise RuntimeError(f"{case_id}: source SHA256 differs from data lock")
        triangle_count = binary_triangle_count(path)
        if triangle_count is None or triangle_count != int(row["triangle_count"]):
            raise RuntimeError(f"{case_id}: STL triangle count differs from data lock")


def generate_skull(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    protocol = task["protocol"]
    lock_row = task["lock_row"]
    source_path = Path(task["source_path"])
    cases_dir = Path(task["cases_dir"])
    manifest_root = Path(task["manifest_root"])
    generator_hash = task["generator_hash"]
    if sha256_file(source_path) != lock_row["source_asset_sha256"].lower():
        raise RuntimeError(f"Source SHA256 mismatch: {source_path}")
    triangles = read_stl_triangles(source_path)
    areas = triangle_areas(triangles)
    skull_id = f"mug500plus__{lock_row['case_id']}"
    family_names = list(protocol["defect_families"])
    records = []
    for family_index, defect_type in enumerate(family_names):
        removed, geometry = choose_defect_geometry(
            triangles, areas, skull_id, defect_type, family_index, protocol
        )
        arrays, point_audit = generate_point_arrays(
            triangles, areas, removed, skull_id, defect_type, protocol
        )
        case_id = f"{skull_id}__{defect_type}"
        point_path = cases_dir / f"{case_id}.npz"
        deterministic_npz(point_path, arrays)
        records.append({
            "case_id": case_id,
            "skull_id": skull_id,
            "defect_type": defect_type,
            "source_dataset": protocol["derived_dataset"]["source_dataset"],
            "source_asset_path": os.path.relpath(source_path, manifest_root),
            "source_asset_sha256": lock_row["source_asset_sha256"].lower(),
            "source_surface_fingerprint_sha256": lock_row[
                "source_surface_fingerprint_sha256"
            ].lower(),
            "surface_fingerprint_algorithm_sha256": lock_row[
                "surface_fingerprint_algorithm_sha256"
            ].lower(),
            "point_path": os.path.relpath(point_path, manifest_root),
            "derived_case_sha256": sha256_file(point_path),
            "generator_sha256": generator_hash,
            "normalization": point_audit["normalization"],
            "geometry": geometry,
            "point_audit": {
                key: value
                for key, value in point_audit.items()
                if key != "normalization"
            },
        })
    return records


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data_lock_dir", type=Path, required=True)
    parser.add_argument("--source_root", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--num_workers", type=int, default=1)
    parser.add_argument("--preflight_only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol = json.loads(args.protocol_json.read_text(encoding="utf-8"))
    if protocol["status"] != "preregistered_generator_not_run":
        raise RuntimeError("M2 generator protocol is not in preregistered state")
    lock_rows = read_data_lock(args.data_lock_dir.resolve())
    source_paths = locate_sources(args.source_root.resolve(), lock_rows)
    audit_locked_sources(source_paths, lock_rows)
    generator_hash = generator_bundle_sha256(args.protocol_json)
    print(f"[ok] healthy125 sources={len(source_paths)}")
    print(f"[sha256] generator_bundle={generator_hash}")
    if args.preflight_only:
        print("[done] preflight only; no derived cases were written")
        return
    if args.out_dir.exists():
        raise RuntimeError(f"Refusing to overwrite output: {args.out_dir}")
    args.out_dir.mkdir(parents=True)
    cases_dir = args.out_dir / "cases"
    cases_dir.mkdir()
    lock_by_case = {row["case_id"].upper(): row for row in lock_rows}
    tasks = [
        {
            "protocol": protocol,
            "lock_row": lock_by_case[case_id],
            "source_path": str(source_paths[case_id]),
            "cases_dir": str(cases_dir.resolve()),
            "manifest_root": str(args.out_dir.resolve()),
            "generator_hash": generator_hash,
        }
        for case_id in sorted(source_paths)
    ]
    records: List[Dict[str, Any]] = []
    workers = max(1, int(args.num_workers))
    if workers == 1:
        for task in tqdm(tasks, desc="MUG500+ M2 skulls"):
            records.extend(generate_skull(task))
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(generate_skull, task) for task in tasks]
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="MUG500+ M2 skulls"
            ):
                records.extend(future.result())
    records.sort(key=lambda row: (row["skull_id"], row["defect_type"]))
    expected_cases = int(protocol["derived_dataset"]["expected_cases"])
    if len(records) != expected_cases:
        raise RuntimeError(f"Expected {expected_cases} cases, got {len(records)}")
    if len({row["derived_case_sha256"] for row in records}) != len(records):
        raise RuntimeError("Derived-case SHA256 values are not unique")
    manifest = args.out_dir / "manifest.jsonl"
    write_jsonl(manifest, records)
    receipt = {
        "protocol_id": protocol["protocol_id"],
        "status": "generated_training_still_locked_pending_D3_data_audit",
        "generator_sha256": generator_hash,
        "source_skulls": len(tasks),
        "derived_cases": len(records),
        "defect_types": list(protocol["defect_families"]),
        "protected_data_used": False,
        "manifest_sha256": sha256_file(manifest),
    }
    receipt_path = args.out_dir / "generation_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out_dir / "files.sha256").write_text(
        "".join(
            f"{sha256_file(path)}  {path.name}\n"
            for path in (manifest, receipt_path)
        ),
        encoding="ascii",
    )
    print(f"[saved] {manifest}")
    print(f"[done] skulls={len(tasks)} cases={len(records)}")
    print("[locked] D3 training remains disabled until manifest and overlap audit")


if __name__ == "__main__":
    main()
