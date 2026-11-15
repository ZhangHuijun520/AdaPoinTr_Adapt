"""Bounded read-only failure audit: <=32 files/8MiB/60s; no model/GPU execution."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,time,zlib

R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_cuda_preparation_20261114_v1'
O=B/'failed_freeze_hook_review_v1'
Q=B/'pending_transport_v1/payload/SCQ_RF_artificial_cuda_execution_request_v1.json'
QH='85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'
assert hashlib.sha256(Q.read_bytes()).hexdigest()==QH
q=json.loads(Q.read_bytes())
I=q['identity'];root=q['entry']['path'].rsplit('/',1)[0]
prefix='''from pathlib import Path
import socket,os,subprocess,hashlib,json,time
assert socket.gethostname()==HOST and os.getuid()==1000
O=Path(OUTPUT);I=Path(INSTALL)
assert not any(p.is_symlink() for p in (O,*O.parents,I,*I.parents))
assert hashlib.sha256((I/'SCQ_RF_artificial_cuda_execution_request_v1.json').read_bytes()).hexdigest()==QHASH
q=json.loads((I/'SCQ_RF_artificial_cuda_execution_request_v1.json').read_bytes())
'''
values=dict(HOST=I['hostname'],OUTPUT=q['output'],INSTALL=root,QHASH=QH)
class Bind(ast.NodeTransformer):
    def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
prefix=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(prefix))))+'\n'
inventory='''files={};directories={};total=0
related=[q['implementation']['scq_factory'],q['implementation']['lqi_decoder'],next(r for r in q['reused_readonly_bindings'] if r['path']==q['model_root']+'/models/AdaPoinTr.py')]
paths=[]
for root,label in [(O,'output'),(I,'installed')]:
 dirs=['.']
 for p in root.rglob('*'):
  assert not p.is_symlink() and (p.is_dir() or p.is_file()),str(p)
  if p.is_dir():dirs.append(str(p.relative_to(root)));assert len(dirs)<=16
  else:paths.append((label+'/'+str(p.relative_to(root)),p));assert len(paths)<=32
 directories[label]=sorted(dirs)
for i,r in enumerate(related):paths.append(('related/'+str(i)+'_'+Path(r['path']).name,Path(r['path'])))
archive=Path('/home/jovyan/bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz')
for suffix in ['', '.sha256','.bytes','.contents.sha256']:paths.append(('upload/'+archive.name+suffix,Path(str(archive)+suffix)))
assert len(paths)<=32
fp=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
for name,p in paths:
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 before=p.stat();total+=before.st_size;assert total<=8388608 and before.st_size<=2097152
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 after=p.stat();assert fp(before)==fp(after)
 files[name]=dict(path=str(p),bytes=after.st_size,sha256=h.hexdigest(),fingerprint=fp(after))
print(json.dumps(dict(status='BOUNDED_STABLE_FAILURE_INVENTORY',files=files,directories=directories,hashed_bytes=total)))
'''
metadata='''import base64
files={};total=0
for root,label in [(O,'output'),(I,'installed')]:
 for p in root.rglob('*'):
  if not p.is_file():continue
  assert not p.is_symlink() and p.stat().st_size<=2097152
  b=p.read_bytes();total+=len(b);assert len(files)<32 and total<=8388608
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
for i,r in enumerate([q['implementation']['scq_factory'],q['implementation']['lqi_decoder'],next(r for r in q['reused_readonly_bindings'] if r['path']==q['model_root']+'/models/AdaPoinTr.py')]):
 p=Path(r['path']);b=p.read_bytes();total+=len(b);assert total<=8388608 and hashlib.sha256(b).hexdigest()==r['sha256']
 files['related/'+str(i)+'_'+p.name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
print(json.dumps(dict(status='BOUNDED_FAILURE_METADATA_READ',files=files,bytes=total)))
'''
finished='''assert (O/'exit_code.txt').read_text().strip()=='1' and (O/'failure.json').is_file() and not (O/'completion.json').exists()
pid=(O/'worker.pid').read_text().strip();assert pid.isdigit()
p=Path('/proc/'+pid);assert not p.exists() or q['entry']['path'].encode() not in (p/'cmdline').read_bytes()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
a=[x.strip() for x in subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')]
v=q['identity'];assert a==[v['gpu_uuid'],v['gpu_name'],v['driver_version'],str(v['nvidia_smi_memory_total_MiB'])]
print(json.dumps(dict(status='FAILED_EXIT1_TMUX_AND_WORKER_ABSENT',hostname=socket.gethostname(),uid=os.getuid(),GPU=a,worker_PID=pid)))
'''
scripts=[]
for label,source in [('finished',finished),('inventory_before',inventory),('metadata',metadata),('inventory_after',inventory)]:
    code=prefix+source;ast.parse(code,feature_version=(3,8));compile(code,label,'exec')
    blob=base64.b64encode(zlib.compress(code.encode(),9)).decode()
    command=shlex.join([I['python_realpath'],'-I','-S','-B','-c',"import zlib,base64;exec(zlib.decompress(base64.b64decode("+repr(blob)+")))"])
    assert len(command.encode())<=2048,(label,len(command.encode()))
    scripts.append((label,code,command))


def save(p,j):
    with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,allow_nan=False)


if '--static' in __import__('sys').argv:
    O.mkdir()
    for label,code,command in scripts:
        with (O/(label+'.remote.py')).open('x',encoding='utf-8') as f:f.write(code)
    save(O/'scope_v1.json',dict(status='READONLY_FAILURE_FREEZE_AND_HOOK_CONTRACT_SCOPE',request_sha256=QH,
         max_files=32,max_unique_content_bytes=8388608,remote_calls=4,overall_wall_seconds=60,
         max_command_bytes=max(len(x[2].encode()) for x in scripts),controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         server_writes=0,model_imports=0,forward=0,CUDA_context=0,request_reuse=False))
    print(json.dumps(dict(status='READONLY_AUDIT_SCRIPTS_STATIC_PASS',calls=4,max_bytes=max(len(x[2].encode()) for x in scripts))))
else:
    assert json.loads((O/'scope_v1.json').read_bytes())['controller_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    start=time.monotonic();stage='before_first_call'
    try:
        for label,code,command in scripts:
            stage=label;remaining=60-(time.monotonic()-start);assert remaining>0
            x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','15','--',command],capture_output=True,timeout=min(remaining,20))
            for kind,data in [('stdout',x.stdout),('stderr',x.stderr)]:
                with (O/(label+'_'+kind+'.bin')).open('xb') as f:f.write(data)
            assert x.returncode==0,(label,x.stdout.decode(errors='replace')[-1500:])
            j=json.loads(x.stdout);save(O/(label+'_result_v1.json'),j)
            if label=='metadata':
                for name,row in j['files'].items():
                    p=O/'downloads'/name;p.parent.mkdir(parents=True,exist_ok=True)
                    raw=base64.b64decode(row['base64']);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
                    with p.open('xb') as f:f.write(raw)
            print(json.dumps(dict(stage=label,status=j['status'])),flush=True)
        save(O/'collection_complete_v1.json',dict(status='READONLY_FAILURE_COLLECTION_COMPLETE',seconds=time.monotonic()-start,server_writes=0,new_forward=0))
    except BaseException as exc:
        save(O/'collection_failed_v1.json',dict(status='FAILED_STOP_NO_RETRY',stage=stage,error=repr(exc)));raise
