"""Bounded read-only observation of the one authorized paired prediction attempt."""
import ast,base64,hashlib,json,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1';A=N/'authorized_execution_v1'
BOOT="import sys,json,base64,io;d=json.load(sys.stdin);sys.stdin=io.TextIOWrapper(io.BytesIO(base64.b64decode(d['stdin'])));exec(compile(base64.b64decode(d['code']),'pair_prediction_readonly_driver','exec'),{'__name__':'__main__'})"
def main():
 sys.stdout.reconfigure(encoding='utf-8');index=sys.argv[1];assert index.isdecimal() and 1<=int(index)<=99
 q=json.loads((N/'development_entry_request_v1.json').read_bytes());scope=json.loads((N/'development_execution_request_v1.json').read_bytes())
 source='''import os,socket,json,subprocess,time
from pathlib import Path
assert socket.gethostname()==HOST and os.getuid()==1000,'current identity'
out=Path(OUT);assert out.is_dir() and not any(p.is_symlink() for p in (out,*out.parents)),'output link/type'
def text(name,cap):
 p=out/name
 if not p.exists():return None
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=cap,'text budget: '+name
 return p.read_text(errors='replace')
def doc(name):
 t=text(name,1048576);return json.loads(t) if t else None
def lines(name,cap):
 t=text(name,cap);return [json.loads(x) for x in t.splitlines()] if t else []
records=lines('inference_manifest.jsonl',1048576);resources=lines('resources.jsonl',4194304)
done=doc('inference_complete.json');completion=doc('completion.json');failure=doc('failure.json');code=text('exit_code.txt',64)
session=subprocess.run(['tmux','has-session','-t',SESSION],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5).returncode==0
pid=text('worker.pid',64);pid=pid.strip() if pid else None;alive=bool(pid and pid.isdecimal() and Path('/proc/'+pid).exists())
log=text('launch.log',1048576)
print(json.dumps(dict(status='READONLY_PAIRED_PREDICTION_STATUS',time_epoch=time.time(),hostname=socket.gethostname(),session_alive=session,worker_pid=pid,worker_alive=alive,exit_code=code.strip() if code else None,prediction_records=len(records),last_prediction=records[-1] if records else None,last_resources=resources[-1] if resources else None,failure=failure,inference_complete=done,completion_archive={k:v for k,v in completion['archive'].items() if k!='members'} if completion else None,completion_status=completion['status'] if completion else None,launch_log_tail='\\n'.join(log.splitlines()[-18:]) if log else None,formal_freeze_audit=False,server_writes=0,observer_forwards=0)),flush=True)
'''
 source='HOST='+repr(q['identity']['hostname'])+'\nOUT='+repr(q['output'])+'\nSESSION='+repr(scope['tmux_session'])+'\n'+source
 raw=source.encode();ast.parse(raw)
 template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_bytes();driver=template.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',hashlib.sha256(raw).hexdigest().encode())
 prefix='prediction_observation_'+index
 with (A/(prefix+'_payload.py')).open('xb') as f:f.write(raw)
 payload=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(raw).decode())).encode();envelope=json.dumps(dict(code=base64.b64encode(driver).decode(),stdin=base64.b64encode(payload).decode())).encode()
 with (A/(prefix+'_started.json')).open('x') as f:json.dump(dict(readonly=True,payload_sha256=hashlib.sha256(raw).hexdigest()),f)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',BOOT],input=envelope,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=160)
 with (A/(prefix+'_capture.json')).open('x') as f:json.dump(dict(returncode=p.returncode,stdout_base64=base64.b64encode(p.stdout).decode(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest()),f,indent=2)
 text=p.stdout.decode('utf-16-le' if b'\x00' in p.stdout else 'utf-8',errors='replace');records=[]
 for line in text.splitlines():
  try:v=json.loads(line)
  except ValueError:continue
  if isinstance(v,dict) and v.get('status')=='READONLY_PAIRED_PREDICTION_STATUS':records.append(v)
 if p.returncode or len(records)!=1:print(text);raise SystemExit(1)
 with (A/(prefix+'_result.json')).open('x') as f:json.dump(records[0],f,indent=2)
 print(json.dumps(records[0]))
if __name__=='__main__':main()
