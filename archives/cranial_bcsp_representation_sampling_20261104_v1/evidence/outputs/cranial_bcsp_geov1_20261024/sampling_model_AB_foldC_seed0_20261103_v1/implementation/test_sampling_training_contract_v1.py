"""Exactly one metadata/bootstrap CPU contract batch; no torch or real auth files."""
import ast,copy,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
I=Path(__file__).resolve().parent;O=I.parent;B=O.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main():
 out=O/'cpu_contract_attempt_v2';out.mkdir(exist_ok=False)
 m=load('sampling_contract_fixture',I/'bcsp_sampling_training_contract_v1.py')
 qc=json.loads((O/'paired_train_data_receipt.json').read_text(encoding='utf-8'))
 records={a:[json.loads(s) for s in (O/a/'train_manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()] for a in m.ARMS}
 folds=json.loads((B/'consolidated_binding_v1/fold_binding.json').read_text(encoding='utf-8'))
 cfg=json.loads((O/'static_training_config_v1.json').read_text(encoding='utf-8'))
 plan=json.loads((O/'shared_order_foldC_seed0_v1.json').read_text(encoding='utf-8'))
 results=[]
 def test(name,fn):
  fn();results.append({'name':name,'status':'PASS'});print('PASS',len(results),name,flush=True)
 def reject(fn):
  try:fn()
  except (ValueError,KeyError):return
  raise AssertionError('invalid contract accepted')
 def valid():
  for arm in m.ARMS:
   r,f=m.metadata_values(qc,records,folds,'C',8192,arm);assert len(r)==315 and len(f['train_sources'])==63
  assert m.validate_static(cfg)==cfg
 test('both same-count sampler arms and fixed static config accepted',valid)
 def oldstage():
  c=copy.deepcopy(cfg);c['stage']='BCSP_INPUT_DENSITY_V1';reject(lambda:m.validate_static(c))
 test('legacy density stage rejected',oldstage)
 test('16k arm rejected',lambda:reject(lambda:m.metadata_values(qc,records,folds,'C',16384,'V1')))
 def leak():
  f=copy.deepcopy(folds);f['folds']['C']['dev_sources'][0]=f['folds']['C']['train_sources'][0]
  reject(lambda:m.metadata_values(qc,records,f,'C',8192,'V1'))
 test('development/train source overlap rejected',leak)
 def missing():
  r=copy.deepcopy(records);r['V1'].pop();reject(lambda:m.metadata_values(qc,r,folds,'C',8192,'V1'))
 test('missing training record rejected',missing)
 def duplicate():
  r=copy.deepcopy(records);r['V1'][1]=copy.deepcopy(r['V1'][0]);reject(lambda:m.metadata_values(qc,r,folds,'C',8192,'V1'))
 test('duplicate/reordered case rejected',duplicate)
 def target():
  r=copy.deepcopy(records);r[m.ARMS[1]][0]['target_array_sha256']='f'*64;reject(lambda:m.metadata_values(qc,r,folds,'C',8192,'V1'))
 test('different paired target rejected',target)
 def frame():
  r=copy.deepcopy(records);r[m.ARMS[1]][0]['normalization']['scale']+=1;reject(lambda:m.metadata_values(qc,r,folds,'C',8192,'V1'))
 test('different paired D-only frame rejected',frame)
 def pointorder():
  r=copy.deepcopy(records);r[m.ARMS[1]][0]['common_point_order_sha256']='e'*64;reject(lambda:m.metadata_values(qc,r,folds,'C',8192,'V1'))
 test('different common input permutation rejected',pointorder)
 def order():
  assert m.validate_order(plan,plan['case_ids'])==plan
  p=copy.deepcopy(plan);p['epochs'][0]['batches'].pop();reject(lambda:m.validate_order(p,plan['case_ids']))
 test('frozen order accepted and 3900-step order mismatch rejected',order)
 def authorization():
  # All objects stay in RAM and are unmistakably labelled artificial fixtures.
  q={k:{} for k in ['QC','GPU_audit','preflight_scope','resource_rebind']}
  q.update(schema='bcsp-sampling-training-request-v1',stage=m.STAGE,status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id='ARTIFICIAL_MEMORY_FIXTURE',fold='C',n_input=8192,arm='V1',paired_initialization=None,
    static_config={'path':'CFG','sha256':m.IMMUTABLE['static_config']},order_plan={'sha256':m.IMMUTABLE['order_plan']},
    preflight_request_sha256='c'*64,identity={'fixture':True},data_root='ARTIFICIAL',model_root='ARTIFICIAL',
    implementation={'runtime':{'sha256':m.IMMUTABLE['training_runtime']}},output='ARTIFICIAL',launch_attempt='ARTIFICIAL')
  grant={'schema':'bcsp-training-authorization-v1','request_sha256':'a'*64,'explicit_user_authorization':True,'user_authorization_text':'ARTIFICIAL MEMORY TEST, NOT USER AUTHORIZATION'}
  rt={'schema':'bcsp-training-runtime-v1','request_sha256':'a'*64,'authorization_sha256':'b'*64}
  values={'Q':q,'A':grant,'R':rt,'CFG':cfg};oldjson,oldrebind=m.json_bound,m.validate_rebind
  try:
   m.json_bound=lambda r:values[r['path']];m.validate_rebind=lambda *args:{'new_identity':q['identity']}
   call=lambda:m.authorize({'path':'Q','sha256':'a'*64},{'path':'A','sha256':'b'*64},{'path':'R','sha256':'d'*64})
   assert call()[0]==q
   m.validate_pair_initialization(None,q,'p','s','o')
   candidate=dict(q,arm=m.ARMS[1],paired_initialization={'path':'ARTIFICIAL_MEMORY_ONLY'})
   value={'schema':'bcsp-sampling-paired-initialization-v1','stage':m.STAGE,'verified_updates':3900,
     'baseline_run_id':'bcsp_sampling_ab_foldC_V1_in8192_out8192_seed0_train_v1','identity':q['identity'],
     'static_config_sha256':q['static_config']['sha256'],'runtime_sha256':q['implementation']['runtime']['sha256'],
     'order_plan_sha256':q['order_plan']['sha256'],'order_canonical_sha256':'o','parameter_sha256':'p','persistent_state_sha256':'s'}
   m.validate_pair_initialization(value,candidate,'p','s','o')
   reject(lambda:m.validate_pair_initialization(value,candidate,'different_initialization','s','o'))
   reject(lambda:m.validate_pair_initialization(None,candidate,'p','s','o'))
   grant['runtime_sha256']='d'*64;reject(call);del grant['runtime_sha256']
   rt['request_sha256']='f'*64;reject(call);rt['request_sha256']='a'*64
   grant['explicit_user_authorization']=False;reject(call);grant['explicit_user_authorization']=True
   q['stage']='BCSP_INPUT_DENSITY_V1';reject(call)
  finally:m.json_bound,m.validate_rebind=oldjson,oldrebind
 test('one-way authorization accepted in RAM; reverse/stale/legacy authorization rejected',authorization)
 def arithmetic():
  original=(B/'training_closure_v5/bcsp_training_runtime_v5.py').read_text(encoding='utf-8')
  expected=original.replace('state = guard.finish()',"state = guard.finish()\n        state['stage'] = 'BCSP_SAMPLING_AB_V1'").replace("'stage': 'BCSP_INPUT_DENSITY_V1'","'stage': 'BCSP_SAMPLING_AB_V1'")
  assert (I/'bcsp_sampling_training_runtime_v1.py').read_text(encoding='utf-8')==expected
  for p in I.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
  entry=load('sampling_entry_bootstrap_fixture',I/'bcsp_sampling_training_entry_v1.py')
  assert all(callable(getattr(entry,n)) for n in ['authorize','verify_qualified_receipt','validate_order'])
  assert 'torch' not in sys.modules and 'numpy' not in sys.modules
 test('training arithmetic unchanged, exact-hash entry bootstrap imports no torch',arithmetic)
 assert len(results)==12
 with (out/'result.json').open('x',encoding='utf-8') as f:json.dump({'status':'PASS','checks':12,'results':results,'test_sha256':sha(Path(__file__)),'GPU_or_model_calls':0,'real_authorization_files_created':0},f,indent=2)
 print('CPU_CONTRACT_12_PASS')
if __name__=='__main__':
 try:main()
 except BaseException:traceback.print_exc();raise
