"""Local P3/request/package only; require the single version2 CPU batch to pass."""
from pathlib import Path
import json,hashlib,ast,importlib.util,tarfile,shutil
V=Path(__file__).resolve().parent;W=V.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p,target=None):return dict(path=target or str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,d):
 with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 cpu=read(V/'CPU_batch_v2/result.json');entry=V/'bcsp_spcg_sixmodel_native_predict_v1.py';test=V/'test_spcg_native_CPU_v2.py';static=read(V/'fixture_path_static_review_v2.json')
 assert cpu['status']=='SPCG_NATIVE_CPU24_PASS' and cpu['count']==24 and cpu['entry']==rec(entry) and cpu['test']==rec(test) and not (V/'CPU_batch_v2/failure.json').exists()
 for r in static['protected_sources']:assert rec(Path(r['path']))==r
 for p in [entry,test,Path(__file__)]:ast.parse(p.read_text(encoding='utf-8'))
 q=read(V/'draft_request_v1.json');index=read(V/'SPCG_sixmodel_input_index_v1.json');aliases=read(V/'local_metadata_map_v1.json');root=str(Path(q['entry']['path']).parent).replace('\\','/')
 p3=dict(status='LOCAL_SPCG_NATIVE_PREDICTION_P3_PASS',entry_sha256=sha(entry),CPU_checks=24,CPU_result=rec(V/'CPU_batch_v2/result.json'),CPU_scope=rec(V/'CPU_scope_v1.json'),test=rec(test),fixture_static_review=rec(V/'fixture_path_static_review_v2.json'),prior_failure=rec(V/'CPU_failure_freeze_v1.json'),checks=dict(six_frozen_models_exact=True,D_only210_inputs630_paired=True,actual_G0_G1_G2_factory_CPU=True,strict_artificial_checkpoint_loading_CPU=True,actual_G2_k8_CPU=True,native630_artificial_loop_CPU=True,coarse_dense_only_outputs_CPU=True,attempt_counter_and_failure_stop_CPU=True,parameter_BN_RNG_equality_CPU=True,source_guard_U_H_readonly_CPU=True,UTC_first_and_active_guard_exception_capture=True,resource_and_native_numeric_contract_unchanged=True,production_entry_unchanged_in_fixture_fix=True,no_real_checkpoint_or_payload_access=True,no_repeated_GPU_preflight=True,cross_device_G0_D_disclosed=True),limitations=cpu['limitations']+['Entry and frozen scientific sources were unchanged after first-batch failure. Version2 only remaps the artificial mother-source record; passed once.','Full server source/dependency/input/checkpoint hashes and current device/disk/targets must be rechecked before installation/execution.'],server_operations=0,GPU=0,forward_real=0,checkpoint_loads_real=0)
 emit(V/'implementation_P3_v1.json',p3);q['P3']=rec(V/'implementation_P3_v1.json',root+'/implementation_P3_v1.json')
 T=V/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir();qp=P/'SPCG_sixmodel_native_execution_request_v1.json';emit(qp,q);qh=sha(qp)
 sp=importlib.util.spec_from_file_location('SPCG_final_pending_contract',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
 original_bound=e.bound;records={q['P3']['path']:V/'implementation_P3_v1.json',**{k:Path(v) for k,v in aliases.items()}}
 auth=dict(schema='bcsp-development-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='IN_MEMORY_STATIC_ONLY_NOT_EXECUTION_AUTHORIZATION');runtime=dict(schema='bcsp-development-runtime-v1',request_sha256=qh,authorization_sha256='a'*64)
 qr=rec(qp);ar=dict(path='IN_MEMORY_AUTH',bytes=0,sha256='a'*64);rr=dict(path='IN_MEMORY_RUNTIME',bytes=0,sha256='b'*64)
 e.bound=lambda r:auth if r['path']==ar['path'] else runtime if r['path']==rr['path'] else original_bound(r)
 try:assert e.authorize(qr,ar,rr)==q;launcher=e.render_launcher(q,qh,'a'*64,'b'*64)
 finally:e.bound=original_bound
 assert '7200s' in launcher and q['entry']['path'] in launcher and q['identity']['gpu_uuid'] in launcher
 emit(V/'final_request_static_review_v1.json',dict(status='FINAL_SPCG_NATIVE630_REQUEST_CONTRACT_PASS',request_sha256=qh,one_way_auth_runtime_launcher_in_memory_only=True,materialized=False,checkpoint_loads=0))
 for p in [entry,test,V/'CPU_scope_v1.json',V/'CPU_batch_v2/result.json',V/'fixture_path_static_review_v2.json',V/'implementation_P3_v1.json',V/'SPCG_sixmodel_input_index_v1.json',V/'SPCG_native_scope_v1.json',V/'final_request_static_review_v1.json']:
  shutil.copyfile(p,P/('CPU_result_v2.json' if p.name=='result.json' else p.name))
 for run in index['runs']:shutil.copyfile(Path(aliases[run['training_audit']['path']]),P/('frozen_'+run['label']+'_training_audit_v1.json'))
 files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(P.iterdir())]
 emit(T/'installation_mapping_v1.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',remote_root=root,request_sha256=qh,files=files,reused='Frozen LQI/SPCG code/U/H/provider,6 checkpoints/training requests,210 exact dev inputs andmetadata; no environment changes.',before_write='Recheck current hostname/GPU and resource/disk>=6GiB, four uploads, all source and dependency hashes, six checkpoint SHA256, 210 input SHA256, original metadata, absent targets/output/control and unlinked parents. Exclusive writes, failure stop.',not_materialized=[*q['launch_contract'].values(),q['output']]))
 arc=T/'bcsp_spcg_sixmodel_native_pending_20261117_v1.tar.gz'
 with tarfile.open(arc,'x:gz') as t:
  t.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc) as t:
  ms=t.getmembers();assert len(ms)==len(files)+1 and all(x.isfile() for x in ms);listing=''.join(hashlib.sha256(t.extractfile(x).read()).hexdigest()+'  '+x.name+'\n' for x in ms)
 for suffix,text in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(text,encoding='utf-8')
 emit(V/'delivery_receipt_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_SHA_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),P3=rec(V/'implementation_P3_v1.json'),install_files=len(files),CPU_checks=24,server_operations=0,GPU=0,prediction_started=False,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
 print(json.dumps(dict(status='SPCG_CPU24_P3_PASS_REQUEST_PENDING',request_SHA256=qh,archive_bytes=arc.stat().st_size,install_files=len(files))))
if __name__=='__main__':main()
