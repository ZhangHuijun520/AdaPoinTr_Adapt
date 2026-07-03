"""Physical-space point-surface metrics for SkullFix evaluation."""

from dataclasses import dataclass
from typing import Dict, Iterable

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class PointSurfaceMetrics:
    """Symmetric nearest-neighbor metrics evaluated in millimeters."""

    cd_l1_mm: float
    assd_mm: float
    hd95_mm: float
    nsd: Dict[float, float]
    pred_to_ref_mean_mm: float
    ref_to_pred_mean_mm: float

    def as_dict(self):
        values = {
            "cd_l1_mm": self.cd_l1_mm,
            "assd_mm": self.assd_mm,
            "hd95_mm": self.hd95_mm,
            "pred_to_ref_mean_mm": self.pred_to_ref_mean_mm,
            "ref_to_pred_mean_mm": self.ref_to_pred_mean_mm,
        }
        values.update(
            {f"nsd_at_{tolerance:g}mm": value for tolerance, value in self.nsd.items()}
        )
        return values


@dataclass(frozen=True)
class PointRimMetrics:
    """Contact-rim agreement measured on the defective skull surface."""

    reference_rim_points: int
    predicted_rim_points: int
    contact_cd_l1_mm: float
    contact_hd95_mm: float
    contact_nsd: Dict[float, float]
    gt_rim_to_pred_mean_mm: float
    gt_rim_to_pred_p95_mm: float

    def as_dict(self):
        values = {
            "reference_rim_points": self.reference_rim_points,
            "predicted_rim_points": self.predicted_rim_points,
            "contact_cd_l1_mm": self.contact_cd_l1_mm,
            "contact_hd95_mm": self.contact_hd95_mm,
            "gt_rim_to_pred_mean_mm": self.gt_rim_to_pred_mean_mm,
            "gt_rim_to_pred_p95_mm": self.gt_rim_to_pred_p95_mm,
        }
        values.update(
            {
                f"contact_nsd_at_{tolerance:g}mm": value
                for tolerance, value in self.contact_nsd.items()
            }
        )
        return values


def _points_array(points, name):
    array = np.asarray(points, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError(f"{name} must have shape (N, 3), got {array.shape}")
    if array.shape[0] == 0:
        raise ValueError(f"{name} must contain at least one point")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains NaN or Inf")
    return array


def _normalization(centroid, scale):
    centroid = np.asarray(centroid, dtype=np.float64)
    scale = float(np.asarray(scale, dtype=np.float64))
    if centroid.shape != (3,) or not np.isfinite(centroid).all():
        raise ValueError(f"centroid must contain three finite values, got {centroid}")
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError(f"scale must be a positive finite scalar, got {scale}")
    return centroid, scale


def normalized_to_world(points, centroid, scale):
    """Restore normalized point coordinates to the NRRD world frame in mm."""

    points = _points_array(points, "points")
    centroid, scale = _normalization(centroid, scale)
    return points * scale + centroid


def world_to_normalized(points, centroid, scale):
    """Map NRRD world coordinates in mm to the stored SkullFix normalization."""

    points = _points_array(points, "points")
    centroid, scale = _normalization(centroid, scale)
    return (points - centroid) / scale


def directed_nearest_neighbor_distances(source, target):
    """Return Euclidean distance from every source point to its nearest target."""

    source = _points_array(source, "source")
    target = _points_array(target, "target")
    distances, _ = cKDTree(target).query(source, k=1)
    return np.asarray(distances, dtype=np.float64)


def point_surface_metrics(
    prediction_world,
    reference_world,
    tolerances_mm: Iterable[float] = (0.5, 1.0, 2.0),
):
    """Compute point-sampled surface metrics in physical millimeter coordinates.

    CD-L1 gives equal weight to the two directed means. ASSD weights every sampled
    point equally across both directions. They are identical when both point sets
    contain the same number of area-uniform samples.
    """

    prediction = _points_array(prediction_world, "prediction_world")
    reference = _points_array(reference_world, "reference_world")
    tolerances = tuple(float(value) for value in tolerances_mm)
    if not tolerances:
        raise ValueError("At least one NSD tolerance is required")
    if any(not np.isfinite(value) or value < 0 for value in tolerances):
        raise ValueError("NSD tolerances must be finite and non-negative")

    pred_to_ref = directed_nearest_neighbor_distances(prediction, reference)
    ref_to_pred = directed_nearest_neighbor_distances(reference, prediction)
    pred_mean = float(pred_to_ref.mean())
    ref_mean = float(ref_to_pred.mean())
    combined = np.concatenate((pred_to_ref, ref_to_pred))

    cd_l1 = 0.5 * (pred_mean + ref_mean)
    assd = float(combined.mean())
    hd95 = float(np.percentile(combined, 95))
    epsilon = np.finfo(np.float64).eps * 32
    nsd = {
        tolerance: float(
            (
                np.count_nonzero(pred_to_ref <= tolerance + epsilon)
                + np.count_nonzero(ref_to_pred <= tolerance + epsilon)
            )
            / combined.size
        )
        for tolerance in tolerances
    }

    return PointSurfaceMetrics(
        cd_l1_mm=cd_l1,
        assd_mm=assd,
        hd95_mm=hd95,
        nsd=nsd,
        pred_to_ref_mean_mm=pred_mean,
        ref_to_pred_mean_mm=ref_mean,
    )


def normalized_point_surface_metrics(
    prediction_normalized,
    reference_normalized,
    centroid,
    scale,
    tolerances_mm: Iterable[float] = (0.5, 1.0, 2.0),
):
    """Restore a SkullFix pair to world coordinates and evaluate it in mm."""

    prediction_world = normalized_to_world(
        prediction_normalized, centroid=centroid, scale=scale
    )
    reference_world = normalized_to_world(
        reference_normalized, centroid=centroid, scale=scale
    )
    return point_surface_metrics(
        prediction_world,
        reference_world,
        tolerances_mm=tolerances_mm,
    )


def point_rim_metrics(
    prediction_implant_world,
    reference_implant_world,
    defective_world,
    rim_band_mm=2.0,
    tolerances_mm: Iterable[float] = (0.5, 1.0, 2.0),
):
    """Compare predicted and reference contact footprints on the defective skull.

    A rim point is a defective-skull surface sample lying within ``rim_band_mm``
    of the corresponding implant surface. This is a point-sampled contact-rim
    metric, not a contour extracted from a voxel segmentation.
    """

    prediction = _points_array(
        prediction_implant_world, "prediction_implant_world"
    )
    reference = _points_array(
        reference_implant_world, "reference_implant_world"
    )
    defective = _points_array(defective_world, "defective_world")
    rim_band_mm = float(rim_band_mm)
    if not np.isfinite(rim_band_mm) or rim_band_mm <= 0:
        raise ValueError("rim_band_mm must be positive and finite")

    defective_to_reference = directed_nearest_neighbor_distances(
        defective, reference
    )
    defective_to_prediction = directed_nearest_neighbor_distances(
        defective, prediction
    )
    reference_rim = defective[defective_to_reference <= rim_band_mm]
    predicted_rim = defective[defective_to_prediction <= rim_band_mm]
    gt_rim_to_prediction = (
        directed_nearest_neighbor_distances(reference_rim, prediction)
        if reference_rim.size
        else np.asarray([], dtype=np.float64)
    )

    if reference_rim.size and predicted_rim.size:
        contact = point_surface_metrics(
            predicted_rim,
            reference_rim,
            tolerances_mm=tolerances_mm,
        )
        contact_cd = contact.cd_l1_mm
        contact_hd95 = contact.hd95_mm
        contact_nsd = contact.nsd
    else:
        contact_cd = float("nan")
        contact_hd95 = float("nan")
        contact_nsd = {
            float(tolerance): float("nan") for tolerance in tolerances_mm
        }

    return PointRimMetrics(
        reference_rim_points=int(reference_rim.shape[0]),
        predicted_rim_points=int(predicted_rim.shape[0]),
        contact_cd_l1_mm=contact_cd,
        contact_hd95_mm=contact_hd95,
        contact_nsd=contact_nsd,
        gt_rim_to_pred_mean_mm=(
            float(gt_rim_to_prediction.mean())
            if gt_rim_to_prediction.size
            else float("nan")
        ),
        gt_rim_to_pred_p95_mm=(
            float(np.percentile(gt_rim_to_prediction, 95))
            if gt_rim_to_prediction.size
            else float("nan")
        ),
    )


def normalized_point_rim_metrics(
    prediction_implant_normalized,
    reference_implant_normalized,
    defective_normalized,
    centroid,
    scale,
    rim_band_mm=2.0,
    tolerances_mm: Iterable[float] = (0.5, 1.0, 2.0),
):
    return point_rim_metrics(
        normalized_to_world(
            prediction_implant_normalized, centroid=centroid, scale=scale
        ),
        normalized_to_world(
            reference_implant_normalized, centroid=centroid, scale=scale
        ),
        normalized_to_world(
            defective_normalized, centroid=centroid, scale=scale
        ),
        rim_band_mm=rim_band_mm,
        tolerances_mm=tolerances_mm,
    )
