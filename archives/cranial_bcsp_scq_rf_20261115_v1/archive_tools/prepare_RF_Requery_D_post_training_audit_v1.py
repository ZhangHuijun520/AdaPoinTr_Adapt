"""Version the read-only RF audit for D; C initial-state provenance is not a C order gate."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/audit_RF_Requery_C_post_training_pair_v1.py').read_text(encoding='utf-8')
changes=[('scq_rf_Requery_C_implementation_20261114_v1','scq_rf_Requery_D_implementation_20261115_v1'),('SCQ_RF_Requery_C_training_execution_request_v1.json','SCQ_RF_Requery_D_training_execution_request_v1.json'),('27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497','4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed'),('exact13installed_files','exact14installed_files'),('all9payload_and3current_controls_match','all10payload_and3current_controls_match'),('before_after_all29file_hashes_stable','before_after_all30file_hashes_stable'),("['folds']['C']","['folds']['D']"),("identity['fold']=='C'","identity['fold']=='D'"),("ba['check_count']==26","ba['check_count']==30"),("variant='RF-Requery',fold='C'","variant='RF-Requery',fold='D'"),('FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS','FORMAL_RF_REQUERY_D_TRAINING_PAIR_FREEZE_AUDIT_PASS')]
for a,b in changes:
 assert a in s,a
 s=s.replace(a,b)
start=s.index(" sr=q['paired_static']");end=s.index(' delta_summary=dict(',start)
block=''' ir=q['initialization_reference'];ip={k:mirror[r['path']] for k,r in ir.items()}
 for key,p in ip.items():assert sha(p)==ir[key]['sha256'] and p.stat().st_size==ir[key]['bytes']
 ia=read(ip['audit']);im=read(ip['construction']);iq=read(ip['request']);ii=read(ip['initialization'])
 check('frozen_RF_initial_model_provenance',ia['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and ia['fold']=='C' and ia['check_count']==34 and all(ia['checks'].values()) and ia['identity']==q['identity'] and ia['common_initial_state_SHA256']==common)
 check('RF_model_parameters_buffers_match_frozen_initial_reference',{k:init[k] for k in ['parameter_sha256','persistent_state_sha256','seed']}=={k:ii[k] for k in ['parameter_sha256','persistent_state_sha256','seed']}==q['expected_model_initialization'])
 check('D_order_is_independent_of_C_initialization_provenance',init['order_sha256']==canonical=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838' and init['order_sha256']!=ii['order_sha256'])
 check('same_RF_sources_and_initializer_identity',all(q['implementation'][k]==r for k,r in iq['implementation'].items() if k not in ('entry','bridge')) and q['rf_initialization']==iq['rf_initialization'] and model['factory']['parent']==im['factory']['parent'])
 re=model['factory']['rf'];ie=im['factory']['rf'];check('same_RF_factory_contract_except_arm',set(re)==set(ie) and all(re[k]==ie[k] for k in re if k!='variant') and ie['variant']=='RF-Static')
 matrix=read(pair_path)
 check('D_matrix_and_frozen_order',all(matrix['FoldD'][k]==q[k] for k in ['QC','order_plan','data_root']) and matrix['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'])
 expected={'Sref_C':('FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS',26),'Static_C':('FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',34),'Requery_C':('FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',43)}
 assert set(q['continuation_evidence'])==set(expected)
 continuation={}
 for key,r in q['continuation_evidence'].items():
  p=mirror[r['path']];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'];a=read(p)
  assert a['status']==expected[key][0] and a['check_count']==expected[key][1] and all(a['checks'].values()) and a['identity']==q['identity'] and a['common_initial_state_SHA256']==common
  continuation[key]=dict(sha256=sha(p),status=a['status'])
 check('C_trio_continuation_evidence_exact',True)
 check('no_nonexistent_Static_D_prerequisite','paired_static' not in q and q['paired_baseline']['request']['sha256']=='888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d')
'''
s=s[:start]+block+s[end:]
s=s.replace("paired_Static_audit_sha256=sha(sp['audit'])","RF_initialization_reference_audit_sha256=sha(ip['audit']),C_continuation_audits=continuation")
s=s.replace("'Common initialization matches hash recorded by bound factory; audit does not independently reconstruct full tensors.'", "'Initialization hashes match frozen model provenance; no tensor reconstruction or checkpoint deserialization. Same-fold pairing is Sref_D; Static_D has not run.'")
ast.parse(s);compile(s,'Requery_D_readonly_audit','exec')
p=R/'local_tools/audit_RF_Requery_D_post_training_pair_v1.py'
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('REQUERY_D_READONLY_TRAINING_PAIR_AUDIT_STATIC_PASS')
