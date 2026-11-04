"""One exploratory A0221 solid-cut pilot. Source mask is never overwritten."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MPLBACKEND='Agg')
import json,sys,zipfile,hashlib,gc
from pathlib import Path
import numpy as np
from scipy import ndimage
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N))
from source_admission_v1 import decode_nrrd
O=N/'a0221_solid_pilot_20261102_v1'
O.mkdir(exist_ok=False)
os.environ['MPLCONFIGDIR']=str(O/'mplconfig')
import matplotlib.pyplot as plt
center=np.array([48.,0.,65.]);radii=np.array([16.,20.,22.])
protocol={'source':'A0221','center_LPS_mm':center.tolist(),'radii_LPS_mm':radii.tolist(),'support_mm':5,'required_FOV_margin_mm':5,'selection':'single exploratory lateral calvarial ROI; no search/retry','foreground':'raw versus largest 6-connected foreground; no filling/smoothing; derived mask is not expert GT','samples':{'D':8192,'G':8192},'seed':20261102}
(O/'protocol.json').write_text(json.dumps(protocol,indent=2))
s=next(x for x in json.loads((N/'other_source_check_v1/results.json').read_text()) if x['id']=='A0221')
with zipfile.ZipFile(s['archive']) as z:b=z.read(s['member'])
assert hashlib.sha256(b).hexdigest()==s['sha256']
a,A,o,f=decode_nrrd(b);raw=a.astype(bool);del a,b
inv=np.linalg.inv(A);steps=np.linalg.norm(A,axis=1)
corners=np.array(list(__import__('itertools').product(*zip(center-radii-5,center+radii+5))))
ci=(corners-o)@inv
margin=float(np.min(np.minimum(ci,np.array(raw.shape)-1-ci)*steps))
assert margin>=5,('FOV margin',margin)
labels,n=ndimage.label(raw);counts=np.bincount(labels.ravel());counts[0]=0;main=labels==counts.argmax();del labels
# Construct ellipsoid analytically in physical LPS, chunked along index axis0.
R=np.zeros(raw.shape,bool)
j,k=np.meshgrid(np.arange(raw.shape[1]),np.arange(raw.shape[2]),indexing='ij')
for i in range(raw.shape[0]):
    w=i*A[0]+j[...,None]*A[1]+k[...,None]*A[2]+o
    R[i]=np.sum(((w-center)/radii)**2,axis=-1)<=1
C=main;G=C&R;D=C&~R
assert G.any() and D.any() and not (D&G).any() and np.array_equal(D|G,C)
rng=np.random.default_rng(20261102)
def faces(mask,other):
    pts=[];axes=[];signs=[];joint=[];areas=[]
    for ax in range(3):
        uv=[x for x in range(3) if x!=ax];area=float(np.linalg.norm(np.cross(A[uv[0]],A[uv[1]])))
        for sign in [-1,1]:
            neigh=np.zeros_like(mask);oth=np.zeros_like(mask)
            src=[slice(None)]*3;dst=src.copy();src[ax]=slice(1,None) if sign==1 else slice(None,-1);dst[ax]=slice(None,-1) if sign==1 else slice(1,None)
            neigh[tuple(dst)]=mask[tuple(src)];oth[tuple(dst)]=other[tuple(src)]
            ix=np.argwhere(mask&~neigh);pts.append(ix);axes.append(np.full(len(ix),ax,np.int8));signs.append(np.full(len(ix),sign,np.int8));joint.append(oth[tuple(ix.T)]);areas.append(np.full(len(ix),area))
    return [np.concatenate(x) for x in [pts,axes,signs,joint,areas]]
gf=faces(G,D);df=faces(D,G)
def joint_centers(fs):
    ix,ax,sg,jt,ar=fs;return ix[jt]@A+o+.5*A[ax[jt]]*sg[jt,None]
gj=joint_centers(gf);dj=joint_centers(df)
from scipy.spatial import cKDTree
assert len(gj)>0 and len(gj)==len(dj)
max_joint_dist=float(cKDTree(dj).query(gj)[0].max());assert max_joint_dist<1e-8
assert np.isclose(gf[4][gf[3]].sum(),df[4][df[3]].sum())
def sample(fs):
    ix,ax,sg,jt,ar=fs;take=rng.choice(len(ix),8192,p=ar/ar.sum());q=ix[take].astype(float);q[np.arange(len(q)),ax[take]]+=.5*sg[take]
    for a in range(3):q[:,a]+=rng.uniform(-.5,.5,len(q))*(ax[take]!=a)
    return q@A+o,jt[take]
gp,gl=sample(gf);dp,dl=sample(df)
np.savez_compressed(O/'sample_points.npz',D_LPS=dp,G_LPS=gp,G_is_cutwall=gl,D_is_cutwall=dl)
rawG=raw&R
result={'source_sha256':s['sha256'],'protocol':protocol,'support_AABB_min_FOV_margin_mm':margin,'raw_foreground_voxels':int(raw.sum()),'derived_foreground_voxels':int(C.sum()),'removed_total':int((raw&~C).sum()),'removed_in_cut':int((rawG&~C).sum()),'raw_cut_voxels':int(rawG.sum()),'G_voxels':int(G.sum()),'D_voxels':int(D.sum()),'G_volume_mm3':float(G.sum()*abs(np.linalg.det(A))),'complement_exact':True,'G_surface_faces':len(gf[0]),'G_native_faces':int((~gf[3]).sum()),'G_cutwall_faces':int(gf[3].sum()),'cutwall_area_mm2':float(gf[4][gf[3]].sum()),'native_surface_area_mm2':float(gf[4][~gf[3]].sum()),'shared_faces_max_center_distance_mm':max_joint_dist,'G_sample_cutwall_count':int(gl.sum()),'D_sample_cutwall_count':int(dl.sum()),'source_modified':False,'training':0,'GPU':0}
# Keep cropped voxel evidence including background; no full training dataset is made.
idx=(corners-o)@inv;low=np.maximum(0,np.floor(idx.min(0)).astype(int));high=np.minimum(raw.shape,np.ceil(idx.max(0)).astype(int)+1);sl=tuple(slice(l,h) for l,h in zip(low,high))
np.savez_compressed(O/'local_voxel_evidence.npz',raw=raw[sl],C=C[sl],D=D[sl],G=G[sl],R=R[sl],index_start=low,directions=A,origin=o)
fig,axs=plt.subplots(1,3,figsize=(15,5),constrained_layout=True)
for ax,(axis,u,v) in zip(axs,[(0,1,2),(1,0,2),(2,0,1)]):
    xx=np.arange(center[u]-radii[u]-8,center[u]+radii[u]+8,.3);yy=np.arange(center[v]-radii[v]-8,center[v]+radii[v]+8,.3);X,Y=np.meshgrid(xx,yy);w=np.zeros(X.shape+(3,));w[...,axis]=center[axis];w[...,u]=X;w[...,v]=Y;ii=((w-o)@inv).reshape(-1,3).T
    def im(m):return ndimage.map_coordinates(m.astype(np.uint8),ii,order=0,prefilter=False).reshape(X.shape)
    dc=im(D);gg=im(G);rr=im(raw&~C);rgb=np.zeros(X.shape+(3,));rgb[dc>0]=[.85,.85,.85];rgb[gg>0]=[.1,.7,1];rgb[rr>0]=[1,.35,.1]
    ax.imshow(rgb,origin='lower',extent=[xx[0]-.15,xx[-1]+.15,yy[0]-.15,yy[-1]+.15],aspect='equal');ax.set_title(f'LPS {"xyz"[axis]}={center[axis]} mm');ax.set_xlabel('xyz'[u]+' (mm)');ax.set_ylabel('xyz'[v]+' (mm)')
fig.suptitle('A0221 exploratory solid cut: retained bone gray; removed block cyan; excluded foreground orange\nNative voxel geometry; no fill/smoothing; one fixed ellipsoid')
fig.savefig(O/'solid_cut_sections.png',dpi=150);plt.close(fig)
(O/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
