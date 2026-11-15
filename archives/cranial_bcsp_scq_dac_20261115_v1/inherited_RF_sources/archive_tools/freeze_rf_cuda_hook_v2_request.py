"""P3 and new pending request after one52-check hook CPU batch; no server calls."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,tarfile

R=Path(__file__).resolve().parent.parent
OLD=R/'outputs/scq_rf_cuda_preparation_20261114_v1'
O=R/'outputs/scq_rf_cuda_preparation_20261114_v2'
PROJECT='/home/jovyan/adapointr_work/PoinTr'
REMOTE=PROJECT+'/third_party/bcsp_scq_rf_cuda_20261114_v2'


def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_bytes())
def emit(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)


static=read(O/'static_review_v2.json')
entry=O/'bcsp_scq_rf_cuda_admission_v2.py';test=O/'test_rf_cuda_entry_cpu_v2.py'
assert static['entry']==rec(entry) and static['test']==rec(test) and all(static['checks'].values())
for row in static['preserved']+[static['prior_entry'],static['prior_test'],static['failure_audit']]:assert rec(Path(row['path']))==row
cpu=read(O/'cpu_entry_batch_v2/result_v1.json')
assert cpu['status']=='RF_CUDA_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['count']==len(cpu['checks'])==len(set(cpu['checks']))==52
assert cpu['entry']==rec(entry) and cpu['test']==rec(test) and not (O/'cpu_entry_batch_v2/failure_v1.json').exists()
assert cpu['engine_counts']==dict(full_forward=5,full_backward=4,full_loss=4,decoder_forward=0,decoder_backward=0,optimizer_steps=0)
assert len(cpu['phases'])==5
for p in cpu['phases']:
    c=p['coordinate_consumers'];assert c['exact_call_contract'] and c['call_counts']['PE']==2 and all(row['exact_equal'] for row in c['comparisons'])
negative_files=sorted((O/'cpu_entry_batch_v2').glob('*_diagnostic.json'))
assert len(negative_files)==6
for p in negative_files:
    d=read(p);assert not d['exact_call_contract'] or any(not r['exact_equal'] for r in d['comparisons'])
ip3=R/'outputs/scq_rf_implementation_20261114_v1/P3_implementation_v2.json'
assert read(ip3)['status']=='LOCAL_RF_IMPLEMENTATION_P3_PASS_ARTIFICIAL_CPU_ONLY'
p3=dict(status='RF_CUDA_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],test=rec(test),CPU=rec(O/'cpu_entry_batch_v2/result_v1.json'),
        CPU_entry_checks=52,CPU_implementation_checks=59,implementation_P3=rec(ip3),static_review=rec(O/'static_review_v2.json'),
        prior_failure_audit=static['failure_audit'],regression_evidence=[rec(p) for p in negative_files],
        checks=dict(original_RF_model_and_initialization_unchanged=True,only_phase_observation_contract_changed=True,
                    dual_PE_call_roles_and_exact_count=True,all_consumer_diagnostics_persist_before_assertions=True,
                    six_negative_contract_regressions_rejected=True,five_phase_engine5F4loss4B0step=True,
                    success_and_failure_restore_contract=True,authorization_and_resource_contracts_unchanged=True,
                    one_CPU_batch_no_retry=True,no_server_or_CUDA=True),
        limitations=cpu['limitations']+['The two-call fixture covers the actual PE role pattern; native CUDA has not run v2.'],
        CUDA=False,server_operations=0,scientific_efficacy='NOT_TESTED')
emit(O/'entry_P3_v2.json',p3)
T=O/'pending_transport_v2';T.mkdir();P=T/'payload';P.mkdir()
named=[(entry,entry.name),(test,test.name),(O/'entry_P3_v2.json','entry_P3_v2.json'),
       (O/'cpu_entry_batch_v2/result_v1.json','entry_CPU_result_v2.json'),(O/'static_review_v2.json','static_review_v2.json'),
       (OLD/'failed_freeze_hook_review_v1/formal_failure_freeze_audit_v1.json','prior_failed_freeze_audit_v1.json')]
for src,name in named:shutil.copyfile(src,P/name)
prior_path=OLD/'pending_transport_v1/payload/SCQ_RF_artificial_cuda_execution_request_v1.json'
old=read(prior_path);oldsha=rec(prior_path)['sha256']
assert oldsha=='85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'
q=copy.deepcopy(old);q['run_id']='SCQ_RF_artificial_cuda_20261114_v2'
q['entry']=rec(entry,REMOTE+'/'+entry.name)
q['entry_P3']=rec(O/'entry_P3_v2.json',REMOTE+'/entry_P3_v2.json')
q['output']=PROJECT+'/logs/cranial_bcsp_fullmamba/'+q['run_id']
q['launch_contract']=dict(tmux_session='bcsp_scq_rf_cuda_20261114_v2',
    request_path=REMOTE+'/SCQ_RF_artificial_cuda_execution_request_v2.json',authorization_path=REMOTE+'/control/authorization_v2.json',
    runtime_path=REMOTE+'/control/runtime_v2.json',launcher_path=REMOTE+'/control/launch_once_v2.sh',launch_attempt_path=REMOTE+'/control/attempt_claim_v2.json',
    log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt',
    materialization_order='authorization -> authorization SHA256 -> one-way runtime -> launcher -> exclusive claim -> tmux',
    parent_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,transport=old['launch_contract']['transport'],exclusive_single_attempt=True,automatic_retry=False)
q['readiness']['status']='LAST_FAILURE_AUDIT_IDENTITY_ONLY_REVERIFY_BEFORE_INSTALLATION'
q['readiness']['last_evidence']=rec(OLD/'failed_freeze_hook_review_v1/formal_failure_freeze_audit_v1.json')
q['readiness']['before_any_write'][2]='Upload archive and3 sidecars, exact member sets and bytes/SHA256; all7 new install targets and new control/output roots absent, original-path symlink checks; old installed RF files only exact read reuse'
q['supersedes']=dict(request_sha256=oldsha,status='ATTEMPTED_FAILED_CONSUMED_DO_NOT_REUSE',actual_counts=dict(forward=1,loss=0,backward=0,optimizer_steps=0),
                     reason='PE hook overwrote query snapshot with second Memory call; v1 failure remains unchanged',
                     failure_audit=rec(P/'prior_failed_freeze_audit_v1.json',REMOTE+'/prior_failed_freeze_audit_v1.json'))
q['coordinate_hook_contract']='One query-MLP, decoder q_pos, decoder v_pos, FC input and relative output; exactly2 calls on shared coordinate_pe: first q_pos/current coarse, second v_pos. Append snapshots, never overwrite; persist per-consumer roles/counts/shapes/dtype/device/finite/exact equality/max_abs BEFORE assertions. No tolerance widening.'
# Keep existing installed RF sources, initialization and implementationP3 as exact readonly reuse.
extra=[q['implementation']['rf_residual'],q['implementation']['rf_factory'],q['rf_initialization'],q['implementation_P3']]
lookup={r['path']:r for r in q['reused_readonly_bindings']}
for row in extra:
    canonical={k:row[k] for k in ('path','bytes','sha256')}
    if row['path'] in lookup:assert lookup[row['path']]==canonical
    lookup[row['path']]=canonical
q['reused_readonly_bindings']=list(lookup.values())
assert q['implementation']==old['implementation'] and q['initialization']==old['initialization'] and q['rf_initialization']==old['rf_initialization']
for key in ('science','phases','limits','fixture','tolerances','numeric','environment','dependencies','optimizer_policy','identity'):assert q[key]==old[key]
request=P/'SCQ_RF_artificial_cuda_execution_request_v2.json';emit(request,q);qh=rec(request)['sha256']
spec=importlib.util.spec_from_file_location('RF_v2_pending_contract_only',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
auth=dict(schema='bcsp-scq-rf-cuda-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_CONTRACT_ONLY_NOT_USER_AUTHORIZATION')
e.authorize(q,qh,auth,'a'*64,dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256=qh,authorization_sha256='a'*64))
script=e.render_launcher(q,qh,'a'*64,'b'*64)
assert script.index('mkdir -p')<script.index(' >') and '\\' not in script.replace('\\n','') and max(len(s.encode()) for s in script.splitlines())<=2048
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=REMOTE,
             files=[dict(member='payload/'+p.name,target=REMOTE+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())],
             read_only_reuse_of_RF_sources_and_initialization=True,preconditions=q['readiness']['before_any_write'],no_runtime_or_launcher_materialization=True)
assert len(mapping['files'])==7
emit(T/'installation_mapping_v2.json',mapping)
archive=T/'bcsp_scq_rf_artificial_cuda_pending_20261114_v2.tar.gz'
with archive.open('xb') as raw:
    with tarfile.open(fileobj=raw,mode='w:gz') as tar:
        tar.add(T/'installation_mapping_v2.json',arcname='installation_mapping_v2.json',recursive=False)
        for p in sorted(P.iterdir()):tar.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(archive) as tar:
    members=tar.getmembers();assert len(members)==8 and all(m.isfile() for m in members)
    listing=''.join(hashlib.sha256(tar.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(archive)['sha256']+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',listing)]:
    with Path(str(archive)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'pending_delivery_v2.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_AUTHORIZATION',request=rec(request),archive=rec(archive),mapping=rec(T/'installation_mapping_v2.json'),
    entry=rec(entry),entry_P3=rec(O/'entry_P3_v2.json'),CPU_entry_checks=52,CPU_implementation_checks=59,
    install_files=7,archive_members=8,RF_model_initialization_and_limits_unchanged=True,previous_request_consumed=True,
    server_operations=0,CUDA_calls=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,training_request_created=False))
print(json.dumps(dict(status='V2_RF_CUDA_PENDING_REQUEST_FROZEN',request_sha256=qh,archive=rec(archive),install_files=7,CPU_checks=52)))
