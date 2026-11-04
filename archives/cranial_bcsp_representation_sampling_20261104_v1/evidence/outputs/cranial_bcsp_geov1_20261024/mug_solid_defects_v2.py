# -*- coding: utf-8 -*-
"""Fixed development100, one inherited cutter per source, raw-mask solid cuts.

Produces research candidates, never anatomical certification or training admission.
No thresholding, mesh repair, largest-component filtering, cutter search, or GPU.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
import csv
import gc
import gzip
import hashlib
import importlib.util
import io
import json
import re
import sys
import time
import traceback
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
import numpy as np
from scipy import ndimage
import psutil

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
OUT=BASE/'mug_solid_defects_v2_20261102'
DATA=Path('E:/dataset/MUG500plus')
LOCK=DATA/'data_locks/mug500plus_d6_development_generation_fourfold_protocol_lock_v1'
HISTORY=ROOT/'d6_experiment_history/snapshots/d6v/datasets/MUG500plusD6Development400_v1/manifest.jsonl'
GEOMETRY=BASE/'skullfix_batch_geometry_qc_v1.py'
START=time.monotonic()
PEAK=0
CASE_START=START
T=np.diag([-1.,-1.,1.])

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dump(p,obj):
    with Path(p).open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)

def load_module(name,p):
    s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

geo=load_module('fixed_exact_geometry',GEOMETRY)
geo.TIMEOUT=3600
geo.START=START

class SourceRejected(Exception):
    pass

def need(ok,reason):
    if not ok:raise SourceRejected(reason)

def guard():
    global PEAK
    rss=psutil.Process().memory_info().rss;PEAK=max(PEAK,rss)
    if rss>8*1024**3 or time.monotonic()-START>3600 or time.monotonic()-CASE_START>180:
        raise RuntimeError('monitored 8 GiB / 60 min / 180 sec case budget exceeded')

def decode(blob):
    match=re.search(br'\r?\n\r?\n',blob[:8192])
    need(match is not None,'NRRD_HEADER_MALFORMED')
    lines=blob[:match.start()].decode('ascii').splitlines()
    need(lines[0].startswith('NRRD000'),'NRRD_MAGIC')
    f={k:v.strip() for k,v in (line.split(':',1) for line in lines[1:]
                               if line and not line.startswith('#') and ':' in line)}
    need(f.get('dimension')=='3' and f.get('encoding')=='gzip','NRRD_UNSUPPORTED_DIMENSION_ENCODING')
    need(not {'data file','byte skip','line skip'}&f.keys(),'NRRD_DETACHED_OR_SKIP_NOT_ALLOWED')
    types={'short':'i2','int16':'i2','unsigned short':'u2','ushort':'u2',
           'unsigned char':'u1','uchar':'u1','uint8':'u1','int':'i4','int32':'i4','float':'f4'}
    need(f.get('type') in types,'NRRD_UNSUPPORTED_SCALAR_TYPE')
    shape=tuple(map(int,f['sizes'].split()))
    need(len(shape)==3 and min(shape)>=3 and np.prod(shape)<=160_000_000,'NRRD_SHAPE_OR_VOXEL_BUDGET')
    dt=np.dtype(types[f['type']]).newbyteorder('>' if f.get('endian','little')=='big' else '<')
    A=np.array([[float(v) for v in row.split(',')] for row in re.findall(r'\(([^)]+)\)',f['space directions'])])
    o=np.array([float(v) for v in f['space origin'].strip('()').split(',')])
    need(A.shape==(3,3) and o.shape==(3,) and np.isfinite(A).all() and np.isfinite(o).all()
         and abs(np.linalg.det(A))>1e-9,'NRRD_INVALID_AFFINE')
    need(f.get('space') in ['left-posterior-superior','right-anterior-superior'],'NRRD_UNKNOWN_SPACE')
    expected=int(np.prod(shape))*dt.itemsize
    with gzip.GzipFile(fileobj=io.BytesIO(blob[match.end():])) as z:raw=z.read(expected+1)
    need(len(raw)==expected,'NRRD_DECODED_SIZE_MISMATCH')
    arr=np.frombuffer(raw,dtype=dt).reshape(shape,order='F')
    minimum,maximum=float(arr.min()),float(arr.max())
    stats={'shape':list(shape),'minimum':minimum,'maximum':maximum,'dtype':str(dt),'header':f}
    if not np.isfinite(minimum) or not np.isfinite(maximum):
        raise SourceRejected('NRRD_NONFINITE_SCALAR')
    # Check all values; min/max alone is insufficient for integer masks such as 0/255.
    need(minimum==0 and maximum in (1,255),'SCALAR_VOLUME_NOT_BINARY_NO_THRESHOLD_APPLIED')
    mask=np.asarray(arr>0,order='C')
    need(int(np.count_nonzero(arr))==int(np.count_nonzero(arr==maximum)),
         'SCALAR_VOLUME_HAS_INTERMEDIATE_LABELS_NO_THRESHOLD_APPLIED')
    if f['space']=='right-anterior-superior':A=A@T;o=o@T
    return mask,A,o,stats

def cutter(shape,A,o,center,frame,radii):
    """Voxel centers inside the inherited physical ellipsoid, evaluated in LPS."""
    R=np.empty(shape,dtype=bool)
    j,k=np.meshgrid(np.arange(shape[1]),np.arange(shape[2]),indexing='ij')
    B=A@frame;offset=(o-center)@frame
    for i in range(shape[0]):
        if i%32==0:guard()
        total=np.zeros(j.shape,dtype=float)
        for axis in range(3):
            q=(i*B[0,axis]+j*B[1,axis]+k*B[2,axis]+offset[axis])/radii[axis]
            total+=q*q
        R[i]=total<=1
    return R

def pack(m):return np.packbits(m.reshape(-1,order='C'),bitorder='little')

def components(mask):
    labels,n=ndimage.label(mask,ndimage.generate_binary_structure(3,1))
    sizes=np.bincount(labels.ravel())[1:]
    result={'count_6':int(n),'largest_voxels':int(sizes.max()),'all_voxels':int(sizes.sum()),
            'largest_fraction':float(sizes.max()/sizes.sum())}
    del labels
    return result

def tests():
    a=np.zeros((21,21,21),bool)
    grid=np.indices(a.shape).transpose(1,2,3,0).astype(float)-10
    rr=np.linalg.norm(grid,axis=-1);a[(rr>=6)&(rr<=8)]=True
    A=np.eye(3);o=np.array([-10.,-10.,-10.]);c=np.array([6.,0.,0.]);f=np.eye(3);r=np.array([5.,5.,5.])
    R=cutter(a.shape,A,o,c,f,r);G=a&R;D=a&~R
    geo.partition(a,D,G)
    _,faces,_=geo.boundary_and_interface(D,G,A)
    assert sum(x['faces'] for x in faces)>0
    assert not a[10,10,10] and not (D|G)[10,10,10]
    noisy=a.copy();noisy[0,0,0]=True
    assert ((noisy&~R)|(noisy&R))[0,0,0]
    rot=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    ar=np.diag([.7,1.1,1.5])@rot
    origin=np.array([-3.,-5.,-7.]);center=np.array([2.,3.,1.]);rad=np.array([4.,5.,6.])
    R2=cutter((9,10,11),ar,origin,center,rot,rad)
    ix=np.indices(R2.shape).transpose(1,2,3,0)
    exact=np.sum((((ix@ar+origin-center)@rot)/rad)**2,axis=-1)<=1
    assert np.array_equal(R2,exact)
    assert np.array_equal(R2,cutter(R2.shape,ar@T,origin@T,center@T,T@rot,rad))
    cp,dp,gp=pack(a),pack(D),pack(G)
    assert np.array_equal(cp,dp|gp) and not np.any(dp&gp)
    assert np.array_equal(np.unpackbits(cp,bitorder='little',count=a.size).reshape(a.shape).astype(bool),a)
    return {'status':'PASS','checks':['solid C=D union G and disjoint', 'nonempty shell cut wall',
             'unfilled inner cavity', 'raw disconnected foreground retained',
             'anisotropic rotated affine equals independent world formula',
             'RAS/LPS equivalent cutter', 'packed solid Boolean complement', 'packed roundtrip']}

def prepare():
    ids=LOCK.joinpath('development100_ids.txt').read_text().split()
    if len(ids)!=100 or len(set(ids))!=100:raise ValueError('development100 identity')
    old=[json.loads(s) for s in HISTORY.read_text(encoding='utf-8').splitlines() if s.strip()]
    by={r['case_id'].split('__')[1]:r for r in old if r['defect_type']=='ellipsoid_medium'}
    if set(by)!=set(ids):raise ValueError('historical medium cutter identity mismatch')
    with (LOCK/'source_fold_assignments.csv').open(encoding='utf-8-sig',newline='') as f:
        folds={r['source_id']:r['fold'] for r in csv.DictReader(f)}
    if set(folds)!=set(ids):raise ValueError('source fold mapping mismatch')
    archives=sorted((DATA/'raw_v20/archives/d6_development100_v1').glob('*/*.zip'))
    inventory={}
    for archive in archives:
        st=archive.stat()
        if archive.is_symlink():raise ValueError('archive symlink')
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                terminal=PurePosixPath(info.filename).name
                if terminal.endswith('.nrrd') and terminal[:-5] in ids:
                    sid=terminal[:-5]
                    if sid in inventory:raise ValueError('duplicate NRRD member identity')
                    originals=[i for i in z.infolist() if PurePosixPath(i.filename).name==sid+'.stl']
                    inventory[sid]={'archive':str(archive),'archive_bytes':st.st_size,'archive_mtime_ns':st.st_mtime_ns,
                        'nrrd_member':info.filename,'nrrd_bytes':info.file_size,'nrrd_crc':info.CRC,
                        'original_stl_member':originals[0].filename if len(originals)==1 else None}
    entries=[]
    for sid in sorted(ids):
        r=by[sid]
        if r['d6_partition']!='development' or r['d6_fold']!=folds[sid]:raise ValueError('historical split drift')
        entries.append({'source_id':sid,'fold':folds[sid],'historical_case_id':r['case_id'],
             'historical_clear_stl_sha256':r['source_asset_sha256'],
             'old_geometry':r['geometry'],'asset':inventory.get(sid)})
    metadata=[Path(__file__),GEOMETRY,geo.READER,HISTORY,LOCK/'development100_ids.txt',LOCK/'source_fold_assignments.csv']
    scope={'status':'FROZEN_BEFORE_NRRD_PAYLOAD','entries':entries,
       'implementation_metadata_sha256':{str(p):sha(p) for p in metadata},
       'protocol':{'id':'MUG_SOLID_DEFECTS_V2_20261102','sources':100,'family':'ellipsoid_medium',
         'one_attempt_per_source':True,'cutter':'inherit each source historical center/frame/radii; no search or adjustment',
         'coordinate_rule':'old cutter in original mesh space; require explicit original STL SPACE=RAS/LPS; map to canonical LPS',
         'C':'all raw nonzero binary foreground; no largest-component removal',
         'D':'C AND NOT R','G':'C AND R','R':'closed ellipsoid evaluated at native voxel centers',
         'output':'full packed C/D/G, native affine, cutter provenance, exact interface audit; no sampled clouds',
         'minimum_G_to_FOV_margin_mm':5,'margin_basis':'G bbox to image voxel-face planes, not entire cutter AABB',
         'cutwall':'six-neighbor D/G shared voxel faces; physical area/normals from affine',
         'new_split':False,'no_rebalance_after_rejections':True,'formal_training_eligible':False,
         'eligibility_reason':'raw binary semantics/foreground anatomy not independently reviewed; geometric validity is a separate label',
         'source_specific_rejections':'record invalid source once, continue other frozen independent sources; no replacement',
         'unexpected_execution_failure':'stop batch without repair or retry',
         'budgets':{'seconds':3600,'case_seconds':180,'RSS_bytes':8*1024**3,'output_bytes':2*1024**3,
                    'NRRD_member_bytes':512*1024**2,'decoded_voxels':160_000_000}},
       'excluded':['sealed confirmation25','previous external holdout','new downloads','CT thresholding',
                   'component deletion/fill/smooth','new cutter families','sampling parameter search','model/GPU/training']}
    dump(OUT/'scope.json',scope)
    return scope

def run_source(e):
    sid=e['source_id'];asset=e['asset']
    row={'source_id':sid,'fold':e['fold'],'historical_case_id':e['historical_case_id'],
         'formal_training_eligible':False,'anatomical_GT_verified':False,'point_clouds_generated':0}
    need(asset is not None,'NRRD_MEMBER_NOT_AVAILABLE')
    p=Path(asset['archive']);st=p.stat()
    if st.st_size!=asset['archive_bytes'] or st.st_mtime_ns!=asset['archive_mtime_ns']:
        raise RuntimeError('archive changed after scope freeze: '+sid)
    need(asset['nrrd_bytes']<=512*1024**2,'NRRD_MEMBER_SIZE_BUDGET')
    with zipfile.ZipFile(p) as z:
        info=z.getinfo(asset['nrrd_member'])
        if info.CRC!=asset['nrrd_crc'] or info.file_size!=asset['nrrd_bytes']:
            raise RuntimeError('NRRD member metadata drift')
        blob=z.read(info);member_sha=hashlib.sha256(blob).hexdigest()
        row['nrrd_member_sha256']=member_sha;row['nrrd_member']=asset['nrrd_member']
        # Store source evidence even when its scalar semantics are rejected.
        dump(OUT/'source_evidence'/f'{sid}.json',{'asset':asset,'nrrd_member_sha256':member_sha})
        C,A,o,scalar=decode(blob);del blob
        row['raw_source']=scalar
        guard()
        need(asset['original_stl_member'] is not None,'ORIGINAL_STL_COORDINATE_DECLARATION_UNAVAILABLE')
        with z.open(asset['original_stl_member']) as f:head=f.read(84)
        header=head[:80].decode('ascii',errors='replace').strip('\x00 ')
        row['original_stl_header']=header
        upper=re.sub(r'\s+','',header.upper())
        if 'SPACE=RAS' in upper:transform=T
        elif 'SPACE=LPS' in upper:transform=np.eye(3)
        else:raise SourceRejected('ORIGINAL_STL_HAS_NO_EXPLICIT_RAS_LPS_COORDINATE_DECLARATION')
        old=e['old_geometry'];center=np.array(old['cut_center_mm'])@transform
        frame=transform@np.array(old['frame']);radii=np.array(old['radii_mm'])
        need(np.allclose(frame.T@frame,np.eye(3),atol=1e-10) and np.all(radii>0),'INHERITED_CUTTER_INVALID')
        row['cutter_LPS']={'center':center.tolist(),'frame_columns':frame.tolist(),'radii':radii.tolist()}
        R=cutter(C.shape,A,o,center,frame,radii);G=C&R;D=C&~R;del R
        need(G.any() and D.any(),'CUTTER_DOES_NOT_PRODUCE_NONEMPTY_D_AND_G')
        geo.partition(C,D,G)
        boundaries,jdirections,jhash=geo.boundary_and_interface(D,G,A)
        countG=int(G.sum());countC=int(C.sum())
        gb=geo.bbox(G);inv=np.linalg.inv(A)
        planes_per_index=1/np.linalg.norm(inv,axis=0)
        margins=np.array([[lo+.5,C.shape[a]-.5-hi] for a,(lo,hi) in enumerate(gb)])*planes_per_index[:,None]
        raw_components=components(C);guard()
        crop=G[tuple(slice(lo,hi+1) for lo,hi in gb)]
        g_components=components(crop)
        warning=['RAW_BINARY_FOREGROUND_NOT_EXPERT_GT']
        if raw_components['count_6']>1:warning.append('RAW_FOREGROUND_HAS_MULTIPLE_COMPONENTS_ALL_RETAINED')
        if g_components['count_6']>1:warning.append('G_HAS_MULTIPLE_COMPONENTS_ALL_RETAINED')
        fov=geo.edge_counts(C)
        if any(fov):warning.append('RAW_COMPLETE_FOREGROUND_TOUCHES_FOV')
        support_pass=bool(margins.min()>=5)
        if not support_pass:warning.append('G_FOV_SUPPORT_MARGIN_BELOW_5MM')
        g_j=sum(d['faces'] for d in jdirections)
        need(boundaries['G']>g_j,'G_HAS_NO_UNKNOWN_ORIGINAL_BOUNDARY')
        path=OUT/'solids'/f'{sid}__ellipsoid_medium__raw_CDG.npz'
        cp,dp,gp=pack(C),pack(D),pack(G)
        with path.open('xb') as f:
            np.savez_compressed(f,C_bits=cp,D_bits=dp,G_bits=gp,shape=np.array(C.shape,dtype=np.int32),
                directions=A,origin=o,cut_center_LPS=center,cut_frame_columns_LPS=frame,cut_radii_mm=radii)
        # Reload stored arrays. Verify saved solids, not just in-memory construction.
        with np.load(path,allow_pickle=False) as n:
            if not (np.array_equal(n['C_bits'],cp) and np.array_equal(n['D_bits'],dp)
                    and np.array_equal(n['G_bits'],gp) and np.array_equal(n['C_bits'],n['D_bits']|n['G_bits'])
                    and not np.any(n['D_bits']&n['G_bits']) and np.array_equal(n['directions'],A)
                    and np.array_equal(n['origin'],o)):
                raise RuntimeError('saved packed solid verification failed')
        row.update(status='GEOMETRY_VALIDATED_RESEARCH_CANDIDATE' if support_pass else 'GEOMETRY_CONSTRUCTED_FOV_SUPPORT_NOT_ADMITTED',
            research_geometry_eligible=support_pass,shape=list(C.shape),canonical_space='LPS',
            raw_C_fingerprint=geo.reader.mask_hash(C),voxels={'C':countC,'D':int(D.sum()),'G':countG},
            G_volume_mm3=countG*float(abs(np.linalg.det(A))),G_to_C_volume_fraction=countG/countC,
            D_boundary_faces=boundaries['D'],G_boundary_faces=boundaries['G'],J_faces=g_j,
            J_area_mm2=sum(d['area_mm2'] for d in jdirections),G_E_faces=boundaries['G']-g_j,
            exact_partition=True,exact_shared_face_pairing=True,opposite_physical_normals=True,
            interface_directions=jdirections,interface_keys_sha256=jhash,
            raw_foreground_components=raw_components,G_components=g_components,
            G_FOV_margin_mm=margins.tolist(),minimum_G_FOV_margin_mm=float(margins.min()),
            C_FOV_contact_voxels=fov,warnings=warning,
            solid_path=str(path.relative_to(OUT)),solid_sha256=sha(path),solid_bytes=path.stat().st_size,
            solid_layout='C-order, numpy packbits bitorder=little, ignore trailing padding bits past prod(shape)',
            C_foreground_semantics='raw original binary foreground retained verbatim; no anatomical cleanup',
            coordinate_evidence_limit='Original STL declaration plus historical clear-STL cutter provenance; no full per-source CT/mesh registration or anatomical certification')
        # Optional nonorthogonal grids are reported instead of geometrically misleading pictures.
        row['section']=geo.section_image(sid,D,G,A,gb)
        if hashlib.sha256(z.read(info)).hexdigest()!=member_sha:
            raise RuntimeError('source NRRD member changed across processing')
        guard()
    after=p.stat()
    if (after.st_size,after.st_mtime_ns)!=(st.st_size,st.st_mtime_ns):raise RuntimeError('archive stat drift')
    return row

def main():
    global CASE_START
    OUT.mkdir(exist_ok=False)
    for d in ['cases','solids','sections','source_evidence']: (OUT/d).mkdir()
    geo.OUT=OUT
    scope=prepare()
    CASE_START=time.monotonic();geo.CASE_START=CASE_START
    dump(OUT/'synthetic_tests.json',tests())
    rows=[]
    for i,e in enumerate(scope['entries']):
        CASE_START=time.monotonic();geo.CASE_START=CASE_START;guard()
        print(f"START {i+1}/100 {e['source_id']}",flush=True)
        try:
            row=run_source(e)
        except (SourceRejected,gzip.BadGzipFile,EOFError,zipfile.BadZipFile) as exc:
            row={'source_id':e['source_id'],'fold':e['fold'],'status':'SOURCE_NOT_ADMITTED_NO_SOLID',
                 'reason':str(exc),'reason_type':type(exc).__name__,'formal_training_eligible':False,
                 'anatomical_GT_verified':False,'replacement_or_retry':False}
        row['elapsed_seconds']=time.monotonic()-CASE_START
        dump(OUT/'cases'/f"{e['source_id']}.json",row);rows.append(row)
        print('DONE',row['source_id'],row['status'],row.get('reason',''),flush=True)
        gc.collect();guard()
        if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*1024**3:
            raise RuntimeError('2 GiB output budget exceeded')
    for name,digest in scope['implementation_metadata_sha256'].items():
        if sha(name)!=digest:raise RuntimeError('metadata or implementation changed during batch')
    summary={'status':'BATCH_COMPLETED_WITH_EXPLICIT_SOURCE_DISPOSITIONS',
             'scope_sha256':sha(OUT/'scope.json'),'source_count':100,
             'status_counts':dict(Counter(r['status'] for r in rows)),
             'source_rejection_reasons':dict(Counter(r['reason'] for r in rows if 'reason' in r)),
             'solids_written':sum('solid_path' in r for r in rows),
             'research_geometry_eligible':sum(r.get('research_geometry_eligible',False) for r in rows),
             'formal_training_eligible':0,'sealed_source_payload_reads':0,'thresholding_or_cleaning':0,
             'new_point_sets':0,'model_GPU_training_calls':0,'one_attempt_per_source':True,
             'elapsed_seconds':time.monotonic()-START,'sampled_RSS_max_bytes':max(PEAK,geo.PEAK),
             'source_preservation':'each decoded constructed source ZIP NRRD member SHA256 rechecked; archive size/mtime checked; whole 50GB container SHA256 not recalculated',
             'training_admission_limit':'No independent anatomical/segmentation review; geometry-only pass is not formal high-precision GT admission'}
    dump(OUT/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=True),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as exc:
        if OUT.exists() and not (OUT/'failure.json').exists():
            dump(OUT/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(exc),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
