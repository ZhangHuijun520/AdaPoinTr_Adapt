from pathlib import Path
import json,hashlib,socket,os,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1');qp=r/'SPCG_CUDA_execution_request_v1.json';b=qp.read_bytes();qh=hashlib.sha256(b).hexdigest();assert qh=='00a69c5cc3d42e04f4caa3c21650dd58db5d8c1b446741a1b42caf6730213d0f';q=json.loads(b);o=Path(q['output']);files=[];total=0
for p in sorted(r.iterdir()):
 if p.is_file():
  assert not p.is_symlink();b=p.read_bytes();total+=len(b);files.append(dict(name=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
assert total<16*1024**2
controls={};output={}
for p in sorted((r/'control').iterdir()):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<32000;controls[p.name]=p.read_text()
for p in sorted(o.iterdir()):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<64000;output[p.name]=p.read_text()
h=Path(q['helper']['path']);hb=h.read_bytes();assert hashlib.sha256(hb).hexdigest()==q['helper']['sha256']
t=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5)
live=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:b=(p/'cmdline').read_bytes()
  except (OSError,PermissionError):continue
  if b'bcsp_spcg_cuda_entry_v1.py' in b and b'--request-sha256' in b:live.append(int(p.name))
print(json.dumps(dict(hostname=socket.gethostname(),request_sha256=qh,identity=q['identity']['gpu_uuid'],selector=q['environment']['CUDA_VISIBLE_DEVICES'],files=files,hashed_bytes=total,controls=controls,output=output,helper_sha256=hashlib.sha256(hb).hexdigest(),tmux_returncode=t.returncode,tmux_stderr=t.stderr.decode(),live_matching_worker_PIDs=live)))
