import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
N=Path(__file__).resolve().parent;sys.path.insert(0,str(N))
import numpy as np
import torch
torch.set_num_threads(2)
import bcsp_development_predict_v1 as p
import bcsp_development_score_v1 as s

F=N/'cpu2';F.mkdir(exist_ok=False)
def emit(name,data):
 path=F/name
 with path.open('x') as f:json.dump(data,f)
 return dict(path=str(path),bytes=path.stat().st_size,sha256=p.sha(path))
def record(path):return dict(path=str(path),bytes=path.stat().st_size,sha256=p.sha(path))
class Tiny(torch.nn.Module):
 def __init__(self):super().__init__();self.bn=torch.nn.BatchNorm1d(3)
 def forward(self,x):
  y=self.bn(x.transpose(1,2)).transpose(1,2);return y[:,:256],y[:,:1].expand(1,8192,3).contiguous()
class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.index=json.loads((N/'development_input_index_v1.json').read_bytes())
  cls.folds=json.loads((N.parent/'consolidated_binding_v1/fold_binding.json').read_bytes())
 def test_01_real_index_full_validation(self):self.assertEqual(len(p.validate_index(self.index,self.folds)[1]),420)
 def test_02_missing_case_rejected(self):
  x=copy.deepcopy(self.index);x['inputs'].pop()
  with self.assertRaises(RuntimeError):p.validate_index(x,self.folds)
 def test_03_own_training_source_rejected(self):
  x=copy.deepcopy(self.index);x['inputs'][0]['source_id']=x['runs'][0]['train_sources'][0]
  with self.assertRaises(RuntimeError):p.validate_index(x,self.folds)
 def test_04_wrong_arm_path_rejected(self):
  x=copy.deepcopy(self.index);x['inputs'][0]['input']['path']=x['inputs'][0]['input']['path'].replace('foldd','foldc')
  with self.assertRaises(RuntimeError):p.validate_index(x,self.folds)
 def test_05_authorize_actual_one_way_chain(self):
  q=emit('q.json',dict(schema='bcsp-four-model-development-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION'))
  a=emit('a.json',dict(schema='bcsp-development-authorization-v1',request_sha256=q['sha256'],explicit_user_authorization=True,user_authorization_text='artificial fixture only'))
  r=emit('r.json',dict(schema='bcsp-development-runtime-v1',request_sha256=q['sha256'],authorization_sha256=a['sha256']))
  self.assertEqual(p.authorize(q,a,r)['status'],'AWAITING_EXPLICIT_USER_AUTHORIZATION')
 def test_06_reverse_auth_binding_rejected(self):
  q=emit('q2.json',dict(schema='bcsp-four-model-development-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION'))
  a=emit('a2.json',dict(schema='bcsp-development-authorization-v1',request_sha256=q['sha256'],explicit_user_authorization=True,user_authorization_text='fixture',runtime_sha256='invalid'))
  r=emit('r2.json',dict(schema='bcsp-development-runtime-v1',request_sha256=q['sha256'],authorization_sha256=a['sha256']))
  with self.assertRaises(RuntimeError):p.authorize(q,a,r)
 def test_07_runtime_auth_drift_rejected(self):
  q=emit('q3.json',dict(schema='bcsp-four-model-development-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION'))
  a=emit('a3.json',dict(schema='bcsp-development-authorization-v1',request_sha256=q['sha256'],explicit_user_authorization=True,user_authorization_text='fixture'))
  r=emit('r3.json',dict(schema='bcsp-development-runtime-v1',request_sha256=q['sha256'],authorization_sha256='bad'))
  with self.assertRaises(RuntimeError):p.authorize(q,a,r)
 def test_08_GT_not_loaded_for_inference(self):
  x=np.ones((8192,3),np.float32);path=F/'input.npz'
  with path.open('xb') as f:np.savez(f,partial=x,implant=np.array([object()],object))
  np.testing.assert_array_equal(p.load_partial(np,dict(input=record(path),n_input=8192)),x)
 def test_09_input_hash_drift_rejected(self):
  with self.assertRaises(RuntimeError):p.load_partial(np,dict(input=dict(path=str(F/'input.npz'),bytes=1,sha256='bad'),n_input=8192))
 def test_10_eval_no_grad_BN_unchanged(self):
  model=Tiny().eval();before={k:v.clone() for k,v in model.state_dict().items()}
  result=p.predict_once(torch,model,torch.randn(1,16,3))
  self.assertEqual(result.shape,(1,8192,3));self.assertTrue(all(v.grad is None for v in model.parameters()))
  self.assertTrue(all(torch.equal(v,model.state_dict()[k]) for k,v in before.items()))
 def test_11_training_mode_denied(self):
  with self.assertRaises(RuntimeError):p.predict_once(torch,Tiny().train(),torch.ones(1,16,3))
 def test_12_checkpoint_exact_metadata(self):
  m=Tiny();path=F/'final.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=m.state_dict()),path)
  target=Tiny();p.load_checkpoint(torch,target,record(path));self.assertTrue(torch.equal(m.bn.weight,target.bn.weight))
 def test_13_checkpoint_updates_denied(self):
  path=F/'bad.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3899,base_model=Tiny().state_dict()),path)
  with self.assertRaises(RuntimeError):p.load_checkpoint(torch,Tiny(),record(path))
 def test_14_explicit_payload_policy(self):
  helper_path=N.parent/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'
  spec=importlib.util.spec_from_file_location('test_frozen_helper',helper_path);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
  policy=p.make_policy(h,[F],F,[F/'input.npz'],[F/'final.pth'],[F/'prediction.npz'])
  policy.check(F/'input.npz');policy.check(F/'final.pth');policy.check(F/'prediction.npz',True)
  for path,write in [(F/'unknown.npz',False),(F/'input.npz',True),(F/'final.pth',True),(F/'.env',False)]:
   with self.assertRaises(RuntimeError):policy.check(path,write)
 def test_15_five_cases_one_source(self):
  rows=[dict(fold='C',source_id='train:001',arm='8192',case_id='train__001__d'+str(i),status='OK',metrics=dict(E_P95_mm=float(i))) for i in range(5)]
  out=s.aggregate_source(rows);self.assertEqual(len(out),1);self.assertEqual(out[0]['metrics']['E_P95_mm'],2)
 def test_16_missing_defect_denied(self):
  with self.assertRaises(ValueError):s.aggregate_source([dict(fold='C',source_id='s',arm='8192',case_id='x',status='OK',metrics={})])
 def test_17_paired_OOF_direction_CI(self):
  rows=[]
  for fold in ['C','D']:
   for i in range(21):
    for arm,value in [('8192',2.),('16384',1.5)]:rows.append(dict(fold=fold,source_id=fold+str(i),arm=arm,metrics=dict(E_P95_mm=value)))
  result=s.paired_summary(rows)['ALL'];self.assertEqual(result['source_count'],42)
  self.assertEqual(result['metrics']['E_P95_mm']['delta_16k_minus_8k']['CI95'],[-.5,-.5])
 def test_18_no_inference_training_calls(self):
  import ast
  tree=ast.parse(Path(p.__file__).read_text())
  forbidden={'backward','train','step','get_loss','load_state_dict_optimizer'}
  self.assertFalse([x.func.attr for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in forbidden])

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
 with (N/'prediction_score_CPU_result_v2.json').open('x') as f:json.dump(dict(status='PASS' if result.wasSuccessful() else 'FAILED_STOP',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),GPU_calls=0,real_model_loads=0,real_predictions=0,torch_version=torch.__version__,implementation={x:hashlib.sha256((N/x).read_bytes()).hexdigest() for x in ['bcsp_development_predict_v1.py','bcsp_development_score_v1.py']}),f,indent=2)
 raise SystemExit(0 if result.wasSuccessful() else 1)
