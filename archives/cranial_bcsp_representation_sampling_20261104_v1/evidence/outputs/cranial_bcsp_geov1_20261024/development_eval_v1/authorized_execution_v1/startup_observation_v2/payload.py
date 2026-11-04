OUT='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/development_four_models_seed0_v1'
HOST='shu-common-25721452-notebook-01dt08-0'
SESSION='bcsp_dev_four_models_seed0_v1'
import json,os,socket,subprocess
from pathlib import Path
assert socket.gethostname()==HOST and os.getuid()==1000,'container identity'
out=Path(OUT);assert out.is_dir() and not any(p.is_symlink() for p in (out,*out.parents)),'output path'
def read(name):
 p=out/name
 if not p.exists():return None
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=1048576,'text budget '+name
 return p.read_text()
code=read('exit_code.txt');failure=read('failure.json');completed=read('inference_complete.json');completion=read('completion.json')
p=out/'inference_manifest.jsonl';count=0;last=None
if p.exists():
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=1048576,'inference manifest budget'
 rows=p.read_text().splitlines();count=len(rows)
 if rows:last=json.loads(rows[-1])
resources=None;p=out/'resources.jsonl'
if p.exists():
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=4194304,'resource log budget'
 lines=p.read_text().splitlines()
 if lines:resources=json.loads(lines[-1])
tail='';p=out/'launch.log'
if p.exists():
 assert not p.is_symlink() and p.stat().st_size<=1048576,'launch log budget'
 tail='\n'.join(p.read_text(errors='replace').splitlines()[-18:])
alive=subprocess.run(['/usr/bin/tmux','has-session','-t',SESSION],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5).returncode==0
print(json.dumps(dict(status='READONLY_STARTUP_OBSERVATION',hostname=socket.gethostname(),session_alive=alive,exit_code=code.strip() if code else None,prediction_records=count,last_prediction=last,last_resources=resources,failure=json.loads(failure) if failure else None,inference_complete=json.loads(completed) if completed else None,completion=json.loads(completion) if completion else None,launch_log_tail=tail,server_writes=0,forward_calls_from_observer=0,formal_freeze_audit=False)))
