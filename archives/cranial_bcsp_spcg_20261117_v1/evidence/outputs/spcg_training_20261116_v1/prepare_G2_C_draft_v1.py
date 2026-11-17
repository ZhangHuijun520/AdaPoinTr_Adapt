"""Prepare a non-executable G2_C contract; do not change implementation or call server."""
from pathlib import Path
import json,hashlib
S=Path(__file__).resolve().parent
V=S/'G2_C_preparation_v1';V.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(name,x):
 with (V/name).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
g1=S/'G1_C_implementation_v1';qp=g1/'pending_transport_v1/payload/SPCG_G1_C_training_execution_request_v1.json'
q=read(qp);g0=S/'UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json';a1=g1/'post_training_freeze_v1/formal_freeze_result_v1.json'
for p,arm in [(g0,'G0'),(a1,'G1')]:
 a=read(p);assert a['arm']==arm and a['fold']=='C' and all(a['checks'].values()) and a['updates']==3900
evidence=S.parents[1]/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/post_CUDA_freeze_v3/server_evidence.json'
native=json.loads(read(evidence)['output']['completion.json']['text'])
q['schema']='bcsp-spcg-G2C-training-CONTRACT-DRAFT-v1'
q['status']='DRAFT_PENDING_IMPLEMENTATION_CPU_P3_NOT_EXECUTABLE'
q['execution_authorized']=False;q['arm']='G2'
oldroot='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G1C_training_20261116_v1'
root='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G2C_training_20261116_v1'
oldrun=q['run_id'];run='SPCG_G2_foldC_seed0_train_20261116_v1'
q['run_id']=run;q['output']=q['output'].replace(oldrun,run)
q['planned_launch_contract']={k:v.replace(oldroot,root).replace(oldrun,run).replace('SPCG_G1_C_training_execution_request','SPCG_G2_C_training_execution_request') for k,v in q.pop('launch_contract').items()}
q['implementation'].pop('entry');q['implementation'].pop('bridge');q.pop('P3')
q['expected_initial_state_sha256']=native['result']['models']['G2']['initial_state_sha256']
q['required_new_implementation']={'entry':root+'/bcsp_spcg_G2_C_training_entry_v1.py','bridge':root+'/bcsp_spcg_G2_C_training_bridge_v1.py','hashes':None,'CPU_result':None,'P3':None}
q['G0_C_freeze']=rec(g0);q['G1_C_freeze']=rec(a1)
q['local_parent_request']=rec(qp)
q['readiness']='No current server check; current identity/resources/assets/315 inputs/new targets must be checked before authorized installation/execution.'
q['draft_limitations']=['Local freeze paths require explicit transport mapping or verified existing remote binding before final request.','No entry/bridge hashes or P3 are invented; this draft cannot be used by an executor.','No authorization/runtime/launcher/claim materialized.']
q['science']['G2_contract_note']='Fixed Sobol256 U; k=8 stable nearest Memory; same H initialization and 1416-dimensional readout; direct Q; no residual, loss, data, decoder or training budget changes.'
emit('G2_C_training_contract_draft_v1.json',q)
emit('G2_C_entry_compatibility_review_v1.json',dict(status='NEEDS_MINIMAL_G2C_ENTRY_BRIDGE_CPU_P3',basis=dict(G1_request=rec(qp),G0_freeze=rec(g0),G1_freeze=rec(a1),CUDA_evidence=rec(evidence)),findings=['Frozen head and factory support G2.','G1 entry validate/build/identity and bridge arm guard explicitly reject G2.','G1 P3 certifies only G1_C; no compatible G2_C entry found.'],scope=['New isolated G2_C entry derived from validated G1_C; only arm/schema/path/P3 binding changes plus G1 formal-freeze binding.','New G2_C bridge derived from G1 bridge, preserving lifecycle/logging and changing arm guard only.','One targeted artificial CPU batch covering real G2 build/authorize path, k8 route, U/H/raw initialization, paired order/counts, no-decay, UTC/exception lifecycle, and rejection cases.','New P3 then final pending request with exact hashes; do not repeat GPU admission.'],server_operations=0,tests_run=0,implementation_changes=0))
emit('preparation_receipt_v1.json',dict(status='CONTRACT_DRAFT_ONLY_NOT_EXECUTION_REQUEST',draft=rec(V/'G2_C_training_contract_draft_v1.json'),review=rec(V/'G2_C_entry_compatibility_review_v1.json'),authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,training_started=False))
print(json.dumps(read(V/'preparation_receipt_v1.json'),ensure_ascii=False))
