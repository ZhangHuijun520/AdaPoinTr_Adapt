"""Freeze failed startup evidence and hash only two fixed input-path candidates per case."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,shutil,subprocess,zlib
R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/pending_request_v1'
O=B/'failed_inputs_readonly_audit_v1';O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(n,v):
 if (O/n).exists():
  assert read(O/n)==v;return
 with (O/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
qpath=B/'payload/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json';RH='b503b487e2ed3a00b60400f2e71c98a2d56931dbdf25a77ff32e717b4ff1e561'
assert sha(qpath)==RH;q=read(qpath);delivery=read(B/'delivery_receipt_v1.json');mp=read(B/'installation_mapping_v1.json');A=B/'authorized_execution_v1'
snapshot=O/'failure_evidence';snapshot.mkdir(exist_ok=True);frozen=[]
for p in sorted(A.iterdir()):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=1048576
 dst=snapshot/p.name
 if not dst.exists():shutil.copyfile(p,dst)
 assert sha(p)==sha(dst)
 frozen.append(dict(source=str(p),frozen_copy=str(dst),bytes=p.stat().st_size,sha256=sha(dst)))
emit('failure_evidence_manifest_v1.json',dict(request_sha256=RH,files=frozen,stop_receipt=read(A/'stop_receipt_v1.json'),controls_locally_materialized=any((A/n).exists() for n in ['authorization_v1.json','runtime_v1.json','launch_once_v1.sh'])))
roots=[q['identity']['project']+'/data/bcsp_geov1_foldc_8192_seed0_v1/points',q['identity']['project']+'/data/bcsp_geov1_foldd_8192_seed0_v1/points']
scope=dict(status='FROZEN_READONLY_SCOPE',hostname=q['identity']['hostname'],uid=1000,request_sha256=RH,exact_roots=roots,unique_cases=210,prediction_occurrences=630,maximum_candidate_paths=420,maximum_file_bytes=2097152,maximum_hashed_bytes=268435456,remote_timeout_seconds=60,no_directory_recursion=True,operations=dict(server_writes=0,NPZ_array_reads=0,checkpoint_loads=0,model_imports=0,GPU_calls=0,installation=0,forward=0,retry=0))
emit('bounded_scope_v1.json',scope)
code='''from pathlib import Path
import socket,os,hashlib,tarfile,json,subprocess,time
assert socket.gethostname()==HOST and os.getuid()==1000
start=time.monotonic();total=0
p=Path(ARCHIVE);assert not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size<1048576 and hashlib.sha256(p.read_bytes()).hexdigest()==DIGEST
with tarfile.open(p) as t:idx=json.loads(t.extractfile('payload/RF_sixmodel_input_index_v1.json').read())
rows=list({r['input']['path']:r for r in idx['inputs']}.values());assert len(rows)==210 and len(idx['inputs'])==630
for root in ROOTS:
 p=Path(root);assert p.is_dir() and not any(x.is_symlink() for x in (p,*p.parents))
def state():
 return dict(targets=[dict(path=x,exists=Path(x).exists(),symlink=Path(x).is_symlink()) for x in TARGETS],tmux_live=subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==0)
before=state();out=[]
for row in rows:
 expected=row['input'];name=Path(expected['path']).name;assert name==row['case_id']+'_8192.npz'
 candidates=[]
 for root in ROOTS:
  p=Path(root)/name;checks=dict(exists=p.exists(),no_links=not any(x.is_symlink() for x in (p,*p.parents))),r=dict(path=str(p))
  r.update(checks=checks)
  if checks['exists'] and checks['no_links']:
   checks['regular_file']=p.is_file()
   if checks['regular_file']:
    st=p.stat();r['bytes']=st.st_size;checks['size_matches']=st.st_size==expected['bytes'];checks['bounded_size']=st.st_size<=2097152
    if checks['bounded_size']:
     assert time.monotonic()-start<50 and total+st.st_size<=268435456
     h=hashlib.sha256()
     with p.open('rb') as f:
      for b in iter(lambda:f.read(1048576),b''):h.update(b);total+=len(b)
     end=p.stat();assert (st.st_size,st.st_mtime_ns,st.st_ctime_ns)==(end.st_size,end.st_mtime_ns,end.st_ctime_ns)
     r['sha256']=h.hexdigest();checks['hash_matches']=r['sha256']==expected['sha256']
  r['valid_match']=all(checks.get(k,False) for k in ['exists','no_links','regular_file','size_matches','bounded_size','hash_matches']);candidates.append(r)
 original=next(c for c in candidates if c['path']==expected['path'])
 out.append(dict(fold=row['fold'],case_id=row['case_id'],expected=expected,original_valid=original['valid_match'],candidates=candidates))
after=state();assert before==after
print(json.dumps(dict(status='BOUNDED_INPUT_PATH_OBSERVATION_COMPLETE',hostname=socket.gethostname(),uid=os.getuid(),before=before,after=after,rows=out,hashed_bytes=total,seconds=time.monotonic()-start,server_writes=0,array_reads=0,new_forward=0)))
'''
# Keep each remote script short; syntax and exact bytes checked before any connection.
code=code.replace("checks=dict(exists=p.exists(),no_links=not any(x.is_symlink() for x in (p,*p.parents))),r=dict(path=str(p))", "checks=dict(exists=p.exists(),no_links=not any(x.is_symlink() for x in (p,*p.parents)));r=dict(path=str(p))")
vals=dict(HOST=q['identity']['hostname'],ARCHIVE='/home/jovyan/'+Path(delivery['archive']['path']).name,DIGEST=delivery['archive']['sha256'],ROOTS=roots,TARGETS=[mp['remote_root'],q['output'],q['launch_attempt'],*list(q['launch_contract'][k] for k in ['authorization','runtime','launcher'])],SESSION=q['launch_contract']['tmux_session'])
class Bind(ast.NodeTransformer):
 def visit_Name(self,n):return ast.copy_location(ast.parse(repr(vals[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in vals else n
code=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(code))));ast.parse(code,feature_version=(3,8))
blob=base64.b85encode(zlib.compress(code.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import zlib,base64;exec(zlib.decompress(base64.b85decode('+repr(blob)+')))'])
assert len(cmd.encode())<=2048,len(cmd.encode())
with (O/'readonly_paths.remote.py').open('x',encoding='utf-8') as f:f.write(code)
emit('static_review_v1.json',dict(status='STATIC_READONLY_BOUNDED_PASS',command_bytes=len(cmd.encode()),scope_sha256=sha(O/'bounded_scope_v1.json'),script_sha256=sha(O/'readonly_paths.remote.py')))
try:
 x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--',cmd],capture_output=True,timeout=75)
 for label,data in [('stdout',x.stdout),('stderr',x.stderr)]:
  with (O/(label+'.bin')).open('xb') as f:f.write(data)
 assert x.returncode==0,(x.returncode,x.stdout.decode(errors='replace')[-1500:])
 result=json.loads(x.stdout);emit('remote_path_observation_v1.json',result)
 rows=result['rows'];resolved=[]
 for r in rows:
  matches=[c for c in r['candidates'] if c['valid_match']]
  resolved.append(dict(fold=r['fold'],case_id=r['case_id'],frozen_expected_path=r['expected']['path'],original_valid=r['original_valid'],matching_paths=[c['path'] for c in matches],bytes=r['expected']['bytes'],sha256=r['expected']['sha256']))
 emit('observed_path_matches_NOT_binding_change_v1.json',dict(status='READONLY_OBSERVATIONS_NOT_EXECUTION_BINDING',cases=resolved))
 checks=dict(exact_request_hash=True,local_failure_evidence_frozen=True,remote_identity_exact=result['hostname']==q['identity']['hostname'] and result['uid']==1000,no_execution_targets_created=all(not x['exists'] and not x['symlink'] for x in result['before']['targets']),tmux_absent=not result['before']['tmux_live'],pre_post_execution_state_stable=result['before']==result['after'],all210_cases_examined=len(rows)==210,all210_have_exact_hash_match=all(r['matching_paths'] for r in resolved),every_case_unique_matching_path=all(len(r['matching_paths'])==1 for r in resolved),bounded_bytes=result['hashed_bytes']<=scope['maximum_hashed_bytes'],no_remote_writes=result['server_writes']==0,no_arrays_or_forward=result['array_reads']==result['new_forward']==0)
 summary=dict(status='READONLY_FAILURE_FREEZE_AND_PATH_CHECK_COMPLETE' if all(checks.values()) else 'READONLY_CHECK_COMPLETE_WITH_GAPS_STOP',checks=checks,original_valid_cases=sum(r['original_valid'] for r in resolved),original_invalid_cases=sum(not r['original_valid'] for r in resolved),unique_match_cases=sum(len(r['matching_paths'])==1 for r in resolved),missing_or_mismatched_cases=sum(not r['matching_paths'] for r in resolved),ambiguous_cases=sum(len(r['matching_paths'])>1 for r in resolved),by_fold={f:dict(cases=sum(r['fold']==f for r in resolved),original_valid=sum(r['fold']==f and r['original_valid'] for r in resolved),matching_parent_directories=sorted({str(Path(p).parent) for r in resolved if r['fold']==f for p in r['matching_paths']})) for f in 'CD'},hashed_bytes=result['hashed_bytes'],remote_seconds=result['seconds'],request_sha256=RH,execution_request_unchanged=True,installation=0,forward=0,server_writes=0,limitation='Read-only metadata and byte hashes; no NPZ payload interpretation or model validation; no permission to alter binding or retry.')
 emit('freeze_and_path_findings_v1.json',summary)
 # Reconfirm original local evidence remains byte-identical to the frozen copies.
 assert all(sha(Path(r['source']))==sha(Path(r['frozen_copy']))==r['sha256'] for r in frozen)
 records=[dict(name=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(O.rglob('*')) if p.is_file()]
 emit('audit_evidence_manifest_v1.json',dict(files=records,server_writes=0,new_forward=0))
 print(json.dumps(summary,ensure_ascii=False))
except BaseException as exc:
 emit('audit_stop_v1.json',dict(status='READONLY_AUDIT_STOP_NO_RETRY',error=repr(exc),server_writes=0,forward=0));raise
