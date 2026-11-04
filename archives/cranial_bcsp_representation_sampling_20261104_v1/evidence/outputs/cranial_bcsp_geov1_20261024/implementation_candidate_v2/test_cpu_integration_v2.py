"""One-shot synthetic CPU tensor validation, no real models or data."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'
import ast
import io
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
import torch
import bcsp_cpu_entry_v2 as entry

torch.set_num_threads(2)
a = entry.load_adapter()

class TensorTests(unittest.TestCase):
    def setUp(self):
        g = torch.Generator().manual_seed(20261024)
        self.x = torch.randn((2, 37, 3), dtype=torch.float64, generator=g)
        self.q = torch.randn((2, 19, 3), dtype=torch.float64, generator=g)
        self.old, self.distance = entry.parent_knn_pair()
    def test_parent_random_sets(self):
        for dtype in (torch.float32, torch.float64):
            x, q = self.x.to(dtype), self.q.to(dtype)
            expected = self.old(7, x, q).sort(dim=-1)[0]
            for chunk in (1, 8, 19, 256):
                got = entry.candidate_knn(7, x, q, chunk).sort(dim=-1)[0]
                torch.testing.assert_close(got, expected, rtol=0, atol=0)
    def test_duplicate_tie_validity(self):
        x = torch.zeros((1, 9, 3)); q = torch.zeros((1, 3, 3))
        got = entry.candidate_knn(4, x, q, 2)
        self.assertEqual(tuple(got.shape), (1, 3, 4))
        for row in got.reshape(-1, 4):
            self.assertEqual(len(set(row.tolist())), 4)
        self.assertTrue(torch.all(self.distance(q, x).gather(2, got) == 0).item())
    def test_equidistant_validity(self):
        x = torch.tensor([[[1.,0,0],[-1.,0,0],[0,1.,0],[0,-1.,0],[4.,0,0]]])
        got = entry.candidate_knn(3, x, torch.zeros((1, 1, 3)), 1)
        self.assertTrue(torch.all(got < 4).item())
    def test_self_neighbor(self):
        got = entry.candidate_knn(1, self.x, self.x, 8)
        torch.testing.assert_close(got[..., 0], torch.arange(37).repeat(2, 1))
    def test_empty_query(self):
        self.assertEqual(tuple(entry.candidate_knn(2, self.x, self.q[:, :0]).shape), (2, 0, 2))
    def test_noncontiguous(self):
        x, q = self.x[:, ::2], self.q[:, ::2]
        torch.testing.assert_close(entry.candidate_knn(4,x,q,3).sort(-1)[0], self.old(4,x,q).sort(-1)[0])
    def test_invalid_k_chunk(self):
        for k, chunk in ((0,256),(38,256),(True,256),(1,0)):
            with self.assertRaises(ValueError): entry.candidate_knn(k,self.x,self.q,chunk)
    def test_nonfinite(self):
        for value in (float('nan'), float('inf')):
            q = self.q.clone(); q[0,0,0] = value
            with self.assertRaises(ValueError): entry.candidate_knn(1,self.x,q)
    def test_dtype_shape(self):
        for x, q in ((self.x.float(),self.q),(self.x.long(),self.q.long()),(self.x[:1],self.q),(self.x[0],self.q)):
            with self.assertRaises(ValueError): entry.candidate_knn(1,x,q)
    def test_no_gradient_graph(self):
        got = entry.candidate_knn(2,self.x.requires_grad_(),self.q.requires_grad_())
        self.assertFalse(got.requires_grad)
        self.assertIsNone(self.x.grad)
    def test_16k_chunk_bound(self):
        g = torch.Generator().manual_seed(19)
        x = torch.randn((1,16384,3),generator=g)
        q = torch.randn((1,257,3),generator=g)
        original = torch.matmul; sizes = []
        def observed(left,right):
            sizes.append(tuple(left.shape)); return original(left,right)
        with patch('torch.matmul',side_effect=observed): got = entry.candidate_knn(16,x,q)
        self.assertEqual(sizes,[(1,256,3),(1,1,3)])
        # Dense parent oracle is bounded to 257 query points, not a 16k-square matrix.
        torch.testing.assert_close(got.sort(-1)[0],self.old(16,x,q).sort(-1)[0])
    def test_parent_and_adapter_drift_rejected(self):
        with patch.object(entry,'V1_SHA','0'*64):
            with self.assertRaises(RuntimeError): entry.load_adapter()
        with patch.object(entry,'PARENT_SHA','0'*64):
            with self.assertRaises(RuntimeError): entry.parent_knn_pair()

class CountingOptimizer:
    def __init__(self): self.steps=0; self.zero_calls=0
    def zero_grad(self): self.zero_calls+=1
    def step(self): self.steps+=1

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='bcsp_cpu_v2_artificial_')
        self.root = Path(self.tmp.name)
        self.partial = np.arange(16384*3,dtype=np.float32).reshape(16384,3)/10000
        np.savez(self.root/'synthetic.npz', partial=self.partial, implant=np.ones((8192,3),np.float32))
        self.base = {'source_id':'synthetic-only','point_path':'synthetic.npz',
                     'schema':'BCSP-normalized-v1','normalization_source':'defective_bbox',
                     'sha256':a.sha256(self.root/'synthetic.npz')}
        self.records = [dict(self.base,case_id='synthetic_%03d'%i) for i in range(315)]
    def tearDown(self): self.tmp.cleanup()
    def dataset(self, records=None, training=True):
        return entry.BCSPDataset(self.root,self.records if records is None else records,
                                 {'synthetic-only'},16384,training)
    def test_tensor_dataset(self):
        x,y = self.dataset()[0]
        self.assertEqual(tuple(x.shape),(16384,3)); self.assertEqual(tuple(y.shape),(8192,3))
        self.assertEqual(x.dtype,torch.float32);self.assertEqual(x.device.type,'cpu')
    def test_inference_has_no_gt(self):
        np.savez(self.root/'synthetic.npz',partial=self.partial)
        self.records[0]['sha256']=a.sha256(self.root/'synthetic.npz')
        self.assertEqual(tuple(self.dataset(records=self.records[:1],training=False)[0].shape),(16384,3))
    def test_duplicate_cases_rejected(self):
        with self.assertRaises(ValueError): self.dataset(records=[self.records[0],self.records[0]])
    def test_source_rejected_before_payload(self):
        bad = dict(self.records[0],source_id='sealed',point_path='absent.npz')
        with self.assertRaises(ValueError): self.dataset(records=[bad])
    def test_full_loader_epoch_knn_and_counter(self):
        ds=self.dataset(); opt=CountingOptimizer(); guard=a.UpdateGuard(); calls=[]
        def callback(x,y):
            self.assertEqual(tuple(x.shape),(8,16384,3));self.assertEqual(tuple(y.shape),(8,8192,3))
            if not calls:
                got=entry.candidate_knn(16,x,x[:,:2],1)
                self.assertEqual(tuple(got.shape),(8,2,16))
            calls.append(1)
        entry.run_cpu_epoch(ds,0,opt,callback,guard)
        self.assertEqual((opt.steps,opt.zero_calls,len(calls),guard.steps),(39,39,39,39))
        # Remaining traversals exercise commit protocol without rereading fixture thousands of times.
        for e in range(1,100): a.run_epoch([(range(8),range(8))]*39,e,opt,lambda x,y:None,guard)
        final=entry.finish_cpu_contract(guard)
        self.assertEqual((opt.steps,final['optimizer_updates'],final['case_exposures']),(3900,3900,31200))
    def test_loader_rejects_wrong_count(self):
        with self.assertRaises(ValueError): entry.build_cpu_loader(self.dataset(records=self.records[:-1]),0)
    def test_loader_rejects_inference(self):
        with self.assertRaises(ValueError): entry.build_cpu_loader(self.dataset(training=False),0)
    def test_epoch_seed_bound(self):
        for e in (-1,100):
            with self.assertRaises(ValueError): entry.build_cpu_loader(self.dataset(),e)
        with self.assertRaises(ValueError): entry.build_cpu_loader(self.dataset(),0,seed=1)
    def test_shuffle_reproducibility(self):
        ds=self.dataset()
        first=list(iter(entry.build_cpu_loader(ds,0).sampler))
        second=list(iter(entry.build_cpu_loader(ds,0).sampler))
        self.assertEqual(first,second)
        self.assertEqual(len(set(first)),315)
    def test_callback_failure_stops_optimizer(self):
        opt=CountingOptimizer(); guard=a.UpdateGuard()
        def fail(*args): raise RuntimeError('artificial failure')
        with self.assertRaises(RuntimeError): entry.run_cpu_epoch(self.dataset(),0,opt,fail,guard)
        self.assertEqual(opt.steps,0);self.assertTrue(guard.failed)

def run_once():
    out = Path(__file__).parent/'cpu_tensor_results_v2'
    out.mkdir(exist_ok=False)
    started=time.monotonic()
    for path in Path(__file__).parent.glob('*.py'): ast.parse(path.read_text(encoding='utf8'))
    # Include all previous 31 tests without running their old __main__ writer.
    sys.modules['bcsp_adapter']=a
    spec=importlib.util.spec_from_file_location('bcsp_previous_tests',entry.V1.parent/'test_bcsp_adapter.py')
    previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(previous),
                             unittest.defaultTestLoader.loadTestsFromTestCase(TensorTests),
                             unittest.defaultTestLoader.loadTestsFromTestCase(IntegrationTests)])
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(suite)
    summary={'status':'PASS_CPU_TENSOR_AND_MINIMAL_CHAIN' if result.wasSuccessful() and not result.skipped else 'FAILED_OR_INCOMPLETE_STOP',
             'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'skipped':[(str(t),why) for t,why in result.skipped], 'seconds':time.monotonic()-started,
             'python':sys.executable,'python_version':sys.version,'torch':torch.__version__,'numpy':np.__version__,
             'cuda_initialized':torch.cuda.is_initialized(),'real_model_calls':0,'real_data_access':0,
             'real_optimizer_updates':0,'synthetic_counter_commits':3900 if result.wasSuccessful() else None,
             'limitations':['CPU-only validation; no CUDA equivalence or VRAM certification',
                            'Only one real synthetic DataLoader traversal; remaining traversals use counter-only batches',
                            'No full production runner, NN forward, scheduler, loss/clip or checkpoint integration',
                            'Legacy registry not changed; BCSPDataset explicit candidate API only']}
    (out/'stdout.txt').write_text(stream.getvalue(),encoding='utf8')
    (out/'result.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(stream.getvalue());print(json.dumps(summary))
    return 0 if summary['status']=='PASS_CPU_TENSOR_AND_MINIMAL_CHAIN' else 1

if __name__=='__main__': raise SystemExit(run_once())
