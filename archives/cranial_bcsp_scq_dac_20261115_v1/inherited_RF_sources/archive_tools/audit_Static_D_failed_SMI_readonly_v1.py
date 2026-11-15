"""Bounded read-only failure freeze; never invokes nvidia-smi or loads production modules."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,zlib
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Static_D_implementation_20261115_v1';O=B/'failed_startup_SMI_review_v1';A=B/'authorized_execution_v1'
Q=B/'pending_transport_v1/payload/SCQ_RF_Static_D_training_execution_request_v1.json';RH='b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,j):
 with p.open('x',encoding='utf-8') as f:json.dump(j,f,ensure_ascii=False,indent=2,allow_nan=False)
assert sha(Q)==RH;q=read(Q);mp=read(B/'pending_transport_v1/installation_mapping_v1.json');root=mp['remote_root']
prefix='''from pathlib import Path
import socket,os,hashlib,json,subprocess,base64
assert socket.gethostname()==HOST and os.getuid()==1000
root=Path(ROOT);out=Path(OUT)
assert not any(p.is_symlink() for p in (root,*root.parents,out,*out.parents))
assert hashlib.sha256((root/'SCQ_RF_Static_D_training_execution_request_v1.json').read_bytes()).hexdigest()==RH
q=json.loads((root/'SCQ_RF_Static_D_training_execution_request_v1.json').read_bytes())
'''
class Bind(ast.NodeTransformer):
 def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
values=dict(HOST=q['identity']['hostname'],ROOT=root,OUT=q['output'],RH=RH)
prefix=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(prefix))))+'\n'
inventory='''assert (out/'exit_code.txt').read_text().strip()=='1' and not (out/'worker.pid').exists()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
assert subprocess.run(['pgrep','-f',q['implementation']['entry']['path']],capture_output=True,timeout=5).returncode==1
files={};dirs={};paths=[];total=0
for label,p in [('output',out),('installed',root)]:
 ds=['.']
 for f in sorted(p.rglob('*')):
  assert not f.is_symlink() and (f.is_file() or f.is_dir())
  if f.is_dir():ds.append(str(f.relative_to(p)));assert len(ds)<=8
  else:paths.append((label+'/'+str(f.relative_to(p)),f))
 dirs[label]=sorted(ds)
paths.append(('helper/preflight_helper.py',Path(q['implementation']['preflight_helper']['path'])))
assert len(paths)<=24
fp=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
for name,p in paths:
 assert not any(x.is_symlink() for x in (p,*p.parents));before=p.stat();assert before.st_size<=2097152
 raw=p.read_bytes();total+=len(raw);assert total<=8388608;after=p.stat();assert fp(before)==fp(after)
 files[name]=dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),fingerprint=fp(after))
print(json.dumps(dict(status='BOUNDED_STABLE_FAILED_STARTUP_INVENTORY',hostname=socket.gethostname(),uid=os.getuid(),exit_code=1,tmux_absent=True,entry_process_absent=True,files=files,directories=dirs,total_bytes=total)))
'''
metadata='''files={};total=0
paths=[(label+'/'+str(f.relative_to(p)),f) for label,p in [('output',out),('installed',root)] for f in sorted(p.rglob('*')) if f.is_file()]
paths.append(('helper/preflight_helper.py',Path(q['implementation']['preflight_helper']['path'])))
assert len(paths)<=24
for name,p in paths:
 assert not p.is_symlink() and p.stat().st_size<=2097152
 raw=p.read_bytes();total+=len(raw);assert total<=8388608
 files[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
print(json.dumps(dict(status='BOUNDED_METADATA_READBACK',files=files,total_bytes=total)))
'''
scripts=[]
for label,code in [('inventory_before',inventory),('metadata',metadata),('inventory_after',inventory)]:
 code=prefix+code;ast.parse(code);compile(code,label,'exec');blob=base64.b64encode(zlib.compress(code.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import zlib,base64;exec(zlib.decompress(base64.b64decode('+repr(blob)+')))']);assert len(cmd.encode())<=2048;scripts.append((label,code,cmd))
import sys
if '--static' in sys.argv:
 O.mkdir()
 for label,code,cmd in scripts:
  with (O/(label+'.remote.py')).open('x',encoding='utf-8') as f:f.write(code)
 emit(O/'scope_v1.json',dict(status='READONLY_FAILURE_FREEZE_AND_STATIC_SMI_CALL_REVIEW',max_files=24,max_file_bytes=2097152,max_total_bytes=8388608,calls=3,per_call_timeout=30,SMI_queries=0,new_forward=0,server_writes=0,controller_sha256=sha(Path(__file__)),max_command_bytes=max(len(v[2].encode()) for v in scripts)))
 print('READONLY_SMI_FAILURE_AUDIT_STATIC_PASS');sys.exit(0)
assert read(O/'scope_v1.json')['controller_sha256']==sha(Path(__file__))
checks={}
def check(k,v):assert v,k;checks[k]=True
try:
 for label,code,cmd in scripts:
  x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',cmd],capture_output=True,timeout=45)
  for name,b in [('stdout',x.stdout),('stderr',x.stderr)]:
   with (O/(label+'_'+name+'.bin')).open('xb') as f:f.write(b)
  assert x.returncode==0,(label,x.stdout.decode(errors='replace')[-1500:]);j=json.loads(x.stdout);emit(O/(label+'_v1.json'),j)
  if label=='metadata':
   for name,r in j['files'].items():
    p=O/'downloads'/name;p.parent.mkdir(parents=True,exist_ok=True);raw=base64.b64decode(r['base64']);assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
    with p.open('xb') as f:f.write(raw)
  print(json.dumps(dict(stage=label,status=j['status'])),flush=True)
 before=read(O/'inventory_before_v1.json');after=read(O/'inventory_after_v1.json');files=before['files'];D=O/'downloads'
 check('all20_files_content_attributes_stable_excluding_atime',before==after and len(files)==20)
 check('exact2output_files',set(n for n in files if n.startswith('output/'))=={'output/launch.log','output/exit_code.txt'})
 check('exact17installed_files_and_directories',sum(n.startswith('installed/') for n in files)==17 and before['directories']==dict(output=['.'],installed=['.','control']))
 check('request_exact_authorized_hash',sha(D/'installed/SCQ_RF_Static_D_training_execution_request_v1.json')==RH)
 for r in mp['files']:
  p=D/'installed'/Path(r['target']).name;assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
 check('all13_installed_payloads_exact',True)
 for name in ['authorization_v1.json','runtime_v1.json','launch_once_v1.sh']:assert (D/'installed/control'/name).read_bytes()==(A/name).read_bytes()
 auth=read(D/'installed/control/authorization_v1.json');rt=read(D/'installed/control/runtime_v1.json')
 check('authorized_controls_and_oneway_runtime_binding',auth['request_sha256']==RH and auth['explicit_user_authorization'] and rt['request_sha256']==RH and rt['authorization_sha256']==sha(D/'installed/control/authorization_v1.json'))
 check('single_claim_consumed',read(D/'installed/control/attempt_claim_v1.json')==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=RH))
 helper=D/'helper/preflight_helper.py';check('helper_fresh_hash_exact_request',sha(helper)==q['implementation']['preflight_helper']['sha256'] and helper.stat().st_size==q['implementation']['preflight_helper']['bytes'])
 entry=D/'installed/bcsp_scq_rf_Static_D_training_entry_v1.py';src=entry.read_text(encoding='utf-8');ht=helper.read_text(encoding='utf-8');log=(D/'output/launch.log').read_text(encoding='utf-8');launcher=(D/'installed/control/launch_once_v1.sh').read_text(encoding='utf-8')
 check('failure_exact_monitor_nonzero_exit_before_PID_model', 'MonitorQueryFailure: monitor query NONZERO_EXIT: ChildNonzeroExit' in log and "gpu=[s.strip() for s in helper.smi(" in log and src.index("gpu=[s.strip() for s in helper.smi(")<src.index("with (out/'worker.pid').open")<src.index('import torch,timm'))
 check('monitor_disabled_before_startup_query',"helper._MONITOR=None" in src and "if monitor:\n            monitor.event(dict(details, event='smi_result'))" in ht)
 ht_tree=ast.parse(ht);smi=next(n for n in ht_tree.body if isinstance(n,ast.FunctionDef) and n.name=='smi');assert "'--id=' + os.environ['CUDA_VISIBLE_DEVICES']" in ast.unparse(smi)
 gpu_query='uuid,name,driver_version,memory.total,memory.used';old_uuid=q['environment']['CUDA_VISIBLE_DEVICES'];new_uuid=q['identity']['gpu_uuid']
 command=['/usr/bin/nvidia-smi','--id='+old_uuid,'--query-gpu='+gpu_query,'--format=csv,noheader,nounits']
 check('frozen_launcher_exports_old_UUID',('export CUDA_VISIBLE_DEVICES='+old_uuid) in launcher and old_uuid==q['historical_identity']['gpu_uuid'] and old_uuid!=new_uuid)
 check('caller_helper_command_selection_confirmed',"helper.smi('"+gpu_query+"')" in src and "return _smi_once(args, SMI_TIMEOUT, _MONITOR)" in ht)
 cls=next(n for n in ht_tree.body if isinstance(n,ast.ClassDef) and n.name=='MonitorQueryFailure');ct=ast.unparse(cls)
 check('exception_details_not_in_printed_message',"self.details = details" in ct and "details['status']" in ct and "details.get('exception_type', '')" in ct and 'stderr' not in ct)
 check('prior_unqualified_resource_query_succeeded',read(A/'identity_resources.json')['GPU'][0]==new_uuid and read(A/'identity_resources.json')['GPU'][2]==q['identity']['driver_version'])
 findings=dict(status='PRECISE_DEVICE_SELECTOR_MISMATCH_AND_LOST_DIAGNOSTICS_CONFIRMED',actual_startup_command=command,shell_display=shlex.join(command),SMI_timeout_seconds=10.0,reap_timeout_seconds=2.0,
 expected_current_uuid=new_uuid,actual_selector_uuid=old_uuid,root_cause='Accepted identity migration updated q.identity but preserved old q.environment.CUDA_VISIBLE_DEVICES, so frozen launcher and helper.smi --id select the historical GPU.',
 error_evidence=dict(printed_exception='monitor query NONZERO_EXIT: ChildNonzeroExit',stderr_recoverable_from_existing_artifacts=False,exact_child_returncode_recoverable=False,stdout_recoverable=False,explanation='Popen captured stdout/stderr/returncode in MonitorQueryFailure.details; _MONITOR=None prevented persistence; exception string omits details; process exited. No additional stderr text or numeric child exit code can be established without a separately authorized rerun.'),
 certainty='Selector mismatch is directly established by server-fresh request+launcher+helper bytes. Specific NVIDIA stderr wording is unavailable; do not invent it or rule out any simultaneous driver issue.',
 minimal_next_fix=['Version current CUDA_VISIBLE_DEVICES together with exact accepted current GPU UUID; preserve numerical env values.','Validate historical CUDA environment against historical identity, and current execution env against only the explicit selector migration.','Persist bounded startup MonitorQueryFailure.details before re-raising, without retries or threshold changes.','One targeted CPU batch exercises actual launcher exports + smi argv with a fake child and nonzero stdout/stderr/returncode persistence; retain stop-on-failure.','New P3 and fresh pending request required; current request is consumed.'],server_writes=0,SMI_query_reexecuted=False,new_forward=0,production_edits=0)
 emit(O/'SMI_failure_cause_findings_v1.json',findings)
 result=dict(status='FORMAL_STATIC_D_FAILED_STARTUP_FREEZE_AUDIT_PASS',checks=checks,count=len(checks),request_sha256=RH,request_consumed=True,reuse_allowed=False,exit_code=1,committed_updates=0,new_forward=0,server_writes=0,SMI_queries=0,files=files,findings=rec(O/'SMI_failure_cause_findings_v1.json'),limitations=['Read-only reconstruction, no replay of failed SMI query.','Captured child diagnostics were not persisted; exact stderr and numeric child status unavailable.'])
 emit(O/'freeze_verification_v1.json',result)
 print(json.dumps(dict(status=result['status'],checks=len(checks),files=len(files),actual_command=command,updates=0)))
except BaseException as exc:
 emit(O/'audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),server_writes=0,new_forward=0));raise
