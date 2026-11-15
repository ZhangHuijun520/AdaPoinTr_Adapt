from pathlib import Path,PurePosixPath
import os,socket,json,hashlib,tarfile,time
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
T=time.monotonic();total=0
def digest(f):
 global total
 h=hashlib.sha256();size=0
 for b in iter(lambda:f.read(4194304),b''):
  total+=len(b);size+=len(b);assert total<=2147483648 and time.monotonic()-T<55;h.update(b)
 return size,h.hexdigest()
pins={'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz': {'bytes': 906620311, 'sha256': '350717ccaa584b93faa49b808355a762a94563f842f9e5f3352bf9a7973e0e01'}, 'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz.contents.sha256': {'bytes': 3453, 'sha256': 'f16e5c10713a91fa93479f85d93103fcb45acfb7248b06200c722865e0140bd3'}}
name='scq_dac_r1_frozen20_transport_20261115_v1.tar.gz';QSHA='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'
home=Path('/home/jovyan');records=[];p=home/name
with p.open('rb') as f:assert digest(f)==(pins[name]['bytes'],pins[name]['sha256'])
s=p.stat()
with (home/(name+'.contents.sha256')).open('rb') as f:assert digest(f)==(pins[name+'.contents.sha256']['bytes'],pins[name+'.contents.sha256']['sha256'])
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
assert (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns)
print(json.dumps(dict(status='UPLOADED_FOUR_FILES_AND_ALL30_MEMBERS_VERIFIED',hostname=socket.gethostname(),files=records,members=seen,payload_files=28,request_sha256=QSHA,request_status=q['status'],streamed_bytes=total,seconds=time.monotonic()-T,server_writes=0,extractions=0,installs=0,checkpoint_loads=0,forwards=0)))
