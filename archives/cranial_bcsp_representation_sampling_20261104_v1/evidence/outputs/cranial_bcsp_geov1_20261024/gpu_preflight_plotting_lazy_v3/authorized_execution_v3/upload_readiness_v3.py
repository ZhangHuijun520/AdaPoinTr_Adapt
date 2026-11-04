import hashlib,json,os,shutil,socket,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
H='7a7a74fcec86bb4fa6c7ab77b74e8d509a26ae75ade73a05d9c8cab183ef2365'
B=Path('/home/jovyan');N='bcsp_gpu_preflight_v3'
def sha(b):return hashlib.sha256(b).hexdigest()

z=B/(N+'.tar.gz')
assert z.stat().st_size==86262 and sha(z.read_bytes())=='dc5ccbfdb92c2321bcbb7f0b3c7806e753993be26d880790ffb7f521621d630d'
assert int((B/(N+'.bytes')).read_text())==86262
assert (B/(N+'.tar.gz.sha256')).read_text().split()==[sha(z.read_bytes()),z.name]
m=B/(N+'.contents.sha256');d=m.read_bytes()
assert sha(d)=='3b5cf48a982443c80f1210962759696f5bda05aface141f2688ef8bd7557ade5'
assert (B/(N+'.contents.sha256.sha256')).read_text().split()==[sha(d),m.name]
with tarfile.open(z,'r:gz') as t:
 ms=t.getmembers();assert len(ms)==26 and len({x.name for x in ms})==26
 assert all(x.isfile() and not x.name.startswith('/') and '..' not in PurePosixPath(x.name).parts for x in ms)
 data={x.name:t.extractfile(x).read() for x in ms}
manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in d.decode('ascii').splitlines()}
assert len(manifest)==26 and set(manifest)==set(data)
assert all(sha(data[k])==v for k,v in manifest.items())
q=json.loads(data['evidence/execution_request_v3.json']);assert sha(data['evidence/execution_request_v3.json'])==H
assert socket.gethostname()==q['identity']['hostname'] and os.getuid()==1000
root=Path(q['future_control_paths']['request']).parents[1]
assert not root.exists() and not any(x.is_symlink() for x in (root,*root.parents))
assert str(Path(sys.executable).resolve())==q['identity']['python_realpath']
assert sys.version.split()[0]==q['identity']['python_version']
assert shutil.disk_usage(B).free>=q['resources']['minimum_free_disk_bytes']
assert not Path(q['future_control_paths']['summary']).parent.exists()
assert subprocess.run(['tmux','has-session','-t',q['future_start_contract']['tmux_session']],capture_output=True).returncode!=0
for r in q['future_limited_deployment']['scope_provider_bindings']+q['future_limited_deployment']['scope_environment_metadata_bindings']:
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],str(p)
for p in map(Path,q['future_control_paths'].values()):
 assert not p.exists() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
for r in q['future_limited_deployment']['files']:
 p=Path(r['server_target']);name=p.relative_to(root).as_posix()
 assert not p.exists() and len(data[name])==r['bytes'] and sha(data[name])==r['sha256']
expected={Path(r['server_target']).relative_to(root).as_posix() for r in q['future_limited_deployment']['files']}
assert set(data)==expected|{'evidence/execution_request_v3.json','control/authorization_v3.json','control/runtime_v3.json','control/launcher_v3.sh'}
print(json.dumps({'status':'UPLOAD_AND_READINESS_PASS','archive_members':26,'frozen_installation_files':22,'provider_environment_hashes':9,'server_writes':0,'root':str(root)}))
