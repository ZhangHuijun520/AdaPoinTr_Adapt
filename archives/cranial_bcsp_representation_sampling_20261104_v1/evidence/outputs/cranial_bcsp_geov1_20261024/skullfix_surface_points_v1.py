# -*- coding: utf-8 -*-
"""SkullFix fixed train80/val10 V1 boundary point preparation; local CPU only."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import csv,gc,hashlib,importlib.util,json,sys,time,traceback
from pathlib import Path
import numpy as np
import psutil

BASE=Path(__file__).resolve().parent
OUT=BASE/'skullfix_surface_points_20261103_v1'
SCOPE=BASE/'main_data_scope_and_surface_sampling_20261102_v1/data_scope_and_sampling_contract_v1.json'
PRIOR=BASE/'skullfix_batch_geometry_qc_20261102_v1'
SAMPLER=BASE/'real_data_qc_v1.py'
READER=BASE/'skullfix_batch_geometry_qc_v1.py'
RAW=Path('E:/dataset/SkullFix/extracted/training_set')
START=time.monotonic()
CASE_START=START
PEAK=0

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dump(p,obj):
    with Path(p).open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)

def module(name,p):
    s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

sb=module('unchanged_boundary_sampler',SAMPLER)
sf=module('unchanged_binary_reader',READER)

def guard():
    global PEAK
    PEAK=max(PEAK,psutil.Process().memory_info().rss)
    if PEAK>8*1024**3 or time.monotonic()-START>3600 or time.monotonic()-CASE_START>180:
        raise RuntimeError('8 GiB monitored RSS / 60 minute batch / 180 second case budget exceeded')

# Reuse unchanged sampling/metric functions with this batch's monitoring callback.
sb.guard=guard

def npz(p,**arrays):
    with p.open('xb') as f:np.savez_compressed(f,**arrays)

def fov_flags(surface,shape):
    q,axis,sign=surface
    axis_position=q[np.arange(len(q)),axis]
    return ((sign==-1)&(axis_position==0))|((sign==1)&(axis_position==np.array(shape)[axis]-1))

def face_membership(points,surface,ids,A,o):
    local=(points-o)@np.linalg.inv(A)-surface[0][ids]
    axis,sign=surface[1][ids],surface[2][ids]
    normal_error=np.abs(local[np.arange(len(local)),axis]-.5*sign)
    if normal_error.max()>1e-9 or np.abs(local).max()>.5+1e-9:
        raise ValueError('sample not on selected native face')
    return float(normal_error.max())

def synthetic_checks():
    a=np.zeros((4,5,6),bool);a[1,2,3]=True
    A=np.diag([.4,.5,.7]);o=np.array([3.,-2.,7.])
    surf=sb.surface(a);assert len(surf[0])==6
    points,ids,centers,w=sb.sample(surf,A,o,0,16384)
    assert np.isclose(w.sum(),2*(.4*.5+.4*.7+.5*.7))
    assert not fov_flags(surf,a.shape).any()
    face_membership(points,surf,ids,A,o)
    rotation=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    rotated=sb.sample(surf,A@rotation,o,0,16384)[0]
    assert np.allclose(rotated-o,(points-o)@rotation)
    other=np.zeros_like(a);other[2,2,3]=True
    sg=sb.surface(other);jd=sb.contact(surf,other);jg=sb.contact(sg,a)
    kd,sd=sb.keys(surf,jd);kg,ss=sb.keys(sg,jg)
    assert len(kd)==1 and np.array_equal(kd,kg) and np.array_equal(sd,-ss)
    edge=np.zeros_like(a);edge[0,0,0]=True
    assert fov_flags(sb.surface(edge),edge.shape).sum()==3
    center,scale=sb.frame(a|other,A,o)
    normalized=((points[:8192]-center)/scale).astype(np.float32)
    assert np.max(np.linalg.norm(normalized.astype(float)*scale+center-points[:8192],axis=1))<1e-3
    assert np.array_equal(points[:8192],sb.sample(surf,A,o,0,16384)[0][:8192])
    return {'status':'PASS','checks':['single-voxel six boundary faces',
        'anisotropic physical face area','sample membership in native face',
        'rigidly rotated affine sampling equivalence','exact D/G face keys and opposite signs',
        'FOV face identification','float32 D-only normalization roundtrip','frozen 16k draw to 8k prefix reproducibility']}

def region_stats(s,tag,w,ids,points,centers):
    fov=tag['FOV'];J=tag['J']
    if np.any(fov&J):raise ValueError('FOV cannot be a shared in-grid D/G interface')
    return {'boundary_faces':len(s[0]),'total_area_mm2':float(w.sum()),
        'J_faces':int(J.sum()),'J_area_mm2':float(w[J].sum()),
        'FOV_faces':int(fov.sum()),'FOV_area_mm2':float(w[fov].sum()),
        'FOV_area_fraction':float(w[fov].sum()/w.sum()),
        'sample_J_points':int(J[ids].sum()),'sample_FOV_points':int(fov[ids].sum()),
        'sample_original_mask_boundary_points':int((~J[ids]).sum()),
        'all_boundary_metric':sb.metric(centers,w,points),
        'J_metric':sb.metric(centers[J],w[J],points),
        'J_provenance_only_metric':sb.metric(centers[J],w[J],points[J[ids]]) if J[ids].any() else None}

def main():
    global CASE_START
    contract=json.loads(SCOPE.read_text(encoding='utf-8'))
    assert sha(SAMPLER)==contract['sampling']['implementation_sha256']
    prior_scope=json.loads((PRIOR/'scope.json').read_text(encoding='utf-8'))
    prior_manifest=json.loads((PRIOR/'artifact_manifest.json').read_text(encoding='utf-8'))
    assert sha(PRIOR/'scope.json')==contract['evidence_sha256'][str(PRIOR/'scope.json')]
    ids=prior_scope['selected_ids'];train=set(prior_scope['selected_train_ids']);val=set(prior_scope['selected_validation_ids'])
    excluded=set(prior_scope['excluded_test_ids'])
    assert len(ids)==90 and len(train)==80 and len(val)==10 and not train&val
    assert set(ids)==train|val and not(set(ids)&excluded)
    assert ids==contract['datasets']['SkullFix']['allowed_geometry_preparation_ids']
    before={}
    for cid in ids:
        for role,name in [('complete','complete_skull'),('defective','defective_skull'),('implant','implant')]:
            p=Path(prior_scope['raw_mapping'][cid][role])
            assert p.resolve()==(RAW/name/f'{cid}.nrrd').resolve()
            assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(RAW.resolve())
            digest=sha(p);assert digest==prior_scope['raw_files_before'][str(p)]['sha256']
            before[str(p)]={'sha256':digest,'bytes':p.stat().st_size}
    dependencies=[Path(__file__),SCOPE,SAMPLER,READER,sb.READER,sb.LOCK,PRIOR/'scope.json',PRIOR/'artifact_manifest.json']
    dependencies.extend(Path(p) for p in prior_scope['implementation_metadata_hashes'])
    frozen={str(p):sha(p) for p in set(dependencies)}
    OUT.mkdir(exist_ok=False)
    for dirname in ['points','diagnostics','cases']:(OUT/dirname).mkdir()
    dump(OUT/'scope.json',{'date':'2026-11-03','status':'FROZEN_BEFORE_RAW_DECODE',
        'authorization':'User instruction: complete new-representation points for the already opened 90 SkullFix cases',
        'source_ids':ids,'train_ids':sorted(train),'validation_ids':sorted(val),'excluded_internal_test_ids':sorted(excluded),
        'raw_files_before':before,'implementation_and_metadata_sha256':frozen,
        'configuration':{'input_draw_count':16384,'saved_input_count':8192,'target_count':8192,'seed':0,
            'sampler':'unchanged V1 world-area-weighted exposed voxel faces',
            'normalization':'D occupied voxel-center world bbox midpoint and half diagonal',
            'input_completed_before_C_G_decode':True,'point_schema':'partial/implant normalized float32',
            'face_labels_stored_separately_diagnostic_only':True,'FOV_faces_included_and_flagged':True},
        'limits':{'seconds':3600,'case_seconds':180,'monitored_RSS_bytes':8*1024**3,'output_bytes':1024**3},
        'prohibitions':['no test payload','no source writes','no geometry cleaning','no new sampling method',
            'no model/checkpoint/GPU/server/training','no automatic failure retry']})
    CASE_START=time.monotonic();dump(OUT/'synthetic_checks.json',synthetic_checks())
    records=[];rows=[]
    for i,cid in enumerate(ids):
        CASE_START=time.monotonic();guard();print(f'START {i+1}/90 {cid}',flush=True)
        prior_path=PRIOR/'cases'/f'{cid}.json'
        assert sha(prior_path)==prior_manifest['files'][str(prior_path.relative_to(PRIOR))]['sha256']
        old=json.loads(prior_path.read_text(encoding='utf-8'))
        rp={k:Path(p) for k,p in prior_scope['raw_mapping'][cid].items()}
        D,A,o,space,values=sf.read_binary(rp['defective']);guard()
        sd=sb.surface(D);draw,di_all,dc,dw=sb.sample(sd,A,o,0,16384)
        pd=draw[:8192];di=di_all[:8192]
        center,scale=sb.frame(D,A,o)
        partial=((pd-center)/scale).astype(np.float32)
        d_face_error=face_membership(pd,sd,di,A,o)
        # Input coordinates are finalized before either complete or target payload is decoded.
        C,B,b,space_c,_=sf.read_binary(rp['complete']);guard()
        G,F,f,space_g,_=sf.read_binary(rp['implant']);guard()
        if not(C.shape==D.shape==G.shape and np.array_equal(A,B) and np.array_equal(A,F)
               and np.array_equal(o,b) and np.array_equal(o,f) and space==space_c==space_g):
            raise ValueError('physical grid mismatch')
        sf.partition(C,D,G)
        if sf.reader.mask_hash(C)!=old['complete_mask_fingerprint']:raise ValueError('complete-mask identity changed')
        jd=sb.contact(sd,G);sg=sb.surface(G);pg,gi,gc_,gw=sb.sample(sg,A,o,0,8192)
        g_face_error=face_membership(pg,sg,gi,A,o)
        target=((pg-center)/scale).astype(np.float32)
        jg=sb.contact(sg,D);kd,ds=sb.keys(sd,jd);kg,gs=sb.keys(sg,jg)
        if not(len(kd)==old['shared_J_faces'] and np.array_equal(kd,kg) and np.array_equal(ds,-gs)):
            raise ValueError('shared cutwall face pairing changed')
        if not np.isclose(dw[jd].sum(),gw[jg].sum(),rtol=1e-12):raise ValueError('shared cutwall area mismatch')
        fd=fov_flags(sd,D.shape);fg=fov_flags(sg,G.shape)
        if np.any(fg):raise ValueError('G unexpectedly touches FOV compared with prior QC')
        dmetric=region_stats(sd,{'J':jd,'FOV':fd},dw,di,pd,dc)
        gmetric=region_stats(sg,{'J':jg,'FOV':fg},gw,gi,pg,gc_)
        gmetric['original_boundary_E_metric']=sb.metric(gc_[~jg],gw[~jg],pg)
        derror=float(np.max(np.linalg.norm(partial.astype(float)*scale+center-pd,axis=1)))
        gerror=float(np.max(np.linalg.norm(target.astype(float)*scale+center-pg,axis=1)))
        if max(derror,gerror)>1e-3 or not np.isfinite(partial).all() or not np.isfinite(target).all():
            raise ValueError('normalized point numeric contract')
        pp=OUT/'points'/f'{cid}_8192.npz'
        npz(pp,partial=partial,implant=target)
        dp=OUT/'diagnostics'/f'{cid}_face_provenance.npz'
        npz(dp,D_sample_voxel_indices=sd[0][di],D_sample_axis=sd[1][di],D_sample_sign=sd[2][di],
            D_sample_face_ids=di,D_sample_is_J=jd[di],D_sample_is_FOV=fd[di],
            G_sample_voxel_indices=sg[0][gi],G_sample_axis=sg[1][gi],G_sample_sign=sg[2][gi],
            G_sample_face_ids=gi,G_sample_is_J=jg[gi],G_sample_is_FOV=fg[gi],directions=A,origin=o,
            normalization_center=center,normalization_scale=np.array(scale))
        with np.load(pp,allow_pickle=False) as n:
            if set(n.files)!={'partial','implant'} or not np.array_equal(n['partial'],partial) or not np.array_equal(n['implant'],target):
                raise ValueError('written training point arrays differ')
        with np.load(dp,allow_pickle=False) as n:
            for prefix,npoints in [('D',8192),('G',8192)]:
                q=n[prefix+'_sample_voxel_indices'].astype(float);axis=n[prefix+'_sample_axis'];sign=n[prefix+'_sample_sign']
                q[np.arange(npoints),axis]+=.5*sign
                face_centers=q@A+o
                actual=pd if prefix=='D' else pg
                if np.max(np.abs(((actual-face_centers)@np.linalg.inv(A))[np.arange(npoints),axis]))>1e-9:
                    raise ValueError('written provenance does not match point coordinates')
        for p in rp.values():
            if sha(p)!=before[str(p)]['sha256']:raise ValueError('raw source changed')
        record={'dataset':'SkullFix','case_id':cid,'source_id':'SkullFix:'+cid,
            'split':'train' if cid in train else 'val','point_path':str(pp.relative_to(OUT)).replace('\\','/'),
            'sha256':sha(pp),'schema':'BCSP-normalized-v1','n_input':8192,'n_target':8192,
            'normalization_source':'defective_bbox','normalization':{'center':center.tolist(),'scale':scale},
            'target_array_sha256':hashlib.sha256(target.tobytes()).hexdigest(),
            'diagnostic_provenance_path':str(dp.relative_to(OUT)).replace('\\','/'),
            'diagnostic_provenance_sha256':sha(dp),'diagnostic_labels_not_input_features':True,
            'raw':{k:{'path':str(p),'sha256':before[str(p)]['sha256']} for k,p in rp.items()}}
        row={'case_id':cid,'split':record['split'],'source_id':record['source_id'],'D':dmetric,'G':gmetric,
            'roundtrip_world_max_mm':{'D':derror,'G':gerror},'native_face_membership_error':{'D':d_face_error,'G':g_face_error},
            'shared_J_pairing_verified':True,'prior_geometry_warnings':old['warnings'],
            'input_completed_before_C_G_decode':True,'inner_outer_anatomical_labels':'not available; no separate coverage certification',
            'elapsed_seconds':time.monotonic()-CASE_START}
        dump(OUT/'cases'/f'{cid}.json',row);rows.append(row);records.append(record)
        print(f"DONE {cid} D_J={dmetric['sample_J_points']} D_FOV={dmetric['sample_FOV_points']} G_J={gmetric['sample_J_points']}",flush=True)
        del C,D,G,sd,sg,draw,di_all,di,dc,dw,pg,gi,gc_,gw,jd,jg,kd,kg,ds,gs,partial,target,fd,fg
        gc.collect();guard()
        if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>1024**3:raise RuntimeError('1 GiB output budget exceeded')
    for p,v in before.items():
        if sha(p)!=v['sha256']:raise ValueError('raw final hash mismatch')
    for p,digest in frozen.items():
        if sha(p)!=digest:raise ValueError('implementation/metadata drift')
    for name,items in [('manifest_8192.jsonl',records),('train_manifest_8192.jsonl',[r for r in records if r['split']=='train']),
                       ('validation_manifest_8192.jsonl',[r for r in records if r['split']=='val'])]:
        with (OUT/name).open('x',encoding='utf-8') as f:
            for r in items:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    assert [r['case_id'] for r in records if r['split']=='train']==sorted(train)
    assert [r['case_id'] for r in records if r['split']=='val']==sorted(val)
    summary={'status':'COMPLETED_NEW_REPRESENTATION_POINTS_NOT_TRAINING_AUTHORIZATION',
        'dataset':'SkullFix','cases':90,'train':80,'validation':10,'excluded_internal_test_payload_reads':0,
        'input_points':8192,'target_points':8192,'input_draw_before_prefix':16384,'sampling_seed':0,
        'raw_files':270,'raw_hashes_unchanged':True,'implementation_and_metadata_unchanged':True,
        'point_files':90,'diagnostic_provenance_files':90,'all_shared_J_faces_verified':True,
        'G_FOV_face_count':sum(r['G']['FOV_faces'] for r in rows),
        'D_FOV_sample_points_total':sum(r['D']['sample_FOV_points'] for r in rows),
        'cases_with_sampled_D_FOV':sum(r['D']['sample_FOV_points']>0 for r in rows),
        'elapsed_seconds':time.monotonic()-START,'sampled_RSS_max_bytes':max(PEAK,sb.PEAK_RSS),
        'model_GPU_server_training_calls':0,
        'limitations':['No inner/outer anatomical labels or complete coverage certification',
          'FOV cap faces retained by inherited V1 and flagged; not natural anatomy',
          'Metrics use native voxel face centers/areas, not continuous anatomical surface truth',
          'One sampling seed; no sampler superiority or trained-model benefit claim',
          'No complete training-loader/GPU validation or new training request implied']}
    dump(OUT/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=True),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as exc:
        if OUT.exists() and not (OUT/'failure.json').exists():
            dump(OUT/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(exc),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
