"""Local P3 and pending request only. Never materializes authorized controls or calls server."""
import ast,hashlib,importlib.util,io,json,shutil,tarfile,copy,shlex
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;R=S.parents[2];PRE=S.parent/'Native_prediction_preparation_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def read(p):return json.loads(p.read_bytes())
def emit(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
entry=S/'bcsp_f0_twofold_native_predict_v1.py';test=S/'test_f0_native_prediction_cpu_v1.py';cpu=S/'artificial_cpu_batch_v1/result_v1.json';result=read(cpu);static=read(S/'static_review_v1.json')
assert result['status']=='F0_NATIVE_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==42 and result['synthetic_forwards']==210 and result['real_decoder_trace_comparison_calls']==2
assert not (cpu.parent/'failure_v1.json').exists()
for rec in result['source_bindings']:assert bind(Path(rec['path']))==rec
for rec in static['files']:assert sha(S/rec['name'])==rec['sha256']
assert static['status']=='STATIC_S0_S1_PASS' and all(static['checks'].values())
policy=read(cpu.parent/'source_policy_stdout.bin');assert all(policy.values())
spec=importlib.util.spec_from_file_location('f0_native_freeze_entry',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
index=read(PRE/'F0_CD_Native_input_index_candidate_v1.json');selection=read(PRE/'recipient_donor_registration_addendum_v1.json')
G=R/'outputs/cranial_bcsp_geov1_20261024'
e.validate_index(index,read(G/'consolidated_binding_v1/fold_binding.json'),selection)
e.validate_source(index,read(G/'development_eval_v1/development_input_index_v1.json'),[json.loads(x) for x in (G/'real_data_qc_v1/manifest_8192.jsonl').read_text().splitlines()])
for run in index['runs']:
 a=read(Path(run['training_audit']['path']));assert sha(Path(run['training_audit']['path']))==e.FROZEN_MODELS[run['label']]['audit_sha256'] and all(a['checks'].values())
 assert a['checkpoint']['sha256']==run['checkpoint']['sha256'] and a['counts']['updates']==3900
old=R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_fourmodel_prediction_implementation_v1/bcsp_h2_fourmodel_native_predict_v1.py'
def nodes(f):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(f.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
inherited=['load_partial','predict_once','source_module','make_policy','Budget','pack','rng_state','geometry_summary'];a,b=nodes(old),nodes(entry);assert all(a[n]==b[n] for n in inherited)
checks=dict(final_source_bytes_match_CPU_and_static=True,actual_four_source_load_under_audit_hook=True,full_authorization_runtime_path_tested=True,F0_production_factory_signature_tested_with_surrogate=True,actual_decoder_trace_on_off_same_CPU_values=True,mother_cache_control_methods_reused_and_cleared=True,all210_coarse20_context10_trace_same_forward=True,GT_payload_never_decoded=True,exact_checkpoint_and_C_D_training_audit_pins=True,strict_checkpoint_negative_cases=True,state_and_CPU_RNG_invariants_tested=True,first_error_stops_before_next_model=True,original_numeric_resource_payload_guards_AST_unchanged=True,POSIX_launcher_parent_before_redirect=True,protocol_timing_deviation_disclosed_not_backdated=True)
p3=dict(status='LOCAL_F0_NATIVE_PREDICTION_P3_PASS',date='2026-11-11',entry_sha256=sha(entry),test_sha256=sha(test),CPU_result=bind(cpu),CPU_checks=42,static_review=bind(S/'static_review_v1.json'),checks=checks,inherited_parent=bind(old),inherited_AST_unchanged=inherited,actual_source_policy=policy,CPU_runtime=dict(python='E:/RelocatedData/zhj/.conda/envs/adapointr/python.exe',torch='2.5.1+cpu'),scope=bind(PRE/'F0_CD_210_Native_prediction_scope_draft_v1.json'),input_index=bind(PRE/'F0_CD_Native_input_index_candidate_v1.json'),selection=bind(PRE/'recipient_donor_registration_addendum_v1.json'),limitations=result['limitations']+['No current server readiness or upload verification in this task','Resource samples before/after each call, external timeout; no dedicated hard GPU/RSS isolation','Opaque extension kernel audit remains limited to prior admission evidence; no universal attention-free kernel claim','Representative five defect types share one recipient source per fold; no independent-patient claim'],real_forwards=0,real_checkpoint_loads=0,real_payload_arrays=0,server_operations=0,GPU_calls=0,repeat_preflight=False)
emit(S/'implementation_P3_v1.json',p3)
O=S/'pending_request_v1';O.mkdir();T=O/'transport_payload';T.mkdir()
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_native_prediction_20261111_v1';output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_development_20261111_v1';mapping=[]
def stage(p,name=None):
 n=name or p.name;t=T/n;shutil.copyfile(p,t);r=dict(path=str(PurePosixPath(remote)/n),bytes=t.stat().st_size,sha256=sha(t));mapping.append(dict(local=str(t.absolute()),target=r['path'],bytes=r['bytes'],sha256=r['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'));return r
train=read(S.parent/'training_entry_v1/F0_FoldC_training_execution_request_v1.json')
oldq=read(old.parent/'pending_request_v1/transport_payload/H2_C_D_fourmodel_native_prediction_execution_request_v1.json')
q=dict(schema='bcsp-f0-twofold-native-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='CRANIAL_BCSP_FULLMAMBA',run_id='F0_CD_native_development_20261111_v1',variant='F0-P-v2',fold='C_D',seed=0,n_input=8192,n_output=8192,batch_size=1,forward_budget=210,unique_cases=210,loss_calls=0,backward=0,optimizer_steps=0,BNCal=0,warmup=0,TTA=0,identity=train['identity'],model_root=train['model_root'],static_config=train['static_config'],preflight_scope=train['preflight_scope'],dependencies=train['dependencies'],environment=train['environment'],limits=e.LIMITS,output=output,launch_attempt=remote+'/control/native_prediction_single_attempt_claim_v1.json',selection_registration_timing='RULE_PRETRAINING_LITERAL_IDS_PRE_NATIVE_NOT_PRETRAINING')
q['entry']=stage(entry);q['input_index']=stage(PRE/'F0_CD_Native_input_index_candidate_v1.json');q['protocol']=stage(PRE/'F0_CD_210_Native_prediction_scope_draft_v1.json');q['selection']=stage(PRE/'recipient_donor_registration_addendum_v1.json');q['P3']=stage(S/'implementation_P3_v1.json')
stage(test);stage(cpu,'CPU_contract_result_v1.json');stage(S/'static_review_v1.json');stage(PRE/'recipient_donor_pairs_v1.csv')
q['training_audits']={run['label']:stage(Path(run['training_audit']['path']),'frozen_'+run['label']+'_training_audit_v1.json') for run in index['runs']}
for k in ['numeric_policy','source_index','source_manifest','fold_binding','helper']:q[k]=oldq[k]
q['implementation']={k:train['implementation'][k] for k in ['encoder','factory','f0_decoder','f0_factory','timezone']}
q['prior_native_admission']=dict(receipt=train['admission']['receipt'],audit=train['admission']['audit'],repeat_preflight=False)
q['expected_artifacts']=dict(predictions=210,coarse_saved=210,context=20,trace=10,trace_layers=8,context_fields=['F','S','z','Q','X'],prediction_keys=['prediction','coarse'],normalized_native=True,GT_alignment=False,postfilter=False,additional_decoder_interventions=0)
control=remote+'/control';lc=dict(tmux_session='bcsp_f0_CD_native_eval_20261111_v1',request_path=remote+'/F0_CD_native_prediction_execution_request_v1.json',authorization=control+'/native_prediction_authorization_v1.json',runtime=control+'/native_prediction_runtime_v1.json',launcher=control+'/native_prediction_launch_once_v1.sh',log=output+'/launch.log',pid=output+'/worker.pid',exit_code=output+'/exit_code.txt',single_attempt=True,timeout_seconds=7200,materialization_order='authorization -> SHA256 -> runtime -> SHA256 -> launcher -> exclusive attempt claim -> unique tmux',parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,transport='Original file bytes directly Base64 encoded; raw byte response capture; wsl --exec, no PowerShell text recoding; command length bound2048')
q['launch_contract']=lc
q['installation_prerequisites']=['Reverify current hostname/UID/Python/GPU UUID and device idle <=256MiB; no reuse of historic identity as current proof','Reverify exact package SHA256/bytes/contents and all new install/output/control targets absent with safe real parents; exclusive create only','Reverify both final checkpoint SHA256/bytes, training audits and all reused dependencies/provider/source/config/metadata bindings','Reverify exact210 development input identities without decoding target tensors','Prior confirmed numeric policy and resource thresholds unchanged; PID namespace telemetry diagnostic only','Separate full request hash execution authorization before materializing receipt/runtime/launcher or starting unique tmux; stop on failure; no automatic retry/resume']
q['provenance']=dict(preparation=bind(PRE/'preparation_manifest_v1.json'),training_audits_frozen=True,current_server_rechecked=False,current_identity_source='Last formally frozen n8xph5-0; fresh readiness verification required',selection_rule_pretraining_literal_ids_preNative=True,selection_timing_deviation_disclosed=True,no_outcome_driven_reselection=True,CPU_success_not_CUDA_or_scientific_success=True,baseline_T0_M0_predictions_reused=True,no_extra_training=True)
q['not_authorized']=['Execute before separate complete request hash authorization','Training/BNCal/loss/backward/optimizer steps','Warmup/TTA/ICP/GT alignment/postfilter','Additional30 decoder interventions or baseline re-inference','New or unopened cases, GT tensor reads, changed sampling/thresholds','Automatic retry/resume or continuing after first failure','Dependency download/build/install/upgrade or GPU preflight repeat','Scoring/bootstrap/formal gate']
# Render a NON-EXECUTABLE review template; never materialize an authorized launcher.
template=e.render_launcher(q,'a'*64,'b'*64,'c'*64).replace('a'*64,'REQUEST_SHA256').replace('b'*64,'AUTHORIZATION_SHA256').replace('c'*64,'RUNTIME_SHA256')
tpl=O/'launcher_REVIEW_TEMPLATE_NOT_AUTHORIZED_v1.txt'
with tpl.open('x',encoding='utf-8',newline='\n') as f:f.write(template)
lc['review_template']=stage(tpl)
req=T/'F0_CD_native_prediction_execution_request_v1.json';emit(req,q)
mapping.append(dict(local=str(req.absolute()),target=lc['request_path'],bytes=req.stat().st_size,sha256=sha(req),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
# Verify final candidate uses the same validation path, with local test controls already generated in CPU batch, without materializing real controls.
assert q['input_index']['sha256']==e.INDEX_SHA and q['protocol']['sha256']==e.PROTOCOL_SHA and q['selection']['sha256']==e.SELECTION_SHA
assert q['P3']['sha256']==sha(S/'implementation_P3_v1.json') and q['entry']['sha256']==sha(entry)
tokens=shlex.split(next(x for x in template.splitlines() if x.startswith('/usr/bin/timeout')))
assert tokens[tokens.index('--request')+1]==lc['request_path'] and not any('\\' in t for t in tokens[:16])
emit(O/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED',remote_root=remote,files=mapping,reused_exact_bindings={k:q[k] for k in ['identity','model_root','preflight_scope','static_config','numeric_policy','fold_binding','source_index','source_manifest','helper','implementation','dependencies']},checkpoints=[run['checkpoint'] for run in index['runs']],unique_input_files=210,not_materialized=[lc['authorization'],lc['runtime'],lc['launcher'],q['launch_attempt'],output]))
archive=O/'bcsp_f0_CD_native_prediction_pending_20261111_v1.tar.gz';members=[(p,'payload/'+p.name) for p in sorted(T.iterdir())]+[(O/'installation_mapping_v1.json','installation_mapping_v1.json')]
with archive.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as tar:
  for p,n in members:
   data=p.read_bytes();info=tarfile.TarInfo(n);info.size=len(data);info.mode=0o600;info.mtime=0;tar.addfile(info,io.BytesIO(data))
with tarfile.open(archive,'r:gz') as tar:
 assert len(tar.getmembers())==len(members)
 for p,n in members:assert tar.extractfile(n).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+n+'\n' for p,n in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(req),archive=bind(archive),installation_files=len(mapping),CPU_contracts=42,synthetic_forwards=210,real_forwards=0,P3_status=p3['status'],server_operations=0,authorized_controls_materialized=False,forward_budget=210,coarse=210,context=20,traces=10,repeat_preflight=False)
emit(O/'pending_request_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))
