# -*- coding: utf-8 -*-
"""Read-only local ROI comparison. Never saves a new training mask or cut."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import hashlib
import itertools
import json
import time
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont
import psutil

BASE=Path(__file__).resolve().parent
OUT=BASE/'mug_GT_literature_and_ROI_review_20261102_v1'
SOURCE=BASE/'mug_solid_defects_v2_20261102'
OLD=BASE/'mug_solid_pilot_20261029_v1/a0221_solid_pilot_20261102_v1'
START=time.monotonic()
PEAK=0

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dump(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False)

def guard():
    global PEAK
    PEAK=max(PEAK,psutil.Process().memory_info().rss)
    if PEAK>8*1024**3 or time.monotonic()-START>900:
        raise RuntimeError('8 GiB monitored RSS / 15 minute bounded review budget')

def main():
    OUT.mkdir(exist_ok=False)
    row=json.loads((SOURCE/'cases/A0221.json').read_text(encoding='utf-8'))
    source=SOURCE/row['solid_path']
    digest=sha(source)
    assert digest==row['solid_sha256']
    protocol=json.loads((OLD/'protocol.json').read_text(encoding='utf-8'))
    center=np.array(protocol['center_LPS_mm']);radii=np.array(protocol['radii_LPS_mm'])
    assert np.array_equal(center,[48,0,65]) and np.array_equal(radii,[16,20,22])
    dump('roi_scope.json',{'input_solid':str(source),'sha256':digest,
        'implementation_sha256':sha(Path(__file__)),'old_ROI_protocol':str(OLD/'protocol.json'),
        'old_ROI_protocol_sha256':sha(OLD/'protocol.json'),
        'source':'A0221','center_LPS_mm':center.tolist(),'radii_mm':radii.tolist(),
        'scope':'largest-6 / largest-26 component counterfactual geometry review only; no production mask admission',
        'support':'physical cutter AABB enlarged by 5mm; not a constant-distance contact band',
        'new_defects':0,'training_masks_written':0,'new_point_clouds':0,'GPU':0,'sealed_payload':0})
    toy=np.zeros((4,4,4),bool);toy[1,1,1]=toy[2,2,2]=True
    assert ndimage.label(toy,ndimage.generate_binary_structure(3,1))[1]==2
    assert ndimage.label(toy,ndimage.generate_binary_structure(3,3))[1]==1
    with np.load(source,allow_pickle=False) as n:
        shape=tuple(n['shape']);A=n['directions'];o=n['origin']
        raw=np.unpackbits(n['C_bits'],bitorder='little',count=int(np.prod(shape))).reshape(shape).astype(bool)
    assert raw.sum()==5534664
    guard()
    inv=np.linalg.inv(A)
    corners=np.array(list(itertools.product(*zip(center-radii-5,center+radii+5))))
    index=(corners-o)@inv
    lo=np.maximum(0,np.floor(index.min(0)).astype(int))
    hi=np.minimum(shape,np.ceil(index.max(0)).astype(int)+1)
    sl=tuple(slice(l,h) for l,h in zip(lo,hi))
    grid=np.indices(tuple(hi-lo)).transpose(1,2,3,0)+lo
    world=grid@A+o
    roi=np.sum(((world-center)/radii)**2,axis=-1)<=1
    rawcrop=raw[sl].copy()
    results={};masks={'raw':raw};crops={'raw':rawcrop}
    for connectivity,rank in [(6,1),(26,3)]:
        labels,num=ndimage.label(raw,ndimage.generate_binary_structure(3,rank))
        sizes=np.bincount(labels.ravel());sizes[0]=0
        keep=labels==int(sizes.argmax());del labels
        crop=keep[sl].copy();removed=rawcrop&~crop
        masks[f'largest{connectivity}']=keep;crops[f'largest{connectivity}']=crop
        results[str(connectivity)]={'component_count':int(num),'main_voxels':int(keep.sum()),
            'raw_voxels':int(raw.sum()),'removed_global':int((raw&~keep).sum()),
            'raw_in_fixed_ellipsoid':int((rawcrop&roi).sum()),
            'retained_in_fixed_ellipsoid':int((crop&roi).sum()),
            'excluded_in_fixed_ellipsoid':int((removed&roi).sum()),
            'excluded_in_saved_support_crop':int(removed.sum()),
            'not_a_segmentation_accuracy':True}
        guard()
    # Exact comparison against the old stored six-connected analysis.
    old=np.load(OLD/'local_voxel_evidence.npz',allow_pickle=False)
    assert np.array_equal(lo,old['index_start'])
    assert np.array_equal(rawcrop,old['raw']) and np.array_equal(crops['largest6'],old['C'])
    assert results['6']['excluded_in_fixed_ellipsoid']==8288
    old.close()
    changes={'C26_minus_C6_in_cut':int((crops['largest26']&~crops['largest6']&roi).sum()),
             'C6_minus_C26_in_cut':int((crops['largest6']&~crops['largest26']&roi).sum()),
             'C26_minus_C6_in_saved_crop':int((crops['largest26']&~crops['largest6']).sum())}
    with (OUT/'review_crop_only.npz').open('xb') as f:
        np.savez_compressed(f,raw=rawcrop,largest6=crops['largest6'],largest26=crops['largest26'],
                            fixed_ROI_membership=roi,index_start=lo,directions=A,origin=o)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    canvas=Image.new('RGB',(1500,1640),'white');draw=ImageDraw.Draw(canvas)
    draw.text((12,10),'MUG500+ A0221 fixed lateral calvarial ROI: connectivity review, not GT certification',fill='black',font=font)
    draw.text((12,36),'Blue=retained foreground; orange=excluded raw foreground; red=previous fixed ellipsoid.',fill='black',font=font)
    draw.text((12,62),'No cavity filling / smoothing / new cut. Display grid 0.4mm does not increase native resolution.',fill='black',font=font)
    for col,axis in enumerate(range(3)):
        u,v=[i for i in range(3) if i!=axis]
        xx=np.arange(center[u]-radii[u]-5,center[u]+radii[u]+5,.4)
        yy=np.arange(center[v]-radii[v]-5,center[v]+radii[v]+5,.4)
        X,Y=np.meshgrid(xx,yy)
        w=np.zeros(X.shape+(3,));w[...,axis]=center[axis];w[...,u]=X;w[...,v]=Y
        ii=((w-o)@inv).reshape(-1,3).T
        rr=ndimage.map_coordinates(raw,ii,order=0,prefilter=False).reshape(X.shape)
        for rownum,key in enumerate(['raw','largest6','largest26']):
            kk=ndimage.map_coordinates(masks[key],ii,order=0,prefilter=False).reshape(X.shape)
            rgb=np.full(X.shape+(3,),245,np.uint8);rgb[kk]=[55,120,190];rgb[rr&~kk]=[245,130,45]
            im=Image.fromarray(rgb)
            scale=min(470/(xx[-1]-xx[0]+.4),450/(yy[-1]-yy[0]+.4))
            width=int((xx[-1]-xx[0]+.4)*scale);height=int((yy[-1]-yy[0]+.4)*scale)
            im=im.resize((width,height),Image.Resampling.NEAREST)
            left=col*500+(500-width)//2;top=150+rownum*490
            canvas.paste(im,(left,top))
            draw.text((col*500+12,top-29),f'{key} | LPS {"xyz"[axis]}={center[axis]:.1f} mm',fill='black',font=font)
            sx=width/(xx[-1]-xx[0]+.4);sy=height/(yy[-1]-yy[0]+.4)
            cx=left+(center[u]-xx[0]+.2)*sx;cy=top+(center[v]-yy[0]+.2)*sy
            draw.ellipse((cx-radii[u]*sx,cy-radii[v]*sy,cx+radii[u]*sx,cy+radii[v]*sy),outline=(205,45,55),width=2)
    canvas.save(OUT/'A0221_fixed_ROI_connectivity_review.png')
    assert sha(source)==digest
    dump('roi_results.json',{'status':'READONLY_REVIEW_COMPLETED_NO_TRAINING_MASK_ADMITTED',
        'source_hash_unchanged':True,'old_6_component_crop_exactly_reproduced':True,
        'center_LPS_mm':center.tolist(),'radii_mm':radii.tolist(),'connectivity_comparison':results,
        'difference_26_vs_6':changes,'elapsed_seconds':time.monotonic()-START,'sampled_RSS_max_bytes':PEAK,
        'limitations':['Connectivity differences are not independently labeled bone/noise errors',
                      'Main-component selection does not remove attached false-positive structures',
                      'No original grayscale CT or expert annotation read in this review',
                      'This crop is a diagnostic artifact, not a new complete skull or training dataset']})
    print(json.dumps({'results':results,'differences':changes},ensure_ascii=True),flush=True)

if __name__=='__main__':main()
