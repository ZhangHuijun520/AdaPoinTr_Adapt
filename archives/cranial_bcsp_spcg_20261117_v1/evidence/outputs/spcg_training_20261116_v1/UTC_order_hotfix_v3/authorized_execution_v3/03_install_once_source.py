from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='0c1891dd121c5763411e9d3278e3e6b92f44409e4ce43bd3f36ad272493099bb'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_G0_C_training_execution_request_v3.json').read();assert hashlib.sha256(qraw).hexdigest()=='871c5216815d5e479446108da979e8c77ce6ea5aec2578ac0573652e51a75d63'
q=json.loads(qraw);assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'];mapping=json.load(t.extractfile('installation_mapping_v3.json'));root=Path(mapping['remote_root'])
def exact(r):
 v=Path(r['path']);assert not any(x.is_symlink() for x in (v,*v.parents));assert v.stat().st_size==r['bytes'] and hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256'],str(v)
assert not root.exists() and not root.is_symlink() and root.parent.is_dir()
for r in mapping['files']:
 assert Path(r['target']).parent==root and not Path(r['target']).exists();b=t.extractfile(r['member']).read();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
assert not any(x.is_symlink() for x in root.parents)
root.mkdir(mode=0o700)
for r in mapping['files']:
 with Path(r['target']).open('xb') as f:f.write(t.extractfile(r['member']).read())
for r in mapping['files']:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
print(json.dumps(dict(status='INSTALLED_8_EXCLUSIVE_HASH_PASS',files=len(mapping['files']))))
