import json,socket,subprocess
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0'
p=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/FoldC_T0_M0_development_20261106_v2')
def read(name):
 f=p/name
 return f.read_text(errors='replace') if f.is_file() else None
def compact_completion(text):
 if not text:return None
 d=json.loads(text);a=d.get('archive',{})
 return dict(status=d.get('status'),forwards=d.get('forwards'),archive={k:a.get(k) for k in ['path','bytes','sha256']},members=len(a.get('members',[])))
manifest=read('inference_manifest.jsonl');attempt=read('forward_attempts.jsonl');resources=read('resources.jsonl')
print(json.dumps(dict(session_present=subprocess.run(['tmux','has-session','-t','bcsp_p1_C_T0_M0_eval_20261106_v2'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,pid=read('worker.pid'),exit_code=read('exit_code.txt'),successful_predictions=len(manifest.splitlines()) if manifest else 0,forward_attempts=len(attempt.splitlines()) if attempt else 0,last_resource=json.loads(resources.splitlines()[-1]) if resources else None,failure=read('failure.json'),completion=compact_completion(read('completion.json')),log_tail=(read('launch.log') or '')[-6000:])))
