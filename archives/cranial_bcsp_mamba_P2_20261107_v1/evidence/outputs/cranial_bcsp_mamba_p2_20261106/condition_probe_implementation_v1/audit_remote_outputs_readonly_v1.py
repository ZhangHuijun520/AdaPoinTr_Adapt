import hashlib,json,os,socket,subprocess,time
from pathlib import Path
start=time.monotonic();seen={};total=0
root=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_condition_probe_20261107_v1')
def stamp(p):
 s=p.stat();return(s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns)
def h(p):
 global total
 p=Path(p);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 a=stamp(p);b=p.read_bytes();total+=len(b);assert total<134217728 and time.monotonic()-start<60
 assert a==stamp(p);seen[str(p)]=a;return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def exact(p,b):assert h(p)=={k:b[k] for k in ['bytes','sha256']},str(p)
qp=root/'condition_probe_execution_request_v1.json';assert h(qp)['sha256']=='9f2a04c381070d54d9e82cc70e800403b12ac7867124ff4b5e52043c1997549c'
q=json.loads(qp.read_bytes());assert socket.gethostname()==q['identity']['hostname'] and os.getuid()==1000
for k in ['entry','core','capture','input_index','P3','parent_entry','helper','static_config','preflight_scope','numeric_policy']:exact(q[k]['path'],q[k])
out=Path(q['output']);assert (out/'exit_code.txt').read_text().strip()=='0' and not (out/'failure.json').exists()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==1
pid=int((out/'worker.pid').read_text());assert not Path('/proc/'+str(pid)).exists()
c=json.loads((out/'completion.json').read_bytes());assert c['status']=='CONDITION_PROBE_ARCHIVED_PENDING_FREEZE_AUDIT' and c['prefixes']==1680 and c['request_sha256']==h(qp)['sha256']
members=c['archive']['members'];assert len(members)==1692 and len({r['name'] for r in members})==1692
for b in members:
 p=Path(b['name']);assert not p.is_absolute() and '..' not in p.parts;exact(out/p,b)
a=out/'development_predictions_v1.tar.gz';exact(a,c['archive']);assert Path(str(a)+'.sha256').read_text().split()[0]==c['archive']['sha256'];assert int(Path(str(a)+'.bytes').read_text())==c['archive']['bytes']
assert Path(str(a)+'.contents.sha256').read_text()==''.join(r['sha256']+'  '+r['name']+'\n' for r in members)
extra={'completion.json','worker.pid','exit_code.txt','launch.log',a.name,a.name+'.sha256',a.name+'.bytes',a.name+'.contents.sha256'}
expected={r['name'] for r in members}|extra
actual={str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()};assert actual==expected
assert {str(p.relative_to(out)) for p in out.rglob('*') if p.is_dir()}=={'features','tmp'}
for p in out.rglob('*'):assert not p.is_symlink()
for n in extra:h(out/n)
L=q['launch_contract'];auth=json.loads(Path(L['authorization_path']).read_bytes());runtime=json.loads(Path(L['runtime_path']).read_bytes());startup=json.loads((root/'control/startup_receipt_v1.json').read_bytes())
assert auth['explicit_user_authorization'] and auth['request_sha256']==runtime['request_sha256']==c['request_sha256']
assert h(L['authorization_path'])['sha256']==runtime['authorization_sha256']==startup['authorization_sha256'];assert h(L['runtime_path'])['sha256']==startup['runtime_sha256'];assert h(L['launcher_path'])['sha256']==startup['launcher_sha256']
assert json.loads(Path(q['launch_attempt']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=c['request_sha256'])
assert all(stamp(Path(p))==v for p,v in seen.items())
print(json.dumps(dict(status='REMOTE_READONLY_OUTPUT_FREEZE_PASS',request_sha256=c['request_sha256'],archive=c['archive']['sha256'],archive_bytes=c['archive']['bytes'],archived_members=len(members),exact_output_files=len(actual),worker_absent=True,tmux_absent=True,exit_code=0,controls_verified=True,stable_content_fingerprints=True,atime_excluded=True,read_bytes=total,seconds=time.monotonic()-start,completion_sha256=h(out/'completion.json')['sha256'],server_writes=0,forward_calls=0)))
