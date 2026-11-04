"""One bounded read-only current-container probe; no uploads, imports or GPU context."""
from pathlib import Path
import base64,hashlib,json,re,shlex,subprocess,sys
B=Path(__file__).resolve().parent/'sampling_model_AB_foldC_seed0_20261103_v1'
SOURCE=b"""import os,socket,json,shutil,subprocess,sys
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');assert p.is_dir() and not p.is_symlink();os.chdir(p)
def call(v):return subprocess.check_output(v,timeout=8).decode().strip()
q='/opt/conda/envs/adapointr-mamba/bin/python'
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),project=str(Path.cwd()),disk_free=shutil.disk_usage(p).free,gpu=call(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader']),compute=call(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader']),python_exists=Path(q).is_file(),python_realpath=str(Path(q).resolve()),python_version=call([q,'--version']))))
"""
def main():
 command='/usr/bin/timeout --signal=TERM --kill-after=2s 25s /opt/conda/bin/python -I -S -B -c '+shlex.quote('import base64;exec(base64.b64decode('+repr(base64.b64encode(SOURCE).decode())+'))')
 assert len(command.encode())<=2048
 scope={'status':'READONLY_PROBE_FROZEN_BEFORE_CALL','expected_hostname':'shu-common-25721452-notebook-v2iwsa-0','source_sha256':hashlib.sha256(SOURCE).hexdigest(),'command_bytes':len(command.encode()),'server_seconds':25,'client_seconds':35,'local_seconds':45,'server_writes':0,'torch_imports_or_CUDA_context':0,'no_retry':True}
 with (B/'server_readonly_scope_v1.json').open('x') as f:json.dump(scope,f,indent=2)
 try:
  p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','35','--',command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
  stdout=p.stdout;stderr=p.stderr;code=p.returncode;timed=False
 except subprocess.TimeoutExpired as e:stdout=e.stdout or b'';stderr=e.stderr or b'';code=None;timed=True
 text=stderr.decode('utf-8',errors='replace')
 text=re.sub(r'(?i)(bearer\s+|token[=:]\s*)\S+',r'\1[REDACTED]',text)
 with (B/'server_readonly_capture_v1.json').open('x') as f:json.dump({'returncode':code,'timeout':timed,'stdout_base64':base64.b64encode(stdout).decode(),'stderr_redacted':text,'stderr_sha256':hashlib.sha256(stderr).hexdigest()},f,indent=2)
 print(json.dumps({'returncode':code,'timeout':timed,'stderr_redacted':text},ensure_ascii=True))
 if code!=0:raise SystemExit(1)
 observation=json.loads(stdout.decode('utf-8'))
 with (B/'server_readonly_observation_v1.json').open('x') as f:json.dump(observation,f,indent=2)
 print(json.dumps(observation,ensure_ascii=True))
if __name__=='__main__':main()
