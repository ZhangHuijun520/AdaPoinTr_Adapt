import hashlib,json,os,socket,time
from pathlib import Path
start=time.monotonic();used=0;rows=[]
assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
root=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3')
def check(p,digest,size):
 global used
 assert len(rows)<40 and time.monotonic()-start<45
 row={'path':str(p),'expected_bytes':size,'expected_sha256':digest}
 row['exists']=p.exists();row['linked']=any(x.is_symlink() for x in (p,*p.parents))
 if not p.is_file() or row['linked']:
  row['match']=False;rows.append(row);return None
 a=p.stat();used+=a.st_size;assert used<=32*1024**2
 data=p.read_bytes();z=p.stat()
 assert (a.st_size,a.st_mtime_ns,a.st_ino)==(z.st_size,z.st_mtime_ns,z.st_ino)
 row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 row['match']=row['bytes']==size and row['sha256']==digest;rows.append(row)
 return data if row['match'] else None
raw=check(root/'evidence/frozen_scope_v3.json','c6edb9bfcf833d2abf98eb18749d03b49a490579d79475e4823750df6a8311e6',23220)
if raw is not None:
 s=json.loads(raw)
 for r in s['bindings']['candidate']:check(root/r['relative_target'],r['sha256'],r['bytes'])
 for r in s['bindings']['isolated_model_project_sources']:check(root/r['relative_path'],r['sha256'],r['bytes'])
 r=s['bindings']['base_config'];check(root/'base_model.yaml',r['sha256'],r['bytes'])
 check(root/'bcsp_artificial_gpu_preflight_v3.py','7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291',32728)
 for r in s['bindings']['provider']+s['bindings']['environment_metadata']:check(Path(r['path']),r['sha256'],r['bytes'])
planned=['/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1',
 '/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1',
 '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1']
targets=[{'path':p,'exists':Path(p).exists(),'linked':any(x.is_symlink() for x in (Path(p),*Path(p).parents))} for p in planned]
assert time.monotonic()-start<45
print(json.dumps({'status':'ASSETS_MATCH' if len(rows)==30 and all(r['match'] for r in rows) else 'FROZEN_ASSET_DIFFERENCES_RECORDED','files':rows,'hashed_bytes':used,'seconds':time.monotonic()-start,'planned_targets':targets,'server_writes':0,'third_party_imports':0}))
