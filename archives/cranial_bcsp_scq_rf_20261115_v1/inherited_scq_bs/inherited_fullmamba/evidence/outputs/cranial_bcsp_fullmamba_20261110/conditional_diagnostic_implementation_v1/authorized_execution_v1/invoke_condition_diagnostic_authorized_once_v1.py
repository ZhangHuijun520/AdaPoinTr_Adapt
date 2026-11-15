"""Original byte transfer and raw response capture; one operation, no retry."""
import ast,base64,hashlib,json,shlex,subprocess,sys,time,zlib
from pathlib import Path
A=Path(__file__).resolve().parent;B=A.parent
QH='a21965cdefdf4a7903b5cb52b235dc5e30f0cd9d25a25915734967ee6ff7eda2'
SOURCE=A/'execute_condition_diagnostic_authorized_once_v1.py'
TARGET='/home/jovyan/adapointr_work/PoinTr/third_party/f0_condition_authorized_operation_20261111_v1.py'
BASE=['wsl.exe','-d','Ubuntu-20.04','--exec'];CLIENT='/home/zhj/.local/bin/hpc5000';EVENTS=[]
def emit(name,obj):
 with (A/name).open('x',encoding='ascii') as f:json.dump(obj,f,indent=2,allow_nan=False)
def invoke(label,args,timeout):
 try:r=subprocess.run(args,capture_output=True,timeout=timeout);out,err,rc=r.stdout,r.stderr,r.returncode
 except subprocess.TimeoutExpired as exc:out,err,rc=exc.stdout or b'',exc.stderr or b'',None
 for k,b in [('stdout',out),('stderr',err)]:
  with (A/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 event=dict(stage=label,returncode=rc,stdout_bytes=len(out),stderr_bytes=len(err),stdout_sha256=hashlib.sha256(out).hexdigest(),stderr_sha256=hashlib.sha256(err).hexdigest());EVENTS.append(event);print(json.dumps(event),flush=True)
 if rc!=0:raise RuntimeError('stage failed or timeout, STOP_NO_RETRY: '+label)
 return out
def cmd(code):
 payload=base64.b64encode(zlib.compress(code.encode('utf-8'),9)).decode('ascii')
 c=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c','import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(payload)+')),"<authorized-readiness>","exec"))'])
 assert len(c.encode())<=2048;return c
READINESS=r'''
import os,socket,pathlib,hashlib,json,sys,subprocess,shutil
P=pathlib.Path;root=P('/home/jovyan/adapointr_work/PoinTr');arc=P('/home/jovyan/bcsp_f0_CD_condition_diagnostic_pending_20261111_v1.tar.gz')
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
assert str(P(sys.executable).resolve())=='/opt/conda/envs/adapointr-mamba/bin/python3.10' and sys.version.split()[0]=='3.10.20'
assert not any(x.is_symlink() for x in (arc,*arc.parents)) and arc.stat().st_size==20841 and hashlib.sha256(arc.read_bytes()).hexdigest()=='dd6f12dd86911e9e4aeb69589e31e01fac15d40bb9bc3413290ee84043575769'
targets=[root/'third_party/bcsp_f0_CD_condition_diagnostic_20261111_v1',root/'logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1',root/'third_party/f0_condition_authorized_operation_20261111_v1.py']
assert all(not p.exists() and not any(x.is_symlink() for x in (p,*p.parents)) for p in targets)
r=subprocess.check_output(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=10,text=True).strip().splitlines();assert len(r)==1;g=[x.strip() for x in r[0].split(',')]
assert g[:4]==['GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed','NVIDIA GeForce RTX 4090 D','575.51.03','24564'] and int(g[4])<=256
assert shutil.disk_usage(root).free>=4294967296
print(json.dumps(dict(status='IDENTITY_UPLOAD_AND_FRESH_TARGETS_PRECHECK_PASS',hostname=socket.gethostname(),GPU=g,free_disk_bytes=shutil.disk_usage(root).free,server_writes=0)))
'''
def main():
 start=time.monotonic()
 try:
  assert hashlib.sha256((B/'frozen_pending_transport_v1/payload/F0_CD_decoder_diagnostic_execution_request_v1.json').read_bytes()).hexdigest()==QH
  b=SOURCE.read_bytes();ast.parse(b.decode('utf-8'));hs=hashlib.sha256(b).hexdigest()
  emit('local_single_execution_claim_v2.json',dict(status='CLAIMED_BEFORE_AUTHORIZED_OPERATION',request_sha256=QH,user_authorization_text='已上传，下一步单独授权此 request 完整SHA256，才能不覆盖安装并启动唯一一次诊断。',operation_source_sha256=hs,no_retry=True))
  pre=cmd(READINESS);emit('initial_readonly_command_v2.json',dict(command=pre,bytes=len(pre.encode())))
  raw=invoke('initial_readonly',BASE+[CLIENT,'exec','--timeout','20','--',pre],35);print(raw.decode('utf-8'),flush=True)
  wsl=invoke('resolve_operation_source',BASE+['wslpath','-a',str(SOURCE)],15).decode('utf-8').strip();assert wsl.startswith('/mnt/e/') and '\n' not in wsl
  invoke('put_exact_operation_control',BASE+[CLIENT,'put',wsl,TARGET],45)
  code='import pathlib,hashlib; p=pathlib.Path('+repr(TARGET)+'); assert not any(x.is_symlink() for x in (p,*p.parents)); b=p.read_bytes(); assert hashlib.sha256(b).hexdigest()=='+repr(hs)+'; exec(compile(b,str(p),"exec"))'
  command=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',code]);assert len(command.encode())<=2048
  emit('authorized_operation_command_v2.json',dict(command=command,bytes=len(command.encode()),source_sha256=hs))
  raw=invoke('verify_install_materialize_single_launch',BASE+[CLIENT,'exec','--timeout','150','--',command],165)
  print(json.dumps(dict(operation_stdout=raw.decode('utf-8',errors='replace')[-16000:]),ensure_ascii=True),flush=True)
  result=dict(status='AUTHORIZED_OPERATION_RETURNED_INSPECT_STARTUP',request_sha256=QH,events=EVENTS,seconds=time.monotonic()-start,automatic_retry=False)
 except BaseException as exc:result=dict(status='FAILED_STOP_NO_RETRY',request_sha256=QH,error=repr(exc),events=EVENTS,seconds=time.monotonic()-start)
 emit('local_authorized_operation_result_v2.json',result);print(json.dumps(result),flush=True)
 return 1 if result['status']=='FAILED_STOP_NO_RETRY' else 0
if __name__=='__main__':sys.exit(main())
