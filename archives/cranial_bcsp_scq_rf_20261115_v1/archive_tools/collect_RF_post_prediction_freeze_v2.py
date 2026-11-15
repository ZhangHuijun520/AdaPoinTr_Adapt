"""Bounded formal readonly collector. No model imports, writes or inference remotely."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,zlib
R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2/pending_request_v2'
F=R/'outputs/scq_rf_pred_freeze_20261115_v2';F.mkdir()
Q=B/'payload/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json'
QH='5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9'
assert hashlib.sha256(Q.read_bytes()).hexdigest()==QH;q=json.loads(Q.read_bytes())
prefix="""from pathlib import Path,PurePosixPath
import socket,os,subprocess,json,hashlib,time,sys
assert socket.gethostname()==HOST and os.getuid()==1000
O=Path(OUT);I=Path(INSTALL)
assert not any(p.is_symlink() for p in (O,*O.parents,I,*I.parents))
qp=I/'SCQ_RF_sixmodel_native_prediction_execution_request_v2.json';assert hashlib.sha256(qp.read_bytes()).hexdigest()==QHASH
q=json.loads(qp.read_bytes())
"""
values=dict(HOST=q['identity']['hostname'],OUT=q['output'],INSTALL=q['entry']['path'].rsplit('/',1)[0],QHASH=QH)
class Bind(ast.NodeTransformer):
 def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
prefix=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(prefix))))+'\n'
sources={}
sources['finished']='''assert (O/'exit_code.txt').read_text().strip()=='0' and not (O/'failure.json').exists()
pid=(O/'worker.pid').read_text().strip();p=Path('/proc/'+pid)
assert not p.exists() or q['entry']['path'].encode() not in (p/'cmdline').read_bytes()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
print(json.dumps(dict(status='EXIT0_TMUX_WORKER_ABSENT',hostname=socket.gethostname(),uid=os.getuid(),free_disk_bytes=__import__('shutil').disk_usage(O).free)))
'''
inventory='''def inventory(root):
 files={};dirs=[];total=0
 for p in [root,*sorted(root.rglob('*'))]:
  assert not p.is_symlink() and (p.is_file() or p.is_dir()),str(p)
  n=str(p.relative_to(root))
  if p.is_dir():dirs.append(n);continue
  b=p.stat();total+=b.st_size;assert len(files)<800 and b.st_size<1073741824 and total<2147483648
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
  a=p.stat();fp=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
  assert fp(b)==fp(a)
  files[n]=dict(bytes=a.st_size,sha256=h.hexdigest(),fingerprint=fp(a))
 return dict(files=files,directories=dirs,hashed_bytes=total)
print(json.dumps(dict(status='EXACT_INVENTORY_AND_STABLE_HASHES',output=inventory(O),installed=inventory(I))))
'''
sources['inventory_before']=inventory
sources['metadata']='''import base64
files={};total=0
for root,label in [(O,'output'),(I,'installed')]:
 for p in sorted(root.rglob('*')):
  if not p.is_file() or (root==O and p.suffix in ('.gz','.npz')):continue
  assert not p.is_symlink() and p.stat().st_size<8388608
  b=p.read_bytes();total+=len(b);assert total<16777216
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
print(json.dumps(dict(status='BOUNDED_METADATA_READ',files=files,bytes=total)))
'''
sources['archive']='''import tarfile
c=json.loads((O/'completion.json').read_bytes());rs={r['name']:r for r in c['archive']['members']}
assert len(rs)==len(c['archive']['members'])==636
with tarfile.open(O/'development_predictions_v1.tar.gz') as t:
 ms=t.getmembers();assert len(ms)==636 and {m.name for m in ms}==set(rs)
 for m in ms:
  assert m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and m.size<8388608
  b=t.extractfile(m).read();r=rs[m.name];p=O/m.name
  assert p.is_file() and len(b)==r['bytes']==p.stat().st_size and hashlib.sha256(b).hexdigest()==r['sha256']==hashlib.sha256(p.read_bytes()).hexdigest(),m.name
print(json.dumps(dict(status='ALL636_ARCHIVE_MEMBER_BYTES_MATCH',members=636,server_extractions=0)))
'''
sources['arrays']='''sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['input_index']['path']).read_bytes());count=0
for row in idx['inputs']:
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:
  assert len(z.files)==9 and set(z.files)=={'prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'}
  d,c,r,v=z['prediction'],z['coarse'],z['Qraw'],z['delta']
  assert d.shape==(8192,3) and c.shape==r.shape==v.shape==(256,3)
  assert all(x.dtype==n.float32 and n.isfinite(x).all() for x in [d,c,r,v])
  assert n.allclose(r+v,c,rtol=2e-5,atol=2e-6)
  a,b,e,f,g=z['Q0'],z['Q1'],z['Q2'],z['delta0'],z['delta1']
  assert all(x.shape==(256,3) and x.dtype==n.float32 and n.isfinite(x).all() for x in [a,b,e,f,g])
  assert n.array_equal(a,r) and n.array_equal(e,c) and n.allclose(a+f,b,rtol=2e-5,atol=2e-6) and n.allclose(b+g,e,rtol=2e-5,atol=2e-6)
  if row['variant']=='S':assert n.array_equal(b,e) and n.array_equal(f,v) and n.count_nonzero(g)==0
 count+=1
assert count==630 and not list((O/'context').iterdir()) and not list((O/'traces').iterdir())
print(json.dumps(dict(status='ALL630_FP32_FINITE_QRAW_QUSED_DELTA_P_PASS',predictions=count,context=0,traces=0,GT_arrays_read=0,GPU_calls=0)))
'''
sources['geometry']='''sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['input_index']['path']).read_bytes());logs=[json.loads(x) for x in (O/'geometry_summary.jsonl').read_text().splitlines()];assert len(logs)==630
maxerr=0.
for row,g in zip(idx['inputs'],logs):
 assert g['run']==row['run'] and g['case_id']==row['case_id']
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:c=z['coarse'].astype('float64');d=z['prediction'].astype('float64');raw=z['Qraw'].astype('float64');delta=z['delta']
 for key,x in [('coarse',c),('dense',d),('Qraw',raw)]:
  mean=x.mean(0);v=x-mean;expected=dict(centroid=mean,bbox_min=x.min(0),bbox_max=x.max(0),radius_gyration=n.sqrt((v*v).sum(1).mean()),covariance_eigenvalues=n.linalg.eigvalsh(v.T@v/len(x)))
  for k,value in expected.items():
   err=float(n.max(n.abs(n.asarray(g[key][k])-value)));maxerr=max(maxerr,err);assert n.allclose(g[key][k],value,rtol=1e-10,atol=1e-12)
 assert g['coarse']['finite_count']==256 and g['dense']['finite_count']==8192
 offsets=d.reshape(256,32,3)-c[:,None,:]
 assert n.allclose(g['mean_dense_minus_coarse'],offsets.mean((0,1)),rtol=1e-10,atol=1e-12) and n.allclose(g['offset_mean_squared_radius'],(offsets**2).sum(2).mean(),rtol=1e-10,atol=1e-12)
 assert g['delta_mean_norm']==float(n.linalg.norm(delta,axis=-1).mean()) and g['delta_max_norm']==float(n.linalg.norm(delta,axis=-1).max())
print(json.dumps(dict(status='ALL630_GEOMETRY_LOGS_RECOMPUTED_PASS',predictions=630,max_absolute_stat_error=maxerr,GT_read=False,scoring=False)))
'''
sources['RF_stages']="""sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['input_index']['path']).read_bytes());gs=[json.loads(x) for x in (O/'geometry_summary.jsonl').read_text().splitlines()];assert len(gs)==630
for row,g in zip(idx['inputs'],gs):
 assert g['run']==row['run'] and g['case_id']==row['case_id'] and g['RF_second_stage_applicable'] is (row['variant']!='S')
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:
  assert set(g['stage_centroids'])=={'Q0','Q1','Q2','delta0','delta1'}
  for k in g['stage_centroids']:assert n.array_equal(n.asarray(g['stage_centroids'][k]),z[k].mean(0))
print(json.dumps(dict(status='ALL630_RF_STAGE_CENTROID_LOGS_RECOMPUTED_PASS',predictions=630,new_forward=0,GT_read=False)))
"""
sources['inventory_after']=inventory
scripts=[]
def add(label,code):
 ast.parse(code,feature_version=(3,8));compile(code,label,'exec');b=base64.b85encode(zlib.compress(code.encode(),9)).decode()
 cmd=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c','import zlib,base64;exec(zlib.decompress(base64.b85decode('+repr(b)+')))']);assert len(cmd.encode())<=2048,(label,len(cmd.encode()))
 scripts.append((label,code,cmd))
for name in ['finished','inventory_before','metadata']:add(name,prefix+sources[name])
static=B/'preexecution_static_v2'
for p in [*sorted(static.glob('asset_*.remote.py')),*sorted(static.glob('checkpoint_*.remote.py')),static/'inputs210.remote.py']:add('fresh_'+p.stem,p.read_text(encoding='utf-8'))
for name in ['archive','arrays','geometry','RF_stages','inventory_after']:add(name,prefix+sources[name])
def save(n,v):
 with (F/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
save('bounded_scope_v1.json',dict(status='READONLY_FORMAL_AUDIT_SCOPE',request_sha256=QH,scripts=len(scripts),max_command_bytes=max(len(v[2].encode()) for v in scripts),expected_predictions=630,expected_output_files=644,expected_installed_files=24,server_writes=0,new_forward=0,checkpoint_loads=0))
stage='begin'
try:
 for label,code,cmd in scripts:
  stage=label
  with (F/(label+'.remote.py')).open('x',encoding='utf-8') as f:f.write(code)
  x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--',cmd],capture_output=True,timeout=75)
  for k,b in [('stdout',x.stdout),('stderr',x.stderr)]:
   with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
  assert x.returncode==0,(label,x.stdout.decode(errors='replace')[-1800:]);v=json.loads(x.stdout);save(label+'_result_v1.json',v)
  if label=='metadata':
   for name,r in v['files'].items():
    p=F/'downloads'/name;p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(r['base64']);assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
    with p.open('xb') as f:f.write(b)
  print(json.dumps(dict(stage=label,status=v['status'])),flush=True)
 save('collection_complete_v1.json',dict(status='READONLY_COLLECTION_COMPLETE',stages=len(scripts),request_sha256=QH,server_writes=0,new_forward=0))
except BaseException as exc:
 save('collection_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',stage=stage,error=repr(exc)));raise
