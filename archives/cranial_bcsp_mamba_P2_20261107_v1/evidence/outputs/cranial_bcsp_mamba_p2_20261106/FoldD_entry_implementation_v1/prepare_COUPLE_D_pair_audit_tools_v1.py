"""Narrow read-only D pair audit; reuse established exact lifecycle/formula checks."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent;C=S.parent/'H2_COUPLE_foldC_initialization_readfix_v2'
oldqh='efba40fdc78db788798ba326d9a393c5e0cac48189bb507a8ec4e9fe1d5f2db9';qh='be3988719fce8860729c80daaa1dcd634000b50c5378605fb6fe377c511e6718'
collector=(S/'collect_AUX_D_post_training_audit_v1.py').read_text(encoding='utf-8').replace(oldqh,qh).replace("F=S/'post_training_freeze_audit_v1'","F=S/'COUPLE_D_post_training_pair_freeze_audit_v1'").replace('AUX_D_pending_request_v1','COUPLE_D_pending_request_v1').replace('H2_AUX_foldD_seed0_training_execution_request_v1.json','H2_COUPLE_foldD_seed0_training_execution_request_v1.json').replace("install=PurePosixPath(q['implementation']['entry']['path']).parent","install=PurePosixPath(q['launch_contract']['request_path']).parent").replace("C=S/'authorized_execution_v1/readback'","C=S/'COUPLE_D_authorized_execution_v1/readback'")
a="ready=json.loads((P/'FoldD_readiness_snapshot_v1.json').read_bytes())";b="ready=json.loads((S/'AUX_D_pending_request_v1/transport_payload/FoldD_readiness_snapshot_v1.json').read_bytes())";assert collector.count(a)==1;collector=collector.replace(a,b)
extra='''# Rehash frozen AUX_D outputs and installed evidence to verify the pair remains intact.
AP=S/'AUX_D_pending_request_v1/transport_payload'
aq=json.loads((AP/'H2_AUX_foldD_seed0_training_execution_request_v1.json').read_bytes())
af=S/'post_training_freeze_audit_v1/audit_report_v1.json'
assert hashlib.sha256(af.read_bytes()).hexdigest()=='6809ed3590807458efe3b36f4964436e03efbd27aa9d6584a56199fc80788e7d'
audit=json.loads(af.read_bytes());assert audit['status']=='FORMAL_H2_AUX_FOLDD_POST_TRAINING_FREEZE_AUDIT_PASS'
for r in audit['files']:add(dict(path=str(PurePosixPath(aq['output'])/r['name']),bytes=r['bytes'],sha256=r['sha256']))
for r in json.loads((S/'post_training_freeze_audit_v1/remote_readonly_receipt_v1.json').read_bytes())['frozen_asset_records']:add(r)
for r in q['aux_pairing'].values():add(r)
'''
assert collector.count('def emit(n,v):')==1;collector=collector.replace('def emit(n,v):',extra+'def emit(n,v):').replace('REMOTE_H2_AUX_POST_TRAINING_FILES_PASS','REMOTE_H2_COUPLE_D_POST_TRAINING_PAIR_FILES_PASS')
analyzer=(C/'analyze_post_training_pair_audit_v2.py').read_text(encoding='utf-8')
analyzer=analyzer.replace('da96af70b5e3018c4a64c13815348f70f61575b3c455139fab155f2bd801fd90',qh).replace("F=S/'post_training_freeze_audit_v1'","F=S/'COUPLE_D_post_training_pair_freeze_audit_v1'").replace("P=S/'final_pending_request_v2/transport_payload';A=S.parent/'H2_AUX_foldC_training_preparation_v1';AP=A/'first_FoldC_request_v1/transport_payload'","P=S/'COUPLE_D_pending_request_v1/transport_payload';A=S;AP=A/'AUX_D_pending_request_v1/transport_payload'")
analyzer=analyzer.replace('H2_COUPLE_foldC_seed0_training_execution_request_v2.json','H2_COUPLE_foldD_seed0_training_execution_request_v1.json').replace('H2_AUX_foldC_seed0_training_execution_request_v1.json','H2_AUX_foldD_seed0_training_execution_request_v1.json').replace('REMOTE_H2_COUPLE_POST_TRAINING_PAIR_FILES_PASS','REMOTE_H2_COUPLE_D_POST_TRAINING_PAIR_FILES_PASS').replace("C=S/'authorized_execution_v2/readback'","C=S/'COUPLE_D_authorized_execution_v1/readback'")
for a,b in [('H2_authorization_v1.json','COUPLE_D_authorization_v1.json'),('H2_runtime_v1.json','COUPLE_D_runtime_v1.json'),('single_attempt_claim_v1.json','COUPLE_D_single_attempt_claim_v1.json')]:analyzer=analyzer.replace(a,b)
analyzer=analyzer.replace("R/'outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/shared_order_foldC_seed0_v1.json'","R/'outputs/cranial_bcsp_mamba_p1_20261104/FoldD_pair_preparation_20261106_v1/shared_order_foldD_seed0_v1.json'").replace("['folds']['C']","['folds']['D']").replace("identity['fold']=='C'","identity['fold']=='D'").replace("A/'server_readiness_v1/metadata/M0_construction.json'","S.parent/'H2_AUX_foldC_training_preparation_v1/server_readiness_v1/metadata/M0_construction.json'").replace('frozen_M0_C_post_training_audit_v1.json','frozen_M0_D_post_training_audit_v1.json').replace('static_H2_AUX_training_config_v1.json','static_H2_AUX_foldD_training_config_v1.json').replace('static_H2_COUPLE_training_config_v1.json','static_H2_COUPLE_foldD_training_config_v1.json').replace('580a0b195c5730e56f260e357e135966e2ab954b9cef7582ff7298b35d33ee1c','6809ed3590807458efe3b36f4964436e03efbd27aa9d6584a56199fc80788e7d').replace('FORMAL_H2_COUPLE_FOLDC_POST_TRAINING_AND_AUX_PAIR_FREEZE_AUDIT_PASS','FORMAL_H2_COUPLE_FOLDD_POST_TRAINING_AND_AUX_PAIR_FREEZE_AUDIT_PASS').replace("emit('audit_report_v2.json',report)","emit('audit_report_v1.json',report)").replace("emit('analysis_failure_v2.json',dict(","emit('analysis_failure_v1.json',dict(")
for n,text in [('collect_COUPLE_D_pair_audit_v1.py',collector),('analyze_COUPLE_D_pair_audit_v1.py',analyzer)]:
 ast.parse(text)
 with (S/n).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('COUPLE_D_READONLY_PAIR_AUDIT_TOOLS_STATIC_PASS')
