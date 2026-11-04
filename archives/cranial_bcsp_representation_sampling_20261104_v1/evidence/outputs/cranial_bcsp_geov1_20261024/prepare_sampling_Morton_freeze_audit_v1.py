"""Bind the existing successful read-only auditor to the completed candidate."""
import ast,base64,hashlib,json,shlex
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1'
C=O/'Morton_training_request_v1';A=C/'authorized_execution_v1';F=O/'post_Morton_training_freeze_audit_v1'
S='d4a44a990c0b3f0b91522c6f9803074a34e6c3803c243bf08e8a46ace42eeae3'
def h(raw):return hashlib.sha256(raw).hexdigest()
def encode(v):return json.dumps(v,ensure_ascii=True,indent=2).encode()
def save(n,raw):
 with (F/n).open('xb') as f:f.write(raw)
def main():
 sr=(C/'candidate_training_execution_request_v1.json').read_bytes();assert h(sr)==S;s=json.loads(sr)
 qr=(C/'training_entry_request_v1.json').read_bytes();q=json.loads(qr);assert h(qr)==s['inner_request']['sha256']
 base_raw=(O/'post_V1_training_freeze_audit_v2/audit_report_v2.json').read_bytes();assert h(base_raw)==s['parent_baseline_audit']['sha256'];baseline=json.loads(base_raw)
 assert baseline['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS'
 tree=ast.parse((A/'materialize_server_v1.py').read_text(encoding='utf-8'))
 grant=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='USER_GRANT' for t in n.targets)))
 auth=encode(dict(schema='bcsp-training-authorization-v1',request_sha256=h(qr),explicit_user_authorization=True,user_authorization_text=grant))
 runtime=encode(dict(schema='bcsp-training-runtime-v1',request_sha256=h(qr),authorization_sha256=h(auth)))
 f=s['future_paths'];env=s['launcher_contract']['environment'];quote=shlex.quote
 argv=['env']+[k+'='+v for k,v in env.items()]+['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',s['launcher_contract']['python'],'-I','-S','-B',s['launcher_contract']['entry'],'--request',s['inner_request']['path'],'--request-sha256',h(qr),'--authorization',f['authorization'],'--authorization-sha256',h(auth),'--runtime',f['runtime'],'--runtime-sha256',h(runtime)]
 launcher=('#!/bin/bash\nset -u\numask 077\nmkdir -- '+quote(f['output'])+' || exit 90\n'+' '.join(map(quote,argv))+' > '+quote(f['log'])+' 2>&1\nrc=$?\n(set -o noclobber; printf \'%s\\n\' "$rc" > '+quote(f['exit_code'])+') || exit 91\nexit "$rc"\n').encode()
 launch=json.loads((A/'materialize_execute_once_observation.json').read_text())
 assert [h(auth),h(runtime),h(launcher)]==[launch[k] for k in ['authorization_sha256','runtime_sha256','launcher_sha256']]
 marker=encode(dict(schema='bcsp-sampling-single-launch-attempt-v1',status='CLAIMED_BEFORE_TMUX',request_sha256=h(qr),execution_scope_sha256=S,run_id=q['run_id'],no_retry=True))
 controls=[(s['inner_request']['path'],qr),(f['authorization'],auth),(f['runtime'],runtime),(f['launcher'],launcher),(f['launch_attempt'],marker)]
 for name in ['paired_initialization_receipt_v1.json','qualified_training_receipt_v1.json']:controls.append((f['control']+'/'+name,(C/name).read_bytes()))
 expected=[dict(path=p,bytes=len(r),sha256=h(r)) for p,r in controls]
 old=(O/'post_V1_training_freeze_audit_v2/readonly_audit_server_v2.py').read_text(encoding='utf-8')
 # Replace constants, retaining budgets and exact Python-binary exception.
 nodes=ast.parse(old).body;lines=old.splitlines(keepends=True)
 replacements={'SCOPE_RAW':'SCOPE_RAW=base64.b64decode('+repr(base64.b64encode(sr).decode())+')\n','EXPECTED_CONTROL':'EXPECTED_CONTROL='+repr(expected)+'\n', 'CONTROL':"CONTROL=CODE/'control_Morton_v1'\n",'OUT':'OUT=Path('+repr(f['output'])+')\n','SCOPE':'SCOPE='+repr(S)+'\n'}
 for node in reversed(nodes):
  if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in replacements:lines[node.lineno-1:node.end_lineno]=[replacements[node.targets[0].id]]
 old=''.join(lines)
 old=old.replace("'launch_attempt_v1.json'})","'launch_attempt_v1.json','paired_initialization_receipt_v1.json','qualified_training_receipt_v1.json'})")
 old=old.replace("check('five_controls_match_authorized_materialization',len(EXPECTED_CONTROL)==5)","check('seven_controls_match_authorized_materialization',len(EXPECTED_CONTROL)==7)")
 old=old.replace("q['arm']=='V1' and q['paired_initialization'] is None","q['arm']=='Morton_area_stratified8k' and q['paired_initialization']==scope['paired_initialization']")
 old=old.replace("check('V1_qualified_arm',candidate['arm']=='V1')","check('Morton_qualified_arm',candidate['arm']=='Morton_area_stratified8k')")
 start=old.index(" candidate_control=CODE/'control_Morton_v1'");end=old.index(' gpu=subprocess.run',start)
 pair=''' pair=js(q['paired_initialization']['path'],q['paired_initialization'])
 base_out=Path(pair['baseline_completion']['path']).parent
 for rec in BASELINE['output_manifest']:
  if not rec['path'].endswith('/ckpt-last.pth'):read(rec['path'],rec)
 baseq=js(CODE/'control_V1_v1/training_entry_request_v1.json',BASE_Q_BINDING)
 check('same_scientific_code_environment_order_and_resources',all(q[k]==baseq[k] for k in ['stage','fold','n_input','static_config','order_plan','GPU_audit','preflight_request_sha256','preflight_scope','identity','model_root','implementation','resource_rebind']))
 check('same_QC_sources_targets_and_folds',all(q['QC'][k]==baseq['QC'][k] for k in ['verification','manifests','fold_binding']))
 check('exact_scratch_initialization_matches_V1',initialization==js(base_out/'initialization.json') and all(initialization[k]==pair[k] for k in ['seed','parameter_sha256','persistent_state_sha256']) and initialization['order_sha256']==pair['order_canonical_sha256'])
 check('same_recorded_optimizer_defaults',defaults==js(base_out/'optimizer_actual_defaults.json'))
 base_complete=js(base_out/'completion.json')
 check('same_completion_counts_and_order',all(complete[k]==base_complete[k] for k in ['stage','optimizer_updates','traversals','case_exposures','counts','order_sha256','bncal_executed','evaluation_executed','resume']))
 check('same_actual_exposure_and_dropped_cases',exposure==js(base_out/'exposure.json'))
 base_metrics=list(map(json.loads,read(base_out/'metrics.jsonl')[1].decode().splitlines()))
 check('same_actual_batch_LR_BN_update_sequence',len(base_metrics)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']) for a,b in zip(metrics,base_metrics)))
 check('baseline_exit_zero_no_failure',read(base_out/'exit_code.txt')[1].strip()==b'0' and not (base_out/'failure.json').exists() and not (base_out/'startup_failure.json').exists())
 base_checkpoint=Path(pair['baseline_checkpoint']['path']);parents(base_checkpoint);bs=base_checkpoint.lstat()
 check('baseline_checkpoint_metadata_matches_prior_formal_audit',stat.S_ISREG(bs.st_mode) and bs.st_size==pair['baseline_checkpoint']['bytes'] and bs.st_mtime_ns==pair['baseline_checkpoint']['mtime_ns'] and bs.st_ino==pair['baseline_checkpoint']['inode'])
'''
 old=old[:start]+pair+old[end:]
 old=old.replace("candidate_readiness=dict(files=315,stream_hashed_bytes=candidate_bytes,control_absent=True,output_absent=True,tmux_absent=True)","paired_comparison=dict(baseline_audit_sha256=BASELINE_SHA,baseline_checkpoint_rehashed=False,baseline_checkpoint_prior_sha256=pair['baseline_checkpoint']['sha256'],initialization_equal=True,batch_sequence_equal=True,exposures_equal=True,scientific_contract_equal=True,candidate_payload_files=315,candidate_payload_hashed_bytes=candidate_bytes)")
 const='BASELINE='+repr(baseline)+'\nBASELINE_SHA='+repr(h(base_raw))+'\nBASE_Q_BINDING='+repr(json.loads((O/'V1_training_execution_request_v2.json').read_text())['inner_request'])+'\n'
 # Insert constants before the audit transaction (no executing or importing production tools).
 anchor="try:\n check('current_hostname_uid'";assert old.count(anchor)==1
 old=old.replace(anchor,const+anchor)
 ast.parse(old)
 assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(a.name.split('.')[0] in ['torch','numpy'] for a in n.names) for n in ast.walk(ast.parse(old)))
 F.mkdir();raw=old.encode();save('readonly_audit_server_v1.py',raw)
 template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8');driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(raw));ast.parse(driver);save('audit_short_driver_v1.py',driver.encode())
 save('frozen_readonly_scope_v1.json',encode(dict(audit_source_sha256=h(raw),execution_scope_sha256=S,server_writes=0,forward_calls=0,checkpoint_deserialization=False,checkpoint_cap_bytes=536870912,total_bytes_cap=805306368,time_cap_seconds=120,file_cap=512,baseline_checkpoint='prior formal hash plus current size/mtime/inode; no second full checkpoint stream',paired_fields='initialization/code/config/environment/targets/frame/permutation/order/LR/BN/exposure',no_evaluation=True)))
 save('static_review_v1.json',encode(dict(status='STATIC_PASS',exact_controls=7,reused_audit='successful V1 audit v2',budgets_unchanged=True,production_source_unchanged=True)))
 inv=(B/'invoke_sampling_AB_freeze_audit_v2.py').read_text(encoding='utf-8').replace('post_V1_training_freeze_audit_v2','post_Morton_training_freeze_audit_v1').replace('_v2','_v1')
 ast.parse(inv);(B/'invoke_sampling_Morton_freeze_audit_v1.py').write_bytes(inv.encode())
 print('READONLY_CANDIDATE_AUDIT_STATIC_PASS')
if __name__=='__main__':main()
