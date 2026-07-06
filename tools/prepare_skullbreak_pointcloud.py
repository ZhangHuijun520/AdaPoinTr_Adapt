#!/usr/bin/env python
"""Convert grouped SkullBreak NRRD volumes into implant point-cloud cases."""

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from prepare_skullfix_pointcloud import (  # noqa: E402
    check_geometry,
    flat_indices_to_world,
    header_geometry,
    parse_split_spec,
    read_binary_volume,
    relative_or_absolute,
    sample_surface,
    sha256_file,
    stable_rng,
    surface_flat_indices,
    surface_normalization,
    triplet_metrics,
    write_json,
)


DEFECT_TYPES = (
    "bilateral",
    "frontoorbital",
    "parietotemporal",
    "random_1",
    "random_2",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Convert the official SkullBreak training and evaluation trees "
            "to grouped, normalized point-cloud NPZ files."
        )
    )
    parser.add_argument("--training_root", type=Path, required=True)
    parser.add_argument(
        "--evaluation_root",
        type=Path,
        help=(
            "Optional official evaluation tree. Omit only for Gate 0-3 "
            "development and pass --expected_test_skulls 0."
        ),
    )
    parser.add_argument("--output_root", type=Path, required=True)
    parser.add_argument("--n_complete", type=int, default=8192)
    parser.add_argument("--n_partial", type=int, default=8192)
    parser.add_argument("--n_implant", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20260703)
    parser.add_argument(
        "--gate_split",
        default="0.8,0.1,0.1",
        help="Group-level train/val/test split within official training skulls.",
    )
    parser.add_argument(
        "--monitor_skulls",
        type=int,
        default=10,
        help=(
            "Official-training skulls used only for full-run monitoring. "
            "They remain part of the full training set."
        ),
    )
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--min_triplet_iou", type=float, default=0.80)
    parser.add_argument("--expected_train_skulls", type=int, default=114)
    parser.add_argument("--expected_test_skulls", type=int, default=20)
    parser.add_argument(
        "--strict_geometry",
        action="store_true",
        help="Fail when complete, defective, and implant geometry differs.",
    )
    parser.add_argument(
        "--strict_quality",
        action="store_true",
        help="Fail when implant/missing IoU is below --min_triplet_iou.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help=(
            "Number of skulls converted in parallel. Each worker can use "
            "substantial RAM for 512^3 volumes; start with 2."
        ),
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def normalize_skull_id(path):
    value = path.stem.lower()
    normalized = "".join(
        character if character.isalnum() else "_"
        for character in value
    ).strip("_")
    if not normalized:
        raise ValueError(f"Cannot derive skull id from {path}")
    return normalized


def find_dataset_root(path):
    path = path.expanduser().resolve()
    candidates = []
    search = [path] + [item for item in path.rglob("*") if item.is_dir()]
    for candidate in search:
        if all(
            (candidate / role).is_dir()
            for role in ("complete_skull", "defective_skull", "implant")
        ):
            candidates.append(candidate)
    unique = sorted(set(candidates))
    if len(unique) != 1:
        rendered = ", ".join(str(item) for item in unique) or "none"
        raise RuntimeError(
            f"Expected one SkullBreak dataset root below {path}, found {rendered}"
        )
    return unique[0]


def resolve_matching_file(role_root, defect_type, relative_complete):
    path = role_root / defect_type / relative_complete
    if path.is_file():
        return path.resolve()

    matches = list((role_root / defect_type).rglob(relative_complete.name))
    if len(matches) != 1:
        rendered = ", ".join(str(item) for item in matches) or "none"
        raise FileNotFoundError(
            f"Expected one match for {relative_complete.name} in "
            f"{role_root / defect_type}, found {rendered}"
        )
    return matches[0].resolve()


def index_skulls(dataset_root, official_split):
    complete_root = dataset_root / "complete_skull"
    defective_root = dataset_root / "defective_skull"
    implant_root = dataset_root / "implant"
    complete_files = sorted(complete_root.rglob("*.nrrd"))
    if not complete_files:
        raise ValueError(f"No complete SkullBreak NRRD files in {complete_root}")

    groups = []
    seen_ids = set()
    for complete in complete_files:
        source_skull_id = normalize_skull_id(complete)
        if source_skull_id in seen_ids:
            raise ValueError(
                f"Duplicate {official_split} skull id {source_skull_id!r}"
            )
        seen_ids.add(source_skull_id)
        relative = complete.relative_to(complete_root)
        cases = []
        for defect_type in DEFECT_TYPES:
            cases.append(
                {
                    "defect_type": defect_type,
                    "defective": resolve_matching_file(
                        defective_root, defect_type, relative
                    ),
                    "implant": resolve_matching_file(
                        implant_root, defect_type, relative
                    ),
                }
            )
        groups.append(
            {
                "official_split": official_split,
                "source_skull_id": source_skull_id,
                "skull_id": f"{official_split}:{source_skull_id}",
                "complete": complete.resolve(),
                "cases": cases,
            }
        )
    return groups


def assign_group_splits(skull_ids, split_spec, seed):
    counts = parse_split_spec(split_spec, len(skull_ids))
    rng = np.random.RandomState(seed)
    shuffled = list(skull_ids)
    rng.shuffle(shuffled)
    assignments = {}
    offset = 0
    for split_name in ("train", "val", "test"):
        count = counts[split_name]
        for skull_id in shuffled[offset : offset + count]:
            assignments[skull_id] = split_name
        offset += count
    return assignments, counts, shuffled


def binary_mask_sha256(volume):
    digest = hashlib.sha256()
    digest.update(np.asarray(volume.shape, dtype=np.int32).tobytes())
    flattened = volume.ravel(order="C")
    chunk_size = 8 * 1024 * 1024
    for start in range(0, flattened.size, chunk_size):
        digest.update(np.packbits(flattened[start : start + chunk_size]).tobytes())
    return digest.hexdigest()


def common_raw_root(training_root, evaluation_root):
    try:
        return Path(
            os.path.commonpath([str(training_root), str(evaluation_root)])
        )
    except ValueError:
        return None


def sample_role(
    flat_indices,
    volume_shape,
    directions,
    origin,
    count,
    centroid,
    scale,
    seed,
    case_id,
    role,
):
    return sample_surface(
        flat_indices,
        volume_shape,
        directions,
        origin,
        count,
        centroid,
        scale,
        stable_rng(seed, case_id, role),
    )


def process_group(args, group, gate_split, monitor_split, points_dir, raw_root):
    complete, complete_header = read_binary_volume(
        group["complete"], args.threshold
    )
    complete_surface = surface_flat_indices(complete)
    complete_directions, complete_origin = header_geometry(complete_header)
    complete_hash = binary_mask_sha256(complete)
    records = []

    for case in group["cases"]:
        defect_type = case["defect_type"]
        case_id = (
            f"{group['official_split']}__{group['source_skull_id']}"
            f"__{defect_type}"
        )
        output_path = points_dir / f"{case_id}.npz"
        if output_path.exists() and not args.overwrite:
            raise FileExistsError(
                f"{output_path} exists; pass --overwrite to replace it"
            )

        defective, defective_header = read_binary_volume(
            case["defective"], args.threshold
        )
        implant, implant_header = read_binary_volume(
            case["implant"], args.threshold
        )
        volumes = {
            "complete": complete,
            "defective": defective,
            "implant": implant,
        }
        headers = {
            "complete": complete_header,
            "defective": defective_header,
            "implant": implant_header,
        }
        directions, origin = check_geometry(
            case_id, volumes, headers, args.strict_geometry
        )
        if not np.allclose(directions, complete_directions, atol=1e-5):
            raise AssertionError("Unexpected complete geometry change")
        if not np.allclose(origin, complete_origin, atol=1e-4):
            raise AssertionError("Unexpected complete origin change")

        quality = triplet_metrics(complete, defective, implant)
        if quality["implant_missing_iou"] < args.min_triplet_iou:
            message = (
                f"{case_id}: implant/missing IoU "
                f"{quality['implant_missing_iou']:.4f} "
                f"< {args.min_triplet_iou:.4f}"
            )
            if args.strict_quality:
                raise ValueError(message)
            print(f"[warning] {message}", file=sys.stderr)

        defective_surface = surface_flat_indices(defective)
        implant_surface = surface_flat_indices(implant)
        centroid, scale = surface_normalization(
            defective_surface,
            defective.shape,
            directions,
            origin,
        )
        sampled = {
            "partial": sample_role(
                defective_surface,
                defective.shape,
                directions,
                origin,
                args.n_partial,
                centroid,
                scale,
                args.seed,
                case_id,
                "defective",
            ),
            "gt": sample_role(
                complete_surface,
                complete.shape,
                directions,
                origin,
                args.n_complete,
                centroid,
                scale,
                args.seed,
                case_id,
                "complete",
            ),
            "implant": sample_role(
                implant_surface,
                implant.shape,
                directions,
                origin,
                args.n_implant,
                centroid,
                scale,
                args.seed,
                case_id,
                "implant",
            ),
        }
        np.savez_compressed(
            output_path,
            partial=sampled["partial"],
            gt=sampled["gt"],
            implant=sampled["implant"],
            centroid=centroid.astype(np.float64),
            scale=np.asarray(scale, dtype=np.float64),
            voxel_shape=np.asarray(complete.shape, dtype=np.int32),
            space_directions=directions.astype(np.float64),
            space_origin=origin.astype(np.float64),
        )

        records.append(
            {
                "dataset": "SkullBreak",
                "case_id": case_id,
                "skull_id": group["skull_id"],
                "source_skull_id": group["source_skull_id"],
                "defect_type": defect_type,
                "split": group["official_split"],
                "official_split": group["official_split"],
                "gate_split": gate_split,
                "monitor_split": monitor_split,
                "point_path": f"points/{output_path.name}",
                "raw": {
                    "complete": relative_or_absolute(
                        group["complete"], raw_root
                    ),
                    "defective": relative_or_absolute(
                        case["defective"], raw_root
                    ),
                    "implant": relative_or_absolute(
                        case["implant"], raw_root
                    ),
                },
                "n_partial": args.n_partial,
                "n_complete": args.n_complete,
                "n_implant": args.n_implant,
                "normalization": {
                    "source": "defective_surface",
                    "centroid": centroid.tolist(),
                    "scale": float(scale),
                },
                "voxel_shape": list(complete.shape),
                "space_directions": directions.tolist(),
                "space_origin": origin.tolist(),
                "complete_mask_sha256": complete_hash,
                "quality": quality,
            }
        )
    return records


def process_group_task(task):
    (
        index,
        total,
        args,
        group,
        gate_split,
        monitor_split,
        points_dir,
        raw_root,
    ) = task
    records = process_group(
        args,
        group,
        gate_split,
        monitor_split,
        points_dir,
        raw_root,
    )
    return index, total, group["skull_id"], gate_split, records


def validate_official_counts(args, train_groups, test_groups):
    expected = (
        ("train", len(train_groups), args.expected_train_skulls),
        ("test", len(test_groups), args.expected_test_skulls),
    )
    for name, actual, target in expected:
        if target > 0 and actual != target:
            raise ValueError(
                f"Expected {target} official {name} skulls, found {actual}. "
                f"Pass --expected_{name}_skulls 0 only for a controlled subset."
            )


def main():
    args = parse_args()
    if min(args.n_complete, args.n_partial, args.n_implant) <= 0:
        raise ValueError("All point counts must be positive")
    if args.monitor_skulls < 0:
        raise ValueError("--monitor_skulls cannot be negative")
    if args.workers <= 0:
        raise ValueError("--workers must be positive")

    training_root = find_dataset_root(args.training_root)
    evaluation_root = (
        find_dataset_root(args.evaluation_root)
        if args.evaluation_root is not None
        else None
    )
    output_root = args.output_root.expanduser().resolve()
    train_groups = index_skulls(training_root, "train")
    test_groups = (
        index_skulls(evaluation_root, "test")
        if evaluation_root is not None
        else []
    )
    if evaluation_root is None and args.expected_test_skulls != 0:
        raise ValueError(
            "Without --evaluation_root, pass --expected_test_skulls 0. "
            "This produces development data only, not an official test set."
        )
    validate_official_counts(args, train_groups, test_groups)

    assignments, gate_counts, shuffled_train = assign_group_splits(
        [group["skull_id"] for group in train_groups],
        args.gate_split,
        args.seed,
    )
    monitor_candidates = [
        skull_id
        for skull_id in shuffled_train
        if assignments[skull_id] == "val"
    ]
    monitor_candidates.extend(
        skull_id
        for skull_id in shuffled_train
        if skull_id not in monitor_candidates
    )
    monitor_ids = set(monitor_candidates[: args.monitor_skulls])

    output_root.mkdir(parents=True, exist_ok=True)
    points_dir = output_root / "points"
    points_dir.mkdir(parents=True, exist_ok=True)
    raw_root = (
        common_raw_root(training_root, evaluation_root)
        if evaluation_root is not None
        else training_root
    )

    all_groups = train_groups + test_groups
    tasks = []
    for index, group in enumerate(all_groups, start=1):
        official_split = group["official_split"]
        gate_split = (
            assignments[group["skull_id"]]
            if official_split == "train"
            else "official_test"
        )
        monitor_split = (
            "monitor" if group["skull_id"] in monitor_ids else None
        )
        tasks.append(
            (
                index,
                len(all_groups),
                args,
                group,
                gate_split,
                monitor_split,
                points_dir,
                raw_root,
            )
        )

    all_records = []
    if args.workers == 1:
        for task in tasks:
            index, total, _, group, gate_split, _, _, _ = task
            print(
                f"[{index:03d}/{total:03d}] "
                f"skull={group['skull_id']} "
                f"official={group['official_split']} gate={gate_split}",
                flush=True,
            )
            all_records.extend(process_group_task(task)[-1])
    else:
        print(
            f"[parallel] workers={args.workers} skulls={len(tasks)}",
            flush=True,
        )
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(process_group_task, task) for task in tasks]
            completed = 0
            for future in as_completed(futures):
                index, total, skull_id, gate_split, records = future.result()
                all_records.extend(records)
                completed += 1
                print(
                    f"[done {completed:03d}/{total:03d}] "
                    f"source_index={index:03d} skull={skull_id} "
                    f"gate={gate_split}",
                    flush=True,
                )

    train_hashes = {
        record["complete_mask_sha256"]
        for record in all_records
        if record["official_split"] == "train"
    }
    test_hashes = {
        record["complete_mask_sha256"]
        for record in all_records
        if record["official_split"] == "test"
    }
    overlap = train_hashes.intersection(test_hashes)
    if overlap:
        raise ValueError(
            "Detected identical complete-skull masks across official "
            f"train/test: {sorted(overlap)}"
        )

    manifest_path = output_root / "manifest.jsonl"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        for record in sorted(
            all_records,
            key=lambda item: (
                item["official_split"],
                item["source_skull_id"],
                item["defect_type"],
            ),
        ):
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    checksums_path = output_root / "SHA256SUMS"
    with open(
        checksums_path, "w", encoding="ascii", newline="\n"
    ) as handle:
        for record in sorted(all_records, key=lambda item: item["case_id"]):
            handle.write(
                f"{sha256_file(output_root / record['point_path'])}  "
                f"{record['point_path']}\n"
            )

    skull_counts = Counter(
        (record["official_split"], record["skull_id"])
        for record in all_records
    )
    if any(count != len(DEFECT_TYPES) for count in skull_counts.values()):
        raise AssertionError("Every SkullBreak skull must have five cases")

    summary = {
        "dataset": "SkullBreak",
        "training_root": str(training_root),
        "evaluation_root": (
            str(evaluation_root) if evaluation_root is not None else None
        ),
        "official": {
            "train_skulls": len(train_groups),
            "train_cases": len(train_groups) * len(DEFECT_TYPES),
            "test_skulls": len(test_groups),
            "test_cases": len(test_groups) * len(DEFECT_TYPES),
        },
        "gate_split_skulls": gate_counts,
        "gate_split_cases": {
            key: value * len(DEFECT_TYPES)
            for key, value in gate_counts.items()
        },
        "monitor_skulls": len(monitor_ids),
        "monitor_cases": len(monitor_ids) * len(DEFECT_TYPES),
        "defect_types": list(DEFECT_TYPES),
        "seed": args.seed,
        "point_cloud": {
            "partial": args.n_partial,
            "complete": args.n_complete,
            "implant": args.n_implant,
        },
        "normalization": "shared defective-surface centroid and max radius",
        "manifest": str(manifest_path),
        "checksums": str(checksums_path),
        "train_test_complete_hash_overlap": 0,
        "quality": {
            "min_implant_missing_iou": min(
                record["quality"]["implant_missing_iou"]
                for record in all_records
            ),
            "mean_implant_missing_iou": float(
                np.mean(
                    [
                        record["quality"]["implant_missing_iou"]
                        for record in all_records
                    ]
                )
            ),
        },
    }
    write_json(output_root / "summary.json", summary)
    write_json(
        output_root / "group_splits.json",
        {
            "gate": {
                split: sorted(
                    skull_id
                    for skull_id, assigned in assignments.items()
                    if assigned == split
                )
                for split in ("train", "val", "test")
            },
            "monitor": sorted(monitor_ids),
            "official_test": sorted(
                group["skull_id"] for group in test_groups
            ),
        },
    )
    print(f"[ok] wrote {len(all_records)} cases to {output_root}")
    print(f"[ok] manifest: {manifest_path}")


if __name__ == "__main__":
    main()
