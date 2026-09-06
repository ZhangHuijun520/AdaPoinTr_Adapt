"""Isolated exact-reduction shadow selector for D6-A R1 S1 feasibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment
import torch


SLOT_COUNT = 32
CANDIDATE_COUNT = 8192
ROW_TOP_K = 32


@dataclass(frozen=True)
class S1Assignment:
    """S1 output plus observation-only reduction diagnostics."""

    hard_assignment: Any
    selected_indices: Any
    slot_to_candidate: Any
    adjusted_objective: np.float64
    union_columns: np.ndarray


def _validate(slot_logits: "torch.Tensor") -> None:
    import torch

    if not torch.is_tensor(slot_logits) or slot_logits.ndim != 3:
        raise ValueError("slot_logits must have shape (1, 32, 8192)")
    if tuple(slot_logits.shape) != (1, SLOT_COUNT, CANDIDATE_COUNT):
        raise ValueError("S1 zero-step requires shape (1, 32, 8192)")
    if slot_logits.dtype != torch.float32:
        raise ValueError("S1 zero-step requires float32 logits")
    if not torch.isfinite(slot_logits).all():
        raise ValueError("slot_logits must be finite")


def adjusted_scores_cpu_float64(slot_logits: "torch.Tensor") -> np.ndarray:
    """Apply the unchanged frozen R1 CPU float64 epsilon adjustment."""

    _validate(slot_logits)
    scores = slot_logits[0].detach().to("cpu", torch.float64).numpy()
    candidate_indices = np.arange(CANDIDATE_COUNT, dtype=np.float64)
    return scores - np.finfo(np.float64).eps * candidate_indices[None, :]


def row_top32_tie_safe_union(adjusted_scores: np.ndarray) -> np.ndarray:
    """Return the ascending union of all row-top32 columns, including ties."""

    scores = np.asarray(adjusted_scores)
    if scores.shape != (SLOT_COUNT, CANDIDATE_COUNT):
        raise ValueError("adjusted_scores must have shape (32, 8192)")
    if scores.dtype != np.float64 or not np.isfinite(scores).all():
        raise ValueError("adjusted_scores must be finite float64")
    cutoff_index = CANDIDATE_COUNT - ROW_TOP_K
    cutoffs = np.partition(scores, cutoff_index, axis=1)[:, cutoff_index]
    retained = np.any(scores >= cutoffs[:, None], axis=0)
    union_columns = np.flatnonzero(retained).astype(np.int64, copy=False)
    if union_columns.size < SLOT_COUNT:
        raise RuntimeError("tie-safe union cannot contain fewer than 32 columns")
    if union_columns.size > CANDIDATE_COUNT:
        raise RuntimeError("tie-safe union exceeds the candidate universe")
    if union_columns.size > 1 and not np.all(np.diff(union_columns) > 0):
        raise RuntimeError("union columns are not strictly ascending")
    return union_columns


def s1_slot_mapping_from_adjusted(
    adjusted_scores: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.float64]:
    """Solve the pure-NumPy/SciPy S1 core for independent equivalence tests."""

    adjusted = np.asarray(adjusted_scores)
    union_columns = row_top32_tie_safe_union(adjusted)
    reduced = adjusted[:, union_columns]
    row_indices, reduced_columns = linear_sum_assignment(reduced, maximize=True)
    if row_indices.shape[0] != SLOT_COUNT or not np.array_equal(
        np.sort(row_indices), np.arange(SLOT_COUNT)
    ):
        raise RuntimeError("S1 assignment did not cover all slots")
    slot_to_candidate = np.empty(SLOT_COUNT, dtype=np.int64)
    slot_to_candidate[row_indices] = union_columns[reduced_columns]
    if np.unique(slot_to_candidate).size != SLOT_COUNT:
        raise RuntimeError("S1 assignment produced duplicate candidates")
    objective = np.sum(
        adjusted[np.arange(SLOT_COUNT), slot_to_candidate], dtype=np.float64
    )
    return slot_to_candidate, union_columns, objective


def s1_exact_reduced_assignment(slot_logits: "torch.Tensor") -> S1Assignment:
    """Solve the S1 reduced exact assignment without changing production R1."""

    adjusted = adjusted_scores_cpu_float64(slot_logits)
    slot_to_candidate, union_columns, objective = s1_slot_mapping_from_adjusted(
        adjusted
    )

    import torch

    hard = torch.zeros_like(slot_logits)
    rows = torch.arange(SLOT_COUNT, device=slot_logits.device)
    columns = torch.as_tensor(
        slot_to_candidate, device=slot_logits.device, dtype=torch.long
    )
    hard[0, rows, columns] = 1.0
    selected = torch.sort(columns).values.unsqueeze(0)
    return S1Assignment(
        hard_assignment=hard,
        selected_indices=selected,
        slot_to_candidate=columns.unsqueeze(0),
        adjusted_objective=objective,
        union_columns=union_columns,
    )


def frozen_reference_diagnostics(
    slot_logits: "torch.Tensor",
) -> Tuple["torch.Tensor", "torch.Tensor", "torch.Tensor", np.float64]:
    """Reproduce S0 diagnostics for comparison, without a production mutation."""

    from utils.mamba_d6a_slot_allocator import deterministic_global_assignment

    adjusted = adjusted_scores_cpu_float64(slot_logits)
    hard, selected = deterministic_global_assignment(slot_logits)
    slot_to_candidate = hard.argmax(dim=-1).to(dtype=torch.long)
    columns = slot_to_candidate[0].detach().cpu().numpy()
    objective = np.sum(adjusted[np.arange(SLOT_COUNT), columns], dtype=np.float64)
    return hard, selected, slot_to_candidate, objective


__all__ = [
    "CANDIDATE_COUNT",
    "ROW_TOP_K",
    "SLOT_COUNT",
    "S1Assignment",
    "adjusted_scores_cpu_float64",
    "frozen_reference_diagnostics",
    "row_top32_tie_safe_union",
    "s1_exact_reduced_assignment",
    "s1_slot_mapping_from_adjusted",
]
