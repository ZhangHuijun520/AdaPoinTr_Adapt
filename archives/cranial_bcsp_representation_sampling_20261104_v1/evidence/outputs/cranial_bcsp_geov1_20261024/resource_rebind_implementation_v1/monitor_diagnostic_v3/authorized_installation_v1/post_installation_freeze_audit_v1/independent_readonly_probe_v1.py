import os,socket,json,stat,hashlib,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
mp=Path('/home/jovyan/bcsp_foldc_8192_monitor_diagnostic_v3_supplement_v1.installation_map.json')
def checked(p):
 for a in p.parents:assert stat.S_ISDIR(a.lstat().st_mode),'invalid/link parent: '+str(a)
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size<=65536
 raw=p.read_bytes();end=p.stat();assert (st.st_size,st.st_mtime_ns,st.st_ino)==(end.st_size,end.st_mtime_ns,end.st_ino)
 return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),uid=st.st_uid,mode=stat.S_IMODE(st.st_mode))
r=checked(mp);assert r['sha256']=='7659ab863df5148c09f59917d9df74a0936b916e09e9f79203368cee37bac9b2'
q=json.loads(mp.read_bytes());rows=[]
for r in q['installation_map']+q['reuse_readonly_not_repackaged']:
 x=checked(Path(r.get('server_target',r.get('path'))))
 assert (x['bytes'],x['sha256'])==(r['bytes'],r['sha256']) and x['uid']==1000 and x['mode']==420
 rows.append(x);assert time.monotonic()-s<25
d=Path(q['explicit_new_evidence_directory']);st=d.lstat();assert stat.S_ISDIR(st.st_mode) and st.st_uid==1000 and stat.S_IMODE(st.st_mode)==448
entries=sorted(str(x) for x in d.iterdir());expected=sorted(r['server_target'] for r in q['installation_map'] if Path(r['server_target']).parent==d)
assert entries==expected and len(entries)==6
print(json.dumps(dict(hostname=socket.gethostname(),uid=1000,files=rows,directory=dict(path=str(d),uid=st.st_uid,mode=448,entries=entries),extra_entries=0,server_writes=0,seconds=time.monotonic()-s)))
