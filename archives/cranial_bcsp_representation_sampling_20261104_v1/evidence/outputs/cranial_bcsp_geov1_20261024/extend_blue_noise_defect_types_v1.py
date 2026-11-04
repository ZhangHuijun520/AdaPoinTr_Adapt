"""Same 12 opened SkullBreak sources, remaining four defects; no sampler edits."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_defect_types_20261103_v1';PRIOR=B/'blue_noise_surface_graph_expanded_20261103_v1'
import hashlib,importlib.util,json,sys,time,traceback
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
import psutil

START=time.monotonic();TYPES=['frontoorbital','parietotemporal','random_1','random_2']
WORKER=B/'expand_blue_noise_surface_graph_v1.py'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for v in iter(lambda:f.read(1048576),b''):h.update(v)
    return h.hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)

def selection():
    prior=json.loads((PRIOR/'protocol.json').read_text());sources=prior['universes']['SkullBreak']['selected_sources']
    assert len(sources)==12 and len(set(sources))==12
    root=B/'real_data_qc_v1';scope=json.loads((root/'scope.json').read_text())
    records=[json.loads(line) for line in (root/'manifest_8192.jsonl').read_text().splitlines()]
    assert len(records)==420
    cases=[]
    for defect in TYPES:
        for source in sources:
            rs=[r for r in records if r['source_id']==source and r['case_id'].endswith('__'+defect)]
            assert len(rs)==1;r=rs[0]
            assert r['case_id'] in scope['case_ids'] and r['source_id'] in scope['sources']
            p=root/'cases'/f"{r['case_id']}.json"
            cases.append({'case':'SkullBreak_'+r['case_id'],'dataset':'SkullBreak','source_id':source,'phase':'four_additional_types',
              'defect_type':defect,'raw':r['raw'],'normalization':r['normalization'],
              'point_file':str(root/r['point_path']),'point_sha256':r['sha256'],'target_array_sha256':r['target_array_sha256'],
              'metadata_case':str(p),'metadata_case_sha256':sha(p),'split':'opened_development'})
    assert len(cases)==48 and len({c['case'] for c in cases})==48
    return cases,sources

def run_worker(c):
    spec=importlib.util.spec_from_file_location('unchanged_expansion_worker',WORKER)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.O=O # Output location only. All point selection and geometry functions unchanged.
    result=m.worker(c)
    for row in result['rows']:row['defect_type']=c['defect_type']
    return result

def main():
    if O.exists():raise RuntimeError('new output only; no retry/resume')
    cases,sources=selection()
    prior=json.loads((PRIOR/'protocol.json').read_text());previous=json.loads((PRIOR/'completion.json').read_text())
    assert previous['status']=='COMPLETED_EXPANDED_GEOMETRY_ONLY'
    deps=[Path(__file__),WORKER,B/'blue_noise_real_surface_graph_v1.py',B/'blue_noise_pilot_v1.py',B/'real_data_qc_v1.py',
      PRIOR/'protocol.json',PRIOR/'completion.json',PRIOR/'metrics.json',B/'real_data_qc_v1/manifest_8192.jsonl',B/'real_data_qc_v1/scope.json']
    for p in [WORKER,B/'blue_noise_real_surface_graph_v1.py',B/'blue_noise_pilot_v1.py',B/'real_data_qc_v1.py']:
        assert sha(p)==prior['input_hashes'][str(p)]
    frozen={str(p):sha(p) for p in deps}
    for c in cases:
        assert sha(c['point_file'])==c['point_sha256'] and sha(c['metadata_case'])==c['metadata_case_sha256']
        frozen[c['point_file']]=c['point_sha256'];frozen[c['metadata_case']]=c['metadata_case_sha256']
        for role in ['defective','implant']:
            v=c['raw'][role];assert sha(v['path'])==v['sha256'];frozen[v['path']]=v['sha256']
    O.mkdir();(O/'cases').mkdir()
    dump(O/'protocol.json',{'status':'FROZEN_BEFORE_FOUR_TYPE_CHECK','cases':cases,'sources':sources,'defect_types':TYPES,
      'input_hashes':frozen,'N':8192,'pool_size':32768,'seeds':[0,1,2],
      'methods':['V1_common_pool','Euclidean_elimination','surface_graph'],
      'scientific_implementation':'exact prior worker, only output-root parameter rebound; no changes to core functions',
      'reuse':'12 bilateral cases reused from previous expanded metrics, no rerun',
      'reference':'same exact native face-center quadrature and physical area weights',
      'assessment':'per defect: mean three seeds within source; report12 source deltas, means, medians and regressions. Across types: mean5 defects within each source, no pseudo-replication',
      'decision_boundary':'do not hide a defect-specific regression in an overall mean; no new tuning or automatic training',
      'resources':{'workers':3,'overall_seconds':5400,'monitored_aggregate_RSS_GiB':8},
      'limitations':['already open selection data, not untouched confirmation','graph distance remains a conservative discretization','no anatomical inner/outer truth labels'],
      'prohibitions':['no new sources','no radius or weight changes','no GPU/model/server/training','no automatic repair/retry','no training request materialization']})
    prior_rows=[r for r in json.loads((PRIOR/'metrics.json').read_text()) if r['dataset']=='SkullBreak']
    assert len(prior_rows)==108 and {r['source_id'] for r in prior_rows}==set(sources)
    rows=[{**r,'defect_type':'bilateral','phase':'reused_bilateral'} for r in prior_rows]
    pool=ProcessPoolExecutor(max_workers=3);peak=0;results=[]
    try:
        pending={pool.submit(run_worker,c):c for c in cases}
        while pending:
            done,_=wait(pending,timeout=5,return_when=FIRST_COMPLETED)
            proc=psutil.Process();rss=proc.memory_info().rss
            for child in proc.children(recursive=True):
                try:rss+=child.memory_info().rss
                except psutil.NoSuchProcess:pass
            peak=max(peak,rss)
            if rss>8*1024**3 or time.monotonic()-START>5400:raise RuntimeError('90min / monitored8GiB aggregate budget')
            for future in done:
                result=future.result();results.append(result);pending.pop(future);rows.extend(result['rows'])
                print('TYPE_CHECK_PROGRESS',len(results),'/48',result['case'],flush=True)
    except BaseException:
        for p in pool._processes.values():p.terminate()
        pool.shutdown(wait=True,cancel_futures=True);raise
    else:pool.shutdown(wait=True)
    assert len(rows)==540 and len({r['case'] for r in rows})==60
    assert all(sha(p)==h for p,h in frozen.items())
    dump(O/'metrics.json',rows)
    dump(O/'completion.json',{'status':'COMPLETED_ALL_FIVE_DEFECT_GEOMETRY_ONLY','sources':12,'new_cases':48,'reused_bilateral_cases':12,
      'total_cases':60,'metric_rows':540,'new_sample_files':432,'seconds':time.monotonic()-START,
      'monitored_aggregate_RSS_peak_bytes':peak,'scientific_core_and_inputs_unchanged':True,
      'no_radius_or_weight_changes':True,'no_GPU_model_server_calls':True,'no_training_request_created':True})
    dump(O/'contents.json',{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file()})
    print('ALL_TYPES_COMPLETE',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'failure.json').exists():dump(O/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(e),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
