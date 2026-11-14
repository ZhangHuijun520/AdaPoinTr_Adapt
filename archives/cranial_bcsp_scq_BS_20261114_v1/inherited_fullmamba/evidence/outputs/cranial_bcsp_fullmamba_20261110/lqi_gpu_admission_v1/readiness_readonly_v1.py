"""Bounded inherited-asset recheck; no imports of ML, writes, installs or CUDA."""
import base64,hashlib,json,shlex,subprocess,sys,zlib
from pathlib import Path
S=Path(__file__).resolve().parent;O=S/'readiness_v1'
IDENTITY=r'''
import socket,os,json,pathlib,sys,subprocess,shutil
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
root=pathlib.Path('/home/jovyan/adapointr_work/PoinTr');assert root.is_dir() and not any(p.is_symlink() for p in (root,*root.parents))
g=subprocess.check_output(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=10,text=True).strip().splitlines();assert len(g)==1
gpu=[x.strip() for x in g[0].split(',')];assert gpu[:4]==['GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed','NVIDIA GeForce RTX 4090 D','575.51.03','24564'] and int(gpu[4])<=256
for name in ['third_party/bcsp_lqi_cuda_20261111_v1','logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1']:
 p=root/name;assert not p.exists() and not any(x.is_symlink() for x in (p,*p.parents))
assert shutil.disk_usage(root).free>=4294967296
print(json.dumps(dict(status='LQI_CURRENT_IDENTITY_RESOURCE_TARGETS_PASS',hostname=socket.gethostname(),uid=os.getuid(),python_realpath=str(pathlib.Path(sys.executable).resolve()),python_version=sys.version.split()[0],GPU=gpu,free_disk_bytes=shutil.disk_usage(root).free,new_targets_absent=True,server_writes=0,CUDA_calls=0)))
'''
ASSETS=r'''
import socket,os,json,pathlib,hashlib,time
P=pathlib.Path;t=time.monotonic();total=0;seen=set();verified=[]
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
def exact(r):
 global total
 p=P(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r['bytes'];a=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):
   h.update(b);total+=len(b);assert total<=1073741824 and time.monotonic()-t<=40
 z=p.stat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns) and h.hexdigest()==r['sha256'];seen.add(str(p));verified.append(r);return p
q=json.loads(exact(QREC).read_bytes());scope=json.loads(exact(q['preflight_scope']).read_bytes());s=scope['bindings'];root=P(q['model_root'])
rs=[q[k] for k in ('helper','native_helper','static_config')]+[q['implementation'][k] for k in ('encoder','factory','timezone')]+q['dependencies']+s['provider']+s['environment_metadata']
rs += [dict(path=str(root/r['relative_target']),bytes=r['bytes'],sha256=r['sha256']) for r in s['candidate']]+[dict(path=str(root/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']) for r in s['isolated_model_project_sources']]
assert len(rs)<=80
for r in rs:
 if r['path'] not in seen:exact(r)
assert hashlib.sha256((root/'base_model.yaml').read_bytes()).hexdigest()==s['base_config']['sha256']
link=P('/usr/share/zoneinfo/UTC');assert link.is_symlink() and os.readlink(link)=='Etc/UTC' and str(link.resolve())=='/usr/share/zoneinfo/Etc/UTC'
exact(dict(path='/usr/share/zoneinfo/Etc/UTC',bytes=118,sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a'))
print(json.dumps(dict(status='LQI_INHERITED_EXACT_ASSETS_PASS',records=verified,files=len(verified),hashed_bytes=total,seconds=time.monotonic()-t,model_imports=0,real_payload_reads=0,server_writes=0,CUDA_calls=0)))
'''
def main():
 O.mkdir();p=S.parent/'conditional_diagnostic_implementation_v1/frozen_pending_transport_v1/payload/F0_CD_decoder_diagnostic_execution_request_v1.json';q=json.loads(p.read_bytes())
 record=dict(path=q['launch_contract']['request_path'],bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 commands=[]
 for label,source in [('identity',IDENTITY),('assets',ASSETS.replace('QREC',repr(record)))]:
  blob=base64.b64encode(zlib.compress(source.encode(),9)).decode();wrapper='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(blob)+')),"<lqi-readiness>","exec"))'
  command=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c',wrapper]);assert len(command.encode())<=2048,len(command.encode());commands.append((label,command))
 with (O/'frozen_commands_v1.json').open('x') as f:json.dump(dict(phases=[dict(name=k,command=v,bytes=len(v.encode())) for k,v in commands],timeout_seconds=45,hash_bytes_max=1073741824,files_max=80,server_writes=0),f,indent=2)
 if sys.argv[1:]!=['--execute']:print('Frozen only');return
 for label,command in commands:
  r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--',command],capture_output=True,timeout=55)
  for k,data in [('stdout',r.stdout),('stderr',r.stderr)]:
   with (O/(label+'_'+k+'.bin')).open('xb') as f:f.write(data)
  if r.returncode:raise RuntimeError('readiness failed stop no retry '+label+' '+repr(r.stdout[-1500:]))
  v=json.loads(r.stdout)
  with (O/(label+'_result_v1.json')).open('x') as f:json.dump(v,f,indent=2)
  print(json.dumps({k:x for k,x in v.items() if k!='records'}),flush=True)
if __name__=='__main__':main()
