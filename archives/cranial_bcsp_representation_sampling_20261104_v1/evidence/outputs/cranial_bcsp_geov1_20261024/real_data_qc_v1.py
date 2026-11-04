"""Fixed 84-source/420-case BCSP scientific data QC. No torch/server/network."""
import os
os.environ['OMP_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
import gc
import hashlib
import importlib.util
import itertools
import json
import sys
import time
import traceback
from collections import Counter
from pathlib import Path
import numpy as np
import psutil
from scipy.spatial import cKDTree

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
OUT=BASE/'real_data_qc_v1'
RAW=Path('E:/dataset/SkullBreak/raw')
MANIFEST=Path('E:/dataset/SkullBreakPC/manifest.jsonl')
BIND=BASE/'consolidated_binding_v1/fold_binding.json'
READER=ROOT/'outputs/cranial_geometry_diagnostic_20261023/analyze_raw_pairs_v1.py'
LOCK=ROOT/'outputs/cranial_scqr_v12_qa_github_publish_20261019/tools/lock_skullbreak_mamba_v12_development_protocol.py'
START=time.monotonic()
CASE_START=START
PEAK_RSS=0
WRITTEN=0

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,obj):
    global WRITTEN
    with Path(p).open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
    WRITTEN+=Path(p).stat().st_size
def guard():
    global PEAK_RSS
    rss=psutil.Process().memory_info().rss;PEAK_RSS=max(PEAK_RSS,rss)
    if time.monotonic()-START>3600:raise RuntimeError('60 minute batch budget')
    if time.monotonic()-CASE_START>900:raise RuntimeError('15 minute case budget')
    if rss>8*1024**3:raise RuntimeError('8 GiB monitored RSS budget')
    if WRITTEN>1024**3:raise RuntimeError('1 GiB output budget')
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
raw=module('fixed_raw_reader',READER)
lock=module('fixed_source_protocol',LOCK)

def surface(mask):
    """Input boundary extractor receives D only; no C/G/J arguments."""
    q=[];axes=[];signs=[]
    for axis in range(3):
        for sign in (-1,1):
            guard()
            a,b=raw.shifted_neighbor(mask,axis,sign)
            exposed=mask.copy();exposed[a]&=~mask[b]
            coords=np.argwhere(exposed).astype(np.int32)
            q.append(coords);axes.append(np.full(len(coords),axis,np.int8));signs.append(np.full(len(coords),sign,np.int8))
    return np.concatenate(q),np.concatenate(axes),np.concatenate(signs)
def face_geometry(s,A,o):
    q,axis,sign=s;p=q.astype(np.float64);p[np.arange(len(p)),axis]+=.5*sign
    centers=p@A+o
    area=np.array([np.linalg.norm(np.cross(A[(a+1)%3],A[(a+2)%3])) for a in range(3)])
    return centers,area[axis]
def sample(s,A,o,seed,n):
    centers,w=face_geometry(s,A,o);rng=np.random.default_rng(seed)
    ids=rng.choice(len(w),n,p=w/w.sum());p=centers[ids].copy();uv=rng.random((n,2))-.5
    for a in range(3):
        sel=s[1][ids]==a
        p[sel]+=uv[sel,0,None]*A[(a+1)%3]+uv[sel,1,None]*A[(a+2)%3]
    return p,ids,centers,w
def contact(s,other):
    q=s[0].copy();q[np.arange(len(q)),s[1]]+=s[2]
    inside=np.all((q>=0)&(q<np.array(other.shape)),axis=1)
    tag=np.zeros(len(q),bool);tag[inside]=other[tuple(q[inside].T)]
    return tag
def keys(s,tag):
    q=s[0][tag].astype(np.int64)*2;q[np.arange(len(q)),s[1][tag]]+=s[2][tag]
    # Axis + doubled integer face center gives a side-independent exact face key.
    k=np.column_stack((s[1][tag],q));order=np.lexsort(k.T[::-1]);return k[order],s[2][tag][order]
def frame(D,A,o):
    mins=[];maxs=[]
    for a in range(3):
        ids=np.where(D.any(axis=tuple(k for k in range(3) if k!=a)))[0]
        if not len(ids):raise ValueError('empty residual')
        mins.append(ids[0]);maxs.append(ids[-1])
    if np.all(A==np.diag(np.diag(A))):world=np.array(list(itertools.product(*zip(mins,maxs))))@A+o
    else:world=np.argwhere(D)@A+o
    lo=world.min(0);hi=world.max(0);center=(lo+hi)/2;scale=float(np.linalg.norm(hi-lo)/2)
    if not np.isfinite(scale) or scale<=0:raise ValueError('degenerate D frame')
    return center,scale
def metric(ref,w,points):
    if not len(ref) or not len(points):raise ValueError('empty metric region')
    tree=cKDTree(points);dist=[]
    for start in range(0,len(ref),65536):guard();dist.append(tree.query(ref[start:start+65536],workers=2)[0])
    d=np.concatenate(dist);ix=np.argsort(d);cum=np.cumsum(w[ix]);p95=d[ix[np.searchsorted(cum,.95*cum[-1])]]
    return {'cover_1mm':float(np.average(d<=1,weights=w)),'cover_2mm':float(np.average(d<=2,weights=w)),'p95_mm':float(p95)}
def pool_reference(centers,w,tag):
    ids=np.flatnonzero(~tag);weights=w[ids]
    chosen=np.random.default_rng(99173).choice(ids,131072,p=weights/weights.sum())
    return centers[chosen],np.ones(len(chosen))
def npz(path,**arrays):
    global WRITTEN
    with path.open('xb') as f:np.savez_compressed(f,**arrays)
    WRITTEN+=path.stat().st_size
def summary_number(v):return {'mean':float(np.mean(v)),'median':float(np.median(v)),'min':float(np.min(v)),'max':float(np.max(v))}

def main():
    global CASE_START
    OUT.mkdir(exist_ok=False);(OUT/'points').mkdir();(OUT/'cases').mkdir()
    records,msha=lock.read_manifest(MANIFEST);binding=json.loads(BIND.read_text(encoding='utf8'))
    if msha!=binding['manifest_sha256']:raise ValueError('metadata manifest drift')
    by=lock.validate_strict_train(lock.strict_train_records(records));confirmation,assign=lock.make_assignments(by)
    selected_ids=set();fold_qc={}
    for label,f in binding['folds'].items():
        train=set(f['train_sources']);dev=set(f['dev_sources'])
        if len(train)!=63 or len(dev)!=21 or train&dev or (train|dev)&confirmation:raise ValueError('source split leak/count')
        if dev!={s for s,a in assign.items() if a==label} or train!=set(assign)-dev:raise ValueError('stable source assignment mismatch')
        for key,sources,expected in [('train_case_ids',train,315),('dev_case_ids',dev,105)]:
            if f[key]!=lock.case_ids_for_skulls(by,sources) or len(f[key])!=expected:raise ValueError('case/source fold mapping mismatch')
            selected_ids.update(f[key])
        if hashlib.sha256(('\n'.join(f['train_case_ids'])+'\n').encode()).hexdigest()!=f['train_allowlist_sha256']:raise ValueError('allowlist hash')
        fold_qc[label]={'train_sources':63,'development_sources':21,'train_cases':315,'development_cases':105,'source_overlap':0,'confirmation_overlap':0}
    if len(selected_ids)!=420 or len(assign)!=84:raise ValueError('development universe')
    record_by_id={x['case_id']:x for x in records}
    selected=[record_by_id[i] for i in sorted(selected_ids)]
    paths=set()
    for r in selected:
        if r['official_split']!='train' or r.get('monitor_split')=='monitor' or r['skull_id'] in confirmation:raise ValueError('payload forbidden')
        for p in r['raw'].values():
            rel=Path(p)
            if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='train':raise ValueError('raw path escape')
            p=RAW/rel
            if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(RAW.resolve()):raise ValueError('raw unavailable/link')
            paths.add(p)
    if len(paths)!=924:raise ValueError('raw unique count')
    before={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)}
    frozen={str(p):sha(p) for p in (Path(__file__),BIND,MANIFEST,READER,LOCK)}
    save(OUT/'scope.json',{'status':'FROZEN_BEFORE_PAYLOAD_PROCESSING','sources':sorted(assign),'case_ids':sorted(selected_ids),'folds':fold_qc,'source_files':before,'implementation_inputs':frozen,'configuration':{'seed':0,'input_points':[8192,16384],'target_points':8192,'input_sampler':'V1_D_only_area_weighted_exposed_faces','nested_input_prefix':True,'reference':'Exact J voxel face centers with world-area weighting; E fixed-seed 131072 face-center area samples','normalization':'D occupied voxel-center world bbox center and half diagonal','no_op_count':0,'timeout_seconds':3600,'case_timeout_seconds':900,'monitored_rss_bytes':8*1024**3,'output_bytes':1024**3},'limitations':['No anatomical inner/outer plate labels; E is pooled original boundary, not outer-only','No payload reads of confirmation, monitor, official test','No training readiness or GPU claim']})
    rows=[];derived={8192:[],16384:[]};source_fingerprints={};previous=None;C=None
    for index,r in enumerate(selected):
        CASE_START=time.monotonic();guard();cid=r['case_id'];sid=r['skull_id'];print('START',index+1,cid,flush=True)
        rp={k:RAW/v for k,v in r['raw'].items()}
        if sid!=previous:
            C,A,o=raw.read_mask(rp['complete']);fp=raw.mask_hash(C)
            if fp in source_fingerprints:raise ValueError('duplicate complete-mask geometry across sources: '+sid+' '+source_fingerprints[fp])
            source_fingerprints[fp]=sid;previous=sid
        D,B,b=raw.read_mask(rp['defective'])
        if D.shape!=C.shape or not np.array_equal(A,B) or not np.array_equal(o,b):raise ValueError('C/D physical grid mismatch')
        # D-only input construction is completed before reading this case's G payload.
        sd=surface(D);pd,di,dc,dw=sample(sd,A,o,0,16384);center,scale=frame(D,A,o)
        G,F,f=raw.read_mask(rp['implant'])
        if G.shape!=C.shape or not np.array_equal(A,F) or not np.array_equal(o,f):raise ValueError('G physical grid mismatch')
        if np.any(D&G) or not np.array_equal(C,D|G):raise ValueError('solid partition mismatch')
        jd=contact(sd,G);sg=surface(G);pg,gi,gc_,gw=sample(sg,A,o,0,8192);jg=contact(sg,D)
        kd,ds=keys(sd,jd);kg,gs=keys(sg,jg)
        if not len(kd) or not np.array_equal(kd,kg) or not np.array_equal(ds,-gs):raise ValueError('exact J face pairing/normals')
        if not np.isclose(dw[jd].sum(),gw[jg].sum(),rtol=1e-12):raise ValueError('J area mismatch')
        e_ref,e_weight=pool_reference(dc,dw,jd);g_e_ref,g_e_w=pool_reference(gc_,gw,jg)
        target=((pg-center)/scale).astype(np.float32)
        target_array_sha=hashlib.sha256(target.tobytes()).hexdigest();normalized=((pd-center)/scale).astype(np.float32)
        row={'case_id':cid,'source_id':sid,'defect_type':r['defect_type'],'partition_mismatches':0,'J_face_keys_paired':len(kd),'D_boundary_faces':len(dc),'D_J_area_mm2':float(dw[jd].sum()),'D_native_area_mm2':float(dw[~jd].sum()),'G_native_area_mm2':float(gw[~jg].sum()),'G_J_sample_count':int(jg[gi].sum()),'G_native_sample_count':int((~jg[gi]).sum()),'target_array_sha256':target_array_sha,'center':center.tolist(),'scale':scale,'inner_outer_semantic_status':'UNRESOLVED_NO_TRUSTED_LABELS','G_J_metric':metric(gc_[jg],gw[jg],pg),'G_native_metric_MC':metric(g_e_ref,g_e_w,pg),'arms':{}}
        jt=cKDTree(dc[jd])
        for n in (8192,16384):
            points=pd[:n];on_j=jd[di[:n]];distance_to_j=jt.query(points,workers=2)[0];support=points[distance_to_j<=2]
            spacing=None
            if len(support)>1:
                d=cKDTree(support).query(support,k=2,workers=2)[0][:,1];spacing={'median_mm':float(np.median(d)),'p95_mm':float(np.percentile(d,95))}
            hist=Counter((int(a),int(s)) for a,s in zip(sd[1][di[:n]],sd[2][di[:n]]))
            row['arms'][str(n)]={'J_sample_count':int(on_j.sum()),'native_sample_count':int((~on_j).sum()),'contact_support_2mm_face_center_count':len(support),'contact_support_nn_spacing':spacing,'normal_axis_sign_counts':{str(k):v for k,v in hist.items()},'J_metric':metric(dc[jd],dw[jd],points),'J_same_provenance_metric':metric(dc[jd],dw[jd],points[on_j]) if on_j.any() else None,'native_metric_MC':metric(e_ref,e_weight,points),'roundtrip_world_max_mm':float(np.max(np.linalg.norm(normalized[:n].astype(float)*scale+center-points,axis=1)))}
            path=OUT/'points'/f'{cid}_{n}.npz';npz(path,partial=normalized[:n],implant=target)
            with np.load(path,allow_pickle=False) as z:
                if z['partial'].shape!=(n,3) or z['implant'].shape!=(8192,3) or not np.array_equal(z['partial'],normalized[:n]) or not np.array_equal(z['implant'],target):raise ValueError('written payload mismatch')
            derived[n].append({'case_id':cid,'source_id':sid,'point_path':str(path.relative_to(OUT)).replace('\\','/'),'sha256':sha(path),'schema':'BCSP-normalized-v1','normalization_source':'defective_bbox','n_input':n,'n_target':8192,'target_array_sha256':target_array_sha,'normalization':{'center':center.tolist(),'scale':scale},'raw':{k:{'path':str(p),'sha256':before[str(p)]['sha256']} for k,p in rp.items()}})
        with np.load(OUT/'points'/f'{cid}_8192.npz',allow_pickle=False) as a,np.load(OUT/'points'/f'{cid}_16384.npz',allow_pickle=False) as z:
            if not np.array_equal(a['partial'],z['partial'][:8192]) or not np.array_equal(a['implant'],z['implant']):raise ValueError('pair prefix/common target mismatch')
        row['paired_input_prefix_verified']=True;row['identical_target_verified']=True
        for p in rp.values():
            if sha(p)!=before[str(p)]['sha256']:raise ValueError('raw source changed: '+str(p))
        row['seconds']=time.monotonic()-CASE_START;row['observed_rss_bytes']=psutil.Process().memory_info().rss
        save(OUT/'cases'/f'{cid}.json',row);rows.append(row)
        print('DONE',index+1,cid,round(row['seconds'],3),flush=True)
        del D,G,sd,sg,pd,pg,di,gi,dc,gc_,dw,gw,jd,jg,kd,kg,ds,gs,normalized,target,jt,e_ref,e_weight,g_e_ref,g_e_w
        gc.collect();guard()
    for p,digest in frozen.items():
        if sha(Path(p))!=digest:raise ValueError('implementation/metadata drift')
    for n,records in derived.items():
        p=OUT/f'manifest_{n}.jsonl'
        with p.open('x',encoding='utf8') as f:
            for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    save(OUT/'fold_qc.json',{'status':'PASS_SOURCE_FOLD_METADATA_AND_DERIVED_IDENTITY','folds':fold_qc,'development_sources':84,'development_cases':420,'confirmation_excluded':20,'raw_files':924,'complete_mask_unique_fingerprints':len(source_fingerprints),'C_D_development_source_overlap':len(set(binding['folds']['C']['dev_sources'])&set(binding['folds']['D']['dev_sources'])),'cross_fold_note':'Training folds overlap by design; not independent datasets','frozen_fold_binding_sha256':sha(BIND),'manifests':{str(n):{'path':str(OUT/f'manifest_{n}.jsonl'),'sha256':sha(OUT/f'manifest_{n}.jsonl')} for n in derived}})
    aggregate={}
    for n in ('8192','16384'):
        aggregate[n]={}
        for metric_name in ('J_metric','native_metric_MC'):
            aggregate[n][metric_name]={key:summary_number([x['arms'][n][metric_name][key] for x in rows]) for key in ('cover_1mm','cover_2mm','p95_mm')}
        aggregate[n]['J_sample_count']=summary_number([x['arms'][n]['J_sample_count'] for x in rows])
        aggregate[n]['contact_support_2mm_count']=summary_number([x['arms'][n]['contact_support_2mm_face_center_count'] for x in rows])
    save(OUT/'summary.json',{'status':'COMPLETED_GEOMETRIC_PAIR_AND_SOURCE_QC_LAYER_SEMANTICS_UNRESOLVED','cases':420,'sources':84,'arms':aggregate,'all_prefix_and_targets_equal':True,'raw_sources_unchanged':True,'G_target_J':{k:summary_number([x['G_J_metric'][k] for x in rows]) for k in ('cover_1mm','cover_2mm','p95_mm')},'elapsed_seconds':time.monotonic()-START,'sampled_peak_rss_bytes':PEAK_RSS,'counted_output_bytes_before_summary':WRITTEN,'gpu_calls':0,'optimizer_updates':0,'training_ready':False,'GPU_validation_started':False,'limits':['Inner/outer anatomical identity unresolved; pooled native E includes all original exposed boundaries, not just outer skull','J metrics use exact discrete face-center area quadrature, not continuous triangle/face distance','Native E coverage uses fixed-seed 131072 area-sampled face centers; no convergence certification','Self-reference V1 geometry; descriptive representation QC, not proof of anatomical superiority','One sampling seed; no sampling uncertainty or trained model result','Resource budgets sampled at checkpoints, not hard isolation or continuous peak monitoring','No complete-P3, formal freeze audit, GPU or training authorization inferred']})
    print('COMPLETED_GEOMETRIC_QC',len(rows),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException:
        if OUT.is_dir() and not (OUT/'failure.json').exists():save(OUT/'failure.json',{'status':'FAILED_STOP_NO_AUTOMATIC_RETRY','traceback':traceback.format_exc(),'seconds':time.monotonic()-START})
        raise
