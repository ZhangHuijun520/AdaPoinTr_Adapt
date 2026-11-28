"""One versioned CPU contract batch. Artificial networks/checkpoints only."""
from pathlib import Path
from types import SimpleNamespace
from contextlib import contextmanager
import copy,hashlib,importlib.util,json,os,sys,tarfile
import numpy as np
import torch

d=Path(__file__).resolve().parent;base=d.parent;project=base.parents[1]
out=d/'cpu_validation_v1';out.mkdir(exist_ok=False)
torch.set_num_threads(2)
h=lambda raw:hashlib.sha256(raw).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
 sys.modules[name]=module;spec.loader.exec_module(module);return module
worker=load('native315_worker_fixture',d/'ejtc_native_rtj315_v1.py')
launcher=load('native315_launcher_fixture',d/'launch_ejtc_native315_v1.py')
frozen_native=load('existing_native_observer',base.parent/'bcsp_oasg_20261124_v1/skullfix_prediction_v2/oasg_sf_native_v2.py')
scope=json.loads((d/'EJTC_RTJ_D_native315_scope_v1.json').read_bytes())
qraw=(d/'Native315_execution_request_CPU_fixture_v1.json').read_bytes();q=json.loads(qraw)
receipts={arm:json.loads(Path(r['local_path']).read_bytes()) for arm,r in scope['training_freeze_receipts'].items()}
reports=[]
def check(name,fn):
 try:details=fn();reports.append(dict(check=name,status='PASS',details=details))
 except Exception as exc:
  reports.append(dict(check=name,status='FAIL',error=repr(exc)))
  (out/'failed_checks.json').write_text(json.dumps(reports,indent=2),encoding='utf-8');raise
 print('PASS '+name,flush=True)
def reject(fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError):return
 raise AssertionError('Invalid fixture accepted')
def record(path):return dict(path=str(path),bytes=path.stat().st_size,sha256=h(path.read_bytes()))
def exact(rec):
 p=Path(rec['path']);assert p.stat().st_size==rec['bytes'] and h(p.read_bytes())==rec['sha256'];return p
def tensor_sha(t):return h(t.detach().cpu().contiguous().numpy().tobytes())
def state_sha(m):return h(b''.join(k.encode()+tensor_sha(v).encode() for k,v in m.state_dict().items()))
helper=SimpleNamespace(state_sha=state_sha,tensor_sha=tensor_sha)
mat=load('native315_materializer',Path(q['authorization_materializer']['local_path']))
a,rt=mat.materialize(qraw,'CPU fixtures only, not execution approval',execution_authorized=True)
digest=h(qraw)
check('N01_actual_serialized_authorization',lambda:worker.authorize(q,digest,json.loads(a),h(a),json.loads(rt)))
def wrong_request(key,value):
 x=copy.deepcopy(q);x[key]=value;reject(lambda:worker.authorize(x,digest,json.loads(a),h(a),json.loads(rt)))
check('N02_wrong_arms_rejected',lambda:wrong_request('arms',['R','T','T']))
check('N03_wrong_seed_rejected',lambda:wrong_request('seeds',[2026112101,2026112803]))
check('N04_extra_forward_budget_rejected',lambda:wrong_request('counts',dict(q['counts'],forward=316)))
def broken_auth():
 x=json.loads(a);x['user_authorization_text']='old missing hash'
 reject(lambda:worker.authorize(q,digest,x,h(a),json.loads(rt)))
check('N05_missing_hash_authorization_rejected',broken_auth)
check('N06_real_frozen_training_receipts',lambda:worker.verify_training(scope,receipts))
def wrong_receipt():
 x=copy.deepcopy(receipts);x['J']['checkpoint']['sha256']='0'*64
 reject(lambda:worker.verify_training(scope,x))
check('N07_wrong_checkpoint_receipt_rejected',wrong_receipt)
def wrong_rng():
 x=copy.deepcopy(receipts);x['T']['initial_state']['rng']['cpu']='0'*64
 reject(lambda:worker.verify_training(scope,x))
check('N08_pairing_RNG_drift_rejected',wrong_rng)
parent=json.loads((base.parent/'bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json').read_bytes())
geo=base.parent/'cranial_bcsp_geov1_20261024'
fold=json.loads((geo/'consolidated_binding_v1/fold_binding.json').read_bytes())
manifest=[json.loads(v) for v in (geo/'real_data_qc_v1/manifest_8192.jsonl').read_bytes().splitlines()]
check('N09_exact_105_case_development_selection',lambda:len(worker.select_inputs(scope,parent,fold,manifest)))
def train_leak():
 x=copy.deepcopy(fold);x['folds']['D']['train_case_ids'].append(scope['case_ids'][0])
 reject(lambda:worker.select_inputs(scope,parent,x,manifest))
check('N10_training_case_overlap_rejected',train_leak)
def coordinate_drift():
 x=copy.deepcopy(scope);x['inputs'][0]['normalization']['scale']*=2
 reject(lambda:worker.select_inputs(x,parent,fold,manifest))
check('N11_normalization_drift_rejected',coordinate_drift)
def budget():
 b=worker.ForwardBudget(scope['case_ids'])
 for arm in worker.ARMS:
  for cid in scope['case_ids']:b.claim(arm,cid)
 b.finish(315);reject(lambda:b.claim('J',scope['case_ids'][-1]))
 return dict(claims=b.calls,extra_call_rejected=True)
check('N12_exact315_budget_and_overrun',budget)
check('N13_wrong_forward_order_rejected',lambda:reject(lambda:worker.ForwardBudget(scope['case_ids']).claim('T',scope['case_ids'][0])))

partial=np.arange(8192*3,dtype=np.float32).reshape(8192,3)*1e-5
point=out/'partial_only.npz'
# Unreadable pickle-only GT proves that loading partial does not require it.
np.savez_compressed(point,partial=partial,implant=np.array([object()],dtype=object))
row=dict(input=record(point),partial_array_sha256=h(partial.tobytes()))
def partial_only():
 keys=[]
 class Archive:
  def __init__(self,real):self.real=real
  def __enter__(self):return self
  def __exit__(self,*args):self.real.close()
  def __getitem__(self,key):
   keys.append(key);assert key=='partial';return self.real[key]
 proxy=SimpleNamespace(load=lambda *a,**kw:Archive(np.load(*a,**kw)),float32=np.float32,isfinite=np.isfinite)
 actual=worker.load_partial(proxy,SimpleNamespace(exact=exact),row)
 assert keys==['partial'] and np.array_equal(actual,partial)
 return dict(accessed_arrays=keys,GT_accesses=0)
check('N14_partial_only_access_spy_and_unreadable_GT',partial_only)
check('N15_partial_array_hash_drift_rejected',lambda:reject(lambda:worker.load_partial(np,SimpleNamespace(exact=exact),dict(row,partial_array_sha256='0'*64))))

class Head(torch.nn.Module):
 def __init__(self):super().__init__();self.bias=torch.nn.Parameter(torch.zeros(3))
 def forward(self,features,positions,anchors):
  delta=torch.zeros_like(anchors)+self.bias
  return delta,anchors+delta
class FC(torch.nn.Module):
 def forward(self,x):return x.new_zeros((1,256,32,3))
class TinyNative(torch.nn.Module):
 def __init__(self):
  super().__init__();base=torch.nn.Module();self.base_model=base
  base.encoder=torch.nn.Module();base.encoder.blocks=torch.nn.Module();blocks=torch.nn.ModuleList()
  for _ in range(6):
   block=torch.nn.Module();block.attn=torch.nn.Module();block.attn.mixer=torch.nn.Identity();blocks.append(block)
  base.encoder.blocks.blocks=blocks
  base.decoder=torch.nn.Module();blocks=torch.nn.ModuleList()
  for _ in range(8):
   block=torch.nn.Module();block.self_ssm=torch.nn.Identity();block.cond_ssm=torch.nn.Identity();blocks.append(block)
  base.decoder.blocks=blocks;base.coarse_pred=Head();self.decode_head=FC();self.forward_calls=0
 def forward(self,x):
  self.forward_calls+=1
  mixers=[b.attn.mixer for b in self.base_model.encoder.blocks.blocks]
  mixers.extend(m for b in self.base_model.decoder.blocks for m in (b.self_ssm,b.cond_ssm))
  for m in [*mixers,*mixers[:14]]:m(x)
  _,coarse=self.base_model.coarse_pred(x[:,:256],x[:,:256],x[:,:256])
  relative=self.decode_head(coarse)
  return coarse,(relative+coarse[:,:,None,:]).reshape(1,8192,3)
 def get_loss(self,*a,**kw):raise AssertionError('Native must not call loss')

cpu_scope=copy.deepcopy(scope);cpu_scope['shared_initial_fingerprint']=state_sha(TinyNative())
constructor_calls=[]
def build(parent,support,torch_module,helper_module,seed,head_seed):
 assert [seed,head_seed]==scope['seeds'];constructor_calls.append((seed,head_seed));return TinyNative(),None
prefix=SimpleNamespace(build_model=build)
for arm,index in zip(worker.ARMS,[1,2,3]):
 m=TinyNative()
 with torch.no_grad():m.base_model.coarse_pred.bias.fill_(index*.001)
 p=out/(arm+'_artificial_checkpoint.pth')
 with p.open('xb') as f:torch.save(dict(base_model=m.state_dict(),epoch=99,updates=3900,stage='BCSP_INPUT_DENSITY_V1',scq_prime_run_identity=dict(variant=arm,fold='D',seed=worker.SEEDS[0])),f)
 cpu_scope['checkpoints'][arm]=record(p)
def construct_and_observe():
 hashes=[]
 for arm in worker.ARMS:
  m=worker.construct_load(torch,helper,prefix,SimpleNamespace(exact=exact),{},cpu_scope,arm)
  m.eval().requires_grad_(False)
  before=state_sha(m);raw=worker.observe(torch,np,frozen_native,m,torch.from_numpy(partial).unsqueeze(0))
  assert m.forward_calls==1 and before==state_sha(m)
  assert set(raw)=={'coarse','prediction','S','delta','parent_index','token_index'}
  hashes.append(h(raw['prediction'].tobytes()))
 assert len(set(hashes))==3 and len(constructor_calls)==3
 return dict(artificial_forward_calls=3,real_Mamba_forward_calls=0,real_frozen_observe_once_used=True)
check('N16_actual_constructor_strict_loading_and_Native_observer',construct_and_observe)
def checkpoint_rejected(change):
 payload=torch.load(cpu_scope['checkpoints']['R']['path'],map_location='cpu',weights_only=True);change(payload)
 p=out/('bad_'+str(len(list(out.glob('bad_*.pth'))))+'.pth')
 with p.open('xb') as f:torch.save(payload,f)
 x=copy.deepcopy(cpu_scope);x['checkpoints']['R']=record(p)
 reject(lambda:worker.construct_load(torch,helper,prefix,SimpleNamespace(exact=exact),{},x,'R'))
check('N17_wrong_checkpoint_arm_rejected',lambda:checkpoint_rejected(lambda p:p['scq_prime_run_identity'].update(variant='J')))
check('N18_wrong_checkpoint_step_rejected',lambda:checkpoint_rejected(lambda p:p.update(updates=3899)))
check('N19_wrong_checkpoint_seed_rejected',lambda:checkpoint_rejected(lambda p:p['scq_prime_run_identity'].update(seed=7)))
check('N20_checkpoint_structure_drift_rejected',lambda:checkpoint_rejected(lambda p:p['base_model'].update(extra=torch.ones(1))))
def raw_payload():
 m=TinyNative().eval();return worker.observe(torch,np,frozen_native,m,torch.from_numpy(partial).unsqueeze(0))
payload=raw_payload()
def bad_payload(key,value):
 p={k:v.copy() for k,v in payload.items()};p[key]=value;reject(lambda:worker.validate_payload(np,p))
check('N21_nonfinite_prediction_rejected',lambda:bad_payload('prediction',np.full((8192,3),np.nan,dtype=np.float32)))
check('N22_wrong_parent_indices_rejected',lambda:bad_payload('parent_index',np.zeros(8192,dtype=np.int64)))
check('N23_changed_coarse_identity_rejected',lambda:bad_payload('coarse',payload['coarse']+1))
check('N24_training_mode_rejected_before_forward',lambda:reject(lambda:worker.observe(torch,np,frozen_native,TinyNative(),torch.from_numpy(partial).unsqueeze(0))))
def boundary():
 x=copy.deepcopy(cpu_scope);x['inputs']=[dict(input=record(point))]
 target=out/'boundary_output';target.mkdir();audit=worker.data_boundary(x,target)
 audit('open',(str(point),'rb',os.O_RDONLY))
 reject(lambda:audit('open',(str(out/'labels.npz'),'rb',os.O_RDONLY)))
 reject(lambda:audit('open',(str(out/'extra.pth'),'rb',os.O_RDONLY)))
 reject(lambda:audit('open',(str(out/'outside.json'),'wb',os.O_WRONLY|os.O_CREAT)))
 allowed=target/f"predictions/R_D__{scope['case_ids'][0]}.npz"
 audit('open',(str(allowed),'wb',os.O_WRONLY|os.O_CREAT))
 return dict(labels_and_extra_checkpoints_denied=True,owned_prediction_allowed=True)
check('N25_data_boundary_labels_and_extra_payload_rejection',boundary)
def state_snapshot():
 m=TinyNative().eval();cpu_torch=SimpleNamespace(get_rng_state=torch.get_rng_state,cuda=SimpleNamespace(get_rng_state=lambda _:torch.tensor([11,12],dtype=torch.uint8)))
 before=worker.snapshot(cpu_torch,np,helper,m);worker.observe(torch,np,frozen_native,m,torch.from_numpy(partial).unsqueeze(0))
 assert before==worker.snapshot(cpu_torch,np,helper,m)
 with torch.no_grad():m.base_model.coarse_pred.bias.add_(1)
 assert before!=worker.snapshot(cpu_torch,np,helper,m)
 return 'Real CPU/Python/NumPy RNG; CUDA RNG is a named CPU fixture'
check('N26_state_RNG_evidence_and_mutation_detection',state_snapshot)
def archive_contract():
 target=out/'archive_fixture';target.mkdir();(target/'predictions').mkdir();saved=[]
 for arm in worker.ARMS:
  for cid in scope['case_ids']:
   p=target/f'predictions/{arm}_D__{cid}.npz';p.write_bytes(b'ARTIFICIAL_ARCHIVE_MEMBER');saved.append(p)
 for name in ['started.json','attempts.jsonl','manifest.jsonl','inference_complete.json','resources.jsonl']:(target/name).write_text('{}\n')
 rec=worker.pack(target,saved,lambda p:h(Path(p).read_bytes()))
 assert rec['members']==320
 with tarfile.open(target/rec['name'],'r:gz') as a:assert len(a.getmembers())==320
 rows=json.loads((target/'archive_members.json').read_bytes());assert len(rows)==320 and len({x['name'] for x in rows})==320
 assert (target/(rec['name']+'.sha256')).read_text().split()==[rec['sha256'],rec['name']]
 assert (target/'archive_members.json.sha256').read_text().split()==[h((target/'archive_members.json').read_bytes()),'archive_members.json']
 return dict(artificial_predictions=315,archive_members=320,download_files=4)
check('N27_exact_archive_member_and_checksum_contract',archive_contract)

def launcher_contract():
 target=out/'launcher_fixture';target.mkdir();fixture=copy.deepcopy(q)
 fixture['binding']['identity'].update(hostname='CPU_FIXTURE',uid=1000,python_realpath=str(Path(sys.executable).resolve()),python_version=sys.version.split()[0])
 fixture['binding']['output']=str(target/'result');fixture['files']={'worker':record(d/'ejtc_native_rtj315_v1.py')}
 fixture['binding']['interpreter']=record(Path(sys.executable).resolve());fixture['launch']['launcher']=record(d/'launch_ejtc_native315_v1.py')
 for key,name in [('request_path','request.json'),('authorization_path','authorization.json'),('runtime_path','runtime.json'),('single_attempt_log','worker.log'),('resource_log','monitor.jsonl')]:fixture['launch'][key]=str(target/name)
 raw=json.dumps(fixture).encode();fid=h(raw);aa,rr=mat.materialize(raw,'CPU only',execution_authorized=True)
 for k,v in [('request_path',raw),('authorization_path',aa),('runtime_path',rr)]:Path(fixture['launch'][k]).write_bytes(v)
 argv=['launcher']
 for k,v in [('request',fixture['launch']['request_path']),('request-sha256',fid),('authorization',fixture['launch']['authorization_path']),('authorization-sha256',h(aa)),('runtime',fixture['launch']['runtime_path']),('runtime-sha256',h(rr))]:argv+=['--'+k,v]
 calls=[]
 class Job:
  returncode=0
  def poll(self):return 0
 def popen(args,**kwargs):
  calls.append((args,kwargs));p=Path(fixture['binding']['output']);p.mkdir();(p/'completion.json').write_text('{}');return Job()
 old=(sys.argv,launcher.os,launcher.socket,launcher.gpu,launcher.shutil,launcher.subprocess)
 try:
  sys.argv=argv;launcher.os=SimpleNamespace(getuid=lambda:1000,path=os.path,environ=dict(os.environ))
  launcher.socket=SimpleNamespace(gethostname=lambda:'CPU_FIXTURE');launcher.gpu=lambda i,r:(1,24090)
  launcher.shutil=SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=64*1024**3))
  launcher.subprocess=SimpleNamespace(Popen=popen,DEVNULL=-3)
  launcher.main()
 finally:sys.argv,launcher.os,launcher.socket,launcher.gpu,launcher.shutil,launcher.subprocess=old
 assert len(calls)==1 and calls[0][0][1:5]==['-I','-S','-B',str(d/'ejtc_native_rtj315_v1.py')]
 assert calls[0][1]['env']['CUDA_VISIBLE_DEVICES']==q['binding']['identity']['gpu_uuid']
 return 'Actual launcher.main, mocked process spawn, exact Native worker argv'
check('N28_actual_launcher_main_and_single_worker_argv',launcher_contract)

receipt=dict(status='EJTC_NATIVE315_TARGETED_CPU_VALIDATION_PASS',passed=len(reports),checks=reports,worker_sha256=h((d/'ejtc_native_rtj315_v1.py').read_bytes()),launcher_sha256=h((d/'launch_ejtc_native315_v1.py').read_bytes()),scope_sha256=h((d/'EJTC_RTJ_D_native315_scope_v1.json').read_bytes()),test_sha256=h(Path(__file__).read_bytes()),torch_version=torch.__version__,numpy_version=np.__version__,CUDA_initialized=torch.cuda.is_initialized(),remote_operations=0,real_Mamba_forward_calls=0,real_optimizer_steps=0,limitations=['Construct/load/observation checks use artificial CPU networks and checkpoints; actual Mamba CUDA execution is not repeated','CUDA RNG and process spawning are explicit CPU fixtures','Archive count check uses artificial member bytes, while production payload shapes are separately tested through the frozen Native observation function'])
assert not receipt['CUDA_initialized']
with (out/'Native315_CPU_validation_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(dict(status=receipt['status'],passed=len(reports),CUDA_initialized=False)))
