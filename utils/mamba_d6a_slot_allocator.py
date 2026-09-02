"""Frozen R0/R1 proposal helpers for Mamba v1.6 D6-A."""

from __future__ import annotations

import inspect
import math
from typing import Dict, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from scipy.optimize import linear_sum_assignment
from torch import nn

from utils.mamba_d4a_proposal import case_balanced_binary_cross_entropy
from utils.mamba_d5a_proposal import (
    D5V1ContextHead,
    d5_v1_set_level_loss,
    geometry_descriptor_27d,
    select_deterministic_top32,
)


CANDIDATE_COUNT = 8192
DESCRIPTOR_DIMENSIONS = 27
POINT_FEATURE_DIMENSIONS = 64
SLOT_COUNT = 32
SLOT_DIMENSIONS = 64
PARAMETER_MAXIMUM = 100000


def _validate_descriptors(descriptors: torch.Tensor) -> None:
    if not torch.is_tensor(descriptors) or descriptors.ndim != 3:
        raise ValueError("descriptors must have shape (B, 8192, 27)")
    if descriptors.shape[1:] != (CANDIDATE_COUNT, DESCRIPTOR_DIMENSIONS):
        raise ValueError("descriptors must have shape (B, 8192, 27)")
    if not descriptors.is_floating_point() or not torch.isfinite(descriptors).all():
        raise ValueError("descriptors must contain finite floating-point values")


def _validate_slot_logits(slot_logits: torch.Tensor, *, fixed_candidates: bool) -> None:
    if not torch.is_tensor(slot_logits) or slot_logits.ndim != 3:
        raise ValueError("slot_logits must have shape (B, 32, N)")
    if slot_logits.shape[1] != SLOT_COUNT:
        raise ValueError("slot_logits must contain exactly 32 slots")
    if fixed_candidates and slot_logits.shape[2] != CANDIDATE_COUNT:
        raise ValueError("production assignment requires exactly 8192 candidates")
    if slot_logits.shape[2] < SLOT_COUNT:
        raise ValueError("candidate count must be at least 32")
    if not slot_logits.is_floating_point() or not torch.isfinite(slot_logits).all():
        raise ValueError("slot_logits must contain finite floating-point values")


def deterministic_global_assignment(
    slot_logits: torch.Tensor,
    *,
    fixed_candidates: bool = True,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Return slot-ordered one-hot assignment and sorted unique selected indices."""

    _validate_slot_logits(slot_logits, fixed_candidates=fixed_candidates)
    batch_size, slot_count, candidate_count = slot_logits.shape
    hard = torch.zeros_like(slot_logits)
    selected_sets = []
    candidate_indices = np.arange(candidate_count, dtype=np.float64)
    epsilon = np.finfo(np.float64).eps
    for batch_index in range(batch_size):
        scores = slot_logits[batch_index].detach().to("cpu", torch.float64).numpy()
        adjusted = scores - epsilon * candidate_indices[None, :]
        row_indices, column_indices = linear_sum_assignment(adjusted, maximize=True)
        if row_indices.shape[0] != slot_count or not np.array_equal(
            np.sort(row_indices), np.arange(slot_count)
        ):
            raise RuntimeError("global assignment did not cover all slots")
        slot_to_candidate = np.empty(slot_count, dtype=np.int64)
        slot_to_candidate[row_indices] = column_indices
        if np.unique(slot_to_candidate).size != slot_count:
            raise RuntimeError("global assignment produced duplicate candidates")
        rows = torch.arange(slot_count, device=slot_logits.device)
        columns = torch.as_tensor(
            slot_to_candidate, device=slot_logits.device, dtype=torch.long
        )
        hard[batch_index, rows, columns] = 1.0
        selected_sets.append(torch.sort(columns).values)
    return hard, torch.stack(selected_sets, dim=0)


def slot_order_greedy_assignment_score(slot_logits: torch.Tensor) -> torch.Tensor:
    """Diagnostic only: score the forbidden slot-order greedy assignment."""

    _validate_slot_logits(slot_logits, fixed_candidates=False)
    totals = []
    for batch in slot_logits:
        available = torch.ones(batch.shape[1], dtype=torch.bool, device=batch.device)
        total = batch.new_zeros(())
        for row in batch:
            masked = row.masked_fill(~available, float("-inf"))
            index = torch.argmax(masked)
            total = total + row[index]
            available[index] = False
        totals.append(total)
    return torch.stack(totals)


def assignment_score(slot_logits: torch.Tensor, hard: torch.Tensor) -> torch.Tensor:
    _validate_slot_logits(slot_logits, fixed_candidates=False)
    if hard.shape != slot_logits.shape:
        raise ValueError("hard assignment must match slot_logits")
    return (slot_logits * hard).sum(dim=(1, 2))


def straight_through_assignment(
    slot_logits: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Use the frozen global hard-forward and row-softmax backward estimator."""

    hard, selected = deterministic_global_assignment(slot_logits)
    soft = torch.softmax(slot_logits, dim=-1)
    ste = hard + (soft - soft.detach())
    if not torch.equal(ste.detach(), hard):
        raise RuntimeError("straight-through hard forward drifted")
    return ste, hard, selected


class D6R1SlotAllocator(nn.Module):
    """27D shared point encoder plus assignment-consistent 32-slot allocator."""

    def __init__(self) -> None:
        super().__init__()
        self.point_encoder = nn.Sequential(
            nn.Linear(27, 64),
            nn.GELU(),
            nn.Linear(64, 64),
            nn.GELU(),
        )
        self.point_calibration = nn.Sequential(
            nn.Linear(219, 128),
            nn.GELU(),
            nn.Linear(128, 64),
            nn.GELU(),
            nn.Linear(64, 1),
        )
        self.slots = nn.Parameter(torch.empty(SLOT_COUNT, SLOT_DIMENSIONS))
        self.global_to_slot = nn.Linear(128, 64)
        self.query = nn.Linear(64, 64)
        self.key = nn.Linear(64, 64)
        self.value = nn.Linear(64, 64)
        self.attention_output = nn.Linear(64, 64)
        self.attention_norm = nn.LayerNorm(64)
        self.ffn = nn.Sequential(nn.Linear(64, 128), nn.GELU(), nn.Linear(128, 64))
        self.ffn_norm = nn.LayerNorm(64)
        self.slot_pointer = nn.Linear(64, 64)
        self.point_pointer = nn.Linear(64, 64)
        self.reset_parameters()
        if self.trainable_parameter_count() > PARAMETER_MAXIMUM:
            raise RuntimeError("D6-A R1 exceeds the frozen parameter gate")

    def reset_parameters(self) -> None:
        nn.init.trunc_normal_(self.slots, std=0.02)
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.trunc_normal_(module.weight, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.LayerNorm):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def trainable_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters() if parameter.requires_grad)

    def forward(self, descriptors: torch.Tensor) -> Dict[str, torch.Tensor]:
        _validate_descriptors(descriptors)
        point_features = self.point_encoder(descriptors)
        mean_context = point_features.mean(dim=1)
        max_context = point_features.amax(dim=1)
        global_context = torch.cat((mean_context, max_context), dim=-1)
        expanded_context = global_context.unsqueeze(1).expand(-1, CANDIDATE_COUNT, -1)
        classifier_input = torch.cat(
            (point_features, expanded_context, descriptors), dim=-1
        )
        if classifier_input.shape[-1] != 219:
            raise RuntimeError("D6-A shared classifier input dimension drifted")
        point_logits = self.point_calibration(classifier_input).squeeze(-1)

        slots = self.slots.unsqueeze(0).expand(descriptors.shape[0], -1, -1)
        slots = slots + self.global_to_slot(global_context).unsqueeze(1)
        queries = self.query(slots)
        keys = self.key(point_features)
        values = self.value(point_features)
        attention_logits = torch.einsum("bsd,bnd->bsn", queries, keys) / math.sqrt(64.0)
        attention = torch.softmax(attention_logits, dim=-1)
        attended = torch.einsum("bsn,bnd->bsd", attention, values)
        slots = self.attention_norm(slots + self.attention_output(attended))
        slots = self.ffn_norm(slots + self.ffn(slots))

        pointer_slots = self.slot_pointer(slots)
        pointer_points = self.point_pointer(point_features)
        slot_logits = torch.einsum(
            "bsd,bnd->bsn", pointer_slots, pointer_points
        ) / math.sqrt(64.0)
        slot_logits = slot_logits + point_logits.unsqueeze(1)
        if slot_logits.shape != (descriptors.shape[0], SLOT_COUNT, CANDIDATE_COUNT):
            raise RuntimeError("D6-A slot logits shape drifted")
        if not torch.isfinite(point_logits).all() or not torch.isfinite(slot_logits).all():
            raise RuntimeError("D6-A R1 produced non-finite logits")
        return {
            "point_features": point_features,
            "point_logits": point_logits,
            "slot_logits": slot_logits,
        }

    @torch.no_grad()
    def infer_indices(self, descriptors: torch.Tensor) -> torch.Tensor:
        """Return sorted 32-index sets. Ground truth is intentionally absent."""

        outputs = self(descriptors)
        _, selected = deterministic_global_assignment(outputs["slot_logits"])
        return selected


def d6a_raw_losses(
    outputs: Dict[str, torch.Tensor],
    positive_mask: torch.Tensor,
) -> Dict[str, torch.Tensor]:
    """Compute the three frozen raw losses before gradient-ratio calibration."""

    point_logits = outputs.get("point_logits")
    slot_logits = outputs.get("slot_logits")
    if point_logits is None or slot_logits is None:
        raise ValueError("outputs must contain point_logits and slot_logits")
    _validate_slot_logits(slot_logits, fixed_candidates=True)
    if point_logits.shape != (slot_logits.shape[0], CANDIDATE_COUNT):
        raise ValueError("point_logits shape drifted")
    mask = torch.as_tensor(positive_mask, device=point_logits.device, dtype=torch.bool)
    if mask.shape != point_logits.shape:
        raise ValueError("positive_mask must have shape (B, 8192)")
    counts = mask.sum(dim=1)
    if torch.any(counts <= 0) or torch.any(counts >= CANDIDATE_COUNT):
        raise ValueError("each case requires 0 < positive_count < 8192")

    point = case_balanced_binary_cross_entropy(point_logits, mask)
    ste, hard, selected = straight_through_assignment(slot_logits)
    selected_positive_mass = (ste * mask.unsqueeze(1)).sum(dim=(1, 2))
    support = (F.softplus(8.0 * (0.5 - selected_positive_mass)) / 8.0).mean()

    soft = torch.softmax(slot_logits, dim=-1)
    row_entropy = (
        -(soft * torch.log(soft + 1.0e-8)).sum(dim=-1) / math.log(CANDIDATE_COUNT)
    ).mean()
    column_mass = soft.sum(dim=1)
    collision = F.relu(column_mass - 1.0).square().sum(dim=1).div(SLOT_COUNT).mean()
    shape = row_entropy + collision
    if not all(torch.isfinite(value) for value in (point, support, shape)):
        raise RuntimeError("D6-A raw loss is non-finite")
    return {
        "L_point": point,
        "L_support": support,
        "L_shape": shape,
        "hard_assignment": hard,
        "selected_indices": selected,
        "selected_positive_mass": selected_positive_mass.detach(),
    }


def inference_signature_has_no_ground_truth() -> bool:
    parameters = inspect.signature(D6R1SlotAllocator.infer_indices).parameters
    return list(parameters) == ["self", "descriptors"]


__all__ = [
    "CANDIDATE_COUNT",
    "D5V1ContextHead",
    "D6R1SlotAllocator",
    "PARAMETER_MAXIMUM",
    "SLOT_COUNT",
    "assignment_score",
    "d5_v1_set_level_loss",
    "d6a_raw_losses",
    "deterministic_global_assignment",
    "geometry_descriptor_27d",
    "inference_signature_has_no_ground_truth",
    "select_deterministic_top32",
    "slot_order_greedy_assignment_score",
    "straight_through_assignment",
]
