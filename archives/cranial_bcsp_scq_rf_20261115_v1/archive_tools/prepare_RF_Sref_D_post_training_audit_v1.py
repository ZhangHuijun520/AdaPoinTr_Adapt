"""Finite version of the proven S-ref audit for frozen Fold D bindings."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/audit_RF_Sref_C_post_training_v1.py').read_text(encoding='utf-8')
changes=[('RF S-ref_C freeze','RF S-ref_D freeze'),('outputs/scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3','outputs/scq_rf_Sref_D_implementation_20261114_v1'),("A=H/'authorized_execution_v3'","A=H/'authorized_execution_v1'"),('pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json','pending_transport_v1/payload/SCQ_RF_Sref_D_training_execution_request_v1.json'),('6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88','888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'),('pending_transport_v3/installation_mapping_v3.json','pending_transport_v1/installation_mapping_v1.json'),('authorization_v3.json','authorization_v1.json'),('runtime_v3.json','runtime_v1.json'),('launch_once_v3.sh','launch_once_v1.sh'),('attempt_claim_v3.json','attempt_claim_v1.json'),('exact11installed_files','exact15installed_files'),('all7payload_and3current_controls_match','all11payload_and3current_controls_match'),('before_after_all27file_hashes_stable','before_after_all31file_hashes_stable'),("['folds']['C']","['folds']['D']"),("identity['fold']=='C'","identity['fold']=='D'"),("q['fold']=='C'","q['fold']=='D'"),("variant='S',fold='C'","variant='S',fold='D'"),('local_mirror_v3.json','final_local_mirror_v1.json')]
for a,b in changes:
 assert a in s,a
 s=s.replace(a,b)
anchor=" delta_summary=dict("
extra=''' pair=read(pair_path)
 check('versioned_matrix_exact_D_bindings',pair['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'] and all(pair['FoldD'][k]==q[k] for k in ['QC','order_plan','data_root']) and pair['resources']==q['resources'] and pair['identity']==q['identity'])
 check('D_canonical_order_matches_frozen_preparation',canonical=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838')
 continuation={}
 expected={'Sref_C':('FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS',26),'Static_C':('FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',34),'Requery_C':('FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',43)}
 assert set(q['continuation_evidence'])==set(expected)
 for key,r in q['continuation_evidence'].items():
  p=mirror[r['path']];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'];a=read(p)
  assert a['status']==expected[key][0] and a['check_count']==expected[key][1] and all(a['checks'].values()) and a['fold']=='C' and a['identity']==q['identity'] and a['common_initial_state_SHA256']==common
  continuation[key]=dict(sha256=sha(p),status=a['status'])
 check('three_C_arms_frozen_continuation_evidence',True)
 c_init=read(mirror[q['continuation_evidence']['Sref_C']['path']])['initialization']
 check('same_seed0_full_initial_parameters_and_buffers_as_Sref_C',all(init[k]==c_init[k] for k in ['parameter_sha256','persistent_state_sha256','seed']))
'''
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor)
s=s.replace('first_Sref_no_old_baseline_reuse','Sref_D_scratch_no_checkpoint_warmstart')
s=s.replace("paired_baseline_audit_sha256=None,delta_summary=delta_summary", "paired_baseline_audit_sha256=None,C_continuation_audits=continuation,delta_summary=delta_summary")
ast.parse(s);compile(s,'Sref_D_readonly_audit','exec')
p=R/'local_tools/audit_RF_Sref_D_post_training_v1.py'
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('SREF_D_READONLY_TRAINING_AUDIT_STATIC_PASS')
