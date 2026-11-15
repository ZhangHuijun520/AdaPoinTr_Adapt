"""Review36 loader CPU checks, inherit unchanged graph evidence, freeze pending CUDA v3."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,tarfile

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_initialization_loader_20261114_v2'
PREV=R/'outputs/scq_rf_cuda_preparation_20261114_v2'
M=R/'outputs/scq_rf_implementation_20261114_v1'
PROJECT='/home/jovyan/adapointr_work/PoinTr'
REMOTE=PROJECT+'/third_party/bcsp_scq_rf_cuda_20261114_v3'


def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)


static=read(O/'static_review_v2.json')
source=O/'bcsp_scq_rf_residual_v2.py';test=O/'test_rf_byte_loader_cpu_v2.py'
assert static['new_source']==rec(source) and all(static['checks'].values())
for row in static['preserved']+[static['prior_source']]:assert rec(Path(row['path']))==row
cpu=read(O/'cpu_loader_batch_v2/result_v2.json')
assert cpu['status']=='RF_FROZEN_BYTE_LOADER_CPU_PASS' and cpu['count']==len(cpu['checks'])==len(set(cpu['checks']))==36
assert cpu['source']==rec(source) and cpu['test']==rec(test) and cpu['regeneration_calls']==0
assert all(cpu[k]==0 for k in ('forward_calls','loss_calls','backward_calls','optimizer_steps')) and cpu['CUDA'] is False
assert not (O/'cpu_loader_batch_v2/failure_v2.json').exists()
manifest=read(M/'initialization_manifest_v1.json')
assert cpu['loaded_tensor_hashes']=={r['name']:r['sha256'] for r in manifest['layout']}
assert cpu['frozen_initialization']==rec(M/'initialization_v1.bin')
prior_ip3=M/'P3_implementation_v2.json';prior_ep3=PREV/'entry_P3_v2.json'
ip3=read(prior_ip3);ep3=read(prior_ep3)
assert ip3['status']=='LOCAL_RF_IMPLEMENTATION_P3_PASS_ARTIFICIAL_CPU_ONLY' and ip3['CPU_checks']==59
assert ep3['status']=='RF_CUDA_ENTRY_LOCAL_P3_PASS' and ep3['CPU_entry_checks']==52
for row in ip3['candidate_sources']+ip3['initialization']+ip3['artifacts']+[ep3['test'],ep3['CPU']]:assert rec(Path(row['path']))==row
entry=PREV/'bcsp_scq_rf_cuda_admission_v2.py'
assert rec(entry)['sha256']==ep3['entry_sha256']
audit_path=PREV/'failed_freeze_initialization_review_v1/formal_failure_freeze_audit_v1.json'
audit=read(audit_path);assert audit['status']=='FORMAL_RF_V2_FAILURE_FREEZE_AUDIT_PASS_CUDA_REMAINS_FAILED' and all(audit['checks'].values())
new_tree=ast.parse(source.read_text(encoding='utf-8'));old_tree=ast.parse((M/'bcsp_scq_rf_residual_v1.py').read_text(encoding='utf-8'))
def rest(tree):return ast.dump(ast.Module([n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='load_initialization'],[]),include_attributes=False)
assert rest(new_tree)==rest(old_tree)
for p in (source,test):compile(p.read_bytes(),str(p),'exec')
p3=dict(status='LOCAL_RF_IMPLEMENTATION_P3_PASS_ARTIFICIAL_CPU_ONLY',
        CPU_checks=59,CPU_checks_semantics='Compatibility field inherited from the unchanged model graph59-check evidence; not59 tests rerun for this loader revision.',
        loader_CPU_checks=36,inherited_model_graph_CPU_checks=59,inherited_entry_CPU_checks=52,
        current_loader_CPU=rec(O/'cpu_loader_batch_v2/result_v2.json'),loader_source=rec(source),loader_test=rec(test),
        static_review=rec(O/'static_review_v2.json'),inherited_model_graph_P3=rec(prior_ip3),inherited_entry_P3=rec(prior_ep3),
        prior_failure_audit=rec(audit_path),frozen_initialization=rec(M/'initialization_v1.bin'),
        checks=dict(only_initialization_loader_AST_changed=True,all36_loader_CPU_checks_pass=True,
                    no_runtime_seed_regeneration=True,frozen_bytes_and_tensor_hashes_unchanged=True,
                    corrupt_or_nonfinite_or_nonzero_output_or_bad_layout_rejected=True,
                    RNG_preserved_and_unchanged_factory_binds_new_module=True,
                    original_forward_descriptor_and_factory_unchanged=True,inherited59_and52_evidence_hashes_unchanged=True,
                    no_server_CUDA_or_model_forward=True),
        limitations=cpu['limitations']+['Original59 graph and52 CUDA-entry CPU checks inherited by exact-source delta, not rerun.',
                                       'No claim of successful native CUDA initialization or RF loss/backward until separate execution and freeze.'],
        server_operations=0,CUDA_calls=0,random_regeneration_calls=0,training_request_created=False)
emit(O/'implementation_P3_v3.json',p3)
entry_p3=copy.deepcopy(ep3)
entry_p3.update(implementation_P3=rec(O/'implementation_P3_v3.json'),loader_CPU_checks=36,
                inherited_entry_P3=rec(prior_ep3),prior_failure_audit=rec(audit_path),
                current_entry_not_retested=True,
                current_scope='Unchanged CUDA entry and52-check CPU evidence; only RF source loader binding changes, covered by36 current CPU checks.')
entry_p3['checks']=dict(entry_p3['checks'],frozen_byte_loader_v2_current36_checks=True,existing_entry_source_identical=True)
emit(O/'entry_P3_v3.json',entry_p3)
T=O/'pending_transport_v3';T.mkdir();P=T/'payload';P.mkdir()
named=[(source,source.name),(test,test.name),(O/'implementation_P3_v3.json','implementation_P3_v3.json'),
       (O/'entry_P3_v3.json','entry_P3_v3.json'),(O/'cpu_loader_batch_v2/result_v2.json','loader_CPU_result_v2.json'),
       (O/'static_review_v2.json','loader_static_review_v2.json'),(audit_path,'prior_v2_failed_freeze_audit_v1.json')]
for src,name in named:shutil.copyfile(src,P/name)
prior_request=PREV/'pending_transport_v2/payload/SCQ_RF_artificial_cuda_execution_request_v2.json'
old=read(prior_request);oldsha=rec(prior_request)['sha256'];assert oldsha=='09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'
q=copy.deepcopy(old);q['run_id']='SCQ_RF_artificial_cuda_20261114_v3'
q['output']=PROJECT+'/logs/cranial_bcsp_fullmamba/'+q['run_id']
q['implementation']['rf_residual']=rec(source,REMOTE+'/'+source.name)
q['implementation_P3']=rec(O/'implementation_P3_v3.json',REMOTE+'/implementation_P3_v3.json')
q['entry_P3']=rec(O/'entry_P3_v3.json',REMOTE+'/entry_P3_v3.json')
q['launch_contract']=dict(old['launch_contract'])
q['launch_contract'].update(tmux_session='bcsp_scq_rf_cuda_20261114_v3',request_path=REMOTE+'/SCQ_RF_artificial_cuda_execution_request_v3.json',
    authorization_path=REMOTE+'/control/authorization_v3.json',runtime_path=REMOTE+'/control/runtime_v3.json',
    launcher_path=REMOTE+'/control/launch_once_v3.sh',launch_attempt_path=REMOTE+'/control/attempt_claim_v3.json',
    log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
q['readiness']['last_evidence']=rec(audit_path)
q['readiness']['before_any_write'][2]='Upload archive and3 sidecars, exact8 new install targets and all control/output paths absent; reverify unchanged CUDA entry, RF factory and frozen initialization as exact readonly reuse. No overwrite.'
q['supersedes']=dict(request_sha256=oldsha,status='ATTEMPTED_FAILED_CONSUMED_DO_NOT_REUSE',actual_counts=dict(forward=1,loss=0,backward=0,optimizer_steps=0),
                    reason='Runtime seed regeneration comparison rejected byte-valid frozen initialization; no RF forward occurred',
                    failure_audit=rec(P/'prior_v2_failed_freeze_audit_v1.json',REMOTE+'/prior_v2_failed_freeze_audit_v1.json'))
q['initialization_loading_contract']=dict(authority='Exact frozen little-endian FP32 file; no runtime seed regeneration',
    binary=q['rf_initialization'],checks=['size924684','SHA256','fixed names/shapes/order','little endian CPU FP32 decoding','all finite','V2 weight/bias zero'],
    seed=2026111402,seed_role='historical provenance only; never re-generate on load',runtime_model_alias='bcsp_scq_rf_residual_v1 mapped to exact versioned v2 source; registered state keys unchanged')
oldresidual=old['implementation']['rf_residual']['path'];oldimplp3=old['implementation_P3']['path']
reused=[r for r in old['reused_readonly_bindings'] if r['path'] not in (oldresidual,oldimplp3)]
for row in [old['entry'],old['implementation']['rf_factory'],old['rf_initialization']]:
    if not any(r['path']==row['path'] for r in reused):reused.append(row)
q['reused_readonly_bindings']=reused
assert q['rf_initialization']==old['rf_initialization'] and q['initialization']==old['initialization'] and q['entry']==old['entry']
assert all(q['implementation'][k]==v for k,v in old['implementation'].items() if k!='rf_residual')
for key in ('science','phases','limits','fixture','tolerances','numeric','environment','dependencies','optimizer_policy','identity'):assert q[key]==old[key]
request=P/'SCQ_RF_artificial_cuda_execution_request_v3.json';emit(request,q);qh=rec(request)['sha256']
spec=importlib.util.spec_from_file_location('unchanged_RF_entry_contract_for_v3',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
auth=dict(schema='bcsp-scq-rf-cuda-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_CONTRACT_ONLY_NOT_EXECUTION_AUTHORIZATION')
e.authorize(q,qh,auth,'a'*64,dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256=qh,authorization_sha256='a'*64))
launcher=e.render_launcher(q,qh,'a'*64,'b'*64)
assert launcher.index('mkdir -p')<launcher.index(' >') and '\\' not in launcher.replace('\\n','') and max(len(line.encode()) for line in launcher.splitlines())<=2048
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=REMOTE,
             files=[dict(member='payload/'+p.name,target=REMOTE+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())],
             preconditions=q['readiness']['before_any_write'],reuse_exact_CUDA_entry_factory_and_initialization=True,no_control_materialization=True)
assert len(mapping['files'])==8;emit(T/'installation_mapping_v3.json',mapping)
archive=T/'bcsp_scq_rf_artificial_cuda_pending_20261114_v3.tar.gz'
with archive.open('xb') as raw:
    with tarfile.open(fileobj=raw,mode='w:gz') as tar:
        tar.add(T/'installation_mapping_v3.json',arcname='installation_mapping_v3.json',recursive=False)
        for p in sorted(P.iterdir()):tar.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(archive) as tar:
    members=tar.getmembers();assert len(members)==9 and all(m.isfile() for m in members)
    listing=''.join(hashlib.sha256(tar.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(archive)['sha256']+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',listing)]:
    with Path(str(archive)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'pending_delivery_v3.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_AUTHORIZATION',request=rec(request),archive=rec(archive),mapping=rec(T/'installation_mapping_v3.json'),
     implementation_P3=rec(O/'implementation_P3_v3.json'),entry_P3=rec(O/'entry_P3_v3.json'),
     current_loader_CPU_checks=36,inherited_model_graph_CPU_checks=59,inherited_entry_CPU_checks=52,
     install_files=8,archive_members=9,frozen_initialization_unchanged=True,random_regeneration_calls=0,
     server_operations=0,CUDA_calls=0,training_request_created=False,controls_materialized=False))
print(json.dumps(dict(status='RF_FROZEN_BYTE_LOADER_P3_PASS_V3_REQUEST_PENDING',request_SHA256=qh,archive=rec(archive),new_CPU_checks=36,install_files=8)))
