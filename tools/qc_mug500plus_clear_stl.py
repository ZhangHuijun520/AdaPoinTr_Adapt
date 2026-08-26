#!/usr/bin/env python3
"""Apply frozen structural QC and duplicate fingerprints to MUG500+ clear STL files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import struct
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Sequence, Tuple

import numpy as np
from tqdm import tqdm


CASE_RE = re.compile(r"^(A\d{4})_clear\.stl$", re.IGNORECASE)
FINGERPRINT_ALGORITHM_ID = "mug500plus-canonical-triangles-v1-normalized-q1e-5"
FINGERPRINT_ALGORITHM_SHA256 = hashlib.sha256(
    FINGERPRINT_ALGORITHM_ID.encode("ascii")
).hexdigest()
MINIMUM_FILE_BYTES = 102400
MINIMUM_TRIANGLES = 1000
MINIMUM_NONDEGENERATE_FRACTION = 0.99
MINIMUM_BBOX_EXTENT_MM = 50.0
MAXIMUM_BBOX_EXTENT_MM = 600.0
MINIMUM_BBOX_ASPECT_RATIO = 0.15


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binary_triangle_count(path: Path) -> int | None:
    size = path.stat().st_size
    if size < 84:
        return None
    with path.open("rb") as handle:
        handle.seek(80)
        count = struct.unpack("<I", handle.read(4))[0]
    return count if 84 + 50 * count == size else None


def read_stl_triangles(path: Path) -> Tuple[np.ndarray, str]:
    count = binary_triangle_count(path)
    if count is not None:
        dtype = np.dtype(
            [("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attr", "<u2")]
        )
        records = np.fromfile(path, dtype=dtype, count=count, offset=84)
        return np.asarray(records["vertices"], dtype=np.float64), "binary"

    vertices: List[List[float]] = []
    with path.open("r", encoding="ascii", errors="strict") as handle:
        for line in handle:
            fields = line.strip().split()
            if len(fields) == 4 and fields[0].lower() == "vertex":
                vertices.append([float(value) for value in fields[1:]])
    if len(vertices) % 3:
        raise RuntimeError("ASCII STL vertex count is not divisible by three")
    return np.asarray(vertices, dtype=np.float64).reshape(-1, 3, 3), "ascii"


def canonical_surface_fingerprint(
    triangles: np.ndarray, bbox_min: np.ndarray, bbox_max: np.ndarray
) -> str:
    center = (bbox_min + bbox_max) * 0.5
    scale = float(np.max(bbox_max - bbox_min))
    if not math.isfinite(scale) or scale <= 0:
        raise RuntimeError("Cannot fingerprint a zero-extent surface")
    quantized = np.rint((triangles - center) / scale * 100000.0).astype("<i4")

    ordered_vertices = np.empty_like(quantized)
    for index, triangle in enumerate(quantized):
        order = np.lexsort((triangle[:, 2], triangle[:, 1], triangle[:, 0]))
        ordered_vertices[index] = triangle[order]
    flattened = ordered_vertices.reshape(len(ordered_vertices), 9)
    order = np.lexsort(tuple(flattened[:, index] for index in reversed(range(9))))
    canonical = np.ascontiguousarray(flattened[order], dtype="<i4")
    digest = hashlib.sha256()
    digest.update(FINGERPRINT_ALGORITHM_ID.encode("ascii") + b"\0")
    digest.update(struct.pack("<Q", len(canonical)))
    digest.update(canonical.tobytes(order="C"))
    return digest.hexdigest()


def evaluate_stl(path: Path) -> Dict[str, Any]:
    match = CASE_RE.fullmatch(path.name)
    case_id = match.group(1).upper() if match else ""
    reasons = []
    size = path.stat().st_size
    if not match:
        reasons.append("unexpected_filename")
    if size < MINIMUM_FILE_BYTES:
        reasons.append("file_too_small")

    try:
        triangles, stl_format = read_stl_triangles(path)
    except Exception as exc:
        return {
            "case_id": case_id,
            "source_path": str(path.resolve()),
            "source_asset_sha256": sha256_file(path),
            "source_surface_fingerprint_sha256": "",
            "surface_fingerprint_algorithm_sha256": FINGERPRINT_ALGORITHM_SHA256,
            "stl_format": "unreadable",
            "file_bytes": size,
            "triangle_count": 0,
            "finite_vertices": False,
            "nondegenerate_fraction": 0.0,
            "bbox_x_mm": "",
            "bbox_y_mm": "",
            "bbox_z_mm": "",
            "bbox_min_extent_mm": "",
            "bbox_max_extent_mm": "",
            "bbox_aspect_ratio": "",
            "surface_area_mm2": "",
            "qc_pass": False,
            "failure_reasons": ";".join(reasons + [f"parse_error:{type(exc).__name__}"]),
        }

    count = int(len(triangles))
    finite = bool(np.isfinite(triangles).all())
    if count < MINIMUM_TRIANGLES:
        reasons.append("too_few_triangles")
    if not finite:
        reasons.append("nonfinite_vertices")

    if finite and count:
        vertices = triangles.reshape(-1, 3)
        bbox_min = vertices.min(axis=0)
        bbox_max = vertices.max(axis=0)
        extents = bbox_max - bbox_min
        cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        double_area = np.linalg.norm(cross, axis=1)
        scale = max(float(np.max(extents)), 1.0)
        nondegenerate = double_area > (scale * scale * 1e-12)
        nondegenerate_fraction = float(np.mean(nondegenerate))
        surface_area = float(np.sum(double_area) * 0.5)
        min_extent = float(np.min(extents))
        max_extent = float(np.max(extents))
        aspect = min_extent / max_extent if max_extent > 0 else 0.0
        if nondegenerate_fraction < MINIMUM_NONDEGENERATE_FRACTION:
            reasons.append("too_many_degenerate_triangles")
        if min_extent < MINIMUM_BBOX_EXTENT_MM:
            reasons.append("bbox_too_small")
        if max_extent > MAXIMUM_BBOX_EXTENT_MM:
            reasons.append("bbox_too_large")
        if aspect < MINIMUM_BBOX_ASPECT_RATIO:
            reasons.append("bbox_aspect_implausible")
        if not math.isfinite(surface_area) or surface_area <= 0:
            reasons.append("invalid_surface_area")
        fingerprint = (
            canonical_surface_fingerprint(triangles, bbox_min, bbox_max)
            if max_extent > 0
            else ""
        )
    else:
        extents = np.array([np.nan, np.nan, np.nan])
        min_extent = max_extent = aspect = surface_area = nondegenerate_fraction = math.nan
        fingerprint = ""

    return {
        "case_id": case_id,
        "source_path": str(path.resolve()),
        "source_asset_sha256": sha256_file(path),
        "source_surface_fingerprint_sha256": fingerprint,
        "surface_fingerprint_algorithm_sha256": FINGERPRINT_ALGORITHM_SHA256,
        "stl_format": stl_format,
        "file_bytes": size,
        "triangle_count": count,
        "finite_vertices": finite,
        "nondegenerate_fraction": nondegenerate_fraction,
        "bbox_x_mm": float(extents[0]),
        "bbox_y_mm": float(extents[1]),
        "bbox_z_mm": float(extents[2]),
        "bbox_min_extent_mm": min_extent,
        "bbox_max_extent_mm": max_extent,
        "bbox_aspect_ratio": aspect,
        "surface_area_mm2": surface_area,
        "qc_pass": not reasons,
        "failure_reasons": ";".join(reasons),
    }


def read_expected_cases(path: Path) -> List[str]:
    cases = [line.strip().upper() for line in path.read_text().splitlines() if line.strip()]
    if not cases or len(cases) != len(set(cases)):
        raise RuntimeError("Expected case list is empty or contains duplicates")
    if any(not re.fullmatch(r"A\d{4}", case) for case in cases):
        raise RuntimeError("Expected case list contains a non-A-series identifier")
    return cases


def apply_duplicate_gate(rows: List[Dict[str, Any]]) -> None:
    by_fingerprint: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        fingerprint = str(row["source_surface_fingerprint_sha256"])
        if fingerprint:
            by_fingerprint[fingerprint].append(row)
    for duplicate_rows in by_fingerprint.values():
        if len(duplicate_rows) < 2:
            continue
        case_ids = ",".join(sorted(str(row["case_id"]) for row in duplicate_rows))
        for row in duplicate_rows:
            reasons = [value for value in str(row["failure_reasons"]).split(";") if value]
            reasons.append(f"duplicate_surface:{case_ids}")
            row["failure_reasons"] = ";".join(reasons)
            row["qc_pass"] = False


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stl_root", type=Path, required=True)
    parser.add_argument("--expected_cases", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    expected = read_expected_cases(args.expected_cases)
    found: Dict[str, List[Path]] = defaultdict(list)
    for path in args.stl_root.rglob("*_clear.stl"):
        match = CASE_RE.fullmatch(path.name)
        if match:
            found[match.group(1).upper()].append(path)

    unexpected = sorted(set(found).difference(expected))
    if unexpected:
        raise RuntimeError(f"STL root contains unplanned A-series cases: {unexpected[:12]}")
    rows = []
    for case_id in tqdm(expected, desc="MUG500+ M1 STL QC"):
        paths = found.get(case_id, [])
        if len(paths) == 1:
            row = evaluate_stl(paths[0])
        else:
            row = {
                "case_id": case_id,
                "source_path": "",
                "source_asset_sha256": "",
                "source_surface_fingerprint_sha256": "",
                "surface_fingerprint_algorithm_sha256": FINGERPRINT_ALGORITHM_SHA256,
                "stl_format": "missing" if not paths else "duplicate_paths",
                "file_bytes": 0,
                "triangle_count": 0,
                "finite_vertices": False,
                "nondegenerate_fraction": 0.0,
                "bbox_x_mm": "",
                "bbox_y_mm": "",
                "bbox_z_mm": "",
                "bbox_min_extent_mm": "",
                "bbox_max_extent_mm": "",
                "bbox_aspect_ratio": "",
                "surface_area_mm2": "",
                "qc_pass": False,
                "failure_reasons": "missing_expected_stl" if not paths else "duplicate_case_paths",
            }
        rows.append(row)
    apply_duplicate_gate(rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "mug500plus_m1_qc_per_case.csv"
    write_csv(csv_path, rows)
    passed = [row for row in rows if bool(row["qc_pass"])]
    summary = {
        "protocol_id": "mug500plus-m1-acquisition-qc-v1",
        "expected_cases": len(expected),
        "qc_pass_cases": len(passed),
        "qc_fail_cases": len(rows) - len(passed),
        "all_metrics_computed_without_model": True,
        "craniotomy_or_B_series_accessed": False,
        "surface_fingerprint_algorithm_id": FINGERPRINT_ALGORITHM_ID,
        "surface_fingerprint_algorithm_sha256": FINGERPRINT_ALGORITHM_SHA256,
        "per_case_csv": str(csv_path),
    }
    summary_path = args.out_dir / "mug500plus_m1_qc_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    with (args.out_dir / "files.sha256").open("w", encoding="ascii", newline="\n") as handle:
        for path in (csv_path, summary_path):
            handle.write(f"{sha256_file(path)}  {path.name}\n")
    print(f"[saved] {csv_path}")
    print(f"[saved] {summary_path}")
    print(f"[done] pass={len(passed)} fail={len(rows) - len(passed)}")
    print("[locked] QC is geometry-only and did not access a model or protected B-series data")


if __name__ == "__main__":
    main()
