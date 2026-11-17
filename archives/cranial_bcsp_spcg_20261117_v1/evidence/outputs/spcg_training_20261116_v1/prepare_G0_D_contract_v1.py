"""Local metadata-only Fold D preparation; no implementation changes or server calls."""
from pathlib import Path,PurePosixPath
import json,hashlib,importlib.util
S=Path(__file__).resolve().parent;W=S.parents[1];V=S/'G0_D_preparation_v1';V.mkdir()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,d):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
parent=S/'UTC_order_hotfix_v3/pending_transport_v3/payload/SPCG_G0_C_training_execution_request_v3.json';q=read(parent)
M=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload';metadata=read(S/'G2_C_implementation_v1/local_metadata_map_v1.json')
contract=Path(metadata[q['implementation']['contract']['path']]);assert rec(contract)['sha256']==q['implementation']['contract']['sha256']
spec=importlib.util.spec_from_file_location('G0D_metadata_contract_only',contract);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
qc=q['QC'];root=str(PurePosixPath(qc['qualified_receipt']['path']).parent)
receipt=M/'qualified_SCQ_D_8192_v1.json';order=M/'shared_order_foldD_seed0_v1.json'
qc['qualified_receipt']=dict(rec(receipt),path=root+'/'+receipt.name)
q['order_plan']=dict(rec(order),path=root+'/'+order.name)
aliases=dict(metadata);aliases[qc['qualified_receipt']['path']]=str(receipt);aliases[q['order_plan']['path']]=str(order)
def local_exact(r):
 p=Path(aliases[r['path']]);actual=rec(p);assert (actual['bytes'],actual['sha256'])==(r['bytes'],r['sha256']);return p
c.exact=local_exact
selected,fold=c.verify_qualified_receipt(read(receipt),qc['verification'],qc['manifests'],qc['fold_binding'],'D',8192)
plan=c.validate_order(read(order),fold['train_case_ids'])
assert len(selected)==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21 and sum(len(x['batches']) for x in plan['epochs'])==3900
proofs={}
for arm,path,status in [('G0',S/'UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json','FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS'),('G1',S/'G1_C_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json','FORMAL_SPCG_G1_C_POST_TRAINING_FREEZE_PASS'),('G2',S/'G2_C_implementation_v1/post_training_freeze_v1/formal_freeze_result_v1.json','FORMAL_SPCG_G2_C_POST_TRAINING_FREEZE_PASS')]:
 a=read(path);assert a['status']==status and all(a['checks'].values());proofs[arm]=rec(path)
oldroot=str(PurePosixPath(q['implementation']['entry']['path']).parent);newroot='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G0D_training_20261116_v1';oldrun=q['run_id'];run='SPCG_G0_foldD_seed0_train_20261116_v1'
q.update(schema='bcsp-spcg-G0D-training-CONTRACT-DRAFT-v1',status='DRAFT_PENDING_IMPLEMENTATION_CPU_P3_NOT_EXECUTABLE',execution_authorized=False,fold='D',run_id=run,data_root='/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1',output=q['output'].replace(oldrun,run))
q['planned_launch_contract']={k:v.replace(oldroot,newroot).replace(oldrun,run).replace('SPCG_G0_C_training_execution_request_v3','SPCG_G0_D_training_execution_request_v1').replace('_v3.json','_v1.json').replace('_v3.sh','_v1.sh') for k,v in q.pop('launch_contract').items()}
q['implementation'].pop('entry');q['implementation'].pop('bridge');q.pop('P3');q['completed_C_matrix_proofs_local']=proofs
q['required_new_implementation']=dict(entry=newroot+'/bcsp_spcg_G0_D_training_entry_v1.py',bridge=newroot+'/bcsp_spcg_G0_D_training_bridge_v1.py',hashes=None,CPU_result=None,P3=None)
q['readiness']='Local frozen D metadata verified; current server D inputs/order/QC/identity/free disk/new targets not checked. Recheck before any authorized install/launch.'
emit('G0_D_training_contract_draft_v1.json',q)
review=dict(status='LOCAL_D_METADATA_PASS_NEEDS_MINIMAL_G0D_ENTRY_BRIDGE',counts=dict(sources=63,train_cases=315,dev_sources=21,dev_cases=105,updates=3900,traversals=100,exposures=31200,drops=300),D_qualified_receipt=rec(receipt),D_order=rec(order),C_matrix_proofs=proofs,checks=dict(frozen_D_QC_metadata_valid=True,D_order_all100_traversals_valid=True,all_C_runs_formally_frozen=True,original_G0_initialization_retained=True),compatibility_findings=['Existing G0 entry validate/authorize only accepts C and G0C P3/schema.','Existing G0 bridge accepts G0/C only. No G0_D dedicated entry found.','G0_D must use original LQI coarse head; do not install G1/G2 SPCG head.'],minimal_scope=['Isolated G0_D entry and bridge derived from validated G0_C, changing fold/schema/P3/run bindings and adding completed C-matrix prerequisite.','One targeted artificial CPU batch, including complete authorize path with frozen D metadata, D order/counts, exact source reads, UTC/exception lifecycle and wrong-fold rejection.','P3 followed by final exact-hash pending execution request; reuse existing CUDA admission.'],server_operations=0,training_started=False,payload_reads=0,tests_run=0)
emit('G0_D_compatibility_and_metadata_review_v1.json',review)
emit('preparation_receipt_v1.json',dict(status='DRAFT_ONLY_NOT_EXECUTABLE',draft=rec(V/'G0_D_training_contract_draft_v1.json'),review=rec(V/'G0_D_compatibility_and_metadata_review_v1.json'),server_operations=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
print(json.dumps(dict(status=review['status'],D_order=q['order_plan'],data_root=q['data_root'],train_cases=len(selected))))
