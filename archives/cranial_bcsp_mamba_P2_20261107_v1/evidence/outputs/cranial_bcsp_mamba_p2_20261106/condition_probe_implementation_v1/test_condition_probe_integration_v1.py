"""One retained artificial CPU integration batch. No real data/checkpoints/GPU."""
import importlib.util,json,hashlib,unittest,time,sys,random,types,copy
from pathlib import Path
import numpy as np
import torch
S=Path(__file__).resolve().parent;B=S/'integration_cpu_batch_v1'
def mod(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
e=mod('entry',S/'condition_probe_entry_v1.py');core=mod('core',S/'condition_probe_core_v1.py');capture=mod('capture',S/'coarse_prefix_capture_v1.py')
parent=mod('parent',S.parents[1]/'cranial_bcsp_mamba_p1_20261104/paired_development_evaluator_v2/bcsp_p1_paired_predict_v2.py')
torch.set_num_threads(2)
def bind(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
class Head(torch.nn.Module):
 def __init__(self):
  super().__init__();self.register_buffer('pattern',torch.linspace(-.1,.1,768).reshape(1,768))
 def forward(self,z):return self.pattern+z[:,:768]*.001
class Toy(torch.nn.Module):
 def __init__(self):
  super().__init__();self.base_model=torch.nn.Module();self.base_model.coarse_pred=Head();self.tail=0
 def forward(self,x):
  self.base_model.coarse_pred(x.mean(1).repeat(1,342)[:,:1024]);self.tail+=1;raise RuntimeError('dense forbidden')
class Helper:
 def validate_model(self,m):e.need(isinstance(m,Toy),'artificial model')
 def state_sha(self,m):return hashlib.sha256(b''.join(v.detach().numpy().tobytes() for v in m.state_dict().values())).hexdigest()
 def tensor_sha(self,v):return hashlib.sha256(v.detach().numpy().tobytes()).hexdigest()
 def assert_numeric(self,t):e.need(not t.is_grad_enabled() or not any(p.grad is not None for p in []),'fixture numeric')
class Budget:
 def __init__(self,out):self.path=out/'resources.jsonl';self.path.open('x').close();self.events=[];self.fail=False
 def sample(self,label,count):
  parent.append_event(self.path,dict(label=label,count=count));self.events.append((label,count))
  if self.fail:raise ValueError('synthetic resource stop')
def build(run):return Toy(),dict(variant=run['variant'],common_state_unchanged=True,artificial_fixture=True,replaced_global_branches=6 if run['variant']=='M0' else 0)
def prepare():
 B.mkdir();(B/'inputs').mkdir();(B/'weights').mkdir();rows=[];runs=[]
 defects=sorted(e.DEFECTS);files={}
 for i in range(84):
  for d in defects:
   cid=f'train__{i:03d}__{d}';v=np.arange(8192*3,dtype=np.float64).reshape(8192,3);x=(np.sin(v*.013+i)*.2).astype('float32');g=(np.cos(v*.017+i)*.1+i*.0001).astype('float32');path=B/'inputs'/(cid+'.npz')
   with path.open('xb') as f:np.savez_compressed(f,partial=x,implant=g)
   z=x.mean(0,dtype=np.float32);# actual torch mean is used for the frozen artificial head reference
   with torch.inference_mode():q=Head()(torch.from_numpy(x).unsqueeze(0).mean(1).repeat(1,342)[:,:1024]).numpy().reshape(256,3).astype('float64')
   files[cid]=dict(input=bind(path),target_array_sha256=hashlib.sha256(g.tobytes()).hexdigest(),coarse=dict(centroid=q.mean(0).tolist(),radius_gyration=float(np.sqrt(((q-q.mean(0))**2).sum(1).mean()))))
 for fold in ['C','D']:
  dev_sources=set(range(63,84)) if fold=='C' else set(range(21))
  train=sorted(c for c in files if int(c.split('__')[1]) not in dev_sources);dev=sorted(set(files)-set(train))
  for variant in ['T0','M0']:
   label=fold+'_'+variant;ck=B/'weights'/(label+'.pth');torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=Toy().state_dict()),ck)
   runs.append(dict(label=label,fold=fold,variant=variant,seed=0,checkpoint=bind(ck),train_case_ids=train,dev_case_ids=dev))
   for role,ids in [('train',train),('development',dev)]:
    for cid in ids:
     a=files[cid];r=dict(run=label,fold=fold,variant=variant,role=role,case_id=cid,source_id='train:'+cid.split('__')[1],input=a['input'],target_array_sha256=a['target_array_sha256'],normalization=dict(center=[0,0,0],scale=100.),normalization_source='defective_bbox')
     if role=='development':r['frozen_coarse']=a['coarse']
     rows.append(r)
 return runs,rows
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.runs,cls.rows=prepare()
 def test01_production_index_contract(self):
  runs=copy.deepcopy(self.runs);rows=copy.deepcopy(self.rows)
  for r in runs:r['checkpoint']['sha256']=e.MODEL_SHA[r['label']]
  for r in rows:r['input']['path']='/home/jovyan/adapointr_work/PoinTr/data/artificial/points/'+r['case_id']+'_8192.npz'
  e.validate_index(dict(runs=runs,inputs=rows))
  rows[0]['source_id']='train:999'
  with self.assertRaises(ValueError):e.validate_index(dict(runs=runs,inputs=rows))
 def test02_authorize_actual_path_and_bindings(self):
  d=B/'controls';d.mkdir();q=d/'q.json';a=d/'a.json';r=d/'r.json'
  e.emit(q,dict(schema='bcsp-p2-condition-probe-execution-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',prefix_budget=1680,backward=0,optimizer_steps=0,dense_forwards=0,BNCal=0));qr=bind(q)
  e.emit(a,dict(schema='bcsp-condition-probe-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='artificial authorized'));ar=bind(a)
  e.emit(r,dict(schema='bcsp-condition-probe-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']));e.authorize(qr,ar,bind(r));qr['sha256']='0'*64
  with self.assertRaises(ValueError):e.authorize(qr,ar,bind(r))
 def test03_target_hash_reject(self):
  row=dict(self.rows[0]);row['target_array_sha256']='0'*64
  with self.assertRaises(ValueError):e.load_target(np,row)
 def test04_native_equivalence_reject(self):
  row=copy.deepcopy(next(r for r in self.rows if r['role']=='development'));row['frozen_coarse']['centroid']=[99,99,99]
  with self.assertRaises(ValueError):e.check_native(np,np.ones((256,3)),row)
 def test05_complete_actual_four_model_writer_reader(self):
  out=B/'complete';out.mkdir();(out/'features').mkdir();budget=Budget(out)
  files=e.execute(torch,np,parent,Helper(),capture,core,self.runs,self.rows,out,budget,build,device='cpu',artificial=True)
  done=json.loads((out/'probe_complete.json').read_text());self.assertEqual(done['prefixes'],1680);self.assertEqual([r['prefix_calls'] for r in done['model_evidence']],[420]*4);self.assertEqual(len(list((out/'features').glob('*.npz'))),1680)
  self.assertEqual(len((out/'prefix_attempts.jsonl').read_text().splitlines()),1680);self.assertEqual(len((out/'tensor_manifest.jsonl').read_text().splitlines()),1680)
  for run in self.runs:
   s=json.loads((out/(run['label']+'_summary.json')).read_text());self.assertEqual(len(s['case_ids']),105);self.assertEqual(len(s['source_equal']['coarse']['source_errors']),21);self.assertEqual(set(s['defects']),e.DEFECTS)
   with np.load(out/(run['label']+'_readout.npz'),allow_pickle=False) as z:self.assertEqual(z['prediction__feature1024'].shape,(105,4));self.assertEqual(z['feature1024__coefficient'].shape,(1024,4))
  archive=parent.pack(out,files);self.assertEqual(len(archive['members']),1692);self.assertFalse((out/'failure.json').exists())
 def test06_resource_failure_stop_persists(self):
  out=B/'failure';out.mkdir();(out/'features').mkdir();budget=Budget(out);budget.fail=True
  with self.assertRaisesRegex(ValueError,'resource stop'):e.execute(torch,np,parent,Helper(),capture,core,self.runs,self.rows,out,budget,build,device='cpu',artificial=True)
  f=json.loads((out/'failure.json').read_text());self.assertEqual(f['prefix_attempts'],0);self.assertFalse(f['automatic_retry']);self.assertFalse((out/'probe_complete.json').exists())
 def test07_no_overwrite(self):
  path=B/'exclusive.json';e.emit(path,dict(ok=True))
  with self.assertRaises(FileExistsError):e.emit(path,dict(ok=False))
 def test08_upstream_error_is_not_capture(self):
  class Broken(Toy):
   def forward(self,x):raise RuntimeError('genuine upstream')
  m=Broken().eval()
  with self.assertRaisesRegex(RuntimeError,'genuine upstream'):capture.capture_prefix(torch,m,torch.ones(1,8192,3))
  self.assertFalse(m.base_model.coarse_pred._forward_hooks)
if __name__=='__main__':
 start=time.monotonic();log=S/'integration_cpu_stdout_v1.txt'
 with log.open('x',encoding='utf-8') as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 result=dict(status='ARTIFICIAL_FULL_INTEGRATION_PASS' if r.wasSuccessful() else 'FAILED_STOP_NO_RETRY',tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),seconds=time.monotonic()-start,python=sys.executable,torch=torch.__version__,numpy=np.__version__,real_checkpoint_loads=0,real_data_reads=0,real_forward_calls=0,GPU_calls=0,artificial_prefixes_expected=1680,bindings=[bind(p) for p in [Path(__file__),S/'condition_probe_entry_v1.py',S/'condition_probe_core_v1.py',S/'coarse_prefix_capture_v1.py',Path(parent.__file__),log]])
 with (S/'integration_cpu_result_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 print(json.dumps(result));sys.exit(0 if r.wasSuccessful() else 1)
