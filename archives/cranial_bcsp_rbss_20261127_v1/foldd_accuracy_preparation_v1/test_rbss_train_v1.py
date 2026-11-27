import ast
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np
from rbss_train_v1 import CheckedLoader, lifecycle, sha, SEED


class Array(np.ndarray):
    detach = cpu = contiguous = lambda self: self
    numpy = lambda self: np.asarray(self)
    device = 'cpu'


class Contract(unittest.TestCase):
    def fixture(self, arm, invalid=False):
        x = np.arange(96, dtype=np.float32).reshape(8,4,3).view(Array)
        pos = np.zeros((8,256,3), np.float32).view(Array)
        native = np.tile(np.arange(256), (8,1)).view(Array)
        ids = list('abcdefgh')
        model = SimpleNamespace(hook=None)
        target = SimpleNamespace(choose=None)
        def hook(fn):
            model.hook = fn
            return SimpleNamespace(remove=lambda: setattr(model,'hook',None))
        model.register_forward_hook = hook
        @contextmanager
        def wrap(m, _torch, choose):
            m.choose = choose
            try:
                yield
            finally:
                m.choose = None
        lib = SimpleNamespace(temporary_order=wrap,content_key=lambda v,*args:sha(v.tobytes()))
        torch = SimpleNamespace(long=np.int64,tensor=lambda x,**kw:np.asarray(x,dtype=kw['dtype']))
        r=list(range(256)); c=r[::-1]; s=[1,0,*r[2:]]
        assets={id:dict(key=sha(v.tobytes()),input_sha256=sha(v.tobytes()),frame={},active=id!='a',
                        order=dict(R=r,C=c,S=s),inverse=dict(R=r,C=c,S=s)) for id,v in zip(ids,x)}
        if invalid:
            assets['b']['key']='wrong'
        src=[(x,None,ids,None)]*39
        return CheckedLoader(src,[ids]*39,assets,model,target,torch,lib,arm,'frozen'),model,target,pos,native,c,s

    def test_shared_batch_and_three_arms(self):
        for arm in 'RCS':
            t,m,k,x,o,c,s=self.fixture(arm)
            it=iter(t);next(it)
            got=k.choose(x,o,o);m.hook();it.close()
            self.assertIsNone(k.choose)
            self.assertIsNone(m.hook)
            if arm=='R':self.assertIsNone(got)
            else:
                order,inv=got
                np.testing.assert_array_equal(order[0],np.arange(256))
                np.testing.assert_array_equal(order[1],c if arm=='C' else s)
                np.testing.assert_array_equal(order,inv)

    def test_fails_before_loss_on_missing_or_wrong_tokens(self):
        t,m,k,x,o,_,_=self.fixture('C',True)
        it=iter(t);next(it)
        with self.assertRaisesRegex(ValueError,'before loss'):m.hook()
        with self.assertRaisesRegex(ValueError,'live anchor/key'):k.choose(x,o,o)
        it.close()
        self.assertIsNone(m.hook)

    def test_guard_rebinds_frozen_lifecycle(self):
        p=Path('E:/ResearchBackups/AdaPoinTr/BCSP_CISC/2026-11-25_archive_v1/github_snapshot/archives/cranial_bcsp_cisc_20261125_v1/bound_sources/09973e15bfeb_bcsp_scq_prime_runtime_v1.py')
        raw=p.read_bytes()
        h='09973e15bfebe820f39bed550b809e814a4b14c022b22863946ad25f3c5dd292'
        self.assertEqual(sha(raw),h)
        [node]=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='train_lifecycle']
        def require(ok,msg):
            if not ok:raise ValueError(msg)
        env=dict(require=require)
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),env)
        bind=lifecycle(SimpleNamespace(train_lifecycle=env['train_lifecycle']),h,lambda x:x)
        opts=dict(device=None,numeric_check=None,resources=None,knn_enable=None,state_fingerprint=None)
        for arm in 'RCS':
            fn=bind(arm)
            with self.assertRaisesRegex(ValueError,'RBSS identity'):
                fn(None,None,None,None,None,run_identity=dict(variant='wrong',fold='D',seed=SEED),**opts)
            with self.assertRaises(TypeError):
                fn(None,None,None,None,None,run_identity=dict(variant=arm,fold='D',seed=SEED),**opts)


if __name__ == '__main__':
    unittest.main(verbosity=2)
