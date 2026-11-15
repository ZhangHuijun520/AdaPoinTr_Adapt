"""Freeze RF-specific pending CUDA request/transport, without server access."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import shutil
import tarfile

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_cuda_preparation_20261114_v1'
M=R/'outputs/scq_rf_implementation_20261114_v1'
PROJECT='/home/jovyan/adapointr_work/PoinTr'
REMOTE=PROJECT+'/third_party/bcsp_scq_rf_cuda_20261114_v1'


def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_bytes())
def emit(p,j):
    if p.exists():
        assert read(p)==j, 'partial local preparation differs: '+str(p)
        return
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,ensure_ascii=False,indent=2,allow_nan=False)


entry=O/'bcsp_scq_rf_cuda_admission_v1.py';test=O/'test_rf_cuda_entry_cpu_v1.py'
spec=importlib.util.spec_from_file_location('rf_cuda_entry_static_contract',entry)
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
cpu=read(O/'cpu_entry_batch_v1/result_v1.json')
assert cpu['status']=='RF_CUDA_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['count']==len(cpu['checks'])==37
assert cpu['entry']==rec(entry) and cpu['test']==rec(test) and not (O/'cpu_entry_batch_v1/failure_v1.json').exists()
ip3=read(M/'P3_implementation_v2.json')
assert ip3['status']=='LOCAL_RF_IMPLEMENTATION_P3_PASS_ARTIFICIAL_CPU_ONLY' and ip3['CPU_checks']==59
for row in ip3['candidate_sources']+ip3['initialization']+ip3['artifacts']+[ip3['test'],ip3['static_review']]:
    assert rec(Path(row['path']))==row
for p in (entry,test):
    compile(p.read_bytes(),str(p),'exec')
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='step' for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))))
prior_path=R/'outputs/cranial_bcsp_scq_cuda_preparation_20261113_v1/pending_transport_v1/payload/SCQ_artificial_cuda_execution_request_v1.json'
prior=read(prior_path)
capture_path=R/'outputs/scq_rf_capture_implementation_20261114_v1/pending_request_v1/payload/SCQ_RF_ten_memory_execution_request_v1.json'
current=read(capture_path)
audit_path=R/'outputs/scq_rf_audit_20261114_v1/formal_post_diagnostic_freeze_audit_v1.json'
audit=read(audit_path);assert audit['status']=='FORMAL_SCQ_RF_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS' and all(audit['checks'].values())
assert rec(capture_path)['sha256']==audit['request_sha256']
ep3=dict(status='RF_CUDA_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],test=rec(test),CPU=rec(O/'cpu_entry_batch_v1/result_v1.json'),
         implementation_P3=rec(M/'P3_implementation_v2.json'),CPU_entry_checks=37,CPU_implementation_checks=59,
         inherited_engine=rec(R/'outputs/cranial_bcsp_scq_cuda_preparation_20261113_v1/bcsp_scq_cuda_admission_v3.py'),
         checks=dict(exact5F4loss4B0step=True,Sref_forward_only=True,one_way_authorization_runtime=True,attempt_caps_before_call=True,
                     actual_phase_engine_with_cheap_CPU_facade=True,initial_same_session_equivalence=True,
                     gradient_evidence_before_assertions=True,zero_output_layer_gradient_expectations=True,
                    _state_RNG_BN_modes_restore_success_and_failure=True,RF_sources_initializer_exact_read_wrapper=True,
                    _POSIX_launcher_parent_before_redirect_and_exit_preserved=True,implementation_and_initialization_unchanged=True),
         CUDA=False,server_operations=0,limitations=cpu['limitations'],readiness='Last zbpgzu-0 audit is historical evidence only; mandatory exact identity/hash/resource/target checks before any installation and activation.')
emit(O/'entry_P3_v1.json',ep3)
T=O/'pending_transport_v1';T.mkdir(exist_ok=True);P=T/'payload';P.mkdir(exist_ok=True)
named=[(entry,entry.name),(M/'bcsp_scq_rf_residual_v1.py','bcsp_scq_rf_residual_v1.py'),(M/'bcsp_scq_rf_factory_v1.py','bcsp_scq_rf_factory_v1.py'),
       (M/'initialization_v1.bin','rf_initialization_v1.bin'),(M/'initialization_manifest_v1.json','rf_initialization_manifest_v1.json'),
       (M/'P3_implementation_v2.json','implementation_P3_v2.json'),(O/'entry_P3_v1.json','entry_P3_v1.json'),
       (O/'cpu_entry_batch_v1/result_v1.json','entry_CPU_result_v1.json'),(M/'cpu_batch_v2/result_v2.json','implementation_CPU_result_v2.json'),
       (test,test.name),(M/'test_scq_rf_cpu_v2.py','test_scq_rf_cpu_v2.py')]
for src,name in named:
    if (P/name).exists():assert (P/name).read_bytes()==src.read_bytes()
    else:shutil.copyfile(src,P/name)
impl={k:copy.deepcopy(v) for k,v in current['implementation'].items() if k!='cuda_entry'}
impl.update(rf_residual=rec(P/'bcsp_scq_rf_residual_v1.py',REMOTE+'/bcsp_scq_rf_residual_v1.py'),rf_factory=rec(P/'bcsp_scq_rf_factory_v1.py',REMOTE+'/bcsp_scq_rf_factory_v1.py'))
runtime=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/bcsp_p1_training_runtime_v1.py'
runtime_record=rec(runtime,PROJECT+'/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_p1_training_runtime_v1.py')
# Bind only relevant existing files; no real input, GT or checkpoint allowlist.
reused=[current[k] for k in ('helper','preflight_scope','static_config','initialization')]+[prior['parent_helper'],runtime_record]
reused+=list({k:v for k,v in impl.items() if not k.startswith('rf_')}.values())+current['dependencies']
# Include exact source/provider/config identities covered by the last finite audit.
scope_file=R/'outputs/cranial_bcsp_geov1_20261024/actual_proxy_trace_20261102_v1/observed_server_frozen_scope_v3.json'
frozen_scope=read(scope_file)
assert rec(scope_file)['sha256']==current['preflight_scope']['sha256']
bindings=frozen_scope['bindings']
for group in ('provider','environment_metadata'):
    reused+=bindings[group]
base_config=bindings['base_config']
reused.append(dict(path=current['model_root']+'/base_model.yaml',bytes=base_config['bytes'],sha256=base_config['sha256']))
source_map={row['relative_path']:row for row in bindings['isolated_model_project_sources']}
source_map.update({row['relative_target']:row for row in bindings['candidate']})
for relative,row in source_map.items():
    assert not relative.startswith('/') and '..' not in Path(relative).parts and '\\' not in relative
    reused.append(dict(path=current['model_root']+'/'+relative,bytes=row['bytes'],sha256=row['sha256']))
# Source-map format follows the already tested helper; exact main() repeats this map at activation.
dedup={}
for row in reused:
    canonical={k:row[k] for k in ('path','bytes','sha256')}
    if row['path'] in dedup:assert dedup[row['path']]==canonical
    dedup[row['path']]=canonical
run='SCQ_RF_artificial_cuda_20261114_v1'
q=dict(schema='bcsp-scq-rf-artificial-cuda-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,
       run_id=run,date='2026-11-14',project=PROJECT,identity=current['identity'],environment=current['environment'],model_root=current['model_root'],
       helper=current['helper'],parent_helper=prior['parent_helper'],preflight_scope=current['preflight_scope'],static_config=current['static_config'],
       timezone_resource=prior['timezone_resource'],dependencies=current['dependencies'],implementation=impl,initialization=current['initialization'],
       rf_initialization=rec(P/'rf_initialization_v1.bin',REMOTE+'/rf_initialization_v1.bin'),optimizer_policy=runtime_record,
       entry=rec(entry,REMOTE+'/'+entry.name),entry_P3=rec(P/'entry_P3_v1.json',REMOTE+'/entry_P3_v1.json'),
       implementation_P3=rec(P/'implementation_P3_v2.json',REMOTE+'/implementation_P3_v2.json'),
       output=PROJECT+'/logs/cranial_bcsp_fullmamba/'+run,science=e.SCIENCE,phases=[list(p) for p in e.PHASES],limits=e.LIMITS,fixture=e.FIXTURE,tolerances=e.TOLERANCE,
       reused_readonly_bindings=list(dedup.values()),
       readiness=dict(status='HISTORICAL_AUDITED_IDENTITY_NOT_CURRENT_LIVENESS',fresh_reverification_required=True,
                      server_checked_this_turn=False,last_evidence=rec(audit_path),
                      before_any_write=['Separate full request SHA256 execution authorization','Exact hostname UID project Python environment provider GPU UUID and driver; mismatch stops, no automatic rebind',
                                        'Upload archive and3 sidecars, exact member sets and bytes/SHA256; all12 install targets and new control/output roots absent, original-path symlink checks',
                                        'All reused bindings and frozen source-map/provider/config hashes; no data/checkpoint reads',
                                        'Initially SMI used<=256MiB, disk free>=4GiB; native runtime limits unchanged'],
                      before_launch='Repeat installed/reused identities and resources, fixed tmux absent, one exclusive claim; failure consumes attempt'),
       numeric=prior['numeric'],resource_policy=prior['resource_policy'],
       initial_equivalence='One S-ref eval forward only; Static and Requery eval compare to that same-session reference at atol1e-6/rtol1e-5; no extra baseline/warmup forward.',
       gradient_contract='Four RF loss/backward phases: all inherited35 shared module prefixes finite active; Q2 finite active; first-head W2 and RF V2 weight/bias finite active; W1/V1 weight/bias zero expected with zero output weights. Record before assertions; nonzero diagnostic heads already CPU-only tested, no additional CUDA intervention.',
       common_state='Full shared model and original SCQ state hashes identical across5 builds; only RF head excluded. RF-Static/Requery share frozen RF initialization bytes.',
       native_calls='Exactly5 whole-model forwards,22 native modules,180 native Mamba forward hook calls; encoder/self10 each, conditional5 each. No decoder-only/warmup or additional forward.',
       restoration='Per phase including failures: restore full state_dict/BN buffers, Python NumPy CPU/CUDA RNG, flags and BN momenta; clear gradients and diagnostic records; no optimizer constructed.',
       optimizer='Only compile exact inherited optimizer_groups function for native classification evidence; no make_optimizer or optimizer construction/step.',
       real_data_allowlist=[],checkpoint_allowlist=[],scientific_efficacy='NOT_TESTED',post_CUDA_formal_freeze_required=True,
       forbidden=['Execution or installation without separate full request SHA256 authorization','Real data/checkpoint, training, BNCal or development evaluation',
                  'Network downloads, upgrades, builds or provider reinstall','Extra forward/loss/backward, warmup, optimizer or automatic retry/resume',
                  'Changes to formula, implementation, frozen initialization, fixture, tolerance or resource thresholds'],
       local_paths_in_evidence='Provenance only; Windows paths must never be executed on the server')
q['resource_policy']=copy.deepcopy(q['resource_policy']);q['resource_policy']['wall']='External timeout1800s plus10s kill grace;5 serial native builds,4 original loss/backward phases.'
q['launch_contract']=dict(tmux_session='bcsp_scq_rf_cuda_20261114_v1',request_path=REMOTE+'/SCQ_RF_artificial_cuda_execution_request_v1.json',
                         authorization_path=REMOTE+'/control/authorization_v1.json',runtime_path=REMOTE+'/control/runtime_v1.json',
                         launcher_path=REMOTE+'/control/launch_once_v1.sh',launch_attempt_path=REMOTE+'/control/attempt_claim_v1.json',
                         log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt',
                         materialization_order='authorization -> authorization SHA256 -> one-way runtime -> launcher -> exclusive claim -> tmux',
                         parent_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,
                         transport='Original file bytes Base64, raw stdout/stderr, WSL --exec, remote script lines<=2048 bytes',
                         exclusive_single_attempt=True,automatic_retry=False)
request=P/'SCQ_RF_artificial_cuda_execution_request_v1.json';emit(request,q);qh=rec(request)['sha256']
auth=dict(schema='bcsp-scq-rf-cuda-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_CONTRACT_TEST_NOT_USER_AUTHORIZATION')
e.authorize(q,qh,auth,'a'*64,dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256=qh,authorization_sha256='a'*64))
launcher=e.render_launcher(q,qh,'a'*64,'b'*64)
assert launcher.index('mkdir -p')<launcher.index(' >') and '\\' not in launcher.replace('\\n','') and max(len(line.encode()) for line in launcher.splitlines())<=2048
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=REMOTE,
             files=[dict(member='payload/'+p.name,target=REMOTE+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())],
             preconditions=q['readiness']['before_any_write'],no_runtime_or_launcher_materialization=True)
assert len(mapping['files'])==12
emit(T/'installation_mapping_v1.json',mapping)
archive=T/'bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz'
with archive.open('xb') as raw:
    with tarfile.open(fileobj=raw,mode='w:gz') as tar:
        tar.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
        for p in sorted(P.iterdir()):tar.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(archive) as tar:
    members=tar.getmembers();assert len(members)==13 and all(m.isfile() and m.size<4*1024**2 for m in members)
    content=''.join(hashlib.sha256(tar.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(archive)['sha256']+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',content)]:
    with Path(str(archive)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'pending_delivery_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_AUTHORIZATION',request=rec(request),archive=rec(archive),
     installation_mapping=rec(T/'installation_mapping_v1.json'),entry=rec(entry),entry_P3=rec(O/'entry_P3_v1.json'),
     installation_files=12,archive_members=13,CPU_implementation_checks=59,CPU_entry_checks=37,
     server_operations=0,CUDA_calls=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,training_request_created=False))
print(json.dumps(dict(status='RF_CUDA_PENDING_REQUEST_FROZEN',request_sha256=qh,archive=rec(archive),install_files=12)))
