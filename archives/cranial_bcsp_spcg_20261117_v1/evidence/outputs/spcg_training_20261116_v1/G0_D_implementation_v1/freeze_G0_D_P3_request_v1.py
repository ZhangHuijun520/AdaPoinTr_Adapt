"""Freeze G0_D local P3, exact-hash pending request and minimal upload package."""
from pathlib import Path,PurePosixPath
import json,hashlib,ast,importlib.util,tarfile,shutil
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p,target=None):return dict(path=target or str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,d):
 with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 cpu=read(V/'CPU_batch_v1/result.json');q=read(V/'draft_G0_D_request_v1.json');entry=V/'bcsp_spcg_G0_D_training_entry_v1.py';bridge=V/'bcsp_spcg_G0_D_training_bridge_v1.py';test=V/'test_G0_D_CPU_v1.py'
 assert cpu['status']=='SPCG_G0_D_CPU_PASS' and cpu['count']==20 and cpu['entry']==rec(entry) and cpu['bridge']==rec(bridge) and cpu['test']==rec(test) and not (V/'CPU_batch_v1/failure.json').exists()
 aliases=read(V/'local_metadata_map_v1.json');root=str(PurePosixPath(q['implementation']['entry']['path']).parent)
 for p in [entry,bridge,test,Path(__file__)]:ast.parse(p.read_text(encoding='utf-8'))
 for x in read(V/'unchanged_inputs_v1.json'):assert rec(Path(x['path']))==x
 p3=dict(status='SPCG_G0D_TRAINING_LOCAL_P3_PASS',entry_sha256=sha(entry),bridge_sha256=sha(bridge),CPU_checks=20,CPU_result=rec(V/'CPU_batch_v1/result.json'),CPU_scope=rec(V/'CPU_scope_v1.json'),inherited_G0_training_P3=rec(S/'UTC_order_hotfix_v3/training_P3_v3.json'),C_matrix_freezes={k:rec(Path(aliases[r['path']])) for k,r in q['C_matrix_freezes'].items()},checks=dict(D_QC315_sources63_order100=True,actual_authorize_complete_metadata_CPU=True,C_fold_and_wrong_data_order_rejected=True,completed_C_matrix_hashes_required=True,original_coarse_head_and_FC_loss_route_CPU=True,same_CUDA_admitted_G0_initialization_bound=True,bridge_only_fold_guard_changed=True,actual_bridge3900_artificial_observations=True,five_Q_gradient_steps_preserved=True,actual_optimizer_group_function_CPU=True,UTC_first_and_exception_cleanup_unchanged=True,source_and_payload_guard_unchanged=True,no_model_data_loss_budget_changes=True,new_run_paths_and_one_way_auth=True,no_dev_tuning=True),limitations=cpu['limitations']+['Current server identity, GPU, D315 payload hashes, reused D metadata and disk/new target readiness must be rechecked before execution.'],server_operations=0,GPU=0,training_started=False)
 emit(V/'training_P3_v1.json',p3);q['P3']=rec(V/'training_P3_v1.json',root+'/training_P3_v1.json')
 T=V/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir();qp=P/'SPCG_G0_D_training_execution_request_v1.json';emit(qp,q);qh=sha(qp)
 sp=importlib.util.spec_from_file_location('G0D_final_contract',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e);original=e.exact
 def mapped(r):
  p=V/'training_P3_v1.json' if r['path']==q['P3']['path'] else Path(aliases[r['path']]);assert rec(p)['bytes']==r['bytes'] and sha(p)==r['sha256'];return p
 e.exact=mapped
 try:
  a=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_STATIC_CONTRACT_ONLY_NOT_USER_AUTHORIZATION');rt=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64);assert e.validate(q,qh,a,'a'*64,rt) is q;launcher=e.render_launcher(q,qh,'a'*64,'b'*64)
 finally:e.exact=original
 assert q['implementation']['entry']['path'] in launcher and '3600s' in launcher and q['fold']=='D' and q['arm']=='G0'
 emit(V/'final_request_static_review_v1.json',dict(status='FINAL_G0_D_PENDING_REQUEST_CONTRACT_PASS',request_sha256=qh,complete_C_matrix_exact=True,D_metadata_and_order_exact=True,one_way_authorization_runtime_launcher_in_memory_only=True,materialized=False))
 for p in [entry,bridge,test,V/'CPU_scope_v1.json',V/'CPU_batch_v1/result.json',V/'training_P3_v1.json',V/'final_request_static_review_v1.json']:shutil.copyfile(p,P/('CPU_result_v1.json' if p.name=='result.json' else p.name))
 for arm,r in q['C_matrix_freezes'].items():shutil.copyfile(Path(aliases[r['path']]),P/(arm+'_C_formal_training_freeze_v1.json'))
 files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(P.iterdir())]
 emit(T/'installation_mapping_v1.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',remote_root=root,request_sha256=qh,files=files,reused='Original G0 LQI/source/runtime/provider; frozen D QC/order metadata and D315 point inputs. No trained checkpoint loaded. No SPCG head installed.',before_write='Recheck current identity/GPU/disk>=8.5GiB/four uploads/all reused hashes/D315 input hashes/D order and C proofs/new target absence and unlinked parents; exclusive writes; failure stop.',not_materialized=list(q['launch_contract'].values())+[q['output']]))
 arc=T/'bcsp_spcg_G0_D_training_pending_20261116_v1.tar.gz'
 with tarfile.open(arc,'x:gz') as t:
  t.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc,'r:gz') as t:
  members=t.getmembers();assert len(members)==len(files)+1 and all(m.isfile() for m in members);listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
 for suffix,value in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(value,encoding='utf-8')
 emit(V/'delivery_receipt_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_SHA_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),P3=rec(V/'training_P3_v1.json'),install_files=len(files),CPU_checks=20,server_operations=0,GPU=0,training_started=False,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
 print(json.dumps(dict(status='G0_D_CPU_P3_PASS_REQUEST_PENDING',request_SHA256=qh,archive_bytes=arc.stat().st_size,install_files=len(files))))
if __name__=='__main__':main()
