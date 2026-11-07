"""Bounded CPU entry tests. Actual parent forward/loss, artificial local operators."""
import hashlib,importlib.util,json,sys,time,types,unittest
from pathlib import Path
from unittest import mock
import numpy as np
import torch
from torch import nn
S=Path(__file__).resolve().parent;I=S.parent/'H2_implementation_v1';sys.path.insert(0,str(I));torch.set_num_threads(2)
def mod(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
entry=mod('h2_cuda_entry',S/'bcsp_h2_cuda_admission_v1.py');fixturemod=mod('h2_original_cpu_fixture',I/'test_h2_cpu_v2.py');adapter=mod('h2_adapter_for_entry',I/'bcsp_h2_model_adapter_v1.py')
parent=mod('h2_P1_parent_for_entry',S.parents[1]/'cranial_bcsp_mamba_p1_20261104/paired_development_evaluator_v2/bcsp_p1_paired_predict_v2.py')
O=S/'artificial_cpu_entry_batch_v1'
def bind(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
class Helper:
 def validate_model(self,m):entry.need(m.num_query==256 and m.num_points==8192,'artificial model contract')
 def state_sha(self,m):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in m.state_dict().values())).hexdigest()
 def tensor_sha(self,v):return hashlib.sha256(v.detach().cpu().numpy().tobytes()).hexdigest()
 def assert_numeric(self,t):entry.need(t.get_default_dtype()==t.float32,'FP32 default')
class LastBN(nn.Module):
 def __init__(self):super().__init__();self.bn=nn.BatchNorm1d(8)
 def forward(self,x):return self.bn(x.transpose(1,2)).transpose(1,2)
class Factory:
 def build_model(self,builder,variant,seed=0):
  m,_=fixturemod.Factory().build_model(builder,variant,seed)
  enc=m.base_model.enc;del m.base_model.enc;m.base_model.add_module('encoder',enc);object.__setattr__(m.base_model,'enc',enc)
  m.base_model.decoder.pos=nn.Sequential(m.base_model.decoder.pos,LastBN())
  return m,dict(variant='M0',artificial_fixture=True,common_state_unchanged=True,replaced_global_branches=6,common_state=dict(sha256=Helper().state_sha(m)))
def builder(mode):return adapter.build_h2(Factory(),fixturemod.Model,mode,0)
class Budget:
 def __init__(self,out):self.path=out/'resources.jsonl';self.path.open('x').close();self.rows=[]
 def sample(self,phase,count):parent.append_event(self.path,dict(phase=phase,forwards=count));self.rows.append((phase,count))
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):O.mkdir();cls.rec=bind(S/'artificial_h2_input_v1.npz');cls.x,cls.g=entry.load_artificial(np,cls.rec)
 def test01_fixture_artificial_finite(self):self.assertEqual(self.x.shape,(8192,3));self.assertEqual(self.g.dtype,np.float32);self.assertTrue(np.isfinite(self.g).all())
 def test02_exact_two_F_two_B_no_optimizer_state_RNG_BN(self):
  out=O/'success';out.mkdir();budget=Budget(out);x=torch.from_numpy(self.x).unsqueeze(0);g=torch.from_numpy(self.g).unsqueeze(0)
  with mock.patch('torch.optim.AdamW',side_effect=AssertionError('optimizer forbidden')),torch.no_grad():counts,results=entry.evaluate_pair(torch,np,parent,Helper(),adapter,builder,x,g,out,budget,device='cpu',artificial=True)
  self.assertEqual(counts,dict(forward_attempts=2,forward_returns=2,loss_calls=2,backward_attempts=2,backward_returns=2,optimizer_steps=0));self.assertEqual(len(results),2);self.assertEqual(len(budget.rows),7)
  self.assertEqual(len((out/'attempts.jsonl').read_text().splitlines()),4)
  for r in results:self.assertEqual(r['state_before'],r['state_after']);self.assertEqual(r['RNG_before'],r['RNG_after']);self.assertFalse(r['optimizer_constructed']);self.assertEqual(r['model_mode'],'eval_with_autograd')
  self.assertEqual(results[0]['H2_log']['H2_scale'],[1.]);self.assertGreater(abs(results[1]['H2_log']['H2_scale'][0]-1),1e-6)
 def test03_builder_failure_no_retry_counts0(self):
  out=O/'builder_failure';out.mkdir();attempt=[]
  def bad(mode):attempt.append(mode);raise RuntimeError('fixed builder failure')
  with self.assertRaises(RuntimeError):entry.evaluate_pair(torch,np,parent,Helper(),adapter,bad,torch.from_numpy(self.x).unsqueeze(0),torch.from_numpy(self.g).unsqueeze(0),out,Budget(out),device='cpu',artificial=True)
  self.assertEqual(attempt,['AUX']);f=json.loads((out/'failure.json').read_text());self.assertEqual(f['counts']['forward_attempts'],0)
 def test04_loss_failure_stops_before_backward(self):
  out=O/'loss_failure';out.mkdir()
  def bad(mode):
   m,c=builder(mode)
   def fail(*a,**kw):raise RuntimeError('fixed loss failure')
   m.get_loss=fail;return m,c
  with self.assertRaises(RuntimeError):entry.evaluate_pair(torch,np,parent,Helper(),adapter,bad,torch.from_numpy(self.x).unsqueeze(0),torch.from_numpy(self.g).unsqueeze(0),out,Budget(out),device='cpu',artificial=True)
  f=json.loads((out/'failure.json').read_text());self.assertEqual(f['counts']['forward_attempts'],1);self.assertEqual(f['counts']['backward_attempts'],0)
 def test05_fixture_hash_rejected(self):
  r=dict(self.rec,sha256='0'*64)
  with self.assertRaises(ValueError):entry.load_artificial(np,r)
 def test06_one_way_authorization_full_path(self):
  d=O/'controls';d.mkdir();q=d/'q.json';a=d/'a.json';r=d/'r.json'
  science=dict(models=['AUX','COUPLE'],forward_attempt_limit=2,backward_attempt_limit=2,optimizer_steps=0,loss_calls=2,real_data_reads=0,checkpoint_loads=0,mode='eval_with_autograd',batch_size=1,n_input=8192,n_output=8192)
  entry.emit(q,dict(schema='bcsp-h2-synthetic-cuda-admission-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',science=science));qr=bind(q)
  entry.emit(a,dict(schema='bcsp-h2-cuda-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='synthetic only'));ar=bind(a)
  entry.emit(r,dict(schema='bcsp-h2-cuda-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']));entry.authorize(qr,ar,bind(r))
  ar['sha256']='0'*64
  with self.assertRaises(ValueError):entry.authorize(qr,ar,bind(r))
 def test07_exact_groups_no_optimizer(self):
  m,_=builder('AUX');rows=entry.optimizer_group_records(torch,bind(I/'bcsp_h2_training_runtime_v1.py'),m);d={r['name']:r for r in rows};self.assertEqual(d['h2_range_head.weight']['weight_decay'],.0005);self.assertEqual(d['h2_range_head.bias']['weight_decay'],0.)
 def test08_non_overwrite(self):
  p=O/'exclusive.json';entry.emit(p,dict(ok=True))
  with self.assertRaises(FileExistsError):entry.emit(p,dict(ok=False))
if __name__=='__main__':
 start=time.monotonic()
 with (S/'cpu_entry_stdout_v1.txt').open('x',encoding='utf-8') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 report=dict(status='H2_CUDA_ENTRY_ARTIFICIAL_CPU_PASS' if r.wasSuccessful() else 'FAILED_STOP_NO_RETRY',tests=r.testsRun,errors=len(r.errors),failures=len(r.failures),seconds=time.monotonic()-start,python=sys.executable,torch=torch.__version__,numpy=np.__version__,bindings=[bind(p) for p in [Path(__file__),S/'bcsp_h2_cuda_admission_v1.py',S/'artificial_h2_input_v1.npz',I/'bcsp_h2_range_v1.py',I/'bcsp_h2_model_adapter_v1.py',I/'bcsp_h2_training_runtime_v1.py',Path(parent.__file__),S/'cpu_entry_stdout_v1.txt']],real_data_reads=0,real_model_imports=0,real_checkpoint_loads=0,GPU_calls=0,optimizer_steps=0,real_training_runs=0,limits=['Real frozen parent forward/loss AST with artificial local operators and losses','BN added to artificial decoder to verify eval freeze; no native Mamba/PointNet2/Chamfer/CUDA','One successful2F/2B CPU path plus two explicit failure-injection tests, no scientific execution'])
 with (S/'cpu_entry_result_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
 print(json.dumps(report));sys.exit(0 if r.wasSuccessful() else 1)
