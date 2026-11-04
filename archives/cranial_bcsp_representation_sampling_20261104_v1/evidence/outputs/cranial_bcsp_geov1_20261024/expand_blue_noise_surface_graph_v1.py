"""Frozen 12-source/dataset expansion; reuse prior six; 18 new cases, CPU only."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_surface_graph_expanded_20261103_v1';PRIOR=B/'blue_noise_real_surface_graph_20261103_v1'
import csv,gc,hashlib,importlib.util,json,sys,time,traceback
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
import numpy as np
import psutil
START=time.monotonic()
METHODS=['V1_common_pool','Euclidean_elimination','surface_graph']

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def npz(p,**x):
    with p.open('xb') as f:np.savez_compressed(f,**x)
def module(name,p):
    sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m

def selection():
    selected=[];universes={};metadata=[]
    for ds,root in [('SkullFix',B/'skullfix_surface_points_20261103_v1'),('SkullBreak',B/'real_data_qc_v1')]:
        mf=root/'manifest_8192.jsonl';scopep=root/'scope.json';scope=json.loads(scopep.read_text(encoding='utf-8'))
        rows=[json.loads(line) for line in mf.read_text(encoding='utf-8').splitlines()]
        if ds=='SkullBreak':rows=[r for r in rows if r['case_id'].endswith('__bilateral')]
        assert len(rows)==(90 if ds=='SkullFix' else 84)
        assert len({r['source_id'] for r in rows})==len(rows)
        for r in rows:
            if ds=='SkullFix':assert r['case_id'] in scope['source_ids'] and r['case_id'] not in scope['excluded_internal_test_ids']
            else:assert r['case_id'] in scope['case_ids'] and r['source_id'] in scope['sources']
        anchors=[r for r in rows if r['case_id'] in ['002','003','004','train__000__bilateral','train__001__bilateral','train__002__bilateral']]
        assert len(anchors)==3
        def rank(r):return hashlib.sha256(('blue_noise_expansion_20261103_v1|'+ds+'|'+r['source_id']).encode()).hexdigest()
        chosen=anchors+sorted([r for r in rows if r not in anchors],key=rank)[:9]
        universes[ds]={'sources':len(rows),'selection_key':'sha256(blue_noise_expansion_20261103_v1|dataset|source_id)',
                       'selected_sources':[r['source_id'] for r in chosen]}
        for r in chosen:
            prior_case=root/'cases'/f"{r['case_id']}.json"
            selected.append({'case':ds+'_'+r['case_id'],'dataset':ds,'source_id':r['source_id'],
              'phase':'prior_six' if r in anchors else 'new_expansion','raw':r['raw'],'normalization':r['normalization'],
              'point_file':str(root/r['point_path']),'point_sha256':r['sha256'],'target_array_sha256':r['target_array_sha256'],
              'metadata_case':str(prior_case),'metadata_case_sha256':sha(prior_case),'split':r.get('split','opened_development')})
        metadata.extend([mf,scopep])
    assert len(selected)==24 and sum(c['phase']=='new_expansion' for c in selected)==18
    return selected,universes,metadata

def worker(c):
    # Frozen scientific functions imported without running their six-case main().
    gm=module('frozen_graph_core',B/'blue_noise_real_surface_graph_v1.py')
    ep=module('frozen_euclidean_core',B/'blue_noise_pilot_v1.py')
    cid=c['case'];out=O/'cases'/cid;out.mkdir();(out/'samples').mkdir()
    begin=time.monotonic();print('CASE_BEGIN',cid,flush=True)
    D,A,o=gm.sb.raw.read_mask(Path(c['raw']['defective']['path']));spacing=np.linalg.norm(A,axis=1)
    assert np.max(np.abs((A/spacing[:,None])@(A/spacing[:,None]).T-np.eye(3)))<1e-8
    s=gm.sb.surface(D);graph,nb,x,info=gm.surface_graph(s,A,o,D.shape);_,w=gm.sb.face_geometry(s,A,o)
    R=2*np.sqrt(w.sum()/8192);sets=[];paths=[]
    for seed in [0,1,2]:
        p,fids,_,_=gm.sb.sample(s,A,o,seed,32768)
        base=np.arange(8192);oldidx,_=ep.eliminate(p,float(w.sum()),8192)
        tree=gm.cKDTree(p);count=(int(tree.count_neighbors(tree,R))-len(p))//2
        if count>8000000:raise RuntimeError('8M pool pair bound')
        pairs=tree.query_pairs(R,output_type='ndarray')
        dist,pi=gm.bounded_paths(p,fids,pairs,graph,nb,x,s,A,o,R,spacing)
        newidx=gm.eliminate(pairs,dist,len(p),R)
        for method,idx in zip(METHODS,[base,oldidx,newidx]):
            assert len(idx)==8192 and len(np.unique(idx))==8192
            npz(out/'samples'/f'seed{seed}_{method}.npz',xyz=p[idx],face_ids=fids[idx],pool_indices=idx)
        sets.append((seed,p,fids,[base,oldidx,newidx]));paths.append({'seed':seed,**pi})
        print('SEED_DONE',cid,seed,flush=True);del pairs,dist;gc.collect()
    # Persist all nine input sets before this case's G payload is decoded.
    G,F,f=gm.sb.raw.read_mask(Path(c['raw']['implant']['path']))
    assert G.shape==D.shape and np.array_equal(A,F) and np.array_equal(o,f) and not(D&G).any()
    J=gm.sb.contact(s,G);assert J.any() and (~J).any();rows=[]
    for seed,p,fids,indices in sets:
        for method,idx in zip(METHODS,indices):
            row={'case':cid,'dataset':c['dataset'],'source_id':c['source_id'],'phase':c['phase'],'seed':seed,'method':method,'count':8192,'regions':{}}
            for name,tag in [('J',J),('E',~J)]:
                same=tag[fids[idx]];assert same.any()
                row['regions'][name]={'point_count':int(same.sum()),'unrestricted':gm.metric(x[tag],w[tag],p[idx]),
                  'same_region':gm.metric(x[tag],w[tag],p[idx[same]])}
            rows.append(row)
    result={'case':cid,'rows':rows,'geometry':{'R':float(R),**info,'path_diagnostics':paths},
      'seconds':time.monotonic()-begin,'graph_checkpoint_peak_RSS_bytes':gm.PEAK,'all_nine_inputs_saved_before_G_decode':True}
    dump(out/'result.json',result)
    print('CASE_COMPLETE',cid,round(result['seconds'],1),flush=True)
    return result

def main():
    if O.exists():raise RuntimeError('new version output only; no resume')
    cases,universes,metadata=selection();prior_protocol=json.loads((PRIOR/'protocol.json').read_text())
    dependencies=[Path(__file__),B/'blue_noise_real_surface_graph_v1.py',B/'blue_noise_pilot_v1.py',B/'real_data_qc_v1.py',
      PRIOR/'protocol.json',PRIOR/'metrics.json',PRIOR/'summary.json',*metadata]
    # All previous scientific implementation identities must remain unchanged.
    for p,h in prior_protocol['source_hashes'].items():assert sha(p)==h
    frozen={str(p):sha(p) for p in dependencies}
    for c in cases:
        assert sha(c['point_file'])==c['point_sha256'] and sha(c['metadata_case'])==c['metadata_case_sha256']
        frozen[c['point_file']]=c['point_sha256'];frozen[c['metadata_case']]=c['metadata_case_sha256']
        for role in ['defective','implant']:
            v=c['raw'][role];assert sha(v['path'])==v['sha256'];frozen[v['path']]=v['sha256']
    O.mkdir();(O/'cases').mkdir()
    dump(O/'protocol.json',{'status':'FROZEN_BEFORE_EXPANDED_GEOMETRY','cases':cases,'universes':universes,'input_hashes':frozen,
      'N':8192,'pool_size':32768,'seeds':[0,1,2],'methods':METHODS,
      'scope':'12 sources per dataset, original3+hash-ranked9; SkullBreak bilateral only; all already open',
      'reuse':'six original cases reused, not rerun; compare new9/dataset separately from all12',
      'unchanged_science':'same original quad graph, ambiguity blocking, endpoint approximation, exponent8, R=2sqrt(area/N), no extra weights',
      'reference':'all native exposed-face centers, original physical area weights; same-region and unrestricted',
      'aggregation':'average seeds within source; source equal within dataset; paired descriptive signs, means and medians; no formal gate/bootstrap',
      'limitations':['open data used for method selection, not untouched confirmation','bilateral-only SkullBreak scope','no reliable anatomical inner/outer labels','conservative graph distance is not exact geodesic'],
      'execution':{'CPU_process_workers':3,'overall_seconds':2700,'worker_original_budget_seconds':1800,'monitored_total_RSS_GiB':8},
      'prohibitions':['no sealed/test or new dataset payload','no model/GPU/server/training','no tuning radius/weights','no automatic failure repair or retry']})
    prior=json.loads((PRIOR/'metrics.json').read_text());results=[]
    for c in cases:
        if c['phase']=='prior_six':
            rows=[{**r,'dataset':c['dataset'],'source_id':c['source_id'],'phase':'prior_six'} for r in prior if r['case']==c['case']]
            assert len(rows)==9;results.append({'case':c['case'],'rows':rows,'reused':True})
    todo=[c for c in cases if c['phase']=='new_expansion'];peak_total=0
    pool=ProcessPoolExecutor(max_workers=3)
    try:
        pending={pool.submit(worker,c):c for c in todo}
        while pending:
            done,_=wait(pending,timeout=5,return_when=FIRST_COMPLETED)
            proc=psutil.Process();total=proc.memory_info().rss
            for child in proc.children(recursive=True):
                try:total+=child.memory_info().rss
                except psutil.NoSuchProcess:pass
            peak_total=max(peak_total,total)
            if total>8*1024**3 or time.monotonic()-START>2700:raise RuntimeError('45min / aggregate monitored8GiB budget')
            for future in done:
                result=future.result();results.append(result);pending.pop(future)
                print('EXPANSION_PROGRESS',len(results)-6,'/18',result['case'],flush=True)
    except BaseException:
        for p in pool._processes.values():p.terminate()
        pool.shutdown(wait=True,cancel_futures=True);raise
    else:pool.shutdown(wait=True)
    rows=[r for result in results for r in result['rows']];assert len(rows)==216
    assert all(sha(p)==h for p,h in frozen.items())
    dump(O/'metrics.json',rows);dump(O/'completion.json',{'status':'COMPLETED_EXPANDED_GEOMETRY_ONLY','cases':24,'sources_per_dataset':12,
      'new_cases':18,'reused_cases':6,'rows':216,'new_sample_files':162,'seconds':time.monotonic()-START,
      'monitored_aggregate_RSS_peak_bytes':peak_total,'all_inputs_unchanged':True,'production_core_unchanged':True,
      'no_model_GPU_server_calls':True,'no_tuning_or_retries':True})
    dump(O/'contents.json',{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file()})
    print('EXPANSION_COMPLETE',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'failure.json').exists():dump(O/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(e),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
