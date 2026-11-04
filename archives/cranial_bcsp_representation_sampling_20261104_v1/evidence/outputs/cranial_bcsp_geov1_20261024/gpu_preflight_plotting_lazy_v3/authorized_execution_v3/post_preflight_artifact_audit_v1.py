import hashlib,json,os,socket,stat,subprocess,time
from pathlib import Path
start=time.monotonic();used=0;rows=[];cache={}
root=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3')
assert socket.gethostname()=='shu-common-25721452-notebook-o9mz8z-0' and os.getuid()==1000
def read(p):
 global used
 assert time.monotonic()-start<45 and len(rows)<64,str(p)
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 a=p.stat();used+=a.st_size;assert used<=32*1024**2,str(p)
 b=p.read_bytes();z=p.stat();assert (a.st_size,a.st_mtime_ns,a.st_ino)==(z.st_size,z.st_mtime_ns,z.st_ino),str(p)
 rows.append({'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mtime_ns':z.st_mtime_ns,'mode':stat.S_IMODE(z.st_mode),'uid':z.st_uid});cache[str(p)]=b
 return b
def inventory(base):
 files=[];dirs=[]
 for parent,ds,fs in os.walk(base,followlinks=False):
  dirs.append(str(Path(parent).relative_to(base)));assert len(dirs)<=32 and len(Path(parent).relative_to(base).parts)<=6
  assert not any((Path(parent)/n).is_symlink() for n in ds+fs)
  files.extend(str((Path(parent)/n).relative_to(base)) for n in fs);assert len(files)<=64
 return sorted(files),sorted(dirs)
m=read(Path('/home/jovyan/bcsp_gpu_preflight_v3.contents.sha256'))
assert hashlib.sha256(m).hexdigest()=='3b5cf48a982443c80f1210962759696f5bda05aface141f2688ef8bd7557ade5'
manifest=[line.split('  ',1) for line in m.decode().splitlines()];assert len(manifest)==26
H=next(h for h,n in manifest if n=='evidence/execution_request_v3.json')
for h,n in manifest:
 assert not n.startswith('/') and '..' not in Path(n).parts
 assert hashlib.sha256(read(root/n)).hexdigest()==h,n
q=json.loads(cache[str(root/'evidence/execution_request_v3.json')])
for r in q['future_limited_deployment']['scope_provider_bindings']+q['future_limited_deployment']['scope_environment_metadata_bindings']:
 b=read(Path(r['path']));assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],r['path']
c=q['future_control_paths'];marker=json.loads(read(Path(c['attempt_marker'])))
assert marker['request_sha256']==H and marker['status']=='CLAIMED_BEFORE_TMUX'
stage_files,stage_dirs=inventory(root);assert set(stage_files)=={n for h,n in manifest}|{'control/launch_attempt_v3.json'}
out=Path(c['summary']).parent;output_files,output_dirs=inventory(out)
assert set(output_files)=={'worker.pid','exit_code.txt','launch.log','summary.json','monitor_events.jsonl'}
text={n:read(out/n).decode('utf-8') for n in output_files}
assert text['exit_code.txt'].strip()=='0';pid=int(text['worker.pid'])
assert pid==1485 and not Path('/proc/'+str(pid)).exists()
assert subprocess.run(['tmux','has-session','-t',q['future_start_contract']['tmux_session']],capture_output=True).returncode==1
assert time.monotonic()-start<45
print(json.dumps({'status':'PASS','files':rows,'hashed_bytes':used,'seconds':time.monotonic()-start,'text':text,'marker':marker,'output_dirs':output_dirs,'tmux_absent':True,'original_PID_absent':True,'remote_writes':0}))
