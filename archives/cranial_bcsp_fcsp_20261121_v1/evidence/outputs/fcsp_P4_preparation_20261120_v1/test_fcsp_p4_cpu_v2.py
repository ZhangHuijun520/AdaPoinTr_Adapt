"""P4 contracts with artificial tensors and metadata only."""

import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import bcsp_fcsp_p4_train_v1 as p4

p4.load_numeric()
torch.set_num_threads(2)


def record(path, raw=None):
    if raw is not None:
        path.write_bytes(raw)
    payload = path.read_bytes()
    return dict(path=str(path), bytes=len(payload), sha256=p4.sha(payload))


def packed(**members):
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **members)
    return buffer.getvalue()


def artificial_cases():
    defects = ("bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2")
    return [f"train__{source:03d}__{defect}" for source in range(63) for defect in defects]


def synthetic_order():
    ids = artificial_cases()
    return dict(schema="bcsp-shared-order-v1", case_ids=ids,
                epochs=[dict(epoch=e, batches=[ids[i:i+8] for i in range(0, 312, 8)],
                             dropped=ids[-3:]) for e in range(100)])


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.head = p4.load_head(record(ROOT / "outputs/fcsp_isolated_implementation_20261120_v1"
                                      / "bcsp_fcsp_head_v1.py"))
        cls.loss = p4.load_loss(record(ROOT / "outputs/p1pub/extensions/chamfer_dist/__init__.py"))

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="fcsp_p4_cpu_", dir=HERE)
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def cache_fixture(self):
        rng = np.random.default_rng(49)
        x = {key: rng.normal(0, .1, shape).astype(np.float32)
             for key, shape in p4.CACHE_FIELDS.items()}
        x["neighbors"] = (np.arange(256, dtype=np.int64)[:, None] + np.arange(1, 9, dtype=np.int64)) % 256
        x["scale"] = np.abs(x["scale"])
        target = rng.normal(0, .1, (8192, 3)).astype(np.float32)
        c = record(self.directory / "cache.npz", packed(**x))
        # If the loader ever decodes partial, allow_pickle=False raises.
        l = record(self.directory / "label.npz", packed(implant=target, partial=np.array([None])))
        l["member_sha256"] = p4.sha(target.tobytes())
        return c, l

    def test_train_only_target_loader_and_bound_hashes(self):
        c, l = self.cache_fixture()
        x, y = p4.load_row(c, l)
        self.assertEqual((x["H"].shape, y.shape), ((256, 384), (8192, 3)))
        with self.assertRaisesRegex(ValueError, "implant member"):
            p4.load_row(c, {**l, "member_sha256": "0" * 64})
        with self.assertRaisesRegex(ValueError, "bound bytes"):
            p4.load_row({**c, "sha256": "0" * 64}, l)

    def test_production_selection_rejects_development_label_routing(self):
        d = self.directory
        labels = d / "labels"
        manifest, selection = [], []
        for case in artificial_cases():
            source = "train:" + case.split("__")[1]
            name = f"C__{case}.npz"
            manifest.append(dict(case_id=case, source_id=source, fold="C", split="train",
                                 input_sha256="a"*64, capture=dict(file=name, bytes=99, sha256="b"*64)))
            selection.append(dict(case_id=case, source_id=source, cache_file=str(d / name),
                                  label_npz=dict(path=str(labels / (case+"_8192.npz")), sha256="a"*64,
                                                 read_member="implant", member_shape=[8192, 3],
                                                 member_dtype="float32", member_sha256="c"*64)))
        manifest.extend(dict(fold="C", split="development", source_id=f"train:{i:03d}") for i in range(63, 84))
        manifest.extend(dict(fold="D", split="development") for _ in range(840-len(manifest)))
        select = dict(status="TRAIN_ONLY_FROZEN_LOCAL_SELECTION", fold="C", rows=selection)
        self.assertEqual(len(p4.bind_training(select, manifest, d, {labels})), 315)
        selection[0]["label_npz"]["path"] = str(d / "development" / "example.npz")
        with self.assertRaisesRegex(ValueError, "label identity"):
            p4.bind_training(select, manifest, d, {labels})

    def test_order_rejects_corruption_and_lr_endpoints(self):
        order = synthetic_order()
        cases = set(order["case_ids"])
        self.assertEqual(len(p4.validate_order(order, cases)), 100)
        order["epochs"][0]["batches"][0][1] = order["epochs"][0]["batches"][0][0]
        with self.assertRaisesRegex(ValueError, "case inventory"):
            p4.validate_order(order, cases)
        self.assertAlmostEqual(p4.learning_rate(1), .000005)
        self.assertEqual(p4.learning_rate(200), .001)
        self.assertGreater(p4.learning_rate(200), p4.learning_rate(201))
        self.assertEqual(p4.learning_rate(3900), .00001)
        with self.assertRaises(ValueError):
            p4.learning_rate(3901)

    def test_scale_and_deterministic_seed_and_zero_head(self):
        d = {"x": p4.load_row(*self.cache_fixture())}
        rng = torch.get_rng_state().clone()
        a, scale = p4.build_training(self.head, d, "cpu")
        with torch.random.fork_rng(devices=[]):
            torch.randn(30)
            b, _ = p4.build_training(self.head, d, "cpu")
        self.assertTrue(torch.equal(torch.get_rng_state(), rng))
        self.assertEqual(p4.state_sha(a), p4.state_sha(b))
        x = d["x"][0]
        offsets = np.linalg.norm(x["P0"].double().numpy()-x["Q"].double().numpy()[:, None], axis=-1)
        self.assertAlmostEqual(scale, np.quantile(offsets, .95, method="linear"), places=12)
        g = x["geometry"][None]
        cond = self.head["geometry_condition"](g, p4.ARM)
        self.assertTrue(torch.equal(cond[:, 0], cond[:, 255]))
        p = x["P0"][None]
        self.assertTrue(torch.equal(a(x["H"][None], cond, p).view(torch.int32), p.view(torch.int32)))

    def test_historical_loss_and_two_head_updates(self):
        prediction = torch.tensor([[[0., 0., 0.], [2., 0., 0.]]], requires_grad=True)
        target = torch.tensor([[[0., 0., 0.], [3., 0., 0.]]])
        value = self.loss(prediction, target)
        self.assertEqual(float(value), .5)
        value.backward()
        self.assertTrue(bool(torch.isfinite(prediction.grad).all()))
        dataset = {"x": p4.load_row(*self.cache_fixture())}
        model, _ = p4.build_training(self.head, dataset, "cpu")
        opt = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.0001, foreach=False, fused=False)
        # Keep the correct production loss on a small artificial subset for CPU.
        loss = lambda a, b: self.loss(a[:, :16], b[:, :16])
        one = p4.train_step(model, dataset, ["x"], "cpu", self.head["geometry_condition"], loss, opt, 1)
        self.assertGreater(one["gradient_norm_pre_clip"], 0)
        self.assertEqual(one["residual"]["max_norm"], 0)
        self.assertEqual(int(model.net[0].weight.grad.count_nonzero()), 0)
        two = p4.train_step(model, dataset, ["x"], "cpu", self.head["geometry_condition"], loss, opt, 2)
        self.assertGreater(two["residual"]["max_norm"], 0)
        self.assertGreater(int(model.net[0].weight.grad.count_nonzero()), 0)
        self.assertEqual(int(opt.state[model.net[0].weight]["step"]), 2)

    def test_checkpoint_and_exact_update_ledger_with_stubbed_steps(self):
        dataset = {"x": p4.load_row(*self.cache_fixture())}
        order = synthetic_order()
        epochs = p4.validate_order(order, set(order["case_ids"]))
        with patch.object(p4, "train_step", return_value=dict(loss=1., nonfinite=0)) as stub:
            p4.train(self.head, self.loss, dataset, epochs, "cpu", self.directory, "hash", lambda _: None)
        self.assertEqual(stub.call_count, 3900)
        done = json.loads((self.directory / "completion.json").read_bytes())
        self.assertEqual((done["updates"], done["exposures"], done["drops"]), (3900, 31200, 300))
        path = self.directory / done["checkpoint"]["file"]
        self.assertEqual(record(path)["sha256"], done["checkpoint"]["sha256"])
        weight = torch.load(path, weights_only=True)
        self.assertEqual((weight["step"], weight["fold"], weight["arm"]), (3900, "C", p4.ARM))
        lines = [json.loads(x) for x in (self.directory/"metrics.jsonl").read_bytes().splitlines()]
        self.assertEqual([x["case_ids"] for x in lines], [b for epoch in epochs for b in epoch["batches"]])

    def test_nonfinite_loss_stops_before_update(self):
        data = {"x": p4.load_row(*self.cache_fixture())}
        model, _ = p4.build_training(self.head, data, "cpu")
        opt = torch.optim.AdamW(model.parameters())
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            p4.train_step(model, data, ["x"], "cpu", self.head["geometry_condition"],
                          lambda a, b: a.mean()*float("nan"), opt, 1)
        self.assertFalse(opt.state)

    def test_exact_authorization_and_claim(self):
        d = self.directory
        r, a, n, c = (str(d/name) for name in ("request.json", "authorization.json", "runtime.json", "claim.json"))
        launch = dict(request=r, authorization=a, runtime=n, claim=c)
        req = dict(schema="bcsp-fcsp-p4-training-v1", status="AWAITING_EXPLICIT_USER_AUTHORIZATION",
                   execution_authorized=False, fold="C", arm=p4.ARM, seed=0, counts=p4.COUNTS, launch=launch)
        def save(path, value):
            return record(Path(path), json.dumps(value).encode())["sha256"]
        rh = save(r, req)
        ah = save(a, dict(schema="bcsp-fcsp-p4-authorization-v1", request_sha256=rh,
                          explicit_user_authorization=True, user_authorization_text="fixture"))
        nh = save(n, dict(schema="bcsp-fcsp-p4-runtime-v1", request_sha256=rh, authorization_sha256=ah))
        save(c, dict(status="CLAIMED_BEFORE_TMUX", request_sha256=rh))
        args = Namespace(request=r, request_sha256=rh, authorization=a, authorization_sha256=ah,
                         runtime=n, runtime_sha256=nh)
        self.assertEqual(p4.authorize(args), req)
        save(c, dict(status="CLAIMED_BEFORE_TMUX", request_sha256="bad"))
        with self.assertRaisesRegex(ValueError, "single attempt"):
            p4.authorize(args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
