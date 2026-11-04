"""One-task local preparation; never invokes a server or training."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,tarfile,io

N=Path(__file__).resolve().parent
V=N.parent
M=V.parent
R=M.parent
BASE=next(p for p in N.parents if p.name=='mamba-ccf-c-1-high-resolution')
PROJECT='/home/jovyan/adapointr_work/PoinTr'
CODE=PROJECT+'/third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
EVID=CODE+'/evidence/research_priority_01dt08_v1'
def raw(p):return Path(p).read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(name,d):
 p=N/name
 with p.open('x',encoding='ascii',newline='\n') as f:json.dump(d,f,ensure_ascii=True,indent=2);f.write('\n')
 return p
def bind(p,server=None):
 p=Path(p);r=dict(path=str(p),bytes=len(raw(p)),sha256=sha(raw(p)))
 if server:r['future_server_path']=server
 return r
def remote(p,server):return dict(path=server,bytes=len(raw(p)),sha256=sha(raw(p)))
def load(p):return json.loads(raw(p))

res=load(N/'resources_observation_v1.json')
assets=load(N/'selected_assets_observation_v1.json')
installed=load(N/'installed327_observation_v1.json')
fresh=load(N/'freshness_observation_v1.json')
assert res['hostname']=='shu-common-25721452-notebook-01dt08-0' and res['uid']==1000
g=[x.strip() for x in res['gpu']['stdout'].strip().split(',')]
assert len(res['gpu']['stdout'].strip().splitlines())==1 and res['gpu']['returncode']==0
assert g[1:4]==['NVIDIA GeForce RTX 4090 D','570.190','24564'] and int(g[4])<=256
assert res['compute_processes']['returncode']==0 and not res['compute_processes']['stdout'].strip()
assert res['disk']['free']>=4294967296
assert fresh['python']==dict(returncode=0,version='Python 3.10.20') and fresh['tmux_returncode']==1
assert all(not x['exists'] and x['parent_exists'] and x['parent_writable'] for x in fresh['paths'])
manifest=BASE/'outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/transport_v1/bcsp_foldc_8192_train_inputs_v1.contents.sha256'
assert sha(raw(manifest))=='1d5f43673c76b93d3195aad25e19de4a229fdc2c23505395d993c548175b823e'
expected={}
for line in raw(manifest).decode().splitlines():
 h,p=line.split('  ',1)
 expected[(CODE+'/'+p[5:]) if p.startswith('code/') else (PROJECT+'/data/bcsp_geov1_foldc_8192_seed0_v1/'+p[5:])]=h
assert len(expected)==len(installed['rows'])==327
assert all(x['status']=='PRESENT' and x['sha256']==expected[x['path']] for x in installed['rows'])
assert len({x['path'] for x in installed['rows']})==327
assert len(assets['assets'])==30
old_receipt=load(R/'resource_rebind_receipt_v1.json')
identity=dict(old_receipt['new_identity'],hostname=res['hostname'],gpu_uuid=g[0],driver_version=g[2])
asset_report=dict(status='READONLY_CHECK_COMPLETE_UPLOAD_PASS_EXECUTION_IDENTITY_REBIND_REQUIRED',
 actual_identity_resources=dict(hostname=res['hostname'],uid=1000,project=PROJECT,GPU=res['gpu'],disk=res['disk'],python=fresh['python']),
 frozen_assets=dict(status='ASSETS_MATCH',matching_files=30,selected_files=30,
 manifest=[dict(path=x['path'],expected_bytes=x['bytes'],expected_sha256=x['sha256']) for x in assets['assets']]),
 installed_training_assets=dict(status='ALL_327_SHA256_MATCH',files=327,hashed_bytes=installed['hashed_bytes']),
 raw_observations=[bind(N/(x+'_observation_v1.json')) for x in ['resources','selected_assets','installed327','freshness']],
 server_writes=0,CUDA_calls=0,current_GPU_execution_validated=False)
rp=dump('readonly_identity_assets_01dt08_v1.json',asset_report)
receipt=copy.deepcopy(old_receipt)
receipt['new_readonly_report']=remote(rp,rp.name)
receipt['new_identity']=identity
receipt['identity_differences']=[dict(field=k,old=receipt['old_identity'][k],new=identity[k]) for k in ['hostname','gpu_uuid','driver_version']]
rr=dump('resource_rebind_01dt08_v1.json',receipt)
old_contract=raw(R/'bcsp_training_contract_v2.py').decode()
text=old_contract.replace(old_receipt['new_identity']['hostname'],identity['hostname']).replace(old_receipt['new_identity']['gpu_uuid'],identity['gpu_uuid'])
text=text.replace(sha(raw(R/'resource_rebind_receipt_v1.json')),sha(raw(rr)))
text=text.replace('readonly_identity_assets_upload_report_v1.json',rp.name)
text=text.replace("'bytes': 22014","'bytes': "+str(len(raw(rp))))
text=text.replace('1ccb8c7fc712cdecb04f260d84b827e422fb1d6926110664783f0033ef9a33c6',sha(raw(rp)))
cp=N/'bcsp_training_contract_01dt08_v3.py'
with cp.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
text=raw(V/'bcsp_training_entry_v4.py').decode()
text=text.replace('bcsp_training_contract_v2.py',cp.name).replace('88b0098ec199fcba7e37c9ca2be7a8d6b69ff246ab0f1b9494445e4a72b41db3',sha(raw(cp)))
ep=N/'bcsp_training_entry_research_v5.py'
with ep.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
for p in [cp,ep]:compile(raw(p),str(p),'exec')
# The candidate differs from the CPU-verified entry only in its sibling module pin.
expected_entry=raw(V/'bcsp_training_entry_v4.py').decode().replace('bcsp_training_contract_v2.py',cp.name).replace('88b0098ec199fcba7e37c9ca2be7a8d6b69ff246ab0f1b9494445e4a72b41db3',sha(raw(cp)))
assert raw(ep).decode()==expected_entry
spec=importlib.util.spec_from_file_location('research_entry_01dt08_offline',ep)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
contract=sys.modules['bcsp_training_contract_v1']
scope=load(BASE/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json')
assert contract.validate_rebind_value(receipt,scope,asset_report)==receipt
for kind in ['wrong_UUID','wrong_report_status']:
 a=copy.deepcopy(receipt);b=copy.deepcopy(asset_report)
 if kind=='wrong_UUID':a['new_identity']['gpu_uuid']='wrong'
 else:b['status']='wrong'
 try:contract.validate_rebind_value(a,scope,b)
 except ValueError:pass
 else:raise AssertionError(kind+' accepted')
p3=dump('local_P3_01dt08_v1.json',dict(status='PASS_MINIMAL_BINDING_ADAPTATION_AND_CPU_METADATA_CHECKS',entry=bind(ep),contract=bind(cp),
 original_resource_CPU_P3=bind(V/'local_P3_receipt_v4.json'),resource_sample_unchanged_from_10_passed_CPU_checks=True,
 new_binding_checks=['entry exact sibling bootstrap','valid current identity metadata accepted','wrong GPU UUID rejected','wrong report status rejected'],
 model_data_runtime_static_order_unchanged=True,server_operations=0,CUDA_calls=0,training_steps=0,
 limitations=['No CUDA execution on current GPU; successful training not guaranteed','Running GPU process ownership is diagnostic only']))
q=load(M/'continuation_train_v2_request_v1/training_entry_request_v3.json')
q['identity']=identity;q['run_id']='bcsp_geov1_b0_foldC_in8192_out8192_seed0_train_v3'
q['output']=PROJECT+'/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3'
q['launch_attempt']=CODE+'/control_train_v3/launch_attempt_v1.json'
q['resource_rebind']=remote(rr,EVID+'/'+rr.name)
q['implementation']['entry']=remote(ep,CODE+'/'+ep.name)
q['implementation']['contract']=remote(cp,CODE+'/'+cp.name)
qp=dump('training_entry_request_v4.json',q)
accept=dict(schema='bcsp-new-device-migration-uncertainty-acceptance-v1',date_Asia_Shanghai='2026-10-26',
 status='PENDING_SCOPE_APPROVAL_CURRENT_DEVICE_UNCERTAINTY_DISCLOSED',new_identity=identity,
 authorizes_only_pending_request_creation=True,is_training_execution_authorization=False,new_gpu_execution_validated=False,
 historical_GPU_evidence_only=True,explicit_current_device_execution_acceptance=False,
 future_full_scope_execution_grant_accepts_disclosed_risk=True,
 accepted_remaining_uncertainty=['No current-device CUDA or complete3900-step validation','No strict running-process ownership guarantee; initial idle and all memory/resource ceilings retained','Failure stops;no automatic retry/resume or threshold/backend changes'])
ap=dump('migration_uncertainty_current_device_v2.json',accept)
# Freeze a small data-only package; installation remains a future authorized action.
items=[(ep,CODE+'/'+ep.name),(cp,CODE+'/'+cp.name),(rp,EVID+'/'+rp.name),(rr,EVID+'/'+rr.name),(p3,EVID+'/'+p3.name),(V/'research_priority_policy_v4_zh.md',EVID+'/research_priority_policy_v4_zh.md')]
mapping=dict(schema='bcsp-research-priority-minimal-installation-v1',status='PREPARED_NOT_DEPLOYED',expected_identity=identity,
 project=PROJECT,new_directory=EVID,files=[dict(archive_member=p.name,source=bind(p),target=t,bytes=len(raw(p)),sha256=sha(raw(p))) for p,t in items],
 rules=['Before writing recheck current identity,archive hash,all six targets absent and all parents safe','Create only the one new evidence directory; use exclusive no-follow file creation,never overwrite','Verify all six installed sizes/hashes and two reused modules before training controller','No installation scripts or model/data changes','Any partial or ambiguous failure stops;do not retry automatically'])
mp=dump('minimal_installation_mapping_v1.json',mapping)
archive=N/'bcsp_research_priority_01dt08_v1.tar.gz'
with archive.open('xb') as out:
 with tarfile.open(fileobj=out,mode='w:gz') as tf:
  for p,t in items:
   ti=tarfile.TarInfo(p.name);ti.size=len(raw(p));ti.mode=0o644;ti.mtime=0
   tf.addfile(ti,io.BytesIO(raw(p)))
with (N/(archive.name+'.sha256')).open('x') as f:f.write(sha(raw(archive))+'  '+archive.name+'\n')
with (N/'bcsp_research_priority_01dt08_v1.contents.sha256').open('x') as f:
 for p,t in items:f.write(sha(raw(p))+'  '+p.name+'\n')
readiness=dump('combined_readiness_report_v1.json',dict(status='NECESSARY_RESOURCES_AND_ASSETS_PASS_DEPLOYMENT_PREPARED_NOT_EXECUTED',
 identity=identity,resources=res,all327_SHA256_match=True,selected30_SHA256_match=True,free_GiB=res['disk']['free']/1024**3,
 new_paths=fresh,local_P3=bind(p3),installation_mapping=bind(mp),archive=bind(archive),server_writes=0,CUDA_calls=0,training_started=False))
outer=load(M/'continuation_train_v2_request_v1/training_execution_request_v3.json')
def rewrite(v):
 if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
 if isinstance(v,list):return [rewrite(x) for x in v]
 if isinstance(v,str):return v.replace('control_train_v2','control_train_v3').replace('seed0_train_v2','seed0_train_v3')
 return v
outer=rewrite(outer)
outer['request_version']=4;outer['actual_training_attempt_index']=3
outer['request_kind']='One fresh scratch training attempt on01dt08 after six-file exclusive installation;PIDdiagnostics nonblocking,all resource/science thresholds unchanged'
outer['entry_request']=bind(qp,CODE+'/control_train_v3/training_execution_request_v1.json')
outer['migration_acceptance']=bind(ap,CODE+'/control_train_v3/migration_uncertainty_acceptance_v1.json')
outer['parent_evidence']={'current_readiness':bind(readiness),'current_binding_P3':bind(p3),'PID_policy_CPU_P3':bind(V/'local_P3_receipt_v4.json')}
outer['scientific_contract']['baseline']='B0 AdaPoinTr Transformer; not Mamba/SCQR'
outer['environment']['CUDA_VISIBLE_DEVICES']=identity['gpu_uuid']
outer['resources_unchanged']['require_no_other_compute_processes']='Startup gate only; running PIDs are diagnostic and not an ownership guarantee'
outer['PID_policy']=dict(mode='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE',raw_PID_mismatch_blocks=False,PID_query_failure_blocks=False,initial_idle_gate_retained=True,strict_namespace_mapping_required=False)
outer['resource_snapshot_evidence']=dict(UTC=res['UTC'],GPU_memory_used_MiB=int(g[4]),compute_processes=0,disk_free_bytes=res['disk']['free'],fixed_training_Python='3.10.20',fresh_output_control_tmux_confirmed=True,not_persistent_admission=True,recheck_before_launch=True)
outer['future_materialization_contract']['authorization_schema']['request_sha256']=sha(raw(qp))
outer['future_materialization_contract']['runtime_schema']['request_sha256']=sha(raw(qp))
argv=outer['future_materialization_contract']['external_training_argv']
argv[8]=q['implementation']['entry']['path']
argv[argv.index('--request-sha256')+1]=sha(raw(qp))
outer['prelaunch_guards'][1]='Recheck the exact deployed six-file map,existing QC/config/order/data and30 selected dependencies; no broad inventory or downloads'
outer['previous_attempt']=dict(failed_run_id='bcsp_geov1_b0_foldC_in8192_out8192_seed0_train_v2',failed_committed_steps=1,
 failed_execution_scope_sha256='ba5100171a8ab4647621fea58747c2abedcdf7b7a8a79a610e13c9a25d656fed',
 failure_audit_sha256='e1f80558c5dd76e4f4882082487a9809516f3d4a981e1162cc1481836fa93348',
 reason='Only raw PID-equality predicate failed; all three memory predicates passed; ownership mapping inconclusive',previous_execution_grant_reusable=False,preserve_old_files=True,new_attempt_is_scratch=True)
outer['known_failure_and_diagnostic_scope']=dict(new_entry=q['implementation']['entry'],only_production_behavior_change='PID mismatch/list/query errors are diagnostics only; no strict ownership guarantee',all_resource_thresholds_unchanged=True,new_device_CUDA_validation=False)
outer['minimal_deployment']=dict(status='PREPARED_NOT_DEPLOYED',installation_mapping=bind(mp),archive=bind(archive),future_upload_path='/home/jovyan/'+archive.name,
 full_scope_execution_authorization_covers='After manual upload,one exclusive six-file installation and installed-hash verification,then exactly one fresh tmux training attempt',
 failure_stops_before_training=True,installed_verification_required_before_controller=True)
outer['local_serialization']['future_rendering_contract'][0]='Only after a new fullSHA execution grant and verified deployment,load exact final scope bytes,bound inner request bytes and current-device acceptance bytes by read_bytes;validate all hashes before rendering.'
outer['current_task_boundary']=dict(server_operations='Four bounded readonly queries;no CUDA or server writes',local_files='Minimal binding modules,evidence,data-only transport and pending requests',runtime_config_created=False,launcher_created=False,training_execution_authorization_created=False,launch_attempt_created=False,training_steps=0)
outer['next']='Manual upload of the small archive;then separate explicit authorization of this fullSHA for frozen non-overwrite deployment and exactly one training attempt. No execution yet.'
op=dump('training_execution_request_v4.json',outer)
assert outer['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and outer['execution_authorized'] is False
assert q['implementation']['runtime']['sha256']=='55ad69b0e87f3fc4ecac68a5ebcc4cdd560c4825ff01363ba9868de5875f0847'
print(json.dumps(dict(status='PREPARED_PENDING_AUTHORIZATION',request=bind(op),archive=bind(archive),files=6,server_writes=0,training_steps=0)))
