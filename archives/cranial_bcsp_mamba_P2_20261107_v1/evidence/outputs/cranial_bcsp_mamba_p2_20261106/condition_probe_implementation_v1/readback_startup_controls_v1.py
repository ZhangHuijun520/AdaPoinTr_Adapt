"""Read back frozen controls/installation receipt; not a post-experiment audit."""
import subprocess,json,hashlib
from pathlib import Path
S=Path(__file__).resolve().parent;A=S/'authorized_execution_v1';q=json.loads((S/'condition_probe_execution_request_v1.json').read_text());L=q['launch_contract'];paths=[L[k] for k in ['authorization_path','runtime_path','launcher_path']]+[str(Path(L['authorization_path']).parent/n) for n in ['readiness_and_installation_receipt_v1.json','startup_receipt_v1.json']]
records=[]
for source in paths:
 target=A/Path(source).name
 if target.exists():raise RuntimeError('readback target exists')
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0;dest=p.stdout.decode().strip()
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','get',source,dest],capture_output=True,timeout=30)
 for kind,blob in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (A/(Path(source).name+'.get_'+kind+'.bin')).open('xb') as f:f.write(blob)
 if r.returncode:raise RuntimeError('readback failed '+source)
 b=target.read_bytes();records.append(dict(path=str(target),server_path=source,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
startup=json.loads((A/'startup_receipt_v1.json').read_bytes());auth=json.loads((A/'authorization_v1.json').read_bytes());runtime=json.loads((A/'runtime_v1.json').read_bytes());byname={Path(r['path']).name:r for r in records}
assert auth['request_sha256']==runtime['request_sha256']==startup['request_sha256']==hashlib.sha256((S/'condition_probe_execution_request_v1.json').read_bytes()).hexdigest()
assert byname['authorization_v1.json']['sha256']==startup['authorization_sha256']==runtime['authorization_sha256']
assert byname['runtime_v1.json']['sha256']==startup['runtime_sha256'] and byname['launch_once_v1.sh']['sha256']==startup['launcher_sha256']
installation=json.loads((A/'readiness_and_installation_receipt_v1.json').read_bytes());assert installation['status']=='EXCLUSIVE_INSTALL_HASHES_PASS'
report=dict(status='STARTUP_CONTROLS_AND_INSTALL_RECEIPT_READBACK_PASS',files=records,unique_cases=installation['unique_cases'],exact_unique_point_paths=installation['exact_unique_point_paths'],model_prefix_success_not_asserted=True,post_experiment_freeze_audit=False)
with (A/'startup_control_readback_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(status=report['status'],files=len(records),unique_cases=report['unique_cases'],exact_unique_point_paths=report['exact_unique_point_paths'])))
