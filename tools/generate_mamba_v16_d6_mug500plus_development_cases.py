#!/usr/bin/env python3
"""Generate the frozen D6 development400 cases; never touches sealed partitions."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

from tqdm import tqdm

from generate_mug500plus_m2_synthetic_defects import (
    audit_locked_sources,
    generate_skull,
    locate_sources,
    sha256_file,
    write_jsonl,
)
from lock_mamba_v16_d6_mug500plus_development_fourfold_protocol import (
    EXPECTED_BASE_PROTOCOL_SHA256,
    EXPECTED_DEFECT_TYPES,
    EXPECTED_DEVELOPMENT_ASSETS_SHA256,
    EXPECTED_DEVELOPMENT_MANIFEST_SHA256,
    EXPECTED_DEVELOPMENT_RECEIPT_SHA256,
    EXPECTED_ENGINE_SHA256,
    read_lineage,
    validate_protocol,
    verify_flat_manifest,
)


def bundle_sha256(paths: List[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted((path.resolve() for path in paths), key=lambda item: item.name):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_effective_protocol(
    d6_protocol: Dict[str, Any], base_protocol: Dict[str, Any]
) -> Dict[str, Any]:
    validate_protocol(d6_protocol)
    engine = d6_protocol["lineage"]["m2_v1_engine"]
    for section in engine["inherited_sections"]:
        if section not in base_protocol:
            raise RuntimeError(f"M2 v1 base protocol lacks inherited section: {section}")
    effective = copy.deepcopy(base_protocol)
    generation = d6_protocol["development_generation"]
    effective["protocol_id"] = generation["effective_protocol_id"]
    effective["status"] = "preregistered_generator_not_run"
    effective["determinism"]["master_seed"] = generation["master_seed"]
    effective["derived_dataset"].update(
        {
            "expected_cases": generation["expected_cases"],
            "source_dataset": generation["source_dataset"],
        }
    )
    effective["split_policy"] = {
        "unit": "source_skull",
        "partition": "development_only",
        "source_skulls": 100,
        "folds": ["A", "B", "C", "D"],
        "fold_dev_skulls": 25,
        "fold_train_skulls": 75,
        "all_defects_from_one_skull_share_fold": True,
        "folds_frozen_before_generation": True,
        "sealed_partitions_excluded": True,
    }
    effective["forbidden"] = sorted(
        set(effective.get("forbidden", [])) | set(d6_protocol["forbidden"])
    )
    if tuple(effective["defect_families"]) != EXPECTED_DEFECT_TYPES:
        raise RuntimeError("Effective D6 defect ordering differs from the frozen contract")
    return effective


def verify_protocol_lock(directory: Path, protocol_bytes: bytes) -> Dict[str, str]:
    manifest_hash = sha256_file(directory / "files.sha256")
    verify_flat_manifest(directory, manifest_hash)
    receipt = json.loads(
        (directory / "d6_development_protocol_lock_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    implementation_hashes = receipt.get("implementation_hashes", {})
    if (
        receipt.get("status")
        != "d6_development_generation_and_fourfold_protocol_locked"
        or receipt.get("protocol_sha256") != hashlib.sha256(protocol_bytes).hexdigest()
        or receipt.get("counts", {}).get("planned_development_cases") != 400
        or implementation_hashes.get("generator_entry")
        != sha256_file(Path(__file__).resolve())
        or implementation_hashes.get("engine") != EXPECTED_ENGINE_SHA256
        or implementation_hashes.get("base_protocol")
        != EXPECTED_BASE_PROTOCOL_SHA256
        or receipt.get("D6_development_synthetic_generation_authorized_next")
        is not True
        or receipt.get("D6A_R0_R1_implementation_frozen") is not True
        or receipt.get("D6_gradient_calibration_authorized") is not False
        or receipt.get("D6A_training_authorized") is not False
        or receipt.get("D6_seed1_authorized") is not False
        or receipt.get("D6B_training_authorized") is not False
        or receipt.get("D6_candidate_selection_authorized") is not False
        or receipt.get("proposal_confirmation_accessed") is not False
        or receipt.get("official_test_accessed") is not False
    ):
        raise RuntimeError("D6 protocol-lock semantics are invalid")
    with (directory / "source_fold_assignments.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 100 or len({row["source_id"] for row in rows}) != 100:
        raise RuntimeError("D6 source-fold assignment lock is invalid")
    return {row["source_id"]: row["fold"] for row in rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development100_qc_lock_dir", type=Path, required=True)
    parser.add_argument("--source125_acquisition_lock_dir", type=Path, required=True)
    parser.add_argument("--protocol_lock_dir", type=Path, required=True)
    parser.add_argument("--development_source_root", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--d6_protocol_json", type=Path, required=True)
    parser.add_argument("--base_protocol_json", type=Path, required=True)
    parser.add_argument("--num_workers", type=int, default=1)
    parser.add_argument("--preflight_only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.d6_protocol_json.read_bytes()
    d6_protocol = json.loads(protocol_bytes)
    if sha256_file(args.base_protocol_json) != EXPECTED_BASE_PROTOCOL_SHA256:
        raise RuntimeError("M2 v1 base protocol drifted")
    engine_path = Path(__file__).with_name("generate_mug500plus_m2_synthetic_defects.py")
    if sha256_file(engine_path) != EXPECTED_ENGINE_SHA256:
        raise RuntimeError("M2 v1 engine drifted")
    base_protocol = json.loads(args.base_protocol_json.read_text(encoding="utf-8"))
    effective = build_effective_protocol(d6_protocol, base_protocol)
    fold_by_source = verify_protocol_lock(args.protocol_lock_dir, protocol_bytes)
    lock_rows, _ = read_lineage(
        args.development100_qc_lock_dir, args.source125_acquisition_lock_dir
    )
    source_paths = locate_sources(args.development_source_root.resolve(), lock_rows)
    audit_locked_sources(source_paths, lock_rows)
    if set(source_paths) != set(fold_by_source):
        raise RuntimeError("Development100 and fourfold locks have different IDs")
    generator_hash = bundle_sha256(
        [Path(__file__), engine_path, args.d6_protocol_json, args.base_protocol_json]
    )
    print(f"[ok] D6 development sources={len(source_paths)}")
    print(f"[sha256] D6 generator_bundle={generator_hash}")
    if args.preflight_only:
        print("[done] preflight only; no derived cases were written")
        print("[locked] sealed partitions were not accessed")
        return
    if args.out_dir.exists():
        raise RuntimeError(f"Refusing to overwrite output: {args.out_dir}")
    args.out_dir.mkdir(parents=True)
    cases_dir = args.out_dir / "cases"
    cases_dir.mkdir()
    lock_by_case = {row["case_id"].upper(): row for row in lock_rows}
    tasks = [
        {
            "protocol": effective,
            "lock_row": lock_by_case[source_id],
            "source_path": str(source_paths[source_id]),
            "cases_dir": str(cases_dir.resolve()),
            "manifest_root": str(args.out_dir.resolve()),
            "generator_hash": generator_hash,
        }
        for source_id in sorted(source_paths)
    ]
    records: List[Dict[str, Any]] = []
    workers = max(1, int(args.num_workers))
    if workers == 1:
        for task in tqdm(tasks, desc="D6 development source skulls"):
            records.extend(generate_skull(task))
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(generate_skull, task) for task in tasks]
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="D6 development source skulls",
            ):
                records.extend(future.result())
    records.sort(key=lambda row: (row["skull_id"], row["defect_type"]))
    if len(records) != 400:
        raise RuntimeError(f"Expected 400 D6 development cases, got {len(records)}")
    for record in records:
        source_id = record["skull_id"].removeprefix("mug500plus__")
        record["d6_fold"] = fold_by_source[source_id]
        record["d6_partition"] = "development"
    manifest = args.out_dir / "manifest.jsonl"
    write_jsonl(manifest, records)
    receipt = {
        "protocol_id": d6_protocol["protocol_id"],
        "status": "generated_training_locked_pending_D6_generation_audit",
        "generator_sha256": generator_hash,
        "development100_files_manifest_sha256": EXPECTED_DEVELOPMENT_MANIFEST_SHA256,
        "development100_receipt_sha256": EXPECTED_DEVELOPMENT_RECEIPT_SHA256,
        "development100_assets_sha256": EXPECTED_DEVELOPMENT_ASSETS_SHA256,
        "source_skulls": 100,
        "derived_cases": 400,
        "manifest_sha256": sha256_file(manifest),
        "D6A_R0_R1_implementation_frozen": True,
        "D6_gradient_calibration_authorized": False,
        "D6A_training_authorized": False,
        "D6_seed1_authorized": False,
        "D6B_training_authorized": False,
        "candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "official_test_accessed": False,
    }
    receipt_path = args.out_dir / "generation_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    (args.out_dir / "files.sha256").write_text(
        f"{sha256_file(manifest)}  manifest.jsonl\n"
        f"{sha256_file(receipt_path)}  generation_receipt.json\n",
        encoding="ascii",
    )
    print(f"[saved] {manifest}")
    print("[done] development_sources=100 cases=400")
    print("[locked] calibration=false training=false seed1=false confirmation=false pending_audit=true")


if __name__ == "__main__":
    main()
