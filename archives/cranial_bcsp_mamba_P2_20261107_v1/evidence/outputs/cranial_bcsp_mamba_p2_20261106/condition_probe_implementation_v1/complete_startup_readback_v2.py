"""Finish two POSIX-path receipt downloads; reuse three verified existing controls."""
import hashlib,json,subprocess
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;A=S/'authorized_execution_v1';q=json.loads((S/'condition_probe_execution_request_v1.json').read_text());L=q['launch_contract']
for name in ['readiness_and_installation_receipt_v1.json','startup_receipt_v1.json']:
 source=str(PurePosixPath(L['authorization_path']).parent/name);target=A/name
 if target.exists():raise RuntimeError('readback target exists')
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0;dest=p.stdout.decode().strip()
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','get',source,dest],capture_output=True,timeout=30)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (A/(name+'.v2_get_'+k+'.bin')).open('xb') as f:f.write(b)
 if r.returncode:raise RuntimeError('readback failed '+source)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
startup=json.loads((A/'startup_receipt_v1.json').read_bytes());auth=json.loads((A/'authorization_v1.json').read_bytes());runtime=json.loads((A/'runtime_v1.json').read_bytes());install=json.loads((A/'readiness_and_installation_receipt_v1.json').read_bytes())
assert auth['request_sha256']==runtime['request_sha256']==startup['request_sha256']==sha(S/'condition_probe_execution_request_v1.json')
assert sha(A/'authorization_v1.json')==startup['authorization_sha256']==runtime['authorization_sha256'];assert sha(A/'runtime_v1.json')==startup['runtime_sha256'];assert sha(A/'launch_once_v1.sh')==startup['launcher_sha256'];assert install['status']=='EXCLUSIVE_INSTALL_HASHES_PASS'
report=dict(status='STARTUP_CONTROLS_READBACK_COMPLETED_PASS',request_sha256=startup['request_sha256'],prior_local_readback_error='Windows Path constructed backslash server paths for two remaining downloads; no effect on running worker; retained original logs',controls_hash_bindings=True,unique_cases=install['unique_cases'],exact_unique_point_paths=install['exact_unique_point_paths'],post_experiment_audit=False,server_mutations=0,files=[dict(path=str(A/n),bytes=(A/n).stat().st_size,sha256=sha(A/n)) for n in ['authorization_v1.json','runtime_v1.json','launch_once_v1.sh','readiness_and_installation_receipt_v1.json','startup_receipt_v1.json']])
with (A/'startup_control_readback_receipt_v2.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='files'}))
