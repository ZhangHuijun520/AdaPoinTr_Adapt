import os,socket,json,stat,hashlib,time
from pathlib import Path
s=time.monotonic();h=socket.gethostname();assert h=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
mp=Path('/home/jovyan/bcsp_foldc_8192_monitor_diagnostic_v3_supplement_v1.installation_map.json')
def parents(p):
 for a in p.parents:
  if os.path.lexists(a):assert stat.S_ISDIR(a.lstat().st_mode),'linked/invalid ancestor: '+str(a)
parents(mp);assert stat.S_ISREG(mp.lstat().st_mode) and mp.stat().st_size==10724
raw=mp.read_bytes();assert hashlib.sha256(raw).hexdigest()=='7659ab863df5148c09f59917d9df74a0936b916e09e9f79203368cee37bac9b2'
q=json.loads(raw);rows=[];reuse=[]
for r in q['installation_map']:
 p=Path(r['server_target']);parents(p);rows.append(dict(path=str(p),exists=os.path.lexists(p)))
p=Path(q['explicit_new_evidence_directory']);parents(p);directory=dict(path=str(p),exists=os.path.lexists(p))
for r in q['reuse_readonly_not_repackaged']:
 p=Path(r['path']);parents(p);st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size==r['bytes']
 raw=p.read_bytes();end=p.stat();assert (st.st_size,st.st_mtime_ns,st.st_ino)==(end.st_size,end.st_mtime_ns,end.st_ino)
 digest=hashlib.sha256(raw).hexdigest();assert digest==r['sha256'];reuse.append(dict(path=str(p),bytes=len(raw),sha256=digest,uid=st.st_uid,mode=stat.S_IMODE(st.st_mode)))
assert len(rows)==7 and len(reuse)==2 and time.monotonic()-s<20
print(json.dumps(dict(hostname=h,uid=1000,targets=rows,new_directory=directory,reuse=reuse,existing_ancestors_directory_only=True,seconds=time.monotonic()-s,server_writes=0)))
