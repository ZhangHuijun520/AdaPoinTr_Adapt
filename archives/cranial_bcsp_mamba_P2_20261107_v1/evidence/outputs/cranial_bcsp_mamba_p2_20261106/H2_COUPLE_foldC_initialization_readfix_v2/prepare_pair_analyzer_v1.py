"""Reuse exact lifecycle checks; add COUPLE formula and frozen AUX pairing checks."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent;A=S.parent/'H2_AUX_foldC_training_preparation_v1'
t=(A/'analyze_post_training_audit_v1.py').read_text(encoding='utf-8')
def once(a,b):
 global t
 assert t.count(a)==1,(a,t.count(a));t=t.replace(a,b)
t=t.replace("P=S/'first_FoldC_request_v1/transport_payload'","P=S/'final_pending_request_v2/transport_payload';A=S.parent/'H2_AUX_foldC_training_preparation_v1';AP=A/'first_FoldC_request_v1/transport_payload';AD=A/'post_training_freeze_audit_v1/downloads'")
t=t.replace('0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517','da96af70b5e3018c4a64c13815348f70f61575b3c455139fab155f2bd801fd90').replace('H2_AUX_foldC_seed0_training_execution_request_v1.json','H2_COUPLE_foldC_seed0_training_execution_request_v2.json').replace('REMOTE_H2_AUX_POST_TRAINING_FILES_PASS','REMOTE_H2_COUPLE_POST_TRAINING_PAIR_FILES_PASS').replace("C=S/'authorized_execution_v1/readback'","C=S/'authorized_execution_v2/readback'")
t=t.replace("S/'server_readiness_v1/metadata/M0_construction.json'","A/'server_readiness_v1/metadata/M0_construction.json'").replace("P/'frozen_M0_C_post_training_audit_v1.json'","AP/'frozen_M0_C_post_training_audit_v1.json'").replace('static_H2_AUX_training_config_v1.json','static_H2_COUPLE_training_config_v1.json')
t=t.replace("x['H2_mode']=='AUX'","x['H2_mode']=='COUPLE'").replace("factory['H2_mode']=='AUX'","factory['H2_mode']=='COUPLE'")
old="   assert x['H2_scale']==[1.]*8 and x['H2_centroid_raw']==x['H2_centroid_used'] and x['H2_radius_raw']==x['H2_radius_used']"
new="""   assert len(x['H2_scale'])==8 and len(x['H2_delta'])==8
   for delta,scale,rq,ru,mq,mu in zip(x['H2_delta'],x['H2_scale'],x['H2_radius_raw'],x['H2_radius_used'],x['H2_centroid_raw'],x['H2_centroid_used']):
    expected_scale=math.exp(math.log(1.25)*math.tanh(delta/math.log(1.25)))
    assert .8-1e-6<=scale<=1.25+1e-6 and close(scale,expected_scale) and close(ru,rq*scale)
    assert all(close(a,b) for a,b in zip(mq,mu))
    coupling_errors['scale']=max(coupling_errors['scale'],abs(scale-expected_scale));coupling_errors['radius']=max(coupling_errors['radius'],abs(ru-rq*scale));coupling_errors['center']=max(coupling_errors['center'],max(abs(a-b) for a,b in zip(mq,mu)))"""
once(old,new)
once(" cases,sources,drops=collections.Counter(),collections.Counter(),collections.Counter();max_t_error=max_aux_error=max_loss_error=0"," cases,sources,drops=collections.Counter(),collections.Counter(),collections.Counter();max_t_error=max_aux_error=max_loss_error=0;coupling_errors=dict(scale=0,radius=0,center=0)")
t=t.replace("check('H2_AUX_all_steps_raw_equals_used_scale_one',True)","check('COUPLE_all_steps_scale_formula_bounds_center_and_radius',True)")
anchor=" peaks={k:max(x[k] for x in resources)"
extra=''' # Reconfirm the archived AUX evidence locally against its freshly rehashed remote files.
 auxaudit=read(A/'post_training_freeze_audit_v1/audit_report_v1.json');auxq=read(AP/'H2_AUX_foldC_seed0_training_execution_request_v1.json')
 check('frozen_AUX_audit_request_and_pairing_pins',sha(A/'post_training_freeze_audit_v1/audit_report_v1.json')==q['aux_pairing']['audit']['sha256']=='580a0b195c5730e56f260e357e135966e2ab954b9cef7582ff7298b35d33ee1c' and sha(AP/'H2_AUX_foldC_seed0_training_execution_request_v1.json')==q['aux_pairing']['request']['sha256']==auxaudit['request_sha256'])
 for r in auxaudit['files']:
  path=auxq['output']+'/'+r['name'];assert frozen[path]['sha256']==r['sha256']
  if r['name']!='ckpt-last.pth':assert sha(AD/r['name'])==r['sha256']
 check('all_frozen_AUX_outputs_including_checkpoint_freshly_rehashed',True)
 check('AUX_COUPLE_full_initial_parameter_persistent_and_order_fingerprints_identical',initial==read(AD/'initialization.json')==auxaudit['initialization']['record'])
 check('dispatch_recorded_exact_AUX_initialization_gate',construction['AUX_initialization_exact_match'] is True and construction['AUX_initialization_sha256']==q['aux_pairing']['initialization']['sha256']==sha(AD/'initialization.json'))
 check('AUX_COUPLE_optimizer_groups_defaults_exposure_and_order_identical',all(read(D/n)==read(AD/n) for n in ['optimizer_actual_defaults.json','optimizer_parameter_groups.json','exposure.json','order_plan.json']))
 oldrows=[json.loads(x) for x in (AD/'metrics.jsonl').read_text().splitlines()];keys=['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed'];assert len(oldrows)==3900
 check('AUX_COUPLE_all3900_actual_batch_and_schedule_records_identical',all(all(x[k]==y[k] for k in keys) for x,y in zip(rows,oldrows)))
 oldfactory=read(AD/'model_construction.json')['factory'];normalized=dict(factory,H2_mode='AUX');check('AUX_COUPLE_factory_evidence_only_mode_differs',normalized==oldfactory)
 auxstatic=read(AP/'static_H2_AUX_training_config_v1.json');static=read(P/'static_H2_COUPLE_training_config_v1.json');normalized_static=dict(static,H2=dict(static['H2'],mode='AUX'))
 check('AUX_COUPLE_scientific_static_config_only_mode_differs',normalized_static==auxstatic and all(q[k]==auxq[k] for k in ['identity','environment','QC','order_plan','data_root','model_root','initialization_reference','numeric_policy','numeric_protocol','pair_contract','dependencies','n_input','n_output']))
 check('first_batch_zero_delta_neutral_scale_and_nonzero_coupling_later',rows[0]['H2_scale']==[1.]*8 and rows[0]['H2_delta']==[0.]*8 and any(abs(v-1)>1e-6 for x in rows[1:] for v in x['H2_scale']))
'''
assert t.count(anchor)==1;t=t.replace(anchor,extra+anchor)
t=t.replace("status='FORMAL_H2_AUX_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS'","status='FORMAL_H2_COUPLE_FOLDC_POST_TRAINING_AND_AUX_PAIR_FREEZE_AUDIT_PASS'")
t=t.replace("H2=dict(mode='AUX',head_parameters=1025,H1_enabled=False,all_scales_one=True,all_raw_used_moments_equal=True,","H2=dict(mode='COUPLE',head_parameters=1025,H1_enabled=False,all_scale_formulas_and_bounds_pass=True,all_coarse_centroids_preserved=True,coupling_roundoff_errors=coupling_errors,")
once(" emit('audit_report_v1.json',report)"," report['AUX_pairing']=dict(frozen_AUX_audit_sha256=sha(A/'post_training_freeze_audit_v1/audit_report_v1.json'),AUX_checkpoint_rehashed=auxaudit['checkpoint'],full_initialization_exact=True,all3900_actual_order_and_schedules_identical=True,optimizer_groups_defaults_identical=True,training_losses_and_gradients_not_required_to_match=True,scientific_config_only_mode_differs=True)\n report['limitations'].append('Coupling formulas checked from logged moments; full raw/used point tensors and gradients not recomputed; bound adapter plus prior CPU/CUDA consumer checks supply path evidence')\n emit('audit_report_v1.json',report)")
ast.parse(t)
with (S/'analyze_post_training_pair_audit_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(t)
print('OFFLINE_PAIR_ANALYZER_STATIC_PASS')
