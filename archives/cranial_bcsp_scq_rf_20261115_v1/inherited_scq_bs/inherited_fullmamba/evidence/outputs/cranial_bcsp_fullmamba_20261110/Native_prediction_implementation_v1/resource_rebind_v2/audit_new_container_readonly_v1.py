"""Bounded read-only rebind evidence; no remote files, imports of ML, or launches."""
import base64,hashlib,json,shlex,subprocess,sys,time,zlib
from pathlib import Path
A=Path(__file__).resolve().parent
PY='/opt/conda/envs/adapointr-mamba/bin/python3.10'
QH='8c2f849a1e3cb9cfbaac5e501f09647fa0de894491501e0d0bd48e09b9e9ee03'
PREFIX=r'''
import os,socket,json,pathlib,sys,hashlib,tarfile,time,shutil,subprocess
P=pathlib.Path;start=time.monotonic();total=0;records=[]
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
def exact(r):
 global total
 p=P(r['path']);assert p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.is_file() and p.stat().st_size==r['bytes'],str(p)
 before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):
   total+=len(b);assert total<=2147483648 and time.monotonic()-start<=55;h.update(b)
 after=p.stat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 assert h.hexdigest()==r['sha256'],str(p);records.append(r);return p
arc=P('/home/jovyan/bcsp_f0_CD_native_prediction_pending_20261111_v1.tar.gz')
exact(dict(path=str(arc),bytes=66360,sha256='c4d115add6cd93207fa1a4bd7d44d395d467e6e395b95372ea6b08890319d1bc'))
with tarfile.open(arc,'r:gz') as t:
 members=t.getmembers();assert len(members)==14 and all(m.isfile() and m.size<1048576 for m in members)
 data={m.name:t.extractfile(m).read() for m in members};assert len(data)==14
qb=data['payload/F0_CD_native_prediction_execution_request_v1.json'];assert hashlib.sha256(qb).hexdigest()=='8c2f849a1e3cb9cfbaac5e501f09647fa0de894491501e0d0bd48e09b9e9ee03'
q=json.loads(qb);index=json.loads(data['payload/F0_CD_Native_input_index_candidate_v1.json'])
'''
IDENTITY=r'''
import os,socket,json,pathlib,sys,shutil,subprocess
p=pathlib.Path('/home/jovyan/adapointr_work/PoinTr')
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
assert p.is_dir() and not any(x.is_symlink() for x in (p,*p.parents))
s=subprocess.check_output(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=10,text=True).strip().splitlines();assert len(s)==1
print(json.dumps(dict(status='READONLY_IDENTITY_RESOURCE',hostname=socket.gethostname(),uid=os.getuid(),python_realpath=str(pathlib.Path(sys.executable).resolve()),python_version=sys.version.split()[0],project=str(p),GPU=[v.strip() for v in s[0].split(',')],free_disk_bytes=shutil.disk_usage(p).free,server_writes=0,CUDA_calls=0)))
'''
PACKAGE=r'''
assert P(str(arc)+'.sha256').read_text().split()[0]=='c4d115add6cd93207fa1a4bd7d44d395d467e6e395b95372ea6b08890319d1bc' and int(P(str(arc)+'.bytes').read_text())==66360
listing=''.join(hashlib.sha256(data[m.name]).hexdigest()+'  '+m.name+'\n' for m in members)
assert P(str(arc)+'.contents.sha256').read_text()==listing
mapping=json.loads(data['installation_mapping_v1.json']);assert len(mapping['files'])==13
for r in mapping['files']:
 b=data['payload/'+P(r['target']).name];assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
targets=[r['target'] for r in mapping['files']]+mapping['not_materialized']+[mapping['remote_root'],'/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_native_prediction_20261111_v2','/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_development_20261111_v2']
assert all(not P(t).exists() and not any(x.is_symlink() for x in (P(t),*P(t).parents)) for t in targets)
print(json.dumps(dict(status='UPLOAD_AND_FRESH_TARGETS_PASS',archive_SHA256=hashlib.sha256(arc.read_bytes()).hexdigest(),request_SHA256=hashlib.sha256(qb).hexdigest(),package_members=len(data),old_install_and_controls_absent=True,new_v2_roots_absent=True,targets=targets,seconds=time.monotonic()-start,server_writes=0)))
'''
ASSETS=r'''
scope=json.loads(exact(q['preflight_scope']).read_bytes());b=scope['bindings'];root=P(q['model_root'])
rs=[q[k] for k in ['static_config','numeric_policy','source_index','source_manifest','fold_binding','helper']]+list(q['implementation'].values())+q['dependencies']+b['provider']+b['environment_metadata']
rs += [dict(path=str(root/r['relative_target']),bytes=r['bytes'],sha256=r['sha256']) for r in b['candidate']]
rs += [dict(path=str(root/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']) for r in b['isolated_model_project_sources']]
seen=set()
for r in rs:
 if r['path'] not in seen:exact(r);seen.add(r['path'])
assert hashlib.sha256((root/'base_model.yaml').read_bytes()).hexdigest()==b['base_config']['sha256']
link=P('/usr/share/zoneinfo/UTC');assert link.is_symlink() and os.readlink(link)=='Etc/UTC' and str(link.resolve())=='/usr/share/zoneinfo/Etc/UTC'
exact(dict(path='/usr/share/zoneinfo/Etc/UTC',bytes=118,sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a'))
print(json.dumps(dict(status='REUSED_SOURCE_PROVIDER_DEPENDENCY_HASHES_PASS',records=records,UTC_link='Etc/UTC',base_config_sha256=b['base_config']['sha256'],hashed_bytes=total,seconds=time.monotonic()-start,imports_ML=0,server_writes=0)))
'''
POINTS=r'''
assert len(index['runs'])==2 and len(index['inputs'])==210
for run in index['runs']:exact(run['checkpoint'])
for row in index['inputs']:exact(row['input'])
print(json.dumps(dict(status='TWO_CHECKPOINT_AND_210_INPUT_IDENTITIES_PASS',records=records,checkpoints=2,inputs=210,hashed_bytes=total,seconds=time.monotonic()-start,arrays_decoded=0,checkpoint_deserialization=0,server_writes=0)))
'''
def call(label,source):
 payload=base64.b64encode(zlib.compress(source.encode('utf-8'),9)).decode('ascii')
 wrapper='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(payload)+')),"<rebind>","exec"))'
 cmd=shlex.join([PY,'-I','-S','-B','-c',wrapper]);assert len(cmd.encode())<=2048,(label,len(cmd.encode()))
 with (A/(label+'_command_v1.json')).open('x',encoding='utf-8') as f:json.dump(dict(command=cmd,bytes=len(cmd.encode()),read_only=True),f)
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--',cmd],capture_output=True,timeout=70)
 for k,v in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (A/(label+'_'+k+'_v1.bin')).open('xb') as f:f.write(v)
 if r.returncode:raise RuntimeError(label+' failed; stop; '+repr(r.stderr[-1200:]))
 result=json.loads(r.stdout);print(json.dumps(dict(phase=label,status=result['status'],command_bytes=len(cmd.encode()),result=result if label=='identity' else {k:v for k,v in result.items() if k not in ('records','targets')})),flush=True)
 return result
def main():
 label=sys.argv[1];assert label in ('identity','package','assets','points')
 try:
  result=call(label,IDENTITY if label=='identity' else PREFIX+{'package':PACKAGE,'assets':ASSETS,'points':POINTS}[label])
  with (A/(label+'_result_v1.json')).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 except BaseException as exc:
  with (A/(label+'_failure_v1.json')).open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)),f)
  raise
if __name__=='__main__':main()
