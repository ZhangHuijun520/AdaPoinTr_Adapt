"""Artificial CPU entry integration; no native models, payloads, server or CUDA."""
import ast,copy,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
import torch
from torch import nn
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];G=ROOT/'outputs/cranial_bcsp_geov1_20261024'
OUT=HERE/'CPU_contracts_v2'
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
entry=module('artificial_P1_training_entry',HERE/'bcsp_p1_training_entry_v1.py')
def state_sha(model,parameters_only=False):
 values=dict(model.named_parameters()) if parameters_only else model.state_dict()
 return hashlib.sha256(b''.join(n.encode()+v.detach().cpu().contiguous().numpy().tobytes() for n,v in values.items())).hexdigest()

class Tiny(nn.Module):
 def __init__(self):super().__init__();self.weight=nn.Parameter(torch.tensor([.1]))
 def forward(self,x):return x*self.weight
 def get_loss(self,ret,target,epoch,partial):return ret.new_zeros(()),(ret-target).square().mean()

class ArtificialBudget(entry.P1Budget):
 def __init__(self,out):
  self.output=Path(out);self.output.mkdir();(self.output/'worker.pid').write_text(str(os.getpid()));(self.output/'resources.jsonl').write_text('');self.records=[];self.local=lambda:(256,0)
 def after_step(self,step):self.records.append(('after_step',step))
 def before_final(self):self.records.append(('before_final',3900))
 def after_final(self):self.records.append(('after_final',3900))

def main():
 OUT.mkdir(exist_ok=False);F=OUT/'fixtures';F.mkdir();checks=[];counter=0
 production_pins=dict(entry.PINNED_EVIDENCE);production_quant=entry.QUANT_REQUEST_SHA
 def check(n,v):
  if not v:raise AssertionError(n)
  checks.append(n)
 def rejects(n,fn):
  try:fn()
  except (ValueError,RuntimeError):checks.append(n)
  else:raise AssertionError(n)
 def bind(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=entry.sha(p))
 def emit(name,v):
  p=F/name
  with p.open('x',encoding='utf-8') as f:json.dump(v,f,allow_nan=False)
  return bind(p)
 def write_lines(name,rows):
  p=F/name
  with p.open('x') as f:
   for row in rows:f.write(json.dumps(row)+'\n')
  return bind(p)
 try:
  torch.set_num_threads(2);torch.manual_seed(8)
  source=G/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
  contract=bind(source/'bcsp_training_contract_01dt08_v3.py');metadata=entry.load_bound('bcsp_training_contract_v1',contract)
  static=json.loads((G/'first_run_freeze_foldC_8192_v1/static_training_config_v1.json').read_bytes());sr=emit('static.json',static)
  sources=['fixture:'+str(i).zfill(3) for i in range(84)];ids=[s.replace(':','__')+'__defect'+str(d) for s in sources for d in range(5)]
  manifests={}
  for count in (8192,16384):
   rows=[]
   for i,cid in enumerate(ids):rows.append(dict(case_id=cid,source_id=sources[i//5],target_array_sha256='0'*64,normalization={'center':[0,0,0],'scale':1},raw={'origin':'ARTIFICIAL_ONLY'},schema='BCSP-normalized-v1',normalization_source='defective_bbox',n_input=count,n_target=8192,point_path='points/'+cid+'_'+str(count)+'.npz',sha256='1'*64))
   manifests[str(count)]=write_lines('manifest_'+str(count)+'.jsonl',rows)
  selected_ids=ids[:315];fold=dict(train_case_ids=selected_ids,train_sources=sources[:63],dev_sources=sources[63:],train_allowlist_sha256=hashlib.sha256(('\n'.join(selected_ids)+'\n').encode()).hexdigest())
  fr=emit('fold.json',dict(folds={'C':fold},confirmation_count_excluded=20))
  verification=emit('QC.json',dict(status=metadata.QC_STATUS,verified_sources=84,verified_cases=420,verified_point_files=840,interpretation={'anatomical_semantics':'UNRESOLVED artificial fixture'},important_file_hashes={'manifest_'+k+'.jsonl':v['sha256'] for k,v in manifests.items()}))
  qualified,selected,_=metadata.bind_metadata(verification,manifests,fr,'C',8192);qualified_record=emit('qualified.json',qualified)
  plan=dict(schema='bcsp-shared-order-v1',case_ids=selected_ids,epochs=[dict(epoch=e,batches=[selected_ids[i:i+8] for i in range(0,312,8)],dropped=selected_ids[312:]) for e in range(100)])
  order=emit('order.json',plan);scope=emit('scope.json',{'ARTIFICIAL_ONLY':True})
  frozen=HERE.parent/'minimal_implementation_v1';gpu=HERE.parent/'gpu_admission_v3'
  impl=dict(entry=bind(HERE/'bcsp_p1_training_entry_v1.py'),contract=contract,runtime=bind(frozen/'bcsp_p1_training_runtime_v1.py'),factory=bind(frozen/'bcsp_p1_model_factory_v1.py'),encoder=bind(frozen/'bcsp_mamba_encoder_v1.py'),preflight_helper=bind(G/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'),timezone=bind(gpu/'exact_utc_resource_v1.py'))
  expected=dict(variant='T0',artificial_fixture=False,common_state_unchanged=True)
  initial=emit('initial.json',dict(factory=expected));identity=dict(hostname='ARTIFICIAL_ONLY')
  parent=emit('quant_request.json',dict(identity=identity,model_root=str(F),data_root=str(F/'data'),batch=[{'ARTIFICIAL_ONLY':True}],dependencies=[],preflight_scope=scope,environment={'ARTIFICIAL_ONLY':'1'},static_config=sr,order_plan=order,factory=impl['factory'],encoder=impl['encoder'],training_runtime=impl['runtime'],helper=impl['preflight_helper'],timezone_implementation=impl['timezone'],diagnostic_baselines={'T0':initial},fold_binding=fr,train_manifest=manifests['8192']))
  entry.QUANT_REQUEST_SHA=parent['sha256']
  audit=emit('audit.json',dict(status='FORMAL_READONLY_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS',request_sha256=parent['sha256'],checks_passed=1,checks={'ARTIFICIAL_ONLY':True},counts=dict(forward_attempts=12,forward_returns=12,loss_calls=4,backward_attempts=4,backward_returns=4,optimizer_steps=0),new_forward_calls=0,new_backward_calls=0,server_writes=0))
  protocol=emit('protocol.json',{'ARTIFICIAL_ONLY':True})
  policy=emit('policy.json',dict(schema='bcsp-p1-confirmed-numeric-policy-v1',status='CONFIRMED_USER_DECISION_NOT_EXECUTION_AUTHORIZATION',user_confirmation='ARTIFICIAL_ONLY',protocol_sha256=protocol['sha256'],quantification_audit_sha256=audit['sha256'],prior_v3_status='FAILED_STOP_NO_RETRY',bitwise_gradient_equality_required_for_training_preparation=False,numeric_tolerance_gate_added=False,deterministic_flags_changed=False,training_execution_authorized=False))
  pair=emit('pair.json',dict(status='FROZEN_PREPARATION_NOT_EXECUTABLE',fold='C',seed=0,arm_order=['T0','M0'],counts=dict(entry.COUNTS,drop_events=300),resources=entry.RESOURCES,model=static['model'],training=static['training'],numeric_policy_sha256=policy['sha256']))
  for k,v in dict(numeric_policy=policy,numeric_protocol=protocol,pair_contract=pair,quantification_audit=audit).items():entry.PINNED_EVIDENCE[k]=v['sha256']
  q=dict(schema='bcsp-p1-training-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='CRANIAL_BCSP_MAMBA_P1',run_id='ARTIFICIAL_ONLY',variant='T0',fold='C',n_input=8192,n_output=8192,static_config=sr,QC=dict(qualified_receipt=qualified_record,verification=verification,manifests=manifests,fold_binding=fr),order_plan=order,identity=identity,data_root=str(F/'data'),model_root=str(F),implementation=impl,preflight_scope=scope,dependencies=[],environment={'ARTIFICIAL_ONLY':'1'},output=str(F/'train_output'),launch_attempt=str(F/'claim.json'),numeric_policy=policy,numeric_protocol=protocol,pair_contract=pair,quantification_audit=audit,quantification_request=parent,initialization_reference=initial,launch_contract={},provenance={'ARTIFICIAL_ONLY':True},not_authorized=['ACTUAL_TRAINING'])
  def triplet(value,auth_mutate=None,runtime_mutate=None):
   nonlocal counter
   counter+=1;qr=emit('request_'+str(counter)+'.json',value);a=dict(schema='bcsp-p1-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY')
   if auth_mutate:auth_mutate(a)
   ar=emit('auth_'+str(counter)+'.json',a);r=dict(schema='bcsp-p1-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'])
   if runtime_mutate:runtime_mutate(r)
   rr=emit('runtime_'+str(counter)+'.json',r);return qr,ar,rr
  authorized=entry.authorize(*triplet(q))
  check('complete authorize real metadata validators with artificial 420 rows',len(authorized[3])==315 and authorized[1]['counts']['updates']==3900)
  rejects('separate execution authorization required',lambda:entry.authorize(*triplet(q,lambda a:a.update(explicit_user_authorization=False))))
  rejects('authorization request hash mismatch',lambda:entry.authorize(*triplet(q,lambda a:a.update(request_sha256='0'*64))))
  rejects('runtime one-way hash mismatch',lambda:entry.authorize(*triplet(q,runtime_mutate=lambda r:r.update(authorization_sha256='0'*64))))
  for name,change in [('M0 not authorized by first T0 request',lambda x:x.update(variant='M0')),('Fold D rejected',lambda x:x.update(fold='D')),('16k input rejected',lambda x:x.update(n_input=16384)),('policy absence rejected',lambda x:x.pop('numeric_policy')),('policy hash drift rejected',lambda x:x['numeric_policy'].update(sha256='0'*64)),('dependency drift rejected',lambda x:x.update(dependencies=[{'drift':True}])),('environment drift rejected',lambda x:x.update(environment={'ARTIFICIAL_ONLY':'2'})),('unexpected reverse binding rejected',lambda x:x.update(runtime_sha256='0'*64))]:
   bad=copy.deepcopy(q);change(bad);rejects(name,lambda:entry.authorize(*triplet(bad)))
  selected=authorized[3];fold=authorized[4]
  paths=entry.payload_paths(F/'data',selected);check('315 allowlisted train payload paths without opening files',len(paths)==315 and not any(p.exists() for p in paths))
  bad=copy.deepcopy(selected);bad[0]['point_path']='../outside.npz';rejects('payload traversal rejected',lambda:entry.payload_paths(F/'data',bad))
  for bad_path in ('/outside.npz','C:/outside.npz','points\\outside.npz','points/./outside.npz'):
   bad=copy.deepcopy(selected);bad[0]['point_path']=bad_path;rejects('noncanonical payload rejected '+bad_path,lambda:entry.payload_paths(F/'data',bad))
  bad=copy.deepcopy(selected);bad[1]['point_path']=bad[0]['point_path'];rejects('duplicate payload path rejected',lambda:entry.payload_paths(F/'data',bad))
  # Reuse exactly the real file-policy class AST; never import its GPU helper main.
  hs=(G/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py').read_text(encoding='utf-8');node=next(n for n in ast.parse(hs).body if isinstance(n,ast.ClassDef) and n.name=='FilePolicy')
  ns=dict(Path=Path,os=os,PAYLOAD={'.npz','.npy','.nrrd','.nii','.stl','.ply','.pth','.pt','.ckpt'},require=entry.require)
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen_file_policy>','exec'),ns)
  class UTC:
   calls=0
   def allow(self,p,write=False):
    if p not in ('/usr/share/zoneinfo/UTC','/usr/share/zoneinfo/Etc/UTC'):return False
    self.calls+=1;entry.require(not write,'UTC writes forbidden');return True
  utc=UTC();helper=types.SimpleNamespace(FilePolicy=ns['FilePolicy'],PAYLOAD=ns['PAYLOAD']);policy_object=entry.make_training_policy(helper,[F],F/'owned',paths,utc)
  policy_object.check('/usr/share/zoneinfo/UTC');check('UTC exact exception precedes generic link/path processing',utc.calls==1)
  rejects('UTC exception is read-only',lambda:policy_object.check('/usr/share/zoneinfo/UTC',True))
  policy_object.check(next(iter(paths)));check('exact training NPZ read allowed',True)
  rejects('training NPZ writes rejected',lambda:policy_object.check(next(iter(paths)),True))
  rejects('development NPZ rejected',lambda:policy_object.check(F/'dev.npz'))
  rejects('other checkpoint rejected',lambda:policy_object.check(F/'owned'/'other.pth',True))
  policy_object.check(F/'owned'/'ckpt-last.pth',True);check('only final checkpoint permitted',True)
  rejects('secret path rejected',lambda:policy_object.check(F/'.aws'/'config'))
  # Full frozen lifecycle with tiny CPU tensors, no NPZ loader or real model.
  tools=types.ModuleType('tools');tools.__path__=[];sys.modules['tools']=tools
  module('tools.bcsp_adapter',G/'implementation_candidate_v4/overlay/tools/bcsp_adapter.py')
  runtime=entry.load_bound('cpu_frozen_P1_runtime',impl['runtime'])
  class Dataset(torch.utils.data.Dataset):
   def __init__(self,root,records,sources,n_input):self.records=records;entry.require(len(records)==315 and len(sources)==63 and n_input==8192,'synthetic dataset dispatch')
   def __len__(self):return 315
   def __getitem__(self,i):return torch.ones(1),torch.full((1,),.5),self.records[i]['case_id'],self.records[i]['source_id']
  runtime.BCSPDataset=Dataset
  helper=types.SimpleNamespace(validate_model=lambda model:None,assert_numeric=lambda t:None,state_sha=state_sha)
  calls=[]
  class Factory:
   def build_model(self,builder,variant,seed):calls.append((variant,seed));return builder(),dict(variant=variant,artificial_fixture=False,common_state_unchanged=True)
  qq=copy.deepcopy(q);qq['output']=str(OUT/'artificial_lifecycle');budget=ArtificialBudget(qq['output']);knn=[]
  result=entry.dispatch_training(qq,static,selected,fold,plan,factory=Factory(),model_builder=Tiny,runtime=runtime,helper=helper,budget=budget,torch=torch,knn_enable=lambda:knn.append(True),expected_factory=expected,device='cpu')
  check('T0 dispatch calls factory once with seed zero',calls==[('T0',0)])
  check('actual frozen CPU lifecycle exact 3900 committed updates',result['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100))
  check('full CPU lifecycle exact exposures and traversals',result['traversals']==100 and result['case_exposures']==31200 and result['optimizer_updates']==3900)
  exposure=json.loads((Path(qq['output'])/'exposure.json').read_bytes());check('300 drop events and source-case exposure agreement',sum(exposure['dropped_case'].values())==300 and sum(exposure['case'].values())==sum(exposure['source'].values())==31200)
  metrics=[json.loads(s) for s in (Path(qq['output'])/'metrics.jsonl').read_text().splitlines()]
  check('actual CPU batch order and LR BN schedule preserved',len(metrics)==3900 and all(r['case_ids']==plan['epochs'][r['epoch']]['batches'][r['batch']] and r['BN_momentum']==max(.9*.5**(r['epoch']/21),.01) and all(abs(l-.0001*max(.9**(r['epoch']/21),.02))<1e-15 for l in r['LR']) for r in metrics))
  check('resource callback count 3902 and before-final order',len(budget.records)==3902 and budget.records[-2:]==[('before_final',3900),('after_final',3900)])
  construction=json.loads((Path(qq['output'])/'model_construction.json').read_bytes());identity_record=json.loads((Path(qq['output'])/'run_identity.json').read_bytes())
  check('construction written after claim and before step without output contract conflict',construction['factory']==expected and identity_record['stage']=='CRANIAL_BCSP_MAMBA_P1' and identity_record['prior_v3_status']=='FAILED_STOP_NO_RETRY')
  check('tiny checkpoint saved and hash verified no checkpoint load',entry.sha(Path(qq['output'])/'ckpt-last.pth')==result['checkpoint_sha256'] and not result['bncal_executed'] and not result['evaluation_executed'] and not result['resume'])
  # M0 dispatch control is checked without creating/authorizing a production M0 request.
  once=[]
  mock_runtime=types.SimpleNamespace(BCSPDataset=Dataset,make_loader=lambda *a:None,train_lifecycle=lambda *a,**k:once.append(k) or {'ARTIFICIAL_M0_DISPATCH_ONLY':True})
  mq=copy.deepcopy(qq);mq['variant']='M0';mb=types.SimpleNamespace()
  entry.dispatch_training(mq,static,selected,fold,plan,factory=Factory(),model_builder=Tiny,runtime=mock_runtime,helper=helper,budget=mb,torch=torch,knn_enable=lambda:None,expected_factory=dict(variant='M0',artificial_fixture=False,common_state_unchanged=True),device='cpu')
  check('M0 factory dispatch reaches only supplied runtime once',calls[-1]==('M0',0) and len(once)==1 and once[0]['device']=='cpu')
  rejects('initialization drift stops before training runtime',lambda:entry.dispatch_training(qq,static,selected,fold,plan,factory=Factory(),model_builder=Tiny,runtime=mock_runtime,helper=helper,budget=mb,torch=torch,knn_enable=lambda:None,expected_factory={},device='cpu'))
  check('mismatch does not retry or call runtime',len(once)==1)
  def failure(*args,**kwargs):once.append('failure');raise RuntimeError('ARTIFICIAL runtime failure')
  mock_runtime.train_lifecycle=failure
  rejects('runtime failure propagates without fallback',lambda:entry.dispatch_training(qq,static,selected,fold,plan,factory=Factory(),model_builder=Tiny,runtime=mock_runtime,helper=helper,budget=mb,torch=torch,knn_enable=lambda:None,expected_factory=expected,device='cpu'))
  check('runtime failure only one call',once[-1]=='failure' and len(once)==2)
  # The unchanged resource class runs against artificial telemetry, never torch.cuda.
  class FakeCUDA:
   def reset_peak_memory_stats(self,n):pass
   def synchronize(self):pass
   def max_memory_allocated(self,n):return 1
   def max_memory_reserved(self,n):return 2
  telemetry_dir=OUT/'telemetry';telemetry_dir.mkdir();fake_t=types.SimpleNamespace(cuda=FakeCUDA());fake_h=types.SimpleNamespace(smi=lambda key,*args:['999999'] if key=='pid' else ['1'])
  resource=entry.TrainingBudget(entry.RESOURCES,telemetry_dir,fake_t,fake_h);resource.local=lambda:(256,0);resource.sample('artificial',0)
  row=json.loads((telemetry_dir/'resources.jsonl').read_text());check('PID telemetry mismatch does not reintroduce namespace block',row['resource_guard_passed'] and row['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE')
  resource.torch.cuda.max_memory_allocated=lambda n:entry.RESOURCES['torch_peak_bytes']+1
  rejects('unchanged memory ceiling enforced',lambda:resource.sample('artificial_fail',1))
  row=json.loads((telemetry_dir/'resources.jsonl').read_text().splitlines()[-1]);check('failed resource sample persisted before stopping',not row['resource_guard_passed'] and 'allocated_within_limit' in row['failed_checks'])
  resource.records=3902;resource.torch.cuda.max_memory_allocated=lambda n:1;rejects('3902 resource-record cap retained',lambda:resource.sample('cap',3900))
  old=ast.parse((source/'bcsp_training_entry_research_v5.py').read_text(encoding='utf-8'));new=ast.parse((HERE/'bcsp_p1_training_entry_v1.py').read_text(encoding='utf-8'))
  get=lambda tree:next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='TrainingBudget')
  check('resource TrainingBudget AST exactly inherited',ast.dump(get(old),include_attributes=False)==ast.dump(get(new),include_attributes=False))
  check('entry contains no optimizer step or torch checkpoint load',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('step','AdamW','Adam','load') and isinstance(n.func.value,ast.Name) and n.func.value.id in ('optimizer','torch') for n in ast.walk(new)))
  entry.PINNED_EVIDENCE.clear();entry.PINNED_EVIDENCE.update(production_pins);entry.QUANT_REQUEST_SHA=production_quant
  check('production evidence pins restored after artificial authorize tests',entry.PINNED_EVIDENCE==production_pins and entry.QUANT_REQUEST_SHA==production_quant)
  result=dict(status='ARTIFICIAL_CPU_P1_TRAINING_ENTRY_CONTRACTS_PASS',count=len(checks),checks=checks,torch_version=torch.__version__,artificial_CPU_optimizer_updates=3900,real_training_runs=0,GPU_calls=0,server_calls=0,actual_Mamba_calls=0,actual_AdaPoinTr_calls=0,real_payload_reads=0,test_only_evidence_pins_temporarily_replaced=True,production_source_unmodified=True,limitations=['Tiny CPU model and artificial metadata only; not CUDA or native model equivalence','Full frozen lifecycle executed on tiny tensors with mocked payload loader and resource callbacks','Native resource class separately checked with artificial telemetry; no GPU preflight repeated'])
  with (OUT/'result_v1.json').open('x') as f:json.dump(result,f,indent=2)
  print(json.dumps(result))
 except BaseException as exc:
  with (OUT/'failure_v1.json').open('x') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc)),f,indent=2)
  raise
 finally:
  entry.PINNED_EVIDENCE.clear();entry.PINNED_EVIDENCE.update(production_pins);entry.QUANT_REQUEST_SHA=production_quant
if __name__=='__main__':main()
