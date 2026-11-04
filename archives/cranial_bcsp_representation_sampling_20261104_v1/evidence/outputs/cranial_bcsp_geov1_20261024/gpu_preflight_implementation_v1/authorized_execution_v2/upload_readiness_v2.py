import hashlib,json,os,shutil,socket,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
H='18432038d32c4857452c96f0795dd4b072a57fa9d38916cf87e10e8215700bc7'
B=Path('/home/jovyan');N='bcsp_gpu_preflight_v2'
def sha(b):return hashlib.sha256(b).hexdigest()
z=B/(N+'.tar.gz')
assert z.stat().st_size==85951 and sha(z.read_bytes())=='ec0ce25c86aef52cca35bd296225776ba6db3575fef2b877646aef0a79dde114'
assert int((B/(N+'.bytes')).read_text())==85951
assert (B/(N+'.tar.gz.sha256')).read_text().split()==[sha(z.read_bytes()),z.name]
m=B/(N+'.contents.sha256');d=m.read_bytes()
assert sha(d)=='416b81e0c8320d5dd8978922db1b6a4347535c1bb7b58cfe52c32fa102736e3d'
assert (B/(N+'.contents.sha256.sha256')).read_text().split()==[sha(d),m.name]
with tarfile.open(z,'r:gz') as t:
 ms=t.getmembers();assert len(ms)==26 and len({x.name for x in ms})==26
 assert all(x.isfile() and not x.name.startswith('/') and '..' not in PurePosixPath(x.name).parts for x in ms)
 data={x.name:t.extractfile(x).read() for x in ms}
manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in d.decode('ascii').splitlines()}
assert len(manifest)==26 and set(manifest)==set(data)
assert all(sha(data[k])==v for k,v in manifest.items())
q=json.loads(data['evidence/execution_request_v2.json']);assert sha(data['evidence/execution_request_v2.json'])==H
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
assert set(data)==expected|{'evidence/execution_request_v2.json','control/authorization_v2.json','control/runtime_v2.json','control/launcher_v2.sh'}
print(json.dumps({'status':'UPLOAD_AND_READINESS_PASS','archive_members':26,'frozen_installation_files':22,'provider_environment_hashes':9,'server_writes':0,'root':str(root)}))
