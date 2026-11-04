# -*- coding: utf-8 -*-
"""Fixed-ROI evidence review only; no automatic anatomical label or C* approval."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2')
import csv,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
OLD=BASE/'mug_GT_literature_and_ROI_review_20261102_v1'
PILOT=BASE/'mug_solid_pilot_20261029_v1/a0221_solid_pilot_20261102_v1'
OUT=BASE/'a0221_foreground_adjudication_20261102_v1'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def dump(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False)

def ray_intervals(masks,A,o,start,xrange,y,z):
    """Exact grid-cell traversal in world x, not resampled thickness measurement."""
    inv=np.linalg.inv(A)
    velocity=inv[0]
    offset=(np.array([0.,y,z])-o)@inv-start
    edges=[float(xrange[0]),float(xrange[1])]
    for a in range(3):
        if abs(velocity[a])<1e-14:continue
        ends=offset[a]+velocity[a]*np.array(xrange)
        lo,hi=float(ends.min()),float(ends.max())
        planes=np.arange(np.ceil(lo-.5),np.floor(hi-.5)+1)+.5
        events=(planes-offset[a])/velocity[a]
        edges.extend(events[(events>xrange[0])&(events<xrange[1])].tolist())
    edges=np.unique(edges)
    mids=(edges[:-1]+edges[1:])/2
    q=np.floor(offset+mids[:,None]*velocity+.5).astype(int)
    shape=np.array(next(iter(masks.values())).shape)
    if not np.all((q>=0)&(q<shape)):raise ValueError('fixed ray leaves saved support crop')
    result={}
    for name,m in masks.items():
        value=m[tuple(q.T)]
        runs=[];current=None
        for i,filled in enumerate(value):
            if filled and current is None:current=float(edges[i])
            if current is not None and (not filled or i==len(value)-1):
                stop=float(edges[i] if not filled else edges[i+1])
                if stop-current>1e-10:runs.append([current,stop])
                current=None
        result[name]=runs
    return result

def main():
    start_time=time.monotonic()
    OUT.mkdir(exist_ok=False)
    input_path=OLD/'review_crop_only.npz'
    inputs=[input_path,OLD/'roi_results.json',OLD/'clear_mesh_results.json',
            OLD/'clear_STL_ROI_sections.npz',PILOT/'local_voxel_evidence.npz',PILOT/'results.json',Path(__file__)]
    hashes={str(p):sha(p) for p in inputs}
    prior=json.loads((OLD/'artifact_manifest_v1.json').read_text(encoding='utf-8'))
    for p in inputs[:4]:
        assert sha(p)==prior['files'][str(p.relative_to(OLD))]['sha256']
    dump('scope.json',{'date':'2026-11-02','source_id':'A0221','inputs_sha256':hashes,
        'center_LPS_mm':[48,0,65],'radii_LPS_mm':[16,20,22],
        'user_has_extra_gray_CT_or_independent_labels':False,
        'support':'existing physical support AABB, not a 5mm Euclidean band',
        'fixed_profiles':{'world_x_range_mm':[27,69],'world_y_mm':[-10,0,10],'world_z_mm':[55,65,75]},
        'purpose':'classify agreement/disagreement evidence and proximity to existing candidate J; decide whether C* can be approved',
        'no_new_ROI_no_locator_no_parameter_scan':True,'training_authorized':False,
        'no_C_star_or_formal_DG_unless_anatomical_evidence_sufficient':True})
    # Small exact-traversal check with known physical cell boundaries.
    toy=np.zeros((4,4,4),bool);toy[1:3,1,1]=True
    result=ray_intervals({'toy':toy},np.eye(3),np.zeros(3),np.zeros(3),[-.5,3.5],1,1)
    assert np.allclose(result['toy'],[[.5,2.5]])
    with np.load(input_path,allow_pickle=False) as n:
        raw=n['raw'];m6=n['largest6'];m26=n['largest26'];R=n['fixed_ROI_membership']
        A=n['directions'];o=n['origin'];index_start=n['index_start']
    assert not np.any(m6&~m26)
    with np.load(PILOT/'local_voxel_evidence.npz',allow_pickle=False) as n:
        assert np.array_equal(m6,n['C']) and np.array_equal(raw,n['raw'])
        assert np.array_equal(R,n['R'])
        D=n['D'];G=n['G']
    assert np.array_equal(D|G,m6) and not np.any(D&G)
    groups={'candidate_core_C6':m6,'connectivity_disputed_C26_minus_C6':m26&~m6,
            'excluded_by_both_raw_minus_C26':raw&~m26}
    assert np.array_equal(np.logical_or.reduce(list(groups.values())),raw)
    # J is the already saved pilot's candidate interface, not a new approved cut.
    centers=[]
    for a in range(3):
        for sign in [-1,1]:
            ds=[slice(None)]*3;gs=ds.copy()
            ds[a]=slice(None,-1) if sign==1 else slice(1,None)
            gs[a]=slice(1,None) if sign==1 else slice(None,-1)
            q=np.argwhere(D[tuple(ds)]&G[tuple(gs)]).astype(float)
            if sign<0:q[:,a]+=1
            q+=index_start;q[:,a]+=.5*sign
            centers.append(q@A+o)
    J=np.concatenate(centers)
    assert len(J)==json.loads((PILOT/'results.json').read_text())['G_cutwall_faces']==6838
    tree=cKDTree(J)
    inventory=[]
    for name,mask in groups.items():
        q=np.argwhere(mask);points=(q+index_start)@A+o
        distance=tree.query(points,workers=2)[0]
        inside=R[tuple(q.T)]
        row={'structure_group':name,'support_crop_voxels':int(mask.sum()),
            'inside_fixed_cut_voxels':int(inside.sum()),
            'inside_cut_within_1mm_candidate_J_centers':int(np.count_nonzero(inside&(distance<=1))),
            'inside_cut_within_2mm_candidate_J_centers':int(np.count_nonzero(inside&(distance<=2))),
            'outside_cut_within_2mm_candidate_J_centers':int(np.count_nonzero((~inside)&(distance<=2))),
            'minimum_voxel_center_to_candidate_J_face_center_mm':float(distance.min())}
        inventory.append(row)
    assert [r['inside_fixed_cut_voxels'] for r in inventory]==[70929,5636,2652]
    profiles=[]
    for y in [-10,0,10]:
        for z in [55,65,75]:
            intervals=ray_intervals({'raw':raw,'C6':m6,'C26':m26},A,o,index_start,[27,69],y,z)
            profiles.append({'y_LPS_mm':y,'z_LPS_mm':z,'x_LPS_range_mm':[27,69],
                'intervals':intervals,'C6_number_of_separated_runs':len(intervals['C6']),
                'chord_intervals_not_anatomical_thickness':True})
    labels=np.zeros(raw.shape,np.uint8)
    for code,mask in enumerate(groups.values(),1):labels[mask]=code
    with (OUT/'structure_review_labels_crop.npz').open('xb') as f:
        np.savez_compressed(f,review_class=labels,fixed_ROI=R,index_start=index_start,directions=A,origin=o)
    dump('structure_inventory.json',{'groups':inventory,
        'labels':{'0':'background','1':'C6 review draft, not all confirmed bone',
                  '2':'connectivity disputed, not automatically restored or removed',
                  '3':'excluded by both candidates, not independently proven noise'},
        'candidate_J_face_centers':len(J),
        'distance_limit':'voxel-center to discrete candidate J face centers; not exact continuous distance or clinical tolerance'})
    with (OUT/'structure_inventory.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(inventory[0]));w.writeheader();w.writerows(inventory)
    dump('fixed_profile_intervals.json',{'method':'exact grid-cell traversal along existing nine fixed x-directed lines',
        'profiles':profiles,'not_anatomical_thickness_measurement':True})
    # A compact fixed-profile audit figure, no image-based anatomical labels.
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    image=Image.new('RGB',(1450,1030),'white');draw=ImageDraw.Draw(image)
    draw.text((12,10),'A0221 fixed x-directed profiles: foreground intervals in native voxel cells',fill='black',font=font)
    draw.text((12,37),'Blue=C6; purple=C26; black=raw. Separated runs are not separate anatomical bone plates.',fill='black',font=font)
    colors={'raw':(45,45,45),'C6':(45,110,195),'C26':(145,75,180)}
    x0,x1=220,1400
    def px(x):return x0+(x-27)/(69-27)*(x1-x0)
    for i,p in enumerate(profiles):
        yy=100+i*93
        draw.text((12,yy),f"y={p['y_LPS_mm']}, z={p['z_LPS_mm']} mm",fill='black',font=font)
        for j,key in enumerate(['raw','C6','C26']):
            y=yy+j*22
            draw.text((165,y-7),key,fill=colors[key],font=font)
            draw.line((x0,y,x1,y),fill=(225,225,225),width=1)
            for left,right in p['intervals'][key]:
                draw.rectangle((px(left),y-4,px(right),y+4),fill=colors[key])
    for x in [27,35,45,55,65,69]:
        draw.text((px(x)-10,970),str(x),fill='black',font=font)
    draw.text((600,1000),'LPS x (mm); fixed lateral support range only',fill='black',font=font)
    image.save(OUT/'fixed_profile_review.png')
    for path,h in hashes.items():assert sha(path)==h
    unresolved_near=sum(r['inside_cut_within_2mm_candidate_J_centers']+
                        r['outside_cut_within_2mm_candidate_J_centers'] for r in inventory[1:])
    dump('review_computation.json',{'status':'READONLY_ADJUDICATION_EVIDENCE_COMPLETED',
        'all_input_hashes_unchanged':True,'candidate_J_matches_prior_pilot':True,
        'unresolved_groups_within_2mm_candidate_J_centers':unresolved_near,
        'C6_multiple_run_profile_count':sum(p['C6_number_of_separated_runs']>1 for p in profiles),
        'elapsed_seconds':time.monotonic()-start_time,'new_formal_entities':0,'training_calls':0,
        'tests':['known cuboid physical ray intervals','C6 subset C26','three-class raw foreground partition',
                 'prior raw/C6/R crop identity','prior D/G partition','prior J face count','group volume counts','input hashes unchanged']})
    print(json.dumps({'inventory':inventory,'unresolved_near_J':unresolved_near,
                      'C6_multi_run_profiles':sum(p['C6_number_of_separated_runs']>1 for p in profiles)},ensure_ascii=True))

if __name__=='__main__':main()
