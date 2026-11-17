from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='0e7dfa82fc484e7cb355b4513833136483989523974babcaa810099da804d43b'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_G1_C_training_execution_request_v1.json').read();assert hashlib.sha256(qraw).hexdigest()=='2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4'
q=json.loads(qraw);assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'];mapping=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(mapping['remote_root'])
def exact(r):
 v=Path(r['path']);assert not any(x.is_symlink() for x in (v,*v.parents));assert v.stat().st_size==r['bytes'] and hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256'],str(v)
import subprocess
assert not root.exists() and not root.is_symlink()
for v in [root,Path(q['output'])]:
 assert not v.exists() and not any(x.is_symlink() for x in (v,*v.parents));assert v.parent.is_dir()
for r in mapping['files']:
 assert not Path(r['target']).exists();b=t.extractfile(r['member']).read();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
v=os.statvfs(p);assert v.f_bavail*v.f_frsize>=int(8.5*1024**3)
g=subprocess.run(['nvidia-smi','--query-gpu=uuid,driver_version,memory.used','--format=csv,noheader,nounits'],capture_output=True,timeout=10,check=True).stdout.decode().strip().split(',')
assert g[0].strip()==q['identity']['gpu_uuid'] and g[1].strip()==q['identity']['driver_version'] and int(g[2])<=256
print(json.dumps(dict(status='TARGETS_ABSENT_RESOURCES_PASS',free_bytes=v.f_bavail*v.f_frsize,GPU=g)))
