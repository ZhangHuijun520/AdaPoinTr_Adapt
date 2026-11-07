"""Local P3 and pending request only. No server/network/materialized authorization/launcher."""
from pathlib import Path, PurePosixPath
import ast
import copy
import hashlib
import io
import json
import shutil
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
P1=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104'
GEO=ROOT/'outputs/cranial_bcsp_geov1_20261024'
DOC=ROOT/'docs/cranial_bcsp_mamba_p2_20261106'
OUT=HERE/'first_FoldC_request_v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,allow_nan=False,indent=2);f.write('\n')
def functions(p):return {n.name:n for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def same(a,b):return ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)

result_path=HERE/'artificial_cpu_batch_v1/result_v1.json'
result=json.loads(result_path.read_bytes())
assert result['status']=='ARTIFICIAL_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==34
assert not (HERE/'artificial_cpu_batch_v1/failure_v1.json').exists()
entry=HERE/'bcsp_p2_h1_training_entry_v1.py';runtime=HERE/'bcsp_p2_h1_training_runtime_v1.py'
for r in result['source_bindings']:
    assert sha(Path(r['path']))==r['sha256']
static=json.loads((HERE/'static_review_v1.json').read_bytes())
assert static['status']=='STATIC_REVIEW_PASS'
for r in static['files']:assert sha(HERE/r['name'])==r['sha256']
parent=functions(P1/'minimal_implementation_v1/bcsp_p1_training_runtime_v1.py');child=functions(runtime)
class RemoveLogs(ast.NodeTransformer):
    def visit_Assign(self,n):
        if any(isinstance(t,ast.Name) and t.id=='h1_event' for t in n.targets):return None
        return self.generic_visit(n)
    def visit_Expr(self,n):
        c=n.value
        if isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and isinstance(c.func.value,ast.Name) and c.func.value.id=='event' and c.func.attr=='update':return None
        return self.generic_visit(n)
assert same(parent['train_lifecycle'],RemoveLogs().visit(child['train_lifecycle']))
assert all(same(v,child[k]) for k,v in parent.items() if k!='train_lifecycle')
production_metadata=GEO/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1/bcsp_training_contract_01dt08_v3.py'
assert sha(production_metadata)=='08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499'
A=functions(production_metadata);B=functions(GEO/'training_closure_v5/bcsp_training_contract_v1.py')
assert all(same(A[k],B[k]) for k in ['validate_static','bind_metadata','verify_qualified_receipt','validate_order'])
protected={
    str(P1/'minimal_implementation_v1/bcsp_p1_training_runtime_v1.py'):'939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee',
    str(P1/'minimal_implementation_v1/bcsp_p1_model_factory_v1.py'):'59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4',
    str(P1/'minimal_implementation_v1/bcsp_mamba_encoder_v1.py'):'5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8',
    str(ROOT/'outputs/cranial_scqr_v12_qa_github_publish_20261019/models/AdaPoinTr.py'):'1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4'}
assert all(sha(Path(p))==h for p,h in protected.items())
p3=dict(status='LOCAL_P2_H1_IMPLEMENTATION_P3_PASS',entry_sha256=sha(entry),runtime_sha256=sha(runtime),
    CPU_result_sha256=sha(result_path),CPU_contracts=34,static_review_sha256=sha(HERE/'static_review_v1.json'),
    review_checks=dict(runtime_lifecycle_only_detached_logging_delta=True,other_runtime_functions_unchanged=True,
        real_metadata_validator_functions_AST_match_CPU_version=True,original_get_loss_AST_used=True,
        full_authorize_with_real_metadata_and_artificial_rows_passed=True,exact_3900_synthetic_lifecycle_passed=True,
        optional_model_guard_adapted_only_for_H1=True,all_other_objectives_disabled=True,
        no_changed_loss_forward_or_Chamfer_recomputation_for_logging=True,protected_hashes_unchanged=True),
    protected_hashes=protected,remaining_limits=['No real Mamba model construction in this CPU batch','No actual CUDA/PointNet2 validation','Current server identity/resources/assets not rechecked','No model performance or training admission conclusion'],
    server_operations=0,production_forward=0,production_backward=0,production_optimizer_steps=0,synthetic_optimizer_steps=3900,
    test_scope='Local CPU loss/config/authorization/tiny lifecycle; not a new general framework')
emit(HERE/'implementation_P3_v1.json',p3)

OUT.mkdir(exist_ok=False);payload=OUT/'transport_payload';payload.mkdir()
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldC_20261106_v1'
output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/M_H1_foldC_seed0_20261106_v1'
mapping=[]
def stage(source,name):
    target=payload/name;shutil.copyfile(source,target)
    record=dict(path=remote+'/'+name,bytes=target.stat().st_size,sha256=sha(target))
    mapping.append(dict(local=str(target),target=record['path'],bytes=record['bytes'],sha256=record['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
    return record
baseline_path=P1/'M0_training_entry_v2/transport_payload/M0_foldC_seed0_training_execution_request_v1.json'
audit_path=P1/'M0_training_entry_v2/post_training_and_pair_freeze_audit_v1/audit_report_v1.json'
base=json.loads(baseline_path.read_bytes());q=copy.deepcopy(base)
h1=dict(enabled=True,mode='centroid_radius',weight=.1,smooth_l1_beta=.1,cvar_fraction=.1,eps=1e-6)
base_static=GEO/'first_run_freeze_foldC_8192_v1/static_training_config_v1.json'
assert sha(base_static)==base['static_config']['sha256']
config=json.loads(base_static.read_bytes());config['model']['coarse_geometry_guard']=h1
emit(OUT/'static_H1_training_config_v1.json',config)
q.update(schema='bcsp-p2-H1-training-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',
    stage='CRANIAL_BCSP_MAMBA_P2_H1',run_id='M_H1_foldC_seed0_20261106_v1',output=output,
    launch_attempt=remote+'/control/single_attempt_claim_v1.json',h1_config=h1)
q['implementation']['entry']=stage(entry,entry.name)
q['implementation']['runtime']=stage(runtime,runtime.name)
q['static_config']=stage(OUT/'static_H1_training_config_v1.json','static_H1_training_config_v1.json')
q['baseline_request']=stage(baseline_path,'frozen_M0_C_request_v1.json')
q['baseline_audit']=stage(audit_path,'frozen_M0_C_post_training_audit_v1.json')
q['h1_formula']=stage(DOC/'P2A_H1唯一公式声明_v1.json','H1_formula_v1.json')
q['p3']=stage(HERE/'implementation_P3_v1.json','implementation_P3_v1.json')
stage(result_path,'CPU_result_v1.json')
lc=dict(tmux_session='bcsp_p2_H1_C_seed0_20261106_v1',authorization=remote+'/control/H1_authorization_v1.json',
    runtime=remote+'/control/H1_runtime_v1.json',launcher=remote+'/control/H1_launch_once_v1.sh',
    log=output+'/launch.log',pid=output+'/worker.pid',exit_code=output+'/exit_code.txt',single_attempt=True,
    timeout_seconds=86400,materialization_order='authorization -> hash -> runtime -> hash -> launcher; exclusive claim before unique tmux',
    parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,
    launcher_argv_template=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',base['identity']['python_realpath'],'-I','-S','-B',q['implementation']['entry']['path'],
        '--request',remote+'/M_H1_foldC_seed0_training_execution_request_v1.json','--request-sha256','<THIS_REQUEST_SHA256>',
        '--authorization',remote+'/control/H1_authorization_v1.json','--authorization-sha256','<AUTHORIZATION_SHA256>',
        '--runtime',remote+'/control/H1_runtime_v1.json','--runtime-sha256','<RUNTIME_SHA256>'])
q['launch_contract']=lc
q['provenance']=dict(baseline='P1 frozen M0 Fold C seed0; scratch common initialization, not checkpoint resume',
    only_scientific_delta='coarse_geometry_guard centroid_radius fixed .1 loss',
    logging_delta='O(N) detached H1 components; no additional forward/CD and no loss addition in runtime',
    local_P3_pass=True,CUDA_H1_verified=False,current_server_rechecked=False,
    identity_source='Last verified P1 identity, NOT asserted currently online; mismatch must stop before materialization/launch',
    readiness_required=['Current hostname/UID/GPU UUID and idle GPU match','Current reused code/provider/environment and all 315 allowlisted data hashes match',
        'All proposed installation/control/run targets absent; safe real parents','No automatic resource rebind or dependency repair'],
    training_started=False,initial_checkpoint_loaded=False)
q['not_authorized']=['Execution before separate complete request SHA256 authorization','Changing current identity or resource thresholds',
    'Automatic retry/resume','Fold D training','T0 or P1 baseline retraining','BNCal or development evaluation',
    'Opening protected data','Dependency downloads/builds/installs/upgrades','Loading a final checkpoint as initialization',
    'Materializing authorization/runtime/launcher while request remains pending']
assert PurePosixPath(lc['authorization']).parent.as_posix()==remote+'/control'
request=payload/'M_H1_foldC_seed0_training_execution_request_v1.json';emit(request,q)
mapping.append(dict(local=str(request),target=remote+'/'+request.name,bytes=request.stat().st_size,sha256=sha(request),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
emit(OUT/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED',remote_root=remote,files=mapping,
    required_before_write='Recheck current exact identity, uploaded bytes/hash, every target absent, parent paths real and inside project',
    materials_not_created=[lc['authorization'],lc['runtime'],lc['launcher'],q['launch_attempt'],output]))
# Freeze a concrete manual-upload bundle, excluding synthetic checkpoints/data and materialized controls.
archive=OUT/'bcsp_p2_H1_foldC_pending_20261106_v1.tar.gz'
members=[(p,'payload/'+p.name) for p in sorted(payload.iterdir())]+[(OUT/'installation_mapping_v1.json','installation_mapping_v1.json')]
with tarfile.open(archive,'w:gz') as tar:
    for p,name in members:
        info=tarfile.TarInfo(name);b=p.read_bytes();info.size=len(b);info.mtime=0;info.mode=0o600
        tar.addfile(info,io.BytesIO(b))
Path(str(archive)+'.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
Path(str(archive)+'.bytes').write_text(str(archive.stat().st_size)+'\n',encoding='ascii')
Path(str(archive)+'.contents.sha256').write_text(''.join(sha(p)+'  '+name+'\n' for p,name in members),encoding='utf-8')
emit(OUT/'preparation_receipt_v1.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_path=str(request),request_sha256=sha(request),
    archive_path=str(archive),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
    P3_status=p3['status'],CPU_contracts=34,actual_training_started=False,current_server_readiness_rechecked=False,
    controls_materialized=False,CUDA_H1_verified=False,additional_FoldD_request_created=False))
print(json.dumps(dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=sha(request),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,CPU_contracts=34),indent=2))
