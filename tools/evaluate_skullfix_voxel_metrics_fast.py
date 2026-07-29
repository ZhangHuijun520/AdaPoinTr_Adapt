#!/usr/bin/env python
"""Parallel, resumable voxel evaluation with legacy-equivalent metrics."""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, OrderedDict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.evaluation_statistics import (  # noqa: E402
    aggregate_rows_by_group,
    describe_rows,
    describe_rows_by_group,
    paired_comparisons,
)
from utils.skullfix_metrics import (  # noqa: E402
    normalized_to_world,
    point_rim_metrics,
    point_surface_metrics,
)
from utils.skullfix_voxel_metrics import (  # noqa: E402
    relative_volume_error,
    splat_world_points_to_mask,
    surface_world_points,
    volume_dice,
)


EVALUATOR_VERSION = "fast-voxel-v2.0"
CACHE_SCHEMA_VERSION = 1


def _implementation_sha256():
    digest = hashlib.sha256()
    for path in (
        Path(__file__).resolve(),
        REPO_ROOT / "utils" / "evaluation_statistics.py",
        REPO_ROOT / "utils" / "skullfix_metrics.py",
        REPO_ROOT / "utils" / "skullfix_voxel_metrics.py",
    ):
        digest.update(str(path.relative_to(REPO_ROOT)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


IMPLEMENTATION_SHA256 = _implementation_sha256()


def require_nrrd():
    try:
        import nrrd
    except ImportError as exc:
        raise ImportError("Install pynrrd before voxel evaluation") from exc
    return nrrd


def header_geometry(header):
    directions = np.asarray(
        header.get("space directions"), dtype=np.float64
    )
    origin = np.asarray(
        header.get("space origin", (0.0, 0.0, 0.0)),
        dtype=np.float64,
    )
    if directions.shape != (3, 3):
        raise ValueError("NRRD space directions must be 3x3")
    return directions, origin


def resolve_raw_path(raw_root, value):
    raw_root = Path(raw_root)
    path = Path(value)
    candidates = [path, raw_root / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Cannot resolve raw NRRD {value!r} below {raw_root}"
    )


def read_mask(path, threshold):
    nrrd = require_nrrd()
    volume, header = nrrd.read(str(path), index_order="F")
    return np.asarray(volume > threshold, dtype=bool), header


def prefixed(prefix, values):
    return {f"{prefix}_{key}": value for key, value in values.items()}


@dataclass(frozen=True)
class EvaluationOptions:
    threshold: float
    splat_radius_mm: float
    rim_band_mm: float
    tolerances_mm: tuple


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate cranial-implant predictions with metrics numerically "
            "equivalent to evaluate_skullfix_voxel_metrics.py."
        )
    )
    parser.add_argument("--prediction_manifest", required=True)
    parser.add_argument("--raw_root", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--splat_radius_mm", type=float, default=1.0)
    parser.add_argument("--rim_band_mm", type=float, default=2.0)
    parser.add_argument("--tolerances_mm", default="0.5,1.0,2.0")
    parser.add_argument("--bootstrap_samples", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=20260702)
    parser.add_argument("--dataset_label", default="SkullFix")
    parser.add_argument("--output_prefix", default="skullfix")
    parser.add_argument(
        "--num_workers",
        type=int,
        default=0,
        help=(
            "Parallel worker processes. Zero selects min(4, logical CPUs). "
            "Use 1 for sequential debugging."
        ),
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=0,
        help="Evaluate only the first N manifest rows; zero evaluates all.",
    )
    parser.add_argument(
        "--cache_dir",
        default=None,
        help="Per-case resume cache (default: OUT_DIR/.fast_voxel_cache).",
    )
    parser.add_argument(
        "--no_resume",
        action="store_true",
        help="Ignore valid cached cases while still refreshing the cache.",
    )
    return parser.parse_args()


def parse_tolerances(value):
    tolerances = tuple(
        float(item.strip())
        for item in str(value).split(",")
        if item.strip()
    )
    if not tolerances:
        raise ValueError("At least one tolerance is required")
    return tolerances


def mask_metrics_from_surfaces(
    prediction,
    reference,
    prediction_surface,
    reference_surface,
    tolerances_mm=(0.5, 1.0, 2.0),
):
    """Match mask_metric_dict while reusing pre-extracted surfaces."""

    surface = point_surface_metrics(
        prediction_surface,
        reference_surface,
        tolerances_mm=tolerances_mm,
    )
    rve = relative_volume_error(prediction, reference)
    values = {
        "dsc": volume_dice(prediction, reference),
        "rve": rve,
        "absolute_rve": abs(rve),
        "surface_assd_mm": surface.assd_mm,
        "surface_hd95_mm": surface.hd95_mm,
    }
    values.update(
        {
            f"surface_dice_at_{tolerance:g}mm": value
            for tolerance, value in surface.nsd.items()
        }
    )
    return values


def voxel_metrics_from_masks(
    prediction_mask,
    complete,
    defective,
    implant,
    directions,
    origin,
    rim_band_mm=2.0,
    tolerances_mm=(0.5, 1.0, 2.0),
    raw_surfaces=None,
):
    """Compute the legacy metric row with each unique surface extracted once."""

    raw_surfaces = raw_surfaces or {}
    complete_surface = raw_surfaces.get("complete")
    if complete_surface is None:
        complete_surface = surface_world_points(
            complete, directions, origin
        )
    defective_surface = raw_surfaces.get("defective")
    if defective_surface is None:
        defective_surface = surface_world_points(
            defective, directions, origin
        )
    implant_surface = raw_surfaces.get("implant")
    if implant_surface is None:
        implant_surface = surface_world_points(
            implant, directions, origin
        )

    prediction_surface = surface_world_points(
        prediction_mask, directions, origin
    )
    final_mask = defective | prediction_mask
    final_surface = surface_world_points(final_mask, directions, origin)

    values = {}
    values.update(
        prefixed(
            "implant",
            mask_metrics_from_surfaces(
                prediction_mask,
                implant,
                prediction_surface,
                implant_surface,
                tolerances_mm=tolerances_mm,
            ),
        )
    )
    values.update(
        prefixed(
            "final",
            mask_metrics_from_surfaces(
                final_mask,
                complete,
                final_surface,
                complete_surface,
                tolerances_mm=tolerances_mm,
            ),
        )
    )
    values.update(
        prefixed(
            "input",
            mask_metrics_from_surfaces(
                defective,
                complete,
                defective_surface,
                complete_surface,
                tolerances_mm=tolerances_mm,
            ),
        )
    )
    rim = point_rim_metrics(
        prediction_surface,
        implant_surface,
        defective_surface,
        rim_band_mm=rim_band_mm,
        tolerances_mm=tolerances_mm,
    )
    values.update(prefixed("rim", rim.as_dict()))
    return values


def _load_raw_entry(
    raw_path,
    threshold,
    raw_cache,
    cacheable_paths,
):
    key = (str(Path(raw_path).resolve()), float(threshold))
    entry = raw_cache.get(key)
    if entry is not None:
        return entry, True
    mask, header = read_mask(raw_path, threshold)
    entry = {
        "mask": mask,
        "header": header,
        "surface": None,
    }
    if key[0] in cacheable_paths:
        raw_cache[key] = entry
    return entry, False


def _entry_surface(entry, directions, origin):
    if entry["surface"] is None:
        entry["surface"] = surface_world_points(
            entry["mask"], directions, origin
        )
    return entry["surface"]


def _evaluate_record(
    index,
    record,
    prediction_root,
    raw_root,
    options,
    raw_cache,
    cacheable_paths,
):
    started = time.perf_counter()
    prediction_started = time.perf_counter()
    prediction_path = Path(prediction_root) / record["prediction_path"]
    with np.load(prediction_path, allow_pickle=False) as payload:
        prediction_normalized = payload["prediction_implant"]
        centroid = payload["centroid"]
        scale = float(payload["scale"])
    prediction_world = normalized_to_world(
        prediction_normalized,
        centroid,
        scale,
    )
    prediction_io_seconds = time.perf_counter() - prediction_started

    raw_started = time.perf_counter()
    entries = {}
    raw_cache_hits = 0
    for role in ("complete", "defective", "implant"):
        raw_path = resolve_raw_path(raw_root, record["raw"][role])
        entries[role], cache_hit = _load_raw_entry(
            raw_path,
            options.threshold,
            raw_cache,
            cacheable_paths,
        )
        raw_cache_hits += int(cache_hit)
    raw_io_seconds = time.perf_counter() - raw_started

    directions, origin = header_geometry(entries["complete"]["header"])
    for role in ("defective", "implant"):
        role_directions, role_origin = header_geometry(
            entries[role]["header"]
        )
        if entries[role]["mask"].shape != entries["complete"]["mask"].shape:
            raise ValueError(
                f"{record['case_id']}: mismatched {role} shape"
            )
        if not np.allclose(role_directions, directions, atol=1e-5):
            raise ValueError(
                f"{record['case_id']}: mismatched {role} directions"
            )
        if not np.allclose(role_origin, origin, atol=1e-4):
            raise ValueError(
                f"{record['case_id']}: mismatched {role} origin"
            )

    splat_started = time.perf_counter()
    prediction_mask = splat_world_points_to_mask(
        prediction_world,
        entries["complete"]["mask"].shape,
        directions,
        origin,
        radius_mm=options.splat_radius_mm,
    )
    splat_seconds = time.perf_counter() - splat_started

    metrics_started = time.perf_counter()
    raw_surfaces = {
        role: _entry_surface(entry, directions, origin)
        for role, entry in entries.items()
    }
    metric_values = voxel_metrics_from_masks(
        prediction_mask,
        entries["complete"]["mask"],
        entries["defective"]["mask"],
        entries["implant"]["mask"],
        directions,
        origin,
        rim_band_mm=options.rim_band_mm,
        tolerances_mm=options.tolerances_mm,
        raw_surfaces=raw_surfaces,
    )
    metrics_seconds = time.perf_counter() - metrics_started

    row = {
        "case_id": record["case_id"],
        "split": record["split"],
        "skull_id": record.get("skull_id", record["case_id"]),
        "defect_type": record.get("defect_type", ""),
    }
    row.update(metric_values)
    timing = {
        "case_id": record["case_id"],
        "cached": False,
        "prediction_io_seconds": prediction_io_seconds,
        "raw_io_seconds": raw_io_seconds,
        "splat_seconds": splat_seconds,
        "metrics_seconds": metrics_seconds,
        "total_seconds": time.perf_counter() - started,
        "raw_cache_hits": raw_cache_hits,
    }
    return index, row, timing


def _evaluate_group(group, prediction_root, raw_root, options):
    path_counts = Counter(
        str(resolve_raw_path(raw_root, record["raw"][role]).resolve())
        for _, record in group
        for role in ("complete", "defective", "implant")
    )
    cacheable_paths = {
        path for path, count in path_counts.items() if count > 1
    }
    raw_cache = {}
    return [
        _evaluate_record(
            index,
            record,
            prediction_root,
            raw_root,
            options,
            raw_cache,
            cacheable_paths,
        )
        for index, record in group
    ]


def _file_identity(path):
    path = Path(path).resolve()
    stat = path.stat()
    return {
        "path": str(path),
        "size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _record_signature(
    index,
    record,
    prediction_root,
    raw_root,
    options,
):
    prediction_path = Path(prediction_root) / record["prediction_path"]
    raw_paths = {
        role: resolve_raw_path(raw_root, record["raw"][role])
        for role in ("complete", "defective", "implant")
    }
    payload = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "index": int(index),
        "record": record,
        "options": asdict(options),
        "prediction": _file_identity(prediction_path),
        "raw": {
            role: _file_identity(path)
            for role, path in sorted(raw_paths.items())
        },
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_case_name(case_id):
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(case_id))
    return value.strip("._") or "case"


def _cache_path(cache_dir, index, case_id):
    return Path(cache_dir) / (
        f"{int(index):06d}_{_safe_case_name(case_id)}.json"
    )


def _load_cached_row(path, signature):
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return None
    if payload.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
        return None
    if payload.get("signature") != signature:
        return None
    row = payload.get("row")
    return row if isinstance(row, dict) else None


def _write_cached_row(path, signature, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "signature": signature,
        "row": row,
    }
    temporary = path.with_name(
        f".{path.name}.tmp-{os.getpid()}"
    )
    temporary.write_text(
        json.dumps(payload, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _group_pending_records(pending):
    grouped = OrderedDict()
    for index, record in pending:
        skull_id = str(record.get("skull_id", record["case_id"]))
        grouped.setdefault(skull_id, []).append((index, record))
    return list(grouped.values())


def _resolved_worker_count(requested, group_count):
    if requested < 0:
        raise ValueError("num_workers must be non-negative")
    if requested == 0:
        requested = min(4, os.cpu_count() or 1)
    if group_count == 0:
        return 1
    return max(1, min(int(requested), int(group_count)))


def evaluate_records(
    records,
    prediction_root,
    raw_root,
    options,
    cache_dir,
    num_workers=0,
    resume=True,
):
    """Evaluate records and preserve their original manifest order."""

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    rows = [None] * len(records)
    timings = [None] * len(records)
    signatures = {}
    pending = []
    cached_cases = 0

    signature_progress = tqdm(
        enumerate(records),
        total=len(records),
        desc="Index inputs",
        unit="case",
        dynamic_ncols=True,
    )
    for index, record in signature_progress:
        signature = _record_signature(
            index,
            record,
            prediction_root,
            raw_root,
            options,
        )
        signatures[index] = signature
        path = _cache_path(cache_dir, index, record["case_id"])
        cached_row = (
            _load_cached_row(path, signature)
            if resume
            else None
        )
        if cached_row is None:
            pending.append((index, record))
            continue
        rows[index] = cached_row
        timings[index] = {
            "case_id": record["case_id"],
            "cached": True,
        }
        cached_cases += 1

    groups = _group_pending_records(pending)
    workers = _resolved_worker_count(num_workers, len(groups))
    progress = tqdm(
        total=len(records),
        initial=cached_cases,
        desc=f"Voxel v2 ({workers} workers)",
        unit="case",
        dynamic_ncols=True,
    )

    def accept_results(results):
        for index, row, timing in results:
            rows[index] = row
            timings[index] = timing
            path = _cache_path(
                cache_dir,
                index,
                records[index]["case_id"],
            )
            _write_cached_row(path, signatures[index], row)
            progress.set_postfix_str(str(row["case_id"]), refresh=False)
            progress.update(1)

    if workers == 1:
        for group in groups:
            accept_results(
                _evaluate_group(
                    group,
                    str(prediction_root),
                    str(raw_root),
                    options,
                )
            )
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _evaluate_group,
                    group,
                    str(prediction_root),
                    str(raw_root),
                    options,
                ): group
                for group in groups
            }
            try:
                for future in as_completed(futures):
                    accept_results(future.result())
            except BaseException:
                for future in futures:
                    future.cancel()
                raise
    progress.close()

    if any(row is None for row in rows):
        raise RuntimeError("Evaluation finished with missing rows")
    return rows, timings, {
        "cached_cases": cached_cases,
        "computed_cases": len(records) - cached_cases,
        "worker_processes": workers,
        "worker_groups": len(groups),
    }


def write_outputs(rows, args, tolerances, execution):
    """Write the same CSV and summary schema as the legacy evaluator."""

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{args.output_prefix}_voxel_per_sample.csv"
    summary_path = out_dir / f"{args.output_prefix}_voxel_summary.json"
    timing_path = out_dir / f"{args.output_prefix}_voxel_timing.json"

    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    metric_keys = [
        key
        for key in rows[0]
        if key not in {"case_id", "split", "skull_id", "defect_type"}
    ] if rows else []
    statistics = describe_rows(
        rows,
        metric_keys,
        bootstrap_samples=args.bootstrap_samples,
        confidence=args.confidence,
        seed=args.seed,
    )
    skull_rows = aggregate_rows_by_group(rows, "skull_id", metric_keys)
    summary = {
        "dataset": args.dataset_label,
        "protocol": {
            "prediction_representation": "fixed-radius surface splatting",
            "splat_radius_mm": args.splat_radius_mm,
            "rim_band_mm": args.rim_band_mm,
            "surface_dice_weighting": "surface-voxel count",
            "tolerances_mm": tolerances,
            "warning": (
                "DSC depends on point-to-voxel splatting and is not directly "
                "comparable to a native voxel-output model unless the same "
                "conversion is applied."
            ),
        },
        "num_samples": len(rows),
        "num_skulls": len(skull_rows),
        "mean": {
            key: values.get("mean")
            for key, values in statistics.items()
        },
        "statistics": statistics,
        "statistics_case_level": statistics,
        "statistics_skull_macro": describe_rows(
            skull_rows,
            metric_keys,
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed + 20000,
        ),
        "by_defect_type": describe_rows_by_group(
            rows,
            "defect_type",
            metric_keys,
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed + 30000,
        ),
        "paired_final_vs_input": paired_comparisons(
            rows,
            candidate_prefix="final",
            baseline_prefix="input",
            bootstrap_samples=args.bootstrap_samples,
            confidence=args.confidence,
            seed=args.seed + 10000,
        ),
        "per_sample_csv": str(csv_path),
    }
    summary_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    timing_path.write_text(
        json.dumps(execution, indent=2) + "\n",
        encoding="utf-8",
    )
    return csv_path, summary_path, timing_path


def main():
    args = parse_args()
    tolerances = parse_tolerances(args.tolerances_mm)
    options = EvaluationOptions(
        threshold=float(args.threshold),
        splat_radius_mm=float(args.splat_radius_mm),
        rim_band_mm=float(args.rim_band_mm),
        tolerances_mm=tolerances,
    )
    manifest_path = Path(args.prediction_manifest)
    prediction_root = manifest_path.parent
    records = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.max_samples < 0:
        raise ValueError("max_samples must be non-negative")
    if args.max_samples:
        records = records[:args.max_samples]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = (
        Path(args.cache_dir)
        if args.cache_dir
        else out_dir / ".fast_voxel_cache"
    )

    wall_started = time.perf_counter()
    rows, timings, execution = evaluate_records(
        records,
        prediction_root,
        args.raw_root,
        options,
        cache_dir,
        num_workers=args.num_workers,
        resume=not args.no_resume,
    )
    execution.update(
        {
            "evaluator_version": EVALUATOR_VERSION,
            "manifest": str(manifest_path),
            "cache_dir": str(cache_dir),
            "resume_enabled": not args.no_resume,
            "wall_seconds_before_summary": (
                time.perf_counter() - wall_started
            ),
            "per_case": timings,
        }
    )
    summary_started = time.perf_counter()
    csv_path, summary_path, timing_path = write_outputs(
        rows,
        args,
        tolerances,
        execution,
    )
    execution["summary_seconds"] = time.perf_counter() - summary_started
    execution["wall_seconds_total"] = time.perf_counter() - wall_started
    timing_path.write_text(
        json.dumps(execution, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[saved] {csv_path}")
    print(f"[saved] {summary_path}")
    print(f"[saved] {timing_path}")
    print(
        "[done] "
        f"computed={execution['computed_cases']} "
        f"cached={execution['cached_cases']} "
        f"workers={execution['worker_processes']}"
    )


if __name__ == "__main__":
    main()
