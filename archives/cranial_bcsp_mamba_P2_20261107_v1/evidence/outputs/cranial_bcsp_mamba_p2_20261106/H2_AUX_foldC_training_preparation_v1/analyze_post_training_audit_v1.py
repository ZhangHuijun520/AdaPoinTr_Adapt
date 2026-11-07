"""Offline evidence checks only; standard library, no arrays/models/checkpoint loading."""
import collections,hashlib,json,math
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[2];F=S/'post_training_freeze_audit_v1';D=F/'downloads';P=S/'first_FoldC_request_v1/transport_payload'
QH='0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def close(a,b):return math.isclose(a,b,rel_tol=2e-6,abs_tol=1e-6)
checks={}
def check(n,v):
 if not v:raise AssertionError(n)
 checks[n]=True
def finite(v):
 if isinstance(v,float):return math.isfinite(v)
 if isinstance(v,list):return all(finite(x) for x in v)
 if isinstance(v,dict):return all(finite(x) for x in v.values())
 return True
def emit(n,v):
 with (F/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
try:
 q=read(P/'H2_AUX_foldC_seed0_training_execution_request_v1.json');check('authorized_request_hash',sha(P/'H2_AUX_foldC_seed0_training_execution_request_v1.json')==QH)
 remote=read(F/'remote_readonly_receipt_v1.json');check('remote_exact15_files_and_stable_inventory',remote['status']=='REMOTE_H2_AUX_POST_TRAINING_FILES_PASS' and remote['exact_output_files']==15 and remote['inventory_unchanged_excluding_atime'])
 check('exit0_worker_and_tmux_absent',remote['exit_code']==0 and remote['worker_absent'] and remote['tmux_absent'] and (D/'exit_code.txt').read_text().strip()=='0')
 for p in D.iterdir():assert sha(p)==remote['output_SHA256']['./'+p.name]
 check('all_downloaded_evidence_matches_fresh_remote_hashes',True)
 C=S/'authorized_execution_v1/readback';auth=read(C/'H2_authorization_v1.json');runtime=read(C/'H2_runtime_v1.json');claim=read(C/'single_attempt_claim_v1.json')
 check('one_way_explicit_authorization_single_attempt',auth['request_sha256']==QH and auth['explicit_user_authorization'] is True and runtime==dict(schema='bcsp-p2-H2-training-runtime-v1',request_sha256=QH,authorization_sha256=sha(C/'H2_authorization_v1.json')) and claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
 frozen={r['path']:r for r in remote['frozen_asset_records']};check('all_installed_and_reused_assets_rehashed',len(frozen)==remote['frozen_assets'] and all(r['sha256'] for r in frozen.values()))
 completed=read(D/'completion.json');expected_counts=dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100)
 check('exact3900_updates_100_traversals_31200_exposures',completed['counts']==expected_counts and completed['optimizer_updates']==3900 and completed['traversals']==100 and completed['case_exposures']==31200)
 check('BNCal_evaluation_resume_false',all(completed[k] is False for k in ['bncal_executed','evaluation_executed','resume']))
 cp=remote['output_SHA256']['./ckpt-last.pth'];check('checkpoint_fresh_SHA256_matches_completion',cp==completed['checkpoint_sha256'] and remote['output_bytes']['ckpt-last.pth']==407239343)
 manifest=read(D/'payload_manifest.json')['files'];expected_manifest=set(remote['output_bytes'])-{'launch.log','worker.pid','exit_code.txt','payload_manifest.json'}
 check('payload_manifest_exact_members_bytes_and_SHA256',len(manifest)==len(expected_manifest) and {x['name'] for x in manifest}==expected_manifest and all(x['bytes']==remote['output_bytes'][x['name']] and x['sha256']==remote['output_SHA256']['./'+x['name']] for x in manifest))
 plan=read(D/'order_plan.json');original_plan=R/'outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/shared_order_foldC_seed0_v1.json'
 initial=read(D/'initialization.json');check('original_raw_and_canonical_order_binding',sha(D/'order_plan.json')==sha(original_plan)==q['order_plan']['sha256'] and canonical(plan)==initial['order_sha256']==completed['order_sha256'])
 fold=read(R/'outputs/cranial_bcsp_geov1_20261024/consolidated_binding_v1/fold_binding.json')['folds']['C'];records=[json.loads(x) for x in (R/'outputs/cranial_bcsp_geov1_20261024/real_data_qc_v1/manifest_8192.jsonl').read_text().splitlines()]
 source={r['case_id']:r['source_id'] for r in records if r['case_id'] in set(plan['case_ids'])}
 check('fixed315_train63_sources_no_development_overlap',plan['case_ids']==fold['train_case_ids'] and len(source)==315 and len(set(source.values()))==63 and not set(fold['train_sources'])&set(fold['dev_sources']))
 rows=[json.loads(x) for x in (D/'metrics.jsonl').read_text().splitlines()];check('exact3900_finite_metric_records',len(rows)==3900 and all(finite(x) for x in rows))
 cases,sources,drops=collections.Counter(),collections.Counter(),collections.Counter();max_t_error=max_aux_error=max_loss_error=0
 for epoch,e in enumerate(plan['epochs']):
  assert e['epoch']==epoch and len(e['batches'])==39 and len(e['dropped'])==3
  flat=sum(e['batches'],[])+e['dropped'];assert len(flat)==len(set(flat))==315 and set(flat)==set(plan['case_ids'])
  for b,batch in enumerate(e['batches']):
   x=rows[epoch*39+b];assert x['step']==epoch*39+b+1 and x['epoch']==epoch and x['batch']==b and x['case_ids']==batch and len(batch)==8 and x['source_ids']==[source[c] for c in batch]
   assert x['LR']==[.0001*max(.9**(epoch/21),.02)]*2 and x['BN_momentum']==max(.9*.5**(epoch/21),.01)
   assert x['clip_max_norm']==10 and x['optimizer_step_committed'] is True and x['grad_norm_before_clip']>=0
   assert x['loss_sparse']==x['loss_denoise']==0 and x['loss_reconstruction']==x['loss_dense']
   assert x['H2_mode']=='AUX' and x['H2_generation']==x['step'] and x['loss_dense_includes_H2_aux'] is True
   assert x['H2_scale']==[1.]*8 and x['H2_centroid_raw']==x['H2_centroid_used'] and x['H2_radius_raw']==x['H2_radius_used']
   for n in ['raw','used','dense','GT']:
    assert len(x['H2_radius_'+n])==8 and all(v>1e-6 for v in x['H2_radius_'+n]) and len(x['H2_centroid_'+n])==8 and all(len(v)==3 for v in x['H2_centroid_'+n])
   assert len(x['H2_delta'])==len(x['H2_target_t'])==8
   for t,rg,rq in zip(x['H2_target_t'],x['H2_radius_GT'],x['H2_radius_raw']):
    target=math.log(rg)-math.log(rq);max_t_error=max(max_t_error,abs(t-target));assert close(t,target)
   errors=[abs(a-t) for a,t in zip(x['H2_delta'],x['H2_target_t'])];aux=sum(.5*v*v/.1 if v<.1 else v-.05 for v in errors)/8
   max_aux_error=max(max_aux_error,abs(aux-x['H2_aux_raw']));assert close(aux,x['H2_aux_raw']) and close(x['H2_aux_weighted'],.1*x['H2_aux_raw'])
   loss=x['loss_original_reconstruction']+x['H2_aux_weighted'];max_loss_error=max(max_loss_error,abs(loss-x['loss_dense']));assert close(loss,x['loss_dense']) and close(x['loss'],x['loss_sparse']+x['loss_dense'])
   cases.update(batch);sources.update(x['source_ids'])
  drops.update(e['dropped'])
 check('all3900_actual_batches_LR_BN_and_commit_match_original',True)
 exposure=dict(case=dict(cases),source=dict(sources),dropped_case=dict(drops),order_sha256=canonical(plan))
 check('full_exposure_and300_drops_match',read(D/'exposure.json')==exposure and sum(cases.values())==sum(sources.values())==31200 and sum(drops.values())==300)
 check('H2_AUX_all_steps_raw_equals_used_scale_one',True)
 check('H2_all_steps_log_radius_target_and_single_weight_loss',True)
 check('zero_initial_head_first_batch_and_later_learning',rows[0]['H2_delta']==[0.]*8 and any(abs(v)>0 for x in rows[1:] for v in x['H2_delta']))
 construction=read(D/'model_construction.json');factory=construction['factory'];original=read(S/'server_readiness_v1/metadata/M0_construction.json')
 common={k:v for k,v in factory.items() if k not in ['H2_mode','H2_contract','common_state_after_H2_unchanged']}
 check('exact_original_M0_factory_and_common_initialization',common==original['factory'] and factory['common_state_after_H2_unchanged'] is True and factory['H2_mode']=='AUX' and dict(factory['H2_contract'],mode='AUX')==q['h2_config'] and construction['H2_head_initialization']=='ALL_ZERO_NO_RNG_DRAW' and not factory['artificial_fixture'])
 check('initialization_seed_and_valid_fingerprints_recorded',initial['seed']==0 and all(len(initial[k])==64 and int(initial[k],16)>=0 for k in ['parameter_sha256','persistent_state_sha256']))
 groups=read(D/'optimizer_parameter_groups.json');oldgroups=original['optimizer_groups'];head=[g for g in groups if g['name'].startswith('h2_range_head.')]
 check('original_optimizer_groups_preserved_plus_exact1025_head',len(groups)==364 and [g for g in groups if not g['name'].startswith('h2_range_head.')]==oldgroups and len(oldgroups)==362 and {g['name'] for g in head}=={'h2_range_head.weight','h2_range_head.bias'} and {g['name']:g['shape'] for g in head}=={'h2_range_head.weight':[1,1024],'h2_range_head.bias':[1]} and all(g['weight_decay']==(0 if g['name'].endswith('.bias') else .0005) for g in head))
 baseline=read(P/'frozen_M0_C_post_training_audit_v1.json');check('optimizer_defaults_match_frozen_M0',read(D/'optimizer_actual_defaults.json')==baseline['optimizer']['defaults'])
 identity=read(D/'run_identity.json');check('run_identity_H2_numeric_policy_and_CUDA_evidence',identity['stage']==q['stage'] and identity['fold']=='C' and identity['variant']=='M0' and identity['seed']==0 and identity['H2']==q['h2_config'] and identity['numeric_policy_sha256']==q['numeric_policy']['sha256'] and identity['CUDA_audit_sha256']==q['cuda_audit']['sha256'] and identity['SSM_gradient_non_bitwise_reproducibility_disclosed'] is True)
 resources=[json.loads(x) for x in (D/'resources.jsonl').read_text().splitlines()];limits=read(P/'static_H2_AUX_training_config_v1.json')['resources']
 assert len(resources)==3902 and [(x['phase'],x['committed_step']) for x in resources]==[('after_step',i) for i in range(1,3901)]+[('before_final',3900),('after_final',3900)]
 for x in resources:
  assert finite(x) and x['limits']==limits and x['resource_guard_passed'] is True and not x['failed_checks'] and all(x['checks'].values())
  assert x['RSS']<=limits['RSS_bytes'] and x['output_bytes']<=limits['output_bytes'] and x['peak_allocated']<=limits['torch_peak_bytes'] and x['peak_reserved']<=limits['torch_peak_bytes'] and x['device_MiB']<=limits['device_MiB'] and x['elapsed_seconds']<=limits['wall_seconds']
  assert x['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
 check('all3902_resource_records_within_original_limits',True)
 check('final_output_size_within_budget',sum(remote['output_bytes'].values())<=limits['output_bytes'])
 peaks={k:max(x[k] for x in resources) for k in ['RSS','peak_allocated','peak_reserved','device_MiB','elapsed_seconds']}
 report=dict(status='FORMAL_H2_AUX_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS',request_sha256=QH,checks_passed=len(checks),checks=checks,checkpoint=dict(name='ckpt-last.pth',bytes=remote['output_bytes']['ckpt-last.pth'],sha256=cp,independently_hashed=True,deserialized=False),counts=dict(updates=3900,traversals=100,case_exposures=31200,drops=300,metrics=3900,resources=3902),initialization=dict(record=initial,original_common_factory_exact=True,zero_head_runtime_check_and_first_batch_delta_pass=True,full_fingerprint_comparison_to_M0='Not equal by design: H2 adds1025 zero parameters; common factory evidence and unchanged-state contract compared instead',initial_tensors_rebuilt=False),order=dict(raw_sha256=sha(D/'order_plan.json'),canonical_sha256=canonical(plan),all3900_batches_LR_BN_match=True),H2=dict(mode='AUX',head_parameters=1025,H1_enabled=False,all_scales_one=True,all_raw_used_moments_equal=True,max_log_target_recompute_error=max_t_error,max_aux_recompute_error=max_aux_error,max_loss_sum_error=max_loss_error),resources=dict(peaks=peaks,PID_warning_records=sum(x['PID_warning'] for x in resources),PID_policy='Diagnostic only; no common PID namespace ownership claim'),files=[dict(name=n,bytes=remote['output_bytes'][n],sha256=h) for n,h in [(p.removeprefix('./'),v) for p,v in remote['output_SHA256'].items()]],frozen_assets=remote['frozen_assets'],server_writes=0,new_forward=0,new_backward=0,checkpoint_loaded=False,BNCal=False,evaluation=False,limitations=['Audit checks recorded initialization evidence and bound source behavior; no initial tensors rebuilt','Checkpoint SHA256 verified from bytes; serialized tensors and embedded H2 metadata not deserialized','Native Mamba finite gradient nondeterminism accepted, not bitwise repeatability','Sampled resource/PID telemetry not hard isolation or ownership proof','Training completion and audit do not establish development accuracy or H2 benefit'])
 emit('audit_report_v1.json',report)
 print(json.dumps({k:report[k] for k in ['status','checks_passed','checkpoint','counts','resources']},indent=2))
except BaseException as exc:
 emit('analysis_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),checks_passed=len(checks),checks=checks));raise
