"""Freeze corrected final request and small transport; local only."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil,tarfile
V=Path(__file__).resolve().parent;S=V.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p,path=None):return dict(path=path or str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=sha(p))
def emit(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
    result=read(V/'CPU_batch_v2/result.json');entry=V/'bcsp_spcg_cuda_entry_v2.py';test=V/'test_binding_hotfix_cpu_v2.py'
    assert result['status']=='SPCG_BINDING_HOTFIX_CPU_PASS' and result['count']==12 and result['entry_sha256']==sha(entry) and result['test_sha256']==sha(test) and not (V/'CPU_batch_v2/failure.json').exists()
    old=read(S/'pending_transport_v2/payload/SPCG_CUDA_execution_request_v1.json');q=read(V/'candidate_request_before_P3_v2.json');root=str(Path(q['entry']['path']).parent).replace('\\','/')
    for p in [entry,test,Path(__file__)]:ast.parse(p.read_text(encoding='utf-8'))
    assert q['science']==old['science'] and q['limits']==old['limits'] and q['fixture']==old['fixture'] and q['implementation']==old['implementation'] and q['real_inputs']==old['real_inputs'] and q['probe_asset']==old['probe_asset'] and q['head_initialization']==old['head_initialization']
    assert q['environment']==dict(old['environment'],CUDA_VISIBLE_DEVICES=old['identity']['gpu_uuid'])
    p3=dict(status='SPCG_LOCAL_P3_PASS',revision='GPU_BINDING_STARTUP_DIAGNOSTIC_V2',entry=rec(entry),CPU_result=rec(V/'CPU_batch_v2/result.json'),CPU_checks=12,inherited_P3=rec(S/'implementation_P3_v1.json'),inherited_CPU_checks=32,inherited_CPU_rerun=False,checks=dict(final_selector_consistency=True,stale_request_authorize_and_render_rejected=True,environment_checked_before_query=True,PID_before_query=True,bounded_original_exception_details_persisted=True,one_query_no_retry=True,original_head_factory_runtime_unchanged=True,U_H_assets_unchanged=True,full_formula_loss_provider_limits_counts_unchanged=True,new_paths_old_request_consumed=True),failure_audit=rec(S/'post_failure_freeze_v1/audit_completion_v1.json'),limitations=['Artificial stdlib SMI substitute; actual GPU query/CUDA/Mamba/full loss not revalidated.','Identity inherited from last authorized read-only evidence; fresh resource/source/new-target checks required before execution.','No claim that retained original stderr from v1 was recovered.'],server_calls=0,CUDA=0,training=0)
    emit(V/'implementation_P3_v2.json',p3);q['P3']=rec(V/'implementation_P3_v2.json',root+'/implementation_P3_v2.json');q['readiness']['new_install_targets_absence_not_yet_observed']=True
    emit(V/'retired_request_v1.json',dict(request_sha256=q['supersedes_consumed_request_sha256'],status='CONSUMED_FAILED_BEFORE_MODEL_NO_REEXECUTION',preserve=True))
    T=V/'pending_transport_v2';T.mkdir();payload=T/'payload';payload.mkdir()
    qp=payload/'SPCG_CUDA_execution_request_v2.json';emit(qp,q)
    sp=importlib.util.spec_from_file_location('final_spcg_v2_static',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
    final=read(qp);assert e.validate_request_gpu(final)==final['identity']['gpu_uuid'];ab,rb=e.materialization(final,sha(qp),'IN_MEMORY_FINAL_CONTRACT_REVIEW_NOT_USER_AUTHORIZATION');e.render_launcher(final,sha(qp),hashlib.sha256(ab).hexdigest(),hashlib.sha256(rb).hexdigest())
    assert final['P3']==rec(V/'implementation_P3_v2.json',root+'/implementation_P3_v2.json') and final['entry']==rec(entry,root+'/'+entry.name)
    for p in [entry,test,V/'implementation_P3_v2.json',V/'CPU_batch_v2/result.json',V/'CPU_scope_v2.json',V/'retired_request_v1.json']:shutil.copyfile(p,payload/('CPU_result_v2.json' if p.name=='result.json' else p.name))
    files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(payload.iterdir())]
    emit(T/'installation_mapping_v2.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',remote_root=root,request_sha256=sha(qp),files=files,reused_assets='All unchanged14-file v1 scientific implementation/assets and inherited dependencies as request records; do not reinstall or overwrite.',before_write='reverify identity, physicalGPU and selector equality, upload hashes, reused hashes, unlinked parents, all new targets/control/output absent; exclusive creation only',not_materialized=[final['launch_contract'][k] for k in ['authorization_path','runtime_path','launcher_path','launch_attempt_path']]+[final['output']]))
    arc=T/'bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz'
    with tarfile.open(arc,'x:gz') as t:
        t.add(T/'installation_mapping_v2.json',arcname='installation_mapping_v2.json',recursive=False)
        for p in sorted(payload.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
    with tarfile.open(arc,'r:gz') as t:
        members=t.getmembers();assert len(members)==len(files)+1 and all(m.isfile() for m in members);listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
    for suffix,value in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(value,encoding='utf-8')
    emit(V/'delivery_receipt_v2.json',dict(status='AWAITING_UPLOAD_VERIFICATION_AND_SEPARATE_EXACT_HASH_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),new_install_files=len(files),P3=rec(V/'implementation_P3_v2.json'),CPU=12,source_changes='isolated entry v2 only; original head/factory/runtime and initialization unchanged',server_operations=0,SMI_queries=0,CUDA=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False))
    print(json.dumps(dict(status='P3_PASS_NEW_REQUEST_PENDING',request_sha256=sha(qp),archive_bytes=arc.stat().st_size,new_install_files=len(files))))
if __name__=='__main__':main()
