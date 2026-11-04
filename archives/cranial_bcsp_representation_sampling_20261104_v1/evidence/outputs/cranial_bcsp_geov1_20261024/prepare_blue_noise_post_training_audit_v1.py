"""Bind the previously successful bounded stdlib audit to this exact finished run."""
import ast,base64,hashlib,json,shlex
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';A=O/'authorized_execution_v1';F=O/'post_Euclidean_training_freeze_audit_v1'
S='40a45089ed847261d9477993118b406048dadd09d15e492a402b455bddfdad74'
def h(b):return hashlib.sha256(b).hexdigest()
def enc(v):return json.dumps(v,ensure_ascii=True,indent=2).encode()
def save(n,b):
    with (F/n).open('xb') as f:f.write(b)
def main():
    sr=(O/'Euclidean_training_execution_request_v1.json').read_bytes();assert h(sr)==S;s=json.loads(sr)
    qr=(O/'Euclidean_training_entry_request_v1.json').read_bytes();q=json.loads(qr);assert h(qr)==s['inner_request']['sha256']
    tree=ast.parse((A/'materialize_server_v1.py').read_text(encoding='utf-8'))
    grant=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='USER_GRANT' for t in n.targets)))
    auth=enc(dict(schema='bcsp-training-authorization-v1',request_sha256=h(qr),explicit_user_authorization=True,user_authorization_text=grant))
    runtime=enc(dict(schema='bcsp-training-runtime-v1',request_sha256=h(qr),authorization_sha256=h(auth)))
    f=s['future_paths'];env=dict(s['launcher_contract']['environment']);env['TMPDIR']=f['output']+'/tmp';quote=shlex.quote
    argv=['env']+[k+'='+v for k,v in env.items()]+['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',s['launcher_contract']['python'],'-I','-S','-B',s['launcher_contract']['entry'],'--request',s['inner_request']['path'],'--request-sha256',h(qr),'--authorization',f['authorization'],'--authorization-sha256',h(auth),'--runtime',f['runtime'],'--runtime-sha256',h(runtime)]
    launcher=('#!/bin/bash\nset -u\numask 077\nmkdir -- '+quote(f['output'])+' || exit 90\n'+' '.join(map(quote,argv))+' > '+quote(f['log'])+' 2>&1\nrc=$?\n(set -o noclobber; printf \'%s\\n\' "$rc" > '+quote(f['exit_code'])+') || exit 91\nexit "$rc"\n').encode()
    launch=json.loads((A/'materialize_execute_once_observation.json').read_bytes())
    assert [h(auth),h(runtime),h(launcher)]==[launch[k] for k in ('authorization_sha256','runtime_sha256','launcher_sha256')]
    marker=enc(dict(schema='bcsp-sampling-single-launch-attempt-v1',status='CLAIMED_BEFORE_TMUX',request_sha256=h(qr),execution_scope_sha256=S,run_id=q['run_id'],no_retry=True))
    controls=[(s['inner_request']['path'],qr),(f['authorization'],auth),(f['runtime'],runtime),(f['launcher'],launcher),(f['launch_attempt'],marker)]
    expected=[dict(path=p,bytes=len(r),sha256=h(r)) for p,r in controls]
    parent=B/'sampling_model_AB_foldC_seed0_20261103_v1/post_V1_training_freeze_audit_v2/readonly_audit_server_v2.py'
    source=parent.read_text(encoding='utf-8');lines=source.splitlines(keepends=True)
    constants={'CODE':"CODE=ROOT/'third_party/bcsp_blue_noise_ab_foldc_seed0_v1'\n",'CONTROL':"CONTROL=CODE/'control_Euclidean_v1'\n",'OUT':'OUT=Path('+repr(f['output'])+')\n','SCOPE':'SCOPE='+repr(S)+'\n','SCOPE_RAW':'SCOPE_RAW=base64.b64decode('+repr(base64.b64encode(sr).decode())+')\n','EXPECTED_CONTROL':'EXPECTED_CONTROL='+repr(expected)+'\n'}
    for n in reversed(ast.parse(source).body):
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants:lines[n.lineno-1:n.end_lineno]=[constants[n.targets[0].id]]
    source=''.join(lines).replace('BCSP_SAMPLING_AB_V1','BCSP_BLUE_NOISE_AB_V1').replace("q['arm']=='V1'","q['arm']=='Euclidean_elimination'").replace("q['QC']['manifests']['V1']","q['QC']['manifests']['Euclidean_elimination']")
    start=source.index(" candidate=js(q['QC']['qualified_receipt']['path'])")
    end=source.index(" gpu=subprocess.run",start)
    source=source[:start]+''' qualified=js(q['QC']['qualified_receipt']['path'])
 check('qualified_Euclidean_arm',qualified['schema']=='bcsp-blue-noise-qualified-v1' and qualified['stage']=='BCSP_BLUE_NOISE_AB_V1' and qualified['arm']=='Euclidean_elimination')
 check('fresh_scratch_no_parent_weights',q['paired_initialization'] is None and static['training']['seed']==0 and static['training']['checkpoint']=='scratch_final_only')
 check('recorded_initialization_matches_same_model_seed0_reference',initialization==EXPECTED_INITIALIZATION)
 payload_bytes=0
 for cid,row in manifest.items():
  need(row['comparison_stage']=='BCSP_BLUE_NOISE_AB_V1' and row['comparison_split']=='train' and row['sampler_arm']=='Euclidean_elimination' and row['sampling_seed']==0,'active sampler scope')
  rel=Path(row['point_path']);need(not rel.is_absolute() and '..' not in rel.parts,'relative payload path')
  rec,_=read(Path(q['data_root'])/rel);need(rec['sha256']==row['sha256'],'active NPZ hash');payload_bytes+=rec['bytes']
 check('active315_stream_hashes_match_frozen_manifest',len(manifest)==315)
 other={x['case_id']:x for x in map(json.loads,read(q['QC']['manifests']['surface_graph']['path'])[1].decode().splitlines())}
 need(len(other)==315 and set(other)==set(manifest),'paired metadata IDs')
 for cid,a in manifest.items():
  b=other[cid];need(all(a[k]==b[k] for k in ['case_id','source_id','target_array_sha256','normalization','common_point_order_sha256']),'paired metadata target/frame/order')
 check('paired_metadata_targets_frame_point_order_equal',True)
 check('scientific_static_counts',static['stage']=='BCSP_BLUE_NOISE_AB_V1' and static['counts']==dict(cases=315,sources=63,batch=8,epochs=100,batches_per_epoch=39,updates=3900,exposures=31200))
''' + source[end:]
    source=source.replace("candidate_readiness=dict(files=315,stream_hashed_bytes=candidate_bytes,control_absent=True,output_absent=True,tmux_absent=True)","active_training_data=dict(files=315,stream_hashed_bytes=payload_bytes,NPZ_decoded=False),paired_graph_metadata_only=True,graph_payloads_read=False")
    ref=B/'sampling_model_AB_foldC_seed0_20261103_v1/post_V1_training_freeze_audit_v2/audit_report_v2.json';reference=json.loads(ref.read_bytes());assert reference['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS'
    anchor="try:\n check('current_hostname_uid'";assert source.count(anchor)==1
    source=source.replace(anchor,'EXPECTED_INITIALIZATION='+repr(reference['initialization'])+'\n'+anchor)
    tree=ast.parse(source)
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(a.name.split('.')[0] in ('numpy','torch') for a in n.names) for n in ast.walk(tree))
    assert 'candidate_bytes' not in source and 'Morton_area_stratified8k' not in source
    F.mkdir();raw=source.encode();save('readonly_audit_server_v1.py',raw)
    template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8')
    driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(raw));ast.parse(driver);save('audit_short_driver_v1.py',driver.encode())
    save('frozen_readonly_scope_v1.json',enc(dict(audit_source_sha256=h(raw),authorized_training_scope_sha256=S,user_scope='formal read-only post-training freeze audit; no new experiment',checkpoint_cap_bytes=536870912,total_bytes_cap=805306368,time_cap_seconds=120,file_cap=512,Python_binary_exact_size=17331920,Python_binary_exact_SHA256='01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d',active_NPZ_stream_hashes=315,graph_NPZ_reads=0,checkpoint_deserialization=False,initial_weights_reconstructed=False,reference_initialization_audit_SHA256=h(ref.read_bytes()),server_writes=0,forward_calls=0)))
    save('static_review_v1.json',enc(dict(status='STATIC_PASS',frozen_controls=5,launcher_materialization_reconstructed=True,established_auditor_parent_SHA256=h(parent.read_bytes()),no_model_imports=True,no_guard_budget_increase=True)))
    inv=(B/'invoke_sampling_AB_freeze_audit_v2.py').read_text(encoding='utf-8').replace('sampling_model_AB_foldC_seed0_20261103_v1/post_V1_training_freeze_audit_v2','blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/post_Euclidean_training_freeze_audit_v1').replace('_v2','_v1')
    ast.parse(inv)
    with (B/'invoke_blue_noise_post_training_audit_v1.py').open('x',encoding='utf-8') as stream:stream.write(inv)
    print('FORMAL_READONLY_AUDIT_STATIC_PASS_NO_SERVER_CALLS')
if __name__=='__main__':main()
