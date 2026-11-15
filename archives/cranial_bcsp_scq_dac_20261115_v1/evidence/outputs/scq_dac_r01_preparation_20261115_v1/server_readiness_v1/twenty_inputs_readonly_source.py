from pathlib import Path
import os,socket,hashlib,json,time,subprocess,shutil,ast
T=time.monotonic();used=0;seen={};last=None
P=Path('/home/jovyan/adapointr_work/PoinTr')
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
def clean(p):
 p=Path(p);assert p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),str(p);return p
def exact(r):
 global used,last
 p=clean(r['path']);last=str(p)
 if str(p) in seen:
  assert (r['bytes'],r['sha256'])==(seen[str(p)]['bytes'],seen[str(p)]['sha256']);return p
 s=p.stat();assert p.is_file() and s.st_size==r['bytes'],str(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):
   used+=len(b);assert used<=805306368 and time.monotonic()-T<55;h.update(b)
 assert h.hexdigest()==r['sha256'],str(p)
 assert (s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)
 seen[str(p)]={'path':str(p),'bytes':r['bytes'],'sha256':r['sha256']};assert len(seen)<=96;return p
old=P/'third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json'
q=json.loads(exact(dict(path=str(old),bytes=18606,sha256='5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9')).read_bytes())

index=json.loads(exact(q['input_index']).read_bytes());wanted=set([('Requery_C', 'train__001__bilateral'), ('Requery_C', 'train__081__bilateral'), ('Requery_C', 'train__053__frontoorbital'), ('Requery_C', 'train__094__frontoorbital'), ('Requery_C', 'train__012__parietotemporal'), ('Requery_C', 'train__025__parietotemporal'), ('Requery_C', 'train__012__random_1'), ('Requery_C', 'train__042__random_1'), ('Requery_C', 'train__025__random_2'), ('Requery_C', 'train__076__random_2'), ('Requery_D', 'train__005__bilateral'), ('Requery_D', 'train__037__bilateral'), ('Requery_D', 'train__008__frontoorbital'), ('Requery_D', 'train__087__frontoorbital'), ('Requery_D', 'train__004__parietotemporal'), ('Requery_D', 'train__044__parietotemporal'), ('Requery_D', 'train__052__random_1'), ('Requery_D', 'train__079__random_1'), ('Requery_D', 'train__062__random_2'), ('Requery_D', 'train__069__random_2')])
rows=[r for r in index['inputs'] if (r['run'],r['case_id']) in wanted]
assert len(rows)==20 and {(r['run'],r['case_id']) for r in rows}==wanted
for r in rows:exact(r['input'])
print(json.dumps(dict(status='EXACT20_INPUT_BYTES_HASHES_PASS_NO_NPZ_DECODE',records=list(seen.values()),rows=[{k:r[k] for k in ('run','fold','case_id','input','normalization')} for r in rows],hashed_bytes=used,seconds=time.monotonic()-T,NPZ_decodes=0,server_writes=0)))
