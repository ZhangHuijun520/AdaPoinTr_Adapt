"""Isolated certified S2 shadow selector with an exact S0 fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment
import torch

from utils.mamba_d6a_r1_s1_exact_assignment import (
    CANDIDATE_COUNT,
    ROW_TOP_K,
    SLOT_COUNT,
    adjusted_scores_cpu_float64,
    frozen_reference_diagnostics,
    row_top32_tie_safe_union,
)


GUARD_MULTIPLIER = 256.0


@dataclass(frozen=True)
class S2Assignment:
    """S2 outputs and observation-only certification diagnostics."""

    hard_assignment: Any
    selected_indices: Any
    slot_to_candidate: Any
    adjusted_objective: np.float64
    route: str
    fallback_reason: str
    union_columns: np.ndarray
    cutoff_gap_minimum: np.float64
    cutoff_guard_maximum: np.float64
    uniqueness_gap: np.float64
    uniqueness_guard: np.float64
    edge_exclusion_solves: int


def _objective(adjusted: np.ndarray, columns: np.ndarray) -> np.float64:
    return np.sum(adjusted[np.arange(SLOT_COUNT), columns], dtype=np.float64)


def cutoff_diagnostics(adjusted: np.ndarray) -> tuple[np.float64, np.float64, bool]:
    """Return the minimum cutoff gap, maximum guard, and ambiguity flag."""

    scores = np.asarray(adjusted)
    if scores.shape != (SLOT_COUNT, CANDIDATE_COUNT):
        raise ValueError("adjusted scores must have shape (32, 8192)")
    if scores.dtype != np.float64 or not np.isfinite(scores).all():
        raise ValueError("adjusted scores must be finite float64")
    positions = (CANDIDATE_COUNT - ROW_TOP_K - 1, CANDIDATE_COUNT - ROW_TOP_K)
    partitioned = np.partition(scores, positions, axis=1)
    thirty_third = partitioned[:, positions[0]]
    thirty_second = partitioned[:, positions[1]]
    gaps = thirty_second - thirty_third
    row_scales = np.maximum(1.0, np.max(np.abs(scores), axis=1))
    guards = GUARD_MULTIPLIER * np.finfo(np.float64).eps * row_scales
    ambiguous = bool(np.any(gaps <= guards))
    return np.min(gaps), np.max(guards), ambiguous


def _solve_reduced(
    adjusted: np.ndarray, union_columns: np.ndarray
) -> tuple[np.ndarray, np.float64, np.ndarray]:
    reduced = adjusted[:, union_columns]
    rows, reduced_columns = linear_sum_assignment(reduced, maximize=True)
    if not np.array_equal(rows, np.arange(SLOT_COUNT)):
        raise RuntimeError("Reduced assignment did not cover every slot in order")
    columns = union_columns[reduced_columns].astype(np.int64, copy=False)
    if np.unique(columns).size != SLOT_COUNT:
        raise RuntimeError("Reduced assignment produced duplicate candidates")
    return columns, _objective(adjusted, columns), reduced


def uniqueness_certificate(
    adjusted: np.ndarray,
    union_columns: np.ndarray,
    best_columns: np.ndarray,
    best_objective: np.float64,
    reduced: np.ndarray,
) -> tuple[np.float64, np.float64, bool, int]:
    """Certify a robustly unique optimum through all 32 edge exclusions."""

    union_positions = {int(column): index for index, column in enumerate(union_columns)}
    alternative_objectives = []
    alternative_abs_sums = []
    for row, original_column in enumerate(best_columns):
        forbidden_position = union_positions[int(original_column)]
        excluded = reduced.copy()
        excluded[row, forbidden_position] = -np.inf
        alt_rows, alt_reduced_columns = linear_sum_assignment(excluded, maximize=True)
        if not np.array_equal(alt_rows, np.arange(SLOT_COUNT)):
            raise RuntimeError("Edge-exclusion assignment did not cover every slot")
        if alt_reduced_columns[row] == forbidden_position:
            raise RuntimeError("Edge-exclusion solver selected the forbidden edge")
        alt_columns = union_columns[alt_reduced_columns]
        if np.unique(alt_columns).size != SLOT_COUNT:
            raise RuntimeError("Edge-exclusion assignment produced duplicate candidates")
        values = adjusted[np.arange(SLOT_COUNT), alt_columns]
        alternative_objectives.append(np.sum(values, dtype=np.float64))
        alternative_abs_sums.append(np.sum(np.abs(values), dtype=np.float64))

    second_index = int(np.argmax(np.asarray(alternative_objectives, dtype=np.float64)))
    second_best = np.float64(alternative_objectives[second_index])
    gap = np.float64(best_objective - second_best)
    best_abs_sum = np.sum(
        np.abs(adjusted[np.arange(SLOT_COUNT), best_columns]), dtype=np.float64
    )
    scale = max(
        1.0,
        abs(float(best_objective)),
        abs(float(second_best)),
        float(best_abs_sum),
        float(alternative_abs_sums[second_index]),
    )
    guard = np.float64(GUARD_MULTIPLIER * np.finfo(np.float64).eps * scale)
    certified = bool(np.isfinite(gap) and np.isfinite(guard) and gap > guard)
    return gap, guard, certified, SLOT_COUNT


def _build_output(
    slot_logits: "torch.Tensor",
    columns: np.ndarray,
    objective: np.float64,
    *,
    route: str,
    fallback_reason: str,
    union_columns: np.ndarray,
    cutoff_gap_minimum: np.float64,
    cutoff_guard_maximum: np.float64,
    uniqueness_gap: np.float64,
    uniqueness_guard: np.float64,
    edge_exclusion_solves: int,
) -> S2Assignment:
    hard = torch.zeros_like(slot_logits)
    rows = torch.arange(SLOT_COUNT, device=slot_logits.device)
    mapped = torch.as_tensor(columns, device=slot_logits.device, dtype=torch.long)
    hard[0, rows, mapped] = 1.0
    selected = torch.sort(mapped).values.unsqueeze(0)
    return S2Assignment(
        hard_assignment=hard,
        selected_indices=selected,
        slot_to_candidate=mapped.unsqueeze(0),
        adjusted_objective=np.float64(objective),
        route=route,
        fallback_reason=fallback_reason,
        union_columns=union_columns,
        cutoff_gap_minimum=np.float64(cutoff_gap_minimum),
        cutoff_guard_maximum=np.float64(cutoff_guard_maximum),
        uniqueness_gap=np.float64(uniqueness_gap),
        uniqueness_guard=np.float64(uniqueness_guard),
        edge_exclusion_solves=edge_exclusion_solves,
    )


def _fallback(
    slot_logits: "torch.Tensor",
    reason: str,
    union_columns: np.ndarray,
    cutoff_gap: np.float64,
    cutoff_guard: np.float64,
    uniqueness_gap: np.float64 = np.float64("nan"),
    uniqueness_guard: np.float64 = np.float64("nan"),
    edge_exclusion_solves: int = 0,
) -> S2Assignment:
    hard, selected, slots, objective = frozen_reference_diagnostics(slot_logits)
    return S2Assignment(
        hard_assignment=hard,
        selected_indices=selected,
        slot_to_candidate=slots,
        adjusted_objective=np.float64(objective),
        route="fallback_s0",
        fallback_reason=reason,
        union_columns=union_columns,
        cutoff_gap_minimum=np.float64(cutoff_gap),
        cutoff_guard_maximum=np.float64(cutoff_guard),
        uniqueness_gap=np.float64(uniqueness_gap),
        uniqueness_guard=np.float64(uniqueness_guard),
        edge_exclusion_solves=edge_exclusion_solves,
    )


def s2_certified_fast_path_assignment(slot_logits: "torch.Tensor") -> S2Assignment:
    """Run certified reduced assignment or independently return complete S0."""

    adjusted = adjusted_scores_cpu_float64(slot_logits)
    cutoff_gap, cutoff_guard, cutoff_ambiguous = cutoff_diagnostics(adjusted)
    union_columns = row_top32_tie_safe_union(adjusted)
    if cutoff_ambiguous:
        return _fallback(
            slot_logits,
            "cutoff_tie_or_near_tie",
            union_columns,
            cutoff_gap,
            cutoff_guard,
        )

    try:
        columns, best_objective, reduced = _solve_reduced(adjusted, union_columns)
        gap, guard, certified, exclusion_solves = uniqueness_certificate(
            adjusted, union_columns, columns, best_objective, reduced
        )
    except (ValueError, RuntimeError):
        return _fallback(
            slot_logits,
            "solver_or_assignment_invariant_failure",
            union_columns,
            cutoff_gap,
            cutoff_guard,
        )

    if not certified:
        return _fallback(
            slot_logits,
            "global_optimum_not_certified_unique",
            union_columns,
            cutoff_gap,
            cutoff_guard,
            gap,
            guard,
            exclusion_solves,
        )
    return _build_output(
        slot_logits,
        columns,
        best_objective,
        route="certified_fast_path",
        fallback_reason="none",
        union_columns=union_columns,
        cutoff_gap_minimum=cutoff_gap,
        cutoff_guard_maximum=cutoff_guard,
        uniqueness_gap=gap,
        uniqueness_guard=guard,
        edge_exclusion_solves=exclusion_solves,
    )


__all__ = [
    "GUARD_MULTIPLIER",
    "S2Assignment",
    "cutoff_diagnostics",
    "s2_certified_fast_path_assignment",
    "uniqueness_certificate",
]
