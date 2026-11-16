"""One artificial RIVE CPU batch; no real NPZ, checkpoint, server or CUDA."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,subprocess,sys,traceback
import torch
from torch import nn
O=Path(__file__).resolve().parent;R=O.parents[1];D=O/'cpu_contract_batch_v1';F=D/'ARTIFICIAL_FIXTURES'
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def main():
 D.mkdir();F.mkdir();checks=[];torch.set_num_threads(2)
 def check(n,v=True):assert v,n;checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError,KeyError,AssertionError):checks.append(n);return
  raise AssertionError('unexpected acceptance '+n)
 def write(name,j):
  p=F/name
  with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2)
  return rec(p)
 try:
  ctx=json.loads((O/'implementation_context_v1.json').read_bytes());q=copy.deepcopy(ctx['candidate']);q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION'
  mirror={k:Path(v) for k,v in ctx['mirror'].items()};ep=O/'bcsp_rive_training_entry_v1.py';bp=O/'bcsp_rive_training_bridge_v1.py'
  e=load('rive_entry_cpu',ep);bridge=load('rive_bridge_cpu',bp)
  q['P3']=write('ARTIFICIAL_P3.json',dict(status='RIVE_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(ep)['sha256'],bridge_sha256=rec(bp)['sha256'],checks=dict(ARTIFICIAL_ONLY=True)))
  original=e.exact;e.exact=lambda r:original(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else original(r)
  sm=e.source_module
  def source(n,r):
   m=sm(n,r)
   if n=='bcsp_training_contract_v1':
    x=m.exact;m.exact=lambda r:x(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else x(r)
   return m
  e.source_module=source;sequence=0
  def authorize(value,change=None,change_rt=None):
   nonlocal sequence
   sequence+=1;sys.modules.pop('bcsp_training_contract_v1',None);qr=write('ARTIFICIAL_q'+str(sequence)+'.json',value)
   a=dict(schema='bcsp-rive-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL CPU ONLY NOT EXECUTION AUTHORIZATION')
   if change:change(a)
   ar=write('ARTIFICIAL_a'+str(sequence)+'.json',a);rt=dict(schema='bcsp-rive-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'])
   if change_rt:change_rt(rt)
   return e.authorize(qr,ar,write('ARTIFICIAL_r'+str(sequence)+'.json',rt))
  _,static,metadata,selected,fold,plan,admission,common=authorize(q)
  check('full Static_C authorize actual metadata path',len(selected)==315 and len(fold['train_sources'])==63 and common==ctx['expected_common'])
  check('effective3600 preserves original86400 config',static['resources']==e.LEGACY_RESOURCES and q['resources']==e.RESOURCES and e.RESOURCES['wall_seconds']==3600 and e.LEGACY_RESOURCES['wall_seconds']==86400)
  check('3900 counts no extra optimizer or model factors',static['counts']==e.COUNTS and sum(len(x['batches']) for x in plan['epochs'])==3900)
  pair=json.loads(mirror[q['pair_contract']['path']].read_bytes())
  def for_arm(arm,ff):
   v=copy.deepcopy(q);v.update(arm=arm,variant=arm,fold=ff)
   for k in ('QC','order_plan','data_root'):v[k]=copy.deepcopy(pair['Fold'+ff][k])
   tag='Static' if arm=='RF-Static' else 'Requery';v['run_id']='SCQ_RIVE_'+tag+'_fold'+ff+'_seed0_train_ARTIFICIAL_v1';v['output']=e.PROJECT+'/logs/cranial_bcsp_fullmamba/'+v['run_id']
   rr=str(Path(v['implementation']['entry']['path']).parent).replace('\\','/');ctl=rr+'/control/'+v['run_id']
   v['launch_contract']=dict(request_path=rr+'/'+v['run_id']+'_execution_request_v1.json',authorization_path=ctl+'/authorization_v1.json',runtime_path=ctl+'/runtime_v1.json',launcher_path=ctl+'/launch_once_v1.sh',tmux_session=v['run_id']);v['launch_attempt']=ctl+'/attempt_claim_v1.json'
   if arm=='RF-Requery':
    a=dict(status='FORMAL_RIVE_POST_TRAINING_FREEZE_AUDIT_PASS',checks=dict(ARTIFICIAL=True),arm='RF-Static',fold=ff,seed=0,identity=v['identity'],pair_contract_sha256=v['pair_contract']['sha256'],expected_model_initialization=v['expected_model_initialization'],order_plan=v['order_plan'],resources=v['resources'],updates=3900,traversals=100,exposures=31200,drops=300,BNCal=False,evaluation=False,resume=False)
    v['paired_baseline']=dict(freeze=write('ARTIFICIAL_'+ff+'_Static_freeze.json',a))
   return v
  qrc=for_arm('RF-Requery','C');qsd=for_arm('RF-Static','D');qrd=for_arm('RF-Requery','D')
  for v in (qrc,qsd,qrd):
   vv,ss,mm,sel,ff,pp,aa,cc=authorize(v)
   check('full authorize '+v['arm']+'_'+v['fold'],len(sel)==315 and len(ff['dev_sources'])==21 and aa['arm']==v['arm'] and aa['fold']==v['fold'] and cc==common)
  # Rebind metadata module for policy assertions later; each authorization is fresh.
  _,static,metadata,selected,fold,plan,admission,common=authorize(q)
  for k,v in [('arm','S-ref'),('variant','RF-Requery'),('fold','D'),('seed',1),('n_input',16384),('n_output',16384),('status','AUTHORIZED'),('execution_authorized',True),('stage','CRANIAL_BCSP_SCQ_RF'),('mode','B'),('run_id','SCQ_RF_OLD')]:
   bad=copy.deepcopy(q);bad[k]=v;reject('reject drift '+k,lambda bad=bad:authorize(bad))
  reject('explicit execution grant required',lambda:authorize(q,lambda a:a.update(explicit_user_authorization=False)))
  reject('no reverse hash cycle',lambda:authorize(q,lambda a:a.update(runtime_sha256='0'*64)))
  reject('oneway runtime binding',lambda:authorize(q,change_rt=lambda r:r.update(authorization_sha256='0'*64)))
  for field in ('runtime','contract','budget_parent','rf_factory','rf_residual'):
   bad=copy.deepcopy(q);bad['implementation'][field]['sha256']='0'*64;reject('frozen source '+field,lambda bad=bad:authorize(bad))
  for field in ('initialization','rf_initialization','native_reference'):
   bad=copy.deepcopy(q);bad[field]['sha256']='0'*64;reject('exact evidence '+field,lambda bad=bad:authorize(bad))
  bad=copy.deepcopy(q);bad['resources']['wall_seconds']=86400;reject('no legacy24h implicit fallback',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['expected_model_initialization']['parameter_sha256']='0'*64;reject('full initial state drift',lambda:authorize(bad))
  for k in ('hostname','gpu_uuid','driver_version'):
   bad=copy.deepcopy(q);bad['identity'][k]='UNBOUND';reject('current identity '+k,lambda bad=bad:authorize(bad))
  bad=copy.deepcopy(q);bad['environment']['CUDA_VISIBLE_DEVICES']='GPU-STALE';reject('stale GPU selector',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['environment']['MKL_NUM_THREADS']='99';reject('numeric env changed',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['capacity']['matrix_capacity_certified']=True;reject('false full matrix capacity',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['science']['updates']=3939;reject('3900 only',lambda:authorize(bad))
  bad=copy.deepcopy(q);bad['paired_baseline']={};reject('Static does not depend on old Sref',lambda:authorize(bad))
  bad=copy.deepcopy(qrc);bad['paired_baseline']=None;reject('Requery requires new Static freeze',lambda:authorize(bad))
  bad=copy.deepcopy(qrc);bad['paired_baseline']['freeze']=q['native_reference'];reject('old RF audit cannot masquerade as RIVE baseline',lambda:authorize(bad))
  script=e.render_launcher(q,'a'*64,'b'*64,'c'*64)
  check('POSIX short launcher log directory before redirection',script.index('mkdir -p')<script.index(' >') and max(len(x.encode()) for x in script.splitlines())<=2048 and '3600s' in script and '86400s' not in script)
  check('launcher current selector fixed','export CUDA_VISIBLE_DEVICES='+q['identity']['gpu_uuid'] in script)
  bad=copy.deepcopy(q);bad['launch_contract']['runtime_path']='C:\\WINDOWS';reject('Windows control path rejected',lambda:authorize(bad))
  allowed=e.payload_paths(str(F/'train_root'),selected);check('315 train allowlist only',len(allowed)==315)
  bad=copy.deepcopy(selected);bad[0]['point_path']='../development.npz';reject('payload escape refused',lambda:e.payload_paths(str(F/'train_root'),bad))
  runtime_path=mirror[q['implementation']['runtime']['path']];tree=ast.parse(runtime_path.read_text(encoding='utf-8'));group_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups');env=dict(require=e.require);exec(compile(ast.Module([group_fn],[]),'original_grouping_only','exec'),env)
  for n,k in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory'),('bcsp_scq_residual_v1','scq_residual'),('bcsp_scq_factory_v1','scq_factory'),('bcsp_scq_rf_residual_v1','rf_residual'),('bcsp_scq_rf_factory_v1','rf_factory')]:load(n,mirror[q['implementation'][k]['path']])
  residual=sys.modules['bcsp_scq_residual_v1'];rfactory=sys.modules['bcsp_scq_rf_factory_v1']
  init=rec(mirror[q['initialization']['path']]);rfinit=rec(mirror[q['rf_initialization']['path']])
  knn=lambda k,s,q:torch.cdist(q,s).topk(k,largest=False,sorted=False).indices
  class Tiny(nn.Module):
   def __init__(self):
    super().__init__();self.base_model=nn.Module();b=self.base_model;b.coarse_pred=nn.Linear(3,768);b.mem=nn.Linear(3,384);b.global_head=nn.Linear(3,1024)
    b.scq=residual.SCQResidual('S',knn,init);b.decoder=SimpleNamespace(knn=knn)
    self.flagged=nn.Parameter(torch.randn(2,2));self.flagged._no_weight_decay=True
    self.loss_func=nn.MSELoss();self.fine_loss_func=nn.MSELoss();self.f0_evidence=dict(artificial_fixture=True)
   def forward(self,x):
    self.seen_input=x;z=x.mean(1);q0=self.base_model.coarse_pred(z).reshape(-1,256,3)
    used,info=self.base_model.scq(x[:,:256],self.base_model.mem(x[:,:256]),self.base_model.global_head(z),q0);self.base_model._scq_last_info=info
    dense=used.repeat_interleave(32,1);return used,used[:,:0],dense[:,:0],dense
   def get_loss(self,ret,target,epoch,partial=None):return ret[-1].new_zeros(()),self.loss_func(ret[0],target[:,::32])+self.fine_loss_func(ret[-1],target)
  def build_s():
   with torch.random.fork_rng(devices=[]):torch.manual_seed(901);return Tiny()
  def build_rf():
   model=build_s();model,ev=rfactory.install(model,'RF-Static',rfinit);return model,dict(parent=dict(parent=dict(artificial_fixture=True)),rf=ev)
  def tensor_sha(t):return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
  baseline=build_s();rfmodel,ev=build_rf()
  check('real RF Requery install preserves all S tensors and RNG',ev['rf']['common_state_preserved'] and ev['rf']['CPU_RNG_preserved'] and all(tensor_sha(t)==tensor_sha(rfmodel.state_dict()[n]) for n,t in baseline.state_dict().items()))
  check('231171 actual new RF parameters',sum(p.numel() for p in rfmodel.base_model.rf.parameters())==231171)
  groups,rows=env['optimizer_groups'](rfmodel);d={r['name']:r['weight_decay'] for r in rows}
  check('eight SCQ RF weights biases use unchanged grouping',all(d['base_model.'+name]==v for name,v in [('scq.W1.weight',.0005),('scq.W2.weight',.0005),('scq.W1.bias',0),('scq.W2.bias',0),('rf.V1.weight',.0005),('rf.V2.weight',.0005),('rf.V1.bias',0),('rf.V2.bias',0)]))
  check('no decay flag preserved and parameter partition unique',d['flagged']==0 and len({id(x) for g in groups for x in g['params']})==sum(len(g['params']) for g in groups))
  gen=torch.Generator().manual_seed(120);partial=torch.randn(8,8192,3,generator=gen)*.3;target=torch.randn(8,8192,3,generator=gen)*.3
  helper=SimpleNamespace(tensor_sha=tensor_sha,validate_model=lambda model:None,assert_numeric=lambda t:None,state_sha=lambda *a:'ARTIFICIAL_STATE')
  class BudgetParent:
   class TrainingBudget:
    def __init__(self,limits,out,torch,helper):self.limits=dict(limits);self.output=Path(out);self.output.mkdir();self.final_calls=0
    def before_step(self,step):pass
    def after_step(self,step):pass
    def before_final(self):self.final_calls+=1
  class RuntimeSpy:
   optimizer_groups=staticmethod(env['optimizer_groups'])
   class BCSPDataset:
    def __init__(self,root,records,sources,n):assert len(records)==315 and len(sources)==63 and n==8192
   @staticmethod
   def make_loader(dataset,plan,epoch):return dict(ARTIFICIAL=True,epoch=epoch)
   @staticmethod
   def train_lifecycle(model,loader,records,plan,out,**kwargs):
    assert loader(0)==dict(ARTIFICIAL=True,epoch=0);budget=kwargs['resources'];model.train();budget.before_step(0)
    ret=model(partial);_,loss=model.get_loss(ret,target,0,partial=partial);loss.backward();budget.after_step(1)
    assert model.seen_input is partial
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.base_model.rf.parameters())
    assert model.base_model.rf.V2.weight.grad.abs().sum()>0
    assert model.base_model.rf.V1.weight.grad.abs().sum()==0
    return dict(optimizer_steps=0)
  class BridgeSpy:
   @staticmethod
   def train_lifecycle(runtime,h,model,*args,**kw):kw.pop('admission');return runtime.train_lifecycle(model,*args,**kw)
  localq=copy.deepcopy(q);localq['output']=str(F/'dispatch_Requery');localq['initialization']=init;localq['rf_initialization']=rfinit
  expected=hashlib.sha256(json.dumps({n:tensor_sha(t) for n,t in baseline.state_dict().items()},sort_keys=True).encode()).hexdigest()
  budget=e.make_budget(BudgetParent,e.RESOURCES,localq['output'],torch,helper,localq,plan)
  calls=[]
  def factory_spy(builder,variant,scq,rfi):
   assert variant=='RF-Static' and scq==init and rfi==rfinit;calls.append(1);return build_rf()
  result=e.dispatch_training(localq,selected,fold,plan,factory=factory_spy,model_builder=lambda:None,runtime=RuntimeSpy,bridge=BridgeSpy,admission=admission,expected_common=expected,helper=helper,budget=budget,torch=torch,knn_enable=lambda:None,device='cpu',artificial_cpu=True)
  log=json.loads((Path(localq['output'])/'SCQ_geometry.jsonl').read_text().strip());parts=log['geometry']
  check('actual dispatch real RF residual forward backward no optimizer',result['optimizer_steps']==0 and calls==[1])
  check('Q2 coarse identity and measured neighbor equality logged',parts['Q2']['centroid']==parts['coarse']['centroid'] and parts['N0_N1_equal'] is True and set(parts)>={'Q0','Q1','Q2','delta0','delta1','dense'})
  check('initial zero second residual leaves Q2 equal Q1',parts['Q1']==parts['Q2'] and parts['delta1']['max_norm']==[0.]*8)
  check('both unchanged losses and exact first batch logged',set(log['loss_components'])=={'coarse_CD','dense_CD'} and log['case_ids']==plan['epochs'][0]['batches'][0])
  reject('early finalization rejected',budget.before_final);budget.logged_geometry=3900;budget.before_final();check('3900 finalization retained',budget.final_calls==1)
  rq=copy.deepcopy(localq);rq.update(arm='RF-Requery',variant='RF-Requery');rq['output']=str(F/'dispatch_Requery_real')
  def requery_factory(builder,variant,scq,rfi):
   assert variant=='RF-Requery';m=build_s();m,ev=rfactory.install(m,variant,rfi);return m,dict(parent=dict(parent=dict(artificial_fixture=True)),rf=ev)
  rb=e.make_budget(BudgetParent,e.RESOURCES,rq['output'],torch,helper,rq,plan)
  ar=dict(admission,arm='RF-Requery')
  rr=e.dispatch_training(rq,selected,fold,plan,factory=requery_factory,model_builder=lambda:None,runtime=RuntimeSpy,bridge=BridgeSpy,admission=ar,expected_common=expected,helper=helper,budget=rb,torch=torch,knn_enable=lambda:None,device='cpu',artificial_cpu=True)
  check('same actual dispatch admits Requery forward backward',rr['optimizer_steps']==0 and rb.logged_geometry==1)
  check('effective resource budget copied without old static mutation',rb.limits['wall_seconds']==3600 and static['resources']['wall_seconds']==86400)
  # Fixed nonzero artificial second head exercises upstream gradients and relative geometry at Q1.
  probe,_=build_rf()
  with torch.no_grad():probe.base_model.scq.W2.weight.fill_(.0001);probe.base_model.rf.V2.weight.fill_(.0001)
  out=probe(partial);info=probe.base_model._scq_last_info;(_,loss)=probe.get_loss(out,target,0);loss.backward()
  check('nonzero artificial second head reaches V1 and first head',probe.base_model.rf.V1.weight.grad.abs().sum()>0 and probe.base_model.scq.W2.weight.grad.abs().sum()>0)
  check('Requery indices recomputed at Q1 and Q2 consumed',torch.equal(info['N1'],info['N0']) and torch.equal(info['Qused'],out[0].detach()) and bool((info['Q1']!=info['Q0']).any()))
  h,description=probe.base_model.rf.describe(partial[:,:256],probe.base_model.mem(partial[:,:256]),probe.base_model.global_head(partial.mean(1)),info['Q1'],info['N0'])
  batch=torch.arange(8)[:,None,None];rel=partial[:,:256][batch,info['N1']]-info['Q1'][:,:,None]
  check('actual Requery relative mean uses Q1 and N1',torch.allclose(description['geometry'][...,:3],rel.mean(2),atol=1e-7,rtol=1e-6))
  # One fixed nondegenerate mechanism fixture; no radius/axis/weight scan.
  base=build_s();static_model,_=rfactory.install(base,'RF-Static',rfinit)
  requery_base=build_s();requery_model,_=rfactory.install(requery_base,'RF-Requery',rfinit)
  check('Static Requery full artificial initial states identical',set(static_model.state_dict())==set(requery_model.state_dict()) and all(tensor_sha(t)==tensor_sha(requery_model.state_dict()[n]) for n,t in static_model.state_dict().items()))
  M=torch.zeros(1,256,3);M[0,:,0]=torch.arange(256)*.01
  Ff=torch.arange(256*384,dtype=torch.float32).reshape(1,256,384)/1000
  z=torch.zeros(1,1024);Qraw=M.clone();Q1=Qraw+torch.tensor([.5,0.,0.]);N0=knn(8,M,Qraw)
  hs,ds=static_model.base_model.rf.describe(M,Ff,z,Q1,N0);hr,dr=requery_model.base_model.rf.describe(M,Ff,z,Q1,N0)
  check('fixed fixture has true changed neighbor sets',not torch.equal(ds['indices'],dr['indices']) and torch.equal(ds['indices'],N0) and torch.equal(dr['indices'],knn(8,M,Q1)))
  check('fixed fixture conditions differ without model changes',not torch.equal(hs,hr) and not torch.equal(ds['geometry'],dr['geometry']))
  fake_info=dict(info);fake_info.update(Q0=Qraw,delta=(Q1-Qraw),Q1=Q1,delta0=(Q1-Qraw),delta1=torch.zeros_like(Q1),Qused=Q1,N0=N0,N1=dr['indices'])
  logging_model=SimpleNamespace(base_model=SimpleNamespace(rf=SimpleNamespace(variant='RF-Static'),_scq_last_info=fake_info))
  sample_ret=(Q1,Q1[:,:0],Q1[:,:0],Q1.repeat_interleave(32,1))
  reject('Static logging refuses mixed neighbor selection',lambda:e.scq_geometry(logging_model,sample_ret))
  inert=SimpleNamespace(__file__=str(runtime_path),train_lifecycle=lambda *a,**kw:kw);fake=SimpleNamespace(f0_evidence=dict(artificial_fixture=False),base_model=SimpleNamespace(rf=SimpleNamespace(variant='RF-Static')))
  check('actual bridge rehash delegates unchanged runtime',bridge.train_lifecycle(inert,q['implementation']['runtime']['sha256'],fake,admission=admission,device='cuda:0',foo=7)==dict(device='cuda:0',foo=7))
  reject('bridge production CPU refused',lambda:bridge.train_lifecycle(inert,q['implementation']['runtime']['sha256'],fake,admission=admission,device='cpu'))
  reject('bridge wrong runtime identity refused',lambda:bridge.train_lifecycle(inert,'0'*64,fake,admission=admission,device='cuda:0'))
  other=SimpleNamespace(f0_evidence=dict(artificial_fixture=False),base_model=SimpleNamespace(rf=SimpleNamespace(variant='RF-Requery')))
  reject('bridge arm mismatch refused',lambda:bridge.train_lifecycle(inert,q['implementation']['runtime']['sha256'],other,admission=admission,device='cuda:0'))
  check('real bridge admits Requery with matching authority',bridge.train_lifecycle(inert,q['implementation']['runtime']['sha256'],other,admission=dict(admission,arm='RF-Requery'),device='cuda:0',foo=8)==dict(device='cuda:0',foo=8))
  owned=F/'policy_owned';owned.mkdir();impl={k:rec(mirror[r['path']]) for k,r in q['implementation'].items()}
  config=dict(entry=rec(ep),cuda=impl['cuda_entry'],native=impl['native_helper'],budget=impl['budget_parent'],helper=impl['preflight_helper'],implementation={k:impl[k] for k in ['encoder','factory','lqi_decoder','lqi_factory']},extra={k:impl[k] for k in ['scq_residual','scq_factory']},initialization=init,rf_initialization=rfinit,runtime=impl['runtime'],contract=impl['contract'],bridge=impl['bridge'],all_implementation=impl,adapter=rec(R/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/tools/bcsp_adapter.py'),owned=str(owned.resolve()),train=str((F/'ARTIFICIAL_TRAIN.npz').resolve()),dev=str((F/'ARTIFICIAL_DEV.npz').resolve()),neighbor=str(runtime_path.parent/'UNBOUND_STATIC_NEIGHBOR.py'))
  finite=dict(implementation=impl,initialization=init,rf_initialization=rfinit)
  check('19 unique finite sources and both initializers',len(e.startup_read_records(finite))==19)
  dup=copy.deepcopy(finite);dup['implementation']['duplicate']=dict(impl['bridge']);check('identical read identities deduplicate',len(e.startup_read_records(dup))==19)
  dup['implementation']['duplicate']['bytes']+=1;reject('conflicting read identities rejected',lambda:e.startup_read_records(dup))
  c=write('ARTIFICIAL_policy.json',config)
  child="import ast,json,sys,types,importlib.util\nfrom pathlib import Path\nimport torch\nc=json.loads(Path(sys.argv[1]).read_bytes())\nfrom torch.utils.data import Dataset,DataLoader\nimport numpy,traceback,linecache,tokenize\ndef load(n,r):\n s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m\ne=load('policy_entry',c['entry']);cu=load('policy_cuda',c['cuda']);native=load('policy_native',c['native']);budget=load('policy_budget',c['budget']);helper=load('policy_helper',c['helper'])\n# Preload the same exact adapter/contract dependencies used by production before the hook.\ntools=types.ModuleType('tools');tools.__path__=[];sys.modules['tools']=tools\nload('tools.bcsp_adapter',c['adapter']);load('bcsp_training_contract_v1',c['contract'])\nguard=cu.ExactSCQReads(native.ExactSourceReads(c['implementation']),e.startup_read_records(dict(implementation=c['all_implementation'],initialization=c['initialization'],rf_initialization=c['rf_initialization'])))\nroots=[Path(sys.prefix),Path(sys.base_prefix)];out=Path(c['owned']);allowed={Path(c['train']):'ARTIFICIAL_HASH'};utc=types.SimpleNamespace(allow=lambda *a:False)\nbase_policy=budget.make_training_policy(helper,roots,out,allowed,utc)\nt=ast.parse(Path(c['entry']['path']).read_text(encoding='utf-8'));node=next(n for n in ast.walk(t) if isinstance(n,ast.ClassDef) and n.name=='Policy');env=dict(base_policy=base_policy,guard=guard,utc=utc);exec(compile(ast.Module([node],[]),'actual_nested_training_policy','exec'),env);policy=env['Policy'](roots,out)\npolicy.check(17,False);policy.check(c['train'],False);policy.check(out/'ckpt-last.pth',True)\nfor p,w in [(c['dev'],False),(c['train'],True),(out/'other.pth',False),(c['extra']['scq_factory']['path'],True),(c['initialization']['path'],True)]:\n try:policy.check(p,w)\n except (ValueError,RuntimeError):pass\n else:raise AssertionError('policy accepted forbidden path')\n# Source-module size/hash/link wrapper must agree with the read guard before import.\ntry:e.source_module('bad_runtime_hash',dict(c['runtime'],sha256='0'*64))\nexcept (ValueError,RuntimeError):pass\nelse:raise AssertionError('runtime wrong hash accepted')\nfor p,w in [(c['runtime']['path'],True),(c['neighbor'],False)]:\n try:policy.check(p,w)\n except (ValueError,RuntimeError):pass\n else:raise AssertionError('runtime write or unbound sibling accepted')\ntry:policy.check(c['rf_initialization']['path'],True)\nexcept (ValueError,RuntimeError):pass\nelse:raise AssertionError('RF initializer write accepted')\nsys.addaudithook(policy.audit)\nloaded=[]\nfor n,k in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory'),('bcsp_scq_residual_v1','scq_residual'),('bcsp_scq_factory_v1','scq_factory')]:\n e.source_module(n,c['all_implementation'][k]);loaded.append(k)\ne.source_module('bcsp_scq_rf_residual_v1',c['all_implementation']['rf_residual']);loaded.append('rf_residual')\ne.source_module('bcsp_scq_rf_factory_v1',c['all_implementation']['rf_factory']);loaded.append('rf_factory')\nbridge=e.source_module('bcsp_scq_training_bridge_v1',c['bridge']);loaded.append('bridge')\nrt=e.source_module('actual_reused_runtime_under_policy',c['runtime']);loaded.append('runtime')\nassert loaded==['encoder','factory','lqi_decoder','lqi_factory','scq_residual','scq_factory','rf_residual','rf_factory','bridge','runtime']\nassert rt.__file__==c['runtime']['path'] and callable(rt.train_lifecycle) and callable(rt.make_optimizer)\nassert rt.BCSPDataset.__module__=='actual_reused_runtime_under_policy'\nassert sys.modules['bcsp_scq_residual_v1'].load_initialization(c['initialization'])['Pfix'].shape==(7,384)\nassert sys.modules['bcsp_scq_rf_residual_v1'].load_initialization(c['rf_initialization'])['V1.weight'].shape==(128,1802)\n# Real bridge validation and runtime rehash; delegated lifecycle is an inert recorder.\ncalls=[];inert=types.SimpleNamespace(__file__=rt.__file__,train_lifecycle=lambda *a,**kw:(calls.append(kw) or 'INERT_NO_TRAINING'))\nfake=types.SimpleNamespace(f0_evidence=dict(artificial_fixture=False),base_model=types.SimpleNamespace(rf=types.SimpleNamespace(variant='RF-Static')))\nassert bridge.train_lifecycle(inert,c['runtime']['sha256'],fake,admission=dict(status='RIVE_FROZEN_NATIVE_EVIDENCE_REUSED',arm='RF-Static',fold='C',seed=0),device='cuda:0',artificial_marker=1)=='INERT_NO_TRAINING'\nassert calls==[dict(device='cuda:0',artificial_marker=1)]\n# Exercise exception source retrieval for every finite source, not only runtime.\nfor k,r in c['all_implementation'].items():\n lines=linecache.getlines(r['path'])\n assert lines and ''.join(lines)==Path(r['path']).read_text(encoding='utf-8'),k\ntry:policy.check(c['neighbor'],False)\nexcept RuntimeError:\n tb=traceback.format_exc()\n assert 'write/read boundary:' in tb and 'inherited_training_budget_v1.py' in tb and 'Original exception was:' not in tb,tb\nelse:raise AssertionError('unbound neighbor accepted')\nfor k,r in c['all_implementation'].items():\n try:policy.check(r['path'],True)\n except (ValueError,RuntimeError):pass\n else:raise AssertionError('source write accepted '+k)\nfor field,value in [('sha256','0'*64),('bytes',c['bridge']['bytes']+1)]:\n try:e.source_module('bad_bridge_'+field,dict(c['bridge'],**{field:value}))\n except (ValueError,RuntimeError):pass\n else:raise AssertionError('bridge identity drift accepted')\nguard.close();print(json.dumps(dict(exact_SCQ_source_bin_reads=True,train_only_NPZ=True,final_only_checkpoint=True,source_writes_denied=True,integer_fd_compatible=True,actual_runtime_source_loaded=True,runtime_write_rejected=True,unbound_runtime_neighbor_rejected=True,wrong_runtime_hash_rejected=True,complete_source_load_order=True,real_bridge_runtime_rehash=True,all17_source_traceback_lines=True,original_exception_preserved=True,all17_bound_source_writes_denied=True,bridge_hash_size_drift_denied=True)))\n"
  cp=subprocess.run([sys.executable,'-I','-B','-c',child,c['path']],capture_output=True,timeout=40)
  for k,v in [('stdout',cp.stdout),('stderr',cp.stderr)]:
   with (D/('policy_'+k+'.bin')).open('xb') as f:f.write(v)
  check('actual complete RF source bridge runtime policy and traceback',cp.returncode==0 and all(json.loads(cp.stdout).values()))
  result=dict(status='RIVE_TRAINING_ARTIFICIAL_CPU_PASS',count=len(checks),checks=checks,entry=rec(ep),bridge=rec(bp),test=rec(Path(__file__)),torch=torch.__version__,artificial_full_forward=3,artificial_backward=3,optimizer_steps=0,CUDA_calls=0,server_operations=0,real_payload_arrays_read=0,checkpoint_loads=0,limitations=['Tiny artificial model with actual unchanged SCQ/RF residuals and install; no native full Mamba CUDA executed.','Original runtime loaded under actual read policy, not executed. Production bridge delegation uses an inert recorder.','Synthetic authorization/runtime fixtures are test-only and grant no production permission.'])
  with (D/'result_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
  print(json.dumps(dict(status='PASS',checks=len(checks))))
 except BaseException as exc:
  with (D/'failure_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()),f,indent=2)
  raise
if __name__=='__main__':main()
