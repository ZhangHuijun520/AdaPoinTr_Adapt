"""Isolated Fold D B/A construction, lifecycle binding and sampled observations."""

import ast
from contextlib import ExitStack, contextmanager
import hashlib
import json
from pathlib import Path
from types import MethodType

import torch
from torch import nn

from bcsp_oasg_head_v1 import HEAD_PARAMETERS, load_head


TRAIN_SEED = 2026112101
MOTHER_SHA256 = "1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4"
RUNTIME_SHA256 = "09973e15bfebe820f39bed550b809e814a4b14c022b22863946ad25f3c5dd292"
HISTORICAL_B_STATE = "5b1ed06363b06747b464810b52e316468d0b3eaffbe7f2eeab92c42557f72b7b"
COARSE_PREFIX = "base_model.coarse_pred."
OBSERVATION_STEPS = frozenset((1, 39, 390, 1950, 3900))


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def identity(variant, fold, seed):
    require(variant in ("B", "A") and fold == "D" and type(seed) is int and seed == TRAIN_SEED,
            "OASG Fold D B/A identity")
    return dict(variant=variant, fold=fold, seed=seed)


def _source(function, expected_digest):
    path = Path(function.__code__.co_filename)
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_digest, "OASG parent source SHA256")
    return path, ast.parse(raw, filename=str(path))


def _same_statement(node, source):
    return ast.dump(node) == ast.dump(ast.parse(source).body[0])


def _compile(node, path, namespace):
    scope = dict(namespace)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), scope)
    return scope[node.name]


def _oasg_forward(base):
    original = base.forward.__func__
    require(original is type(base).forward, "OASG requires original coarse forward")
    path, tree = _source(original, MOTHER_SHA256)
    [owner] = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PCTransformer"]
    [node] = [item for item in owner.body if isinstance(item, ast.FunctionDef) and item.name == "forward"]
    require(node.lineno == original.__code__.co_firstlineno, "OASG original forward entry")
    [coarse_at] = [i for i, item in enumerate(node.body) if _same_statement(
        item, "learned_coarse = self.coarse_pred(global_feature).reshape(bs, -1, 3)")]
    [memory_at] = [i for i, item in enumerate(node.body) if _same_statement(item, "mem = self.mem_link(x)")]
    require(coarse_at < memory_at, "OASG original Memory order")
    memory = node.body.pop(memory_at)
    old_coarse = node.body[coarse_at]
    coarse = ast.parse("learned_coarse, _ = self.coarse_pred(global_feature, mem, coor)").body[0]
    node.body[coarse_at:coarse_at + 1] = [
        ast.copy_location(memory, old_coarse), ast.copy_location(coarse, old_coarse)]
    return MethodType(_compile(node, path, original.__globals__), base)


def _state(model, tensor_sha, *, shared_only=False):
    return {
        name: dict(shape=list(value.shape), dtype=str(value.dtype), sha256=tensor_sha(value))
        for name, value in model.state_dict().items()
        if not (shared_only and name.startswith(COARSE_PREFIX))
    }


def _digest(records):
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def construct(run, legacy_builder, initialization, *, np, prime, seeded, lqi, scq, artificial_mixer=None):
    identity(**run)
    is_candidate = run["variant"] == "A"
    require((initialization is not None) == is_candidate, "OASG A-only initializer")
    # Both arms start from the exact historical B constructor, without an SCQ residual.
    model, history = prime.construct(prime.identity("B", run["fold"], run["seed"]), legacy_builder, None,
                                     torch=torch, np=np, parent=seeded, lqi=lqi, scq=scq,
                                     artificial_mixer=artificial_mixer)
    historical_b = history["common_initial_state_SHA256"]
    if artificial_mixer is None:
        require(historical_b == HISTORICAL_B_STATE, "frozen historical full B initial state")
    base = model.base_model
    require(type(base.mem_link) is nn.Identity, "OASG token-wise Identity Memory link")
    shared = _state(model, seeded.tensor_sha, shared_only=True)
    old_total = sum(parameter.numel() for parameter in model.parameters())
    if is_candidate:
        initial_rng = torch.random.get_rng_state()
        require(sum(p.numel() for p in base.coarse_pred.parameters()) == 1836800, "original coarse head size")
        forward = _oasg_forward(base)
        base.coarse_pred = load_head(initialization).train(base.training)
        base.forward = forward
        require(torch.equal(initial_rng, torch.random.get_rng_state()), "OASG initializer changed training RNG")
        require(_state(model, seeded.tensor_sha, shared_only=True) == shared, "OASG changed common initial state")
    total = sum(parameter.numel() for parameter in model.parameters())
    require(total == old_total + (HEAD_PARAMETERS - 1836800 if is_candidate else 0), "OASG parameter count")
    return model, dict(run_identity=dict(run), historical_B_initial_state_SHA256=historical_b,
                       shared_initial_state_SHA256=_digest(shared), shared_tensors=len(shared),
                       initializer_sha256=initialization["sha256"] if is_candidate else None,
                       total_parameters=total, artificial_fixture=artificial_mixer is not None)


def bind_training_lifecycle(runtime):
    """Keep the frozen optimizer loop and use the OASG identity at its first guard."""
    original = runtime.train_lifecycle
    path, tree = _source(original, RUNTIME_SHA256)
    [node] = [item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "train_lifecycle"]
    old_guard = node.body[1]
    require(node.lineno == original.__code__.co_firstlineno and _same_statement(old_guard, """
require(set(run_identity) == {'variant', 'fold', 'seed'} and run_identity['variant'] in ('B', 'F', 'S')
        and run_identity['fold'] in ('C', 'D') and type(run_identity['seed']) is int
        and run_identity['seed'] in (2026112101, 2026112102), 'SCQ-PRIME runtime identity')
"""), "OASG original runtime guard")
    node.body[1] = ast.copy_location(ast.parse("_oasg_identity(**run_identity)").body[0], old_guard)
    return _compile(node, path, {**original.__globals__, "_oasg_identity": identity})


class TrainingObservations:
    def __init__(self, resources, emit):
        self.resources = resources
        self.emit = emit
        self.step = None
        self.geometry = None
        self.delta = None
        self.losses = {}

    def before_step(self, completed):
        self.resources.before_step(completed)
        require(self.step is None, "unconsumed OASG observation")
        if completed + 1 in OBSERVATION_STEPS:
            self.step = completed + 1

    def head_output(self, module, args, outputs):
        if self.step is not None:
            self.delta = outputs[1].detach()

    def model_output(self, module, args, outputs):
        if self.step is None:
            return
        require(module.training and self.geometry is None, "one observed training forward")
        with torch.no_grad():
            coarse = outputs[0].detach()
            self.geometry = dict(center=coarse.mean(1).cpu().tolist(), minimum=coarse.amin(1).cpu().tolist(),
                                 maximum=coarse.amax(1).cpu().tolist())
            if self.delta is not None:
                probs = self.delta.new_tensor([0.5, 0.95])
                self.geometry["anchor_displacement_p50_p95"] = torch.quantile(
                    self.delta.norm(dim=-1), probs, dim=1).T.cpu().tolist()

    def loss_output(self, name):
        def capture(module, args, value):
            if self.step is not None:
                require(name not in self.losses, "one observed loss per component")
                self.losses[name] = float(value.detach())
        return capture

    def after_step(self, step):
        if self.step is not None:
            require(self.step == step and self.geometry is not None and set(self.losses) == {"coarse", "dense"},
                    "OASG observation follows original forward and both losses")
            self.emit(dict(step=step, frame="D-only normalized", geometry=self.geometry, losses=dict(self.losses)))
            self.step = self.geometry = self.delta = None
            self.losses.clear()
        self.resources.after_step(step)

    def before_final(self):
        require(self.step is None, "unfinished OASG observation")
        self.resources.before_final()

    def after_final(self):
        self.resources.after_final()


@contextmanager
def observe_training(model, run, resources, emit):
    """Observe selected existing batches through removable hooks, without extra forwards."""
    identity(**run)
    obs = TrainingObservations(resources, emit)
    with ExitStack() as hooks:
        if run["variant"] == "A":
            hooks.callback(model.base_model.coarse_pred.register_forward_hook(obs.head_output).remove)
        hooks.callback(model.register_forward_hook(obs.model_output).remove)
        hooks.callback(model.loss_func.register_forward_hook(obs.loss_output("coarse")).remove)
        hooks.callback(model.fine_loss_func.register_forward_hook(obs.loss_output("dense")).remove)
        yield obs
