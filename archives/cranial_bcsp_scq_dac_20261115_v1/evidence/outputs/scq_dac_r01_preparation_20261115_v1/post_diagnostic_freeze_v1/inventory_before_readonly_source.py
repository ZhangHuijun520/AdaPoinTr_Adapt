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

assert (O/'exit_code.txt').read_text().strip()=='0' and not (O/'failure.json').exists()
pid=int((O/'worker.pid').read_text())
try:assert q['entry']['path'].encode() not in (Path('/proc')/str(pid)/'cmdline').read_bytes()
except FileNotFoundError:pass
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
result={};total=0
for root,label in ((I,'installed'),(O,'output')):
 files={};dirs=[]
 for p in [root,*sorted(root.rglob('*'))]:
  assert not p.is_symlink() and (p.is_file() or p.is_dir()),str(p)
  n=str(p.relative_to(root))
  if p.is_dir():dirs.append(n);continue
  s=p.stat();total+=s.st_size;assert len(files)<64 and total<1200000000
  d=h(p);a=p.stat();fp=lambda t:[t.st_dev,t.st_ino,t.st_mode,t.st_size,t.st_mtime_ns,t.st_ctime_ns]
  assert fp(s)==fp(a);files[n]=dict(bytes=s.st_size,sha256=d,fingerprint=fp(a))
 result[label]=dict(files=files,directories=dirs)
print(json.dumps(dict(status='FINISHED_EXACT_SCOPED_STABLE_INVENTORY',results=result,hashed_bytes=total,seconds=time.monotonic()-T,server_writes=0)))
