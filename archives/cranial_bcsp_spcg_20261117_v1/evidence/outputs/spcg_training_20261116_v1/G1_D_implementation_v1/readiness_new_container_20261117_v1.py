from pathlib import Path
import json,hashlib,subprocess,base64,zlib
V=Path(__file__).resolve().parent;O=V/'resource_rebind_yxwd3w_readonly_v1';O.mkdir()
q=json.loads((V/'pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v1.json').read_text(encoding='utf-8'))
d=json.loads((V/'delivery_receipt_v1.json').read_text(encoding='utf-8'));a=Path(d['archive']['path']);rows=[dict(path='/home/jovyan/'+p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [a,*[Path(str(a)+x) for x in ['.sha256','.bytes','.contents.sha256']]]]
mapping=json.loads((V/'pending_transport_v1/installation_mapping_v1.json').read_text(encoding='utf-8'))
code="""from pathlib import Path
import os,json,socket,hashlib,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');assert not any(x.is_symlink() for x in (p,*p.parents));s=os.statvfs(p)
r=dict(hostname=socket.gethostname(),uid=os.getuid(),available_bytes=s.f_bavail*s.f_frsize,required_bytes=int(8.5*1024**3),uploads=[],targets=[])
for x in ROWS:
 f=Path(x['path']);v=dict(path=str(f),exists=f.exists(),linked=any(y.is_symlink() for y in (f,*f.parents)))
 if v['exists'] and not v['linked']:v.update(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest());v['matches']=v['bytes']==x['bytes'] and v['sha256']==x['sha256']
 r['uploads'].append(v)
for name in TARGETS:
 f=Path(name);r['targets'].append(dict(path=name,exists=f.exists(),linked=any(x.is_symlink() for x in (f,*f.parents))))
g=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,timeout=10);r['GPU']=dict(returncode=g.returncode,stdout=g.stdout.decode(errors='replace'),stderr=g.stderr.decode(errors='replace'))
print(json.dumps(r))
""".replace('ROWS',repr(rows)).replace('TARGETS',repr([mapping['remote_root'],q['output']]))
compile(code,'newcontainer','exec');(O/'remote_source.py').write_text(code,encoding='utf-8')
c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','25','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(args).encode())<=2048
r=subprocess.run(args,capture_output=True,timeout=30);(O/'stdout.bin').write_bytes(r.stdout);(O/'stderr.bin').write_bytes(r.stderr);assert r.returncode==0
v=json.loads(r.stdout);(O/'result.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(v))
