"""Local fixed3 metadata/coordinate provenance; never creates bone masks."""
import os
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
import gc,hashlib,itertools,json,time,zipfile
from pathlib import Path
import numpy as np
import psutil
N=Path(__file__).resolve().parent
DT=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
T=np.diag([-1.,-1.,1.])
def need(ok,text):
 if not ok:raise ValueError(text)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
def emit(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False)
def keys(bits):
 b=bits.astype(np.uint64)
 return b[:,0]*np.uint64(11400714785074694791)^b[:,1]*np.uint64(14029467366897019727)^b[:,2]*np.uint64(1609587929392839161)
def match_exact(bits,q,found):
 # Hash narrows candidates only; all matches additionally compare12 coordinate bytes.
 k=keys(q);order=np.argsort(k);ks=k[order];positions=np.searchsorted(ks,keys(bits));safe=np.minimum(positions,len(ks)-1)
 candidate=np.flatnonzero((positions<len(ks))&(ks[safe]==keys(bits)))
 for i in candidate:
  j=order[positions[i]]
  if np.array_equal(bits[i],q[j]):found[j]=True
def inspect_original(stream,size,q,guard):
 head=stream.read(84);need(len(head)==84 and b'SPACE=RAS' in head[:80],'explicit original STL RAS header')
 count=int.from_bytes(head[80:84],'little');need(size==84+50*count,'original STL record size')
 found=np.zeros(len(q),bool);h=hashlib.sha256(head);lo=np.full(3,np.inf);hi=-lo
 for start in range(0,count,65536):
  data=stream.read(min(65536,count-start)*50);need(len(data)==min(65536,count-start)*50,'original STL truncated');h.update(data);guard(len(data))
  v=np.frombuffer(data,dtype=DT)['v'];need(np.isfinite(v).all(),'original finite vertices');lo=np.minimum(lo,v.min(axis=(0,1)));hi=np.maximum(hi,v.max(axis=(0,1)))
  if not found.all():match_exact(np.ascontiguousarray(v.reshape(-1,3)).view('<u4'),q,found)
 return dict(header80=head[:80].decode('ascii',errors='backslashreplace').rstrip('\x00 '),sha256=h.hexdigest(),triangles=count,minimum=lo.tolist(),maximum=hi.tolist(),query_count=len(q),exact_query_matches=int(found.sum()),all_sampled_coordinates_found=bool(found.all()))
def main():
 scope=json.loads((N/'scope.json').read_bytes());need(sha(__file__)==scope['implementation_sha256'],'code identity')
 out=N/'results';out.mkdir(exist_ok=False);start=time.monotonic();case_start=start;read_bytes=0;peak=0;rows=[]
 def guard(n=0):
  nonlocal read_bytes,peak
  read_bytes+=n;peak=max(peak,psutil.Process().memory_info().rss)
  need(read_bytes<=6442450944 and peak<=8589934592 and time.monotonic()-start<=300 and time.monotonic()-case_start<=120,'bounded provenance budget')
 try:
  archive=Path(scope['archive']['path']);st=archive.stat();need(st.st_size==scope['archive']['bytes'],'official archive size');md5=hashlib.md5();h=hashlib.sha256()
  with archive.open('rb') as f:
   for b in iter(lambda:f.read(8388608),b''):guard(len(b));md5.update(b);h.update(b)
  need(md5.hexdigest()==scope['archive']['official_v20_md5'],'official v20 archive MD5 mismatch')
  archive_identity=dict(path=str(archive),bytes=st.st_size,MD5=md5.hexdigest(),SHA256=h.hexdigest(),official_v20_MD5_match=True,other_case_geometry_decoded=False)
  print('OFFICIAL_ARCHIVE_MD5_MATCH',flush=True)
  with zipfile.ZipFile(archive) as z:
   for case in scope['cases']:
    case_start=time.monotonic();guard();p=Path(case['clear_stl']['path']);need(p.stat().st_size==case['clear_stl']['bytes'] and sha(p)==case['clear_stl']['sha256'],'clear STL binding')
    guard(p.stat().st_size)
    with p.open('rb') as f:
     head=f.read(84);count=int.from_bytes(head[80:84],'little');need(p.stat().st_size==84+50*count,'clear STL record size')
     ids=np.linspace(0,count*3-1,256,dtype=np.int64);points=[]
     for i in ids:f.seek(84+(int(i)//3)*50+12+(int(i)%3)*12);points.append(np.frombuffer(f.read(12),dtype='<f4').copy())
    points=np.array(points,dtype='<f4');need(np.isfinite(points).all(),'clear samples finite');q=np.unique(points.view('<u4'),axis=0)
    member=case['original_stl'];info=z.getinfo(member['member']);need(info.file_size==member['bytes'] and info.CRC==member['CRC'],'original STL ZIP binding')
    with z.open(member['member']) as f:original=inspect_original(f,info.file_size,q,guard)
    source=case['admission'];bounds=source['nrrd']['physical_bounds'];lo=np.array(bounds['minimum']);hi=np.array(bounds['maximum']);corners=np.array(list(itertools.product(*zip(lo,hi))))@T
    ras_lo=corners.min(0);ras_hi=corners.max(0);clear_lo=np.array(source['clear_stl']['minimum']);clear_hi=np.array(source['clear_stl']['maximum'])
    inside=bool(np.all(clear_lo>=original['minimum']) and np.all(clear_hi<=original['maximum']))
    clear_frame_supported=original['all_sampled_coordinates_found'] and inside
    geometry=source['historical_ellipsoid'];center=np.array(geometry['cut_center_mm']);frame=np.array(geometry['frame']);radii=np.array(geometry['radii_mm'])
    metadata_transform=dict(from_frame='ORIGINAL_STL_RAS',to_frame='NRRD_DECLARED_LPS',matrix4x4=np.diag([-1.,-1.,1.,1.]).tolist(),basis='Explicit SPACE=RAS original STL header and NRRD left-posterior-superior;no fit/ICP',clear_STL_inheritance_supported_by_fixed_sample=clear_frame_supported,not_a_whole_mesh_coordinate_proof=True)
    row=dict(source_id=case['source_id'],original_STL=original,clear_header80=head[:80].decode('ascii',errors='backslashreplace').rstrip('\x00 '),sample_indices=ids.tolist(),sample_clear_points_RAS=points.tolist(),clear_bounds_within_original_bounds=inside,
     coordinate_convention=metadata_transform,NRRD_bounds_RAS=dict(minimum=ras_lo.tolist(),maximum=ras_hi.tolist()),clear_mesh_fully_inside_NRRD_FOV_after_metadata_transform=bool(np.all(clear_lo>=ras_lo)&np.all(clear_hi<=ras_hi)),
     fixed_cut_in_LPS_if_clear_inherits_RAS=dict(center=(T@center).tolist(),frame=(T@frame).tolist(),radii=radii.tolist()) if clear_frame_supported else None,
     historical_cut_center_inside_NRRD_FOV_after_transform=bool(np.all(center>=ras_lo)&np.all(center<=ras_hi)) if clear_frame_supported else None,
     complete_bone_mask_obtained=False,segmentation_applied=False,fit_or_repair_applied=False)
    emit(out/(case['source_id']+'_coordinate_evidence.json'),row);rows.append(row);gc.collect();guard()
    print('COORDINATE_EVIDENCE',case['source_id'],original['exact_query_matches'],original['query_count'],clear_frame_supported,flush=True)
  need(archive.stat().st_mtime_ns==st.st_mtime_ns and archive.stat().st_size==st.st_size,'archive changed')
  emit(out/'results.json',dict(status='COORDINATE_METADATA_COMPLETED_COMPLETE_BONE_MASKS_NOT_OBTAINED',archive_identity=archive_identity,cases=rows,seconds=time.monotonic()-start,counted_read_bytes=read_bytes,monitored_RSS_max=peak,source_files_written=0,complete_bone_masks_created=0,server_calls=0,GPU_calls=0,training=0))
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),completed_cases=rows,read_bytes=read_bytes));raise
if __name__=='__main__':main()
