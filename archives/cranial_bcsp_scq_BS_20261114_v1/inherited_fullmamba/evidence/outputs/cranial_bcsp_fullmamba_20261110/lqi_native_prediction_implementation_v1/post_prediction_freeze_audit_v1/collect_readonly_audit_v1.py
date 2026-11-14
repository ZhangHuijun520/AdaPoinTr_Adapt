"""Dedicated bounded read-only audit collector. No server writes or model imports."""
import ast,base64,hashlib,json,shlex,subprocess,sys,time,zlib
from pathlib import Path
F=Path(__file__).resolve().parent;B=F.parent;QH='cab2831f27913766d7009101ec86d9a6e642a40b9330359dbfc8ff5928610fb6'
Q=B/'pending_request_final_v1/transport_payload/LQI_CD_native_prediction_execution_request_v1.json';assert hashlib.sha256(Q.read_bytes()).hexdigest()==QH
q=json.loads(Q.read_bytes());idx=json.loads((B/'pending_request_final_v1/transport_payload/LQI_CD_Native_input_index_candidate_v1.json').read_bytes())
ROOT=q['output'];INSTALL=q['entry']['path'].rsplit('/',1)[0]
PREFIX="import os,json,hashlib,socket,time,sys\nfrom pathlib import Path,PurePosixPath\nO=Path("+repr(ROOT)+");I=Path("+repr(INSTALL)+")\nassert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000\nassert not any(p.is_symlink() for p in (O,*O.parents,I,*I.parents))\nq=json.loads((I/'LQI_CD_native_prediction_execution_request_v1.json').read_bytes());assert hashlib.sha256((I/'LQI_CD_native_prediction_execution_request_v1.json').read_bytes()).hexdigest()=="+repr(QH)+"\n"
FINISHED=r'''
import subprocess
assert (O/'exit_code.txt').read_text().strip()=='0' and not Path('/proc/'+(O/'worker.pid').read_text().strip()).exists()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
assert not (O/'failure.json').exists()
print(json.dumps(dict(status='EXIT0_WORKER_TMUX_ABSENT',hostname=socket.gethostname(),uid=os.getuid(),free_disk_bytes=__import__('shutil').disk_usage(O).free)))
'''
INVENTORY=r'''
def fingerprint(p):
 s=p.lstat();return [s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def inventory(root):
 rows={};dirs=[]
 for p in [root,*sorted(root.rglob('*'))]:
  assert not p.is_symlink() and (p.is_file() or p.is_dir()),str(p)
  n=str(p.relative_to(root))
  if p.is_dir():dirs.append(n)
  else:rows[n]=fingerprint(p)
 return dict(files=rows,directories=dirs)
print(json.dumps(dict(status='INVENTORY_REGULAR_ONLY',output=inventory(O),install=inventory(I))))
'''
HASH_OUTPUT=r'''
rows=[];total=0;start=time.monotonic()
for p in sorted(O.rglob('*')):
 if not p.is_file():continue
 assert not p.is_symlink();a=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);total+=len(b);assert total<2147483648 and time.monotonic()-start<40
 z=p.stat();assert (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 rows.append(dict(name=str(p.relative_to(O)),bytes=z.st_size,sha256=h.hexdigest()))
print(json.dumps(dict(status='ALL_OUTPUT_STABLE_HASHES',files=rows,hashed_bytes=total,seconds=time.monotonic()-start)))
'''
METADATA=r'''
import base64
files={};total=0
for root,label in [(O,'output'),(I,'installed')]:
 for p in sorted(root.rglob('*')):
  if not p.is_file() or (root==O and p.suffix not in ('.json','.jsonl','.txt','.log','.pid','.sha256','.bytes')):continue
  assert not p.is_symlink() and p.stat().st_size<8388608
  b=p.read_bytes();total+=len(b);assert total<16777216
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
print(json.dumps(dict(status='BOUNDED_METADATA_READ',files=files,bytes=total)))
'''
ASSETS=r'''
idx=json.loads(Path(q['input_index']['path']).read_bytes());receipt=json.loads((I/'control/readiness_and_installation_receipt_v2.json').read_bytes())
rs={r['path']:r for r in receipt['read_manifest'] if not str(r['path']).startswith(str(I)+'/')}
for run in idx['runs']:rs[run['checkpoint']['path']]=run['checkpoint']
for row in idx['inputs']:rs[row['input']['path']]=row['input']
total=0;rows=[];start=time.monotonic()
for r in rs.values():
 p=Path(r['path']);assert p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file() and p.stat().st_size==r['bytes'],str(p)
 a=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):total+=len(b);assert total<2147483648 and time.monotonic()-start<40;h.update(b)
 z=p.stat();assert (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns) and h.hexdigest()==r['sha256'],str(p)
 rows.append(dict(**r,fingerprint=[z.st_dev,z.st_ino,z.st_mode,z.st_size,z.st_mtime_ns,z.st_ctime_ns]))
print(json.dumps(dict(status='FROZEN_ASSETS_FRESH_STABLE_HASH_PASS',records=rows,hashed_bytes=total,seconds=time.monotonic()-start,checkpoint_deserialization=0,arrays_decoded=0)))
'''
ARCHIVE=r'''
import tarfile
c=json.loads((O/'completion.json').read_bytes());a=c['archive'];rs={r['name']:r for r in a['members']};assert len(rs)==len(a['members'])==216
count=total=0
with tarfile.open(O/'development_predictions_v1.tar.gz','r:gz') as t:
 ms=t.getmembers();assert len(ms)==216 and {m.name for m in ms}==set(rs)
 for m in ms:
  assert m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and m.size<20971520
  b=t.extractfile(m).read();r=rs[m.name];p=O/m.name
  assert p.is_file() and not p.is_symlink() and len(b)==r['bytes']==p.stat().st_size and hashlib.sha256(b).hexdigest()==r['sha256']==hashlib.sha256(p.read_bytes()).hexdigest(),m.name
  count+=1;total+=len(b)
assert count==216
print(json.dumps(dict(status='EXACT216_ARCHIVE_MEMBERS_HASH_SIZE_PARITY_PASS',members=count,member_bytes=total,server_extractions=0)))
'''
ARRAYS=r'''
sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['input_index']['path']).read_bytes());count=0
for row in idx['inputs']:
 assert row['cache_context'] is False and row['save_full_decoder_trace'] is False
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:
  assert len(z.files)==2 and set(z.files)=={'prediction','coarse'}
  d,c=z['prediction'],z['coarse']
  assert d.shape==(8192,3) and c.shape==(256,3) and all(x.dtype==n.float32 and n.isfinite(x).all() for x in [d,c])
 count+=1
assert count==210 and not list((O/'context').iterdir()) and not list((O/'traces').iterdir())
print(json.dumps(dict(status='ALL210_FP32_FINITE_NATIVE_Q_P_ARRAYS_PASS',predictions=count,coarse=count,context=0,traces=0,trace_layers=0,GT_arrays_read=0,GPU_calls=0)))
'''
GEOMETRY=r'''
sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['input_index']['path']).read_bytes());logs=[json.loads(x) for x in (O/'geometry_summary.jsonl').read_text().splitlines()];assert len(logs)==210
maxerr=0.
for row,g in zip(idx['inputs'],logs):
 assert g['run']==row['run'] and g['case_id']==row['case_id']
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:c=z['coarse'].astype('float64');d=z['prediction'].astype('float64')
 for key,x in [('coarse',c),('dense',d)]:
  m=x.mean(0);v=x-m;expected=dict(centroid=m,bbox_min=x.min(0),bbox_max=x.max(0),radius_gyration=n.sqrt((v*v).sum(1).mean()),covariance_eigenvalues=n.linalg.eigvalsh(v.T@v/len(x)))
  assert g[key]['finite_count']==len(x)
  for k,val in expected.items():
   err=float(n.max(n.abs(n.asarray(g[key][k])-val)));maxerr=max(maxerr,err);assert n.allclose(g[key][k],val,rtol=1e-10,atol=1e-12),(row['case_id'],key,k)
 offsets=d.reshape(256,32,3)-c[:,None,:]
 assert n.allclose(g['mean_dense_minus_coarse'],offsets.mean((0,1)),rtol=1e-10,atol=1e-12) and n.allclose(g['offset_mean_squared_radius'],(offsets**2).sum(2).mean(),rtol=1e-10,atol=1e-12)
print(json.dumps(dict(status='ALL210_SAVED_NATIVE_GEOMETRY_SUMMARIES_RECOMPUTED_PASS',predictions=210,max_absolute_stat_error=maxerr,GT_read=False,scoring=False)))
'''
SOURCES={'finished':FINISHED,'inventory_before':INVENTORY,'hashes_before':HASH_OUTPUT,'metadata':METADATA,'assets':ASSETS,'archive':ARCHIVE,'arrays':ARRAYS,'geometry':GEOMETRY,'hashes_after':HASH_OUTPUT,'inventory_after':INVENTORY}
def command(source):
 blob=base64.b64encode(zlib.compress((PREFIX+source).encode(),9)).decode();code='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(blob)+')),"<freeze-readonly>","exec"))'
 c=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c',code]);assert len(c.encode())<=2048,len(c.encode());return c
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def call(label):
 c=command(SOURCES[label]);emit(F/(label+'_command_v1.json'),dict(command=c,bytes=len(c.encode()),read_only=True))
 try:r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--',c],capture_output=True,timeout=55);out,err,rc=r.stdout,r.stderr,r.returncode
 except subprocess.TimeoutExpired as exc:out,err,rc=exc.stdout or b'',exc.stderr or b'',None
 for k,b in [('stdout',out),('stderr',err)]:
  with (F/(label+'_'+k+'_v1.bin')).open('xb') as f:f.write(b)
 if rc!=0:raise RuntimeError(label+' failed stop no retry: '+repr(err[-1200:]))
 v=json.loads(out);emit(F/(label+'_result_v1.json'),v)
 if label=='metadata':
  for name,r in v['files'].items():
   p=F/'downloads'/name;p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(r['base64'],validate=True);assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
   with p.open('xb') as f:f.write(b)
 print(json.dumps(dict(stage=label,status=v['status'],stdout_bytes=len(out),command_bytes=len(c.encode()))),flush=True)
def main():
 label=sys.argv[1];assert label in SOURCES
 try:call(label)
 except BaseException as exc:emit(F/(label+'_failure_v1.json'),dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)));raise
if __name__=='__main__':main()
