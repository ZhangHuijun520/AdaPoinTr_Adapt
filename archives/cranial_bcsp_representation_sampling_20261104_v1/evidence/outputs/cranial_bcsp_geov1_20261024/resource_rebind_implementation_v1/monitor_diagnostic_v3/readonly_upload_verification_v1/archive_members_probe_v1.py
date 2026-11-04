import os,socket,json,hashlib,tarfile,stat,time
from pathlib import Path,PurePosixPath
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
n='/home/jovyan/bcsp_foldc_8192_monitor_diagnostic_v3_supplement_v1'
def bound(suffix,digest):
 p=Path(n+suffix);assert all(stat.S_ISDIR(x.lstat().st_mode) for x in p.parents)
 assert stat.S_ISREG(p.lstat().st_mode) and p.stat().st_size<=65536
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest;return raw
q=json.loads(bound('.installation_map.json','7659ab863df5148c09f59917d9df74a0936b916e09e9f79203368cee37bac9b2'))
bound('.tar.gz','f165a848f59926b608194c18f8a936be7afc7b495e4d5a78bba7d7ebae0d87b4')
expected={r['archive_member']:r for r in q['installation_map']};rows=[]
with tarfile.open(n+'.tar.gz','r:gz') as t:
 ms=t.getmembers();assert len(ms)==len({m.name for m in ms})==len(expected)==7 and {m.name for m in ms}==set(expected)
 for m in ms:
  assert m.isfile() and not m.issym() and not m.islnk() and m.mode==420 and m.size==expected[m.name]['bytes'] and m.size<=65536
  p=PurePosixPath(m.name);assert not p.is_absolute() and '..' not in p.parts
  raw=t.extractfile(m).read();h=hashlib.sha256(raw).hexdigest();assert h==expected[m.name]['sha256']
  rows.append(dict(member=m.name,bytes=len(raw),sha256=h))
  assert time.monotonic()-s<20
assert sum(x['bytes'] for x in rows)==39036
print(json.dumps(dict(status='UPLOAD_SEVEN_MEMBERS_PASS',members=rows,server_writes=0,extracted_files=0,seconds=time.monotonic()-s)))
