import base64,hashlib,json,subprocess,time
from pathlib import Path
N=Path(__file__).resolve().parent
scope=N/'reference_preparation_scope_v2.json'
with (N/'reference_build_attempt_v2.json').open('x') as f:json.dump(dict(scope_sha256=hashlib.sha256(scope.read_bytes()).hexdigest(),single_attempt=True,model_calls=0),f)
start=time.time()
try:
 r=subprocess.run([r'C:\Users\zhj\.conda\envs\adapointr\python.exe','-I','-B',str(N/'build_reference_bank_v2.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3610)
 cap=dict(returncode=r.returncode,stdout_base64=base64.b64encode(r.stdout).decode(),stderr_base64=base64.b64encode(r.stderr).decode(),timeout=False)
except subprocess.TimeoutExpired as e:
 cap=dict(returncode=None,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode(),timeout=True)
cap['elapsed_seconds']=time.time()-start
with (N/'reference_build_capture_v2.json').open('x') as f:json.dump(cap,f,indent=2)
print(base64.b64decode(cap['stdout_base64']).decode(errors='replace'))
print(base64.b64decode(cap['stderr_base64']).decode(errors='replace'))
raise SystemExit(0 if cap['returncode']==0 and not cap['timeout'] else 1)
