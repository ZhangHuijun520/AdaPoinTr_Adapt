"""Complete local pending freeze using POSIX lexical paths, not Windows absolute resolution."""
from pathlib import Path,PurePosixPath
import hashlib,json,importlib.util,shutil,tarfile
V=Path(__file__).resolve().parent;T=V/'pending_transport_v3';P=T/'payload';qp=P/'SPCG_CUDA_execution_request_v3.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p):return dict(path=str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=sha(p))
def emit(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
q=json.loads(qp.read_text(encoding='utf-8'));entry=V/'bcsp_spcg_cuda_entry_v3.py';root=str(PurePosixPath(q['entry']['path']).parent);qh=sha(qp)
s=importlib.util.spec_from_file_location('spcg_final_posix_v3',entry);e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
assert q['exact_observation_outputs']==[str(PurePosixPath(q['output'])/('real_D_%02d.npz'%i)) for i in range(5)]
assert [p.name for p in e.exact_output_paths(V/'CPU_batch_v6/owned')]==['real_D_%02d.npz'%i for i in range(5)]
assert e.validate_request_gpu(q)==q['identity']['gpu_uuid'] and q['entry']['sha256']==sha(entry) and q['P3']['sha256']==sha(V/'implementation_P3_v3.json')
ab,rb=e.materialization(q,qh,'IN_MEMORY_STATIC_REVIEW_ONLY_NOT_AUTHORIZATION');script=e.render_launcher(q,qh,hashlib.sha256(ab).hexdigest(),hashlib.sha256(rb).hexdigest());assert root in script
emit(V/'final_request_contract_review_v3.json',dict(status='FINAL_REQUEST_STATIC_CONTRACT_PASS_NOT_RUNTIME',request_sha256=qh,POSIX_lexical_paths=True,Windows_fixture_path_names_agree=True,selector_identity_equal=True,exact5_outputs=True,source_entry_P3_hashes_equal=True,science=q['science'],authorization_runtime_launcher_rendered_in_memory_only=True,actual_materialization=False,prior_static_check_limitation='Windows Path incorrectly resolves Linux absolute output into local drive; corrected only local comparison, source/request/CPU unchanged'))
send=[entry,V/'test_output_policy_cpu_v6.py',V/'implementation_P3_v3.json',V/'CPU_batch_v6/result.json',V/'CPU_batch_v6/completion_receipt_v6.json',V/'CPU_scope_v3.json',V/'Windows_CPU_scope_v6.json',V/'retired_request_v2.json',V/'final_request_contract_review_v3.json']
for p in send:shutil.copyfile(p,P/('CPU_result_v6.json' if p.name=='result.json' else p.name))
files=[dict(member='payload/'+p.name,target=root+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p),overwrite=False) for p in sorted(P.iterdir())]
L=q['launch_contract'];emit(T/'installation_mapping_v3.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',remote_root=root,request_sha256=qh,files=files,reused_assets='Unchanged v1 head/factory/runtime and U/H; inherited LQI/Mamba/provider and exact project sources; rehash/reuse only',required_before_install='Current identity/GPU selector exact, uploaded4file hashes, reused exact hashes incl traceback sources, parents no links, all new targets/control/output absent and original resources pass; any mismatch stop',not_materialized=[L[k] for k in ['authorization_path','runtime_path','launcher_path','launch_attempt_path']]+[q['output']],overwrite=False,retry=False))
arc=T/'bcsp_spcg_output_policy_pending_20261116_v3.tar.gz'
with tarfile.open(arc,'x:gz') as t:
 t.add(T/'installation_mapping_v3.json',arcname='installation_mapping_v3.json',recursive=False)
 for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(arc,'r:gz') as t:
 members=t.getmembers();assert len(members)==len(files)+1 and all(x.isfile() for x in members);listing=''.join(hashlib.sha256(t.extractfile(x).read()).hexdigest()+'  '+x.name+'\n' for x in members)
for suffix,value in [('.sha256',sha(arc)+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:Path(str(arc)+suffix).write_text(value,encoding='utf-8')
emit(V/'delivery_receipt_v3.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_COMPLETE_HASH_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),P3=rec(V/'implementation_P3_v3.json'),install_files=len(files),CPU_checks=12,server_calls=0,CUDA=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,training_request_created=False))
print(json.dumps(dict(status='P3_PASS_NEW_V3_REQUEST_PENDING',request_SHA256=qh,archive_bytes=arc.stat().st_size,install_files=len(files))))
