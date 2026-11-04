"""Bounded read-only startup observation, no checkpoints loaded or model calls."""
import base64,hashlib,json,re,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';A=O/'Morton_training_request_v1/authorized_execution_v1'
BOOT="import sys,json,base64,io;d=json.load(sys.stdin);sys.stdin=io.TextIOWrapper(io.BytesIO(base64.b64decode(d['stdin'])));exec(compile(base64.b64decode(d['code']),'frozen_observation_driver','exec'),{'__name__':'__main__'})"
def main():
 sys.stdout.reconfigure(encoding='utf-8')
 index=sys.argv[1];assert index.isdecimal() and 4<=int(index)<=99
 scope=json.loads((O/'Morton_training_request_v1/candidate_training_execution_request_v1.json').read_text(encoding='utf-8'))
 source='''import os,socket,json,subprocess,time
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
O=Path(OUTPUT);parents=[O.parent,*O.parent.parents];assert all(p.is_dir() and not p.is_symlink() for p in parents)
def read(name,cap=16384):
 p=O/name
 if not p.is_file():return None
 assert not p.is_symlink()
 with p.open('rb') as f:f.seek(max(0,p.stat().st_size-cap));return f.read(cap).decode('utf-8',errors='replace')
def last(name):
 text=read(name)
 if not text:return None
 for line in reversed(text.splitlines()):
  try:return json.loads(line)
  except ValueError:pass
 return None
def document(name):
 text=read(name)
 if not text:return None
 try:return json.loads(text)
 except ValueError:return None
session=subprocess.run(['tmux','has-session','-t',SESSION],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5).returncode==0
pid=read('worker.pid',64);pid=pid.strip() if pid else None
alive=bool(pid and pid.isdigit() and Path('/proc/'+pid).exists())
exitcode=read('exit_code.txt',64);failure=document('failure.json') or document('startup_failure.json');completion=document('completion.json')
metric=last('metrics.jsonl');resource=last('resources.jsonl')
state='EXITED' if exitcode is not None else 'FAILED' if failure else 'TRAINING_RUNNING' if session and alive and metric and metric.get('optimizer_step_committed') else 'STARTING_OR_UNCONFIRMED'
gpu=subprocess.run(['nvidia-smi','--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=8)
print(json.dumps(dict(schema='bcsp-sampling-startup-observation-v1',state=state,tmux_alive=session,worker_pid=pid,container_pid_alive=alive,exit_code=exitcode.strip() if exitcode else None,failure=failure,completion=completion,last_metric=metric,last_resource=resource,log_tail=read('launch.log'),initialization_written=(O/'initialization.json').is_file(),gpu=gpu.stdout.decode().strip(),GPU_query_returncode=gpu.returncode,observation_time_epoch=time.time(),model_calls_in_observer=0)))
'''
 source='OUTPUT='+repr(scope['future_paths']['output'])+'\nSESSION='+repr(scope['future_paths']['tmux'])+'\n'+source
 raw=source.encode();h=hashlib.sha256(raw).hexdigest()
 template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8')
 driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h).encode()
 payload=json.dumps({'payload_base64':base64.b64encode(raw).decode(),'mode':'execute_once'}).encode()
 envelope=json.dumps({'code':base64.b64encode(driver).decode(),'stdin':base64.b64encode(payload).decode()}).encode()
 prefix='startup_observation_'+index
 with (A/(prefix+'_started.json')).open('x') as f:json.dump({'scope_sha256':'d4a44a990c0b3f0b91522c6f9803074a34e6c3803c243bf08e8a46ace42eeae3','source_sha256':h,'read_only':True,'no_training_launch_or_retry':True},f,indent=2)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',BOOT],input=envelope,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=150)
 with (A/(prefix+'_capture.json')).open('x') as f:json.dump({'returncode':p.returncode,'stdout_base64':base64.b64encode(p.stdout).decode(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()},f,indent=2)
 print(p.stdout.decode('utf-16-le' if b'\x00' in p.stdout else 'utf-8',errors='replace'),flush=True)
 if p.returncode:raise SystemExit(1)
 records=[]
 for line in p.stdout.decode('utf-8',errors='replace').splitlines():
  try:v=json.loads(line)
  except ValueError:continue
  if isinstance(v,dict) and v.get('schema')=='bcsp-sampling-startup-observation-v1':records.append(v)
 assert len(records)==1
 with (A/(prefix+'_result.json')).open('x') as f:json.dump(records[0],f,indent=2)
 print('READONLY_STATE',records[0]['state'],flush=True)
if __name__=='__main__':main()
