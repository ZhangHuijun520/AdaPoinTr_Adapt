from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v2.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='65a0b9e0a9295e88eb76768e7dadf58476a582c0bac6365a0823093cebeb0ebb'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_G1_D_training_execution_request_v2.json').read();assert hashlib.sha256(qraw).hexdigest()=='d0e171d7ef70bef996cb1e4b1fb7006bd7173cc0aecf9b580d130b25fb2d998e'
q=json.loads(qraw);assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'];mapping=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(mapping['remote_root'])
def exact(r):
 v=Path(r['path']);assert not any(x.is_symlink() for x in (v,*v.parents));assert v.stat().st_size==r['bytes'] and hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256'],str(v)
import importlib.util,subprocess
for r in mapping['files']:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
assert not Path(q['output']).exists();L=q['launch_contract'];control=Path(L['authorization_path']).parent;assert not control.exists()
sp=importlib.util.spec_from_file_location('authorized_spcg_entry',q['implementation']['entry']['path']);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
qh=hashlib.sha256(qraw).hexdigest();auth=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='User authorized exactG1_D_v2 request3900step execution2026-11-17')
ab=(json.dumps(auth,indent=2)+chr(10)).encode();rt=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256=hashlib.sha256(ab).hexdigest());rb=(json.dumps(rt,indent=2)+chr(10)).encode()
e.validate(q,qh,auth,hashlib.sha256(ab).hexdigest(),rt)
script=e.render_launcher(q,qh,hashlib.sha256(ab).hexdigest(),hashlib.sha256(rb).hexdigest()).encode()
assert not control.parent.exists() and not any(x.is_symlink() for x in control.parents)
control.parent.mkdir(mode=0o700);control.mkdir(mode=0o700)
for name,b in [(L['authorization_path'],ab),(L['runtime_path'],rb),(L['launcher_path'],script)]:
 with Path(name).open('xb') as f:f.write(b)
with Path(L['launch_attempt_path']).open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh),f)
v=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'/bin/bash',L['launcher_path']],capture_output=True,timeout=10)
print(json.dumps(dict(status='SINGLE_TMUX_ATTEMPT',returncode=v.returncode,stderr=v.stderr.decode(errors='replace'),session=L['tmux_session'],output=q['output'])))
assert v.returncode==0
