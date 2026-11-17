from pathlib import Path
import os,json,socket,stat,time
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');roots=['logs/cranial_bcsp_fullmamba_n0','third_party/bcsp_scq_dac_r1_20261115_v1','archives/server_small_items_backup_v1_20261019'];rows=[];links=[];start=time.monotonic()
for rel in roots:
 root=p/rel;assert not any(x.is_symlink() for x in (root,*root.parents))
 for parent,dirs,files in os.walk(root,followlinks=False):
  assert time.monotonic()-start<20 and len(rows)<4000
  dirs[:]=[d for d in dirs if not (Path(parent)/d).is_symlink()]
  for name in files:
   v=Path(parent)/name;s=v.lstat()
   if stat.S_ISREG(s.st_mode):rows.append(dict(path=str(v),bytes=s.st_size,allocated=s.st_blocks*512,nlink=s.st_nlink,mtime_ns=s.st_mtime_ns))
   elif stat.S_ISLNK(s.st_mode):links.append(str(v))
print(json.dumps(dict(files=rows,links=links)))
