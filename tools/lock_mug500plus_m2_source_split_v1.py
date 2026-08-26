#!/usr/bin/env python3
"""Validate and immutably lock the MUG500+ M2 100/25 source-skull split."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


PROTOCOL_ID = "mug500plus-m2-d3-source-split-100-25-v1"
EXPECTED_DEFECT_TYPES = {
    "ellipsoid_large",
    "ellipsoid_medium",
    "ellipsoid_small",
    "irregular_medium",
}
REQUIRED_RECORD_FIELDS = {
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
}
DEFAULT_PROTOCOL = Path(__file__).resolve().parents[1] / "docs" / (
    "mamba_v13_d3_mug500plus_m2_source_split_100_25_protocol_v1.json"
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_bytes(rows: Sequence[Sequence[Any]]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode("utf-8")


def stable_key(salt: str, namespace: str, value: str) -> str:
    return sha256_bytes(f"{salt}|{namespace}|{value}".encode("utf-8"))


def valid_sha256(value: Any) -> bool:
    text = str(value)
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def verify_hash_manifest(directory: Path) -> None:
    manifest = directory / "files.sha256"
    if not manifest.is_file():
        raise RuntimeError(f"Missing hash manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise RuntimeError(f"Malformed hash-manifest line: {line!r}")
        expected, raw_name = parts
        name = raw_name.lstrip("*").strip()
        if Path(name).name != name:
            raise RuntimeError(f"Nested or absolute hash-manifest path: {name}")
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected.lower():
            raise RuntimeError(f"Frozen hash mismatch: {path}")


def validate_protocol(protocol: Dict[str, Any]) -> None:
    if (
        protocol.get("protocol_id") != PROTOCOL_ID
        or protocol.get("status") != "preregistered_not_generated"
    ):
        raise RuntimeError("Unexpected source-split protocol")
    lineage = protocol.get("lineage", {})
    lineage_hashes = (
        lineage.get("m1_healthy125_data_lock", {}).get("receipt_sha256"),
        lineage.get("m1_healthy125_data_lock", {}).get(
            "files_manifest_sha256"
        ),
        lineage.get("m2_generation_audit", {}).get("summary_sha256"),
        lineage.get("m2_generation_audit", {}).get("files_manifest_sha256"),
        lineage.get("m2_generation_audit", {}).get(
            "portable_manifest_sha256"
        ),
        lineage.get("protected_overlap_v21_adjudication", {}).get(
            "receipt_sha256"
        ),
        lineage.get("protected_overlap_v21_adjudication", {}).get(
            "files_manifest_sha256"
        ),
    )
    if any(not valid_sha256(value) for value in lineage_hashes):
        raise RuntimeError("Invalid frozen lineage SHA256")
    correction = protocol.get("preregistration_correction", {})
    if (
        correction.get("corrected_value_verified_from_frozen_file") is not True
        or correction.get("data_lock_output_existed_at_correction") is not False
        or correction.get("split_assignments_had_been_generated") is not False
    ):
        raise RuntimeError("Pre-generation hash correction is not transparent")
    contract = protocol.get("input_contract", {})
    if (
        contract.get("source_skulls") != 125
        or contract.get("derived_cases") != 500
        or contract.get("cases_per_source_skull") != 4
        or set(contract.get("defect_types", [])) != EXPECTED_DEFECT_TYPES
        or contract.get("source_dataset") != "mug500plus-v20-healthy125"
        or not valid_sha256(contract.get("generator_sha256"))
        or not valid_sha256(contract.get("surface_fingerprint_algorithm_sha256"))
    ):
        raise RuntimeError("Invalid source-split input contract")
    split = protocol.get("split_rule", {})
    if (
        split.get("unit") != "source_skull"
        or split.get("salt") != "mamba-v13-d3-independent-data-v1-20260811"
        or split.get("holdout_selection")
        != "25 lexicographically smallest holdout keys"
        or split.get("development_skulls") != 100
        or split.get("locked_holdout_skulls") != 25
        or split.get("development_folds") != ["A", "B", "C", "D"]
        or split.get("development_skulls_per_fold") != 25
        or split.get("same_source_skull_never_crosses_partition_or_fold")
        is not True
        or split.get("model_or_geometry_metrics_used") is not False
        or split.get("manual_reassignment_allowed") is not False
    ):
        raise RuntimeError("Invalid or mutable source-split rule")
    holdout = protocol.get("holdout_policy", {})
    if any(
        holdout.get(key) is not False
        for key in (
            "holdout_model_inference_allowed_before_method_freeze",
            "holdout_metrics_allowed_before_method_freeze",
            "holdout_visual_review_allowed_before_method_freeze",
        )
    ):
        raise RuntimeError("Holdout access is not locked")
    effect = protocol.get("lock_effect", {})
    if (
        effect.get("permit_candidate_protocol_and_config_preparation") is not True
        or effect.get("start_training_automatically") is not False
        or effect.get("training_unlocked") is not False
    ):
        raise RuntimeError("Data lock must not automatically unlock training")


def verify_upstream(
    protocol: Dict[str, Any],
    m1_lock_dir: Path,
    m2_audit_dir: Path,
    adjudication_dir: Path,
) -> Dict[str, str]:
    lineage = protocol["lineage"]
    m1 = lineage["m1_healthy125_data_lock"]
    m2 = lineage["m2_generation_audit"]
    v21 = lineage["protected_overlap_v21_adjudication"]

    verify_hash_manifest(m1_lock_dir)
    verify_hash_manifest(m2_audit_dir)
    verify_hash_manifest(adjudication_dir)
    checks = {
        "m1_data_lock_receipt": sha256_file(m1_lock_dir / "data_lock_receipt.json"),
        "m1_files_manifest": sha256_file(m1_lock_dir / "files.sha256"),
        "m2_generation_summary": sha256_file(
            m2_audit_dir / "generation_audit_summary.json"
        ),
        "m2_files_manifest": sha256_file(m2_audit_dir / "files.sha256"),
        "m2_portable_manifest": sha256_file(
            m2_audit_dir / "manifest_portable.jsonl"
        ),
        "v21_adjudication_receipt": sha256_file(
            adjudication_dir / "overlap_v21_adjudication_receipt.json"
        ),
        "v21_files_manifest": sha256_file(adjudication_dir / "files.sha256"),
    }
    expected = {
        "m1_data_lock_receipt": m1["receipt_sha256"],
        "m1_files_manifest": m1["files_manifest_sha256"],
        "m2_generation_summary": m2["summary_sha256"],
        "m2_files_manifest": m2["files_manifest_sha256"],
        "m2_portable_manifest": m2["portable_manifest_sha256"],
        "v21_adjudication_receipt": v21["receipt_sha256"],
        "v21_files_manifest": v21["files_manifest_sha256"],
    }
    mismatches = [name for name in checks if checks[name] != expected[name]]
    if mismatches:
        raise RuntimeError(f"Frozen lineage hash mismatch: {mismatches}")

    m1_receipt = json.loads(
        (m1_lock_dir / "data_lock_receipt.json").read_text(encoding="utf-8")
    )
    if (
        m1_receipt.get("data_lock_id") != m1["data_lock_id"]
        or m1_receipt.get("status") != "locked"
        or m1_receipt.get("healthy_skulls") != 125
        or m1_receipt.get("craniotomy_or_B_series_accessed") is not False
    ):
        raise RuntimeError("M1 healthy125 lock is invalid")

    generation = json.loads(
        (m2_audit_dir / "generation_audit_summary.json").read_text(
            encoding="utf-8"
        )
    )
    required_true = (
        "all_derived_hashes_verified",
        "all_geometry_gates_verified",
        "all_npz_contracts_verified",
        "portable_paths",
    )
    if (
        generation.get("audit_id") != m2["audit_id"]
        or generation.get("source_skulls") != 125
        or generation.get("derived_cases") != 500
        or any(generation.get(key) is not True for key in required_true)
        or generation.get("protected_data_used") is not False
        or generation.get("training_unlocked") is not False
    ):
        raise RuntimeError("M2 generation audit is invalid")

    adjudication = json.loads(
        (adjudication_dir / "overlap_v21_adjudication_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    if (
        adjudication.get("protocol_id") != v21["protocol_id"]
        or adjudication.get("status") != v21["required_status"]
        or adjudication.get("automatic_gate_passed") is not True
        or adjudication.get("data_split_lock_allowed") is not True
        or adjudication.get("training_unlocked") is not False
        or adjudication.get("raw_protected_arrays_reopened") is not False
        or adjudication.get("model_metrics_used") is not False
        or adjudication.get("model_predictions_used") is not False
    ):
        raise RuntimeError("v2.1 adjudication does not permit the data-lock step")
    return checks


def read_and_validate_manifest(
    path: Path, protocol: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    contract = protocol["input_contract"]
    if len(records) != contract["derived_cases"]:
        raise RuntimeError(f"Expected 500 manifest records, got {len(records)}")
    by_skull: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    case_ids = set()
    derived_hashes = set()
    source_owner = {}
    surface_owner = {}
    for index, record in enumerate(records, 1):
        missing = REQUIRED_RECORD_FIELDS.difference(record)
        if missing:
            raise RuntimeError(f"Manifest row {index} missing fields: {sorted(missing)}")
        case_id = str(record["case_id"])
        skull_id = str(record["skull_id"])
        if not case_id or case_id in case_ids or not skull_id:
            raise RuntimeError(f"Duplicate or empty case/skull ID at row {index}")
        case_ids.add(case_id)
        for field in (
            "source_asset_sha256",
            "source_surface_fingerprint_sha256",
            "surface_fingerprint_algorithm_sha256",
            "derived_case_sha256",
            "generator_sha256",
        ):
            record[field] = str(record[field]).lower()
            if not valid_sha256(record[field]):
                raise RuntimeError(f"Invalid {field} at row {index}")
        if (
            record["source_dataset"] != contract["source_dataset"]
            or record["generator_sha256"] != contract["generator_sha256"]
            or record["surface_fingerprint_algorithm_sha256"]
            != contract["surface_fingerprint_algorithm_sha256"]
        ):
            raise RuntimeError(f"Frozen M2 contract mismatch at row {index}")
        for field in ("source_asset_path", "point_path"):
            if Path(str(record[field]).replace("\\", "/")).is_absolute():
                raise RuntimeError(f"Non-portable absolute path at row {index}")
        derived_hash = record["derived_case_sha256"]
        if derived_hash in derived_hashes:
            raise RuntimeError(f"Duplicate derived hash at row {index}")
        derived_hashes.add(derived_hash)
        source_hash = record["source_asset_sha256"]
        surface_hash = record["source_surface_fingerprint_sha256"]
        if source_owner.setdefault(source_hash, skull_id) != skull_id:
            raise RuntimeError("One source asset maps to multiple skull IDs")
        if surface_owner.setdefault(surface_hash, skull_id) != skull_id:
            raise RuntimeError("One surface fingerprint maps to multiple skull IDs")
        by_skull[skull_id].append(record)

    if len(by_skull) != contract["source_skulls"]:
        raise RuntimeError(f"Expected 125 source skulls, got {len(by_skull)}")
    if len(source_owner) != 125 or len(surface_owner) != 125:
        raise RuntimeError("Source assets or surface fingerprints are not one-to-one")
    for skull_id, skull_records in by_skull.items():
        defects = {str(record["defect_type"]) for record in skull_records}
        if len(skull_records) != 4 or defects != EXPECTED_DEFECT_TYPES:
            raise RuntimeError(f"Incomplete four-family source skull: {skull_id}")
        if len({record["source_asset_sha256"] for record in skull_records}) != 1:
            raise RuntimeError(f"Multiple source assets for {skull_id}")
        if len({record["source_surface_fingerprint_sha256"] for record in skull_records}) != 1:
            raise RuntimeError(f"Multiple surface fingerprints for {skull_id}")
    return records, dict(by_skull)


def make_partitions(
    skull_ids: Sequence[str], protocol: Dict[str, Any]
) -> Tuple[set, Dict[str, str]]:
    split = protocol["split_rule"]
    salt = split["salt"]
    ordered_holdout = sorted(
        skull_ids, key=lambda value: (stable_key(salt, "holdout", value), value)
    )
    holdout = set(ordered_holdout[: split["locked_holdout_skulls"]])
    development = sorted(
        (value for value in skull_ids if value not in holdout),
        key=lambda value: (stable_key(salt, "fold", value), value),
    )
    folds = split["development_folds"]
    fold_by_skull = {
        skull_id: folds[index % len(folds)]
        for index, skull_id in enumerate(development)
    }
    return holdout, fold_by_skull


def ids_for_skulls(
    by_skull: Dict[str, List[Dict[str, Any]]], skull_ids: Sequence[str]
) -> List[str]:
    return sorted(
        str(record["case_id"])
        for skull_id in skull_ids
        for record in by_skull[skull_id]
    )


def render_report(receipt: Dict[str, Any]) -> bytes:
    counts = receipt["counts"]
    lines = [
        "# MUG500+ M2 `100/25` source-skull 数据锁报告",
        "",
        "> 本锁只使用冻结的 M2 portable manifest、上游审计凭据和 source skull ID；未使用模型或几何难度指标。",
        "",
        "## 划分结果",
        "",
        f"- source skull：{counts['total_skulls']}。",
        f"- derived case：{counts['total_cases']}。",
        f"- development：{counts['development_skulls']} skull / {counts['development_cases']} cases。",
        f"- locked holdout：{counts['locked_holdout_skulls']} skull / {counts['locked_holdout_cases']} cases。",
        f"- development folds：{counts['fold_dev_skulls']} skull。",
        f"- fold cases：{counts['fold_dev_cases']}。",
        "- source-skull partition/fold leakage：0。",
        "- 每个 skull 四种缺损完整性：通过。",
        "",
        "## 权限边界",
        "",
        f"- candidate protocol/config preparation：`{receipt['candidate_protocol_preparation_allowed']}`。",
        f"- training unlocked：`{receipt['training_unlocked']}`。",
        f"- holdout metrics consumed：`{receipt['holdout_metrics_consumed']}`。",
        "- 方法冻结前禁止 holdout 推理、指标、可视化和人工比较。",
        "- 下一步必须单独冻结 S0/S1/S2 配置、loss/query 规则、训练与选择凭据。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_outputs(
    records: Sequence[Dict[str, Any]],
    by_skull: Dict[str, List[Dict[str, Any]]],
    protocol: Dict[str, Any],
    protocol_bytes: bytes,
    upstream_hashes: Dict[str, str],
) -> Dict[str, bytes]:
    holdout, fold_by_skull = make_partitions(sorted(by_skull), protocol)
    development = set(fold_by_skull)
    files: Dict[str, bytes] = {
        "source_split_protocol_v1.json": protocol_bytes,
    }

    def add_ids(name: str, values: Sequence[str]) -> None:
        files[name] = ("\n".join(sorted(values)) + "\n").encode("utf-8")

    add_ids("development_skull_ids.txt", development)
    add_ids("locked_holdout_skull_ids.txt", holdout)
    add_ids("development_case_ids.txt", ids_for_skulls(by_skull, development))
    add_ids("locked_holdout_case_ids.txt", ids_for_skulls(by_skull, holdout))
    folds = protocol["split_rule"]["development_folds"]
    for fold in folds:
        fold_dev = {
            skull_id for skull_id, assigned in fold_by_skull.items()
            if assigned == fold
        }
        fold_train = development.difference(fold_dev)
        add_ids(f"fold{fold}_dev_skull_ids.txt", fold_dev)
        add_ids(f"fold{fold}_train_skull_ids.txt", fold_train)
        add_ids(f"fold{fold}_dev_case_ids.txt", ids_for_skulls(by_skull, fold_dev))
        add_ids(
            f"fold{fold}_train_case_ids.txt", ids_for_skulls(by_skull, fold_train)
        )

    skull_rows = [[
        "skull_id",
        "source_asset_sha256",
        "source_surface_fingerprint_sha256",
        "partition",
        "fold",
        "holdout_key",
        "fold_key",
    ]]
    case_rows = [["case_id", "skull_id", "defect_type", "partition", "fold"]]
    augmented = []
    salt = protocol["split_rule"]["salt"]
    for skull_id in sorted(by_skull):
        partition = "locked_holdout" if skull_id in holdout else "development"
        fold = "" if skull_id in holdout else fold_by_skull[skull_id]
        first = by_skull[skull_id][0]
        skull_rows.append([
            skull_id,
            first["source_asset_sha256"],
            first["source_surface_fingerprint_sha256"],
            partition,
            fold,
            stable_key(salt, "holdout", skull_id),
            stable_key(salt, "fold", skull_id),
        ])
        for record in sorted(by_skull[skull_id], key=lambda item: item["case_id"]):
            case_rows.append([
                record["case_id"],
                skull_id,
                record["defect_type"],
                partition,
                fold,
            ])
            item = dict(record)
            item["d3_partition"] = partition
            item["d3_fold"] = fold or None
            augmented.append(item)
    files["skull_assignments.csv"] = csv_bytes(skull_rows)
    files["case_assignments.csv"] = csv_bytes(case_rows)
    files["manifest_with_split.jsonl"] = "".join(
        json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n"
        for item in sorted(augmented, key=lambda value: value["case_id"])
    ).encode("utf-8")

    fold_skull_counts = collections.Counter(fold_by_skull.values())
    fold_case_counts = {
        fold: 4 * fold_skull_counts[fold] for fold in folds
    }
    receipt = {
        "protocol_id": PROTOCOL_ID,
        "status": "source_split_locked",
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "upstream_hashes": upstream_hashes,
        "source_manifest_sha256": upstream_hashes["m2_portable_manifest"],
        "split_salt": salt,
        "split_unit": "source_skull",
        "counts": {
            "total_skulls": len(by_skull),
            "total_cases": len(records),
            "development_skulls": len(development),
            "development_cases": len(ids_for_skulls(by_skull, development)),
            "locked_holdout_skulls": len(holdout),
            "locked_holdout_cases": len(ids_for_skulls(by_skull, holdout)),
            "fold_dev_skulls": {
                fold: fold_skull_counts[fold] for fold in folds
            },
            "fold_dev_cases": fold_case_counts,
        },
        "source_skull_partition_leakage": 0,
        "source_skull_fold_leakage": 0,
        "model_metrics_used": False,
        "geometry_difficulty_used": False,
        "manual_reassignments": [],
        "holdout_inference_consumed": False,
        "holdout_metrics_consumed": False,
        "holdout_visual_review_consumed": False,
        "candidate_protocol_preparation_allowed": True,
        "training_unlocked": False,
        "next_step": "freeze_D3_S0_S1_S2_candidate_configs_and_execution_protocol",
    }
    files["source_split_lock_receipt.json"] = (
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    files["source_split_lock_report_zh.md"] = render_report(receipt)
    hashes = [f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)]
    files["files.sha256"] = ("\n".join(hashes) + "\n").encode("ascii")
    return files


def write_locked(files: Dict[str, bytes], output_dir: Path) -> None:
    if output_dir.exists():
        existing = {
            str(path.relative_to(output_dir)): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing != files:
            raise RuntimeError("Refusing to overwrite a non-identical source split")
        print(f"[locked] existing source split is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, payload in files.items():
        (output_dir / name).write_bytes(payload)
    print(f"[saved] immutable 100/25 source-skull data lock: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1_data_lock_dir", type=Path, required=True)
    parser.add_argument("--m2_audit_dir", type=Path, required=True)
    parser.add_argument("--v21_adjudication_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--protocol_json", type=Path, default=DEFAULT_PROTOCOL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol_path = args.protocol_json.resolve()
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes.decode("utf-8"))
    validate_protocol(protocol)
    upstream_hashes = verify_upstream(
        protocol,
        args.m1_data_lock_dir.resolve(),
        args.m2_audit_dir.resolve(),
        args.v21_adjudication_dir.resolve(),
    )
    manifest_path = args.m2_audit_dir.resolve() / "manifest_portable.jsonl"
    records, by_skull = read_and_validate_manifest(manifest_path, protocol)
    files = render_outputs(
        records, by_skull, protocol, protocol_bytes, upstream_hashes
    )
    write_locked(files, args.output_dir.resolve())
    receipt = json.loads(files["source_split_lock_receipt.json"])
    print(
        f"[ok] development={receipt['counts']['development_skulls']} skulls/"
        f"{receipt['counts']['development_cases']} cases "
        f"holdout={receipt['counts']['locked_holdout_skulls']} skulls/"
        f"{receipt['counts']['locked_holdout_cases']} cases"
    )
    print(f"[ok] folds={receipt['counts']['fold_dev_skulls']}")
    print("[locked] holdout inference/metrics/visual review were not consumed")
    print("[locked] D3 training was not started or unlocked")


if __name__ == "__main__":
    main()
