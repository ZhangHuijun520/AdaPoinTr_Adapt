"""Finite read-only Requery freeze and exact pairing against both frozen references."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/audit_RF_Static_C_post_training_pair_v1.py').read_text(encoding='utf-8')
s=s.replace('scq_rf_Static_C_implementation_20261114_v1','scq_rf_Requery_C_implementation_20261114_v1')
s=s.replace('SCQ_RF_Static_C_training_execution_request_v1.json','SCQ_RF_Requery_C_training_execution_request_v1.json')
s=s.replace('a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f','27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497')
s=s.replace('exact12installed_files','exact13installed_files').replace('all8payload_and3current_controls_match','all9payload_and3current_controls_match').replace('before_after_all28file_hashes_stable','before_after_all29file_hashes_stable')
s=s.replace("'delta1','N0_N1_equal'} and parts['N0_N1_equal'] is True", "'delta1','N0_N1_equal','neighbor_set_overlap'} and type(parts['N0_N1_equal']) is bool\n  assert len(parts['neighbor_set_overlap'])==8 and all(math.isfinite(x) and 0<=x<=1 for x in parts['neighbor_set_overlap'])\n  if parts['N0_N1_equal']:assert parts['neighbor_set_overlap']==[1.]*8")
s=s.replace('all3900_batches_LR_BN_losses_RF_stages_and_Static_indices','all3900_batches_LR_BN_losses_RF_stages_and_measured_Requery_neighbors')
s=s.replace("model['factory']['rf']['variant']=='RF-Static'", "model['factory']['rf']['variant']=='RF-Requery'")
s=s.replace("identity['variant']=='RF-Static'","identity['variant']=='RF-Requery'").replace("identity['arm']=='RF-Static'","identity['arm']=='RF-Requery'").replace("model['arm']=='RF-Static'","model['arm']=='RF-Requery'")
anchor=" delta_summary=dict("
assert s.count(anchor)==1
extra=''' sr=q['paired_static'];sp={k:mirror[r['path']] for k,r in sr.items()}
 for key,p in sp.items():assert sha(p)==sr[key]['sha256'] and p.stat().st_size==sr[key]['bytes']
 sa=read(sp['audit']);sm=read(sp['construction']);sq=read(sp['request']);sD=sp['construction'].parent
 check('formal_Static_reference_hashes_and_counts',sa['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and sa['check_count']==34 and all(sa['checks'].values()) and sa['identity']==q['identity'] and (sa['updates'],sa['traversals'],sa['exposures'],sa['drops'])==(3900,100,31200,300))
 check('Static_same_Sref_frozen_reference',sa['paired_baseline_audit_sha256']==sha(paths['audit']))
 check('Static_science_resources_data_both_initializers_identical',all(q[k]==sq[k] for k in ['science','identity','resources','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','rf_initialization','admission']))
 check('exact_full_Static_initial_parameters_and_buffers',init==read(sp['initialization'])==sa['initialization']==q['expected_full_initialization'])
 check('Static_same_full_common_S_initial_state',model['common_initial_state_SHA256']==sm['common_initial_state_SHA256']==sa['common_initial_state_SHA256']==common and model['factory']['parent']==sm['factory']['parent'])
 rf_evidence=model['factory']['rf'];static_rf=sm['factory']['rf']
 check('same_RF_factory_contract_except_arm',set(rf_evidence)==set(static_rf) and all(rf_evidence[k]==static_rf[k] for k in rf_evidence if k!='variant') and static_rf['variant']=='RF-Static')
 for name in ['order_plan.json','exposure.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','metrics.jsonl']:
  assert sha(sD/name)==sa['artifacts']['output/'+name]['sha256']
 check('Static_identical_order_exposure_defaults_all419groups',all(sha(out/n)==sha(sD/n) for n in ['order_plan.json','exposure.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json']))
 static_metrics=[json.loads(x) for x in (sD/'metrics.jsonl').read_text().splitlines()]
 check('Static_all3900_actual_batches_and_schedules',len(static_metrics)==3900 and all(all(x[k]==y[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']) for x,y in zip(metrics,static_metrics)))
 check('Static_frozen_sources_identical_except_entry_bridge',all(q['implementation'][k]==r for k,r in sq['implementation'].items() if k not in ('entry','bridge')))
'''
s=s.replace(anchor,extra+anchor)
s=s.replace('Static_N0_N1_equal_steps=', 'Requery_N0_N1_equal_steps=')
s=s.replace("for r in geo))\n result=dict", "for r in geo),mean_neighbor_set_overlap=sum(sum(r['geometry']['neighbor_set_overlap']) for r in geo)/(3900*8),minimum_case_neighbor_set_overlap=min(min(r['geometry']['neighbor_set_overlap']) for r in geo))\n result=dict")
s=s.replace("status='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',variant='RF-Static'", "status='FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',variant='RF-Requery'")
s=s.replace("arm='RF-Static',paired_baseline_audit_sha256=sha(paths['audit'])", "arm='RF-Requery',paired_baseline_audit_sha256=sha(paths['audit']),paired_Static_audit_sha256=sha(sp['audit'])")
s=s.replace("'No scientific efficacy inference from training loss.'", "'No scientific efficacy inference from training loss.','Neighbor equality and overlap are recorded summaries, not independently recomputed KNN from full tensors in this read-only audit.'")
ast.parse(s);compile(s,'Requery_C_readonly_audit','exec')
p=R/'local_tools/audit_RF_Requery_C_post_training_pair_v1.py'
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('REQUERY_C_READONLY_POST_TRAINING_PAIR_AUDIT_STATIC_PASS')
