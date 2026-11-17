from pathlib import Path
import json,subprocess,base64,zlib
V=Path(__file__).resolve().parent;O=V/'authorized_execution_v1'
code="""from pathlib import Path
import os,json,socket,time
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
o=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G0_foldD_seed0_train_20261116_v1');pid=(o/'worker.pid').read_text().strip();assert pid=='52545';p=Path('/proc')/pid;r=dict(hostname=socket.gethostname(),utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),pid=pid,proc_exists=p.exists(),files={})
for name in ['status','wchan','io','stat']:
 if (p/name).is_file():r[name]=(p/name).read_text()[:6000]
for name in ['ckpt-last.pth','completion.json','exit_code.txt','failure.json','startup_failure.json','training_error_traceback.json']:
 f=o/name
 if f.exists():
  assert not f.is_symlink();s=f.stat();r['files'][name]=dict(bytes=s.st_size,mtime=s.st_mtime)
  if name.endswith('.json') or name=='exit_code.txt':r['files'][name]['text']=f.read_text()[:5000]
s=os.statvfs(o);r['free_bytes']=s.f_bavail*s.f_frsize
print(json.dumps(r))
"""
compile(code,'finalization_status','exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))"
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','20','--','/usr/bin/python3','-I','-S','-B','-c',c],capture_output=True,timeout=25)
(O/'finalization_20261117_v1_stdout.bin').write_bytes(r.stdout);(O/'finalization_20261117_v1_stderr.bin').write_bytes(r.stderr);assert r.returncode==0
d=json.loads(r.stdout);(O/'finalization_20261117_v1_result.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(d))
