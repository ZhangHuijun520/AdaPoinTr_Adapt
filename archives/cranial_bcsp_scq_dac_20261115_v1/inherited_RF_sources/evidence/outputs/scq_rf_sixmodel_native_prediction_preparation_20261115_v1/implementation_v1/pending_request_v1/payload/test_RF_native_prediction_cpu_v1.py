"""One bounded artificial CPU batch. No real arrays/checkpoints, GPU or remote calls."""
from pathlib import Path
from functools import partial
import ast,copy,hashlib,importlib.util,json,random,shlex,subprocess,sys,traceback,types
import numpy as np
import torch
from torch import nn
S=Path(__file__).resolve().parent;R=S.parents[2];O=S/'artificial_cpu_batch_v1'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def fp(m):return hashlib.sha256(b''.join(n.encode()+v.detach().cpu().contiguous().numpy().tobytes() for n,v in m.state_dict().items())).hexdigest()
def main():
 O.mkdir();torch.set_num_threads(2);checks=[];p=load('scq_prediction_cpu_entry',S/'bcsp_scq_rf_sixmodel_native_predict_v1.py')
 def check(n,v=True):
  assert v,n
  assert n not in checks;checks.append(n)
 def reject(n,fn):
  try:fn()
  except (RuntimeError,ValueError,AssertionError,KeyError,TypeError):check(n);return
  raise AssertionError('unexpected accept '+n)
 def emit(n,j):f=O/n;p.emit(f,j);return rec(f)
 try:
  ctx=json.loads((S/'context_v1.json').read_bytes());q=copy.deepcopy(ctx['candidate']);mirror=ctx['mirror'];index=json.loads((S/'RF_sixmodel_input_index_v1.json').read_bytes())
  C=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1';folds=json.loads((C/'candidate_payload/fold_binding.json').read_bytes());manifest=[json.loads(x) for x in (C/'candidate_payload/manifest_8192.jsonl').read_text().splitlines()]
  check('01 six-model630 metadata index',len(p.validate_index(index,folds)[1])==630)
  p.validate_source(index,None,manifest);check('02 provenance paired normalization metadata')
  for name,mutate in [('03 missing case',lambda x:x['inputs'].pop()),('04 wrong checkpoint',lambda x:x['runs'][0]['checkpoint'].update(sha256='0'*64)),('05 wrongfold',lambda x:x['runs'][0].update(fold='D')),('06 wrongarm',lambda x:x['runs'][1].update(variant='S')),('07 extra cache',lambda x:x['inputs'][0].update(cache_context=True)),('08 missing Qraw',lambda x:x['inputs'][0].update(save_Qraw=False)),('09 path swap',lambda x:x['inputs'][0]['input'].update(path=x['inputs'][315]['input']['path']))]:
   bad=copy.deepcopy(index);mutate(bad);reject(name,lambda:p.validate_index(bad,folds))
  bad=copy.deepcopy(index);bad['inputs'][0]['normalization']['scale']*=2;reject('10 normalization drift',lambda:p.validate_source(bad,None,manifest))
  serial=0
  def triplet(change=None,yes=True,reverse=False):
   nonlocal serial
   serial+=1;v=copy.deepcopy(q)
   if change:change(v)
   qr=emit('q'+str(serial)+'.json',v);ar=emit('a'+str(serial)+'.json',dict(schema='bcsp-development-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_ONLY'))
   rr=emit('r'+str(serial)+'.json',dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if reverse else ar['sha256']));return qr,ar,rr
  p.authorize(*triplet());check('11 actual complete authorize one-way chain')
  reject('12 absent authorization',lambda:p.authorize(*triplet(yes=False)))
  reject('13 runtime digest drift',lambda:p.authorize(*triplet(reverse=True)))
  reject('14 extra forward',lambda:p.authorize(*triplet(lambda v:v.update(forward_budget=631))))
  reject('15 backward prohibited',lambda:p.authorize(*triplet(lambda v:v.update(backward=1))))
  reject('16 BNCal prohibited',lambda:p.authorize(*triplet(lambda v:v.update(BNCal=1))))
  for name,change in [('wrong execution GPU selector',lambda v:v['environment'].update(CUDA_VISIBLE_DEVICES='GPU-WRONG')),('wrong device-confound disclosure',lambda v:v['comparison_qualification'].update(strict_same_device_D_pair=True)),('old model budget',lambda v:v.update(forward_budget=420)),('unauthorized current request flag',lambda v:v.update(execution_authorized=True))]:
   reject(name,lambda:p.authorize(*triplet(change)))
  original_exact=p.exact
  def mapped(r):return original_exact(dict(r,path=mirror.get(r['path'],r['path'])))
  # Resolve only local frozen evidence; no remote paths opened.
  numeric=emit('artificial_numeric_policy.json',{})
  evidence=copy.deepcopy(q);evidence['numeric_policy']=numeric
  # Server environment binaries are not present locally; exact remote dependencies
  # remain frozen in the real request and must be reverified before activation.
  evidence['dependencies']=[]
  evidence['P3']=emit('artificial_P3.json',dict(status='LOCAL_RF_NATIVE_PREDICTION_P3_PASS',entry_sha256=q['entry']['sha256'],checks={'artificial_only':True}))
  p.exact=mapped
  try:
   p.validate_evidence(evidence,index);check('17 all six real frozen audit metadata and ten module pins')
   bad=copy.deepcopy(evidence);bad['training_audits']['Static_D']=bad['training_audits']['Sref_D'];reject('18 swapped audit rejected',lambda:p.validate_evidence(bad,index))
  finally:p.exact=original_exact
  impl={k:dict(v,path=mirror[v['path']]) for k,v in q['implementation'].items()};initialization=dict(q['initialization'],path=mirror[q['initialization']['path']]);rf_initialization=dict(q['rf_initialization'],path=mirror[q['rf_initialization']['path']])
  child=r'''
import ctypes,hashlib,importlib.util,json,sys,types,traceback,linecache
from pathlib import Path
import torch
c=json.loads(Path(sys.argv[1]).read_bytes())
def load(n,r):
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
p=load('policy_entry',c['entry']);h=load('policy_helper',c['helper']);g=p.make_source_guard(c['implementation'],c['initialization'],c['rf_initialization'],[c['entry'],c['helper']])
u=types.SimpleNamespace(allow=lambda *a:False)
policy=p.make_policy(h,[],c['owned'],[],[],[],u,g);sys.addaudithook(policy.audit)
f=p.load_scq_builder(c['implementation']);assert callable(f['scq'].build_model) and callable(f['rf'].build_model)
assert p.exact(c['initialization']).read_bytes() and p.exact(c['rf_initialization']).read_bytes()
for r in [*c['implementation'].values(),c['entry'],c['helper']]:
 assert linecache.getline(r['path'],1)
try:exec(compile("raise RuntimeError('ARTIFICIAL_TRACEBACK')",c['implementation']['rf_factory']['path'],'exec'))
except RuntimeError as exc:assert 'ARTIFICIAL_TRACEBACK' in ''.join(traceback.format_exception(type(exc),exc,exc.__traceback__))
for r in [*c['implementation'].values(),c['initialization'],c['rf_initialization'],c['entry'],c['helper']]:
 try:Path(r['path']).open('wb')
 except (RuntimeError,ValueError):pass
 else:raise AssertionError('source write allowed')
try:Path(c['neighbor']).read_bytes()
except (RuntimeError,ValueError):pass
else:raise AssertionError('neighbor read allowed')
g.close();print(json.dumps(dict(six_source_load=True,exact_initializer_read=True,writes_denied=True,neighbor_denied=True)))
'''
  neighbor=O/'neighbor.py';neighbor.write_bytes(b'VALUE=1\n');owned=O/'policy_owned';owned.mkdir()
  fixture=emit('source_policy_fixture.json',dict(entry=rec(S/'bcsp_scq_rf_sixmodel_native_predict_v1.py'),implementation=impl,initialization=initialization,rf_initialization=rf_initialization,helper=dict(q['helper'],path=mirror[q['helper']['path']]),owned=str(owned.absolute()),neighbor=str(neighbor.absolute())))
  cp=subprocess.run([sys.executable,'-I','-B','-c',child,fixture['path']],capture_output=True,timeout=45)
  for k,b in [('stdout',cp.stdout),('stderr',cp.stderr)]:
   with (O/('source_policy_'+k+'.bin')).open('xb') as f:f.write(b)
  check('19 actual six-source loader and bin under real audit policy',cp.returncode==0 and all(json.loads(cp.stdout).values()))
  factories=p.load_scq_builder(impl);factory=factories['scq']
  # Reuse previously validated artificial constructors and actual mother computational classes.
  SNAP=R/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot'
  knn=lambda k,s,x:torch.cdist(x,s).topk(k,largest=False).indices
  env=dict(torch=torch,nn=nn,partial=partial,knn=knn,factory=factory,init=initialization,R=R,SNAP=SNAP,types=types,ast=ast)
  fixture_src=(R/'outputs/cranial_bcsp_scq_implementation_20261113_v1/test_scq_cpu_v1.py').read_text(encoding='utf-8')
  fixture_src=fixture_src[fixture_src.index('  env=dict(torch=torch'):fixture_src.index('  rng=torch.random.get_rng_state().clone();mix=')]
  import textwrap
  exec(compile(textwrap.dedent(fixture_src),'frozen_artificial_constructor_reuse','exec'),env)
  def legacy():
   m=env['legacy']();m.num_points=8192;m.base_model.encoder_type='graph';m.base_model.encoder_adapter.enabled=False;return m
  mix=env['env']['ArtificialCausalMixer'];actual=[];evs={}
  for arm in ('S','RF-Static','RF-Requery'):
   m,ev=(factory.build_artificial_fixture(legacy,mix,'S',initialization) if arm=='S' else factories['rf'].build_artificial_fixture(legacy,mix,arm,initialization,rf_initialization));m.eval();p.validate_model(m,ev,True)
   with torch.no_grad():
    m.base_model.scq.W2.bias.copy_(torch.tensor([.1,-.05,.03]))
    if arm!='S':m.base_model.rf.V2.bias.copy_(torch.tensor([.02,.01,-.01]))
   before=fp(m);rng=torch.get_rng_state().clone();x=torch.linspace(-.5,.5,8192*3).reshape(1,8192,3)
   co,de=p.predict_once(torch,m,x);raw,delta,stages,applies=p.scq_arrays(torch,np,m,co)
   check('20 actual mother '+arm+' full forward Qraw used delta',co.shape==(1,256,3) and de.shape==(1,8192,3) and np.allclose(raw+delta,co) and np.any(delta!=0) and applies is (arm!='S') and np.allclose(stages['Q0']+stages['delta0'],stages['Q1']) and np.allclose(stages['Q1']+stages['delta1'],stages['Q2']))
   check('21 actual mother '+arm+' state RNG stable',before==fp(m) and torch.equal(rng,torch.get_rng_state()))
   actual.append(m);evs[arm]=ev
  old_mixer=factory.parent.parent.native_mixer;factory.parent.parent.native_mixer=mix
  try:
   built,be=p.build_scq_model(factories,legacy,dict(variant='S'),initialization,rf_initialization)
   check('22 actual production SCQ builder dispatch signature',be['scq']['variant']=='S' and hasattr(built.base_model,'scq'))
   for v in ('RF-Static','RF-Requery'):
    bm,bv=p.build_scq_model(factories,legacy,dict(variant=v),initialization,rf_initialization);check('production RF dispatch '+v,bv['rf']['variant']==v and bm.base_model.rf.variant==v);del bm
  finally:factory.parent.parent.native_mixer=old_mixer
  # Wrong output order must not be silently remapped.
  fake=types.SimpleNamespace(base_model=types.SimpleNamespace(scq=True,_scq_last_info=dict(Q0=torch.zeros(1,256,3),Qused=torch.zeros(1,256,3),delta=torch.zeros(1,256,3))))
  reject('23 inconsistent Qused output rejected',lambda:p.scq_arrays(torch,np,fake,np.ones((1,256,3),np.float32)))
  # Stage equations reject a silently permuted intermediate, even with Q2 correct.
  bad_info=dict(Q0=torch.zeros(1,256,3),Q1=torch.ones(1,256,3),Qused=torch.zeros(1,256,3),delta=torch.zeros(1,256,3),delta0=torch.zeros(1,256,3),delta1=torch.zeros(1,256,3))
  fake_rf=types.SimpleNamespace(base_model=types.SimpleNamespace(scq=True,rf=True,_scq_last_info=bad_info))
  reject('RF stage equation mismatch rejected',lambda:p.scq_arrays(torch,np,fake_rf,np.zeros((1,256,3),np.float32)))
  del built,actual;import gc;gc.collect()
  class Base(nn.Module):
   def __init__(self,arm):
    super().__init__();self.decoder=nn.Module();self.decoder.blocks=nn.ModuleList([nn.Identity() for _ in range(8)]);self.center_num=[512,256];self.encoder_type='graph';self.query_selection='learned_only';self.use_denoise=False;self.encoder_adapter=types.SimpleNamespace(enabled=False);self.full_instrumentation_enabled=False
    self.scq=nn.Identity();self._scq_last_info=None
    if arm.startswith('RF-'):self.rf=nn.Identity();self.rf.variant=arm
  class Model(nn.Module):
   def __init__(self,arm='S',fail=False):
    super().__init__();self.weight=nn.Parameter(torch.tensor(.1));self.base_model=Base(arm);self.num_query=256;self.num_points=8192;self.factor=32;self.decoder_type='fc';self.denoise_weight=0;self.fine_coverage_weight=1;self.fine_local_weight=0;self.scqr_contract=types.SimpleNamespace(enabled=False);self.calls=0;self.fail=fail;self.full_instrumentation_enabled=False
    for k in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']:setattr(self,k,False)
   def enable_full_instrumentation(self,on=True):self.full_instrumentation_enabled=bool(on);self.base_model.full_instrumentation_enabled=bool(on)
   def pop_full_instrumentation(self):return None
   def forward(self,x):
    self.calls+=1
    if self.fail:raise RuntimeError('ARTIFICIAL_FAIL')
    raw=x[:,:256]+self.weight;delta=torch.full_like(raw,.01) if hasattr(self.base_model,'scq') else torch.zeros_like(raw);co=raw+delta
    if hasattr(self.base_model,'scq'):d0=delta;d1=torch.full_like(raw,.02) if hasattr(self.base_model,'rf') else torch.zeros_like(raw);q1=co;co=q1+d1;self.base_model._scq_last_info=dict(Q0=raw,Qused=co,delta=d0+d1,Q1=q1,delta0=d0,delta1=d1)
    return co,co[:,:,None].expand(-1,-1,32,-1).reshape(1,8192,3)
  ck=O/'synthetic3900.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=Model().state_dict()),ck)
  m=Model();p.load_checkpoint(torch,m,dict(checkpoint=rec(ck)));check('24 actual strict synthetic checkpoint load',fp(m)==fp(Model()))
  for name,change in [('25 wrong updates',lambda v:v.update(updates=3899)),('26 missing state',lambda v:v['base_model'].pop('weight')),('27 extra state',lambda v:v['base_model'].update(extra=torch.zeros(1)))]:
   v=torch.load(ck,weights_only=True);change(v);f=O/(name.split()[0]+'.pth');torch.save(v,f);reject(name,lambda:p.load_checkpoint(torch,Model(),dict(checkpoint=rec(f))))
  array=np.arange(8192*3,dtype=np.float32).reshape(8192,3)*1e-5;npz=O/'artificial_input.npz'
  with npz.open('xb') as f:np.savez_compressed(f,partial=array)
  accessed=[]
  class Archive:
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def __getitem__(self,k):accessed.append(k);assert k=='partial';return array
  proxy=types.SimpleNamespace(load=lambda *a,**kw:Archive(),float32=np.float32,isfinite=np.isfinite)
  p.load_partial(proxy,dict(input=rec(npz),n_input=8192));check('28 partial only no GT array access',accessed==['partial'])
  runs=copy.deepcopy(index['runs']);rows=copy.deepcopy(index['inputs'])
  for run in runs:run['checkpoint']=rec(ck)
  for row in rows:row['input']=rec(npz)
  helper=types.SimpleNamespace(assert_numeric=lambda t:None,state_sha=fp,tensor_sha=lambda t:hashlib.sha256(t.cpu().numpy().tobytes()).hexdigest())
  out=O/'synthetic630';out.mkdir()
  for n in ('predictions','context','traces'):(out/n).mkdir()
  models=[];events=[]
  def builder(run):m=Model(run['variant']);models.append(m);return m,evs[run['variant']]
  files,logs,states=p.execute_pair(torch,np,helper,runs,rows,out,types.SimpleNamespace(sample=lambda *a:events.append(a)),builder,device='cpu',artificial_cpu=True)
  check('29 exactly630 forward and630 predictions',len(files)==len(set(files))==sum(m.calls for m in models)==630 and [m.calls for m in models]==[105]*6)
  check('30 six states and all available CPU RNG unchanged',len(states)==6 and all(v['state_before']==v['state_after'] and v['RNG_before']==v['RNG_after'] for v in states))
  check('31 every output Qraw Qused delta P',all(set(np.load(f,allow_pickle=False).files)=={'prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'} for f in files))
  check('32 no context trace or extra model calls',not list((out/'context').iterdir()) and not list((out/'traces').iterdir()))
  journal=[json.loads(x) for x in (out/'forward_attempts.jsonl').read_text().splitlines()]
  check('33 pre-forward claims exact630 order',[v['forward_index'] for v in journal]==list(range(1,631)))
  geometry=[json.loads(x) for x in (out/'geometry_summary.jsonl').read_text().splitlines()]
  check('34 all geometry finite and all raw outputs',len(geometry)==630 and all(v['coarse']['finite_count']==256 and v['dense']['finite_count']==8192 and 'Qraw' in v for v in geometry))
  check('35 resource samples per forward and run',len(events)==1267 and events[-1]==('all_complete',630))
  archive=p.pack(out,files+logs);check('36 archive exact634 members hashes',len(archive['members'])==634 and all(p.sha(out/v['name'])==v['sha256'] for v in archive['members']))
  failed=O/'forced_fail';failed.mkdir();calls=[]
  def broken(run):calls.append(run['label']);return Model(run['variant'],True),evs[run['variant']]
  reject('37 first failure stops no next model',lambda:p.execute_pair(torch,np,helper,runs,rows,failed,types.SimpleNamespace(sample=lambda *a:None),broken,device='cpu',artificial_cpu=True))
  failure=json.loads((failed/'failure.json').read_bytes());check('38 failed attempted count preserved',calls==['Sref_C'] and failure['forward_attempts']==1 and failure['valid_forward_returns']==0)
  launcher=p.render_launcher(q,'a'*64,'b'*64,'c'*64);command=next(v for v in launcher.splitlines() if v.startswith('/usr/bin/timeout'));tokens=shlex.split(command)
  check('39 POSIX launcher and parent before redirect',launcher.index('mkdir -p --')<launcher.index(' >') and '\\' not in command and tokens[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','7200s'])
  old=R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2/bcsp_scq_fourmodel_native_predict_v2.py'
  def nodes(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
  aa,bb=nodes(old),nodes(S/'bcsp_scq_rf_sixmodel_native_predict_v1.py');inherited=['load_partial','predict_once','ExactSourceReads','source_module','make_policy','Budget','pack','rng_state','geometry_summary','load_checkpoint','render_launcher']
  check('40 inherited data numeric resource checkpoint launcher AST identical',all(aa[n]==bb[n] for n in inherited))
  p.emit(O/'result_v1.json',dict(status='RF_NATIVE_CPU_CONTRACT_PASS',checks=checks,checks_passed=len(checks),synthetic_forwards=630,actual_mother_artificial_full_forwards=3,real_data_arrays=0,real_checkpoint_loads=0,GPU_calls=0,server_operations=0,entry=rec(S/'bcsp_scq_rf_sixmodel_native_predict_v1.py'),test=rec(Path(__file__)),source_bindings=[*impl.values(),initialization,rf_initialization],limitations=['Actual mother and SCQ factory exercised with artificial grouper/causal mixer, not native CUDA.','630 outer fixture forwards test lifecycle only; not630 project-model performance predictions.','CUDA state/RNG requires future authorized native execution; no repeat GPU preflight.']))
  print(json.dumps(dict(status='RF_NATIVE_CPU_CONTRACT_PASS',checks=len(checks),synthetic_forwards=630,actual_mother_artificial_full_forwards=3)))
 except BaseException as e:
  p.emit(O/'failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(e),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
