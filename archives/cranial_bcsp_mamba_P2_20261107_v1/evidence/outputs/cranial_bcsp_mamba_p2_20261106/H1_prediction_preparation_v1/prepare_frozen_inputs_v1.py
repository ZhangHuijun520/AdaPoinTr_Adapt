"""Local metadata-only prediction preparation; no executable entry/request or model imports."""
import ast
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
P1=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104'
H=ROOT/'outputs/cranial_bcsp_mamba_p2_20261106/H1_implementation_v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def emit(n,x):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

sources=[];runs=[];inputs=[];coarse={};comparisons={}
for fold,sub,train,auditrel,expected in [
 ('C','paired_development_evaluator_v2','first_FoldC_request_v1/transport_payload/M_H1_foldC_seed0_training_execution_request_v1.json','post_training_freeze_audit_v1/audit_report_v1.json','6839d694cdd8068085dceea1426aa9d55e71faeaff39a9032bf21af6b1e8b5b4'),
 ('D','FoldD_paired_development_entry_v1','FoldD_request_v1/transport_payload/M_H1_foldD_seed0_training_execution_request_v1.json','FoldD_request_v1/post_training_freeze_audit_v1/audit_report_v1.json','6a76aa7dc156c0e2eeef29d4e03b253f624373ced8a48abebe1af4c99d7e789d')]:
    d=P1/sub/'transport_payload';idx=read(d/'paired_development_input_index_v1.json');oldpro=read(d/'paired_development_protocol_v1.json')
    qpath=H/train;apath=H/auditrel;q=read(qpath);a=read(apath)
    assert a['status']==f'FORMAL_P2_H1_FOLD{fold}_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS'
    assert a['request_sha256']==sha(qpath) and a['checks_passed']==len(a['checks']) and all(a['checks'].values())
    assert a['checkpoint']['sha256']==expected and a['checkpoint']['bytes']==407224375
    old=next(r for r in idx['runs'] if r['label']==fold+'_M0');run=copy.deepcopy(old)
    run.update(label=fold+'_M_H1',checkpoint=dict(path=q['output']+'/ckpt-last.pth',bytes=407224375,sha256=expected),
        training_request_sha256=sha(qpath),training_freeze_audit_sha256=sha(apath),H1=copy.deepcopy(q['h1_config']))
    rows=copy.deepcopy([r for r in idx['inputs'] if r['run']==fold+'_M0'])
    assert len(rows)==105 and [r['case_id'] for r in rows]==run['dev_case_ids']
    assert len(set(run['train_sources']))==63 and len(set(run['dev_sources']))==21 and not set(run['train_sources'])&set(run['dev_sources'])
    assert set(Counter(r['source_id'] for r in rows).values())=={5}
    assert set(r['source_id'] for r in rows)==set(run['dev_sources'])
    for r in rows:
        assert r['normalization_source']=='defective_bbox' and r['normalization']['scale']>0 and r['n_input']==8192
        r['run']=run['label']
    # Cross-folder storage is inherited byte-for-byte from the audited P1 index, never guessed.
    original=[r for r in idx['inputs'] if r['run']==fold+'_M0']
    assert all(all(r[k]==oldr[k] for k in ['case_id','source_id','input','normalization','normalization_source','target_array_sha256']) for r,oldr in zip(rows,original))
    coarse[fold]=oldpro['coarse_tensor_cases'];assert set(coarse[fold])<=set(run['dev_case_ids'])
    predictor=P1/sub/('bcsp_p1_paired_predict_v2.py' if fold=='C' else 'bcsp_p1_foldD_paired_predict_v1.py')
    tree=ast.parse(predictor.read_text(encoding='utf-8'))
    anchors={n.name:dict(start=n.lineno,end=n.end_lineno) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['validate_index','validate_evidence','execute_pair','main','load_checkpoint','predict_once','validate_source']}
    prioraudit=P1/sub/'post_prediction_freeze_audit_v1/audit_report_v1.json'
    assert read(prioraudit)['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS'
    comparisons[fold]=dict(label=fold+'_M0',previous_prediction_audit=rec(prioraudit),old_checkpoint_SHA256=old['checkpoint']['sha256'],new_forward_calls_budgeted=0,availability='Archived locally; payload archive not reopened or rehashed in this metadata-only task')
    sources.extend([rec(p) for p in [d/'paired_development_input_index_v1.json',d/'paired_development_protocol_v1.json',qpath,apath,predictor]])
    runs.append(run);inputs.extend(rows)
    emit('compatibility_anchors_'+fold+'_v1.json',dict(source=rec(predictor),anchors=anchors))

assert len(inputs)==210 and len({r['case_id'] for r in inputs})==210
assert not set(runs[0]['dev_sources'])&set(runs[1]['dev_sources'])
assert runs[0]['H1']==runs[1]['H1']
emit('H1_C_D_input_index_candidate_v1.json',dict(schema='bcsp-p2-H1-twofold-development-index-candidate-v1',status='FROZEN_INPUTS_PENDING_ENTRY_IMPLEMENTATION',runs=runs,inputs=inputs,forward_budget=210,unique_cases=210,input_file_count=210,point_payloads_read=0,server_paths_revalidated=False,source_bindings=sources,baseline_prediction_comparison=comparisons))
emit('H1_C_D_prediction_protocol_candidate_v1.json',dict(schema='bcsp-p2-H1-twofold-development-protocol-candidate-v1',status='PENDING_ENTRY_IMPLEMENTATION_NOT_EXECUTION_AUTHORIZATION',
    models=['C_M_H1','D_M_H1'],fold_order=['C','D'],forwards_per_model=105,forward_budget=210,batch_size=1,warmup=0,TTA=0,loss_calls=0,backward=0,optimizer_steps=0,BNCal=0,
    input_key='partial',n_input=8192,n_output=8192,coarse=256,H1=runs[0]['H1'],checkpoint_selection='Formally frozen final epoch99/update3900 checkpoints only',
    state_RNG_contract='Sequential models, eval/inference_mode; parameters/BN and Python/NumPy/CPU/CUDA RNG before/after each105cases equal',
    normalization='Fixed D-only normalization; normalized predictions; native world-mm offline scoring; no GT alignment/ICP',
    coarse_tensor_cases_by_fold=coarse,geometry_summary='Same-forward coarse/dense centroid, radius, bbox, covariance and mean displacement; no extra forward or GT read',
    limits=dict(wall_seconds=7200,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296),
    failure_policy='Stop immediately; no automatic retry/resume or continuing the second model after failure',
    baseline='Reuse frozen P1 M0 predictions, zero baseline re-inference in this210forward budget; verify local archive before scoring',
    scoring='Subsequent separate CPU scoring under unchanged E/J/CD/risk definitions; no scoring or gate in prediction',
    prohibited=['training','BNCal','backward','loss','protected partitions','new cases','parameter scan','repeated GPU preflight','baseline forwards','checkpoint instrumentation beyond existing summaries']))
emit('prediction_request_preparation_draft_v1.json',dict(status='BLOCKED_ON_MINIMAL_PREDICTION_ENTRY_IMPLEMENTATION',is_execution_request=False,execution_ready=False,
    target='Two fixed H1 checkpoints, C105+D105=210 predictions',existing_entry_directly_compatible=False,
    blockers=['Same-fold T0/M0 validation incompatible with one H1 model per fold','helper.validate_model rejects H1 enabled','base YAML equality rejects H1-only config delta','training-audit validators expect P1 T0/M0 receipt rather than P2 H1 freeze evidence','hard-coded fold/data/output/representative mappings require exact twofold dispatch'],
    required_limited_implementation=['One isolated H1 twofold prediction entry derived from audited P1 code; keep old entries unchanged','Exact H1 attribute/config and two checkpoint freeze binding','C/D105 index/source validation and exact data paths','Preserve existing checkpoint loader, file guards, source reader, numeric/backend, eval/RNG/state/resource/claim semantics','Targeted artificial CPU tests plus local P3; final request only after final source hash'],
    implementation_authorized_by_this_task=False,final_entry_sha256=None,final_execution_request_created=False,server_operations=0,checkpoints_loaded=0,predictions_executed=0))
print(json.dumps(dict(status='COMPATIBILITY_REVIEW_COMPLETE_INPUTS_FROZEN_FINAL_REQUEST_BLOCKED',runs=2,per_fold105=True,total_predictions=210,implementation_changes=0,server_calls=0)))
