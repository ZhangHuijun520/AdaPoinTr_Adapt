"""Reuse the successful Euclidean auditor; add exact paired-run evidence checks."""
import ast,base64,hashlib,json,shlex
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';C=O/'graph_request_v2';A=C/'authorized_execution_v1';F=C/'post_training_audit_v1'
S='1072fad5cbbb970fe37cf6300445d705b8dc99a38aba3fc20cb70cac6cf227d5'
def h(b):return hashlib.sha256(b).hexdigest()
def encode(v):return json.dumps(v,ensure_ascii=True,indent=2).encode()
def save(name,raw):
    with (F/name).open('xb') as f:f.write(raw)
def main():
    sr=(C/'candidate_training_execution_request_v1.json').read_bytes();assert h(sr)==S;s=json.loads(sr)
    qr=(C/'training_entry_request_v1.json').read_bytes();q=json.loads(qr);assert h(qr)==s['inner_request']['sha256']
    basefile=O/'post_Euclidean_training_freeze_audit_v1/audit_report_v1.json';br=basefile.read_bytes();baseline=json.loads(br)
    assert h(br)==s['parent_baseline_audit']['sha256'] and baseline['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and all(baseline['checks'].values())
    tree=ast.parse((A/'materialize_server_v1.py').read_text(encoding='utf-8'))
    grant=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='USER_GRANT' for t in n.targets)))
    auth=encode(dict(schema='bcsp-training-authorization-v1',request_sha256=h(qr),explicit_user_authorization=True,user_authorization_text=grant))
    runtime=encode(dict(schema='bcsp-training-runtime-v1',request_sha256=h(qr),authorization_sha256=h(auth)))
    f=s['future_paths'];env=dict(s['launcher_contract']['environment']);env['TMPDIR']=f['output']+'/tmp';quote=shlex.quote
    argv=['env']+[k+'='+v for k,v in env.items()]+['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',s['launcher_contract']['python'],'-I','-S','-B',s['launcher_contract']['entry'],'--request',s['inner_request']['path'],'--request-sha256',h(qr),'--authorization',f['authorization'],'--authorization-sha256',h(auth),'--runtime',f['runtime'],'--runtime-sha256',h(runtime)]
    launcher=('#!/bin/bash\nset -u\numask 077\nmkdir -- '+quote(f['output'])+' || exit 90\n'+' '.join(map(quote,argv))+' > '+quote(f['log'])+' 2>&1\nrc=$?\n(set -o noclobber; printf \'%s\\n\' "$rc" > '+quote(f['exit_code'])+') || exit 91\nexit "$rc"\n').encode()
    launched=json.loads((A/'materialize_execute_once_observation.json').read_bytes())
    assert [h(auth),h(runtime),h(launcher)]==[launched[k] for k in ('authorization_sha256','runtime_sha256','launcher_sha256')]
    marker=encode(dict(schema='bcsp-sampling-single-launch-attempt-v1',status='CLAIMED_BEFORE_TMUX',request_sha256=h(qr),execution_scope_sha256=S,run_id=q['run_id'],no_retry=True))
    controls=[(s['inner_request']['path'],qr),(f['authorization'],auth),(f['runtime'],runtime),(f['launcher'],launcher),(f['launch_attempt'],marker)]
    for name in ('paired_initialization_receipt_v1.json','qualified_training_receipt_v1.json'):controls.append((f['control']+'/'+name,(C/name).read_bytes()))
    expected=[dict(path=p,bytes=len(raw),sha256=h(raw)) for p,raw in controls]
    parent=O/'post_Euclidean_training_freeze_audit_v1/readonly_audit_server_v1.py'
    source=parent.read_text(encoding='utf-8')
    # Swap active and paired metadata roles, before replacing embedded scope constants.
    source=source.replace("'Euclidean_elimination'","'__BASE_ARM__'").replace("'surface_graph'","'Euclidean_elimination'").replace("'__BASE_ARM__'","'surface_graph'")
    source=source.replace('qualified_Euclidean_arm','qualified_graph_arm')
    source=source.replace("q['paired_initialization'] is None","q['paired_initialization']==scope['paired_initialization']")
    source=source.replace("'launch_attempt_v1.json'})","'launch_attempt_v1.json','paired_initialization_receipt_v1.json','qualified_training_receipt_v1.json'})")
    source=source.replace("check('five_controls_match_authorized_materialization',len(EXPECTED_CONTROL)==5)","check('seven_controls_match_authorized_materialization',len(EXPECTED_CONTROL)==7)")
    source=source.replace('paired_graph_metadata_only=True,graph_payloads_read=False','paired_Euclidean_metadata_only=True,graph_payloads_read=True')
    lines=source.splitlines(keepends=True)
    constants={'CONTROL':"CONTROL=CODE/'control_surface_graph_v1'\n",'OUT':'OUT=Path('+repr(f['output'])+')\n','SCOPE':'SCOPE='+repr(S)+'\n','SCOPE_RAW':'SCOPE_RAW=base64.b64decode('+repr(base64.b64encode(sr).decode())+')\n','EXPECTED_CONTROL':'EXPECTED_CONTROL='+repr(expected)+'\n','EXPECTED_INITIALIZATION':'EXPECTED_INITIALIZATION='+repr(baseline['initialization'])+'\n'}
    for n in reversed(ast.parse(source).body):
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants:lines[n.lineno-1:n.end_lineno]=[constants[n.targets[0].id]]
    source=''.join(lines)
    anchor=' gpu=subprocess.run';assert source.count(anchor)==1
    paircheck=''' pair=js(q['paired_initialization']['path'],q['paired_initialization'])
 check('paired_receipt_bound_to_formal_Euclidean_audit',pair['baseline_freeze_audit_sha256']==BASELINE_AUDIT_SHA and pair['baseline_checkpoint']==BASELINE_CHECKPOINT and pair['verified_updates']==3900)
 base_out=Path(pair['baseline_completion']['path']).parent
 for record in BASELINE_OUTPUT:
  if not record['path'].endswith('/ckpt-last.pth'):read(record['path'],record)
 baseq=js(BASE_REQUEST['path'],BASE_REQUEST)
 check('same_scientific_code_environment_order_resources',all(q[k]==baseq[k] for k in ['stage','fold','n_input','static_config','order_plan','GPU_audit','preflight_request_sha256','preflight_scope','identity','model_root','implementation','resource_rebind']))
 check('same_QC_sources_targets_and_folds',all(q['QC'][k]==baseq['QC'][k] for k in ['verification','manifests','fold_binding']))
 check('exact_initialization_matches_Euclidean',initialization==js(base_out/'initialization.json') and all(initialization[k]==pair[k] for k in ['seed','parameter_sha256','persistent_state_sha256']) and initialization['order_sha256']==pair['order_canonical_sha256'])
 check('same_recorded_optimizer_defaults',defaults==js(base_out/'optimizer_actual_defaults.json'))
 bc=js(base_out/'completion.json')
 check('same_completion_counts_and_order',all(complete[k]==bc[k] for k in ['stage','optimizer_updates','traversals','case_exposures','counts','order_sha256','bncal_executed','evaluation_executed','resume']))
 check('same_actual_exposure_and_dropped_cases',exposure==js(base_out/'exposure.json'))
 bm=list(map(json.loads,read(base_out/'metrics.jsonl')[1].decode().splitlines()))
 check('same_all3900_actual_batch_LR_BN_update_sequence',len(bm)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']) for a,b in zip(metrics,bm)))
 check('Euclidean_exit_zero_no_failure',read(base_out/'exit_code.txt')[1].strip()==b'0' and not (base_out/'failure.json').exists() and not (base_out/'startup_failure.json').exists())
 bp=Path(pair['baseline_checkpoint']['path']);parents(bp);bs=bp.lstat()
 check('Euclidean_checkpoint_metadata_matches_formal_hash_evidence',stat.S_ISREG(bs.st_mode) and bs.st_size==BASELINE_CHECKPOINT['bytes'] and bs.st_ino==BASELINE_CHECKPOINT['inode'] and bs.st_mtime_ns==BASELINE_CHECKPOINT['mtime_ns'])
 READ_STAMPS[str(bp)]=stamp(bs)
'''
    source=source.replace(anchor,paircheck+anchor)
    source=source.replace('current_GPU_metadata=observed,','current_GPU_metadata=observed,paired_comparison=dict(baseline_audit_sha256=BASELINE_AUDIT_SHA,baseline_checkpoint_rehashed=False,baseline_checkpoint_prior_sha256=BASELINE_CHECKPOINT[\'sha256\'],baseline_checkpoint_metadata_stable=True,initialization_equal=True,all3900_batch_sequence_equal=True,exposures_equal=True,scientific_contract_equal=True),')
    base_request=json.loads((O/'Euclidean_training_execution_request_v1.json').read_bytes())['inner_request']
    constants='BASELINE_AUDIT_SHA='+repr(h(br))+'\nBASELINE_CHECKPOINT='+repr(baseline['checkpoint'])+'\nBASELINE_OUTPUT='+repr(baseline['output_manifest'])+'\nBASE_REQUEST='+repr(base_request)+'\n'
    source=source.replace("try:\n check('current_hostname_uid'",constants+"try:\n check('current_hostname_uid'")
    parsed=ast.parse(source)
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(a.name.split('.')[0] in ('torch','numpy') for a in n.names) for n in ast.walk(parsed))
    assert "q['arm']=='surface_graph'" in source and "manifest={x['case_id']:x for x in map(json.loads,read(q['QC']['manifests']['surface_graph']['path'])" in source
    F.mkdir();raw=source.encode();save('readonly_audit_server_v1.py',raw)
    template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8')
    driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(raw));ast.parse(driver);save('audit_short_driver_v1.py',driver.encode())
    save('frozen_readonly_scope_v1.json',encode(dict(audit_source_sha256=h(raw),execution_scope_sha256=S,baseline_formal_audit_sha256=h(br),server_writes=0,forward_calls=0,checkpoint_deserialization=False,checkpoint_cap_bytes=536870912,total_bytes_cap=805306368,time_cap_seconds=120,file_cap=512,active_graph_NPZ_stream_hashes=315,baseline_checkpoint='previous formal stream hash plus current size/inode/mtime stability; no second full baseline stream',paired_fields='same code/config/environment, initialization, all3900 batches, LR/BN, exposures/drops, target/frame/order metadata')))
    save('static_review_v1.json',encode(dict(status='STATIC_PASS',exact_controls=7,parent_auditor_sha256=h(parent.read_bytes()),launcher_reconstruction_verified=True,no_budget_increase=True)))
    inv=(B/'invoke_blue_noise_post_training_audit_v1.py').read_text(encoding='utf-8').replace('first_training_request_v2/post_Euclidean_training_freeze_audit_v1','first_training_request_v2/graph_request_v2/post_training_audit_v1')
    ast.parse(inv)
    with (B/'invoke_blue_noise_graph_freeze_audit_v1.py').open('x',encoding='utf-8') as out:out.write(inv)
    print('GRAPH_AND_PAIRED_READONLY_AUDIT_STATIC_PASS_NO_SERVER_CALLS')
if __name__=='__main__':main()
