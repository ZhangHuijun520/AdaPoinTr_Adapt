"""Derive the existing stdlib post-training auditor for this exact sampling run."""
import ast,base64,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';A=O/'authorized_execution_v2';F=O/'post_V1_training_freeze_audit_v1'
def h(raw):return hashlib.sha256(raw).hexdigest()
def encode(v):return json.dumps(v,ensure_ascii=True,indent=2).encode()
def main():
 F.mkdir(exist_ok=False)
 raw=(O/'V1_training_execution_request_v2.json').read_bytes();S=h(raw);assert S=='4a889afad90b1a8a52fcb75691c71990d03af8b7d120a96608ac4b9b85cb7a62'
 scope=json.loads(raw);qr=(O/'V1_training_entry_request_v1.json').read_bytes();q=json.loads(qr)
 tree=ast.parse((A/'materialize_server_v1.py').read_text(encoding='utf-8'))
 grant=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='USER_GRANT' for t in n.targets)))
 auth=encode({'schema':'bcsp-training-authorization-v1','request_sha256':h(qr),'explicit_user_authorization':True,'user_authorization_text':grant})
 runtime=encode({'schema':'bcsp-training-runtime-v1','request_sha256':h(qr),'authorization_sha256':h(auth)})
 marker=encode({'schema':'bcsp-sampling-single-launch-attempt-v1','status':'CLAIMED_BEFORE_TMUX','request_sha256':h(qr),'execution_scope_sha256':S,'run_id':q['run_id'],'no_retry':True})
 controls=[(scope['inner_request']['path'],qr),(scope['future_paths']['authorization'],auth),(scope['future_paths']['runtime'],runtime),(scope['future_paths']['launcher'],(A/'launcher_expected_v1.sh').read_bytes()),(scope['future_paths']['launch_attempt'],marker)]
 expected=[dict(path=p,bytes=len(r),sha256=h(r)) for p,r in controls]
 old=(B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1/post_training_audit_v1.py').read_text(encoding='utf-8')
 old=old.replace("CODE=ROOT/'third_party/bcsp_geov1_training_foldc_8192_seed0_v1'","CODE=ROOT/'third_party/bcsp_sampling_ab_foldc_seed0_v1'")
 old=old.replace("CONTROL=CODE/'control_train_v3'","CONTROL=CODE/'control_V1_v1'")
 old=old.replace("OUT=ROOT/'logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3'","OUT=Path("+repr(scope['future_paths']['output'])+")")
 old=old.replace("SCOPE='16655f4494fe2458619129958a370d240866a15b339ec2d40b595d827b675f0a'","SCOPE="+repr(S))
 old=old.replace('402653184 if checkpoint','536870912 if checkpoint').replace('536870912','805306368')
 # The preceding replacement also raises the checkpoint cap to768MiB; set the
 # dedicated checkpoint limit explicitly while retaining the total768MiB cap.
 old=old.replace('limit=805306368 if checkpoint','limit=536870912 if checkpoint')
 old=old.replace('time.monotonic()-START<90','time.monotonic()-START<120')
 old=old.replace("shu-common-25721452-notebook-01dt08-0","shu-common-25721452-notebook-v2iwsa-0")
 start=old.index(" scope=js(CONTROL/'training_execution_scope_v3.json')")
 end=old.index(" q=js(CONTROL/'training_execution_request_v1.json')",start)
 old=old[:start]+''' scope=json.loads(SCOPE_RAW)
 check('full_authorized_execution_scope_hash',hashlib.sha256(SCOPE_RAW).hexdigest()==SCOPE)
 check('exact_control_file_set',{p.name for p in CONTROL.iterdir()}=={'training_entry_request_v1.json','authorization_v1.json','runtime_v1.json','launch_once_v1.sh','launch_attempt_v1.json'})
 for r in EXPECTED_CONTROL:read(r['path'],r)
 check('five_controls_match_authorized_materialization',len(EXPECTED_CONTROL)==5)
'''+old[end:]
 old=old.replace("CONTROL/'training_execution_request_v1.json'","CONTROL/'training_entry_request_v1.json'")
 old=old.replace("scope['entry_request']['sha256']","scope['inner_request']['sha256']")
 old=old.replace("CONTROL/'training_authorization_v1.json'","CONTROL/'authorization_v1.json'").replace("CONTROL/'training_runtime_v1.json'","CONTROL/'runtime_v1.json'")
 old=old.replace("scope['future_paths']['tmux_session']","scope['future_paths']['tmux']")
 old=old.replace("q['QC']['manifests']['8192']","q['QC']['manifests']['V1']")
 old=old.replace("pins=[q['static_config'],q['order_plan'],q['QC']['fold_binding'],q['QC']['manifests']['V1'],q['resource_rebind'],*q['implementation'].values()]",
   "pins=[q['static_config'],q['order_plan'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),q['QC']['verification'],q['QC']['qualified_receipt'],q['resource_rebind'],q['preflight_scope'],q['GPU_audit'],*q['implementation'].values()]")
 old=old.replace("check('completion_exact_counts'", "check('correct_sampling_stage',q['stage']==complete['stage']=='BCSP_SAMPLING_AB_V1' and q['arm']=='V1' and q['paired_initialization'] is None)\n check('completion_exact_counts'",1)
 old=old.replace("check('fixed315_train_allowlist'", "check('fixed315_train_allowlist'",1)
 # Append initialization, actual optimizer metadata and candidate readiness to
 # the same read-only transaction before its final tree stability check.
 anchor=" check('result_tree_stable_atime_excluded',tree()==before)"
 addition=''' initialization=js(OUT/'initialization.json')
 check('recorded_initialization_seed_and_fingerprints',initialization['seed']==0 and all(isinstance(initialization[k],str) and len(initialization[k])==64 and all(c in '0123456789abcdef' for c in initialization[k]) for k in ['parameter_sha256','persistent_state_sha256']))
 defaults=js(OUT/'optimizer_actual_defaults.json')
 check('recorded_optimizer_defaults',defaults['lr']==.0001 and defaults['betas']==[.9,.999] and defaults['eps']==1e-8 and defaults['amsgrad'] is False)
 rebind=js(q['resource_rebind']['path'])
 for key in ['readonly_identity','readonly_assets']:read(rebind[key]['path'],rebind[key])
 assets=js(rebind['readonly_assets']['path'])
 check('exact30_source_provider_asset_record',assets['status']=='SELECTED30_HASH_PASS' and len(assets['assets'])==30)
 for r in assets['assets']:read(r['path'],r)
 candidate=js(q['QC']['qualified_receipt']['path']);check('V1_qualified_arm',candidate['arm']=='V1')
 other={r['case_id']:r for r in map(json.loads,read(q['QC']['manifests']['Morton_area_stratified8k']['path'])[1].decode().splitlines())}
 check('candidate315_metadata_ready',len(other)==315 and set(other)==set(fold['train_case_ids']))
 candidate_bytes=0
 candidate_root=Path(str(q['data_root']).rsplit('/',1)[0])/'Morton_area_stratified8k'
 for cid,a in manifest.items():
  b=other[cid]
  need(all(a[k]==b[k] for k in ['case_id','source_id','target_array_sha256','normalization','common_point_order_sha256']),'candidate target/frame/order pairing')
  need(b['source_id'] in fold['train_sources'] and b['sampler_arm']=='Morton_area_stratified8k' and b['n_input']==b['n_target']==8192,'candidate training scope')
  rel=Path(b['point_path']);need(not rel.is_absolute() and '..' not in rel.parts,'candidate relative path')
  row,_=read(candidate_root/rel);need(row['sha256']==b['sha256'],'candidate file hash');candidate_bytes+=row['bytes']
 check('candidate315_stream_hashes_match_frozen_manifest',True)
 candidate_control=CODE/'control_Morton_v1'
 candidate_output=OUT.parent/'bcsp_sampling_ab_foldC_Morton_in8192_out8192_seed0_train_v1'
 check('new_candidate_control_and_output_absent',not candidate_control.exists() and not candidate_control.is_symlink() and not candidate_output.exists() and not candidate_output.is_symlink())
 candidate_tmux=subprocess.run(['tmux','has-session','-t','bcsp_sampling_ab_foldc_morton_seed0_train_v1'],capture_output=True,timeout=5)
 check('new_candidate_tmux_absent',candidate_tmux.returncode==1)
 gpu=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,timeout=10)
 need(gpu.returncode==0,'current GPU metadata query')
 observed=[s.strip() for s in gpu.stdout.decode().strip().split(',')]
 check('same_gpu_identity_for_future_paired_request',observed[:4]==[q['identity']['gpu_uuid'],q['identity']['gpu_name'],q['identity']['driver_version'],str(q['identity']['nvidia_smi_memory_total_MiB'])])
 check('all_hashed_files_stable_atime_excluded',all(stamp(Path(p).lstat())==record for p,record in READ_STAMPS.items()))
'''
 assert anchor in old;old=old.replace(anchor,addition+anchor)
 old=old.replace("rows.append(row);value=", "need(len(rows)<512,'bounded exact file count');READ_STAMPS[str(p)]=stamp(st);rows.append(row);value=")
 old=old.replace("START=time.monotonic();TOTAL=0;cache={};checks={};rows=[]","START=time.monotonic();TOTAL=0;cache={};checks={};rows=[];READ_STAMPS={}")
 old=old.replace("all_bound_files=rows,", "all_bound_files=[r for r in rows if not r['path'].endswith('.npz')],initialization=initialization,optimizer_defaults=defaults,candidate_readiness=dict(files=315,stream_hashed_bytes=candidate_bytes,control_absent=True,output_absent=True,tmux_absent=True),current_GPU_metadata=observed,")
 # Keep exception handling independent of variables initialized late in the audit.
 old=old.replace("checks=checks,all_bound_files=[r for r in rows if not r['path'].endswith('.npz')],initialization=initialization,optimizer_defaults=defaults,candidate_readiness=dict(files=315,stream_hashed_bytes=candidate_bytes,control_absent=True,output_absent=True,tmux_absent=True),current_GPU_metadata=observed,server_writes=0", "checks=checks,all_bound_files=[r for r in rows if not r['path'].endswith('.npz')],server_writes=0")
 old=old.replace('checkpoint_loaded=False,model_imported=False','checkpoint_loaded=False,checkpoint_stream_hashed=True,initialization_weights_reconstructed=False,NPZ_decoded=False,model_imported=False')
 # Insert immutable caller constants after imports, before the main transaction.
 pos=old.index('START=time.monotonic()')
 constants='import base64\nSCOPE_RAW=base64.b64decode('+repr(base64.b64encode(raw).decode())+')\nEXPECTED_CONTROL='+repr(expected)+'\n'
 old=old[:pos]+constants+old[pos:]
 ast.parse(old)
 with (F/'readonly_audit_server_v1.py').open('xb') as f:f.write(old.encode())
 template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8')
 driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(old.encode())).replace('120s ','150s ').replace("'135'","'165'")
 ast.parse(driver)
 with (F/'audit_short_driver_v1.py').open('xb') as f:f.write(driver.encode())
 with (F/'frozen_readonly_scope_v1.json').open('x',encoding='utf-8') as f:json.dump({'status':'FROZEN_BEFORE_SERVER_READ','authorized_parent_sha256':S,'audit_source_sha256':h(old.encode()),'checkpoint_max_bytes':536870912,'total_hashed_bytes_max':805306368,'per_text_max_bytes':16777216,'max_exact_files':512,'max_output_tree_entries':32,'monitored_seconds':120,'external_timeout_seconds':150,'candidate_NPZ_stream_hashes':315,'no_NPZ_or_checkpoint_deserialization':True,'GPU_or_model_calls':0,'server_writes':0,'retry':False},f,indent=2)
 print('READONLY_AUDIT_STATIC_PASS',len(old.encode()))
if __name__=='__main__':main()
