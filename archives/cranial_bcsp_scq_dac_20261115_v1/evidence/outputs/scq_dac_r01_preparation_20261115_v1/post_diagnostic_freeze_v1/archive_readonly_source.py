from pathlib import Path
import os,socket,json,hashlib,time,subprocess,base64
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
I=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1')
Q=I/'SCQ_DAC_R1_execution_request_v1.json'
assert hashlib.sha256(Q.read_bytes()).hexdigest()=='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'
q=json.loads(Q.read_bytes());O=Path(q['output']);T=time.monotonic()
assert not any(p.is_symlink() for root in (I,O) for p in (root,*root.parents))
def h(p):
 a=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):assert time.monotonic()-T<55;a.update(b)
 return a.hexdigest()

import tarfile
c=json.loads((O/'completion.json').read_bytes());a=c['archive'];p=Path(a['path']);assert p.parent==O and p.stat().st_size==a['bytes'] and h(p)==a['sha256']
rows={r['name']:r for r in a['members']};assert len(rows)==len(a['members'])==24
assert (O/(p.name+'.sha256')).read_text().split()[0]==a['sha256'] and int((O/(p.name+'.bytes')).read_text())==a['bytes']
catalog={n:d for d,n in (l.split('  ',1) for l in (O/(p.name+'.contents.sha256')).read_text().splitlines())};assert len(catalog)==24
assert catalog=={n:r['sha256'] for n,r in rows.items()}
seen={};notes=[]
with tarfile.open(p,'r|gz') as t:
 for m in t:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.name not in seen and m.name in rows
  raw=t.extractfile(m).read();r=rows[m.name];assert len(raw)==m.size==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
  current=(O/m.name).read_bytes()
  if m.name=='resources.jsonl':
   assert current.startswith(raw);extra=current[len(raw):].splitlines();assert len(extra)==1 and json.loads(extra[0])['phase']=='archived'
   notes.append('archive resources is exact stable prefix; final archived sample added after packing by frozen entry')
  else:assert current==raw
  seen[m.name]=r
print(json.dumps(dict(status='ARCHIVE24_STREAM_MEMBERS_AND_SIDECARS_PASS',archive=dict(path=str(p),bytes=p.stat().st_size,sha256=a['sha256']),members=seen,notes=notes,server_writes=0)))
