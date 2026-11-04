import hashlib,json,os,socket,tarfile,time
from pathlib import Path,PurePosixPath
start=time.monotonic()
assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
B=Path('/home/jovyan');N='bcsp_foldc_8192_train_inputs_v1'
z=B/(N+'.tar.gz');m=B/(N+'.contents.sha256')
assert all(p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) for p in (z,m))
a=z.stat();assert a.st_size==49773476
h=hashlib.sha256()
with z.open('rb') as f:
 for block in iter(lambda:f.read(1048576),b''):h.update(block)
assert h.hexdigest()=='fc3c4daa64f7a90ff6396d039c43344ab4d07947d12b675c1ecd4d6c54a08c0d'
raw=m.read_bytes();assert hashlib.sha256(raw).hexdigest()=='1d5f43673c76b93d3195aad25e19de4a229fdc2c23505395d993c548175b823e'
lines=[s.split('  ',1) for s in raw.decode('ascii').splitlines()]
expected={name:digest for digest,name in lines};assert len(lines)==len(expected)==327
rows=[];seen=set();total=0
with tarfile.open(z,'r|gz') as t:
 for info in t:
  assert time.monotonic()-start<45 and len(rows)<327
  name=PurePosixPath(info.name)
  assert info.isfile() and not info.issym() and not info.islnk() and not info.isdev()
  assert not name.is_absolute() and '..' not in name.parts and '\\' not in info.name
  assert info.name not in seen and info.name in expected and 0<info.size<=4*1024**2
  seen.add(info.name);total+=info.size;assert total<=64*1024**2
  data=t.extractfile(info).read();digest=hashlib.sha256(data).hexdigest()
  assert len(data)==info.size and digest==expected[info.name],info.name
  rows.append({'member':info.name,'bytes':info.size,'sha256':digest})
assert seen==set(expected) and len(rows)==327 and total==51686451
assert sum(r['member'].startswith('data/points/') and r['member'].endswith('_8192.npz') for r in rows)==315
assert sum(r['member'].startswith('code/') for r in rows)==12
b=z.stat();assert (a.st_size,a.st_mtime_ns,a.st_ino)==(b.st_size,b.st_mtime_ns,b.st_ino)
assert time.monotonic()-start<45
print(json.dumps({'status':'UPLOADED_ARCHIVE_EXACT_MEMBERS_PASS','members':rows,'uncompressed_bytes':total,'seconds':time.monotonic()-start,'server_writes':0,'filesystem_extraction':False,'NPZ_decoding':False,'model_or_test_calls':0}))
