from pathlib import Path
import json,subprocess,base64,zlib
S=Path(__file__).resolve().parent;O=S/'authorized_execution_v1';n=len(list(O.glob('status_*_stdout.bin')))+1
code="""from pathlib import Path
import json,subprocess
p=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G0_foldD_seed0_train_20261116_v1');r=dict(files=sorted(x.name for x in p.iterdir()))
for name in ['worker.pid','exit_code.txt','failure.json','startup_failure.json','startup_monitor_failure.json','completion.json']:
 if (p/name).is_file():r[name]=(p/name).read_text()[-7000:]
for name in ['metrics.jsonl','resources.jsonl']:
 if (p/name).is_file():
  with (p/name).open('rb') as f:
   f.seek(0,2);size=f.tell();f.seek(max(0,size-16384));lines=f.read().decode(errors='replace').splitlines();r[name+'_last']=lines[-1:]
if (p/'launch.log').is_file():
 with (p/'launch.log').open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-8000));r['log_tail']=f.read().decode(errors='replace')
r['tmux_live']=subprocess.run(['tmux','has-session','-t','SPCG_G0_foldD_seed0_train_20261116_v1'],capture_output=True,timeout=5).returncode==0
print(json.dumps(r))
"""
b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',c],capture_output=True,timeout=30)
(O/('status_%02d_stdout.bin'%n)).write_bytes(r.stdout);(O/('status_%02d_stderr.bin'%n)).write_bytes(r.stderr);assert r.returncode==0
d=json.loads(r.stdout);(O/('status_%02d_result.json'%n)).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(d,ensure_ascii=False))
