"""Cranial-SCQR v1.1 components and frozen variant contract."""

from __future__ import annotations

from dataclasses import dataclass

from .contact_support import (
    ContactSupportHead,
    build_contact_support_labels,
    case_balanced_binary_cross_entropy,
)
from .local_geometry import RawLocalGeometryResidual, stable_knn_indices
from .query_conditioning import ContactConditionedQueryAttention


VARIANT_MATRIX = {
    "B0": {
        "enabled": False,
        "local_geometry_enabled": False,
        "contact_supervision_enabled": False,
        "query_conditioning_enabled": False,
        "contact_bias_beta": 0.0,
    },
    "A1": {
        "enabled": True,
        "local_geometry_enabled": True,
        "contact_supervision_enabled": True,
        "query_conditioning_enabled": False,
        "contact_bias_beta": 0.0,
    },
    "Q0": {
        "enabled": True,
        "local_geometry_enabled": True,
        "contact_supervision_enabled": True,
        "query_conditioning_enabled": True,
        "contact_bias_beta": 0.0,
    },
    "QC": {
        "enabled": True,
        "local_geometry_enabled": True,
        "contact_supervision_enabled": True,
        "query_conditioning_enabled": True,
        "contact_bias_beta": 1.0,
    },
}


@dataclass(frozen=True)
class SCQRContract:
    variant: str
    enabled: bool
    local_geometry_enabled: bool
    contact_supervision_enabled: bool
    query_conditioning_enabled: bool
    contact_bias_beta: float
    initialization_seed: int
    auxiliary_loss_weight: float | None


def _read(config, name, default=None):
    return getattr(config, name, default) if config is not None else default


def validate_scqr_config(
    config,
    *,
    embed_dim,
    num_query,
    center_num,
    denoise_weight,
):
    """Validate the exact B0/A1/Q0/QC v1.1 matrix without running tensors."""

    # Absence of the new block means a legacy AdaPoinTr configuration, not an
    # explicit SCQR B0 experiment. Preserve that path compatible with
    # historical settings (including their denoise choices).
    if config is None:
        return SCQRContract(
            variant="B0",
            enabled=False,
            local_geometry_enabled=False,
            contact_supervision_enabled=False,
            query_conditioning_enabled=False,
            contact_bias_beta=0.0,
            initialization_seed=31001,
            auxiliary_loss_weight=None,
        )

    variant = str(_read(config, "variant", "B0"))
    if variant not in VARIANT_MATRIX:
        raise ValueError(f"unsupported Cranial-SCQR variant: {variant!r}")
    expected = VARIANT_MATRIX[variant]
    observed = {
        "enabled": bool(_read(config, "enabled", False)),
        "local_geometry_enabled": bool(
            _read(config, "local_geometry_enabled", False)
        ),
        "contact_supervision_enabled": bool(
            _read(config, "contact_supervision_enabled", False)
        ),
        "query_conditioning_enabled": bool(
            _read(config, "query_conditioning_enabled", False)
        ),
        "contact_bias_beta": float(_read(config, "contact_bias_beta", 0.0)),
    }
    if observed != expected:
        raise ValueError(
            f"Cranial-SCQR {variant} matrix mismatch: "
            f"expected={expected}, observed={observed}"
        )
    locked_values = {
        "embed_dim": (int(embed_dim), 384),
        "num_query": (int(num_query), 256),
        "final_proxy_count": (int(center_num[-1]), 256),
        "local_knn_small": (int(_read(config, "local_knn_small", 16)), 16),
        "local_knn_large": (int(_read(config, "local_knn_large", 32)), 32),
        "attention_dim": (int(_read(config, "attention_dim", 128)), 128),
        "warmup_epochs": (int(_read(config, "warmup_epochs", 20)), 20),
        "rim_band_mm": (float(_read(config, "rim_band_mm", 2.0)), 2.0),
        "alpha_local_init": (float(_read(config, "alpha_local_init", 0.01)), 0.01),
        "alpha_query_init": (float(_read(config, "alpha_query_init", 0.01)), 0.01),
        "attention_dropout": (float(_read(config, "attention_dropout", 0.0)), 0.0),
        "probability_floor": (
            float(_read(config, "probability_floor", 1.0e-4)),
            1.0e-4,
        ),
        "denoise_weight": (float(denoise_weight), 0.0),
    }
    mismatches = {
        key: values for key, values in locked_values.items() if values[0] != values[1]
    }
    if list(center_num) != [512, 256]:
        mismatches["center_num"] = (list(center_num), [512, 256])
    if mismatches:
        raise ValueError(f"Cranial-SCQR frozen contract mismatch: {mismatches}")

    auxiliary_loss_weight = _read(config, "auxiliary_loss_weight", None)
    if auxiliary_loss_weight is not None:
        auxiliary_loss_weight = float(auxiliary_loss_weight)
        if not 0.0 < auxiliary_loss_weight <= 1.0:
            raise ValueError("auxiliary_loss_weight must be in (0, 1]")
    if variant == "B0" and auxiliary_loss_weight is not None:
        raise ValueError("B0 must not configure an auxiliary loss weight")

    initialization_seed = int(_read(config, "initialization_seed", 31001))
    if initialization_seed < 0:
        raise ValueError("initialization_seed must be non-negative")
    return SCQRContract(
        variant=variant,
        initialization_seed=initialization_seed,
        auxiliary_loss_weight=auxiliary_loss_weight,
        **observed,
    )


__all__ = [
    "ContactConditionedQueryAttention",
    "ContactSupportHead",
    "RawLocalGeometryResidual",
    "SCQRContract",
    "VARIANT_MATRIX",
    "build_contact_support_labels",
    "case_balanced_binary_cross_entropy",
    "stable_knn_indices",
    "validate_scqr_config",
]
