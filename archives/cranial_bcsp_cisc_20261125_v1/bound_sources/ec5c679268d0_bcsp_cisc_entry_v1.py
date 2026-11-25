"""Bind CISC to the first query of a frozen-architecture OASG model."""

import ast
import hashlib
from io import BytesIO
from types import MethodType
from typing import NamedTuple

import numpy as np
import torch

import bcsp_oasg_entry_v1 as oasg
from bcsp_oasg_head_v1 import ObservationAnchoredHead
from bcsp_cisc_head_v1 import AUX_WEIGHT, N_INPUT, CiscObservationHead, auxiliary_loss


class Losses(NamedTuple):
    original: torch.Tensor
    interface: torch.Tensor
    total: torch.Tensor


def verified_labels(raw, partial, *, label_sha256, partial_sha256):
    """Bind the P0b sidecar to the untouched input rows before tensor conversion."""
    if (partial.shape != (N_INPUT, 3) or partial.dtype != np.float32
            or hashlib.sha256(partial.tobytes()).hexdigest() != partial_sha256
            or hashlib.sha256(raw).hexdigest() != label_sha256):
        raise ValueError("CISC label sidecar or ordered partial SHA256")
    with np.load(BytesIO(raw), allow_pickle=False) as bundle:
        if sorted(bundle.files) != ["face_id", "is_j", "row_id"]:
            raise ValueError("unexpected CISC sidecar fields")
        rows, face, labels = (bundle[key] for key in ("row_id", "face_id", "is_j"))
    if (rows.dtype.kind not in "iu" or not np.array_equal(rows, np.arange(N_INPUT))
            or face.shape != (N_INPUT,) or face.dtype.kind not in "iu" or np.any(face < 0)
            or labels.shape != (N_INPUT,) or labels.dtype != np.bool_):
        raise ValueError("invalid CISC sidecar row identity")
    return labels


def _conditional_forward(base):
    original = type(base).forward
    path, tree = oasg._source(original, oasg.MOTHER_SHA256)
    [owner] = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PCTransformer"]
    [node] = [item for item in owner.body if isinstance(item, ast.FunctionDef) and item.name == "forward"]
    oasg.require(node.lineno == original.__code__.co_firstlineno, "CISC original forward entry")
    [coarse_at] = [i for i, item in enumerate(node.body) if oasg._same_statement(
        item, "learned_coarse = self.coarse_pred(global_feature).reshape(bs, -1, 3)")]
    [memory_at] = [i for i, item in enumerate(node.body) if oasg._same_statement(item, "mem = self.mem_link(x)")]
    oasg.require(coarse_at < memory_at, "CISC original Memory order")
    memory = node.body.pop(memory_at)
    old_coarse = node.body[coarse_at]
    call = ast.parse("learned_coarse, _ = self.coarse_pred(global_feature, mem, coor, xyz)").body[0]
    node.body[coarse_at:coarse_at + 1] = [
        ast.copy_location(memory, old_coarse), ast.copy_location(call, old_coarse)]
    return MethodType(oasg._compile(node, path, original.__globals__), base)


def attach(model, arm, *, prior=None, auxiliary_seed=None):
    """Start with an OASG A-architecture model, built with shared frozen initial tensors."""
    if arm not in ("R", "U", "I"):
        raise ValueError("unknown CISC arm")
    base = model.base_model
    head = base.coarse_pred
    if (type(head) is not ObservationAnchoredHead or type(base.mem_link) is not torch.nn.Identity
            or base.query_selection != "learned_only" or base.num_query != 256 or base.use_denoise):
        raise ValueError("expected frozen OASG learned-only architecture")
    if arm == "R":
        if prior is not None or auxiliary_seed is not None:
            raise ValueError("R has no interface head")
        return model
    if prior is None or any(p.device.type != "cpu" for p in head.parameters()):
        raise ValueError("attach CISC to the CPU model with its training Fold prior")
    forward = _conditional_forward(base)
    base.coarse_pred = CiscObservationHead(head, arm, prior, auxiliary_seed).train(head.training)
    base.forward = forward
    return model


def training_losses(model, points, target, epoch, labels=None):
    """Expose the sole CISC supervision route without adding a label argument to the model."""
    head = model.base_model.coarse_pred
    candidate = isinstance(head, CiscObservationHead)
    if (labels is not None) != candidate or not model.training:
        raise ValueError("invalid CISC training mode or missing auxiliary labels")
    if candidate and (labels.dtype != torch.bool or labels.shape != points.shape[:2]
                      or labels.device != points.device):
        raise ValueError("CISC labels must be aligned Boolean input rows")
    captured = []
    if candidate:
        with head.conditioner.register_forward_hook(lambda _m, _a, result: captured.append(result)):
            result = model(points)
        if len(captured) != 1:
            raise RuntimeError("expected one interface condition for one training forward")
    else:
        result = model(points)
    sparse, dense = model.get_loss(result, target, epoch, partial=points)
    original = sparse + dense
    interface = auxiliary_loss(captured[0], labels) if candidate else original.new_zeros(())
    return Losses(original, interface, original + AUX_WEIGHT * interface)
