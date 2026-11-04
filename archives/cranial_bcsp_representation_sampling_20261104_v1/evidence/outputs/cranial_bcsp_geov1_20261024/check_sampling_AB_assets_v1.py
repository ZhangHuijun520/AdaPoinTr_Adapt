"""One reuse of the historical exact30 asset check, rebound to confirmed host."""
from pathlib import Path
import base64,hashlib,json,re,shlex,subprocess
B=Path(__file__).resolve().parent
O=B/'sampling_model_AB_foldC_seed0_20261103_v1'
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1/selected_assets_probe_v1.py'
source=P.read_bytes().replace(b'shu-common-25721452-notebook-01dt08-0',b'shu-common-25721452-notebook-v2iwsa-0')
assert b'01dt08-0' not in source
command='/usr/bin/timeout --signal=TERM --kill-after=2s 35s /opt/conda/bin/python -I -S -B -c '+shlex.quote(source.decode('ascii'))
assert len(command.encode())<=2048
with (O/'server_assets_scope_v1.json').open('x') as f:json.dump({'source_sha256':hashlib.sha256(source).hexdigest(),'command_bytes':len(command.encode()),'scope':'historical exact30 model/provider/config/training assets, <=20MB <=35sec; no payload/model import','no_retry':True,'server_writes':0},f,indent=2)
try:
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--',command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=55)
 code=p.returncode;out=p.stdout;err=p.stderr;timed=False
except subprocess.TimeoutExpired as e:code=None;out=e.stdout or b'';err=e.stderr or b'';timed=True
stderr=re.sub(r'(?i)(bearer\s+|token[=:]\s*)\S+',r'\1[REDACTED]',err.decode('utf-8',errors='replace'))
with (O/'server_assets_capture_v1.json').open('x') as f:json.dump({'returncode':code,'timeout':timed,'stdout_base64':base64.b64encode(out).decode(),'stderr_redacted':stderr},f,indent=2)
print(json.dumps({'returncode':code,'timeout':timed}))
if code!=0:raise SystemExit(1)
v=json.loads(out.decode('utf-8'))
with (O/'server_assets_observation_v1.json').open('x') as f:json.dump(v,f,indent=2)
print(json.dumps({'status':v['status'],'assets':len(v['assets']),'hashed_bytes':v['hashed_bytes']}))
