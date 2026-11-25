"""One CPU batch on synthetic tensors, using the previously verified LQI fixture."""

import ast
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import numpy as np
import torch
from torch import nn

import bcsp_oasg_entry_v1 as entry
from bcsp_oasg_head_v1 import HEAD_PARAMETERS, HEAD_SEED, ObservationAnchoredHead, load_head


HERE = Path(__file__).resolve().parent
PRIME = HERE.parents[1] / "scq_prime_entry_20261121_v1"
sys.path.insert(0, str(PRIME))
import test_scq_prime_entry_cpu_v1 as legacy

RESULT = {}


def cpu_model(arm, builder, mixer, initializer=None):
    return entry.construct(entry.identity(arm, "D", entry.TRAIN_SEED), builder, initializer,
                           np=np, prime=legacy.entry, seeded=legacy.parent, lqi=legacy.scq.parent,
                           scq=legacy.scq, artificial_mixer=mixer)


class ReachedLifecycle(Exception):
    pass


def runtime_fixture():
    path = PRIME / "bcsp_scq_prime_runtime_v1.py"
    tree = ast.parse(path.read_bytes(), str(path))
    runtime = SimpleNamespace()
    def reached_order(*args):
        raise ReachedLifecycle
    [lifecycle] = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "train_lifecycle"]
    [groups] = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "optimizer_groups"]
    for function in (lifecycle, groups):
        ns = {"require": entry.require, "validate_order": reached_order}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), ns)
        setattr(runtime, function.name, ns[function.name])
    return runtime


class HeadContracts(unittest.TestCase):
    def test_serialized_initializer_seed_size_and_rng(self):
        raw = Path(INITIALIZER["path"]).read_bytes()
        rng = torch.random.get_rng_state().clone()
        head = load_head(INITIALIZER)
        self.assertEqual(sum(p.numel() for p in head.parameters()), HEAD_PARAMETERS)
        self.assertEqual(b"".join(p.detach().numpy().tobytes() for p in head.parameters()), raw)
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        self.assertEqual(INITIALIZER["seed"], HEAD_SEED)

    def test_rejects_bad_initializer_digest_size_seed(self):
        for key, value in (("sha256", "0" * 64), ("bytes", 1), ("seed", entry.TRAIN_SEED)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                load_head({**INITIALIZER, key: value})

    def test_formula_joint_permutation_and_pointwise_feature_effect(self):
        head = ObservationAnchoredHead()
        z = torch.zeros(2, 1024)
        memory = torch.zeros(2, 256, 384)
        coordinates = torch.linspace(-0.6, 0.6, 2 * 256 * 3).reshape(2, 256, 3)
        with torch.no_grad():
            for p in head.parameters():
                p.zero_()
            head[0].weight[0, 1024] = head[2].weight[0, 0] = head[4].weight[0, 0] = 1
            head[0].weight[1, 0] = head[2].weight[1, 1] = head[4].weight[1, 1] = 1
            q0, delta0 = head(z, memory, coordinates)
            memory[:, 9, 0] = 2
            z[1, 0] = 2
            q, delta = head(z, memory, coordinates)
            perm = torch.arange(255, -1, -1)
            q_permuted, delta_permuted = head(z, memory[:, perm], coordinates[:, perm])
        self.assertTrue(torch.equal(q0, coordinates))
        self.assertEqual(torch.count_nonzero(delta0).item(), 0)
        self.assertTrue(torch.equal(q, coordinates + delta))
        self.assertTrue(torch.equal(q_permuted, q[:, perm]) and torch.equal(delta_permuted, delta[:, perm]))
        self.assertEqual(torch.count_nonzero(delta[..., 0]).item(), 2)
        self.assertTrue((delta[:, 9, 0] > 0).all())
        self.assertTrue((delta[1, :, 1] > 0).all() and (delta[0, :, 1] == 0).all())

    def test_rejects_unaligned_shapes(self):
        with self.assertRaisesRegex(ValueError, "paired 256-token"):
            ObservationAnchoredHead()(torch.zeros(1, 1024), torch.zeros(1, 255, 384), torch.zeros(1, 256, 3))


class EntryContracts(unittest.TestCase):
    def test_rejects_wrong_arm_fold_seed_and_head_attachment(self):
        for args in (("F", "D", entry.TRAIN_SEED), ("A", "C", entry.TRAIN_SEED), ("A", "D", 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                entry.identity(*args)
        for arm, record in (("A", None), ("B", INITIALIZER)):
            with self.assertRaisesRegex(ValueError, "A-only initializer"):
                cpu_model(arm, None, None, record)

    def test_runtime_adapts_only_identity_without_starting_training(self):
        original = runtime_fixture()
        bound = entry.bind_training_lifecycle(original)
        kwargs = dict(device="cpu", numeric_check=None, resources=None, knn_enable=None, state_fingerprint=None)
        args = (None, None, [], None, None)
        for arm in ("A", "B"):
            with self.subTest(arm=arm), self.assertRaises(ReachedLifecycle):
                bound(*args, **kwargs, run_identity=entry.identity(arm, "D", entry.TRAIN_SEED))
        with self.assertRaisesRegex(ValueError, "SCQ-PRIME runtime identity"):
            original.train_lifecycle(*args, **kwargs, run_identity=entry.identity("A", "D", entry.TRAIN_SEED))
        with self.assertRaisesRegex(ValueError, "OASG Fold D"):
            bound(*args, **kwargs, run_identity=dict(variant="F", fold="D", seed=entry.TRAIN_SEED))

    def test_full_artificial_cpu_graph_state_consumers_and_loss(self):
        builder, mixer = legacy.artificial_fixture()
        reference_run = legacy.entry.identity("B", "D", entry.TRAIN_SEED)
        reference, proof = legacy.entry.construct(reference_run, builder, None, torch=torch, np=np,
                                                 parent=legacy.parent, lqi=legacy.scq.parent,
                                                 scq=legacy.scq, artificial_mixer=mixer)
        b, b_proof = cpu_model("B", builder, mixer)
        rng_at_b = torch.random.get_rng_state().clone()
        gen = torch.Generator().manual_seed(825)
        x = torch.randn(1, 8192, 3, generator=gen) * .31
        y = torch.randn(1, 8192, 3, generator=gen) * .23 + .07
        with torch.no_grad():
            expected = reference.eval()(x)
            actual = b.eval()(x)
        self.assertTrue(all(torch.equal(u, v) for u, v in zip(expected, actual)))
        self.assertEqual(proof["common_initial_state_SHA256"], b_proof["historical_B_initial_state_SHA256"])
        self.assertIs(b.base_model.forward.__func__, type(b.base_model).forward)
        self.assertFalse(hasattr(b.base_model, "scq"))
        del reference

        a, a_proof = cpu_model("A", builder, mixer, INITIALIZER)
        self.assertTrue(torch.equal(rng_at_b, torch.random.get_rng_state()))
        self.assertEqual(a_proof["shared_initial_state_SHA256"], b_proof["shared_initial_state_SHA256"])
        self.assertEqual(a_proof["historical_B_initial_state_SHA256"], b_proof["historical_B_initial_state_SHA256"])
        self.assertEqual(a_proof["total_parameters"] - b_proof["total_parameters"], 3843)
        self.assertIsInstance(a.base_model.coarse_pred, ObservationAnchoredHead)
        self.assertFalse(hasattr(a.base_model, "scq"))
        original_groups = runtime_fixture().optimizer_groups
        groups = {r["name"]: r["weight_decay"] for r in original_groups(a)[1]}
        actual_head = {n: v for n, v in groups.items() if n.startswith(entry.COARSE_PREFIX)}
        want_head = {
            f"{entry.COARSE_PREFIX}{layer}.{field}": val
            for layer in (0, 2, 4) for field, val in (("weight", .0005), ("bias", 0.))
        }
        self.assertEqual(actual_head, want_head)
        del b

        bound = {}
        def seed_capture(module, args, values):
            bound["memory"], bound["anchors"] = args[1:]
            bound["coarse"], bound["delta"] = values
        def embedding_capture(module, args):
            bound["embedding"] = args[0]
        def decoder_capture(module, args, kwargs):
            bound["decoder"] = kwargs
        def rebuild_input_capture(module, args):
            bound["rebuild_input"] = args[0]
        handles = [
            a.base_model.coarse_pred.register_forward_hook(seed_capture),
            a.base_model.mlp_query.register_forward_pre_hook(embedding_capture),
            a.base_model.decoder.register_forward_pre_hook(decoder_capture, with_kwargs=True),
            a.reduce_map.register_forward_pre_hook(rebuild_input_capture),
        ]
        a.full_instrumentation_enabled = True
        try:
            with torch.no_grad():
                q, dense = a.eval()(x)
        finally:
            for handle in handles:
                handle.remove()
            a.full_instrumentation_enabled = False
        self.assertIs(bound["decoder"]["v"], bound["memory"])
        self.assertIs(bound["decoder"]["v_pos"], bound["anchors"])
        self.assertTrue(torch.equal(q, bound["anchors"] + bound["delta"]))
        self.assertTrue(torch.equal(q, bound["coarse"]))
        self.assertTrue(torch.equal(q, bound["decoder"]["q_pos"]))
        self.assertTrue(torch.equal(q, bound["embedding"][..., -3:]))
        rebuild = a._last_full_instrumentation
        self.assertTrue(torch.equal(q, bound["rebuild_input"][..., -3:]))
        self.assertTrue(torch.equal(dense.view(1, 256, 32, 3), q[:, :, None] + rebuild["relative_xyz"]))
        self.assertEqual(tuple(dense.shape), (1, 8192, 3))

        events = []
        observations = []
        resources = SimpleNamespace(before_step=lambda step: events.append(("before", step)),
                                    after_step=lambda step: events.append(("after", step)))
        with entry.observe_training(a, entry.identity("A", "D", entry.TRAIN_SEED), resources, observations.append) as obs:
            obs.before_step(0)
            ret = a.train()(x)
            denoise, loss = a.get_loss(ret, y, 0, partial=x)
            self.assertEqual(float(denoise), 0.)
            loss.backward()
            self.assertAlmostEqual(float(loss), obs.losses["coarse"] + obs.losses["dense"], places=6)
            obs.after_step(1)
            obs.before_step(1)
            obs.after_step(2)
        self.assertEqual(events, [("before", 0), ("after", 1), ("before", 1), ("after", 2)])
        self.assertEqual([o["step"] for o in observations], [1])
        self.assertIn("anchor_displacement_p50_p95", observations[0]["geometry"])
        self.assertTrue(all(not module._forward_hooks for module in
                            (a, a.loss_func, a.fine_loss_func, a.base_model.coarse_pred)))
        for module in (a.base_model.coarse_pred, a.base_model.input_proj, a.decode_head):
            grads = [p.grad for p in module.parameters()]
            self.assertTrue(all(g is not None and torch.isfinite(g).all().item() for g in grads))
            self.assertTrue(any(torch.count_nonzero(g).item() for g in grads))
        RESULT.update(b=b_proof, a=a_proof, synthetic_training_losses=observations[0]["losses"])


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir()
    torch.set_num_threads(2)
    path = HERE / "artificial_cpu_v1" / "OASG_head_init_seed2026112402_v1.bin"
    INITIALIZER = dict(path=str(path), sha256="a445481a3400d4c8ef6d07af164d64430d9fc2c9ec30a80f0d339bb5a636966b",
                       bytes=7362572, seed=HEAD_SEED)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == INITIALIZER["sha256"]
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (out / "cpu_contract_result_v2.json").write_text(json.dumps(
        dict(passed=result.wasSuccessful(), tests=result.testsRun, failures=len(result.failures),
             errors=len(result.errors), initializer=INITIALIZER, torch=torch.__version__, numpy=np.__version__,
             python=sys.version.split()[0], device="cpu", fixtures="artificial", optimizer_steps=0,
             native_mamba_forward=0, observed=RESULT),
        indent=2, allow_nan=False) + "\n", encoding="utf-8")
    sys.exit(0 if result.wasSuccessful() else 1)
