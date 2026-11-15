"""Bounded CPU-only entry checks; main/native CUDA never run."""
import ast,copy,hashlib,importlib.util,json,random,sys,subprocess,traceback
from pathlib import Path
from types import SimpleNamespace
import torch,numpy as np
from torch import nn
O=Path(__file__).resolve().parent;R=O.parents[1];D=O/'cpu_entry_batch_v1'
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main():
 D.mkdir();checks=[];torch.set_num_threads(2)
 def check(n,v=True):
  assert bool(v),n
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError,KeyError):checks.append(n);return
  raise AssertionError('unexpected accept '+n)
 def emit(n,j):
  with (D/n).open('x',encoding='utf-8') as f:json.dump(j,f,indent=2)
 try:
  e=load('scq_entry_cpu',O/'bcsp_scq_cuda_admission_v1.py')
  check('4F4loss4B0step fixed phases',e.SCIENCE['full_forward']==e.SCIENCE['full_loss']==e.SCIENCE['full_backward']==4 and e.PHASES==[('B_eval1','B',1,False),('F_eval1','F',1,False),('S_eval1','S',1,False),('S_train8','S',8,True)])
  q=dict(schema='bcsp-scq-artificial-cuda-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,science=e.SCIENCE,phases=[list(p) for p in e.PHASES],limits=e.LIMITS,fixture=e.FIXTURE,tolerances=e.TOLERANCE,readiness=dict(fresh_reverification_required=True))
  auth=dict(schema='bcsp-scq-cuda-authorization-v1',request_sha256='a'*64,explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY')
  runtime=dict(schema='bcsp-scq-cuda-runtime-v1',request_sha256='a'*64,authorization_sha256='b'*64)
  check('actual authorize one-way contract',e.authorize(q,'a'*64,auth,'b'*64,runtime) is q)
  for key,value in [('science',dict(e.SCIENCE,full_forward=5)),('phases',[]),('limits',dict(e.LIMITS,wall_seconds=1801)),('fixture',dict(e.FIXTURE,input_seed=0)),('status','AUTHORIZED'),('readiness',dict(fresh_reverification_required=False))]:
   bad=copy.deepcopy(q);bad[key]=value;reject('contract drift denied '+key,lambda:e.authorize(bad,'a'*64,auth,'b'*64,runtime))
  reject('authorization false denied',lambda:e.authorize(q,'a'*64,dict(auth,explicit_user_authorization=False),'b'*64,runtime))
  reject('reverse hash binding denied',lambda:e.authorize(q,'a'*64,dict(auth,runtime_sha256='c'*64),'b'*64,runtime))
  reject('runtime wrong hash denied',lambda:e.authorize(q,'a'*64,auth,'c'*64,runtime))
  counts=e.counters();events=[]
  for _ in range(4):e.claim(counts,'full_forward',events.append)
  check('attempt before call four caps',len(events)==4 and counts['full_forward']==4)
  reject('fifth forward denied',lambda:e.claim(counts,'full_forward',events.append))
  reject('optimizer claim denied',lambda:e.claim(counts,'optimizer_steps',events.append))
  reject('extra decoder forward denied',lambda:e.claim(counts,'decoder_forward',events.append))
  lq=dict(project='/home/jovyan/adapointr_work/PoinTr',output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1',launch_contract=dict(request_path='/tmp/q.json',authorization_path='/tmp/a.json',runtime_path='/tmp/r.json'),limits=e.LIMITS,identity=dict(python_realpath='/opt/conda/envs/adapointr-mamba/bin/python3.10'),entry=dict(path='/tmp/entry.py'),environment=dict(PYTHONDONTWRITEBYTECODE='1'))
  rendered=e.render_launcher(lq,'a'*64,'b'*64,'c'*64)
  check('POSIX output parent before redirection exclusive output','\\' not in rendered.replace('\\n','') and rendered.index('mkdir -p')<rendered.index(' >') and 'mkdir '+lq['output']+'\n' in rendered)
  check('launcher exact timeout exit preservation','--kill-after=10s 1800s' in rendered and 'exit "$rc"' in rendered and all(len(s.encode())<=2048 for s in rendered.splitlines()))
  reject('truncated launcher hash denied',lambda:e.render_launcher(lq,'a'*8,'b'*64,'c'*64))
  def tsha(t):return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
  def state(m,parameters_only=False):return hashlib.sha256(repr([(n,tsha(t)) for n,t in (m.named_parameters() if parameters_only else m.state_dict().items())]).encode()).hexdigest()
  helper=SimpleNamespace(tensor_sha=tsha,state_sha=state)
  parent=SimpleNamespace(rng_state=lambda *args:(repr(random.getstate()),repr(np.random.get_state()),tsha(torch.get_rng_state())))
  class Proxy:
   cuda=SimpleNamespace(get_rng_state=lambda _:torch.get_rng_state(),set_rng_state=lambda s,_:torch.set_rng_state(s),synchronize=lambda:None)
   def __getattr__(self,n):return getattr(torch,n)
  prior=R/'outputs/cranial_bcsp_fullmamba_20261110/gpu_admission_v1/test_f0_cuda_entry_cpu_v1.py'
  tree=ast.parse(prior.read_text(encoding='utf-8'));run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');nodes=[n for n in run.body if isinstance(n,ast.ClassDef) and n.name in ('Gain','FullFixture')]
  env=dict(torch=torch,nn=nn);exec(compile(ast.Module(nodes,[]),'cheap_inherited_classes','exec'),env)
  class TinySCQ(nn.Module):
   def __init__(self):
    super().__init__();self.W1=nn.Linear(3,3);self.W2=nn.Linear(3,3);nn.init.zeros_(self.W2.weight);nn.init.zeros_(self.W2.bias)
   def forward(self,q):
    d=self.W2(torch.nn.functional.gelu(self.W1(q)));return q+d,dict(Q0=q.detach(),Qused=(q+d).detach(),delta=d.detach())
  class Fixture(env['FullFixture']):
   def __init__(self,variant,fail=False):
    super().__init__();self.variant=variant;self.fail=fail;self.increase_dim=nn.Linear(3,3);self.decode_head=nn.Linear(3,3)
    for b in self.base_model.decoder.blocks:b.norm_v=nn.LayerNorm(3)
    if variant!='B':self.base_model.scq=TinySCQ()
   def forward(self,x):
    self.forward_calls+=1
    if self.fail:raise RuntimeError('ARTIFICIAL_FORWARD_FAILURE')
    y=self.bn(x.transpose(1,2)).mean(-1);y=self.reduce_map(self.base_model.coarse_pred(y))+self.base_model.decoder.coordinate_pe(y)
    y=y+sum(p for n,p in self.named_parameters() if n.endswith('.weight') and p.ndim==0)
    y=y+sum(b.norm_v(y) for b in self.base_model.decoder.blocks);y=self.decode_head(self.increase_dim(y));q=y[:,None].expand(-1,256,-1)
    if self.variant!='B':q,self.base_model._scq_last_info=self.base_model.scq(q)
    dense=q[:,:1].expand(-1,8192,-1)
    return (q,q[:,:0],dense[:,:0],dense) if self.training else (q,dense)
  g=torch.Generator().manual_seed(411);x=torch.randn(8,8192,3,generator=g);target=torch.randn(8,8192,3,generator=g);counts=e.counters();journal=[];ref=None;records=[]
  for phase in e.PHASES:
   with torch.random.fork_rng(devices=[]):torch.manual_seed(0);model=Fixture(phase[1]).eval()
   before=state(model);rng=torch.get_rng_state().clone()
   record,baseline=e.phase_checks(Proxy(),np,model,helper,parent,x,target,phase,ref,counts,journal.append,lambda *args:None)
   if baseline is not None:ref=baseline
   records.append(record)
   check('actual phase loop restores state modes RNG '+phase[0],state(model)==before and not any(m.training for m in model.modules()) and torch.equal(rng,torch.get_rng_state()) and model.forward_calls==model.loss_calls==1)
  check('actual phase engine exact4F4loss4B',counts['full_forward']==counts['full_loss']==counts['full_backward']==4 and counts['optimizer_steps']==counts['decoder_forward']==counts['decoder_backward']==0)
  check('all35 shared gradient prefixes nonzero finite',all(len(r['gradients']['module_norm_sums'])==35 and all(v>0 for v in r['gradients']['module_norm_sums'].values()) for r in records))
  check('F S initial comparisons reuse same forwards',all(all(t['close'] for t in r['initial_equivalence']) for r in records[1:3]))
  check('SCQ W2 active W1 zero expected',all(r['SCQ_gradients']['W2.weight']>0 and r['SCQ_gradients']['W1.weight']==0 for r in records[1:]))
  check('B8 BN changed logged restored',bool(records[-1]['BN_changed']) and all(not r['BN_changed'] for r in records[:-1]))
  failing=Fixture('S',True).eval();before=state(failing);fc=e.counters();fj=[]
  reject('failure first forward stops no retry',lambda:e.phase_checks(Proxy(),np,failing,helper,parent,x,target,e.PHASES[-1],ref,fc,fj.append,lambda *args:None))
  check('failure counts precise and state restored',fc['full_forward']==1 and fc['full_backward']==fc['full_loss']==0 and before==state(failing) and not failing.training and fj[-1]['state_restored'])
  reject('inactive required gradient rejected',lambda:e.gradients(torch,nn.Linear(3,3),['missing']))
  # Actual finite source policy in a fresh child. No model/CUDA entry invocation.
  N=R/'outputs/cranial_bcsp_fullmamba_n0b_capture_fix_20261113_v2/post_diagnostic_freeze_v1/scope_snapshot.json';scope=json.loads(N.read_bytes())
  implementation={k:rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'/n) for k,n in [('encoder','bcsp_mamba_encoder_v1.py'),('factory','bcsp_p1_model_factory_v1.py')]}
  implementation.update({k:rec(R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1'/n) for k,n in [('lqi_decoder','bcsp_lqi_decoder_v1.py'),('lqi_factory','bcsp_lqi_factory_v1.py')]})
  impl=R/'outputs/cranial_bcsp_scq_implementation_20261113_v1'
  extra={k:rec(impl/n) for k,n in [('scq_residual','bcsp_scq_residual_v1.py'),('scq_factory','bcsp_scq_factory_v1.py'),('initialization','initialization_v1.bin')]}
  owned=D/'owned';owned.mkdir();neighbor=D/'unbound.bin';neighbor.write_bytes(b'UNBOUND')
  config=dict(entry=rec(O/'bcsp_scq_cuda_admission_v1.py'),native=rec(R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_native_prediction_implementation_v1/bcsp_lqi_twofold_native_predict_v1.py'),helper=rec(R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'),implementation=implementation,extra=extra,owned=str(owned.resolve()),neighbor=str(neighbor.resolve()))
  emit('policy_fixture_v1.json',config)
  child='''import json,sys,types,importlib.util
from pathlib import Path
import torch
c=json.loads(Path(sys.argv[1]).read_bytes())
def load(n,r):
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
e=load('child_scq_entry',c['entry']);p=load('child_native',c['native']);h=load('child_helper',c['helper'])
base=p.ExactSourceReads(c['implementation']);g=e.ExactSCQReads(base,list(c['extra'].values()))
policy=p.make_policy(h,[],Path(c['owned']),[],[],[],types.SimpleNamespace(allow=lambda *args:False),g);sys.addaudithook(policy.audit)
for n,k in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory')]:e.source_module(n,c['implementation'][k])
r=e.source_module('bcsp_scq_residual_v1',c['extra']['scq_residual']);e.source_module('bcsp_scq_factory_v1',c['extra']['scq_factory'])
values=r.load_initialization(c['extra']['initialization']);assert values['W1.weight'].shape==(384,1802)
for path,write in [(c['extra']['initialization']['path'],True),(c['extra']['scq_factory']['path'],True),(c['neighbor'],False)]:
 try:policy.check(path,write)
 except (ValueError,RuntimeError):pass
 else:raise AssertionError('unbound read or bound write allowed')
g.close();print(json.dumps(dict(actual_SCQ_imports=True,exact_bin_read=True,bound_writes_denied=True,neighbor_denied=True)))
'''
  cp=subprocess.run([sys.executable,'-I','-B','-c',child,str(D/'policy_fixture_v1.json')],capture_output=True,timeout=30)
  for k,v in [('stdout',cp.stdout),('stderr',cp.stderr)]:
   with (D/('policy_'+k+'.bin')).open('xb') as f:f.write(v)
  check('actual SCQ two-source and binary read policy',cp.returncode==0 and all(json.loads(cp.stdout).values()))
  emit('result_v1.json',dict(status='SCQ_CUDA_ENTRY_ARTIFICIAL_CPU_PASS',count=len(checks),checks=checks,entry=rec(O/'bcsp_scq_cuda_admission_v1.py'),test=rec(Path(__file__)),engine_counts=counts,phase_records=records,torch=torch.__version__,CUDA=False,server_operations=0,real_data=False,checkpoint_loads=0,limitations=['Phase engine uses cheap artificial CPU model/loss and CPU-only CUDA API facade.','Actual frozen SCQ source imports and initializer read policy exercised; no native provider/Mamba or production GPU execution.']))
  print(json.dumps(dict(status='PASS',count=len(checks))))
 except BaseException as exc:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
