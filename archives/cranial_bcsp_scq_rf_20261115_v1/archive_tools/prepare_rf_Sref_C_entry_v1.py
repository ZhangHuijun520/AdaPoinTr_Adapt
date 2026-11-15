"""Prepare isolated S-ref_C entry/bridge and frozen context. No tests or server calls."""
from pathlib import Path
import ast,copy,hashlib,json,shutil

R=Path(__file__).resolve().parent.parent
OLD=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1'
RF=R/'outputs/scq_rf_initialization_loader_20261114_v2'
O=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1';O.mkdir()
REMOTE='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1'


def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)


review=read(R/'outputs/scq_rf_Sref_C_training_review_20261114_v1/training_contract_and_entry_review_v1.json')
for row in review['sources'].values():assert rec(Path(row['path']))==row
audit_path=RF/'post_CUDA_freeze_audit_v3/freeze_verification_v3.json'
AH=rec(audit_path)['sha256']
src=Path(review['sources']['entry']['path']).read_text(encoding='utf-8')
src=src.replace('SCQ Fold C B/S training entry.', 'RF-stage S-ref Fold C isolated training entry.')
src=src.replace("ADMISSION_SHA='f7fad610b67d96da91c02c6ff879f861d4b101851db5548b05b3117345512895'","ADMISSION_SHA="+repr(AH))
src=src.replace("CUDA_REQUEST_SHA='0f5aec8c30d0044547cd8806c5663aeb4f0f9643e254a65ce562f5d45641521b'","CUDA_REQUEST_SHA='8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'")
begin=src.index('def validate_admission(q):');end=src.index('\ndef scq_geometry(',begin)
replacement='''def validate_admission(q):
    a=q['admission'];require(set(a)=={'audit','inventory','construction','completion','request'},'admission fields')
    require(a['audit']['sha256']==ADMISSION_SHA and a['request']['sha256']==CUDA_REQUEST_SHA,'current RF native admission anchors')
    audit=bound(a['audit']);inventory=bound(a['inventory']);cuda=bound(a['request']);construct=bound(a['construction']);complete=bound(a['completion'])
    counts=dict(full_forward=5,full_backward=4,full_loss=4,decoder_forward=0,decoder_backward=0,optimizer_steps=0)
    require(audit['status']=='FORMAL_RF_POST_CUDA_FREEZE_AUDIT_PASS' and audit['request_sha256']==CUDA_REQUEST_SHA and audit['counts']==counts and all(audit['checks'].values()),'formal RF audit')
    require(complete['counts']==counts and sum(complete['native_SSM_calls'].values())==180 and not complete['optimizer_constructed'] and complete['real_data_reads']==complete['checkpoint_loads']==0,'native5forward completion')
    for key in ('construction','completion'):
        r=inventory['files']['output/'+key+'.json'];require(all(r[k]==a[key][k] for k in ('bytes','sha256')),'audited '+key)
    for key in ('identity','model_root','preflight_scope','dependencies','environment'):
        require(q[key]==cuda[key],'same current admitted '+key)
    require(q['static_config']==cuda['static_config'] and q['initialization']==cuda['initialization'],'original static and SCQ initialization')
    for key in ('encoder','factory','lqi_decoder','lqi_factory','scq_residual','scq_factory','timezone'):
        require(q['implementation'][key]==cuda['implementation'][key],'admitted S-ref implementation '+key)
    rows=construct['models']
    require([r['phase'] for r in rows]==['S_ref_eval1','Static_eval1','Requery_eval1','Static_train8','Requery_train8'] and len({r['shared_initial_state_SHA256'] for r in rows})==1,'same full original S initial state')
    require(rows[0]['parameters']==40596676 and rows[0]['new_parameters']==0,'S-ref no second head')
    return dict(status='SCQ_RF_NATIVE_CUDA_ADMISSION_PASS',audit_sha256=ADMISSION_SHA,CUDA_request_sha256=CUDA_REQUEST_SHA),rows[0]['shared_initial_state_SHA256']


def authorize(qr,ar,rr):
    q=bound(qr);a=bound(ar);runtime=bound(rr)
    require(q['schema']=='bcsp-scq-rf-Sref-C-training-request-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False and q['stage']=='CRANIAL_BCSP_SCQ_RF','pending RF-stage training')
    require(q['arm']=='S-ref' and q['variant']=='S' and q['fold']=='C' and q['seed']==0 and q['n_input']==q['n_output']==8192,'S-ref_C first run only')
    require(q['run_id'].startswith('SCQ_RF_Sref_foldC_seed0_train_') and Path(q['output']).name==q['run_id'] and q['paired_baseline'] is None,'scratch S-ref first without old B baseline')
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-scq-rf-training-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate execution authorization')
    require(runtime==dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
    for key,r in q['implementation'].items():
        if key in PINS:require(r['sha256']==PINS[key],'unchanged '+key)
        exact(r)
    p3=bound(q['P3']);require(p3['status']=='RF_SREF_C_TRAINING_ENTRY_LOCAL_P3_PASS' and p3['entry_sha256']==q['implementation']['entry']['sha256'] and p3['bridge_sha256']==q['implementation']['bridge']['sha256'] and p3['native_admission_sha256']==ADMISSION_SHA,'new entry P3')
    admission,common=validate_admission(q)
    exact(q['initialization']);ready=bound(q['readiness'])
    require(ready['status']=='LOCAL_METADATA_VERIFIED_FRESH_SERVER_CHECK_REQUIRED' and ready['fresh_reverification_required'] is True and ready['payload_arrays_read']==0,'fresh readiness required')
    metadata=source_module('bcsp_training_contract_v1',q['implementation']['contract'])
    static=metadata.validate_static(bound(q['static_config']));require(static['counts']==COUNTS and static['resources']==RESOURCES,'unchanged3900 and resources')
    selected,fold=metadata.verify_qualified_receipt(bound(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192)
    plan=metadata.validate_order(bound(q['order_plan']),fold['train_case_ids'])
    pair=bound(q['pair_contract'])
    require(pair['status']=='FROZEN_RF_SREF_STATIC_REQUERY_CD_CONTRACT_NOT_AUTHORIZATION' and pair['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'] and pair['counts']==COUNTS and pair['resources']==RESOURCES and pair['seed']==0,'fixed new six-run order')
    require(pair['identity']==q['identity'] and pair['FoldC']['QC']==q['QC'] and pair['FoldC']['order_plan']==q['order_plan'] and pair['FoldC']['data_root']==q['data_root'] and pair['static_config']==q['static_config'] and pair['native_admission_sha256']==ADMISSION_SHA,'current RF pairing and metadata')
    require(pair['initialization']==q['initialization'] and pair['expected_Sref_common_state_SHA256']==common,'full original S initial state includes SCQ')
    return q,static,metadata,selected,fold,plan,admission,common

'''
src=src[:begin]+replacement+src[end:]
src=src.replace("if not n.startswith('base_model.scq.')","if not n.startswith('base_model.rf.')")
anchor="    helper.validate_model(model)\n"
assert src.count(anchor)==1
src=src.replace(anchor,anchor+"    require(not hasattr(model.base_model,'rf'),'S-ref must not install RF second head')\n    if not artificial_cpu:require(evidence['scq']['total_parameters']==40596676,'native S-ref parameter count')\n")
src=src.replace("variant=q['variant'])","variant=q['variant'],arm=q['arm'],stage=q['stage'])")
src=src.replace("dict(stage=q['stage'],variant=q['variant'],fold='C'", "dict(stage=q['stage'],arm=q['arm'],variant=q['variant'],fold='C'")
entry=O/'bcsp_scq_rf_Sref_C_training_entry_v1.py';compile(src,str(entry),'exec')
with entry.open('x',encoding='utf-8',newline='\n') as f:f.write(src)
bridge_src=Path(review['sources']['bridge']['path']).read_text(encoding='utf-8').replace('Thin SCQ caller bridge.','Thin RF-stage S-ref caller bridge.').replace('SCQ_NATIVE_CUDA_ADMISSION_PASS','SCQ_RF_NATIVE_CUDA_ADMISSION_PASS')
bridge=O/'bcsp_scq_rf_training_bridge_v1.py';compile(bridge_src,str(bridge),'exec')
with bridge.open('x',encoding='utf-8',newline='\n') as f:f.write(bridge_src)
# Context files, not request/authorization/runtime. Exact metadata references stay unchanged.
old_request=OLD/'S_C_pending_preparation_v1/pending_transport_v1/payload/SCQ_S_FoldC_training_execution_request_v1.json'
q=read(old_request);cuda_path=RF/'pending_transport_v3/payload/SCQ_RF_artificial_cuda_execution_request_v3.json';cuda=read(cuda_path)
parent_context=read(OLD/'training_context_candidate_v1.json');mirror=dict(parent_context['mirror'])
for row in review['verified_metadata']:mirror[row['remote']['path']]=row['local']['path']
proof={}
for key,path,name in [('audit',audit_path,'RF_CUDA_freeze_audit_v3.json'),
                     ('inventory',RF/'post_CUDA_freeze_audit_v3/inventory_before_result_v1.json','RF_CUDA_inventory_v3.json'),
                     ('construction',RF/'post_CUDA_freeze_audit_v3/downloads/output/construction.json','RF_CUDA_construction_v3.json'),
                     ('completion',RF/'post_CUDA_freeze_audit_v3/downloads/output/completion.json','RF_CUDA_completion_v3.json'),
                     ('request',cuda_path,'RF_CUDA_request_v3.json')]:
    target=O/name;shutil.copyfile(path,target);proof[key]=rec(target,REMOTE+'/'+name);mirror[proof[key]['path']]=str(target.resolve())
impl=dict(q['implementation'])
for k in ('encoder','factory','lqi_decoder','lqi_factory','scq_residual','scq_factory','timezone'):impl[k]=cuda['implementation'][k]
impl.update(entry=rec(entry,REMOTE+'/'+entry.name),bridge=rec(bridge,REMOTE+'/'+bridge.name),preflight_helper=cuda['helper'],native_helper=cuda['parent_helper'],cuda_entry=cuda['entry'])
mirror[impl['entry']['path']]=str(entry.resolve());mirror[impl['bridge']['path']]=str(bridge.resolve())
source_mirror=read(R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2/pending_request_v2/local_mirror_v2.json')
mirror.update(source_mirror)
known=dict(encoder=R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_mamba_encoder_v1.py',factory=R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_model_factory_v1.py',
    lqi_decoder=R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1/bcsp_lqi_decoder_v1.py',lqi_factory=R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1/bcsp_lqi_factory_v1.py',
    scq_residual=R/'outputs/cranial_bcsp_scq_implementation_20261113_v1/bcsp_scq_residual_v1.py',scq_factory=R/'outputs/cranial_bcsp_scq_implementation_20261113_v1/bcsp_scq_factory_v1.py',
    timezone=R/'outputs/cranial_bcsp_mamba_p1_20261104/gpu_admission_v3/exact_utc_resource_v1.py',
    preflight_helper=R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py',
    native_helper=R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_native_prediction_implementation_v1/bcsp_lqi_twofold_native_predict_v1.py',
    cuda_entry=R/'outputs/scq_rf_cuda_preparation_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py')
for key,path in known.items():assert rec(path)['sha256']==impl[key]['sha256'];mirror[impl[key]['path']]=str(path.resolve())
mirror[cuda['initialization']['path']]=str(R/'outputs/cranial_bcsp_scq_implementation_20261113_v1/initialization_v1.bin')
pair=dict(status='FROZEN_RF_SREF_STATIC_REQUERY_CD_CONTRACT_NOT_AUTHORIZATION',arm_order=['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'],
    seed=0,counts=review['scientific_contract'] | {},resources=review['resources'])
pair['counts']={k:review['scientific_contract'][k] for k in ('batch','epochs','batches_per_epoch','updates','exposures')}
pair['counts'].update(cases=315,sources=63)
pair.update(identity=cuda['identity'],FoldC=dict(QC=q['QC'],order_plan=q['order_plan'],data_root=q['data_root']),static_config=q['static_config'],
    initialization=cuda['initialization'],native_admission_sha256=AH,expected_Sref_common_state_SHA256=review['expected_common_full_S_state_SHA256'],
    from_scratch=True,load_historical_checkpoint=False,scientific_changes_for_first_run='None: same original S architecture, same V1 points/order/loss3900, fresh same-device reference')
emit(O/'RF_six_run_contract_v1.json',pair);pair_rec=rec(O/'RF_six_run_contract_v1.json',REMOTE+'/RF_six_run_contract_v1.json');mirror[pair_rec['path']]=str(O/'RF_six_run_contract_v1.json')
ready=dict(status='LOCAL_METADATA_VERIFIED_FRESH_SERVER_CHECK_REQUIRED',fresh_reverification_required=True,payload_arrays_read=0,payload_files_hashed=0,
    current_identity_source=rec(audit_path),server_checked_this_preparation=False,
    before_write=['Full request execution authorization','Fresh identity resources and all reused files','315 exact train payload hashes; no dev/confirmation payload access','All new targets and controls absent; no symlink ancestors or overwrite'],
    budget_note='Keep4GiB per-run free disk minimum and plan total archive capacity before six-run matrix; no hard-cgroup/PID ownership framework')
emit(O/'FoldC_readiness_v1.json',ready);ready_rec=rec(O/'FoldC_readiness_v1.json',REMOTE+'/FoldC_readiness_v1.json');mirror[ready_rec['path']]=str(O/'FoldC_readiness_v1.json')
q.update(schema='bcsp-scq-rf-Sref-C-training-request-v1',status='DRAFT_NOT_EXECUTABLE',execution_authorized=False,stage='CRANIAL_BCSP_SCQ_RF',arm='S-ref',variant='S',
    run_id='SCQ_RF_Sref_foldC_seed0_train_20261114_v1',identity=cuda['identity'],implementation=impl,admission=proof,pair_contract=pair_rec,readiness=ready_rec,
    paired_baseline=None,environment=cuda['environment'],dependencies=cuda['dependencies'],preflight_scope=cuda['preflight_scope'],model_root=cuda['model_root'],initialization=cuda['initialization'])
q['output']='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/'+q['run_id']
q['launch_attempt']=REMOTE+'/control/attempt_claim_v1.json'
q['launch_contract']=dict(tmux_session='bcsp_scq_rf_Sref_C_train_20261114_v1',request_path=REMOTE+'/SCQ_RF_Sref_C_training_execution_request_v1.json',
    authorization_path=REMOTE+'/control/authorization_v1.json',runtime_path=REMOTE+'/control/runtime_v1.json',launcher_path=REMOTE+'/control/launch_once_v1.sh',
    original_file_byte_transport=True,parent_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,automatic_retry=False,resume=False,
    log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
q['P3']=dict(path=REMOTE+'/training_entry_P3_v1.json',bytes=0,sha256='0'*64)
q['not_authorized']=['Execution before separate full request SHA256 authorization','Warmstart/resume/retry','Other runs, BNCal, evaluation, GPU preflight repetition','Data outside exact315 training allowlist','Changes to model/loss/order/numeric runtime or resource thresholds']
emit(O/'context_v1.json',dict(status='IMPLEMENTATION_CONTEXT_NOT_EXECUTION_REQUEST',candidate=q,mirror=mirror,remote_root=REMOTE,review=rec(R/'outputs/scq_rf_Sref_C_training_review_20261114_v1/training_contract_and_entry_review_v1.json')))
oldtree=ast.parse(Path(review['sources']['entry']['path']).read_text(encoding='utf-8'));newtree=ast.parse(src)
funcs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
a,b=funcs(oldtree),funcs(newtree)
changed=[k for k in a if a[k]!=b[k]];assert set(changed)=={'validate_admission','authorize','dispatch_training','make_budget'}
emit(O/'static_review_v1.json',dict(status='RF_SREF_ENTRY_STATIC_PASS_NOT_CPU',entry=rec(entry),bridge=rec(bridge),changed_functions=changed,
    unchanged_runtime=review['sources']['runtime'],unchanged_contract=review['sources']['contract'],base_entry=review['sources']['entry'],base_bridge=review['sources']['bridge'],
    checks=dict(only_admission_authorization_identity_fingerprint_dispatch_metadata_changed=True,no_training_runtime_edit=True,no_model_or_data_edit=True,
                exact3900_resources_unchanged=True,latest_formal_CUDA_bound=True,Sref_first_no_old_B_baseline=True),server_operations=0,CPU_tests=0))
print(json.dumps(dict(status='SREF_C_ENTRY_BRIDGE_CONTEXT_STATIC_PASS',changed_functions=changed,metadata_sources=len(mirror),execution_request=False)))
