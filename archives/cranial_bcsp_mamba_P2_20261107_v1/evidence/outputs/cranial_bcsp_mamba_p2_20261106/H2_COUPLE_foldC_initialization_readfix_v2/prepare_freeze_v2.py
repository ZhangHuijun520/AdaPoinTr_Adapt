"""Adapt the already-reviewed local pending-request freezer for this exact v2 fix."""
from pathlib import Path
import ast
S=Path(__file__).resolve().parent;OLD=S.parent/'H2_COUPLE_foldC_request_preparation_v1'
text=(OLD/'freeze_P3_and_pending_request_v1.py').read_text(encoding='utf-8')
def once(a,b):
 global text
 assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b)
text=text.replace('bcsp_h2_couple_foldC_training_entry_v1.py','bcsp_h2_couple_foldC_training_entry_v2.py')
text=text.replace("==32","==40").replace('CPU_contracts=32','CPU_contracts=40')
once('AssertionError(\'22 training imports bind own exact H2 modules\')','AssertionError(\'32 reused H2 module parent available to read policy\')')
text=text.replace("reason='Test22 retained the AUX-only sys.path text assertion'","reason='Legacy test32 contiguous read_roots text assertion conflicted with inserted exact file root'")
text=text.replace("resolution='Only test assertion updated to exact reused-module parent; final32-check batch retained separately'","resolution='Only test32 changed to AST membership; production entry unchanged; final40-check batch includes actual installed audit-hook regression'")
text=text.replace("O=S/'final_pending_request_v1'","O=S/'final_pending_request_v2'")
text=text.replace('bcsp_p2_H2_COUPLE_foldC_20261107_v1','bcsp_p2_H2_COUPLE_foldC_20261107_v2').replace('H2_COUPLE_foldC_seed0_20261107_v1','H2_COUPLE_foldC_seed0_20261107_v2').replace('bcsp_p2_H2_COUPLE_C_seed0_20261107_v1','bcsp_p2_H2_COUPLE_C_seed0_20261107_v2').replace('H2_COUPLE_foldC_seed0_training_execution_request_v1.json','H2_COUPLE_foldC_seed0_training_execution_request_v2.json').replace('bcsp_p2_H2_COUPLE_foldC_pending_20261107_v1.tar.gz','bcsp_p2_H2_COUPLE_foldC_pending_20261107_v2.tar.gz')
once("config=S/'static_H2_COUPLE_training_config_candidate_v1.json'","config=S.parent/'H2_COUPLE_foldC_request_preparation_v1/static_H2_COUPLE_training_config_candidate_v1.json'")
anchor="p3=dict(status='LOCAL_H2_COUPLE_TRAINING_ENTRY_P3_PASS'"
addition='''failed_root=S.parent/'H2_COUPLE_foldC_request_preparation_v1'
failed_audit=failed_root/'failed_attempt_freeze_audit_v1/audit_report_v1.json'
failure=json.loads(failed_audit.read_bytes());assert failure['status']=='FORMAL_COUPLE_V1_FAILED_STARTUP_FREEZE_AUDIT_PASS' and failure['optimizer_steps']==0 and failure['request_reusable'] is False
oldentry=failed_root/'bcsp_h2_couple_foldC_training_entry_v1.py'
oldroot="read_roots=[root,impl,Path(q['implementation']['h2_range']['path']).parent,"
newroot="read_roots=[root,impl,Path(q['aux_pairing']['initialization']['path']),Path(q['implementation']['h2_range']['path']).parent,"
assert entry.read_text().replace(newroot,oldroot)==oldentry.read_text()
policy_child=json.loads((cpu.parent/'actual_policy_child_stdout.bin').read_bytes());assert all(policy_child.values())
'''
once(anchor,addition+anchor)
once("emit(S/'implementation_P3_v1.json',p3)","p3.update(implementation_version='v2_exact_initialization_read_binding',failed_v1_formal_audit=bind(failed_audit),one_expression_production_delta=True,actual_policy_audit_hook_checks=policy_child,model_and_training_contract_unchanged=True)\nemit(S/'implementation_P3_v1.json',p3)")
anchor="q['not_authorized']=copy.deepcopy(aq['not_authorized'])"
addition="q['provenance']['superseded_attempt']=dict(request_sha256=failure['request_sha256'],status='ATTEMPT_CONSUMED_FAILED_BEFORE_TRAINING_NO_REUSE',failure_audit=stage(failed_audit,'frozen_COUPLE_v1_failure_audit.json'))\nq['provenance']['v2_only_change']='Exact AUX initialization.json read-only file root; no parent directory allowlist; original size and SHA checks retained'\n"
once(anchor,addition+anchor)
once("readiness_required_before_execution=True,server_operations=0","readiness_required_before_execution=True,failed_v1_request_reusable=False,failed_v1_audit_sha256=sha(failed_audit),server_operations=0")
ast.parse(text)
with (S/'freeze_P3_and_pending_request_v2.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('V2_LOCAL_FREEZER_STATIC_PASS')
