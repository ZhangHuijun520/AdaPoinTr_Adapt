import os,json,time
from pathlib import Path
start=time.monotonic();rows=[];scanned=0
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 scanned+=1
 assert scanned<=512 and time.monotonic()-start<10
 try:
  if p.stat().st_uid!=os.getuid():continue
  name=(p/'comm').read_text().strip()
  if name not in ('python','python3','python3.8','python3.10','timeout','bash','sh'):continue
  args=(p/'cmdline').read_bytes()[:32768].split(bytes([0]))
  match=any(b'hpc5000' in a for a in args)
  marker=any(b'BCSP_EXCLUSIVE_INSTALL_337_V1' in a or b'42d0b302e40ec0d127c147063b0df9ddd662aa1ef37d964387dd3c8081cd6e62' in a for a in args)
  if match and int(p.name)!=os.getpid():
   status=(p/'status').read_text();fields=dict(x.split(':',1) for x in status.splitlines() if ':' in x)
   rows.append(dict(pid=int(p.name),comm=name,state=fields.get('State','').strip(),ppid=fields.get('PPid','').strip(),hpc_client=True,installation_marker=marker,argument_bytes=sum(map(len,args))))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
print(json.dumps(dict(uid=os.getuid(),processes=rows,scanned=scanned,seconds=time.monotonic()-start,no_signals_sent=True)))
