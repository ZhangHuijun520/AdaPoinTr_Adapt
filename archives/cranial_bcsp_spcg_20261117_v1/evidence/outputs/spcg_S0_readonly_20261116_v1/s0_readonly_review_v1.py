"""One bounded S0 document/metadata review; never import model or read NPZ/checkpoint payload."""
from pathlib import Path
import json,hashlib,base64,zlib,subprocess,time,sys,stat
W=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent
P='/home/jovyan/adapointr_work/PoinTr'
HOST='shu-common-25721452-notebook-lwwgl9-0'
ctx=json.loads((W/'outputs/scq_rive_training_implementation_20261115_v1/implementation_context_v1.json').read_text(encoding='utf-8'))
old=json.loads((W/'outputs/scq_RIVE_server_cleanup_20261116_v1/authorized_execution_v1/server_preserved_after.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
keys=['encoder','factory','lqi_decoder','lqi_factory','runtime','contract','budget_parent','timezone']
assets=[ctx['candidate']['implementation'][k] for k in keys]
meta=['static_training_config_v1.json','qualified_SCQ_C_8192_v1.json','qualified_SCQ_D_8192_v1.json','real_data_qc_verification_v1.json','manifest_8192.jsonl','fold_binding.json','shared_order_foldC_seed0_v1.json','shared_order_foldD_seed0_v1.json']
for n in meta:
 p=P+'/third_party/bcsp_scq_foldC_training_20261113_v1/'+n; assets.append(dict(path=p,**{k:old['files'][p][k] for k in ('bytes','sha256')}))
model_local=W/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot/models/AdaPoinTr.py'
assets.append(dict(path=ctx['candidate']['model_root']+'/models/AdaPoinTr.py',bytes=model_local.stat().st_size,sha256=sha(model_local)))
for d in ctx['candidate']['dependencies'][:3]:assets.append(d)
assert len(assets)==20 and sum(x['bytes'] for x in assets)<8*1024**2
scope=dict(status='FROZEN_READONLY_S0_NO_IMPLEMENTATION',hostname=HOST,project=P,files=assets,max_content_files=20,max_content_bytes=8*1024**2,max_stat_NPZ_files=630,remote_total_budget_seconds=60,per_call_timeout_seconds=15,command_bytes_max=2048,real_payload_reads=0,checkpoint_loads=0,model_imports=0,server_writes=0,tests=0,forward=0)
save('S0_readonly_scope_v1.json',scope)
if '--prepare-only' in sys.argv:print(json.dumps(dict(files=len(assets),bytes=sum(x['bytes'] for x in assets))));sys.exit(0)
assert not (O/'S0_remote_result_v1.json').exists(), 'no repeated audit'
start=time.monotonic(); phases=[]
def remote(label,code):
 assert time.monotonic()-start<60,'total budget'
 b=base64.b64encode(zlib.compress(code.encode())).decode()
 c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
 args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',c]
 assert len(subprocess.list2cmdline(args).encode())<=2048,'short entry limit'
 (O/(label+'_remote_source.py')).write_text(code,encoding='utf-8')
 r=subprocess.run(args,capture_output=True,timeout=min(15,60-(time.monotonic()-start)))
 (O/(label+'_stdout.bin')).write_bytes(r.stdout);(O/(label+'_stderr.bin')).write_bytes(r.stderr)
 save(label+'_transport.json',dict(returncode=r.returncode,command_bytes=len(subprocess.list2cmdline(args).encode()),stdout_sha256=hashlib.sha256(r.stdout).hexdigest(),stderr_sha256=hashlib.sha256(r.stderr).hexdigest()))
 assert r.returncode==0,(label,r.returncode)
 v=json.loads(r.stdout.decode('utf-8'));phases.append(dict(label=label,result=v));return v
identity="""import os,socket,json,subprocess
from pathlib import Path
p=Path('/home/jovyan/adapointr_work/PoinTr');assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
assert p.resolve()==p and p.is_dir();os.chdir(p)
s=os.statvfs(p)
g=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader'],capture_output=True,timeout=5)
t=subprocess.run(['git','status','--short','--untracked-files=no'],capture_output=True,timeout=5)
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),cwd=os.getcwd(),available_bytes=s.f_bavail*s.f_frsize,gpu_returncode=g.returncode,gpu_stdout=g.stdout.decode(errors='replace'),gpu_stderr=g.stderr.decode(errors='replace'),git_returncode=t.returncode,git_stdout=t.stdout.decode(errors='replace')[:8000],git_stderr=t.stderr.decode(errors='replace')[:1000])))
"""
try:
 ident=remote('01_identity',identity)
 for j in range(0,len(assets),5):
  rows=assets[j:j+5]
  body="import json,hashlib,stat\nfrom pathlib import Path\na="+repr(rows)+"\nr=[]\n"
  body+="for x in a:\n p=Path(x['path']);assert not any(v.is_symlink() for v in (p,*p.parents));s=p.stat();assert stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'];b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert h==x['sha256'],str(p);r.append(dict(path=str(p),bytes=len(b),sha256=h))\nprint(json.dumps(r))\n"
  remote('02_assets_'+str(j//5),body)
 data="""import json,stat,hashlib
from pathlib import Path
p=Path('/home/jovyan/adapointr_work/PoinTr');m=p/'third_party/bcsp_scq_foldC_training_20261113_v1';f=json.loads((m/'fold_binding.json').read_text())['folds'];r={}
for fold in ['C','D']:
 root=p/('data/bcsp_geov1_fold'+fold.lower()+'_8192_seed0_v1/points');assert root.is_dir() and not any(v.is_symlink() for v in (root,*root.parents));rows=[]
 for s in f[fold]['train_sources']:
  for t in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']:
   q=root/('train__'+s.split(':')[1]+'__'+t+'_8192.npz');v=q.lstat();assert stat.S_ISREG(v.st_mode) and v.st_size>0;rows.append([str(q),v.st_size,v.st_mtime_ns])
 assert len(rows)==315;r[fold]=dict(root=str(root),files=len(rows),bytes=sum(x[1] for x in rows),stat_rows_sha256=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),rows=rows)
print(json.dumps(r))
"""
 d=remote('03_data_stat_only',data)
 # All 420 dev accesses follow the opposite-fold training roots; no NPZ opens here.
 status='S0_REMOTE_SOURCE_HASH_AND_METADATA_PASS_NO_EXECUTION_ADMISSION'
except Exception as e:
 status='S0_READONLY_STOP';save('S0_remote_result_v1.json',dict(status=status,error=repr(e),phases=phases,seconds=time.monotonic()-start));raise
save('S0_remote_result_v1.json',dict(status=status,phases=phases,seconds=time.monotonic()-start,operations=dict(server_writes=0,NPZ_payload_reads=0,checkpoint_loads=0,model_imports=0,tests=0,forward=0)))
print(json.dumps(dict(status=status,seconds=time.monotonic()-start,available_bytes=ident['available_bytes'],hashed_files=len(assets),hashed_bytes=sum(x['bytes'] for x in assets),NPZ_stat_files=630)))
