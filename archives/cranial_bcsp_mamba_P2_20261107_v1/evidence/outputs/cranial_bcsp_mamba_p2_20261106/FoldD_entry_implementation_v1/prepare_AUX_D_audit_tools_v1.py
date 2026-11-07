"""Adapt existing read-only collection and exact AUX lifecycle checks to D bindings."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent;A=S.parent/'H2_AUX_foldC_training_preparation_v1'
def adapt(t):
 return t.replace('0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517','efba40fdc78db788798ba326d9a393c5e0cac48189bb507a8ec4e9fe1d5f2db9').replace('first_FoldC_request_v1','AUX_D_pending_request_v1').replace('H2_AUX_foldC_seed0_training_execution_request_v1.json','H2_AUX_foldD_seed0_training_execution_request_v1.json')
collector=adapt((A/'collect_post_training_audit_v1.py').read_text(encoding='utf-8'))
old="ready=json.loads((S/'server_readiness_v1/readiness_receipt_v1.json').read_bytes())\nfor r in ready['assets']:add(r)"
new="""ready=json.loads((P/'FoldD_readiness_snapshot_v1.json').read_bytes())
for r in ready['metadata_bindings_verified']:add(r)
# Exact reused source/provider/environment bindings inherited from the frozen installed request.
for r in [*q['implementation'].values(),q['static_config'],q['baseline_request'],q['baseline_audit'],q['p3'],q['readiness'],q['cuda_audit'],q['order_plan'],q['initialization_reference'],q['numeric_policy'],q['numeric_protocol'],q['pair_contract'],q['preflight_scope'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),*q['dependencies']]:add(r)
R=S.parents[2];scope=json.loads((R/'outputs/cranial_bcsp_geov1_20261024/actual_proxy_trace_20261102_v1/observed_server_frozen_scope_v3.json').read_bytes())
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:add(r)
for key,rel in [('candidate','relative_target'),('isolated_model_project_sources','relative_path')]:
 for r in scope['bindings'][key]:add(dict(path=str(PurePosixPath(q['model_root'])/r[rel]),bytes=r['bytes'],sha256=r['sha256']))"""
assert collector.count(old)==1;collector=collector.replace(old,new).replace("q=json.loads(Q.read_bytes());out=","P=S/'AUX_D_pending_request_v1/transport_payload'\nq=json.loads(Q.read_bytes());out=")
analyzer=adapt((A/'analyze_post_training_audit_v1.py').read_text(encoding='utf-8'))
analyzer=analyzer.replace("C/'H2_authorization_v1.json'","C/'AUX_D_authorization_v1.json'").replace("C/'H2_runtime_v1.json'","C/'AUX_D_runtime_v1.json'").replace("C/'single_attempt_claim_v1.json'","C/'AUX_D_single_attempt_claim_v1.json'")
analyzer=analyzer.replace("R/'outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/shared_order_foldC_seed0_v1.json'","R/'outputs/cranial_bcsp_mamba_p1_20261104/FoldD_pair_preparation_20261106_v1/shared_order_foldD_seed0_v1.json'")
analyzer=analyzer.replace("['folds']['C']","['folds']['D']").replace("S/'server_readiness_v1/metadata/M0_construction.json'","S.parent/'H2_AUX_foldC_training_preparation_v1/server_readiness_v1/metadata/M0_construction.json'").replace('frozen_M0_C_post_training_audit_v1.json','frozen_M0_D_post_training_audit_v1.json').replace("identity['fold']=='C'","identity['fold']=='D'").replace('static_H2_AUX_training_config_v1.json','static_H2_AUX_foldD_training_config_v1.json').replace('FORMAL_H2_AUX_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS','FORMAL_H2_AUX_FOLDD_POST_TRAINING_FREEZE_AUDIT_PASS')
for name,text in [('collect_AUX_D_post_training_audit_v1.py',collector),('analyze_AUX_D_post_training_audit_v1.py',analyzer)]:
 ast.parse(text)
 with (S/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('AUX_D_READONLY_AUDIT_TOOLS_STATIC_PASS')
