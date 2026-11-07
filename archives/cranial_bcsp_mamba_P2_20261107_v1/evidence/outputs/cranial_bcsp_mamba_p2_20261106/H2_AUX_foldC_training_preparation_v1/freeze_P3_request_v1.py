"""Local P3, pending request and transport. Never materialize authorized controls."""
import ast,copy,hashlib,importlib.util,io,json,shlex,shutil,tarfile
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;R=S.parents[2];H=S.parent/'H2_implementation_v1';G=S.parent/'H2_cuda_admission_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
entry=S/'bcsp_h2_aux_foldC_training_entry_v1.py'
spec=importlib.util.spec_from_file_location('h2_pending_entry',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
cpu=S/'artificial_cpu_batch_v1/result_v1.json';result=json.loads(cpu.read_bytes());assert result['status']=='H2_AUX_ENTRY_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==24
assert all(sha(Path(r['path']))==r['sha256'] for r in result['source_bindings'])
review=json.loads((S/'static_review_v1.json').read_bytes());assert review['status']=='STATIC_S0_S1_PASS' and all(sha(S/r['name'])==r['sha256'] for r in review['files'])
assert not (S/'artificial_cpu_batch_v1/failure_v1.json').exists()
core=json.loads((H/'implementation_P3_v1.json').read_bytes());assert core['status']=='LOCAL_H2_IMPLEMENTATION_P3_PASS'
assert sha(H/'implementation_P3_v1.json')=='896ca7a86f9ae2722069d83fbb58053982c48bb345487c280002dc1f3c8e9a15'
for k,n in [('h2_range','bcsp_h2_range_v1.py'),('h2_adapter','bcsp_h2_model_adapter_v1.py'),('runtime','bcsp_h2_training_runtime_v1.py')]:assert sha(H/n)==e.H2_HASHES[k]
cuda=G/'post_cuda_freeze_audit_20261107_v1/formal_audit_report_v1.json';assert sha(cuda)==e.CUDA_AUDIT_SHA and json.loads(cuda.read_bytes())['status']=='FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS'
ready=S/'server_readiness_v1/readiness_receipt_v1.json';readiness=json.loads(ready.read_bytes());assert readiness['status']=='BOUNDED_H2_AUX_C_READINESS_PASS' and readiness['identity']==e.CURRENT_IDENTITY
assert readiness['training_payloads']==315 and readiness['all_hashes_and_sizes_match'] and readiness['install_and_output_absent']
parent=S.parent/'H1_implementation_v1/bcsp_p2_h1_training_entry_v1.py'
def funcs(p):return {n.name:n for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
pf,cf=funcs(parent),funcs(entry)
for n in ['require','no_links','sha','exact','json_bound','emit','load_bound','payload_paths','make_training_policy','TrainingBudget','P1Budget']:
 assert ast.dump(pf[n],include_attributes=False)==ast.dump(cf[n],include_attributes=False)
protected={
 'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_model_factory_v1.py':'59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4',
 'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_mamba_encoder_v1.py':'5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8',
 'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_training_runtime_v1.py':'939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee',
 'outputs/cranial_scqr_v12_qa_github_publish_20261019/models/AdaPoinTr.py':'1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4'}
assert all(sha(R/p)==h for p,h in protected.items())
p3=dict(status='LOCAL_H2_AUX_TRAINING_ENTRY_P3_PASS',entry_sha256=sha(entry),H2_source_hashes=e.H2_HASHES,CPU_result_sha256=sha(cpu),CPU_contracts=24,core_H2_P3_sha256=sha(H/'implementation_P3_v1.json'),formal_CUDA_audit_sha256=sha(cuda),readiness_receipt_sha256=sha(ready),protected_source_hashes=protected,
 checks=dict(full_authorize_real_metadata_artificial_rows=True,scratch_zero_head_RNG_contract=True,H1_disabled=True,exact_AUX_dispatch=True,original_order_forwarded=True,original_dataset_interface=True,resource_payload_guards_AST_unchanged=True,original_model_factory_encoder_runtime_protected=True,H2_core_and_runtime_unchanged_since_CUDA=True,PID_telemetry_diagnostic_only_consistent_with_confirmed_policy=True,only_device_identity_rebound=True),
 limitations=['Artificial CPU facade at native-model boundary; not a real model training test','Already passed CUDA uses eval/autograd B1 and artificial head intervention, not batch8 training-mode BN','Training head must start all-zero; no synthetic CUDA bias is reused','Finite native Mamba gradient nondeterminism accepted; not exact gradient reproducibility','No scientific benefit established','Resource monitoring is sampled, no cgroup isolation'],server_writes=0,training_started=False,production_optimizer_steps=0)
emit(S/'implementation_P3_v1.json',p3)
O=S/'first_FoldC_request_v1';O.mkdir();P=O/'transport_payload';P.mkdir()
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_AUX_foldC_20261107_v1';output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1';mapping=[]
def stage(source,name=None):
 name=name or source.name;target=P/name;shutil.copyfile(source,target)
 rec=dict(path=str(PurePosixPath(remote)/name),bytes=target.stat().st_size,sha256=sha(target))
 mapping.append(dict(local=str(target.absolute()),target=rec['path'],bytes=rec['bytes'],sha256=rec['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'));return rec
bp=R/'outputs/cranial_bcsp_mamba_p1_20261104/M0_training_entry_v2/transport_payload/M0_foldC_seed0_training_execution_request_v1.json'
ba=bp.parents[1]/'post_training_and_pair_freeze_audit_v1/audit_report_v1.json'
assert sha(bp)==e.FROZEN_BASELINES['C']['request_sha256'] and sha(ba)==e.FROZEN_BASELINES['C']['audit_sha256']
base=json.loads(bp.read_bytes());q=copy.deepcopy(base)
st=R/'outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/static_training_config_v1.json';assert sha(st)==base['static_config']['sha256']
config=json.loads(st.read_bytes());config['H2']=e.H2;emit(O/'static_H2_AUX_training_config_v1.json',config)
q.update(schema='bcsp-p2-H2-AUX-training-request-v1',stage='CRANIAL_BCSP_MAMBA_P2_H2',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id='H2_AUX_foldC_seed0_20261107_v1',identity=e.CURRENT_IDENTITY,output=output,launch_attempt=remote+'/control/single_attempt_claim_v1.json',h2_config=e.H2)
q['environment']['CUDA_VISIBLE_DEVICES']=e.CURRENT_IDENTITY['gpu_uuid']
q['implementation']['entry']=stage(entry)
for k,n in [('h2_range','bcsp_h2_range_v1.py'),('h2_adapter','bcsp_h2_model_adapter_v1.py'),('runtime','bcsp_h2_training_runtime_v1.py')]:q['implementation'][k]=stage(H/n)
q['static_config']=stage(O/'static_H2_AUX_training_config_v1.json');q['baseline_request']=stage(bp,'frozen_M0_C_request_v1.json');q['baseline_audit']=stage(ba,'frozen_M0_C_post_training_audit_v1.json')
q['p3']=stage(S/'implementation_P3_v1.json');q['cuda_audit']=stage(cuda,'formal_H2_CUDA_audit_v1.json');q['readiness']=stage(ready,'readiness_receipt_v1.json');stage(cpu,'CPU_result_v1.json')
lc=dict(tmux_session='bcsp_p2_H2_AUX_C_seed0_20261107_v1',authorization=remote+'/control/H2_authorization_v1.json',runtime=remote+'/control/H2_runtime_v1.json',launcher=remote+'/control/H2_launch_once_v1.sh',request_path=remote+'/H2_AUX_foldC_seed0_training_execution_request_v1.json',log=output+'/launch.log',pid=output+'/worker.pid',exit_code=output+'/exit_code.txt',single_attempt=True,timeout_seconds=86400,materialization_order='authorization -> hash -> runtime -> hash -> launcher; exclusive claim before unique tmux',parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True)
q['provenance']=dict(baseline='P1 frozen M0 Fold C seed0; scratch common initialization, never final checkpoint resume',only_scientific_delta='Zero-initialized1025-parameter H2-AUX head plus fixed .1 auxiliary; no generation coupling; H1 off',logging='Existing H2 runtime; actual one-loss-per-forward records raw/used/dense/GT radius/center and auxiliary',current_identity_rebound=True,readiness='Exact315 train payload byte hashes; no arrays decoded; fresh installation/output absent',finite_Mamba_gradient_nondeterminism_disclosed=True,resource_policy='Original limits; sampled monitoring and stop, no cgroup guarantee; PID telemetry diagnostic only',legacy_baseline_references='t0_pairing/quantification/numeric_protocol retained unchanged as provenance; actual H2 admission uses formal cuda_audit',local_P3_pass=True,training_started=False)
q['not_authorized']=['Execution before separate complete request SHA256 authorization','Automatic retry/resume','Other fold/mode/seed','BNCal or development evaluation','Changing frozen data/model/order/3900-step contract','Dependency download/install/build/upgrade','Loading a final checkpoint as initialization','Using artificial CUDA .1 head bias for training','Materializing authorization/runtime/launcher while pending']
args=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',q['identity']['python_realpath'],'-I','-S','-B',q['implementation']['entry']['path'],'--request',lc['request_path'],'--request-sha256','REQUEST_SHA256','--authorization',lc['authorization'],'--authorization-sha256','AUTHORIZATION_SHA256','--runtime',lc['runtime'],'--runtime-sha256','RUNTIME_SHA256']
out=PurePosixPath(output);lines=['#!/bin/bash','set -u','umask 077','cd '+shlex.quote(e.PROJECT)+' || exit 120']
for p in reversed((out,*out.parents)):
 if str(p)!='/':lines.append('[ ! -L '+shlex.quote(str(p))+' ] || exit 121')
lines+=['mkdir -p -- '+shlex.quote(str(out.parent))+' || exit 122','mkdir -- '+shlex.quote(output)+' || exit 123','exec >>'+shlex.quote(lc['log'])+' 2>&1','env \\']
lines[-1]='env '+chr(92)
for k,v in q['environment'].items():lines.append(shlex.quote(k+'='+v.replace('<owned_output>',output))+' '+chr(92))
lines+=[' '+(' '+chr(92)+'\n ').join(map(shlex.quote,args)),'result=$?','printf "%s\\n" "$result" > '+shlex.quote(lc['exit_code']),'exit "$result"']
template=O/'launch_once_template_v1.sh'
with template.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
assert '\\' not in str(out.parent) and max(map(len,template.read_text().splitlines()))<2048
lc['launcher_template']=stage(template);q['launch_contract']=lc
request=P/'H2_AUX_foldC_seed0_training_execution_request_v1.json';emit(request,q)
mapping.append(dict(local=str(request.absolute()),target=lc['request_path'],bytes=request.stat().st_size,sha256=sha(request),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
emit(O/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED',remote_root=remote,files=mapping,reused_data_root=q['data_root'],reused315_data_hashes=readiness['training_payload_hashes'],required_before_write='Recheck identity, uploaded package/hash, all new targets absent and real safe parents; no overwrite. No provider/environment change.',materials_not_created=[lc['authorization'],lc['runtime'],lc['launcher'],q['launch_attempt'],output]))
archive=O/'bcsp_p2_H2_AUX_foldC_pending_20261107_v1.tar.gz';members=[(p,'payload/'+p.name) for p in sorted(P.iterdir())]+[(O/'installation_mapping_v1.json','installation_mapping_v1.json')]
with tarfile.open(archive,'w:gz') as tar:
 for p,name in members:
  b=p.read_bytes();info=tarfile.TarInfo(name);info.size=len(b);info.mode=0o600;info.mtime=0;tar.addfile(info,io.BytesIO(b))
with tarfile.open(archive,'r:gz') as tar:
 assert {m.name for m in tar.getmembers()}=={n for p,n in members}
 for p,name in members:assert tar.extractfile(name).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+name+'\n' for p,name in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_path=str(request.absolute()),request_sha256=sha(request),archive_path=str(archive.absolute()),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,installation_files=len(mapping),CPU_contracts=24,P3_status=p3['status'],readiness_status=readiness['status'],training_started=False,server_writes=0)
emit(O/'pending_request_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))
