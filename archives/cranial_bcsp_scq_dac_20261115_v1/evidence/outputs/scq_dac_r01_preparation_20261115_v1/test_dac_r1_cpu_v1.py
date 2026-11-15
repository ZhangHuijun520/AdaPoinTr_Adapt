"""Single retained artificial CPU batch. No actual skull payload/checkpoint/CUDA."""
import ast,copy,hashlib,importlib.util,json,sys,time,traceback,types
from pathlib import Path
import numpy as np
import torch
from torch import nn
O=Path(__file__).resolve().parent;R=O.parents[1];OUT=O/'cpu_contract_batch_v1'
def module(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def rec(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 OUT.mkdir();start=time.monotonic();checks=[]
 def check(name,ok=True):
  if not ok:raise AssertionError(name)
  checks.append(name)
 def reject(name,fn):
  try:fn()
  except (RuntimeError,ValueError,AssertionError):check(name);return
  raise AssertionError('unexpected acceptance: '+name)
 try:
  torch.set_num_threads(2)
  c=module('dac_cpu_core',O/'bcsp_scq_dac_r1_core_v1.py');e=module('dac_cpu_entry',O/'bcsp_scq_dac_r1_entry_v1.py')
  prior=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2'
  legacy=module('dac_cpu_native_library',prior/'bcsp_scq_rf_sixmodel_native_predict_v2.py')
  old=json.loads((prior/'RF_sixmodel_input_index_v2.json').read_bytes());selected=json.loads((O/'selected20_cases_v1.json').read_bytes())
  check('01 exact20 selection including balanced cells',len(e.validate_selection(c,selected,old))==20)
  reverse=copy.deepcopy(old);reverse['inputs'].reverse();check('02 order-independent hash selection',c.select_cases(old)==c.select_cases(reverse))
  bad=copy.deepcopy(selected);bad['cases'][0]['input']['sha256']='0'*64
  reject('03 modified input binding rejected',lambda:e.validate_selection(c,bad,old))
  check('04 seven predeclared pressure cases preserved',sum(r['selection']=='PREDECLARED_STRESS_CASE' for r in selected['cases'])==7)
  u=torch.tensor([[[1.,0,0],[1.,0,0],[1.,0,0],[0,0,0],[0,0,0]]]);v=torch.tensor([[[2.,0,0],[0,1.,0],[-1.,0,0],[1.,0,0],[0,0,0]]])
  avg,dac,a=c.combine(torch,u,v)
  check('05 aligned unequal magnitude selects new',torch.equal(dac[0,0],v[0,0]) and a['a'][0,0]==1)
  check('06 orthogonal/negative cos fixed average',torch.equal(dac[0,1:3],avg[0,1:3]))
  check('07 opposite equal magnitude can cancel',torch.equal(dac[0,2],torch.zeros(3)))
  check('08 one/both zero finite and alpha half',torch.equal(a['a'][0,3:],torch.ones(2,1)*.5) and torch.isfinite(dac).all())
  tiny=torch.tensor([[[1e-4,0,0]]]);_,d,aa=c.combine(torch,tiny,tiny*3)
  check('09 small same direction uses true cosine',torch.allclose(aa['a'],torch.ones_like(aa['a']),atol=1e-7) and torch.allclose(d,tiny*3))
  _,_,bb=c.combine(torch,tiny*100,tiny*.1)
  check('10 independent valid positive scaling invariant',torch.allclose(aa['a'],bb['a'],atol=1e-7))
  _,_,near=c.combine(torch,tiny*1e-4,tiny)
  check('11 near-zero direction explicitly undefined',not near['valid'].item() and near['a'].item()==.5)
  check('12 alpha detached while proposals graph-bearing',not c.combine(torch,u.clone().requires_grad_(),v.clone().requires_grad_())[2]['a'].requires_grad)
  reject('13 nonfinite proposal rejected',lambda:c.combine(torch,u*float('nan'),v))
  check('14 DAC decomposition and convex norm bound',torch.allclose(dac,avg+.5*a['c'].clamp_min(0)*(v-u)) and bool((dac.norm(dim=-1)<=torch.maximum(u.norm(dim=-1),v.norm(dim=-1))+1e-6).all()))
  state=R/'deliverables/scq_RF_20261115_v1/public_payload/inherited_scq_bs/inherited_fullmamba/parent_source_snapshot/models'
  env=dict(torch=torch,nn=nn)
  for filename,names in [('Transformer_utils.py',{'Mlp'}),('AdaPoinTr.py',{'SimpleRebuildFCLayer'})]:
   tree=ast.parse((state/filename).read_text(encoding='utf-8'));nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(state/filename),'exec'),env)
  tree=ast.parse((state/'AdaPoinTr.py').read_text(encoding='utf-8'));cl=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AdaPoinTr');fn=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='forward');exec(compile(ast.Module(body=[fn],type_ignores=[]),str(state/'AdaPoinTr.py'),'exec'),env)
  rfmod=module('dac_cpu_actual_frozen_residual',R/'outputs/scq_rf_initialization_loader_20261114_v2/bcsp_scq_rf_residual_v2.py')
  def knn(k,M,Q):return torch.cdist(Q,M).topk(k,largest=False).indices
  class First(nn.Module):
   def forward(self,M,F,z,Q):return Q+torch.tensor([.04,-.03,.02]),dict(indices=knn(8,M,Q))
  class Decoder(nn.Module):
   def forward(self,q,v,q_pos,v_pos,**kw):return q+v.mean(1,keepdim=True)*.01+q_pos.mean(-1,keepdim=True)
  class Base(nn.Module):
   def __init__(self):
    super().__init__();self.encoder=nn.Identity();self.coarse_pred=nn.Linear(1024,768);self.scq=First();self.mlp_query=nn.Linear(1027,384);self.decoder=Decoder()
    self.rf=rfmod.RFResidual.__new__(rfmod.RFResidual);nn.Module.__init__(self.rf);self.rf.variant='RF-Requery';self.rf.knn=knn;self.rf.V1=nn.Linear(1802,128);self.rf.V2=nn.Linear(128,3)
    self.use_denoise=False;self.query_selection='learned_only';self.scqr_query_conditioner=None;self.full_instrumentation_enabled=False
    self.register_buffer('feature',torch.sin(torch.arange(256*384,dtype=torch.float32).reshape(1,256,384)*.03))
   def forward(self,x,epoch=None):
    M=x[:,:256];F=self.encoder(self.feature+x.mean());z=x.mean((1,2))[:,None].expand(-1,1024);Q0=self.coarse_pred(z).reshape(1,256,3)
    Q1,info=self.scq(M,F,z,Q0);Q2,info2=self.rf(M,F,z,Q1,info['indices'])
    q=self.mlp_query(torch.cat((z[:,None,:].expand(-1,256,-1),Q2),-1));return self.decoder(q=q,v=F,q_pos=Q2,v_pos=M),Q2,0,None
  class Model(nn.Module):
   forward=env['forward']
   def __init__(self):
    super().__init__();self.base_model=Base();self.decoder_type='fc';self.factor=32;self.num_query=256;self.full_instrumentation_enabled=False
    self.increase_dim=nn.Sequential(nn.Conv1d(384,1024,1),nn.BatchNorm1d(1024),nn.LeakyReLU(.2),nn.Conv1d(1024,1024,1));self.reduce_map=nn.Linear(1411,384);self.decode_head=env['SimpleRebuildFCLayer'](768,32)
   def enable_full_instrumentation(self,value):self.full_instrumentation_enabled=value;self.base_model.full_instrumentation_enabled=value
  torch.manual_seed(17);model=Model().eval();x=torch.randn(1,8192,3)
  oldstat={k:v.clone() for k,v in model.state_dict().items()};rng=torch.get_rng_state().clone()
  def hookcount(m):return {id(v):(len(v._forward_pre_hooks),len(v._forward_hooks)) for v in m.modules()}
  hooks=hookcount(model)
  with torch.inference_mode():
   result=c.diagnose_case(torch,model,x,c.Calls(),'ARTIFICIAL')
   M,F,z,Q1,N0=(torch.from_numpy(result[k]) for k in ('M','F','z','Q1','N0'))
   oldvariant=model.base_model.rf.variant;model.base_model.rf.variant='RF-Static'
   expected,_=model.base_model.rf.describe(M,F,z,Q1,N0);model.base_model.rf.variant=oldvariant
   check('15 duplicated old descriptor equals actual frozen Static describe',torch.equal(expected,c.old_descriptor(torch,M,F,z,Q1,N0)))
   check('16 original mother full forward FC handoff matches captured Native',np.array_equal(model(x)[1].numpy(),result['P_R']))
   eq=c.decode_only(torch,model,M,F,z,torch.from_numpy(result['Q2_R']),c.Calls(),'NEUTRAL')
   check('17 suffix Q2_R reproduces actual mother Native without encoder',np.array_equal(eq.numpy(),result['P_R']))
  check('18 exact20/40 contract counts named without full-forward conflation',c.COUNTS==dict(native=20,decoder_only=40,decoder=60,h1_new=20,h1_old=20,first_head=20))
  check('19 hooks removed after successful capture',hookcount(model)==hooks)
  check('20 parameters BN buffers and RNG unchanged',all(torch.equal(v,model.state_dict()[k]) for k,v in oldstat.items()) and torch.equal(rng,torch.get_rng_state()))
  check('21 all saved stages include true Memory/context/deltas',{'M','F','z','Q0','Q1','N0','N1','u','v','Q2_R','Q2_A','Q2_D','P_R','P_A','P_D','a','c','valid'}<=result.keys())
  check('22 Q1 geometry affects old context rather than stale Q0',not torch.equal(c.old_descriptor(torch,M,F,z,Q1,N0)[...,-7:],c.old_descriptor(torch,M,F,z,torch.from_numpy(result['Q0']),N0)[...,-7:]))
  def failing(*args):raise RuntimeError('ARTIFICIAL controlled decoder failure')
  failhook=model.base_model.decoder.register_forward_pre_hook(failing);with_fail=hookcount(model)
  with torch.inference_mode():reject('23 fail-stop capture leaves no newly leaked hooks',lambda:c.diagnose_case(torch,model,x,c.Calls(),'FAIL'))
  check('24 exception hook cleanup restores original hook set',hookcount(model)==with_fail);failhook.remove()
  budget=c.Calls()
  for _ in range(20):budget.claim('native','ARTIFICIAL')
  reject('25 hard budget rejects21st Native',lambda:budget.claim('native','ARTIFICIAL'))
  # Actual entry-loop integration: artificial checkpoint and NPZ only.
  fixture=OUT/'ARTIFICIAL';fixture.mkdir();partial=fixture/'partial.npz'
  np.savez(partial,partial=x[0].numpy(),gt=np.array([object()],dtype=object))
  check('26 D loader ignores forbidden GT object member',np.array_equal(legacy.load_partial(np,dict(input=rec(partial),n_input=8192)),x[0].numpy()))
  replay=fixture/'native.npz'
  with torch.inference_mode():Q,P=model(x)
  np.savez(replay,coarse=Q[0].numpy(),prediction=P[0].numpy())
  ck=fixture/'artificial_epoch99_step3900.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=model.state_dict()),ck)
  runs=[dict(label='Requery_'+f,variant='RF-Requery',fold=f,checkpoint=rec(ck)) for f in 'CD'];rows=copy.deepcopy(selected['cases'])
  for row in rows:row['input']=rec(partial);row['replay']=rec(replay)
  out=OUT/'loop';out.mkdir();(out/'cases').mkdir()
  def fingerprint(m):return hashlib.sha256(b''.join(t.detach().numpy().tobytes() for t in m.state_dict().values())).hexdigest()
  helper=types.SimpleNamespace(state_sha=fingerprint,tensor_sha=lambda t:hashlib.sha256(t.detach().numpy().tobytes()).hexdigest(),assert_numeric=lambda t:None)
  events=[];resources=types.SimpleNamespace(sample=lambda phase,n:events.append((phase,n)))
  files,states,counts=e.execute_cases(torch,np,legacy,helper,c,runs,rows,out,resources,lambda run:Model(),device='cpu',artificial=True)
  check('27 actual entry loop captures20 natives40 suffixes',counts==c.COUNTS and len(files)==22 and len(list((out/'cases').glob('*.npz')))==20)
  check('28 loop preserves per-model state RNG and no gradients',len(states)==2 and all(s['state_before']==s['state_after'] and s['RNG_unchanged'] for s in states))
  logs=[json.loads(x) for x in (out/'calls.jsonl').read_text().splitlines()]
  check('29 claims persist before each call finalcounts correct',len(logs)==sum(c.COUNTS.values())==180 and logs[-1]['counts']==c.COUNTS)
  check('30 complete manifests bind input/checkpoint/frame for20 cases',len((out/'diagnostic_manifest.jsonl').read_text().splitlines())==20 and len(events)==40)
  # Complete authorize() function on retained artificial control files.
  minimal=dict(schema=e.SCHEMA,status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,calls=c.COUNTS,batch_size=1,limits=dict(wall_seconds=600),identity=dict(hostname='ARTIFICIAL',gpu_uuid='ARTIFICIAL',driver_version='ARTIFICIAL'),expected_identity=dict(hostname='ARTIFICIAL',gpu_uuid='ARTIFICIAL',driver_version='ARTIFICIAL'),models=[dict(label=k,checkpoint=dict(sha256=v)) for k,v in e.PINNED_CP.items()],readiness=dict(fresh_remote_recheck_required=True,verified_this_preparation=False),formula=dict(version='DAC-plan-v2',epsilon_norm=1e-6,alpha='0.5+0.5*relu(cosine)',near_zero='alpha=0.5',detach='alpha_only'),**{k:0 for k in ('loss','backward','optimizer_steps','BNCal','TTA','warmup')})
  def write(name,data):
   p=fixture/name
   with p.open('x') as f:json.dump(data,f)
   return rec(p)
  qr=write('request.json',minimal);ar=write('authorization.json',dict(schema='bcsp-dac-r1-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL CPU FIXTURE ONLY'));rr=write('runtime.json',dict(schema='bcsp-dac-r1-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']))
  check('31 full authorize() accepts exact one-way artificial controls',e.authorize(qr,ar,rr)==minimal)
  reject('32 wrong request bytes/hash rejected',lambda:e.authorize(dict(qr,sha256='0'*64),ar,rr))
  badrr=write('circular_runtime.json',dict(schema='bcsp-dac-r1-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'],extra_reverse_binding=True))
  reject('33 runtime extra or reverse fields rejected',lambda:e.authorize(qr,ar,badrr))
  # PurePosixPath launcher rendering only, no shell, WSL or server calls.
  qlaunch=dict(identity=dict(project='/home/jovyan/adapointr_work/PoinTr',python_realpath='/opt/conda/envs/adapointr-mamba/bin/python3.10'),output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/ARTIFICIAL_DAC',entry=dict(path='/home/jovyan/adapointr_work/PoinTr/third_party/ARTIFICIAL/entry.py'),environment=dict(TMPDIR='<owned_output>/tmp'),launch_contract=dict(request_path='/home/jovyan/adapointr_work/PoinTr/third_party/ARTIFICIAL/request.json',authorization='/home/jovyan/adapointr_work/PoinTr/third_party/ARTIFICIAL/auth.json',runtime='/home/jovyan/adapointr_work/PoinTr/third_party/ARTIFICIAL/runtime.json',log='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/ARTIFICIAL_DAC/launch.log',exit_code='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/ARTIFICIAL_DAC/exit_code.txt'))
  rendered=e.render_launcher(qlaunch,'1'*64,'2'*64,'3'*64)
  check('34 POSIX launcher parents before redirect length2048',max(map(len,rendered.splitlines()))<=2048 and '\\' not in rendered.split('mkdir -p -- ')[1].splitlines()[0] and rendered.index('mkdir -- ')<rendered.index(' >'))
  reject('35 partial authorization hash forbidden',lambda:e.render_launcher(qlaunch,'1'*63,'2'*64,'3'*64))
  rejected=False
  try:out.mkdir()
  except FileExistsError:rejected=True
  check('36 existing CPU artifact directory never overwritten',rejected)
  report=dict(status='ARTIFICIAL_CPU_CONTRACT_PASS',checks=checks,count=len(checks),seconds=time.monotonic()-start,artificial=True,CUDA=0,actual_skull_payload=0,actual_checkpoint_load=0,server_operations=0,optimizer_steps=0,model_scope='Actual frozen RF residual + original mother top forward/FC class with artificial encoder/decoder; not native Mamba proof',counts=counts,sources=[rec(O/'bcsp_scq_dac_r1_core_v1.py'),rec(O/'bcsp_scq_dac_r1_entry_v1.py'),rec(Path(__file__))])
  with (OUT/'result_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
  print(json.dumps(dict(status=report['status'],checks=len(checks),seconds=report['seconds'])))
 except BaseException as exc:
  with (OUT/'failure_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',passed=checks,error=repr(exc),traceback=traceback.format_exc()),f,indent=2)
  raise
if __name__=='__main__':main()
