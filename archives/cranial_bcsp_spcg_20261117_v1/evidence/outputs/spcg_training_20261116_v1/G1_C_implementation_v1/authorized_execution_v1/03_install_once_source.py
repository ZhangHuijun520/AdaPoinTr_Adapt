from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='0e7dfa82fc484e7cb355b4513833136483989523974babcaa810099da804d43b'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_G1_C_training_execution_request_v1.json').read();assert hashlib.sha256(qraw).hexdigest()=='2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4'
q=json.loads(qraw);assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'];mapping=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(mapping['remote_root'])
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
print(json.dumps(dict(status='INSTALLED_9_EXCLUSIVE_HASH_PASS',files=len(mapping['files']))))
