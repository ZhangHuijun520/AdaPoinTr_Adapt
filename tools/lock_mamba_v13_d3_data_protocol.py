#!/usr/bin/env python
"""Audit and immutably lock the independent D3 skull-level data protocol."""

import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path


PROTOCOL_ID = "mamba-v13-d3-contact-support-structuralization-v1"
SPLIT_SALT = "mamba-v13-d3-independent-data-v1-20260811"
FOLDS = "ABCD"
HASH_FIELDS = (
    "source_asset_sha256",
    "source_surface_fingerprint_sha256",
    "surface_fingerprint_algorithm_sha256",
    "derived_case_sha256",
    "generator_sha256",
)
REQUIRED_FIELDS = {
    "case_id",
    "skull_id",
    "defect_type",
    "source_dataset",
    "source_asset_path",
    "source_asset_sha256",
    "source_surface_fingerprint_sha256",
    "surface_fingerprint_algorithm_sha256",
    "point_path",
    "derived_case_sha256",
    "generator_sha256",
    "normalization",
}
PROTECTED_DATASET_NAMES = {"skullbreak", "skullfix"}
EXPECTED_DEFECT_TYPES = {
    "ellipsoid_small",
    "ellipsoid_medium",
    "ellipsoid_large",
    "irregular_medium",
}


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_key(namespace, value):
    return sha256_bytes(f"{SPLIT_SALT}|{namespace}|{value}".encode("utf-8"))


def resolve_asset(manifest_path, raw_path):
    path = Path(str(raw_path)).expanduser()
    if not path.is_absolute():
        path = manifest_path.parent / path
    return path.resolve()


def read_manifest(path):
    raw = path.read_bytes()
    records = [
        json.loads(line)
        for line in raw.decode("utf-8").splitlines()
        if line.strip()
    ]
    return records, sha256_bytes(raw)


def read_protected_fingerprints(path):
    raw = path.read_bytes()
    fingerprints = set()
    for line_number, line in enumerate(raw.decode("ascii").splitlines(), 1):
        value = line.strip().split()[0] if line.strip() else ""
        if not value or value.startswith("#"):
            continue
        if len(value) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
            raise ValueError(
                f"Invalid protected fingerprint at line {line_number}: {value!r}"
            )
        fingerprints.add(value.lower())
    if not fingerprints:
        raise ValueError("Protected fingerprint manifest is empty")
    return fingerprints, sha256_bytes(raw)


def validate_records(
    records,
    manifest_path,
    protected_fingerprints,
    generator_sha256,
    surface_fingerprint_algorithm_sha256,
    minimum_skulls,
):
    if not records:
        raise ValueError("Independent-data manifest is empty")
    generator_sha256 = generator_sha256.lower()
    surface_fingerprint_algorithm_sha256 = (
        surface_fingerprint_algorithm_sha256.lower()
    )
    case_ids = set()
    derived_hashes = set()
    source_hash_to_skull = {}
    surface_hash_to_skull = {}
    by_skull = defaultdict(list)
    verified_assets = {}

    for line_number, record in enumerate(records, 1):
        missing = REQUIRED_FIELDS.difference(record)
        if missing:
            raise ValueError(
                f"Manifest line {line_number} is missing {sorted(missing)}"
            )
        for field in HASH_FIELDS:
            value = str(record[field]).lower()
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(f"Line {line_number}: invalid {field}")
            record[field] = value
        if record["generator_sha256"] != generator_sha256:
            raise ValueError(f"Line {line_number}: generator SHA256 mismatch")
        if (
            record["surface_fingerprint_algorithm_sha256"]
            != surface_fingerprint_algorithm_sha256
        ):
            raise ValueError(
                f"Line {line_number}: surface fingerprint algorithm mismatch"
            )

        source_dataset = str(record["source_dataset"]).strip().lower()
        if source_dataset in PROTECTED_DATASET_NAMES:
            raise ValueError(
                f"Line {line_number}: protected dataset name is not external: "
                f"{source_dataset}"
            )
        case_id = str(record["case_id"])
        skull_id = str(record["skull_id"])
        if not case_id or case_id in case_ids:
            raise ValueError(f"Duplicate or empty case ID: {case_id!r}")
        case_ids.add(case_id)

        source_hash = record["source_asset_sha256"]
        surface_hash = record["source_surface_fingerprint_sha256"]
        derived_hash = record["derived_case_sha256"]
        if (
            source_hash in protected_fingerprints
            or surface_hash in protected_fingerprints
            or derived_hash in protected_fingerprints
        ):
            raise ValueError(f"{case_id}: overlaps a protected data fingerprint")
        owner = source_hash_to_skull.setdefault(source_hash, skull_id)
        if owner != skull_id:
            raise ValueError(
                f"Source asset {source_hash} is assigned to multiple skull IDs"
            )
        surface_owner = surface_hash_to_skull.setdefault(surface_hash, skull_id)
        if surface_owner != skull_id:
            raise ValueError(
                f"Surface fingerprint {surface_hash} maps to multiple skull IDs"
            )
        if derived_hash in derived_hashes:
            raise ValueError(f"Duplicate derived-case hash: {derived_hash}")
        derived_hashes.add(derived_hash)

        normalization = record["normalization"]
        if not isinstance(normalization, dict):
            raise ValueError(f"{case_id}: normalization metadata is missing")
        centroid = normalization.get("centroid")
        scale = normalization.get("scale")
        if (
            not isinstance(centroid, list)
            or len(centroid) != 3
            or any(not math.isfinite(float(value)) for value in centroid)
            or not math.isfinite(float(scale))
            or float(scale) <= 0
        ):
            raise ValueError(f"{case_id}: invalid normalization metadata")

        source_path = resolve_asset(manifest_path, record["source_asset_path"])
        point_path = resolve_asset(manifest_path, record["point_path"])
        for asset_path, expected, role in (
            (source_path, source_hash, "source asset"),
            (point_path, derived_hash, "derived case"),
        ):
            if not asset_path.is_file():
                raise FileNotFoundError(f"{case_id}: missing {role}: {asset_path}")
            cache_key = str(asset_path)
            actual_hash = verified_assets.get(cache_key)
            if actual_hash is None:
                actual_hash = sha256_file(asset_path)
                verified_assets[cache_key] = actual_hash
            if actual_hash != expected:
                raise ValueError(f"{case_id}: {role} SHA256 mismatch")
        by_skull[skull_id].append(record)

    if len(by_skull) < minimum_skulls:
        raise ValueError(
            f"Need at least {minimum_skulls} independent skulls, got {len(by_skull)}"
        )
    expected_defects = None
    for skull_id, skull_records in by_skull.items():
        source_hashes = {item["source_asset_sha256"] for item in skull_records}
        surface_hashes = {
            item["source_surface_fingerprint_sha256"] for item in skull_records
        }
        defect_types = {str(item["defect_type"]) for item in skull_records}
        if len(source_hashes) != 1 or len(surface_hashes) != 1:
            raise ValueError(f"{skull_id}: one skull must map to one source asset")
        if len(defect_types) != len(skull_records):
            raise ValueError(f"{skull_id}: duplicate defect types")
        if expected_defects is None:
            expected_defects = defect_types
        elif defect_types != expected_defects:
            raise ValueError(
                f"{skull_id}: defect-type set differs from other source skulls"
            )
    return by_skull, sorted(expected_defects)


def make_partitions(by_skull, holdout_fraction):
    skull_ids = sorted(by_skull)
    holdout_count = max(1, int(math.floor(len(skull_ids) * holdout_fraction + 0.5)))
    holdout = set(
        sorted(skull_ids, key=lambda item: stable_key("holdout", item))[
            :holdout_count
        ]
    )
    development = sorted(
        (item for item in skull_ids if item not in holdout),
        key=lambda item: stable_key("fold", item),
    )
    fold_by_skull = {
        skull_id: FOLDS[index % len(FOLDS)]
        for index, skull_id in enumerate(development)
    }
    return holdout, fold_by_skull


def csv_bytes(rows):
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode("utf-8")


def ids_for_skulls(by_skull, skull_ids):
    return sorted(
        str(record["case_id"])
        for skull_id in skull_ids
        for record in by_skull[skull_id]
    )


def render_outputs(
    by_skull,
    defect_types,
    source_manifest_sha256,
    protected_manifest_sha256,
    generator_sha256,
    surface_fingerprint_algorithm_sha256,
    holdout_fraction,
):
    holdout, fold_by_skull = make_partitions(by_skull, holdout_fraction)
    development = set(fold_by_skull)
    files = {}

    def add_ids(name, values):
        files[name] = ("\n".join(values) + "\n").encode("utf-8")

    add_ids("development_case_ids.txt", ids_for_skulls(by_skull, development))
    add_ids("locked_holdout_case_ids.txt", ids_for_skulls(by_skull, holdout))
    for fold in FOLDS:
        dev_skulls = {
            skull_id for skull_id, assigned in fold_by_skull.items()
            if assigned == fold
        }
        add_ids(f"fold{fold}_dev_case_ids.txt", ids_for_skulls(by_skull, dev_skulls))
        add_ids(
            f"fold{fold}_train_case_ids.txt",
            ids_for_skulls(by_skull, development.difference(dev_skulls)),
        )

    skull_rows = [["skull_id", "source_asset_sha256", "partition", "fold"]]
    case_rows = [["case_id", "skull_id", "defect_type", "partition", "fold"]]
    for skull_id in sorted(by_skull):
        partition = "locked_holdout" if skull_id in holdout else "development"
        fold = "" if skull_id in holdout else fold_by_skull[skull_id]
        source_hash = by_skull[skull_id][0]["source_asset_sha256"]
        skull_rows.append([skull_id, source_hash, partition, fold])
        for record in sorted(by_skull[skull_id], key=lambda item: item["case_id"]):
            case_rows.append([
                str(record["case_id"]), skull_id, str(record["defect_type"]),
                partition, fold,
            ])
    files["skull_assignments.csv"] = csv_bytes(skull_rows)
    files["case_assignments.csv"] = csv_bytes(case_rows)

    fold_counts = {
        fold: sum(value == fold for value in fold_by_skull.values())
        for fold in FOLDS
    }
    protocol = {
        "protocol_id": PROTOCOL_ID,
        "status": "training_unlocked_after_independent_data_audit",
        "split_salt": SPLIT_SALT,
        "source_manifest_sha256": source_manifest_sha256,
        "protected_fingerprints_sha256": protected_manifest_sha256,
        "synthetic_generator_sha256": generator_sha256,
        "surface_fingerprint_algorithm_sha256": (
            surface_fingerprint_algorithm_sha256
        ),
        "split_unit": "source_skull",
        "defect_types": defect_types,
        "counts": {
            "total_skulls": len(by_skull),
            "total_cases": sum(map(len, by_skull.values())),
            "development_skulls": len(development),
            "locked_holdout_skulls": len(holdout),
            "fold_dev_skulls": fold_counts,
        },
        "protected_data_used": False,
        "training_unlocked": True,
    }
    files["protocol.json"] = (
        json.dumps(protocol, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    hashes = [f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    return files


def write_locked(files, output_dir):
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*") if path.is_file()
        }
        expected = dict(files)
        if existing != expected:
            raise RuntimeError(
                "Refusing to overwrite a non-identical D3 data protocol"
            )
        print(f"[locked] existing protocol is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] locked independent-data protocol: {output_dir}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--protected_fingerprints", type=Path, required=True)
    parser.add_argument("--generator_sha256", required=True)
    parser.add_argument("--surface_fingerprint_algorithm_sha256", required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--expected_skulls", type=int, default=125)
    parser.add_argument("--holdout_fraction", type=float, default=0.2)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.expected_skulls != 125:
        raise ValueError("D3 MUG500+ protocol requires exactly 125 source skulls")
    if not 0.1 <= args.holdout_fraction <= 0.5:
        raise ValueError("holdout_fraction must be in [0.1, 0.5]")
    generator_hash = args.generator_sha256.lower()
    if (
        len(generator_hash) != 64
        or any(ch not in "0123456789abcdef" for ch in generator_hash)
    ):
        raise ValueError("generator_sha256 must contain 64 hex characters")
    surface_algorithm_hash = args.surface_fingerprint_algorithm_sha256.lower()
    if (
        len(surface_algorithm_hash) != 64
        or any(ch not in "0123456789abcdef" for ch in surface_algorithm_hash)
    ):
        raise ValueError(
            "surface_fingerprint_algorithm_sha256 must contain 64 hex characters"
        )
    records, manifest_hash = read_manifest(args.manifest)
    protected, protected_hash = read_protected_fingerprints(
        args.protected_fingerprints
    )
    by_skull, defect_types = validate_records(
        records,
        args.manifest.resolve(),
        protected,
        generator_hash,
        surface_algorithm_hash,
        args.expected_skulls,
    )
    if len(by_skull) != args.expected_skulls:
        raise ValueError(
            f"D3 requires exactly {args.expected_skulls} source skulls, "
            f"got {len(by_skull)}"
        )
    if set(defect_types) != EXPECTED_DEFECT_TYPES:
        raise ValueError(
            f"D3 defect families differ from locked M2: {defect_types}"
        )
    if sum(map(len, by_skull.values())) != 500:
        raise ValueError("D3 requires exactly 125 x 4 = 500 derived cases")
    files = render_outputs(
        by_skull,
        defect_types,
        manifest_hash,
        protected_hash,
        generator_hash,
        surface_algorithm_hash,
        args.holdout_fraction,
    )
    write_locked(files, args.output_dir)
    print(
        f"[ok] independent skulls={len(by_skull)} "
        f"cases={sum(map(len, by_skull.values()))}"
    )
    print("[locked] protected data overlap=0; holdout remains inaccessible")


if __name__ == "__main__":
    main()
