from pathlib import Path
import subprocess,json,base64,zlib
V=Path(__file__).resolve().parent;O=V/'authorized_execution_v1';n=len(list(O.glob('status_*_stdout.bin')))+1
code="""from pathlib import Path
import json,os,socket,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
o=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_sixmodel_native_development_20261117_v1');r=dict(files=sorted(x.name for x in o.iterdir()))
for name in ['worker.pid','exit_code.txt','failure.json','error_traceback.json']:
 p=o/name
 if p.is_file():r[name]=p.read_text()[-10000:]
for name in ['inference_manifest.jsonl','forward_attempts.jsonl','resources.jsonl']:
 p=o/name
 if p.is_file():
  with p.open('rb') as f:lines=f.read().splitlines()
  r[name]=dict(records=len(lines),last=json.loads(lines[-1]) if lines else None)
if (o/'predictions').is_dir():r['prediction_files']=len(list((o/'predictions').glob('*.npz')))
if (o/'completion.json').is_file():
 c=json.loads((o/'completion.json').read_text());r['completion']=dict(status=c.get('status'),forwards=c.get('forwards'),request_sha256=c.get('request_sha256'),archive={k:v for k,v in c.get('archive',{}).items() if k in ['path','bytes','sha256']})
if (o/'inference_complete.json').is_file():
 c=json.loads((o/'inference_complete.json').read_text());r['inference_complete']=dict(status=c['status'],forwards=c['forwards'],models=[dict(run=x['run'],forwards=x['forwards'],state_equal=x['state_before']==x['state_after'],RNG_equal=x['RNG_before']==x['RNG_after']) for x in c['models']])
if (o/'launch.log').is_file():
 with (o/'launch.log').open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-2500));r['log_tail']=f.read().decode(errors='replace')
r['tmux_live']=subprocess.run(['tmux','has-session','-t','SPCG_sixmodel_native_development_20261117_v1'],capture_output=True,timeout=5).returncode==0
print(json.dumps(r))
"""
compile(code,'status_native630','exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','20','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(args).encode())<=2048
r=subprocess.run(args,capture_output=True,timeout=25);(O/('status_%02d_stdout.bin'%n)).write_bytes(r.stdout);(O/('status_%02d_stderr.bin'%n)).write_bytes(r.stderr);assert r.returncode==0
d=json.loads(r.stdout);(O/('status_%02d_result.json'%n)).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(d))
