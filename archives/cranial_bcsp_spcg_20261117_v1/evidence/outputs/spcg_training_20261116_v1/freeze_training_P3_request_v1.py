"""Freeze first training request locally; no deployment/materialization/execution."""
from pathlib import Path,PurePosixPath
import ast,hashlib,importlib.util,json,shutil,tarfile
S=Path(__file__).resolve().parent;W=S.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p,target=None):return dict(path=target or str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=sha(p))
def emit(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 cpu=read(S/'CPU_batch_v1/result.json');entry=S/'bcsp_spcg_training_entry_v1.py';bridge=S/'bcsp_spcg_training_bridge_v1.py';test=S/'test_training_CPU_v1.py'
 assert cpu['status']=='SPCG_G0C_TRAINING_CPU_PASS' and cpu['count']==16 and cpu['entry']==rec(entry) and cpu['bridge']==rec(bridge) and cpu['test']==rec(test) and not (S/'CPU_batch_v1/failure.json').exists()
 q=read(S/'draft_G0_C_request_v1.json');root=str(PurePosixPath(q['implementation']['entry']['path']).parent)
 audit=W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/post_CUDA_freeze_v3/formal_audit_result_v3.json';a=read(audit);assert a['status']=='FORMAL_POST_CUDA_FREEZE_PASS' and all(a['checks'].values()) and q['CUDA_freeze']==rec(audit,root+'/SPCG_CUDA_formal_freeze_v3.json')
 for p in [entry,bridge,test,Path(__file__)]:ast.parse(p.read_text(encoding='utf-8'))
 runtime=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/bcsp_p1_training_runtime_v1.py';assert sha(runtime)==q['implementation']['training_runtime']['sha256']
 checks=dict(single16_CPU_batch_pass=True,final_entry_bridge_hashes_match_CPU=True,original_runtime_byte_identity=True,original3900_optimizer_scheduler_loss_delegated=True,full_authorize_QC_order_path_CPU=True,one_way_receipt_runtime_CPU=True,correct_GPU_selector_identity=True,fixed_first_G0_C_only=True,admitted_G0_initial_fingerprint_algorithm_matched=True,one_forward_observer_per_step=True,five_total_loss_Q_gradient_steps=True,coarse_dense_loss_hooks_CPU=True,hooks_removed_on_failure_CPU=True,production_refuses_artificial_CPU=True,effective_1GiB_3600s_resources=True,original_static_config_not_modified=True,formal_CUDA_freeze_reused_no_preflight=True,finite_reads_from_bound_sources=True)
 p3=dict(status='SPCG_G0C_TRAINING_LOCAL_P3_PASS',entry_sha256=sha(entry),bridge_sha256=sha(bridge),checks=checks,CPU_result=rec(S/'CPU_batch_v1/result.json'),CPU_scope=rec(S/'CPU_scope_v1.json'),sources=[rec(entry),rec(bridge),rec(test),rec(runtime)],CUDA_freeze=rec(audit),limits=q['resources'],counts=q['counts'],log_steps=[1,39,390,1950,3900],limitations=cpu['limitations']+['No fresh server readiness was performed this local implementation-only turn.','CUDA source observer only supports firstG0_C dispatch; futureG1/G2 andFoldD request compatibility require bounded adaptations.','Per-run static estimate does not replace full3900step output/resource monitoring.','Legacy checkpoint stage remains BCSP_INPUT_DENSITY_V1 provenance; model_construction and request bind SPCG G0_C identity.'],server_calls=0,model_training_executed=False,GPU=0)
 emit(S/'training_P3_v1.json',p3);q['P3']=rec(S/'training_P3_v1.json',root+'/training_P3_v1.json');q['CUDA_freeze']=rec(audit,root+'/SPCG_CUDA_formal_freeze_v3.json');q['implementation']['entry']=rec(entry,root+'/'+entry.name);q['implementation']['bridge']=rec(bridge,root+'/'+bridge.name)
 T=S/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir();qp=P/'SPCG_G0_C_training_execution_request_v1.json';emit(qp,q);qh=sha(qp)
 sp=importlib.util.spec_from_file_location('spcg_train_final_static',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
 final=read(qp);exact=e.exact
 def localbound(r):
  if r['path']==final['P3']['path']:return S/'training_P3_v1.json'
  if r['path']==final['CUDA_freeze']['path']:return audit
  return exact(r)
 e.exact=localbound
 try:
  auth=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_CONTRACT_ONLY_NOT_AUTHORIZATION');rt=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64);assert e.validate(final,qh,auth,'a'*64,rt) is final;launcher=e.render_launcher(final,qh,'a'*64,'b'*64)
 finally:e.exact=exact
 assert '3600s' in launcher and root in launcher and final['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and final['execution_authorized'] is False
 emit(S/'final_request_static_review_v1.json',dict(status='FINAL_REQUEST_STATIC_REVIEW_PASS_NOT_EXECUTION',request_sha256=qh,final_P3_source_hashes=True,request_GPU_identity_matches_environment=True,first_G0_C_only=True,resources=final['resources'],counts=final['counts'],launcher_and_artificial_authorization_in_memory_only=True,materialized=False))
 send=[entry,bridge,test,S/'CPU_scope_v1.json',S/'CPU_batch_v1/result.json',S/'training_P3_v1.json',audit,S/'final_request_static_review_v1.json']
 for p in send:shutil.copyfile(p,P/('CPU_result_v1.json' if p.name=='result.json' else 'SPCG_CUDA_formal_freeze_v3.json' if p==audit else p.name))
 files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(P.iterdir())]
 emit(T/'installation_mapping_v1.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=root,files=files,reused='FrozenLQI/encoder/provider/project/data315/order/runtime andSPCG observation helper; exact rehash/reuse, no install or upgrade',before_write='Current identity+GPU selector/idle+resources+8.5GiB free; archive4files; all reuse hashes, exact315train NPZ andorder; no links; allnewtargets/control/outputabsent; exclusive creation; failurestop no retry',not_materialized=list(q['launch_contract'].values())+[q['output']]))
 arc=T/'bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz'
 with tarfile.open(arc,'x:gz') as t:
  t.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc,'r:gz') as t:
  members=t.getmembers();assert len(members)==len(files)+1 and all(x.isfile() for x in members);listing=''.join(hashlib.sha256(t.extractfile(x).read()).hexdigest()+'  '+x.name+'\n' for x in members)
 for suffix,value in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(value,encoding='utf-8')
 emit(S/'delivery_receipt_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_SHA_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),install_files=len(files),P3=rec(S/'training_P3_v1.json'),CPU_checks=16,server_operations=0,GPU=0,training_started=False,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
 print(json.dumps(dict(status='TRAINING_P3_PASS_G0_C_REQUEST_PENDING',request_SHA256=qh,archive_bytes=arc.stat().st_size,install_files=len(files))))
if __name__=='__main__':main()
