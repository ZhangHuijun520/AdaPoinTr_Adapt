"""One-use install/call scaffolding, bound to this separately authorized AUX_D hash."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;A=S.parent/'H2_AUX_foldC_training_preparation_v1'
old='0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517';qh='efba40fdc78db788798ba326d9a393c5e0cac48189bb507a8ec4e9fe1d5f2db9'
def adapt(t):
 return t.replace(old,qh).replace('8f76cdaacd06fba2353624885fe7ea24d4b16afb949f1ee781fe33e78d279324','53faa00c363145cc16413af174d861bdf32659ed77eb176c3ee531c83bcb9bc3').replace('bcsp_p2_H2_AUX_foldC_pending_20261107_v1.tar.gz','bcsp_p2_H2_AUX_foldD_pending_20261107_v1.tar.gz').replace('bcsp_p2_H2_AUX_foldC_20261107_v1','bcsp_p2_H2_foldD_20261107_v1').replace('H2_AUX_foldC_seed0_training_execution_request_v1.json','H2_AUX_foldD_seed0_training_execution_request_v1.json').replace('H2_AUX_C_authorized_once_20261107_v1.py','H2_AUX_D_authorized_once_20261107_v1.py').replace('first_FoldC_request_v1','AUX_D_pending_request_v1').replace('execute_authorized_H2_AUX_once_v1.py','execute_authorized_H2_AUX_D_once_v1.py')
s=adapt((A/'execute_authorized_H2_AUX_once_v1.py').read_text(encoding='utf-8')).replace('65611','60068').replace("len(members)==14,'exact14 archive members'","len(members)==12,'exact12 archive members'").replace("q['fold']=='C'","q['fold']=='D'").replace('AUX C contract','AUX D contract').replace('H2-AUX C install','H2-AUX D install').replace('H2-AUX Fold C only','H2-AUX Fold D only').replace("mapping['status']=='FROZEN_NOT_INSTALLED' and len(mapping['files'])==13","mapping['status']=='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED' and len(mapping['files'])==11").replace('exclusive13_file_install','exclusive11_file_install')
before=" ready=json.loads(payload['payload/readiness_receipt_v1.json']);need(ready['status']=='BOUNDED_H2_AUX_C_READINESS_PASS' and ready['identity']==I and ready['training_payloads']==315,'frozen readiness')\n seen={r['path'] for r in ROWS}\n for r in ready['assets']:\n  if r['path'] not in seen:exact(r);seen.add(r['path'])"
after=""" ready=json.loads(payload['payload/FoldD_readiness_snapshot_v1.json']);need(ready['status']=='FOLDD_H2_NECESSARY_READONLY_READINESS_PASS' and ready['identity']==I and ready['training_cases']==315 and ready['sources']==63,'frozen D readiness')
 need(q['aux_pairing'] is None,'AUX D only; no COUPLE D')
 reused=[q['order_plan'],q['initialization_reference'],q['numeric_policy'],q['numeric_protocol'],q['pair_contract'],q['preflight_scope'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),*q['dependencies']]
 scope=json.loads(exact(q['preflight_scope']).read_bytes());bindings=scope['bindings'];modelroot=clean(q['model_root'])
 reused+=bindings['provider']+bindings['environment_metadata']
 for r in bindings['candidate']:reused.append(dict(path=str(modelroot/r['relative_target']),bytes=r['bytes'],sha256=r['sha256']))
 for r in bindings['isolated_model_project_sources']:reused.append(dict(path=str(modelroot/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']))
 seen={r['path'] for r in ROWS}
 for r in reused:
  if r['path'] not in seen:exact(r);seen.add(r['path'])
 need(sha(modelroot/'base_model.yaml')==bindings['base_config']['sha256'],'base model config')"""
assert s.count(before)==1;s=s.replace(before,after).replace("point_hashes=ready['training_payload_hashes']","point_hashes=ready['point_SHA256']")
v=adapt((A/'invoke_authorized_H2_AUX_once_v1.py').read_text(encoding='utf-8'))
back=adapt((A/'readback_startup_v1.py').read_text(encoding='utf-8')).replace("'H2_authorization_v1.json','H2_runtime_v1.json','H2_launch_once_v1.sh'","'AUX_D_authorization_v1.json','AUX_D_runtime_v1.json','AUX_D_launch_once_v1.sh'").replace("'single_attempt_claim_v1.json'","'AUX_D_single_attempt_claim_v1.json'").replace("('H2_authorization_v1.json'","('AUX_D_authorization_v1.json'").replace("('H2_runtime_v1.json'","('AUX_D_runtime_v1.json'").replace("('H2_launch_once_v1.sh'","('AUX_D_launch_once_v1.sh'")
for name,text in [('execute_authorized_H2_AUX_D_once_v1.py',s),('invoke_authorized_H2_AUX_D_once_v1.py',v),('readback_AUX_D_startup_v1.py',back)]:
 ast.parse(text)
 with (S/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
p=S/'AUX_D_pending_request_v1/transport_payload/H2_AUX_foldD_seed0_training_execution_request_v1.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==qh
review=dict(status='AUTHORIZED_AUX_D_CALL_STATIC_REVIEW_PASS',request_sha256=qh,archive_bytes=60068,new_install_files=11,training_fold='D',training_mode='AUX',raw_byte_transport=True,command_limit_bytes=2048,no_retry=True,COUPLE_D_not_executed=True,frozen_request_and_model_source_unchanged=True,files=[dict(name=n,bytes=(S/n).stat().st_size,sha256=hashlib.sha256((S/n).read_bytes()).hexdigest()) for n in ['execute_authorized_H2_AUX_D_once_v1.py','invoke_authorized_H2_AUX_D_once_v1.py','readback_AUX_D_startup_v1.py']])
with (S/'authorized_AUX_D_call_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
print(review['status'])
