#!/usr/bin/env python3
"""Synthetic CPU contracts for the frozen Q0 reverse intervention."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import torch


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import analyze_cranial_scqr_v11_l4_round_a_q0_reverse_intervention as analyzer
import run_cranial_scqr_v11_l4_round_a_q0_reverse_intervention as runner


PROTOCOL_PATH = (
    REPO_ROOT
    / "docs/cranial_scqr_v1_research_2026_09_10"
    / "l4_round_a_q0_reverse_inference_intervention_protocol_v1.json"
)


def protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def metric_values(primary: float) -> dict:
    row = {field: primary for field in analyzer.DISTANCE_METRICS}
    row.update({field: 0.5 for field in analyzer.UNIT_INTERVAL_METRICS})
    row.update(
        {
            "rim_reference_rim_points": 100,
            "rim_predicted_rim_points": 100,
            "zero_contact_2mm": 0,
            "disaster": 0,
        }
    )
    return row


def identity(fold: str, source_index: int, defect_index: int) -> dict:
    source = f"{fold}{source_index:02d}"
    defect = f"defect_{defect_index}"
    return {
        "fold": fold,
        "seed": 0,
        "case_id": f"{source}_{defect}",
        "skull_id": f"skull:{source}",
        "source_skull_id": source,
        "defect_type": defect,
    }


def synthetic_rows() -> tuple[list[dict], list[dict], list[dict]]:
    reverse: list[dict] = []
    frozen_round_a: list[dict] = []
    frozen_qc: list[dict] = []
    for fold in analyzer.FOLDS:
        for source_index in range(21):
            for defect_index in range(5):
                ident = identity(fold, source_index, defect_index)
                for candidate in ("B0", "A1", "Q0", "QC"):
                    base = 8.0 if candidate == "Q0" else 9.0
                    frozen_round_a.append(
                        {
                            **ident,
                            "run_key": f"{candidate}_fold{fold}_seed0",
                            "candidate": candidate,
                            **metric_values(base),
                        }
                    )
                for condition, value in (
                    ("native_qc", 8.1504),
                    ("bias_zero", 8.15),
                    ("case_mean_probability", 8.15),
                    ("fixed_seed_within_case_probability_permutation", 8.1502),
                ):
                    frozen_qc.append(
                        {
                            **ident,
                            "run_key": f"QC_fold{fold}_seed0",
                            "candidate": "QC",
                            "condition": condition,
                            **metric_values(value),
                            "coarse_condition_max_abs_normalized": 0.0,
                        }
                    )
                for condition, value in (("native_q0", 8.0), ("q0_beta1", 8.001)):
                    reverse.append(
                        {
                            **ident,
                            "run_key": f"Q0_fold{fold}_seed0",
                            "candidate": "Q0",
                            "condition": condition,
                            **metric_values(value),
                            "coarse_condition_max_abs_normalized": 0.0,
                            "q0_beta1_attention_max_abs_normalized": (
                                0.02 if condition == "q0_beta1" else 0.0
                            ),
                            "q0_beta1_prediction_max_abs_normalized": (
                                1e-6 if condition == "q0_beta1" else 0.0
                            ),
                        }
                    )
    return reverse, frozen_round_a, frozen_qc


class ProtocolTests(unittest.TestCase):
    def test_frozen_protocol_and_boundaries(self) -> None:
        value = protocol()
        analyzer.validate_protocol(value)
        self.assertEqual(value["protocol_id"], analyzer.PROTOCOL_ID)
        self.assertFalse(value["authorization_boundary"]["gpu_use_authorized"])
        self.assertFalse(value["authorization_boundary"]["round_b_authorized"])
        self.assertEqual(value["factorial_design"]["q0_conditions"]["order"], list(analyzer.CONDITIONS))

    def test_protocol_mutations_fail_closed(self) -> None:
        for mutation in ("id", "condition", "threshold", "count", "authorization"):
            value = protocol()
            if mutation == "id":
                value["protocol_id"] = "wrong"
            elif mutation == "condition":
                value["factorial_design"]["q0_conditions"]["order"].reverse()
            elif mutation == "threshold":
                value["numeric_contract"]["inference_effect_practical_inactivity_threshold_mm"] = 0.02
            elif mutation == "count":
                value["future_execution_contract"]["model_case_forward_calls_expected"] = 419
            else:
                value["authorization_boundary"]["gpu_use_authorized"] = True
            with self.assertRaises(analyzer.ContractError):
                analyzer.validate_protocol(value)


class BetaOverrideTests(unittest.TestCase):
    class Module(torch.nn.Module):
        def __init__(self, beta: float = 0.0) -> None:
            super().__init__()
            self.weight = torch.nn.Parameter(torch.tensor([2.0]))
            self.register_buffer("beta", torch.tensor(beta, dtype=torch.float32))

    def test_exact_override_and_restore(self) -> None:
        module = self.Module()
        before = runner.parent_runner.model_state_hashes(module)
        ledger = runner.AccessLedger()
        with runner.temporary_beta_one(module, ledger):
            self.assertEqual(float(module.beta.item()), 1.0)
            self.assertEqual(module.beta.dtype, torch.float32)
        self.assertEqual(float(module.beta.item()), 0.0)
        self.assertEqual(before, runner.parent_runner.model_state_hashes(module))
        self.assertEqual(ledger.counts["temporary_beta_assignments"], 1)
        self.assertEqual(ledger.counts["temporary_beta_restorations"], 1)

    def test_restore_after_exception(self) -> None:
        module = self.Module()
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            with runner.temporary_beta_one(module):
                raise RuntimeError("synthetic")
        self.assertEqual(float(module.beta.item()), 0.0)
        self.assertFalse(hasattr(module, "_q0_reverse_beta_override_active"))

    def test_wrong_native_beta_and_nested_override_fail(self) -> None:
        with self.assertRaises(analyzer.ContractError):
            with runner.temporary_beta_one(self.Module(1.0)):
                pass
        module = self.Module()
        with runner.temporary_beta_one(module):
            with self.assertRaises(analyzer.ContractError):
                with runner.temporary_beta_one(module):
                    pass

    def test_invalid_beta_tensor_fails(self) -> None:
        module = self.Module()
        module.beta = torch.tensor([0.0, 0.0])
        with self.assertRaises(analyzer.ContractError):
            with runner.temporary_beta_one(module):
                pass


class AuthorizationAndLedgerTests(unittest.TestCase):
    def good_authorization(self, output: Path) -> dict:
        return {
            "authorization_effective": True,
            "execution_authorized": True,
            "authorized_once": True,
            "protocol_id": analyzer.PROTOCOL_ID,
            "protocol_sha256": analyzer.PROTOCOL_SHA256,
            "output_directory": str(output),
            "authorized_counts": {
                "checkpoint_loads": 2,
                "npz_opens": 210,
                "model_case_forward_calls": 420,
                "conditions_per_case": 2,
                "temporary_beta_assignments": 210,
                "temporary_beta_restorations": 210,
                "qc_checkpoint_loads": 0,
                "qc_model_forwards": 0,
            },
            "q0_reverse_intervention": True,
            "protected_payload_access": {
                "confirmation20": False,
                "official_test": False,
                "old_monitor": False,
                "MUG": False,
                "train_outside_dev": False,
            },
            "qc_checkpoint_rerun": False,
            "training_authorized": False,
            "bncal_authorized": False,
            "round_b_authorized": False,
        }

    def test_exact_separate_authorization(self) -> None:
        output = Path("/tmp/q0_reverse_synthetic_output")
        good = self.good_authorization(output)
        runner.validate_execution_authorization(good, analyzer.PROTOCOL_SHA256, output)
        for key in ("authorization_effective", "execution_authorized", "authorized_once"):
            bad = copy.deepcopy(good)
            bad[key] = False
            with self.assertRaises(analyzer.ContractError):
                runner.validate_execution_authorization(bad, analyzer.PROTOCOL_SHA256, output)
        bad = copy.deepcopy(good)
        bad["authorized_counts"]["model_case_forward_calls"] = 421
        with self.assertRaises(analyzer.ContractError):
            runner.validate_execution_authorization(bad, analyzer.PROTOCOL_SHA256, output)
        bad = copy.deepcopy(good)
        bad["qc_checkpoint_rerun"] = True
        with self.assertRaises(analyzer.ContractError):
            runner.validate_execution_authorization(bad, analyzer.PROTOCOL_SHA256, output)

    def test_ledger_exact_budget(self) -> None:
        ledger = runner.AccessLedger()
        for fold in analyzer.FOLDS:
            run_key = f"Q0_fold{fold}_seed0"
            ledger.record_checkpoint_load(run_key)
            for index in range(105):
                ledger.record_npz_open(run_key, f"{fold}_{index}")
                for member in runner.ALLOWED_NPZ_MEMBERS:
                    ledger.record_member(member)
                ledger.record_forward()
                ledger.record_forward()
                ledger.record_beta_assignment()
                ledger.record_beta_restoration()
        ledger.assert_final()
        ledger.counts["model_case_forward_calls"] -= 1
        with self.assertRaises(analyzer.ContractError):
            ledger.assert_final()

    def test_path_containment(self) -> None:
        with self.assertRaises(analyzer.ContractError):
            runner.resolve_under(REPO_ROOT, "../escape")
        with self.assertRaises(analyzer.ContractError):
            runner.resolve_under(REPO_ROOT, "/tmp/absolute")


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows, cls.round_a, cls.qc = synthetic_rows()

    def test_complete_factorial_analysis(self) -> None:
        sources, deltas, summary, receipt = analyzer.analyze_reverse_rows(
            self.rows, self.round_a, self.qc, protocol()
        )
        self.assertEqual(len(sources), 168)
        self.assertEqual(len(deltas), 168)
        interaction = summary["comparisons"]["factorial_interaction"][analyzer.PRIMARY]["combined"]
        self.assertAlmostEqual(interaction, 0.0006, places=10)
        self.assertEqual(receipt["overall_classification"], "WEIGHT_STATE_DOMINANT_ROBUST")
        self.assertFalse(receipt["round_b_authorized"])
        self.assertFalse(receipt["automatic_next_run"])

    def test_bootstrap_is_deterministic(self) -> None:
        sources = analyzer.aggregate_factorial_sources(self.rows, self.round_a, self.qc)
        deltas = analyzer.paired_factorial_deltas(sources)
        selected = [row for row in deltas if row["comparison"] == "q0_beta1_minus_native_q0"]
        first = analyzer.stratified_cluster_bootstrap(selected, analyzer.PRIMARY)
        second = analyzer.stratified_cluster_bootstrap(selected, analyzer.PRIMARY)
        self.assertEqual(first, second)
        with self.assertRaises(analyzer.ContractError):
            analyzer.stratified_cluster_bootstrap(selected, analyzer.PRIMARY, seed=1)

    def test_native_reproduction_and_coarse_boundaries_fail_closed(self) -> None:
        bad = copy.deepcopy(self.rows)
        target = next(row for row in bad if row["condition"] == "native_q0")
        target[analyzer.PRIMARY] += 1.1e-5
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_execution_controls(bad, self.round_a, self.qc, protocol())
        bad = copy.deepcopy(self.rows)
        target = next(row for row in bad if row["condition"] == "q0_beta1")
        target["coarse_condition_max_abs_normalized"] = 1.1e-7
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_execution_controls(bad, self.round_a, self.qc, protocol())

    def test_pairing_and_frozen_matrix_fail_closed(self) -> None:
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_reverse_rows(self.rows[:-1])
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_execution_controls(
                self.rows, self.round_a, self.qc[1:], protocol()
            )

    def test_classification_boundaries(self) -> None:
        sources = analyzer.aggregate_factorial_sources(self.rows, self.round_a, self.qc)
        deltas = analyzer.paired_factorial_deltas(sources)
        summary = analyzer.build_summary(sources, deltas)
        controls = {"status": "PASS"}
        directional = copy.deepcopy(summary)
        directional["comparisons"]["q0_beta1_minus_native_qc"][analyzer.PRIMARY]["bootstrap"]["ci95_high"] = 0.1
        result = analyzer.classify_weight_state(directional, controls)
        self.assertEqual(result["overall_classification"], "WEIGHT_STATE_DOMINANT_DIRECTIONAL")
        material = copy.deepcopy(summary)
        for scope in ("A", "combined"):
            material["comparisons"]["q0_beta1_minus_native_q0"][analyzer.PRIMARY][scope] = 0.02
        result = analyzer.classify_weight_state(material, controls)
        self.assertEqual(result["q0_reverse_effect_classification"], "Q0_REVERSE_EFFECT_MATERIAL")
        self.assertFalse(result["round_b_authorized"])

    def test_nonfinite_and_duplicate_rows_fail(self) -> None:
        bad = copy.deepcopy(self.rows)
        bad[0][analyzer.PRIMARY] = float("inf")
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_reverse_rows(bad)
        bad = copy.deepcopy(self.rows)
        bad[1] = copy.deepcopy(bad[0])
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_reverse_rows(bad)


class ExclusiveWriteTests(unittest.TestCase):
    def test_exclusive_json_and_csv_writes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            analyzer._write_json_exclusive(root / "one.json", {"ok": True})
            with self.assertRaises(FileExistsError):
                analyzer._write_json_exclusive(root / "one.json", {"ok": False})
            analyzer.write_csv(root / "one.csv", [{"a": 1}])
            with self.assertRaises(FileExistsError):
                analyzer.write_csv(root / "one.csv", [{"a": 2}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
