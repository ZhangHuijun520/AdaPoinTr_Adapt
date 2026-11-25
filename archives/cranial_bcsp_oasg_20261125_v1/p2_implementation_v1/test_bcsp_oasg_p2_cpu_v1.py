"""Artificial CPU contracts for the P2 short entry."""

import json
from pathlib import Path
import random
import sys
import unittest

import numpy as np
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "p1_implementation_v1"))
import bcsp_oasg_p2_cuda_v1 as entry


class Seed(nn.Module):
    def __init__(self, arm):
        super().__init__()
        self.arm = arm
        self.proj = nn.Linear(3, 3)

    def forward(self, z, memory, anchors):
        delta = self.proj(memory)
        return (anchors + delta, delta) if self.arm == "A" else delta


class Decoder(nn.Module):
    def forward(self, *, q, q_pos, v_pos):
        return q


class Dense(nn.Linear):
    def forward(self, features):
        return super().forward(features).unsqueeze(2).expand(-1, -1, 32, -1)


class Fixture(nn.Module):
    def __init__(self, arm, fault=None):
        super().__init__()
        self.arm, self.fault = arm, fault
        self.base_model = nn.Module()
        self.base_model.coarse_pred = Seed(arm)
        self.base_model.encoder = nn.Sequential(nn.Linear(3, 3), nn.BatchNorm1d(3))
        self.base_model.mlp_query = nn.Identity()
        self.base_model.decoder = Decoder()
        self.reduce_map = nn.Linear(3, 3)
        self.decode_head = Dense(3, 3)
        self.eval()
        self.base_model.encoder[1].train()
        self.base_model.encoder[1].momentum = .37
        for p in self.parameters():
            p.grad = torch.full_like(p, 2.)

    def forward(self, x):
        random.random()
        np.random.rand()
        torch.rand(1)
        b = self.base_model
        anchors = x[:, :256]
        memory = b.encoder(anchors.reshape(-1, 3)).reshape(8, 256, 3)
        seed = b.coarse_pred(memory.mean(1), memory, anchors)
        q = seed[0] if self.arm == "A" else seed
        embedded = b.mlp_query(q)
        b.decoder(q=embedded, q_pos=q, v_pos=anchors)
        features = self.reduce_map(q + 1 if self.fault == "coordinate" else q)
        dense = (q.unsqueeze(2) + self.decode_head(features)).reshape(8, 8192, 3)
        return q, q[:, :0], dense[:, :0], dense

    def get_loss(self, outputs, target, epoch, partial):
        if self.fault == "loss":
            raise RuntimeError("fixture loss failure")
        q, dense = outputs[0], outputs[3]
        loss = (q - target[:, :256]).square().mean() + (dense - target).square().mean()
        if self.fault == "backward":
            def fail(_):
                raise RuntimeError("fixture backward failure")
            loss.register_hook(fail)
        return loss.new_zeros(()), loss


class Contract(unittest.TestCase):
    def setUp(self):
        rng = torch.Generator().manual_seed(102)
        self.batch = tuple(torch.randn(8,8192,3,generator=rng) for _ in range(2))
        self.events, self.models = [], []

    def invoke(self, fault=None, fault_arm="B"):
        def build(run):
            model = Fixture(run["variant"], fault if run["variant"] == fault_arm else None)
            self.models.append(model)
            shared = "different" if run["variant"] == "A" and fault == "common" else "same"
            return model, dict(run_identity=run, shared_initial_state_SHA256=shared)
        return entry._run(self.batch, build, torch.device("cpu"), self.events.append, lambda *_: None, 0)

    def test_exact_counts_and_same_arm_order(self):
        self.assertEqual(self.invoke(), entry.LIMITS)
        self.assertEqual([(x["arm"],x["operation"]) for x in self.events if x["kind"]=="call"],
                         [(a,op) for a in entry.ARMS for op in ("forward","loss","backward")])
        rows = [x for x in self.events if x["kind"] == "arm_result"]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["coordinates_valid"] and r["changed_bn_buffers"] and r["peak_bytes"] is None for r in rows))

    def test_gradient_bn_modes_and_rng_restore(self):
        saved = entry.rng_digest(entry.rng(torch.device("cpu")))
        self.invoke()
        self.assertEqual(entry.rng_digest(entry.rng(torch.device("cpu"))), saved)
        restored = [x for x in self.events if x["kind"] == "restoration"]
        self.assertEqual(len(restored), 2)
        self.assertTrue(all(all(x["checks"].values()) for x in restored))
        for model in self.models:
            self.assertFalse(model.training)
            self.assertTrue(model.base_model.encoder[1].training)
            self.assertEqual(model.base_model.encoder[1].momentum, .37)
            self.assertEqual(int(model.base_model.encoder[1].num_batches_tracked), 0)
            self.assertTrue(all(torch.all(p.grad == 2) for p in model.parameters()))
            self.assertTrue(all(not m._forward_hooks and not m._forward_pre_hooks for m in model.modules()))

    def test_coordinate_loss_and_backward_fail_stop(self):
        for fault, message, limit in (("coordinate","coarse consumer mismatch",(1,0,0)),
                                      ("loss","fixture loss failure",(1,1,0)),
                                      ("backward","fixture backward failure",(1,1,1))):
            with self.subTest(fault=fault):
                self.events.clear()
                self.models.clear()
                with self.assertRaisesRegex((RuntimeError,ValueError), message):
                    self.invoke(fault)
                self.assertEqual(len(self.models),1)
                failure = next(x for x in self.events if x["kind"]=="failure")
                self.assertEqual(tuple(failure["counts"][k] for k in ("forward","loss","backward")),limit)
                self.assertEqual(failure["counts"]["optimizer_step"],0)
                self.assertTrue(all(next(x for x in self.events if x["kind"]=="restoration")["checks"].values()))

    def test_common_init_mismatch_precedes_second_forward(self):
        with self.assertRaisesRegex(ValueError,"common initialization"):
            self.invoke("common")
        self.assertEqual([x["arm"] for x in self.events if x["kind"]=="call"], ["B"]*3)

    def test_bad_batch_stops_before_construction(self):
        self.batch = tuple(t[:7] for t in self.batch)
        with self.assertRaisesRegex(ValueError,"shared first batch"):
            self.invoke()
        self.assertFalse(self.models)
        self.assertFalse(any(x["kind"]=="call" for x in self.events))


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir()
    torch.set_num_threads(2)
    test = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    with (out / "cpu_result_v1.json").open("x", encoding="utf-8") as f:
        json.dump(dict(passed=test.wasSuccessful(), tests=test.testsRun, failures=len(test.failures),
                       errors=len(test.errors), device="cpu", torch_version=torch.__version__,
                       artificial=True, optimizer_steps=0, native_mamba_forward=0), f, indent=2)
        f.write("\n")
    sys.exit(0 if test.wasSuccessful() else 1)
