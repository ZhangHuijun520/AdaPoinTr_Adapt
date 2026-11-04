from pathlib import Path
import subprocess,shlex,json,hashlib,base64,datetime
b=Path(__file__).resolve().parent
source=(b/'probe_v1.py').read_bytes()
command='/usr/bin/timeout --signal=TERM --kill-after=2s 35s /opt/conda/bin/python3.8 -I -S -B -c '+shlex.quote(source.decode('ascii'))
assert len(command.encode())<=2048
scope=dict(schema='procfs-self-readonly-scope-v1',expected_hostname='shu-common-25721452-notebook-01dt08-0',expected_uid=1000,files=['/proc/self/mountinfo','/proc/self/status'],links=['/proc/self/ns/pid','/proc/self/ns/pid_for_children','/proc/self/ns/mnt','/proc/self/ns/user'],mountinfo_max_bytes=262144,status_max_bytes=16384,max_procfs_entries=32,max_output_bytes=65536,command_bytes=len(command.encode()),probe_sha256=hashlib.sha256(source).hexdigest(),remote_timeout_seconds=35,client_timeout_seconds=45,local_timeout_seconds=55,candidate_paths_opened=0,server_writes=0,CUDA_contexts_created=0,retries=0)
with (b/'frozen_scope_v1.json').open('x',encoding='ascii') as f:json.dump(scope,f,indent=2)
with (b/'attempt_started_v1.json').open('x',encoding='ascii') as f:json.dump(dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope_sha256=hashlib.sha256((b/'frozen_scope_v1.json').read_bytes()).hexdigest()),f)
try:
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--',command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=55)
 cap=dict(returncode=p.returncode,stdout_base64=base64.b64encode(p.stdout).decode(),stderr_base64=base64.b64encode(p.stderr).decode(),timeout=False)
except subprocess.TimeoutExpired as e:
 cap=dict(returncode=None,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode(),timeout=True)
with (b/'process_capture_v1.json').open('x',encoding='ascii') as f:json.dump(cap,f,indent=2)
print(json.dumps(dict(returncode=cap['returncode'],timeout=cap['timeout'],capture_sha256=hashlib.sha256((b/'process_capture_v1.json').read_bytes()).hexdigest(),command_bytes=scope['command_bytes'])))
if cap['returncode']==0:
 d=json.loads(base64.b64decode(cap['stdout_base64']).decode('utf-8'))
 with (b/'observation_v1.json').open('x',encoding='ascii') as f:json.dump(d,f,indent=2)
 print(json.dumps(d))
