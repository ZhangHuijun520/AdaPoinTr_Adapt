"""Single read-only upload/identity gate. No installation or GPU."""
from pathlib import Path
import base64,zlib,subprocess,json,hashlib
S=Path(__file__).resolve().parent;O=S/'authorized_upload_readiness_v3';O.mkdir()
d=json.loads((S/'delivery_receipt_v3.json').read_text(encoding='utf-8'))
d['sidecars']=[dict(path=str(Path(d['archive']['path']+x)),bytes=Path(d['archive']['path']+x).stat().st_size,sha256=hashlib.sha256(Path(d['archive']['path']+x).read_bytes()).hexdigest()) for x in ['.sha256','.bytes','.contents.sha256']]
rows=[dict(path='/home/jovyan/'+Path(x['path']).name,bytes=x['bytes'],sha256=x['sha256']) for x in [d['archive'],*d['sidecars']]]
code="""import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=ROWS
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
""".replace('ROWS',repr(rows))
b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',c]
assert len(subprocess.list2cmdline(args).encode())<=2048
(O/'remote_source.py').write_text(code,encoding='utf-8')
p=subprocess.run(args,capture_output=True,timeout=30);(O/'stdout.bin').write_bytes(p.stdout);(O/'stderr.bin').write_bytes(p.stderr)
assert p.returncode==0,p.returncode
v=json.loads(p.stdout.decode());(O/'result.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(v))
