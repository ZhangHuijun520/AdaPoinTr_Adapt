"""Local G2_D pending scope only; preserve phased implementation/execution boundaries."""
from pathlib import Path,PurePosixPath
import json,hashlib
S=Path(__file__).resolve().parent;V=S/'G2_D_preparation_v1';V.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,d):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
oldpath=S/'G2_C_implementation_v1/pending_transport_v1/payload/SPCG_G2_C_training_execution_request_v1.json';q=read(oldpath)
g1path=S/'G1_D_rebind_v2/pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v2.json';g1=read(g1path)
proofpath=S/'G1_D_rebind_v2/post_training_freeze_v2/formal_freeze_result_v2.json';proof=read(proofpath)
assert proof['status']=='FORMAL_SPCG_G1_D_POST_TRAINING_FREEZE_PASS' and all(proof['checks'].values()) and proof['request_sha256']==rec(g1path)['sha256']
assert (proof['fold'],proof['updates'],proof['traversals'],proof['exposures'],proof['drops'])==('D',3900,100,31200,300)
for k in ['counts','resources','science','static_config','probe_asset','head_initialization','mother_source','expected_initial_state_sha256','parent_G0_initial_state_sha256']:assert q[k]==g1[k],k
for k in ['identity','environment','data_root','QC','order_plan','startup_free_disk_bytes','capacity','resource_migration']:q[k]=g1[k]
assert q['order_plan']==proof['order_plan'] and q['expected_initial_state_sha256']==proof['initialization_raw_tensor_fingerprint'] and q['identity']['gpu_uuid']==proof['pairing']['G1_D_gpu_uuid']
q.pop('G0_C_freeze');q.pop('G1_C_freeze');q['G0_D_freeze']=g1['G0_D_freeze'];q['G1_D_freeze']=rec(proofpath)
q['resource_migration']=dict(q['resource_migration'],schema='spcg-G2D-resource-continuation-DRAFT-v1',paired_G1_D_request_sha256=rec(g1path)['sha256'])
root='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G2D_training_20261117_v1';run='SPCG_G2_foldD_seed0_train_20261117_v1';control=root+'/control/'+run
q.update(schema='bcsp-spcg-G2D-training-CONTRACT-DRAFT-v1',status='DRAFT_PENDING_IMPLEMENTATION_CPU_P3_NOT_EXECUTABLE',execution_authorized=False,fold='D',run_id=run,output=q['project']+'/logs/cranial_bcsp_fullmamba/'+run)
q.pop('P3');q.pop('launch_contract');q['implementation'].pop('entry');q['implementation'].pop('bridge')
q['planned_launch_contract']=dict(request_path=root+'/SPCG_G2_D_training_execution_request_v1.json',authorization_path=control+'/authorization_v1.json',runtime_path=control+'/runtime_v1.json',launcher_path=control+'/launch_once_v1.sh',launch_attempt_path=control+'/attempt_claim_v1.json',tmux_session=run)
q['required_new_implementation']=dict(entry=root+'/bcsp_spcg_G2_D_training_entry_v1.py',bridge=root+'/bcsp_spcg_G2_D_training_bridge_v1.py',hashes=None,CPU_result=None,P3=None)
q['readiness']='No current server operation. Exact G1_D device required; startup>=6GiB, runtime>=4GiB and output<=1GiB. Recheck all reused hashes/D315 inputs and new targets before execution. Local proof path requires final transport mapping.'
emit('G2_D_training_contract_draft_v1.json',q)
emit('G2_D_compatibility_review_v1.json',dict(status='LOCAL_CONTRACT_READY_REQUIRES_G2D_ENTRY_BRIDGE_CPU_P3',G1_D_freeze=rec(proofpath),G1_D_request=rec(g1path),G2_C_request=rec(oldpath),checks=dict(G1_D_formal_freeze=True,same_G1_D_device=True,same_U_H_complete_initial_state=True,same_D_order3900_contract=True,same_runtime_limits=True,startup6GiB_retained=True,G0_D_cross_device_limitation_retained=True),findings=['Existing frozen head/factory already support G2 k8; no scientific module change needed.','G2_C entry/bridge only accept C and old startup8.5GiB, without G1_D same-device continuation contract.','G1_D entry supports rebound identity/startup6GiB but only G1; it cannot execute G2 unmodified.'],minimal_scope=['Isolated G2_D entry and bridge; merge proven G2 build with proven G1_D identity/startup6GiB guard.','Bind G1_D formal freeze and assert same device/initialization/D order; keep G0_D only as disclosed cross-device reference.','One targeted CPU batch covering actual G2 k8 build, full authorize D metadata, exact assets, identity/budget/paired-proof rejection and unchanged logs/lifecycle.','P3 then final exact-hash pending request; no repeated GPU admission.'],server_operations=0,tests_run=0,implementation_changes=0,training_started=False))
emit('preparation_receipt_v1.json',dict(status='CONTRACT_DRAFT_ONLY_NOT_EXECUTION_REQUEST',draft=rec(V/'G2_D_training_contract_draft_v1.json'),review=rec(V/'G2_D_compatibility_review_v1.json'),authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,server_operations=0))
print(json.dumps(dict(status='G2_D_CONTRACT_DRAFT_READY_NO_EXECUTION',GPU=q['identity']['gpu_uuid'],order_sha256=q['order_plan']['sha256'],startup_GiB=q['startup_free_disk_bytes']/1024**3)))
