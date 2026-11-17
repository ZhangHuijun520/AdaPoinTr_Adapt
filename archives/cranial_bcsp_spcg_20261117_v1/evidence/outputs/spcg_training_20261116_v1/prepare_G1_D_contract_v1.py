"""Local G1_D contract and compatibility review; no server or implementation changes."""
from pathlib import Path,PurePosixPath
import json,hashlib,importlib.util
S=Path(__file__).resolve().parent;W=S.parents[1];V=S/'G1_D_preparation_v1';V.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,d):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
parent=S/'G1_C_implementation_v1/pending_transport_v1/payload/SPCG_G1_C_training_execution_request_v1.json';q=read(parent)
g0path=S/'G0_D_implementation_v1/pending_transport_v1/payload/SPCG_G0_D_training_execution_request_v1.json';g0=read(g0path);freeze=S/'G0_D_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json';proof=read(freeze)
assert proof['status']=='FORMAL_SPCG_G0_D_POST_TRAINING_FREEZE_PASS' and all(proof['checks'].values()) and proof['request_sha256']==rec(g0path)['sha256']
assert (proof['fold'],proof['updates'],proof['traversals'],proof['exposures'],proof['drops'])==('D',3900,100,31200,300)
for k in ['identity','environment','static_config','counts','resources','science']:assert q[k]==g0[k],k
q['QC']=g0['QC'];q['order_plan']=g0['order_plan'];q['data_root']=g0['data_root'];q.pop('G0_C_freeze')
assert q['parent_G0_initial_state_sha256']==proof['initialization_raw_tensor_fingerprint']
aliases=read(S/'G0_D_implementation_v1/local_metadata_map_v1.json');M=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload'
def local(r):
 p=Path(aliases[r['path']]);a=rec(p);assert (a['bytes'],a['sha256'])==(r['bytes'],r['sha256']);return p
sp=importlib.util.spec_from_file_location('G1D_metadata_only',local(q['implementation']['contract']));c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c);c.exact=local
selected,fold=c.verify_qualified_receipt(read(local(q['QC']['qualified_receipt'])),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'D',8192);plan=c.validate_order(read(local(q['order_plan'])),fold['train_case_ids'])
assert proof['order_plan']==q['order_plan'] and len(selected)==315 and len(plan['epochs'])==100
assets=read(S/'G2_C_implementation_v1/local_metadata_map_v1.json')
for k in ['probe_asset','head_initialization','mother_source']:
 p=Path(assets[q[k]['path']]);a=rec(p);assert (a['bytes'],a['sha256'])==(q[k]['bytes'],q[k]['sha256'])
root='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G1D_training_20261117_v1';run='SPCG_G1_foldD_seed0_train_20261117_v1';control=root+'/control/'+run
q.update(schema='bcsp-spcg-G1D-training-CONTRACT-DRAFT-v1',status='DRAFT_PENDING_IMPLEMENTATION_CPU_P3_NOT_EXECUTABLE',execution_authorized=False,fold='D',run_id=run,output=q['project']+'/logs/cranial_bcsp_fullmamba/'+run,G0_D_freeze=rec(freeze))
q.pop('P3');q.pop('launch_contract');q['implementation'].pop('entry');q['implementation'].pop('bridge')
q['planned_launch_contract']=dict(request_path=root+'/SPCG_G1_D_training_execution_request_v1.json',authorization_path=control+'/authorization_v1.json',runtime_path=control+'/runtime_v1.json',launcher_path=control+'/launch_once_v1.sh',launch_attempt_path=control+'/attempt_claim_v1.json',tmux_session=run)
q['required_new_implementation']=dict(entry=root+'/bcsp_spcg_G1_D_training_entry_v1.py',bridge=root+'/bcsp_spcg_G1_D_training_bridge_v1.py',hashes=None,CPU_result=None,P3=None)
q['readiness']='Local D metadata/order/G0_D formal freeze and U/H exact bytes checked. Current server identity/resource/D315 input hashes/reused metadata/new targets not rechecked. Final proof transport mapping not yet frozen.'
emit('G1_D_training_contract_draft_v1.json',q)
emit('G1_D_compatibility_and_metadata_review_v1.json',dict(status='LOCAL_G1D_CONTRACT_READY_REQUIRES_MINIMAL_ENTRY_BRIDGE',G0_D_freeze=rec(freeze),parent_G1_C_request=rec(parent),matched_G0_D_request=rec(g0path),checks=dict(G0_D_formal_freeze=True,D315_metadata_and_order100=True,same_D_order_and3900_contract=True,same_identity_environment_static_config=True,U_H_mother_source_bytes_bound=True,G0_shared_scratch_initialization=True),findings=['Frozen head/factory already support G1 global256 aggregation; do not change scientific module.','Existing G1 entry validate/authorize/build logging and bridge explicitly bind C; G1D cannot reuse them unmodified.','G0_D freeze must replace G0_C pair prerequisite; final request requires actual new entry/bridge hashes and new P3.'],minimal_scope=['Isolated G1_D entry plus bridge fold adaptation; keep G1 factory, head, U/H, original runtime and all numeric/resource limits unchanged.','One targeted artificial CPU batch: complete authorize with D metadata, actual G1 build/mother route, wrong-fold/G0_D proof rejection, same order and initialization, logs/optimizer/UTC/exception lifecycle.','New P3 and exact-hash pending request. Reuse existing CUDA admission, no repeated GPU preflight.'],server_operations=0,tests_run=0,payload_reads=0,implementation_changes=0))
emit('preparation_receipt_v1.json',dict(status='CONTRACT_DRAFT_ONLY_NOT_EXECUTION_REQUEST',draft=rec(V/'G1_D_training_contract_draft_v1.json'),review=rec(V/'G1_D_compatibility_and_metadata_review_v1.json'),authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,training_started=False,server_operations=0))
print(json.dumps(dict(status='G1_D_CONTRACT_DRAFT_READY_NO_EXECUTION',order_sha256=q['order_plan']['sha256'],updates=q['counts']['updates'],G0_D_freeze_sha256=rec(freeze)['sha256'])))
