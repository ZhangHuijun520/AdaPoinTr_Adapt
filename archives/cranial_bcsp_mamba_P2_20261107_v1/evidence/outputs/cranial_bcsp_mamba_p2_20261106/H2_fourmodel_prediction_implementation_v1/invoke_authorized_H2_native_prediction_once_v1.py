"""Raw-byte, short-command transport for this unique authorization. No retry."""
import hashlib,json,shlex,subprocess,time
from pathlib import Path
S=Path(__file__).resolve().parent;A=S/'authorized_execution_v1';A.mkdir()
QH='b95b866a6b3a0eaeb1e840e003ecd426847ed47b07675b6c1f7644b5aee97170'
assert hashlib.sha256((S/'pending_request_v1/transport_payload/H2_C_D_fourmodel_native_prediction_execution_request_v1.json').read_bytes()).hexdigest()==QH
helper=S/'execute_authorized_H2_native_prediction_once_v1.py';target='/home/jovyan/adapointr_work/PoinTr/third_party/H2_fourmodel_native_authorized_once_20261107_v1.py';hh=hashlib.sha256(helper.read_bytes()).hexdigest()
BASE=['wsl.exe','-d','Ubuntu-20.04','--exec'];CLIENT='/home/zhj/.local/bin/hpc5000';events=[];start=time.monotonic()
def invoke(label,args,timeout):
 try:r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 except subprocess.TimeoutExpired as exc:
  for k,b in [('stdout',exc.stdout or b''),('stderr',exc.stderr or b'')]:
   with (A/(label+'_timeout_'+k+'.bin')).open('xb') as f:f.write(b)
  raise
 for suffix,blob in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (A/(label+'_'+suffix+'.bin')).open('xb') as f:f.write(blob)
 event=dict(stage=label,returncode=r.returncode,stdout_bytes=len(r.stdout),stderr_bytes=len(r.stderr),stdout_sha256=hashlib.sha256(r.stdout).hexdigest(),stderr_sha256=hashlib.sha256(r.stderr).hexdigest());events.append(event);print(json.dumps(event),flush=True)
 if r.returncode:raise RuntimeError('transport/remote stage failed: '+label)
 return r.stdout
try:
 with (A/'local_single_attempt_claim_v1.json').open('x',encoding='ascii') as f:json.dump(dict(status='CLAIMED_BEFORE_TRANSPORT',request_sha256=QH,no_retry=True,helper_sha256=hh),f)
 path=invoke('resolve_WSL_path',BASE+['wslpath','-a',str(helper)],15).decode().strip();assert path.startswith('/mnt/e/') and '\n' not in path
 check='test "$(hostname)" = shu-common-25721452-notebook-1lvq9b-0 && test "$(id -u)" = 1000 && test ! -e '+shlex.quote(target)+' && test ! -L '+shlex.quote(target)
 invoke('identity_and_staging_target_absent',BASE+[CLIENT,'exec','--timeout','15','--',check],25)
 invoke('put_exact_operation_helper',BASE+[CLIENT,'put',path,target],45)
 code='import pathlib,hashlib; b=pathlib.Path('+repr(target)+').read_bytes(); assert hashlib.sha256(b).hexdigest()=='+repr(hh)+'; exec(compile(b,"<authorized_single_operation>","exec"))'
 command=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',code]);assert len(command.encode())<=2048
 out=invoke('verify_install_materialize_launch',BASE+[CLIENT,'exec','--timeout','170','--',command],180)
 print(out.decode(errors='replace')[-14000:],flush=True)
 result=dict(status='AUTHORIZED_OPERATION_RETURNED_INSPECT_STARTUP',request_sha256=QH,events=events,seconds=time.monotonic()-start,no_retry=True)
except BaseException as exc:
 result=dict(status='FAILED_STOP_NO_RETRY',request_sha256=QH,error=repr(exc),events=events,seconds=time.monotonic()-start);print(json.dumps(result),flush=True)
finally:
 with (A/'local_operation_result_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
if result['status']=='FAILED_STOP_NO_RETRY':raise SystemExit(1)
