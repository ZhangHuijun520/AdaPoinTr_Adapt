#!/usr/bin/env python3
"""Run the preregistered high-resolution MUG500+ protected-overlap audit v2."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist
from tqdm import tqdm


PROTOCOL_ID = "mug500plus-m2-protected-overlap-audit-v2"
V1_AUDIT_ID = "mug500plus-m2-protected-overlap-audit-v1"
DEFAULT_PROTOCOL = Path(__file__).resolve().parents[1] / "docs" / (
    "mamba_v13_d3_mug500plus_phase_m2_overlap_audit_protocol_v2.json"
)
ORIENTATIONS = tuple(
    (permutation, signs)
    for permutation in itertools.permutations(range(3))
    for signs in itertools.product((-1.0, 1.0), repeat=3)
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def resolve_asset(manifest: Path, raw: str) -> Path:
    normalized = str(raw).replace("\\", os.sep).replace("/", os.sep)
    path = Path(normalized)
    if not path.is_absolute():
        path = manifest.parent / path
    return path.resolve()


def deterministic_subsample(points: np.ndarray, count: int) -> np.ndarray:
    if len(points) < count:
        raise RuntimeError(f"Need at least {count} points, got {len(points)}")
    order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
    positions = np.linspace(0, len(order) - 1, count, dtype=np.int64)
    return np.ascontiguousarray(points[order[positions]], dtype=np.float64)


def normalize_points(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise RuntimeError(f"Invalid complete point cloud: {points.shape}")
    centered = points - points.mean(axis=0)
    rms = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))
    if not math.isfinite(rms) or rms <= 0:
        raise RuntimeError("Complete point cloud has invalid RMS radius")
    return centered / rms


def geometry_representation(
    point_path: Path,
    coarse_count: int,
    high_count: int,
    descriptor_count: int,
) -> Dict[str, np.ndarray]:
    with np.load(point_path, allow_pickle=False) as sample:
        points = normalize_points(sample["gt"])
    covariance = np.cov(points, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.maximum(eigenvalues[order], 0.0)
    eigenvectors = eigenvectors[:, order]
    eigenvalues /= max(float(eigenvalues.sum()), 1e-12)

    coarse = deterministic_subsample(points, coarse_count) @ eigenvectors
    high = deterministic_subsample(points, high_count) @ eigenvectors
    descriptor_points = deterministic_subsample(points, descriptor_count)
    radial = np.linalg.norm(points, axis=1)
    pairwise = pdist(descriptor_points, metric="euclidean")
    quantiles = np.linspace(0.02, 0.98, 49)
    descriptor = np.concatenate((
        eigenvalues,
        np.quantile(radial, quantiles),
        np.quantile(pairwise, quantiles),
    ))
    return {
        "coarse": np.ascontiguousarray(coarse),
        "high": np.ascontiguousarray(high),
        "descriptor": np.ascontiguousarray(descriptor),
    }


def symmetric_distances(first: np.ndarray, second: np.ndarray) -> Tuple[float, float]:
    first_tree = cKDTree(first)
    second_tree = cKDTree(second)
    first_to_second = second_tree.query(first, k=1, workers=1)[0]
    second_to_first = first_tree.query(second, k=1, workers=1)[0]
    cd_l1 = float((first_to_second.mean() + second_to_first.mean()) * 0.5)
    hd95 = float(max(
        np.quantile(first_to_second, 0.95),
        np.quantile(second_to_first, 0.95),
    ))
    return cd_l1, hd95


def best_coarse_orientations(
    fixed: np.ndarray, moving: np.ndarray, retain: int
) -> List[Tuple[Tuple[int, int, int], Tuple[float, float, float]]]:
    scored = []
    for permutation, signs in ORIENTATIONS:
        oriented = moving[:, permutation] * np.asarray(signs)
        cd_l1, hd95 = symmetric_distances(fixed, oriented)
        scored.append((cd_l1, hd95, permutation, signs))
    scored.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    return [(item[2], item[3]) for item in scored[:retain]]


def rigid_fit(source: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    source_mean = source.mean(axis=0)
    target_mean = target.mean(axis=0)
    source_centered = source - source_mean
    target_centered = target - target_mean
    u, _, vt = np.linalg.svd(source_centered.T @ target_centered)
    rotation = u @ vt
    if np.linalg.det(rotation) < 0:
        u[:, -1] *= -1.0
        rotation = u @ vt
    translation = target_mean - source_mean @ rotation
    return rotation, translation


def refined_distances(
    first: Dict[str, np.ndarray],
    second: Dict[str, np.ndarray],
    retained_orientations: int,
    iterations: int,
) -> Tuple[float, float]:
    orientations = best_coarse_orientations(
        first["coarse"], second["coarse"], retained_orientations
    )
    fixed = first["high"]
    fixed_tree = cKDTree(fixed)
    best = (math.inf, math.inf)
    for permutation, signs in orientations:
        moving = second["high"][:, permutation] * np.asarray(signs)
        for _ in range(iterations):
            nearest = fixed_tree.query(moving, k=1, workers=1)[1]
            rotation, translation = rigid_fit(moving, fixed[nearest])
            updated = moving @ rotation + translation
            if float(np.max(np.abs(updated - moving))) < 1e-8:
                moving = updated
                break
            moving = updated
        metrics = symmetric_distances(fixed, moving)
        if metrics < best:
            best = metrics
    return best


def percentile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def csv_bytes(rows: Sequence[Sequence[Any]]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode("utf-8")


def verify_v1(audit_dir: Path, expected_summary_hash: str) -> None:
    summary_path = audit_dir / "overlap_audit_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (
        summary.get("audit_id") != V1_AUDIT_ID
        or summary.get("automatic_gate_passed") is not False
        or sha256_file(summary_path) != expected_summary_hash
    ):
        raise RuntimeError("Frozen v1 audit does not match the v2 amendment")


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if (
        protocol.get("protocol_id") != PROTOCOL_ID
        or protocol.get("status") != "preregistered_not_run"
        or not protocol["amendment"]["v1_result_remains_immutable"]
    ):
        raise RuntimeError("Overlap-audit v2 protocol is not preregistered")
    boundary = protocol["access_boundary"]
    if (
        boundary["allowed_arrays"] != ["gt"]
        or boundary["model_predictions_allowed"]
        or boundary["model_metrics_allowed"]
        or boundary["defect_or_implant_arrays_allowed"]
        or boundary["mug_B_series_or_craniotomy_allowed"]
    ):
        raise RuntimeError("Protected access boundary is invalid")


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical v2 audit")
        print(f"[locked] existing v2 audit is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] immutable protected-overlap audit v2: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2_manifest", type=Path, required=True)
    parser.add_argument("--skullbreak_manifest", type=Path, required=True)
    parser.add_argument("--skullfix_manifest", type=Path, required=True)
    parser.add_argument("--v1_audit_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, default=DEFAULT_PROTOCOL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol_json.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    verify_v1(
        args.v1_audit_dir.resolve(),
        protocol["amendment"]["source_v1_summary_sha256"],
    )

    m2_manifest = args.m2_manifest.resolve()
    protected_manifests = {
        "skullbreak": args.skullbreak_manifest.resolve(),
        "skullfix": args.skullfix_manifest.resolve(),
    }
    m2_rows = read_jsonl(m2_manifest)
    if len(m2_rows) != 500 or len({row["skull_id"] for row in m2_rows}) != 125:
        raise RuntimeError("M2 portable manifest is not exact 125 x 4")

    protected_rows: Dict[str, List[Dict[str, Any]]] = {}
    protected_hashes: Dict[str, set] = collections.defaultdict(set)
    for dataset, manifest in protected_manifests.items():
        selected = []
        for row in read_jsonl(manifest):
            point_path = resolve_asset(manifest, row["point_path"])
            point_hash = sha256_file(point_path)
            protected_hashes[point_hash].add(f"{dataset}|point|{row['case_id']}")
            complete_hash = row.get("complete_mask_sha256")
            if complete_hash:
                protected_hashes[str(complete_hash).lower()].add(
                    f"{dataset}|complete|{row.get('skull_id', row['case_id'])}"
                )
            selected.append({
                "case_id": str(row["case_id"]),
                "skull_id": str(row.get("skull_id", row["case_id"])),
                "point_path": point_path,
            })
        protected_rows[dataset] = selected

    mug_hashes: Dict[str, set] = collections.defaultdict(set)
    for row in m2_rows:
        for field in (
            "source_asset_sha256",
            "source_surface_fingerprint_sha256",
            "derived_case_sha256",
        ):
            mug_hashes[str(row[field]).lower()].add(
                f"mug500plus|{field}|{row['case_id']}"
            )
    intersections = sorted(set(mug_hashes).intersection(protected_hashes))
    exact_rows: List[List[Any]] = [["sha256", "mug_labels", "protected_labels"]]
    for value in intersections:
        exact_rows.append([
            value,
            ";".join(sorted(mug_hashes[value])),
            ";".join(sorted(protected_hashes[value])),
        ])

    m2_by_skull: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for row in m2_rows:
        item = dict(row)
        item["point_path"] = resolve_asset(m2_manifest, row["point_path"])
        m2_by_skull[str(row["skull_id"])].append(item)
    protected_by_skull: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for dataset, rows in protected_rows.items():
        grouped: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
        for row in rows:
            grouped[row["skull_id"]].append(row)
        protected_by_skull[dataset] = grouped

    geometry = protocol["geometry_representation"]
    alignment = protocol["rigid_alignment"]
    cache: Dict[str, Dict[str, np.ndarray]] = {}

    def representation(path: Path) -> Dict[str, np.ndarray]:
        key = str(path)
        if key not in cache:
            cache[key] = geometry_representation(
                path,
                int(geometry["coarse_alignment_points"]),
                int(geometry["high_resolution_points"]),
                int(geometry["descriptor_points"]),
            )
        return cache[key]

    def metrics(first: Dict[str, Any], second: Dict[str, Any]) -> Tuple[float, float]:
        return refined_distances(
            representation(Path(first["point_path"])),
            representation(Path(second["point_path"])),
            int(alignment["coarse_initializations_retained"]),
            int(alignment["icp_iterations"]),
        )

    representatives: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {
        "mug500plus": [
            (skull_id, min(items, key=lambda row: row["case_id"]))
            for skull_id, items in sorted(m2_by_skull.items())
        ]
    }
    for dataset, grouped in protected_by_skull.items():
        representatives[dataset] = [
            (skull_id, min(items, key=lambda row: row["case_id"]))
            for skull_id, items in sorted(grouped.items())
        ]

    calibration_jobs = []
    for skull_id, items in sorted(m2_by_skull.items()):
        ordered = sorted(items, key=lambda row: row["case_id"])
        calibration_jobs.append(("positive", "mug500plus", skull_id, ordered[0], ordered[1]))
    for skull_id, items in sorted(protected_by_skull["skullbreak"].items()):
        ordered = sorted(items, key=lambda row: row["case_id"])
        calibration_jobs.append(("positive", "skullbreak", skull_id, ordered[0], ordered[1]))
    for dataset in ("mug500plus", "skullbreak", "skullfix"):
        items = representatives[dataset]
        for index, (skull_id, first) in enumerate(items):
            other_id, second = items[(index + 1) % len(items)]
            calibration_jobs.append((
                "negative", dataset, f"{skull_id}|{other_id}", first, second
            ))

    calibration_rows: List[List[Any]] = [[
        "label", "dataset", "pair_id", "first_case_id", "second_case_id",
        "symmetric_cd_l1_normalized", "symmetric_hd95_normalized",
    ]]
    calibration_values = {"positive": [], "negative": []}
    for label, dataset, pair_id, first, second in tqdm(
        calibration_jobs, desc="Overlap v2 calibration"
    ):
        cd_l1, hd95 = metrics(first, second)
        calibration_values[label].append((cd_l1, hd95))
        calibration_rows.append([
            label, dataset, pair_id, first["case_id"], second["case_id"],
            cd_l1, hd95,
        ])

    positive_cd = percentile((item[0] for item in calibration_values["positive"]), 0.99)
    positive_hd = percentile((item[1] for item in calibration_values["positive"]), 0.99)
    negative_cd = percentile((item[0] for item in calibration_values["negative"]), 0.01)
    negative_hd = percentile((item[1] for item in calibration_values["negative"]), 0.01)
    calibration_separated = positive_cd < negative_cd and positive_hd < negative_hd
    cd_threshold = (positive_cd + negative_cd) * 0.5
    hd_threshold = (positive_hd + negative_hd) * 0.5

    all_representatives = [item for rows in representatives.values() for item in rows]
    descriptor_matrix = np.vstack([
        representation(Path(item[1]["point_path"]))["descriptor"]
        for item in all_representatives
    ])
    median = np.median(descriptor_matrix, axis=0)
    mad = np.median(np.abs(descriptor_matrix - median), axis=0) * 1.4826
    scale = np.maximum(mad, 1e-6)

    shortlist = int(protocol["candidate_screen"]["nearest_protected_per_mug_skull"])
    candidate_jobs = []
    for dataset in ("skullbreak", "skullfix"):
        protected = representatives[dataset]
        protected_descriptors = np.vstack([
            representation(Path(item[1]["point_path"]))["descriptor"]
            for item in protected
        ])
        protected_scaled = (protected_descriptors - median) / scale
        for mug_skull_id, mug_item in representatives["mug500plus"]:
            mug_descriptor = representation(Path(mug_item["point_path"]))["descriptor"]
            distances = np.linalg.norm(
                protected_scaled - (mug_descriptor - median) / scale, axis=1
            )
            for rank, index in enumerate(np.argsort(distances)[:shortlist], 1):
                protected_id, protected_item = protected[int(index)]
                candidate_jobs.append((
                    dataset, mug_skull_id, mug_item, protected_id,
                    protected_item, rank, float(distances[index]),
                ))

    candidate_rows: List[List[Any]] = [[
        "protected_dataset", "mug_skull_id", "mug_case_id",
        "protected_skull_id", "protected_case_id", "descriptor_rank",
        "descriptor_distance", "symmetric_cd_l1_normalized",
        "symmetric_hd95_normalized", "suspect_near_duplicate",
    ]]
    suspects = []
    for job in tqdm(candidate_jobs, desc="Overlap v2 high-resolution candidates"):
        dataset, mug_id, mug_item, protected_id, protected_item, rank, distance = job
        cd_l1, hd95 = metrics(mug_item, protected_item)
        suspect = cd_l1 <= cd_threshold and hd95 <= hd_threshold
        row = [
            dataset, mug_id, mug_item["case_id"], protected_id,
            protected_item["case_id"], rank, distance, cd_l1, hd95, int(suspect),
        ]
        candidate_rows.append(row)
        if suspect:
            suspects.append(row)

    passed = calibration_separated and not intersections and not suspects
    if not calibration_separated:
        status = "blocked_calibration_not_separated"
    elif intersections:
        status = "blocked_exact_overlap"
    elif suspects:
        status = "blocked_high_resolution_suspects"
    else:
        status = "passed"

    summary = {
        "audit_id": PROTOCOL_ID,
        "status": status,
        "protocol_sha256": sha256_file(protocol_path),
        "source_v1_summary_sha256": protocol["amendment"]["source_v1_summary_sha256"],
        "m2_manifest_sha256": sha256_file(m2_manifest),
        "protected_manifest_sha256": {
            name: sha256_file(path) for name, path in protected_manifests.items()
        },
        "counts": {
            "mug_source_skulls": len(representatives["mug500plus"]),
            "skullbreak_source_skulls": len(representatives["skullbreak"]),
            "skullfix_source_skulls": len(representatives["skullfix"]),
            "positive_calibration_pairs": len(calibration_values["positive"]),
            "negative_calibration_pairs": len(calibration_values["negative"]),
            "cross_dataset_candidate_pairs": len(candidate_jobs),
            "exact_hash_intersections": len(intersections),
            "high_resolution_suspects": len(suspects),
        },
        "calibration": {
            "positive_cd_q99": positive_cd,
            "positive_hd95_q99": positive_hd,
            "negative_cd_q01": negative_cd,
            "negative_hd95_q01": negative_hd,
            "separated": calibration_separated,
        },
        "thresholds": {
            "symmetric_cd_l1_normalized": cd_threshold,
            "symmetric_hd95_normalized": hd_threshold,
            "rule": "midpoint_between_positive_q99_and_negative_q01",
        },
        "automatic_gate_passed": passed,
        "selection_inert": True,
        "model_predictions_used": False,
        "model_metrics_used": False,
        "protected_defect_or_implant_arrays_used": False,
        "mug_B_series_or_craniotomy_used": False,
        "training_unlocked": passed,
    }
    report = f"""# MUG500+ M2 protected-overlap high-resolution audit v2

> v2 是 v1 失败后的预注册独立复核。v1 冻结结果未被改写；本审计不访问模型预测、模型指标、implant/defect 数组或 MUG B-series。

- positive calibration pairs：{len(calibration_values['positive'])}
- negative calibration pairs：{len(calibration_values['negative'])}
- calibration separated：{calibration_separated}
- exact hash intersections：{len(intersections)}
- high-resolution candidate pairs：{len(candidate_jobs)}
- high-resolution suspects：{len(suspects)}
- CD threshold：{cd_threshold:.8f}
- HD95 threshold：{hd_threshold:.8f}
- automatic gate：{'通过' if passed else '未通过'}
- D3 training：{'可进入 100/25 数据冻结步骤' if passed else '继续锁定'}
"""
    files = {
        "calibration_pairs.csv": csv_bytes(calibration_rows),
        "high_resolution_candidates.csv": csv_bytes(candidate_rows),
        "exact_hash_intersections.csv": csv_bytes(exact_rows),
        "overlap_audit_v2_summary.json": (
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
        "overlap_audit_v2_report_zh.md": report.encode("utf-8"),
    }
    hashes = [f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    write_locked(files, args.output_dir.resolve())

    print(f"[calibration] separated={calibration_separated}")
    print(f"[gate] exact={len(intersections)} suspects={len(suspects)}")
    print(f"[{'ok' if passed else 'blocked'}] high-resolution overlap audit v2")
    print(f"[locked] D3 training {'may proceed to data lock' if passed else 'remains disabled'}")


if __name__ == "__main__":
    main()
