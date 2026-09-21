#!/usr/bin/env python3
"""Synthetic CPU-only contract tests for the Round A-I intervention tools."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


# Hide every GPU before importing torch or either implementation module.
os.environ["CUDA_VISIBLE_DEVICES"] = ""
TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import analyze_cranial_scqr_v11_l4_round_a_intervention as analyzer  # noqa: E402
import run_cranial_scqr_v11_l4_round_a_intervention as runner  # noqa: E402


DEFECTS = ("bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2")
PROTOCOL_PATH = (
    REPO_ROOT
    / "docs/cranial_scqr_v1_research_2026_09_10"
    / "l4_round_a_intervention_protocol_v2.json"
)


def synthetic_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def _metric_values(base: float, distance_offset: float = 0.0) -> dict:
    values = {
        metric: base + distance_offset + 0.001 * index
        for index, metric in enumerate(analyzer.DISTANCE_METRICS)
    }
    values.update({
        "implant_nsd_at_1mm": 0.80,
        "final_nsd_at_1mm": 0.85,
        "rim_contact_precision": 0.75,
        "rim_contact_recall": 0.70,
        "rim_reference_rim_points": 100,
        "rim_predicted_rim_points": 90,
        "zero_contact_2mm": 0,
        "disaster": 0,
    })
    return values


def synthetic_rows() -> tuple[list[dict], list[dict]]:
    condition_offsets = {
        "native_qc": 0.10,
        "bias_zero": 0.00,
        "case_mean_probability": 0.00,
        "fixed_seed_within_case_probability_permutation": 0.20,
    }
    rows: list[dict] = []
    frozen: list[dict] = []
    for fold in analyzer.FOLDS:
        for source_index in range(21):
            source = f"{fold}_source_{source_index:02d}"
            for defect_index, defect in enumerate(DEFECTS):
                case_id = f"{fold}_case_{source_index:02d}_{defect_index}"
                base = 2.0 + 0.01 * source_index + 0.001 * defect_index
                identity = {
                    "fold": fold,
                    "seed": 0,
                    "case_id": case_id,
                    "skull_id": source,
                    "source_skull_id": source,
                    "defect_type": defect,
                }
                for candidate, offset in (("Q0", -0.05), ("QC", 0.10)):
                    frozen.append({
                        **identity,
                        "run_key": f"{candidate}_fold{fold}_seed0",
                        "candidate": candidate,
                        **_metric_values(base, offset),
                    })
                for condition in analyzer.CONDITIONS:
                    rows.append({
                        **identity,
                        "run_key": f"QC_fold{fold}_seed0",
                        "candidate": "QC",
                        "condition": condition,
                        **_metric_values(base, condition_offsets[condition]),
                        "coarse_condition_max_abs_normalized": 0.0,
                        "negative_control_attention_max_abs": (
                            1e-8 if condition == "case_mean_probability" else 0.0
                        ),
                        "negative_control_prediction_max_abs_normalized": (
                            1e-8 if condition == "case_mean_probability" else 0.0
                        ),
                    })
    return rows, frozen


def classification_summary(
    *,
    bias_a: float,
    bias_b: float,
    bias_low: float,
    bias_high: float,
    permutation_a: float,
    permutation_b: float,
    permutation_low: float,
    permutation_high: float,
    training_combined: float = 0.1,
    training_low: float = 0.05,
) -> dict:
    def item(a: float, b: float, low: float, high: float) -> dict:
        return {
            "A": a,
            "B": b,
            "combined": 0.5 * (a + b),
            "bootstrap": {"ci95_low": low, "ci95_high": high},
        }

    return {
        "comparisons": {
            "bias_zero_minus_native_qc": {
                analyzer.PRIMARY: item(bias_a, bias_b, bias_low, bias_high)
            },
            "fixed_permutation_minus_native_qc": {
                analyzer.PRIMARY: item(
                    permutation_a, permutation_b, permutation_low, permutation_high
                )
            },
            "bias_zero_minus_frozen_Q0": {
                analyzer.PRIMARY: {
                    "A": training_combined,
                    "B": training_combined,
                    "combined": training_combined,
                    "bootstrap": {
                        "ci95_low": training_low,
                        "ci95_high": training_combined + 0.1,
                    },
                },
            },
        }
    }


class ProtocolAndAuthorizationTests(unittest.TestCase):
    def test_frozen_protocol_and_non_authorization_boundary(self) -> None:
        protocol = synthetic_protocol()
        analyzer.validate_protocol(protocol)
        self.assertFalse(protocol["future_execution_contract"]["execution_authorized_by_this_protocol"])
        self.assertFalse(protocol["authorization_boundary"]["real_checkpoint_loads_authorized"])
        self.assertFalse(protocol["authorization_boundary"]["real_npz_opens_authorized"])
        self.assertFalse(protocol["authorization_boundary"]["gpu_use_authorized"])
        self.assertFalse(protocol["authorization_boundary"]["round_b_authorized"])
        self.assertEqual(tuple(protocol["conditions"]["order"]), analyzer.CONDITIONS)
        self.assertEqual(runner.SEED, analyzer.SEED)
        self.assertEqual(runner.SEED, 0)
        self.assertEqual(protocol["protocol_id"], analyzer.PROTOCOL_ID)
        self.assertEqual(protocol["status"], analyzer.PROTOCOL_STATUS)
        self.assertEqual(
            protocol["conditions"]["permutation_seed_namespace_protocol_id"],
            analyzer.PERMUTATION_SEED_NAMESPACE_PROTOCOL_ID,
        )
        self.assertEqual(
            runner.PERMUTATION_SEED_NAMESPACE_PROTOCOL_ID,
            analyzer.PERMUTATION_SEED_NAMESPACE_PROTOCOL_ID,
        )

    def test_protocol_tampering_fails_closed(self) -> None:
        for mutation in ("condition", "count", "authorization", "roles"):
            with self.subTest(mutation):
                protocol = synthetic_protocol()
                if mutation == "condition":
                    protocol["conditions"]["order"][0] = "other"
                elif mutation == "count":
                    protocol["future_execution_contract"]["npz_opens_expected"] = 840
                elif mutation == "authorization":
                    protocol["authorization_boundary"]["gpu_use_authorized"] = True
                else:
                    protocol["analysis_contract"]["comparison_roles"][
                        "case_mean_probability_minus_bias_zero"
                    ] = "SCIENTIFIC_MECHANISM_COMPARISON"
                with self.assertRaises(analyzer.ContractError):
                    analyzer.validate_protocol(protocol)
        for field, value in (
            (
                "protocol_id",
                "cranial-scqr-v1.1-L4-roundA-I-same-QC-checkpoint-intervention-v1",
            ),
            ("status", "FROZEN_IMPLEMENTATION_PROTOCOL_EXECUTION_NOT_AUTHORIZED"),
        ):
            with self.subTest(v1_field=field):
                protocol = synthetic_protocol()
                protocol[field] = value
                with self.assertRaises(analyzer.ContractError):
                    analyzer.validate_protocol(protocol)

    def test_execution_authorization_must_be_separate_exact_and_single_use(self) -> None:
        output = Path("/tmp/synthetic-round-a-i-output")
        binding = "1" * 64
        good = {
            "authorization_effective": True,
            "execution_authorized": True,
            "authorized_once": True,
            "protocol_id": analyzer.PROTOCOL_ID,
            "protocol_sha256": binding,
            "output_directory": str(output),
            "authorized_counts": {
                "checkpoint_loads": 2,
                "npz_opens": 210,
                "model_case_forward_calls": 840,
                "conditions_per_case": 4,
            },
            "protected_payload_access": {
                "confirmation20": False,
                "official_test": False,
                "old_monitor": False,
                "MUG": False,
                "train_outside_dev": False,
            },
            "q0_checkpoint_rerun": False,
            "round_b_authorized": False,
        }
        runner.validate_execution_authorization(good, binding, output)
        for key in ("authorization_effective", "execution_authorized", "authorized_once"):
            bad = copy.deepcopy(good)
            bad[key] = False
            with self.assertRaises(analyzer.ContractError):
                runner.validate_execution_authorization(bad, binding, output)
        bad = copy.deepcopy(good)
        bad["protected_payload_access"]["official_test"] = True
        with self.assertRaises(analyzer.ContractError):
            runner.validate_execution_authorization(bad, binding, output)
        bad = copy.deepcopy(good)
        bad["round_b_authorized"] = True
        with self.assertRaises(analyzer.ContractError):
            runner.validate_execution_authorization(bad, binding, output)


class ProbabilityInterventionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import torch

        cls.torch = torch

    def test_condition_transforms_are_deterministic_and_nonmutating(self) -> None:
        probability = self.torch.tensor([[0.1, 0.2, 0.4, 0.7, 0.9]], dtype=self.torch.float32)
        original = probability.clone()
        native = runner.intervene_probability(
            probability, "native_qc", fold="A", case_id="synthetic"
        )
        zero = runner.intervene_probability(
            probability, "bias_zero", fold="A", case_id="synthetic"
        )
        mean = runner.intervene_probability(
            probability, "case_mean_probability", fold="A", case_id="synthetic"
        )
        first = runner.intervene_probability(
            probability,
            "fixed_seed_within_case_probability_permutation",
            fold="A",
            case_id="synthetic",
        )
        second = runner.intervene_probability(
            probability,
            "fixed_seed_within_case_probability_permutation",
            fold="A",
            case_id="synthetic",
        )
        self.assertIs(native, probability)
        self.assertTrue(self.torch.equal(zero, self.torch.ones_like(probability)))
        self.assertTrue(self.torch.equal(mean, probability.mean(-1, keepdim=True).expand_as(probability)))
        self.assertTrue(self.torch.equal(first, second))
        self.assertTrue(self.torch.equal(first.sort().values, probability.sort().values))
        self.assertTrue(self.torch.equal(probability, original))
        anchors = (
            ("A", "synthetic", 3303371663911662006),
            ("B", "synthetic", 6020625845059555098),
            ("A", "train__000__frontoorbital", 1522429693624156821),
        )
        for fold, case_id, expected in anchors:
            self.assertEqual(
                runner.derive_permutation_seed(analyzer.PROTOCOL_ID, fold, case_id),
                expected,
            )
        with self.assertRaises(analyzer.ContractError):
            runner.derive_permutation_seed(
                analyzer.PERMUTATION_SEED_NAMESPACE_PROTOCOL_ID, "A", "synthetic"
            )

    def test_case_mean_and_bias_zero_are_softmax_equivalent(self) -> None:
        probability = self.torch.tensor([[0.1, 0.3, 0.5, 0.8]], dtype=self.torch.float64)
        logits = self.torch.tensor(
            [[[0.2, -0.4, 0.8, 0.1], [-1.0, 0.3, 0.7, 0.2]]],
            dtype=self.torch.float64,
        )
        zero = runner.intervene_probability(
            probability, "bias_zero", fold="B", case_id="equivalence"
        )
        mean = runner.intervene_probability(
            probability, "case_mean_probability", fold="B", case_id="equivalence"
        )
        attention_zero = self.torch.softmax(logits + zero.log().unsqueeze(1), dim=-1)
        attention_mean = self.torch.softmax(logits + mean.log().unsqueeze(1), dim=-1)
        self.assertLessEqual(runner.max_abs_difference(attention_zero, attention_mean), 1e-12)

    def test_temporary_hook_is_removed_and_state_is_unchanged(self) -> None:
        torch = self.torch

        class ToyConditioner(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.weight = torch.nn.Parameter(torch.tensor(2.0))
                self.register_buffer("beta", torch.tensor(1.0))

            def forward(self, query, proxy, position, probability, epoch=None):
                return query + self.weight * probability.mean()

        module = ToyConditioner()
        state_before = runner.parent_runner.model_state_hashes(module)
        ledger = runner.AccessLedger()
        probability = torch.tensor([[0.1, 0.2, 0.4]])
        with runner.temporary_probability_intervention(
            module,
            "bias_zero",
            fold="A",
            case_id="hook-case",
            ledger=ledger,
        ) as captured:
            module(torch.zeros(1), torch.zeros(1), torch.zeros(1), probability)
            self.assertIn("original_probability", captured)
            self.assertEqual(len(module._forward_pre_hooks), 1)
        self.assertEqual(len(module._forward_pre_hooks), 0)
        self.assertEqual(ledger.counts["probability_hooks_registered"], 1)
        self.assertEqual(ledger.counts["probability_hooks_removed"], 1)
        runner.parent_runner.assert_state_unchanged(
            state_before, runner.parent_runner.model_state_hashes(module)
        )

    def test_forward_condition_reads_wrapped_backbone_instrumentation(self) -> None:
        torch = self.torch

        class QueryOutput:
            def __init__(self, residual) -> None:
                self.residual = residual

        class ToyConditioner(torch.nn.Module):
            def forward(self, query, proxy, position, probability, epoch=None):
                self.attention = torch.softmax(probability.float(), dim=-1).unsqueeze(1)
                return QueryOutput(torch.zeros_like(query))

        class ToyBackbone(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.scqr_query_conditioner = ToyConditioner()

        class ToyWrappedModel(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.base_model = ToyBackbone()
                self.probability = torch.tensor([[0.1, 0.3, 0.8]])

            def forward(self, partial):
                self.base_model.scqr_query_conditioner(
                    partial, partial, partial, self.probability
                )
                return partial, partial + 1.0

            def pop_full_instrumentation(self):
                return {"backbone": {
                    "scqr_query_attention": (
                        self.base_model.scqr_query_conditioner.attention
                    )
                }}

        partial = torch.zeros((1, 3, 3), dtype=torch.float32)
        model = ToyWrappedModel()
        result = runner._forward_condition(
            model, partial, "native_qc", "A", "synthetic-native", runner.AccessLedger()
        )
        self.assertIn("backbone", result["instrumentation"])
        self.assertNotIn("scqr_query_attention", result["instrumentation"])
        self.assertTrue(torch.equal(
            result["attention"], model.base_model.scqr_query_conditioner.attention
        ))

    def test_invalid_probability_or_condition_fails_closed(self) -> None:
        with self.assertRaises(analyzer.ContractError):
            runner.intervene_probability(
                self.torch.ones(3), "bias_zero", fold="A", case_id="bad"
            )
        with self.assertRaises(analyzer.ContractError):
            runner.intervene_probability(
                self.torch.ones(1, 3), "unknown", fold="A", case_id="bad"
            )


class LedgerAndPathTests(unittest.TestCase):
    def test_exact_future_ledger_and_forbidden_member(self) -> None:
        ledger = runner.AccessLedger()
        with self.assertRaises(analyzer.ContractError):
            ledger.record_member("complete")
        for fold in analyzer.FOLDS:
            run_key = f"QC_fold{fold}_seed0"
            ledger.record_checkpoint_load(run_key)
            for case_index in range(105):
                ledger.record_npz_open(run_key, f"{fold}_{case_index}")
                for member in runner.ALLOWED_NPZ_MEMBERS:
                    ledger.record_member(member)
                for condition in analyzer.CONDITIONS:
                    ledger.record_forward()
                    if condition != "native_qc":
                        ledger.record_probability_hook_registered()
                        ledger.record_probability_hook_removed()
        ledger.assert_final()
        self.assertEqual(ledger.receipt_counts()["model_case_forward_calls"], 840)

    def test_path_and_hash_checks_use_only_temporary_synthetic_files(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            payload = root / "synthetic.txt"
            payload.write_bytes(b"synthetic only\n")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            self.assertEqual(runner.resolve_under(root, "synthetic.txt"), payload.resolve())
            runner.verify_file(payload, digest, payload.stat().st_size)
            with self.assertRaises(analyzer.ContractError):
                runner.resolve_under(root, "../escape", must_exist=False)
            with self.assertRaises(analyzer.ContractError):
                runner.verify_file(payload, "0" * 64)


class AnalysisContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = synthetic_protocol()
        cls.rows, cls.frozen = synthetic_rows()

    def test_full_pairing_controls_bootstrap_and_non_authorizing_classification(self) -> None:
        sources, deltas, summary, receipt = analyzer.analyze_intervention_rows(
            self.rows, self.frozen, self.protocol
        )
        self.assertEqual(len(sources), 168)
        self.assertEqual(len(deltas), 168)
        self.assertEqual(receipt["mechanism_classification"], "IMMEDIATE_BIAS_HARM_ROBUST")
        self.assertEqual(
            receipt["training_path_classification"],
            "TRAINING_PATH_RESIDUAL_GAP_ROBUST",
        )
        self.assertFalse(receipt["round_b_authorized"])
        self.assertFalse(receipt["automatic_next_run"])
        self.assertFalse(receipt["automatic_beta_tuning"])
        control = receipt["execution_controls"]
        self.assertTrue(control["native_reproduction_pass"])
        self.assertTrue(control["case_mean_probability_attention_equivalence_pass"])
        self.assertTrue(control["downstream_negative_control_diagnostics_non_gating"])
        self.assertNotIn("case_mean_probability_equals_bias_zero_pass", control)
        self.assertEqual(
            receipt["scientific_classification_comparisons"],
            list(analyzer.SCIENTIFIC_CLASSIFICATION_COMPARISONS),
        )
        self.assertEqual(
            receipt["diagnostic_only_comparisons"],
            list(analyzer.DIAGNOSTIC_ONLY_COMPARISONS),
        )
        self.assertTrue(all(
            row["comparison_role"] == analyzer.COMPARISON_ROLES[row["comparison"]]
            for row in deltas
        ))
        self.assertEqual(
            summary["comparisons"]["case_mean_probability_minus_bias_zero"][
                "comparison_role"
            ],
            "DIAGNOSTIC_ONLY_NOT_USED_FOR_SCIENTIFIC_CLASSIFICATION",
        )
        comparison = summary["comparisons"]["bias_zero_minus_native_qc"]
        self.assertEqual(comparison["case_primary_win_tie_loss"]["left_better"], 210)
        self.assertEqual(comparison["source_primary_win_tie_loss"]["left_better"], 42)

    def test_bootstrap_is_deterministic_and_source_stratified(self) -> None:
        sources = analyzer.aggregate_intervention_sources(self.rows)
        q0 = analyzer.aggregate_frozen_q0_sources(self.frozen)
        deltas = analyzer.paired_source_deltas(sources, q0)
        selected = [
            row for row in deltas
            if row["comparison"] == "bias_zero_minus_native_qc"
        ]
        first = analyzer.stratified_cluster_bootstrap(selected, analyzer.PRIMARY)
        second = analyzer.stratified_cluster_bootstrap(selected, analyzer.PRIMARY)
        self.assertEqual(first, second)
        self.assertEqual(first["seed"], 20260910)
        self.assertEqual(first["samples"], 10000)

    def test_native_reproduction_attention_and_coarse_fail_closed(self) -> None:
        for kind in ("native", "attention", "coarse"):
            with self.subTest(kind):
                rows = copy.deepcopy(self.rows)
                if kind == "native":
                    target = next(row for row in rows if row["condition"] == "native_qc")
                    target[analyzer.PRIMARY] += 0.001
                elif kind == "attention":
                    target = next(
                        row for row in rows if row["condition"] == "case_mean_probability"
                    )
                    target["negative_control_attention_max_abs"] = 2e-6
                else:
                    rows[0]["coarse_condition_max_abs_normalized"] = 2e-7
                with self.assertRaises(analyzer.ContractError):
                    analyzer.validate_execution_controls(rows, self.frozen, self.protocol)

    def test_downstream_negative_control_diagnostics_are_non_gating(self) -> None:
        rows = copy.deepcopy(self.rows)
        target = next(
            row
            for row in rows
            if row["condition"] == "case_mean_probability" and row["fold"] == "A"
        )
        target[analyzer.PRIMARY] += 0.25
        target["final_nsd_at_1mm"] -= 0.10
        target["rim_contact_precision"] = float("nan")
        target["rim_predicted_rim_points"] += 1
        target["zero_contact_2mm"] = 1
        target["negative_control_prediction_max_abs_normalized"] = 2e-6
        controls = analyzer.validate_execution_controls(rows, self.frozen, self.protocol)
        self.assertTrue(controls["case_mean_probability_attention_equivalence_pass"])
        self.assertTrue(controls["downstream_negative_control_diagnostics_non_gating"])
        diagnostics = controls["negative_control_downstream_diagnostics"]
        self.assertAlmostEqual(
            diagnostics["distance_metric_max_abs_mm_by_field"][analyzer.PRIMARY], 0.25
        )
        self.assertAlmostEqual(
            diagnostics["unit_interval_metric_max_abs_by_field"][
                "final_nsd_at_1mm"
            ],
            0.10,
        )
        self.assertEqual(
            diagnostics["optional_na_mismatch_count_by_field"][
                "rim_contact_precision"
            ],
            1,
        )
        self.assertEqual(
            diagnostics["integer_and_boolean_mismatch_count_by_field"][
                "rim_predicted_rim_points"
            ],
            1,
        )
        self.assertEqual(
            diagnostics["integer_and_boolean_mismatch_count_by_field"][
                "zero_contact_2mm"
            ],
            1,
        )
        self.assertEqual(diagnostics["prediction_max_abs_normalized"], 2e-6)

    def test_incomplete_unpaired_and_nonfinite_rows_fail_closed(self) -> None:
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_intervention_rows(self.rows[:-1])
        bad = copy.deepcopy(self.rows)
        target = next(
            row for row in bad
            if row["condition"] == "bias_zero" and row["fold"] == "A"
        )
        target["case_id"] = "unpaired"
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_intervention_rows(bad)
        bad = copy.deepcopy(self.rows)
        bad[0][analyzer.PRIMARY] = float("nan")
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_intervention_rows(bad)
        bad = copy.deepcopy(self.rows)
        bad[0]["rim_contact_precision"] = float("inf")
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_intervention_rows(bad)
        bad = copy.deepcopy(self.rows)
        bad[0]["zero_contact_2mm"] = 2
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_intervention_rows(bad)


class ClassificationBoundaryTests(unittest.TestCase):
    controls = {
        "status": "PASS",
        "case_mean_probability_attention_equivalence_pass": True,
        "downstream_negative_control_diagnostics_non_gating": True,
    }

    def test_robust_directional_inactive_alignment_and_mixed_classes(self) -> None:
        cases = [
            (
                "IMMEDIATE_BIAS_HARM_ROBUST",
                classification_summary(
                    bias_a=-0.1, bias_b=-0.1, bias_low=-0.2, bias_high=-0.01,
                    permutation_a=0.2, permutation_b=0.2,
                    permutation_low=0.1, permutation_high=0.3,
                ),
            ),
            (
                "IMMEDIATE_BIAS_HARM_DIRECTIONAL",
                classification_summary(
                    bias_a=-0.2, bias_b=0.1, bias_low=-0.2, bias_high=0.2,
                    permutation_a=0.1, permutation_b=0.1,
                    permutation_low=-0.1, permutation_high=0.3,
                ),
            ),
            (
                "CONDITIONING_EFFECT_INACTIVE",
                classification_summary(
                    bias_a=0.005, bias_b=-0.005, bias_low=-0.01, bias_high=0.01,
                    permutation_a=0.004, permutation_b=-0.004,
                    permutation_low=-0.01, permutation_high=0.01,
                ),
            ),
            (
                "SPATIAL_ALIGNMENT_BENEFIT_ROBUST",
                classification_summary(
                    bias_a=0.1, bias_b=0.1, bias_low=0.01, bias_high=0.2,
                    permutation_a=0.2, permutation_b=0.2,
                    permutation_low=0.05, permutation_high=0.3,
                ),
            ),
            (
                "MIXED_OR_INCONCLUSIVE",
                classification_summary(
                    bias_a=0.1, bias_b=-0.02, bias_low=-0.1, bias_high=0.2,
                    permutation_a=0.2, permutation_b=-0.1,
                    permutation_low=-0.2, permutation_high=0.3,
                ),
            ),
        ]
        for expected, summary in cases:
            with self.subTest(expected):
                receipt = analyzer.classify_mechanism(summary, self.controls)
                self.assertEqual(receipt["mechanism_classification"], expected)
                self.assertFalse(receipt["round_b_authorized"])

    def test_training_gap_directional_and_no_gap(self) -> None:
        directional = classification_summary(
            bias_a=0.1, bias_b=0.1, bias_low=-0.1, bias_high=0.2,
            permutation_a=0.2, permutation_b=0.2,
            permutation_low=-0.1, permutation_high=0.3,
            training_combined=0.05, training_low=-0.02,
        )
        no_gap = classification_summary(
            bias_a=0.1, bias_b=0.1, bias_low=-0.1, bias_high=0.2,
            permutation_a=0.2, permutation_b=0.2,
            permutation_low=-0.1, permutation_high=0.3,
            training_combined=-0.05, training_low=-0.1,
        )
        self.assertEqual(
            analyzer.classify_mechanism(directional, self.controls)[
                "training_path_classification"
            ],
            "TRAINING_PATH_RESIDUAL_GAP_DIRECTIONAL",
        )
        self.assertEqual(
            analyzer.classify_mechanism(no_gap, self.controls)[
                "training_path_classification"
            ],
            "NO_POSITIVE_TRAINING_PATH_RESIDUAL_GAP",
        )

    def test_diagnostic_only_comparison_cannot_change_classification(self) -> None:
        summary = classification_summary(
            bias_a=-0.1, bias_b=-0.1, bias_low=-0.2, bias_high=-0.01,
            permutation_a=0.2, permutation_b=0.2,
            permutation_low=0.1, permutation_high=0.3,
        )
        baseline = analyzer.classify_mechanism(summary, self.controls)
        summary["comparisons"]["case_mean_probability_minus_bias_zero"] = {
            analyzer.PRIMARY: {
                "A": 1e12,
                "B": -1e12,
                "combined": 1e12,
                "bootstrap": {"ci95_low": -1e12, "ci95_high": 1e12},
            }
        }
        changed = analyzer.classify_mechanism(summary, self.controls)
        self.assertEqual(
            baseline["mechanism_classification"], changed["mechanism_classification"]
        )
        self.assertEqual(
            baseline["training_path_classification"],
            changed["training_path_classification"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
