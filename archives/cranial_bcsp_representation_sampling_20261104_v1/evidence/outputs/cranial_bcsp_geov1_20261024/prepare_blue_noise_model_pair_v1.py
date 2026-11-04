"""Prepare Fold C train/dev E/G data, same seed0 pool and frozen scientific cores.
No model, GPU, server, training request or launcher. Reuse60, generate360.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1'
MASTER=B/'real_data_qc_v1';PREV=B/'sampling_model_AB_foldC_seed0_20261103_v1';CHECK=B/'blue_noise_defect_types_20261103_v1'
import gc,hashlib,importlib.util,json,sys,time,traceback
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
import numpy as np
import psutil
START=time.monotonic();ARMS=['Euclidean_elimination','surface_graph'];STAGE='BCSP_BLUE_NOISE_AB_V1'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for v in iter(lambda:f.read(1048576),b''):h.update(v)
    return h.hexdigest()
def arrsha(a):return hashlib.sha256(a.tobytes()).hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def npz(p,**x):
    with p.open('xb') as f:np.savez_compressed(f,**x)
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def permutation(cid):
    # Identical existing point-order policy; no new ordering confound.
    digest=hashlib.sha256(('BCSP_SAMPLING_AB_V1|point-order|'+cid).encode('ascii')).digest()
    return np.random.Generator(np.random.PCG64(int.from_bytes(digest[:8],'big'))).permutation(8192)

def selection():
    folds=json.loads((B/'consolidated_binding_v1/fold_binding.json').read_text());fold=folds['folds']['C']
    scope=json.loads((MASTER/'scope.json').read_text())
    records=[json.loads(line) for line in (MASTER/'manifest_8192.jsonl').read_text().splitlines()]
    by={r['case_id']:r for r in records};train=fold['train_case_ids'];dev=fold['dev_case_ids']
    assert len(train)==315 and len(dev)==105 and len(set(train+dev))==420
    assert set(train+dev)==set(by)==set(scope['case_ids'])
    assert len(fold['train_sources'])==63 and len(fold['dev_sources'])==21 and not(set(fold['train_sources'])&set(fold['dev_sources']))
    assert folds['confirmation_count_excluded']==20
    manifests={}
    roots=[CHECK,B/'blue_noise_surface_graph_expanded_20261103_v1',B/'blue_noise_real_surface_graph_20261103_v1',B/'blue_noise_pilot_20261103_v1']
    for root in roots:
        manifests[str(root)]={k.replace('\\','/'):v for k,v in json.loads((root/'contents.json').read_text()).items()}
    cases=[]
    for cid in train+dev:
        r=by[cid];full='SkullBreak_'+cid;cached={}
        split='train' if cid in train else 'development'
        assert r['source_id'] in fold['train_sources' if split=='train' else 'dev_sources']
        for arm in ARMS:
            for root in roots:
                patterns=[f'cases/{full}/samples/seed0_{arm}.npz',f'samples/{full}_seed0_{arm}.npz']
                hit=next((rel for rel in patterns if rel in manifests[str(root)]),None)
                if hit:
                    cached[arm]={'path':str(root/hit),'sha256':manifests[str(root)][hit]['sha256']};break
        assert len(cached) in [0,2]
        cases.append({'case_id':cid,'source_id':r['source_id'],'split':split,'record':r,
          'master_point_file':str(MASTER/r['point_path']),'cached':cached})
    assert sum(bool(c['cached']) for c in cases)==60
    return cases,folds

def worker(c):
    gm=module('frozen_blue_graph_core',B/'blue_noise_real_surface_graph_v1.py')
    ep=module('frozen_blue_euclidean_core',B/'blue_noise_pilot_v1.py')
    begin=time.monotonic();cid=c['case_id'];r=c['record'];print('DATA_BEGIN',cid,'reuse' if c['cached'] else 'generate',flush=True)
    D,A,o=gm.sb.raw.read_mask(Path(r['raw']['defective']['path']));spacing=np.linalg.norm(A,axis=1)
    assert np.max(np.abs((A/spacing[:,None])@(A/spacing[:,None]).T-np.eye(3)))<1e-8
    center,scale=gm.sb.frame(D,A,o)
    assert np.array_equal(center,np.array(r['normalization']['center'])) and scale==r['normalization']['scale']
    s=gm.sb.surface(D);pool,fids,x,w=gm.sb.sample(s,A,o,0,32768);R=2*np.sqrt(w.sum()/8192)
    indices={};geometry=None
    if c['cached']:
        for arm in ARMS:
            spec=c['cached'][arm];assert sha(spec['path'])==spec['sha256']
            with np.load(spec['path'],allow_pickle=False) as z:
                ix=z['pool_indices'].copy();assert np.array_equal(pool[ix],z['xyz'])
            indices[arm]=ix
    else:
        indices[ARMS[0]],_=ep.eliminate(pool,float(w.sum()),8192)
        graph,nb,x,topology=gm.surface_graph(s,A,o,D.shape)
        tree=gm.cKDTree(pool);pairs_n=(int(tree.count_neighbors(tree,R))-32768)//2
        if pairs_n>8000000:raise RuntimeError('frozen8M pool-pair limit')
        pairs=tree.query_pairs(R,output_type='ndarray')
        dist,path=gm.bounded_paths(pool,fids,pairs,graph,nb,x,s,A,o,R,spacing)
        indices[ARMS[1]]=gm.eliminate(pairs,dist,32768,R)
        geometry={**topology,'paths':path};del graph,nb,pairs,dist;gc.collect()
    for ix in indices.values():assert len(ix)==8192 and len(np.unique(ix))==8192 and ix.min()>=0 and ix.max()<32768
    raw={arm:pool[ix] for arm,ix in indices.items()}
    selection_path=O/'source_selections'/f'{cid}.npz'
    # Selection is persisted before target payload is loaded; no G/J in selection interfaces.
    npz(selection_path,Euclidean_xyz=raw[ARMS[0]],graph_xyz=raw[ARMS[1]],Euclidean_pool_indices=indices[ARMS[0]],graph_pool_indices=indices[ARMS[1]],
      center=center,scale=np.array(scale),pool_sha256=np.array(arrsha(pool)))
    assert sha(c['master_point_file'])==r['sha256']
    with np.load(c['master_point_file'],allow_pickle=False) as z:target=z['implant'].copy()
    assert target.shape==(8192,3) and target.dtype==np.float32 and np.isfinite(target).all() and arrsha(target)==r['target_array_sha256']
    perm=permutation(cid);permhash=arrsha(perm.astype('<i8'));records={};partialhash={}
    for arm in ARMS:
        normalized=((raw[arm]-center)/scale).astype(np.float32);partial=normalized[perm].copy()
        assert partial.shape==(8192,3) and partial.dtype==np.float32 and np.isfinite(partial).all()
        path=O/arm/'points'/f'{cid}_8192.npz';npz(path,partial=partial,implant=target)
        with np.load(path,allow_pickle=False) as z:
            assert set(z.files)=={'partial','implant'} and np.array_equal(z['partial'],partial) and np.array_equal(z['implant'],target)
            assert np.array_equal(z['partial'][np.argsort(perm)],normalized)
        partialhash[arm]=arrsha(normalized)
        records[arm]={**r,'point_path':str(path.relative_to(O/arm)).replace('\\','/'),'sha256':sha(path),'sampler_arm':arm,
          'comparison_stage':STAGE,'comparison_split':c['split'],'sampling_seed':0,'common_point_order_sha256':permhash,
          'source_point_file':str(selection_path),'source_point_sha256':sha(selection_path)}
    pair={'case_id':cid,'source_id':r['source_id'],'target_array_sha256':r['target_array_sha256'],'normalization':r['normalization'],
      'common_permutation_sha256':permhash,'original_partial_array_sha256':partialhash,'selection_path':str(selection_path.relative_to(O)),
      'selection_sha256':sha(selection_path),'reused_frozen_geometry':bool(c['cached'])}
    result={'case_id':cid,'split':c['split'],'records':records,'pair':pair,'geometry':geometry,'R':float(R),
      'sampling_seed':0,'selection_saved_before_target_decode':True,'seconds':time.monotonic()-begin}
    dump(O/'case_receipts'/f'{cid}.json',result);print('DATA_COMPLETE',cid,round(result['seconds'],1),flush=True)
    return result

def main():
    if O.exists():raise RuntimeError('new output only; no automatic resume/retry')
    cases,folds=selection();fold=folds['folds']['C']
    prior=json.loads((CHECK/'protocol.json').read_text())
    cores=[B/'blue_noise_real_surface_graph_v1.py',B/'blue_noise_pilot_v1.py',B/'real_data_qc_v1.py']
    for p in cores:assert sha(p)==prior['input_hashes'][str(p)]
    deps=[Path(__file__),*cores,CHECK/'protocol.json',CHECK/'completion.json',B/'consolidated_binding_v1/fold_binding.json',
      MASTER/'manifest_8192.jsonl',MASTER/'scope.json',PREV/'static_training_config_v1.json',PREV/'shared_order_foldC_seed0_v1.json']
    frozen={str(p):sha(p) for p in deps}
    for c in cases:
        r=c['record'];assert sha(c['master_point_file'])==r['sha256'];frozen[c['master_point_file']]=r['sha256']
        v=r['raw']['defective'];assert sha(v['path'])==v['sha256'];frozen[v['path']]=v['sha256']
        for v in c['cached'].values():assert sha(v['path'])==v['sha256'];frozen[v['path']]=v['sha256']
    order=json.loads((PREV/'shared_order_foldC_seed0_v1.json').read_text())
    assert order['case_ids']==fold['train_case_ids'] and len(order['epochs'])==100
    assert all(len(e['batches'])==39 and len(e['dropped'])==3 and all(len(b)==8 for b in e['batches']) for e in order['epochs'])
    O.mkdir();(O/'source_selections').mkdir();(O/'case_receipts').mkdir()
    for arm in ARMS:(O/arm/'points').mkdir(parents=True)
    dump(O/'preparation_protocol.json',{'status':'FROZEN_BEFORE_DATA_PREPARATION','stage':STAGE,'cases':cases,'input_hashes':frozen,
      'fold':'C','train_cases':315,'train_sources':63,'development_cases':105,'development_sources':21,'arms':ARMS,
      'input':8192,'target':8192,'pool':32768,'sampling_seed':0,'reused_cases':60,'new_geometry_cases':360,
      'scientific_rules':'unchanged E/G kernels, radius formula and original surface graph; no GT-assisted input selection',
      'point_order':'existing SHA256 BCSP_SAMPLING_AB_V1|point-order|case_id -> PCG64 permutation8192, same for both arms',
      'target':'unchanged existing normalized8192 missing-bone complete-boundary target; source-file and array hash checked',
      'training_policy':'both scratch seed0, identical initialization fingerprints and frozen order required at execution; not initialized here',
      'counts':{'batch':8,'traversals':100,'updates':3900,'exposures':31200,'drops':300},
      'resources':{'workers':4,'overall_seconds':10800,'monitored_total_RSS_GiB':8},
      'prohibitions':['no model/GPU/server/deployment','no training/evaluation/BNCal','no runtime/launcher/authorization receipt','no sampler tuning','no automatic failure retry']})
    # Reused cases first to establish paired-data plumbing without repeating graph calculations.
    todo=sorted(cases,key=lambda c:(not bool(c['cached']),c['case_id']));pool=ProcessPoolExecutor(max_workers=4);results=[];peak=0
    try:
        pending={pool.submit(worker,c):c for c in todo}
        while pending:
            done,_=wait(pending,timeout=5,return_when=FIRST_COMPLETED)
            proc=psutil.Process();rss=proc.memory_info().rss
            for child in proc.children(recursive=True):
                try:rss+=child.memory_info().rss
                except psutil.NoSuchProcess:pass
            peak=max(peak,rss)
            if rss>8*1024**3 or time.monotonic()-START>10800:raise RuntimeError('3h / monitored8GiB aggregate budget')
            for future in done:
                result=future.result();results.append(result);pending.pop(future)
                print('PAIR_PROGRESS',len(results),'/420',result['case_id'],flush=True)
    except BaseException:
        for process in pool._processes.values():process.terminate()
        pool.shutdown(wait=True,cancel_futures=True);raise
    else:pool.shutdown(wait=True)
    by={r['case_id']:r for r in results};assert len(by)==420
    for split,ids,status in [('train',fold['train_case_ids'],'PAIRED_315_TRAIN_INPUTS_VERIFIED_NOT_GPU_READY'),
                             ('development',fold['dev_case_ids'],'PAIRED_105_DEVELOPMENT_INPUTS_PREPARED_NOT_EVALUATED')]:
        for arm in ARMS:
            filename='train_manifest_8192.jsonl' if split=='train' else 'dev_manifest_8192.jsonl'
            with (O/arm/filename).open('x',encoding='utf-8') as f:
                for cid in ids:f.write(json.dumps(by[cid]['records'][arm],ensure_ascii=False)+'\n')
        dump(O/('paired_train_data_receipt.json' if split=='train' else 'paired_dev_data_receipt.json'),
          {'status':status,'stage':STAGE,'cases':len(ids),'sources':len({by[cid]['pair']['source_id'] for cid in ids}),
           'arms':ARMS,'input':8192,'target':8192,'sampling_seed':0,'target_and_frame_equal':True,'same_permutation_per_case':True,
           'point_geometry_unchanged':True,'comparison_split':split,'pairs':[by[cid]['pair'] for cid in ids]})
    config=json.loads((PREV/'static_training_config_v1.json').read_text());config['stage']=STAGE
    dump(O/'static_training_config_v1.json',config)
    with (O/'shared_order_foldC_seed0_v1.json').open('xb') as f:f.write((PREV/'shared_order_foldC_seed0_v1.json').read_bytes())
    assert all(sha(p)==h for p,h in frozen.items())
    dump(O/'data_preparation_completion.json',{'status':'PAIRED_FOLD_C_DATA_PREPARED_NOT_TRAINING_AUTHORIZED','stage':STAGE,
      'cases':420,'train_cases':315,'dev_cases':105,'point_files':840,'reused_cases':60,'new_geometry_cases':360,
      'same_targets_frames_permutations':True,'batch_order_bytes_unchanged':True,'initialization_policy_bound_not_executed':True,
      'raw_targets_existing_inputs_and_sampler_cores_unchanged':True,'seconds':time.monotonic()-START,
      'monitored_total_RSS_peak_bytes':peak,'GPU_model_server_calls':0})
    dump(O/'data_artifact_manifest.json',{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file()})
    print('ALL_PAIR_DATA_PREPARED',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'data_failure.json').exists():dump(O/'data_failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(e),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
