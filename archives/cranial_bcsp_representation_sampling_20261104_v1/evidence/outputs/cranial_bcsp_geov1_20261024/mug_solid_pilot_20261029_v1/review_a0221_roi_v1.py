"""Read-only local foreground review; no new masks or sampling produced."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',MPLBACKEND='Agg')
from pathlib import Path
import json,hashlib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
N=Path(__file__).resolve().parent/'a0221_solid_pilot_20261102_v1'
O=N/'foreground_review_v1';O.mkdir(exist_ok=False)
os.environ['MPLCONFIGDIR']=str(O/'mplconfig')
import matplotlib.pyplot as plt
p=N/'local_voxel_evidence.npz';source_hash=hashlib.sha256(p.read_bytes()).hexdigest()
a=np.load(p);raw=a['raw'];C=a['C'];R=a['R'];G=a['G'];D=a['D'];A=a['directions'];o=a['origin'];start=a['index_start'];origin=start@A+o;inv=np.linalg.inv(A);steps=np.linalg.norm(A,axis=1)
excluded=raw&~C;dist=ndimage.distance_transform_edt(~C,sampling=steps)
def summary(v):return {'n':len(v),'median_mm':float(np.median(v)),'p95_mm':float(np.percentile(v,95)),'maximum_mm':float(v.max())}
result={'input_npz_sha256':source_hash,'scope':'fixed cut plus existing 5mm support AABB; cropped component sizes are lower bounds','excluded_in_cut':int((excluded&R).sum()),'excluded_in_support_crop':int(excluded.sum()),'excluded_to_C_center_distance':summary(dist[excluded]),'excluded_in_cut_within_1mm_of_C_centers':int((excluded&R&(dist<=1)).sum()),'excluded_in_cut_farther_than_2mm':int((excluded&R&(dist>2)).sum())}
for conn in [6,26]:
    labs,n=ndimage.label(excluded,structure=ndimage.generate_binary_structure(3,1 if conn==6 else 3));sizes=np.bincount(labs.ravel());sizes[0]=0;ids=np.unique(labs[excluded&R]);ids=ids[ids>0]
    result['excluded_%d_connectivity'%conn]={'crop_component_count':int(n),'components_intersecting_cut':len(ids),'largest_crop_component_sizes_intersecting_cut':sorted(sizes[ids].tolist(),reverse=True)[:12],'cut_voxels_in_crop_components_le_3':int(np.sum((excluded&R)&(sizes[labs]<=3)))}
# Direct face adjacency and diagonal proximity are geometric observations only.
result['excluded_touching_C_in_26_neighborhood_in_cut']=int((excluded&R&ndimage.binary_dilation(C,structure=np.ones((3,3,3)))).sum())
# Profile audit: sample fixed LPS x-lines through side calvarium. No smoothing or repair.
profiles=[]
for y in [-10.,0.,10.]:
 for z in [55.,65.,75.]:
    xx=np.arange(25,72,.2);w=np.column_stack([xx,np.full(len(xx),y),np.full(len(xx),z)]);idx=((w-origin)@inv).T
    valid=((idx>=0)&(idx<=np.array(C.shape)[:,None]-1)).all(0)
    line=ndimage.map_coordinates(C.astype(np.uint8),idx,order=0,prefilter=False);runs=ndimage.find_objects(ndimage.label(line)[0]);intervals=[[float(xx[s[0].start]),float(xx[s[0].stop-1]+.2)] for s in runs]
    profiles.append({'y_LPS_mm':y,'z_LPS_mm':z,'retained_foreground_x_intervals_mm':intervals,'full_profile_inside_saved_crop':bool(valid.all()),'resolution_mm':.2})
result['side_shell_profiles']=profiles
fig,axes=plt.subplots(2,3,figsize=(15,9),constrained_layout=True)
for ax,(axis,value) in zip(axes.flat,[(1,-10),(1,0),(1,10),(2,55),(2,65),(2,75)]):
    u,v=[k for k in range(3) if k!=axis];bounds={0:(28,70),1:(-25,25),2:(40,92)};xx=np.arange(*bounds[u],.2);yy=np.arange(*bounds[v],.2);X,Y=np.meshgrid(xx,yy);w=np.empty(X.shape+(3,));w[...,axis]=value;w[...,u]=X;w[...,v]=Y;idx=((w-origin)@inv).reshape(-1,3).T
    def res(m):return ndimage.map_coordinates(m.astype(np.uint8),idx,order=0,prefilter=False).reshape(X.shape)
    cc=res(C);ex=res(excluded);rg=res(R);rgb=np.zeros(X.shape+(3,));rgb[cc>0]=[.8,.8,.8];rgb[(cc>0)&(rg>0)]=[.15,.7,1];rgb[ex>0]=[1,.35,.1]
    ax.imshow(rgb,origin='lower',extent=[xx[0]-.1,xx[-1]+.1,yy[0]-.1,yy[-1]+.1],aspect='equal');ax.set_title('LPS %s = %g mm'%('xyz'[axis],value));ax.set_xlabel('xyz'[u]+' mm');ax.set_ylabel('xyz'[v]+' mm')
fig.suptitle('A0221 fixed ROI foreground review: retained gray/cyan; excluded orange\nNearest-neighbor display at 0.2 mm; source resolution unchanged; crop outside shown as background')
fig.savefig(O/'local_foreground_sections.png',dpi=150);plt.close(fig)
assert hashlib.sha256(p.read_bytes()).hexdigest()==source_hash
(O/'findings.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
