"""One artificial CPU batch; real D metadata/authorize/mother route/bridge, no payload/GPU."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,types,textwrap,traceback
import torch
from torch import nn
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'CPU_batch_v1'
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def main():
 O.mkdir();scope=json.loads((V/'CPU_scope_v1.json').read_text(encoding='utf-8'));checks=[];torch.set_num_threads(2)
 def check(i,v):assert v,scope['checks'][i-1];assert len(checks)==i-1;checks.append(scope['checks'][i-1])
 def reject(fn):
  try:fn()
  except (ValueError,AssertionError,RuntimeError,KeyError):return True
  return False
 try:
  entry=V/'bcsp_spcg_G0_D_training_entry_v1.py';bridge=V/'bcsp_spcg_G0_D_training_bridge_v1.py';e=load('G0D_entry',entry);b=load('G0D_bridge',bridge);q=json.loads((V/'draft_G0_D_request_v1.json').read_text(encoding='utf-8'));original=copy.deepcopy(q)
  check(1,q['counts']==e.COUNTS and q['resources']==e.RESOURCES and q['arm']=='G0' and q['fold']=='D' and q['science']==dict(updates=3900,traversals=100,exposures=31200,drops=300,from_scratch=True,BNCal=False,evaluation=False,resume=False,retry=False))
  check(2,bridge.read_text(encoding='utf-8').replace("q['fold']=='D'","q['fold']=='C'")==(S/'bcsp_spcg_training_bridge_v1.py').read_text(encoding='utf-8'))
  aliases=json.loads((V/'local_metadata_map_v1.json').read_text(encoding='utf-8'));proofs={arm:json.loads(Path(aliases[r['path']]).read_text(encoding='utf-8')) for arm,r in q['C_matrix_freezes'].items()}
  check(3,len(proofs)==3 and all(all(p['checks'].values()) for p in proofs.values()) and proofs['G0']['initialization_raw_tensor_fingerprint']==q['expected_initial_state_sha256'])
  base=W/'outputs/spcg_implementation_20261116_v1';MOTHER=W/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot/models/AdaPoinTr.py'
  source=(base/'test_spcg_cpu_v1.py').read_text(encoding='utf-8');fixture=source[source.index('        env=dict(torch=torch'):source.index('        def build(arm):')];env=dict(torch=torch,nn=nn,ast=ast,types=types,W=W,MOTHER=MOTHER);exec(compile(textwrap.dedent(fixture),'actual_mother_fixture_definitions','exec'),env)
  with torch.random.fork_rng(devices=[]):torch.manual_seed(11);m=env['Model']()
  m.train();D=torch.randn(1,8192,3);target=torch.randn_like(D);ret=m(D)
  check(4,hasattr(m.base_model,'coarse_pred') and not hasattr(m.base_model,'spcg_head') and ret[0].shape==(1,256,3) and ret[-1].shape==(1,8192,3))
  ret[0].retain_grad();losses=m.get_loss(ret,target,0,partial=D);sum(losses).backward()
  check(5,ret[0].grad is not None and bool(torch.isfinite(ret[0].grad).all()) and float(ret[0].grad.norm())>0 and float(losses[0])==0)
  native=json.loads(json.loads((base/'output_policy_hotfix_v3/post_CUDA_freeze_v3/server_evidence.json').read_text())['output']['completion.json']['text'])
  check(6,q['expected_initial_state_sha256']==native['result']['models']['G0']['initial_state_sha256'])
  # Artificial auth/P3 are local fixtures only; real production files are not materialized.
  fakep3=O/'P3_fixture.json';fakep3.write_text(json.dumps(dict(status='SPCG_G0D_TRAINING_LOCAL_P3_PASS',entry_sha256=q['implementation']['entry']['sha256'],bridge_sha256=q['implementation']['bridge']['sha256'])),encoding='utf-8')
  originalexact=e.exact;originalsource=e.source
  def mapped(r):
   if r['path']==q['P3']['path']:return fakep3
   if r['path'] in aliases:
    p=Path(aliases[r['path']]);a=rec(p);assert (a['bytes'],a['sha256'])==(r['bytes'],r['sha256']);return p
   return originalexact(r)
  def source_alias(n,r):
   mod=originalsource(n,r)
   if n=='bcsp_training_contract_v1':mod.exact=mapped
   return mod
  e.exact=mapped;e.source=source_alias
  a=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256='a'*64,explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY_NO_EXECUTION_AUTHORITY');runtime=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256='a'*64,authorization_sha256='b'*64)
  qp=O/'request_fixture.json';qp.write_text(json.dumps(q),encoding='utf-8');ap=O/'auth_fixture.json';ap.write_text(json.dumps(dict(a,request_sha256=rec(qp)['sha256'])),encoding='utf-8');rp=O/'runtime_fixture.json';rp.write_text(json.dumps(dict(runtime,request_sha256=rec(qp)['sha256'],authorization_sha256=rec(ap)['sha256'])),encoding='utf-8')
  authorized,static,selected,fold,plan=e.authorize(rec(qp),rec(ap),rec(rp))
  check(7,authorized==q and len(selected)==315 and len(fold['train_sources'])==63 and len(plan['epochs'])==100 and sum(len(x['batches']) for x in plan['epochs'])==3900)
  bad=copy.deepcopy(q);bad['fold']='C';data=copy.deepcopy(q);data['data_root']=data['data_root'].replace('foldd','foldc')
  check(8,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)) and reject(lambda:e.validate(data,'a'*64,a,'b'*64,runtime)))
  bad=copy.deepcopy(q);bad['order_plan']['path']=bad['order_plan']['path'].replace('foldD','foldC');arm=copy.deepcopy(q);arm['arm']='G2'
  check(9,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)) and reject(lambda:e.validate(arm,'a'*64,a,'b'*64,runtime)))
  bad=copy.deepcopy(q);bad['C_matrix_freezes'].pop('G2');spoof=copy.deepcopy(q);spoof['C_matrix_freezes']['G1']['sha256']='0'*64
  check(10,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)) and reject(lambda:e.validate(spoof,'a'*64,a,'b'*64,runtime)))
  bad=copy.deepcopy(q);bad['environment']['CUDA_VISIBLE_DEVICES']='GPU-stale';check(11,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)))
  check(12,reject(lambda:e.validate(q,'a'*64,dict(a,runtime_sha256='c'*64),'b'*64,runtime)) and reject(lambda:e.validate(q,'a'*64,a,'c'*64,runtime)))
  launcher=e.render_launcher(q,'a'*64,'b'*64,'c'*64);check(13,launcher.index('mkdir -p')<launcher.index(' >') and '3600s' in launcher and all('\\' not in p for p in q['launch_contract'].values()))
  def fn(p,n):return ast.dump(next(x for x in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(x,ast.FunctionDef) and x.name==n),include_attributes=False)
  code=entry.read_text(encoding='utf-8');check(14,fn(entry,'fail_with_traceback')==fn(S/'UTC_order_hotfix_v3/bcsp_spcg_training_entry_v3.py','fail_with_traceback') and code.index('if utc.allow(filename,write):return')<code.index('if guard.allow(filename,write):return'))
  inherited=json.loads((S/'startup_chain_hotfix_v2/CPU_batch_v3/result.json').read_text());check(15,inherited['count']==12 and inherited['child_checks']['real_chain'])
  # Actual bridge hooks exercise all3900 observation records with a tiny artificial model.
  class CD(nn.Module):
   def forward(self,x,y):return x.mean().square()+.01*x.square().mean()
  class Tiny(nn.Module):
   def __init__(self):super().__init__();self.weight=nn.Parameter(torch.tensor(.3));self.loss_func=CD();self.fine_loss_func=CD();self.f0_evidence=dict(artificial_fixture=True)
   def forward(self,D):Q=self.weight.expand(1,256,3);P=self.weight.expand(1,8192,3);return Q,Q[:,:0],P[:,:0],P
  out=O/'artificial_bridge_run';out.mkdir();fq=copy.deepcopy(q);fq['output']=str(out);tm=Tiny();counts=dict(forward=0,backward=0);final=[]
  h=load('bcsp_spcg_head_v1',base/'bcsp_spcg_head_v1.py');observe=load('G0D_observe_cpu',base/'bcsp_spcg_runtime_v1.py')
  budget=types.SimpleNamespace(after_step=lambda step:None,before_final=lambda:final.append(True));helper=types.SimpleNamespace(assert_numeric=lambda *a:None,state_sha=lambda *a:'fixture')
  life=Path(aliases[q['implementation']['training_runtime']['path']]);rt=types.SimpleNamespace(__file__=str(life),BCSPDataset=lambda *a:'ARTIFICIAL_NO_PAYLOAD',make_loader=lambda *a:None)
  def lifecycle(model,loader,*args,**kw):
   for step in range(1,3901):
    model.zero_grad();r=model(torch.zeros(1,1,3));counts['forward']+=1;(model.loss_func(r[0],None)+model.fine_loss_func(r[-1],None)).backward();counts['backward']+=1;kw['resources'].after_step(step)
   kw['resources'].before_final();return counts
  rt.train_lifecycle=lifecycle
  result=b.dispatch(fq,tm,rt,selected,fold,plan,helper,budget,observe,device='cpu',artificial_cpu=True)
  rows=[json.loads(x) for x in (out/'SPCG_geometry.jsonl').read_text().splitlines()]
  check(16,len(rows)==3900 and [x['step'] for x in rows if 'total_loss_Q_gradient' in x]==[1,39,390,1950,3900])
  check(17,result==dict(forward=3900,backward=3900) and final==[True] and all(set(x['loss_components'])=={'coarse_CD','dense_CD'} and x['case_ids']==plan['epochs'][(x['step']-1)//39]['batches'][(x['step']-1)%39] for x in rows))
  bad=copy.deepcopy(fq);bad['fold']='C';check(18,reject(lambda:b.dispatch(bad,tm,rt,selected,fold,plan,helper,budget,observe,device='cpu',artificial_cpu=True)))
  node=next(n for n in ast.parse(life.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups');ns=dict(require=e.need);exec(compile(ast.Module(body=[node],type_ignores=[]),str(life),'exec'),ns);groups,records=ns['optimizer_groups'](m);oldhead=[x for x in records if x['name'].startswith('base_model.coarse_pred.')]
  check(19,len(oldhead)==4 and all(x['weight_decay']==(0 if x['name'].endswith('.bias') else .0005) for x in oldhead) and not any(x['name'].startswith('base_model.spcg_head.') for x in records))
  check(20,q==original and rec(entry)['sha256']==q['implementation']['entry']['sha256'] and rec(bridge)['sha256']==q['implementation']['bridge']['sha256'] and all(rec(Path(x['path']))==x for x in json.loads((V/'unchanged_inputs_v1.json').read_text(encoding='utf-8'))))
  e.exact=originalexact;e.source=originalsource
  result=dict(status='SPCG_G0_D_CPU_PASS',count=len(checks),checks=checks,entry=rec(entry),bridge=rec(bridge),test=rec(Path(__file__)),CPU_scope=rec(V/'CPU_scope_v1.json'),artificial_bridge_counts=counts,server_operations=0,GPU=0,optimizer_updates=0,limitations=['Mother forward/FC/coarse+dense loss route uses artificial encoder/decoder and surrogate CD, not actual CUDA/Mamba.','3900 bridge observation steps use a tiny artificial model with backward but no optimizer updates; no real payload read.','Full authorize uses frozen actual D metadata and path aliases with artificial P3/auth fixtures; no execution authority.','Production initialization matched by frozen CUDA/G0 proof binding, not regenerated with the artificial fixture.','Existing source-policy/import-chain evidence inherited; no GPU preflight repeated.'])
  (O/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS20_G0D_CPU_NO_SERVER')
 except BaseException as ex:
  (O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
if __name__=='__main__':main()
