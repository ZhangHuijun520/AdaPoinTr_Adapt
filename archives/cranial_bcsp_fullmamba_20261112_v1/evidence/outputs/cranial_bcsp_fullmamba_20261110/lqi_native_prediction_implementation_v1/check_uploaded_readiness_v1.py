"""One bounded remote readonly readiness call; original bytes and raw capture."""
import base64,hashlib,json,shlex,subprocess,sys,zlib
from pathlib import Path
S=Path(__file__).resolve().parent;O=S/'uploaded_readonly_verification_v1'
QH='cab2831f27913766d7009101ec86d9a6e642a40b9330359dbfc8ff5928610fb6'
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def main():
 O.mkdir()
 pending=S/'pending_request_final_v1';q= pending/'transport_payload/LQI_CD_native_prediction_execution_request_v1.json'
 assert hashlib.sha256(q.read_bytes()).hexdigest()==QH
 names=['bcsp_lqi_CD_native_prediction_pending_20261111_v1.tar.gz'+s for s in ('','.sha256','.bytes','.contents.sha256')]
 records=[dict(name=n,bytes=(pending/n).stat().st_size,sha256=hashlib.sha256((pending/n).read_bytes()).hexdigest()) for n in names]
 code='''import os,socket,sys,json,pathlib,hashlib,shutil,subprocess
P=pathlib.Path;root=P('/home/jovyan/adapointr_work/PoinTr')
host=socket.gethostname();assert host=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000,(host,os.getuid())
assert str(P(sys.executable).resolve())=='/opt/conda/envs/adapointr-mamba/bin/python3.10' and sys.version.split()[0]=='3.10.20'
assert root.is_dir() and not any(p.is_symlink() for p in (root,*root.parents))
rows=[]
for r in RECORDS:
 p=P('/home/jovyan')/r['name'];safe=not any(x.is_symlink() for x in (p,*p.parents));exists=p.is_file()
 actual=dict(exists=exists,safe=safe)
 if exists and safe:
  actual.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 actual['matches']=safe and exists and actual['bytes']==r['bytes'] and actual['sha256']==r['sha256'];rows.append(dict(name=r['name'],**actual))
targets=[root/'third_party/bcsp_lqi_CD_native_prediction_20261111_v1',root/'logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1',root/'third_party/lqi_native_authorized_operation_20261111_v1.py']
fresh=all(not p.exists() and not any(x.is_symlink() for x in (p,*p.parents)) for p in targets)
g=subprocess.check_output(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=10,text=True).strip().splitlines()
assert len(g)==1;gpu=[x.strip() for x in g[0].split(',')]
gpu_ok=gpu[:4]==['GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed','NVIDIA GeForce RTX 4090 D','575.51.03','24564'] and int(gpu[4])<=256
session=subprocess.run(['tmux','has-session','-t','bcsp_lqi_CD_native_eval_20261111_v1'],capture_output=True,timeout=5).returncode
free=shutil.disk_usage(root).free
print(json.dumps(dict(status='READONLY_PRECHECK_COMPLETE',hostname=host,UID=os.getuid(),uploads=rows,all_uploads_match=all(r['matches'] for r in rows),new_roots_absent=fresh,GPU=gpu,GPU_identity_idle_pass=gpu_ok,tmux_absent=session==1,free_disk_bytes=free,disk_pass=free>=4294967296,server_writes=0)))
'''.replace('RECORDS',repr(records))
 payload=base64.b64encode(zlib.compress(code.encode(),9)).decode()
 command=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c','import base64,zlib;exec(zlib.decompress(base64.b64decode('+repr(payload)+')))'])
 assert len(command.encode())<=2048
 emit(O/'initial_readonly_command_v1.json',dict(command=command,bytes=len(command.encode()),request_sha256=QH))
 try:
  r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','25','--',command],capture_output=True,timeout=40)
  out,err,rc=r.stdout,r.stderr,r.returncode
 except subprocess.TimeoutExpired as e:out,err,rc=e.stdout or b'',e.stderr or b'',None
 for name,b in [('stdout',out),('stderr',err)]:
  with (O/('initial_readonly_'+name+'.bin')).open('xb') as f:f.write(b)
 result=dict(returncode=rc,request_sha256=QH,server_writes=0)
 if rc==0:
  try:result['observation']=json.loads(out)
  except ValueError:result.update(error='Non-JSON response; stop',stdout_preview=out.decode('utf-8',errors='replace')[-1000:])
 else:result['error']=err.decode('utf-8',errors='replace')[-1500:]
 emit(O/'initial_readonly_result_v1.json',result);print(json.dumps(result,ensure_ascii=True))
 return 0 if rc==0 and 'observation' in result else 1
if __name__=='__main__':sys.exit(main())
