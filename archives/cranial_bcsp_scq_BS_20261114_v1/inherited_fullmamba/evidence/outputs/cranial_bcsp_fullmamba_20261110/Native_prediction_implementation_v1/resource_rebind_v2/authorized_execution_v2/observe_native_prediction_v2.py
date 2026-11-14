"""Bounded read-only observation, not a formal freeze audit."""
import base64,json,shlex,subprocess,sys,zlib
from pathlib import Path
A=Path(__file__).resolve().parent;label=sys.argv[1];assert label.isidentifier()
code=r'''
import pathlib,json,os,socket,subprocess
P=pathlib.Path;out=P('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_development_20261111_v2')
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
assert not any(p.is_symlink() for p in (out,*out.parents))
r=dict(hostname=socket.gethostname(),tmux_present=subprocess.run(['tmux','has-session','-t','bcsp_f0_CD_native_eval_20261111_v2'],capture_output=True,timeout=5).returncode==0,files=[p.name for p in out.iterdir()] if out.exists() else [],predictions=len(list((out/'predictions').glob('*.npz'))),contexts=len(list((out/'context').glob('*.npz'))),traces=len(list((out/'traces').glob('*.npz'))))
for n in ['exit_code.txt','failure.json','worker.pid','launch.log']:
 p=out/n
 if p.is_file():
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-7000));r[n]=f.read().decode('utf-8',errors='replace')
for n in ['forward_attempts.jsonl','inference_manifest.jsonl','resources.jsonl']:
 p=out/n
 if p.is_file():
  with p.open('rb') as f:
   lines=f.read().splitlines();r[n+'_count']=len(lines)
   if lines:r[n+'_last']=json.loads(lines[-1])
for n in ['completion.json','inference_complete.json']:
 p=out/n
 if p.is_file():
  j=json.loads(p.read_bytes());r[n]={k:j[k] for k in ('status','forwards','context_cases','trace_cases','request_sha256') if k in j}
if r.get('worker.pid'):r['worker_live']=P('/proc/'+r['worker.pid'].strip()).exists()
print(json.dumps(r))
'''
payload=base64.b64encode(zlib.compress(code.encode(),9)).decode();wrapper='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(payload)+')),"<observe-only>","exec"))'
command=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',wrapper]);assert len(command.encode())<=2048
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','15','--',command],capture_output=True,timeout=25)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (A/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
if r.returncode:print(json.dumps(dict(returncode=r.returncode)));sys.exit(1)
v=json.loads(r.stdout)
with (A/(label+'_result.json')).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
print(json.dumps(v,ensure_ascii=True))
