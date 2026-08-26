#!/usr/bin/env python3
"""Run the preregistered exact-hash and near-duplicate geometry audit."""

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


DEFAULT_PROTOCOL = Path(__file__).resolve().parents[1] / "docs" / (
    "mamba_v13_d3_mug500plus_phase_m2_overlap_audit_protocol_v1.json"
)
PROTOCOL_ID = "mug500plus-m2-protected-overlap-audit-v1"
SIGN_COMBINATIONS = tuple(itertools.product((-1.0, 1.0), repeat=3))
AXIS_PERMUTATIONS = tuple(itertools.permutations(range(3)))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_asset(manifest: Path, raw: str) -> Path:
    normalized = str(raw).replace("\\", os.sep).replace("/", os.sep)
    path = Path(normalized)
    if not path.is_absolute():
        path = manifest.parent / path
    return path.resolve()


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def deterministic_subsample(points: np.ndarray, count: int) -> np.ndarray:
    order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
    positions = np.linspace(0, len(order) - 1, count, dtype=np.int64)
    return np.ascontiguousarray(points[order[positions]], dtype=np.float64)


def normalize_points(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 1024:
        raise RuntimeError(f"Invalid complete point cloud shape: {points.shape}")
    if not np.isfinite(points).all():
        raise RuntimeError("Complete point cloud contains NaN or Inf")
    centered = points - points.mean(axis=0)
    rms = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))
    if not math.isfinite(rms) or rms <= 0:
        raise RuntimeError("Complete point cloud has zero RMS radius")
    return centered / rms


def geometry_representation(
    point_path: Path, comparison_count: int, descriptor_count: int
) -> Dict[str, np.ndarray]:
    with np.load(point_path, allow_pickle=False) as sample:
        points = normalize_points(sample["gt"])
    covariance = np.cov(points, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.maximum(eigenvalues[order], 0.0)
    eigenvectors = eigenvectors[:, order]
    eigenvalues /= max(float(eigenvalues.sum()), 1e-12)
    comparison = deterministic_subsample(points, comparison_count)
    descriptor_points = deterministic_subsample(points, descriptor_count)
    radial = np.linalg.norm(points, axis=1)
    pairwise = pdist(descriptor_points, metric="euclidean")
    quantiles = np.linspace(0.02, 0.98, 33)
    descriptor = np.concatenate(
        (eigenvalues, np.quantile(radial, quantiles), np.quantile(pairwise, quantiles))
    )
    return {
        "canonical": np.ascontiguousarray(comparison @ eigenvectors),
        "descriptor": descriptor,
    }


def aligned_distances(first: np.ndarray, second: np.ndarray) -> Tuple[float, float]:
    first_tree = cKDTree(first)
    best = (math.inf, math.inf)
    for permutation in AXIS_PERMUTATIONS:
        permuted = second[:, permutation]
        for signs in SIGN_COMBINATIONS:
            oriented = permuted * np.asarray(signs, dtype=np.float64)
            second_tree = cKDTree(oriented)
            first_to_second = second_tree.query(first, k=1, workers=1)[0]
            second_to_first = first_tree.query(oriented, k=1, workers=1)[0]
            cd_l1 = float(
                (first_to_second.mean() + second_to_first.mean()) * 0.5
            )
            hd95 = float(
                max(
                    np.quantile(first_to_second, 0.95),
                    np.quantile(second_to_first, 0.95),
                )
            )
            if (cd_l1, hd95) < best:
                best = (cd_l1, hd95)
    return best


def csv_bytes(rows: Sequence[Sequence[Any]]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode("utf-8")


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if (
        protocol.get("protocol_id") != PROTOCOL_ID
        or protocol.get("status") != "preregistered_not_run"
    ):
        raise RuntimeError("Overlap-audit protocol is not preregistered")
    boundary = protocol["access_boundary"]
    if (
        boundary["allowed_arrays"] != ["gt"]
        or boundary["model_predictions_allowed"]
        or boundary["model_metrics_allowed"]
        or boundary["defect_or_implant_arrays_allowed"]
    ):
        raise RuntimeError("Protected-data access boundary is invalid")
    if int(protocol["candidate_screen"]["nearest_protected_per_mug_skull"]) != 10:
        raise RuntimeError("Candidate shortlist size changed after preregistration")


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical overlap audit")
        print(f"[locked] existing overlap audit is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] immutable protected-overlap audit: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2_manifest", type=Path, required=True)
    parser.add_argument("--skullbreak_manifest", type=Path, required=True)
    parser.add_argument("--skullfix_manifest", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, default=DEFAULT_PROTOCOL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol_json.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    validate_protocol(protocol)
    m2_manifest = args.m2_manifest.resolve()
    protected_manifests = {
        "skullbreak": args.skullbreak_manifest.resolve(),
        "skullfix": args.skullfix_manifest.resolve(),
    }
    m2_rows = read_jsonl(m2_manifest)
    if len(m2_rows) != 500 or len({row["skull_id"] for row in m2_rows}) != 125:
        raise RuntimeError("M2 portable manifest is not exact 125 x 4")

    protected_rows: Dict[str, List[Dict[str, Any]]] = {}
    protected_hash_labels: Dict[str, set] = collections.defaultdict(set)
    for dataset, manifest in protected_manifests.items():
        rows = read_jsonl(manifest)
        selected = []
        for row in tqdm(rows, desc=f"Hash protected {dataset}"):
            point_path = resolve_asset(manifest, row["point_path"])
            if not point_path.is_file():
                raise FileNotFoundError(point_path)
            point_hash = sha256_file(point_path)
            protected_hash_labels[point_hash].add(
                f"{dataset}|point_npz|{row['case_id']}"
            )
            complete_hash = row.get("complete_mask_sha256")
            if complete_hash:
                protected_hash_labels[str(complete_hash).lower()].add(
                    f"{dataset}|complete_mask|{row.get('skull_id', row['case_id'])}"
                )
            selected.append({
                "case_id": str(row["case_id"]),
                "skull_id": str(row.get("skull_id", row["case_id"])),
                "point_path": point_path,
            })
        protected_rows[dataset] = selected

    mug_hash_labels: Dict[str, set] = collections.defaultdict(set)
    for row in m2_rows:
        for field in (
            "source_asset_sha256",
            "source_surface_fingerprint_sha256",
            "derived_case_sha256",
        ):
            mug_hash_labels[str(row[field]).lower()].add(
                f"mug500plus|{field}|{row['case_id']}"
            )
    intersections = sorted(set(mug_hash_labels).intersection(protected_hash_labels))
    exact_rows: List[List[Any]] = [["sha256", "mug_labels", "protected_labels"]]
    for value in intersections:
        exact_rows.append([
            value,
            ";".join(sorted(mug_hash_labels[value])),
            ";".join(sorted(protected_hash_labels[value])),
        ])

    protected_lines = []
    for value in sorted(protected_hash_labels):
        label = ";".join(sorted(protected_hash_labels[value]))
        protected_lines.append(f"{value}  {label}")
    protected_fingerprints = ("\n".join(protected_lines) + "\n").encode("ascii")

    comparison_count = int(protocol["geometry_representation"]["comparison_points"])
    descriptor_count = int(protocol["geometry_representation"]["descriptor_points"])
    cache: Dict[str, Dict[str, np.ndarray]] = {}

    def representation(path: Path) -> Dict[str, np.ndarray]:
        key = str(path)
        if key not in cache:
            cache[key] = geometry_representation(
                path, comparison_count, descriptor_count
            )
        return cache[key]

    m2_by_skull = collections.defaultdict(list)
    for row in m2_rows:
        item = dict(row)
        item["point_path"] = resolve_asset(m2_manifest, row["point_path"])
        m2_by_skull[str(row["skull_id"])].append(item)
    protected_by_skull = {}
    for dataset, rows in protected_rows.items():
        grouped = collections.defaultdict(list)
        for row in rows:
            grouped[row["skull_id"]].append(row)
        protected_by_skull[dataset] = grouped

    calibration_rows: List[List[Any]] = [[
        "dataset", "skull_id", "first_case_id", "second_case_id",
        "symmetric_cd_l1_normalized", "symmetric_hd95_normalized",
    ]]
    calibration_metrics = []
    calibration_pairs = []
    for skull_id, items in sorted(m2_by_skull.items()):
        items = sorted(items, key=lambda row: row["case_id"])
        base = next(row for row in items if row["defect_type"] == "ellipsoid_small")
        for item in items:
            if item is not base:
                calibration_pairs.append(("mug500plus", skull_id, base, item))
    for skull_id, items in sorted(protected_by_skull["skullbreak"].items()):
        items = sorted(items, key=lambda row: row["case_id"])
        for item in items[1:]:
            calibration_pairs.append(("skullbreak", skull_id, items[0], item))
    for dataset, skull_id, first, second in tqdm(
        calibration_pairs, desc="Calibrate same-source geometry"
    ):
        first_rep = representation(Path(first["point_path"]))
        second_rep = representation(Path(second["point_path"]))
        cd_l1, hd95 = aligned_distances(
            first_rep["canonical"], second_rep["canonical"]
        )
        calibration_metrics.append((cd_l1, hd95))
        calibration_rows.append([
            dataset,
            skull_id,
            first["case_id"],
            second["case_id"],
            cd_l1,
            hd95,
        ])
    calibration_array = np.asarray(calibration_metrics, dtype=np.float64)
    cd_threshold = max(0.01, 1.5 * float(np.quantile(calibration_array[:, 0], 0.99)))
    hd_threshold = max(0.03, 1.5 * float(np.quantile(calibration_array[:, 1], 0.99)))

    mug_representatives = []
    for skull_id, items in sorted(m2_by_skull.items()):
        item = min(items, key=lambda row: row["case_id"])
        mug_representatives.append((skull_id, item))
    protected_representatives = {}
    for dataset, grouped in protected_by_skull.items():
        protected_representatives[dataset] = [
            (skull_id, min(items, key=lambda row: row["case_id"]))
            for skull_id, items in sorted(grouped.items())
        ]

    all_entries = list(mug_representatives)
    for entries in protected_representatives.values():
        all_entries.extend(entries)
    descriptor_matrix = np.vstack(
        [representation(Path(item[1]["point_path"]))["descriptor"] for item in all_entries]
    )
    median = np.median(descriptor_matrix, axis=0)
    mad = np.median(np.abs(descriptor_matrix - median), axis=0) * 1.4826
    scale = np.maximum(mad, 1e-6)

    candidate_rows: List[List[Any]] = [[
        "protected_dataset", "mug_skull_id", "mug_case_id",
        "protected_skull_id", "protected_case_id", "descriptor_rank",
        "descriptor_distance", "symmetric_cd_l1_normalized",
        "symmetric_hd95_normalized", "suspect_near_duplicate",
    ]]
    suspects = []
    shortlist_count = int(
        protocol["candidate_screen"]["nearest_protected_per_mug_skull"]
    )
    pair_jobs = []
    for dataset, protected in protected_representatives.items():
        protected_descriptors = np.vstack([
            representation(Path(item[1]["point_path"]))["descriptor"]
            for item in protected
        ])
        protected_scaled = (protected_descriptors - median) / scale
        for mug_skull_id, mug_item in mug_representatives:
            mug_rep = representation(Path(mug_item["point_path"]))
            mug_scaled = (mug_rep["descriptor"] - median) / scale
            distances = np.linalg.norm(protected_scaled - mug_scaled, axis=1)
            nearest = np.argsort(distances)[:shortlist_count]
            for rank, index in enumerate(nearest, 1):
                protected_skull_id, protected_item = protected[int(index)]
                pair_jobs.append((
                    dataset, mug_skull_id, mug_item, protected_skull_id,
                    protected_item, rank, float(distances[index]),
                ))
    for job in tqdm(pair_jobs, desc="Audit protected near duplicates"):
        (
            dataset,
            mug_skull_id,
            mug_item,
            protected_skull_id,
            protected_item,
            rank,
            descriptor_distance,
        ) = job
        mug_rep = representation(Path(mug_item["point_path"]))
        protected_rep = representation(Path(protected_item["point_path"]))
        cd_l1, hd95 = aligned_distances(
            mug_rep["canonical"], protected_rep["canonical"]
        )
        suspect = cd_l1 <= cd_threshold and hd95 <= hd_threshold
        row = [
            dataset,
            mug_skull_id,
            mug_item["case_id"],
            protected_skull_id,
            protected_item["case_id"],
            rank,
            descriptor_distance,
            cd_l1,
            hd95,
            int(suspect),
        ]
        candidate_rows.append(row)
        if suspect:
            suspects.append(row)

    passed = not intersections and not suspects
    summary = {
        "audit_id": PROTOCOL_ID,
        "status": "passed" if passed else "blocked_suspected_overlap",
        "protocol_sha256": sha256_file(protocol_path),
        "m2_manifest_sha256": sha256_file(m2_manifest),
        "protected_manifest_sha256": {
            name: sha256_file(path) for name, path in protected_manifests.items()
        },
        "counts": {
            "mug_source_skulls": len(mug_representatives),
            "skullbreak_source_skulls": len(protected_representatives["skullbreak"]),
            "skullfix_source_skulls": len(protected_representatives["skullfix"]),
            "protected_fingerprints": len(protected_hash_labels),
            "exact_hash_intersections": len(intersections),
            "within_source_calibration_pairs": len(calibration_pairs),
            "cross_dataset_candidate_pairs": len(pair_jobs),
            "near_duplicate_suspects": len(suspects),
        },
        "thresholds": {
            "symmetric_cd_l1_normalized": cd_threshold,
            "symmetric_hd95_normalized": hd_threshold,
            "calibration_rule": "max(floor, 1.5 * within-source q99)",
        },
        "automatic_gate_passed": passed,
        "selection_inert": True,
        "model_predictions_used": False,
        "model_metrics_used": False,
        "protected_defect_or_implant_arrays_used": False,
        "mug_B_series_or_craniotomy_used": False,
        "training_unlocked": False,
    }
    report = f"""# MUG500+ M2 protected-overlap 审计\n\n> 本审计仅用于数据泄漏排查，不用于模型、loss、ordering、seed 或 query 规则选择。\n\n- MUG500+ source skull：{len(mug_representatives)}\n- SkullBreak protected source skull：{len(protected_representatives['skullbreak'])}\n- SkullFix protected source skull：{len(protected_representatives['skullfix'])}\n- exact hash intersection：{len(intersections)}\n- near-duplicate suspect：{len(suspects)}\n- CD threshold：{cd_threshold:.8f}\n- HD95 threshold：{hd_threshold:.8f}\n- 自动门控：{'通过' if passed else '未通过'}\n- 模型预测/指标访问：否\n- MUG500+ B-series/craniotomy 访问：否\n- D3 training：仍保持锁定，需继续冻结 100/25 数据协议\n"""
    files = {
        "protected_fingerprints.sha256": protected_fingerprints,
        "within_source_calibration.csv": csv_bytes(calibration_rows),
        "near_duplicate_candidates.csv": csv_bytes(candidate_rows),
        "exact_hash_intersections.csv": csv_bytes(exact_rows),
        "overlap_audit_summary.json": (
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
        "overlap_audit_report_zh.md": report.encode("utf-8"),
    }
    hashes = [
        f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)
    ]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    write_locked(files, args.output_dir.resolve())
    print(f"[gate] exact intersections={len(intersections)} suspects={len(suspects)}")
    print(f"[gate] CD={cd_threshold:.8f} HD95={hd_threshold:.8f}")
    print(f"[{'ok' if passed else 'blocked'}] protected-overlap automatic gate")
    print("[locked] D3 training remains disabled until the 100/25 data lock")


if __name__ == "__main__":
    main()
