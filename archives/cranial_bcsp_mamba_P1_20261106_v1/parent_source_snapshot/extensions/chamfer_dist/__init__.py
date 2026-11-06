# -*- coding: utf-8 -*-
# @Author: Thibault GROUEIX
# @Date:   2019-08-07 20:54:24
# @Last Modified by:   Haozhe Xie
# @Last Modified time: 2019-12-18 15:06:25
# @Email:  cshzxie@gmail.com

import torch

try:
    import chamfer
except ImportError:
    chamfer = None


def _torch_chamfer_forward(xyz1, xyz2):
    dist = torch.cdist(xyz1, xyz2, p=2) ** 2
    dist1 = dist.min(dim=2)[0]
    dist2 = dist.min(dim=1)[0]
    return dist1, dist2


class ChamferFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, xyz1, xyz2):
        if chamfer is None:
            raise RuntimeError("compiled chamfer extension is not available")
        dist1, dist2, idx1, idx2 = chamfer.forward(xyz1, xyz2)
        ctx.save_for_backward(xyz1, xyz2, idx1, idx2)

        return dist1, dist2

    @staticmethod
    def backward(ctx, grad_dist1, grad_dist2):
        xyz1, xyz2, idx1, idx2 = ctx.saved_tensors
        grad_xyz1, grad_xyz2 = chamfer.backward(xyz1, xyz2, idx1, idx2, grad_dist1, grad_dist2)
        return grad_xyz1, grad_xyz2


class ChamferDistanceL2(torch.nn.Module):
    f''' Chamder Distance L2
    '''
    def __init__(self, ignore_zeros=False):
        super().__init__()
        self.ignore_zeros = ignore_zeros

    def forward(self, xyz1, xyz2):
        batch_size = xyz1.size(0)
        if batch_size == 1 and self.ignore_zeros:
            non_zeros1 = torch.sum(xyz1, dim=2).ne(0)
            non_zeros2 = torch.sum(xyz2, dim=2).ne(0)
            xyz1 = xyz1[non_zeros1].unsqueeze(dim=0)
            xyz2 = xyz2[non_zeros2].unsqueeze(dim=0)

        if chamfer is None:
            dist1, dist2 = _torch_chamfer_forward(xyz1, xyz2)
        else:
            dist1, dist2 = ChamferFunction.apply(xyz1, xyz2)
        return torch.mean(dist1) + torch.mean(dist2)

class ChamferDistanceL2_split(torch.nn.Module):
    f''' Chamder Distance L2
    '''
    def __init__(self, ignore_zeros=False):
        super().__init__()
        self.ignore_zeros = ignore_zeros

    def forward(self, xyz1, xyz2):
        batch_size = xyz1.size(0)
        if batch_size == 1 and self.ignore_zeros:
            non_zeros1 = torch.sum(xyz1, dim=2).ne(0)
            non_zeros2 = torch.sum(xyz2, dim=2).ne(0)
            xyz1 = xyz1[non_zeros1].unsqueeze(dim=0)
            xyz2 = xyz2[non_zeros2].unsqueeze(dim=0)

        if chamfer is None:
            dist1, dist2 = _torch_chamfer_forward(xyz1, xyz2)
        else:
            dist1, dist2 = ChamferFunction.apply(xyz1, xyz2)
        return torch.mean(dist1), torch.mean(dist2)

class ChamferDistanceL1(torch.nn.Module):
    f''' Chamder Distance L1
    '''
    def __init__(self, ignore_zeros=False):
        super().__init__()
        self.ignore_zeros = ignore_zeros

    def forward(self, xyz1, xyz2):
        batch_size = xyz1.size(0)
        if batch_size == 1 and self.ignore_zeros:
            non_zeros1 = torch.sum(xyz1, dim=2).ne(0)
            non_zeros2 = torch.sum(xyz2, dim=2).ne(0)
            xyz1 = xyz1[non_zeros1].unsqueeze(dim=0)
            xyz2 = xyz2[non_zeros2].unsqueeze(dim=0)

        if chamfer is None:
            dist1, dist2 = _torch_chamfer_forward(xyz1, xyz2)
        else:
            dist1, dist2 = ChamferFunction.apply(xyz1, xyz2)
        # import pdb
        # pdb.set_trace()
        dist1 = torch.sqrt(dist1)
        dist2 = torch.sqrt(dist2)
        return (torch.mean(dist1) + torch.mean(dist2))/2


class ChamferDistanceL1Directional(torch.nn.Module):
    """Weighted L1 Chamfer with explicit prediction and coverage directions."""

    def __init__(self, pred_to_ref_weight=1.0, ref_to_pred_weight=1.0):
        super().__init__()
        self.pred_to_ref_weight = float(pred_to_ref_weight)
        self.ref_to_pred_weight = float(ref_to_pred_weight)
        if self.pred_to_ref_weight < 0 or self.ref_to_pred_weight < 0:
            raise ValueError("Directional Chamfer weights must be non-negative")
        if self.pred_to_ref_weight + self.ref_to_pred_weight == 0:
            raise ValueError("At least one directional Chamfer weight must be positive")

    def forward(self, prediction, reference):
        if chamfer is None:
            pred_to_ref, ref_to_pred = _torch_chamfer_forward(
                prediction,
                reference,
            )
        else:
            pred_to_ref, ref_to_pred = ChamferFunction.apply(
                prediction,
                reference,
            )
        pred_to_ref = torch.sqrt(pred_to_ref).mean()
        ref_to_pred = torch.sqrt(ref_to_pred).mean()
        weight_sum = self.pred_to_ref_weight + self.ref_to_pred_weight
        return (
            self.pred_to_ref_weight * pred_to_ref
            + self.ref_to_pred_weight * ref_to_pred
        ) / weight_sum


class ChamferDistanceL1Stable(torch.nn.Module):
    """L1 Chamfer with a clamped square root for direct point optimization."""

    def __init__(self, squared_distance_epsilon=1e-12):
        super().__init__()
        self.squared_distance_epsilon = float(squared_distance_epsilon)
        if self.squared_distance_epsilon <= 0:
            raise ValueError("squared_distance_epsilon must be positive")

    def forward(self, xyz1, xyz2):
        if chamfer is None:
            dist1, dist2 = _torch_chamfer_forward(xyz1, xyz2)
        else:
            dist1, dist2 = ChamferFunction.apply(xyz1, xyz2)
        dist1 = torch.sqrt(
            torch.clamp(dist1, min=self.squared_distance_epsilon)
        )
        dist2 = torch.sqrt(
            torch.clamp(dist2, min=self.squared_distance_epsilon)
        )
        return (torch.mean(dist1) + torch.mean(dist2)) / 2


class ChamferDistanceL1_PM(torch.nn.Module):
    f''' Chamder Distance L1
    '''
    def __init__(self, ignore_zeros=False):
        super().__init__()
        self.ignore_zeros = ignore_zeros

    def forward(self, xyz1, xyz2):
        batch_size = xyz1.size(0)
        if batch_size == 1 and self.ignore_zeros:
            non_zeros1 = torch.sum(xyz1, dim=2).ne(0)
            non_zeros2 = torch.sum(xyz2, dim=2).ne(0)
            xyz1 = xyz1[non_zeros1].unsqueeze(dim=0)
            xyz2 = xyz2[non_zeros2].unsqueeze(dim=0)

        if chamfer is None:
            dist1, _ = _torch_chamfer_forward(xyz1, xyz2)
        else:
            dist1, _ = ChamferFunction.apply(xyz1, xyz2)
        dist1 = torch.sqrt(dist1)
        return torch.mean(dist1)

