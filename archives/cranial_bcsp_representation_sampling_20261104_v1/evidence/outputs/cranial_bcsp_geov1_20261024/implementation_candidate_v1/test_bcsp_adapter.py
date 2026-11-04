"""Synthetic CPU contracts only. No real dataset/model imports."""
import ast, json, tempfile, unittest, importlib.util
from pathlib import Path
import numpy as np
import bcsp_adapter as a

class KnnTests(unittest.TestCase):
    def setUp(self):
        r=np.random.default_rng(20261024);self.x=r.normal(size=(2,37,3));self.q=r.normal(size=(2,19,3))
    def test_chunks(self):
        expected=np.argsort(np.sum((self.q[:,:,None,:]-self.x[:,None,:,:])**2,axis=-1),axis=-1)[...,:7]
        for chunk in (1,8,19,256):np.testing.assert_array_equal(a.numpy_knn(7,self.x,self.q,chunk),expected)
    def test_self(self):
        np.testing.assert_array_equal(a.numpy_knn(1,self.x,self.x)[...,0],np.tile(np.arange(37),(2,1)))
    def test_ties(self):
        x=np.zeros((1,8,3));np.testing.assert_array_equal(a.numpy_knn(3,x,x),np.tile(np.arange(3),(1,8,1)))
    def test_empty_query(self):self.assertEqual(a.numpy_knn(2,self.x,self.q[:,:0]).shape,(2,0,2))
    def test_bad_k(self):
        for k in (0,38,True):
            with self.assertRaises(ValueError):a.numpy_knn(k,self.x,self.q)
    def test_bad_chunk(self):
        with self.assertRaises(ValueError):a.numpy_knn(1,self.x,self.q,0)
    def test_nonfinite(self):
        x=self.x.copy();x[0,0,0]=np.nan
        with self.assertRaises(ValueError):a.numpy_knn(1,x,self.q)
    def test_dtype(self):
        with self.assertRaises(ValueError):a.numpy_knn(1,self.x.astype('f4'),self.q)
    def test_shape(self):
        with self.assertRaises(ValueError):a.numpy_knn(1,self.x,self.q[:1])
    def test_float32(self):self.assertEqual(a.numpy_knn(3,self.x.astype('f4'),self.q.astype('f4'),8).shape,(2,19,3))
    def test_legacy_scope(self):
        marker=object();self.assertIs(a.knn_dispatch(lambda *args:marker,1,None,None),marker)
        with self.assertRaises(RuntimeError):
            with a.bcsp_knn_scope():raise RuntimeError('synthetic')
        self.assertFalse(a._ACTIVE.get())
    @unittest.skipUnless(importlib.util.find_spec('torch'),'PyTorch absent: actual tensor path NOT VERIFIED')
    def test_torch_cpu(self):
        import torch
        x=torch.tensor(self.x);q=torch.tensor(self.q)
        old=torch.topk(torch.sum((q[:,:,None]-x[:,None])**2,dim=-1),7,dim=-1,largest=False,sorted=False)[1]
        got=a.torch_knn(7,x,q,8)
        np.testing.assert_array_equal(np.sort(got.numpy(),axis=-1),np.sort(old.numpy(),axis=-1))

class DataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bcsp_artificial_');self.root=Path(self.tmp.name)
        self.partial=np.zeros((8192,3),np.float32);self.target=np.ones((8192,3),np.float32)
        np.savez(self.root/'case.npz',partial=self.partial,implant=self.target)
        self.r={'source_id':'synthetic','point_path':'case.npz','schema':'BCSP-normalized-v1','normalization_source':'defective_bbox','sha256':a.sha256(self.root/'case.npz')}
    def tearDown(self):self.tmp.cleanup()
    def test_training(self):
        x,y=a.load_case(self.root,self.r,{'synthetic'},8192,True);np.testing.assert_array_equal(y,self.target)
    def test_inference(self):self.assertIsNone(a.load_case(self.root,self.r,{'synthetic'},8192)[1])
    def test_gt_replacement(self):
        x,_=a.load_case(self.root,self.r,{'synthetic'},8192)
        np.savez(self.root/'case.npz',partial=self.partial,implant=np.full_like(self.target,np.nan))
        self.r['sha256']=a.sha256(self.root/'case.npz')
        y,_=a.load_case(self.root,self.r,{'synthetic'},8192);np.testing.assert_array_equal(x,y)
        with self.assertRaises(ValueError):a.load_case(self.root,self.r,{'synthetic'},8192,True)
    def test_source_exclusion(self):
        with self.assertRaises(ValueError):a.load_case(self.root,self.r,set(),8192)
    def test_hash(self):
        self.r['sha256']='0'*64
        with self.assertRaises(ValueError):a.load_case(self.root,self.r,{'synthetic'},8192)
    def test_escape(self):
        self.r['point_path']='../outside.npz'
        with self.assertRaises(ValueError):a.load_case(self.root,self.r,{'synthetic'},8192)
    def test_frame(self):
        self.r['normalization_source']='complete_skull'
        with self.assertRaises(ValueError):a.load_case(self.root,self.r,{'synthetic'},8192)
    def test_input_count(self):
        with self.assertRaises(ValueError):a.load_case(self.root,self.r,{'synthetic'},16384)

class CounterTests(unittest.TestCase):
    def test_full_3900(self):
        g=a.UpdateGuard()
        class Optimizer:
            def __init__(self):self.n=0
            def zero_grad(self):pass
            def step(self):self.n+=1
        opt=Optimizer();loader=[(range(8),range(8))]*39
        for epoch in range(100):a.run_epoch(loader,epoch,opt,lambda x,y:None,g)
        self.assertEqual(opt.n,3900);self.assertEqual(g.finish()['case_exposures'],31200)
        with self.assertRaises(RuntimeError):g.begin_epoch(100,39)
    def test_wrong_epoch(self):
        with self.assertRaises(RuntimeError):a.UpdateGuard().begin_epoch(1,39)
    def test_wrong_batches(self):
        with self.assertRaises(RuntimeError):a.UpdateGuard().begin_epoch(0,40)
    def test_wrong_batch(self):
        g=a.UpdateGuard();g.begin_epoch(0,39)
        with self.assertRaises(RuntimeError):g.before_step(7)
    def test_pending(self):
        g=a.UpdateGuard();g.begin_epoch(0,39);g.before_step(8)
        with self.assertRaises(RuntimeError):g.before_step(8)
    def test_early_end(self):
        g=a.UpdateGuard();g.begin_epoch(0,39)
        with self.assertRaises(RuntimeError):g.end_epoch()
    def test_no_commit_without_step(self):
        with self.assertRaises(RuntimeError):a.UpdateGuard().after_step()
    def test_latched_failure(self):
        g=a.UpdateGuard();g.abort()
        with self.assertRaises(RuntimeError):g.begin_epoch(0,39)
    def test_old_contract_rejected(self):
        with self.assertRaises(ValueError):a.Contract(epochs=101)
    def test_incomplete_finish(self):
        with self.assertRaises(RuntimeError):a.UpdateGuard().finish()
    def test_failed_callback_no_step(self):
        class O:
            def zero_grad(self):pass
            def step(self):raise AssertionError('optimizer must not run')
        def fail(*args):raise ValueError('synthetic gradient failure')
        g=a.UpdateGuard()
        with self.assertRaises(ValueError):a.run_epoch([(range(8),range(8))]*39,0,O(),fail,g)
        self.assertTrue(g.failed);self.assertEqual(g.steps,0);self.assertFalse(a._ACTIVE.get())

if __name__=='__main__':
    import io
    out=Path(__file__).parent/'cpu_tests_v1'
    out.mkdir(exist_ok=False)
    for p in Path(__file__).parent.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
    stream=io.StringIO();res=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)))
    (out/'stdout.txt').write_text(stream.getvalue(),encoding='utf8')
    summary={'tests_run':res.testsRun,'failures':len(res.failures),'errors':len(res.errors),'skipped':[(str(t),why) for t,why in res.skipped],'status':'PASS_AVAILABLE_CPU_CONTRACTS_TORCH_UNVERIFIED' if res.wasSuccessful() else 'FAILED_STOP','model_calls':0,'GPU_calls':0,'real_data_access':0}
    (out/'result.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(stream.getvalue());print(json.dumps(summary))
    raise SystemExit(0 if res.wasSuccessful() else 1)
