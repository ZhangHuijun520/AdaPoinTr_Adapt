"""Read only this run's status. No checkpoint read or formal freeze audit."""
import datetime,json,shlex,subprocess
from pathlib import Path
S=Path(__file__).resolve().parent
q=json.loads((S/'first_FoldC_request_v1/transport_payload/H2_AUX_foldC_seed0_training_execution_request_v1.json').read_bytes())
O=S/'status_checks';O.mkdir(exist_ok=True);stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
code="import pathlib,json,socket,os,subprocess; from collections import deque; assert socket.gethostname()=="+repr(q['identity']['hostname'])+" and os.getuid()==1000; p=pathlib.Path("+repr(q['output'])+"); d={'hostname':socket.gethostname()}; d['files']={f.name:f.stat().st_size for f in p.iterdir() if f.is_file()}; d['exit_code']=(p/'exit_code.txt').read_text().strip() if (p/'exit_code.txt').exists() else None; pid=(p/'worker.pid').read_text().strip() if (p/'worker.pid').exists() else None; d['worker_PID']=pid; d['worker_present']=bool(pid and pathlib.Path('/proc/'+pid).exists()); d['tmux_present']=subprocess.run(['tmux','has-session','-t',"+repr(q['launch_contract']['tmux_session'])+"],capture_output=True).returncode==0; d['completion']=json.loads((p/'completion.json').read_bytes()) if (p/'completion.json').exists() else None; d['failure']=json.loads((p/'failure.json').read_bytes()) if (p/'failure.json').exists() else None; m=p/'metrics.jsonl'; rows=deque(m.open(),maxlen=1) if m.exists() else []; d['last_metric']=json.loads(rows[-1]) if rows else None; d['log_tail']=(p/'launch.log').read_text(errors='replace')[-3000:]; print(json.dumps(d))"
cmd=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c',code]);assert len(cmd.encode())<=2048
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','20','--',cmd],capture_output=True,timeout=30)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (O/(stamp+'_'+k+'.bin')).open('xb') as f:f.write(b)
assert r.returncode==0,('status transport failed',r.returncode,r.stderr[:512])
d=json.loads(r.stdout);d['local_observation_time']=stamp
with (O/(stamp+'_status.json')).open('x',encoding='utf-8') as f:json.dump(d,f,indent=2)
last=d['last_metric'] or {};print(json.dumps(dict(hostname=d['hostname'],exit_code=d['exit_code'],worker_present=d['worker_present'],tmux_present=d['tmux_present'],last_step=last.get('step'),H2_mode=last.get('H2_mode'),completion=d['completion'],failure=d['failure'],files=d['files'],log_tail=d['log_tail']),ensure_ascii=True))
