"""Freeze synthetic2F/2B/0 request and transport only; no server connection."""
import ast,copy,hashlib,json,shlex,tarfile
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;I=S.parent/'H2_implementation_v1';R=S.parents[2]
ROOT=PurePosixPath('/home/jovyan/adapointr_work/PoinTr');INSTALL=ROOT/'third_party/bcsp_p2_h2_cuda_admission_20261107_v1';OUT=ROOT/'logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1'
def bind(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def remote(p,name=None):b=bind(p);b['path']=str(INSTALL/(name or Path(p).name));return b
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def emit(name,obj):
 with (S/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,allow_nan=False)
cpu=read(S/'cpu_entry_result_v1.json');assert cpu['status']=='H2_CUDA_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['tests']==8 and cpu['errors']==cpu['failures']==0
for b in cpu['bindings']:assert bind(b['path'])==b
impl=read(I/'implementation_P3_v1.json');assert impl['status']=='LOCAL_H2_IMPLEMENTATION_P3_PASS' and impl['CPU_checks']==33
for b in impl['production_sources']:assert bind(b['path'])==b
for name in ['AUX','COUPLE']:
 result=read(S/'artificial_cpu_entry_batch_v1/success'/(name+'_result.json'));assert result['state_before']==result['state_after'] and result['RNG_before']==result['RNG_after'] and result['optimizer_constructed'] is False
last=read(S/'artificial_cpu_entry_batch_v1/success/COUPLE_result.json');assert last['counts']==dict(forward_attempts=2,forward_returns=2,loss_calls=2,backward_attempts=2,backward_returns=2,optimizer_steps=0)
entry=bind(S/'bcsp_h2_cuda_admission_v1.py');tree=ast.parse((S/'bcsp_h2_cuda_admission_v1.py').read_text(encoding='utf-8'))
evaluate=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_pair')
assert not any(isinstance(n,ast.Attribute) and n.attr in ['step','train'] for n in ast.walk(evaluate))
assert len([n for n in ast.walk(evaluate) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='backward'])==1
assert len([n for n in ast.walk(evaluate) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='model'])==1
p3=dict(status='LOCAL_H2_CUDA_ENTRY_CPU_P3_PASS',entry_sha256=entry['sha256'],CPU_checks=8,CPU_result=bind(S/'cpu_entry_result_v1.json'),H2_implementation_P3=bind(I/'implementation_P3_v1.json'),fixture=bind(S/'artificial_h2_input_v1.npz'),sources=[bind(S/'bcsp_h2_cuda_admission_v1.py')]+impl['production_sources'],checks=dict(actual_two_eval_autograd_forwards_and_backwards_on_CPU=True,real_parent_forward_loss_AST_with_artificial_operators=True,nonzero_fixture_scale_exercises_coupling=True,BN_and_full_state_and_RNG_fingerprints_preserved=True,head_and_coarse_and_encoder_finite_nonzero_gradients=True,no_optimizer_constructed_or_step=True,single_attempt_failure_counts_persist=True,fixture_schema_and_hash_guard=True,one_way_authorization_runtime=True,static_no_checkpoint_or_training_loop=True,previous33_H2_tests_and_sources_bound=True),limits=['CPU artificial operators/losses are not actual Mamba/PointNet2/Chamfer/CUDA validation','GPU protocol uses eval plus autograd; does not validate training-mode BN, batch8 training resources, 3900-step stability or scientific benefit','Fixed nonzero synthetic head configuration is before snapshots and separate from zero-initialized training contract','Only finite gradients are required; previously disclosed finite Mamba gradient nondeterminism is not hidden by cross-arm/bitwise equality assertions'],server_operations=0,real_data_reads=0,real_checkpoint_loads=0,GPU_calls=0,optimizer_steps=0)
emit('entry_P3_v1.json',p3)
basepath=S.parent/'condition_probe_implementation_v1/condition_probe_execution_request_v1.json';base=read(basepath)
keys=['identity','environment','dependencies','implementation','numeric_policy','preflight_scope','static_config','helper','model_root','limits'];q={k:copy.deepcopy(base[k]) for k in keys}
q['limits']['wall_seconds']=900
science=dict(models=['AUX','COUPLE'],forward_attempt_limit=2,backward_attempt_limit=2,optimizer_steps=0,loss_calls=2,real_data_reads=0,checkpoint_loads=0,mode='eval_with_autograd',batch_size=1,n_input=8192,n_output=8192)
q.update(schema='bcsp-h2-synthetic-cuda-admission-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,science=science,entry=remote(S/'bcsp_h2_cuda_admission_v1.py'),h2_range=remote(I/'bcsp_h2_range_v1.py'),h2_adapter=remote(I/'bcsp_h2_model_adapter_v1.py'),h2_training_runtime=remote(I/'bcsp_h2_training_runtime_v1.py'),artificial_input=remote(S/'artificial_h2_input_v1.npz'),fixture_definition=remote(S/'artificial_fixture_definition_v1.json'),P3=remote(S/'entry_P3_v1.json'),H2_implementation_P3=remote(I/'implementation_P3_v1.json','H2_implementation_P3_v1.json'),parent_entry=copy.deepcopy(base['parent_entry']),output=str(OUT),launch_attempt=str(INSTALL/'control/launch_attempt_v1.json'))
L=dict(tmux_session='bcsp_h2_artificial_cuda_20261107_v1',request_path=str(INSTALL/'H2_artificial_cuda_execution_request_v1.json'),authorization_path=str(INSTALL/'control/authorization_v1.json'),runtime_path=str(INSTALL/'control/runtime_v1.json'),launcher_path=str(INSTALL/'control/launch_once_v1.sh'),log=str(OUT/'launch.log'),PID=str(OUT/'worker.pid'),exit_code=str(OUT/'exit_code.txt'),materialization_order='authorization -> hash -> runtime(one-way authorization binding) -> launcher; exclusive claim before unique tmux',parent_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,transport='Original file bytes, no text decode/reencode',single_attempt=True,automatic_retry=False)
q['launch_contract']=L
args=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','900s',q['identity']['python_realpath'],'-I','-S','-B',q['entry']['path'],'--request',L['request_path'],'--request-sha256','REQUEST_SHA256','--authorization',L['authorization_path'],'--authorization-sha256','AUTHORIZATION_SHA256','--runtime',L['runtime_path'],'--runtime-sha256','RUNTIME_SHA256']
env=[k+'='+v.replace('<owned_output>',str(OUT)) for k,v in q['environment'].items()]
launch='#!/bin/bash\nset -u\numask 077\ncd '+shlex.quote(q['identity']['project'])+' || exit 120\n'
for p in [*reversed(OUT.parents),OUT]:
 if str(p)!='/':launch+='[ ! -L '+shlex.quote(str(p))+' ] || exit 121\n'
launch+='mkdir -p -- '+shlex.quote(str(OUT.parent))+' || exit 122\nmkdir -- '+shlex.quote(str(OUT))+' || exit 123\nexec >>'+shlex.quote(L['log'])+' 2>&1\nenv \\\n'+' \\\n'.join(shlex.quote(x) for x in env+args)+'\nresult=$?\nprintf "%s\\n" "$result" > '+shlex.quote(L['exit_code'])+'\nexit "$result"\n'
assert max(map(len,launch.splitlines()))<2048
with (S/'launch_once_template_v1.sh').open('x',encoding='ascii',newline='\n') as f:f.write(launch)
L['launcher_template']=remote(S/'launch_once_template_v1.sh')
q['fixture_contract']=dict(artifact_bytes_frozen=True,definition='Synthetic ellipsoid spiral partial and analytic curve target; not cranial data',head=dict(original_training_zero_init_verified=True,synthetic_weight=1e-3/1024,synthetic_bias=.1,set_before_state_RNG_snapshots=True,same_both_modes=True,checkpoint_not_loaded=True),BN='all eval throughout; no running stats update or restoration',autograd='explicit enable_grad around one native eval forward, convert tuple2 to no-denoise loss tuple4 without new forward, one backward per arm',RNG='record/assert original before/after Python/NumPy/CPU/CUDA fingerprints; no restore to mask changes',gradients='finite all existing grads, nonzero head/coarse/encoder; no cross-arm bitwise gradient equality',state='hash all parameters and persistent buffers before/after; no optimizer created')
q['readiness_prerequisites']=['Fresh hostname/uid/GPU UUID/driver/Python/source/provider identities must match; inherited identity is not a current readiness claim','Initial physical GPU <=256MiB, disk >=4GiB; PID ownership diagnostic only','Rehash exact uploaded transport, all new targets absent, safe parents, exclusive no-overwrite install','Rehash only frozen inherited project sources/provider/environment/extensions; no general inventory expansion','Only exact artificial NPZ is payload-readable; no real dataset or checkpoint allowlist','Unique claim/session/output; failure stops with counters; no retry/resume','900s wall budget is conservative for two import/construct/F/B paths, not a timing promise; RSS8GiB/torch20GiB/device22528MiB/output1GiB/disk4GiB retained']
q['not_authorized']=['Execution before separate full SHA256 authorization','Model training, optimizer construction/step or BNCal','Real NPZ/NRRD/STL/checkpoint reads','Extra warmup/forward/backward, repeated universal preflight or timing loops','Changing model/provider/limits/fixture or loss backend','Downloading/upgrading/building dependencies','Automatic retry/resume or H2 training admission based solely on this test']
q['provenance']=dict(parent_request=bind(basepath),H2_draft=bind(R/'docs/cranial_bcsp_mamba_p2_20261106/H2_输入范围条件与生成路径软耦合_最小假设草案_zh_v1.md'),H2_implementation_P3=bind(I/'implementation_P3_v1.json'),local_cpu_only=True,prior_probe_same_container_completed=True,fresh_server_verification_not_done_in_this_preparation=True)
emit('H2_artificial_cuda_execution_request_v1.json',q)
mapping=[]
for p,name in [(S/'bcsp_h2_cuda_admission_v1.py',None),(I/'bcsp_h2_range_v1.py',None),(I/'bcsp_h2_model_adapter_v1.py',None),(I/'bcsp_h2_training_runtime_v1.py',None),(S/'artificial_h2_input_v1.npz',None),(S/'artificial_fixture_definition_v1.json',None),(S/'entry_P3_v1.json',None),(I/'implementation_P3_v1.json','H2_implementation_P3_v1.json'),(S/'H2_artificial_cuda_execution_request_v1.json',None),(S/'launch_once_template_v1.sh',None)]:mapping.append(dict(local=bind(p),target=str(INSTALL/(name or p.name)),archive_name=name or p.name,overwrite=False))
emit('frozen_transport_installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED',files=mapping))
archive=S/'bcsp_p2_H2_artificial_cuda_pending_20261107_v1.tar.gz'
with archive.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as tf:
  for r in mapping:tf.add(r['local']['path'],arcname=r['archive_name'],recursive=False)
for suffix,text in [('sha256',bind(archive)['sha256']+'  '+archive.name+'\n'),('bytes',str(archive.stat().st_size)+'\n'),('contents.sha256',''.join(r['local']['sha256']+'  '+r['archive_name']+'\n' for r in mapping))]:
 with Path(str(archive)+'.'+suffix).open('x',encoding='ascii') as f:f.write(text)
with tarfile.open(archive,'r:gz') as tf:
 assert len(tf.getmembers())==10
 for r in mapping:blob=tf.extractfile(r['archive_name']).read();assert len(blob)==r['local']['bytes'] and hashlib.sha256(blob).hexdigest()==r['local']['sha256']
request=bind(S/'H2_artificial_cuda_execution_request_v1.json')
emit('request_preparation_receipt_v1.json',dict(status='H2_CUDA_REQUEST_AWAITING_EXPLICIT_USER_AUTHORIZATION',request=request,transport=bind(archive),transport_members=10,CPU_entry_tests=8,previous_H2_CPU_tests=33,CUDA_calls=0,real_data_reads=0,real_checkpoint_loads=0,server_operations=0,authorized_controls_materialized=False,training_request_created=False))
print(json.dumps(dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=request,transport=bind(archive),CPU_entry_tests=8,transport_members=10,server_operations=0)))
