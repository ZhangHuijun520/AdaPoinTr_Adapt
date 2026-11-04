import os,socket,json,stat,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr');c=r/'third_party/bcsp_geov1_training_foldc_8192_seed0_v1';d=r/'data/bcsp_geov1_foldc_8192_seed0_v1'
dirs=[c,d,c/'evidence',d/'points',c/'evidence/resource_rebind_v1'];rows=[];dr=[]
for p in dirs:
 assert time.monotonic()-s<15
 for a in (p,*p.parents):assert stat.S_ISDIR(a.lstat().st_mode),'directory/link: '+str(a)
 st=p.lstat();dr.append(dict(path=str(p),mode=stat.S_IMODE(st.st_mode),uid=st.st_uid))
 assert st.st_uid==1000 and stat.S_IMODE(st.st_mode)==448,'directory ownership/mode'
 for e in os.scandir(p):
  st=e.stat(follow_symlinks=False);kind='FILE' if stat.S_ISREG(st.st_mode) else 'DIR' if stat.S_ISDIR(st.st_mode) else 'OTHER'
  assert kind!='OTHER','linked/special entry: '+e.path
  assert st.st_uid==1000 and stat.S_IMODE(st.st_mode)==(420 if kind=='FILE' else 448),'entry ownership/mode: '+e.path
  rows.append(dict(path=e.path,kind=kind,mode=stat.S_IMODE(st.st_mode),uid=st.st_uid))
  assert len(rows)<=340
print(json.dumps(dict(hostname=socket.gethostname(),uid=1000,entries=rows,directories=dr,seconds=time.monotonic()-s,server_writes=0,contents_read=False)))
