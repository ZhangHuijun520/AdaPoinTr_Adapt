from pathlib import Path
import os,socket,json,hashlib
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_native_prediction_20261117_v1');b=(r/'SPCG_sixmodel_native_execution_request_v1.json').read_bytes();assert hashlib.sha256(b).hexdigest()=='c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc';q=json.loads(b);o=Path(q['output'])
def read(p):return json.loads(p.read_bytes())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<128*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns);return dict(bytes=s.st_size,sha256=h.hexdigest())
idx=read(Path(q['input_index']['path']));assert record(Path(q['input_index']['path']))=={k:q['input_index'][k] for k in ['bytes','sha256']}
import zipfile,struct,ast,array,sys,math
assert sys.byteorder=='little';count=0
for row in idx['inputs']:
 with zipfile.ZipFile(o/row['prediction_filename']) as z:
  assert set(z.namelist())=={'prediction.npy','coarse.npy'} and len(z.namelist())==2
  for key,n in [('prediction',8192),('coarse',256)]:
   b=z.read(key+'.npy');assert b[:6]==b'\x93NUMPY';version=b[6];assert version in [1,2,3];size=2 if version==1 else 4;hlen=int.from_bytes(b[8:8+size],'little');assert hlen<4096;end=8+size+hlen;header=ast.literal_eval(b[8+size:end].decode());assert header['descr']=='<f4' and header['shape']==(n,3) and header['fortran_order'] is False and len(b)-end==n*12
   values=array.array('f');values.frombytes(b[end:]);assert all(math.isfinite(x) for x in values)
 count+=1
print(json.dumps(dict(checks=dict(all630_arrays_shape_dtype_finite=True,no_extra_RF_GT_arrays=True),files=count)))
