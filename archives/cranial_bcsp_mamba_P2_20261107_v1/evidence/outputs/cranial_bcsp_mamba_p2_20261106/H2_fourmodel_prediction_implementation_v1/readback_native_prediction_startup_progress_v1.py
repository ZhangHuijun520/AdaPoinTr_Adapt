"""Read startup controls and current progress only; never launch/retry."""
import hashlib,json,shlex,subprocess
from pathlib import Path
S=Path(__file__).resolve().parent;A=S/'authorized_execution_v1';D=A/'readback';D.mkdir()
QH='b95b866a6b3a0eaeb1e840e003ecd426847ed47b07675b6c1f7644b5aee97170'
q=json.loads((S/'pending_request_v1/transport_payload/H2_C_D_fourmodel_native_prediction_execution_request_v1.json').read_bytes());L=q['launch_contract'];root=str(Path(L['authorization']).parent).replace('\\','/')
# Linux path rendering must never use the Windows Path parent semantics.
from pathlib import PurePosixPath
root=str(PurePosixPath(L['authorization']).parent)
B=['wsl.exe','-d','Ubuntu-20.04','--exec'];C='/home/zhj/.local/bin/hpc5000'
names=['native_prediction_authorization_v1.json','native_prediction_runtime_v1.json','native_prediction_launch_once_v1.sh','readiness_and_installation_receipt_v1.json','prelaunch_authorization_contract_v1.json','native_prediction_single_attempt_claim_v1.json','startup_receipt_v1.json']
for name in names:
 target=D/name;p=subprocess.run(B+['wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0
 r=subprocess.run(B+[C,'get',root+'/'+name,p.stdout.decode().strip()],capture_output=True,timeout=25)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (A/('get_'+name+'_'+k+'.bin')).open('xb') as f:f.write(b)
 assert r.returncode==0,name
receipt=json.loads((D/'startup_receipt_v1.json').read_bytes());assert receipt['request_sha256']==QH
for name,key in [('native_prediction_authorization_v1.json','authorization_sha256'),('native_prediction_runtime_v1.json','runtime_sha256'),('native_prediction_launch_once_v1.sh','launcher_sha256')]:assert hashlib.sha256((D/name).read_bytes()).hexdigest()==receipt[key]
code="import pathlib,json; p=pathlib.Path(OUTPUT); d={'output':str(p)}; d['files']=[{'name':f.name,'bytes':f.stat().st_size} for f in p.iterdir() if f.is_file()]; d['exit_code']=(p/'exit_code.txt').read_text().strip() if (p/'exit_code.txt').exists() else None; pid=(p/'worker.pid').read_text().strip() if (p/'worker.pid').exists() else None; d['worker_PID']=pid; d['worker_present']=bool(pid and pathlib.Path('/proc/'+pid).exists()); m=p/'inference_manifest.jsonl'; rows=m.read_text().splitlines() if m.exists() else []; d['metric_records']=len(rows); d['last_metric']=json.loads(rows[-1]) if rows else None; d['prediction_files']=len(list((p/'predictions').glob('*.npz'))) if (p/'predictions').exists() else 0; d['failure']=json.loads((p/'failure.json').read_bytes()) if (p/'failure.json').exists() else None; d['log_tail']=(p/'launch.log').read_text(errors='replace')[-5000:]; print(json.dumps(d))".replace('OUTPUT',repr(q['output']))
cmd=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c',code]);assert len(cmd.encode())<2048
r=subprocess.run(B+[C,'exec','--timeout','20','--',cmd],capture_output=True,timeout=30)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (A/('startup_progress_'+k+'.bin')).open('xb') as f:f.write(b)
assert r.returncode==0
d=json.loads(r.stdout);d['request_sha256']=QH
with (A/'startup_progress_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(d,f,indent=2)
print(json.dumps(dict(worker_PID=d['worker_PID'],worker_present=d['worker_present'],successful_prediction_records=d['metric_records'],prediction_files=d['prediction_files'],last_run=(d['last_metric'] or {}).get('run'),last_forward_index=(d['last_metric'] or {}).get('forward_index'),exit_code=d['exit_code'],failure=d['failure'],log_tail=d['log_tail']),ensure_ascii=True))
