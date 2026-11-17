from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_cuda_pending_20261116_v2.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='ac9dbd1007db1ec5d3824684361ce55691bb36aaa41b8f484b5b9b4f37a6a5e4'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_CUDA_execution_request_v1.json').read();assert hashlib.sha256(qraw).hexdigest()=='00a69c5cc3d42e04f4caa3c21650dd58db5d8c1b446741a1b42caf6730213d0f'
q=json.loads(qraw);mapping=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(mapping['remote_root'])
def exact(r):
 v=Path(r['path']);assert not any(x.is_symlink() for x in (v,*v.parents));assert v.stat().st_size==r['bytes'] and hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256'],str(v)
import importlib.util,subprocess
for r in mapping['files']:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
assert not Path(q['output']).exists();L=q['launch_contract'];control=Path(L['authorization_path']).parent;assert not control.exists()
sp=importlib.util.spec_from_file_location('authorized_spcg_entry',q['entry']['path']);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
qh=hashlib.sha256(qraw).hexdigest();ab,rb=e.materialization(q,qh,'User authorized this exact request and11forward/3loss/3backward/0step in chat2026-11-16')
script=e.render_launcher(q,qh,hashlib.sha256(ab).hexdigest(),hashlib.sha256(rb).hexdigest()).encode()
control.mkdir(mode=0o700)
for name,b in [(L['authorization_path'],ab),(L['runtime_path'],rb),(L['launcher_path'],script)]:
 with Path(name).open('xb') as f:f.write(b)
with Path(L['launch_attempt_path']).open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh),f)
v=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'/bin/bash',L['launcher_path']],capture_output=True,timeout=10)
print(json.dumps(dict(status='SINGLE_TMUX_ATTEMPT',returncode=v.returncode,stderr=v.stderr.decode(errors='replace'),session=L['tmux_session'],output=q['output'])))
assert v.returncode==0
