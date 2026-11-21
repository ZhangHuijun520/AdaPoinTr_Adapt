"""Observe the bound AdaPoinTr FC consumer without replacing the live path."""

import hashlib
import io
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from bcsp_fcsp_head_v1 import CHILDREN, INPUT_POINTS, PARENTS, require_fp32


@dataclass(frozen=True)
class FCCache:
    q: torch.Tensor
    h: torch.Tensor
    p0: torch.Tensor


def load_partial(path, expected_bytes, expected_sha256):
    """Verify the packed NPZ, then decode only the partial member."""
    with Path(path).open("rb") as file:
        blob = file.read(expected_bytes + 1)
    if len(blob) != expected_bytes or hashlib.sha256(blob).hexdigest() != expected_sha256:
        raise ValueError("input NPZ identity mismatch")
    with np.load(io.BytesIO(blob), allow_pickle=False) as packed:
        partial = packed["partial"].copy()
    if partial.dtype != np.float32 or partial.shape != (INPUT_POINTS, 3) or not np.isfinite(partial).all():
        raise ValueError("invalid partial member")
    return partial


def same_fp32_bytes(left, right):
    return (left.dtype == right.dtype == torch.float32
            and left.shape == right.shape and left.device == right.device
            and torch.equal(left.contiguous().view(torch.int32), right.contiguous().view(torch.int32)))


def _snapshot(model):
    state = hashlib.sha256()
    for name, value in sorted((*model.named_parameters(), *model.named_buffers())):
        state.update(repr((name, str(value.dtype), tuple(value.shape))).encode())
        state.update(value.detach().cpu().reshape(-1).contiguous().view(torch.uint8).numpy().tobytes())
    cpu_rng = torch.get_rng_state().numpy().tobytes()
    cuda_rng = (tuple(rng.cpu().numpy().tobytes() for rng in torch.cuda.get_rng_state_all())
                if torch.cuda.is_initialized() else ())
    numpy_rng = np.random.get_state()
    return (state.hexdigest(), tuple((key, layer.training) for key, layer in model.named_modules()),
            cpu_rng, cuda_rng, random.getstate(),
            (numpy_rng[0], numpy_rng[1].tobytes(), *numpy_rng[2:]))


def _check_donor(model, partial):
    if (model.decoder_type, model.num_query, model.factor) != ("fc", PARENTS, CHILDREN):
        raise ValueError("unexpected donor FC geometry")
    if any(layer.training for layer in model.modules()) or any(p.requires_grad for p in model.parameters()):
        raise ValueError("donor must be frozen and fully in eval mode")
    if partial.ndim != 3 or partial.shape[0] == 0:
        raise ValueError("nonempty batched partial input required")
    require_fp32("partial", partial, (partial.shape[0], INPUT_POINTS, 3))


def _read_result(result, batch):
    if not isinstance(result, (tuple, list)) or len(result) != 2:
        raise ValueError("native eval must return Q and flattened P0")
    q, p0 = result
    require_fp32("returned Q", q, (batch, PARENTS, 3))
    require_fp32("returned P0", p0, (batch, PARENTS * CHILDREN, 3))
    return q, p0


class _FCObserver:
    def __init__(self, batch, parent_width):
        self.batch = batch
        self.parent_width = parent_width
        self.seen = []

    def _note(self, event, expected_prefix):
        if tuple(self.seen) != expected_prefix:
            raise ValueError("unexpected FC consumer call order")
        self.seen.append(event)

    def coarse(self, _module, _args, output):
        self._note("coarse", ())
        if not isinstance(output, (tuple, list)) or len(output) != 4 or output[2] != 0:
            raise ValueError("unexpected base-model eval output")
        self.q = output[1].detach().clone()
        require_fp32("base-model Q", self.q, (self.batch, PARENTS, 3))

    def reduced(self, _module, _args, output):
        self._note("reduced", ("coarse",))
        self.reduced_object = output

    def fc_input(self, module, args):
        self._note("fc_input", ("coarse", "reduced"))
        if len(args) != 1 or args[0] is not self.reduced_object:
            raise ValueError("decode_head must consume the actual reduce_map output")
        if module.step != CHILDREN or module.input_dims != 2 * self.parent_width:
            raise ValueError("unexpected child count or internally pooled width in decode_head")
        require_fp32("actual decode_head input", args[0], (self.batch, PARENTS, self.parent_width))
        self.h = args[0].detach().clone()

    def fc_output(self, _module, args, output):
        self._note("fc_output", ("coarse", "reduced", "fc_input"))
        if not same_fp32_bytes(args[0], self.h):
            raise ValueError("decode_head mutated its input")
        require_fp32("FC relative XYZ", output, (self.batch, PARENTS, CHILDREN, 3))
        self.relative = output.detach().clone()


def capture_fc(model, partial):
    """Run once, require the observed offset+Q path, and return grad-safe copies."""
    _check_donor(model, partial)
    observer = _FCObserver(partial.shape[0], model.reduce_map.out_features)
    hooks = []
    try:
        hooks.append(model.base_model.register_forward_hook(observer.coarse))
        hooks.append(model.reduce_map.register_forward_hook(observer.reduced))
        hooks.append(model.decode_head.register_forward_pre_hook(observer.fc_input))
        hooks.append(model.decode_head.register_forward_hook(observer.fc_output))
        with torch.inference_mode():
            q, flat_p = _read_result(model(partial), observer.batch)
            if observer.seen != ["coarse", "reduced", "fc_input", "fc_output"]:
                raise ValueError("incomplete actual FC consumer observation")
            if not same_fp32_bytes(q, observer.q):
                raise ValueError("returned Q does not preserve base-model parent order")
            expected_p = (observer.relative + q.unsqueeze(-2)).reshape_as(flat_p)
            if not same_fp32_bytes(flat_p, expected_p):
                raise ValueError("returned P0 does not preserve FC parent-major layout")
    finally:
        for hook in hooks:
            hook.remove()
    with torch.inference_mode(False), torch.no_grad():
        return FCCache(q.detach().clone(), observer.h.detach().clone(),
                       flat_p.reshape(observer.batch, PARENTS, CHILDREN, 3).detach().clone())


def verify_capture_pair(model, partial):
    """Admission pair only. Compare unobserved/observed bytes and model/RNG state."""
    _check_donor(model, partial)
    before = _snapshot(model)
    try:
        with torch.inference_mode():
            natural = tuple(t.detach().clone() for t in _read_result(model(partial), partial.shape[0]))
        if _snapshot(model) != before:
            raise ValueError("unobserved donor mutated state or RNG")
        captured = capture_fc(model, partial)
        if not (same_fp32_bytes(natural[0], captured.q)
                and same_fp32_bytes(natural[1], captured.p0.flatten(1, 2))):
            raise ValueError("observer changed native output bytes")
        return captured
    finally:
        if _snapshot(model) != before:
            raise ValueError("donor state or RNG changed during admission")
