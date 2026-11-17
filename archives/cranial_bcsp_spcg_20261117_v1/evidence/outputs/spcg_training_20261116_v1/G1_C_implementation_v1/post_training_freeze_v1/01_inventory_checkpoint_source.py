from pathlib import Path
import json,hashlib,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G1C_training_20261116_v1');qp=r/'SPCG_G1_C_training_execution_request_v1.json';qb=qp.read_bytes();assert hashlib.sha256(qb).hexdigest()=='2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4';q=json.loads(qb);o=Path(q['output'])
def read(p):return json.loads(p.read_text())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<600*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(t.st_size,t.st_mtime_ns,t.st_ino);return dict(bytes=s.st_size,sha256=h.hexdigest())
import subprocess
files={p.name:record(p) for p in o.iterdir() if p.is_file()};dirs={p.name:list(p.iterdir()) for p in o.iterdir() if p.is_dir()};assert all(not v for v in dirs.values())
manifest=read(o/'payload_manifest.json')['files'];checks=dict(manifest_unique=len(manifest)==len({x['name'] for x in manifest}),manifest_hashes=all(files[x['name']]==dict(bytes=x['bytes'],sha256=x['sha256']) for x in manifest),manifest_scope={x['name'] for x in manifest}==set(files)-{'launch.log','worker.pid','exit_code.txt','payload_manifest.json'},exit_zero=(o/'exit_code.txt').read_text()=='0\n',worker_absent=not Path('/proc/'+(o/'worker.pid').read_text().strip()).exists())
checks['tmux_absent']=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
c=read(o/'completion.json');checks['checkpoint_hash']=files['ckpt-last.pth']['sha256']==c['checkpoint_sha256'];print(json.dumps(dict(files=files,directories=list(dirs),checks=checks,completion=c)))
