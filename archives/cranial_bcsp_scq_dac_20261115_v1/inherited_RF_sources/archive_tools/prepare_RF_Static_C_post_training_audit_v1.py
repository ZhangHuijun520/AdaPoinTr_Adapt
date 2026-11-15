"""Adapt the frozen read-only S-ref audit to Static geometry and paired evidence."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/audit_RF_Sref_C_post_training_v1.py').read_text(encoding='utf-8')
s=s.replace('outputs/scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3','outputs/scq_rf_Static_C_implementation_20261114_v1')
s=s.replace("A=H/'authorized_execution_v3'","A=H/'authorized_execution_v1'")
s=s.replace('pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json','pending_transport_v1/payload/SCQ_RF_Static_C_training_execution_request_v1.json')
s=s.replace('6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88','a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f')
s=s.replace('pending_transport_v3/installation_mapping_v3.json','pending_transport_v1/installation_mapping_v1.json')
for old,new in [('authorization_v3.json','authorization_v1.json'),('runtime_v3.json','runtime_v1.json'),('launch_once_v3.sh','launch_once_v1.sh'),('attempt_claim_v3.json','attempt_claim_v1.json'),('exact11installed_files','exact12installed_files'),('all7payload_and3current_controls_match','all8payload_and3current_controls_match'),('before_after_all27file_hashes_stable','before_after_all28file_hashes_stable'),('local_mirror_v3.json','final_local_mirror_v1.json')]:s=s.replace(old,new)
s=s.replace("assert set(parts)=={'coarse','dense','Q0','delta'}","assert set(parts)=={'coarse','dense','Q0','Q1','Q2','delta','delta0','delta1','N0_N1_equal'} and parts['N0_N1_equal'] is True")
start=s.index("  raw=parts['Q0'];delta=");end=s.index("  ls=g['loss_components']",start)
s=s[:start]+'''  for name in ['Q0','Q1','Q2']:
   t=parts[name];assert set(t)=={'centroid','radius'} and len(t['centroid'])==len(t['radius'])==8
   assert all(len(c)==3 and all(math.isfinite(x) for x in c) for c in t['centroid']) and all(math.isfinite(x) and x>=0 for x in t['radius'])
  assert parts['Q2']=={k:parts['coarse'][k] for k in ['centroid','radius']}
  for dname,rawname,usedname in [('delta','Q0','Q2'),('delta0','Q0','Q1'),('delta1','Q1','Q2')]:
   delta=parts[dname];assert set(delta)=={'mean_norm','max_norm','centroid'} and all(len(delta[k])==8 for k in delta)
   for rawc,usedc,dc,mean_norm,max_norm in zip(parts[rawname]['centroid'],parts[usedname]['centroid'],delta['centroid'],delta['mean_norm'],delta['max_norm']):
    assert len(dc)==3 and all(math.isfinite(x) for x in dc+[mean_norm,max_norm]) and 0<=mean_norm<=max_norm+1e-6
    assert math.sqrt(sum(x*x for x in dc))<=mean_norm+1e-5 and all(math.isclose(u-r,d,rel_tol=2e-4,abs_tol=2e-6) for u,r,d in zip(usedc,rawc,dc))
  for d,d0,d1 in zip(parts['delta']['centroid'],parts['delta0']['centroid'],parts['delta1']['centroid']):
   assert all(math.isclose(x,y+z,rel_tol=2e-4,abs_tol=2e-6) for x,y,z in zip(d,d0,d1))
  assert all(t<=a+b+1e-5 for t,a,b in zip(parts['delta']['mean_norm'],parts['delta0']['mean_norm'],parts['delta1']['mean_norm']))
  if i==0:assert parts['Q1']==parts['Q2'] and parts['delta1']['max_norm']==[0.]*8
'''+s[end:]
s=s.replace('all_actual_batches_LR_BN_loss_geometry_and_S_delta_identity','all3900_batches_LR_BN_losses_RF_stages_and_Static_indices')
start=s.index(" check('native_common_initialization_matches'");end=s.index(" for r in groups:",start)
s=s[:start]+''' check('native_common_initialization_matches',model['common_initial_state_SHA256']==common and model['factory']['parent']['parent']['artificial_fixture'] is False and model['factory']['parent']['scq']['variant']=='S' and model['factory']['rf']['variant']=='RF-Static' and model['factory']['rf']['additional_parameters']==231171 and model['factory']['rf']['total_parameters']==40827847 and model['factory']['rf']['initialization_sha256']==q['rf_initialization']['sha256'])
 check('both_frozen_head_initializers',model['factory']['parent']['scq']['initialization_sha256']==q['initialization']['sha256'] and model['factory']['rf']['common_state_preserved'] and model['factory']['rf']['CPU_RNG_preserved'])
 expected_new={'base_model.scq.W1.weight':.0005,'base_model.scq.W2.weight':.0005,'base_model.scq.W1.bias':0.,'base_model.scq.W2.bias':0.,'base_model.rf.V1.weight':.0005,'base_model.rf.V2.weight':.0005,'base_model.rf.V1.bias':0.,'base_model.rf.V2.bias':0.}
 check('all8_SCQ_RF_parameter_groups',model['new_optimizer_groups']==expected_new)
 groups=readout('optimizer_parameter_groups.json');defaults=readout('optimizer_actual_defaults.json');check('unique419parameters_total',len(groups)==len({r['name'] for r in groups})==419 and sum(math.prod(r['shape']) for r in groups)==40827847 and len([r for r in groups if r['name'].startswith('base_model.rf.')])==4)
'''+s[end:]
s=s.replace("identity['variant']=='S'","identity['variant']=='RF-Static'").replace("identity['arm']=='S-ref'","identity['arm']=='RF-Static'").replace("model['arm']=='S-ref'","model['arm']=='RF-Static'")
old=" check('first_Sref_no_old_baseline_reuse',q['paired_baseline'] is None and q['arm']=='S-ref' and q['fold']=='C')"
assert old in s
pair=''' ref=q['paired_baseline'];paths={k:mirror[r['path']] for k,r in ref.items()}
 for key,p in paths.items():assert sha(p)==ref[key]['sha256'] and p.stat().st_size==ref[key]['bytes']
 ba=read(paths['audit']);bm=read(paths['construction']);bq=read(paths['request']);bD=paths['construction'].parent
 check('formal_Sref_reference_hashes_and_counts',ba['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and ba['check_count']==26 and all(ba['checks'].values()) and ba['identity']==q['identity'] and ba['updates']==3900 and ba['exposures']==31200)
 check('paired_science_resource_data_order_identical',all(q[k]==bq[k] for k in ['science','identity','resources','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','admission']))
 check('paired_full_S_state_and_factory_preserved',model['common_initial_state_SHA256']==bm['common_initial_state_SHA256']==ba['common_initial_state_SHA256'] and model['factory']['parent']==bm['factory'])
 check('paired_order_exposure_optimizer_defaults_identical',all(sha(out/n)==sha(bD/n) for n in ['order_plan.json','exposure.json','optimizer_actual_defaults.json']))
 bmetrics=[json.loads(x) for x in (bD/'metrics.jsonl').read_text().splitlines()];bgroups=read(bD/'optimizer_parameter_groups.json')
 for name in ['metrics.jsonl','optimizer_parameter_groups.json']:assert sha(bD/name)==ba['artifacts']['output/'+name]['sha256']
 check('paired_all3900_actual_batches_and_schedules',len(bmetrics)==3900 and all(all(x[k]==y[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']) for x,y in zip(metrics,bmetrics)))
 check('paired_all_shared_optimizer_groups_exact',[r for r in groups if not r['name'].startswith('base_model.rf.')]==bgroups)
 check('same_frozen_shared_sources_except_entry_bridge',all(q['implementation'][k]==r for k,r in bq['implementation'].items() if k not in ('entry','bridge')))
'''
s=s.replace(old,pair)
s=s.replace("status='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS',variant='S'","status='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',variant='RF-Static'")
s=s.replace("arm='S-ref',paired_baseline_audit_sha256=None","arm='RF-Static',paired_baseline_audit_sha256=sha(paths['audit'])")
s=s.replace("units='D-only normalized, descriptive logging only; no accuracy conclusion')","units='D-only normalized, descriptive logging only; no accuracy conclusion',RF_second_residual_mean=sum(sum(r['geometry']['delta1']['mean_norm']) for r in geo)/(3900*8),Static_N0_N1_equal_steps=sum(r['geometry']['N0_N1_equal'] for r in geo))")
ast.parse(s);compile(s,'Static_C_audit','exec')
p=R/'local_tools/audit_RF_Static_C_post_training_pair_v1.py'
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('STATIC_C_READONLY_POST_TRAINING_PAIR_AUDIT_STATIC_PASS')
