"""One fixed local CPU reference build; no model,checkpoint or prediction reads."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2'
import ast,gc,gzip,hashlib,json,re,sys,time
import importlib.metadata as md
from pathlib import Path
import numpy as np
import psutil
sys.path.insert(0,str(Path(__file__).resolve().parent))
from bcsp_eval_metrics_v1 import surface_references

N=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_bound(r):
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
def emit(p,obj):
 with p.open('x',encoding='ascii') as f:json.dump(obj,f,ensure_ascii=True,indent=2,allow_nan=False)
def main():
 scope=json.loads((N/'reference_preparation_scope_v2.json').read_bytes())
 cases=json.loads(read_bound(scope['case_index']).read_bytes())['cases'];assert len(cases)==210
 read_bound(scope['protocol']);read_bound(scope['original_QC'])
 for record in scope['implementation']:read_bound(record)
 reader=read_bound(scope['raw_reader']);tree=ast.parse(reader.read_text(encoding='utf-8'))
 functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['header','read_mask']]
 namespace=dict(np=np,gzip=gzip,re=re)
 exec(compile(ast.Module(body=functions,type_ignores=[]),'fixed_existing_NRRD_reader','exec'),namespace)
 out=Path(scope['output']);out.mkdir(exist_ok=False)
 start=time.monotonic();case_start=start;written=0;peak=0;rows=[]
 def guard():
  nonlocal peak
  rss=psutil.Process().memory_info().rss;peak=max(peak,rss)
  assert rss<=scope['limits']['RSS_bytes'] and written<=scope['limits']['output_bytes']
  assert time.monotonic()-start<=3600 and time.monotonic()-case_start<=120
 try:
  for i,row in enumerate(cases):
   case_start=time.monotonic();guard();masks={};coords={};files=[]
   for role in ['defective','implant']:
    record=row['raw'][role];p=Path(record['path']);assert not p.is_symlink() and p.resolve().is_relative_to(Path(scope['raw_read_root']).resolve())
    assert sha(p)==record['sha256'];m,a,o=namespace['read_mask'](p);guard()
    masks[role]=m;coords[role]=(a,o);files.append(dict(role=role,path=str(p),sha256=record['sha256']))
   d,g=masks['defective'],masks['implant'];a,o=coords['defective']
   assert d.shape==g.shape and np.array_equal(a,coords['implant'][0]) and np.array_equal(o,coords['implant'][1])
   qc=json.loads(read_bound(row['original_case_QC']).read_bytes())
   assert np.allclose(row['normalization']['center'],qc['center'],rtol=0,atol=1e-10) and row['normalization']['scale']==qc['scale']
   ref=surface_references(g,d,a,o);guard()
   assert ref['a_is_j'].any() and (~ref['a_is_j']).any()
   assert int(ref['a_is_j'].sum())==qc['J_face_keys_paired']
   assert np.isclose(ref['a_weights'][ref['a_is_j']].sum(),qc['D_J_area_mm2'],rtol=1e-12)
   assert np.isclose(ref['a_weights'][~ref['a_is_j']].sum(),qc['G_native_area_mm2'],rtol=1e-12)
   path=out/(row['case_id']+'.npz')
   with path.open('xb') as f:np.savez_compressed(f,**ref)
   written+=path.stat().st_size
   for rec in files:assert sha(Path(rec['path']))==rec['sha256']
   rows.append(dict(case_id=row['case_id'],source_id=row['source_id'],fold=row['fold'],path=str(path),bytes=path.stat().st_size,sha256=sha(path),
    A_faces=len(ref['a_centers']),A_J_faces=int(ref['a_is_j'].sum()),B_triangles=len(ref['b_centers']),raw=files,normalization=row['normalization'],target_array_sha256=row['target_array_sha256'],point_files=row['point_files']))
   guard();print('REFERENCE',i+1,row['case_id'],flush=True)
   del masks,coords,d,g,ref;gc.collect()
  emit(out/'reference_manifest_v1.json',dict(status='FROZEN_210_CASE_A1_A2_B_REFERENCES',cases=rows,protocol_sha256=scope['protocol']['sha256'],complete_C_decoded=False,model_predictions_used=False,
   versions=dict(python=sys.version,numpy=np.__version__,scipy=md.version('scipy'),skimage=md.version('scikit-image'),psutil=md.version('psutil')),seconds=time.monotonic()-start,observed_peak_RSS=peak,reference_bytes=written))
  print(json.dumps(dict(status='REFERENCE_BANK_COMPLETE',cases=210,seconds=time.monotonic()-start,bytes=written)),flush=True)
  return 0
 except BaseException as exc:
  emit(out/'failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),completed_cases=len(rows),partial_manifest=rows,server_operations=0,model_calls=0))
  raise

if __name__=='__main__':raise SystemExit(main())
