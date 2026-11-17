"""Local only: UTC ordering patch P3 and fresh G0_C request."""
from pathlib import Path,PurePosixPath
import json,hashlib,ast,importlib.util,shutil,tarfile
V=Path(__file__).resolve().parent;S=V.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p,target=None):return dict(path=target or str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=sha(p))
def emit(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 entry=V/'bcsp_spcg_training_entry_v3.py';test=V/'test_UTC_order_CPU_v3.py';cpu=read(V/'CPU_contract_batch_v3/result.json');assert cpu['status']=='SPCG_G0C_UTC_ORDER_CPU_PASS' and cpu['count']==12 and cpu['entry']==rec(entry) and cpu['test']==rec(test) and not (V/'CPU_contract_batch_v3/failure.json').exists()
 for p in [entry,test,Path(__file__)]:ast.parse(p.read_text(encoding='utf-8'))
 oldpath=S/'startup_chain_hotfix_v2/pending_transport_v2/payload/SPCG_G0_C_training_execution_request_v2.json';old=read(oldpath);q=read(oldpath);root=q['project']+'/third_party/bcsp_spcg_G0C_training_20261116_v3';run='SPCG_G0_foldC_seed0_train_20261116_v3';co=root+'/control/'+run
 audit=S/'startup_chain_hotfix_v2/post_failure_freeze_UTC_v2/formal_audit_result_v2.json';a=read(audit);assert a['status']=='FORMAL_READONLY_G0C_V2_UTC_FAILURE_FREEZE_PASS' and all(a['checks'].values())
 p3=dict(status='SPCG_G0C_TRAINING_LOCAL_P3_PASS',revision='UTC_FIRST_DISPATCH_V3',entry_sha256=sha(entry),bridge_sha256=q['implementation']['bridge']['sha256'],CPU_checks=12,CPU_result=rec(V/'CPU_contract_batch_v3/result.json'),CPU_scope=rec(V/'CPU_scope_v3.json'),inherited_P3=rec(S/'startup_chain_hotfix_v2/training_P3_v2.json'),inherited_import_chain_CPU=rec(S/'startup_chain_hotfix_v2/CPU_batch_v3/result.json'),inherited_lifecycle_CPU=rec(S/'CPU_batch_v1/result.json'),failure_audit=rec(audit),checks=dict(only_one_UTC_allow_line_added=True,UTC_exact_read_before_source_guard=True,UTC_write_denied=True,UTC_validation_drift_propagates=True,other_links_rejected=True,source_readonly_unchanged=True,payload_guard_unchanged=True,exception_capture_before_cleanup_unchanged=True,head_import_chain_unchanged=True,model_loss_data_order_budget_unchanged=True,new_run_paths_and_request=True),limitations=cpu['limitations']+['No actual model training or GPU repeated; use previous formalCUDAfreeze.','Initial preparation stopped before contract assertions due to existing directory/missing scope; retained emptyCPU_batch_v3; actual12-item batch in CPU_contract_batch_v3 ran once.','Current server readiness must be reverified before execution.'],server_calls=0,GPU=0,training=0)
 emit(V/'training_P3_v3.json',p3)
 q.update(run_id=run,output=q['project']+'/logs/cranial_bcsp_fullmamba/'+run,P3=rec(V/'training_P3_v3.json',root+'/training_P3_v3.json'),supersedes_consumed_request_sha256=sha(oldpath));q['implementation']['entry']=rec(entry,root+'/'+entry.name);q['launch_contract']=dict(request_path=root+'/SPCG_G0_C_training_execution_request_v3.json',authorization_path=co+'/authorization_v3.json',runtime_path=co+'/runtime_v3.json',launcher_path=co+'/launch_once_v3.sh',launch_attempt_path=co+'/attempt_claim_v3.json',tmux_session=run)
 for k in ['counts','resources','science','identity','environment','QC','order_plan','data_root','model_root','dependencies','expected_initial_state_sha256','CUDA_freeze','static_config']:assert q[k]==old[k]
 assert {k:r for k,r in q['implementation'].items() if k!='entry'}=={k:r for k,r in old['implementation'].items() if k!='entry'}
 q['UTC_dispatch_contract']='intFD -> ExactUTCReader.allow -> exactsourceguard -> inherited training payload/root policy; exactresource binding unchanged'
 T=V/'pending_transport_v3';T.mkdir();P=T/'payload';P.mkdir();qp=P/'SPCG_G0_C_training_execution_request_v3.json';emit(qp,q);qh=sha(qp)
 sp=importlib.util.spec_from_file_location('train_v3_final_static',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e);original=e.exact
 def local(r):
  if r['path']==q['P3']['path']:return V/'training_P3_v3.json'
  if r['path']==q['CUDA_freeze']['path']:return S.parents[1]/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/post_CUDA_freeze_v3/formal_audit_result_v3.json'
  return original(r)
 e.exact=local
 try:
  auth=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_STATIC_ONLY_NOT_AUTHORIZATION');rt=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64);assert e.validate(q,qh,auth,'a'*64,rt) is q;launcher=e.render_launcher(q,qh,'a'*64,'b'*64)
 finally:e.exact=original
 assert q['implementation']['entry']['path'] in launcher and '3600s' in launcher
 emit(V/'final_request_static_review_v3.json',dict(status='FINAL_V3_REQUEST_STATIC_PASS',request_sha256=qh,science_resources_unchanged=True,head_source_binding_unchanged=True,UTC_order_regression_pass=True,oneway_authorization_runtime_launcher_in_memory_only=True,materialized=False))
 emit(V/'retired_request_v2.json',dict(status='CONSUMED_FAILED_BEFORE_FORWARD_NO_REEXECUTION',request_sha256=sha(oldpath),audit=rec(audit),training_updates=0))
 for p in [entry,test,V/'training_P3_v3.json',V/'CPU_scope_v3.json',V/'CPU_contract_batch_v3/result.json',V/'final_request_static_review_v3.json',V/'retired_request_v2.json']:shutil.copyfile(p,P/('CPU_result_v3.json' if p.name=='result.json' else p.name))
 files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(P.iterdir())]
 emit(T/'installation_mapping_v3.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',remote_root=root,request_sha256=qh,files=files,reused='All unchanged exact scientific/source/runtime/head/bridge/provider/data/order/CUDAfreeze records; rehash/reuse only',before_write='identityGPUselector/resources8.5GiB,archive4files,allreusehashes315traininginputs/order,parentlinks,newtargets/control/outputabsent;exclusivewrite;anyfailurestop',not_materialized=list(q['launch_contract'].values())+[q['output']]))
 arc=T/'bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz'
 with tarfile.open(arc,'x:gz') as t:
  t.add(T/'installation_mapping_v3.json',arcname='installation_mapping_v3.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc,'r:gz') as t:
  ms=t.getmembers();assert len(ms)==len(files)+1 and all(m.isfile() for m in ms);listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in ms)
 for suffix,value in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(value,encoding='utf-8')
 emit(V/'delivery_receipt_v3.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_SHA_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),install_files=len(files),P3=rec(V/'training_P3_v3.json'),CPU_checks=12,server_operations=0,GPU=0,training_started=False,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
 print(json.dumps(dict(status='P3_PASS_G0_C_V3_PENDING',request_SHA256=qh,archive_bytes=arc.stat().st_size,install_files=len(files))))
if __name__=='__main__':main()
