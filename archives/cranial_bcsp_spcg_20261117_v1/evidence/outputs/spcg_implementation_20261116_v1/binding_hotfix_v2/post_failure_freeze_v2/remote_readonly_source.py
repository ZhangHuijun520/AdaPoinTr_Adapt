from pathlib import Path
import json,hashlib,os,socket,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v2');p=r/'SPCG_CUDA_execution_request_v2.json';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='a2b1961158b58199e212130654ddd274ce617c90e24448f22ba70a0062c2343e';q=json.loads(b);out=Path(q['output']);result=dict(hostname=socket.gethostname(),installed=[],control={},output={},directories=[],sources=[]);total=0
def item(p,text=False):
 global total
 assert not p.is_symlink() and p.is_file();s=p.stat();assert s.st_size<=8*1024**2;total+=s.st_size;assert total<=16*1024**2;b=p.read_bytes();v=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 if text:v['text']=b.decode('utf-8')
 return v
for p in sorted(r.iterdir()):
 if p.is_file():result['installed'].append(dict(path=str(p),**item(p)))
for p in sorted((r/'control').iterdir()):result['control'][p.name]=item(p,True)
for p in sorted(out.iterdir()):
 if p.is_dir():
  assert not p.is_symlink();result['directories'].append(dict(name=p.name,children=sorted(x.name for x in p.iterdir())))
 else:
  assert p.suffix.lower() not in ['.npz','.pth','.bin'];result['output'][p.name]=item(p,True)
for key in ['parent_helper','helper','entry']:
 x=q[key];v=item(Path(x['path']),True);assert v['sha256']==x['sha256'] and v['bytes']==x['bytes'];result['sources'].append(dict(key=key,path=x['path'],**v))
t=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5);result['tmux_returncode']=t.returncode;result['worker_live']=Path('/proc/'+result['output']['worker.pid']['text'].strip()).exists();result['hashed_bytes']=total
print(json.dumps(result))
