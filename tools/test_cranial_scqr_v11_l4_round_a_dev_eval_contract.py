#!/usr/bin/env python3
"""Synthetic CPU-only contract tests for the frozen L4 Round A tools."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


# Prevent accidental GPU visibility before importing the modules under test.
os.environ["CUDA_VISIBLE_DEVICES"] = ""
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import analyze_cranial_scqr_v11_l4_round_a as analyzer  # noqa: E402
import run_cranial_scqr_v11_l4_round_a_dev_eval as runner  # noqa: E402


DEFECTS = ("bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2")


def synthetic_protocol() -> dict:
    matrix = []
    for candidate in analyzer.CANDIDATES:
        for fold in analyzer.FOLDS:
            matrix.append({
                "run_key": f"{candidate}_fold{fold}_seed0",
                "candidate": candidate,
                "fold": fold,
                "seed": 0,
            })
    return {
        "protocol_id": analyzer.PROTOCOL_ID,
        "checkpoint_matrix": matrix,
        "development_allowlists": {
            "A": {"cases": 105, "sources": 21, "cases_per_source": 5},
            "B": {"cases": 105, "sources": 21, "cases_per_source": 5},
        },
        "round_a_analysis_contract": {
            "bootstrap_seed": 20260910,
            "bootstrap_samples": 10000,
            "round_b_authorized_by_gate_result": False,
        },
    }


def synthetic_rows() -> list[dict]:
    offsets = {"B0": 0.0, "A1": -0.03, "Q0": -0.08, "QC": -0.20}
    rows = []
    for candidate in analyzer.CANDIDATES:
        for fold in analyzer.FOLDS:
            for source_index in range(21):
                source = f"{fold}_source_{source_index:02d}"
                for defect_index, defect in enumerate(DEFECTS):
                    case_id = f"{fold}_case_{source_index:02d}_{defect_index}"
                    base = 2.0 + 0.01 * source_index + 0.001 * defect_index
                    rows.append({
                        "run_key": f"{candidate}_fold{fold}_seed0",
                        "candidate": candidate,
                        "fold": fold,
                        "seed": 0,
                        "case_id": case_id,
                        "skull_id": source,
                        "source_skull_id": source,
                        "defect_type": defect,
                        "rim_gt_rim_to_pred_p95_mm": base + offsets[candidate],
                        "implant_cd_l1_mm": 0.8,
                        "implant_pred_to_ref_mean_mm": 0.7,
                        "implant_ref_to_pred_mean_mm": 0.9,
                        "implant_hd95_mm": 1.5,
                        "implant_nsd_at_1mm": 0.85,
                        "final_cd_l1_mm": 0.6,
                        "final_hd95_mm": 1.2,
                        "final_nsd_at_1mm": 0.90,
                        "rim_reference_rim_points": 100,
                        "rim_predicted_rim_points": 90,
                        "rim_gt_rim_to_pred_mean_mm": 0.7,
                        "rim_contact_cd_l1_mm": 0.5,
                        "rim_contact_hd95_mm": 1.0,
                        "rim_contact_precision": 0.8,
                        "rim_contact_recall": 0.7,
                        "zero_contact_2mm": 0,
                        "disaster": 0,
                    })
    return rows


def passing_gate_inputs() -> tuple[dict, dict]:
    qc_b0 = {
        analyzer.PRIMARY: {"A": -0.10, "B": -0.10, "combined": -0.10},
        "implant_cd_l1_mm": {"A": 0.10, "B": 0.10, "combined": 0.10},
        "final_cd_l1_mm": {"A": 0.10, "B": 0.10, "combined": 0.10},
        "final_hd95_mm": {"A": 0.50, "B": 0.50, "combined": 0.50},
        "final_nsd_at_1mm": {"A": -0.01, "B": -0.01, "combined": -0.01},
    }
    qc_q0 = copy.deepcopy(qc_b0)
    qc_q0[analyzer.PRIMARY] = {"A": -0.01, "B": -0.01, "combined": -1e-12}
    summary = {"comparisons": {"QC_minus_B0": qc_b0, "QC_minus_Q0": qc_q0}}
    counts = {
        candidate: {
            fold: {"zero_contact": 0, "disaster": 0}
            for fold in analyzer.FOLDS
        }
        for candidate in analyzer.CANDIDATES
    }
    return summary, counts


class ProtocolAndBindingTests(unittest.TestCase):
    def test_repo_root_import_binding_resolves_models(self) -> None:
        self.assertIn(str(runner.REPO_ROOT), sys.path)
        specification = importlib.util.find_spec("models")
        self.assertIsNotNone(specification)
        self.assertEqual(
            Path(specification.origin).resolve(),
            (runner.REPO_ROOT / "models" / "__init__.py").resolve(),
        )

    def test_exact_matrix_and_protocol(self) -> None:
        analyzer.validate_protocol(synthetic_protocol())
        bad = synthetic_protocol()
        bad["checkpoint_matrix"][0]["candidate"] = "OTHER"
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_protocol(bad)

    def test_path_traversal_and_hash_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            payload = root / "bound.txt"
            payload.write_bytes(b"synthetic binding\n")
            expected = hashlib.sha256(payload.read_bytes()).hexdigest()
            self.assertEqual(runner.resolve_under(root, "bound.txt"), payload.resolve())
            runner.verify_file(payload, expected, payload.stat().st_size)
            with self.assertRaises(analyzer.ContractError):
                runner.resolve_under(root, "../escape.txt", must_exist=False)
            with self.assertRaises(analyzer.ContractError):
                runner.resolve_under(root, str(payload))
            with self.assertRaises(analyzer.ContractError):
                runner.verify_file(payload, "0" * 64)

    def test_execution_authorization_must_be_separate_exact_and_once(self) -> None:
        binding = "1" * 64
        good = {
            "authorization_effective": True,
            "execution_authorized": True,
            "protocol_id": analyzer.PROTOCOL_ID,
            "protocol_sha256": binding,
            "authorized_once": True,
            "protected_payload_access": {
                "confirmation20": False, "official_test": False,
                "old_monitor": False, "MUG": False, "train": False,
            },
        }
        runner.validate_execution_authorization(good, binding)
        for key in ("authorization_effective", "execution_authorized", "authorized_once"):
            bad = copy.deepcopy(good)
            bad[key] = False
            with self.assertRaises(analyzer.ContractError):
                runner.validate_execution_authorization(bad, binding)
        bad = copy.deepcopy(good)
        bad["protected_payload_access"]["official_test"] = True
        with self.assertRaises(analyzer.ContractError):
            runner.validate_execution_authorization(bad, binding)


class AccessAndOrderingTests(unittest.TestCase):
    def test_member_and_counter_ledger(self) -> None:
        ledger = runner.AccessLedger()
        with self.assertRaises(analyzer.ContractError):
            ledger.record_member("complete")
        for checkpoint in range(8):
            ledger.record_checkpoint_load(f"run_{checkpoint}")
        for run in range(8):
            for case in range(105):
                ledger.record_npz_open(f"run_{run}", f"case_{case}")
                for member in runner.ALLOWED_NPZ_MEMBERS:
                    ledger.record_member(member)
                ledger.record_forward()
        ledger.assert_final()
        with self.assertRaises(analyzer.ContractError):
            ledger.record_npz_open("run_0", "case_0")
        incomplete = runner.AccessLedger()
        with self.assertRaises(analyzer.ContractError):
            incomplete.assert_final()

    def test_partial_only_and_targets_after_forward(self) -> None:
        events = []
        partial, implant, gt = object(), object(), object()

        def forward(value):
            self.assertIs(value, partial)
            events.append("forward_partial_only")
            return "prediction"

        def metric(prediction, seen_partial, seen_implant, seen_gt):
            self.assertEqual(events, ["forward_partial_only"])
            self.assertEqual(prediction, "prediction")
            self.assertIs(seen_partial, partial)
            self.assertIs(seen_implant, implant)
            self.assertIs(seen_gt, gt)
            events.append("metric_targets")
            return 7

        self.assertEqual(
            runner.forward_then_metrics(forward, partial, implant, gt, metric), 7
        )
        self.assertEqual(events, ["forward_partial_only", "metric_targets"])

    def test_state_immutability(self) -> None:
        before = {
            "parameters": runner.hash_tensor_mapping({"p": np.asarray([1.0], dtype=np.float32)}),
            "buffers": runner.hash_tensor_mapping({"b": np.asarray([2.0], dtype=np.float32)}),
        }
        runner.assert_state_unchanged(before, dict(before))
        changed = dict(before)
        changed["buffers"] = runner.hash_tensor_mapping({"b": np.asarray([3.0], dtype=np.float32)})
        with self.assertRaises(analyzer.ContractError):
            runner.assert_state_unchanged(before, changed)


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = synthetic_rows()
        cls.sources, cls.deltas, cls.summary, cls.gate = analyzer.analyze_case_rows(
            cls.rows, synthetic_protocol()
        )

    def test_source_aggregation_pairing_and_pass_is_non_authorizing(self) -> None:
        self.assertEqual(len(self.sources), 168)
        self.assertEqual(len(self.deltas), 168)
        self.assertEqual(self.gate["classification"], "PASS")
        self.assertTrue(self.gate["all_gate_requirements_pass"])
        self.assertFalse(self.gate["round_b_authorized"])
        self.assertFalse(self.gate["automatic_next_run"])
        tails = self.summary["tail_reports"]["comparisons"]["QC_minus_B0"]
        self.assertEqual(tails["paired_improved_case_count"], 210)
        self.assertEqual(tails["paired_improved_source_count"], 42)

    def test_bootstrap_is_deterministic_and_source_stratified(self) -> None:
        rows = [row for row in self.deltas if row["comparison"] == "QC_minus_B0"]
        first = analyzer.stratified_cluster_bootstrap(rows, analyzer.PRIMARY)
        second = analyzer.stratified_cluster_bootstrap(rows, analyzer.PRIMARY)
        self.assertEqual(first, second)
        self.assertEqual(first["seed"], 20260910)
        self.assertEqual(first["samples"], 10000)

    def test_nonfinite_primary_fails_but_zero_contact_na_is_explicit(self) -> None:
        bad = [dict(row) for row in self.rows]
        bad[0][analyzer.PRIMARY] = float("nan")
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_case_rows(bad)
        allowed = [dict(row) for row in self.rows]
        allowed[0]["zero_contact_2mm"] = 1
        allowed[0]["rim_contact_hd95_mm"] = float("nan")
        allowed[0]["rim_contact_precision"] = float("nan")
        sources = analyzer.aggregate_source_rows(allowed)
        affected = next(
            row for row in sources
            if row["candidate"] == "B0" and row["fold"] == "A"
            and row["source_skull_id"] == "A_source_00"
        )
        self.assertIsNone(affected["rim_contact_hd95_mm"])
        self.assertEqual(affected["zero_contact_2mm_count"], 1)

    def test_incomplete_or_unpaired_matrix_fails(self) -> None:
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_case_rows(self.rows[:-1])
        bad = [dict(row) for row in self.rows]
        target = next(row for row in bad if row["candidate"] == "QC" and row["fold"] == "A")
        target["case_id"] = "unpaired_case"
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_case_rows(bad)


class GateBoundaryTests(unittest.TestCase):
    def test_all_inclusive_boundaries_pass_and_strict_qcq0_zero_fails(self) -> None:
        summary, counts = passing_gate_inputs()
        receipt = analyzer.evaluate_gate(summary, counts)
        self.assertEqual(receipt["classification"], "PASS")
        self.assertFalse(receipt["round_b_authorized"])
        summary["comparisons"]["QC_minus_Q0"][analyzer.PRIMARY]["combined"] = 0.0
        failed = analyzer.evaluate_gate(summary, counts)
        self.assertFalse(failed["all_gate_requirements_pass"])

    def test_every_numeric_threshold_can_fail_closed(self) -> None:
        mutations = [
            ("primary_fold_A_nonworsening", analyzer.PRIMARY, "A", 1e-12),
            ("primary_fold_B_nonworsening", analyzer.PRIMARY, "B", 1e-12),
            ("primary_combined_improvement", analyzer.PRIMARY, "combined", -0.10 + 1e-12),
            ("implant_cd_l1_mm_A", "implant_cd_l1_mm", "A", 0.10 + 1e-12),
            ("implant_cd_l1_mm_B", "implant_cd_l1_mm", "B", 0.10 + 1e-12),
            ("implant_cd_l1_mm_combined", "implant_cd_l1_mm", "combined", 0.10 + 1e-12),
            ("final_cd_l1_mm_A", "final_cd_l1_mm", "A", 0.10 + 1e-12),
            ("final_cd_l1_mm_B", "final_cd_l1_mm", "B", 0.10 + 1e-12),
            ("final_cd_l1_mm_combined", "final_cd_l1_mm", "combined", 0.10 + 1e-12),
            ("final_hd95_mm_A", "final_hd95_mm", "A", 0.50 + 1e-12),
            ("final_hd95_mm_B", "final_hd95_mm", "B", 0.50 + 1e-12),
            ("final_hd95_mm_combined", "final_hd95_mm", "combined", 0.50 + 1e-12),
            ("final_nsd_at_1mm_A", "final_nsd_at_1mm", "A", -0.01 - 1e-12),
            ("final_nsd_at_1mm_B", "final_nsd_at_1mm", "B", -0.01 - 1e-12),
            ("final_nsd_at_1mm_combined", "final_nsd_at_1mm", "combined", -0.01 - 1e-12),
        ]
        for expected_name, metric, scope, value in mutations:
            with self.subTest(expected_name):
                summary, counts = passing_gate_inputs()
                summary["comparisons"]["QC_minus_B0"][metric][scope] = value
                receipt = analyzer.evaluate_gate(summary, counts)
                check = next(item for item in receipt["checks"] if item["name"] == expected_name)
                self.assertFalse(check["passed"])
                self.assertFalse(receipt["all_gate_requirements_pass"])

    def test_count_execution_resource_and_numeric_gates(self) -> None:
        for kind, fold in (("zero_contact", "A"), ("zero_contact", "B"), ("disaster", "A"), ("disaster", "B")):
            with self.subTest(kind=kind, fold=fold):
                summary, counts = passing_gate_inputs()
                counts["QC"][fold][kind] = 1
                self.assertFalse(analyzer.evaluate_gate(summary, counts)["all_gate_requirements_pass"])
        for keyword in ("numeric_complete", "execution_ok", "resource_ok"):
            with self.subTest(keyword):
                summary, counts = passing_gate_inputs()
                self.assertEqual(
                    analyzer.evaluate_gate(summary, counts, **{keyword: False})["classification"],
                    "NO_GO",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
