HOST='shu-common-25721452-notebook-v2iwsa-0'
OUT='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_blue_noise_ab_v1/bcsp_blue_pair_foldC_seed0_dev_v1'
SESSION='bcsp_blue_pair_foldc_seed0_dev_v1'
import os,socket,json,subprocess,time
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
print(json.dumps(dict(status='READONLY_PAIRED_PREDICTION_STATUS',time_epoch=time.time(),hostname=socket.gethostname(),session_alive=session,worker_pid=pid,worker_alive=alive,exit_code=code.strip() if code else None,prediction_records=len(records),last_prediction=records[-1] if records else None,last_resources=resources[-1] if resources else None,failure=failure,inference_complete=done,completion_archive={k:v for k,v in completion['archive'].items() if k!='members'} if completion else None,completion_status=completion['status'] if completion else None,launch_log_tail='\n'.join(log.splitlines()[-18:]) if log else None,formal_freeze_audit=False,server_writes=0,observer_forwards=0)),flush=True)
