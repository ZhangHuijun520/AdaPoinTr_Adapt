from pathlib import Path
import json,base64,zlib,subprocess
V=Path(__file__).resolve().parent;O=V/'authorized_execution_v3';index=len(list(O.glob('status_*_result.json')))+1
code="""from pathlib import Path
import json,subprocess
p=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G0_G1_G2_CUDA_20261116_v3');r=dict(files=sorted(x.name for x in p.iterdir()))
for name in ['worker.pid','exit_code.txt','startup_failure.json','startup_query_result.json','failure.json','monitor_failure.json']:
 if (p/name).is_file():r[name]=(p/name).read_text()[-12000:]
if (p/'completion.json').is_file():
 c=json.loads((p/'completion.json').read_text());r['completion']=dict(status=c['status'],counts=c['result']['counts'],native_SSM_calls=sum(c['native_calls'].values()),models={k:dict(construction=v['construction'],estimate=v['estimate']) for k,v in c['result']['models'].items()})
if (p/'events.jsonl').is_file():r['events_tail']=(p/'events.jsonl').read_text().splitlines()[-2:]
if (p/'launch.log').is_file():r['launch_tail']=(p/'launch.log').read_text()[-6000:]
r['tmux_live']=subprocess.run(['tmux','has-session','-t','SPCG_G0_G1_G2_CUDA_20261116_v3'],capture_output=True,timeout=5).returncode==0
print(json.dumps(r))
"""
b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',c],capture_output=True,timeout=30)
(O/('status_%02d_stdout.bin'%index)).write_bytes(p.stdout);(O/('status_%02d_stderr.bin'%index)).write_bytes(p.stderr);assert p.returncode==0
r=json.loads(p.stdout);(O/('status_%02d_result.json'%index)).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))
