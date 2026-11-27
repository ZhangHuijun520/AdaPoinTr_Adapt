"""Local substitution for the selected OASG encoder mixer order."""
from contextlib import contextmanager
import hashlib
import json
from types import MethodType


def need(ok, msg):
    if not ok:
        raise ValueError(msg)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def content_key(x, frame, positions, native, geometry, version):
    envelope = dict(input=sha(x.tobytes()), dtype=x.dtype.str, shape=list(x.shape), frame=frame,
                    axes="SkullBreak LPS mm", geometry=geometry,
                    anchors=sha(positions.tobytes()), anchor_dtype=positions.dtype.str,
                    anchor_shape=list(positions.shape), native=sha(native.astype("<i8").tobytes()), version=version)
    return sha(json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode())


@contextmanager
def temporary_order(target, torch, select):
    """Execute the original bidirectional computation with two replacement indices."""
    old = target.forward
    original_attr = target.__dict__.get("forward")
    native = old.__func__.__globals__
    gather = native["gather_tokens"]
    lex = native["lexicographic_order"]

    def forward(self, x, pos):
        need(x.ndim == 3 and x.shape[:2] == pos.shape[:2] and x.shape[-1] == 384, "target shape")
        order, inverse = lex(pos)
        chosen = select(pos, order, inverse)
        if chosen is None:
            return old(x, pos)
        order, inverse = chosen
        need(x.device == pos.device and x.dtype == torch.float32 and bool(torch.isfinite(x).all()), "target dtype")
        x_sorted = gather(x, order).contiguous()
        fwd = self.mixer(x_sorted)
        rev = self.mixer(x_sorted.flip(1).contiguous()).flip(1)
        need(fwd.shape == rev.shape == x.shape, "native two scans")
        result = gather((fwd + rev) * 0.5, inverse)
        need(result.dtype == x.dtype and bool(torch.isfinite(result).all()), "selected SSM output")
        return result

    target.forward = MethodType(forward, target)
    try:
        yield
    finally:
        if original_attr is None:
            del target.forward
        else:
            target.forward = original_attr


def schedule(active, fallback, batch):
    need(len(active) == len(set(active)) == 5 and fallback not in active, "timing selection")
    need(len(batch) == len(set(batch)) == 8 and {active[0], fallback} <= set(batch), "training batch")
    arms = ("R", "C", "S")
    rows = []
    def add(phase, arm, cases, kind=None):
        rows.append(dict(index=len(rows) + 1, phase=phase, arm=arm, cases=list(cases), kind=kind))
    for _ in range(2):
        add("native", "R", active[:1])
    for arm in arms:
        add("forced", arm, active[:1])
    for cid in (active[0], fallback):
        for arm in arms:
            add("manipulation", arm, [cid])
    for _ in range(3):
        for arm in arms:
            add("batch8", arm, batch)
    for kind in ("hot", "cold"):
        for cid in active:
            for arm in arms:
                add("warmup", arm, [cid], kind)
        for rep in range(5):
            for cid in active:
                for arm in arms[rep % 3:] + arms[:rep % 3]:
                    add("timed", arm, [cid], kind)
    need(len(rows) == 200, "P1 forward count")
    return rows
