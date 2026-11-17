from pathlib import Path
import json,hashlib,socket,os,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G0C_training_20261116_v2');q=json.loads((r/'SPCG_G0_C_training_execution_request_v2.json').read_bytes());o=Path(q['output']);total=0
def item(p,text=False):
 global total
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));b=p.read_bytes();total+=len(b);assert len(b)<4*1024**2 and total<16*1024**2;v=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 if text:v['text']=b.decode()
 return v
d=dict(installed={p.name:item(p) for p in r.iterdir() if p.is_file()},controls={p.name:item(p,True) for p in Path(q['launch_contract']['authorization_path']).parent.iterdir()},output={},directories=[],sources={})
for p in o.iterdir():
 if p.is_dir():assert not p.is_symlink();d['directories'].append(dict(name=p.name,children=[x.name for x in p.iterdir()]))
 else:assert p.suffix not in ['.pth','.npz','.bin'];d['output'][p.name]=item(p,True)
records=list(q['implementation'].values())+[q['native_helper']]
head=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1/bcsp_spcg_head_v1.py');records.append(dict(path=str(head)))
for x in records:
 v=item(Path(x['path']),True)
 if 'sha256' in x:assert v['sha256']==x['sha256'] and v['bytes']==x['bytes']
 d['sources'][x['path']]=v
d['worker_live']=Path('/proc/'+d['output']['worker.pid']['text'].strip()).exists();d['tmux_live']=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==0;d['hashed_bytes']=total
link=Path('/usr/share/zoneinfo/UTC');target=Path('/usr/share/zoneinfo/Etc/UTC');b=target.read_bytes()
d['UTC']=dict(link=str(link),is_symlink=link.is_symlink(),link_text=os.readlink(link),resolved=str(link.resolve()),target=str(target),target_regular=target.is_file(),target_linked=any(x.is_symlink() for x in (target,*target.parents)),link_parent_linked=any(x.is_symlink() for x in link.parents),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
print(json.dumps(d))
