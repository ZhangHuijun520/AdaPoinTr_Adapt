"""One bounded read-only failed-attempt freeze; never execute nvidia-smi or model."""
from pathlib import Path
import base64,zlib,json,subprocess,hashlib
S=Path(__file__).resolve().parent;O=S/'post_failure_freeze_v1';O.mkdir()
code="""from pathlib import Path
import json,hashlib,socket,os,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1');qp=r/'SPCG_CUDA_execution_request_v1.json';b=qp.read_bytes();qh=hashlib.sha256(b).hexdigest();assert qh=='00a69c5cc3d42e04f4caa3c21650dd58db5d8c1b446741a1b42caf6730213d0f';q=json.loads(b);o=Path(q['output']);files=[];total=0
for p in sorted(r.iterdir()):
 if p.is_file():
  assert not p.is_symlink();b=p.read_bytes();total+=len(b);files.append(dict(name=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
assert total<16*1024**2
controls={};output={}
for p in sorted((r/'control').iterdir()):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<32000;controls[p.name]=p.read_text()
for p in sorted(o.iterdir()):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<64000;output[p.name]=p.read_text()
h=Path(q['helper']['path']);hb=h.read_bytes();assert hashlib.sha256(hb).hexdigest()==q['helper']['sha256']
t=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5)
live=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:b=(p/'cmdline').read_bytes()
  except (OSError,PermissionError):continue
  if b'bcsp_spcg_cuda_entry_v1.py' in b and b'--request-sha256' in b:live.append(int(p.name))
print(json.dumps(dict(hostname=socket.gethostname(),request_sha256=qh,identity=q['identity']['gpu_uuid'],selector=q['environment']['CUDA_VISIBLE_DEVICES'],files=files,hashed_bytes=total,controls=controls,output=output,helper_sha256=hashlib.sha256(hb).hexdigest(),tmux_returncode=t.returncode,tmux_stderr=t.stderr.decode(),live_matching_worker_PIDs=live)))
"""
b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',c]
assert len(subprocess.list2cmdline(args).encode())<=2048
(O/'remote_readonly_source.py').write_text(code,encoding='utf-8')
p=subprocess.run(args,capture_output=True,timeout=30);(O/'stdout.bin').write_bytes(p.stdout);(O/'stderr.bin').write_bytes(p.stderr);assert p.returncode==0,p.returncode
v=json.loads(p.stdout);(O/'server_evidence.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
mapping=json.loads((S/'pending_transport_v2/installation_mapping_v1.json').read_text(encoding='utf-8'));byname={x['name']:x for x in v['files']}
checks=dict(exact_14_installed_set=set(byname)=={Path(x['target']).name for x in mapping['files']},installed_SHA_and_size=all(byname[Path(x['target']).name]['sha256']==x['sha256'] and byname[Path(x['target']).name]['bytes']==x['bytes'] for x in mapping['files']),exit_one=v['output'].get('exit_code.txt')=='1\n',only_launch_log_exit=set(v['output'])=={'launch.log','exit_code.txt'},tmux_absent=v['tmux_returncode']==1,no_worker=not v['live_matching_worker_PIDs'])
co=v['controls'];a=json.loads(co['authorization_v1.json']);rt=json.loads(co['runtime_v1.json']);ah=hashlib.sha256(co['authorization_v1.json'].encode()).hexdigest()
checks['one_way_authorization']=a['request_sha256']==v['request_sha256'] and rt==dict(schema='bcsp-spcg-runtime-v1',request_sha256=v['request_sha256'],authorization_sha256=ah)
checks['single_claim']=json.loads(co['launch_attempt_v1.json'])==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=v['request_sha256'])
checks['launcher_exports_frozen_stale_selector']='export CUDA_VISIBLE_DEVICES='+v['selector']+'\n' in co['launch_once_v1.sh']
assert all(checks.values()),checks
command=['/usr/bin/nvidia-smi','--id='+v['selector'],'--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']
out=dict(status='FORMAL_READONLY_FAILURE_FREEZE_PASS_EXECUTION_FAILED',checks=checks,request_sha256=v['request_sha256'],reconstructed_actual_SMI_argv=command,argv_basis='hash-bound helper.smi + hash-bound request + deployed launcher export; not a rerun or preserved argv event',identity_gpu=v['identity'],frozen_selector=v['selector'],binding_mismatch=True,original_SMI_returncode_numeric='NOT_PERSISTED',original_SMI_stdout='NOT_PERSISTED',original_SMI_stderr='NOT_PERSISTED',observed_exception='MonitorQueryFailure NONZERO_EXIT ChildNonzeroExit',root_cause='Request generator copied stale environment CUDA_VISIBLE_DEVICES while rebinding identity.gpu_uuid; startup omitted cross-field validation and failed to serialize exception.details before its try/except.',model_counts=dict(forward=0,loss=0,backward=0,optimizer_step=0),request_consumed=True,server_writes=0,SMI_queries=0,models=0,limitations=['No recovery of original child stderr is possible from retained files. Do not invent numeric child exit code or claim exclusive root cause beyond evidenced selector error.','Process view restricted to current container; no host namespace claim.'])
(O/'formal_failure_audit_result_v1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
