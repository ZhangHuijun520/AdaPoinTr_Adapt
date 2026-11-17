"""One bounded G1 CPU batch; actual head/factory/mother forward with cheap fixture backbone."""
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
  entry=V/'bcsp_spcg_G1_C_training_entry_v1.py';bridge=V/'bcsp_spcg_G1_C_training_bridge_v1.py';e=load('actualG1_entry',entry);q=json.loads((V/'draft_G1_C_request_v1.json').read_text(encoding='utf-8'));base=W/'outputs/spcg_implementation_20261116_v1';original=copy.deepcopy(q)
  check(1,q['arm']=='G1' and q['fold']=='C' and q['counts']==e.COUNTS and q['resources']==e.RESOURCES)
  check(2,bridge.read_text(encoding='utf-8').replace("q['arm']=='G1'","q['arm']=='G0'")==(S/'bcsp_spcg_training_bridge_v1.py').read_text(encoding='utf-8'))
  baseline=S/'UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json';frozen=json.loads(baseline.read_text());check(3,frozen['order_plan']==q['order_plan'] and frozen['initialization_raw_tensor_fingerprint']==q['parent_G0_initial_state_sha256'])
  assets=dict(probe_asset=base/'artificial_cpu_batch_v1/probe_U_fp32_v1.bin',head_initialization=base/'artificial_cpu_batch_v1/head_initialization_fp32_v1.bin',mother_source=MOTHER)
  check(4,all(rec(p)['sha256']==q[k]['sha256'] and rec(p)['bytes']==q[k]['bytes'] for k,p in assets.items()))
  h=load('bcsp_spcg_head_v1',base/'bcsp_spcg_head_v1.py');f=load('G1_reference_factory',base/'bcsp_spcg_factory_v1.py')
  # Reuse only fixture definitions; do not execute the previous test batch.
  source=(base/'test_spcg_cpu_v1.py').read_text(encoding='utf-8');fixture=source[source.index('        env=dict(torch=torch'):source.index('        def build(arm):')];env=dict(torch=torch,nn=nn,ast=ast,types=types,W=W,MOTHER=MOTHER);exec(compile(textwrap.dedent(fixture),'inherited_actual_mother_fixture_definitions','exec'),env);Model=env['Model']
  def legacy():
   with torch.random.fork_rng(devices=[]):torch.manual_seed(11);return Model()
  U=h.from_bytes(assets['probe_asset'].read_bytes(),(256,3));H=assets['head_initialization'].read_bytes();ref=legacy();parentfinger=e.raw_state_fingerprint(ref);ref,change=f.install(ref,'G1',U,H,MOTHER,rec(MOTHER)['sha256']);expected=e.raw_state_fingerprint(ref)
  fixtureq=copy.deepcopy(q);fixtureq['parent_G0_initial_state_sha256']=parentfinger;fixtureq['expected_initial_state_sha256']=expected
  for k,p in assets.items():fixtureq[k]=rec(p)
  fixtureq['implementation']['spcg_factory']=rec(base/'bcsp_spcg_factory_v1.py');sys.modules['bcsp_lqi_factory_v1']=types.SimpleNamespace(build_model=lambda builder,seed:(builder(),dict(artificial_fixture=True)))
  m,evidence=e.build_G1(fixtureq,legacy);check(5,hasattr(m.base_model,'spcg_head') and m.base_model.spcg_head.arm=='G1' and not hasattr(m.base_model,'coarse_pred') and h.head_bytes(m.base_model.spcg_head)==H)
  m.train();D=torch.randn(1,8192,3);target=torch.randn_like(D);ret=m(D);losses=m.get_loss(ret,target,0,partial=D);ret[0].retain_grad();sum(losses).backward();check(6,ret[0].shape==(1,256,3) and ret[-1].shape==(1,8192,3) and ret[0].grad is not None and bool(torch.isfinite(ret[0].grad).all()))
  check(7,e.raw_state_fingerprint(ref)==expected and evidence['change']['head_parameters']==1845763)
  # Actual validate() reads real frozen evidence, local remapping only avoids remote paths.
  fakep3=O/'P3.json';fakep3.write_text(json.dumps(dict(status='SPCG_G1C_TRAINING_LOCAL_P3_PASS',entry_sha256=q['implementation']['entry']['sha256'],bridge_sha256=q['implementation']['bridge']['sha256'])))
  mapping={q['P3']['path']:fakep3,q['G0_C_freeze']['path']:baseline,q['CUDA_freeze']['path']:base/'output_policy_hotfix_v3/post_CUDA_freeze_v3/formal_audit_result_v3.json',**{q[k]['path']:p for k,p in assets.items()}}
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
  policy=load('policy_G1_parent_entry',S/'UTC_order_hotfix_v3/bcsp_spcg_training_entry_v3.py')
  def fn(p,n):return ast.dump(next(x for x in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(x,ast.FunctionDef) and x.name==n),include_attributes=False)
  check(13,fn(entry,'fail_with_traceback')==fn(S/'UTC_order_hotfix_v3/bcsp_spcg_training_entry_v3.py','fail_with_traceback') and 'if utc.allow(filename,write):return' in entry.read_text())
  order=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/shared_order_foldC_seed0_v1.json';life=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/bcsp_p1_training_runtime_v1.py';check(14,rec(order)['sha256']==q['order_plan']['sha256'] and rec(life)['sha256']==q['implementation']['training_runtime']['sha256'])
  actual=[n for n,p in m.named_parameters() if n.startswith('base_model.spcg_head.')];check(15,len(actual)==6 and all(p.ndim==1 or n.endswith('.weight') for n,p in m.named_parameters() if n.startswith('base_model.spcg_head.')))
  check(16,q==original and rec(entry)['sha256']==q['implementation']['entry']['sha256'] and rec(bridge)['sha256']==q['implementation']['bridge']['sha256'])
  (O/'result.json').write_text(json.dumps(dict(status='SPCG_G1_C_CPU_PASS',count=len(checks),checks=checks,entry=rec(entry),bridge=rec(bridge),test=rec(Path(__file__)),head=rec(base/'bcsp_spcg_head_v1.py'),factory=rec(base/'bcsp_spcg_factory_v1.py'),artificial_G1_init=expected,total_loss=float(sum(losses).detach()),server_operations=0,GPU=0,limitations=['Actual G1 head/factory and motherforward/FC/loss route exercised with artificial encoder/decoder/cheaploss; actualMamba andproductioncdist not rerun.','Inherited training lifecycle and sourcepolicy tests reused; no3900step run.','CPU baseline fingerprint is artificial, production fingerprint remains CUDAadmitted frozenG1 identity.']),indent=2),encoding='utf-8');print('PASS16_G1_CPU_NO_SERVER')
 except BaseException as ex:(O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
if __name__=='__main__':main()
