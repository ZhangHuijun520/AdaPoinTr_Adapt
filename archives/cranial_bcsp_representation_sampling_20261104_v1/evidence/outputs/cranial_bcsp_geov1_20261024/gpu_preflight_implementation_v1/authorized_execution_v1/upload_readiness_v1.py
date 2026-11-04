import hashlib,json,os,shutil,socket,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
H='68938b967e6c84702e980d6d1ee43435d8cb6408d6b5748b83b33eef83d66738'
B=Path('/home/jovyan');N='bcsp_gpu_preflight_v1'
def sha(b):return hashlib.sha256(b).hexdigest()
z=B/(N+'.tar.gz')
assert z.stat().st_size==81545 and sha(z.read_bytes())=='7e8de6c4e6e60cdc5293b5010278d019b8da314c24087419493d71e5b1e87d93'
assert int((B/(N+'.bytes')).read_text())==81545
assert (B/(N+'.tar.gz.sha256')).read_text().split()==[sha(z.read_bytes()),z.name]
m=B/(N+'.contents.sha256');d=m.read_bytes()
assert sha(d)=='3c7d874fc9b31a4bd6ad0c53ada412ade1b6ec82e4c0de336bbdcfb59865db57'
assert (B/(N+'.contents.sha256.sha256')).read_text().split()==[sha(d),m.name]
with tarfile.open(z,'r:gz') as t:
 ms=t.getmembers();assert len(ms)==26 and len({x.name for x in ms})==26
 assert all(x.isfile() and not x.name.startswith('/') and '..' not in PurePosixPath(x.name).parts for x in ms)
 data={x.name:t.extractfile(x).read() for x in ms}
manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in d.decode('ascii').splitlines()}
assert len(manifest)==26 and set(manifest)==set(data)
assert all(sha(data[k])==v for k,v in manifest.items())
q=json.loads(data['evidence/execution_request_v1.json']);assert sha(data['evidence/execution_request_v1.json'])==H
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
assert set(data)==expected|{'evidence/execution_request_v1.json','control/authorization_v1.json','control/runtime_v1.json','control/launcher_v1.sh'}
print(json.dumps({'status':'UPLOAD_AND_READINESS_PASS','archive_members':26,'frozen_installation_files':22,'provider_environment_hashes':9,'server_writes':0,'root':str(root)}))
