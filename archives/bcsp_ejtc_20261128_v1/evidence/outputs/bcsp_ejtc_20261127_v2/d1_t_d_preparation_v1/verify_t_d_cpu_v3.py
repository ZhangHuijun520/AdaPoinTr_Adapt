"""One bounded CPU batch. All tensors and checkpoints below are artificial fixtures."""
from pathlib import Path
from types import SimpleNamespace,ModuleType
from collections import Counter
from contextlib import contextmanager
import ast,copy,hashlib,importlib.util,json,math,os,random,sys,time
import numpy as np
import torch

d=Path(__file__).resolve().parent;base=d.parent;project=base.parents[1]
out=d/'cpu_validation_v3';out.mkdir(exist_ok=False)
torch.set_num_threads(2)
torch.manual_seed(713)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
 return module
worker=load('ejtc_t_worker_cpu',d/'ejtc_train_t_d_v1.py')
launcher=load('ejtc_t_launcher_cpu',d/'launch_ejtc_t_d_v1.py')
candidate=load('frozen_ejtc_loss',base/'ejtc_loss_cpu_candidate_v1.py')
original=load('original_ejtc_cpu_fixtures',base/'verify_ejtc_cpu_v1.py')
for p,digest in original.files.items():assert sha(p.read_bytes())==digest
ch,origin,_=original.make_original()
reports=[]
def check(name,fn):
 try:
  detail=fn();reports.append(dict(check=name,status='PASS',detail=detail))
 except Exception as exc:
  reports.append(dict(check=name,status='FAIL',error=repr(exc)))
  (out/'failed_checks.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
  raise
 print('PASS '+name,flush=True)
def reject(fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError):return
 raise AssertionError('Invalid fixture accepted')
def tensor_sha(t):return sha(t.detach().cpu().contiguous().numpy().tobytes())
def state_sha(model,parameters_only=False):
 rows=model.named_parameters() if parameters_only else model.state_dict().items()
 return sha(b''.join(n.encode()+tensor_sha(v).encode() for n,v in rows))
helper=SimpleNamespace(state_sha=state_sha,tensor_sha=tensor_sha)

class TinyModel(torch.nn.Module):
 def __init__(self):
  super().__init__()
  self.anchors=torch.nn.Parameter(torch.randn(11,3)*.1)
  self.register_buffer('fixture_buffer',torch.tensor([1.]))
  for k,v in vars(origin).items():setattr(self,k,copy.deepcopy(v))
 def forward(self,x):
  dense=self.anchors.unsqueeze(0)+x[:,:1,:]*.01
  return dense[:,:3,:],dense[:,:0,:],dense[:,:0,:],dense
for name in ['build_loss_func','get_fine_loss_components','get_loss']:
 setattr(TinyModel,name,getattr(type(origin),name))

model=TinyModel();x=torch.randn(2,11,3);g=torch.randn(2,11,3)+.2
def components(m,ret,target,epoch,partial):return worker.loss_components(ch,candidate,m,ret,target,epoch,partial)
def value_gradient():
 ret=model(x);s,base_loss=model.get_loss(ret,g,0,partial=x)
 dist=torch.cdist(ret[3],g)
 expected_aux=dist.min(dim=1).values.sort(descending=True,stable=True).values[:,:2].mean()
 reference=s+base_loss+worker.LAMBDA*expected_aux
 reference_grad=torch.autograd.grad(reference,model.anchors)[0]
 ret=model(x);s,dense,aux=components(model,ret,g,0,x)
 tested=s+dense+worker.LAMBDA*aux
 tested_grad=torch.autograd.grad(tested,model.anchors)[0]
 torch.testing.assert_close(tested,reference,atol=1e-7,rtol=1e-6)
 torch.testing.assert_close(aux,expected_aux,atol=1e-7,rtol=1e-6)
 torch.testing.assert_close(tested_grad,reference_grad,atol=1e-7,rtol=1e-5)
 return dict(loss_abs=float((tested-reference).abs()),grad_max_abs=float((tested_grad-reference_grad).abs().max()))
check('C01_actual_frozen_get_loss_value_and_gradient',value_gradient)
def distance_calls():
 calls=[];real=ch._torch_chamfer_forward
 def observed(a,b):calls.append((a.shape[1],b.shape[1]));return real(a,b)
 ch._torch_chamfer_forward=observed
 try:components(model,model(x),g,0,x)
 finally:ch._torch_chamfer_forward=real
 # Original coarse CD is preserved; dense CD is computed exactly once.
 assert calls==[(3,11),(11,11)],calls
 assert 'forward' not in vars(model.fine_loss_func)
 return dict(coarse_distance_calls=1,dense_distance_calls=1)
check('C02_no_duplicate_dense_distance_or_persistent_patch',distance_calls)
def restoration():
 real=model.get_loss
 def fail(*args,**kwargs):raise ValueError('artificial get_loss failure')
 model.get_loss=fail
 try:reject(lambda:components(model,model(x),g,0,x))
 finally:del model.get_loss
 assert 'forward' not in vars(model.fine_loss_func)
check('C03_loss_hook_restored_on_exception',restoration)
def duplicate():
 def twice(ret,target,*args,**kwargs):
  model.fine_loss_func(ret[3],target);return ret[3].new_zeros(()),model.fine_loss_func(ret[3],target)
 model.get_loss=twice
 try:reject(lambda:components(model,model(x),g,0,x))
 finally:del model.get_loss
 assert 'forward' not in vars(model.fine_loss_func)
check('C04_repeated_dense_call_rejected',duplicate)
def tails():
 v=torch.tensor([5.,5.,4.,3.,2.,1.,0.,0.,0.,0.,0.],requires_grad=True)
 assert candidate.tail_indices(v).tolist()==[0,1]
 candidate.tail_mean(v).backward();assert v.grad.tolist()==[.5,.5,0,0,0,0,0,0,0,0,0]
check('C05_ceiling_ties_and_target_row_gradient',tails)
def zero():
 p=torch.zeros(1,11,3,requires_grad=True);target=torch.zeros_like(p)
 layer=ch.ChamferDistanceL1Directional(pred_to_ref_weight=1.,ref_to_pred_weight=1.)
 value,v=candidate.dense_loss_and_target_distances(ch,layer,p,target)
 assert value.item()==0 and candidate.auxiliary(v,'T').item()==0
 # Preserve the already documented original sqrt-at-zero behavior; do not alter gradients.
check('C06_zero_distance_values_without_changing_backend',zero)

fixture=out/'state';fixture.mkdir();initial=fixture/'common_initial_state.pth'
with initial.open('xb') as f:torch.save(model.state_dict(),f)
record=dict(path=str(initial),bytes=initial.stat().st_size,sha256=sha(initial.read_bytes()))
mh,ph=state_sha(model),state_sha(model,True)
def load_initial():
 with torch.no_grad():model.anchors.add_(1)
 worker.load_common_state(torch,helper,model,record,mh,ph)
 assert state_sha(model)==mh
check('C07_strict_frozen_state_loading',load_initial)
bad=copy.deepcopy(record);bad['sha256']='0'*64
check('C08_initial_byte_drift_rejected',lambda:reject(lambda:worker.load_common_state(torch,helper,model,bad,mh,ph)))
check('C09_parameter_fingerprint_drift_rejected',lambda:reject(lambda:worker.load_common_state(torch,helper,model,record,mh,'0'*64)))
def trained_rejected():
 p=out/'trained';p.mkdir();p=p/'common_initial_state.pth'
 with p.open('xb') as f:torch.save(dict(base_model=model.state_dict(),optimizer={}),f)
 r=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
 reject(lambda:worker.load_common_state(torch,helper,model,r,mh,ph))
check('C10_trained_checkpoint_payload_rejected',trained_rejected)
def missing_keys():
 p=out/'missing';p.mkdir();p=p/'common_initial_state.pth'
 with p.open('xb') as f:torch.save({'anchors':model.anchors.detach()},f)
 r=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
 reject(lambda:worker.load_common_state(torch,helper,model,r,mh,ph))
check('C11_strict_state_structure_rejected',missing_keys)
def cpu_rng_test():
 fake=SimpleNamespace(manual_seed=torch.manual_seed,get_rng_state=torch.get_rng_state,
                      cuda=SimpleNamespace(get_rng_state=lambda index:torch.tensor([17,18],dtype=torch.uint8)))
 random.seed(worker.SEED);np.random.seed(worker.SEED);torch.manual_seed(worker.SEED)
 expected=dict(python=sha(repr(random.getstate()).encode()),numpy=sha(np.random.get_state()[1].tobytes()),cpu=tensor_sha(torch.get_rng_state()),cuda=tensor_sha(fake.cuda.get_rng_state(0)))
 assert worker.seed_pair_rng(fake,np,helper,expected)==expected
 expected['cuda']='0'*64
 reject(lambda:worker.seed_pair_rng(fake,np,helper,expected))
 return 'CPU RNG real; CUDA state is an explicit fixture, no CUDA initialized'
check('C12_all_four_RNG_fields_and_mismatch_stop',cpu_rng_test)

qraw=(d/'T_D_execution_request_CPU_fixture_v2.json').read_bytes();q=json.loads(qraw);rid=sha(qraw)
materializer=load('fixed_authorization_materializer',base/'d1_r_d_preparation_v2/transport_h7vvrr_v2/materialize_rd_authorization_v3.py')
auth,rt=materializer.materialize(qraw,'CPU fixture only, no execution authorization',execution_authorized=True)
def auth_ok():worker.authorize(q,rid,json.loads(auth),sha(auth),json.loads(rt))
check('C13_actual_serialized_T_authorize_path',auth_ok)
def bad_request(field,value):
 v=copy.deepcopy(q);v[field]=value
 reject(lambda:worker.authorize(v,rid,json.loads(auth),sha(auth),json.loads(rt)))
check('C14_wrong_arm_rejected',lambda:bad_request('arm','R'))
check('C15_lambda_drift_rejected',lambda:bad_request('lambda',.1))
check('C16_wrong_step_contract_rejected',lambda:bad_request('counts',dict(steps=3899)))
def bad_pairing():
 v=copy.deepcopy(q);v['pairing']['start_rng']['cpu']='0'*64
 reject(lambda:worker.authorize(v,rid,json.loads(auth),sha(auth),json.loads(rt)))
check('C17_start_RNG_contract_drift_rejected',bad_pairing)
def old_auth_rejected():
 v=json.loads(auth);v['user_authorization_text']='old broken text'
 reject(lambda:worker.authorize(q,rid,v,sha(auth),json.loads(rt)))
check('C18_missing_request_hash_text_rejected',old_auth_rejected)

# Import the unchanged real runtime and its real count/order guards, using only
# isolated CPU fixture modules to avoid importing project model package initializers.
adapter=load('tools.bcsp_adapter',project/'outputs/cranial_bcsp_geov1_20261024/implementation_candidate_v4/overlay/tools/bcsp_adapter.py')
tools_pkg=ModuleType('tools');tools_pkg.__path__=[];sys.modules['tools']=tools_pkg
contract=load('bcsp_training_contract_v1',project/'outputs/cranial_bcsp_geov1_20261024/training_closure_v5/bcsp_training_contract_v1.py')
runtime_path=project/'outputs/scq_prime_publication_20261122_v1/archives/cranial_bcsp_scq_prime_20261122_v1/code/bcsp_scq_prime_runtime_v1.py'
assert sha(runtime_path.read_bytes())=='09973e15bfebe820f39bed550b809e814a4b14c022b22863946ad25f3c5dd292'
runtime=load('frozen_scq_prime_runtime_cpu',runtime_path)
parent=json.loads((project/'outputs/bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json').read_bytes())
plan_path=base/'d1_r_d_preparation_v3/post_training_freeze_audit_v3/evidence/order_plan.json'
assert sha(plan_path.read_bytes())==q['order_file_sha256']
plan=json.loads(plan_path.read_bytes())
records=[dict(case_id=cid,source_id='train:'+cid.split('__')[1]) for cid in plan['case_ids']]
sources=sorted({r['source_id'] for r in records})
class TinyDataset:
 def __init__(self):self.records=records
 def __len__(self):return 315
 def __getitem__(self,i):
  v=torch.arange(33,dtype=torch.float32).reshape(11,3)*.01+i*.0001
  return v,v+.4,records[i]['case_id'],records[i]['source_id']
def full_loop():
 tiny=TinyModel();dataset=TinyDataset();loopout=out/'full_lifecycle';loopout.mkdir()
 calls=Counter();checkpoint={}
 resources=SimpleNamespace(before_step=lambda step:calls.update(['before_step']),after_step=lambda step:calls.update(['after_step']),before_final=lambda:calls.update(['before_final']),after_final=lambda:calls.update(['after_final']))
 def claim(p):assert Path(p)==loopout;return loopout
 run=worker.lifecycle(runtime,sha(runtime_path.read_bytes()),claim,components)
 started=time.monotonic()
 done=run(tiny,lambda epoch:runtime.make_loader(dataset,plan,epoch),records,plan,str(loopout),device='cpu',numeric_check=lambda t:None,resources=resources,knn_enable=lambda:calls.update(['knn']),state_fingerprint=state_sha,run_identity=dict(variant='T',fold='D',seed=worker.SEED))
 assert done['optimizer_updates']==3900 and done['case_exposures']==31200 and done['traversals']==100
 rows=[json.loads(v) for v in (loopout/'metrics.jsonl').read_bytes().splitlines()];assert len(rows)==3900
 for i,row in enumerate(rows):
  epoch,bi=divmod(i,39)
  assert row['case_ids']==plan['epochs'][epoch]['batches'][bi]
  assert row['step']==i+1 and row['ejtc_applied_lambda']==worker.LAMBDA
  assert math.isclose(row['loss'],row['loss_sparse']+row['loss_dense']+worker.LAMBDA*row['ejtc_auxiliary'],rel_tol=1e-6,abs_tol=1e-7)
  assert math.isclose(row['ejtc_weighted_auxiliary'],worker.LAMBDA*row['ejtc_auxiliary'],rel_tol=1e-6,abs_tol=1e-7)
 payload=torch.load(loopout/'ckpt-last.pth',map_location='cpu',weights_only=True)
 assert payload['scq_prime_run_identity']==dict(variant='T',fold='D',seed=worker.SEED)
 assert payload['updates']==3900 and payload['epoch']==99
 assert calls==Counter(before_step=3900,after_step=3900,before_final=1,after_final=1,knn=1)
 return dict(artificial_optimizer_updates=3900,real_model_updates=0,seconds=time.monotonic()-started,actual_frozen_order_verified=True,all_metrics_loss_decomposition_verified=True)
check('C19_actual_frozen_3900_step_CPU_lifecycle',full_loop)
def loop_identity_rejected():
 run=worker.lifecycle(runtime,sha(runtime_path.read_bytes()),lambda p:Path(p),components)
 reject(lambda:run(None,None,None,None,None,device='cpu',numeric_check=None,resources=None,knn_enable=None,state_fingerprint=None,run_identity=dict(variant='R',fold='D',seed=worker.SEED)))
check('C20_real_lifecycle_wrong_identity_rejected_before_output',loop_identity_rejected)
check('C21_runtime_byte_drift_rejected',lambda:reject(lambda:worker.lifecycle(runtime,'0'*64,lambda p:Path(p),components)))

def launcher_path():
 testout=out/'launcher_fixture';testout.mkdir()
 fixture=copy.deepcopy(q);fixture['binding']['identity'].update(hostname='CPU_FIXTURE',uid=1000,python_realpath=str(Path(sys.executable).resolve()),python_version=sys.version.split()[0])
 fixture['binding']['install_root']=str(testout)
 fixture['binding']['output']=str(testout/'result')
 fixture['launch']['launcher']=dict(path=str(d/'launch_ejtc_t_d_v1.py'),bytes=(d/'launch_ejtc_t_d_v1.py').stat().st_size,sha256=sha((d/'launch_ejtc_t_d_v1.py').read_bytes()))
 fixture['files']={'worker':dict(path=str(d/'ejtc_train_t_d_v1.py'),bytes=(d/'ejtc_train_t_d_v1.py').stat().st_size,sha256=sha((d/'ejtc_train_t_d_v1.py').read_bytes()))}
 fixture['binding']['interpreter']=dict(path=str(Path(sys.executable).resolve()),bytes=Path(sys.executable).stat().st_size,sha256=sha(Path(sys.executable).read_bytes()))
 for key,name in [('request_path','request.json'),('authorization_path','authorization.json'),('runtime_path','runtime.json'),('single_attempt_log','worker.log'),('resource_log','monitor.jsonl')]:fixture['launch'][key]=str(testout/name)
 fixture_raw=json.dumps(fixture).encode();fid=sha(fixture_raw)
 aa,rr=materializer.materialize(fixture_raw,'CPU fixture only',execution_authorized=True)
 for key,raw in [('request_path',fixture_raw),('authorization_path',aa),('runtime_path',rr)]:Path(fixture['launch'][key]).write_bytes(raw)
 argv=['launcher']
 for key,value in [('request',fixture['launch']['request_path']),('request-sha256',fid),('authorization',fixture['launch']['authorization_path']),('authorization-sha256',sha(aa)),('runtime',fixture['launch']['runtime_path']),('runtime-sha256',sha(rr))]:argv+=['--'+key,value]
 captured=[]
 class Job:
  returncode=0
  def poll(self):return 0
 def popen(args,**kw):
  captured.append((args,kw));Path(fixture['binding']['output']).mkdir();(Path(fixture['binding']['output'])/'completion.json').write_text('{}')
  return Job()
 oldargv=sys.argv;old=(launcher.socket,launcher.os,launcher.gpu,launcher.shutil,launcher.subprocess)
 try:
  sys.argv=argv
  launcher.socket=SimpleNamespace(gethostname=lambda:'CPU_FIXTURE')
  launcher.os=SimpleNamespace(getuid=lambda:1000,path=os.path,environ=dict(os.environ))
  launcher.gpu=lambda i,r:(1,24090)
  launcher.shutil=SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=64*1024**3))
  launcher.subprocess=SimpleNamespace(Popen=popen,DEVNULL=subprocess_DEVNULL)
  launcher.main()
 finally:
  sys.argv=oldargv;launcher.socket,launcher.os,launcher.gpu,launcher.shutil,launcher.subprocess=old
 assert len(captured)==1
 args,kwargs=captured[0]
 assert Path(args[0]).resolve()==Path(fixture['binding']['identity']['python_realpath']).resolve()
 assert args[1:5]==['-I','-S','-B',fixture['files']['worker']['path']]
 assert kwargs['env']['CUDA_VISIBLE_DEVICES']==fixture['binding']['identity']['gpu_uuid']
 assert json.loads((testout/'monitor.jsonl').read_text())==dict(state='WORKER_COMPLETE',exit_code=0)
 return 'Actual launcher.main() executed with explicit fake subprocess; no real process spawned'
subprocess_DEVNULL=-3
check('C22_actual_launcher_main_and_exact_worker_argv',launcher_path)

receipt=dict(status='T_D_TARGETED_CPU_VALIDATION_PASS',checks=reports,passed=len(reports),worker_sha256=sha((d/'ejtc_train_t_d_v1.py').read_bytes()),launcher_sha256=sha((d/'launch_ejtc_t_d_v1.py').read_bytes()),loss_candidate_sha256=sha((base/'ejtc_loss_cpu_candidate_v1.py').read_bytes()),runtime_sha256=sha(runtime_path.read_bytes()),test_sha256=sha(Path(__file__).read_bytes()),torch_version=torch.__version__,numpy_version=np.__version__,execution_device='CPU',real_model_forward_calls=0,real_model_optimizer_steps=0,CUDA_initialized=torch.cuda.is_initialized(),remote_operations=0,limitations=['Artificial 11-point model exercised unchanged frozen get_loss and 3900-step lifecycle; it is not the actual Mamba model','CUDA RNG was a named fixture; actual CUDA RNG matching remains mandatory at training startup','Actual launcher.main tested with fake Popen; no remote process was spawned'])
assert receipt['CUDA_initialized'] is False
with (out/'T_D_CPU_validation_receipt_v3.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(dict(status=receipt['status'],passed=len(reports),CUDA_initialized=False)))
