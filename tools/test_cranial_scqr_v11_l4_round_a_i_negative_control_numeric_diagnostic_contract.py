#!/usr/bin/env python3
"""Synthetic CPU-only contract tests for the scalar numerical diagnostic."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import sys
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path
from unittest import mock


# Hide every GPU before importing torch or either implementation module.
os.environ["CUDA_VISIBLE_DEVICES"] = ""
TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import torch  # noqa: E402
import analyze_cranial_scqr_v11_l4_round_a_i_negative_control_numeric_diagnostic as analyzer  # noqa: E402
import run_cranial_scqr_v11_l4_round_a_i_negative_control_numeric_diagnostic as runner  # noqa: E402


PROTOCOL_PATH = (
    REPO_ROOT
    / "docs/cranial_scqr_v1_research_2026_09_10"
    / "l4_round_a_intervention_negative_control_numeric_diagnostic_protocol_v1.json"
)
IMPLEMENTATION_REQUEST_PATH = (
    REPO_ROOT
    / "docs/cranial_scqr_v1_research_2026_09_10"
    / "l4_round_a_intervention_negative_control_numeric_diagnostic_implementation_authorization_request_v1.json"
)


def frozen_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def complete_ledger() -> runner.AccessLedger:
    ledger = runner.AccessLedger()
    ledger.record_checkpoint_load(analyzer.RUN_KEY)
    ledger.record_npz_open(analyzer.FOLD, analyzer.CASE_ID)
    ledger.record_member("partial")
    for label in analyzer.FORWARD_ORDER:
        ledger.record_probability_hook_registered()
        ledger.record_forward(label)
        ledger.record_probability_hook_removed()
    ledger.assert_final()
    return ledger


def state_hashes(suffix: str = "") -> dict[str, str]:
    return {
        "parameters": hashlib.sha256(f"parameters{suffix}".encode()).hexdigest(),
        "buffers": hashlib.sha256(f"buffers{suffix}".encode()).hexdigest(),
    }


def synthetic_records(mode: str = "exact") -> OrderedDict[str, dict]:
    """Create only in-memory CPU tensors; no model, checkpoint, or NPZ exists."""

    if mode not in {"exact", "repeat", "centered_roundoff", "downstream"}:
        raise ValueError(mode)
    probability = torch.tensor([[0.1, 0.2, 0.6, 0.9]], dtype=torch.float64)
    base_logits = torch.tensor(
        [[[0.2, -0.4, 0.8, 0.1], [-1.0, 0.3, 0.7, 0.2]]],
        dtype=torch.float64,
    )
    centered = base_logits - base_logits.mean(dim=-1, keepdim=True)
    attention = torch.softmax(base_logits, dim=-1)
    coarse = torch.arange(12, dtype=torch.float64).reshape(1, 4, 3) / 100.0
    residual = torch.arange(6, dtype=torch.float64).reshape(1, 2, 3) / 1000.0
    pre_decoder = residual + 0.25
    post_decoder = pre_decoder + 0.5
    prediction = coarse + 0.75
    shift = math.log(float(probability.mean().item()))
    records: OrderedDict[str, dict] = OrderedDict()
    for label in analyzer.FORWARD_ORDER:
        condition = (
            "bias_zero" if label.startswith("bias_zero_") else "case_mean_probability"
        )
        raw = base_logits.clone()
        if condition == "case_mean_probability":
            raw = raw + shift
        stage_centered = centered.clone()
        stage_attention = attention.clone()
        stage_residual = residual.clone()
        stage_pre = pre_decoder.clone()
        stage_post = post_decoder.clone()
        stage_prediction = prediction.clone()
        stage_coarse = coarse.clone()
        if mode == "repeat" and label == "bias_zero_rep1":
            stage_coarse.reshape(-1)[0] += 1e-7
            stage_residual.reshape(-1)[0] += 1e-7
            stage_pre.reshape(-1)[0] += 1e-6
            stage_post.reshape(-1)[0] += 2e-6
            stage_prediction.reshape(-1)[0] += 3e-6
        if mode == "centered_roundoff" and condition == "case_mean_probability":
            stage_centered.reshape(-1)[0] += 1e-12
            stage_attention.reshape(-1)[0] += 2e-12
            stage_residual.reshape(-1)[0] += 4e-12
            stage_pre.reshape(-1)[0] += 8e-12
            stage_post.reshape(-1)[0] += 1e-9
            stage_prediction.reshape(-1)[0] += 2e-9
        if mode == "downstream" and condition == "case_mean_probability":
            stage_attention.reshape(-1)[0] += 1e-10
            stage_residual.reshape(-1)[0] += 1e-8
            stage_pre.reshape(-1)[0] += 5e-8
            stage_post.reshape(-1)[0] += 2e-6
            stage_prediction.reshape(-1)[0] += 3e-6
        intervened = (
            torch.ones_like(probability)
            if condition == "bias_zero"
            else probability.mean(dim=-1, keepdim=True).expand_as(probability)
        )
        tensors = OrderedDict(
            (
                ("original_contact_probability", probability.clone()),
                ("intervened_contact_probability", intervened.clone()),
                ("coarse", stage_coarse),
                ("query_logits_raw", raw),
                ("query_logits_row_centered", stage_centered),
                ("query_attention", stage_attention),
                ("query_residual", stage_residual),
                ("query_pre_decoder", stage_pre),
                ("query_post_decoder", stage_post),
                ("predicted_implant", stage_prediction),
            )
        )
        records[label] = {"condition": condition, "stage_tensors": tensors}
    return records


def compile_result(mode: str = "exact") -> dict:
    states = state_hashes()
    return runner.compile_scalar_result(
        synthetic_records(mode), complete_ledger(), states, dict(states)
    )


def valid_execution_authorization(output: Path) -> dict:
    return {
        "authorization_effective": True,
        "execution_authorized": True,
        "authorized_once": True,
        "protocol_id": analyzer.PROTOCOL_ID,
        "protocol_sha256": analyzer.PROTOCOL_SHA256,
        "output_directory": str(output),
        "fold": analyzer.FOLD,
        "case_id": analyzer.CASE_ID,
        "forward_order": list(analyzer.FORWARD_ORDER),
        "conditions": list(analyzer.CONDITIONS),
        "allowed_npz_members": ["partial"],
        "authorized_counts": {
            "checkpoint_loads": 1,
            "npz_opens": 1,
            "partial_reads": 1,
            "model_case_forward_calls": 4,
            "conditions": 2,
            "replicates_per_condition": 2,
        },
        "protected_payload_access": {
            "implant": False,
            "gt": False,
            "Fold_B": False,
            "Q0": False,
            "native_qc": False,
            "fixed_permutation": False,
            "confirmation20": False,
            "official_test": False,
            "old_monitor": False,
            "MUG": False,
        },
        "automatic_retry": False,
        "formal_round_a_i_retry": False,
        "threshold_change_authorized": False,
        "training_authorized": False,
        "bncal_authorized": False,
        "round_b_authorized": False,
        "automatic_next_run": False,
    }


class ProtocolAndAuthorizationTests(unittest.TestCase):
    def test_frozen_protocol_and_implementation_request_boundaries(self) -> None:
        protocol = frozen_protocol()
        analyzer.validate_protocol(protocol)
        request = json.loads(IMPLEMENTATION_REQUEST_PATH.read_text(encoding="utf-8"))
        self.assertFalse(request["authorization_effective"])
        self.assertFalse(
            request["authorized_checks_if_user_explicitly_approves_this_request"][
                "real_checkpoint_or_data_use"
            ]
        )
        self.assertFalse(
            request["post_implementation_boundary"][
                "implementation_success_authorizes_real_execution"
            ]
        )
        self.assertEqual(analyzer.PROTOCOL_SHA256, runner.PROTOCOL_SHA256)
        self.assertEqual(analyzer.FORWARD_ORDER, runner.FORWARD_ORDER)

    def test_protocol_tampering_fails_closed(self) -> None:
        mutations = (
            lambda p: p["exact_case"].__setitem__("fold", "B"),
            lambda p: p["future_real_execution_contract"].__setitem__("forward_count", 5),
            lambda p: p["future_real_execution_contract"].__setitem__(
                "allowed_npz_members", ["partial", "implant"]
            ),
            lambda p: p["authorization_boundary"].__setitem__(
                "gpu_use_authorized_by_this_protocol", True
            ),
        )
        for mutation in mutations:
            protocol = frozen_protocol()
            mutation(protocol)
            with self.assertRaises(analyzer.ContractError):
                analyzer.validate_protocol(protocol)

    def test_execution_authorization_is_separate_exact_and_single_use(self) -> None:
        output = Path("/tmp/synthetic-one-case-diagnostic")
        good = valid_execution_authorization(output)
        runner.validate_execution_authorization(good, analyzer.PROTOCOL_SHA256, output)
        for key in ("authorization_effective", "execution_authorized", "authorized_once"):
            bad = copy.deepcopy(good)
            bad[key] = False
            with self.assertRaises(analyzer.ContractError):
                runner.validate_execution_authorization(bad, analyzer.PROTOCOL_SHA256, output)
        bad = copy.deepcopy(good)
        bad["conditions"] = ["native_qc", "bias_zero"]
        with self.assertRaises(analyzer.ContractError):
            runner.validate_execution_authorization(bad, analyzer.PROTOCOL_SHA256, output)
        bad = copy.deepcopy(good)
        bad["protected_payload_access"]["gt"] = True
        with self.assertRaises(analyzer.ContractError):
            runner.validate_execution_authorization(bad, analyzer.PROTOCOL_SHA256, output)
        bad = copy.deepcopy(good)
        bad["round_b_authorized"] = True
        with self.assertRaises(analyzer.ContractError):
            runner.validate_execution_authorization(bad, analyzer.PROTOCOL_SHA256, output)


class InterventionAndLedgerTests(unittest.TestCase):
    def test_two_probability_transforms_are_exact_and_nonmutating(self) -> None:
        probability = torch.tensor([[0.1, 0.2, 0.7]], dtype=torch.float32)
        original = probability.clone()
        zero = runner.intervene_probability(
            probability, "bias_zero", fold=analyzer.FOLD, case_id=analyzer.CASE_ID
        )
        mean = runner.intervene_probability(
            probability,
            "case_mean_probability",
            fold=analyzer.FOLD,
            case_id=analyzer.CASE_ID,
        )
        self.assertTrue(torch.equal(zero, torch.ones_like(probability)))
        self.assertTrue(
            torch.equal(mean, probability.mean(-1, keepdim=True).expand_as(probability))
        )
        self.assertTrue(torch.equal(probability, original))
        for condition in ("native_qc", "fixed_probability_permutation", "other"):
            with self.assertRaises(analyzer.ContractError):
                runner.intervene_probability(
                    probability, condition, fold=analyzer.FOLD, case_id=analyzer.CASE_ID
                )
        with self.assertRaises(analyzer.ContractError):
            runner.intervene_probability(
                probability, "bias_zero", fold="B", case_id=analyzer.CASE_ID
            )

    def test_exact_arithmetic_softmax_negative_control(self) -> None:
        probability = torch.tensor([[0.1, 0.3, 0.5, 0.8]], dtype=torch.float64)
        logits = torch.tensor(
            [[[0.2, -0.4, 0.8, 0.1], [-1.0, 0.3, 0.7, 0.2]]],
            dtype=torch.float64,
        )
        zero = torch.ones_like(probability)
        mean = probability.mean(-1, keepdim=True).expand_as(probability)
        attention_zero = torch.softmax(logits + zero.log().unsqueeze(1), dim=-1)
        attention_mean = torch.softmax(logits + mean.log().unsqueeze(1), dim=-1)
        self.assertLessEqual(
            float((attention_zero - attention_mean).abs().max().item()), 1e-15
        )

    def test_ledger_rejects_wrong_member_case_order_and_extra_forward(self) -> None:
        ledger = runner.AccessLedger()
        with self.assertRaises(analyzer.ContractError):
            ledger.record_member("implant")
        with self.assertRaises(analyzer.ContractError):
            ledger.record_npz_open("B", analyzer.CASE_ID)
        ledger = runner.AccessLedger()
        ledger.record_checkpoint_load(analyzer.RUN_KEY)
        with self.assertRaises(analyzer.ContractError):
            ledger.record_checkpoint_load(analyzer.RUN_KEY)
        ledger = runner.AccessLedger()
        with self.assertRaises(analyzer.ContractError):
            ledger.record_forward("case_mean_probability_rep0")
        ledger = complete_ledger()
        with self.assertRaises(analyzer.ContractError):
            ledger.record_forward("bias_zero_rep0")

    def test_temporary_hook_removal_uses_only_a_cpu_toy_module(self) -> None:
        class ToyConditioner(torch.nn.Module):
            def forward(self, query, proxy, position, probability, epoch=None):
                return query + probability.mean()

        module = ToyConditioner()
        ledger = runner.AccessLedger()
        probability = torch.tensor([[0.1, 0.2, 0.4]], dtype=torch.float32)
        with runner.temporary_probability_intervention(
            module,
            "bias_zero",
            fold=analyzer.FOLD,
            case_id=analyzer.CASE_ID,
            ledger=ledger,
        ) as captured:
            module(torch.zeros(1), torch.zeros(1), torch.zeros(1), probability)
            self.assertEqual(len(module._forward_pre_hooks), 1)
            self.assertIn("original_contact_probability", captured)
            self.assertIn("intervened_contact_probability", captured)
        self.assertEqual(len(module._forward_pre_hooks), 0)
        self.assertEqual(ledger.counts["probability_hooks_registered"], 1)
        self.assertEqual(ledger.counts["probability_hooks_removed"], 1)


class ScalarMathTests(unittest.TestCase):
    def test_summary_hash_error_percentile_and_mm_conversion(self) -> None:
        left = torch.zeros((1, 2, 3), dtype=torch.float32)
        right = torch.tensor(
            [[[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]], dtype=torch.float32
        )
        summary = runner.scalar_summary(right)
        self.assertEqual(summary["element_count"], 6)
        self.assertEqual(summary["shape"], [1, 2, 3])
        self.assertEqual(summary["max"], 2.0)
        self.assertEqual(summary["tensor_sha256"], runner.tensor_sha256(right.clone()))
        error = runner.pairwise_error(left, right)
        self.assertEqual(error["max_abs"], 2.0)
        self.assertAlmostEqual(error["mean_abs"], 0.5)
        prediction = runner.prediction_error(left, right, analyzer.NORMALIZATION_SCALE_MM)
        self.assertEqual(prediction["coordinate_max_abs_normalized"], 2.0)
        self.assertAlmostEqual(
            prediction["coordinate_max_abs_mm"], 2.0 * analyzer.NORMALIZATION_SCALE_MM
        )
        self.assertEqual(prediction["point_l2_max_normalized"], 2.0)

    def test_tensor_sha_is_byte_sensitive_even_when_numeric_error_is_zero(self) -> None:
        positive_zero = torch.tensor([0.0], dtype=torch.float32)
        negative_zero = torch.tensor([-0.0], dtype=torch.float32)
        error = runner.pairwise_error(positive_zero, negative_zero)
        self.assertEqual(error["max_abs"], 0.0)
        self.assertFalse(error["bitwise_equal"])
        self.assertNotEqual(error["left_tensor_sha256"], error["right_tensor_sha256"])

    def test_changed_model_state_fails_closed(self) -> None:
        with self.assertRaises(analyzer.ContractError):
            runner.compile_scalar_result(
                synthetic_records(),
                complete_ledger(),
                state_hashes(),
                state_hashes("changed"),
            )


class DiagnosticClassificationTests(unittest.TestCase):
    def test_exact_negative_control_is_descriptive_and_non_authorizing(self) -> None:
        result = compile_result("exact")
        analysis = analyzer.analyze_scalar_result(result)
        self.assertEqual(analysis["diagnosis"], "EXACT_NEGATIVE_CONTROL_REPRODUCED")
        self.assertEqual(analysis["earliest_nonzero_cross_condition_stage"], "none")
        self.assertFalse(analysis["evidence_flags"]["repeat_nondeterminism_present"])
        self.assertFalse(analysis["round_a_i_retry_authorized"])
        self.assertFalse(analysis["threshold_change_authorized"])
        self.assertFalse(analysis["round_b_authorized"])
        json.dumps(result, allow_nan=False)

    def test_injected_repeat_variability_is_inconclusive(self) -> None:
        analysis = analyzer.analyze_scalar_result(compile_result("repeat"))
        self.assertTrue(analysis["evidence_flags"]["repeat_nondeterminism_present"])
        self.assertTrue(analysis["evidence_flags"]["inconclusive"])
        self.assertEqual(analysis["diagnosis"], "INCONCLUSIVE_REPEAT_VARIABILITY")

    def test_injected_centered_logit_roundoff_is_localized(self) -> None:
        analysis = analyzer.analyze_scalar_result(compile_result("centered_roundoff"))
        self.assertTrue(
            analysis["evidence_flags"]["cross_condition_roundoff_before_softmax"]
        )
        self.assertEqual(
            analysis["earliest_nonzero_cross_condition_stage"],
            "query_logits_row_centered",
        )
        self.assertEqual(
            analysis["diagnosis"], "CONSTANT_SHIFT_ROUNDOFF_BEFORE_SOFTMAX"
        )

    def test_injected_softmax_difference_and_downstream_amplification(self) -> None:
        analysis = analyzer.analyze_scalar_result(compile_result("downstream"))
        self.assertTrue(analysis["evidence_flags"]["softmax_roundoff_first_visible"])
        self.assertTrue(analysis["evidence_flags"]["downstream_amplification_present"])
        self.assertEqual(
            analysis["earliest_nonzero_cross_condition_stage"], "query_attention"
        )
        threshold = analysis["parent_threshold_observation"]
        self.assertFalse(threshold["attention_exceeds_reference"])
        self.assertTrue(threshold["prediction_exceeds_reference"])
        self.assertTrue(threshold["reference_only_no_threshold_change"])


class ScalarOnlyAndBoundaryTests(unittest.TestCase):
    def test_raw_tensor_coordinate_extra_condition_and_extra_case_are_rejected(self) -> None:
        result = compile_result()
        bad = copy.deepcopy(result)
        bad["raw_tensor_values"] = [1.0, 2.0, 3.0]
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_scalar_result(bad)
        bad = copy.deepcopy(result)
        bad["per_forward"]["bias_zero_rep0"]["stages"]["predicted_implant"][
            "coordinates"
        ] = [[0.0, 0.0, 0.0]]
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_scalar_result(bad)
        bad = copy.deepcopy(result)
        bad["per_forward"]["bias_zero_rep0"]["condition"] = "native_qc"
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_scalar_result(bad)
        bad = copy.deepcopy(result)
        bad["identity"]["case_id"] = "train__001__frontoorbital"
        with self.assertRaises(analyzer.ContractError):
            analyzer.validate_scalar_result(bad)

    def test_failure_receipt_contains_only_validated_scalar_summaries(self) -> None:
        summary = runner.scalar_summary(torch.ones((1, 2), dtype=torch.float32))
        receipt = runner.build_failure_receipt(
            analyzer.ContractError("synthetic failure"),
            runner.AccessLedger(),
            {"bias_zero_rep0": {"query_attention": summary}},
        )
        self.assertEqual(receipt["status"], "FAILED_STOPPED_NO_RETRY")
        self.assertFalse(receipt["raw_tensors_saved"])
        self.assertFalse(receipt["point_coordinates_saved"])
        self.assertFalse(receipt["automatic_retry"])
        self.assertFalse(receipt["round_b_authorized"])
        json.dumps(receipt, allow_nan=False)
        with self.assertRaises(analyzer.ContractError):
            runner.build_failure_receipt(
                RuntimeError("bad"),
                runner.AccessLedger(),
                {"bias_zero_rep0": {"predicted_coordinates": summary}},
            )

    def test_path_and_hash_checks_use_only_temporary_non_npz_files(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            payload = root / "synthetic.txt"
            payload.write_bytes(b"synthetic scalar contract\n")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            self.assertEqual(runner.resolve_under(root, "synthetic.txt"), payload.resolve())
            runner.verify_file(payload, digest, payload.stat().st_size)
            with self.assertRaises(analyzer.ContractError):
                runner.resolve_under(root, "../escape", must_exist=False)
            with self.assertRaises(analyzer.ContractError):
                runner.verify_file(payload, "0" * 64)

    def test_pure_contract_path_never_calls_real_access_boundaries(self) -> None:
        states = state_hashes()
        with mock.patch.object(
            runner.np, "load", side_effect=AssertionError("NPZ access")
        ) as npz, mock.patch.object(
            torch, "load", side_effect=AssertionError("checkpoint access")
        ) as checkpoint, mock.patch.object(
            torch.cuda, "is_available", side_effect=AssertionError("CUDA query")
        ) as cuda_query, mock.patch.object(
            runner, "_load_model", side_effect=AssertionError("model build")
        ) as model:
            result = runner.compile_scalar_result(
                synthetic_records(), complete_ledger(), states, dict(states)
            )
            analyzer.analyze_scalar_result(result)
        npz.assert_not_called()
        checkpoint.assert_not_called()
        cuda_query.assert_not_called()
        model.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
