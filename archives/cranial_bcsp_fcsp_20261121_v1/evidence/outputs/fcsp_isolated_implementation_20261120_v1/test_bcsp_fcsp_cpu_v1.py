"""Only artificial tensors. Execute bound FC and Chamfer fragments without importing a donor."""

import ast
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch
from torch import nn


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from bcsp_fcsp_capture_v1 import capture_fc, load_partial, same_fp32_bytes, verify_capture_pair
from bcsp_fcsp_head_v1 import PlacementHead, coarse_geometry, fit_residual_scale, geometry_condition


def load_bound_ast(relative, digest):
    path = PROJECT / relative
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"unexpected source identity: {path.name}")
    return path, ast.parse(raw).body


def binding(nodes, name):
    return next(node for node in nodes if getattr(node, "name", None) == name)


def real_source_fragments():
    path, nodes = load_bound_ast(
        "outputs/p1pub/models/AdaPoinTr.py",
        "1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4",
    )
    outer = binding(binding(nodes, "AdaPoinTr").body, "forward")
    fc = binding(nodes, "SimpleRebuildFCLayer")
    scope = {"torch": torch, "nn": nn, "Mlp": lambda a, b, c: nn.Sequential(nn.Linear(a, b),
                                                                               nn.GELU(), nn.Linear(b, c))}
    exec(compile(ast.Module(body=[fc, outer], type_ignores=[]), str(path), "exec"), scope)
    loss_path, loss_nodes = load_bound_ast(
        "outputs/p1pub/extensions/chamfer_dist/__init__.py",
        "6456934164750c2d326236effe4827dc37c77a7d6d915d3c28fa65a90a9b1c50",
    )
    names = ("_torch_chamfer_forward", "ChamferDistanceL1Directional")
    parts = ast.Module(body=[binding(loss_nodes, name) for name in names], type_ignores=[])
    loss_scope = {"torch": torch, "chamfer": None}
    exec(compile(parts, str(loss_path), "exec"), loss_scope)
    return scope["forward"], scope["SimpleRebuildFCLayer"], loss_scope[names[1]]


class ToyBase(nn.Module):
    def __init__(self):
        super().__init__()
        order = (torch.arange(256) * 17 + 11) % 256
        self.register_buffer("order", order)
        self.register_buffer("inverse", order.argsort())
        self.project = nn.Linear(3, 5)

    def forward(self, xyz, epoch=None):
        q = xyz[:, :256].contiguous()
        h = self.project(q[:, self.order])[:, self.inverse]
        return h, q, 0, None


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        real_forward, fc_class, loss_class = real_source_fragments()

        class ArtificialDonor(nn.Module):
            forward = real_forward

            def __init__(self):
                super().__init__()
                self.decoder_type = "fc"
                self.num_query = 256
                self.factor = 32
                self.full_instrumentation_enabled = False
                self.base_model = ToyBase()
                self.increase_dim = nn.Conv1d(5, 6, 1)
                self.reduce_map = nn.Linear(6 + 5 + 3, 5)
                self.decode_head = fc_class(10, 32, 12)

        cls.donor_class = ArtificialDonor
        cls.loss_class = loss_class

    def setUp(self):
        torch.manual_seed(417)
        self.xyz = torch.rand(1, 8192, 3)
        self.model = self.donor_class().eval().requires_grad_(False)

    def test_actual_consumer_and_replay(self):
        cached = verify_capture_pair(self.model, self.xyz)
        self.assertEqual(cached.h.shape, (1, 256, 5))
        self.assertEqual(cached.p0.shape, (1, 256, 32, 3))
        with torch.no_grad():
            base = self.model.base_model
            self.assertFalse(torch.equal(base.order, base.inverse))
            q = self.xyz[:, :256]
            ordered_h = base.project(q[:, base.order])[:, base.inverse]
            case = self.model.increase_dim(ordered_h.transpose(1, 2)).transpose(1, 2).max(1)[0]
            h = self.model.reduce_map(torch.cat((case[:, None].expand(-1, 256, -1), ordered_h, q), -1))
            pooled = h.max(1)[0][:, None].expand(-1, 256, -1)
            offsets = self.model.decode_head.layer(torch.cat((pooled, h), -1)).reshape(1, 256, 32, 3)
            self.assertTrue(same_fp32_bytes(h, cached.h))
            self.assertTrue(same_fp32_bytes(q.unsqueeze(-2) + offsets, cached.p0))
        for value in (cached.q, cached.h, cached.p0):
            self.assertFalse(torch.is_inference(value))
            self.assertFalse(value.requires_grad)

    def test_capture_pair_decouples_trace_from_original(self):
        with torch.inference_mode():
            cached = capture_fc(self.model, self.xyz)
        self.assertFalse(any(torch.is_inference(v) for v in (cached.q, cached.h, cached.p0)))
        self.assertFalse(self.model.full_instrumentation_enabled)
        self.assertTrue(same_fp32_bytes(cached.q, self.xyz[:, :256]))
        self.assertFalse(self.model.reduce_map._forward_hooks)
        self.assertFalse(self.model.decode_head._forward_pre_hooks)

    def test_wrong_parent_order_is_rejected(self):
        hook = self.model.register_forward_hook(lambda _m, _x, out: (
            out[0], out[1].reshape(1, 256, 32, 3).roll(1, dims=1).flatten(1, 2)
        ))
        try:
            with self.assertRaisesRegex(ValueError, "parent-major"):
                capture_fc(self.model, self.xyz)
            self.assertFalse(self.model.base_model._forward_hooks)
            self.assertFalse(self.model.reduce_map._forward_hooks)
            self.assertFalse(self.model.decode_head._forward_pre_hooks)
            self.assertFalse(self.model.decode_head._forward_hooks)
        finally:
            hook.remove()

    def test_nonoriginal_h_is_rejected(self):
        hook = self.model.decode_head.register_forward_pre_hook(lambda _m, args: (args[0].roll(3, dims=1),))
        try:
            with self.assertRaisesRegex(ValueError, "actual reduce_map output"):
                capture_fc(self.model, self.xyz)
            self.assertEqual(len(self.model.decode_head._forward_pre_hooks), 1)
        finally:
            hook.remove()

    def test_donor_rng_and_mode_guards(self):
        hook = self.model.register_forward_pre_hook(lambda _m, _args: (torch.rand(1), None)[1])
        try:
            with self.assertRaisesRegex(ValueError, "state or RNG"):
                verify_capture_pair(self.model, self.xyz)
        finally:
            hook.remove()
        self.model.train()
        with self.assertRaisesRegex(ValueError, "eval mode"):
            capture_fc(self.model, self.xyz)

    def test_donor_buffer_guard(self):
        hook = self.model.register_forward_hook(lambda module, _x, _out: self.change_buffer(module))
        try:
            with self.assertRaisesRegex(ValueError, "state or RNG"):
                verify_capture_pair(self.model, self.xyz)
        finally:
            hook.remove()

    @staticmethod
    def change_buffer(model):
        model.base_model.order[0] = 0

    def test_local_descriptor_analytic_and_ties(self):
        q = torch.arange(256, dtype=torch.float32).view(1, 256, 1) * torch.tensor([1., 2., 3.])
        geometry, neighbors, scale = coarse_geometry(q)
        self.assertEqual(neighbors[0, 128].tolist(), [127, 129, 126, 130, 125, 131, 124, 132])
        np.testing.assert_allclose(scale[0, 128], (14 * 7.5) ** .5, rtol=1e-6)
        np.testing.assert_allclose(geometry[0, 128, 3:9], np.array([1, 2, 3, 4, 6, 9]) / 14,
                                   rtol=1e-6, atol=1e-7)
        self.assertTrue(same_fp32_bytes(geometry, coarse_geometry(q + 16)[0]))
        mirrored = coarse_geometry(q * torch.tensor([-1., 1., 1.]))[0]
        self.assertTrue(torch.equal(mirrored[..., 4:6], -geometry[..., 4:6]))

    def test_slot_permutation_without_ties(self):
        q = self.xyz[:, :256]
        order = self.model.base_model.order
        g, indices, _ = coarse_geometry(q)
        pg, pi, _ = coarse_geometry(q[:, order])
        self.assertTrue(same_fp32_bytes(pg, g[:, order]))
        self.assertTrue(torch.equal(order[pi], indices[:, order]))

    def test_degenerate_q_is_retained_nonfinite_is_blocked(self):
        q = torch.zeros((1, 256, 3))
        g, indices, scale = coarse_geometry(q)
        self.assertFalse(bool((indices == torch.arange(256)[None, :, None]).any()))
        self.assertTrue(torch.equal(scale, torch.zeros_like(scale)))
        self.assertTrue(torch.equal(g[..., :9], torch.zeros_like(g[..., :9])))
        self.assertTrue(torch.isfinite(g).all().item())
        q[0, 0, 0] = torch.nan
        with self.assertRaisesRegex(ValueError, "finite FP32"):
            coarse_geometry(q)

    def test_conditions_and_native_zero_output(self):
        cache = capture_fc(self.model, self.xyz)
        g = coarse_geometry(cache.q)[0]
        first = PlacementHead(cache.h.shape[-1], 0.2)
        second = PlacementHead(cache.h.shape[-1], 0.2)
        second.load_state_dict(first.state_dict())
        self.assertEqual(sum(x.numel() for x in first.parameters()), sum(x.numel() for x in second.parameters()))
        gb = geometry_condition(g, "B0-Global")
        self.assertTrue(same_fp32_bytes(gb, gb[:, :1].expand_as(gb)))
        self.assertIs(geometry_condition(g, "B1-Local"), g)
        self.assertTrue(same_fp32_bytes(first(cache.h, gb, cache.p0), cache.p0))
        self.assertTrue(same_fp32_bytes(second(cache.h, g, cache.p0), cache.p0))
        self.assertFalse(same_fp32_bytes(torch.tensor([-0.0]), torch.tensor([0.0])))

    def test_scale_is_pooled_linear_quantile_and_bounded(self):
        q = torch.zeros((2, 256, 3))
        p = torch.zeros((2, 256, 32, 3))
        p[..., 0] = torch.arange(2 * 256 * 32).reshape(2, 256, 32) / 65536
        expected = float(np.quantile(p[..., 0].numpy().astype(np.float64), .95, method="linear"))
        self.assertAlmostEqual(fit_residual_scale(q, p), expected, places=14)
        head = PlacementHead(5, expected)
        with torch.no_grad():
            head.net[-1].bias.fill_(20.)
        delta = head(torch.zeros(2, 256, 5), torch.zeros(2, 256, 10), p) - p
        self.assertLessEqual(float(delta.detach().abs().max()), expected + 1e-7)
        with self.assertRaisesRegex(ValueError, "invalid pooled"):
            fit_residual_scale(q, torch.zeros_like(p))

    def test_exact_loss_and_zero_gradient_staging(self):
        q, h, p0 = (self.xyz[:, :256], torch.rand(1, 256, 5, requires_grad=True),
                    torch.rand(1, 256, 32, 3, requires_grad=True))
        head = PlacementHead(5, .2)
        g = coarse_geometry(q)[0].requires_grad_()
        # Separate coordinate ranges ensure no zero distances in this gradient test.
        target = torch.rand(1, 17, 3) + 2
        loss_fn = self.loss_class()
        opt = torch.optim.AdamW(head.parameters(), lr=.001, weight_decay=.0001)
        for step in range(2):
            opt.zero_grad(set_to_none=True)
            dense = head(h, g, p0).flatten(1, 2)
            dist = torch.cdist(dense, target)
            oracle = .5 * (dist.min(-1).values.mean() + dist.min(-2).values.mean())
            loss = loss_fn(dense, target)
            self.assertTrue(torch.allclose(loss, oracle, atol=1e-7, rtol=1e-7))
            loss.backward()
            self.assertTrue(all(torch.isfinite(x.grad).all().item() for x in head.parameters()))
            self.assertEqual(head.net[0].weight.grad.count_nonzero().item() > 0, step == 1)
            self.assertGreater(head.net[-1].weight.grad.count_nonzero().item(), 0)
            self.assertTrue(all(x.grad is None for x in (h, g, p0)))
            opt.step()

    def test_bound_loss_reports_exact_overlap_gradient(self):
        points = torch.tensor([[[0., 0., 0.], [1., 0., 0.]]], requires_grad=True)
        value = self.loss_class()(points, points.detach().clone())
        self.assertEqual(value.item(), 0.0)
        value.backward()
        type(self).overlap_gradient_finite = bool(torch.isfinite(points.grad).all())
        # A finite forward does not certify the gradient of the historical sqrt path.
        self.assertFalse(type(self).overlap_gradient_finite)

    def test_synthetic_batch8_head_optimizes_both_arms(self):
        h = torch.rand(8, 256, 5)
        q = torch.rand(8, 256, 3)
        p = torch.rand(8, 256, 32, 3)
        local = coarse_geometry(q)[0]
        target = p + torch.tensor([.04, -.03, .02])
        initial = PlacementHead(5, .2).state_dict()
        for arm in ("B0-Global", "B1-Local"):
            with self.subTest(arm=arm):
                head = PlacementHead(5, .2)
                head.load_state_dict(initial)
                opt = torch.optim.AdamW(head.parameters(), lr=.001, weight_decay=.0001)
                geometry = geometry_condition(local, arm)
                start = (head(h, geometry, p) - target).square().mean().item()
                for _ in range(20):
                    opt.zero_grad(set_to_none=True)
                    (head(h, geometry, p) - target).square().mean().backward()
                    opt.step()
                final = (head(h, geometry, p) - target).square().mean().item()
                self.assertLess(final, start)

    def test_npz_partial_only_with_unreadable_implant(self):
        packet = io.BytesIO()
        x = np.zeros((8192, 3), dtype=np.float32)
        np.savez(packet, partial=x, implant=np.array([object()], dtype=object))
        raw = packet.getvalue()
        with tempfile.TemporaryDirectory(prefix="fcsp_cpu_", dir=HERE) as folder:
            path = Path(folder) / "artificial.npz"
            path.write_bytes(raw)
            np.testing.assert_array_equal(load_partial(path, len(raw), hashlib.sha256(raw).hexdigest()), x)
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                load_partial(path, len(raw), "0" * 64)


if __name__ == "__main__":
    torch.set_num_threads(2)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    print(json.dumps({"tests": result.testsRun, "passed": result.wasSuccessful(),
                      "pytorch": str(torch.__version__), "numpy": np.__version__,
                      "historical_chamfer_exact_overlap_gradient_finite":
                          getattr(Contracts, "overlap_gradient_finite", None),
                      "real_data_cases": 0, "real_model_forward": 0, "cuda_calls": 0}))
    raise SystemExit(not result.wasSuccessful())
