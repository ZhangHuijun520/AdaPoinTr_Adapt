"""Artificial tensor and inherited-computation checks for the isolated CISC entry."""

import hashlib
import importlib.util
import inspect
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest

import numpy as np
import torch


HERE = Path(__file__).resolve().parent
OASG = HERE.parent / "bcsp_oasg_20261124_v1/p1_implementation_v1"
sys.path[:0] = [str(HERE), str(OASG)]
import bcsp_cisc_entry_v1 as entry
from bcsp_cisc_head_v1 import (
    Condition, CiscObservationHead, CutConditioner, EXTRA_PARAMETERS, assign, auxiliary_loss, describe,
)
import test_bcsp_oasg_cpu_v2 as inherited
from bcsp_oasg_head_v1 import ObservationAnchoredHead


class CpuContracts(unittest.TestCase):
    def test_chunking_tie_empty_and_mass(self):
        x = torch.zeros(2, 2051, 3, requires_grad=True)
        s = torch.tensor([[[-1., 0, 0], [1., 0, 0], [5., 0, 0]]] * 2)
        v, n = assign(x, s)
        self.assertTrue(torch.equal(v, torch.zeros_like(v)))
        self.assertEqual(n.tolist(), [[2051, 0, 0]] * 2)
        self.assertFalse(v.requires_grad or n.requires_grad)
        points = torch.randn(2, 2051, 3, generator=torch.Generator().manual_seed(3))
        v, n = assign(points, s)
        direct = (points[:, :, None] - s[:, None]).square().sum(-1).argmin(-1)
        self.assertTrue(torch.equal(v, direct))
        self.assertTrue(torch.equal(n.sum(1), torch.full((2,), 2051)))

    def test_distribution_analytic_empty_fallback_and_reordered_inputs(self):
        x = torch.tensor([[[0., 0, 0], [0., 0, 0], [2., 0, 0], [2., 0, 0]]])
        s = torch.tensor([[[0., 0, 0], [2., 0, 0], [8., 0, 0]]])
        v, n = assign(x, s)
        logits = torch.logit(torch.tensor([[.25, .75, .999]]))
        spatial = describe(x, s, v, n, logits, "I")
        uniform = describe(x, s, v, n, logits, "U")
        torch.testing.assert_close(spatial[0, :, 0], torch.tensor([.25, .75, .5]))
        torch.testing.assert_close(uniform[0, :, 0], torch.full((3,), .5))
        torch.testing.assert_close(spatial[0, :, 2], s[0, :, 0] - 1.5)
        torch.testing.assert_close(uniform[0, :, 2], s[0, :, 0] - 1.)
        torch.testing.assert_close(spatial[0, :, 5], torch.full((3,), .75))
        self.assertEqual(torch.count_nonzero(spatial[0, :, 6:]).item(), 0)
        reordered = torch.tensor([2, 0, 3, 1])
        xe = x[:, reordered]
        ve, ne = assign(xe, s)
        torch.testing.assert_close(spatial, describe(xe, s, ve, ne, logits, "I"))
        perm = [2, 0, 1]
        vp, np_ = assign(x, s[:, perm])
        torch.testing.assert_close(spatial[:, perm], describe(x, s[:, perm], vp, np_, logits[:, perm], "I"))

    def test_constant_and_extreme_supports_finite(self):
        x = torch.tensor([[[0., 1, 0], [1., 0, 2], [2., 0, 0]]])
        s = torch.cat((x, x + 4), dim=1)
        v, n = assign(x, s)
        for scalar in (-100., 0., 100.):
            logits = torch.full(n.shape, scalar)
            u = describe(x, s, v, n, logits, "U")
            i = describe(x, s, v, n, logits, "I")
            torch.testing.assert_close(u, i)
            self.assertTrue(torch.isfinite(i).all())

    def test_auxiliary_bce_weights_and_empty_cell_gradient(self):
        x = torch.tensor([[[0., 0, 0], [0., 0, 0], [2., 0, 0], [2., 0, 0]]])
        s = torch.tensor([[[0., 0, 0], [2., 0, 0], [8., 0, 0]]])
        v, n = assign(x, s)
        logits = torch.tensor([[.7, -.5, 1.]], requires_grad=True)
        cond = Condition(torch.empty(0), logits, v, n)
        y = torch.tensor([[True, False, True, True]])
        result = auxiliary_loss(cond, y)
        pointwise = torch.nn.functional.binary_cross_entropy_with_logits(logits.gather(1, v), y.float())
        torch.testing.assert_close(result, pointwise)
        result.backward()
        self.assertEqual(logits.grad[0, 2].item(), 0)
        self.assertEqual(torch.count_nonzero(logits.grad).item(), 2)
        with self.assertRaises(ValueError):
            auxiliary_loss(cond, y.float())

    def test_artificial_oblique_interface_provenance(self):
        # Reuse the historical sampler only on two artificial adjacent voxels.
        path = HERE.parent / "cranial_bcsp_geov1_20261024/real_data_qc_v1.py"
        spec = importlib.util.spec_from_file_location("cisc_cpu_geometry", path)
        sampler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sampler)
        d = np.zeros((3, 3, 3), dtype=bool)
        g = d.copy()
        d[1, 1, 1], g[2, 1, 1] = True, True
        a = np.array([[1., 0.1, 0.], [0., 2., .4], [.3, 0., 3.]])
        origin = np.array([5., -1., 3.])
        ds, gs = sampler.surface(d), sampler.surface(g)
        jd, jg = sampler.contact(ds, g), sampler.contact(gs, d)
        dk, sign_d = sampler.keys(ds, jd)
        gk, sign_g = sampler.keys(gs, jg)
        np.testing.assert_array_equal(dk, gk)
        np.testing.assert_array_equal(sign_d, -sign_g)
        p, indices, centers, area = sampler.sample(ds, a, origin, 0, 16384)
        self.assertAlmostEqual(area[jd].item(), np.linalg.norm(np.cross(a[1], a[2])))
        np.testing.assert_allclose(centers[jd][0], np.array([1.5, 1., 1.]) @ a + origin)
        aligned = jd[indices[:8192]]
        self.assertTrue(aligned.any() and (~aligned).any())
        np.testing.assert_allclose((p[:8192][aligned] - origin) @ np.linalg.inv(a),
                                   np.column_stack((np.full(aligned.sum(), 1.5),
                                                    ((p[:8192][aligned] - origin) @ np.linalg.inv(a))[:, 1:])))

    @staticmethod
    def models():
        init = dict(path=str(OASG / "artificial_cpu_v1/OASG_head_init_seed2026112402_v1.bin"),
                    sha256="a445481a3400d4c8ef6d07af164d64430d9fc2c9ec30a80f0d339bb5a636966b",
                    bytes=7362572, seed=inherited.HEAD_SEED)
        builder, mixer = inherited.legacy.artificial_fixture()
        models = {}
        for arm in ("R", "U", "I"):
            model, _ = inherited.cpu_model("A", builder, mixer, init)
            rng = torch.random.get_rng_state().clone()
            opts = {} if arm == "R" else dict(prior=.13, auxiliary_seed=2026112605)
            models[arm] = entry.attach(model, arm, **opts)
            assert torch.equal(rng, torch.random.get_rng_state())
        return models

    def test_shared_graph_and_loss_consumer(self):
        r, u, i = self.models().values()
        common = r.state_dict()
        for candidate in (u, i):
            state = candidate.state_dict()
            self.assertTrue(all(torch.equal(v, state[k]) for k, v in common.items()))
            self.assertEqual(sum(p.numel() for p in candidate.parameters())
                             - sum(p.numel() for p in r.parameters()), EXTRA_PARAMETERS)
        self.assertTrue(all(torch.equal(x, i.state_dict()[k]) for k, x in u.state_dict().items()))
        self.assertNotIn("labels", inspect.signature(i.forward).parameters)

        gen = torch.Generator().manual_seed(875)
        x = torch.randn(1, 8192, 3, generator=gen) * .33
        for model in (r, u, i):
            model.eval()
        with torch.inference_mode():
            qr, pr = r(x)
            for model in (u, i):
                q, p = model(x)
                torch.testing.assert_close(q, qr, atol=1e-6, rtol=1e-5)
                torch.testing.assert_close(p, pr, atol=1e-6, rtol=1e-5)
            with self.assertRaises(TypeError):
                i(x, labels=x[..., 0] > 0)
        del r, u, common, state

        head = i.base_model.coarse_pred
        with torch.no_grad():
            head.condition_map.weight[0, 0] = 2
            head.conditioner.last.weight[0, 0] = 1
        observed = {}
        handles = [
            head.register_forward_hook(lambda m, args, out: observed.update(q=out[0], s=args[2], f=args[1],
                                                                            x_same=args[3] is x)),
            i.base_model.decoder.register_forward_pre_hook(
                lambda m, args, kwargs: observed.update(decoder=kwargs), with_kwargs=True),
            i.reduce_map.register_forward_pre_hook(lambda m, args: observed.update(rebuild=args[0])),
            i.decode_head.register_forward_hook(lambda m, args, out: observed.update(relative=out)),
            i.loss_func.register_forward_pre_hook(lambda m, args: observed.update(coarse_loss=args[0])),
            i.fine_loss_func.register_forward_pre_hook(lambda m, args: observed.update(dense_loss=args[0])),
        ]
        y = x[..., 0] > 0
        target = torch.randn(1, 8192, 3, generator=gen) * .23
        try:
            with torch.inference_mode():
                i.eval()
                qi, pi = i(x)
                self.assertTrue(observed["x_same"])
                self.assertIs(observed["decoder"]["v_pos"], observed["s"])
                self.assertIs(observed["decoder"]["v"], observed["f"])
                self.assertTrue(torch.equal(qi, observed["q"]))
                self.assertTrue(torch.equal(qi, observed["decoder"]["q_pos"]))
                self.assertTrue(torch.equal(qi, observed["rebuild"][..., -3:]))
                self.assertTrue(torch.equal(pi.reshape(1, 256, 32, 3), qi[:, :, None] + observed["relative"]))
                self.assertFalse(torch.equal(qi, qr))
                i.train()
                a = entry.training_losses(i, x, target, 0, y)
                q_before = observed["coarse_loss"].clone()
                dense_before = observed["dense_loss"].clone()
                b = entry.training_losses(i, x, target, 0, ~y)
                self.assertTrue(torch.equal(q_before, observed["coarse_loss"]))
                self.assertTrue(torch.equal(dense_before, observed["dense_loss"]))
                self.assertEqual(a.original.item(), b.original.item())
                self.assertNotEqual(a.interface.item(), b.interface.item())
            loss = entry.training_losses(i, x, target, 0, y)
            self.assertTrue(torch.equal(observed["q"], observed["coarse_loss"]))
            self.assertTrue(torch.equal(observed["dense_loss"].reshape(1, 256, 32, 3),
                                        observed["q"][:, :, None] + observed["relative"]))
            loss.total.backward()
            for p in (head.conditioner.first.weight, head.conditioner.last.weight, head.condition_map.weight):
                self.assertTrue(torch.isfinite(p.grad).all())
                self.assertGreater(torch.count_nonzero(p.grad).item(), 0)
            self.assertAlmostEqual(loss.total.item(), loss.original.item() + .05 * loss.interface.item(), places=6)
        finally:
            for handle in handles:
                handle.remove()
        self.assertFalse(head.conditioner._forward_hooks)

    def test_initial_gradient_paths(self):
        head = CutConditioner("I", .1, 2026112605)
        g = torch.Generator().manual_seed(7)
        x = torch.randn(1, 8192, 3, generator=g)
        f = torch.randn(1, 256, 384, generator=g, requires_grad=True)
        cond = head(x, x[:, :256], f)
        loss = auxiliary_loss(cond, x[..., 0] > .8)
        loss.backward()
        self.assertEqual(torch.count_nonzero(head.first.weight.grad).item(), 0)
        self.assertGreater(torch.count_nonzero(head.last.weight.grad).item(), 0)

    def test_verified_sidecar_blocks_mismatched_input_and_row_order(self):
        x = np.arange(8192 * 3, dtype=np.float32).reshape(8192, 3)
        rows = np.arange(8192)
        y = rows % 4 == 0
        partial_hash = hashlib.sha256(x.tobytes()).hexdigest()

        def decode(order, partial, wrong_hash=False):
            buffer = BytesIO()
            np.savez_compressed(buffer, row_id=order, face_id=rows // 3, is_j=y)
            raw = buffer.getvalue()
            digest = "0" * 64 if wrong_hash else hashlib.sha256(raw).hexdigest()
            return entry.verified_labels(raw, partial, label_sha256=digest, partial_sha256=partial_hash)

        np.testing.assert_array_equal(decode(rows, x), y)
        with self.assertRaisesRegex(ValueError, "input|partial"):
            decode(rows, x[::-1])
        with self.assertRaisesRegex(ValueError, "SHA256"):
            decode(rows, x, True)
        with self.assertRaisesRegex(ValueError, "row identity"):
            decode(rows[::-1], x)

    def test_generation_gradient_through_spatial_description(self):
        generator = torch.Generator().manual_seed(19)
        x = torch.randn(1, 8192, 3, generator=generator) * .3
        f = torch.randn(1, 256, 384, generator=generator)
        z = torch.randn(1, 1024, generator=generator)
        i = CiscObservationHead(ObservationAnchoredHead(), "I", .1, 2026112605)
        u = CiscObservationHead(ObservationAnchoredHead(), "U", .1, 2026112605)
        q, _ = i(z, f, x[:, :256], x)
        grad, = torch.autograd.grad(q[0, 0, 0], i.condition_map.weight)
        self.assertGreater(torch.count_nonzero(grad).item(), 0)
        with torch.no_grad():
            i.condition_map.weight[:, 0] = .1
            i.conditioner.last.weight[0, 0] = 1.
            u.load_state_dict(i.state_dict())
        qi, _ = i(z, f, x[:, :256], x)
        qu, _ = u(z, f, x[:, :256], x)
        self.assertGreater((qi - qu).abs().max().item(), 1e-6)
        grads = torch.autograd.grad(qi[0, 0, 0], (i.conditioner.first.weight, i.conditioner.last.weight))
        self.assertTrue(all(torch.isfinite(g).all() and torch.count_nonzero(g) for g in grads))


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir()
    torch.set_num_threads(2)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CpuContracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    files = [HERE / name for name in ("bcsp_cisc_head_v1.py", "bcsp_cisc_entry_v1.py", Path(__file__).name)]
    report = dict(passed=result.wasSuccessful(), tests=result.testsRun, failures=len(result.failures),
                  errors=len(result.errors), device="cpu", torch=torch.__version__, numpy=np.__version__,
                  python=sys.version.split()[0], synthetic_only=True, optimizer_steps=0, native_mamba_calls=0,
                  sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    with (out / "result.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    sys.exit(not result.wasSuccessful())
