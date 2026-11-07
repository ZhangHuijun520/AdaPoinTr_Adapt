"""Offline exact manifest/count/state/RNG/H2 audit. No fitting, scoring or model loading."""
import collections,hashlib,json,math
from pathlib import Path
S=Path(__file__).resolve().parent;F=S/'post_prediction_freeze_audit_v1';D=F/'downloads';P=S/'pending_request_v1/transport_payload';QH='b95b866a6b3a0eaeb1e840e003ecd426847ed47b07675b6c1f7644b5aee97170'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
checks={}
def check(n,v):
 if not v:raise AssertionError(n)
 checks[n]=True
def finite(v):
 if isinstance(v,float):return math.isfinite(v)
 if isinstance(v,list):return all(finite(x) for x in v)
 if isinstance(v,dict):return all(finite(x) for x in v.values())
 return True
def close(a,b):return math.isclose(a,b,rel_tol=2e-6,abs_tol=1e-6)
def emit(n,v):
 with (F/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
try:
 qp=P/'H2_C_D_fourmodel_native_prediction_execution_request_v1.json';q=read(qp);check('authorized_request_hash',sha(qp)==QH)
 remote=read(F/'remote_readonly_receipt_v1.json');check('exit0_worker_tmux_absent',remote['exit_code']==0 and remote['worker_and_tmux_absent'] and (D/'exit_code.txt').read_text().strip()=='0')
 check('exact433_files_and_stable_inventory',remote['exact_output_files']==433 and remote['inventory_unchanged_excluding_atime'])
 check('fresh420_finite_FP32_predictions_and425_archive_members',remote['archive_member_array_audit']['status']=='TAR_425_HASHES_AND420_FINITE_ARRAYS_PASS' and remote['archive_member_array_audit']['prediction_arrays']==420 and remote['archive_member_array_audit']['members']==425)
 check('exact20_preregistered_coarse_cases',read(F/'coarse_positions_receipt_v1.json')['status']=='EXACT20_PREREGISTERED_COARSE_MEMBERS_PASS')
 check('text_downloads_match_fresh_remote_hashes',all(sha(p)==remote['output_SHA256']['./'+p.name] for p in D.iterdir()))
 C=S/'authorized_execution_v1/readback';auth=read(C/'native_prediction_authorization_v1.json');runtime=read(C/'native_prediction_runtime_v1.json');claim=read(C/'native_prediction_single_attempt_claim_v1.json')
 check('explicit_one_way_authorization_single_claim',auth['request_sha256']==QH and auth['explicit_user_authorization'] is True and runtime==dict(schema='bcsp-development-runtime-v1',request_sha256=QH,authorization_sha256=sha(C/'native_prediction_authorization_v1.json')) and claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
 idx=read(P/'H2_C_D_fourmodel_input_index_v1.json');proto=read(P/'H2_fourmodel_native_prediction_protocol_v1.json');check('frozen_input_protocol_hashes',sha(P/'H2_C_D_fourmodel_input_index_v1.json')==q['input_index']['sha256'] and sha(P/'H2_fourmodel_native_prediction_protocol_v1.json')==q['protocol']['sha256'])
 done=read(D/'inference_complete.json');completed=read(D/'completion.json');check('exact420_completed_no_training_BNCal_loss_backward',done['status']=='P2_H2_FOURMODEL_420_NATIVE_FORWARD_COMPLETE' and done['forwards']==completed['forwards']==420 and done['request_sha256']==completed['request_sha256']==QH and all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']))
 manifest=lines(D/'inference_manifest.jsonl');journal=lines(D/'forward_attempts.jsonl');geometry=lines(D/'geometry_summary.jsonl');check('three_exact420_finite_logs',len(manifest)==len(journal)==len(geometry)==420 and all(finite(x) for x in manifest+geometry))
 byrun={r['label']:r for r in idx['runs']};expectedfiles=set();scaleerr=radiuserr=centererr=0
 for i,(row,m,j,g) in enumerate(zip(idx['inputs'],manifest,journal,geometry),1):
  run=byrun[row['run']];label=row['run'];cid=row['case_id'];assert m['forward_index']==j['forward_index']==i and j['status']=='CLAIMED_BEFORE_FORWARD'
  assert all(x['run']==label and x['case_id']==cid for x in [m,j,g])
  assert all(m[k]==row[k] for k in ['variant','source_id','fold','n_input','normalization']) and m['n_output']==8192 and m['input_sha256']==row['input']['sha256'] and m['checkpoint_sha256']==run['checkpoint']['sha256'] and m['operational_seconds']>=0
  rec=m['prediction'];name='predictions/'+label+'__'+cid+'.npz';assert rec['name']==name and rec['bytes']==remote['output_bytes'][name] and rec['sha256']==remote['output_SHA256']['./'+name] and name not in expectedfiles;expectedfiles.add(name)
  h=g['H2'];assert h['mode']==run['mode'] and h['condition_override'] is None and h['GT_read'] is False and h['loss_calls']==0 and g['frame']=='native_D_only_normalized_no_GT' and len(h['delta'])==len(h['scale'])==1
  delta,scale=h['delta'][0],h['scale'][0];assert h['raw']['radius']>1e-6 and h['used']['radius']>1e-6
  for part in ['coarse','dense']:
   x=g[part];assert len(x['centroid'])==len(x['bbox_min'])==len(x['bbox_max'])==len(x['covariance_eigenvalues'])==3 and all(a<=b for a,b in zip(x['bbox_min'],x['bbox_max'])) and x['radius_gyration']>0
  assert all(close(a,b) for a,b in zip(g['coarse']['centroid'],h['used']['centroid'])) and close(g['coarse']['radius_gyration'],h['used']['radius'])
  assert all(close(a,b) for a,b in zip(g['mean_dense_minus_coarse'],[a-b for a,b in zip(g['dense']['centroid'],g['coarse']['centroid'])]))
  if run['mode']=='AUX':assert scale==1 and h['raw']==h['used']
  else:
   expected=math.exp(math.log(1.25)*math.tanh(delta/math.log(1.25)));assert .8-1e-6<=scale<=1.25+1e-6 and close(scale,expected) and close(h['used']['radius'],h['raw']['radius']*scale) and all(close(a,b) for a,b in zip(h['raw']['centroid'],h['used']['centroid']))
   scaleerr=max(scaleerr,abs(scale-expected));radiuserr=max(radiuserr,abs(h['used']['radius']-h['raw']['radius']*scale));centererr=max(centererr,max(abs(a-b) for a,b in zip(h['raw']['centroid'],h['used']['centroid'])))
 check('every_prediction_hash_size_and_original_case_order',len(expectedfiles)==420)
 check('all420_attempts_claimed_once_no_extra_or_missing',len({(r['run'],r['case_id']) for r in journal})==420)
 check('per_model105_and210_unique_cases_same_fold_inputs',collections.Counter(m['run'] for m in manifest)=={r['label']:105 for r in idx['runs']} and len({m['case_id'] for m in manifest})==210)
 check('native_H2_modes_no_GT_loss_or_override_all_cases',True)
 check('AUX_identity_COUPLE_scale_formula_center_radius_and_dense_summaries',True)
 models=done['models'];check('four_models_in_fixed_order',len(models)==4 and [m['run'] for m in models]==proto['model_order'])
 for m,run in zip(models,idx['runs']):
  assert m['forwards']==105 and m['mode']=='eval_inference_mode' and m['BNCal']==m['optimizer']==m['backward']==0
  assert m['state_before']==m['state_after'] and len(m['state_before'])==64 and m['RNG_before']==m['RNG_after'] and set(m['RNG_before'])=={'CPU','CUDA','Python','numpy'} and all(m['RNG_before'].values())
  e=m['construction'];assert e['variant']=='M0' and e['seed']==0 and e['replaced_global_branches']==6 and e['common_state_unchanged'] is True and e['artificial_fixture'] is False and e['H2_mode']==run['mode'] and e['H2_contract']==proto['H2_common'] and e['common_state_after_H2_unchanged'] is True
 check('all_four_parameter_and_persistent_BN_state_fingerprints_unchanged',True)
 check('all_four_CPU_CUDA_Python_numpy_RNG_unchanged',True)
 check('actual_native_M0_and_correct_H2_construction_records',True)
 archive=completed['archive'];aname='development_predictions_v1.tar.gz';ah=remote['output_SHA256']['./'+aname];assert archive['path']==q['output']+'/'+aname and archive['bytes']==remote['output_bytes'][aname] and archive['sha256']==ah
 check('archive_actual_SHA256_bytes_and3_sidecars_match', (D/(aname+'.sha256')).read_text().split()==[ah,aname] and int((D/(aname+'.bytes')).read_text())==archive['bytes'])
 members=archive['members'];expectedmembers=expectedfiles|{'inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl'}
 check('archive_exact425_members_match_all_current_files',len(members)==425 and {r['name'] for r in members}==expectedmembers and all(r['bytes']==remote['output_bytes'][r['name']] and r['sha256']==remote['output_SHA256']['./'+r['name']] for r in members))
 check('archive_content_sidecar_exact_order_and_SHA256',(D/(aname+'.contents.sha256')).read_text()==''.join(r['sha256']+'  '+r['name']+'\n' for r in members))
 resources=lines(D/'resources.jsonl');sequence=[]
 for model in range(4):
  sequence.append(('model_start:'+proto['model_order'][model],105*model))
  for fwd in range(105*model+1,105*(model+1)+1):sequence.extend([('before_forward',fwd-1),('after_forward',fwd)])
 sequence.append(('all_complete',420));assert len(resources)==845 and [(x['phase'],x['forwards']) for x in resources]==sequence
 L=q['limits']
 for x in resources:
  assert finite(x) and all(x['checks'].values()) and not x['failed_checks'] and x['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
  v=x['values'];assert all(v[k]<=L[k] for k in ['RSS_bytes','output_bytes','device_MiB']) and v['peak_allocated']<=L['torch_peak_bytes'] and v['peak_reserved']<=L['torch_peak_bytes'] and v['elapsed_seconds']<=L['wall_seconds'] and v['free_disk_bytes']>=L['minimum_free_disk_bytes']
 check('all845_resource_records_exact_sequence_within_limits',True)
 check('final_outputs_including_archive_below1GiB',sum(remote['output_bytes'].values())<=L['output_bytes'])
 frozen={r['path']:r for r in remote['frozen_asset_records']};check('four_checkpoints_and_frozen_sources_freshly_rehashed',len(frozen)==remote['frozen_assets'] and all(frozen[r['checkpoint']['path']]==r['checkpoint'] for r in idx['runs']))
 p3=read(P/'implementation_P3_v1.json');check('entry_P3_and_protocol_bindings_unchanged',p3['entry_sha256']==q['entry']['sha256']==sha(P/'bcsp_h2_fourmodel_native_predict_v1.py') and p3['status']=='LOCAL_H2_FOURMODEL_PREDICTION_P3_PASS')
 peaks={k:max(x['values'][k] for x in resources) for k in ['RSS_bytes','output_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds']}
 report=dict(status='FORMAL_H2_FOURMODEL_POST_PREDICTION_FREEZE_AUDIT_PASS',request_sha256=QH,checks_passed=len(checks),checks=checks,counts=dict(models=4,per_model=105,forwards=420,prediction_files=420,unique_cases=210,unique_sources=42,archive_members=425,coarse_arrays=20,resource_records=845),archive=dict(path=archive['path'],bytes=archive['bytes'],sha256=ah,content_sidecar_sha256=sha(D/(aname+'.contents.sha256'))),models=[dict(run=m['run'],state_before=m['state_before'],state_after=m['state_after'],RNG_before_sha256=hashlib.sha256(json.dumps(m['RNG_before'],sort_keys=True).encode()).hexdigest(),RNG_after_sha256=hashlib.sha256(json.dumps(m['RNG_after'],sort_keys=True).encode()).hexdigest(),forwards=m['forwards'],checkpoint=run['checkpoint']) for m,run in zip(models,idx['runs'])],H2_native_checks=dict(no_override=True,no_GT_read_or_loss=True,AUX_raw_used_identity=True,COUPLE_formula_bounds_and_moments=True,max_scale_roundoff=scaleerr,max_radius_roundoff=radiuserr,max_centroid_roundoff=centererr),resources=dict(peaks=peaks,PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'),frozen_assets=remote['frozen_assets'],server_writes=0,new_forward=0,new_backward=0,checkpoint_loaded=False,archive_extracted=False,scoring_executed=False,BNCal=False,extra_condition_intervention=False,limitations=['State/RNG invariance audited from bound code and saved fingerprints; full parameters/BN tensors not rebuilt by this audit','420 prediction arrays and20 fixed coarse arrays checked for shape/dtype/finite values without reference geometry; no accuracy or clinical correctness conclusion','Same-forward H2 moments check formulas, not clinical shape/interface benefit','Native finite Mamba nondeterminism and sampled resource/PID limitations inherited','Archive remains on server; no long-term local backup claimed'])
 emit('audit_report_v1.json',report);print(json.dumps({k:report[k] for k in ['status','checks_passed','counts','archive','resources']},indent=2))
except BaseException as exc:
 emit('analysis_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks));raise
