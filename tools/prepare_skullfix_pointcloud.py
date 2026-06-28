#!/usr/bin/env python
"""Convert paired SkullFix NRRD volumes into normalized point-cloud samples."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage


ROLE_ALIASES = {
    "complete": ("complete", "complete_skull", "healthy", "original", "ground_truth", "gt"),
    "defective": ("defective", "defective_skull", "defected", "incomplete", "input"),
    "implant": ("implant", "implants", "bone_flap", "boneflap", "removed"),
}
CASE_NOISE_TOKENS = {
    "complete",
    "healthy",
    "original",
    "ground",
    "truth",
    "gt",
    "defective",
    "defected",
    "incomplete",
    "input",
    "implant",
    "implants",
    "bone",
    "flap",
    "removed",
    "skull",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Pair SkullFix complete/defective/implant NRRD files, sample their "
            "surfaces in physical coordinates, and normalize every triplet with "
            "statistics computed from the complete skull."
        )
    )
    parser.add_argument("--input_root", type=Path, required=True)
    parser.add_argument("--output_root", type=Path, required=True)
    parser.add_argument("--complete_dir", type=Path)
    parser.add_argument("--defective_dir", type=Path)
    parser.add_argument("--implant_dir", type=Path)
    parser.add_argument("--n_complete", type=int, default=8192)
    parser.add_argument("--n_partial", type=int, default=8192)
    parser.add_argument("--n_implant", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20260628)
    parser.add_argument(
        "--normalization_source",
        choices=("defective", "complete"),
        default="defective",
        help=(
            "Surface used to compute the shared centroid and scale. "
            "Use defective for leakage-free inference."
        ),
    )
    parser.add_argument(
        "--split",
        default="80,10,10",
        help="Train/val/test counts or ratios, for example 80,10,10 or 0.8,0.1,0.1.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="NRRD values greater than this threshold are treated as occupied.",
    )
    parser.add_argument(
        "--min_triplet_iou",
        type=float,
        default=0.90,
        help="Warn when implant vs. (complete - defective) IoU is below this value.",
    )
    parser.add_argument(
        "--strict_geometry",
        action="store_true",
        help="Fail instead of warning when triplet geometry or IoU checks fail.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def require_nrrd():
    try:
        import nrrd
    except ImportError as exc:
        raise RuntimeError(
            "pynrrd is required for SkullFix conversion. Install it with "
            "`python -m pip install pynrrd`."
        ) from exc
    return nrrd


def normalize_token(value):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def canonical_case_id(path, role_root=None):
    relative_path = path.relative_to(role_root) if role_root is not None else path
    parts = list(relative_path.parts)
    parts[-1] = Path(parts[-1]).stem
    tokens = []
    for part in parts:
        tokens.extend(
            token
            for token in normalize_token(part).split("_")
            if token and token not in CASE_NOISE_TOKENS
        )
    case_id = "_".join(tokens)
    if not case_id:
        raise ValueError(f"Could not derive a case id from filename: {path.name}")
    return case_id


def find_role_directory(input_root, role, explicit_path):
    if explicit_path is not None:
        directory = explicit_path.expanduser()
        if not directory.is_absolute():
            directory = input_root / directory
        directory = directory.resolve()
        if not directory.is_dir():
            raise FileNotFoundError(f"{role} directory not found: {directory}")
        return directory

    aliases = {normalize_token(alias) for alias in ROLE_ALIASES[role]}
    candidates = []
    for directory in [input_root] + [p for p in input_root.rglob("*") if p.is_dir()]:
        normalized_name = normalize_token(directory.name)
        if not any(
            normalized_name == alias
            or normalized_name.startswith(f"{alias}_")
            or normalized_name.endswith(f"_{alias}")
            for alias in aliases
        ):
            continue
        count = sum(1 for _ in directory.rglob("*.nrrd"))
        if count:
            candidates.append((count, directory))

    if len(candidates) != 1:
        rendered = ", ".join(f"{path} ({count})" for count, path in candidates) or "none"
        raise RuntimeError(
            f"Expected exactly one auto-detected {role} directory, found: {rendered}. "
            f"Pass --{role}_dir explicitly."
        )
    return candidates[0][1]


def index_role_files(directory, role):
    indexed = {}
    for path in sorted(directory.rglob("*.nrrd")):
        case_id = canonical_case_id(path, directory)
        if case_id in indexed:
            raise ValueError(
                f"Duplicate {role} case id '{case_id}': "
                f"{indexed[case_id]} and {path}"
            )
        indexed[case_id] = path.resolve()
    if not indexed:
        raise ValueError(f"No .nrrd files found in {directory}")
    return indexed


def pair_triplets(role_files):
    all_ids = set().union(*(set(files) for files in role_files.values()))
    missing = {}
    for case_id in sorted(all_ids):
        absent = [role for role, files in role_files.items() if case_id not in files]
        if absent:
            missing[case_id] = absent
    if missing:
        preview = "\n".join(
            f"  {case_id}: missing {', '.join(roles)}"
            for case_id, roles in list(missing.items())[:20]
        )
        raise ValueError(
            f"Found {len(missing)} incomplete SkullFix pairings:\n{preview}"
        )
    return [
        {
            "case_id": case_id,
            **{role: files[case_id] for role, files in role_files.items()},
        }
        for case_id in sorted(all_ids)
    ]


def parse_split_spec(spec, n_cases):
    values = [float(value.strip()) for value in spec.split(",")]
    if len(values) != 3 or any(value < 0 for value in values):
        raise ValueError("--split must contain three non-negative values")

    if all(value.is_integer() for value in values) and int(sum(values)) == n_cases:
        counts = [int(value) for value in values]
    else:
        total = sum(values)
        if total <= 0:
            raise ValueError("--split values must sum to a positive number")
        raw = [value / total * n_cases for value in values]
        counts = [int(np.floor(value)) for value in raw]
        for index in np.argsort([value - base for value, base in zip(raw, counts)])[::-1]:
            if sum(counts) == n_cases:
                break
            counts[int(index)] += 1
    if sum(counts) != n_cases:
        raise AssertionError("Internal split count error")
    return dict(zip(("train", "val", "test"), counts))


def assign_splits(case_ids, split_counts, seed):
    rng = np.random.RandomState(seed)
    shuffled = list(case_ids)
    rng.shuffle(shuffled)
    assignments = {}
    offset = 0
    for split_name in ("train", "val", "test"):
        count = split_counts[split_name]
        for case_id in shuffled[offset : offset + count]:
            assignments[case_id] = split_name
        offset += count
    return assignments


def read_binary_volume(path, threshold):
    nrrd = require_nrrd()
    volume, header = nrrd.read(str(path), index_order="F")
    if volume.ndim != 3:
        raise ValueError(f"{path}: expected a 3D volume, got shape {volume.shape}")
    return np.asarray(volume > threshold, dtype=bool), header


def header_geometry(header):
    directions = header.get("space directions")
    if directions is not None:
        try:
            directions = np.asarray(directions, dtype=np.float64)
        except (TypeError, ValueError):
            directions = None
    if directions is None or directions.shape != (3, 3) or not np.isfinite(directions).all():
        spacings = header.get("spacings", (1.0, 1.0, 1.0))
        spacings = np.asarray(spacings, dtype=np.float64)
        if spacings.shape != (3,) or not np.isfinite(spacings).all():
            spacings = np.ones(3, dtype=np.float64)
        directions = np.diag(spacings)

    origin = header.get("space origin", (0.0, 0.0, 0.0))
    origin = np.asarray(origin, dtype=np.float64)
    if origin.shape != (3,) or not np.isfinite(origin).all():
        origin = np.zeros(3, dtype=np.float64)
    return directions, origin


def check_geometry(case_id, volumes, headers, strict):
    reference_role = "complete"
    reference_shape = volumes[reference_role].shape
    reference_directions, reference_origin = header_geometry(headers[reference_role])
    problems = []

    for role in ("defective", "implant"):
        if volumes[role].shape != reference_shape:
            raise ValueError(
                f"{case_id}: {role} shape {volumes[role].shape} "
                f"!= complete shape {reference_shape}"
            )
        directions, origin = header_geometry(headers[role])
        if not np.allclose(directions, reference_directions, atol=1e-5):
            problems.append(f"{role} space directions differ from complete")
        if not np.allclose(origin, reference_origin, atol=1e-4):
            problems.append(f"{role} space origin differs from complete")

    if problems:
        message = f"{case_id}: " + "; ".join(problems)
        if strict:
            raise ValueError(message)
        print(f"[warning] {message}", file=sys.stderr)
    return reference_directions, reference_origin


def surface_flat_indices(volume):
    structure = ndimage.generate_binary_structure(3, 1)
    eroded = ndimage.binary_erosion(volume, structure=structure, border_value=0)
    boundary = volume & ~eroded
    flat_indices = np.flatnonzero(boundary.ravel(order="C"))
    if flat_indices.size == 0:
        raise ValueError("Binary volume has no occupied surface voxels")
    return flat_indices


def flat_indices_to_world(flat_indices, shape, directions, origin):
    coordinates = np.column_stack(np.unravel_index(flat_indices, shape, order="C"))
    return origin + coordinates.astype(np.float64) @ directions


def surface_normalization(flat_indices, shape, directions, origin):
    chunk_size = 250000
    coordinate_sum = np.zeros(3, dtype=np.float64)
    count = 0
    for start in range(0, flat_indices.size, chunk_size):
        world = flat_indices_to_world(
            flat_indices[start : start + chunk_size], shape, directions, origin
        )
        coordinate_sum += world.sum(axis=0)
        count += world.shape[0]
    centroid = coordinate_sum / count

    max_radius = 0.0
    for start in range(0, flat_indices.size, chunk_size):
        world = flat_indices_to_world(
            flat_indices[start : start + chunk_size], shape, directions, origin
        )
        max_radius = max(
            max_radius,
            float(np.linalg.norm(world - centroid, axis=1).max()),
        )
    if max_radius <= 0:
        raise ValueError("Complete skull normalization scale is zero")
    return centroid, max_radius


def stable_rng(seed, case_id, role):
    digest = hashlib.sha256(f"{case_id}:{role}".encode("utf-8")).digest()
    role_seed = int.from_bytes(digest[:4], byteorder="little", signed=False)
    return np.random.RandomState((seed + role_seed) % (2**32))


def sample_surface(
    flat_indices,
    shape,
    directions,
    origin,
    count,
    centroid,
    scale,
    rng,
):
    chosen = rng.choice(flat_indices, size=count, replace=flat_indices.size < count)
    world = flat_indices_to_world(chosen, shape, directions, origin)
    return ((world - centroid) / scale).astype(np.float32)


def relative_or_absolute(path, root):
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def triplet_metrics(complete, defective, implant):
    missing = complete & ~defective
    implant_union = np.count_nonzero(missing | implant)
    implant_iou = (
        float(np.count_nonzero(missing & implant) / implant_union)
        if implant_union
        else 1.0
    )
    reconstructed = defective | implant
    reconstruction_union = np.count_nonzero(reconstructed | complete)
    reconstruction_iou = (
        float(np.count_nonzero(reconstructed & complete) / reconstruction_union)
        if reconstruction_union
        else 1.0
    )
    defective_extra_fraction = float(
        np.count_nonzero(defective & ~complete) / max(np.count_nonzero(defective), 1)
    )
    return {
        "implant_missing_iou": implant_iou,
        "reconstruction_iou": reconstruction_iou,
        "defective_extra_fraction": defective_extra_fraction,
        "complete_voxels": int(np.count_nonzero(complete)),
        "defective_voxels": int(np.count_nonzero(defective)),
        "implant_voxels": int(np.count_nonzero(implant)),
        "missing_voxels": int(np.count_nonzero(missing)),
    }


def process_triplet(args, triplet, split, points_dir):
    case_id = triplet["case_id"]
    output_path = points_dir / f"{case_id}.npz"
    if output_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"{output_path} already exists; pass --overwrite to replace it"
        )

    volumes = {}
    headers = {}
    for role in ("complete", "defective", "implant"):
        volumes[role], headers[role] = read_binary_volume(
            triplet[role], args.threshold
        )

    directions, origin = check_geometry(
        case_id, volumes, headers, args.strict_geometry
    )
    metrics = triplet_metrics(
        volumes["complete"], volumes["defective"], volumes["implant"]
    )
    if metrics["implant_missing_iou"] < args.min_triplet_iou:
        message = (
            f"{case_id}: implant/missing IoU "
            f"{metrics['implant_missing_iou']:.4f} < {args.min_triplet_iou:.4f}"
        )
        if args.strict_geometry:
            raise ValueError(message)
        print(f"[warning] {message}", file=sys.stderr)

    surfaces = {
        role: surface_flat_indices(volume) for role, volume in volumes.items()
    }
    normalization_role = args.normalization_source
    centroid, scale = surface_normalization(
        surfaces[normalization_role],
        volumes[normalization_role].shape,
        directions,
        origin,
    )

    requested_counts = {
        "complete": args.n_complete,
        "defective": args.n_partial,
        "implant": args.n_implant,
    }
    sampled = {}
    for role, count in requested_counts.items():
        sampled[role] = sample_surface(
            surfaces[role],
            volumes[role].shape,
            directions,
            origin,
            count,
            centroid,
            scale,
            stable_rng(args.seed, case_id, role),
        )

    np.savez_compressed(
        output_path,
        partial=sampled["defective"],
        gt=sampled["complete"],
        implant=sampled["implant"],
        centroid=centroid.astype(np.float64),
        scale=np.asarray(scale, dtype=np.float64),
        voxel_shape=np.asarray(volumes["complete"].shape, dtype=np.int32),
        space_directions=directions.astype(np.float64),
        space_origin=origin.astype(np.float64),
    )

    return {
        "dataset": "SkullFix",
        "case_id": case_id,
        "split": split,
        "point_path": f"points/{output_path.name}",
        "raw": {
            role: relative_or_absolute(triplet[role], args.input_root)
            for role in ("complete", "defective", "implant")
        },
        "n_partial": args.n_partial,
        "n_complete": args.n_complete,
        "n_implant": args.n_implant,
        "normalization": {
            "source": f"{normalization_role}_surface",
            "centroid": centroid.tolist(),
            "scale": float(scale),
        },
        "voxel_shape": list(volumes["complete"].shape),
        "space_directions": directions.tolist(),
        "space_origin": origin.tolist(),
        "quality": metrics,
    }


def write_json(path, payload):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    args = parse_args()
    args.input_root = args.input_root.expanduser().resolve()
    args.output_root = args.output_root.expanduser().resolve()
    if not args.input_root.is_dir():
        raise FileNotFoundError(f"Input root not found: {args.input_root}")
    if min(args.n_complete, args.n_partial, args.n_implant) <= 0:
        raise ValueError("All point counts must be positive")

    role_directories = {
        role: find_role_directory(
            args.input_root, role, getattr(args, f"{role}_dir")
        )
        for role in ("complete", "defective", "implant")
    }
    role_files = {
        role: index_role_files(directory, role)
        for role, directory in role_directories.items()
    }
    triplets = pair_triplets(role_files)
    split_counts = parse_split_spec(args.split, len(triplets))
    assignments = assign_splits(
        [triplet["case_id"] for triplet in triplets], split_counts, args.seed
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    points_dir = args.output_root / "points"
    points_dir.mkdir(parents=True, exist_ok=True)

    pairing_report = {
        "dataset": "SkullFix",
        "input_root": str(args.input_root),
        "role_directories": {
            role: str(directory) for role, directory in role_directories.items()
        },
        "role_counts": {role: len(files) for role, files in role_files.items()},
        "paired_triplets": len(triplets),
        "split_counts": split_counts,
        "seed": args.seed,
    }
    write_json(args.output_root / "pairing_report.json", pairing_report)

    records = []
    for index, triplet in enumerate(triplets, start=1):
        case_id = triplet["case_id"]
        print(
            f"[{index:03d}/{len(triplets):03d}] "
            f"case={case_id} split={assignments[case_id]}"
        )
        records.append(
            process_triplet(
                args, triplet, assignments[case_id], points_dir
            )
        )

    manifest_path = args.output_root / "manifest.jsonl"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        for record in sorted(records, key=lambda item: item["case_id"]):
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    split_case_ids = {
        split: sorted(
            record["case_id"]
            for record in records
            if record["split"] == split
        )
        for split in ("train", "val", "test")
    }
    write_json(args.output_root / "splits.json", split_case_ids)

    with open(
        args.output_root / "SHA256SUMS",
        "w",
        encoding="ascii",
        newline="\n",
    ) as handle:
        for record in sorted(records, key=lambda item: item["case_id"]):
            point_path = args.output_root / record["point_path"]
            handle.write(
                f"{sha256_file(point_path)}  {record['point_path']}\n"
            )

    summary = {
        **pairing_report,
        "manifest": str(manifest_path),
        "splits_file": str(args.output_root / "splits.json"),
        "checksums": str(args.output_root / "SHA256SUMS"),
        "point_cloud": {
            "partial": args.n_partial,
            "complete": args.n_complete,
            "implant": args.n_implant,
        },
        "normalization": (
            f"shared {args.normalization_source}-surface centroid and max radius"
        ),
        "quality": {
            "min_implant_missing_iou": min(
                record["quality"]["implant_missing_iou"] for record in records
            ),
            "mean_implant_missing_iou": float(
                np.mean(
                    [
                        record["quality"]["implant_missing_iou"]
                        for record in records
                    ]
                )
            ),
        },
    }
    write_json(args.output_root / "summary.json", summary)
    print(f"[ok] wrote {len(records)} samples to {args.output_root}")
    print(f"[ok] manifest: {manifest_path}")


if __name__ == "__main__":
    main()
