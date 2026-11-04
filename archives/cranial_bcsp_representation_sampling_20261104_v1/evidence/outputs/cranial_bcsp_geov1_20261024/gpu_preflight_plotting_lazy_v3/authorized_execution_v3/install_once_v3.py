import hashlib,json,os,socket,subprocess,sys,tarfile
from pathlib import Path
H='7a7a74fcec86bb4fa6c7ab77b74e8d509a26ae75ade73a05d9c8cab183ef2365'
def sha(b):return hashlib.sha256(b).hexdigest()
z=Path('/home/jovyan/bcsp_gpu_preflight_v3.tar.gz')
assert z.stat().st_size==86262 and sha(z.read_bytes())=='dc5ccbfdb92c2321bcbb7f0b3c7806e753993be26d880790ffb7f521621d630d'
with tarfile.open(z,'r:gz') as t:
 ms=t.getmembers();assert len(ms)==26 and all(x.isfile() for x in ms)
 data={x.name:t.extractfile(x).read() for x in ms}
assert sha(data['evidence/execution_request_v3.json'])==H
q=json.loads(data['evidence/execution_request_v3.json'])
assert socket.gethostname()==q['identity']['hostname'] and os.getuid()==1000
assert str(Path(sys.executable).resolve())==q['identity']['python_realpath']
root=Path(q['future_control_paths']['request']).parents[1]
assert not root.exists() and not any(x.is_symlink() for x in (root,*root.parents))
assert not Path(q['future_control_paths']['summary']).parent.exists()
assert subprocess.run(['tmux','has-session','-t',q['future_start_contract']['tmux_session']],capture_output=True).returncode!=0
for r in q['future_limited_deployment']['scope_provider_bindings']+q['future_limited_deployment']['scope_environment_metadata_bindings']:
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],str(p)
order=[Path(r['server_target']).relative_to(root).as_posix() for r in q['future_limited_deployment']['files']]
order+=['evidence/execution_request_v3.json','control/authorization_v3.json','control/runtime_v3.json','control/launcher_v3.sh']
assert len(order)==len(set(order))==len(data)==26 and set(order)==set(data)
for r in q['future_limited_deployment']['files']:
 name=Path(r['server_target']).relative_to(root).as_posix()
 assert len(data[name])==r['bytes'] and sha(data[name])==r['sha256']
assert all(not (root/name).exists() and '..' not in Path(name).parts and not name.startswith('/') for name in order)
root.mkdir(mode=0o700)
for name in order:
 p=root/name;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 assert p.parent.resolve()==p.parent and not any(x.is_symlink() for x in (p,*p.parents))
 fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(data[name])
 assert p.stat().st_size==len(data[name]) and sha(p.read_bytes())==sha(data[name]),str(p)
print(json.dumps({'status':'EXCLUSIVE_INSTALL_PASS','files':26,'request_sha256':H,'targets':[str(root/n) for n in order],'GPU_calls':0,'launched':False}))
