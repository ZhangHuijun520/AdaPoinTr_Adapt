"""Finite readonly source/metadata review; not implementation, tests, request or server action."""
from pathlib import Path
from collections import Counter
import ast,hashlib,importlib.util,json

R=Path(__file__).resolve().parent.parent
OLD=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1'
O=R/'outputs/scq_rf_Sref_C_training_review_20261114_v1';O.mkdir()
RF=R/'outputs/scq_rf_initialization_loader_20261114_v2'
Q=OLD/'S_C_pending_preparation_v1/pending_transport_v1/payload/SCQ_S_FoldC_training_execution_request_v1.json'


def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)


q=read(Q);context=read(OLD/'training_context_candidate_v1.json');mirror=context['mirror']
contract=OLD/'candidate_payload/bcsp_training_contract_01dt08_v3.py'
assert rec(contract)['sha256']==q['implementation']['contract']['sha256']
spec=importlib.util.spec_from_file_location('RF_readonly_metadata_only',contract);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original_exact=m.exact
def local_exact(record):
    assert record['path'] in mirror,'unmapped exact metadata path '+record['path']
    return original_exact(dict(record,path=mirror[record['path']]))
m.exact=local_exact
static=m.validate_static(read(local_exact(q['static_config'])))
selected,fold=m.verify_qualified_receipt(read(local_exact(q['QC']['qualified_receipt'])),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192)
plan=m.validate_order(read(local_exact(q['order_plan'])),fold['train_case_ids'])
exposure,dropped=Counter(),Counter()
for epoch in plan['epochs']:
    for batch in epoch['batches']:exposure.update(batch)
    dropped.update(epoch['dropped'])
assert len(selected)==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21
assert not set(fold['train_sources']) & set(fold['dev_sources'])
assert len({r['case_id'] for r in selected})==315
assert set(Counter(r['source_id'] for r in selected).values())=={5}
assert sum(exposure.values())==31200 and sum(dropped.values())==300
assert all(exposure[cid]+dropped[cid]==100 for cid in plan['case_ids'])
assert len(plan['epochs'])*len(plan['epochs'][0]['batches'])==3900
cuda_path=RF/'pending_transport_v3/payload/SCQ_RF_artificial_cuda_execution_request_v3.json';cuda=read(cuda_path)
audit_path=RF/'post_CUDA_freeze_audit_v3/freeze_verification_v3.json';audit=read(audit_path)
assert audit['status']=='FORMAL_RF_POST_CUDA_FREEZE_AUDIT_PASS' and all(audit['checks'].values()) and audit['request_sha256']==rec(cuda_path)['sha256']
construction_path=RF/'post_CUDA_freeze_audit_v3/downloads/output/construction.json';construction=read(construction_path)
current_common=construction['models'][0]['shared_initial_state_SHA256']
assert len({r['shared_initial_state_SHA256'] for r in construction['models']})==1
assert cuda['static_config']==q['static_config'] and cuda['initialization']==q['initialization']
for key in ('encoder','factory','lqi_decoder','lqi_factory','scq_residual','scq_factory','timezone'):
    assert cuda['implementation'][key]==q['implementation'][key]
finished=read(RF/'post_CUDA_freeze_audit_v3/finished_result_v1.json')
assert finished['hostname']==cuda['identity']['hostname'] and finished['GPU'][0]==cuda['identity']['gpu_uuid']
paths=dict(entry=OLD/'UTC_order_hotfix_v2/bcsp_scq_training_entry_v2.py',bridge=OLD/'bcsp_scq_training_bridge_v1.py',
           runtime=OLD/'candidate_payload/bcsp_p1_training_runtime_v1.py',contract=contract)
for key,p in paths.items():
    if key in ('runtime','contract','bridge'):assert rec(p)['sha256']==q['implementation'][key]['sha256']
    ast.parse(p.read_text(encoding='utf-8'))
text={k:p.read_text(encoding='utf-8') for k,p in paths.items()}
assert "full_forward=4,full_backward=4,full_loss=4" in text['entry']
assert "q['variant'] in ('B','S')" in text['entry'] and "['B_C','S_C','B_D','S_D']" in text['entry']
assert "S requires formal B freeze" in text['entry']
assert "if not n.startswith('base_model.scq.')" in text['entry']
assert "admission['status']!='SCQ_NATIVE_CUDA_ADMISSION_PASS'" in text['bridge']
runtime_tree=ast.parse(text['runtime'])
runtime_class=next(n for n in runtime_tree.body if isinstance(n,ast.FunctionDef) and n.name=='train_lifecycle')
assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='range' and len(n.args)==1 and isinstance(n.args[0],ast.Constant) and n.args[0].value==100 for n in ast.walk(runtime_class))
assert 'checkpoint_legacy_stage' in text['entry'] and "'stage': 'BCSP_INPUT_DENSITY_V1'" in text['runtime']
anchors={k:[dict(line=i,text=line.strip()) for i,line in enumerate(text[k].splitlines(),1) if any(token in line for token in ["ADMISSION_SHA=","CUDA_REQUEST_SHA=","full_forward=4","q['variant'] in ('B','S')","S requires formal B freeze","['B_C','S_C','B_D','S_D']","base_model.scq.')","SCQ_NATIVE_CUDA_ADMISSION_PASS","range(100)","counts['step'] += 1","scheduler.step()","stage': 'BCSP_INPUT_DENSITY_V1'"])] for k in paths}
metadata_records=[q['static_config'],q['QC']['qualified_receipt'],q['QC']['verification'],*q['QC']['manifests'].values(),q['QC']['fold_binding'],q['order_plan']]
review=dict(status='READONLY_SREF_C_CONTRACT_VERIFIED_ENTRY_INCOMPATIBLE_NO_EXECUTION_REQUEST',
    sources={k:rec(p) for k,p in paths.items()},anchors=anchors,
    verified_metadata=[dict(remote=r,local=rec(local_exact(r))) for r in metadata_records],
    scientific_contract=dict(stage='SCQ_RF',arm='S-ref',underlying_factory_variant='S',fold='C',seed=0,
        n_input=8192,n_output=8192,coarse_points=256,train_sources=63,train_cases=315,dev_sources_metadata_only=21,
        dev_cases_metadata_only=105,confirmation_count_excluded_recorded=20,epochs=100,batches_per_epoch=39,batch=8,
        updates=3900,exposures=31200,drops=300,per_case_exposure_plus_drop=100,
        order_file=q['order_plan'],order_canonical_sha256=m.canonical_sha(plan),train_allowlist_sha256=fold['train_allowlist_sha256'],
        data_root=q['data_root'],data_root_origin='Exact frozen Fold C training request path, not inferred from directory names',
        sampling='fixed BCSP V1',model_parameters=40596676,RF_second_head=False,
        optimizer='unchanged AdamW lr1e-4 betas(.9,.999) eps1e-8 clip10, explicitSSM/1D/bias no-decay',
        LR='1e-4*max(.9**(epoch/21),.02)',BN='max(.9*.5**(epoch/21),.01)',
        initialization='from scratch seed0 plus frozen original SCQ initializer; no historical checkpoint warmstart',
        BNCal=False,evaluation=False,resume=False,automatic_retry=False),
    numerical_static=static['training'],resources=static['resources'],
    current_CUDA_admission=rec(audit_path),current_CUDA_request=rec(cuda_path),
    device_identity=cuda['identity'],device_evidence='Latest formal CUDA freeze identity; not fresh server liveness or training-data hash verification this turn',
    expected_common_full_S_state_SHA256=current_common,common_state_scope='Include encoder/LQI/SCQ/BN and all persistent state; exclude only nonexistent RF head in S-ref; matches native5-build evidence',
    blockers=['Old entry pins historical4forward/4backward admission instead of current5forward/4backward RF audit.',
              'Old B/S sequence and paired_baseline requirement force B_C before S_C; new S-ref_C must start first without an old B checkpoint.',
              'Old common-state fingerprint excludes SCQ; new native admission fingerprint includes original SCQ and excludes only RF.',
              'Old pair identity and protocol B_C,S_C,B_D,S_D differ from current device and planned Sref_C,Static_C,Requery_C,Sref_D,Requery_D,Static_D.',
              'Bridge admits the old SCQ status; phase/run identity and required log attribution must bind the new RF stage while leaving numerical runtime unchanged.'],
    reusable_without_numerical_edits=['Model factory SCQ S branch, frozen original initializer and all shared model code','Pure QC/static/order metadata validators','315 case allowlist and exact100x39 order bytes','Original training runtime, optimizer, LR/BN schedules and resource ceilings'],
    limitations=['Payload files were not opened, hashed or decoded; current315 payload presence/hash and resources require fresh remote check before execution.',
                 'QC semantic limitations preserved; metadata validation is not a new anatomical accuracy or training-memory certification.',
                 'Runtime final checkpoint stage BCSP_INPUT_DENSITY_V1 is legacy serialization provenance; new wrapper must log actual SCQ_RF stage explicitly.'],
    server_operations=0,payload_reads=0,checkpoint_loads=0,model_imports=0,CPU_contract_tests=0,
    production_edits=0,execution_request_created=False,execution_controls_materialized=False,training_started=False)
emit(O/'training_contract_and_entry_review_v1.json',review)
proposal=dict(status='PROPOSED_MINIMAL_SREF_C_ENTRY_ADAPTATION_NOT_EXECUTION_REQUEST',execution_authorized=False,
    scope='One S-ref Fold C isolated entry, minimal bridge admission adapter, targeted CPU test and P3; no framework or GPU preflight extension',
    permitted_candidate_files=['bcsp_scq_rf_Sref_C_training_entry_v1.py','bcsp_scq_rf_training_bridge_v1.py','test_scq_rf_Sref_C_entry_cpu_v1.py'],
    unchanged=[rec(paths[k]) for k in ('runtime','contract')]+[q['order_plan'],q['static_config'],q['initialization']],
    bind_admission=rec(audit_path),scientific_contract=review['scientific_contract'],resources=static['resources'],
    required_checks=['Actual authorize() with current admission/QC/order files on artificial filesystem fixture; reject stale admission, B-before-S baseline, wrong fold/device/hash/count.',
                     'Full shared state fingerprint includes SCQ and matches the admitted S-ref reference; no RF head installed.',
                     'Unchanged runtime dispatch, no-decay policy, geometry logging and3900-step accounting, fail-stop and one-way authorization/runtime.',
                     'Static rendering contract and exact source/bin read bindings; do not generate runnable controls before separate execution authorization.'],
    success='After one targeted CPU batch and P3, create final versioned pending execution request with final implementation hashes.',
    forbidden=['Changing model/data/sampling/loss/optimizer/order/3900/resources','GPU preflight repetition or real training/evaluation/BNCal','Reusing old training request or historical B as a required matched reference'])
emit(O/'minimal_entry_adaptation_scope_v1.json',proposal)
print(json.dumps(dict(status=review['status'],cases=315,steps=3900,exposures=31200,drops=300,order_SHA256=m.canonical_sha(plan),current_common_state_SHA256=current_common,request_created=False)))
