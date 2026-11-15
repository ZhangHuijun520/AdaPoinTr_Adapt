"""P3 and pending first S-ref_C request after successful UTC-fixture CPU batch."""
from pathlib import Path,PurePosixPath
import ast,copy,hashlib,importlib.util,json,shutil,sys,tarfile

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1'
RF=R/'outputs/scq_rf_initialization_loader_20261114_v2'


def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)


ctx=read(O/'context_v1.json');q=copy.deepcopy(ctx['candidate']);C=ctx['remote_root']
entry=O/'bcsp_scq_rf_Sref_C_training_entry_v1.py';bridge=O/'bcsp_scq_rf_training_bridge_v1.py';test=O/'test_scq_rf_Sref_C_entry_cpu_v2.py'
static=read(O/'static_review_v1.json');fixture=read(O/'fixture_v2_static_review.json');prior=read(O/'P3_gap_review_v1.json')
for row in [static['entry'],static['bridge'],static['unchanged_runtime'],static['unchanged_contract'],prior['test'],prior['failure'],prior['child_stderr'],prior['child_stdout']]:assert rec(Path(row['path']))==row
cpu_path=O/'cpu_entry_batch_v2/result_v1.json';cpu=read(cpu_path)
assert cpu['status']=='RF_SREF_TRAINING_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['count']==len(cpu['checks'])==len(set(cpu['checks']))==36
assert cpu['entry']==rec(entry) and cpu['bridge']==rec(bridge) and cpu['test']==rec(test)==fixture['test']
assert cpu['optimizer_steps']==cpu['CUDA_calls']==cpu['server_operations']==cpu['real_payload_arrays_read']==0
assert not (O/'cpu_entry_batch_v2/failure_v1.json').exists()
assert all(read(O/'cpu_entry_batch_v2/policy_stdout.bin').values()) and (O/'cpu_entry_batch_v2/policy_stderr.bin').stat().st_size==0
for p in (entry,bridge,test):compile(p.read_bytes(),str(p),'exec')
p3=dict(status='RF_SREF_C_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],bridge_sha256=rec(bridge)['sha256'],
    native_admission_sha256=q['admission']['audit']['sha256'],CPU_checks=36,CPU=rec(cpu_path),test=rec(test),
    static_review=rec(O/'static_review_v1.json'),fixture_review=rec(O/'fixture_v2_static_review.json'),
    previous_CPU_failure=rec(O/'cpu_entry_batch_v1/failure_v1.json'),CPU_attempts=2,
    unchanged_runtime=static['unchanged_runtime'],unchanged_metadata_contract=static['unchanged_contract'],
    checks=dict(all36_current_CPU_checks_pass=True,actual_authorize_current_admission_QC_order=True,Sref_first_no_old_B=True,
                full_shared_state_scope_includes_SCQ=True,no_RF_second_head=True,original_runtime_and3900_unchanged=True,
                no_decay_markers_and_geometry_loss_dispatch=True,actual_source_bin_train_only_policy=True,
                artificial_utc_context_supplied=True,one_way_authorization_runtime=True,
                production_entry_bridge_unchanged_during_fixture_fix=True,original_failure_preserved=True,no_server_GPU_or_training=True),
    limitations=cpu['limitations']+['CPU file policy uses a supplied UTC stub; actual UTC reader and native backend covered by the separately frozen CUDA evidence.',
                                   'No fresh server identity/315 payload hash verification this turn. Requires exact checks before installation/launch.'],
    server_operations=0,CUDA_calls=0,training_started=False)
emit(O/'training_entry_P3_v1.json',p3)
T=O/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir()
names=[entry.name,bridge.name,test.name,'training_entry_P3_v1.json','static_review_v1.json','fixture_v2_static_review.json',
       'RF_six_run_contract_v1.json','FoldC_readiness_v1.json','RF_CUDA_freeze_audit_v3.json','RF_CUDA_inventory_v3.json',
       'RF_CUDA_construction_v3.json','RF_CUDA_completion_v3.json','RF_CUDA_request_v3.json']
for name in names:shutil.copyfile(O/name,P/name)
shutil.copyfile(cpu_path,P/'training_CPU_result_v2.json')
q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION'
q['P3']=rec(O/'training_entry_P3_v1.json',C+'/training_entry_P3_v1.json')
q['CPU_evidence']=rec(P/'training_CPU_result_v2.json',C+'/training_CPU_result_v2.json')
q['resources']=read(R/'outputs/scq_rf_Sref_C_training_review_20261114_v1/training_contract_and_entry_review_v1.json')['resources']
q['science']=dict(train_sources=63,train_cases=315,batch=8,traversals=100,batches_per_traversal=39,updates=3900,exposures=31200,drops=300,
                  n_input=8192,n_output=8192,seed=0,from_scratch=True,optimizer='AdamW',BNCal=False,evaluation=False,resume=False,retry=False)
q['checkpoint_selection']='Only fixed epoch99 step3900 final checkpoint. Legacy checkpoint stage field retained as provenance; actual stage/arm in run_identity.json.'
q['shared_initialization_contract']='Full persistent original S state including SCQ/BN matches current same-device CUDA S-ref; no RF head; no history checkpoint loading.'
q['numeric_disclosure']='FP32, TF32=false; inherited accepted finite gradient non-bitwise reproducibility. Do not require exact equality of repeated native backward values.'
q['activation_prerequisites']=['Separate full request SHA256 authorization','Fresh exact hostname GPU UUID driver interpreter/provider and all reused file hashes',
    'Upload archive+3 sidecars verified; new15 targets/control/output absent; exclusive writes and original ancestor link checks',
    '315 exact Fold C training payload hashes and source identity; no development/confirmation payload reads',
    'Initially GPU<=256MiB, free disk>=4GiB and cumulative archive budget assessed; all frozen runtime thresholds enforced',
    'Authorization -> authorizationSHA -> one-way runtime -> original-byte launcher -> exclusive claim -> unique tmux; failure stop, no automatic retry/resume']
q['stage_matrix_note']='First only S-ref_C. Later Static/Requery and Fold D require separate preparation and execution authorizations.'
mirror={k:Path(v) for k,v in ctx['mirror'].items()};mirror[q['P3']['path']]=O/'training_entry_P3_v1.json'
for p in P.iterdir():mirror[C+'/'+p.name]=p
# Only metadata/source records become a fresh-reverification allowlist. No implicit payload access.
reused={}
def collect(value):
    if isinstance(value,dict):
        if {'path','bytes','sha256'}<=set(value):
            if str(value['path']).startswith('/') and not str(value['path']).startswith(C+'/'):
                reused[value['path']]={k:value[k] for k in ('path','bytes','sha256')}
        else:
            for item in value.values():collect(item)
    elif isinstance(value,list):
        for item in value:collect(item)
collect({k:q[k] for k in ('implementation','static_config','QC','order_plan','initialization','dependencies','preflight_scope')})
scope_path=R/'outputs/cranial_bcsp_geov1_20261024/actual_proxy_trace_20261102_v1/observed_server_frozen_scope_v3.json'
scope=read(scope_path);assert rec(scope_path)['sha256']==q['preflight_scope']['sha256']
sources={r['relative_path']:r for r in scope['bindings']['isolated_model_project_sources']}
sources.update({r['relative_target']:r for r in scope['bindings']['candidate']})
for relative,row in sources.items():
    assert not PurePosixPath(relative).is_absolute() and '..' not in PurePosixPath(relative).parts
    reused[q['model_root']+'/'+relative]=dict(path=q['model_root']+'/'+relative,bytes=row['bytes'],sha256=row['sha256'])
for row in scope['bindings']['provider']+scope['bindings']['environment_metadata']:
    reused[row['path']]={k:row[k] for k in ('path','bytes','sha256')}
cfg=scope['bindings']['base_config'];reused[q['model_root']+'/base_model.yaml']=dict(path=q['model_root']+'/base_model.yaml',bytes=cfg['bytes'],sha256=cfg['sha256'])
q['reused_readonly_bindings']=list(reused.values())
request=P/'SCQ_RF_Sref_C_training_execution_request_v1.json';emit(request,q);QH=rec(request)['sha256']
mirror[q['launch_contract']['request_path']]=request
# Exercise final actual authorize path with pure metadata and memory-only synthetic controls.
spec=importlib.util.spec_from_file_location('RF_Sref_final_metadata_contract_only',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
exact=e.exact
e.exact=lambda r:exact(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else exact(r)
original_source=e.source_module
def source_module(name,record):
    m=original_source(name,record)
    if name=='bcsp_training_contract_v1':
        f=m.exact;m.exact=lambda r:f(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else f(r)
    return m
e.source_module=source_module
auth=dict(schema='bcsp-scq-rf-training-authorization-v1',request_sha256=QH,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_FINAL_CONTRACT_ONLY_NOT_USER_EXECUTION_AUTHORIZATION')
ar=dict(path='MEMORY_ONLY_AUTH',bytes=0,sha256='a'*64);rr=dict(path='MEMORY_ONLY_RUNTIME',bytes=0,sha256='b'*64)
runtime=dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=QH,authorization_sha256='a'*64)
bound=e.bound;e.bound=lambda r:auth if r['path']==ar['path'] else runtime if r['path']==rr['path'] else bound(r)
sys.modules.pop('bcsp_training_contract_v1',None)
_,static_config,metadata,selected,fold,plan,admission,common=e.authorize(rec(request,q['launch_contract']['request_path']),ar,rr)
assert len(selected)==315 and static_config['counts']==e.COUNTS and common==read(O/'RF_six_run_contract_v1.json')['expected_Sref_common_state_SHA256']
launcher=e.render_launcher(q,QH,'a'*64,'b'*64)
assert launcher.index('mkdir -p')<launcher.index(' >') and '\\' not in launcher.replace('\\n','') and max(len(line.encode()) for line in launcher.splitlines())<=2048
emit(O/'final_authorize_contract_review_v1.json',dict(status='FINAL_PENDING_SREF_C_AUTHORIZE_PATH_PASS',request=rec(request),entry=rec(entry),bridge=rec(bridge),
    CPU_checks=36,counts=e.COUNTS,resources=e.RESOURCES,common_state_SHA256=common,server_operations=0,model_imports=0,
    real_payload_reads=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
files=[dict(member='payload/'+p.name,target=C+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())]
assert len(files)==15
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=QH,remote_root=C,files=files,
    new_control_directory=C+'/control',new_output=q['output'],preconditions=q['activation_prerequisites'],
    no_runtime_launcher_or_training_materialized=True,source_metadata_only_archive_no_real_points_or_checkpoints=True)
emit(T/'installation_mapping_v1.json',mapping)
arc=T/'bcsp_scq_rf_Sref_foldC_training_pending_20261114_v1.tar.gz'
with arc.open('xb') as raw:
    with tarfile.open(fileobj=raw,mode='w:gz') as tar:
        tar.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
        for p in sorted(P.iterdir()):tar.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(arc) as tar:
    members=tar.getmembers();assert len(members)==16 and len({m.name for m in members})==16 and all(m.isfile() for m in members)
    listing=''.join(hashlib.sha256(tar.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(arc)['sha256']+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:
    with Path(str(arc)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'pending_delivery_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_REQUEST_SHA256_EXECUTION_AUTHORIZATION',request=rec(request),archive=rec(arc),
    installation_mapping=rec(T/'installation_mapping_v1.json'),P3=rec(O/'training_entry_P3_v1.json'),CPU_checks=36,install_files=15,archive_members=16,
    reused_assets=len(reused),stage='SCQ_RF',arm='S-ref',fold='C',steps=3900,server_operations=0,CUDA_calls=0,training_started=False,controls_materialized=False))
emit(O/'final_request_local_mirror_v1.json',{k:str(v.resolve()) for k,v in mirror.items()})
print(json.dumps(dict(status='SREF_C_P3_PASS_PENDING_REQUEST_FROZEN',request_SHA256=QH,archive=rec(arc),CPU_checks=36,install_files=15)))
