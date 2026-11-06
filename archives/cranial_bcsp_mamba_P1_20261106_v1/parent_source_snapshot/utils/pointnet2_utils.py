"""PointNet++ utility adapter.

Use the compiled pointnet2_ops package when it is available. Fall back to a
small pure PyTorch implementation for local toy smoke tests.
"""

import torch

try:
    from pointnet2_ops import pointnet2_utils as _official_pointnet2_utils
except ImportError:
    _official_pointnet2_utils = None


def using_fallback():
    return _official_pointnet2_utils is None


if _official_pointnet2_utils is not None:
    furthest_point_sample = _official_pointnet2_utils.furthest_point_sample
    gather_operation = _official_pointnet2_utils.gather_operation
    grouping_operation = _official_pointnet2_utils.grouping_operation
    three_nn = _official_pointnet2_utils.three_nn
    three_interpolate = _official_pointnet2_utils.three_interpolate
    ball_query = _official_pointnet2_utils.ball_query
else:

    def _square_distance(src, dst):
        dist = -2 * torch.matmul(src, dst.transpose(1, 2))
        dist = dist + torch.sum(src ** 2, dim=-1).unsqueeze(-1)
        dist = dist + torch.sum(dst ** 2, dim=-1).unsqueeze(1)
        return dist.clamp_min_(0)


    def furthest_point_sample(xyz, npoint):
        if xyz.dim() != 3 or xyz.size(-1) != 3:
            raise ValueError(f"expected xyz with shape [B, N, 3], got {tuple(xyz.shape)}")
        batch_size, num_points, _ = xyz.shape
        if npoint > num_points:
            raise ValueError(f"npoint={npoint} cannot exceed num_points={num_points}")

        device = xyz.device
        centroids = torch.zeros(batch_size, npoint, dtype=torch.long, device=device)
        distance = torch.full((batch_size, num_points), 1e10, device=device)
        farthest = torch.zeros(batch_size, dtype=torch.long, device=device)
        batch_indices = torch.arange(batch_size, dtype=torch.long, device=device)

        for i in range(npoint):
            centroids[:, i] = farthest
            centroid = xyz[batch_indices, farthest].view(batch_size, 1, 3)
            dist = torch.sum((xyz - centroid) ** 2, dim=-1)
            distance = torch.minimum(distance, dist)
            farthest = torch.max(distance, dim=-1)[1]
        return centroids


    def gather_operation(features, idx):
        idx = idx.long()
        if features.dim() != 3 or idx.dim() != 2:
            raise ValueError(
                f"expected features [B, C, N] and idx [B, S], got {tuple(features.shape)} and {tuple(idx.shape)}"
            )
        idx_expand = idx.unsqueeze(1).expand(-1, features.size(1), -1)
        return torch.gather(features, 2, idx_expand)


    def grouping_operation(features, idx):
        idx = idx.long()
        if features.dim() != 3 or idx.dim() != 3:
            raise ValueError(
                f"expected features [B, C, N] and idx [B, S, K], got {tuple(features.shape)} and {tuple(idx.shape)}"
            )
        b, c, n = features.shape
        _, s, k = idx.shape
        features_expand = features.unsqueeze(2).expand(b, c, s, n)
        idx_expand = idx.unsqueeze(1).expand(b, c, s, k)
        return torch.gather(features_expand, 3, idx_expand)


    def three_nn(unknown, known):
        if known.size(1) == 0:
            raise ValueError("known must contain at least one point")
        k = min(3, known.size(1))
        dist, idx = torch.topk(torch.cdist(unknown, known), k=k, dim=-1, largest=False, sorted=True)
        if k < 3:
            pad_dist = dist[..., -1:].expand(-1, -1, 3 - k)
            pad_idx = idx[..., -1:].expand(-1, -1, 3 - k)
            dist = torch.cat([dist, pad_dist], dim=-1)
            idx = torch.cat([idx, pad_idx], dim=-1)
        return dist, idx.long()


    def three_interpolate(features, idx, weight):
        grouped = grouping_operation(features, idx)
        return torch.sum(grouped * weight.unsqueeze(1), dim=-1)


    def ball_query(radius, nsample, xyz, new_xyz):
        del radius
        sqrdists = _square_distance(new_xyz, xyz)
        _, idx = torch.topk(sqrdists, k=min(nsample, xyz.size(1)), dim=-1, largest=False, sorted=False)
        if idx.size(-1) < nsample:
            pad = idx[..., -1:].expand(-1, -1, nsample - idx.size(-1))
            idx = torch.cat([idx, pad], dim=-1)
        return idx.long()
