"""One artificial CPU contract batch; no real arrays, weights, CUDA, deployment or scoring."""
import ast,copy,hashlib,importlib.util,json,random,subprocess,sys,types,traceback,shlex
from pathlib import Path
from functools import partial
import numpy as np
import torch
from torch import nn
S=Path(__file__).resolve().parent;R=S.parents[2];PRE=S.parent/'Native_prediction_preparation_v1';O=S/'artificial_cpu_batch_v1'

def module(n,path):
 s=importlib.util.spec_from_file_location(n,path);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def main():
 O.mkdir();torch.set_num_threads(2);p=module('f0_native_cpu_entry',S/'bcsp_f0_twofold_native_predict_v1.py');checks=[]
 def check(n,v=True):
  if not v:raise AssertionError(n)
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (RuntimeError,ValueError,AssertionError,KeyError):checks.append(n);return
  raise AssertionError('unexpected accept: '+n)
 def rec(f):return dict(path=str(f.absolute()),bytes=f.stat().st_size,sha256=p.sha(f))
 def emit(n,v):f=O/n;p.emit(f,v);return rec(f)
 def fingerprint(m):return hashlib.sha256(b''.join(n.encode()+v.detach().cpu().contiguous().numpy().tobytes() for n,v in m.state_dict().items())).hexdigest()
 try:
  index=json.loads((PRE/'F0_CD_Native_input_index_candidate_v1.json').read_bytes());selection=json.loads((PRE/'recipient_donor_registration_addendum_v1.json').read_bytes());protocol=rec(PRE/'F0_CD_210_Native_prediction_scope_draft_v1.json')
  G=R/'outputs/cranial_bcsp_geov1_20261024';folds=json.loads((G/'consolidated_binding_v1/fold_binding.json').read_bytes());source=json.loads((G/'development_eval_v1/development_input_index_v1.json').read_bytes());manifest=[json.loads(x) for x in (G/'real_data_qc_v1/manifest_8192.jsonl').read_text().splitlines()]
  check('01 actual metadata twofold210 index',len(p.validate_index(index,folds,selection)[1])==210)
  p.validate_source(index,source,manifest);check('02 original source normalization and input metadata')
  for n,mutate in [('03 missing case',lambda x:x['inputs'].pop()),('04 wrong checkpoint',lambda x:x['runs'][0]['checkpoint'].update(sha256='0'*64)),('05 order drift',lambda x:x['inputs'].__setitem__(0,x['inputs'][1])),('06 omit all-case coarse',lambda x:x['inputs'][20].update(save_coarse=False)),('07 extra cache case',lambda x:x['inputs'][20].update(cache_context=True)),('08 variant drift',lambda x:x['runs'][1].update(variant='M0'))]:
   bad=copy.deepcopy(index);mutate(bad);reject(n,lambda:p.validate_index(bad,folds,selection))
  bad=copy.deepcopy(selection);bad['literal_table_proven_frozen_before_training']=True;reject('09 no backdated registration',lambda:p.validate_index(index,folds,bad))
  bad=copy.deepcopy(index);bad['inputs'][0]['normalization']['scale']*=2;reject('10 altered normalization provenance',lambda:p.validate_source(bad,source,manifest))
  serial=0
  def triplet(change=None,yes=True,runtime_good=True):
   nonlocal serial
   serial+=1;q=dict(schema='bcsp-f0-twofold-native-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',forward_budget=210,batch_size=1,backward=0,optimizer_steps=0,BNCal=0,loss_calls=0,warmup=0,TTA=0,limits=p.LIMITS,input_index=rec(PRE/'F0_CD_Native_input_index_candidate_v1.json'),protocol=protocol,selection=rec(PRE/'recipient_donor_registration_addendum_v1.json'),selection_registration_timing='RULE_PRETRAINING_LITERAL_IDS_PRE_NATIVE_NOT_PRETRAINING')
   if change:change(q)
   qr=emit('q'+str(serial)+'.json',q);ar=emit('a'+str(serial)+'.json',dict(schema='bcsp-development-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_TEST_ONLY'))
   rr=emit('r'+str(serial)+'.json',dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'] if runtime_good else '0'*64));return qr,ar,rr
  p.authorize(*triplet());check('11 full authorize one-way binding')
  reject('12 authorization required',lambda:p.authorize(*triplet(yes=False)))
  reject('13 runtime mismatch',lambda:p.authorize(*triplet(runtime_good=False)))
  reject('14 extra forward denied',lambda:p.authorize(*triplet(lambda q:q.update(forward_budget=211))))
  reject('15 warmup denied',lambda:p.authorize(*triplet(lambda q:q.update(warmup=1))))
  impl={}
  for k,n in [('encoder','bcsp_mamba_encoder_v1.py'),('factory','bcsp_p1_model_factory_v1.py')]:impl[k]=rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'/n)
  for k,n in [('f0_factory','bcsp_f0_factory_v1.py'),('f0_decoder','bcsp_f0_decoder_v1.py')]:impl[k]=rec(S.parent/'implementation_v1'/n)
  evidence=dict(training_audits={r['label']:r['training_audit'] for r in index['runs']},implementation=impl,dependencies=[],numeric_policy=emit('numeric.json',{}),entry=rec(S/'bcsp_f0_twofold_native_predict_v1.py'),protocol=protocol,P3=emit('p3_fixture.json',dict(status='LOCAL_F0_NATIVE_PREDICTION_P3_PASS',entry_sha256=p.sha(S/'bcsp_f0_twofold_native_predict_v1.py'),checks={'artificial':True})))
  p.validate_evidence(evidence,index);check('16 both real frozen training audit metadata')
  bad=copy.deepcopy(evidence);bad['training_audits']['D_F0']=bad['training_audits']['C_F0'];reject('17 swapped fold audit denied',lambda:p.validate_evidence(bad,index))
  # The actual four source loader is exercised under an audit hook in an isolated child.
  child=r'''
import ctypes,hashlib,importlib.util,json,sys,types
from pathlib import Path
import torch
c=json.loads(Path(sys.argv[1]).read_bytes())
def load(n,r):
 assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'];s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
p=load('actual_policy_entry',c['entry']);h=load('actual_policy_helper',c['helper']);guard=p.ExactSourceReads(c['implementation']);utc=types.SimpleNamespace(allow=lambda *a:False)
policy=p.make_policy(h,[],c['owned'],[],[],[],utc,guard);sys.addaudithook(policy.audit)
factory=p.load_f0_builder(c['implementation'])
assert callable(factory.build_model) and factory.F0Decoder.__module__=='bcsp_f0_decoder_v1'
for rec in c['implementation'].values():
 try:Path(rec['path']).open('w')
 except (RuntimeError,ValueError):pass
 else:raise AssertionError('write allowed')
try:Path(c['neighbor']).read_bytes()
except (RuntimeError,ValueError):pass
else:raise AssertionError('neighbor allowed')
guard.close();print(json.dumps(dict(actual_four_source_load=True,writes_denied=True,neighbor_denied=True)))
'''
  neighbor=O/'neighbor.py';neighbor.write_bytes(b'VALUE=99\n');owned=O/'policy_owned';owned.mkdir()
  fixture=emit('source_policy_fixture.json',dict(entry=rec(S/'bcsp_f0_twofold_native_predict_v1.py'),implementation=impl,helper=rec(G/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'),neighbor=str(neighbor.absolute()),owned=str(owned.absolute())))
  proc=subprocess.run([sys.executable,'-I','-B','-c',child,fixture['path']],capture_output=True,timeout=30)
  for name,data in [('stdout',proc.stdout),('stderr',proc.stderr)]:
   with (O/('source_policy_'+name+'.bin')).open('xb') as f:f.write(data)
  check('18 actual four sources under real policy hook',proc.returncode==0 and all(json.loads(proc.stdout).values()))
  # Real F0 decoder/factory with artificial causal mixer; no native Mamba claim.
  factory=p.load_f0_builder(impl)
  env=dict(torch=torch,nn=nn,partial=partial,factory=factory)
  def knn_point(k,xyz,query):return torch.cdist(query,xyz).topk(k,largest=False).indices
  def index_points(points,idx):return points[torch.arange(points.shape[0]).view(-1,1,1),idx]
  env.update(knn_point=knn_point,index_points=index_points,trunc_normal_=nn.init.trunc_normal_)
  SNAP=R/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/models'
  for filename,names in [('Transformer_utils.py',{'Mlp','Attention','CrossAttention','DynamicGraphAttention','LayerScale'}),('AdaPoinTr.py',{'CrossAttnBlockApi','TransformerDecoder','PointTransformerDecoder'})]:
   t=ast.parse((SNAP/filename).read_text(encoding='utf-8'));nodes=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SNAP/filename),'exec'),env)
  env['env']=env
  t=ast.parse((S.parent/'implementation_v1/test_f0_cpu_v1.py').read_text(encoding='utf-8'))
  nodes=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name in {'ArtificialCausalMixer','EncoderFixture','ArtificialModel'}]
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'prior_artificial_model_classes','exec'),env)
  torch.manual_seed(170);m,ev=factory.build_artificial_fixture(env['ArtificialModel'],env['ArtificialCausalMixer']);m.eval()
  q=torch.randn(1,256,384);mem=torch.randn_like(q);qp=torch.randn(1,256,3);sp=torch.randn_like(qp)
  before=fingerprint(m);rng=torch.get_rng_state().clone()
  with torch.inference_mode():plain=m.base_model.decoder(q,mem,qp,sp);traced,layers=m.base_model.decoder(q,mem,qp,sp,return_instrumentation=True)
  check('19 real F0 eight-layer trace on/off numerically identical',torch.equal(plain,traced) and len(layers)==8)
  check('20 trace keeps state and CPU RNG',fingerprint(m)==before and torch.equal(rng,torch.get_rng_state()))
  trace=dict(coarse_point_cloud=qp,backbone=dict(encoder_memory=mem,encoder_coordinates=sp,global_feature=torch.zeros(1,1024),coarse=qp,query_pre_decoder=q,decoder_layers=layers))
  ctx,tr=p.capture_context(torch,np,trace,qp.numpy(),True)
  check('21 exact context and40 layer arrays',set(ctx)=={'F','S','z','Q','X'} and len(tr)==40 and np.array_equal(ctx['z'],np.zeros((1,1024),np.float32)))
  bad=copy.deepcopy(trace);bad['backbone']['coarse']=qp+1;reject('22 output Q drift denied',lambda:p.capture_context(torch,np,bad,qp.numpy(),True))
  bad=copy.deepcopy(trace);bad['backbone']['decoder_layers']=layers[:-1];reject('23 missing decoder layer denied',lambda:p.capture_context(torch,np,bad,qp.numpy(),True))
  # Exercise production build_model(legacy_builder,seed=0) signature with supplied artificial mixer.
  old=factory.parent.native_mixer;factory.parent.native_mixer=env['ArtificialCausalMixer']
  try:built,real_ev=factory.build_model(env['ArtificialModel'],seed=0)
  finally:factory.parent.native_mixer=old
  check('24 actual production factory call signature',real_ev['version']=='F0-P-v2-implementation-v1' and real_ev['parent']['variant']=='M0')
  del m,built,plain,traced,trace,layers
  # Cheap outer fixture for all210 paths; actual mother instrumentation methods reused.
  mother=ast.parse((SNAP/'AdaPoinTr.py').read_text(encoding='utf-8'))
  outer=next(n for n in mother.body if isinstance(n,ast.ClassDef) and n.name=='AdaPoinTr')
  methods=[n for n in outer.body if isinstance(n,ast.FunctionDef) and n.name in {'enable_full_instrumentation','pop_full_instrumentation'}]
  menv={};exec(compile(ast.Module(body=methods,type_ignores=[]),'actual_mother_instrumentation_methods','exec'),menv)
  class Base(nn.Module):
   def __init__(self):
    super().__init__();self.decoder=nn.Module();self.decoder.blocks=nn.ModuleList([nn.Identity() for _ in range(8)]);self.center_num=[512,256];self.encoder_type='graph';self.query_selection='learned_only';self.use_denoise=False;self.encoder_adapter=types.SimpleNamespace(enabled=False);self.full_instrumentation_enabled=False;self._last_full_instrumentation=None
   def enable_full_instrumentation(self,on=True):self.full_instrumentation_enabled=bool(on);self._last_full_instrumentation=None
   def pop_full_instrumentation(self):r=self._last_full_instrumentation;self._last_full_instrumentation=None;return r
  class Model(nn.Module):
   enable_full_instrumentation=menv['enable_full_instrumentation'];pop_full_instrumentation=menv['pop_full_instrumentation']
   def __init__(self,fail=False):
    super().__init__();self.weight=nn.Parameter(torch.tensor(.1));self.base_model=Base();self.num_query=256;self.num_points=8192;self.factor=32;self.decoder_type='fc';self.denoise_weight=0;self.fine_coverage_weight=1;self.fine_local_weight=0;self.scqr_contract=types.SimpleNamespace(enabled=False)
    for k in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']:setattr(self,k,False)
    self.full_instrumentation_enabled=False;self._last_full_instrumentation=None;self.calls=0;self.fail=fail
   def forward(self,x):
    self.calls+=1
    if self.fail:raise RuntimeError('ARTIFICIAL_FORWARD_FAIL')
    co=x[:,:256]+self.weight;dense=co[:,:,None,:].expand(-1,-1,32,-1).reshape(1,8192,3)
    if self.full_instrumentation_enabled:
     f=co[:,:,:1].expand(-1,-1,384);layers=[dict(layer_index=j,**{k:f for k in ('input','after_self','prefix_suffix','after_cross','output')}) for j in range(8)]
     self.base_model._last_full_instrumentation=dict(encoder_memory=f,encoder_coordinates=x[:,:256],global_feature=torch.zeros(1,1024),coarse=co,query_pre_decoder=f,decoder_layers=layers)
     self._last_full_instrumentation=dict(coarse_point_cloud=co,rebuild_global_feature=torch.ones(1,1024))
    return co,dense
  ce=copy.deepcopy(ev);ce['artificial_fixture']=True
  mp=Model();ck=O/'synthetic3900.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=mp.state_dict()),ck)
  mp2=Model();p.load_checkpoint(torch,mp2,dict(checkpoint=rec(ck)));check('25 actual strict synthetic checkpoint load',fingerprint(mp)==fingerprint(mp2))
  for n,change in [('26 wrong update metadata',lambda d:d.update(updates=3899)),('27 missing state key',lambda d:d['base_model'].pop('weight')),('28 unexpected state key',lambda d:d['base_model'].update(extra=torch.zeros(1)))]:
   d=torch.load(ck,weights_only=True);change(d);f=O/(n.split()[0]+'.pth');torch.save(d,f);reject(n,lambda:p.load_checkpoint(torch,Model(),dict(checkpoint=rec(f))))
  array=np.arange(8192*3,dtype=np.float32).reshape(8192,3)*1e-5;npz=O/'artificial_input.npz'
  with npz.open('xb') as f:np.savez_compressed(f,partial=array)
  accessed=[]
  class Archive:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def __getitem__(self,k):accessed.append(k);assert k=='partial';return array
  proxy=types.SimpleNamespace(load=lambda *a,**kw:Archive(),float32=np.float32,isfinite=np.isfinite)
  p.load_partial(proxy,dict(input=rec(npz),n_input=8192));check('29 partial only no GT array',accessed==['partial'])
  helper=types.SimpleNamespace(assert_numeric=lambda t:None,state_sha=fingerprint,tensor_sha=lambda x:hashlib.sha256(x.cpu().numpy().tobytes()).hexdigest())
  runs=copy.deepcopy(index['runs']);rows=copy.deepcopy(index['inputs'])
  for run in runs:run['checkpoint']=rec(ck)
  for row in rows:row['input']=rec(npz)
  out=O/'synthetic210';out.mkdir()
  for n in ('predictions','context','traces'):(out/n).mkdir()
  events=[];models=[]
  def builder(run):m=Model();models.append(m);return m,ce
  files,logs,states=p.execute_pair(torch,np,helper,runs,rows,out,types.SimpleNamespace(sample=lambda *a:events.append(a)),builder,device='cpu',artificial_cpu=True)
  check('30 exact210 forward calls and240 npz',len(files)==240 and len(set(files))==240 and sum(m.calls for m in models)==210 and all(m.calls==105 for m in models))
  check('31 both model states and CPU numpy Python RNG unchanged',len(states)==2 and all(s['state_before']==s['state_after'] and s['RNG_before']==s['RNG_after'] for s in states))
  check('32 all210 predictions have Q and P',all(set(np.load(f,allow_pickle=False).files)=={'prediction','coarse'} for f in files if f.parent.name=='predictions'))
  check('33 exact20 context10 traces no extra forward',len(list((out/'context').glob('*.npz')))==20 and len(list((out/'traces').glob('*.npz')))==10)
  check('34 mother clear methods reset both caches',all(not m.full_instrumentation_enabled and not m.base_model.full_instrumentation_enabled and m.pop_full_instrumentation() is None for m in models))
  journal=[json.loads(x) for x in (out/'forward_attempts.jsonl').read_text().splitlines()];check('35 pre-forward unique claims',len(journal)==210 and [v['forward_index'] for v in journal]==list(range(1,211)))
  geo=[json.loads(x) for x in (out/'geometry_summary.jsonl').read_text().splitlines()];check('36 geometry finite counts',len(geo)==210 and all(v['coarse']['finite_count']==256 and v['dense']['finite_count']==8192 for v in geo))
  check('37 original percase resource sampling',len(events)==423 and events[-1]==('all_complete',210))
  archive=p.pack(out,files+logs);check('38 archive member hashes and counts',len(archive['members'])==244 and all(p.sha(out/r['name'])==r['sha256'] for r in archive['members']))
  failed=O/'forced_fail';failed.mkdir();calls=[]
  def broken(run):calls.append(run['label']);return Model(fail=True),ce
  reject('39 first failure stops before next model',lambda:p.execute_pair(torch,np,helper,runs,rows,failed,types.SimpleNamespace(sample=lambda *a:None),broken,device='cpu',artificial_cpu=True))
  f=json.loads((failed/'failure.json').read_bytes());check('40 failure preserves attempted count',calls==['C_F0'] and f['forward_attempts']==1 and f['valid_forward_returns']==0)
  qlaunch=dict(output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_20261111_v1',limits=p.LIMITS,identity=dict(project='/home/jovyan/adapointr_work/PoinTr',python_realpath='/opt/conda/envs/adapointr-mamba/bin/python3.10'),entry=dict(path='/home/jovyan/adapointr_work/PoinTr/third_party/f0/entry.py'),environment={'TMPDIR':'<owned_output>/tmp'},launch_contract=dict(request_path='/home/jovyan/adapointr_work/PoinTr/third_party/f0/q.json',authorization='/home/jovyan/adapointr_work/PoinTr/third_party/f0/a.json',runtime='/home/jovyan/adapointr_work/PoinTr/third_party/f0/r.json',log='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_20261111_v1/launch.log',exit_code='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_20261111_v1/exit_code.txt'))
  launch=p.render_launcher(qlaunch,'a'*64,'b'*64,'c'*64);cmd=next(x for x in launch.splitlines() if x.startswith('/usr/bin/timeout'));tokens=shlex.split(cmd)
  check('41 POSIX launcher parent before redirect and exact argv',launch.index('mkdir -p --')<launch.index(' >') and '\\' not in cmd and tokens[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','7200s'] and tokens[tokens.index('--request')+1]==qlaunch['launch_contract']['request_path'])
  original=ast.parse((R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_fourmodel_prediction_implementation_v1/bcsp_h2_fourmodel_native_predict_v1.py').read_text(encoding='utf-8'));current=ast.parse((S/'bcsp_f0_twofold_native_predict_v1.py').read_text(encoding='utf-8'))
  def node(t,n):return next(x for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==n)
  inherited=['load_partial','predict_once','source_module','make_policy','Budget','pack','rng_state','geometry_summary']
  check('42 inherited numeric resource and data guards AST unchanged',all(ast.dump(node(original,n),include_attributes=False)==ast.dump(node(current,n),include_attributes=False) for n in inherited))
  result=dict(status='F0_NATIVE_CPU_CONTRACT_PASS',checks=checks,checks_passed=len(checks),synthetic_forwards=210,real_decoder_trace_comparison_calls=2,real_data_arrays=0,real_checkpoint_loads=0,GPU_calls=0,server_operations=0,source_bindings=[rec(S/'bcsp_f0_twofold_native_predict_v1.py'),rec(Path(__file__)),*impl.values()],limitations=['Real F0 factory/decoder with artificial causal mixer; no native Mamba CUDA certification','210-loop uses lightweight artificial outer forward and actual mother cache control methods','Actual parent full forward not executed; original project source/instrumentation contract statically reviewed','CUDA state/RNG invariants await authorized Native execution; no CPU scientific performance claim'])
  p.emit(O/'result_v1.json',result);print(json.dumps(result,ensure_ascii=False))
 except BaseException as exc:
  p.emit(O/'failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise

if __name__=='__main__':main()
