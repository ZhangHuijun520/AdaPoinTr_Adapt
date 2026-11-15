"""One CPU-only entry contract batch. No main(), WSL, CUDA or real payloads."""
import ast,copy,ctypes,hashlib,importlib.util,json,random,subprocess,sys,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from torch import nn
S=Path(__file__).resolve().parent;B=S.parent;R=S.parents[2];O=S/'artificial_cpu_entry_batch_v1'
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def main():
 O.mkdir();torch.set_num_threads(2);checks=[]
 def check(n,v=True):
  if not v:raise AssertionError(n)
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (RuntimeError,ValueError,AssertionError,KeyError):checks.append(n);return
  raise AssertionError('accepted '+n)
 def emit(n,x):
  with (O/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,allow_nan=False)
 try:
  e=load('lqi_cpu_cuda_entry',S/'bcsp_lqi_cuda_admission_v1.py')
  check('01 exact2 full F2loss2B zero decoder-only and optimizer',e.SCIENCE==dict(full_forward=2,full_backward=2,full_loss=2,decoder_forward=0,decoder_backward=0,optimizer_steps=0,real_data_reads=0,checkpoint_loads=0,input_points=8192,output_points=8192,full_batches=[1,8]))
  q=dict(schema='bcsp-lqi-synthetic-cuda-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,science=copy.deepcopy(e.SCIENCE),tolerances=e.TOLERANCE,limits=e.LIMITS,fixture=e.FIXTURE,readiness=dict(identity_verified=True,inherited_assets_verified=True))
  auth=dict(schema='bcsp-lqi-cuda-authorization-v1',request_sha256='a'*64,explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_CPU_ONLY');rt=dict(schema='bcsp-lqi-cuda-runtime-v1',request_sha256='a'*64,authorization_sha256='b'*64)
  e.authorize(q,'a'*64,auth,'b'*64,rt);check('02 full actual authorize contract')
  for name,key,val in [('03 extra forward rejected','science',dict(e.SCIENCE,full_forward=3)),('04 B8 cannot silently shrink','science',dict(e.SCIENCE,full_batches=[1,1])),('05 resource threshold drift rejected','limits',dict(e.LIMITS,device_MiB=24564)),('06 fixture seed drift rejected','fixture',dict(e.FIXTURE,input_seed=0)),('07 readiness absent rejected','readiness',dict(identity_verified=False,inherited_assets_verified=True))]:
   bad=copy.deepcopy(q);bad[key]=val;reject(name,lambda:e.authorize(bad,'a'*64,auth,'b'*64,rt))
  reject('08 no explicit authorization',lambda:e.authorize(q,'a'*64,dict(auth,explicit_user_authorization=False),'b'*64,rt))
  reject('09 reverse receipt binding rejected',lambda:e.authorize(q,'a'*64,dict(auth,runtime_sha256='c'*64),'b'*64,rt))
  reject('10 wrong one-way runtime rejected',lambda:e.authorize(q,'a'*64,auth,'c'*64,rt))
  c=e.counters();events=[];e.claim(c,'full_forward',events.append);e.claim(c,'full_forward',events.append)
  check('11 claim before call exact cap',len(events)==2 and events[-1]['counts']['full_forward']==2)
  reject('12 third F denied',lambda:e.claim(c,'full_forward',events.append));reject('13 decoder-only denied',lambda:e.claim(c,'decoder_forward',events.append));reject('14 optimizer claim denied',lambda:e.claim(c,'optimizer_steps',events.append))
  launchq=dict(project='/home/jovyan/adapointr_work/PoinTr',output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1',launch_contract=dict(request_path='/tmp/q.json',authorization_path='/tmp/a.json',runtime_path='/tmp/r.json'),limits=e.LIMITS,identity=dict(python_realpath='/opt/conda/envs/adapointr-mamba/bin/python3.10'),entry=dict(path='/tmp/entry.py'),environment=dict(CUBLAS_WORKSPACE_CONFIG=':4096:8'))
  launch=e.render_launcher(launchq,'a'*64,'b'*64,'c'*64)
  check('15 POSIX parent and short lines', '\\' not in launch.replace('\\n','') and max(len(l.encode()) for l in launch.splitlines())<=2048)
  check('16 parent before redirect exclusive output',launch.index('mkdir -p')<launch.index(' >') and 'mkdir '+launchq['output']+'\n' in launch)
  check('17 timeout exitcode symlink refusal', '--kill-after=10s 1800s' in launch and 'exit "$rc"' in launch and '[ ! -L '+launchq['output']+' ] || exit 121' in launch)
  reject('18 shortened hash rejected',lambda:e.render_launcher(launchq,'a'*8,'b'*64,'c'*64))
  def tensor_sha(t):
   t=t.detach().cpu().contiguous();return hashlib.sha256(ctypes.string_at(t.data_ptr(),t.numel()*t.element_size())).hexdigest()
  def state_sha(m,parameters_only=False):return hashlib.sha256(repr([(n,tensor_sha(t)) for n,t in (m.named_parameters() if parameters_only else m.state_dict().items())]).encode()).hexdigest()
  helper=SimpleNamespace(tensor_sha=tensor_sha,state_sha=state_sha)
  parent=SimpleNamespace(rng_state=lambda *args:(repr(random.getstate()),repr(np.random.get_state()),tensor_sha(torch.get_rng_state())))
  class TorchProxy:
   cuda=SimpleNamespace(get_rng_state=lambda _:torch.get_rng_state(),set_rng_state=lambda s,_:torch.set_rng_state(s),synchronize=lambda:None)
   def __getattr__(self,n):return getattr(torch,n)
  # Reuse original lightweight full-loop fixture classes, not prior test execution.
  tree=ast.parse((B/'gpu_admission_v1/test_f0_cuda_entry_cpu_v1.py').read_text(encoding='utf-8'));run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');nodes=[n for n in run.body if isinstance(n,ast.ClassDef) and n.name in ('Gain','FullFixture')];env=dict(torch=torch,nn=nn);exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen_cheap_fixture_classes','exec'),env)
  class FullFixture(env['FullFixture']):
   def __init__(self,fail=False):
    super().__init__();self.increase_dim=nn.Linear(3,3);self.decode_head=nn.Linear(3,3);self.fail=fail
    for block in self.base_model.decoder.blocks:block.norm_v=nn.LayerNorm(3)
   def forward(self,x):
    self.forward_calls+=1
    if self.fail and self.training:raise RuntimeError('ARTIFICIAL_TRAIN_FORWARD_FAILURE')
    y=self.bn(x.transpose(1,2)).mean(-1);y=self.reduce_map(self.base_model.coarse_pred(y))+self.base_model.decoder.coordinate_pe(y)
    y=y+sum(p for n,p in self.named_parameters() if n.endswith('.weight') and p.ndim==0)
    y=y+sum(b.norm_v(y) for b in self.base_model.decoder.blocks)
    y=self.decode_head(self.increase_dim(y));coarse=y[:,None].expand(-1,256,-1);dense=y[:,None].expand(-1,8192,-1)
    return (coarse,coarse[:,:0],dense[:,:0],dense) if self.training else (coarse,dense)
  model=FullFixture().eval();initial=state_sha(model);x=torch.randn(8,8192,3);target=torch.randn_like(x);counts=e.counters();journal=[]
  records=e.full_checks(TorchProxy(),np,model,helper,parent,x,target,counts,journal.append,lambda *args:None)
  check('19 actual full loop exactly2F2loss2B',model.forward_calls==model.loss_calls==counts['full_forward']==counts['full_loss']==counts['full_backward']==2)
  check('20 eval B1 train B8 only',[(r['phase'],r['batch']) for r in records]==[('eval_1',1),('train_1',8)])
  check('21 train BN changes logged eval BN unchanged',not records[0]['BN_changed'] and bool(records[1]['BN_changed']))
  check('22 all35 gradient module norms positive finite',all(len(r['gradients']['module_norm_sums'])==35 and all(v>0 for v in r['gradients']['module_norm_sums'].values()) for r in records))
  check('23 state RNG mode restoration event valid',state_sha(model)==initial and not any(m.training for m in model.modules()) and journal[-1]==dict(kind='FULL_RESTORATION',state_restored=True,RNG_restored=True,modes_restored=True))
  check('24 no repeat comparison or decoder calls',all('repeat' not in r for r in records) and counts['decoder_forward']==counts['decoder_backward']==counts['optimizer_steps']==0)
  failing=FullFixture(fail=True).eval();initial=state_sha(failing);fc=e.counters();failure_journal=[]
  reject('25 first train failure stops without retry',lambda:e.full_checks(TorchProxy(),np,failing,helper,parent,x,target,fc,failure_journal.append,lambda *args:None))
  check('26 state modes restored on failure counts precise',state_sha(failing)==initial and not failing.training and fc['full_forward']==2 and fc['full_backward']==fc['full_loss']==1 and failing.forward_calls==2)
  reject('27 nonfinite gradient rejected',lambda:e.gradients(torch,SimpleNamespace(named_parameters=lambda:[('bad',SimpleNamespace(grad=torch.tensor(float('nan'))))]),['bad']))
  reject('28 inactive required module rejected',lambda:e.gradients(torch,nn.Linear(3,3),['missing']))
  # Exercise actual four-module LQI import dispatch under inherited finite read policy.
  native=B/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py';impl={}
  for k,n in [('encoder','bcsp_mamba_encoder_v1.py'),('factory','bcsp_p1_model_factory_v1.py')]:impl[k]=rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'/n)
  for k,n in [('lqi_decoder','bcsp_lqi_decoder_v1.py'),('lqi_factory','bcsp_lqi_factory_v1.py')]:impl[k]=rec(B/'lqi_implementation_v1'/n)
  neighbor=O/'neighbor.py';neighbor.write_bytes(b'UNAUTHORIZED=1\n');owned=O/'owned';owned.mkdir()
  config=O/'source_fixture.json';config.write_text(json.dumps(dict(native=rec(native),entry=rec(S/'bcsp_lqi_cuda_admission_v1.py'),helper=rec(R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'),implementation=impl,neighbor=str(neighbor.absolute()),owned=str(owned.absolute()))),encoding='utf-8')
  child=r'''
import ctypes,hashlib,importlib.util,json,sys,types
from pathlib import Path
import torch
c=json.loads(Path(sys.argv[1]).read_bytes())
def load(n,r):
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
p=load('lqi_policy_native',c['native']);h=load('lqi_policy_helper',c['helper']);e=load('lqi_policy_entry',c['entry']);impl=c['implementation']
guard=p.ExactSourceReads(dict(encoder=impl['encoder'],factory=impl['factory'],f0_decoder=impl['lqi_decoder'],f0_factory=impl['lqi_factory']))
policy=p.make_policy(h,[],Path(c['owned']),[],[],[],types.SimpleNamespace(allow=lambda *args:False),guard);sys.addaudithook(policy.audit)
for n,k in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory')]:e.source_module(n,impl[k])
assert 'bcsp_f0_decoder_v1' not in sys.modules and sys.modules['bcsp_lqi_factory_v1'].F0Decoder.__module__=='bcsp_lqi_decoder_v1'
try:Path(impl['lqi_decoder']['path']).open('w')
except (RuntimeError,ValueError):pass
else:raise AssertionError('write allowed')
try:Path(c['neighbor']).read_bytes()
except (RuntimeError,ValueError):pass
else:raise AssertionError('neighbor allowed')
guard.close();print('{"actual_LQI_dispatch":true,"source_write_denied":true,"neighbor_denied":true}')
'''
  cp=subprocess.run([sys.executable,'-I','-B','-c',child,str(config)],capture_output=True,timeout=30)
  for key,value in [('stdout',cp.stdout),('stderr',cp.stderr)]:
   with (O/('source_policy_'+key+'.bin')).open('xb') as f:f.write(value)
  check('29 real candidate source dispatch under exact policy',cp.returncode==0 and all(json.loads(cp.stdout).values()))
  emit('result.json',dict(status='LQI_CUDA_ENTRY_ARTIFICIAL_CPU_PASS',count=len(checks),checks=checks,entry=rec(S/'bcsp_lqi_cuda_admission_v1.py'),test=rec(Path(__file__)),implementation=impl,full_engine_counts=counts,gradient_prefix_count=35,torch=torch.__version__,CUDA=False,server_operations=0,real_payloads=False,limitations=['Full-loss control loop uses an artificial cheap MSE fixture; production Chamfer and nativeMamba/CUDA not executed.','LQI tensor formula and backward already have separate frozen55-assertion implementation evidence; not replayed in this batch.']))
  print(json.dumps(dict(status='PASS',assertions=len(checks))))
 except BaseException as exc:
  emit('failure.json',dict(status='FAILED_STOP_NO_RETRY',completed_checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
