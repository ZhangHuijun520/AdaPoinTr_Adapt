from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/audit_RF_Requery_D_post_training_pair_v2.py').read_text(encoding='utf-8')
s=s.replace("H=R/'outputs/scq_rf_Requery_D_implementation_20261115_v1';D=H/'post_training_freeze_v2';A=H/'authorized_execution_v1'", "H=R/'outputs/scq_rf_Static_D_implementation_20261115_v1/selector_diagnostic_hotfix_v2';D=H/'post_training_freeze_v1';A=H/'authorized_execution_v2'")
s=s.replace("pending_transport_v1/payload/SCQ_RF_Requery_D_training_execution_request_v1.json", "pending_transport_v2/payload/SCQ_RF_Static_D_training_execution_request_v2.json").replace("4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed", "9d7ac459e9a969c36df67ddaee4c5c0aaac2c68b322dcf58097c54f59caa402b")
s=s.replace("pending_transport_v1/installation_mapping_v1.json", "pending_transport_v2/installation_mapping_v2.json")
start=s.index(" continuity=remote(")
end=s.index(" inv=remote('inventory_before'",start)
s=s[:start]+s[end:]
for a,b in [('authorization_v1.json','authorization_v2.json'),('runtime_v1.json','runtime_v2.json'),('launch_once_v1.sh','launch_once_v2.sh'),('attempt_claim_v1.json','attempt_claim_v2.json'),('final_local_mirror_v1.json','final_local_mirror_v2.json')]:s=s.replace(a,b)
s=s.replace("parts=g['geometry'];assert set(parts)=={'coarse','dense','Q0','Q1','Q2','delta','delta0','delta1','N0_N1_equal','neighbor_set_overlap'} and type(parts['N0_N1_equal']) is bool\n  assert len(parts['neighbor_set_overlap'])==8 and all(math.isfinite(x) and 0<=x<=1 for x in parts['neighbor_set_overlap'])\n  if parts['N0_N1_equal']:assert parts['neighbor_set_overlap']==[1.]*8", "parts=g['geometry'];assert set(parts)=={'coarse','dense','Q0','Q1','Q2','delta','delta0','delta1','N0_N1_equal'} and parts['N0_N1_equal'] is True")
s=s.replace('all3900_batches_LR_BN_losses_RF_stages_and_measured_Requery_neighbors','all3900_batches_LR_BN_losses_RF_stages_and_Static_indices').replace("'RF-Requery'", "'RF-Static'")
s=s.replace("check('exact14installed_files'", "check('exact12installed_files'").replace("check('all10payload_and3current_controls_match'", "check('all8payload_and3current_controls_match'").replace("check('before_after_all30file_hashes_stable'", "check('before_after_all28file_hashes_stable'")
s=s[:s.index(" ref=q['paired_baseline']")]+'''\n # Historical records retain their original device identity. Only selector may differ in environment.
 historical=q['historical_identity'];current=q['identity']
 check('only_three_identity_fields_changed',{k for k in current if current[k]!=historical[k]}=={'hostname','gpu_uuid','driver_version'})
 migration=q['accepted_device_migration'];migration_path=mirror[migration['path']]
 check('accepted_migration_evidence_hash',sha(migration_path)==migration['sha256'] and migration_path.stat().st_size==migration['bytes'])
 check('current_selector_bound',q['environment']['CUDA_VISIBLE_DEVICES']==current['gpu_uuid'])
 check('cross_device_qualification_explicit',q['comparison_qualification']==dict(C_pair='SAME_DEVICE_PRIMARY_MECHANISM_EVIDENCE',D_Static_vs_Requery='DEVICE_AND_DRIVER_CONFOUNDED_SUPPLEMENTARY_EVIDENCE',strict_same_device_D_pair=False,do_not_attribute_all_differences_to_requery=True))
 def bound_set(ref):
  paths={k:mirror[r['path']] for k,r in ref.items()}
  for k,p in paths.items():assert sha(p)==ref[k]['sha256'] and p.stat().st_size==ref[k]['bytes']
  return paths
 def audited_output(a,p,name):
  f=p/name;assert sha(f)==a['artifacts']['output/'+name]['sha256'] and f.stat().st_size==a['artifacts']['output/'+name]['bytes'];return f
 def pair(ref,label,RF):
  paths=bound_set(ref);a=read(paths['audit']);bq=read(paths['request']);bm=read(paths['construction']);bd=paths['construction'].parent
  expected_status='FORMAL_RF_REQUERY_D_TRAINING_PAIR_FREEZE_AUDIT_PASS' if RF else 'FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS'
  check(label+'_frozen_audit',a['status']==expected_status and all(a['checks'].values()) and a['check_count']==(43 if RF else 30) and a['identity']==historical and a['updates']==3900 and a['exposures']==31200)
  keys=['science','resources','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','pair_contract','initialization','admission']
  check(label+'_scientific_contract_identical',all(q[k]==bq[k] for k in keys))
  env=bq['environment'];check(label+'_environment_only_selector_changed',set(env)==set(q['environment']) and {k for k in env if env[k]!=q['environment'][k]}=={'CUDA_VISIBLE_DEVICES'} and env['CUDA_VISIBLE_DEVICES']==historical['gpu_uuid'])
  check(label+'_shared_factory_initial_state',model['common_initial_state_SHA256']==bm['common_initial_state_SHA256']==a['common_initial_state_SHA256'] and model['factory']['parent']==(bm['factory']['parent'] if RF else bm['factory']))
  check(label+'_order_exposures_optimizer_defaults_exact',all(sha(out/n)==sha(audited_output(a,bd,n)) for n in ['order_plan.json','exposure.json','optimizer_actual_defaults.json']))
  bmetrics=[json.loads(x) for x in audited_output(a,bd,'metrics.jsonl').read_text().splitlines()]
  check(label+'_all3900_batches_schedules_paired',len(bmetrics)==3900 and all(all(x[k]==y[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']) for x,y in zip(metrics,bmetrics)))
  bgroups=read(audited_output(a,bd,'optimizer_parameter_groups.json'))
  check(label+'_optimizer_groups_exact',(groups if RF else [r for r in groups if not r['name'].startswith('base_model.rf.')])==bgroups)
  check(label+'_same_sources_except_entry_bridge',all(q['implementation'][k]==r for k,r in bq['implementation'].items() if k not in ('entry','bridge')))
  if RF:
   bi=read(paths['initialization']);check(label+'_full_initial_parameters_buffers_exact',all(init[k]==bi[k]==q['expected_model_initialization'][k] for k in ['parameter_sha256','persistent_state_sha256','seed']))
   x=model['factory']['rf'];y=bm['factory']['rf'];check(label+'_RF_factory_only_variant_differs',set(x)==set(y) and all(x[k]==y[k] for k in x if k!='variant') and y['variant']=='RF-Requery' and x['variant']=='RF-Static')
  return sha(paths['audit'])
 pairs={label:pair(q[key],label,RF) for key,label,RF in [('paired_baseline','Sref_D',False),('paired_requery','Requery_D',True)]}
 check('expected_full_RF_initialization',all(init[k]==q['expected_model_initialization'][k] for k in ['parameter_sha256','persistent_state_sha256','seed']))
 expected={'Sref_C':('FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS',26),'Static_C':('FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',34),'Requery_C':('FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',43)}
 continuation={}
 for key,r in q['continuation_evidence'].items():
  p=mirror[r['path']];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'];a=read(p)
  assert a['status']==expected[key][0] and a['check_count']==expected[key][1] and all(a['checks'].values()) and a['identity']==historical and a['common_initial_state_SHA256']==common
  continuation[key]=dict(sha256=sha(p),status=a['status'])
  if key=='Static_C':
   source=R/'outputs/scq_rf_Static_C_implementation_20261114_v1/post_training_freeze_v1/output'
   ci=read(audited_output(a,source,'initialization.json'));cm=read(audited_output(a,source,'model_construction.json'))
   check('Static_C_same_full_initialization_and_RF_factory',all(init[k]==ci[k] for k in ['parameter_sha256','persistent_state_sha256','seed']) and model['factory']==cm['factory'])
 check('all_C_trio_evidence_hashes_and_historical_identity',set(continuation)==set(expected))
 matrix=read(pair_path);check('D_matrix_order_and_data_unchanged',all(matrix['FoldD'][k]==q[k] for k in ['QC','order_plan','data_root']) and matrix['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'])
 check('run_identity_current_and_historical_disclosed',identity['execution_identity']==current and identity['historical_pair_identity']==historical and identity['cross_device_confounded_D_comparison'] is True)
 summary=dict(Static_N0_N1_equal_steps=sum(g['geometry']['N0_N1_equal'] for g in geo),RF_second_residual_mean=sum(sum(g['geometry']['delta1']['mean_norm']) for g in geo)/(3900*8),max_query_delta_norm=max(max(g['geometry']['delta']['max_norm']) for g in geo),units='D-only normalized; descriptive only, no efficacy conclusion')
 result=dict(status='FORMAL_RF_STATIC_D_TRAINING_PAIR_FREEZE_AUDIT_PASS',variant='RF-Static',fold='D',identity=current,historical_identity=historical,comparison_qualification=q['comparison_qualification'],request_sha256=RH,updates=3900,traversals=100,exposures=31200,drops=300,order_sha256=canonical,checkpoint=checkpoint,initialization=init,common_initial_state_SHA256=common,checks=checks,check_count=len(checks),counts=counts,peaks={k:max(r[k] for r in resources) for k in ['RSS','peak_allocated','peak_reserved','device_MiB','elapsed_seconds']},paired_audits=pairs,C_continuation_audits=continuation,delta_summary=summary,artifacts=inv['files'],BNCal=False,evaluation=False,resume=False,operations=dict(new_forward=0,new_backward=0,server_writes=0,checkpoint_loaded=False,checkpoint_downloaded=False),limitations=['D Static comparison is GPU/driver confounded supplementary evidence; C same-device pair remains primary mechanism evidence.','Checkpoint streamed twice without deserialization; initialization fingerprints verified against frozen records, not reconstructed tensors.','Static neighbor reuse verified from logged summaries and bound implementation, not independently recomputed KNN.','Resource telemetry is sampled; no PID namespace ownership guarantee or per-row free-disk telemetry.','No scientific efficacy conclusion from training logs.'])
 emit('freeze_verification_v1.json',result);print(json.dumps(dict(status=result['status'],checks=len(checks),checkpoint=checkpoint,updates=3900,peaks=result['peaks'])))
except BaseException as exc:
 emit('audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),new_forward=0));raise
'''
ast.parse(s)
p=R/'local_tools/audit_RF_Static_D_post_training_pair_v1.py'
with p.open('x',encoding='utf-8') as f:f.write(s)
print(p)
