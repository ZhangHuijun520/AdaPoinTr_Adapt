"""One artificial CPU entry/bridge/policy batch. No real optimizer lifecycle or GPU."""
from pathlib import Path
from types import SimpleNamespace
import ast,json,hashlib,copy,importlib.util,sys,traceback,subprocess
import torch
from torch import nn
O=Path(__file__).resolve().parent;R=O.parents[1];D=O/'cpu_batch_v2';F=D/'ARTIFICIAL_FIXTURES'
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main():
 D.mkdir();F.mkdir();checks=[];torch.set_num_threads(2)
 def check(n,v=True):
  assert bool(v),n
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError,KeyError,AssertionError):checks.append(n);return
  raise AssertionError('unexpected accept '+n)
 def write(name,j):
  p=F/name
  with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2)
  return rec(p)
 try:
  e=load('scq_training_entry_cpu',O/'bcsp_scq_training_entry_v1.py');bridge=load('scq_bridge_cpu',O/'bcsp_scq_training_bridge_v1.py')
  ctx=json.loads((O/'training_context_candidate_v1.json').read_bytes());q=copy.deepcopy(ctx['request_candidate']);q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['implementation']['entry']=dict(q['implementation']['entry'],**{k:rec(O/'bcsp_scq_training_entry_v1.py')[k] for k in ['bytes','sha256']})
  mirror={k:Path(v) for k,v in ctx['mirror'].items()};mirror.update({q['implementation']['entry']['path']:O/'bcsp_scq_training_entry_v1.py',q['implementation']['bridge']['path']:O/'bcsp_scq_training_bridge_v1.py'})
  g=R/'outputs/cranial_bcsp_scq_cuda_preparation_20261113_v1';m=R/'outputs/cranial_bcsp_scq_implementation_20261113_v1'
  for k,p in [('encoder',R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_mamba_encoder_v1.py'),('factory',R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_model_factory_v1.py'),('lqi_decoder',R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1/bcsp_lqi_decoder_v1.py'),('lqi_factory',R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1/bcsp_lqi_factory_v1.py'),('scq_residual',m/'bcsp_scq_residual_v1.py'),('scq_factory',m/'bcsp_scq_factory_v1.py'),('preflight_helper',R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'),('timezone',R/'outputs/cranial_bcsp_mamba_p1_20261104/gpu_admission_v3/exact_utc_resource_v1.py'),('native_helper',R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_native_prediction_implementation_v1/bcsp_lqi_twofold_native_predict_v1.py'),('cuda_entry',g/'bcsp_scq_cuda_admission_v3.py')]:
   assert rec(p)['sha256']==q['implementation'][k]['sha256'];mirror[q['implementation'][k]['path']]=p
  mirror[q['initialization']['path']]=m/'initialization_v1.bin'
  p3=write('ARTIFICIAL_P3.json',dict(status='SCQ_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=q['implementation']['entry']['sha256'],bridge_sha256=q['implementation']['bridge']['sha256'],native_admission_sha256=e.ADMISSION_SHA));q['P3']=p3
  original_exact=e.exact
  e.exact=lambda r:original_exact(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else original_exact(r)
  original_source_module=e.source_module
  def fixture_source_module(name,record):
   module=original_source_module(name,record)
   if name=='bcsp_training_contract_v1':
    metadata_exact=module.exact
    module.exact=lambda r:metadata_exact(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else metadata_exact(r)
   return module
  e.source_module=fixture_source_module
  sequence=0
  def authorize(value,auth_change=None,runtime_change=None):
   nonlocal sequence
   sequence+=1;sys.modules.pop('bcsp_training_contract_v1',None)
   qr=write('ARTIFICIAL_q'+str(sequence)+'.json',value)
   auth=dict(schema='bcsp-scq-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL CPU ONLY NOT ACTUAL EXECUTION APPROVAL')
   if auth_change:auth_change(auth)
   ar=write('ARTIFICIAL_a'+str(sequence)+'.json',auth)
   rt=dict(schema='bcsp-scq-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'])
   if runtime_change:runtime_change(rt)
   return e.authorize(qr,ar,write('ARTIFICIAL_r'+str(sequence)+'.json',rt))
  result=authorize(q);_,static,metadata,selected,fold,plan,admission,common=result
  check('actual full authorize with real frozen CUDA and metadata',len(selected)==315 and len(fold['train_sources'])==63 and static['counts']==e.COUNTS and static['resources']==e.RESOURCES)
  check('original full100x39 order validated without payload',len(plan['epochs'])==100 and sum(len(r['batches']) for r in plan['epochs'])==3900)
  for key,value in [('variant','F'),('fold','D'),('n_input',16384),('seed',1),('status','AUTHORIZED'),('execution_authorized',True)]:
   bad=copy.deepcopy(q);bad[key]=value;reject('contract drift rejected '+key,lambda bad=bad:authorize(bad))
  reject('no separate authorization rejected',lambda:authorize(q,lambda a:a.update(explicit_user_authorization=False)))
  reject('reverse receipt binding rejected',lambda:authorize(q,lambda a:a.update(runtime_sha256='0'*64)))
  reject('wrong one-way runtime rejected',lambda:authorize(q,runtime_change=lambda r:r.update(authorization_sha256='0'*64)))
  for key in ['identity','admission','implementation']:
   bad=copy.deepcopy(q)
   if key=='identity':bad['identity']['gpu_uuid']='GPU-OTHER'
   elif key=='admission':bad['admission']['audit']['sha256']='0'*64
   else:bad['implementation']['runtime']['sha256']='0'*64
   reject('frozen '+key+' drift rejected',lambda bad=bad:authorize(bad))
  sq=copy.deepcopy(q);sq['variant']='S';sq['run_id']=q['run_id'].replace('SCQ_B_','SCQ_S_',1);sq['output']=q['output'].replace('SCQ_B_','SCQ_S_',1);reject('S before formal B freeze rejected',lambda:authorize(sq))
  ba=write('ARTIFICIAL_B_freeze.json',dict(status='FORMAL_SCQ_POST_TRAINING_FREEZE_AUDIT_PASS',variant='B',fold='C',updates=3900,identity=q['identity'],order_sha256=metadata.canonical_sha(plan)))
  bc=write('ARTIFICIAL_B_construction.json',dict(common_initial_state_SHA256=common));sq['paired_baseline']=dict(audit=ba,construction=bc)
  check('future S interface requires matched B evidence',authorize(sq)[0]['variant']=='S')
  allowed=e.payload_paths(q['data_root'],selected);check('315 exact train path allowlist metadata only',len(allowed)==315)
  badsel=copy.deepcopy(selected);badsel[0]['point_path']='../development.npz';reject('payload escape rejected',lambda:e.payload_paths(q['data_root'],badsel))
  badsel=copy.deepcopy(selected);badsel[1]=badsel[0];reject('duplicate payload rejected',lambda:e.payload_paths(q['data_root'],badsel))
  script=e.render_launcher(q,'a'*64,'b'*64,'c'*64)
  check('launcher POSIX parent before redirect and exact timeout',script.index('mkdir -p')<script.index(' >') and '--kill-after=5s 86400s' in script and '\\' not in script.replace('\\n','') and max(len(x.encode()) for x in script.splitlines())<=2048)
  reject('launcher abbreviated hash rejected',lambda:e.render_launcher(q,'a'*8,'b'*64,'c'*64))
  # Original runtime optimizer grouping; never construct AdamW or run its lifecycle.
  runtime_path=mirror[q['implementation']['runtime']['path']];rtree=ast.parse(runtime_path.read_text(encoding='utf-8'));group_fn=next(n for n in rtree.body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups');genv=dict(require=e.require);exec(compile(ast.Module([group_fn],[]),'original_optimizer_groups_only','exec'),genv)
  sys.path.insert(0,str(m));residual=load('bcsp_scq_residual_v1',m/'bcsp_scq_residual_v1.py');init=rec(m/'initialization_v1.bin')
  knn=lambda k,s,q:torch.cdist(q,s).topk(k,largest=False,sorted=False).indices
  class Tiny(nn.Module):
   def __init__(self,variant):
    super().__init__();self.base_model=nn.Module();b=self.base_model;b.coarse_pred=nn.Linear(3,768);b.mem=nn.Linear(3,384);b.global_head=nn.Linear(3,1024)
    self.flagged=nn.Parameter(torch.randn(2,2));self.flagged._no_weight_decay=True
    self.loss_func=nn.MSELoss();self.fine_loss_func=nn.MSELoss();self.f0_evidence=dict(artificial_fixture=True);self.seen_input=None
    if variant=='S':b.scq=residual.SCQResidual('S',knn,init)
   def forward(self,x):
    self.seen_input=x;z=x.mean(1);q0=self.base_model.coarse_pred(z).reshape(-1,256,3)
    if hasattr(self.base_model,'scq'):q0,self.base_model._scq_last_info=self.base_model.scq(x[:,:256],self.base_model.mem(x[:,:256]),self.base_model.global_head(z),q0)
    p=q0.repeat_interleave(32,1);return q0,q0[:,:0],p[:,:0],p
   def get_loss(self,ret,target,epoch,partial=None):
    return ret[-1].new_zeros(()),self.loss_func(ret[0],target[:,::32])+self.fine_loss_func(ret[-1],target)
  def build(variant):
   with torch.random.fork_rng(devices=[]):torch.manual_seed(901);return Tiny(variant)
  group_model=build('S');groups,rows=genv['optimizer_groups'](group_model);decays={r['name']:r['weight_decay'] for r in rows}
  check('original grouping handles4 SCQ parameters exactly',all(decays['base_model.scq.'+n]==v for n,v in [('W1.weight',.0005),('W2.weight',.0005),('W1.bias',0),('W2.bias',0)]))
  check('original explicit SSM no-decay marker retained',decays['flagged']==0 and next(r for r in rows if r['name']=='flagged')['reason']=='explicit_no_weight_decay')
  def tensor_sha(t):return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
  helper=SimpleNamespace(tensor_sha=tensor_sha,validate_model=lambda model:None,assert_numeric=lambda t:None,state_sha=lambda *args:'ARTIFICIAL_STATE_ONLY')
  class BudgetParent:
   class TrainingBudget:
    def __init__(self,limits,out,torch,helper):self.output=Path(out);self.output.mkdir();self.final_calls=0
    def before_step(self,step):pass
    def after_step(self,step):pass
    def before_final(self):self.final_calls+=1
  g=torch.Generator().manual_seed(120);partial=torch.randn(8,8192,3,generator=g)*.3;target=torch.randn(8,8192,3,generator=g)*.3
  class RuntimeSpy:
   optimizer_groups=staticmethod(genv['optimizer_groups'])
   class BCSPDataset:
    def __init__(self,root,records,sources,n):assert len(records)==315 and len(sources)==63 and n==8192
   @staticmethod
   def make_loader(dataset,plan,epoch):return dict(ARTIFICIAL=True,epoch=epoch)
   @staticmethod
   def train_lifecycle(model,loader_factory,records,plan,out,**kwargs):
    assert loader_factory(0)==dict(ARTIFICIAL=True,epoch=0);budget=kwargs['resources'];model.train();budget.before_step(0)
    ret=model(partial);_,loss=model.get_loss(ret,target,0,partial=partial);loss.backward();budget.after_step(1)
    assert model.seen_input is partial
    return dict(status='ARTIFICIAL_ONE_FORWARD_BACKWARD_ONLY',optimizer_steps=0)
  class BridgeSpy:
   @staticmethod
   def train_lifecycle(runtime,sha,model,*args,**kwargs):kwargs.pop('admission');return runtime.train_lifecycle(model,*args,**kwargs)
  for variant in ['B','S']:
   sample=build(variant);before={n:tensor_sha(t) for n,t in sample.state_dict().items() if not n.startswith('base_model.scq.')};fingerprint=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()
   localq=copy.deepcopy(q);localq['variant']=variant;localq['output']=str(F/('dispatch_'+variant))
   budget=e.make_budget(BudgetParent,e.RESOURCES,localq['output'],torch,helper,localq,plan)
   def factory_spy(builder,v,initializer):return build(v),dict(parent=dict(artificial_fixture=True))
   result=e.dispatch_training(localq,selected,fold,plan,factory=factory_spy,model_builder=lambda:None,runtime=RuntimeSpy,bridge=BridgeSpy,admission=admission,expected_common=fingerprint,helper=helper,budget=budget,torch=torch,knn_enable=lambda:None,device='cpu',artificial_cpu=True)
   log=[json.loads(s) for s in (Path(localq['output'])/'SCQ_geometry.jsonl').read_text().splitlines()]
   check('actual dispatch hooks original losses geometry '+variant,result['optimizer_steps']==0 and len(log)==1 and log[0]['case_ids']==plan['epochs'][0]['batches'][0] and set(log[0]['loss_components'])=={'coarse_CD','dense_CD'} and 'Q0' in log[0]['geometry'] and 'delta' in log[0]['geometry'])
   reject('finalization before3900 denied '+variant,budget.before_final)
   budget.logged_geometry=3900;budget.before_final();check('exact3900 finalization guard '+variant,budget.final_calls==1)
  # Actual bridge signature and authorization gates, using an inert runtime spy.
  calls=[];inert=SimpleNamespace(__file__=str(runtime_path),train_lifecycle=lambda *args,**kwargs:(calls.append(kwargs) or 'DELEGATED_NOT_EXECUTED'))
  fake=SimpleNamespace(f0_evidence=dict(artificial_fixture=False))
  check('actual bridge delegates pinned runtime without changing kwargs',bridge.train_lifecycle(inert,q['implementation']['runtime']['sha256'],fake,admission=admission,device='cuda:0',foo=7)=='DELEGATED_NOT_EXECUTED' and calls[0]==dict(device='cuda:0',foo=7))
  reject('bridge CPU production denied',lambda:bridge.train_lifecycle(inert,q['implementation']['runtime']['sha256'],fake,admission=admission,device='cpu'))
  reject('bridge fixture production denied',lambda:bridge.train_lifecycle(inert,q['implementation']['runtime']['sha256'],SimpleNamespace(f0_evidence=dict(artificial_fixture=True)),admission=admission,device='cuda:0'))
  reject('bridge wrong runtime hash denied',lambda:bridge.train_lifecycle(inert,'0'*64,fake,admission=admission,device='cuda:0'))
  # Fresh child runs actual nested training file policy and actual six source imports.
  owned=F/'policy_owned';owned.mkdir();config=dict(entry=rec(O/'bcsp_scq_training_entry_v1.py'),cuda=rec(g/'bcsp_scq_cuda_admission_v3.py'),native=rec(mirror[q['implementation']['native_helper']['path']]),budget=rec(mirror[q['implementation']['budget_parent']['path']]),helper=rec(mirror[q['implementation']['preflight_helper']['path']]),implementation={k:rec(mirror[q['implementation'][k]['path']]) for k in ['encoder','factory','lqi_decoder','lqi_factory']},extra={k:rec(mirror[q['implementation'][k]['path']]) for k in ['scq_residual','scq_factory']},initialization=init,owned=str(owned.resolve()),train=str((F/'ARTIFICIAL_TRAIN.npz').resolve()),dev=str((F/'ARTIFICIAL_DEV.npz').resolve()))
  config_record=write('ARTIFICIAL_policy.json',config)
  child='''import ast,json,sys,types,importlib.util
from pathlib import Path
import torch
c=json.loads(Path(sys.argv[1]).read_bytes())
def load(n,r):
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
e=load('policy_entry',c['entry']);cu=load('policy_cuda',c['cuda']);native=load('policy_native',c['native']);budget=load('policy_budget',c['budget']);helper=load('policy_helper',c['helper'])
guard=cu.ExactSCQReads(native.ExactSourceReads(c['implementation']),list(c['extra'].values())+[c['initialization']])
roots=[];out=Path(c['owned']);allowed={Path(c['train']):'ARTIFICIAL_HASH'};utc=types.SimpleNamespace(allow=lambda *a:False)
base_policy=budget.make_training_policy(helper,roots,out,allowed,utc)
t=ast.parse(Path(c['entry']['path']).read_text(encoding='utf-8'));node=next(n for n in ast.walk(t) if isinstance(n,ast.ClassDef) and n.name=='Policy');env=dict(base_policy=base_policy,guard=guard);exec(compile(ast.Module([node],[]),'actual_nested_training_policy','exec'),env);policy=env['Policy'](roots,out)
policy.check(17,False);policy.check(c['train'],False);policy.check(out/'ckpt-last.pth',True)
for p,w in [(c['dev'],False),(c['train'],True),(out/'other.pth',False),(c['extra']['scq_factory']['path'],True),(c['initialization']['path'],True)]:
 try:policy.check(p,w)
 except (ValueError,RuntimeError):pass
 else:raise AssertionError('policy accepted forbidden path')
sys.addaudithook(policy.audit)
for n,k in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory')]:e.source_module(n,c['implementation'][k])
r=e.source_module('bcsp_scq_residual_v1',c['extra']['scq_residual']);e.source_module('bcsp_scq_factory_v1',c['extra']['scq_factory']);assert r.load_initialization(c['initialization'])['Pfix'].shape==(7,384)
guard.close();print(json.dumps(dict(exact_SCQ_source_bin_reads=True,train_only_NPZ=True,final_only_checkpoint=True,source_writes_denied=True,integer_fd_compatible=True)))
'''
  cp=subprocess.run([sys.executable,'-I','-B','-c',child,config_record['path']],capture_output=True,timeout=30)
  for k,v in [('stdout',cp.stdout),('stderr',cp.stderr)]:
   with (D/('policy_'+k+'.bin')).open('xb') as f:f.write(v)
  check('actual training policy SCQ reads train only and fd guard',cp.returncode==0 and all(json.loads(cp.stdout).values()))
  record=dict(status='SCQ_TRAINING_ENTRY_ARTIFICIAL_CPU_PASS',count=len(checks),checks=checks,entry=rec(O/'bcsp_scq_training_entry_v1.py'),bridge=rec(O/'bcsp_scq_training_bridge_v1.py'),test=rec(Path(__file__)),torch=torch.__version__,optimizer_steps=0,CUDA_calls=0,server_operations=0,real_payload_arrays_read=0,limitations=['Real frozen metadata/QC/order and native admission evidence read; no real point payload or checkpoint.','B/S dispatch uses tiny artificial model, real SCQ residual and runtime/bridge spies; one artificial F/B per arm, no optimizer or3900-step run.','Original optimizer grouping function exercised without optimizer construction; main native training remains unexecuted.'])
  with (D/'result_v1.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
  print(json.dumps(dict(status='PASS',checks=len(checks))))
 except BaseException as exc:
  with (D/'failure_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()),f,indent=2)
  raise
if __name__=='__main__':main()
