import base64,json,shlex,subprocess,sys,zlib
from pathlib import Path
A=Path(__file__).resolve().parent;label=sys.argv[1];assert label.isidentifier()
CODE=r'''
import pathlib,json,os,socket,subprocess
P=pathlib.Path;out=P('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1')
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000 and not any(x.is_symlink() for x in (out,*out.parents))
r=dict(hostname=socket.gethostname(),session_present=subprocess.run(['tmux','has-session','-t','bcsp_lqi_cuda_20261111_v1'],capture_output=True,timeout=5).returncode==0,files=[p.name for p in out.iterdir()])
for name in ['exit_code.txt','worker.pid','failure.json','monitor_failure.json','launch.log']:
 p=out/name
 if p.is_file():
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-5000));r[name]=f.read().decode('utf-8',errors='replace')
for name in ['events.jsonl','resources.jsonl']:
 p=out/name
 if p.is_file():
  data=[json.loads(x) for x in p.read_text().splitlines()];r[name+'_count']=len(data)
  if data:r[name+'_last']=data[-1] if name=='resources.jsonl' else {k:v for k,v in data[-1].items() if k in ('kind','operation','counts','phase','batch','loss','state_restored','RNG_restored','modes_restored')}
  if name=='events.jsonl':r['phases']=[dict(phase=x['phase'],batch=x['batch'],loss=x['loss']) for x in data if 'phase' in x and 'loss' in x]
p=out/'completion.json'
if p.is_file():
 c=json.loads(p.read_bytes());r['completion']={k:v for k,v in c.items() if k not in ('native_SSM_calls','dispatch_observations')};r['native_SSM_total']=sum(c['native_SSM_calls'].values())
if r.get('worker.pid'):r['worker_live']=P('/proc/'+r['worker.pid'].strip()).exists()
print(json.dumps(r))
'''
blob=base64.b64encode(zlib.compress(CODE.encode(),9)).decode();wrapper='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(blob)+')),"<lqi-observe>","exec"))'
cmd=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',wrapper]);assert len(cmd.encode())<=2048
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','20','--',cmd],capture_output=True,timeout=30)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (A/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
assert r.returncode==0,(r.returncode,r.stdout[-1500:]);v=json.loads(r.stdout)
with (A/(label+'_result.json')).open('x') as f:json.dump(v,f,indent=2)
print(json.dumps(v))
