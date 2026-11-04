"""Fixed3 MUG source admission. Never thresholds gray volumes or repairs meshes."""
import os
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2'
import argparse,gc,gzip,hashlib,io,itertools,json,re,sys,time,zipfile
from pathlib import Path
import numpy as np
import psutil
N=Path(__file__).resolve().parent
def need(ok,text):
 if not ok:raise ValueError(text)
def h(raw):return hashlib.sha256(raw).hexdigest()
def dump(p,x):
 with Path(p).open('x',encoding='ascii') as f:json.dump(x,f,ensure_ascii=True,indent=2,allow_nan=False)
def decode_nrrd(blob):
 match=re.search(br'\r?\n\r?\n',blob[:8192]);need(match is not None,'bounded NRRD header')
 lines=blob[:match.start()].decode('ascii').splitlines();need(lines[0].startswith('NRRD000'),'NRRD magic')
 fields={k:v.strip() for k,v in (s.split(':',1) for s in lines[1:] if s and not s.startswith('#') and ':' in s)}
 need(fields.get('type')=='short' and fields.get('dimension')=='3' and fields.get('encoding')=='gzip','fixed scalar int16 gzip NRRD')
 need(not {'data file','byte skip','line skip'}&fields.keys(),'detached/skip data forbidden')
 shape=tuple(map(int,fields['sizes'].split()));need(len(shape)==3 and all(n>0 for n in shape) and int(np.prod(shape))<=160000000,'voxel budget')
 need(fields.get('endian') in ['little','big'],'explicit endian')
 dtype=np.dtype('<i2' if fields['endian']=='little' else '>i2')
 directions=np.array([[float(x) for x in v.split(',')] for v in re.findall(r'\(([^)]+)\)',fields['space directions'])])
 origin=np.array([float(x) for x in fields['space origin'].strip('()').split(',')])
 need(directions.shape==(3,3) and origin.shape==(3,) and np.isfinite(directions).all() and np.isfinite(origin).all() and abs(np.linalg.det(directions))>1e-9,'physical affine')
 expected=int(np.prod(shape))*2
 with gzip.GzipFile(fileobj=io.BytesIO(blob[match.end():])) as z:data=z.read(expected+1)
 need(len(data)==expected,'exact decoded bytes')
 return np.frombuffer(data,dtype=dtype).reshape(shape,order='F'),directions,origin,fields
def histogram(volume):
 hist=np.zeros(65536,np.int64);flat=volume.ravel(order='K')
 for start in range(0,len(flat),1048576):hist+=np.bincount(flat[start:start+1048576].astype(np.int32)+32768,minlength=65536)
 values=np.flatnonzero(hist)-32768;counts=hist[values+32768];cum=hist.cumsum();total=int(cum[-1])
 percent={str(q):int(np.searchsorted(cum,q*total/100,side='left')-32768) for q in [0.5,1,5,50,95,99,99.5]}
 top=np.argsort(counts)[-12:][::-1]
 return dict(unique_values=len(values),minimum=int(values[0]),maximum=int(values[-1]),negative_voxels=int(hist[:32768].sum()),zero_voxels=int(hist[32768]),positive_voxels=int(hist[32769:].sum()),
  percentiles=percent,most_frequent=[dict(value=int(values[i]),count=int(counts[i])) for i in top],
  binary_value_candidate=bool(set(values.tolist()) in [{0,1},{0,255}]),label_semantics='UNCONFIRMED_NO_BONE_MASK_METADATA'),values,counts
def physical_bounds(shape,a,o):
 corners=np.array(list(itertools.product(*[(0,n-1) for n in shape])))@a+o
 return dict(minimum=corners.min(0).tolist(),maximum=corners.max(0).tolist(),center_span_mm=(corners.max(0)-corners.min(0)).tolist(),
  axis_center_lengths_mm=((np.array(shape)-1)*np.linalg.norm(a,axis=1)).tolist())
def stl_bounds(stream,size):
 head=stream.read(84);need(len(head)==84,'STL header');count=int.from_bytes(head[80:84],'little');need(size==84+50*count and count>0,'binary STL record count')
 dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')]);lo=np.full(3,np.inf);hi=-lo;digest=hashlib.sha256(head)
 for start in range(0,count,65536):
  raw=stream.read(min(65536,count-start)*50);need(len(raw)==min(65536,count-start)*50,'STL exact bytes');digest.update(raw)
  vertices=np.frombuffer(raw,dtype=dtype)['vertices'];need(np.isfinite(vertices).all(),'finite STL');lo=np.minimum(lo,vertices.min(axis=(0,1)));hi=np.maximum(hi,vertices.max(axis=(0,1)))
 return dict(triangles=count,minimum=lo.tolist(),maximum=hi.tolist(),span_mm=(hi-lo).tolist(),sha256=digest.hexdigest())
def main():
 p=argparse.ArgumentParser();p.add_argument('--scope',required=True);p.add_argument('--scope-sha256',required=True);args=p.parse_args()
 scope_path=Path(args.scope);need(h(scope_path.read_bytes())==args.scope_sha256,'frozen scope SHA');scope=json.loads(scope_path.read_bytes())
 need(h(Path(__file__).read_bytes())==scope['implementation_sha256'],'implementation identity')
 out=Path(scope['output']);out.mkdir(exist_ok=False);start=time.monotonic();case_start=start;peak=0;rows=[];panels=[]
 def guard():
  nonlocal peak
  peak=max(peak,psutil.Process().memory_info().rss);need(peak<=8589934592 and time.monotonic()-start<=3600 and time.monotonic()-case_start<=900,'RSS/time budget')
  need(sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=1073741824,'output budget')
 archive=Path(scope['archive']['path']);st=archive.stat();need(st.st_size==scope['archive']['bytes'] and st.st_mtime_ns==scope['archive']['mtime_ns'],'archive stat drift')
 try:
  with zipfile.ZipFile(archive) as z:
   for item in scope['cases']:
    case_start=time.monotonic();guard();sid=item['source_id'];name=item['nrrd']['member'];info=z.getinfo(name)
    need(info.file_size==item['nrrd']['bytes'] and info.CRC==item['nrrd']['CRC'],'fixed ZIP member metadata')
    need(info.file_size<=67108864,'compressed NRRD member budget');blob=z.read(name);need(len(blob)==info.file_size,'ZIP exact member')
    volume,a,o,fields=decode_nrrd(blob);guard();stats,values,counts=histogram(volume);bounds=physical_bounds(volume.shape,a,o)
    path=Path(item['clear_stl']['path']);before=path.stat()
    need(not any(p.is_symlink() for p in (path,*path.parents)) and before.st_size==item['clear_stl']['bytes'],'clear STL type/size')
    with path.open('rb') as f:mesh=stl_bounds(f,before.st_size)
    need(mesh['sha256']==item['clear_stl']['sha256'],'historical clear STL SHA')
    after=path.stat();need((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'STL changed')
    need(h(z.read(name))==h(blob),'NRRD member changed')
    # No binary mask is inferred from scalar sign or grayscale intensity.
    reasons=[]
    if not stats['binary_value_candidate']:reasons.append('SCALAR_VALUES_ARE_NOT_A_BINARY_BONE_MASK')
    else:reasons.append('BINARY_VALUES_ALONE_DO_NOT_PROVE_BONE_LABEL_SEMANTICS')
    if min(volume.shape)<3:reasons.append('LESS_THAN_THREE_SLICES_ON_ONE_AXIS_NOT_A_COMPLETE_3D_SKULL_VOLUME')
    inside=all(bounds['minimum'][k]<=mesh['minimum'][k] and bounds['maximum'][k]>=mesh['maximum'][k] for k in range(3))
    if not inside:reasons.append('NRRD_CENTER_BOUNDS_DO_NOT_CONTAIN_CLEAR_STL_UNDER_IDENTITY_COORDINATES')
    reasons.append('NO_VERIFIED_NRRD_TO_STL_PHYSICAL_CORRESPONDENCE_FOR_CUT_PARAMETERS')
    row=dict(source_id=sid,status='UNRESOLVED_SOURCE_NOT_ADMITTED_NO_DEFECT_GENERATED',blocking_reasons=reasons,
     nrrd=dict(member=name,bytes=len(blob),sha256=h(blob),header=fields,shape=list(volume.shape),dtype=str(volume.dtype),directions=a.tolist(),origin=o.tolist(),physical_bounds=bounds,scalar_statistics=stats),
     clear_stl=dict(path=str(path),bytes=before.st_size,**mesh),historical_ellipsoid=item['historical_ellipsoid'],
     coordinate_comparison=dict(identity_mapping_verified=False,STL_inside_NRRD_center_AABB=inside,interpretation='Bounds compared without fitting;STL has no coordinate-system declaration;no ICP/shift/scale applied'),
     segmentation_applied=False,threshold_applied=False,defects_generated=0,point_pairs_generated=0)
    dump(out/(sid+'_source_admission.json'),row);rows.append(row)
    slices=[]
    for axis in range(3):slices.append(np.take(volume,volume.shape[axis]//2,axis=axis).copy())
    panels.append(dict(source_id=sid,slices=slices,shape=volume.shape,steps=np.linalg.norm(a,axis=1),vmin=stats['percentiles']['1'],vmax=stats['percentiles']['99']))
    with (out/(sid+'_scalar_histogram.npz')).open('xb') as f:np.savez_compressed(f,values=values,counts=counts)
    print('SOURCE_NOT_ADMITTED',sid,stats['unique_values'],list(volume.shape),flush=True)
    del volume,blob;gc.collect();guard()
  need(archive.stat().st_size==st.st_size and archive.stat().st_mtime_ns==st.st_mtime_ns,'archive changed across batch')
  os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(out/'mplconfig')
  import matplotlib;matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  fig,axes=plt.subplots(3,3,figsize=(13,11),constrained_layout=True)
  for ri,panel in enumerate(panels):
   for axis in range(3):
    ax=axes[ri,axis];u,v=[i for i in range(3) if i!=axis];im=panel['slices'][axis]
    obj=ax.imshow(im.T,origin='lower',cmap='gray',vmin=panel['vmin'],vmax=max(panel['vmin']+1,panel['vmax']),
     extent=[-.5*panel['steps'][u],(im.shape[0]-.5)*panel['steps'][u],-.5*panel['steps'][v],(im.shape[1]-.5)*panel['steps'][v]],aspect='equal',interpolation='nearest')
    ax.set_title(panel['source_id']+' | axis'+str(axis)+' mid | shape '+str(tuple(panel['shape'])),fontsize=9)
    ax.set_xlabel('axis'+str(u)+' distance (mm)');ax.set_ylabel('axis'+str(v)+' distance (mm)');fig.colorbar(obj,ax=ax,shrink=.65,label='Scalar value')
  fig.suptitle('MUG fixed3 source admission: native center slices; no bone mask / no cut / no point sampling',fontsize=13)
  fig.supxlabel('Equal-mm axis scaling. 1st-99th percentile display window only; no segmentation or geometric fitting.',fontsize=10)
  fig.savefig(out/'source_volume_sections_v1.png',dpi=150);plt.close(fig);guard()
  result=dict(status='FIXED3_SOURCE_ADMISSION_COMPLETED_ALL_UNRESOLVED',cases=rows,source_count=3,admitted=0,not_admitted=3,defects_generated=0,point_pairs_generated=0,
   scientific_status='ENTITY_DEFECT_AND_8K_SAMPLING_VALIDATION_NOT_RUN_BECAUSE_NO_TRUSTED_COMPLETE_BONE_MASK',
   server_calls=0,GPU_calls=0,training=0,thresholds_or_mesh_repairs_applied=False,source_bytes_unchanged=True,
   seconds=time.monotonic()-start,monitored_peak_RSS_bytes=peak,limits=scope['limits'],scope_sha256=args.scope_sha256)
  dump(out/'results.json',result);print(json.dumps({k:v for k,v in result.items() if k!='cases'}),flush=True)
 except BaseException as exc:
  dump(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),completed_source_rows=rows,server_calls=0,GPU_calls=0,training=0));raise
if __name__=='__main__':main()
