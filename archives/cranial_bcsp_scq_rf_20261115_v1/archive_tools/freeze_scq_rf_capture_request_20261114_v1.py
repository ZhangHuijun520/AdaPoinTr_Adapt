"""Freeze passed observer P3 and a pending ten-forward request; no execution."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,io,json,shlex,shutil,tarfile
R=Path(__file__).resolve().parent.parent;S=R/'outputs/scq_rf_capture_implementation_20261114_v1'
O=S/'pending_request_v1';assert not O.exists();O.mkdir();T=O/'payload';T.mkdir()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
ctx=json.loads((S/'context_v1.json').read_bytes());q=copy.deepcopy(ctx['candidate']);remote=ctx['remote_root']
cpu_path=S/'artificial_cpu_batch_v2/result_v1.json';cpu=json.loads(cpu_path.read_bytes());static_path=S/'static_review_v2.json';static=json.loads(static_path.read_bytes())
entry=S/'bcsp_scq_rf_memory_capture_v1.py';test=S/'test_scq_rf_observer_cpu_v2.py'
assert cpu['status']=='SCQ_RF_OBSERVER_ARTIFICIAL_CPU_CONTRACT_PASS' and cpu['checks_passed']==len(cpu['checks'])==len(set(cpu['checks']))==32
assert not (cpu_path.parent/'failure_v1.json').exists()
assert rec(entry)==cpu['entry'] and rec(test)==cpu['test']
assert rec(entry)['sha256']=='678a6fffcba13a7b4dec354833fc8275bcd3081adffe5b4581673b977086e5c9'
assert static['status']=='SCQ_RF_TEST32_LIMITED_STATIC_REVIEW_PASS' and all(static['checks'].values())
for record in cpu['parent_sources']+static['changed_files']:assert rec(Path(record['path']))==record
assert rec(S/'test_scq_rf_observer_cpu_v1.py')['sha256']=='aa1171cc1457e089cde655a7241a693a222de371ba35873a710bcfb349303095'
mapping=[]
def stage(path,name=None,sub=''):
    n=name or path.name;dest=T/sub/n;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists()
    shutil.copyfile(path,dest);assert dest.read_bytes()==path.read_bytes()
    record=dict(rec(dest),path=remote+'/'+(sub+'/' if sub else '')+n)
    mapping.append(dict(member='payload/'+(sub+'/' if sub else '')+n,target=record['path'],bytes=record['bytes'],sha256=record['sha256'],overwrite=False))
    return record
q['entry']=stage(entry);q['capture_scope']=stage(Path(ctx['stage_scope']))
cpu_record=stage(cpu_path,'CPU_contract_result_v2.json');static_record=stage(static_path)
test_record=stage(test)
checks=dict(final_entry_matches_passed_batch=True,entry_and_production_guards_unchanged=True,only_test32_and_versioned_output_changed=True,all32_checks_pass=True,actual_frozen_SCQ_residual_hook_used=True,actual_authorize_one_way_function_tested=True,actual_ten_case_execute_path_tested=True,hook_no_return_mutation_and_cleanup=True,state_and_CPU_RNG_unchanged=True,partial_only_and_GT_condition_denied=True,second_KNN_only_no_RF_head=True,known_failure_stops_without_retry=True,production_CPU_bypass_denied=True,POSIX_arguments_timeout_exit_redirection_checked=True,parent_exact_read_numeric_and_resource_helpers_reused=True,real_GPU_not_claimed=True)
p3=dict(status='SCQ_RF_OBSERVER_LOCAL_P3_PASS',date='2026-11-14',entry_sha256=q['entry']['sha256'],test_sha256=test_record['sha256'],CPU_checks=32,CPU_result=cpu_record,static_review=static_record,checks=checks,parent_sources=cpu['parent_sources'],previous_failed_batch=rec(S/'artificial_cpu_batch_v1/failure_v1.json'),limitations=cpu['limitations']+['No current server identity/resource/provider/asset check this task; mandatory before installation/execution.','No native CUDA/Mamba observation, inference equivalence or scientific feasibility conclusion this task.','Full production isolated main not executed on CPU. Reused source policy remains frozen; native readiness is a separate step.'],server_operations=0,GPU_calls=0,real_checkpoint_loads=0,real_forward=0,training=0,repeat_GPU_preflight=False)
emit(S/'implementation_P3_v1.json',p3);q['P3']=stage(S/'implementation_P3_v1.json')
scope=json.loads(Path(ctx['stage_scope']).read_bytes());cases={(x['fold'],x['case_id']):x for x in scope['cases']}
native=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ/2026-11-14_native_development_eval/development_predictions_v1.tar.gz')
assert rec(native)['sha256']=='57e7c761510bd8fb0f4758a49eb38354231ba8b0893eab16513f1b478350838d'
want={x['frozen_prediction']['member']:x for x in scope['cases']};saved={}
with tarfile.open(native,'r|gz') as tar:
    for member in tar:
        assert member.isfile()
        if member.name not in want:continue
        c=want[member.name];b=tar.extractfile(member).read();assert len(b)==c['frozen_prediction']['bytes'] and hashlib.sha256(b).hexdigest()==c['frozen_prediction']['sha256']
        path=O/('reference_'+c['fold']+'__'+c['case_id']+'.npz')
        with path.open('xb') as f:f.write(b)
        saved[(c['fold'],c['case_id'])]=stage(path,'S_'+c['fold']+'__'+c['case_id']+'.npz','references')
assert len(saved)==10
for row in q['cases']:
    assert row['reference']==saved[(row['fold'],row['case_id'])]
q['stage_A_evidence']=rec(R/'outputs/scq_rf_stageA_readonly_20261114_v1/delivery_verification_v1.json')
q['scientific_contract']=dict(task='Ten fixed trained-S observations only; actual Memory N0/N1 and descriptor difference, no efficacy inference',capture_keys=['M','F','z','Qraw','delta0','Q1','N0','N1','h_static','h_requery','prediction','coarse'],GT_or_reference_geometry=False,Native_prediction_references_only=True,z='backbone global_feature at original SCQ input',case_order='C seven then D three as frozen',no_resampling=True,no_RF_head=True)
q['installation_prerequisites']=list(q['activation_prerequisites'])
q['provenance']=dict(CPU_pass_does_not_prove_CUDA=True,source_or_provider_change=False,previous_request_reused_for_execution=False,server_checked_this_turn=False,fresh_readiness_required=True,identity='Pinned previously observed zbpgzu-0, not a liveness claim; mismatch requires a new explicit rebind/request, not silent substitution')
request=T/'SCQ_RF_ten_memory_execution_request_v1.json';emit(request,q)
request_record=rec(request);mapping.append(dict(member='payload/'+request.name,target=q['launch_contract']['request_path'],bytes=request_record['bytes'],sha256=request_record['sha256'],overwrite=False))
with Path(str(request)+'.sha256').open('x',encoding='ascii') as f:f.write(request_record['sha256']+'  '+request.name+'\n')
spec=importlib.util.spec_from_file_location('scq_rf_final_static_validation',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);e.validate(q)
parent_path=Path(ctx['parent_entry_local']);sp=importlib.util.spec_from_file_location('scq_rf_frozen_parent_render_only',parent_path);parent=importlib.util.module_from_spec(sp);sp.loader.exec_module(parent)
text=e.render_launcher(q,'a'*64,'b'*64,'c'*64,parent);cmd=shlex.split(next(x for x in text.splitlines() if x.startswith('/usr/bin/timeout')))
assert max(len(x.encode()) for x in text.splitlines())<=2048 and cmd[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','1800s']
assert all(cmd[cmd.index(flag)+1]==q['launch_contract'][key] for flag,key in [('--request','request_path'),('--authorization','authorization'),('--runtime','runtime')])
assert text.index('mkdir --')<text.index(' >') and 'printf "%s\\n" "$rc" >' in text
# Verify only existing local source mirrors. No Linux path is opened on Windows.
mirror=json.loads((R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2/pending_request_v2/local_mirror_v2.json').read_bytes())
verified=[];remote_only=[]
for record in [*q['implementation'].values(),q['initialization'],q['helper'],q['static_config'],q['preflight_scope'],*q['dependencies']]:
    if record['path'] in mirror and Path(mirror[record['path']]).is_file():
        p=Path(mirror[record['path']]);rr=rec(p);assert rr['bytes']==record['bytes'] and rr['sha256']==record['sha256'];verified.append(dict(remote=record['path'],local=rr))
    else:remote_only.append(record)
mp=O/'installation_mapping_v1.json';emit(mp,dict(status='FROZEN_NOT_INSTALLED_REQUIRES_FRESH_READINESS',remote_root=remote,files=mapping,reused_parent_entry=q['parent_entry'],reused_parent_request=q['parent_request'],reused_implementation=q['implementation'],checkpoint_files=[x['checkpoint'] for x in q['runs']],inputs=[x['input'] for x in q['cases']],control_directory=remote+'/control',output=q['output'],request_sha256=request_record['sha256'],no_overwrite=True,server_operations=0,materialization='separate authorization -> receipt SHA256 -> runtime -> launcher -> exclusive claim -> one tmux'))
archive=O/'bcsp_scq_rf_ten_memory_pending_20261114_v1.tar.gz';members=[(p,'payload/'+p.relative_to(T).as_posix()) for p in sorted(T.rglob('*')) if p.is_file() and not p.name.endswith('.sha256')]+[(mp,mp.name)]
with archive.open('xb') as raw:
    with tarfile.open(fileobj=raw,mode='w:gz') as tar:
        for p,name in members:
            b=p.read_bytes();info=tarfile.TarInfo(name);info.size=len(b);info.mode=0o600;info.mtime=0;tar.addfile(info,io.BytesIO(b))
with tarfile.open(archive) as tar:
    assert len(tar.getmembers())==len(members)
    for p,name in members:assert tar.extractfile(name).read()==p.read_bytes()
ah=rec(archive)
for suffix,value in [('.sha256',ah['sha256']+'  '+archive.name+'\n'),('.bytes',str(ah['bytes'])+'\n'),('.contents.sha256',''.join(rec(p)['sha256']+'  '+name+'\n' for p,name in members))]:
    with Path(str(archive)+suffix).open('x',encoding='ascii') as f:f.write(value)
emit(O/'local_validation_v1.json',dict(status='PENDING_REQUEST_AND_TRANSPORT_STATIC_BYTES_VERIFIED',source_mirrors_verified=verified,remote_binary_or_unmapped_bindings_not_reverified=remote_only,request=request_record,archive=ah,installed_targets=len(mapping),archive_members=len(members),fixture_authorizations_not_packaged=True,actual_authorization_or_runtime_or_launcher_created=False,server_readiness_not_claimed=True,GPU_calls=0))
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=request_record,archive=ah,P3=rec(S/'implementation_P3_v1.json'),CPU_checks=32,installation_files=len(mapping),counts=q['counts'],server_operations=0,GPU_calls=0,production_entry_unchanged=True,authorized_controls_materialized=False)
emit(O/'delivery_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=True))
