import datetime,json,shlex,subprocess
from pathlib import Path
S=Path(__file__).resolve().parent;O=S/'status_checks';O.mkdir(exist_ok=True);stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');q=json.loads((S/'pending_request_v1/transport_payload/H2_C_D_fourmodel_native_prediction_execution_request_v1.json').read_bytes())
code="import pathlib,json,socket,os,subprocess; p=pathlib.Path(OUTPUT); assert socket.gethostname()==HOST and os.getuid()==1000; d={}; d['exit_code']=(p/'exit_code.txt').read_text().strip() if (p/'exit_code.txt').exists() else None; pid=(p/'worker.pid').read_text().strip() if (p/'worker.pid').exists() else None; d['worker_present']=bool(pid and pathlib.Path('/proc/'+pid).exists()); d['tmux_present']=subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==0; d['predictions']=len(list((p/'predictions').glob('*.npz'))); d['failure']=json.loads((p/'failure.json').read_bytes()) if (p/'failure.json').exists() else None; c=json.loads((p/'completion.json').read_bytes()) if (p/'completion.json').exists() else {}; d['completion']={k:v for k,v in c.items() if k!='archive'}; d['archive']={k:v for k,v in c.get('archive',{}).items() if k!='members'}; d['archive_members']=len(c.get('archive',{}).get('members',[])); print(json.dumps(d))"
code=code.replace('OUTPUT',repr(q['output'])).replace('HOST',repr(q['identity']['hostname'])).replace('SESSION',repr(q['launch_contract']['tmux_session']))
cmd=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c',code]);assert len(cmd.encode())<=2048
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','20','--',cmd],capture_output=True,timeout=30)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (O/(stamp+'_'+k+'.bin')).open('xb') as f:f.write(b)
assert r.returncode==0,(r.returncode,r.stderr[:512]);d=json.loads(r.stdout)
with (O/(stamp+'_status.json')).open('x',encoding='utf-8') as f:json.dump(d,f,indent=2)
print(json.dumps(d))
