"""Local evidence cross-check only: no prediction, scoring, fitting, or model loading."""
import ast,collections,hashlib,importlib.util,json,math
from pathlib import Path,PurePosixPath
F=Path(__file__).resolve().parent;B=F.parent;D=F/'downloads';O=D/'output';I=D/'installed'
QH='cab2831f27913766d7009101ec86d9a6e642a40b9330359dbfc8ff5928610fb6'
checks={}
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]
def check(name,ok):
 if not ok:raise AssertionError(name)
 checks[name]=True
def emit(name,v):
 with (F/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def finite(v):
 if isinstance(v,float):return math.isfinite(v)
 if isinstance(v,dict):return all(finite(x) for x in v.values())
 if isinstance(v,list):return all(finite(x) for x in v)
 return True
def issha(v):return isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def rng_valid(r):
 assert set(r)=={'CPU','CUDA','Python','numpy'} and issha(r['CPU']) and issha(r['CUDA'])
 p=ast.literal_eval(r['Python']);assert len(p)==3 and p[0]==3 and len(p[1])==625 and 0<=p[1][-1]<=624
 assert all(isinstance(x,int) and 0<=x<=2**32 for x in p[1][:-1]) and (p[2] is None or math.isfinite(p[2]))
 prefix=repr('MT19937');s=r['numpy'];assert s.startswith(prefix)
 state=s[len(prefix):len(prefix)+4992];assert len(bytes.fromhex(state))==2496
 tail=ast.literal_eval(s[len(prefix)+4992:]);assert len(tail)==3 and 0<=tail[0]<=624 and tail[1] in (0,1) and math.isfinite(tail[2])
 return True
try:
 qp=I/'LQI_CD_native_prediction_execution_request_v1.json';q=read(qp);scope=read(F/'audit_scope_v1.json');index=read(I/'LQI_CD_Native_input_index_candidate_v1.json')
 check('authorized_request_exact_hash_and_pending_template_status',sha(qp)==QH and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION')
 finished=read(F/'finished_result_v1.json')
 check('current_container_uid_exit0_worker_tmux_absent',finished['status']=='EXIT0_WORKER_TMUX_ABSENT' and finished['hostname']==q['identity']['hostname'] and finished['uid']==1000 and (O/'exit_code.txt').read_text().strip()=='0')
 before=read(F/'inventory_before_result_v1.json');after=read(F/'inventory_after_result_v1.json')
 check('all_content_fingerprints_stable_excluding_atime',before==after)
 check('exact224_output_files_and5_directories',set(before['output']['files'])==set(scope['expected_output_files']) and len(before['output']['files'])==224 and set(before['output']['directories'])=={'.','predictions','context','traces','tmp'})
 control_names={'native_prediction_authorization_v1.json','native_prediction_runtime_v1.json','native_prediction_launch_once_v1.sh','native_prediction_single_attempt_claim_v1.json','readiness_and_installation_receipt_v2.json','startup_receipt_v2.json'}
 mapping=read(B/'pending_request_final_v1/installation_mapping_v1.json');install_names={PurePosixPath(r['target']).name for r in mapping['files']}
 check('exact14_install6_controls_and2_directories',len(install_names)==14 and set(before['install']['files'])==install_names|{'control/'+n for n in control_names} and set(before['install']['directories'])=={'.','control'})
 hb=read(F/'hashes_before_result_v1.json');ha=read(F/'hashes_after_result_v1.json')
 hashes={r['name']:r for r in hb['files']}
 check('two_fresh_full_output_hash_passes_equal',hb['files']==ha['files'] and len(hashes)==224)
 check('all_output_sizes_match_inventory',all(r['bytes']==before['output']['files'][n][3] for n,r in hashes.items()))
 check('all14_install_targets_match_frozen_mapping',all((I/PurePosixPath(r['target']).name).stat().st_size==r['bytes'] and sha(I/PurePosixPath(r['target']).name)==r['sha256'] for r in mapping['files']))
 metadata=read(F/'metadata_result_v1.json')
 check('all33_metadata_copies_match_fresh_remote_hashes',len(metadata['files'])==33 and all((D/n).stat().st_size==r['bytes'] and sha(D/n)==r['sha256'] for n,r in metadata['files'].items()))
 check('output_metadata_agrees_with_independent_hash_pass',all(r['sha256']==hashes[n.removeprefix('output/')]['sha256'] for n,r in metadata['files'].items() if n.startswith('output/')))
 C=I/'control';auth=read(C/'native_prediction_authorization_v1.json');runtime=read(C/'native_prediction_runtime_v1.json');claim=read(C/'native_prediction_single_attempt_claim_v1.json');startup=read(C/'startup_receipt_v2.json')
 check('explicit_authorization_exact_schema_request_hash',set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-development-authorization-v1' and auth['request_sha256']==QH and auth['explicit_user_authorization'] is True and QH in auth['user_authorization_text'])
 check('runtime_one_way_authorization_hash_binding',runtime==dict(schema='bcsp-development-runtime-v1',request_sha256=QH,authorization_sha256=sha(C/'native_prediction_authorization_v1.json')))
 check('single_attempt_claim_no_retry',claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
 entry=I/'bcsp_lqi_twofold_native_predict_v1.py';spec=importlib.util.spec_from_file_location('audit_inert_entry',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
 check('launcher_exact_rendered_bytes', (C/'native_prediction_launch_once_v1.sh').read_text(encoding='utf-8')==e.render_launcher(q,QH,sha(C/'native_prediction_authorization_v1.json'),sha(C/'native_prediction_runtime_v1.json')))
 check('startup_receipt_hash_chain_and_session',startup['request_sha256']==QH and startup['session']==q['launch_contract']['tmux_session'] and startup['tmux_returncode']==0 and startup['authorization_sha256']==sha(C/'native_prediction_authorization_v1.json') and startup['runtime_sha256']==sha(C/'native_prediction_runtime_v1.json') and startup['launcher_sha256']==sha(C/'native_prediction_launch_once_v1.sh'))
 receipt=read(C/'readiness_and_installation_receipt_v2.json')
 check('bound_exclusive_installation_receipt',receipt['status']=='FOURTEEN_EXCLUSIVE_INSTALL_HASHES_PASS' and receipt['request_sha256']==QH and receipt['overwritten_files']==0 and receipt['development_input_files_hashed']==210 and receipt['checkpoint_files_hashed']==2)
 check('no_failure_or_unexpected_execution_artifact','failure.json' not in hashes and not any('failure' in n for n in before['install']['files']))
 check('scope_index_entry_P3_bindings',all(sha(I/PurePosixPath(q[k]['path']).name)==q[k]['sha256'] for k in ['entry','input_index','protocol','P3']))
 p3=read(I/'implementation_P3_v1.json');check('prior_CPU46_and_P3_preserved',p3['status']=='LOCAL_LQI_NATIVE_PREDICTION_P3_PASS' and p3['entry_sha256']==sha(entry) and p3['CPU_checks']==46 and all(p3['checks'].values()))
 check('fixed_F0_case_scope_no_reselection',q['scope_origin']=='EXACT_FROZEN_F0_DEVELOPMENT_CASES_NO_RESELECTION')
 done=read(O/'inference_complete.json');completion=read(O/'completion.json')
 check('exact210_native_complete_no_training_BNCal_loss_backward',done['status']=='LQI_CD_210_NATIVE_FORWARD_COMPLETE' and done['forwards']==completion['forwards']==210 and done['context_cases']==0 and done['trace_cases']==0 and all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']) and done['request_sha256']==completion['request_sha256']==QH)
 manifest=rows(O/'inference_manifest.jsonl');journal=rows(O/'forward_attempts.jsonl');geometry=rows(O/'geometry_summary.jsonl');caches=rows(O/'cache_manifest.jsonl')
 check('exact210_manifest_claim_geometry_and0_cache_records',len(manifest)==len(journal)==len(geometry)==210 and len(caches)==0 and all(finite(x) for x in manifest+geometry+caches))
 runs={run['label']:run for run in index['runs']};expectedpred=set();cache_expected={}
 for i,(row,m,j,g) in enumerate(zip(index['inputs'],manifest,journal,geometry),1):
  run=runs[row['run']]
  assert m['forward_index']==j['forward_index']==i and j['status']=='CLAIMED_BEFORE_FORWARD'
  assert all(x['run']==row['run'] and x['case_id']==row['case_id'] for x in (m,j,g))
  assert all(m[k]==row[k] for k in ['variant','source_id','fold','n_input','normalization']) and m['n_output']==8192 and m['input_sha256']==row['input']['sha256'] and m['checkpoint_sha256']==run['checkpoint']['sha256'] and m['operational_seconds']>=0
  r=m['prediction'];assert r['name']==row['prediction_filename'] and r['bytes']==hashes[r['name']]['bytes'] and r['sha256']==hashes[r['name']]['sha256'];expectedpred.add(r['name'])
  assert g['frame']=='native_D_only_normalized_no_GT' and g['coarse']['finite_count']==256 and g['dense']['finite_count']==8192
  for flag,folder in [('cache_context','context'),('save_full_decoder_trace','traces')]:
   if row[flag]:cache_expected[folder+'/'+row['run']+'__'+row['case_id']+'.npz']=(row,i,run)
 check('all210_case_order_input_checkpoint_normalization_bindings',len(expectedpred)==210)
 check('exact_unique_pre_forward_claims_no_extra_calls',len({(r['run'],r['case_id']) for r in journal})==210 and [r['forward_index'] for r in journal]==list(range(1,211)))
 check('per_fold105_original_order_21_sources5_types',collections.Counter(r['run'] for r in manifest)=={'C_LQI':105,'D_LQI':105} and all([r['case_id'] for r in manifest if r['run']==run['label']]==run['dev_case_ids'] and len({r['source_id'] for r in manifest if r['run']==run['label']})==21 for run in index['runs']))
 for c in caches:
  row,i,run=cache_expected[c['name']]
  assert c['run']==row['run'] and c['case_id']==row['case_id'] and c['forward_index']==i and c['input_sha256']==row['input']['sha256'] and c['checkpoint_sha256']==run['checkpoint']['sha256'] and c['normalization']==row['normalization'] and c['bytes']==hashes[c['name']]['bytes'] and c['sha256']==hashes[c['name']]['sha256'] and c['z_definition']=='backbone.global_feature before query, not rebuild_global_feature'
 check('cache0_exact_unique_names_and_same_forward_provenance',len({c['name'] for c in caches})==0 and {c['name'] for c in caches}==set(cache_expected))
 arrays=read(F/'arrays_result_v1.json');check('all210_FP32_finite_dense8192_and_coarse256_arrays',arrays['status']=='ALL210_FP32_FINITE_NATIVE_Q_P_ARRAYS_PASS' and arrays['predictions']==arrays['coarse']==210)
 check('no_extra_context_or_trace_arrays',arrays['context']==arrays['traces']==arrays['trace_layers']==0)
 geometry_audit=read(F/'geometry_result_v1.json')
 check('all210_native_geometry_logs_recomputed_from_saved_points',geometry_audit['status']=='ALL210_SAVED_NATIVE_GEOMETRY_SUMMARIES_RECOMPUTED_PASS' and geometry_audit['predictions']==210)
 models=done['models'];model_receipts=[]
 check('two_models_C_D_order_and105_inference_only',len(models)==2 and [m['run'] for m in models]==['C_LQI','D_LQI'] and all(m['forwards']==105 and m['mode']=='eval_inference_mode' and m['BNCal']==m['optimizer']==m['backward']==0 for m in models))
 for m in models:
  assert issha(m['state_before']) and m['state_before']==m['state_after'] and m['RNG_before']==m['RNG_after'] and rng_valid(m['RNG_before'])
  v=m['construction'];assert v['version']=='F0-LQI-implementation-v1' and v['artificial_fixture'] is False and v['new_mamba_mixers']==16 and v['shared_coordinate_pe_parameters']==1152 and v['decoder_seed']==20261110 and v['expected_decoder_native_calls']==24 and v['expected_total_native_calls']==36 and v['common_initialization_preserved']
  assert v['parent']['variant']=='M0' and v['parent']['seed']==0 and v['parent']['replaced_global_branches']==6 and v['parent']['common_state_unchanged'] and v['parent']['artificial_fixture'] is False and v['inventory']['forbidden_registered_modules']==[]
  model_receipts.append(dict(run=m['run'],state_before=m['state_before'],state_after=m['state_after'],RNG_before_sha256=hashlib.sha256(json.dumps(m['RNG_before'],sort_keys=True).encode()).hexdigest(),RNG_after_sha256=hashlib.sha256(json.dumps(m['RNG_after'],sort_keys=True).encode()).hexdigest(),forwards=m['forwards'],checkpoint=runs[m['run']]['checkpoint']))
 check('both_parameter_and_persistent_BN_fingerprints_unchanged',True)
 check('both_CPU_CUDA_RNG_hash_and_Python_numpy_state_unchanged_valid_formats',True)
 check('actual_native_LQI_construction_and_no_registered_attention',all(m['construction']['variant']=='F0-LQI-v1' and m['construction']['conditional_sequence']=='query_aligned_local_memory_interleaving' and m['construction']['trace_prefix_suffix_semantics']=='interleaved conditional query-position output' and m['construction']['additional_learned_parameters']==0 for m in models))
 resource=rows(O/'resources.jsonl');expected=[]
 for run_no,label in enumerate(['C_LQI','D_LQI']):
  expected.append(('model_start:'+label,run_no*105))
  for i in range(run_no*105+1,(run_no+1)*105+1):expected.extend([('before_forward',i-1),('after_forward',i)])
 expected.append(('all_complete',210))
 check('all423_resource_records_exact_phase_forward_sequence',len(resource)==423 and [(r['phase'],r['forwards']) for r in resource]==expected)
 L=q['limits']
 for r in resource:
  assert finite(r) and r['container_PID']==int((O/'worker.pid').read_text()) and r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
  v=r['values'];actual=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=L['wall_seconds'],disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
  assert r['checks']==actual and all(actual.values()) and r['failed_checks']==[]
 check('all_resource_conditions_independently_recomputed_pass',True)
 check('resource_elapsed_monotonic_and_final_disk_within_budget',all(a['values']['elapsed_seconds']<=b['values']['elapsed_seconds'] for a,b in zip(resource,resource[1:])) and finished['free_disk_bytes']>=L['minimum_free_disk_bytes'])
 check('all_outputs_including_archive_below1GiB',sum(r['bytes'] for r in hashes.values())<=L['output_bytes'])
 archive=completion['archive'];an='development_predictions_v1.tar.gz';ar=hashes[an]
 check('fresh_archive_sha256_bytes_matches_completion',archive['path']==q['output']+'/'+an and archive['sha256']==ar['sha256'] and archive['bytes']==ar['bytes'])
 check('archive_hash_and_bytes_sidecars_match',(O/(an+'.sha256')).read_text().split()==[ar['sha256'],an] and int((O/(an+'.bytes')).read_text())==ar['bytes'])
 members=archive['members'];expectedmembers=expectedpred|set(cache_expected)|{'forward_attempts.jsonl','inference_manifest.jsonl','geometry_summary.jsonl','cache_manifest.jsonl','inference_complete.json','resources.jsonl'}
 check('exact216_unique_archive_members_and_current_file_hashes',len(members)==len({r['name'] for r in members})==216 and {r['name'] for r in members}==expectedmembers and all(r['sha256']==hashes[r['name']]['sha256'] and r['bytes']==hashes[r['name']]['bytes'] for r in members))
 check('archive_content_sidecar_order_and_digests_match',(O/(an+'.contents.sha256')).read_text()==''.join(r['sha256']+'  '+r['name']+'\n' for r in members))
 arc=read(F/'archive_result_v1.json');check('all216_archived_bytes_equal_current_files_no_extraction',arc['status']=='EXACT216_ARCHIVE_MEMBERS_HASH_SIZE_PARITY_PASS' and arc['members']==216 and arc['server_extractions']==0)
 assets=read(F/'assets_result_v1.json');frozen={r['path']:r for r in assets['records']}
 check('exact_frozen_assets_freshly_hashed_without_deserialization',assets['status']=='FROZEN_ASSETS_FRESH_STABLE_HASH_PASS' and len(frozen)==len(assets['records']) and set(frozen)==({r['path'] for r in receipt['read_manifest'] if not r['path'].startswith(q['entry']['path'].rsplit('/',1)[0]+'/')}|{r['checkpoint']['path'] for r in index['runs']}|{r['input']['path'] for r in index['inputs']}) and assets['checkpoint_deserialization']==assets['arrays_decoded']==0)
 for run in index['runs']:
  r=run['checkpoint'];assert all(frozen[r['path']][k]==r[k] for k in ['path','bytes','sha256'])
 for row in index['inputs']:
  r=row['input'];assert all(frozen[r['path']][k]==r[k] for k in ['path','bytes','sha256'])
 check('both_checkpoints_all210_original_inputs_still_exact',True)
 needed=[q[k] for k in ['preflight_scope','static_config','numeric_policy','source_index','source_manifest','fold_binding','helper']]+list(q['implementation'].values())+q['dependencies']+[q['prior_native_admission'][k] for k in ['receipt','audit']]
 check('required_source_dependency_and_metadata_coverage',all(r['path'] in frozen and all(frozen[r['path']][k]==r[k] for k in ['bytes','sha256']) for r in needed))
 peaks={k:max(r['values'][k] for r in resource) for k in ['RSS_bytes','output_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds']}
 peaks['minimum_free_disk_bytes']=min(r['values']['free_disk_bytes'] for r in resource)
 audit=dict(status='FORMAL_LQI_CD_POST_PREDICTION_FREEZE_AUDIT_PASS',date='2026-11-11',request_sha256=QH,checks_passed=len(checks),checks=checks,exit_code=0,worker_and_tmux_absent=True,counts=dict(models=2,per_fold=105,forwards=210,prediction_files=210,coarse_arrays=210,context_files=0,trace_files=0,trace_layers=0,output_files=224,installation_files=14,control_files=6,archive_members=216,resource_records=423,frozen_asset_files=len(frozen)),models=model_receipts,resources=dict(sampled_peaks=peaks,actual_total_output_bytes=sum(r['bytes'] for r in hashes.values()),PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'),archive=dict(path=archive['path'],bytes=archive['bytes'],sha256=archive['sha256'],sidecars=[dict(name=an+'.'+suffix,bytes=hashes[an+'.'+suffix]['bytes'],sha256=hashes[an+'.'+suffix]['sha256']) for suffix in ['sha256','bytes','contents.sha256']]),geometry_log_max_absolute_recompute_error=geometry_audit['max_absolute_stat_error'],metadata_download_bytes=metadata['bytes'],inventory_and_hashes_stable_excluding_atime=True,operations=dict(server_writes=0,new_forward=0,new_backward=0,optimizer_steps=0,GT_arrays_read=0,checkpoint_deserialization=0,GPU_calls=0,scoring=0,BNCal=0),limitations=['State/BN and RNG invariance checked from bound implementation plus saved before/after fingerprints, without reconstructing model tensors','Array and saved-geometry consistency is not accuracy or clinical correctness; no GT scoring performed','Same opened F0 development cases retained; no additional mechanism diagnostic or outcome-driven case selection','Native CUDA admission occurred on previous UUID/driver; this Native run completed on current bound device, not a universal kernel audit','Resource monitoring is sampled, PID telemetry diagnostic only, no exclusive hard isolation guarantee','Prediction archive remains on server; no local long-term archive backup claimed'])
 emit('post_prediction_freeze_audit_result_v1.json',audit)
 emit('download_four_files_manifest_v1.json',dict(status='SERVER_ARCHIVE_FROZEN_AWAITING_USER_DOWNLOAD',request_sha256=QH,suggested_local_directory='E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_LQI/2026-11-11_native_development_eval',files=[dict(name=an,path=archive['path'],bytes=archive['bytes'],sha256=archive['sha256'])]+[dict(**r,path=q['output']+'/'+r['name']) for r in audit['archive']['sidecars']],local_archive_verified=False))
 print(json.dumps({k:audit[k] for k in ['status','checks_passed','counts','resources','archive']},ensure_ascii=False,indent=2))
except BaseException as exc:
 emit('audit_analysis_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),checks_passed=len(checks),checks=checks));raise
