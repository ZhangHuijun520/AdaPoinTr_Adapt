import os,socket,json,hashlib,tarfile,time
from pathlib import Path,PurePosixPath
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
n='/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1'
def bound(suffix,digest):
 p=Path(n+suffix);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size<=65536
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest;return raw
q=json.loads(bound('.installation_map.json','93d5ca2e34ddf39a5ecc40e53d8610b1c05d35ba1ead5082f28947f6119f6332'))
bound('.tar.gz','278e2678c5af9da2fd18b08cbf27b73ee6f2e48c4dbc42f0382a907417893987')
expected={r['archive_member']:r for r in q['installation_map']};rows=[]
with tarfile.open(n+'.tar.gz','r:gz') as t:
 ms=t.getmembers();assert len(ms)==len({m.name for m in ms})==len(expected)==10 and {m.name for m in ms}==set(expected)
 for m in ms:
  assert m.isfile() and not m.issym() and not m.islnk() and m.mode==420 and m.size==expected[m.name]['bytes'] and m.size<=65536
  p=PurePosixPath(m.name);assert not p.is_absolute() and '..' not in p.parts
  raw=t.extractfile(m).read();d=hashlib.sha256(raw).hexdigest();assert d==expected[m.name]['sha256'];rows.append(dict(member=m.name,bytes=len(raw),sha256=d))
assert sum(r['bytes'] for r in rows)==87842 and time.monotonic()-s<25
print(json.dumps(dict(status='UPLOAD_ARCHIVE_MEMBERS_PASS',members=rows,server_writes=0,extracted_files=0,seconds=time.monotonic()-s)))
