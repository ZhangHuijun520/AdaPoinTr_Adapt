#!/usr/bin/env python
"""Observation-only contact-support replay for frozen D2.2 checkpoints."""

import argparse
import csv
import hashlib
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.spatial import cKDTree
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "../"))

from datasets import build_dataset_from_cfg  # noqa: E402
from tools import builder  # noqa: E402
from utils.config import cfg_from_yaml_file  # noqa: E402
from utils.mamba_d22_contact_support import (  # noqa: E402
    DEFAULT_BANDS,
    band_key,
    distance_profile,
)
from utils.skullfix_metrics import normalized_to_world  # noqa: E402


POSTHOC_PROTOCOL_SHA256 = (
    "04313b68281eeba3028eba5b8ee02166c1ab2b9e72a1f5f2f745ffb88a301c65"
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records_root", type=Path, required=True)
    parser.add_argument("--negative_receipt", type=Path, required=True)
    parser.add_argument("--posthoc_protocol", type=Path, required=True)
    parser.add_argument("--development_case_ids", type=Path, required=True)
    parser.add_argument("--confirmation_case_ids", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--bands_mm",
        default=",".join(str(value) for value in DEFAULT_BANDS),
    )
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path, expected=None):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256_file(path)
    if expected is not None and actual != expected:
        raise RuntimeError(f"SHA256 mismatch: {path}")
    return actual


def verify_sidecar(path):
    sidecar = Path(str(path) + ".sha256")
    fields = sidecar.read_text(encoding="ascii").split()
    if len(fields) < 2 or Path(fields[1]).name != Path(path).name:
        raise RuntimeError(f"Invalid SHA256 sidecar: {sidecar}")
    return verify(path, fields[0])


def read_case_ids(path):
    values = {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    if not values:
        raise RuntimeError(f"Empty case-ID file: {path}")
    return values


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_locked(path, rows):
    if not rows:
        raise RuntimeError(f"No rows for {path}")
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=list(rows[0]), lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    encoded = buffer.getvalue().encode("utf-8")
    if path.exists() and path.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite non-identical replay: {path}")
    path.write_bytes(encoded)


def write_text_locked(path, text):
    encoded = text.encode("utf-8")
    if path.exists() and path.read_bytes() != encoded:
        raise RuntimeError(f"Refusing to overwrite non-identical replay: {path}")
    path.write_bytes(encoded)


def load_full_sample(dataset, index):
    record = dataset.get_record(index)
    point_path = Path(record["point_path"])
    if not point_path.is_absolute():
        point_path = Path(dataset.data_root) / point_path
    with np.load(point_path, allow_pickle=False) as sample:
        arrays = {
            "partial": sample["partial"].astype(np.float32, copy=True),
            "implant": sample["implant"].astype(np.float32, copy=True),
        }
    return record, arrays


def prefixed(values, prefix):
    return {f"{prefix}_{key}": value for key, value in values.items()}


def main():
    args = parse_args()
    bands = tuple(
        float(item.strip()) for item in args.bands_mm.split(",") if item.strip()
    )
    if bands != DEFAULT_BANDS:
        raise RuntimeError(
            f"Post-hoc bands are frozen as {DEFAULT_BANDS}, got {bands}"
        )
    negative_hash = verify_sidecar(args.negative_receipt)
    negative = json.loads(args.negative_receipt.read_text(encoding="utf-8"))
    posthoc_hash = verify(args.posthoc_protocol)
    if posthoc_hash != POSTHOC_PROTOCOL_SHA256:
        raise RuntimeError(
            "Post-hoc protocol differs from the pre-replay frozen declaration"
        )
    posthoc = json.loads(args.posthoc_protocol.read_text(encoding="utf-8"))
    if negative.get("winner") is not None:
        raise RuntimeError("Post-hoc replay requires frozen winner=None")
    if negative.get("round_b_allowed") is not False:
        raise RuntimeError("Post-hoc replay requires Round B to remain blocked")
    integrity = posthoc["integrity"]
    required_flags = {
        "post_hoc": True,
        "observation_only": True,
        "selection_inert": True,
        "may_change_d22_winner": False,
        "may_unlock_round_b": False,
        "confirmation20_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
    }
    if any(integrity.get(key) != value for key, value in required_flags.items()):
        raise RuntimeError("Invalid post-hoc integrity declaration")

    development_ids = read_case_ids(args.development_case_ids)
    confirmation_ids = read_case_ids(args.confirmation_case_ids)
    if development_ids & confirmation_ids:
        raise RuntimeError("Development and confirmation case sets overlap")
    if len(development_ids) != 420:
        raise RuntimeError(
            f"Expected 420 development case IDs, found {len(development_ids)}"
        )

    record_paths = sorted(args.records_root.glob("*/run_record.json"))
    if len(record_paths) != 12:
        raise RuntimeError(f"Expected 12 run records, found {len(record_paths)}")
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    rows = []
    replay_count_deltas = []
    observed_by_candidate = {candidate: set() for candidate in ("R0", "R1", "R2")}
    input_hashes = {
        str(args.negative_receipt): negative_hash,
        str(args.posthoc_protocol): posthoc_hash,
        str(args.development_case_ids): verify(args.development_case_ids),
        str(args.confirmation_case_ids): verify(args.confirmation_case_ids),
    }

    for record_path in record_paths:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        candidate = record["candidate"]
        fold = record["fold"]
        seed = int(record["seed"])
        if candidate not in observed_by_candidate or seed != 0:
            raise RuntimeError(f"Unexpected run record: {record_path}")
        config_artifact = record["artifacts"]["config"]
        checkpoint_artifact = record["artifacts"]["checkpoint"]
        metrics_artifact = record["artifacts"]["metrics_csv"]
        config_path = Path(config_artifact["path"])
        checkpoint_path = Path(checkpoint_artifact["path"])
        metrics_path = Path(metrics_artifact["path"])
        for path, artifact in (
            (config_path, config_artifact),
            (checkpoint_path, checkpoint_artifact),
            (metrics_path, metrics_artifact),
        ):
            input_hashes[str(path)] = verify(path, artifact["sha256"])
        input_hashes[str(record_path)] = verify(record_path)
        frozen_rows = {
            row["case_id"]: row for row in read_csv(metrics_path)
        }

        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        config = cfg_from_yaml_file(str(config_path))
        dataset_cfg = config.dataset.val
        dataset = build_dataset_from_cfg(dataset_cfg._base_, dataset_cfg.others)
        if len(dataset) != 105:
            raise RuntimeError(f"{candidate}/fold{fold}: expected 105 cases")
        model = builder.model_builder(config.model)
        builder.load_model(model, str(checkpoint_path))
        model.to(device).eval()

        with torch.no_grad():
            for index in tqdm(
                range(len(dataset)),
                desc=f"D2.2 support {candidate}/fold{fold}",
                dynamic_ncols=True,
            ):
                _, case_id, data = dataset[index]
                partial, _ = data
                output = model(partial.unsqueeze(0).to(device))
                coarse = output[0][0].detach().cpu().numpy()
                dense = output[-1][0].detach().cpu().numpy()
                if not np.isfinite(coarse).all() or not np.isfinite(dense).all():
                    raise RuntimeError(f"Non-finite model output: {case_id}")

                source, arrays = load_full_sample(dataset, index)
                case_id = str(case_id)
                if case_id not in development_ids:
                    raise RuntimeError(f"Protected/non-development case: {case_id}")
                if case_id in confirmation_ids:
                    raise RuntimeError(f"Confirmation case accessed: {case_id}")
                if source.get("official_split") != "train":
                    raise RuntimeError(f"Non-train official split: {case_id}")
                if source.get("monitor_split") == "monitor":
                    raise RuntimeError(f"Old monitor case accessed: {case_id}")
                observed_by_candidate[candidate].add(case_id)

                norm = source["normalization"]
                centroid, scale = norm["centroid"], norm["scale"]
                partial_world = normalized_to_world(
                    arrays["partial"], centroid, scale
                )
                reference_world = normalized_to_world(
                    arrays["implant"], centroid, scale
                )
                defective_to_reference = np.asarray(
                    cKDTree(reference_world).query(partial_world, k=1)[0],
                    dtype=np.float64,
                )
                reference_rim_2mm = partial_world[
                    defective_to_reference <= 2.0
                ]
                if reference_rim_2mm.shape[0] == 0:
                    raise RuntimeError(f"Empty 2 mm reference rim: {case_id}")
                reference_counts = {
                    f"reference_rim_points_at_{band_key(band)}": int(
                        np.count_nonzero(defective_to_reference <= band)
                    )
                    for band in bands
                }
                coarse_profile = distance_profile(
                    coarse,
                    partial_world,
                    reference_rim_2mm,
                    centroid,
                    scale,
                    bands,
                )
                dense_profile = distance_profile(
                    dense,
                    partial_world,
                    reference_rim_2mm,
                    centroid,
                    scale,
                    bands,
                )
                frozen = frozen_rows[case_id]
                frozen_count = int(float(frozen["rim_predicted_rim_points"]))
                replay_count = dense_profile[
                    "predicted_rim_points_at_2mm"
                ]
                replay_count_deltas.append(abs(replay_count - frozen_count))
                if replay_count != frozen_count:
                    raise RuntimeError(
                        f"2 mm support replay mismatch {candidate}/{case_id}: "
                        f"frozen={frozen_count}, replay={replay_count}"
                    )
                rows.append({
                    "candidate": candidate,
                    "fold": fold,
                    "seed": seed,
                    "case_id": case_id,
                    "skull_id": source.get("skull_id", ""),
                    "defect_type": source.get("defect_type", ""),
                    "frozen_dense_predicted_rim_points_at_2mm": frozen_count,
                    "frozen_zero_contact_at_2mm": int(frozen_count == 0),
                    **reference_counts,
                    **prefixed(coarse_profile, "coarse"),
                    **prefixed(dense_profile, "dense"),
                })
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    for candidate, case_ids in observed_by_candidate.items():
        if case_ids != development_ids:
            raise RuntimeError(
                f"{candidate}: replay case set differs from development84"
            )
    if len(rows) != 1260:
        raise RuntimeError(f"Expected 1260 replay rows, found {len(rows)}")

    rows.sort(key=lambda row: (row["candidate"], row["case_id"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_case_path = args.output_dir / "contact_support_per_case.csv"
    write_csv_locked(per_case_path, rows)
    summary = {
        "replay_version": "mamba-v12-d22-contact-support-replay-v1",
        "records": len(rows),
        "candidates": ["R0", "R1", "R2"],
        "cases_per_candidate": 420,
        "stages": ["coarse", "dense"],
        "bands_mm": list(bands),
        "maximum_frozen_dense_2mm_count_delta": max(replay_count_deltas),
        "post_hoc": True,
        "observation_only": True,
        "selection_inert": True,
        "winner": None,
        "round_b_allowed": False,
        "protected_splits_accessed": False,
        "confirmation20_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
        "negative_receipt_sha256": negative_hash,
        "posthoc_protocol_sha256": posthoc_hash,
        "input_sha256": dict(sorted(input_hashes.items())),
        "outputs": {"per_case": per_case_path.name},
    }
    summary_path = args.output_dir / "contact_support_replay_summary.json"
    write_text_locked(
        summary_path,
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )
    for path in (per_case_path, summary_path):
        Path(str(path) + ".sha256").write_text(
            f"{sha256_file(path)}  {path.name}\n", encoding="ascii"
        )
    print(f"[saved] {per_case_path}")
    print(f"[saved] {summary_path}")
    print("[done] post-hoc contact-support replay records=1260")
    print("[locked] selection unchanged; Round B remains forbidden")
    print("[locked] no protected split was accessed")


if __name__ == "__main__":
    main()
