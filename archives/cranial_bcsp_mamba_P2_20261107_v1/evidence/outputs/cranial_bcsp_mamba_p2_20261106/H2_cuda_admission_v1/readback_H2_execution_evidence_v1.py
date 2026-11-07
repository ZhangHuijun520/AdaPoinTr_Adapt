"""Read back authorized run evidence; completion observation, not formal freeze audit."""
import hashlib,json,subprocess
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;A=S/'authorized_execution_v1';D=A/'readback';D.mkdir();q=json.loads((S/'H2_artificial_cuda_execution_request_v1.json').read_text());L=q['launch_contract'];control=PurePosixPath(L['authorization_path']).parent;out=PurePosixPath(q['output'])
sources=[PurePosixPath(L[k]) for k in ['authorization_path','runtime_path','launcher_path']]+[control/n for n in ['readiness_and_installation_receipt_v1.json','startup_receipt_v1.json']]+[out/n for n in ['completion.json','AUX_result.json','COUPLE_result.json','resources.jsonl','attempts.jsonl','payload_manifest.json','exit_code.txt','launch.log']]
files=[]
for source in sources:
 target=D/source.name;assert not target.exists()
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','get',str(source),p.stdout.decode().strip()],capture_output=True,timeout=30)
 for name,blob in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (D/(source.name+'.get_'+name+'.bin')).open('xb') as f:f.write(blob)
 if r.returncode:raise RuntimeError('readback failure '+str(source))
 files.append(dict(path=str(target),server_path=str(source),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
def read(name):return json.loads((D/name).read_bytes())
def sha(name):return hashlib.sha256((D/name).read_bytes()).hexdigest()
startup=read('startup_receipt_v1.json');auth=read('authorization_v1.json');runtime=read('runtime_v1.json');done=read('completion.json');qh=hashlib.sha256((S/'H2_artificial_cuda_execution_request_v1.json').read_bytes()).hexdigest()
assert startup['request_sha256']==auth['request_sha256']==runtime['request_sha256']==done['request_sha256']==qh
assert sha('authorization_v1.json')==startup['authorization_sha256']==runtime['authorization_sha256'];assert sha('runtime_v1.json')==startup['runtime_sha256'];assert sha('launch_once_v1.sh')==startup['launcher_sha256']
assert (D/'exit_code.txt').read_text().strip()=='0' and done['counts']==dict(forward_attempts=2,forward_returns=2,loss_calls=2,backward_attempts=2,backward_returns=2,optimizer_steps=0)
report=dict(status='H2_CUDA_EXECUTION_EXIT0_PENDING_FORMAL_FREEZE_AUDIT',request_sha256=qh,counts=done['counts'],weight_BN_RNG_equal_recorded=done['weight_BN_RNG_equal'],real_data_reads=done['real_data_reads'],checkpoint_loads=done['checkpoint_loads'],training_executed=done['training_executed'],BNCal=done['BNCal'],startup_controls_one_way_hash_verified=True,files=files,formal_post_execution_audit=False,automatic_retry=False)
with (A/'completion_observation_and_readback_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='files'}))
