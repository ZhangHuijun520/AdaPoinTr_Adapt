#!/usr/bin/env python3
"""Freeze D4 M2 generation planning and four source-skull folds."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


PROTOCOL_ID = "mamba-v14-d4-mug500plus-m2-fourfold-v1"
SOURCE_LOCK_PROTOCOL_ID = "mamba-v14-d4-mug500plus-source100-final-qc-lock-v1"
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "6103ebc8010441ad7a0c7eff4f96b3df0cae0e359de79258182b59917b5f12eb"
)
EXPECTED_SOURCE_RECEIPT_SHA256 = (
    "c76cc14db549badb08bf2e9005b58f4825067c0af17431c989359e9697d0c98a"
)
EXPECTED_SOURCE_ASSETS_SHA256 = (
    "0e81a5a41e1a972d5d2d66c3603fcb101b9d6f8b4878460f259e4035514c1d15"
)
EXPECTED_ENGINE_SHA256 = (
    "88a839afffadaa4d0eaf3fa7293e2cef0fdb2cccb7beb2af5062a91fc0f3adf7"
)
EXPECTED_BASE_PROTOCOL_SHA256 = (
    "1da529947cdce9972a2ce7881c05df891191d54026a96ed229c872cdd7e18768"
)
EXPECTED_DEFECT_TYPES = (
    "ellipsoid_small",
    "ellipsoid_medium",
    "ellipsoid_large",
    "irregular_medium",
)
REQUIRED_ASSET_FIELDS = {
    "case_id",
    "portable_source_path",
    "source_asset_sha256",
    "source_surface_fingerprint_sha256",
    "surface_fingerprint_algorithm_sha256",
    "file_bytes",
    "triangle_count",
    "qc_pass",
    "batch_id",
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


def csv_bytes(fieldnames: Sequence[str], rows: Iterable[Dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def stable_key(salt: str, source_id: str) -> str:
    return sha256_bytes(f"{salt}|fold|{source_id}".encode("utf-8"))


def verify_flat_manifest(directory: Path, expected_manifest_hash: str) -> None:
    manifest = directory / "files.sha256"
    if sha256_file(manifest) != expected_manifest_hash:
        raise RuntimeError("Frozen source100 files.sha256 drifted")
    for raw in manifest.read_text(encoding="ascii").splitlines():
        expected, name = raw.split(maxsplit=1)
        name = name.lstrip("*")
        if Path(name).name != name:
            raise RuntimeError(f"Nested source-lock manifest path: {name}")
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Source-lock hash-chain failure: {path}")


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if (
        protocol.get("protocol_id") != PROTOCOL_ID
        or protocol.get("status") != "preregistered_generation_not_run"
    ):
        raise RuntimeError("Unexpected D4 M2 protocol")
    lineage = protocol.get("lineage", {})
    source = lineage.get("source100_qc_lock", {})
    engine = lineage.get("m2_v1_engine", {})
    if (
        source.get("files_manifest_sha256") != EXPECTED_SOURCE_MANIFEST_SHA256
        or source.get("receipt_sha256") != EXPECTED_SOURCE_RECEIPT_SHA256
        or source.get("assets_csv_sha256") != EXPECTED_SOURCE_ASSETS_SHA256
        or source.get("required_sources") != 100
        or source.get("required_qc_pass") != 100
        or source.get("required_prior_overlap") != 0
        or engine.get("implementation_sha256") != EXPECTED_ENGINE_SHA256
        or engine.get("base_protocol_sha256") != EXPECTED_BASE_PROTOCOL_SHA256
        or engine.get("inherited_sections_must_be_unmodified") is not True
    ):
        raise RuntimeError("D4 M2 lineage contract changed")
    overrides = protocol.get("d4_generation_overrides", {})
    if (
        overrides.get("source_skulls") != 100
        or overrides.get("defects_per_source") != 4
        or overrides.get("expected_cases") != 400
        or overrides.get("overwrite_allowed") is not False
    ):
        raise RuntimeError("D4 generation counts or overwrite policy changed")
    defects = protocol.get("defect_contract", {})
    if (
        tuple(defects.get("defect_types", ())) != EXPECTED_DEFECT_TYPES
        or defects.get("all_four_required_per_source") is not True
    ):
        raise RuntimeError("D4 defect contract changed")
    folds = protocol.get("four_fold_rule", {})
    if (
        folds.get("salt") != "mamba-v14-d4-m2-source-fourfold-v1-20260829"
        or folds.get("folds") != ["A", "B", "C", "D"]
        or folds.get("dev_sources_per_fold") != 25
        or folds.get("train_sources_per_fold") != 75
        or folds.get("dev_cases_per_fold") != 100
        or folds.get("train_cases_per_fold") != 300
        or folds.get("same_source_four_cases_share_fold") is not True
        or folds.get("model_or_geometry_metrics_used") is not False
        or folds.get("manual_reassignment_allowed") is not False
    ):
        raise RuntimeError("D4 four-fold rule changed")
    effect = protocol.get("lock_effect", {})
    if (
        effect.get("D4_M2_generation_authorized_after_protocol_lock") is not True
        or effect.get("D4_M2_generation_started_by_lock") is not False
        or any(
            effect.get(key) is not False
            for key in (
                "D4_training_authorized",
                "D4_candidate_selection_authorized",
                "D3_holdout_access_authorized",
                "SkullBreak_confirmation20_access_authorized",
                "official_test_access_authorized",
            )
        )
    ):
        raise RuntimeError("D4 authorization boundary changed")


def read_source_lock(directory: Path) -> List[Dict[str, str]]:
    verify_flat_manifest(directory, EXPECTED_SOURCE_MANIFEST_SHA256)
    receipt_path = directory / "source100_qc_lock_receipt.json"
    assets_path = directory / "source100_assets.csv"
    if sha256_file(receipt_path) != EXPECTED_SOURCE_RECEIPT_SHA256:
        raise RuntimeError("Frozen source100 receipt drifted")
    if sha256_file(assets_path) != EXPECTED_SOURCE_ASSETS_SHA256:
        raise RuntimeError("Frozen source100 assets CSV drifted")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("protocol_id") != SOURCE_LOCK_PROTOCOL_ID
        or receipt.get("status") != "source100_qc_locked_complete"
        or receipt.get("counts")
        != {"batches": 3, "qc_fail": 0, "qc_pass": 100, "sources": 100}
        or receipt.get("global_duplicate_and_overlap_gates_passed") is not True
        or receipt.get("protected_data_accessed") is not False
        or receipt.get("D4_M2_protocol_preparation_authorized_next") is not True
    ):
        raise RuntimeError("Frozen source100 receipt semantics are invalid")
    with assets_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if not REQUIRED_ASSET_FIELDS.issubset(reader.fieldnames or []):
            raise RuntimeError("Source100 assets schema is incomplete")
    ids = [row["case_id"] for row in rows]
    if len(rows) != 100 or len(set(ids)) != 100:
        raise RuntimeError("Source100 assets are not exactly 100 unique sources")
    if any(row["qc_pass"].lower() != "true" for row in rows):
        raise RuntimeError("Source100 assets contain a QC failure")
    return sorted(rows, key=lambda row: row["case_id"])


def assign_folds(source_ids: Sequence[str], protocol: Dict[str, Any]) -> Dict[str, str]:
    if len(source_ids) != 100 or len(set(source_ids)) != 100:
        raise RuntimeError("Four-fold assignment requires 100 unique source IDs")
    rule = protocol["four_fold_rule"]
    ordered = sorted(
        source_ids,
        key=lambda source_id: (stable_key(rule["salt"], source_id), source_id),
    )
    folds = rule["folds"]
    result = {
        source_id: folds[index % len(folds)]
        for index, source_id in enumerate(ordered)
    }
    counts = {fold: list(result.values()).count(fold) for fold in folds}
    if counts != {fold: 25 for fold in folds}:
        raise RuntimeError(f"Unexpected D4 fold counts: {counts}")
    return result


def case_ids(source_ids: Iterable[str], defect_types: Sequence[str]) -> List[str]:
    return sorted(
        f"mug500plus__{source_id}__{defect}"
        for source_id in source_ids
        for defect in defect_types
    )


def render_outputs(
    rows: Sequence[Dict[str, str]],
    protocol: Dict[str, Any],
    protocol_bytes: bytes,
    implementation_paths: Dict[str, Path],
) -> Dict[str, bytes]:
    source_ids = [row["case_id"] for row in rows]
    fold_by_source = assign_folds(source_ids, protocol)
    folds = protocol["four_fold_rule"]["folds"]
    defects = protocol["defect_contract"]["defect_types"]
    files: Dict[str, bytes] = {"d4_m2_fourfold_protocol_v1.json": protocol_bytes}

    def add_ids(name: str, values: Iterable[str]) -> None:
        files[name] = ("\n".join(sorted(values)) + "\n").encode("ascii")

    add_ids("source100_ids.txt", source_ids)
    assignment_rows = []
    plan_rows = []
    for row in rows:
        source_id = row["case_id"]
        fold = fold_by_source[source_id]
        assignment_rows.append(
            {
                "source_id": source_id,
                "fold": fold,
                "fold_key": stable_key(protocol["four_fold_rule"]["salt"], source_id),
                "source_asset_sha256": row["source_asset_sha256"],
                "source_surface_fingerprint_sha256": row[
                    "source_surface_fingerprint_sha256"
                ],
                "portable_source_path": row["portable_source_path"],
            }
        )
        for defect in defects:
            plan_rows.append(
                {
                    "case_id": f"mug500plus__{source_id}__{defect}",
                    "source_id": source_id,
                    "defect_type": defect,
                    "fold": fold,
                    "source_asset_sha256": row["source_asset_sha256"],
                    "portable_source_path": row["portable_source_path"],
                }
            )
    files["source_fold_assignments.csv"] = csv_bytes(
        (
            "source_id",
            "fold",
            "fold_key",
            "source_asset_sha256",
            "source_surface_fingerprint_sha256",
            "portable_source_path",
        ),
        assignment_rows,
    )
    files["generation_plan.jsonl"] = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in sorted(plan_rows, key=lambda row: row["case_id"])
    ).encode("utf-8")
    all_sources = set(source_ids)
    for fold in folds:
        dev = {source for source, assigned in fold_by_source.items() if assigned == fold}
        train = all_sources - dev
        add_ids(f"fold{fold}_dev_source_ids.txt", dev)
        add_ids(f"fold{fold}_train_source_ids.txt", train)
        add_ids(f"fold{fold}_dev_case_ids.txt", case_ids(dev, defects))
        add_ids(f"fold{fold}_train_case_ids.txt", case_ids(train, defects))

    implementation_hashes = {
        name: sha256_file(path) for name, path in sorted(implementation_paths.items())
    }
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "d4_m2_generation_and_fourfold_protocol_locked",
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "source100_files_manifest_sha256": EXPECTED_SOURCE_MANIFEST_SHA256,
        "source100_receipt_sha256": EXPECTED_SOURCE_RECEIPT_SHA256,
        "source100_assets_sha256": EXPECTED_SOURCE_ASSETS_SHA256,
        "implementation_hashes": implementation_hashes,
        "counts": {
            "sources": 100,
            "planned_cases": 400,
            "defects_per_source": 4,
            "folds": 4,
            "dev_sources_per_fold": 25,
            "train_sources_per_fold": 75,
            "dev_cases_per_fold": 100,
            "train_cases_per_fold": 300,
        },
        "source_fold_leakage": 0,
        "model_or_geometry_metrics_used_for_assignment": False,
        "manual_reassignments": [],
        "generation_started": False,
        "D4_M2_generation_authorized_next": True,
        "D4_training_authorized": False,
        "D4_candidate_selection_authorized": False,
        "protected_data_accessed": False,
        "next_step": "run_frozen_D4_M2_generation_then_separate_generation_audit",
    }
    files["d4_m2_protocol_lock_receipt.json"] = canonical_json_bytes(receipt)
    files["d4_m2_protocol_lock_report_zh.md"] = (
        "# Mamba v1.4 D4 M2 生成与来源级四折锁\n\n"
        "> 本锁未生成派生病例，未训练模型，未访问保护集。\n\n"
        "- 来源：100。\n"
        "- 计划病例：400（每来源四种缺损）。\n"
        "- 四折：每折 25 dev / 75 train 来源。\n"
        "- 每折病例：100 dev / 300 train。\n"
        "- source-skull fold leakage：0。\n"
        "- 下一步只授权冻结的 D4 M2 生成；训练与候选选择继续关闭。\n"
    ).encode("utf-8")
    files["files.sha256"] = "".join(
        f"{sha256_bytes(payload)}  {name}\n"
        for name, payload in sorted(files.items())
    ).encode("ascii")
    return files


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)).replace("\\", "/"): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical D4 M2 protocol lock")
        print(f"[locked] existing D4 M2 protocol lock is byte-identical: {output_dir}")
        return
    working = output_dir.with_name(f".{output_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Working protocol-lock directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in files.items():
        (working / name).write_bytes(payload)
    os.replace(working, output_dir)
    print(f"[saved] D4 M2 generation/fourfold protocol lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source100_qc_lock_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, required=True)
    parser.add_argument("--generator_entry", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--base_protocol", type=Path, required=True)
    parser.add_argument("--test_script", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.protocol_json.read_bytes()
    protocol = json.loads(protocol_bytes)
    validate_protocol(protocol)
    if sha256_file(args.engine) != EXPECTED_ENGINE_SHA256:
        raise RuntimeError("M2 v1 engine implementation drifted")
    if sha256_file(args.base_protocol) != EXPECTED_BASE_PROTOCOL_SHA256:
        raise RuntimeError("M2 v1 base protocol drifted")
    rows = read_source_lock(args.source100_qc_lock_dir)
    files = render_outputs(
        rows,
        protocol,
        protocol_bytes,
        {
            "base_protocol": args.base_protocol,
            "engine": args.engine,
            "generator_entry": args.generator_entry,
            "protocol_locker": Path(__file__).resolve(),
            "tests": args.test_script,
        },
    )
    write_locked(files, args.out_dir)
    print("[done] sources=100 planned_cases=400 folds=4")
    print("[authorized-next] frozen D4 M2 generation only")
    print("[locked] training=false selection=false protected=false")


if __name__ == "__main__":
    main()
