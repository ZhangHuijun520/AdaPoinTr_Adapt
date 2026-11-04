"""One CPU-only batch: synthetic tensor/checkpoint fixtures, no real model calls."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
import copy,hashlib,importlib.util,io,json,sys,unittest
from pathlib import Path
import numpy as np
import torch
torch.set_num_threads(2)
N=Path(__file__).resolve().parent;sys.path.insert(0,str(N))
import bcsp_blue_pair_predict_v1 as p
F=N/'cpu_contract_v1';F.mkdir()
def record(path):return dict(path=str(path),bytes=path.stat().st_size,sha256=p.sha(path))
def emit(name,data):
 path=F/name
 with path.open('x') as f:json.dump(data,f)
 return record(path)
class Tiny(torch.nn.Module):
 def __init__(self):super().__init__();self.bn=torch.nn.BatchNorm1d(3)
 def forward(self,x):
  y=self.bn(x.transpose(1,2)).transpose(1,2);return y[:,:4],y[:,:1].expand(1,8192,3).contiguous()
class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.index=json.loads((N/'development_input_index_v1.json').read_bytes())
  cls.folds=json.loads((N.parent/'consolidated_binding_v1/fold_binding.json').read_bytes())
 def reject(self,mutator):
  index=copy.deepcopy(self.index);mutator(index)
  with self.assertRaises((RuntimeError,KeyError)):p.validate_index(index,self.folds)
 def test_01_actual_105_case_index(self):self.assertEqual(len(p.validate_index(self.index,self.folds)[1]),210)
 def test_02_missing_case(self):self.reject(lambda x:x['inputs'].pop())
 def test_03_duplicate_case(self):self.reject(lambda x:x['inputs'].__setitem__(1,copy.deepcopy(x['inputs'][0])))
 def test_04_training_source(self):self.reject(lambda x:x['inputs'][0].__setitem__('source_id',x['runs'][0]['train_sources'][0]))
 def test_05_wrong_root(self):self.reject(lambda x:x['inputs'][0]['input'].__setitem__('path','/tmp/x.npz'))
 def test_06_wrong_arm(self):self.reject(lambda x:x['inputs'][0].__setitem__('arm','surface_graph'))
 def test_07_target_mismatch(self):self.reject(lambda x:x['inputs'][105].__setitem__('target_array_sha256','bad'))
 def test_08_frame_mismatch(self):self.reject(lambda x:x['inputs'][105]['normalization'].__setitem__('scale',1.0))
 def test_09_permutation_mismatch(self):self.reject(lambda x:x['inputs'][105].__setitem__('common_point_order_sha256','bad'))
 def chain(self,prefix,schema='bcsp-blue-noise-pair-development-prediction-v1',bad_runtime=False,reverse=False):
  q=emit(prefix+'_q.json',dict(schema=schema,status='AWAITING_EXPLICIT_USER_AUTHORIZATION'))
  a=dict(schema='bcsp-development-authorization-v1',request_sha256=q['sha256'],explicit_user_authorization=True,user_authorization_text='SYNTHETIC CPU TEST FIXTURE ONLY; not production authorization')
  if reverse:a['runtime_sha256']='bad'
  a=emit(prefix+'_a.json',a)
  r=emit(prefix+'_r.json',dict(schema='bcsp-development-runtime-v1',request_sha256=q['sha256'],authorization_sha256='bad' if bad_runtime else a['sha256']))
  return q,a,r
 def test_10_one_way_authorize(self):self.assertEqual(p.authorize(*self.chain('good'))['schema'],'bcsp-blue-noise-pair-development-prediction-v1')
 def test_11_old_request_rejected(self):
  with self.assertRaises(RuntimeError):p.authorize(*self.chain('old',schema='bcsp-four-model-development-prediction-v1'))
 def test_12_runtime_drift_and_reverse_binding(self):
  for kw in [dict(bad_runtime=True),dict(reverse=True)]:
   with self.assertRaises(RuntimeError):p.authorize(*self.chain('bad'+str(len(list(F.iterdir()))),**kw))
 def test_13_correct_checkpoint_marker(self):
  m=Tiny();path=F/'synthetic_final.pth';torch.save(dict(stage='BCSP_BLUE_NOISE_AB_V1',epoch=99,updates=3900,base_model=m.state_dict()),path)
  t=Tiny();p.load_checkpoint(torch,t,record(path));self.assertTrue(torch.equal(m.bn.weight,t.bn.weight))
 def test_14_old_checkpoint_stage_rejected(self):
  path=F/'synthetic_old.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=Tiny().state_dict()),path)
  with self.assertRaises(RuntimeError):p.load_checkpoint(torch,Tiny(),record(path))
 def test_15_incomplete_updates_rejected(self):
  path=F/'synthetic_incomplete.pth';torch.save(dict(stage='BCSP_BLUE_NOISE_AB_V1',epoch=99,updates=3899,base_model=Tiny().state_dict()),path)
  with self.assertRaises(RuntimeError):p.load_checkpoint(torch,Tiny(),record(path))
 def test_16_eval_cpu_no_grad_BN_or_rng_change(self):
  m=Tiny().eval();x=torch.ones(1,16,3);state={k:v.clone() for k,v in m.state_dict().items()};rng=torch.get_rng_state().clone()
  y=p.predict_once(torch,m,x)
  self.assertEqual(y.shape,(1,8192,3));self.assertTrue(all(torch.equal(v,m.state_dict()[k]) for k,v in state.items()));self.assertTrue(torch.equal(rng,torch.get_rng_state()));self.assertTrue(all(v.grad is None for v in m.parameters()))
 def test_17_training_mode_rejected(self):
  with self.assertRaises(RuntimeError):p.predict_once(torch,Tiny().train(),torch.ones(1,16,3))
 def test_18_invalid_output_rejected(self):
  class Wrong(Tiny):
   def forward(self,x):return x,x
  with self.assertRaises(RuntimeError):p.predict_once(torch,Wrong().eval(),torch.ones(1,16,3))
 def test_19_GT_not_read_for_prediction(self):
  path=F/'synthetic_input.npz';x=np.ones((8192,3),np.float32)
  with path.open('xb') as f:np.savez(f,partial=x,implant=np.array([object()],object))
  np.testing.assert_array_equal(p.load_partial(np,dict(input=record(path),n_input=8192)),x)
 def test_20_payload_read_write_allowlist(self):
  helper=N.parent/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'
  spec=importlib.util.spec_from_file_location('frozen_cpu_helper',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  policy=p.make_policy(m,[F],F,[F/'synthetic_input.npz'],[F/'synthetic_final.pth'],[F/'prediction.npz'])
  policy.check(F/'synthetic_input.npz');policy.check(F/'synthetic_final.pth');policy.check(F/'prediction.npz',True)
  for path,write in [(F/'unknown.npz',False),(F/'synthetic_input.npz',True),(F/'synthetic_final.pth',True),(F/'.env',False)]:
   with self.assertRaises(RuntimeError):policy.check(path,write)
if __name__=='__main__':
 log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
 text=log.getvalue()
 with (F/'stdout.txt').open('x',encoding='utf-8') as f:f.write(text)
 with (N/'CPU_contract_result_v1.json').open('x') as f:json.dump(dict(status='PASS' if result.wasSuccessful() else 'FAILED_STOP_NO_RETRY',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),GPU_calls=0,real_model_loads=0,real_predictions=0,torch_version=torch.__version__,source_sha256=p.sha(N/'bcsp_blue_pair_predict_v1.py'),test_sha256=p.sha(Path(__file__)),stdout_sha256=p.sha(F/'stdout.txt')),f,indent=2)
 print(text);raise SystemExit(0 if result.wasSuccessful() else 1)
