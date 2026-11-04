import os,socket,json,hashlib,stat
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
c=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1')
def read(p):
 for a in p.parents:assert stat.S_ISDIR(a.lstat().st_mode),'parent '+str(a)
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=2097152
 raw=p.read_bytes();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ino)
 return raw
raw=read(c/'control_train_v3/training_execution_request_v1.json')
assert hashlib.sha256(raw).hexdigest()=='5cf2b4f93eb903c77702e9b493a8e8dd2700ceda448d77ea518ecc4c76e9ee0c'
q=json.loads(raw)
pins=[*q['implementation'].values(),q['static_config'],q['order_plan'],q['GPU_audit'],q['preflight_scope'],q['resource_rebind'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values()]
rows=[]
for r in pins:
 raw=read(Path(r['path']));assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'hash '+r['path']
 rows.append(r)
p=Path(q['output'])
print(json.dumps(dict(status='EXACT_REUSED_BINDINGS_PASS',files=rows,parent_initialization=json.loads(read(p/'initialization.json')),parent_completion=json.loads(read(p/'completion.json')),parent_exit=read(p/'exit_code.txt').decode().strip(),server_writes=0,CUDA_calls=0)))
