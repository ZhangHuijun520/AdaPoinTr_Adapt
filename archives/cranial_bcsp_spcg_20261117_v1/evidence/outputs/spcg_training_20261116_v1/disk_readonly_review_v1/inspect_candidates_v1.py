from pathlib import Path
import json,subprocess,base64,zlib
O=Path(__file__).resolve().parent
code="""from pathlib import Path
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
"""
compile(code,'candidate_metadata','exec');(O/'candidate_remote_source.py').write_text(code,encoding='utf-8')
c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','25','--','/usr/bin/python3','-I','-S','-B','-c',c]
assert len(subprocess.list2cmdline(a).encode())<2048
r=subprocess.run(a,capture_output=True,timeout=30);(O/'candidate_stdout.bin').write_bytes(r.stdout);(O/'candidate_stderr.bin').write_bytes(r.stderr);assert r.returncode==0
d=json.loads(r.stdout);(O/'candidate_metadata_v1.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(count=len(d['files']),largest=sorted(d['files'],key=lambda x:x['bytes'],reverse=True)[:20])))
