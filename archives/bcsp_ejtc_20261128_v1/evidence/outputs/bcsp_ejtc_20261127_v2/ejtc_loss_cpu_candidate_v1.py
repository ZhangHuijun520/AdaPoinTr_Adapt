"""Isolated candidate for the frozen Fold D directional Chamfer contract."""

import torch


def dense_loss_and_target_distances(chamfer, dense_loss, prediction, target):
    """Return the original dense scalar and its differentiable G-to-P vector."""
    if chamfer.chamfer is not None:
        raise ValueError("frozen cdist backend required")
    if type(dense_loss) is not chamfer.ChamferDistanceL1Directional:
        raise TypeError("frozen directional dense loss required")
    if (dense_loss.pred_to_ref_weight, dense_loss.ref_to_pred_weight) != (1.0, 1.0):
        raise ValueError("frozen dense direction weights required")
    pred_sq, target_sq = chamfer._torch_chamfer_forward(prediction, target)
    pred_distance = torch.sqrt(pred_sq)
    target_distance = torch.sqrt(target_sq)
    wp, wg = dense_loss.pred_to_ref_weight, dense_loss.ref_to_pred_weight
    dense = (wp * pred_distance.mean() + wg * target_distance.mean()) / (wp + wg)
    return dense, target_distance


def tail_indices(distance):
    if distance.ndim != 1 or not distance.numel():
        raise ValueError("tail requires a nonempty vector")
    k = (distance.numel() + 9) // 10
    return torch.argsort(distance.detach(), descending=True, stable=True)[:k]


def tail_mean(distance):
    return distance[tail_indices(distance)].mean()


def auxiliary(distance, arm, labels=None):
    if distance.ndim != 2 or not distance.shape[0] or not torch.isfinite(distance).all():
        raise ValueError("invalid distance batch")
    if arm == "T" and labels is None:
        return torch.stack([tail_mean(d) for d in distance]).mean()
    if arm != "J" or labels is None or labels.shape != distance.shape or labels.dtype != torch.bool:
        raise ValueError("invalid arm or label identity")
    terms = []
    for d, is_j in zip(distance, labels):
        e, j = d[~is_j], d[is_j]
        if min(e.numel(), j.numel()) < 32:
            raise ValueError("insufficient region samples")
        terms.append(0.5 * (tail_mean(e) + tail_mean(j)))
    return torch.stack(terms).mean()
