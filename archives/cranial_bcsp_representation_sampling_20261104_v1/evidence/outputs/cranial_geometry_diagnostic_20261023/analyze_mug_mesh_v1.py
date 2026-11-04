"""Three fixed MUG source meshes: read-only topology, sections, stored-cloud QA.

No mesh repair/caps, synthetic cases, new samples, model or server operations.
Exact-coordinate welding changes only in-memory indexing, not geometry.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import csv
import gc
import hashlib
import json
import struct
import sys
import time
from pathlib import Path
import numpy as np
import scipy
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
OUT=BASE/'mug_mesh_v1'
SOURCE=Path('E:/dataset/MUG500plus/raw_v20/clear_stl/d6_development100_v1/batch_001')
POINTS=Path('E:/Codex/2026-06-06/mamba-ccf-c-1-high-resolution/d6_experiment_history/snapshots/d6v/datasets/MUG500plusD6Development400_v1/cases')

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def dump(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False)

def read_stl(path):
    with path.open('rb') as f:
        f.seek(80)
        count=struct.unpack('<I',f.read(4))[0]
    assert path.stat().st_size==84+50*count
    dt=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
    rec=np.fromfile(path,dtype=dt,count=count,offset=84)
    tri=np.array(rec['vertices'],dtype=np.float32)
    assert np.isfinite(tri).all()
    return tri

def pack_edges(a,b):
    return (np.minimum(a,b).astype(np.uint64)<<np.uint64(32))|np.maximum(a,b).astype(np.uint64)

def unpack_edges(keys):
    return np.column_stack((keys>>np.uint64(32),keys&np.uint64(0xffffffff))).astype(np.int32)

def topology(f,areas):
    n=len(f)
    assert n>0
    keys=np.concatenate([pack_edges(f[:,0],f[:,1]),pack_edges(f[:,1],f[:,2]),pack_edges(f[:,2],f[:,0])])
    order=np.argsort(keys)
    sorted_keys=keys[order]
    del keys
    starts=np.r_[0,np.flatnonzero(sorted_keys[1:]!=sorted_keys[:-1])+1]
    counts=np.diff(np.r_[starts,len(sorted_keys)])
    unique=sorted_keys[starts].copy()
    shared=np.flatnonzero(sorted_keys[1:]==sorted_keys[:-1])
    a=(order[shared]%n).astype(np.int32)
    b=(order[shared+1]%n).astype(np.int32)
    graph=coo_matrix((np.ones(len(a),dtype=np.uint8),(a,b)),shape=(n,n)).tocsr()
    nc,labels=connected_components(graph,directed=False)
    del graph,a,b,shared,sorted_keys
    orientation=np.concatenate([np.where(f[:,0]<f[:,1],1,-1),np.where(f[:,1]<f[:,2],1,-1),np.where(f[:,2]<f[:,0],1,-1)]).astype(np.int8)
    sums=np.add.reduceat(orientation[order],starts)
    invalid=(counts!=2)|(sums!=0)
    bad_labels=np.unique(labels[order[starts[invalid]]%n])
    comp_faces=np.bincount(labels,minlength=nc)
    comp_area=np.bincount(labels,weights=areas,minlength=nc)
    biggest=np.argsort(comp_area)[::-1][:10]
    summary={'triangles':n,'unique_edges':len(unique),'boundary_edges':int((counts==1).sum()),
             'nonmanifold_edges':int((counts>2).sum()),
             'two_face_winding_inconsistent_edges':int(((counts==2)&(sums!=0)).sum()),
             'face_edge_connected_components':int(nc),
             'edge_closed_consistently_oriented_components':int(nc-len(bad_labels)),
             'zero_area_faces':int((areas==0).sum()),
             'largest_components':[{'faces':int(comp_faces[i]),'area_mm2':float(comp_area[i]),
                                    'fraction_surface_area':float(comp_area[i]/areas.sum()),
                                    'edge_closed_consistently_oriented':bool(i not in bad_labels)} for i in biggest],
             'solid_validity':'Not certified: no self-intersection, containment or surgical validation'}
    return summary,unique,counts

def boundary_components(v,keys):
    if not len(keys):
        return {'components':0,'simple_closed_cycles':0,'total_length_mm':0.,'details':[]}
    edges=unpack_edges(keys)
    vertices,inv=np.unique(edges,return_inverse=True)
    ij=inv.reshape(-1,2)
    graph=coo_matrix((np.ones(len(ij),dtype=np.uint8),(ij[:,0],ij[:,1])),shape=(len(vertices),len(vertices))).tocsr()
    nc,lab=connected_components(graph,directed=False)
    degree=np.bincount(ij.ravel(),minlength=len(vertices))
    elab=lab[ij[:,0]]
    lengths=np.linalg.norm(v[edges[:,0]].astype(float)-v[edges[:,1]],axis=1)
    totals=np.bincount(elab,weights=lengths,minlength=nc)
    details=[]
    for i in np.argsort(totals)[::-1]:
        deg=degree[lab==i]
        details.append({'edges':int((elab==i).sum()),'vertices':int((lab==i).sum()),
                        'length_mm':float(totals[i]),'simple_closed_cycle':bool((deg==2).all()),
                        'degree_min':int(deg.min()),'degree_max':int(deg.max())})
    return {'components':int(nc),'simple_closed_cycles':sum(x['simple_closed_cycle'] for x in details),
            'total_length_mm':float(lengths.sum()),'details':details}

def profile(tri,geometry):
    center=np.array(geometry['cut_center_mm'])
    frame=np.array(geometry['frame'])
    radii=np.array(geometry['radii_mm'])
    assert np.allclose(frame.T@frame,np.eye(3),atol=1e-12)
    mask=np.zeros(len(tri),dtype=bool)
    area=np.empty(len(tri))
    for start in range(0,len(tri),100000):
        q=tri[start:start+100000].astype(float)
        local=(q.mean(axis=1)-center)@frame
        mask[start:start+len(q)]=np.sum((local/radii)**2,axis=1)<=1
        area[start:start+len(q)]=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)/2
    assert mask.sum()==geometry['removed_triangles']
    assert (~mask).sum()==geometry['remaining_triangles']
    assert np.isclose(area[mask].sum()/area.sum(),geometry['removed_surface_area_fraction'],rtol=1e-10,atol=1e-12)
    return mask,area

def section(loc,f,removed,axis):
    d=loc[:,axis]
    sd=d[f]
    cross=(sd.min(axis=1)<=0)&(sd.max(axis=1)>0)
    selected=np.flatnonzero(cross)
    q=loc[f[selected]]
    dd=sd[selected]
    other=[i for i in range(3) if i!=axis]
    pts=np.full((len(q),3,2),np.nan)
    for k,(a,b) in enumerate([(0,1),(1,2),(2,0)]):
        active=((dd[:,a]<=0)&(dd[:,b]>0))|((dd[:,a]>0)&(dd[:,b]<=0))
        t=dd[active,a]/(dd[active,a]-dd[active,b])
        hit=q[active,a]+t[:,None]*(q[active,b]-q[active,a])
        pts[active,k]=hit[:,other]
    good=~np.isnan(pts[:,:,0])
    assert (good.sum(axis=1)==2).all()
    seg=pts[good].reshape(-1,2,2)
    return seg,removed[selected],other

def edge_plane_hits(loc,keys,axis):
    edges=unpack_edges(keys)
    q=loc[edges]
    d=q[:,:,axis]
    active=((d[:,0]<=0)&(d[:,1]>0))|((d[:,0]>0)&(d[:,1]<=0))
    q,d=q[active],d[active]
    t=d[:,0]/(d[:,0]-d[:,1])
    hit=q[:,0]+t[:,None]*(q[:,1]-q[:,0])
    return hit[:,[a for a in range(3) if a!=axis]]

def normal_axis_hits(seg,axes):
    if 2 not in axes:
        return []
    u=axes.index(next(a for a in axes if a!=2))
    w=axes.index(2)
    d=seg[:,:,u]
    active=((d[:,0]<=0)&(d[:,1]>0))|((d[:,0]>0)&(d[:,1]<=0))
    q=seg[active]
    dd=d[active]
    t=dd[:,0]/(dd[:,0]-dd[:,1])
    hits=np.sort(q[:,0,w]+t*(q[:,1,w]-q[:,0,w]))
    if not len(hits):
        return []
    return hits[np.r_[True,np.diff(hits)>1e-4]].tolist()

def figures(sid,loc,f,removed,newkeys,p,geometry):
    im=Image.new('RGB',(1800,1190),'white')
    dr=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    dr.text((20,12),f'{sid}: exact STL sections in frozen cut frame (U,V,N), units mm',fill='black',font=font)
    dr.text((20,45),'Blue=retained original faces; orange=removed original faces; magenta=new open-edge intersections',fill='black',font=small)
    dr.text((20,70),'Bottom: ROI + existing input points within +/-1 mm slab (black). No wall/cap or new point was generated.',fill='black',font=small)
    axis_intersections=[]
    for col,axis in enumerate([2,1,0]):
        seg,rm,axes=section(loc,f,removed,axis)
        hits=edge_plane_hits(loc,newkeys,axis)
        ray=normal_axis_hits(seg,axes)
        axis_intersections.append({'plane_axis':axis,'normal_axis_intersections_mm':ray,
                                   'positive_normal_intersections_mm':[x for x in ray if x>0],
                                   'source_section_segments':len(seg),'new_open_edge_crossings':len(hits)})
        allpts=seg.reshape(-1,2)
        for row in range(2):
            if row==0:
                lo=allpts.min(axis=0)-4
                hi=allpts.max(axis=0)+4
            else:
                r=np.asarray(geometry['radii_mm'])[axes]
                lo=-r*1.25
                hi=r*1.25
            scale=min(550/(hi[0]-lo[0]),430/(hi[1]-lo[1]))
            left,top=col*600+25,170+row*500
            width,height=(hi-lo)*scale
            def xy(q):
                return left+(q[...,0]-lo[0])*scale,top+(hi[1]-q[...,1])*scale
            dr.rectangle((left,top,left+width,top+height),outline='#777777')
            dr.text((left,top-45),f'{"UVN"[axes[0]]}/{"UVN"[axes[1]]}; {"UVN"[axis]}=0; '+('full' if row==0 else 'defect ROI'),fill='black',font=small)
            for a,flag in zip(seg,rm):
                if np.any(a.min(axis=0)<lo) or np.any(a.max(axis=0)>hi):
                    continue
                x,y=xy(a)
                dr.line((x[0],y[0],x[1],y[1]),fill=('#D55E00' if row==0 else '#EFC5A7') if flag else '#0072B2',width=2)
            for point in hits:
                if (point>=lo).all() and (point<=hi).all():
                    x,y=xy(point)
                    dr.ellipse((x-3,y-3,x+3,y+3),fill='#CC0077')
            if row==1:
                pm=p[np.abs(p[:,axis])<=1][:,axes]
                pm=pm[((pm>=lo)&(pm<=hi)).all(axis=1)]
                for pt in pm:
                    x,y=xy(pt)
                    dr.ellipse((x-2,y-2,x+2,y+2),fill='black')
                dr.text((left,top-22),f'Input points in slab / ROI: {len(pm)}',fill='black',font=small)
            dr.text((left,top+height+6),f'{hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} mm (equal aspect)',fill='black',font=small)
    im.save(OUT/(sid+'_mesh_sections.png'))
    return axis_intersections

def sanity():
    v=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],dtype=np.float32)
    f=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]],dtype=np.int32)
    a=np.full(12,.5)
    s,k,c=topology(f,a)
    assert s['boundary_edges']==0 and s['nonmanifold_edges']==0 and s['face_edge_connected_components']==1
    assert s['two_face_winding_inconsistent_edges']==0
    s,k,c=topology(f[1:],a[1:])
    assert s['boundary_edges']==3
    assert boundary_components(v,k[c==1])['simple_closed_cycles']==1
    f2=np.vstack((f,f+8))
    assert topology(f2,np.r_[a,a])[0]['face_edge_connected_components']==2
    assert topology(np.vstack((f,f[0])),np.r_[a,.5])[0]['nonmanifold_edges']==3
    seg,_,axes=section(v.astype(float)-.5,f,np.zeros(12,dtype=bool),0)
    assert len(seg)==8 and len(normal_axis_hits(seg,axes))==2
    return 7

def main():
    assert not OUT.exists(), 'Refuse overwrite'
    OUT.mkdir()
    started=time.time()
    checks=sanity()
    records=[i['record'] for i in json.loads((BASE/'result_v2/selected_scope.json').read_text())['cases'] if i['dataset']=='MUG500plus']
    assert [r['case_id'].split('__')[1] for r in records]==['A0136','A0137','A0138']
    plans=[]
    for rec in records:
        sid=rec['case_id'].split('__')[1]
        stl=SOURCE/(sid+'_clear.stl')
        npz=POINTS/(rec['case_id']+'.npz')
        assert sha(stl)==rec['source_asset_sha256'] and sha(npz)==rec['derived_case_sha256']
        plans.append({'record':rec,'stl':str(stl),'npz':str(npz),
                      'stl_sha256_before':sha(stl),'npz_sha256_before':sha(npz)})
    dump('scope.json',{'cases':plans,'sanity_checks':checks,'source_data_readonly':True,
                       'case_selection':'Same three previously frozen D6 development ellipsoid_medium cases',
                       'budgets':'One sequential CPU pass over 3 STL and 3 existing NPZ; no extra cases, cut parameters, or sampling',
                       'mesh_semantics':'Exact numeric coordinate indexing only; no epsilon welding, caps, repair or solid inference',
                       'coverage_reference':'Triangle-centroid area quadrature on retained source faces; new open-edge midpoint length quadrature',
                       'tolerances_mm':[1,2]})
    results=[]
    for plan in plans:
        t0=time.time()
        rec=plan['record']
        sid=rec['case_id'].split('__')[1]
        print('READ',sid,flush=True)
        tri=read_stl(Path(plan['stl']))
        removed,areas=profile(tri,rec['geometry'])
        print('PROFILE_MATCH',sid,'faces',len(tri),'removed',int(removed.sum()),flush=True)
        print('INDEX_EXACT_VERTICES',sid,flush=True)
        v,inv=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True)
        f=inv.reshape(-1,3).astype(np.int32)
        del inv,tri
        gc.collect()
        print('TOPOLOGY_FULL',sid,'vertices',len(v),flush=True)
        full,fullkeys,fullcounts=topology(f,areas)
        print('TOPOLOGY_RETAINED',sid,flush=True)
        partial,pkeys,pcounts=topology(f[~removed],areas[~removed])
        openkeys=pkeys[pcounts==1]
        pos=np.searchsorted(fullkeys,openkeys)
        assert np.array_equal(fullkeys[pos],openkeys)
        original_counts=fullcounts[pos]
        inherited=openkeys[original_counts==1]
        newkeys=openkeys[original_counts==2]
        irregular=openkeys[original_counts>2]
        assert len(openkeys)==len(inherited)+len(newkeys)+len(irregular)
        newbound=boundary_components(v,newkeys)
        fullbound=boundary_components(v,fullkeys[fullcounts==1])
        with np.load(plan['npz'],allow_pickle=False) as z:
            scale=float(z['scale'])
            center=np.asarray(z['centroid'],dtype=float)
            p=np.asarray(z['partial'],dtype=float)*scale+center
            g=np.asarray(z['implant'],dtype=float)*scale+center
            stored_rim=np.asarray(z['reference_rim_mask'],dtype=bool)
        assert p.shape==(8192,3) and g.shape==(8192,3)
        sparseband=cKDTree(g).query(p,workers=1)[0]<=2
        assert np.array_equal(sparseband,stored_rim)
        tree=cKDTree(p)
        cover=np.zeros(2)
        centroid_dist_sum=0.
        print('COVERAGE_AND_SECTIONS',sid,flush=True)
        for start in range(0,len(f),100000):
            end=min(start+100000,len(f))
            keep=~removed[start:end]
            q=v[f[start:end][keep]].astype(float).mean(axis=1)
            w=areas[start:end][keep]
            dd=tree.query(q,workers=1)[0]
            cover+=np.array([w[dd<=e].sum() for e in [1,2]])
            centroid_dist_sum+=float((w*dd).sum())
        edges=unpack_edges(newkeys)
        mid=(v[edges[:,0]].astype(float)+v[edges[:,1]])/2
        length=np.linalg.norm(v[edges[:,0]].astype(float)-v[edges[:,1]],axis=1)
        if len(mid):
            edist=tree.query(mid,workers=1)[0]
            edgecover={str(e):float(length[edist<=e].sum()/length.sum()) for e in [1,2]}
            band=cKDTree(mid).query(p,workers=1)[0]<=2
            edist_metrics={'mean_length_weighted_mm':float((length*edist).sum()/length.sum()),
                           'p95_unweighted_midpoint_mm':float(np.percentile(edist,95)),
                           'max_midpoint_mm':float(edist.max())}
        else:
            edgecover=None
            band=np.zeros(len(p),dtype=bool)
            edist_metrics=None
        loc=(v.astype(float)-np.array(rec['geometry']['cut_center_mm']))@np.array(rec['geometry']['frame'])
        ploc=(p-np.array(rec['geometry']['cut_center_mm']))@np.array(rec['geometry']['frame'])
        slices=figures(sid,loc,f,removed,newkeys,ploc,rec['geometry'])
        stl_after=sha(Path(plan['stl']))
        npz_after=sha(Path(plan['npz']))
        assert stl_after==plan['stl_sha256_before'] and npz_after==plan['npz_sha256_before']
        res={'source_id':sid,'case_id':rec['case_id'],'source_stl_path':plan['stl'],'existing_npz_path':plan['npz'],
             'source_stl_sha256_before':plan['stl_sha256_before'],'source_stl_sha256_after':stl_after,
             'npz_sha256_before':plan['npz_sha256_before'],'npz_sha256_after':npz_after,
             'geometry_matches_frozen_face_counts_and_area_fraction':True,
             'source_triangles':len(f),'retained_triangles':int((~removed).sum()),'removed_triangles':int(removed.sum()),
             'exact_coordinate_vertices':len(v),'source_surface_area_mm2':float(areas.sum()),
             'retained_source_surface_area_mm2':float(areas[~removed].sum()),
             'source_topology':full,'retained_topology':partial,'source_boundary_components':fullbound,
             'retained_boundary_inherited_from_source_edges':len(inherited),
             'retained_boundary_created_by_deletion_edges':len(newkeys),
             'retained_boundary_from_source_nonmanifold_edges':len(irregular),
             'new_open_edge_components':newbound,
             'new_cutwall_triangles_created':0,
             'cutwall_area_coverage':'UNDEFINED: no new cut-wall surface exists in this face-deletion representation',
             'retained_surface_centroid_area_coverage_at_1mm':float(cover[0]/areas[~removed].sum()),
             'retained_surface_centroid_area_coverage_at_2mm':float(cover[1]/areas[~removed].sum()),
             'retained_centroid_distance_area_weighted_mean_mm':centroid_dist_sum/areas[~removed].sum(),
             'new_open_edge_midpoint_length_coverage':edgecover,'new_open_edge_nearest_input_distances':edist_metrics,
             'input_points_within_2mm_new_edge_midpoints':int(band.sum()),
             'input_points_within_2mm_sparse_implant':int(sparseband.sum()),
             'edge_band_sparse_band_overlap':int((band&sparseband).sum()),
             'edge_band_only':int((band&~sparseband).sum()),'sparse_band_only':int((sparseband&~band).sum()),
             'sections':slices,'internal_cavity_semantics':'Not automatically labelled; closed components and multi-crossings are not anatomical proof',
             'new_points_generated':0,'mesh_repair':False,'elapsed_seconds':time.time()-t0}
        dump(sid+'_metrics.json',res)
        results.append(res)
        print('DONE',sid,'source_open',full['boundary_edges'],'new_open',len(newkeys),'new_cycles',newbound['simple_closed_cycles'],flush=True)
        del v,f,loc,ploc,removed,areas,fullkeys,fullcounts,pkeys,pcounts,edges,mid,length,p,g,tree
        gc.collect()
    dump('results.json',{'status':'COMPLETED_THREE_FIXED_MUG_MESH_CASES','cases':results,'sanity_checks':checks,
                          'elapsed_seconds':time.time()-started,'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,
                          'server_operations':0,'model_imports':0,'gpu_operations':0,'source_writes':0,'source_cases_added':0,
                          'limits':['No global anatomical inner/outer semantic labels or histological cavity annotations',
                                    'No self-intersection or solid validity certificate',
                                    'Coverage references are centroid/midpoint quadrature, not exact continuous distances',
                                    'No cut-wall surface was constructed, so its coverage cannot be computed or called zero',
                                    'Same three development sources, not a population study']})
    with (OUT/'summary.csv').open('x',encoding='utf-8',newline='') as out:
        fields=['source','source_faces','source_open_edges','source_components','retained_open_edges','new_open_edges','new_boundary_cycles','global_coverage_2mm','edge_length_coverage_2mm','edge_band_points','sparse_band_points']
        w=csv.DictWriter(out,fieldnames=fields)
        w.writeheader()
        for r in results:
            values=[r['source_id'],r['source_triangles'],r['source_topology']['boundary_edges'],
                    r['source_topology']['face_edge_connected_components'],r['retained_topology']['boundary_edges'],
                    r['retained_boundary_created_by_deletion_edges'],r['new_open_edge_components']['simple_closed_cycles'],
                    r['retained_surface_centroid_area_coverage_at_2mm'],
                    None if r['new_open_edge_midpoint_length_coverage'] is None else r['new_open_edge_midpoint_length_coverage']['2'],
                    r['input_points_within_2mm_new_edge_midpoints'],r['input_points_within_2mm_sparse_implant']]
            w.writerow(dict(zip(fields,values)))
    with (OUT/'files.sha256').open('x') as out:
        for p in sorted(OUT.iterdir()):
            if p.is_file() and p.name!='files.sha256':
                out.write(sha(p)+'  '+p.name+'\n')
    print('COMPLETED_THREE_FIXED_MUG_MESH_CASES',flush=True)

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        if OUT.exists() and not (OUT/'failure.json').exists():
            dump('failure.json',{'status':'STOPPED','type':type(e).__name__,'error':str(e)})
        raise
