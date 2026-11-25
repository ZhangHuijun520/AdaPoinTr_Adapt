"""One B/A zero-update confirmation, called by the bound P2 launcher."""

from contextlib import ExitStack
import hashlib
import random

import numpy as np
import torch
from torch import nn

from bcsp_oasg_entry_v1 import HISTORICAL_B_STATE, TRAIN_SEED


ARMS = ("B", "A")
LIMITS = dict(forward=2, loss=2, backward=2, optimizer_step=0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rng(device):
    return (random.getstate(), np.random.get_state(), torch.get_rng_state(),
            torch.cuda.get_rng_state(device) if device.type == "cuda" else None)


def rng_digest(state):
    py, numpy, cpu, cuda = state
    digest = hashlib.sha256(repr((py, numpy[0], numpy[2:])).encode())
    for t in (numpy[1], cpu, cuda):
        if t is not None:
            digest.update(t.numpy().tobytes() if isinstance(t, torch.Tensor) else t.tobytes())
    return digest.hexdigest()


def restore_rng(state, device):
    py, numpy, cpu, cuda = state
    random.setstate(py)
    np.random.set_state(numpy)
    torch.set_rng_state(cpu)
    if cuda is not None:
        torch.cuda.set_rng_state(cuda, device)


def state_digest(state):
    digest = hashlib.sha256()
    for name, value in sorted(state.items()):
        digest.update(repr((name, value.shape, value.dtype)).encode())
        digest.update(value.contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def capture_coordinates(model, arm, hooks):
    trace = {}

    def save(name, value):
        require(name not in trace, "duplicate coordinate consumer: " + name)
        trace[name] = value.detach()

    def capture_head(_, args, result):
        save("anchors", args[2])
        save("delta", result[1])
        save("generated", result[0])

    def capture_decoder(_, args, kwargs):
        save("decoder", kwargs["q_pos"])
        save("decoder_anchors", kwargs["v_pos"])

    base = model.base_model
    if arm == "A":
        hooks.callback(base.coarse_pred.register_forward_hook(capture_head).remove)
    hooks.callback(base.mlp_query.register_forward_pre_hook(
        lambda _, args: save("embedding", args[0][..., -3:])).remove)
    hooks.callback(base.decoder.register_forward_pre_hook(capture_decoder, with_kwargs=True).remove)
    hooks.callback(model.reduce_map.register_forward_pre_hook(
        lambda _, args: save("rebuild", args[0][..., -3:])).remove)
    hooks.callback(model.decode_head.register_forward_hook(
        lambda _, args, output: save("relative", output)).remove)
    return trace


def check_coordinates(trace, arm, coarse, dense):
    for key in ("embedding", "decoder", "rebuild"):
        require(torch.equal(trace[key], coarse), "coarse consumer mismatch: " + key)
    require(trace["relative"].shape == (8, 256, 32, 3)
            and torch.equal(dense.reshape(8, 256, 32, 3), coarse.unsqueeze(2) + trace["relative"]),
            "FC parent and child coordinates")
    if arm == "A":
        require(torch.equal(trace["anchors"], trace["decoder_anchors"])
                and torch.equal(trace["generated"], coarse)
                and torch.equal(trace["anchors"] + trace["delta"], coarse), "A anchor plus displacement")


def gradients(model):
    groups = {
        "coarse_head": model.base_model.coarse_pred,
        "shared_encoder": model.base_model.encoder,
        "dense_head": model.decode_head,
    }
    result = {}
    for name, module in groups.items():
        grad = {n: p.grad for n, p in module.named_parameters() if p.requires_grad}
        result[name] = {n: float(v.detach().norm(dtype=torch.float64)) for n, v in grad.items() if v is not None}
        require(grad and result[name] and all(np.isfinite(list(result[name].values())))
                and any(v > 0 for v in result[name].values()), "finite nonzero gradients: " + name)
        if name == "coarse_head":
            require(len(grad) == len(result[name]), "missing coarse head gradient")
    return result


def run_arm(model, arm, x, y, device, counts, emit, sample, peak_limit):
    params = dict(model.named_parameters())
    buffers = dict(model.named_buffers())
    state = {n: t.detach().cpu().clone() for n, t in {**params, **buffers}.items()}
    saved_grad = {n: None if p.grad is None else p.grad.detach().cpu().clone() for n, p in params.items()}
    modes = [(m, m.training) for m in model.modules()]
    bn = [(m, m.momentum) for m, _ in modes if isinstance(m, nn.modules.batchnorm._BatchNorm)]
    saved_rng = rng(device)
    digest = state_digest(state)
    rng_before = rng_digest(saved_rng)

    def claim(key):
        require(counts[key] < LIMITS[key], "P2 count exceeded: " + key)
        counts[key] += 1
        emit(dict(kind="call", arm=arm, operation=key, counts=dict(counts)))

    def peak():
        if device.type == "cpu":
            return None
        torch.cuda.synchronize(device)
        value = dict(allocated=torch.cuda.max_memory_allocated(device), reserved=torch.cuda.max_memory_reserved(device))
        require(max(value.values()) <= peak_limit, f"P2 peak memory budget: {value}")
        return value

    try:
        model.train()
        model.zero_grad(set_to_none=True)
        for module, _ in bn:
            require(module.track_running_stats, "ordinary training BN tracking required")
            module.momentum = .9
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        sample(arm, "before_forward")
        with ExitStack() as hooks, torch.enable_grad():
            trace = capture_coordinates(model, arm, hooks)
            claim("forward")
            outputs = model(x)
            require(len(outputs) == 4 and outputs[1].numel() == outputs[2].numel() == 0, "original B/A training return")
            coarse, dense = outputs[0], outputs[3]
            require(coarse.shape == (8, 256, 3) and dense.shape == (8, 8192, 3)
                    and all(t.dtype == torch.float32 and bool(torch.isfinite(t).all()) for t in (coarse, dense)),
                    "P2 finite FP32 output shapes")
            check_coordinates(trace, arm, coarse.detach(), dense.detach())
            claim("loss")
            denoise, reconstruction = model.get_loss(outputs, y, epoch=0, partial=x)
            loss = denoise + reconstruction
            require(loss.ndim == 0 and loss.requires_grad and torch.isfinite(loss).item()
                    and float(denoise.detach()) == 0., "original reconstruction-only loss")
            peak()
            sample(arm, "before_backward")
            claim("backward")
            loss.backward()
        memory = peak()
        grad = gradients(model)
        changed_buffers = [n for n, v in buffers.items() if not torch.equal(v.detach().cpu(), state[n])]
        require(all(torch.equal(v.detach().cpu(), state[n]) for n, v in params.items()), "parameter changed")
        require(all(n.endswith(("running_mean", "running_var", "num_batches_tracked")) for n in changed_buffers),
                "unexpected buffer change")
        sample(arm, "after_backward")
        emit(dict(kind="arm_result", arm=arm, loss=float(loss.detach()), coarse=list(coarse.shape),
                  dense=list(dense.shape), coordinates_valid=True, gradients=grad,
                  changed_bn_buffers=changed_buffers, peak_bytes=memory))
    finally:
        with torch.no_grad():
            for name, tensor in {**params, **buffers}.items():
                tensor.copy_(state[name])
            for n, p in params.items():
                p.grad = None if saved_grad[n] is None else saved_grad[n].to(p.device)
        for m, mode in modes:
            m.training = mode
        for m, momentum in bn:
            m.momentum = momentum
        restore_rng(saved_rng, device)
        after = state_digest({n: t.detach().cpu() for n, t in {**params, **buffers}.items()})
        rng_after = rng_digest(rng(device))
        restored = dict(state=after == digest, rng=rng_after == rng_before,
                        modes=all(m.training == mode for m, mode in modes),
                        bn=all(m.momentum == momentum for m, momentum in bn),
                        gradients=all(p.grad is None if saved_grad[n] is None else
                                      p.grad is not None and torch.equal(p.grad.detach().cpu(), saved_grad[n])
                                      for n, p in params.items()))
        emit(dict(kind="restoration", arm=arm, checks=restored, state_before=digest, state_after=after,
                  rng_before=rng_before, rng_after=rng_after))
        require(all(restored.values()), "P2 arm restoration failure")


def _run(batch, construct, device, emit, sample, peak_limit, initializer_sha=None):
    counts = dict.fromkeys(LIMITS, 0)
    initial_rng = rng(device)
    try:
        require(len(batch) == 2 and all(t.shape == (8, 8192, 3) and t.dtype == torch.float32
                                        and bool(torch.isfinite(t).all()) for t in batch), "P2 shared first batch")
        baseline = None
        for arm in ARMS:
            run = dict(variant=arm, fold="D", seed=TRAIN_SEED)
            model, evidence = construct(run)
            require(evidence["run_identity"] == run, "P2 arm identity")
            if device.type == "cuda":
                require(not evidence["artificial_fixture"]
                        and evidence["historical_B_initial_state_SHA256"] == HISTORICAL_B_STATE,
                        "P2 frozen native B construction")
                require(evidence["initializer_sha256"] == (initializer_sha if arm == "A" else None),
                        "P2 frozen A initializer")
            shared = evidence["shared_initial_state_SHA256"]
            if arm == "B":
                baseline = shared
            require(baseline == shared, "P2 B/A common initialization")
            emit(dict(kind="construction", arm=arm, evidence=evidence))
            model.to(device)
            run_arm(model, arm, *(t.detach().to(device, copy=True) for t in batch), device,
                    counts, emit, sample, peak_limit)
            del model
        require(counts == LIMITS, "P2 incomplete call counts")
        return counts
    except Exception as error:
        emit(dict(kind="failure", error=repr(error), counts=dict(counts)))
        raise
    finally:
        restore_rng(initial_rng, device)
        expected, actual = rng_digest(initial_rng), rng_digest(rng(device))
        emit(dict(kind="session_restoration", rng_before=expected, rng_after=actual, counts=dict(counts)))
        require(expected == actual, "P2 session RNG restoration")


def run_cuda(*, ordered_case_ids, load_batch, construct, initializer_sha, emit, sample, peak_limit):
    """Execute only after the separate launcher verifies the request and its asset bindings."""
    require(len(ordered_case_ids) == len(set(ordered_case_ids)) == 8, "P2 first batch identity")
    require(type(peak_limit) is int and peak_limit > 0 and len(initializer_sha) == 64, "P2 bound limits")
    require(torch.cuda.is_available() and torch.cuda.device_count() == 1, "P2 single native CUDA device")
    require(not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32
            and not torch.is_autocast_enabled(), "P2 FP32 without TF32 or AMP")
    actual_ids, partial, target = load_batch()
    require(list(actual_ids) == list(ordered_case_ids), "P2 batch order differs from request")
    return _run((partial, target), construct, torch.device("cuda:0"), emit, sample, peak_limit, initializer_sha)
