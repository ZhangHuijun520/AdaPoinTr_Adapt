"""Two bounded read-only calls; no ML imports, array decoding, install or launch."""
import base64,hashlib,json,shlex,subprocess,sys,zlib
from pathlib import Path
S=Path(__file__).resolve().parent;O=S/'server_readiness_v1'
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
 O.mkdir();base=S.parent/'Native_prediction_implementation_v1/resource_rebind_v2';qpath=base/'transport_payload/F0_CD_native_prediction_execution_request_v2.json';q=json.loads(qpath.read_bytes())
 completion=base/'post_prediction_freeze_audit_v1/downloads/output/completion.json'
 rows=json.loads((S/'context_index_candidate_v1.json').read_bytes())['pairs'];assets=sorted([r[k] for r in rows for k in ('recipient_context','donor_context','Native_trace','Native_prediction')],key=lambda r:r['path'])
 expected=digest(json.dumps(assets,sort_keys=True,separators=(',',':')).encode())
 identity="""
import socket,os,json,subprocess,shutil,sys,pathlib
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
g=subprocess.check_output(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=10,text=True).strip().splitlines()
assert len(g)==1
print(json.dumps(dict(status='IDENTITY_RESOURCE_READONLY',hostname=socket.gethostname(),uid=os.getuid(),python_realpath=str(pathlib.Path(sys.executable).resolve()),python_version=sys.version.split()[0],GPU=[s.strip() for s in g[0].split(',')],free_disk_bytes=shutil.disk_usage('/home/jovyan/adapointr_work/PoinTr').free,server_writes=0,CUDA_calls=0)))
"""
 remote_q=q['launch_contract']['request_path']
 assets_source="""
import socket,os,json,hashlib,pathlib,time
P=pathlib.Path;t=time.monotonic();n=0;seen=set()
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
def exact(r):
 global n
 p=P(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents));assert p.is_file() and p.stat().st_size==r['bytes'];h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):
   n+=len(b);assert n<=1300000000 and time.monotonic()-t<=55;h.update(b)
 assert h.hexdigest()==r['sha256'],str(p);seen.add(str(p));return p
q=json.loads(exact(QREC).read_bytes());c=json.loads(exact(CREC).read_bytes());idx=json.loads(exact(q['input_index']).read_bytes())
names=set()
for fold,r,d in [('C','001','003'),('D','004','005')]:
 for k in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']:
  for folder,source in [('context',r),('context',d),('traces',r),('predictions',r)]:names.add(folder+'/'+fold+'_F0__train__'+source+'__'+k+'.npz')
rows=sorted([dict(path=q['output']+'/'+r['name'],bytes=r['bytes'],sha256=r['sha256']) for r in c['archive']['members'] if r['name'] in names],key=lambda r:r['path'])
assert len(rows)==40 and hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()==DIGEST
for r in rows+[r['checkpoint'] for r in idx['runs']]+[q[k] for k in ['entry','helper','static_config','preflight_scope']]+list(q['implementation'].values()):exact(r)
targets=['/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_condition_diagnostic_20261111_v1','/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1']
for s in targets:
 p=P(s);assert not p.exists() and not any(x.is_symlink() for x in (p,*p.parents))
print(json.dumps(dict(status='EXACT40_CACHES_TWO_WEIGHTS_REUSED_SOURCES_PASS',files=len(seen),hashed_bytes=n,seconds=time.monotonic()-t,cache_identity_digest=DIGEST,new_targets_absent=True,arrays_decoded=0,checkpoint_deserialization=0,CUDA_calls=0,server_writes=0)))
"""
 assets_source=assets_source.replace('QREC',repr(dict(path=remote_q,bytes=qpath.stat().st_size,sha256=digest(qpath.read_bytes())))).replace('CREC',repr(dict(path=q['output']+'/completion.json',bytes=completion.stat().st_size,sha256=digest(completion.read_bytes())))).replace('DIGEST',repr(expected))
 commands=[]
 for label,src in [('identity',identity),('assets',assets_source)]:
  payload=base64.b64encode(zlib.compress(src.encode(),9)).decode();wrapper='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(payload)+')),"<fixed-condition-readiness>","exec"))'
  command=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c',wrapper]);assert len(command.encode())<=2048,(label,len(command.encode()))
  commands.append((label,command))
 (O/'frozen_commands.json').write_text(json.dumps([dict(phase=k,command=v,bytes=len(v.encode())) for k,v in commands],indent=2),encoding='utf-8')
 if sys.argv[1:]!=['--execute']:print('commands frozen; no connection');return
 for label,command in commands:
  result=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--',command],capture_output=True,timeout=70)
  for key,data in [('stdout',result.stdout),('stderr',result.stderr)]:
   with (O/(label+'_'+key+'.bin')).open('xb') as f:f.write(data)
  if result.returncode:raise RuntimeError(label+' returncode '+str(result.returncode)+' '+repr(result.stderr[-1200:]))
  value=json.loads(result.stdout)
  with (O/(label+'_result.json')).open('x') as f:json.dump(value,f,indent=2)
  print(json.dumps(value),flush=True)
if __name__=='__main__':main()
