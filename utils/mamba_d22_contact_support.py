"""Pure geometry helpers for D2.2 contact-support replay."""

import numpy as np
from scipy.spatial import cKDTree

from utils.skullfix_metrics import normalized_to_world


DEFAULT_BANDS = (0.5, 1.0, 2.0, 3.0, 4.0, 5.0)
DISTANCE_PERCENTILES = (1, 5, 50, 95)


def band_key(value):
    return f"{float(value):g}mm".replace(".", "p")


def distance_profile(
    stage_normalized,
    partial_world,
    reference_rim_2mm_world,
    centroid,
    scale,
    bands=DEFAULT_BANDS,
):
    """Describe stage support on the defective skull in millimeters."""

    stage_world = normalized_to_world(stage_normalized, centroid, scale)
    partial_world = np.asarray(partial_world, dtype=np.float64)
    reference_rim_2mm_world = np.asarray(
        reference_rim_2mm_world, dtype=np.float64
    )
    if partial_world.ndim != 2 or partial_world.shape[1] != 3:
        raise ValueError("partial_world must have shape (N, 3)")
    if (
        reference_rim_2mm_world.ndim != 2
        or reference_rim_2mm_world.shape[1] != 3
        or reference_rim_2mm_world.shape[0] == 0
    ):
        raise ValueError("reference_rim_2mm_world must be a non-empty (N, 3) array")
    if not np.isfinite(partial_world).all() or not np.isfinite(
        reference_rim_2mm_world
    ).all():
        raise ValueError("Contact-support inputs must be finite")
    bands = tuple(float(value) for value in bands)
    if bands != DEFAULT_BANDS:
        raise ValueError(f"D2.2 contact bands are frozen as {DEFAULT_BANDS}")

    stage_tree = cKDTree(stage_world)
    defective_to_stage = np.asarray(
        stage_tree.query(partial_world, k=1)[0], dtype=np.float64
    )
    rim_to_stage = np.asarray(
        stage_tree.query(reference_rim_2mm_world, k=1)[0], dtype=np.float64
    )
    output = {
        "point_count": int(stage_world.shape[0]),
        "defective_to_stage_min_mm": float(defective_to_stage.min()),
        "defective_to_stage_max_mm": float(defective_to_stage.max()),
        "gt_rim2_to_stage_min_mm": float(rim_to_stage.min()),
        "gt_rim2_to_stage_mean_mm": float(rim_to_stage.mean()),
        "gt_rim2_to_stage_max_mm": float(rim_to_stage.max()),
    }
    for percentile in DISTANCE_PERCENTILES:
        output[f"defective_to_stage_p{percentile}_mm"] = float(
            np.percentile(defective_to_stage, percentile)
        )
        output[f"gt_rim2_to_stage_p{percentile}_mm"] = float(
            np.percentile(rim_to_stage, percentile)
        )
    recovery = None
    for band in bands:
        count = int(np.count_nonzero(defective_to_stage <= band))
        key = band_key(band)
        output[f"predicted_rim_points_at_{key}"] = count
        output[f"contact_exists_at_{key}"] = int(count > 0)
        if recovery is None and count > 0:
            recovery = band
    output["recovery_band_mm"] = "" if recovery is None else float(recovery)
    output["zero_contact_margin_at_2mm"] = float(
        defective_to_stage.min() - 2.0
    )
    return output
