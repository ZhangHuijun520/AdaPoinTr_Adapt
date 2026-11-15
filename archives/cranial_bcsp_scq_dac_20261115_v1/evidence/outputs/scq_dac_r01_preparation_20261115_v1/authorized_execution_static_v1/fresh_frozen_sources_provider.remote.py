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

records=list(q['implementation'].values())+[q[k] for k in ('entry','helper','static_config','preflight_scope','initialization','rf_initialization','input_index')]+q['dependencies']
for r in records:exact(r)
s=json.loads(Path(q['preflight_scope']['path']).read_bytes());b=s['bindings'];root=Path(q['model_root'])
for r in b['candidate']:exact(dict(r,path=str(root/r['relative_target'])))
for r in b['isolated_model_project_sources']:exact(dict(r,path=str(root/r['relative_path'])))
exact(dict(b['base_config'],path=str(root/'base_model.yaml')))
for r in b['provider']+b['environment_metadata']:exact(r)
v=dict(link='/usr/share/zoneinfo/UTC',link_text='Etc/UTC',target='/usr/share/zoneinfo/Etc/UTC',bytes=118,sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a')
assert Path(v['link']).is_symlink() and os.readlink(v['link'])==v['link_text'] and str(Path(v['link']).resolve())==v['target']
assert not any(p.is_symlink() for p in Path(v['link']).parents);exact(dict(path=v['target'],bytes=v['bytes'],sha256=v['sha256']))
print(json.dumps(dict(status='FROZEN_CODE_PROVIDER_AND_EXACT_DEPENDENCIES_PASS',records=list(seen.values()),hashed_bytes=used,UTC_contract=v,seconds=time.monotonic()-T,package_imports=0,server_writes=0)))
