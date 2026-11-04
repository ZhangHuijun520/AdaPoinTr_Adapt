# -*- coding: utf-8 -*-
"""Read-only same-source clear-mesh overlay on the already frozen ROI."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
OUT=BASE/'mug_GT_literature_and_ROI_review_20261102_v1'
MESH=Path('E:/dataset/MUG500plus/raw_v20/clear_stl/d6_development100_v1/batch_001/A0221_clear.stl')
HISTORY=BASE.parents[1]/'d6_experiment_history/snapshots/d6v/datasets/MUG500plusD6Development400_v1/manifest.jsonl'
DT=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dump(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)

def main():
    start=time.monotonic()
    old=[json.loads(s) for s in HISTORY.read_text(encoding='utf-8').splitlines()]
    record=next(r for r in old if r['case_id']=='mug500plus__A0221__ellipsoid_medium')
    expected=record['source_asset_sha256']
    before=MESH.stat()
    dump('clear_mesh_scope.json',{'source_id':'A0221','path':str(MESH),'expected_sha256':expected,
        'expected_bytes':before.st_size,'mtime_ns':before.st_mtime_ns,
        'implementation_sha256':sha(Path(__file__)),
        'coordinate_rule':'fixed RAS to LPS diag(-1,-1,1), inherited previously checked same-source evidence; no fitted transform',
        'planes_LPS_mm':{'x':48,'y':0,'z':65},'max_seconds':180,
        'no_voxelization':True,'no_mesh_repair':True,'no_new_cut':True})
    c=np.array([48.,0.,65.]);r=np.array([16.,20.,22.])
    lo=c-r-5;hi=c+r+5;segments=[[],[],[]];local_triangles=0
    digest=hashlib.sha256()
    with MESH.open('rb') as f:
        head=f.read(84);digest.update(head);count=int.from_bytes(head[80:84],'little')
        assert before.st_size==84+50*count
        for startface in range(0,count,65536):
            assert time.monotonic()-start<180
            raw=f.read(min(65536,count-startface)*50);digest.update(raw)
            v=np.frombuffer(raw,dtype=DT)['v'].astype(float)*[-1,-1,1]
            assert np.isfinite(v).all()
            hit=np.all(v.max(1)>=lo,axis=1)&np.all(v.min(1)<=hi,axis=1)
            v=v[hit];local_triangles+=len(v)
            for a in range(3):
                d=v[:,:,a]-c[a];cross=(d.min(1)<0)&(d.max(1)>0)
                vv=v[cross];dd=d[cross]
                pairs=[];owners=[]
                for j,k in [(0,1),(1,2),(2,0)]:
                    take=np.flatnonzero(dd[:,j]*dd[:,k]<0)
                    if len(take):
                        t=dd[take,j]/(dd[take,j]-dd[take,k])
                        pairs.append(vv[take,j]+t[:,None]*(vv[take,k]-vv[take,j]));owners.append(take)
                if pairs:
                    points=np.concatenate(pairs);owner=np.concatenate(owners)
                    order=np.argsort(owner,kind='stable');owner=owner[order];points=points[order]
                    _,first,n=np.unique(owner,return_index=True,return_counts=True);first=first[n==2]
                    segments[a].append(np.stack([points[first],points[first+1]],axis=1))
    assert digest.hexdigest()==expected
    segments=[np.concatenate(x) if x else np.empty((0,2,3)) for x in segments]
    after=MESH.stat();assert (after.st_size,after.st_mtime_ns)==(before.st_size,before.st_mtime_ns)
    crop=OUT/'review_crop_only.npz'
    with np.load(crop,allow_pickle=False) as n:
        A=n['directions'];o=n['origin'];low=n['index_start'];masks={k:n[k] for k in ['raw','largest6','largest26']}
    inv=np.linalg.inv(A)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    canvas=Image.new('RGB',(1500,1640),'white');draw=ImageDraw.Draw(canvas)
    draw.text((12,10),'MUG500+ A0221: same-source clear STL versus raw / component-derived foreground',fill='black',font=font)
    draw.text((12,36),'Green=clear-STL section; blue=retained mask; orange=excluded raw mask; red=previous ROI.',fill='black',font=font)
    draw.text((12,62),'Same-source guide, not independent anatomical GT. RAS->LPS fixed; no ICP, fill or smoothing.',fill='black',font=font)
    for col,axis in enumerate(range(3)):
        u,v=[i for i in range(3) if i!=axis]
        xx=np.arange(lo[u],hi[u],.4);yy=np.arange(lo[v],hi[v],.4)
        X,Y=np.meshgrid(xx,yy);w=np.zeros(X.shape+(3,));w[...,axis]=c[axis];w[...,u]=X;w[...,v]=Y
        ii=(((w-o)@inv)-low).reshape(-1,3).T
        raw=ndimage.map_coordinates(masks['raw'],ii,order=0,prefilter=False).reshape(X.shape)
        scale=min(470/(xx[-1]-xx[0]+.4),450/(yy[-1]-yy[0]+.4))
        width=int((xx[-1]-xx[0]+.4)*scale);height=int((yy[-1]-yy[0]+.4)*scale)
        sx=width/(xx[-1]-xx[0]+.4);sy=height/(yy[-1]-yy[0]+.4)
        for row,key in enumerate(['raw','largest6','largest26']):
            keep=ndimage.map_coordinates(masks[key],ii,order=0,prefilter=False).reshape(X.shape)
            rgb=np.full(X.shape+(3,),245,np.uint8);rgb[keep]=[55,120,190];rgb[raw&~keep]=[245,130,45]
            panel=Image.fromarray(rgb).resize((width,height),Image.Resampling.NEAREST)
            pd=ImageDraw.Draw(panel)
            for seg in segments[axis]:
                xy=[((point[u]-xx[0]+.2)*sx,(point[v]-yy[0]+.2)*sy) for point in seg]
                pd.line(xy,fill=(0,175,75),width=2)
            cx=(c[u]-xx[0]+.2)*sx;cy=(c[v]-yy[0]+.2)*sy
            pd.ellipse((cx-r[u]*sx,cy-r[v]*sy,cx+r[u]*sx,cy+r[v]*sy),outline=(205,45,55),width=1)
            left=col*500+(500-width)//2;top=150+row*490
            canvas.paste(panel,(left,top))
            draw.text((col*500+12,top-29),f'{key} | LPS {"xyz"[axis]}={c[axis]:.1f} mm',fill='black',font=font)
    canvas.save(OUT/'A0221_fixed_ROI_clear_STL_overlay.png')
    with (OUT/'clear_STL_ROI_sections.npz').open('xb') as f:
        np.savez_compressed(f,**{f'plane_{i}_segments_LPS':x for i,x in enumerate(segments)})
    dump('clear_mesh_results.json',{'source_hash_matches':True,'source_stat_unchanged':True,
        'source_sha256':digest.hexdigest(),'total_triangles':count,'triangles_intersecting_support_AABB':local_triangles,
        'plane_section_segment_counts':[len(x) for x in segments],
        'elapsed_seconds':time.monotonic()-start,
        'limit':'Strict straddling triangle-plane intersections; coplanar/vertex-on-plane degeneracies not counted. Mesh guide is same-source, not independent CT verification.',
        'new_defects':0,'mask_edits':0,'mesh_edits':0})
    print('clear-STL overlay complete',local_triangles,[len(x) for x in segments])

if __name__=='__main__':main()
