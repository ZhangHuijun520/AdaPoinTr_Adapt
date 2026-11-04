from pathlib import Path
import subprocess,shlex,json,hashlib,base64
b=Path(__file__).resolve().parent
names=['freshness']
scope=[]
for name in names:
 raw=(b/(name+'_probe_v1.py')).read_bytes()
 command='/usr/bin/timeout --signal=TERM --kill-after=2s 35s /opt/conda/bin/python3.8 -I -S -B -c '+shlex.quote(raw.decode('ascii'))
 assert len(command.encode())<=2048
 scope.append(dict(name=name,source_sha256=hashlib.sha256(raw).hexdigest(),command_bytes=len(command.encode())))
with (b/'freshness_scope_v1.json').open('x') as f:json.dump(dict(probes=scope,remote_seconds=35,client_seconds=45,local_seconds=55,no_retries=True,server_writes=0,CUDA_calls=0),f,indent=2)
for item in scope:
 name=item['name'];raw=(b/(name+'_probe_v1.py')).read_bytes()
 command='/usr/bin/timeout --signal=TERM --kill-after=2s 35s /opt/conda/bin/python3.8 -I -S -B -c '+shlex.quote(raw.decode('ascii'))
 with (b/(name+'_attempt_started.json')).open('x') as f:json.dump(item,f)
 try:
  p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--',command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=55)
  cap=dict(returncode=p.returncode,stdout_base64=base64.b64encode(p.stdout).decode(),stderr_base64=base64.b64encode(p.stderr).decode(),timeout=False)
 except subprocess.TimeoutExpired as e:
  cap=dict(returncode=None,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode(),timeout=True)
 with (b/(name+'_capture_v1.json')).open('x') as f:json.dump(cap,f,indent=2)
 print(json.dumps(dict(probe=name,returncode=cap['returncode'],timeout=cap['timeout'])),flush=True)
 if cap['returncode']!=0:raise SystemExit(1)
 d=json.loads(base64.b64decode(cap['stdout_base64']).decode())
 with (b/(name+'_observation_v1.json')).open('x') as f:json.dump(d,f,indent=2)
 print(json.dumps(d),flush=True)
