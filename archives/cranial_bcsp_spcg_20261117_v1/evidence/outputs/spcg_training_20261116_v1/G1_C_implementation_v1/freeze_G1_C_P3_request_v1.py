"""Local G1_C P3 and pending execution request; no server calls."""
from pathlib import Path,PurePosixPath
import json,hashlib,ast,importlib.util,shutil,tarfile
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p,target=None):return dict(path=target or str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=sha(p))
def emit(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 cpu=read(V/'CPU_batch_v1/result.json');entry=V/'bcsp_spcg_G1_C_training_entry_v1.py';bridge=V/'bcsp_spcg_G1_C_training_bridge_v1.py';test=V/'test_G1_C_CPU_v1.py';q=read(V/'draft_G1_C_request_v1.json');root=str(PurePosixPath(q['implementation']['entry']['path']).parent)
 assert cpu['status']=='SPCG_G1_C_CPU_PASS' and cpu['count']==16 and cpu['entry']==rec(entry) and cpu['bridge']==rec(bridge) and cpu['test']==rec(test) and not (V/'CPU_batch_v1/failure.json').exists()
 baseline=S/'UTC_order_hotfix_v3/post_training_freeze_v3/formal_freeze_result_v3.json';a=read(baseline);assert a['status']=='FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS' and all(a['checks'].values()) and q['G0_C_freeze']==rec(baseline,root+'/G0_C_formal_training_freeze_v3.json')
 for p in [entry,bridge,test,Path(__file__)]:ast.parse(p.read_text(encoding='utf-8'))
 p3=dict(status='SPCG_G1C_TRAINING_LOCAL_P3_PASS',entry_sha256=sha(entry),bridge_sha256=sha(bridge),CPU_checks=16,CPU_result=rec(V/'CPU_batch_v1/result.json'),CPU_scope=rec(V/'CPU_scope_v1.json'),G0_C_freeze=rec(baseline),inherited_training_P3=rec(S/'UTC_order_hotfix_v3/training_P3_v3.json'),checks=dict(actual_G1_factory_head_CPU=True,exact_U_H_bytes_CPU=True,old_head_removed=True,shared_untrained_LQI_parent_bound=True,admitted_G1_full_initial_state_bound=True,real_mother_forward_FC_loss_route_CPU=True,G0_same_fold_order_and_counts_required=True,complete_original_lifecycle_delegated=True,bridge_only_G1_arm_guard_changed=True,UTC_first_and_exception_cleanup_inherited=True,head_explicit_load_before_observe=True,precise_head_init_asset_reads_bound=True,no_optimizer_or_loss_changes=True,no_dev_results_or_tuning=True,new_run_paths_pending_only=True),limitations=cpu['limitations']+['Fresh server identity/resource/new-target readiness not checked this local implementation round.','OnlyG1_C now supported; G2/D remain separately scoped.'],server_operations=0,GPU=0,training_started=False)
 emit(V/'training_P3_v1.json',p3);q['P3']=rec(V/'training_P3_v1.json',root+'/training_P3_v1.json')
 T=V/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir();qp=P/'SPCG_G1_C_training_execution_request_v1.json';emit(qp,q);qh=sha(qp)
 spec=importlib.util.spec_from_file_location('finalG1static',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);original=e.exact;base=W/'outputs/spcg_implementation_20261116_v1'
 localmap={q['P3']['path']:V/'training_P3_v1.json',q['G0_C_freeze']['path']:baseline,q['CUDA_freeze']['path']:base/'output_policy_hotfix_v3/post_CUDA_freeze_v3/formal_audit_result_v3.json',q['probe_asset']['path']:base/'artificial_cpu_batch_v1/probe_U_fp32_v1.bin',q['head_initialization']['path']:base/'artificial_cpu_batch_v1/head_initialization_fp32_v1.bin',q['mother_source']['path']:W/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot/models/AdaPoinTr.py'}
 def local(r):
  if r['path'] in localmap:
   p=localmap[r['path']];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
  return original(r)
 e.exact=local
 try:
  auth=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_CONTRACT_ONLY_NOT_USER_AUTHORIZATION');rt=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64);assert e.validate(q,qh,auth,'a'*64,rt) is q;launcher=e.render_launcher(q,qh,'a'*64,'b'*64)
 finally:e.exact=original
 assert q['implementation']['entry']['path'] in launcher and '3600s' in launcher
 emit(V/'final_request_static_review_v1.json',dict(status='FINAL_G1_C_REQUEST_CONTRACT_PASS_NOT_EXECUTION',request_sha256=qh,paired_G0_freeze_exact=True,identity_and_order_inherited_G0=True,U_H_and_mother_source_exact=True,one_way_authorization_runtime_and_launcher_in_memory_only=True,materialized=False))
 for p in [entry,bridge,test,V/'CPU_scope_v1.json',V/'CPU_batch_v1/result.json',V/'training_P3_v1.json',baseline,V/'final_request_static_review_v1.json']:shutil.copyfile(p,P/('CPU_result_v1.json' if p.name=='result.json' else 'G0_C_formal_training_freeze_v3.json' if p==baseline else p.name))
 files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(P.iterdir())]
 emit(T/'installation_mapping_v1.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',remote_root=root,request_sha256=qh,files=files,reused='FrozenSPCGhead/factory/observe/U/H, originaltrainingruntime/LQI/provider/data/order andCUDAfreeze. No G0trainedcheckpoint loaded.',before_write='CurrentidentityGPUselector/resources8.5GiB/upload4hashes/allreusedsourceandU_Hhashes/315traininginputs/order/newtargets/control/outputabsent/unlinkedparents. Exclusivecreate;failurestop.',not_materialized=list(q['launch_contract'].values())+[q['output']]))
 arc=T/'bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz'
 with tarfile.open(arc,'x:gz') as t:
  t.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc,'r:gz') as t:
  ms=t.getmembers();assert len(ms)==len(files)+1 and all(m.isfile() for m in ms);listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in ms)
 for suffix,value in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(value,encoding='utf-8')
 emit(V/'delivery_receipt_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_SHA_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),P3=rec(V/'training_P3_v1.json'),install_files=len(files),CPU_checks=16,server_operations=0,GPU=0,training_started=False,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
 print(json.dumps(dict(status='G1_C_CPU_P3_PASS_REQUEST_PENDING',request_SHA256=qh,archive_bytes=arc.stat().st_size,install_files=len(files))))
if __name__=='__main__':main()
