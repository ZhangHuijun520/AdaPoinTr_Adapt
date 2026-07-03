"""Voxel and voxel-surface metrics for SkullFix NRRD evaluation."""

from typing import Iterable

import numpy as np
from scipy import ndimage

from utils.skullfix_metrics import point_rim_metrics, point_surface_metrics


def volume_dice(prediction, reference):
    prediction = np.asarray(prediction, dtype=bool)
    reference = np.asarray(reference, dtype=bool)
    if prediction.shape != reference.shape:
        raise ValueError("Dice masks must have matching shapes")
    denominator = np.count_nonzero(prediction) + np.count_nonzero(reference)
    if denominator == 0:
        return 1.0
    intersection = np.count_nonzero(prediction & reference)
    return float(2.0 * intersection / denominator)


def relative_volume_error(prediction, reference):
    pred_count = np.count_nonzero(prediction)
    ref_count = np.count_nonzero(reference)
    if ref_count == 0:
        return 0.0 if pred_count == 0 else float("inf")
    return float((pred_count - ref_count) / ref_count)


def binary_surface(mask):
    mask = np.asarray(mask, dtype=bool)
    structure = ndimage.generate_binary_structure(3, 1)
    return mask & ~ndimage.binary_erosion(
        mask,
        structure=structure,
        border_value=0,
    )


def indices_to_world(indices, directions, origin):
    indices = np.asarray(indices, dtype=np.float64)
    directions = np.asarray(directions, dtype=np.float64)
    origin = np.asarray(origin, dtype=np.float64)
    return origin + indices @ directions


def surface_world_points(mask, directions, origin):
    indices = np.argwhere(binary_surface(mask))
    if indices.size == 0:
        raise ValueError("Mask has no occupied surface voxels")
    return indices_to_world(indices, directions, origin)


def _splat_offsets(radius_mm, spacings):
    radius_mm = float(radius_mm)
    spacings = np.asarray(spacings, dtype=np.float64)
    limits = np.ceil(radius_mm / spacings).astype(int)
    grid = np.stack(
        np.meshgrid(
            *[
                np.arange(-limit, limit + 1, dtype=np.int64)
                for limit in limits
            ],
            indexing="ij",
        ),
        axis=-1,
    ).reshape(-1, 3)
    distances = np.linalg.norm(grid * spacings, axis=1)
    return grid[distances <= radius_mm + 1e-9]


def splat_world_points_to_mask(
    points_world,
    shape,
    directions,
    origin,
    radius_mm=1.0,
):
    """Rasterize points into a fixed-radius physical-space voxel band."""

    points = np.asarray(points_world, dtype=np.float64)
    directions = np.asarray(directions, dtype=np.float64)
    origin = np.asarray(origin, dtype=np.float64)
    shape = tuple(int(value) for value in shape)
    if directions.shape != (3, 3) or np.linalg.matrix_rank(directions) < 3:
        raise ValueError("space directions must be an invertible 3x3 matrix")
    if radius_mm < 0:
        raise ValueError("radius_mm must be non-negative")

    continuous_indices = (points - origin) @ np.linalg.inv(directions)
    centers = np.rint(continuous_indices).astype(np.int64)
    spacings = np.linalg.norm(directions, axis=1)
    offsets = _splat_offsets(radius_mm, spacings)
    mask = np.zeros(shape, dtype=bool)

    for offset in offsets:
        indices = centers + offset
        valid = np.ones(indices.shape[0], dtype=bool)
        for axis, size in enumerate(shape):
            valid &= (indices[:, axis] >= 0) & (indices[:, axis] < size)
        indices = indices[valid]
        if indices.size:
            mask[tuple(indices.T)] = True
    return mask


def voxel_surface_metrics(
    prediction,
    reference,
    directions,
    origin,
    tolerances_mm: Iterable[float] = (0.5, 1.0, 2.0),
):
    prediction_surface = surface_world_points(
        prediction, directions, origin
    )
    reference_surface = surface_world_points(
        reference, directions, origin
    )
    return point_surface_metrics(
        prediction_surface,
        reference_surface,
        tolerances_mm=tolerances_mm,
    )


def mask_metric_dict(
    prediction,
    reference,
    directions,
    origin,
    tolerances_mm=(0.5, 1.0, 2.0),
):
    surface = voxel_surface_metrics(
        prediction,
        reference,
        directions,
        origin,
        tolerances_mm=tolerances_mm,
    )
    values = {
        "dsc": volume_dice(prediction, reference),
        "rve": relative_volume_error(prediction, reference),
        "absolute_rve": abs(relative_volume_error(prediction, reference)),
        "surface_assd_mm": surface.assd_mm,
        "surface_hd95_mm": surface.hd95_mm,
    }
    values.update(
        {
            f"surface_dice_at_{tolerance:g}mm": value
            for tolerance, value in surface.nsd.items()
        }
    )
    return values


def voxel_rim_metric_dict(
    prediction_implant,
    reference_implant,
    defective,
    directions,
    origin,
    rim_band_mm=2.0,
    tolerances_mm=(0.5, 1.0, 2.0),
):
    metrics = point_rim_metrics(
        surface_world_points(prediction_implant, directions, origin),
        surface_world_points(reference_implant, directions, origin),
        surface_world_points(defective, directions, origin),
        rim_band_mm=rim_band_mm,
        tolerances_mm=tolerances_mm,
    )
    return metrics.as_dict()
