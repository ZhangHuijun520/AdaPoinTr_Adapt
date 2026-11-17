"""Local final evidence freeze and pending request. No server/GPU/test execution."""
from pathlib import Path,PurePosixPath
import ast,hashlib,importlib.util,json,shutil,tarfile
V=Path(__file__).resolve().parent;S=V.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p,target=None):p=Path(p);return dict(path=target or str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 cpu=read(V/'CPU_batch_v6/result.json');entry=V/'bcsp_spcg_cuda_entry_v3.py';test=V/'test_output_policy_cpu_v6.py';win=read(V/'Windows_CPU_scope_v6.json')
 assert cpu['status']=='SPCG_OUTPUT_POLICY_LIFECYCLE_CPU_PASS' and cpu['count']==12 and cpu['entry']==rec(entry) and cpu['test']==rec(test) and not (V/'CPU_batch_v6/failure.json').exists()
 assert all(sha(x['path'])==x['sha256'] for x in win['production_sources']) and sha(test)==win['test_sha256']
 for record in cpu['actual_policy_sources']:assert rec(record['path'])==record
 for p in [entry,test,Path(__file__)]:ast.parse(p.read_text(encoding='utf-8'))
 oldpath=S/'binding_hotfix_v2/pending_transport_v2/payload/SPCG_CUDA_execution_request_v2.json';q=read(oldpath);old=read(oldpath);project=q['project'];root=project+'/third_party/bcsp_spcg_cuda_20261116_v3';run='SPCG_G0_G1_G2_CUDA_20261116_v3'
 p3=dict(status='SPCG_LOCAL_P3_PASS',revision='EXACT_OUTPUT_AND_TRACEBACK_POLICY_V3',entry=rec(entry),test=rec(test),CPU_result=rec(V/'CPU_batch_v6/result.json'),CPU_completion=rec(V/'CPU_batch_v6/completion_receipt_v6.json'),CPU_checks=12,windows_fixture_scope=rec(V/'Windows_CPU_scope_v6.json'),inherited_P3=rec(S/'binding_hotfix_v2/implementation_P3_v2.json'),actual_inherited_policy_sources=cpu['actual_policy_sources'],failure_audit=rec(S/'binding_hotfix_v2/post_failure_freeze_v2/formal_audit_result_v2.json'),checks=dict(exact_five_output_paths_pass=True,neighbor_NPZ_denied=True,input_write_denied=True,exact_traceback_sources_readonly=True,source_write_denied=True,actual_linecache_traceback_under_audit=True,negative_hash_rejected_before_guard_close=True,Windows_binary_proxy_test_child_only=True,self_source_binding_test_only=True,production_model_guard_bytes_unchanged=True,formula_assets_loss_provider_limits_counts_unchanged=True,new_request_paths_old_request_consumed=True),prior_failed_CPU_batches_preserved=['CPU_batch_v3','CPU_batch_v4','CPU_batch_v5'],limitations=['CPU file-policy regression only; no new native Mamba/full loss/CUDA execution.','Windows test adapter and self-source read binding are fixture-only, absent from production entry.','Resource/source/identity/new-target readiness inherited from last evidence; fresh verification mandatory before installation/launch.','Prior v2 completed6synthetic forwards3loss3backward and attempted1real forward, then failed; not a full admission.'],server_calls=0,GPU=0,training=0)
 emit(V/'implementation_P3_v3.json',p3)
 q.update(run_id=run,output=project+'/logs/cranial_bcsp_fullmamba/'+run,entry=rec(entry,root+'/'+entry.name),P3=rec(V/'implementation_P3_v3.json',root+'/implementation_P3_v3.json'),supersedes_consumed_request_sha256=sha(oldpath))
 L=q['launch_contract'];L.update(tmux_session=run,request_path=root+'/SPCG_CUDA_execution_request_v3.json',authorization_path=root+'/control/authorization_v3.json',runtime_path=root+'/control/runtime_v3.json',launcher_path=root+'/control/launch_once_v3.sh',launch_attempt_path=root+'/control/launch_attempt_v3.json',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
 q['exact_observation_outputs']=[q['output']+'/real_D_%02d.npz'%i for i in range(5)]
 q['traceback_readonly_sources']=[q[k] for k in ['parent_helper','helper','timezone_implementation','entry']]
 q['revision_scope']='Five exact NPZ observation outputs + four already-bound traceback infrastructure sources. No directory-wide payload/source relaxation; no Windows test shim in production.'
 for k in ['science','limits','fixture','implementation','real_inputs','probe_asset','head_initialization','identity','environment','dependencies']:assert q[k]==old[k],k
 assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid']
 emit(V/'retired_request_v2.json',dict(status='CONSUMED_FAILED_STOP_NO_REEXECUTION',request_sha256=sha(oldpath),counts=dict(forward=7,loss=3,backward=3,step=0),formal_failure_audit=rec(S/'binding_hotfix_v2/post_failure_freeze_v2/formal_audit_result_v2.json')))
 T=V/'pending_transport_v3';T.mkdir();P=T/'payload';P.mkdir();qp=P/'SPCG_CUDA_execution_request_v3.json';emit(qp,q);qh=sha(qp)
 sp=importlib.util.spec_from_file_location('static_final_spcg_v3',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
 final=read(qp);assert e.validate_request_gpu(final)==final['identity']['gpu_uuid'];assert [str(p) for p in e.exact_output_paths(final['output'])]==final['exact_observation_outputs']
 ab,rb=e.materialization(final,qh,'IN_MEMORY_STATIC_REVIEW_ONLY_NOT_USER_AUTHORIZATION');script=e.render_launcher(final,qh,hashlib.sha256(ab).hexdigest(),hashlib.sha256(rb).hexdigest())
 assert root in script and final['entry']==rec(entry,root+'/'+entry.name) and final['P3']==rec(V/'implementation_P3_v3.json',root+'/implementation_P3_v3.json')
 emit(V/'final_request_contract_review_v3.json',dict(status='FINAL_REQUEST_STATIC_CONTRACT_PASS_NOT_RUNTIME',request_sha256=qh,selector_identity_equal=True,exact5_outputs=True,source_entry_P3_hashes_equal=True,science=q['science'],authorization_runtime_launcher_rendered_in_memory_only=True,actual_materialization=False))
 send=[entry,test,V/'implementation_P3_v3.json',V/'CPU_batch_v6/result.json',V/'CPU_batch_v6/completion_receipt_v6.json',V/'CPU_scope_v3.json',V/'Windows_CPU_scope_v6.json',V/'retired_request_v2.json',V/'final_request_contract_review_v3.json']
 for p in send:shutil.copyfile(p,P/('CPU_result_v6.json' if p.name=='result.json' else p.name))
 files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(P.iterdir())]
 emit(T/'installation_mapping_v3.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',remote_root=root,request_sha256=qh,files=files,reused_assets='Unchanged v1 model head/factory/runtime and rawU/H, inherited LQI/Mamba/provider/project sources; rehash and reuse only',required_before_install='Current identity and GPU selector exact, uploaded4files hashes, all reused exact hashes incl traceback sources, parent no symlinks, all new targets/control/output absent, resource thresholds; stop on mismatch',not_materialized=[L[k] for k in ['authorization_path','runtime_path','launcher_path','launch_attempt_path']]+[q['output']],overwrite=False,retry=False))
 arc=T/'bcsp_spcg_output_policy_pending_20261116_v3.tar.gz'
 with tarfile.open(arc,'x:gz') as t:
  t.add(T/'installation_mapping_v3.json',arcname='installation_mapping_v3.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc,'r:gz') as t:
  members=t.getmembers();assert len(members)==len(files)+1 and all(x.isfile() for x in members);listing=''.join(hashlib.sha256(t.extractfile(x).read()).hexdigest()+'  '+x.name+'\n' for x in members)
 for suffix,value in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(value,encoding='utf-8')
 emit(V/'delivery_receipt_v3.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_COMPLETE_HASH_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),P3=rec(V/'implementation_P3_v3.json'),install_files=len(files),CPU_checks=12,server_calls=0,CUDA=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,training_request_created=False))
 print(json.dumps(dict(status='P3_PASS_NEW_V3_REQUEST_PENDING',request_SHA256=qh,archive_bytes=arc.stat().st_size,install_files=len(files))))
if __name__=='__main__':main()
