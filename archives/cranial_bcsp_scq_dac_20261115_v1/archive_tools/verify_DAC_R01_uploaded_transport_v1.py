"""One bounded readonly remote stream verification; never extracts/installs or loads models."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,zlib
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_dac_r01_preparation_20261115_v1';O=B/'uploaded_transport_readonly_v1';O.mkdir(exist_ok=True)
receipt=json.loads((R/'server_uploads/scq_dac_r1_frozen20_20261115_v1/transport_verification_receipt_v1.json').read_bytes())
pins={Path(r['path']).name:{k:r[k] for k in ('bytes','sha256')} for r in [receipt['archive']]+receipt['sidecars']}
qsha=receipt['request_sha256'];archive=Path(receipt['archive']['path']).name
source='''from pathlib import Path,PurePosixPath
import os,socket,json,hashlib,tarfile,time
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
T=time.monotonic();total=0
def digest(f):
 global total
 h=hashlib.sha256();size=0
 for b in iter(lambda:f.read(4194304),b''):
  total+=len(b);size+=len(b);assert total<=2147483648 and time.monotonic()-T<55;h.update(b)
 return size,h.hexdigest()
pins='''+repr(pins)+'''
name='''+repr(archive)+''';QSHA='''+repr(qsha)+'''
home=Path('/home/jovyan');records=[]
for n,r in pins.items():
 p=home/n;assert not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file()
 s=p.stat();assert s.st_size==r['bytes']
 with p.open('rb') as f:a=digest(f)
 assert a==(r['bytes'],r['sha256']),n
 assert (s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)
 records.append(dict(name=n,bytes=a[0],sha256=a[1]))
p=home/name
assert (home/(name+'.sha256')).read_text().split()[0]==pins[name]['sha256']
assert int((home/(name+'.bytes')).read_text())==pins[name]['bytes']
catalog={}
for line in (home/(name+'.contents.sha256')).read_text().splitlines():
 h,n=line.split('  ',1);assert n not in catalog;catalog[n]=h
assert len(catalog)==30
seen={};metadata={}
with tarfile.open(p,'r:gz') as t:
 for m in t:
  n=m.name;parts=PurePosixPath(n);assert m.isfile() and not parts.is_absolute() and '..' not in parts.parts and n in catalog and n not in seen
  if n in ('metadata/install_manifest_v1.json','payload/SCQ_DAC_R1_execution_request_v1.json'):
   assert m.size<65536;raw=t.extractfile(m).read();a=(len(raw),hashlib.sha256(raw).hexdigest());metadata[n]=json.loads(raw)
  else:
   with t.extractfile(m) as f:a=digest(f)
  assert a==(m.size,catalog[n]),n;seen[n]=dict(bytes=a[0],sha256=a[1])
assert set(seen)==set(catalog)
q=metadata['payload/SCQ_DAC_R1_execution_request_v1.json'];manifest=metadata['metadata/install_manifest_v1.json']
assert seen['payload/SCQ_DAC_R1_execution_request_v1.json']['sha256']==QSHA
assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
assert q['calls']['native']==20 and q['calls']['decoder_only']==40 and q['optimizer_steps']==q['backward']==q['loss']==0
assert manifest['request_sha256']==QSHA and len(manifest['files'])==28
root=PurePosixPath(manifest['root']);assert str(root)=='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1'
for r in manifest['files']:
 assert str(PurePosixPath(r['target']).relative_to(root))==r['member'].removeprefix('payload/')
 assert seen[r['member']]==dict(bytes=r['bytes'],sha256=r['sha256'])
print(json.dumps(dict(status='UPLOADED_FOUR_FILES_AND_ALL30_MEMBERS_VERIFIED',hostname=socket.gethostname(),files=records,members=seen,payload_files=28,request_sha256=QSHA,request_status=q['status'],streamed_bytes=total,seconds=time.monotonic()-T,server_writes=0,extractions=0,installs=0,checkpoint_loads=0,forwards=0)))
'''
prefix,tail=source.split('\np=home/name\n',1)
phase1=prefix+"\nprint(json.dumps(dict(status='FOUR_UPLOAD_FILES_HASH_PASS',files=records,seconds=time.monotonic()-T,server_writes=0)))\n"
common=source.split("home=Path('/home/jovyan');records=[]",1)[0]
common=common.replace(repr(pins),repr({k:pins[k] for k in (archive,archive+'.contents.sha256')}))
phase2=common+"home=Path('/home/jovyan');records=[];p=home/name\nwith p.open('rb') as f:assert digest(f)==(pins[name]['bytes'],pins[name]['sha256'])\ns=p.stat()\nwith (home/(name+'.contents.sha256')).open('rb') as f:assert digest(f)==(pins[name+'.contents.sha256']['bytes'],pins[name+'.contents.sha256']['sha256'])\n"+tail
phase2=phase2.replace("print(json.dumps(dict(status=", "assert (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns)\nprint(json.dumps(dict(status=")
commands=[]
for label,src in [('four_files',phase1),('archive_members',phase2)]:
 ast.parse(src);blob=base64.b85encode(zlib.compress(src.encode(),9)).decode();wrapper='import base64,zlib;exec(zlib.decompress(base64.b85decode('+repr(blob)+')))'
 command=shlex.join(['/usr/bin/python3','-I','-S','-B','-c',wrapper]);assert len(command.encode())<=2048,(label,len(command.encode()))
 (O/(label+'_source_v1.py')).write_text(src,encoding='utf-8');commands.append((label,command))
with (O/'frozen_call_v1.json').open('x') as f:json.dump(dict(calls=[dict(phase=l,command_bytes=len(c.encode()),timeout_seconds=60) for l,c in commands],file_targets=list(pins),request_sha256=qsha,server_writes=0),f,indent=2)
answers={}
for label,command in commands:
 x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--',command],capture_output=True,timeout=75)
 for k,v in [('stdout',x.stdout),('stderr',x.stderr)]:
  with (O/(label+'_'+k+'_v1.bin')).open('xb') as f:f.write(v)
 assert x.returncode==0,('READONLY_UPLOAD_VERIFICATION_FAILED_STOP',label,x.returncode,x.stdout.decode(errors='replace')[-1500:],x.stderr.decode(errors='replace')[-1500:])
 answers[label]=json.loads(x.stdout)
v=answers['archive_members'];v['files']=answers['four_files']['files'];assert v['request_sha256']==qsha and len(v['members'])==30
with (O/'upload_verification_v1.json').open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v[k] for k in ('status','hostname','payload_files','request_sha256','seconds','server_writes','installs','forwards')}))
