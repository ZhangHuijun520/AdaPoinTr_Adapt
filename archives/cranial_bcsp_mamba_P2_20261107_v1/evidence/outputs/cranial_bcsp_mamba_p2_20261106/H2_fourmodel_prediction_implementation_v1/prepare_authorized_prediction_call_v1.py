"""Unique frozen-hash verify/install/launch call; no scientific source changes."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;A=S.parent/'FoldD_entry_implementation_v1'
old='efba40fdc78db788798ba326d9a393c5e0cac48189bb507a8ec4e9fe1d5f2db9';qh='b95b866a6b3a0eaeb1e840e003ecd426847ed47b07675b6c1f7644b5aee97170'
def adapt(t):
 return t.replace(old,qh).replace('53faa00c363145cc16413af174d861bdf32659ed77eb176c3ee531c83bcb9bc3','69f9c1863250d7425471b4294726d0a278406d26565f496839207b0fcf9fbbcd').replace('bcsp_p2_H2_AUX_foldD_pending_20261107_v1.tar.gz','bcsp_p2_H2_fourmodel_native_prediction_pending_20261107_v1.tar.gz').replace('bcsp_p2_H2_foldD_20261107_v1','bcsp_p2_H2_fourmodel_native_prediction_20261107_v1').replace('H2_AUX_foldD_seed0_training_execution_request_v1.json','H2_C_D_fourmodel_native_prediction_execution_request_v1.json').replace('AUX_D_pending_request_v1','pending_request_v1').replace('H2_AUX_D_authorized_once_20261107_v1.py','H2_fourmodel_native_authorized_once_20261107_v1.py').replace('execute_authorized_H2_AUX_D_once_v1.py','execute_authorized_H2_native_prediction_once_v1.py')
t=adapt((A/'execute_authorized_H2_AUX_D_once_v1.py').read_text(encoding='utf-8')).replace('60068','74716').replace('One authorized H2-AUX D install/materialization/launch','One authorized H2 four-model native prediction install/materialization/launch')
oldgate=" need(q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['fold']=='D' and q['variant']=='M0' and q['h2_config']['mode']=='AUX' and q['n_input']==q['n_output']==8192,'AUX D contract')"
newgate=" need(q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['schema']=='bcsp-p2-H2-fourmodel-native-prediction-v1' and q['forward_budget']==420 and q['batch_size']==1 and q['unique_cases']==210 and q['backward']==q['optimizer_steps']==q['BNCal']==q['loss_calls']==0,'420 Native-only contract')"
assert t.count(oldgate)==1;t=t.replace(oldgate,newgate)
oldlist=" for r in [*q['implementation'].values(),q['static_config'],q['baseline_request'],q['baseline_audit'],q['p3'],q['cuda_audit'],q['readiness'],L['launcher_template']]:"
newlist=" for r in [q['entry'],q['input_index'],q['protocol'],q['P3'],*q['implementation'].values(),q['static_config'],q['numeric_policy'],q['helper'],L['launcher_template'],*q['training_audits'].values()]:"
assert t.count(oldlist)==1;t=t.replace(oldlist,newlist)
a=t.index(" stage('reverify_fixed_assets_and315_training_bytes')");b=t.index(" version=subprocess.check_output",a)
readiness=""" stage('reverify_fixed_assets_four_checkpoints_and210_inputs')
 idx=json.loads(payload['payload/'+Path(q['input_index']['path']).name]);protocol=json.loads(payload['payload/'+Path(q['protocol']['path']).name])
 need(len(idx['runs'])==4 and len(idx['inputs'])==420 and protocol['forward_budget']==420 and protocol['extra_intervention']['authorized'] is False,'4x105 native only')
 reused=[q['preflight_scope'],q['fold_binding'],q['source_index'],q['source_manifest'],q['numeric_policy'],q['static_config'],q['helper'],*q['implementation'].values(),*q['dependencies']]
 scope=json.loads(exact(q['preflight_scope']).read_bytes());bindings=scope['bindings'];modelroot=clean(q['model_root'])
 reused+=bindings['provider']+bindings['environment_metadata']
 for r in bindings['candidate']:reused.append(dict(path=str(modelroot/r['relative_target']),bytes=r['bytes'],sha256=r['sha256']))
 for r in bindings['isolated_model_project_sources']:reused.append(dict(path=str(modelroot/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']))
 seen={r['path'] for r in ROWS}
 for r in reused:
  if r['path'] not in seen:exact(r);seen.add(r['path'])
 need(sha(modelroot/'base_model.yaml')==bindings['base_config']['sha256'],'base model config')
 for run in idx['runs']:
  need(run['mode'] in ('AUX','COUPLE') and run['fold'] in ('C','D') and len(run['dev_case_ids'])==105,'native run roles')
  exact(run['checkpoint'])
 unique={}
 for row in idx['inputs']:
  rec=row['input']
  if rec['path'] in unique:need(unique[rec['path']]==rec,'shared input binding drift')
  else:unique[rec['path']]=rec
 need(len(unique)==210,'210 exact shared input files')
 for r in unique.values():exact(r)
"""
t=t[:a]+readiness+t[b:]
t=t.replace("train_NPZ_byte_hashes=315","development_NPZ_byte_hashes=210,checkpoint_byte_hashes=4")
t=t.replace("schema='bcsp-p2-H2-training-authorization-v1'","schema='bcsp-development-authorization-v1'").replace("schema='bcsp-p2-H2-training-runtime-v1'","schema='bcsp-development-runtime-v1'").replace('H2-AUX Fold D only','H2 four-model420 Native prediction only, no condition intervention/scoring/training')
t=t.replace("exact(q['implementation']['entry'])","exact(q['entry'])")
start=t.index(" validated=entry.authorize(");end=t.index(" stage('single_attempt_claim_and_tmux')",start)
validation=""" validated=entry.authorize(expected[request_name],record(L['authorization'],authsha),record(L['runtime'],runtime_sha))
 need(validated==q,'actual request authorization')
 runs,rows=entry.validate_index(idx,entry.bound(q['fold_binding']))
 entry.validate_source(idx,entry.bound(q['source_index']),[json.loads(line) for line in exact(q['source_manifest']).read_text().splitlines()])
 entry.validate_evidence(q,idx)
 emit(control/'prelaunch_authorization_contract_v1.json',dict(status='ACTUAL_AUTHORIZE_INDEX_SOURCE_EVIDENCE_PASS',request_sha256=QH,models=4,development_rows=420,unique_cases=210,forward_budget=420,backward=0,loss_calls=0,optimizer_steps=0,model_constructed=False))
"""
t=t[:start]+validation+t[end:]
v=adapt((A/'invoke_authorized_H2_AUX_D_once_v1.py').read_text(encoding='utf-8'))
back=adapt((A/'readback_AUX_D_startup_v1.py').read_text(encoding='utf-8')).replace('AUX_D_authorization_v1.json','native_prediction_authorization_v1.json').replace('AUX_D_runtime_v1.json','native_prediction_runtime_v1.json').replace('AUX_D_launch_once_v1.sh','native_prediction_launch_once_v1.sh').replace('AUX_D_single_attempt_claim_v1.json','native_prediction_single_attempt_claim_v1.json')
files={'execute_authorized_H2_native_prediction_once_v1.py':t,'invoke_authorized_H2_native_prediction_once_v1.py':v,'readback_native_prediction_startup_v1.py':back}
for name,source in files.items():
 ast.parse(source)
 with (S/name).open('x',encoding='utf-8',newline='\n') as f:f.write(source)
q=S/'pending_request_v1/transport_payload/H2_C_D_fourmodel_native_prediction_execution_request_v1.json';assert hashlib.sha256(q.read_bytes()).hexdigest()==qh
review=dict(status='AUTHORIZED_H2_NATIVE_CALL_STATIC_REVIEW_PASS',request_sha256=qh,archive_bytes=74716,new_install_files=11,readiness_checkpoint_hashes=4,readiness_unique_input_hashes=210,forward_budget=420,GT_payload_decoding_before_execution=False,extra_intervention=False,raw_byte_transport=True,command_limit_bytes=2048,no_retry=True,frozen_request_and_production_sources_unchanged=True,files=[dict(name=n,bytes=(S/n).stat().st_size,sha256=hashlib.sha256((S/n).read_bytes()).hexdigest()) for n in files])
with (S/'authorized_native_call_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
print(review['status'])
