"""Freeze Fold D8k transport and pending scope after real-authorize CPU contracts."""
from pathlib import Path
import copy,hashlib,importlib.util,io,json,tarfile
N=Path(__file__).resolve().parent;B=N.parent;I=N/'implementation_v1'
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
def raw(p):return Path(p).read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(raw(p))
def dump(name,d):
 p=N/name
 with p.open('x',encoding='ascii',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=True,allow_nan=False);f.write('\n')
 return p
def bind(p,server=None):
 r=dict(path=str(Path(p).absolute()),bytes=len(raw(p)),sha256=sha(raw(p)))
 if server:r['future_server_path']=server
 return r
q=load(N/'training_entry_request_candidate_v1.json');results=load(I/'cpu_contract_v1/results_v1.json')
assert results['status']=='PASS_15_FULL_AUTHORIZE_CPU_CONTRACTS' and results['testsRun']==15
pair=load(N/'paired315_data_verification_v1.json');assert pair['train_cases']==315 and pair['all_targets_byte_identical'] and pair['all8192_inputs_are_16384_prefixes']
ep=I/'bcsp_training_entry_foldD_8192_v7.py';cp=I/'bcsp_training_contract_foldD_8192_v5.py'
oldcp=(P/'bcsp_training_contract_01dt08_v3.py').read_text()
expected=oldcp.replace("require(q['fold'] == 'C' and q['n_input'] == 8192, 'first rebound run only')","require(q['fold'] == 'D' and q['n_input'] == 8192, 'Fold D 8k arm only')")
expected=expected.replace("q['order_plan']['sha256'] == IMMUTABLE['order_plan']","q['order_plan']['sha256'] == FOLD_D_ORDER_SHA")
order=N/'shared_order_foldD_seed0_v1.json';qualified=N/'qualified_data_qc_foldD_8192_v1.json'
expected=expected.replace('def authorize(request_record, authorization_record, runtime_record):',"# Current Fold D order is pinned separately; IMMUTABLE retains historical rebind evidence.\nFOLD_D_ORDER_SHA = '"+sha(raw(order))+"'\n\ndef authorize(request_record, authorization_record, runtime_record):")
assert cp.read_text()==expected
expected=(P/'bcsp_training_entry_research_v5.py').read_text().replace('bcsp_training_contract_01dt08_v3.py',cp.name).replace('08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499',sha(raw(cp)))
assert ep.read_text()==expected
spec=importlib.util.spec_from_file_location('FoldD_order_metadata_check',cp);contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
folds=load(B/'consolidated_binding_v1/fold_binding.json');contract.validate_order(load(order),folds['folds']['D']['train_case_ids'])
expected_qualified=dict(schema='bcsp-training-qualified-QC-v1',status='QUALIFIED_FOR_FIXED_TRAINING_GEOMETRY',verification=q['QC']['verification'],manifests=q['QC']['manifests'],fold_binding=q['QC']['fold_binding'],fold='D',n_input=8192,manifest_sha256=q['QC']['manifests']['8192']['sha256'],train_allowlist_sha256=folds['folds']['D']['train_allowlist_sha256'],limitations=list(contract.LIMITS),payload_reverified_by_this_mapping=False)
assert load(qualified)==expected_qualified
p3=dump('local_P3_v1.json',dict(status='PASS_FOLD_D_MINIMAL_INTERFACE_AND_FULL_AUTHORIZE_CPU',date_Asia_Shanghai='2026-10-26',
 real_authorize_CPU_contracts=results,additional_controller_predicates=dict(positive=4,negative=3),actual_order_validator_passed=True,
 only_contract_changes=['Dedicated FoldD8192 gate','Dedicated FoldD orderSHA separate from unchanged historical receipt constants'],entry_change='Sibling contract filename/SHA only',
 model_runtime_static_sampling_backend_numeric_resources_unchanged=True,
 files=[bind(p) for p in [ep,cp,I/'test_full_authorize_v1.py',I/'cpu_process_capture_v1.json',I/'cpu_stdout_v1.log',I/'cpu_stderr_v1.log',I/'cpu_contract_v1/results_v1.json',N/'candidate_static_review_v1.json',N/'shared_order_derivation_v1.json',N/'paired315_data_verification_v1.json']],
 CPU_fixture_inventory=[dict(file=str(p.relative_to(N)),bytes=p.stat().st_size,sha256=sha(raw(p))) for p in sorted((I/'cpu_contract_v1').rglob('*')) if p.is_file()],
 server_writes=0,CUDA_calls=0,limitation='CPU metadata success is not GPU full training admission;unchanged resource monitoring and stop contract apply'))
qp=N/'training_entry_request_v1.json'
with qp.open('xb') as f:f.write(raw(N/'training_entry_request_candidate_v1.json'))
CODE=q['implementation']['entry']['path'].rsplit('/',1)[0]
DATA=q['data_root'];CONTROL=q['launch_attempt'].rsplit('/',1)[0];OUT=q['output']
items=[]
for r in pair['case_rows']:
 items.append(dict(archive_member=r['point_path'],target=DATA+'/'+r['point_path'],bytes=r['bytes'],sha256=r['sha256'],local_file=str((B/'real_data_qc_v1'/r['point_path']).absolute())))
for p,target in [(ep,q['implementation']['entry']['path']),(cp,q['implementation']['contract']['path']),(order,q['order_plan']['path']),(qualified,q['QC']['qualified_receipt']['path'])]:
 items.append(dict(archive_member='code/'+p.name,target=target,bytes=len(raw(p)),sha256=sha(raw(p)),local_file=str(p.absolute())))
assert len(items)==319
mp=dump('installation_mapping_v1.json',dict(schema='bcsp-foldD-8192-minimal-installation-v1',status='PREPARED_NOT_DEPLOYED',expected_identity=q['identity'],project=q['identity']['project'],code_root=CODE,data_root=DATA,
 directories=[DATA,DATA+'/points'],files=items,reused_static=q['static_config'],reused_runtime=q['implementation']['runtime'],
 rules=['Before writing recheck identity,archive hash,all319 targets absent and safe parents','Exclusive no-follow writes;create only two listed data directories;never overwrite','Verify all319 installed hashes;no installation scripts','Recheck GPUidle,memory/disk/timeout budgets and unused control/output/tmux immediately before one launch','Failure stops;no automatic retry,resume,batch/backend change or cleanup']))
archive=N/'bcsp_foldD_8192_seed0_inputs_and_entry_v1.tar.gz'
with archive.open('xb') as out:
 with tarfile.open(fileobj=out,mode='w:gz') as tf:
  for r in items:
   data=raw(r['local_file']);assert len(data)==r['bytes'] and sha(data)==r['sha256']
   ti=tarfile.TarInfo(r['archive_member']);ti.size=len(data);ti.mode=0o644;ti.mtime=0
   tf.addfile(ti,io.BytesIO(data))
with (N/(archive.name+'.sha256')).open('x') as f:f.write(sha(raw(archive))+'  '+archive.name+'\n')
with (N/'bcsp_foldD_8192_seed0_inputs_and_entry_v1.contents.sha256').open('x') as f:
 for r in items:f.write(r['sha256']+'  '+r['archive_member']+'\n')
s=load(P/'training_execution_request_v4.json');oldout=s['future_paths']['output'];oldcontrol=s['future_paths']['entry_request'].rsplit('/',1)[0]
def rewrite(v):
 if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
 if isinstance(v,list):return [rewrite(x) for x in v]
 if isinstance(v,str):return v.replace(oldout,OUT).replace(oldcontrol,CONTROL).replace('bcsp_geov1_b0_foldc_in8192_seed0_train_v3','bcsp_geov1_b0_foldd_in8192_seed0_train_v1')
 return v
s=rewrite(s);s['request_version']=1;s['run_id']=q['run_id'];s['actual_training_attempt_index']=1
s['request_kind']='First Fold D8k baseline scratch attempt;exclusive installation of315NPZ,two metadata files andtwo dedicated modules;one training launch after new fullSHA authorization'
s['entry_request']=bind(qp,CONTROL+'/training_execution_request_v1.json');s['future_paths']['execution_scope']=CONTROL+'/training_execution_scope_v1.json'
s['parent_evidence']=dict(resources=bind(N/'resources_observation_v1.json'),reused_assets=bind(N/'assets_observation_v1.json'),fresh_targets=bind(N/'freshness_observation_v1.json'),paired_FoldD_data=bind(N/'paired315_data_verification_v1.json'),FoldD_order_derivation=bind(N/'shared_order_derivation_v1.json'),implementation_P3=bind(p3),
 FoldC8_freeze=bind(P/'freeze_audit_v1/audit_report_v1.json'),FoldC16_freeze=bind(B/'foldC_16384_training_v1/authorize_gate_hotfix_v2/freeze_audit_v1/audit_report_v1.json'))
s['scientific_contract']['fold']='D';s['scientific_contract']['order_plan']=q['order_plan'];s['scientific_contract']['qualified_QC']=q['QC']['qualified_receipt']
s['scientific_contract']['real_payload_scope']='Only exact315 Fold D train8k NPZ;21 Fold D development sources and20 confirmation sources excluded;C/D training sources overlap by planned cross-validation'
s['scientific_contract']['shared_order_semantics']='Within Fold D both input arms share this exact order;case IDs differ fromFold C but use the same frozen315-position permutations'
resource=load(N/'resources_observation_v1.json')
s['resource_snapshot_evidence']=dict(UTC=resource['UTC'],GPU_memory_used_MiB=1,compute_processes=0,disk_free_bytes=resource['disk']['free'],not_persistent_admission=True,recheck_before_launch=True)
s['future_materialization_contract']['authorization_schema']['request_sha256']=sha(raw(qp));s['future_materialization_contract']['runtime_schema']['request_sha256']=sha(raw(qp))
argv=s['future_materialization_contract']['external_training_argv'];argv[8]=q['implementation']['entry']['path'];argv[argv.index('--request-sha256')+1]=sha(raw(qp))
s['prelaunch_guards'][1]='Verify319-file exact installation and existing frozen model/provider/environment,static/runtime/QC bindings;no broad inventory or downloads'
s['prelaunch_guards'][3]='Frozen Fold D315 train-case allowlist and shared_order_foldD_seed0_v1;never substitute Fold C case IDs or regenerate GPU-launch shuffle'
s['local_serialization']['controller_template']=bind(N/'controller_template_foldD_8192_v1.py')
s['local_serialization']['future_rendering_contract'][0]='Only after new fullSHA grant and verified319-file installation,load exact raw finalscope,strict entryrequest and current-device risk record;validate every bound hash before rendering.'
s['previous_attempt']=dict(status='FIRST_ATTEMPT_FOR_FOLD_D_8192',earlier_C_grants_reusable=False,new_attempt_is_scratch=True)
s['known_failure_and_diagnostic_scope']=dict(dedicated_FoldD8192_gate_and_order_pin=True,full_authorize_CPU_contracts_passed=15,all_resource_thresholds_unchanged=True,PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE',no_new_GPU_preflight=True)
s['minimal_deployment']=dict(status='PREPARED_NOT_DEPLOYED',installation_mapping=bind(mp),archive=bind(archive),future_upload_path='/home/jovyan/'+archive.name,
 full_scope_execution_authorization_covers='After manual upload,exclusive319-file installation and readback hashes,then exactly one new Fold D8k tmux training attempt',failure_stops_before_training=True,installed_verification_required_before_controller=True)
s['FoldD_design']=dict(train_sources=63,train_cases=315,development_sources=21,development_cases=105,confirmation_excluded=20,train_allowlist_sha256=pair['train_allowlist_sha256'],
 same_initial_parameter_and_persistent_state_expected={k:v for k,v in load(N/'assets_observation_v1.json')['parent_initialization'].items() if k!='order_sha256'},
 order_SHA256=q['order_plan']['sha256'],order_canonical_SHA256=sha(json.dumps(load(order),sort_keys=True,separators=(',',':'),allow_nan=False).encode()),
 initialization_note='Model seed0 and architecture unchanged;parameter/persistent fingerprints should matchC,while case-order fingerprint must matchnew Fold Dorder',
 historical_rebind_note='Inherited resource receipt and its IMMUTABLE hashes remain historical source evidence;actual Fold D order is separately pinned in dedicated contract',
 paired_16k_training_not_authorized=True)
s['current_task_boundary']=dict(server_operations='Three bounded readonly queries only',server_writes=0,CUDA_calls=0,local_files='FoldD315 pairing proof,shared order,two modules,15 full authorize CPUcontracts,P3,transport,pending requests',production_authorization_created=False,runtime_config_created=False,launcher_created=False,training_started=False)
s['next']='Upload exact archive,then separately authorize this fullSHA for frozen installation and one Fold D8k run;no automatic training,BNCal,evaluation or16k followup'
op=dump('training_execution_request_v1.json',s)
with (N/'training_execution_request_v1.json.sha256').open('x') as f:f.write(sha(raw(op))+'  '+op.name+'\n')
print(json.dumps(dict(status='PREPARED_AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(op),archive=bind(archive),transport_files=319,CPU_authorize_contracts_passed=15,server_writes=0,training_started=False)))
