from pathlib import Path
import os,socket,json,hashlib,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v3');q=json.loads((r/'SPCG_CUDA_execution_request_v3.json').read_bytes());o=Path(q['output']);total=0
def record(p,text=False):
 global total
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert s.st_size<8*1024**2;total+=s.st_size;assert total<32*1024**2;b=p.read_bytes();v=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 if text:v['text']=b.decode()
 return v
d=dict(installed={p.name:record(p) for p in r.iterdir() if p.is_file()},controls={p.name:record(p,True) for p in (r/'control').iterdir()},output={},directories=[])
for p in sorted(o.iterdir()):
 if p.is_dir():
  assert not p.is_symlink();d['directories'].append(dict(name=p.name,children=[str(x.relative_to(p)) for x in p.rglob('*')]))
 else:d['output'][p.name]=record(p,p.suffix!='.npz')
d['reused']={}
for x in list(q['implementation'].values())+[q[k] for k in ['entry','helper','parent_helper','timezone_implementation','probe_asset','head_initialization','mother_source']]:
 v=record(Path(x['path']));assert v['bytes']==x['bytes'] and v['sha256']==x['sha256'];d['reused'][x['path']]=v
d['worker_live']=Path('/proc/'+d['output']['worker.pid']['text'].strip()).exists();d['tmux_live']=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==0;d['hashed_bytes']=total
print(json.dumps(d))
