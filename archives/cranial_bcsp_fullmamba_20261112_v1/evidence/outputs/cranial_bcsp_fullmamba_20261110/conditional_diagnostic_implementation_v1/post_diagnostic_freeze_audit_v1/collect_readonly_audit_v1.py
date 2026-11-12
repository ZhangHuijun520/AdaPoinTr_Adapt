"""Dedicated bounded read-only audit collector. No server writes or model imports."""
import ast,base64,hashlib,json,shlex,subprocess,sys,time,zlib
from pathlib import Path
F=Path(__file__).resolve().parent;B=F.parent;QH='a21965cdefdf4a7903b5cb52b235dc5e30f0cd9d25a25915734967ee6ff7eda2'
Q=B/'frozen_pending_transport_v1/payload/F0_CD_decoder_diagnostic_execution_request_v1.json';assert hashlib.sha256(Q.read_bytes()).hexdigest()==QH
q=json.loads(Q.read_bytes());idx=json.loads((B/'frozen_pending_transport_v1/payload/context_index_candidate_v1.json').read_bytes())
ROOT=q['output'];INSTALL=q['entry']['path'].rsplit('/',1)[0]
PREFIX="import os,json,hashlib,socket,time,sys\nfrom pathlib import Path,PurePosixPath\nO=Path("+repr(ROOT)+");I=Path("+repr(INSTALL)+")\nassert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000\nassert not any(p.is_symlink() for p in (O,*O.parents,I,*I.parents))\nq=json.loads((I/'F0_CD_decoder_diagnostic_execution_request_v1.json').read_bytes());assert hashlib.sha256((I/'F0_CD_decoder_diagnostic_execution_request_v1.json').read_bytes()).hexdigest()=="+repr(QH)+"\n"
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
idx=json.loads(Path(q['context_index']['path']).read_bytes());receipt=json.loads((I/'control/readiness_and_installation_receipt_v1.json').read_bytes())
rs={r['path']:r for r in receipt['read_manifest'] if not str(r['path']).startswith(str(I)+'/')}
for run in idx['runs']:rs[run['checkpoint']['path']]=run['checkpoint']
for row in idx['pairs']:
 for k in ('recipient_context','donor_context','Native_trace','Native_prediction'):rs[row[k]['path']]=row[k]
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
c=json.loads((O/'completion.json').read_bytes());a=c['archive'];rs={r['name']:r for r in a['members']};assert len(rs)==len(a['members'])==65
count=total=0
with tarfile.open(O/'development_predictions_v1.tar.gz','r:gz') as t:
 ms=t.getmembers();assert len(ms)==65 and {m.name for m in ms}==set(rs)
 for m in ms:
  assert m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and m.size<20971520
  b=t.extractfile(m).read();r=rs[m.name];p=O/m.name
  assert p.is_file() and not p.is_symlink() and len(b)==r['bytes']==p.stat().st_size and hashlib.sha256(b).hexdigest()==r['sha256']==hashlib.sha256(p.read_bytes()).hexdigest(),m.name
  count+=1;total+=len(b)
assert count==65
print(json.dumps(dict(status='EXACT246_ARCHIVE_MEMBERS_HASH_SIZE_PARITY_PASS',members=count,member_bytes=total,server_extractions=0)))
'''
ARRAYS=r'''
sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['context_index']['path']).read_bytes());pred=traces=layers=0
for r in idx['pairs']:
 with n.load(r['recipient_context']['path'],allow_pickle=False) as z:Q=z['Q'];X=z['X']
 with n.load(r['Native_trace']['path'],allow_pickle=False) as z:native={k:z[k] for k in z.files}
 for c in q['conditions']:
  name=r['run']+'__'+r['recipient']+'__'+c+'.npz'
  with n.load(O/'predictions'/name,allow_pickle=False) as z:
   assert set(z.files)=={'prediction','coarse'} and len(z.files)==2
   assert z['prediction'].shape==(8192,3) and z['prediction'].dtype==n.float32 and n.isfinite(z['prediction']).all() and n.array_equal(z['coarse'],Q[0]);pred+=1
  with n.load(O/'traces'/name,allow_pickle=False) as z:
   keys={f'layer_{i}__{k}' for i in range(8) for k in ['input','after_self','prefix_suffix','after_cross','output']}
   assert len(z.files)==40 and set(z.files)==keys
   assert all(z[k].shape==(1,256,384) and z[k].dtype==n.float32 and n.isfinite(z[k]).all() for k in keys)
   assert n.array_equal(z['layer_0__input'],X) and all(n.array_equal(z[f'layer_{i}__output'],z[f'layer_{i+1}__input']) for i in range(7))
   assert n.allclose(z['layer_0__after_self'],native['layer_0__after_self'],atol=1e-6,rtol=1e-5)
   if c=='local_graph_donor':assert n.allclose(z['layer_0__prefix_suffix'],native['layer_0__prefix_suffix'],atol=1e-6,rtol=1e-5)
   traces+=1;layers+=8
assert pred==traces==30 and layers==240
print(json.dumps(dict(status='ALL30_ARRAYS_FIXED_Q_X_CHAIN_ISOLATION_PASS',predictions=pred,traces=traces,layers=layers,first_self_native=30,local_first_prefix_native=10,GT_access=0,GPU_calls=0)))
'''
GEOMETRY=r'''
sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['context_index']['path']).read_bytes());logs=[json.loads(x) for x in (O/'responses.jsonl').read_text().splitlines()];assert len(logs)==30
count=0;maxerr=0.
def compare(a,b,s):
 global count,maxerr
 a=a.astype('float64');b=b.astype('float64');d=a-b
 values=dict(max_abs=float(n.abs(d).max()),mean_abs=float(n.abs(d).mean()),RMSE=float(n.sqrt((d*d).mean())),relative_L2=float(n.linalg.norm(d)/max(n.linalg.norm(b),1e-12)))
 for k,v in values.items():
  err=abs(v-s[k]);maxerr=max(maxerr,err);assert n.isclose(v,s[k],atol=1e-10,rtol=1e-9),(k,v,s[k])
 assert bool(n.allclose(a,b,atol=1e-6,rtol=1e-5))==s['allclose'];count+=1
j=0
for r in idx['pairs']:
 with n.load(r['recipient_context']['path'],allow_pickle=False) as z:Q=z['Q'][0]
 order=n.lexsort((Q[:,2],Q[:,1],Q[:,0]))
 with n.load(r['Native_trace']['path'],allow_pickle=False) as z:baseline={k:z[k] for k in z.files}
 with n.load(r['Native_prediction']['path'],allow_pickle=False) as z:P0=z['prediction']
 for condition in q['conditions']:
  label=r['run']+'__'+r['recipient']+'__'+condition;log=logs[j];j+=1
  assert log['index']==j and log['label']==label and log['donor']==r['donor'] and len(log['layers'])==64
  with n.load(O/'traces'/(label+'.npz'),allow_pickle=False) as z:
   for s in log['layers']:
    key=f"layer_{s['layer']}__{s['stage']}";a,b=z[key],baseline[key]
    if s['group']!='all':
     lo,hi={'early':(0,86),'middle':(86,171),'late':(171,256)}[s['group']];a=a[:,order[lo:hi]];b=b[:,order[lo:hi]]
    compare(a,b,s)
  with n.load(O/'predictions'/(label+'.npz'),allow_pickle=False) as z:P=z['prediction']
  compare(P[None],P0[None],log['dense']['normalized']);scale=n.float32(r['normalization']['scale'])
  compare((P*scale)[None],(P0*scale)[None],log['dense']['world_mm'])
assert j==30 and count==1980
print(json.dumps(dict(status='ALL1920_LAYER60_DENSE_RESPONSES_RECOMPUTED_PASS',case_conditions=j,comparisons=count,max_absolute_float_error=maxerr,GT_read=0,new_model_calls=0)))
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
