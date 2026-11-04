"""One-shot artificial CPU closure. Retain all fixtures; never import real models."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2'
os.environ['MKL_NUM_THREADS']='2'
import ast
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import torch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PARENT=ROOT/'outputs/cranial_scqr_v12_qa_github_publish_20261019'
OVERLAY=HERE/'overlay'
OUT=HERE/'closure_cpu_v4'
sys.path.insert(0,str(OVERLAY))
from tools import bcsp_runtime as r
torch.set_num_threads(2)

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p):return ast.parse(Path(p).read_text(encoding='utf8'))
def function(p,name):return next(n for n in tree(p).body if isinstance(n,ast.FunctionDef) and n.name==name)
def knn_namespace():
    p=OVERLAY/'models/Transformer_utils.py'
    nodes=[function(p,n) for n in ('enable_bcsp_knn','square_distance','knn_point')]
    ns={'torch':torch,'_BCSP_KNN_ENABLED':False}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns)
    return ns

class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__();self.bias=torch.nn.Parameter(torch.tensor([.75]));self.bn=torch.nn.BatchNorm1d(3)
    def forward(self,x):return self.bn(x.mean(1)).mean(1)+self.bias
    def get_loss(self,ret,target,epoch,partial=None):
        loss=(ret-target.mean((1,2))).square().mean()
        return loss*.5,loss*.5

class Batches:
    def __init__(self):self.p=torch.arange(48,dtype=torch.float32).reshape(8,2,3)/50;self.y=torch.zeros(8,2,3)
    def __len__(self):return 39
    def __iter__(self):return iter([(self.p,self.y)]*39)

class Closure(unittest.TestCase):
    def test_01_frozen_mother_identity(self):
        b=json.loads((ROOT/'outputs/cranial_bcsp_geov1_20261024/consolidated_binding_v1/mother_and_training_design_binding_v1.json').read_text(encoding='utf8'))
        for item in b['files']:self.assertEqual(digest(item['parent_path']),item['sha256'])
    def test_02_legacy_runner_suffix_unchanged(self):
        old=function(PARENT/'tools/runner.py','run_net');new=function(OVERLAY/'tools/runner.py','run_net')
        self.assertEqual(ast.dump(ast.Module(body=old.body,type_ignores=[])),ast.dump(ast.Module(body=new.body[1:],type_ignores=[])))
    def test_03_dispatch_actual_branch_fails_closed(self):
        fn=function(OVERLAY/'tools/runner.py','run_net');ns={}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'isolated_runner_ast','exec'),ns)
        with self.assertRaisesRegex(PermissionError,'separate execution authorization'):
            ns['run_net'](SimpleNamespace(),{'bcsp_execution':{'stage':r.STAGE}})
    def test_04_actual_model_import_and_legacy_knn(self):
        imports=[n for n in tree(PARENT/'models/AdaPoinTr.py').body if isinstance(n,ast.ImportFrom)]
        self.assertTrue(any(n.module=='models.Transformer_utils' and n.names[0].name=='*' for n in imports))
        old=function(PARENT/'models/Transformer_utils.py','knn_point');new=function(OVERLAY/'models/Transformer_utils.py','knn_point')
        self.assertEqual(ast.dump(ast.Module(body=old.body,type_ignores=[])),ast.dump(ast.Module(body=new.body[1:],type_ignores=[])))
        ns=knn_namespace();x=torch.randn(1,37,3);q=torch.randn(1,19,3)
        expected=ns['square_distance'](q,x).topk(7,dim=-1,largest=False,sorted=False).indices
        torch.testing.assert_close(ns['knn_point'](7,x,q),expected,rtol=0,atol=0)
    def test_05_actual_knn_16k_full_keys_chunked(self):
        ns=knn_namespace();ns['enable_bcsp_knn']()
        g=torch.Generator().manual_seed(24);x=torch.randn(1,16384,3,generator=g);q=torch.randn(1,257,3,generator=g)
        shapes=[];original=torch.matmul
        def observed(a,b):shapes.append(list(a.shape));return original(a,b)
        with patch('torch.matmul',side_effect=observed):got=ns['knn_point'](16,x,q)
        self.assertEqual(shapes,[[1,256,3],[1,1,3]])
        expected=ns['square_distance'](q,x).topk(16,dim=-1,largest=False,sorted=False).indices
        torch.testing.assert_close(got.sort(-1).values,expected.sort(-1).values,rtol=0,atol=0)
    def test_06_dataset_loader_real_synthetic_arrays(self):
        data=OUT/'synthetic_data';data.mkdir()
        p=data/'artificial.npz';np.savez(p,partial=np.zeros((8192,3),np.float32),implant=np.ones((8192,3),np.float32))
        sources=['S%02d'%i for i in range(63)]
        self.__class__.records=[{'case_id':s+'_'+str(j),'source_id':s,'point_path':p.name,'sha256':digest(p),'schema':'BCSP-normalized-v1','normalization_source':'defective_bbox'} for s in sources for j in range(5)]
        self.__class__.dataset=r.BCSPDataset(data,self.records,sources,8192)
        self.__class__.sources=sources
        loader=r.make_loader(self.dataset,0);self.assertEqual(len(loader),39)
        exposures=0
        for x,y in loader:
            self.assertEqual(tuple(x.shape),(8,8192,3));self.assertTrue(torch.all(y==1).item());exposures+=len(x)
        self.assertEqual(exposures,312)
    def test_07_dataset_rejects_wrong_counts_duplicates(self):
        for records,sources in ((self.records[:-1],self.sources),(self.records,self.sources[:-1]),([self.records[0]]*315,self.sources)):
            with self.assertRaises(ValueError):r.BCSPDataset(OUT,records,sources,8192)
    def test_08_real_optimizer_full_lifecycle(self):
        model=Tiny();before=model.bias.detach().clone();small=Batches();observed=[]
        original=r.make_optimizer
        def make(m):
            optimizer=original(m)
            optimizer.register_step_post_hook(lambda *args:observed.append(1))
            return optimizer
        # One real 315-case DataLoader traversal; 99 repeated tiny synthetic traversals.
        with patch.object(r,'make_optimizer',side_effect=make):
            receipt=r.train_lifecycle(model,lambda e:r.make_loader(self.dataset,e) if e==0 else small,OUT/'synthetic_success')
        self.assertEqual(receipt['optimizer_updates'],3900);self.assertEqual(receipt['traversals'],100)
        self.assertEqual(len(observed),3900);self.assertFalse(torch.equal(before,model.bias.detach()))
        self.assertEqual(receipt['counts'],{'forward':3900,'backward':3900,'clip':3900,'step':3900,'lr_scheduler':100,'bn_scheduler':100})
        checkpoint=OUT/'synthetic_success/ckpt-last.pth'
        state=torch.load(checkpoint,map_location='cpu',weights_only=True)
        self.assertTrue(all(int(s['step'])==3900 for s in state['optimizer']['state'].values()))
        self.assertEqual(state['scheduler']['last_epoch'],100)
        self.assertEqual(receipt['checkpoint_sha256'],digest(checkpoint))
        self.assertFalse(receipt['bncal_executed']);self.assertFalse(receipt['evaluation_executed'])
        self.assertEqual(sorted(p.name for p in checkpoint.parent.iterdir()),['ckpt-last.pth','completion.json'])
    def test_09_nonfinite_loss_stops_no_final(self):
        class Bad(Tiny):
            def get_loss(self,*args,**kwargs):return self.bias.sum()*float('nan'),self.bias.sum()
        with self.assertRaisesRegex(ValueError,'nonfinite loss'):r.train_lifecycle(Bad(),lambda e:Batches(),OUT/'synthetic_nonfinite')
        f=json.loads((OUT/'synthetic_nonfinite/failure.json').read_text())
        self.assertEqual(f['committed_steps'],0);self.assertFalse((OUT/'synthetic_nonfinite/ckpt-last.pth').exists())
    def test_10_optimizer_failure_stops_no_commit(self):
        original=r.make_optimizer
        def make(m):
            opt=original(m)
            def fail(*args):raise RuntimeError('synthetic optimizer failure')
            opt.register_step_pre_hook(fail)
            return opt
        with patch.object(r,'make_optimizer',side_effect=make):
            with self.assertRaisesRegex(RuntimeError,'synthetic optimizer failure'):r.train_lifecycle(Tiny(),lambda e:Batches(),OUT/'synthetic_step_failure')
        f=json.loads((OUT/'synthetic_step_failure/failure.json').read_text())
        self.assertEqual(f['committed_steps'],0);self.assertEqual(f['counts']['step'],0)
    def test_11_existing_output_not_reused(self):
        with self.assertRaises(FileExistsError):r.train_lifecycle(Tiny(),lambda e:Batches(),OUT/'synthetic_success')
    def test_12_static_all_overlay_and_no_model_import(self):
        for p in OVERLAY.rglob('*.py'):compile(p.read_text(encoding='utf8'),str(p),'exec')
        self.assertNotIn('models.AdaPoinTr',sys.modules)
        self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'],'')

if __name__=='__main__':
    OUT.mkdir(exist_ok=False)
    frozen={str(p.relative_to(HERE)):digest(p) for p in sorted(OVERLAY.rglob('*.py'))}
    frozen[Path(__file__).name]=digest(__file__)
    (OUT/'input_manifest.json').write_text(json.dumps(frozen,indent=2),encoding='utf8')
    buffer=io.StringIO()
    result=unittest.TextTestRunner(stream=buffer,verbosity=2,failfast=True).run(unittest.defaultTestLoader.loadTestsFromTestCase(Closure))
    log=buffer.getvalue();print(log,end='')
    (OUT/'stdout.txt').write_text(log,encoding='utf8')
    artifacts={str(p.relative_to(OUT)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()}
    receipt={'status':'PASS_ARTIFICIAL_CPU_ONLY' if result.wasSuccessful() else 'FAILED_STOP_NO_RETRY','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'torch':torch.__version__,'python':sys.version,'artifacts':artifacts,'limits':['No real AdaPoinTr construction or forward','No CUDA execution or resource validation','No real data QC','Synthetic optimizer checkpoint only; not research model weights','Not a formal post-test freeze audit or training authorization']}
    (OUT/'result.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
    sys.exit(0 if result.wasSuccessful() else 1)
