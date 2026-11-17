from pathlib import Path
import os,socket,json,hashlib,tarfile
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
a=Path('/home/jovyan/bcsp_spcg_sixmodel_native_pending_20261117_v1.tar.gz');assert not a.is_symlink() and hashlib.sha256(a.read_bytes()).hexdigest()=='90182af9e43ee2053831f6bc9d52dcf8bf5bc978ac7b4231fc01e26a86fed5a4'
t=tarfile.open(a);assert all(x.isfile() for x in t.getmembers());qb=t.extractfile('payload/SPCG_sixmodel_native_execution_request_v1.json').read();assert hashlib.sha256(qb).hexdigest()=='c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc'
q=json.loads(qb);m=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(m['remote_root']);idx=json.load(t.extractfile('payload/SPCG_sixmodel_input_index_v1.json'))
def exact(r):
 p=Path(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size==r['bytes'];h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 assert h.hexdigest()==r['sha256'] and (s.st_size,s.st_mtime_ns,s.st_ino)==(p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ino),str(p)
import importlib.util,subprocess
for r in m['files']:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
L=q['launch_contract'];c=Path(L['authorization']).parent;assert not c.parent.exists() and not Path(q['output']).exists() and not any(x.is_symlink() for x in c.parents)
s=importlib.util.spec_from_file_location('spcg_entry',q['entry']['path']);e=importlib.util.module_from_spec(s);s.loader.exec_module(e);qh=hashlib.sha256(qb).hexdigest();auth=dict(schema='bcsp-development-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='User authorized exact SPCG Native630 request single execution2026-11-17');ab=(json.dumps(auth,indent=2)+chr(10)).encode();ah=hashlib.sha256(ab).hexdigest();rt=dict(schema='bcsp-development-runtime-v1',request_sha256=qh,authorization_sha256=ah);rb=(json.dumps(rt,indent=2)+chr(10)).encode();rh=hashlib.sha256(rb).hexdigest();script=e.render_launcher(q,qh,ah,rh).encode()
c.parent.mkdir(mode=0o700);c.mkdir(mode=0o700)
for name,b in [(L['authorization'],ab),(L['runtime'],rb),(L['launcher'],script)]:
 with Path(name).open('xb') as f:f.write(b)
e.authorize(dict(path=L['request_path'],bytes=len(qb),sha256=qh),dict(path=L['authorization'],bytes=len(ab),sha256=ah),dict(path=L['runtime'],bytes=len(rb),sha256=rh))
with Path(q['launch_attempt']).open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh),f)
v=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'/bin/bash',L['launcher']],capture_output=True,timeout=10);print(json.dumps(dict(status='SINGLE_TMUX_ATTEMPT',returncode=v.returncode,stderr=v.stderr.decode(errors='replace'),session=L['tmux_session'],output=q['output'])));assert v.returncode==0
