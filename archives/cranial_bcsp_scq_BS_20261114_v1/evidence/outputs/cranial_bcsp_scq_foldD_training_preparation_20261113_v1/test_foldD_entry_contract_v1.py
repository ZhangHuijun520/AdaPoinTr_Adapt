"""Bounded CPU/std-library FoldD contract checks; no model imports, payloads or training."""
from pathlib import Path
from types import SimpleNamespace
import ast,json,hashlib,importlib.util,sys,copy,traceback
O=Path(__file__).resolve().parent;R=O.parents[1];B=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1';D=O/'CPU_contract_v1';D.mkdir()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_bytes())
def emit(p,j):
 with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2)
checks=[]
def check(n,v=True):checks.append(n) if v else (_ for _ in ()).throw(AssertionError(n))
def reject(n,fn):
 try:fn()
 except (ValueError,RuntimeError,AssertionError,KeyError):checks.append(n);return
 raise AssertionError('unexpected accept '+n)
try:
 ctx=read(O/'FoldD_context_v1.json');q=ctx['candidate'];mirror={k:Path(v) for k,v in ctx['mirror'].items()};entry=O/'bcsp_scq_foldD_training_entry_v1.py'
 spec=importlib.util.spec_from_file_location('SCQ_D_contract_entry',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
 original=e.exact;e.exact=lambda r:original(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else original(r)
 source=e.source_module
 def module(name,r):
  m=source(name,r)
  if name=='bcsp_training_contract_v1':
   f=m.exact;m.exact=lambda r:f(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else f(r)
  return m
 e.source_module=module
 real_bound=e.bound;memory={};counter=0
 def bound(r):return memory[r['path']] if r['path'].startswith('ARTIFICIAL_MEMORY_') else real_bound(r)
 e.bound=bound
 def mem(j):
  global counter
  counter+=1;name='ARTIFICIAL_MEMORY_'+str(counter);raw=json.dumps(j,sort_keys=True).encode();memory[name]=j;return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 q['P3']=mem(dict(status='SCQ_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=q['implementation']['entry']['sha256'],bridge_sha256=q['implementation']['bridge']['sha256'],native_admission_sha256=e.ADMISSION_SHA))
 def authorize(value,am=None,rm=None):
  sys.modules.pop('bcsp_training_contract_v1',None);qr=mem(value);a=dict(schema='bcsp-scq-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL MEMORY CONTRACT ONLY')
  if am:am(a)
  ar=mem(a);runtime=dict(schema='bcsp-scq-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'])
  if rm:rm(runtime)
  return e.authorize(qr,ar,mem(runtime))
 v=authorize(q);_,static,metadata,selected,fold,plan,admission,common=v
 check('actual D full authorize real native admission and locked QC',len(selected)==315 and len(fold['train_sources'])==63 and plan['case_ids']==fold['train_case_ids'])
 pair=read(B/'SCQ_BS_CD_pair_contract_v1.json');check('D frozen before C training no config adaptation',q['QC']==pair['FoldD']['QC'] and q['order_plan']==pair['FoldD']['order_plan'] and q['data_root']==pair['FoldD']['data_root'] and q['static_config']==pair['static_config'] and q['identity']==pair['identity'])
 check('exact3900updates31200exposures300drop',static['counts']==e.COUNTS and static['resources']==e.RESOURCES and len(plan['epochs'])==100 and sum(len(r['batches']) for r in plan['epochs'])==3900 and sum(len(r['dropped']) for r in plan['epochs'])==300)
 for key,value in [('fold','C'),('variant','F'),('n_input',16384),('seed',1),('status','AUTHORIZED'),('execution_authorized',True),('run_id','SCQ_B_foldC_seed0_train_fake')]:
  bad=copy.deepcopy(q);bad[key]=value;reject('reject contract drift '+key,lambda bad=bad:authorize(bad))
 reject('separate authorization mandatory',lambda:authorize(q,lambda a:a.update(explicit_user_authorization=False)))
 reject('reverse receipt binding rejected',lambda:authorize(q,lambda a:a.update(runtime_sha256='0'*64)))
 reject('runtime one way wrong SHA rejected',lambda:authorize(q,rm=lambda r:r.update(authorization_sha256='0'*64)))
 for key in ['identity','QC','order_plan','data_root','runtime']:
  bad=copy.deepcopy(q)
  if key=='identity':bad[key]['gpu_uuid']='GPU-UNAUTHORIZED'
  elif key=='QC':bad[key]=pair['FoldC']['QC']
  elif key=='order_plan':bad[key]=pair['FoldC']['order_plan']
  elif key=='data_root':bad[key]=pair['FoldC']['data_root']
  else:bad['implementation']['runtime']['sha256']='0'*64
  reject('no cross fold or identity drift '+key,lambda bad=bad:authorize(bad))
 sq=copy.deepcopy(q);sq['variant']='S';sq['run_id']=q['run_id'].replace('SCQ_B_','SCQ_S_',1);sq['output']=q['output'].replace('SCQ_B_','SCQ_S_',1)
 reject('S_D without B_D formal freeze rejected',lambda:authorize(sq))
 sq['paired_baseline']=dict(audit=mem(dict(status='FORMAL_SCQ_POST_TRAINING_FREEZE_AUDIT_PASS',variant='B',fold='D',updates=3900,identity=q['identity'],order_sha256=metadata.canonical_sha(plan))),construction=mem(dict(common_initial_state_SHA256=common)))
 check('future S_D accepts only matched synthetic D gate',authorize(sq)[0]['variant']=='S')
 ba=copy.deepcopy(memory[sq['paired_baseline']['audit']['path']]);ba['fold']='C';sq['paired_baseline']['audit']=mem(ba);reject('C baseline cannot authorize S_D',lambda:authorize(sq))
 check('315 exact D train allowlist metadata only',len(e.payload_paths(q['data_root'],selected))==315)
 script=e.render_launcher(q,'a'*64,'b'*64,'c'*64);check('launcher exact86400seconds POSIX parent before redirect','--kill-after=5s 86400s' in script and script.index('mkdir -p')<script.index(' >') and '\\' not in script.replace('\\n','') and max(len(s.encode()) for s in script.splitlines())<=2048)
 # Actual D run_identity and3900 final guard, without torch/budget/GPU execution.
 class Parent:
  class TrainingBudget:
   def __init__(self,limits,out,torch,helper):self.output=Path(out);self.output.mkdir();self.final_calls=0
   def before_step(self,n):pass
   def before_final(self):self.final_calls+=1
   def after_step(self,n):pass
 budget=e.make_budget(Parent,e.RESOURCES,D/'synthetic_log',None,None,q,plan);budget.first_step_evidence={'ARTIFICIAL':True};budget.pending_geometry=None;budget.pending_losses={};budget.logged_geometry=0;budget.before_step(0)
 check('D actual emitted run identity foldD',read(budget.output/'run_identity.json')['fold']=='D')
 reject('finalization before3900 still fails',budget.before_final);budget.logged_geometry=3900;budget.before_final();check('exact3900 finalization unchanged',budget.final_calls==1)
 ta=ast.parse((B/'UTC_order_hotfix_v2/bcsp_scq_training_entry_v2.py').read_text(encoding='utf-8'));tb=ast.parse(entry.read_text(encoding='utf-8'))
 for n in ta.body:
  if isinstance(n,ast.FunctionDef) and n.name not in ['authorize','make_budget']:
   d=next(t for t in tb.body if isinstance(t,ast.FunctionDef) and t.name==n.name);assert ast.dump(n,include_attributes=False)==ast.dump(d,include_attributes=False)
 check('model dispatch main UTC policy and bridge path AST inherited unchanged',True)
 results=dict(status='FOLDD_TRAINING_ENTRY_CPU_CONTRACT_PASS',count=len(checks),checks=checks,entry=rec(entry),test=rec(Path(__file__)),order_canonical_sha256=metadata.canonical_sha(plan),train_sources=63,train_cases=315,counts=e.COUNTS,resources=e.RESOURCES,model_imports=0,real_payload_reads=0,optimizer_steps=0,GPU_calls=0,server_operations=0,limitations=['Real frozen metadata/native admission and actual authorize path verified via exact byte mirrors; authorization controls only in memory.','No new model CPU forward; unchanged model dispatch/policy/lifecycle inherit earlier CPU and real CUDA evidence.','Current server identity/resources and315 D train hashes remain to be checked after execution authorization.'])
 emit(D/'result_v1.json',results);print(json.dumps(dict(status='PASS',checks=len(checks))))
except BaseException as exc:
 emit(D/'failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise
