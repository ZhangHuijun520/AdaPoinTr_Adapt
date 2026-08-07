#!/usr/bin/env python
"""Lock the D2.1 geometry-guard amendment before candidate training."""

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_base_protocol(protocol_dir):
    manifest = protocol_dir / "files.sha256"
    if not manifest.is_file():
        raise FileNotFoundError(f"Missing base protocol manifest: {manifest}")
    for line in manifest.read_text(encoding="ascii").splitlines():
        expected, name = line.split(None, 1)
        path = protocol_dir / Path(name.strip()).name
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"Base protocol hash mismatch: {path}")
    protocol = json.loads((protocol_dir / "protocol.json").read_text())
    if protocol.get("status") != "preregistered_before_candidate_training":
        raise RuntimeError("Base D2 protocol is not the frozen preregistered version")
    return protocol


def payload(base_protocol_dir, gt_replay_summary):
    base = verify_base_protocol(base_protocol_dir)
    replay = json.loads(gt_replay_summary.read_text())
    required_replay_flags = {
        "post_hoc": True,
        "observation_only": True,
        "selection_inert": True,
        "round_b_allowed": False,
        "locked_confirmation_used": False,
        "old_monitor_used": False,
        "official_test_used": False,
    }
    for key, expected in required_replay_flags.items():
        if replay.get(key) != expected:
            raise RuntimeError(f"GT replay boundary mismatch: {key}")
    if float(replay.get("maximum_frozen_implant_hd95_replay_delta_mm", -1)) != 0:
        raise RuntimeError("GT replay did not reproduce frozen Implant HD95")

    return {
        "protocol_name": "mamba-v12-d21-coarse-geometry-guard-dev-v1",
        "status": "preregistered_before_d21_candidate_training",
        "amends": base["protocol_name"],
        "base_protocol_json": str(base_protocol_dir / "protocol.json"),
        "base_protocol_sha256": sha256_file(base_protocol_dir / "protocol.json"),
        "base_protocol_manifest_sha256": sha256_file(base_protocol_dir / "files.sha256"),
        "trigger": {
            "d2_round_a_status": "blocked_insufficient_eligible_candidates",
            "original_round_b_allowed": False,
            "reason": "post-hoc GT replay localized catastrophe geometry at coarse/query stage",
            "gt_replay_summary": str(gt_replay_summary),
            "gt_replay_summary_sha256": sha256_file(gt_replay_summary),
            "gt_replay_records": replay["records"],
            "frozen_implant_hd95_replay_delta_mm": 0.0,
        },
        "data_boundary": {
            "reuse_development84": True,
            "reuse_folds_A_to_D": True,
            "reuse_is_iterative_development": True,
            "locked_confirmation20_allowed": False,
            "old_monitor_allowed": False,
            "official_test_allowed": False,
        },
        "frozen_model_base": {
            "candidate": "C0/O0-xyz",
            "adapter_mechanism": "o0",
            "ordering": "xyz",
            "alpha_init": 0.01,
            "alpha_warmup_epochs": 20,
            "input_points": 8192,
            "output_points": 8192,
        },
        "geometry_loss_common": {
            "weight": 0.01,
            "normalization": "divide geometry distances by per-sample GT radial RMS",
            "smooth_l1_beta": 0.1,
            "eps": 1.0e-6,
            "gt_usage": "training supervision only; never an inference input",
        },
        "candidates": {
            "Q0": {"mode": "none", "description": "frozen C0/O0-xyz baseline"},
            "Q1": {"mode": "centroid", "description": "normalized coarse centroid guard"},
            "Q2": {"mode": "centroid_radius", "description": "equal centroid and log-radius guard"},
            "Q3": {
                "mode": "coverage_cvar",
                "description": "mean worst 10 percent normalized GT-to-coarse distance",
                "cvar_fraction": 0.1,
            },
        },
        "rounds": {
            "A": "Q0-Q3 x folds A-D x seed 0",
            "B": "frozen top two x folds A-D x seed 1; only after Round-A receipt",
        },
        "selection_rules": {
            "catastrophe": "nonfinite core metric or rim_contact_hd95_mm > 50.0",
            "round_a_catastrophe_gate": "candidate catastrophe rate <= Q0 catastrophe rate and zero nonfinite cases",
            "final_noninferiority": {
                "final_cd_l1_mm_delta_max": 0.10,
                "final_hd95_mm_delta_max": 0.50,
                "final_nsd_at_1mm_delta_min": -0.01,
            },
            "efficiency_vs_q0": {
                "peak_gpu_memory_ratio_max": 1.25,
                "inference_latency_ratio_max": 1.75,
                "training_epoch_time_ratio_max": 1.75,
            },
            "ranking": [
                "catastrophe_rate",
                "rim_contact_hd95_mm_p95",
                "rim_contact_hd95_mm_max",
                "implant_hd95_mm_mean",
                "rim_contact_cd_l1_mm_mean",
                "negative_rim_contact_nsd_at_1mm_mean",
            ],
            "stop_if_fewer_than_two_eligible": True,
        },
        "locked_statements": {
            "original_d2_round_b_remains_forbidden": True,
            "posthoc_replay_does_not_select_a_candidate": True,
            "no_candidate_changes_after_first_q_candidate_training": True,
            "confirmation_and_official_test_cannot_reopen_development": True,
        },
    }


def write_locked(output_dir, protocol):
    encoded = (json.dumps(protocol, indent=2, sort_keys=True) + "\n").encode("utf-8")
    files = {
        "protocol_amendment.json": encoded,
        "protocol_amendment.json.sha256": (
            hashlib.sha256(encoded).hexdigest()
            + "  protocol_amendment.json\n"
        ).encode("ascii"),
    }
    if output_dir.exists():
        extras = sorted(
            path.name for path in output_dir.iterdir() if path.name not in files
        )
        mismatches = [
            name for name, content in files.items()
            if not (output_dir / name).is_file()
            or (output_dir / name).read_bytes() != content
        ]
        if extras or mismatches:
            raise RuntimeError(
                f"Refusing to overwrite D2.1 protocol: mismatches={mismatches}, extras={extras}"
            )
        print(f"[locked] existing D2.1 protocol is byte-identical: {output_dir}")
        return
    output_dir.mkdir(parents=True)
    for name, content in files.items():
        (output_dir / name).write_bytes(content)
    print(f"[saved] locked D2.1 protocol: {output_dir}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_protocol_dir", type=Path, required=True)
    parser.add_argument("--gt_replay_summary", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    write_locked(
        args.output_dir,
        payload(args.base_protocol_dir, args.gt_replay_summary),
    )
    print("[locked] confirmation20, old monitor, and official test remain forbidden")
    print("[locked] original D2 Round B remains forbidden")


if __name__ == "__main__":
    main()
