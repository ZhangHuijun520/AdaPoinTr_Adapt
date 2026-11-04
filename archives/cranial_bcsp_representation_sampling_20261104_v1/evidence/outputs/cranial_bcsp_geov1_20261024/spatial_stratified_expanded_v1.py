# -*- coding: utf-8 -*-
"""One local CPU expansion of the frozen sampler. No model/server or tuning."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
import csv,gc,hashlib,importlib.util,json,sys,threading,time,traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import psutil
from scipy.spatial import cKDTree
B=Path(__file__).resolve().parent;O=B/'spatial_stratified_expanded_20261103_v1'
SF=B/'skullfix_surface_points_20261103_v1';SB=B/'real_data_qc_v1'
START=time.monotonic();PEAK=0;STOP=threading.Event();LOCK=threading.Lock()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pilot=module('frozen_pilot',B/'spatial_stratified_pilot_v1.py');sb=pilot.sb
def guard():
    global PEAK
    if STOP.is_set():raise RuntimeError('batch cancelled after first failure')
    rss=psutil.Process().memory_info().rss
    with LOCK:PEAK=max(PEAK,rss)
    if time.monotonic()-START>5400 or rss>8*1024**3:
        STOP.set();raise RuntimeError('90 minute / 8 GiB monitored process budget exceeded')
sb.guard=guard
def metric(d,w):return pilot.metrics(d,w)
def query(tree,x):
    parts=[]
    for a in range(0,len(x),65536):guard();parts.append(tree.query(x[a:a+65536],workers=1)[0])
    return np.concatenate(parts)
def npz(p,**arrays):
    with p.open('xb') as f:np.savez_compressed(f,**arrays)
def samplefile(cid,seed,method):return O/'samples'/f'{cid}_seed{seed}_{method}.npz'

def prepare_cases():
    cases=[]
    folds=json.loads((B/'consolidated_binding_v1/fold_binding.json').read_text(encoding='utf-8'))['folds']
    sf_scope=json.loads((SF/'scope.json').read_text(encoding='utf-8'))
    sb_scope=json.loads((SB/'scope.json').read_text(encoding='utf-8'))
    for dataset,root in [('SkullFix',SF),('SkullBreak',SB)]:
        records=[json.loads(x) for x in (root/'manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()]
        for r in records:
            rawid=r['case_id'];cid=dataset+'_'+rawid
            oldpath=root/'cases'/f'{rawid}.json';old=json.loads(oldpath.read_text(encoding='utf-8'))
            if dataset=='SkullFix':
                assert rawid in sf_scope['source_ids'] and rawid not in sf_scope['excluded_internal_test_ids']
                facecount=old['D']['J_faces'];area=old['D']['J_area_mm2'];split=r['split'];fold_roles={}
            else:
                assert rawid in sb_scope['case_ids'] and r['source_id'] in sb_scope['sources']
                facecount=old['J_face_keys_paired'];area=old['D_J_area_mm2'];split='opened_development'
                fold_roles={f:('train' if r['source_id'] in v['train_sources'] else 'dev' if r['source_id'] in v['dev_sources'] else 'excluded') for f,v in folds.items()}
                assert 'excluded' not in fold_roles.values()
            cases.append({'id':cid,'dataset':dataset,'raw_case_id':rawid,'source_id':r['source_id'],'split':split,
                'defect_type':old.get('defect_type','single_fixed_defect'),'fold_roles':fold_roles,
                'raw':r['raw'],'point_file':str(root/r['point_path']),'point_sha256':r['sha256'],
                'target_array_sha256':r['target_array_sha256'],'normalization':r['normalization'],
                'prior_case_file':str(oldpath),'prior_case_sha256':sha(oldpath),
                'expected_J_faces':facecount,'expected_J_area':area,
                'inherited_warnings':old.get('prior_geometry_warnings',old.get('warnings',[]))})
    assert len(cases)==510 and sum(c['dataset']=='SkullFix' for c in cases)==90
    assert len({c['source_id'] for c in cases if c['dataset']=='SkullBreak'})==84
    assert all(sum(c['source_id']==s for c in cases if c['dataset']=='SkullBreak')==5 for s in sb_scope['sources'])
    return cases

def case_run(c,full_review=False):
    try:return _case_run(c,full_review)
    except BaseException:
        STOP.set();raise
def _case_run(c,full_review):
    guard();begin=time.monotonic();cid=c['id'];raw={k:Path(v['path']) for k,v in c['raw'].items()}
    D,A,o=sb.raw.read_mask(raw['defective']);s=sb.surface(D);x,w=sb.face_geometry(s,A,o)
    if full_review:
        saved=json.loads((O/'cases'/f'{cid}.json').read_text(encoding='utf-8'))
        results=[]
        # Re-evaluate saved inputs only: no resampling, no GT-based selection.
        G,F,f=sb.raw.read_mask(raw['implant']);assert np.array_equal(A,F) and np.array_equal(o,f)
        J=sb.contact(s,G)
        for r in saved['metrics']:
            p=O/r['sample_path'];assert sha(p)==r['sample_sha256']
            with np.load(p,allow_pickle=False) as z:points=z['xyz']
            d=query(cKDTree(points),x)
            results.append({'seed':r['seed'],'method':r['method'],'J':metric(d[J],w[J]),'E':metric(d[~J],w[~J]),'all':metric(d,w)})
        dump(O/'full_reference_review'/f'{cid}.json',{'case':cid,'metrics':results,'seconds':time.monotonic()-begin,'resampling_calls':0})
        return {'case':cid,'metrics':results}
    center,scale=sb.frame(D,A,o)
    assert np.array_equal(center,np.array(c['normalization']['center'])) and scale==c['normalization']['scale']
    assert sha(c['point_file'])==c['point_sha256']
    with np.load(c['point_file'],allow_pickle=False) as original:
        base_partial=original['partial'].copy()
        assert hashlib.sha256(original['implant'].tobytes()).hexdigest()==c['target_array_sha256']
    samples=[]
    for seed in [0,1,2]:
        for method in ['uniform8k','Morton_area_stratified8k']:
            t=time.monotonic()
            if method=='uniform8k':
                p,ids,_,_=sb.sample(s,A,o,seed,16384);p=p[:8192];ids=ids[:8192]
            else:p,ids=pilot.stratified(s,A,o,seed)
            sec=time.monotonic()-t;pilot.membership(p,s,ids,A,o)
            partial=((p-center)/scale).astype(np.float32)
            assert np.isfinite(partial).all() and partial.shape==(8192,3)
            if seed==0 and method=='uniform8k':assert np.array_equal(partial,base_partial)
            path=samplefile(cid,seed,method);npz(path,xyz=p,partial=partial,face_ids=ids.astype(np.int32),center=center,scale=np.array(scale))
            samples.append((seed,method,p,ids,sec,path,sha(path)));guard()
    # All three paired seeds are on disk before G decode. Complete C is hash-bound
    # to existing partition QC and is not decoded afresh in this geometry comparison.
    G,F,f=sb.raw.read_mask(raw['implant']);assert G.shape==D.shape and np.array_equal(A,F) and np.array_equal(o,f) and not(D&G).any()
    J=sb.contact(s,G);assert J.sum()==c['expected_J_faces'] and np.isclose(w[J].sum(),c['expected_J_area'],rtol=1e-10)
    ff=pilot.fov(s,D.shape);eids=np.flatnonzero(~J);earea=float(w[eids].sum())
    refids=np.random.default_rng(99173).choice(eids,131072,p=w[eids]/earea)
    ew=np.full(len(refids),earea/len(refids));jw=w[J]
    reference=np.concatenate([x[J],x[refids]]);weights=np.concatenate([jw,ew]);nj=int(J.sum())
    row=[];labels={}
    for seed,method,p,ids,sec,path,digest in samples:
        dist=query(cKDTree(p),reference);nn=cKDTree(p).query(p,k=2,workers=1)[0][:,1]
        support=query(cKDTree(x[J]),p)<=2
        row.append({'seed':seed,'method':method,'J':metric(dist[:nj],jw),'E_MC':metric(dist[nj:],ew),'all_mixed_quadrature':metric(dist,weights),
            'J_face_point_count':int(J[ids].sum()),'support_2mm_center_reference_count':int(support.sum()),
            'NN_median_mm':float(np.median(nn)),'NN_p05_mm':float(np.percentile(nn,5)),
            'NN_fraction_lt_0_5mm':float(np.mean(nn<.5)),'FOV_sample_count':int(ff[ids].sum()),
            'sampling_seconds':sec,'sample_path':str(path.relative_to(O)).replace('\\','/'),'sample_sha256':digest})
        labels[f'{method}_seed{seed}_J']=J[ids];labels[f'{method}_seed{seed}_FOV']=ff[ids]
    npz(O/'diagnostics'/f'{cid}.npz',**labels)
    out={**c,'metrics':row,'J_area_fraction':float(w[J].sum()/w.sum()),'FOV_area_fraction':float(w[ff].sum()/w.sum()),
        'D_boundary_faces':len(x),'J_faces':nj,'all_inputs_saved_before_G_decode':True,
        'seed0_existing_input_reproduced':True,'target_array_hash_verified':True,
        'complete_C_partition_QC_inherited_via_unchanged_hash_not_redecoded':True,'seconds':time.monotonic()-begin}
    dump(O/'cases'/f'{cid}.json',out);guard()
    return out

def parallel(cases,review=False):
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending={pool.submit(case_run,c,review):c for c in cases}
        try:
            for future in as_completed(pending):
                result=future.result();results.append(result)
                print(('REVIEW' if review else 'DONE'),f'{len(results)}/{len(cases)}',pending[future]['id'],flush=True)
                guard()
        except BaseException:
            STOP.set()
            for f in pending:f.cancel()
            raise
    return sorted(results,key=lambda r:r.get('id',r.get('case')))

def main():
    cases=prepare_cases()
    old=json.loads((B/'spatial_stratified_pilot_20261103_v1/frozen_protocol.json').read_text(encoding='utf-8'))
    assert sha(B/'spatial_stratified_pilot_v1.py')==old['source_and_implementation_sha256'][str(B/'spatial_stratified_pilot_v1.py')]
    raw={v['path']:v['sha256'] for c in cases for v in c['raw'].values()}
    assert len(raw)==1194
    for p,h in raw.items():assert sha(p)==h
    deps=[Path(__file__),B/'spatial_stratified_pilot_v1.py',B/'real_data_qc_v1.py',sb.READER,sb.LOCK,
        B/'spatial_stratified_pilot_20261103_v1/frozen_protocol.json',SF/'manifest_8192.jsonl',SB/'manifest_8192.jsonl',SF/'scope.json',SB/'scope.json',B/'consolidated_binding_v1/fold_binding.json']
    frozen={str(p):sha(p) for p in deps}
    O.mkdir(exist_ok=False)
    for sub in ['samples','cases','diagnostics','full_reference_review']:(O/sub).mkdir()
    dump(O/'frozen_protocol.json',{'status':'FROZEN_BEFORE_EXPANDED_SAMPLING','date':'2026-11-03','cases':cases,
      'raw_hashes':raw,'implementation_metadata_hashes':frozen,'candidate_changed':False,'seeds':[0,1,2],'input':8192,'target':8192,
      'reference':{'J':'all native J face centers, world area weighting','E':'131072 area-IID sampled native E centers, seed99173 shared across methods/seeds',
        'all':'exact J plus MC E with total physical area weights; approximation','posthoc_review':'full native E/all re-evaluation of saved inputs, no resampling'},
      'review_selection':'worst10 case means J Cover2 per dataset, plus SF004/018/062 and all six pilot cases; deduplicated',
      'review_rule_frozen_before_results':True,'aggregation':'average seeds within defect, then five defects within SkullBreak source; source equal by dataset; no pooled independence claim',
      'selection_caution':'all sources already opened; exploratory data not independent confirmation',
      'limits':{'seconds':5400,'process_RSS_checkpoint_bytes':8*1024**3,'output_bytes':2*1024**3,'concurrent_CPU_workers':4},
      'prohibitions':['no sealed/test payload','no geometry or targets change','no sampler tuning/retries','no models/GPU/server/training']})
    results=parallel(cases);dump(O/'all_case_results.json',results)
    def delta(r):
        a=np.mean([m['J']['cover_2mm'] for m in r['metrics'] if m['method']=='uniform8k'])
        b=np.mean([m['J']['cover_2mm'] for m in r['metrics'] if m['method']=='Morton_area_stratified8k'])
        return float(b-a)
    chosen=set()
    for ds in ['SkullFix','SkullBreak']:
        chosen.update(r['id'] for r in sorted([r for r in results if r['dataset']==ds],key=lambda r:(delta(r),r['id']))[:10])
    chosen.update(['SkullFix_004','SkullFix_018','SkullFix_062','SkullFix_002','SkullFix_003']+[f'SkullBreak_train__{c}__bilateral' for c in ['000','001','002']])
    selected=[c for c in cases if c['id'] in chosen]
    dump(O/'full_reference_review_selection.json',{'status':'SELECTED_BY_FROZEN_WORST_CASE_RULE','cases':sorted(chosen),
        'source_case_mean_J_deltas':{r['id']:delta(r) for r in results if r['id'] in chosen}})
    review=parallel(selected,True);dump(O/'full_reference_review_results.json',review)
    for p,h in raw.items():assert sha(p)==h
    for p,h in frozen.items():assert sha(p)==h
    for c in cases:
        assert sha(c['point_file'])==c['point_sha256'] and sha(c['prior_case_file'])==c['prior_case_sha256']
    bytes_out=sum(p.stat().st_size for p in O.rglob('*') if p.is_file());assert bytes_out<2*1024**3
    dump(O/'completion.json',{'status':'COMPLETED_EXPLORATORY_GEOMETRY_NOT_MODEL_AUTHORIZATION','cases':510,'SkullFix_sources':90,'SkullBreak_sources':84,'SkullBreak_defects':420,
      'metric_rows':3060,'sample_files':3060,'full_reference_review_cases':len(review),
      'raw_files_unchanged':1194,'targets_and_existing_inputs_unchanged':True,'candidate_implementation_unchanged':True,
      'seeds':[0,1,2],'seconds':time.monotonic()-START,'checkpoint_peak_RSS_bytes':PEAK,'output_bytes_before_summary':bytes_out,
      'GPU_forward_training_calls':0,'no_automatic_retry':True})
    print('EXPANDED_COMPLETED',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'failure.json').exists():dump(O/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(e),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
