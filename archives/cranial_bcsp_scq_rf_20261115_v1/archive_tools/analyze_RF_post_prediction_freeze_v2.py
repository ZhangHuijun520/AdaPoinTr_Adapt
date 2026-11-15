"""Local hash/count/state/RNG consistency audit; no scoring or model loading."""
from pathlib import Path,PurePosixPath
from collections import Counter
import ast,hashlib,importlib.util,json,math
R=Path(__file__).resolve().parent.parent;F=R/'outputs/scq_rf_pred_freeze_20261115_v2';D=F/'downloads';O=D/'output';I=D/'installed'
B=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2/pending_request_v2'
QH='5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9';checks={}
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def check(n,v):checks[n]=bool(v);assert v,n
def emit(n,j):
 with (F/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def finite(v):
 if isinstance(v,float):return math.isfinite(v)
 if isinstance(v,dict):return all(finite(x) for x in v.values())
 if isinstance(v,list):return all(finite(x) for x in v)
 return True
def issha(v):return isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def rng_valid(v):
 assert set(v)=={'CPU','CUDA','Python','numpy'} and issha(v['CPU']) and issha(v['CUDA'])
 p=ast.literal_eval(v['Python']);assert len(p)==3 and p[0]==3 and len(p[1])==625 and 0<=p[1][-1]<=624
 assert all(isinstance(x,int) and 0<=x<=2**32 for x in p[1][:-1]) and (p[2] is None or math.isfinite(p[2]))
 prefix=repr('MT19937');s=v['numpy'];assert s.startswith(prefix)
 assert len(bytes.fromhex(s[len(prefix):len(prefix)+4992]))==2496
 tail=ast.literal_eval(s[len(prefix)+4992:]);assert len(tail)==3 and 0<=tail[0]<=624 and tail[1] in (0,1) and math.isfinite(tail[2]);return True
try:
 qfile=I/'SCQ_RF_sixmodel_native_prediction_execution_request_v2.json';q=read(qfile);idx=read(I/'RF_sixmodel_input_index_v2.json');mapping=read(B/'installation_mapping_v2.json')
 check('request_exact_authorized_hash',sha(qfile)==QH and sha(B/'payload'/qfile.name)==QH and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and not q['execution_authorized'])
 done=read(O/'inference_complete.json');completion=read(O/'completion.json');finished=read(F/'finished_result_v1.json')
 check('current_identity_exit0_worker_tmux_absent',finished['status']=='EXIT0_TMUX_WORKER_ABSENT' and finished['hostname']==q['identity']['hostname'] and finished['uid']==1000 and (O/'exit_code.txt').read_text().strip()=='0')
 before=read(F/'inventory_before_result_v1.json');after=read(F/'inventory_after_result_v1.json');hashes=before['output']['files'];installed=before['installed']['files']
 check('two_full_hash_and_content_fingerprint_passes_stable_excluding_atime',before==after)
 prednames={r['prediction_filename'] for r in idx['inputs']}
 top={'launch.log','worker.pid','resources.jsonl','inference_manifest.jsonl','forward_attempts.jsonl','development_predictions_v1.tar.gz','development_predictions_v1.tar.gz.contents.sha256','geometry_summary.jsonl','cache_manifest.jsonl','inference_complete.json','development_predictions_v1.tar.gz.sha256','development_predictions_v1.tar.gz.bytes','completion.json','exit_code.txt'}
 check('exact644_output_files_and5_directories',len(prednames)==630 and set(hashes)==prednames|top and set(before['output']['directories'])=={'.','predictions','context','traces','tmp'})
 controls={'native_prediction_authorization_v2.json','native_prediction_runtime_v2.json','native_prediction_launch_once_v2.sh','attempt_claim_v2.json'}
 check('exact20_installed_and4_controls',len(mapping['files'])==20 and len(installed)==24 and set(installed)=={PurePosixPath(r['target']).name for r in mapping['files']}|{'control/'+n for n in controls} and set(before['installed']['directories'])=={'.','control'})
 for r in mapping['files']:
  p=I/PurePosixPath(r['target']).name;assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
 check('all20_installed_files_match_frozen_mapping',True)
 meta=read(F/'metadata_result_v1.json')
 for name,r in meta['files'].items():
  p=D/name;label,relative=name.split('/',1);h=hashes if label=='output' else installed
  assert p.stat().st_size==r['bytes']==h[relative]['bytes'] and sha(p)==r['sha256']==h[relative]['sha256']
 check('all37_metadata_copies_match_independent_remote_hashes',len(meta['files'])==37)
 c=I/'control';auth=read(c/'native_prediction_authorization_v2.json');rt=read(c/'native_prediction_runtime_v2.json');claim=read(c/'attempt_claim_v2.json')
 check('explicit_authorization_and_one_way_runtime',set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-development-authorization-v1' and auth['explicit_user_authorization'] is True and auth['request_sha256']==QH and QH in auth['user_authorization_text'] and rt==dict(schema='bcsp-development-runtime-v1',request_sha256=QH,authorization_sha256=sha(c/'native_prediction_authorization_v2.json')))
 check('single_attempt_claim',claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
 entry=I/'bcsp_scq_rf_sixmodel_native_predict_v2.py';sp=importlib.util.spec_from_file_location('inert_scq_freeze_entry',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
 check('launcher_exact_original_UTF8_bytes',(c/'native_prediction_launch_once_v2.sh').read_bytes()==e.render_launcher(q,QH,sha(c/'native_prediction_authorization_v2.json'),sha(c/'native_prediction_runtime_v2.json')).encode('utf-8'))
 for k in ['entry','input_index','protocol','P3','path_resolution','numeric_policy']:
  r=q[k];assert sha(I/PurePosixPath(r['path']).name)==r['sha256']
 check('entry_index_scope_P3_path_resolution_numeric_bindings',True)
 p3=read(I/'implementation_P3_v2.json');check('new24_and_inherited51_CPU_P3_preserved',p3['status']=='LOCAL_RF_NATIVE_PREDICTION_P3_PASS' and p3['entry_sha256']==sha(entry) and p3['CPU_checks']==24 and p3['inherited_CPU_checks']==51 and all(p3['checks'].values()))
 resolution=read(I/'input_path_resolution_v2.json')
 check('only_frozen_input_paths_changed_current_identity_and_D_confound_preserved',resolution['unique_cases']==210 and resolution['prediction_rows_changed']==630 and resolution['case_source_fold_order_hash_size_normalization_unchanged'] and resolution['roots']==e.DATA_ROOTS and q['identity']==e.CURRENT_IDENTITY and q['comparison_qualification']==e.QUALIFICATION and q['comparison_qualification']['strict_same_device_D_pair'] is False)
 check('frozen_index_validator_current_input_metadata',len(e.validate_index(idx,read(Path(read(B/'local_mirror_v2.json')[q['fold_binding']['path']])))[1])==630)
 for run in idx['runs']:
  a=read(I/PurePosixPath(q['training_audits'][run['label']]['path']).name)
  assert sha(I/PurePosixPath(q['training_audits'][run['label']]['path']).name)==run['training_audit']['sha256']
  assert a['status']==e.FROZEN_MODELS[run['label']]['audit_status'] and all(a['checks'].values()) and a['identity']==e.FROZEN_MODELS[run['label']]['identity'] and a['request_sha256']==run['training_request']['sha256'] and a['checkpoint']=={k:run['checkpoint'][k] for k in ('bytes','sha256')}
 check('all6_training_freezes_and_checkpoints_bound',True)
 check('completion630_no_training_BNCal_loss_backward',done['status']=='SCQ_RF_SIXMODEL_630_NATIVE_FORWARD_COMPLETE' and done['forwards']==completion['forwards']==630 and done['context_cases']==done['trace_cases']==0 and all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']) and done['request_sha256']==completion['request_sha256']==QH)
 manifest=lines(O/'inference_manifest.jsonl');journal=lines(O/'forward_attempts.jsonl');geometry=lines(O/'geometry_summary.jsonl');caches=lines(O/'cache_manifest.jsonl')
 check('exact630_manifest_claims_geometry_and0_caches',len(manifest)==len(journal)==len(geometry)==630 and caches==[] and finite(manifest+geometry))
 runs={r['label']:r for r in idx['runs']}
 for i,(row,m,j,g) in enumerate(zip(idx['inputs'],manifest,journal,geometry),1):
  run=runs[row['run']];assert j['forward_index']==m['forward_index']==i and j['status']=='CLAIMED_BEFORE_FORWARD'
  assert all(x['run']==row['run'] and x['case_id']==row['case_id'] for x in (m,j,g))
  assert all(m[k]==row[k] for k in ('variant','fold','source_id','n_input','normalization')) and m['n_output']==8192 and m['input_sha256']==row['input']['sha256'] and m['checkpoint_sha256']==run['checkpoint']['sha256'] and m['operational_seconds']>=0
  r=m['prediction'];assert r['name']==row['prediction_filename'] and all(r[k]==hashes[r['name']][k] for k in ['bytes','sha256'])
  assert row['save_coarse'] is row['save_Qraw'] is True and row['cache_context'] is row['save_full_decoder_trace'] is False and g['frame']=='native_D_only_normalized_no_GT'
 check('all630_actual_order_case_input_weight_frame_hashes',True)
 check('exact630_unique_pre_forward_claims',len({(v['run'],v['case_id']) for v in journal})==630 and [v['forward_index'] for v in journal]==list(range(1,631)))
 check('each_run105_21sources_five_types',Counter(v['run'] for v in manifest)=={k:105 for k in runs} and all([v['case_id'] for v in manifest if v['run']==run['label']]==run['dev_case_ids'] and len({v['source_id'] for v in manifest if v['run']==run['label']})==21 and set(Counter(v['source_id'] for v in manifest if v['run']==run['label']).values())=={5} for run in idx['runs']))
 for f in 'CD':
  parts=[[v for v in manifest if v['run']==arm+'_'+f] for arm in ['Sref','Static','Requery']]
  assert all(all(x[k]==y[k]==z[k] for k in ['case_id','source_id','input_sha256','normalization']) for x,y,z in zip(*parts))
 check('three_arms_same_fold_paired_inputs_frames_order',len({r['input']['path'] for r in idx['inputs']})==210)
 check('all630_saved_arrays_FP32_finite_Qraw_Qused_delta_identity',read(F/'arrays_result_v1.json')['status']=='ALL630_FP32_FINITE_QRAW_QUSED_DELTA_P_PASS')
 ga=read(F/'geometry_result_v1.json');check('all630_geometry_statistics_independently_recomputed',ga['status']=='ALL630_GEOMETRY_LOGS_RECOMPUTED_PASS' and ga['predictions']==630 and ga['GT_read'] is ga['scoring'] is False)
 models=done['models'];model_receipts=[]
 check('six_models_in_fixed_order_105_inference_only',len(models)==6 and [m['run'] for m in models]==['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D'] and all(m['forwards']==105 and m['mode']=='eval_inference_mode' and m['BNCal']==m['optimizer']==m['backward']==0 for m in models))
 for m in models:
  assert issha(m['state_before']) and m['state_before']==m['state_after'] and m['RNG_before']==m['RNG_after'] and rng_valid(m['RNG_before'])
  ev=m['construction'];is_rf='rf' in ev;scq_ev=ev['parent'] if is_rf else ev;v=scq_ev['parent'];s=scq_ev['scq'];arm=runs[m['run']]['variant'];assert is_rf is (arm!='S')
  assert v['version']=='F0-LQI-implementation-v1' and v['artificial_fixture'] is False and v['variant']=='F0-LQI-v1' and v['new_mamba_mixers']==16 and v['shared_coordinate_pe_parameters']==1152 and v['common_initialization_preserved']
  assert v['conditional_sequence']=='query_aligned_local_memory_interleaving' and v['additional_learned_parameters']==0 and v['inventory']['forbidden_registered_modules']==[]
  assert v['parent']['variant']=='M0' and v['parent']['seed']==0 and v['parent']['replaced_global_branches']==6 and v['parent']['common_state_unchanged']
  assert s['version']=='SCQ-v2-implementation-v1' and s['variant']=='S' and s['common_initialization_preserved'] and s['mother_sha256']=='1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4'
  assert s['new_parameters']==693507 and s['total_parameters']==40596676 and s['initialization_sha256']==q['initialization']['sha256']
  if is_rf:
   rf=ev['rf'];assert rf['variant']==arm and rf['additional_parameters']==231171 and rf['total_parameters']==40827847 and rf['initialization_sha256']==q['rf_initialization']['sha256'] and rf['common_state_preserved'] and rf['CPU_RNG_preserved']
  model_receipts.append(dict(run=m['run'],forwards=105,state_before=m['state_before'],state_after=m['state_after'],RNG_before_sha256=hashlib.sha256(json.dumps(m['RNG_before'],sort_keys=True).encode()).hexdigest(),RNG_after_sha256=hashlib.sha256(json.dumps(m['RNG_after'],sort_keys=True).encode()).hexdigest(),checkpoint=runs[m['run']]['checkpoint']))
 check('all630_RF_stage_centroids_independently_recomputed',read(F/'RF_stages_result_v1.json')['status']=='ALL630_RF_STAGE_CENTROID_LOGS_RECOMPUTED_PASS')
 check('all6_parameter_and_persistent_BN_fingerprints_unchanged',True)
 check('all6_CPU_CUDA_Python_numpy_RNG_unchanged_and_valid',True)
 check('actual_native_LQI_SCQ_RF_construction_and_parameter_counts',True)
 resources=lines(O/'resources.jsonl');expected=[]
 for n,label in enumerate(['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D']):
  expected.append(('model_start:'+label,n*105))
  for i in range(n*105+1,(n+1)*105+1):expected.extend([('before_forward',i-1),('after_forward',i)])
 expected.append(('all_complete',630));check('exact1267_resource_phase_and_forward_sequence',len(resources)==1267 and [(r['phase'],r['forwards']) for r in resources]==expected)
 L=q['limits']
 for r in resources:
  assert finite(r) and r['container_PID']==int((O/'worker.pid').read_text()) and r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
  v=r['values'];actual=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=L['wall_seconds'],disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
  assert r['checks']==actual and all(actual.values()) and r['failed_checks']==[]
 check('all_resource_conditions_recomputed',all(a['values']['elapsed_seconds']<=b['values']['elapsed_seconds'] for a,b in zip(resources,resources[1:])) and sum(r['bytes'] for r in hashes.values())<=L['output_bytes'])
 archive=completion['archive'];an='development_predictions_v1.tar.gz';ar=hashes[an]
 check('fresh_archive_hash_size_match_completion',archive['path']==q['output']+'/'+an and archive['bytes']==ar['bytes'] and archive['sha256']==ar['sha256'])
 check('archive_SHA_and_bytes_sidecars',(O/(an+'.sha256')).read_text().split()==[ar['sha256'],an] and int((O/(an+'.bytes')).read_text())==ar['bytes'])
 members=archive['members'];expectedmembers=prednames|{'forward_attempts.jsonl','inference_manifest.jsonl','geometry_summary.jsonl','cache_manifest.jsonl','inference_complete.json','resources.jsonl'}
 check('exact636_archive_members_current_hashes',len(members)==len({r['name'] for r in members})==636 and {r['name'] for r in members}==expectedmembers and all(all(r[k]==hashes[r['name']][k] for k in ['bytes','sha256']) for r in members))
 check('content_sidecar_exact_member_order_hashes',(O/(an+'.contents.sha256')).read_text()==''.join(r['sha256']+'  '+r['name']+'\n' for r in members))
 check('all636_archived_bytes_equal_outputs_no_extraction',read(F/'archive_result_v1.json')==dict(status='ALL636_ARCHIVE_MEMBER_BYTES_MATCH',members=636,server_extractions=0))
 assets=list(F.glob('fresh_asset_*_result_v1.json'));cps=list(F.glob('fresh_checkpoint_*_result_v1.json'));inp=read(F/'fresh_inputs210.remote_result_v1.json')
 check('all_frozen_assets_six_checkpoints_and210_inputs_fresh_hashes',len(assets)==15 and len(cps)==6 and all(read(p)['status']=='EXACT_HASHES_PASS' for p in assets+cps) and inp['status']=='ALL210_INPUT_HASHES_PASS' and inp['files']==210 and inp['array_reads']==0)
 check('no_extra_failure_or_execution_artifacts','failure.json' not in hashes and not (F/'collection_failure_v1.json').exists() and read(F/'collection_complete_v1.json')['status']=='READONLY_COLLECTION_COMPLETE')
 peaks={k:max(r['values'][k] for r in resources) for k in ['RSS_bytes','output_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds']};peaks['minimum_free_disk_bytes']=min(r['values']['free_disk_bytes'] for r in resources)
 sidecars=[dict(name=an+'.'+s,bytes=hashes[an+'.'+s]['bytes'],sha256=hashes[an+'.'+s]['sha256']) for s in ['sha256','bytes','contents.sha256']]
 audit=dict(status='FORMAL_SCQ_RF_SIXMODEL_POST_PREDICTION_FREEZE_AUDIT_PASS',date='2026-11-15',request_sha256=QH,checks=checks,checks_passed=len(checks),identity=q['identity'],training_identities={k:v['identity'] for k,v in e.FROZEN_MODELS.items()},comparison_qualification=q['comparison_qualification'],counts=dict(models=6,per_model=105,forwards=630,prediction_files=630,Qraw=630,Qused=630,delta=630,dense=630,output_files=644,installed_files=20,control_files=4,archive_members=636,resource_records=1267,context=0,traces=0),models=model_receipts,archive=dict(path=archive['path'],bytes=ar['bytes'],sha256=ar['sha256'],sidecars=sidecars),resource_peaks=peaks,geometry_recompute_max_absolute_error=ga['max_absolute_stat_error'],operations=dict(server_writes=0,new_forward=0,new_backward=0,checkpoint_deserialization=0,GPU_calls=0,GT_arrays_read=0,scoring=0,BNCal=0),limitations=['State/BN and RNG equality checked from bound source and recorded before/after fingerprints, not by loading model tensors.','Numpy decodes saved model output arrays only; no GT accuracy/clinical correctness conclusion.','D Static training GPU UUID/driver differ from D Sref/Requery; D comparison is supplementary device-confounded evidence, C remains same-device primary mechanism evidence. All six predictions use the same current device.','Sampled resource monitoring, no PID ownership or hard isolation claim.','Previous v1 input-path failure preserved. This audit targets only the authorized successful v2 prediction; no repeated model inference.','Archive remains server-side; no claim of local long-term backup.'])
 emit('post_prediction_freeze_audit_result_v1.json',audit)
 emit('download_four_files_manifest_v1.json',dict(status='SERVER_FROZEN_AWAITING_DOWNLOAD',suggested_local_directory='E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_native_development_eval',local_archive_verified=False,files=[dict(name=an,path=archive['path'],bytes=ar['bytes'],sha256=ar['sha256'])]+[dict(**r,path=q['output']+'/'+r['name']) for r in sidecars]))
 print(json.dumps(dict(status=audit['status'],checks=len(checks),counts=audit['counts'],archive=audit['archive'],resource_peaks=peaks)))
except BaseException as exc:
 emit('audit_analysis_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc)));raise
