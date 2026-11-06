"""Artificial CPU contracts; never opens real NPZ/checkpoints or connects remotely."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2'
import copy,hashlib,importlib.util,io,json,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
torch.set_num_threads(2)
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N))
import bcsp_p1_paired_predict_v1 as p
F=N/'cpu_contract_v1'
F.mkdir()

def record(path):return dict(path=str(path),bytes=path.stat().st_size,sha256=p.sha(path))
def emit(name,data):
 path=F/name;p.emit(path,data);return record(path)
def digest(t):return hashlib.sha256(t.detach().cpu().numpy().tobytes()).hexdigest()
class Helper:
 tensor_sha=staticmethod(digest)
 @staticmethod
 def state_sha(m):return {k:digest(v) for k,v in m.state_dict().items()}
 @staticmethod
 def validate_model(m):assert isinstance(m,Tiny)
 @staticmethod
 def assert_numeric(t):pass  # CPU fake; production uses the unchanged frozen CUDA helper
class Tiny(torch.nn.Module):
 def __init__(self,mode=None):super().__init__();self.bn=torch.nn.BatchNorm1d(3);self.calls=0;self.mode=mode
 def forward(self,x):
  self.calls+=1
  assert torch.is_inference_mode_enabled() and not torch.is_grad_enabled()
  if self.mode=='fail':raise RuntimeError('synthetic forward failure')
  if self.mode=='rng':torch.rand(1)
  if self.mode=='state':self.bn.running_mean.add_(1)
  y=self.bn(x.transpose(1,2)).transpose(1,2)
  return y[:,:256].contiguous(),y[:,:1].expand(1,8192,3).contiguous()
class Budget:
 def __init__(self):self.events=[]
 def sample(self,label,count):self.events.append((label,count))
class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.index=json.loads((N.parent/'FoldC_paired_development_preparation_20261106_v1/paired_development_input_index_candidate_v1.json').read_bytes())
  cls.index.update(schema='bcsp-p1-paired-development-index-v1',status='FROZEN_FOR_SEPARATE_EXECUTION_AUTHORIZATION')
  cls.folds=json.loads((N.parents[1]/'cranial_bcsp_geov1_20261024/consolidated_binding_v1/fold_binding.json').read_bytes())
  cls.source=json.loads((N.parents[1]/'cranial_bcsp_geov1_20261024/development_eval_v1/development_input_index_v1.json').read_bytes())
  cls.x=np.arange(8192*3,dtype=np.float32).reshape(8192,3)/8192
  cls.input=F/'synthetic_input.npz'
  with cls.input.open('xb') as f:np.savez(f,partial=cls.x,implant=np.array([object()],object))
  cls.ckpt=F/'synthetic_final.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=Tiny().state_dict()),cls.ckpt)
 def reject(self,fn):
  d=copy.deepcopy(self.index);fn(d)
  with self.assertRaises((RuntimeError,KeyError)):p.validate_index(d,self.folds)
 def test_01_frozen_actual_index(self):self.assertEqual(len(p.validate_index(self.index,self.folds)[1]),210)
 def test_02_original_provenance(self):p.validate_source(self.index,self.source)
 def test_03_missing_case(self):self.reject(lambda d:d['inputs'].pop())
 def test_04_duplicate(self):self.reject(lambda d:d['inputs'].__setitem__(1,d['inputs'][0]))
 def test_05_training_source(self):self.reject(lambda d:d['inputs'][0].__setitem__('source_id','train:000'))
 def test_06_wrong_arm(self):self.reject(lambda d:d['runs'][1].__setitem__('variant','T0'))
 def test_07_wrong_root(self):self.reject(lambda d:d['inputs'][0]['input'].__setitem__('path','/tmp/x.npz'))
 def test_08_pair_frame(self):self.reject(lambda d:d['inputs'][105]['normalization'].__setitem__('scale',1))
 def test_09_pair_hash(self):self.reject(lambda d:d['inputs'][105]['input'].__setitem__('sha256','bad'))
 def test_10_pair_target(self):self.reject(lambda d:d['inputs'][105].__setitem__('target_array_sha256','bad'))
 def test_11_ninput(self):self.reject(lambda d:d['runs'][0].__setitem__('n_input',16384))
 def test_12_seed(self):self.reject(lambda d:d['runs'][1].__setitem__('seed',1))
 def chain(self,name,**kw):
  q=emit(name+'_q.json',dict(schema=kw.get('schema','bcsp-p1-paired-development-prediction-v1'),status=kw.get('status','AWAITING_EXPLICIT_USER_AUTHORIZATION')))
  a=dict(schema='bcsp-development-authorization-v1',request_sha256=q['sha256'],explicit_user_authorization=kw.get('authorized',True),user_authorization_text='ARTIFICIAL CPU ONLY')
  if kw.get('reverse'):a['runtime_sha256']='bad'
  ar=emit(name+'_a.json',a);r=emit(name+'_r.json',dict(schema='bcsp-development-runtime-v1',request_sha256=q['sha256'],authorization_sha256='bad' if kw.get('drift') else ar['sha256']))
  return q,ar,r
 def test_13_one_way_authorization(self):p.authorize(*self.chain('good'))
 def test_14_old_schema(self):
  with self.assertRaises(RuntimeError):p.authorize(*self.chain('old',schema='bcsp-blue-noise-pair-development-prediction-v1'))
 def test_15_no_authorization(self):
  with self.assertRaises(RuntimeError):p.authorize(*self.chain('no',authorized=False))
 def test_16_reverse_binding(self):
  with self.assertRaises(RuntimeError):p.authorize(*self.chain('reverse',reverse=True))
 def test_17_runtime_drift(self):
  with self.assertRaises(RuntimeError):p.authorize(*self.chain('drift',drift=True))
 def test_18_checkpoint_final_strict(self):p.load_checkpoint(torch,Tiny(),record(self.ckpt))
 def test_19_checkpoint_bad_updates(self):
  path=F/'bad_updates.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3899,base_model=Tiny().state_dict()),path)
  with self.assertRaises(RuntimeError):p.load_checkpoint(torch,Tiny(),record(path))
 def test_20_checkpoint_wrong_variant_keys(self):
  path=F/'bad_keys.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model={}),path)
  with self.assertRaises(RuntimeError):p.load_checkpoint(torch,Tiny(),record(path))
 def test_21_partial_only_poisoned_GT(self):np.testing.assert_array_equal(p.load_partial(np,dict(input=record(self.input),n_input=8192)),self.x)
 def test_22_eval_inference_shapes(self):
  m=Tiny().eval();before=Helper.state_sha(m);rng=p.rng_state(torch,np,Helper,False)
  c,d=p.predict_once(torch,m,torch.from_numpy(self.x).unsqueeze(0));self.assertEqual(c.shape,(1,256,3));self.assertEqual(d.shape,(1,8192,3));self.assertEqual(before,Helper.state_sha(m));self.assertEqual(rng,p.rng_state(torch,np,Helper,False));self.assertTrue(all(v.grad is None for v in m.parameters()))
 def test_23_train_mode(self):
  with self.assertRaises(RuntimeError):p.predict_once(torch,Tiny(),torch.from_numpy(self.x).unsqueeze(0))
 def test_24_bad_coarse(self):
  class Wrong(Tiny):
   def forward(self,x):return x[:,:1],x
  with self.assertRaises(RuntimeError):p.predict_once(torch,Wrong().eval(),torch.from_numpy(self.x).unsqueeze(0))
 def test_25_nan_dense(self):
  class Wrong(Tiny):
   def forward(self,x):return x[:,:256],x*float('nan')
  with self.assertRaises(RuntimeError):p.predict_once(torch,Wrong().eval(),torch.from_numpy(self.x).unsqueeze(0))
 def test_26_geometry_translation(self):
  c=np.zeros((1,256,3),np.float32);d=np.ones((1,8192,3),np.float32)
  a=p.geometry_summary(np,c,d);self.assertEqual(a['mean_dense_minus_coarse'],[1,1,1]);self.assertEqual(a['offset_mean_squared_radius'],3);self.assertEqual(a['dense']['radius_gyration'],0)
 def run_pair(self,name,mode=None):
  out=F/name;out.mkdir();(out/'predictions').mkdir();runs=copy.deepcopy(self.index['runs']);rows=copy.deepcopy(self.index['inputs']);models=[]
  for r in runs:r['checkpoint']=record(self.ckpt)
  for r in rows:r['input']=record(self.input)
  budget=Budget()
  def builder(run):
   m=Tiny(mode);models.append(m)
   return m,dict(variant=run['variant'],replaced_global_branches=6 if run['variant']=='M0' else 0,common_state_unchanged=True,artificial_fixture=False)
  # Fake construction evidence here is synthetic, not a claim of native Mamba verification.
  result=lambda:p.execute_pair(torch,np,Helper,runs,rows,out,budget,builder,[rows[0]['case_id']],device='cpu')
  return out,models,budget,result
 def test_27_full_210_artificial_pair(self):
  out,models,budget,run=self.run_pair('full210');pred,extra,evidence=run()
  self.assertEqual([m.calls for m in models],[105,105]);self.assertEqual(len(pred),210);self.assertEqual(len((out/'forward_attempts.jsonl').read_text().splitlines()),210)
  self.assertEqual(len((out/'inference_manifest.jsonl').read_text().splitlines()),210);self.assertEqual(len((out/'geometry_summary.jsonl').read_text().splitlines()),210)
  self.assertEqual(sum('coarse' in np.load(x).files for x in pred),2)
  self.assertTrue(all(e['state_before']==e['state_after'] and e['RNG_before']==e['RNG_after'] for e in evidence))
  a=p.pack(out,pred+extra);self.assertEqual(len(a['members']),213);self.assertEqual(a['sha256'],p.sha(a['path']))
 def test_28_failed_call_counted_no_retry(self):
  out,models,_,run=self.run_pair('failure',mode='fail')
  with self.assertRaises(RuntimeError):run()
  d=json.loads((out/'failure.json').read_bytes());self.assertEqual((d['forward_attempts'],d['valid_forward_returns']),(1,0));self.assertEqual(len(models),1);self.assertEqual(models[0].calls,1)
 def test_29_rng_mutation_stops(self):
  out,models,_,run=self.run_pair('rng_mutation',mode='rng')
  with self.assertRaisesRegex(RuntimeError,'RNG'):run()
  self.assertEqual(len(models),1)
 def test_30_state_mutation_stops(self):
  out,models,_,run=self.run_pair('state_mutation',mode='state')
  with self.assertRaisesRegex(RuntimeError,'state'):run()
  self.assertEqual(len(models),1)
 def test_31_payload_policy(self):
  hp=N.parents[1]/'cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'
  spec=importlib.util.spec_from_file_location('fixture_helper',hp);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
  class UTC:
   def allow(self,name,write):return False
  policy=p.make_policy(h,[F],F,[self.input],[self.ckpt],[F/'pred.npz'],UTC())
  policy.check(self.input);policy.check(self.ckpt);policy.check(F/'pred.npz',True)
  for path,write in [(F/'other.pth',False),(self.input,True),(self.ckpt,True),(F/'.env',False)]:
   with self.assertRaises(RuntimeError):policy.check(path,write)
 def test_32_resource_budget_preserved(self):
  import ast
  old=N.parents[1]/'cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_blue_pair_predict_v1.py'
  def cls(path):return ast.dump(next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Budget'))
  self.assertEqual(cls(old),cls(N/'bcsp_p1_paired_predict_v1.py'))
 def test_33_production_no_CPU_bypass(self):
  source=(N/'bcsp_p1_paired_predict_v1.py').read_text();self.assertNotIn('device=args',source);self.assertNotIn('.backward(',source);self.assertNotIn('optimizer.step(',source);self.assertIn('weights_only=True',source)
 def test_34_exclusive_output(self):
  path=F/'exclusive.json';p.emit(path,dict(a=1))
  with self.assertRaises(FileExistsError):p.emit(path,dict(a=2))
 def test_35_hash_drift(self):
  r=record(self.input);r['sha256']='0'*64
  with self.assertRaises(RuntimeError):p.exact(r)

if __name__=='__main__':
 log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
 (F/'stdout.txt').write_text(log.getvalue(),encoding='utf8')
 p.emit(N/'CPU_contract_result_v1.json',dict(status='PASS' if result.wasSuccessful() else 'FAILED_STOP_NO_RETRY',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),GPU_calls=0,server_operations=0,real_checkpoint_loads=0,real_point_payload_reads=0,native_Mamba_verified=False,torch_version=torch.__version__,source_sha256=p.sha(N/'bcsp_p1_paired_predict_v1.py'),test_sha256=p.sha(Path(__file__)),stdout_sha256=p.sha(F/'stdout.txt')))
 print(log.getvalue());raise SystemExit(0 if result.wasSuccessful() else 1)
