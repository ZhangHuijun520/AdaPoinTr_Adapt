"""Freeze local P3 and pending request/package. No remote calls or real controls."""
import ast,copy,hashlib,importlib.util,io,json,shutil,tarfile,shlex
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;B=S.parent;R=B.parents[1];PRE=B/'lqi_native_prediction_preparation_v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
entry=S/'bcsp_lqi_twofold_native_predict_v1.py';test=S/'test_lqi_native_prediction_cpu_v1.py'
cpu=S/'artificial_cpu_batch_v1/result_v1.json';result=read(cpu);static=read(S/'static_review_final_v1.json')
assert result['status']=='LQI_NATIVE_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==46
assert result['synthetic_forwards']==210 and result['real_decoder_trace_comparison_calls']==2
assert not (cpu.parent/'failure_v1.json').exists()
for rec in result['source_bindings']:assert bind(Path(rec['path']))==rec
for rec in static['files']:assert sha(S/rec['name'])==rec['sha256']
assert static['status']=='STATIC_S0_S1_PASS' and all(static['checks'].values())
policy=read(cpu.parent/'source_policy_stdout.bin');assert all(policy.values())
spec=importlib.util.spec_from_file_location('lqi_native_freeze',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
index=read(PRE/'LQI_CD_Native_input_index_candidate_v1.json');G=R/'outputs/cranial_bcsp_geov1_20261024'
e.validate_index(index,read(G/'consolidated_binding_v1/fold_binding.json'))
e.validate_source(index,read(G/'development_eval_v1/development_input_index_v1.json'),[json.loads(x) for x in (G/'real_data_qc_v1/manifest_8192.jsonl').read_text().splitlines()])
old=B/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py'
def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
inherited=['load_partial','predict_once','source_module','make_policy','Budget','pack','rng_state','geometry_summary','load_checkpoint','render_launcher']
a,b=nodes(old),nodes(entry);assert all(a[n]==b[n] for n in inherited)
changes=[n for n in b if n not in a or b[n]!=a[n]]
assert set(changes)=={'ExactSourceReads','authorize','validate_index','validate_evidence','load_lqi_builder','validate_model','execute_pair','main'}
scope=read(PRE/'LQI_CD_210_Native_prediction_scope_v1.json')
assert scope['inference']['forward_attempt_budget']==210 and scope['outputs']['context_caches']==0
for run in index['runs']:
 audit=read(Path(run['training_audit']['path']));assert all(audit['checks'].values()) and audit['checkpoint']['sha256']==run['checkpoint']['sha256']
 assert run['training_audit']['sha256']==e.FROZEN_MODELS[run['label']]['audit_sha256']
checks=dict(final_sources_bound_to_CPU=True,static_S0_S1_pass=True,actual_LQI_four_source_load_under_real_read_policy=True,source_write_and_neighbor_denied=True,full_authorize_one_way_binding_CPU=True,actual_production_factory_call_with_artificial_mixer=True,F0_identity_and_old_conditioning_rejected=True,exact210_synthetic_forward_and_outputs=True,partial_only_no_GT_tensor=True,strict_checkpoint_negative_cases=True,all_Q_and_P_saved_no_old_mechanism_cache=True,state_RNG_and_failure_stop_CPU=True,inherited_numeric_resource_payload_guards_unchanged=True,unchanged_source_fold_input_normalization_metadata=True,final_C_D_training_and_pairing_evidence_bound=True,POSIX_launcher_parent_before_redirect=True,no_GPU_preflight_repeat=True)
p3=dict(status='LOCAL_LQI_NATIVE_PREDICTION_P3_PASS',date='2026-11-11',entry_sha256=sha(entry),test_sha256=sha(test),CPU_result=bind(cpu),CPU_checks=46,static_review=bind(S/'static_review_final_v1.json'),checks=checks,inherited_entry=bind(old),inherited_AST_unchanged=inherited,changed_functions=changes,actual_source_policy=policy,scope=bind(PRE/'LQI_CD_210_Native_prediction_scope_v1.json'),input_index=bind(PRE/'LQI_CD_Native_input_index_candidate_v1.json'),CPU_runtime=dict(python='E:/RelocatedData/zhj/.conda/envs/adapointr/python.exe',torch='2.5.1+cpu'),limitations=['Some inherited CPU result labels say F0; bound source policy/loader and actual construction evidence are LQI. No F0 model was substituted for LQI.','Real LQI factory/decoder exercised with artificial causal mixer; not native Mamba CUDA validation.','210 artificial outer forwards are interface tests, not 210 project model forwards.','No real payload or checkpoint loaded; no fresh server identity/resource/existence verification this task.','Current identity/assets/resources and all new targets must be reverified before installation/activation; unknown or changed identity stops.','Existing finite gradient nondeterminism disclosure remains; this prediction task has no backward.','Resource monitoring is observational, not dedicated hard isolation; SMI PID diagnostic only.'],real_forwards=0,real_checkpoint_loads=0,real_payload_arrays=0,server_operations=0,GPU_calls=0,repeat_preflight=False)
assert read(S/'implementation_P3_v1.json')==p3  # Reuse already frozen valid P3; never overwrite.
O=S/'pending_request_final_v1';O.mkdir();T=O/'transport_payload';T.mkdir()
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1'
output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1'
mapping=[]
def stage(p,name=None):
 n=name or p.name;t=T/n;shutil.copyfile(p,t);rec=dict(path=str(PurePosixPath(remote)/n),bytes=t.stat().st_size,sha256=sha(t));mapping.append(dict(local=str(t.resolve()),target=rec['path'],bytes=rec['bytes'],sha256=rec['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'));return rec
q=copy.deepcopy(read(B/'Native_prediction_implementation_v1/resource_rebind_v2/transport_payload/F0_CD_native_prediction_execution_request_v2.json'))
q.update(schema='bcsp-lqi-twofold-native-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id='LQI_CD_native_development_20261111_v1',variant='F0-LQI-v1',output=output,launch_attempt=remote+'/control/native_prediction_single_attempt_claim_v1.json',scope_origin='EXACT_FROZEN_F0_DEVELOPMENT_CASES_NO_RESELECTION')
for k in ['selection','selection_registration_timing','resource_rebind_audit','resource_rebind_supplement']:q.pop(k,None)
q['entry']=stage(entry);q['input_index']=stage(PRE/'LQI_CD_Native_input_index_candidate_v1.json');q['protocol']=stage(PRE/'LQI_CD_210_Native_prediction_scope_v1.json');q['P3']=stage(S/'implementation_P3_v1.json')
for p in [test,cpu,S/'static_review_final_v1.json',cpu.parent/'source_policy_stdout.bin',PRE/'preparation_validation_receipt_v1.json']:
 stage(p,'CPU_contract_result_v1.json' if p==cpu else p.name)
q['training_audits']={run['label']:stage(Path(run['training_audit']['path']),'frozen_'+run['label']+'_training_audit_v1.json') for run in index['runs']}
q['pairing_audits']={run['label']:stage(Path(run['pairing_audit']['path']),'frozen_'+run['label']+'_pairing_audit_v1.json') for run in index['runs']}
train=read(B/'lqi_training_entry_v1/LQI_FoldC_training_execution_request_v1.json')
q['implementation']={k:train['implementation'][k] for k in ['encoder','factory','lqi_decoder','lqi_factory','timezone']}
q['prior_native_admission']=dict(receipt=train['admission']['receipt'],audit=train['admission']['audit'],repeat_preflight=False)
q['expected_artifacts']=dict(predictions=210,coarse_saved=210,context=0,trace=0,prediction_keys=['prediction','coarse'],normalized_native=True,GT_alignment=False,postfilter=False,additional_decoder_interventions=0)
c=remote+'/control'
q['launch_contract']=dict(tmux_session='bcsp_lqi_CD_native_eval_20261111_v1',request_path=remote+'/LQI_CD_native_prediction_execution_request_v1.json',authorization=c+'/native_prediction_authorization_v1.json',runtime=c+'/native_prediction_runtime_v1.json',launcher=c+'/native_prediction_launch_once_v1.sh',log=output+'/launch.log',pid=output+'/worker.pid',exit_code=output+'/exit_code.txt',single_attempt=True,timeout_seconds=7200,materialization_order='authorization -> SHA256 -> runtime -> SHA256 -> launcher -> exclusive attempt claim -> unique tmux',parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,transport='Original file bytes Base64; raw byte response capture; wsl --exec; command line <=2048 bytes')
q['provenance']=dict(preparation_receipt=bind(PRE/'preparation_validation_receipt_v1.json'),scope=bind(PRE/'LQI_CD_210_Native_prediction_scope_v1.json'),formal_LQI_C_D_training_frozen=True,frozen_F0_prediction_audit=scope['frozen_F0_prediction_audit'],current_server_rechecked=False,current_identity_source='Last formal LQI FoldD v2 freeze audit in zv9bqd-0; not a live check',current_readiness='MANDATORY_BEFORE_INSTALLATION_AND_EXECUTION; no claim of fresh readiness',CPU_success_not_CUDA_or_scientific_success=True,F0_predictions_reused_no_reinference=True,no_outcome_driven_case_selection=True,real_forwards_this_task=0)
q['not_authorized']=['Execution before separate full request SHA256 authorization','Training/BNCal/loss/backward/optimizer steps','Warmup/TTA/ICP/GT alignment/postfilter','Mechanism interventions, F0 re-inference, extra cases or GT payload reads','Automatic retry/resume or continuing after first failure','Dependency download/build/install/upgrade or GPU preflight repeat','Scoring/bootstrap/formal gate']
q['installation_prerequisites']=['Freshly verify exact current hostname/UID/Python/GPU UUID/idle <=256MiB and frozen resource budgets; drift or unknown stops','Reverify archive SHA256/bytes/content set, all new install/control/output paths absent and safe parents; exclusive create only','Reverify both LQI checkpoint SHA256/bytes, training/pairing/admission and all reused source/config/provider/dependency pins','Reverify all210 input file identities; do not read target arrays','Separate complete request SHA256 execution authorization before any real authorization/runtime/launcher/attempt claim/tmux materialization','Failure stops; no automatic retry/resume, scoring or training']
q['limits']=e.LIMITS
# Review in memory only: no real launcher or authorization/runtime files created.
template=e.render_launcher(q,'a'*64,'b'*64,'c'*64)
command=next(line for line in template.splitlines() if line.startswith('/usr/bin/timeout'))
assert 'LQI_CD_native_development_20261111_v1' in template and all('\\' not in token for token in shlex.split(command))
req=T/'LQI_CD_native_prediction_execution_request_v1.json';emit(req,q)
mapping.append(dict(local=str(req.resolve()),target=q['launch_contract']['request_path'],bytes=req.stat().st_size,sha256=sha(req),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
# Validate final request authorization contract entirely in memory; not a real authorization.
qrec=bind(req);oldbound=e.bound
fake={'Q':q,'A':dict(schema='bcsp-development-authorization-v1',request_sha256=qrec['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_MEMORY_ONLY_NOT_USER_AUTHORIZATION'),'R':dict(schema='bcsp-development-runtime-v1',request_sha256=qrec['sha256'],authorization_sha256='b'*64)}
try:
 e.bound=lambda r:fake[r['path']]
 assert e.authorize(dict(qrec,path='Q'),dict(path='A',sha256='b'*64),dict(path='R'))==q
finally:e.bound=oldbound
assert q['input_index']['sha256']==e.INDEX_SHA and q['protocol']['sha256']==e.PROTOCOL_SHA
for k,h in e.PINS.items():assert q['implementation'][k]['sha256']==h
emit(O/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED',remote_root=remote,files=mapping,reused_exact_bindings={k:q[k] for k in ['identity','model_root','preflight_scope','static_config','numeric_policy','fold_binding','source_index','source_manifest','helper','implementation','dependencies','prior_native_admission']},checkpoints=[r['checkpoint'] for r in index['runs']],input_files=210,not_materialized=[q['launch_contract'][k] for k in ['authorization','runtime','launcher']]+[q['launch_attempt'],output]))
archive=O/'bcsp_lqi_CD_native_prediction_pending_20261111_v1.tar.gz'
members=[(p,'payload/'+p.name) for p in sorted(T.iterdir())]+[(O/'installation_mapping_v1.json','installation_mapping_v1.json')]
with archive.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as tar:
  for p,n in members:
   data=p.read_bytes();ti=tarfile.TarInfo(n);ti.size=len(data);ti.mode=0o600;ti.mtime=0;tar.addfile(ti,io.BytesIO(data))
with tarfile.open(archive,'r:gz') as tar:
 assert len(tar.getmembers())==len(members)
 for p,n in members:assert tar.extractfile(n).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+n+'\n' for p,n in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(req),archive=bind(archive),installation_files=len(mapping),CPU_contracts=46,synthetic_forwards=210,P3_status=p3['status'],real_forwards=0,server_operations=0,authorized_controls_materialized=False,forward_budget=210,repeat_preflight=False,final_request_memory_authorization_contract=True,fresh_server_readiness_required=True)
emit(O/'pending_request_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))
