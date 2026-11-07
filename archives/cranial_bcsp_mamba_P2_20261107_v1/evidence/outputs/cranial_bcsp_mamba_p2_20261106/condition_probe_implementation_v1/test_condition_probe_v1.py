import importlib.util,json,time,unittest,hashlib,os,sys
from pathlib import Path
import numpy as np
import torch
S=Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,S/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('condition_probe_core_v1');p=module('coarse_prefix_capture_v1')
torch.set_num_threads(2)
class Toy(torch.nn.Module):
    def __init__(self):
        super().__init__();self.base_model=torch.nn.Module();self.base_model.coarse_pred=torch.nn.Linear(1024,768);self.tail=0;self.fail=False
    def forward(self,x):
        if self.fail:raise RuntimeError('upstream actual failure')
        z=x.mean(1).repeat(1,342)[:,:1024];q=self.base_model.coarse_pred(z)
        self.tail+=1;raise RuntimeError('decoder must not execute')
def data():
    train=[];dev=[]
    for i in range(84):
        for j,d in enumerate(['bilateral','frontoorbital','parietotemporal','random_1','random_2']):
            v=np.sin(np.arange(18)+i+j);r=dict(case_id=f'train__{i:03d}__{d}',source_id=f'train:{i:03d}',fold='C',variant='M0',target4=np.r_[v[:3],v[3]/10],coarse4=np.r_[v[:3]+.2,v[3]/10+.1],geometry18=v,feature1024=np.resize(v,1024),scale=100.)
            (train if i<63 else dev).append(r)
    return train,dev
class Tests(unittest.TestCase):
    def test01_moments(self):np.testing.assert_allclose(c.moments([[-1,0,0],[1,0,0]]),[0,0,0,0])
    def test02_zero_radius_rejected(self):
        with self.assertRaises(ValueError):c.moments([[0,0,0]])
    def test03_geometry_exact(self):
        g=c.geometry18([[-1,0,0],[1,0,0]]);self.assertEqual(g.shape,(18,));np.testing.assert_allclose(g[:9],[0,0,0,1,0,0,0,0,0]);np.testing.assert_allclose(g[9:12],[-.8,0,.8])
    def test04_equal_sources(self):np.testing.assert_allclose(c.source_weights(['a','a','b']),[.25,.25,.5])
    def test05_exact_mean_lambda(self):
        x=np.array([[-1.],[1.]]);y=np.tile(x,(1,4));fit=c.fit_ridge(x,y,['a','b']);np.testing.assert_allclose(fit['coefficient'],.5);np.testing.assert_allclose(c.predict(fit,x),y*.5)
    def test06_constant_columns(self):
        f=c.fit_ridge(np.ones((3,2)),np.ones((3,4)),['a','b','c']);np.testing.assert_allclose(c.predict(f,[[99,12]]),1)
    def test07_error_units(self):np.testing.assert_allclose(c.errors([[1,0,0,np.log(2)]],[[0,0,0,0]],[10]),[[10,1,np.log(2)]])
    def test08_nonfinite_rejected(self):
        with self.assertRaises(ValueError):c.geometry18([[np.nan,0,0]])
    def test09_prefix_shapes_and_no_tail(self):
        m=Toy().eval();r=p.capture_prefix(torch,m,torch.ones(1,8192,3));self.assertEqual(tuple(r['feature1024'].shape),(1,1024));self.assertEqual(tuple(r['coarse'].shape),(1,256,3));self.assertEqual(m.tail,0);self.assertFalse(r['coarse'].requires_grad);self.assertFalse(m.base_model.coarse_pred._forward_hooks)
    def test10_prefix_exact_head(self):
        m=Toy().eval();x=torch.ones(1,8192,3);expected=m.base_model.coarse_pred(x.mean(1).repeat(1,342)[:,:1024]).reshape(1,256,3);r=p.capture_prefix(torch,m,x);torch.testing.assert_close(r['coarse'],expected,rtol=0,atol=0)
    def test11_upstream_error_and_cleanup(self):
        m=Toy().eval();m.fail=True
        with self.assertRaisesRegex(RuntimeError,'actual failure'):p.capture_prefix(torch,m,torch.ones(1,8192,3))
        self.assertFalse(m.base_model.coarse_pred._forward_hooks);self.assertFalse(m.base_model.coarse_pred._forward_pre_hooks)
    def test12_eval_required(self):
        with self.assertRaises(ValueError):p.capture_prefix(torch,Toy(),torch.ones(1,8192,3))
    def test13_state_rng_unchanged(self):
        m=Toy().eval();before={k:v.clone() for k,v in m.state_dict().items()};rng=torch.random.get_rng_state().clone();p.capture_prefix(torch,m,torch.ones(1,8192,3));self.assertTrue(torch.equal(rng,torch.random.get_rng_state()));self.assertTrue(all(torch.equal(v,m.state_dict()[k]) for k,v in before.items()))
    def test14_foreign_hooks_rejected(self):
        m=Toy().eval();h=m.base_model.coarse_pred.register_forward_hook(lambda *args:None)
        try:
            with self.assertRaises(ValueError):p.capture_prefix(torch,m,torch.ones(1,8192,3))
        finally:h.remove()
    def test15_partial_contract(self):
        with self.assertRaises(ValueError):p.capture_prefix(torch,Toy().eval(),torch.ones(1,8,3))
    def test16_actual_full_reader_and_no_dev_fit(self):
        a,b=data();r=c.compare(a,b);self.assertEqual(set(r['predictions']),{'constant','coarse','geometry18','feature1024'});self.assertEqual(len(r['source_errors']['feature1024']),21);self.assertEqual(r['case_errors']['coarse'].shape,(105,3));self.assertFalse(r['development_fitted']);self.assertEqual(r['model_updates'],0)
        y=np.array([row['target4'] for row in a]);np.testing.assert_allclose(r['fits']['feature1024']['y_mean'],y.mean(0),atol=1e-14)
        # Poisoned development targets cannot affect coefficients: predict has no target input.
        old=r['predictions']['feature1024'].copy()
        for row in b:row['target4']=np.ones(4)*1000
        np.testing.assert_array_equal(c.predict(r['fits']['feature1024'],[row['feature1024'] for row in b]),old)
    def test17_source_leak_rejected(self):
        a,b=data();b[0]['source_id']=a[0]['source_id']
        with self.assertRaises(ValueError):c.compare(a,b)
    def test18_mixed_model_rejected(self):
        a,b=data();b[0]['variant']='T0'
        with self.assertRaises(ValueError):c.compare(a,b)
    def test19_missing_case_rejected(self):
        a,b=data()
        with self.assertRaises(ValueError):c.compare(a,b[:-1])
    def test20_dual_matches_primal(self):
        x=np.arange(30,dtype=float).reshape(5,6);y=np.arange(20,dtype=float).reshape(5,4);fit=c.fit_ridge(x,y,list('abcde'));X=(x-x.mean(0))/x.std(0);Y=(y-y.mean(0))/y.std(0);expected=np.linalg.solve(X.T@X/5+np.eye(6),X.T@Y/5);np.testing.assert_allclose(fit['coefficient'],expected,atol=1e-14)
if __name__=='__main__':
    out=S/'artificial_cpu_batch_v1';out.mkdir();start=time.monotonic()
    with (out/'stdout_v1.txt').open('x',encoding='utf-8') as stream:
        run=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    result=dict(status='ARTIFICIAL_CPU_CONTRACT_PASS' if run.wasSuccessful() else 'FAILED_STOP_NO_RETRY',tests=run.testsRun,failures=len(run.failures),errors=len(run.errors),seconds=time.monotonic()-start,python=sys.executable,torch=torch.__version__,numpy=np.__version__,CUDA_calls=0,real_data_rows=0,real_model_imports=0,real_forward_calls=0,artificial_orchestrated_training_rows=315,artificial_orchestrated_development_rows=105,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),S/'condition_probe_core_v1.py',S/'coarse_prefix_capture_v1.py']},stdout_sha256=hashlib.sha256((out/'stdout_v1.txt').read_bytes()).hexdigest())
    with (out/'result_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result));sys.exit(0 if run.wasSuccessful() else 1)
