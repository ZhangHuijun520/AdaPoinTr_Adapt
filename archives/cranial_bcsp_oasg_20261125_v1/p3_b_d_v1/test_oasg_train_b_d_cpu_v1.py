"""CPU-only authorization, metadata and lifecycle handoff for the first B run."""

import ast
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import oasg_train_b_d_v1 as worker


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "p1_implementation_v1"))
import bcsp_oasg_entry_v1 as entry


def read(path):
    return json.loads(path.read_bytes())


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        draft = read(HERE.parent / "P3_B_D_training_request_preparation_v1.json")
        meta = {}
        for key in ("fold", "point_manifest", "order"):
            ref = draft["local_reference_bindings"][key]
            raw = (PROJECT / ref["path"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == ref["sha256"]
            meta[key] = raw
        cls.fold = json.loads(meta["fold"])
        cls.manifest = [json.loads(x) for x in meta["point_manifest"].splitlines()]
        cls.order = json.loads(meta["order"])
        cls.p2 = read(HERE.parent / "P2_formal_post_CUDA_freeze_receipt_v1.json")
        cls.q = dict(schema="bcsp-oasg-p3-b-d-train-v1", status="AWAITING_EXPLICIT_USER_AUTHORIZATION",
                     execution_authorized=False, run=worker.RUN, counts=worker.COUNTS,
                     order=dict(sha256=worker.ORDER_SHA), p2_receipt=dict(sha256=worker.P2_SHA),
                     boundary=dict(retry=False, resume=False, development=False, BNCal=False),
                     identity=cls.p2["identity"], shared_initial_state_sha256=cls.p2["gradient_checks"]["shared"],
                     data_root="/synthetic_only", output="/synthetic_only/out")

    def test_one_way_auth_and_reject_arm_or_count_drift(self):
        r, a = "1"*64, "2"*64
        auth = dict(schema="bcsp-oasg-p3-b-d-authorization-v1", request_sha256=r,
                    explicit_user_authorization=True, user_authorization_text="artificial fixture")
        runtime = dict(schema="bcsp-oasg-p3-b-d-runtime-v1", request_sha256=r, authorization_sha256=a)
        worker.authorize(self.q, r, auth, a, runtime)
        for q in ({**self.q, "run": {**worker.RUN, "variant": "A"}},
                  {**self.q, "counts": {**worker.COUNTS, "updates": 3899}},
                  {**self.q, "execution_authorized": True}):
            with self.assertRaises(ValueError):
                worker.authorize(q,r,auth,a,runtime)
        with self.assertRaisesRegex(ValueError,"authorization"):
            worker.authorize(self.q,r,{**auth,"explicit_user_authorization":False},a,runtime)
        with self.assertRaisesRegex(ValueError,"runtime"):
            worker.authorize(self.q,r,auth,a,{**runtime,"authorization_sha256":"3"*64})

    def test_actual_metadata_and_epoch_rejects_case_drift(self):
        rows, sources = worker.select_training(self.fold,self.manifest,self.order)
        self.assertEqual((len(rows),len(sources)),(315,63))
        self.assertEqual([r["case_id"] for r in rows],self.order["case_ids"])
        epochs = list(self.order["epochs"])
        first = dict(epochs[0])
        first["batches"] = [first["batches"][1],*first["batches"][1:]]
        epochs[0] = first
        with self.assertRaisesRegex(ValueError,"complete Fold D epoch"):
            worker.select_training(self.fold,self.manifest,{**self.order,"epochs":epochs})

    def test_p2_requires_same_device_and_restoration(self):
        worker.check_admission(self.p2,self.q)
        with self.assertRaisesRegex(ValueError,"same-device"):
            worker.check_admission(self.p2,{**self.q,"identity":{**self.q["identity"],"gpu_uuid":"different"}})
        with self.assertRaisesRegex(ValueError,"same-device"):
            worker.check_admission({**self.p2,"gradient_checks":{**self.p2["gradient_checks"],"restoration":False}},self.q)

    def test_exclusive_output_members_and_pid(self):
        d=OUT/"layout_fixture"
        d.mkdir()
        for n in ("worker.pid","launcher.pid","launch.log","model_construction.json","p3_resources.jsonl"):
            (d/n).write_text(str(os.getpid()) if n=="worker.pid" else "",encoding="ascii")
        for n in ("tmp","cache","mplconfig","triton","hf"):
            (d/n).mkdir()
        self.assertEqual(worker.claim_owned_training_output(d),d)
        (d/"ckpt-last.pth").touch()
        with self.assertRaisesRegex(ValueError,"fresh"):
            worker.claim_owned_training_output(d)

    def test_parent_lifecycle_adapter_and_dispatch_without_optimizer(self):
        path=PROJECT/"outputs/scq_prime_entry_20261121_v1/bcsp_scq_prime_runtime_v1.py"
        tree=ast.parse(path.read_bytes(),str(path))
        [node]=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="train_lifecycle"]
        observed=[]
        class Handoff(Exception):
            pass
        def order_check(plan,ids):
            observed.append((plan,ids))
            raise Handoff
        ns={"require":worker.need,"validate_order":order_check}
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),"exec"),ns)
        @contextmanager
        def observe(model,run,res,emit):
            self.assertEqual(run,worker.RUN)
            yield res
        runtime=SimpleNamespace(train_lifecycle=ns["train_lifecycle"],
                                BCSPDataset=lambda root,rows,sources,n: self.assertEqual(n,8192))
        wrapper=SimpleNamespace(bind_training_lifecycle=entry.bind_training_lifecycle,observe_training=observe)
        evidence=dict(artificial_fixture=False,run_identity=worker.RUN,initializer_sha256=None,
                      historical_B_initial_state_SHA256=worker.HISTORICAL_B,
                      shared_initial_state_SHA256=self.q["shared_initial_state_sha256"])
        helper=SimpleNamespace(assert_numeric=None,state_sha=None)
        args=(self.q,object(),evidence,wrapper,runtime,[{"case_id":"stub"}],[],self.order,None,helper,None,None)
        with self.assertRaisesRegex(ValueError,"native B"):
            worker.dispatch(*args,"cpu")
        with self.assertRaises(Handoff):
            worker.dispatch(*args,"cuda:0")
        self.assertEqual(observed,[(self.order,["stub"])])
        self.assertNotIn("claim_output",ns)


if __name__ == "__main__":
    OUT=Path(sys.argv[1]).resolve()
    OUT.mkdir()
    outcome=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    with (OUT/"result_v1.json").open("x",encoding="ascii") as f:
        json.dump(dict(tests=outcome.testsRun,failures=len(outcome.failures),errors=len(outcome.errors),
                       passed=outcome.wasSuccessful(),actual_training_reads=0,cuda_calls=0,
                       optimizer_steps=0,model_forward=0),f)
    sys.exit(0 if outcome.wasSuccessful() else 1)
