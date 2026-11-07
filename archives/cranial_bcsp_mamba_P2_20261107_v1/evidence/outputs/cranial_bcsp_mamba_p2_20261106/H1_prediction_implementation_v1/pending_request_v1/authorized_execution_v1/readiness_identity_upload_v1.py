import hashlib,json,os,pathlib,shutil,socket,subprocess,tarfile
P=pathlib.Path('/home/jovyan/adapointr_work/PoinTr')
A=pathlib.Path('/home/jovyan/bcsp_p2_H1_twofold_prediction_pending_20261106_v1.tar.gz')
R=P/'third_party/bcsp_p2_H1_twofold_prediction_20261106_v1'
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
assert P.is_dir() and not P.is_symlink()
assert A.is_file() and not A.is_symlink() and A.stat().st_size==48956
assert hashlib.sha256(A.read_bytes()).hexdigest()=='00eab49474bd23d4d0139dc1e74078e61b5c2a5b4678b081c0d4c53aa891fe9b'
for suffix in ('.sha256','.bytes','.contents.sha256'):
 p=pathlib.Path(str(A)+suffix);assert p.is_file() and not p.is_symlink()
assert pathlib.Path(str(A)+'.sha256').read_text().split()[0]==hashlib.sha256(A.read_bytes()).hexdigest()
assert int(pathlib.Path(str(A)+'.bytes').read_text())==A.stat().st_size
with tarfile.open(A) as t:
 mapping=json.load(t.extractfile('installation_mapping_v1.json'))
 assert mapping['remote_root']==str(R) and len(mapping['files'])==8
 for m in mapping['files']:
  target=pathlib.Path(m['target']);assert target.parent==R and not target.exists() and not target.is_symlink()
 assert not R.exists() and not R.is_symlink()
 for parent in (R.parent,*R.parent.parents):assert parent.is_dir() and not parent.is_symlink()
 qbytes=t.extractfile('payload/H1_C_D_development_execution_request_v1.json').read()
 assert hashlib.sha256(qbytes).hexdigest()=='90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147'
 q=json.loads(qbytes)
 for name in (q['output'],q['launch_attempt'],q['launch_contract']['authorization'],q['launch_contract']['runtime'],q['launch_contract']['launcher']):
  p=pathlib.Path(name);assert not p.exists() and not p.is_symlink()
gpu=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
assert gpu.returncode==0
v=[x.strip() for x in gpu.stdout.strip().split(',')];I=q['identity']
assert v[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256
pids=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
assert pids.returncode==0 and not pids.stdout.strip()
free=shutil.disk_usage(P).free;assert free>=4294967296
print(json.dumps(dict(status='READONLY_IDENTITY_UPLOAD_TARGETS_PASS',hostname=socket.gethostname(),uid=os.getuid(),gpu=v,free_bytes=free,upload_files=4,install_targets=8,server_writes=0)),flush=True)
