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
pins={'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz': {'bytes': 906620311, 'sha256': '350717ccaa584b93faa49b808355a762a94563f842f9e5f3352bf9a7973e0e01'}, 'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz.sha256': {'bytes': 116, 'sha256': '95f38be8c7d7c905a18fa01962590d40f1748f711c7e2441909f9c8a4c426393'}, 'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz.bytes': {'bytes': 11, 'sha256': '03edefedf07e76d0d649d875924c389ea4c518e4275bfbaabd852d7bfd3d9d19'}, 'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz.contents.sha256': {'bytes': 3453, 'sha256': 'f16e5c10713a91fa93479f85d93103fcb45acfb7248b06200c722865e0140bd3'}}
name='scq_dac_r1_frozen20_transport_20261115_v1.tar.gz';QSHA='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'
home=Path('/home/jovyan');records=[]
for n,r in pins.items():
 p=home/n;assert not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file()
 s=p.stat();assert s.st_size==r['bytes']
 with p.open('rb') as f:a=digest(f)
 assert a==(r['bytes'],r['sha256']),n
 assert (s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)
 records.append(dict(name=n,bytes=a[0],sha256=a[1]))
print(json.dumps(dict(status='FOUR_UPLOAD_FILES_HASH_PASS',files=records,seconds=time.monotonic()-T,server_writes=0)))
