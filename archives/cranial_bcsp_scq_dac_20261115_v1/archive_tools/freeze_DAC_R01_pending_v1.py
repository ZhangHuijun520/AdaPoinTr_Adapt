"""Read retained local CPU evidence; freeze P3 and pending request, never run server/model."""
from pathlib import Path
import hashlib,json,importlib.util
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_dac_r01_preparation_20261115_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def rec(p,remote=None):
 p=Path(p);return dict(path=str(p.absolute()) if remote is None else remote,bytes=p.stat().st_size,sha256=sha(p))
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
bindings=json.loads((O/'preparation_bindings_v1.json').read_bytes());remote=bindings['remote']
oldpath=Path(bindings['prior_request']['path']);assert sha(oldpath)==bindings['prior_request']['sha256'];old=json.loads(oldpath.read_bytes())
static=json.loads((O/'static_review_v1.json').read_bytes());cpu=O/'cpu_contract_batch_v1/result_v1.json';result=json.loads(cpu.read_bytes())
assert result['status']=='ARTIFICIAL_CPU_CONTRACT_PASS' and result['count']==36 and len(result['checks'])==36
for record in static['sources']+result['sources']:
 p=Path(record['path']);assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256']
assert not (O/'cpu_contract_batch_v1/failure_v1.json').exists()
outputs=[rec(p) for p in sorted((O/'cpu_contract_batch_v1').rglob('*')) if p.is_file()]
save(O/'CPU_artifact_hash_manifest_v1.json',dict(status='READONLY_LOCAL_POST_TEST_HASH_REVIEW',files=outputs,tests_rerun=False,CUDA=False))
p3=O/'local_P3_v1.json'
checks=dict(plan_v2_confirmed=True,selection20_balanced_and_seven_fixed=True,two_original_checkpoint_bytes_reverified=True,twenty_replay_archive_members_verified=True,syntax_and_original_link_checks=True,actual_mother_FC_and_RF_residual_used_in_CPU=True,old_geometry_recomputed_at_Q1=True,exact_authorize_function_tested=True,oneway_runtime_tested=True,native_suffix_budget_separate=True,hooks_removed_after_failure=True,GT_member_not_read=True,zero_loss_backward_optimizer_in_production=True,no_architecture_or_provider_change=True,source_hashes_unchanged_after_CPU=True,local_test_artifacts_hashed=True)
save(p3,dict(status='LOCAL_DAC_R1_P3_PASS',checks=checks,check_count=len(checks),CPU=rec(cpu),static_review=rec(O/'static_review_v1.json'),artifacts=rec(O/'CPU_artifact_hash_manifest_v1.json'),entry=rec(O/'bcsp_scq_dac_r1_entry_v1.py'),core=rec(O/'bcsp_scq_dac_r1_core_v1.py'),native_library=old['entry'],counts=result['counts'],limitations=['Artificial encoder/decoder; not proof of native Mamba CUDA equivalence','Actual checkpoint deserialize and Native numerical replay NOT performed','No current remote resource/source verification in this preparation','No GT geometry scores or candidate decision computed']))
out='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1'
controls=remote+'/control'
limits=dict(old['limits']);limits.update(wall_seconds=600,output_bytes=268435456)
q=dict(schema='bcsp-scq-dac-r1-frozen-weight-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,stage='R0_R1_CAPTURE_ONLY_NO_GT_SCORING',calls=result['counts'],batch_size=1,loss=0,backward=0,optimizer_steps=0,BNCal=0,TTA=0,warmup=0,identity=old['identity'],expected_identity={k:old['identity'][k] for k in ('hostname','gpu_uuid','driver_version')},identity_provenance=dict(hostname='User confirmed qx2k0r-0 in this turn',resource_values='Inherited frozen evidence; must be checked freshly before deployment/launch'),readiness=dict(fresh_remote_recheck_required=True,verified_this_preparation=False),entry=rec(O/'bcsp_scq_dac_r1_entry_v1.py',remote+'/bcsp_scq_dac_r1_entry_v1.py'),core=rec(O/'bcsp_scq_dac_r1_core_v1.py',remote+'/bcsp_scq_dac_r1_core_v1.py'),native_library=old['entry'],selection=bindings['selection'],legacy_index=old['input_index'],protocol=bindings['protocol'],P3=rec(p3,remote+'/local_P3_v1.json'),models=bindings['models'],formula=json.loads((O/'R01_protocol_v1.json').read_bytes())['formula'],limits=limits,output=out,launch_attempt=controls+'/attempt_claim_v1.json',environment=old['environment'],launch_contract=dict(tmux_session='bcsp_scq_dac_r1_frozen20_20261115_v1',request_path=remote+'/SCQ_DAC_R1_execution_request_v1.json',authorization=controls+'/authorization_v1.json',runtime=controls+'/runtime_v1.json',launcher=controls+'/launch_once_v1.sh',log=out+'/launch.log',pid=out+'/worker.pid',exit_code=out+'/exit_code.txt',single_attempt=True,timeout_seconds=600,parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,raw_bytes_Base64_only=True),forbidden=['training/resume/retry','GT or E/J access in GPU process','parameter/BN update','environment download/install/upgrade','decoder/encoder scientific source edits','GT registration or Native score substitution','automatic follow-up scoring or training'],post_run='Formal readonly post-diagnostic freeze audit, local download/verification, then separately scoped offline geometry interpretation; capture itself makes no GO decision')
for k in ('model_root','helper','preflight_scope','static_config','dependencies','implementation','initialization','rf_initialization'):q[k]=old[k]
mapping=json.loads((O/'candidate_restore_and_install_mapping_v1.json').read_bytes())['files']
for filename in ('bcsp_scq_dac_r1_entry_v1.py','bcsp_scq_dac_r1_core_v1.py','selected20_cases_v1.json','R01_protocol_v1.json','local_P3_v1.json'):
 p=O/filename;mapping.append(dict(local=str(p.absolute()),remote=remote+'/'+filename,bytes=p.stat().st_size,sha256=sha(p),action='NEW_NO_OVERWRITE'))
assert len(mapping)==27 and len({r['remote'] for r in mapping})==27
q['deployment_assets']=[{k:r[k] for k in ('remote','bytes','sha256','action')} for r in mapping]
q['deployment_contract']=dict(no_overwrite=True,new_parent_directory=remote,all_targets_absent_before_first_write=True,write_parent_checked_no_links=True,old_deleted_checkpoint_paths_not_reused=True,asset_count_excluding_request=27,request_file_additional=True,weights=2,replay_files=20,new_code=2,selection_protocol_P3=3,source_environment_readiness_required=True,failed_install_requires_readonly_state_check_no_automatic_retry=True)
pending=O/'pending_request_v1';pending.mkdir();request=pending/'SCQ_DAC_R1_execution_request_v1.json';save(request,q)
save(pending/'candidate_no_overwrite_install_mapping_v1.json',dict(status='FROZEN_NOT_UPLOADED_NOT_INSTALLED',files=mapping+[dict(local=str(request.absolute()),remote=q['launch_contract']['request_path'],bytes=request.stat().st_size,sha256=sha(request),action='NEW_NO_OVERWRITE')],count=28,server_operations=0))
with (pending/'SCQ_DAC_R1_execution_request_v1.json.sha256').open('x') as f:f.write(sha(request)+'  '+request.name+'\n')
sp=importlib.util.spec_from_file_location('dac_render_only',O/'bcsp_scq_dac_r1_entry_v1.py');entry=importlib.util.module_from_spec(sp);sp.loader.exec_module(entry)
rendered=entry.render_launcher(q,'1'*64,'2'*64,'3'*64)
assert all(len(line)<=2048 for line in rendered.splitlines()) and rendered.index('mkdir -- ')<rendered.index(' >')
# Do not save a runnable launcher or create authorization/runtime/claim files.
save(pending/'pending_freeze_receipt_v1.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=rec(request),P3=rec(p3),mapped_assets=28,asset_bytes=sum(r['bytes'] for r in mapping)+request.stat().st_size,render_review=dict(PurePosixPath=True,max_line_bytes=max(len(line.encode()) for line in rendered.splitlines()),parent_before_redirect=True,placeholder_launcher_not_materialized=True),authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,model_executed=False,server_operations=0))
print(json.dumps(dict(status='LOCAL_P3_AND_PENDING_REQUEST_FROZEN',CPU_checks=result['count'],P3_checks=len(checks),request_sha256=sha(request),mapped_files=28,weight_bytes=sum(r['checkpoint']['bytes'] for r in q['models']),server_operations=0)))
