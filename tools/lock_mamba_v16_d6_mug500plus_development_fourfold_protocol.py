#!/usr/bin/env python3
"""Freeze D6 development100 synthetic generation and source-level fourfolds."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


PROTOCOL_ID = "mamba-v16-d6-mug500plus-development-generation-fourfold-v1"
DEVELOPMENT_LOCK_PROTOCOL_ID = "mamba-v16-d6-development100-final-qc-lock-v1"
ACQUISITION_LOCK_PROTOCOL_ID = (
    "mamba-v16-d6-mug500plus-source125-terminal-acquisition-v1"
)
EXPECTED_DEVELOPMENT_MANIFEST_SHA256 = (
    "ba62bbe839e044d98a1f73be2fa2d0f2973ca771ab9e0911548dd77e81376ed2"
)
EXPECTED_DEVELOPMENT_RECEIPT_SHA256 = (
    "97e26338d4d4bff743a20e0a830ca6e34f1c64f8dfd0de5115d91f22aec93cef"
)
EXPECTED_DEVELOPMENT_ASSETS_SHA256 = (
    "a1f06fba94158074a116033d62b37c267479c7f630a10bee94c0383980083d0c"
)
EXPECTED_ACQUISITION_MANIFEST_SHA256 = (
    "d8509c44dd36575d46784972f70ec8f808754d3ffa84f390655ef3e5467c0fc1"
)
EXPECTED_ACQUISITION_RECEIPT_SHA256 = (
    "865b9fb30ef52c532ae5dd4c5ff18405833dee0570144ee94957cf5c460dab71"
)
EXPECTED_PARTITION_HASHES = {
    "development": "833595b000732cb56a3d729fcb1121a0c70018bf030505aa9584020498a2cc68",
    "proposal_confirmation": "7adb4a0dcf6eb7897d66110f32f425fa36a5c5561f729bd173200bcd1386d632",
}
PARTITION_FILES = {
    "development": "d6_development100_ids.txt",
    "proposal_confirmation": "d6_proposal_confirmation25_ids.txt",
}
EXPECTED_ZERO_STEP_REPORT_SHA256 = (
    "7f093b50e660e4828bec85b5c0f75ce2f6dc487198c648516b933969ff267b85"
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
    if not manifest.is_file() or sha256_file(manifest) != expected_manifest_hash:
        raise RuntimeError(f"Frozen manifest drifted: {directory}")
    for raw in manifest.read_text(encoding="ascii").splitlines():
        expected, name = raw.split(maxsplit=1)
        name = name.lstrip("*")
        if Path(name).name != name:
            raise RuntimeError(f"Nested manifest path is forbidden: {name}")
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Hash-chain failure: {path}")


def read_ids(path: Path, expected_hash: str, expected_count: int) -> List[str]:
    if sha256_file(path) != expected_hash:
        raise RuntimeError(f"Frozen ID file drifted: {path.name}")
    values = [line.strip() for line in path.read_text(encoding="ascii").splitlines()]
    if len(values) != expected_count or len(set(values)) != expected_count:
        raise RuntimeError(f"Unexpected membership in {path.name}")
    return values


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if (
        protocol.get("protocol_id") != PROTOCOL_ID
        or protocol.get("status") != "preregistered_generation_not_run"
    ):
        raise RuntimeError("Unexpected D6 development generation protocol")
    lineage = protocol.get("lineage", {})
    development = lineage.get("development100_qc_lock", {})
    acquisition = lineage.get("source125_acquisition_lock", {})
    engine = lineage.get("m2_v1_engine", {})
    zero_step = lineage.get("d6a_zero_step", {})
    if (
        development.get("files_manifest_sha256")
        != EXPECTED_DEVELOPMENT_MANIFEST_SHA256
        or development.get("receipt_sha256")
        != EXPECTED_DEVELOPMENT_RECEIPT_SHA256
        or development.get("assets_csv_sha256")
        != EXPECTED_DEVELOPMENT_ASSETS_SHA256
        or development.get("required_sources") != 100
        or development.get("required_qc_pass") != 100
        or development.get("required_prior_overlap") != 0
        or acquisition.get("files_manifest_sha256")
        != EXPECTED_ACQUISITION_MANIFEST_SHA256
        or acquisition.get("receipt_sha256") != EXPECTED_ACQUISITION_RECEIPT_SHA256
        or acquisition.get("development100_ids_sha256")
        != EXPECTED_PARTITION_HASHES["development"]
        or acquisition.get("proposal_confirmation25_ids_sha256")
        != EXPECTED_PARTITION_HASHES["proposal_confirmation"]
        or acquisition.get("proposal_confirmation_accessed") is not False
        or zero_step.get("complete_result_sha256")
        != EXPECTED_ZERO_STEP_REPORT_SHA256
        or zero_step.get("D6_cases_accessed") != 0
        or zero_step.get("model_updates") != 0
        or engine.get("implementation_sha256") != EXPECTED_ENGINE_SHA256
        or engine.get("base_protocol_sha256") != EXPECTED_BASE_PROTOCOL_SHA256
        or engine.get("inherited_sections_must_be_unmodified") is not True
    ):
        raise RuntimeError("D6 lineage contract changed")
    generation = protocol.get("development_generation", {})
    if (
        generation.get("source_skulls") != 100
        or generation.get("defects_per_source") != 4
        or generation.get("expected_cases") != 400
        or generation.get("overwrite_allowed") is not False
    ):
        raise RuntimeError("D6 generation contract changed")
    defects = protocol.get("defect_contract", {})
    if (
        tuple(defects.get("defect_types", ())) != EXPECTED_DEFECT_TYPES
        or defects.get("all_four_required_per_source") is not True
    ):
        raise RuntimeError("D6 defect contract changed")
    folds = protocol.get("four_fold_rule", {})
    if (
        folds.get("salt")
        != "mamba-v16-d6-development100-source-fourfold-v1-20260903"
        or folds.get("folds") != ["A", "B", "C", "D"]
        or folds.get("dev_sources_per_fold") != 25
        or folds.get("train_sources_per_fold") != 75
        or folds.get("dev_cases_per_fold") != 100
        or folds.get("train_cases_per_fold") != 300
        or folds.get("same_source_four_cases_share_fold") is not True
        or folds.get("model_or_geometry_metrics_used") is not False
        or folds.get("manual_reassignment_allowed") is not False
    ):
        raise RuntimeError("D6 four-fold rule changed")
    sealed = protocol.get("sealed_partition_contract", {})
    if (
        sealed.get("proposal_confirmation_sources") != 25
        or sealed.get("geometry_may_be_read_by_this_stage") is not False
        or sealed.get("archives_may_be_extracted_by_this_stage") is not False
        or sealed.get("derived_cases_may_be_generated_by_this_stage") is not False
    ):
        raise RuntimeError("D6 sealed-partition boundary changed")
    effect = protocol.get("lock_effect", {})
    if (
        effect.get("D6_development_synthetic_generation_authorized_after_protocol_lock")
        is not True
        or effect.get("D6_development_synthetic_generation_started_by_lock") is not False
        or effect.get("D6A_R0_R1_implementation_frozen") is not True
        or any(
            effect.get(key) is not False
            for key in (
                "D6_gradient_calibration_authorized",
                "D6A_training_authorized",
                "D6_seed1_authorized",
                "D6B_training_authorized",
                "D6_candidate_selection_authorized",
                "proposal_confirmation_access_authorized",
                "official_test_access_authorized",
            )
        )
    ):
        raise RuntimeError("D6 authorization boundary changed")


def read_lineage(
    development_lock: Path, acquisition_lock: Path
) -> Tuple[List[Dict[str, str]], Dict[str, List[str]]]:
    verify_flat_manifest(development_lock, EXPECTED_DEVELOPMENT_MANIFEST_SHA256)
    verify_flat_manifest(acquisition_lock, EXPECTED_ACQUISITION_MANIFEST_SHA256)
    development_receipt_path = development_lock / "development100_qc_lock_receipt.json"
    acquisition_receipt_path = acquisition_lock / "source_acquisition_lock_receipt.json"
    assets_path = development_lock / "development100_assets.csv"
    if sha256_file(development_receipt_path) != EXPECTED_DEVELOPMENT_RECEIPT_SHA256:
        raise RuntimeError("Development100 receipt drifted")
    if sha256_file(acquisition_receipt_path) != EXPECTED_ACQUISITION_RECEIPT_SHA256:
        raise RuntimeError("Source125 acquisition receipt drifted")
    if sha256_file(assets_path) != EXPECTED_DEVELOPMENT_ASSETS_SHA256:
        raise RuntimeError("Development100 assets CSV drifted")
    development_receipt = json.loads(development_receipt_path.read_text(encoding="utf-8"))
    acquisition_receipt = json.loads(acquisition_receipt_path.read_text(encoding="utf-8"))
    if (
        development_receipt.get("protocol_id") != DEVELOPMENT_LOCK_PROTOCOL_ID
        or development_receipt.get("status") != "development100_qc_locked_complete"
        or development_receipt.get("counts")
        != {
            "batches": 3,
            "prior_geometry_sources_checked": 325,
            "prior_source_ids_checked": 375,
            "qc_fail": 0,
            "qc_pass": 100,
            "sources": 100,
        }
        or development_receipt.get("global_duplicate_and_overlap_gates_passed") is not True
        or development_receipt.get("proposal_confirmation_accessed") is not False
        or development_receipt.get("protected_data_accessed") is not False
        or development_receipt.get("synthetic_generation_authorized") is not False
        or development_receipt.get("D6_data_generation_protocol_preparation_authorized_next")
        is not True
    ):
        raise RuntimeError("Development100 receipt semantics are invalid")
    if (
        acquisition_receipt.get("protocol_id") != ACQUISITION_LOCK_PROTOCOL_ID
        or acquisition_receipt.get("status")
        != "source125_terminal_two_partition_acquisition_locked"
        or acquisition_receipt.get("proposal_confirmation_extraction_authorized")
        is not False
        or acquisition_receipt.get("protected_data_accessed") is not False
    ):
        raise RuntimeError("Source125 acquisition semantics are invalid")
    with assets_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if not REQUIRED_ASSET_FIELDS.issubset(reader.fieldnames or []):
            raise RuntimeError("Development100 assets schema is incomplete")
    ids = [row["case_id"] for row in rows]
    if len(rows) != 100 or len(set(ids)) != 100:
        raise RuntimeError("Development assets are not exactly 100 unique sources")
    if any(row["qc_pass"].lower() != "true" for row in rows):
        raise RuntimeError("Development assets contain a QC failure")
    partitions = {
        name: read_ids(
            acquisition_lock / PARTITION_FILES[name],
            EXPECTED_PARTITION_HASHES[name],
            100 if name == "development" else 25,
        )
        for name in PARTITION_FILES
    }
    if set(ids) != set(partitions["development"]):
        raise RuntimeError("Development assets and acquisition membership differ")
    if set(partitions["development"]) & set(partitions["proposal_confirmation"]):
        raise RuntimeError("D6 source partitions overlap")
    return sorted(rows, key=lambda row: row["case_id"]), partitions


def assign_folds(source_ids: Sequence[str], protocol: Dict[str, Any]) -> Dict[str, str]:
    if len(source_ids) != 100 or len(set(source_ids)) != 100:
        raise RuntimeError("Four-fold assignment requires 100 unique development IDs")
    rule = protocol["four_fold_rule"]
    ordered = sorted(
        source_ids,
        key=lambda source_id: (stable_key(rule["salt"], source_id), source_id),
    )
    folds = rule["folds"]
    result = {source_id: folds[index % 4] for index, source_id in enumerate(ordered)}
    if {fold: list(result.values()).count(fold) for fold in folds} != {
        fold: 25 for fold in folds
    }:
        raise RuntimeError("Unexpected D6 fold counts")
    return result


def case_ids(source_ids: Iterable[str], defect_types: Sequence[str]) -> List[str]:
    return sorted(
        f"mug500plus__{source_id}__{defect}"
        for source_id in source_ids
        for defect in defect_types
    )


def render_outputs(
    rows: Sequence[Dict[str, str]],
    partitions: Dict[str, List[str]],
    protocol: Dict[str, Any],
    protocol_bytes: bytes,
    implementation_paths: Dict[str, Path],
) -> Dict[str, bytes]:
    source_ids = [row["case_id"] for row in rows]
    fold_by_source = assign_folds(source_ids, protocol)
    folds = protocol["four_fold_rule"]["folds"]
    defects = protocol["defect_contract"]["defect_types"]
    files: Dict[str, bytes] = {
        "d6_development_generation_fourfold_protocol_v1.json": protocol_bytes
    }

    def add_ids(name: str, values: Iterable[str]) -> None:
        files[name] = ("\n".join(sorted(values)) + "\n").encode("ascii")

    add_ids("development100_ids.txt", source_ids)
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
    files["sealed_partition_bindings.json"] = canonical_json_bytes(
        {
            "proposal_confirmation": {
                "source_count": len(partitions["proposal_confirmation"]),
                "ids_sha256": EXPECTED_PARTITION_HASHES["proposal_confirmation"],
                "geometry_accessed": False,
                "archive_extracted": False,
                "derived_cases_generated": False,
            },
        }
    )
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "d6_development_generation_and_fourfold_protocol_locked",
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "development100_files_manifest_sha256": EXPECTED_DEVELOPMENT_MANIFEST_SHA256,
        "development100_receipt_sha256": EXPECTED_DEVELOPMENT_RECEIPT_SHA256,
        "development100_assets_sha256": EXPECTED_DEVELOPMENT_ASSETS_SHA256,
        "source125_acquisition_manifest_sha256": EXPECTED_ACQUISITION_MANIFEST_SHA256,
        "source125_acquisition_receipt_sha256": EXPECTED_ACQUISITION_RECEIPT_SHA256,
        "partition_id_file_sha256": EXPECTED_PARTITION_HASHES,
        "implementation_hashes": {
            name: sha256_file(path) for name, path in sorted(implementation_paths.items())
        },
        "counts": {
            "development_sources": 100,
            "planned_development_cases": 400,
            "defects_per_source": 4,
            "folds": 4,
            "dev_sources_per_fold": 25,
            "train_sources_per_fold": 75,
            "dev_cases_per_fold": 100,
            "train_cases_per_fold": 300,
            "proposal_confirmation_sources_sealed": 25,
        },
        "source_fold_leakage": 0,
        "model_or_geometry_metrics_used_for_assignment": False,
        "manual_reassignments": [],
        "generation_started": False,
        "D6_development_synthetic_generation_authorized_next": True,
        "D6A_R0_R1_implementation_frozen": True,
        "D6_gradient_calibration_authorized": False,
        "D6A_training_authorized": False,
        "D6_seed1_authorized": False,
        "D6B_training_authorized": False,
        "D6_candidate_selection_authorized": False,
        "proposal_confirmation_accessed": False,
        "official_test_accessed": False,
        "next_step": "run_frozen_D6_development400_generation_then_separate_audit",
    }
    files["d6_development_protocol_lock_receipt.json"] = canonical_json_bytes(receipt)
    files["d6_development_protocol_lock_report_zh.md"] = (
        "# Mamba v1.6 D6 development100 合成生成与来源级四折锁\n\n"
        "> 本锁未生成病例、未训练模型、未访问 confirmation25。\n\n"
        "- development 来源：100。\n"
        "- 计划病例：400（每来源四种冻结缺损）。\n"
        "- 四折：每折 25 dev / 75 train 来源，100 dev / 300 train 病例。\n"
        "- source-skull fold leakage：0。\n"
        "- proposal-confirmation25：仅绑定 ID 哈希，保持未访问。\n"
        "- 下一步只授权冻结的 development400 生成；校准、训练、seed-1 和选择继续关闭。\n"
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
            raise RuntimeError("Refusing to overwrite a non-identical D6 protocol lock")
        print(f"[locked] existing D6 protocol lock is byte-identical: {output_dir}")
        return
    working = output_dir.with_name(f".{output_dir.name}.working")
    if working.exists():
        raise RuntimeError(f"Working protocol-lock directory requires inspection: {working}")
    working.mkdir(parents=True)
    for name, payload in files.items():
        path = working / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    os.replace(working, output_dir)
    print(f"[saved] D6 development generation/fourfold protocol lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development100_qc_lock_dir", type=Path, required=True)
    parser.add_argument("--source125_acquisition_lock_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, required=True)
    parser.add_argument("--generator_entry", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--base_protocol", type=Path, required=True)
    parser.add_argument("--zero_step_report", type=Path, required=True)
    parser.add_argument("--test_script", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_bytes = args.protocol_json.read_bytes()
    protocol = json.loads(protocol_bytes)
    validate_protocol(protocol)
    if sha256_file(args.engine) != EXPECTED_ENGINE_SHA256:
        raise RuntimeError("M2 v1 engine drifted")
    if sha256_file(args.base_protocol) != EXPECTED_BASE_PROTOCOL_SHA256:
        raise RuntimeError("M2 v1 base protocol drifted")
    if sha256_file(args.zero_step_report) != EXPECTED_ZERO_STEP_REPORT_SHA256:
        raise RuntimeError("D6-A zero-step complete result drifted")
    rows, partitions = read_lineage(
        args.development100_qc_lock_dir, args.source125_acquisition_lock_dir
    )
    files = render_outputs(
        rows,
        partitions,
        protocol,
        protocol_bytes,
        {
            "base_protocol": args.base_protocol,
            "engine": args.engine,
            "generator_entry": args.generator_entry,
            "protocol_locker": Path(__file__).resolve(),
            "tests": args.test_script,
            "zero_step_report": args.zero_step_report,
        },
    )
    write_locked(files, args.out_dir)
    print("[done] development_sources=100 planned_cases=400 folds=4")
    print("[authorized-next] frozen D6 development400 generation only")
    print("[locked] generation_not_started=true calibration=false training=false seed1=false confirmation=false")


if __name__ == "__main__":
    main()
