"""Local P3 and new pendingG0_C request; no server, test or execution calls."""
from pathlib import Path,PurePosixPath
import ast,hashlib,importlib.util,json,shutil,tarfile
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p,target=None):p=Path(p);return dict(path=target or str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 entry=V/'bcsp_spcg_training_entry_v2.py';test=V/'test_startup_chain_CPU_v3.py';cpu=read(V/'CPU_batch_v3/result.json');scope=read(V/'CPU_environment_scope_v3.json')
 assert cpu['status']=='SPCG_G0C_STARTUP_CHAIN_ENV_CPU_PASS' and cpu['count']==12 and cpu['entry']==rec(entry) and cpu['test']==rec(test) and not (V/'CPU_batch_v3/failure.json').exists()
 assert sha(entry)==scope['production_entry_sha256'] and sha(test)==scope['test_sha256']
 for name,r in cpu['dependencies'].items():assert rec(r['path'])==r,name
 inherited=read(S/'CPU_batch_v1/result.json');assert inherited['bridge']==rec(S/'bcsp_spcg_training_bridge_v1.py') and inherited['status']=='SPCG_G0C_TRAINING_CPU_PASS'
 audit=S/'post_failure_freeze_v1/formal_audit_result_v1.json';assert read(audit)['status']=='FORMAL_READONLY_TRAINING_FAILURE_FREEZE_PASS'
 oldpath=S/'pending_transport_v1/payload/SPCG_G0_C_training_execution_request_v1.json';old=read(oldpath);q=read(oldpath);project=q['project'];root=project+'/third_party/bcsp_spcg_G0C_training_20261116_v2';run='SPCG_G0_foldC_seed0_train_20261116_v2';controls=root+'/control/'+run
 head=read(W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/pending_transport_v3/payload/SPCG_CUDA_execution_request_v3.json')['implementation']['head'];localhead=W/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_head_v1.py';assert head['sha256']==sha(localhead) and head['bytes']==localhead.stat().st_size
 for p in [entry,test,Path(__file__)]:ast.parse(p.read_text(encoding='utf-8'))
 p3=dict(status='SPCG_G0C_TRAINING_LOCAL_P3_PASS',revision='HEAD_IMPORT_AND_GUARD_ACTIVE_FAILURE_EXIT_V2',entry_sha256=sha(entry),bridge_sha256=sha(S/'bcsp_spcg_training_bridge_v1.py'),CPU_result=rec(V/'CPU_batch_v3/result.json'),CPU_scope=rec(V/'CPU_environment_scope_v3.json'),CPU_checks=12,inherited_training_P3=rec(S/'training_P3_v1.json'),inherited_lifecycle_CPU=rec(S/'CPU_batch_v1/result.json'),inherited_CPU_checks=16,failed_training_audit=rec(audit),source_dependencies=cpu['dependencies'],checks=dict(final_entry_matches_CPU=True,head_precise_path_size_SHA_bound=True,explicit_bridge_head_observe_runtime_order=True,real_head_observe_runtime_modules_CPU_imported=True,original_bridge_and_runtime_unchanged=True,original_formula_loss_data_counts_resources_unchanged=True,full_original_authorization_metadata_contract_inherited=True,exception_formatted_with_live_guard=True,original_exception_persisted_before_cleanup=True,explicit_exit_one_no_late_KeyError_CPU=True,environment_readonly_root_matches_CPU_prefix=True,source_and_environment_writes_denied=True,Windows_adapter_fixture_only=True,new_run_paths_old_request_retired=True),limits=q['resources'],counts=q['counts'],limitations=['12newCPU checks plus inherited16; real3900stepMamba training not performed.','CPU child imports actual frozen training module and runs artificial observation tensor backward only; noDataset/model/optimizer.','Prior head import failure is retired evidence, not a model effect.','Server state not freshly queried in this local freeze; all hashes/current device/resources/newtargets must be rechecked before execution.','CUDA admission reused; no new GPUpreflight.'],server_calls=0,GPU=0,training_started=False)
 emit(V/'training_P3_v2.json',p3)
 q.update(run_id=run,output=project+'/logs/cranial_bcsp_fullmamba/'+run,P3=rec(V/'training_P3_v2.json',root+'/training_P3_v2.json'),supersedes_consumed_request_sha256=sha(oldpath),startup_failure_policy='Persist full formatted exception while exact-source guard is live; SystemExit1; finally closes guard and UTC; no retry')
 q['implementation']['entry']=rec(entry,root+'/'+entry.name);q['implementation']['head']=head
 q['launch_contract']=dict(request_path=root+'/SPCG_G0_C_training_execution_request_v2.json',authorization_path=controls+'/authorization_v2.json',runtime_path=controls+'/runtime_v2.json',launcher_path=controls+'/launch_once_v2.sh',launch_attempt_path=controls+'/attempt_claim_v2.json',tmux_session=run)
 for k in ['counts','resources','science','identity','environment','QC','order_plan','data_root','model_root','dependencies','expected_initial_state_sha256','CUDA_freeze','static_config']:assert q[k]==old[k],k
 assert {k:r for k,r in q['implementation'].items() if k not in ['head','entry']}=={k:r for k,r in old['implementation'].items() if k!='entry'}
 assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False and q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid']
 T=V/'pending_transport_v2';T.mkdir();P=T/'payload';P.mkdir();qp=P/'SPCG_G0_C_training_execution_request_v2.json';emit(qp,q);qh=sha(qp)
 sp=importlib.util.spec_from_file_location('final_training_v2_contract',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e);original=e.exact
 def local(record):
  if record['path']==q['P3']['path']:return V/'training_P3_v2.json'
  if record['path']==q['CUDA_freeze']['path']:return W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/post_CUDA_freeze_v3/formal_audit_result_v3.json'
  return original(record)
 e.exact=local
 try:
  auth=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_STATIC_ONLY_NOT_AUTHORIZATION');rt=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64);assert e.validate(q,qh,auth,'a'*64,rt) is q;launcher=e.render_launcher(q,qh,'a'*64,'b'*64)
 finally:e.exact=original
 assert q['implementation']['entry']['path'] in launcher and root in launcher and '3600s' in launcher
 emit(V/'final_request_static_review_v2.json',dict(status='FINAL_V2_REQUEST_CONTRACT_PASS_NOT_EXECUTION',request_sha256=qh,head=head,entry_SHA=sha(entry),original_science_unchanged=True,full_authorization_runtime_and_POSIX_launcher_in_memory_only=True,materialized=False))
 emit(V/'retired_request_v1.json',dict(status='CONSUMED_FAILED_BEFORE_MODEL_NO_REEXECUTION',request_sha256=sha(oldpath),failure_audit=rec(audit),training_updates=0))
 send=[entry,test,V/'training_P3_v2.json',V/'CPU_scope_v2.json',V/'CPU_environment_scope_v3.json',V/'CPU_batch_v3/result.json',V/'CPU_batch_v3/completion_receipt_v3.json',V/'final_request_static_review_v2.json',V/'retired_request_v1.json']
 for p in send:shutil.copyfile(p,P/('CPU_result_v3.json' if p.name=='result.json' else p.name))
 files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(P.iterdir())]
 emit(T/'installation_mapping_v2.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=root,files=files,reused='Original unchanged training bridge/runtime/observe+exact head, parentmodel/provider/data/order and CUDAfreeze; no reinstall or upgrade',before_write='Verify currentidentityGPU/selector/resources8.5GiB,upload4files,allreuse hashes315input/order,parent no links,newtargets/control/output all absent; exclusive write; any failure stop',not_materialized=list(q['launch_contract'].values())+[q['output']]))
 arc=T/'bcsp_spcg_G0_C_startup_hotfix_pending_20261116_v2.tar.gz'
 with tarfile.open(arc,'x:gz') as t:
  t.add(T/'installation_mapping_v2.json',arcname='installation_mapping_v2.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc,'r:gz') as t:
  members=t.getmembers();assert len(members)==len(files)+1 and all(m.isfile() for m in members);listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
 for suffix,value in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(value,encoding='utf-8')
 emit(V/'delivery_receipt_v2.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_SHA_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),P3=rec(V/'training_P3_v2.json'),install_files=len(files),CPU_checks=12,inherited_CPU_checks=16,server_operations=0,GPU=0,training_started=False,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
 print(json.dumps(dict(status='NEW_P3_PASS_G0_C_V2_PENDING',request_SHA256=qh,archive_bytes=arc.stat().st_size,install_files=len(files))))
if __name__=='__main__':main()
