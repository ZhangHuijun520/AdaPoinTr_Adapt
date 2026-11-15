from pathlib import Path
import os,socket,json,hashlib,time,subprocess,base64
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
I=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1')
Q=I/'SCQ_DAC_R1_execution_request_v1.json'
assert hashlib.sha256(Q.read_bytes()).hexdigest()=='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'
q=json.loads(Q.read_bytes());O=Path(q['output']);T=time.monotonic()
assert not any(p.is_symlink() for root in (I,O) for p in (root,*root.parents))
def h(p):
 a=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):assert time.monotonic()-T<55;a.update(b)
 return a.hexdigest()

files={};total=0
for root,label in ((I,'installed'),(O,'output')):
 for p in sorted(root.rglob('*')):
  if not p.is_file() or p.suffix in ('.pth','.npz','.gz'):continue
  assert not p.is_symlink() and p.stat().st_size<2097152
  raw=p.read_bytes();total+=len(raw);assert total<16777216
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
print(json.dumps(dict(status='CONTROL_AND_RUNTIME_METADATA_READONLY',files=files,bytes=total,server_writes=0)))
