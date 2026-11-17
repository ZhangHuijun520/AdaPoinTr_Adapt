"""One bounded G2 CPU batch; actual head/factory/mother forward with cheap fixture backbone."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,types,textwrap,traceback
import torch
from torch import nn
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'CPU_batch_v1';MOTHER=W/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot/models/AdaPoinTr.py'
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def main():
 O.mkdir();scope=json.loads((V/'CPU_scope_v1.json').read_text());checks=[];torch.set_num_threads(2)
 def check(n,v):assert v,scope['checks'][n-1];assert len(checks)==n-1;checks.append(scope['checks'][n-1])
 def reject(fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError):return True
  return False
 try:
  entry=V/'bcsp_spcg_G2_C_training_entry_v1.py';bridge=V/'bcsp_spcg_G2_C_training_bridge_v1.py';e=load('actualG2_entry',entry);q=json.loads((V/'draft_G2_C_request_v1.json').read_text(encoding='utf-8'));base=W/'outputs/spcg_implementation_20261116_v1';original=copy.deepcopy(q)
  check(1,q['arm']=='G2' and q['fold']=='C' and q['counts']==e.COUNTS and q['resources']==e.RESOURCES)
  check(2,bridge.read_text(encoding='utf-8').replace("q['arm']=='G2'","q['arm']=='G0'")==(S/'bcsp_spcg_training_bridge_v1.py').read_text(encoding='utf-8'))
  baseline=S/'UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json';frozen=json.loads(baseline.read_text());check(3,frozen['order_plan']==q['order_plan'] and frozen['initialization_raw_tensor_fingerprint']==q['parent_G0_initial_state_sha256'])
  assets=dict(probe_asset=base/'artificial_cpu_batch_v1/probe_U_fp32_v1.bin',head_initialization=base/'artificial_cpu_batch_v1/head_initialization_fp32_v1.bin',mother_source=MOTHER)
  check(4,all(rec(p)['sha256']==q[k]['sha256'] and rec(p)['bytes']==q[k]['bytes'] for k,p in assets.items()))
  h=load('bcsp_spcg_head_v1',base/'bcsp_spcg_head_v1.py');f=load('G2_reference_factory',base/'bcsp_spcg_factory_v1.py')
  # Reuse only fixture definitions; do not execute the previous test batch.
  source=(base/'test_spcg_cpu_v1.py').read_text(encoding='utf-8');fixture=source[source.index('        env=dict(torch=torch'):source.index('        def build(arm):')];env=dict(torch=torch,nn=nn,ast=ast,types=types,W=W,MOTHER=MOTHER);exec(compile(textwrap.dedent(fixture),'inherited_actual_mother_fixture_definitions','exec'),env);Model=env['Model']
  def legacy():
   with torch.random.fork_rng(devices=[]):torch.manual_seed(11);return Model()
  U=h.from_bytes(assets['probe_asset'].read_bytes(),(256,3));H=assets['head_initialization'].read_bytes();ref=legacy();parentfinger=e.raw_state_fingerprint(ref);ref,change=f.install(ref,'G2',U,H,MOTHER,rec(MOTHER)['sha256']);expected=e.raw_state_fingerprint(ref)
  fixtureq=copy.deepcopy(q);fixtureq['parent_G0_initial_state_sha256']=parentfinger;fixtureq['expected_initial_state_sha256']=expected
  for k,p in assets.items():fixtureq[k]=rec(p)
  fixtureq['implementation']['spcg_factory']=rec(base/'bcsp_spcg_factory_v1.py');sys.modules['bcsp_lqi_factory_v1']=types.SimpleNamespace(build_model=lambda builder,seed:(builder(),dict(artificial_fixture=True)))
  m,evidence=e.build_G2(fixtureq,legacy);check(5,hasattr(m.base_model,'spcg_head') and m.base_model.spcg_head.arm=='G2' and not hasattr(m.base_model,'coarse_pred') and h.head_bytes(m.base_model.spcg_head)==H)
  m.train();D=torch.randn(1,8192,3);target=torch.randn_like(D);ret=m(D);losses=m.get_loss(ret,target,0,partial=D);ret[0].retain_grad();sum(losses).backward();check(6,ret[0].shape==(1,256,3) and ret[-1].shape==(1,8192,3) and ret[0].grad is not None and bool(torch.isfinite(ret[0].grad).all()))
  check(7,e.raw_state_fingerprint(ref)==expected and evidence['change']['head_parameters']==1845763)
  # Actual validate() reads real frozen evidence, local remapping only avoids remote paths.
  fakep3=O/'P3.json';fakep3.write_text(json.dumps(dict(status='SPCG_G2C_TRAINING_LOCAL_P3_PASS',entry_sha256=q['implementation']['entry']['sha256'],bridge_sha256=q['implementation']['bridge']['sha256'])))
  mapping={q['P3']['path']:fakep3,q['G0_C_freeze']['path']:baseline,q['G1_C_freeze']['path']:S/'G1_C_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json',q['CUDA_freeze']['path']:base/'output_policy_hotfix_v3/post_CUDA_freeze_v3/formal_audit_result_v3.json',**{q[k]['path']:p for k,p in assets.items()}}
  originalexact=e.exact
  def local(r):
   if r['path'] in mapping:return mapping[r['path']]
   return originalexact(r)
  e.exact=local;a=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256='a'*64,explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_CPU_ONLY');runtime=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256='a'*64,authorization_sha256='b'*64)
  assert e.validate(q,'a'*64,a,'b'*64,runtime) is q
  bad=copy.deepcopy(q);bad['parent_G0_initial_state_sha256']='0'*64;check(8,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)))
  bad=copy.deepcopy(q);bad['arm']='G0';gpu=copy.deepcopy(q);gpu['environment']['CUDA_VISIBLE_DEVICES']='GPU-stale';check(9,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)) and reject(lambda:e.validate(gpu,'a'*64,a,'b'*64,runtime)))
  check(10,reject(lambda:e.validate(q,'a'*64,dict(a,runtime_sha256='c'*64),'b'*64,runtime)) and reject(lambda:e.validate(q,'a'*64,a,'c'*64,runtime)))
  e.exact=originalexact
  check(11,'LOG_STEPS=(1,39,390,1950,3900)' in bridge.read_text() and 'runtime.train_lifecycle(' in bridge.read_text())
  chain=json.loads((S/'startup_chain_hotfix_v2/CPU_batch_v3/result.json').read_text());check(12,chain['count']==12 and chain['child_checks']['real_chain'])
  policy=load('policy_G2_parent_entry',S/'UTC_order_hotfix_v3/bcsp_spcg_training_entry_v3.py')
  def fn(p,n):return ast.dump(next(x for x in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(x,ast.FunctionDef) and x.name==n),include_attributes=False)
  check(13,fn(entry,'fail_with_traceback')==fn(S/'UTC_order_hotfix_v3/bcsp_spcg_training_entry_v3.py','fail_with_traceback') and 'if utc.allow(filename,write):return' in entry.read_text())
  order=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/shared_order_foldC_seed0_v1.json';life=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/bcsp_p1_training_runtime_v1.py';check(14,rec(order)['sha256']==q['order_plan']['sha256'] and rec(life)['sha256']==q['implementation']['training_runtime']['sha256'])
  actual=[n for n,p in m.named_parameters() if n.startswith('base_model.spcg_head.')];check(15,len(actual)==6 and all(p.ndim==1 or n.endswith('.weight') for n,p in m.named_parameters() if n.startswith('base_model.spcg_head.')))
  check(16,q==original and rec(entry)['sha256']==q['implementation']['entry']['sha256'] and rec(bridge)['sha256']==q['implementation']['bridge']['sha256'])
  # Additional G2-specific tests, same single batch, no training or data payload.
  shared=legacy();shared,_=f.install(shared,'G1',U,H,MOTHER,rec(MOTHER)['sha256']);shared.train()
  check(17,e.raw_state_fingerprint(shared)==expected and not torch.equal(shared(D)[0],ret[0]))
  ss=torch.randn(1,256,3,requires_grad=True);ff=torch.randn(1,256,384,requires_grad=True);zz=torch.randn(1,1024,requires_grad=True)
  desc,detail=m.base_model.spcg_head.describe(D,ss,ff,zz)
  expected_idx=torch.argsort(((ss[:,None]-detail['A'][:,:,None]).detach()**2).sum(-1),dim=-1,stable=True)[...,:8]
  check(18,torch.equal(detail['index'],expected_idx) and detail['index'].shape==(1,256,8) and torch.equal(m.base_model.spcg_head(D,ss,ff,zz),m.base_model.spcg_head.net(desc)))
  m.base_model.spcg_head(D,ss,ff,zz).square().mean().backward()
  check(19,all(t.grad is not None and bool(torch.isfinite(t.grad).all()) and float(t.grad.norm())>0 for t in [ss,ff,zz]))
  # Full authorize() with actual frozen metadata validators. Only path aliases and artificial P3/auth are substituted.
  aliases=json.loads((V/'local_metadata_map_v1.json').read_text(encoding='utf-8'))
  def mapped(r):
   if r['path']==q['P3']['path']:return fakep3
   p=Path(aliases[r['path']]);assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];return p
  oldsource=e.source
  def scoped_source(n,r):
   mod=oldsource(n,r)
   if n=='bcsp_training_contract_v1':mod.exact=mapped
   return mod
  e.exact=mapped;e.source=scoped_source
  qfixture=O/'request_fixture.json';qfixture.write_text(json.dumps(q),encoding='utf-8');af=O/'authorization_fixture.json';af.write_text(json.dumps(dict(a,request_sha256=rec(qfixture)['sha256'])),encoding='utf-8');rf=O/'runtime_fixture.json';rf.write_text(json.dumps(dict(runtime,request_sha256=rec(qfixture)['sha256'],authorization_sha256=rec(af)['sha256'])),encoding='utf-8')
  def fullmapped(r):
   if r['path'] in {str(x.resolve()) for x in [qfixture,af,rf]}:return originalexact(r)
   return mapped(r)
  e.exact=fullmapped
  authorized,static,selected,fold,plan=e.authorize(rec(qfixture),rec(af),rec(rf))
  check(20,authorized==q and len(selected)==315 and len(fold['train_sources'])==63 and len(plan['epochs'])==100)
  bad=copy.deepcopy(q);bad['expected_initial_state_sha256']='0'*64;wrong=copy.deepcopy(q);wrong['arm']='G1'
  check(21,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,runtime)) and reject(lambda:e.validate(wrong,'a'*64,a,'b'*64,runtime)))
  launcher=e.render_launcher(q,'a'*64,'b'*64,'c'*64)
  check(22,all('\\' not in p for p in q['launch_contract'].values()) and '3600s' in launcher and q['implementation']['entry']['path'] in launcher and q['launch_contract']['runtime_path'] in launcher)
  groupfn=next(n for n in ast.parse(life.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups');ns=dict(require=lambda ok,msg:e.need(ok,msg));exec(compile(ast.Module(body=[groupfn],type_ignores=[]),str(life),'exec'),ns);groups,rows=ns['optimizer_groups'](m);headrows=[x for x in rows if x['name'].startswith('base_model.spcg_head.')]
  check(23,len(headrows)==6 and all(x['weight_decay']==(0 if x['name'].endswith('.bias') else .0005) for x in headrows))
  check(24,all(rec(Path(x['path']))==x for x in json.loads((V/'unchanged_inputs_v1.json').read_text(encoding='utf-8'))))
  e.exact=originalexact;e.source=oldsource
  (O/'result.json').write_text(json.dumps(dict(status='SPCG_G2_C_CPU_PASS',count=len(checks),checks=checks,entry=rec(entry),bridge=rec(bridge),test=rec(Path(__file__)),head=rec(base/'bcsp_spcg_head_v1.py'),factory=rec(base/'bcsp_spcg_factory_v1.py'),artificial_G2_init=expected,total_loss=float(sum(losses).detach()),server_operations=0,GPU=0,limitations=['Actual G2 head/factory and motherforward/FC/loss route exercised with artificial encoder/decoder/cheaploss; actualMamba andproductioncdist not rerun.','Inherited training lifecycle and sourcepolicy tests reused; no3900step run.','CPU baseline fingerprint is artificial, production fingerprint remains CUDAadmitted frozenG2 identity. Full authorize uses real metadata validators with frozen metadata aliases and artificial auth/P3; it grants no execution authority.']),indent=2),encoding='utf-8');print('PASS24_G2_CPU_NO_SERVER')
 except BaseException as ex:(O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
if __name__=='__main__':main()
