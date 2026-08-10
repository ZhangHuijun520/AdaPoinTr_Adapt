#!/usr/bin/env python
"""Verify the frozen D2.2 negative-result and post-hoc archive payload."""

import argparse
import hashlib
import json
from pathlib import Path


CANDIDATES = ("R0", "R1", "R2")
FOLDS = ("A", "B", "C", "D")
D22_ROOT = Path("logs/skullbreak_mamba_v12_d22_local_rim")
SELECTION = D22_ROOT / "round_a_selection.json"
NEGATIVE_ROOT = D22_ROOT / "frozen_negative_result_v1"
POSTHOC_ROOT = D22_ROOT / "posthoc_contact_support_v1"
REPLAY_SUMMARY = POSTHOC_ROOT / "replay/contact_support_replay_summary.json"
ANALYSIS_SUMMARY = POSTHOC_ROOT / "analysis/contact_support_posthoc_summary.json"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository or restored archive root.",
    )
    parser.add_argument(
        "--write_checkpoint_list",
        type=Path,
        help="Optionally write the 12 checkpoint paths, one per line.",
    )
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(root, relative):
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f"Required file is missing: {relative}")
    return path


def load_json(root, relative):
    path = require_file(root, relative)
    return path, json.loads(path.read_text(encoding="utf-8"))


def resolve_manifest_entry(root, manifest, name):
    name = name.lstrip("*")
    repository_relative = root / name
    if repository_relative.is_file():
        return repository_relative
    manifest_relative = manifest.parent / name
    if manifest_relative.is_file():
        return manifest_relative
    raise FileNotFoundError(
        f"Manifest entry is missing: manifest={manifest} entry={name}"
    )


def verify_sha_manifest(root, relative):
    manifest = require_file(root, relative)
    checked = 0
    for line_number, line in enumerate(
        manifest.read_text(encoding="ascii").splitlines(), start=1
    ):
        if not line.strip():
            continue
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or len(fields[0]) != 64:
            raise RuntimeError(
                f"Invalid SHA256 line: {relative}:{line_number}"
            )
        expected, name = fields
        target = resolve_manifest_entry(root, manifest, name.strip())
        actual = sha256_file(target)
        if actual.lower() != expected.lower():
            raise RuntimeError(f"SHA256 mismatch: {target}")
        checked += 1
    if checked == 0:
        raise RuntimeError(f"Empty SHA256 manifest: {relative}")
    return checked


def verify_file_sidecar(root, relative):
    path = require_file(root, relative)
    sidecar = require_file(root, Path(str(relative) + ".sha256"))
    fields = sidecar.read_text(encoding="ascii").split()
    if len(fields) < 2 or len(fields[0]) != 64:
        raise RuntimeError(f"Invalid SHA256 sidecar: {sidecar}")
    if Path(fields[1]).name != path.name:
        raise RuntimeError(f"SHA256 sidecar names another file: {sidecar}")
    if sha256_file(path).lower() != fields[0].lower():
        raise RuntimeError(f"SHA256 mismatch: {path}")
    return path


def verify_record_artifacts(root, record):
    artifacts = record.get("artifacts", {})
    required = {
        "config",
        "checkpoint",
        "metrics_csv",
        "metrics_summary",
        "efficiency",
        "training_log",
        "preflight_receipt",
        "protocol",
        "implementation_amendment",
    }
    missing = sorted(required - set(artifacts))
    if missing:
        raise RuntimeError(f"Run record artifact keys are missing: {missing}")
    for name, artifact in artifacts.items():
        path = require_file(root, Path(artifact["path"]))
        actual = sha256_file(path)
        if actual != artifact["sha256"]:
            raise RuntimeError(
                f"Run-record artifact hash mismatch: {name}={path}"
            )


def verify_selection(root):
    selection_path = verify_file_sidecar(root, SELECTION)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    checks = {
        "locked": selection.get("locked") is True,
        "winner": selection.get("winner") is None,
        "round_b_allowed": selection.get("round_b_allowed") is False,
        "protected_splits_accessed": (
            selection.get("protected_splits_accessed") is False
        ),
        "eligible_order": selection.get("eligible_order") == [],
    }
    for candidate, expected_nonfinite in (("R0", 2), ("R1", 2), ("R2", 3)):
        summary = selection["summaries"][candidate]
        checks[f"{candidate}_nonfinite"] = (
            summary.get("nonfinite_case_count") == expected_nonfinite
        )
        if candidate != "R0":
            failed = sorted(
                gate
                for gate, passed in summary.get("gates", {}).items()
                if not passed
            )
            checks[f"{candidate}_failed_gate"] = failed == ["nonfinite"]
            checks[f"{candidate}_eligible"] = summary.get("eligible") is False
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError("Selection semantic checks failed: " + ", ".join(failed))
    for value, expected in selection.get("input_sha256", {}).items():
        path = require_file(root, Path(value))
        if sha256_file(path) != expected:
            raise RuntimeError(f"Selection input hash mismatch: {path}")
    return selection


def verify_negative_freeze(root):
    verify_sha_manifest(root, NEGATIVE_ROOT / "files.sha256.sha256")
    verify_sha_manifest(root, NEGATIVE_ROOT / "files.sha256")
    receipt_path = verify_file_sidecar(
        root, NEGATIVE_ROOT / "negative_result_receipt.json"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks = {
        "winner": receipt.get("winner") is None,
        "round_b_allowed": receipt.get("round_b_allowed") is False,
        "selection_locked": receipt.get("selection_locked") is True,
        "run_records": receipt.get("run_records") == 12,
        "protected_splits_accessed": (
            receipt.get("protected_splits_accessed") is False
        ),
        "confirmation20_used": receipt.get("confirmation20_used") is False,
        "old_monitor_used": receipt.get("old_monitor_used") is False,
        "official_test_used": receipt.get("official_test_used") is False,
        "selection_inert": (
            receipt.get("post_hoc_replay_may_change_selection") is False
        ),
    }
    expected_counts = {"R0": 2, "R1": 2, "R2": 3}
    observed = receipt.get("nonfinite_zero_contact_cases", {})
    checks["zero_contact_counts"] = {
        candidate: len(observed.get(candidate, [])) for candidate in CANDIDATES
    } == expected_counts
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError(
            "Negative-freeze semantic checks failed: " + ", ".join(failed)
        )
    return receipt


def verify_posthoc(root):
    verify_sha_manifest(
        root, POSTHOC_ROOT / "posthoc_tree_sha256.txt.sha256"
    )
    verify_sha_manifest(root, POSTHOC_ROOT / "posthoc_tree_sha256.txt")
    replay_path = verify_file_sidecar(root, REPLAY_SUMMARY)
    analysis_path = verify_file_sidecar(root, ANALYSIS_SUMMARY)
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    common = {
        "post_hoc": True,
        "observation_only": True,
        "selection_inert": True,
        "winner": None,
        "round_b_allowed": False,
        "protected_splits_accessed": False,
        "confirmation20_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
    }
    failed = []
    for label, payload in (("replay", replay), ("analysis", analysis)):
        for key, expected in common.items():
            if payload.get(key) != expected:
                failed.append(f"{label}_{key}")
    if replay.get("records") != 1260:
        failed.append("replay_records")
    if replay.get("cases_per_candidate") != 420:
        failed.append("replay_cases_per_candidate")
    if replay.get("maximum_frozen_dense_2mm_count_delta") != 0:
        failed.append("replay_equivalence")
    if analysis.get("records") != 1260:
        failed.append("analysis_records")
    if analysis.get("unique_cases") != 420:
        failed.append("analysis_unique_cases")
    transitions = analysis.get("dense_2mm_transitions_vs_R0", {})
    expected_transitions = {
        "R1": {"resolved": 2, "induced": 2},
        "R2": {"resolved": 2, "induced": 3},
    }
    for candidate, expected in expected_transitions.items():
        item = transitions.get(candidate, {})
        for key, value in expected.items():
            if item.get(key) != value:
                failed.append(f"{candidate}_{key}")
    if failed:
        raise RuntimeError("Post-hoc semantic checks failed: " + ", ".join(failed))
    return replay, analysis


def verify_run_records(root):
    records_root = root / D22_ROOT / "round_a"
    record_paths = sorted(records_root.glob("*/run_record.json"))
    if len(record_paths) != 12:
        raise RuntimeError(f"Expected 12 run records, found {len(record_paths)}")
    observed = set()
    checkpoints = []
    for record_path in record_paths:
        relative = record_path.relative_to(root)
        verify_file_sidecar(root, relative)
        record = json.loads(record_path.read_text(encoding="utf-8"))
        key = (record.get("candidate"), record.get("fold"), record.get("seed"))
        if key in observed:
            raise RuntimeError(f"Duplicate candidate/fold/seed record: {key}")
        observed.add(key)
        verify_record_artifacts(root, record)
        checkpoint = Path(record["artifacts"]["checkpoint"]["path"])
        if checkpoint.name != "ckpt-last-bncal.pth":
            raise RuntimeError(f"Non-canonical checkpoint: {checkpoint}")
        sidecar = require_file(root, Path(str(checkpoint) + ".json"))
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        if metadata.get("reset_running_stats") is not True:
            raise RuntimeError(f"Invalid BNCal metadata: {sidecar}")
        checkpoints.append(checkpoint)
    expected = {
        (candidate, fold, 0) for candidate in CANDIDATES for fold in FOLDS
    }
    if observed != expected:
        raise RuntimeError(
            f"Run-record matrix differs: missing={sorted(expected - observed)} "
            f"extra={sorted(observed - expected)}"
        )
    if len(set(checkpoints)) != 12:
        raise RuntimeError("Expected 12 unique BNCal checkpoints")
    return sorted(checkpoints)


def main():
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    verify_selection(root)
    verify_negative_freeze(root)
    verify_posthoc(root)
    checkpoints = verify_run_records(root)
    if args.write_checkpoint_list:
        output = args.write_checkpoint_list
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "".join(f"{path.as_posix()}\n" for path in checkpoints),
            encoding="utf-8",
        )
        print(f"[saved] checkpoint list: {output}")
    print("[ok] D2.2 run-record matrix: 3 candidates x 4 folds x seed 0")
    print("[ok] 12 unique BNCal checkpoints and sidecars")
    print("[ok] frozen winner=None and Round B forbidden")
    print("[ok] replay records=1260 and dense 2 mm count replay delta=0")
    print("[ok] post-hoc remains observation-only and selection-inert")
    print("[locked] confirmation20, old monitor, and official test were not used")


if __name__ == "__main__":
    main()
