import os,socket,json,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
ancestors=set();pid=os.getpid()
while pid and len(ancestors)<16:
 ancestors.add(pid);st=Path('/proc',str(pid),'status').read_text();pid=int(next(x.split()[1] for x in st.splitlines() if x.startswith('PPid:')))
rows=[];scanned=0
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 scanned+=1
 assert scanned<=512 and time.monotonic()-s<10
 try:
  if p.stat().st_uid!=1000 or int(p.name) in ancestors:continue
  name=(p/'comm').read_text().strip()
  if name not in ('python','python3','python3.8','python3.10','timeout','bash','sh','nvidia-smi'):continue
  args=(p/'cmdline').read_bytes()[:32768].split(bytes([0]))
  marker=any(b'BCSP_EXCLUSIVE_INSTALL_337_V1' in a or b'42d0b302e40ec0d127c147063b0df9ddd662aa1ef37d964387dd3c8081cd6e62' in a for a in args)
  stdin_python=name=='python3.8' and b'-I' in args and b'-S' in args and b'-B' in args and b'-c' not in args
  status=(p/'status').read_text();fields=dict(x.split(':',1) for x in status.splitlines() if ':' in x)
  rows.append(dict(pid=int(p.name),comm=name,ppid=fields.get('PPid','').strip(),state=fields.get('State','').strip(),installation_marker=marker,isolated_stdin_python=stdin_python))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
print(json.dumps(dict(hostname=socket.gethostname(),uid=1000,processes=rows,audit_ancestors_excluded=sorted(ancestors),scanned=scanned,seconds=time.monotonic()-s,server_writes=0,no_signals_sent=True)))
