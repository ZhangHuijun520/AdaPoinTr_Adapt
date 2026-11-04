import hashlib,json,os,socket,stat,subprocess,time
from pathlib import Path
start=time.monotonic();used=0;rows=[]
root=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v2')
assert socket.gethostname()=='shu-common-25721452-notebook-o9mz8z-0' and os.getuid()==1000
def read(p):
 global used
 assert time.monotonic()-start<45 and len(rows)<64,str(p)
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 a=p.stat();used+=a.st_size;assert used<=32*1024**2,str(p)
 b=p.read_bytes();z=p.stat();assert (a.st_size,a.st_mtime_ns,a.st_ino)==(z.st_size,z.st_mtime_ns,z.st_ino),str(p)
 rows.append({'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mtime_ns':z.st_mtime_ns,'mode':stat.S_IMODE(z.st_mode),'uid':z.st_uid})
 return b
m=read(Path('/home/jovyan/bcsp_gpu_preflight_v2.contents.sha256'))
assert hashlib.sha256(m).hexdigest()=='416b81e0c8320d5dd8978922db1b6a4347535c1bb7b58cfe52c32fa102736e3d'
manifest=[line.split('  ',1) for line in m.decode().splitlines()];assert len(manifest)==26
for h,n in manifest:assert hashlib.sha256(read(root/n)).hexdigest()==h,n
q=json.loads((root/'evidence/execution_request_v2.json').read_text(encoding='utf-8'))
for r in q['future_limited_deployment']['scope_provider_bindings']+q['future_limited_deployment']['scope_environment_metadata_bindings']:
 b=read(Path(r['path']));assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],r['path']
c=q['future_control_paths'];marker=json.loads(read(Path(c['attempt_marker'])))
assert marker['request_sha256']=='18432038d32c4857452c96f0795dd4b072a57fa9d38916cf87e10e8215700bc7'
out=Path(c['summary']).parent;text={};dirs=0
for parent,ds,fs in os.walk(out,followlinks=False):
 dirs+=1;assert dirs<=32 and len(Path(parent).relative_to(out).parts)<=6
 for n in ds:assert not (Path(parent)/n).is_symlink()
 for n in fs:
  p=Path(parent)/n;assert p.suffix.lower() not in {'.npz','.npy','.pt','.pth','.ckpt','.nrrd','.stl'},str(p)
  b=read(p)
  if n in {'launch.log','exit_code.txt','worker.pid','monitor_failure.json','startup_failure.json','summary.json'}:
   assert len(b)<=65536;text[n]=b.decode('utf-8')
rc=subprocess.run(['tmux','has-session','-t',q['future_start_contract']['tmux_session']],capture_output=True).returncode
assert rc!=0 and not Path('/proc/1025').exists()
assert text['exit_code.txt'].strip()=='1' and 'PHASE arm_start' not in text['launch.log']
assert 'summary.json' not in text and 'monitor_failure.json' not in text and 'startup_failure.json' in text
print(json.dumps({'status':'FAILED_ARTIFACT_INTEGRITY_PASS_NOT_PREFLIGHT_PASS','files':rows,'hashed_bytes':used,'seconds':time.monotonic()-start,'text':text,'tmux_absent':True,'original_PID_absent':True,'remote_writes':0}))
