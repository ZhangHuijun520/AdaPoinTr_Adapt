"""Read-only fixed three development sources; no masks modified or defects made."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLBACKEND='Agg')
import sys,json,time,hashlib,zipfile,gc,itertools
from pathlib import Path
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import psutil
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N.parent))
from source_admission_v1 import decode_nrrd
os.environ['MPLCONFIGDIR']=str(N/'mplconfig_geometry')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
DT=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
T=np.diag([-1.,-1.,1.])
START=time.monotonic()
def hashkeys(bits):
    b=bits.astype(np.uint64)
    return b[:,0]*np.uint64(11400714785074694791)^b[:,1]*np.uint64(14029467366897019727)^b[:,2]*np.uint64(1609587929392839161)
def guard():
    assert time.monotonic()-START<1200,'20 minute bound'
    assert psutil.Process().memory_info().rss<8*1024**3,'8 GiB RSS bound'
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,indent=2,allow_nan=False)
def stream_mesh(f,size,planes,query=None):
    head=f.read(84);count=int.from_bytes(head[80:84],'little');assert size==84+50*count
    h=hashlib.sha256(head);lo=np.full(3,np.inf);hi=-lo
    ids=np.unique(np.linspace(0,count-1,min(count,16384),dtype=int));samples=[];segs=[[] for _ in planes]
    found=np.zeros(0 if query is None else len(query),bool)
    if query is not None:
        qb=np.ascontiguousarray(query,dtype='<f4').view('<u4');qk=hashkeys(qb);qorder=np.argsort(qk);sortedq=qk[qorder]
    for start in range(0,count,65536):
        guard();raw=f.read(min(65536,count-start)*50);assert len(raw)==min(65536,count-start)*50;h.update(raw)
        vv=np.frombuffer(raw,dtype=DT)['v'];assert np.isfinite(vv).all()
        lo=np.minimum(lo,vv.min((0,1)));hi=np.maximum(hi,vv.max((0,1)))
        take=ids[(ids>=start)&(ids<start+len(vv))]-start
        if len(take):samples.append(vv[take].mean(1).astype(float)@T)
        if query is not None and not found.all():
            # Exact float32 coordinate tuples, no tolerance or registration.
            vb=np.ascontiguousarray(vv.reshape(-1,3)).view('<u4');vk=hashkeys(vb);pos=np.searchsorted(sortedq,vk);safe=np.minimum(pos,len(sortedq)-1)
            candidates=np.flatnonzero((pos<len(sortedq))&(vk==sortedq[safe]))
            for i in candidates:
                j=qorder[pos[i]]
                if np.array_equal(vb[i],qb[j]):found[j]=True
        v=vv.astype(float)@T
        for j,(axis,value) in enumerate(planes):
            d=v[:,:,axis]-value;cross=(d.min(1)<0)&(d.max(1)>0)
            tri=v[cross];dd=d[cross]
            if not len(tri):continue
            pairs=[];owners=[]
            for a,b in [(0,1),(1,2),(2,0)]:
                ok=(dd[:,a]*dd[:,b]<0);ix=np.flatnonzero(ok)
                if len(ix):
                    t=dd[ix,a]/(dd[ix,a]-dd[ix,b]);pairs.append(tri[ix,a]+t[:,None]*(tri[ix,b]-tri[ix,a]));owners.append(ix)
            if pairs:
                pts=np.concatenate(pairs);own=np.concatenate(owners);order=np.argsort(own,kind='stable');pts=pts[order];own=own[order]
                unique,first,counts=np.unique(own,return_index=True,return_counts=True);first=first[counts==2]
                if len(first):segs[j].append(np.stack([pts[first],pts[first+1]],axis=1))
    return {'header':head[:80].decode('ascii',errors='replace').rstrip('\0 '),'sha256':h.hexdigest(),'triangles':count,'bounds_RAS':[lo.tolist(),hi.tolist()],
            'exact_clear_query_matches':int(found.sum()),'clear_query_count':len(found)},np.concatenate(samples),[np.concatenate(s) if s else np.empty((0,2,3)) for s in segs]
def stats(a):
    return {'n':len(a),'median':float(np.median(a)),'p95':float(np.percentile(a,95)),'max':float(np.max(a))}
def main():
    out=N/'geometry_results_v2';out.mkdir(exist_ok=False)
    sources=json.loads((N/'results.json').read_text());rows=[]
    for source in sources:
        sid=source['id'];print('BEGIN',sid,flush=True);path=Path(source['archive']);before=path.stat()
        with zipfile.ZipFile(path) as z:
            blob=z.read(source['member']);assert hashlib.sha256(blob).hexdigest()==source['sha256']
            arr,A,o,fields=decode_nrrd(blob);assert set(np.unique(arr))=={0,1};mask=arr.astype(bool);del blob,arr
            inv=np.linalg.inv(A);step=np.linalg.norm(A,axis=1);assert np.allclose(A@A.T,np.diag(step**2),atol=1e-5)
            # Per-axis foreground range without allocating all foreground coordinates.
            ranges=[];faces=[]
            for k in range(3):
                counts=mask.sum(axis=tuple(i for i in range(3) if i!=k));ix=np.flatnonzero(counts)
                ranges.append([int(ix[0]),int(ix[-1])]);faces.append({'axis':k,'low':int(counts[0]),'high':int(counts[-1]),'first_last_nonzero':ranges[-1]})
            corners=np.array(list(itertools.product(*ranges)))@A+o;lo=corners.min(0);hi=corners.max(0)
            mid=(lo+hi)/2
            planes=[(0,mid[0]),(1,mid[1])]+[(2,float(lo[2]+f*(hi[2]-lo[2]))) for f in [.45,.65,.8,.9]]
            clear_name=source['member'].replace('.nrrd','_clear.stl');info=z.getinfo(clear_name)
            # Stream clear for identity/bounds and select exact vertices for original coordinate inheritance.
            with z.open(clear_name) as f:
                head=f.read(84);n=int.from_bytes(head[80:84],'little');assert info.file_size==84+50*n
                ids=np.unique(np.linspace(0,n*3-1,64,dtype=int));query=[];digest=hashlib.sha256(head);clo=np.full(3,np.inf);chi=-clo
                for start in range(0,n,65536):
                    raw=f.read(min(65536,n-start)*50);digest.update(raw);v=np.frombuffer(raw,dtype=DT)['v'];clo=np.minimum(clo,v.min((0,1)));chi=np.maximum(chi,v.max((0,1)))
                    ii=ids[(ids>=start*3)&(ids<(start+len(v))*3)]-start*3
                    if len(ii):query.extend(v.reshape(-1,3)[ii]);guard()
            original=source['member'].replace('.nrrd','.stl');info=z.getinfo(original)
            with z.open(original) as f:mesh,samples,segs=stream_mesh(f,info.file_size,planes,np.array(query))
            explicit_ras='SPACE=RAS' in mesh['header']
            # Boundary voxel-center reference, not exact continuous surface distance.
            boundary=mask & ~ndimage.binary_erosion(mask,structure=ndimage.generate_binary_structure(3,1),border_value=0)
            bi=np.argwhere(boundary);world=bi@A+o;tree=cKDTree(world);dist=tree.query(samples,k=1,workers=2)[0]
            idx=(samples-o)@inv;inside=((idx>=-.5)&(idx<=np.array(mask.shape)-.5)).all(1)
            halo=.5*float(np.linalg.norm(step))
            near=dist<=halo+1e-4
            identity_dist=tree.query(samples@T,k=1,workers=2)[0] if not explicit_ras else None
            # Cavity geometry: no anatomical segmentation inferred from labels alone.
            fig,axes=plt.subplots(2,3,figsize=(15,10),constrained_layout=True)
            section_rows=[]
            for j,((axis,value),ax) in enumerate(zip(planes,axes.flat)):
                u,v=[k for k in range(3) if k!=axis]
                xx=np.arange(lo[u]-3,hi[u]+3,.4);yy=np.arange(lo[v]-3,hi[v]+3,.4);X,Y=np.meshgrid(xx,yy)
                p=np.empty(X.shape+(3,));p[...,axis]=value;p[...,u]=X;p[...,v]=Y;ii=(p-o)@inv
                image=ndimage.map_coordinates(mask.astype(np.uint8),ii.reshape(-1,3).T,order=0,mode='constant',cval=0,prefilter=False).reshape(X.shape)
                ax.imshow(image,origin='lower',extent=[xx[0]-.2,xx[-1]+.2,yy[0]-.2,yy[-1]+.2],cmap='gray',vmin=0,vmax=1,interpolation='nearest',aspect='equal')
                if explicit_ras and len(segs[j]):ax.add_collection(LineCollection(segs[j][:,:,[u,v]],colors='#ff5353',linewidths=.4,alpha=.75))
                ax.set_title(f'{sid}: LPS {"xyz"[axis]}={value:.1f} mm');ax.set_xlabel(f'{"xyz"[u]} (mm)');ax.set_ylabel(f'{"xyz"[v]} (mm)')
                section_rows.append({'axis_LPS':axis,'coordinate_mm':value,'mesh_intersection_segments':len(segs[j]),'raster_resolution_mm':.4})
            caption='original STL intersections (red), declared RAS to LPS' if explicit_ras else 'STL frame undeclared; mask only; candidate transforms evaluated separately'
            fig.suptitle(f'{sid}: native binary bone (white); {caption}\nNo fitting, thresholding, filling or defect generation',fontsize=12)
            fig.savefig(out/(sid+'_sections.png'),dpi=150);plt.close(fig)
            # Local superior midsagittal trace for inner/outer shell separation inspection.
            row={'source_id':sid,'nrrd_sha256':source['sha256'],'shape':list(mask.shape),'spacing_mm':step.tolist(),'directions_rows_LPS':A.tolist(),'origin_LPS':o.tolist(),
                 'foreground_voxels':int(mask.sum()),'foreground_volume_mm3':float(mask.sum()*abs(np.linalg.det(A))),'bone_index_ranges':ranges,'image_boundary_contacts':faces,
                 'foreground_world_AABB_LPS':[lo.tolist(),hi.tolist()],'original_STL':mesh,'clear_STL':{'sha256':digest.hexdigest(),'bounds_RAS':[clo.tolist(),chi.tolist()]},
                 'STL_centroid_sample_count':len(samples),'sample_inside_NRRD_half_voxel_FOV_fraction':float(inside.mean()),'nearest_boundary_voxel_center_mm':stats(dist),
                 'half_voxel_diagonal_mm':halo,'sample_within_half_diagonal_fraction':float(near.mean()),'sample_within_1mm_fraction':float((dist<=1).mean()),
                 'coordinate_transform_RAS_to_LPS':T.tolist(),'sections':section_rows,'anatomical_inner_outer_labels_created':False,'defects_generated':0}
            row['original_STL_explicit_RAS']=explicit_ras
            if identity_dist is not None:row['undeclared_frame_candidates']={'RAS_to_LPS_boundary_distance_mm':stats(dist),'identity_LPS_boundary_distance_mm':stats(identity_dist),'no_coordinate_convention_assumed_from_best_fit':True}
            write(out/(sid+'.json'),row);rows.append(row)
            print('DONE',sid,'distance',row['nearest_boundary_voxel_center_mm'],'faces',faces,flush=True)
            del mask,boundary,bi,world,tree,samples,segs;gc.collect();guard()
        after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    write(out/'results.json',{'cases':rows,'seconds':time.monotonic()-START,'server_calls':0,'GPU_calls':0,'mask_modifications':0,'defects_generated':0})
if __name__=='__main__':main()
