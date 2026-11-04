"""Fixed-cardinality Euclidean compact-kernel sample elimination; CPU pilot only.
Inspired by Yuksel 2015, not a bitwise reproduction or strict minimum-radius guarantee.
No point movement, topology change, target-assisted selection, or model calls.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2')
import gc, hashlib, heapq, importlib.util, json, sys, time, traceback
from pathlib import Path
import numpy as np
import psutil
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix

B=Path(__file__).resolve().parent
O=B/'blue_noise_pilot_20261103_v1'
SCOPE=B.parent/'cranial_geometry_diagnostic_20261023/raw_pairing_v1/scope.json'
START=time.monotonic(); PEAK=0
N=8192; POOL=4*N; SEEDS=[0,1,2]

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)

def guard():
    global PEAK
    rss=psutil.Process().memory_info().rss;PEAK=max(PEAK,rss)
    if time.monotonic()-START>1800 or rss>6*1024**3:raise RuntimeError('30min / monitored 6GiB budget')

spec=importlib.util.spec_from_file_location('unchanged_surface_helpers',B/'real_data_qc_v1.py')
sb=importlib.util.module_from_spec(spec);spec.loader.exec_module(sb);sb.guard=guard

def eliminate(p,area,n=N):
    """All pairs within fixed R; delete largest sum of (1-d/R)^8.
    R=2 sqrt(area/n), dimensionally a surface-area spacing, frozen not fitted.
    Labels, normals, G and J are intentionally absent from this interface.
    """
    guard();r=2*np.sqrt(area/n)
    tree=cKDTree(p)
    edge_count=(int(tree.count_neighbors(tree,r))-len(p))//2
    if edge_count>8000000:raise RuntimeError('8M undirected pair budget exceeded')
    pairs=tree.query_pairs(r,output_type='ndarray');assert len(pairs)==edge_count
    d=np.linalg.norm(p[pairs[:,0]]-p[pairs[:,1]],axis=1)
    w=(1-d/r)**8
    graph=coo_matrix((np.r_[w,w],(np.r_[pairs[:,0],pairs[:,1]],np.r_[pairs[:,1],pairs[:,0]])),shape=(len(p),len(p))).tocsr()
    weights=np.asarray(graph.sum(axis=1)).ravel()
    alive=np.ones(len(p),bool);versions=np.zeros(len(p),np.int64)
    heap=[(-float(v),i,0) for i,v in enumerate(weights)];heapq.heapify(heap)
    del pairs,d,w;guard()
    for step in range(len(p)-n):
        while True:
            _,i,v=heapq.heappop(heap)
            if alive[i] and v==versions[i]:break
        alive[i]=False
        lo,hi=graph.indptr[i:i+2];js=graph.indices[lo:hi];ww=graph.data[lo:hi]
        active=alive[js];js=js[active];ww=ww[active]
        weights[js]-=ww;versions[js]+=1
        for j in js:heapq.heappush(heap,(-float(weights[j]),int(j),int(versions[j])))
        if step%1024==0:
            guard()
            if len(heap)>8*len(p):
                heap=[(-float(weights[j]),int(j),int(versions[j])) for j in np.flatnonzero(alive)];heapq.heapify(heap)
    ids=np.flatnonzero(alive);assert len(ids)==n
    return ids,{'radius_mm':float(r),'undirected_edges':edge_count,'pool_count':len(p)}

def brute(p,area,n):
    r=2*np.sqrt(area/n);d=np.linalg.norm(p[:,None]-p[None,:],axis=-1)
    w=np.maximum(0,1-d/r)**8;np.fill_diagonal(w,0);alive=np.ones(len(p),bool)
    for _ in range(len(p)-n):
        score=w[:,alive].sum(1);score[~alive]=-np.inf;alive[np.argmax(score)]=False
    return np.flatnonzero(alive)

def checks():
    p=np.random.default_rng(7).normal(size=(70,3));a=60.
    ids,_=eliminate(p,a,20);assert np.array_equal(ids,brute(p,a,20))
    again,_=eliminate(p,a,20);assert np.array_equal(ids,again)
    t=.413;R=np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
    rotated,_=eliminate(p@R+np.array([4.,-8.,3.]),a,20);assert np.array_equal(ids,rotated)
    assert len(ids)==20 and len(set(ids))==20 and np.isfinite(p[ids]).all()
    assert np.array_equal(p,np.random.default_rng(7).normal(size=(70,3)))
    return {'status':'PASS','checks':['heap agrees with exhaustive deletion','same-seed deterministic',
      'rigid covariance on non-tied artificial coordinates','exact cardinality and uniqueness','finite original subset','input immutable'],
      'limitations':'No tie-invariance guarantee; no blue-noise spectral certification; no minimum-distance guarantee'}

def metric(ref,w,p):
    tree=cKDTree(p);out=[]
    for start in range(0,len(ref),65536):guard();out.append(tree.query(ref[start:start+65536],workers=2)[0])
    d=np.concatenate(out);ix=np.argsort(d);cw=np.cumsum(w[ix]);p95=d[ix[np.searchsorted(cw,.95*cw[-1])]]
    return {'cover_0_5mm':float(np.average(d<=.5,weights=w)), 'cover_1mm':float(np.average(d<=1,weights=w)),
      'cover_2mm':float(np.average(d<=2,weights=w)),'p95_mm':float(p95),'max_mm':float(d.max())}

def npz(p,**x):
    with p.open('xb') as f:np.savez_compressed(f,**x)

def measure(cid,seed,p,ids,method,ref,w,labels,point_labels,regions,extra,refname):
    row={'case':cid,'seed':seed,'method':method,'count':len(p),'reference':refname,**extra,'regions':{}}
    for name,tag in regions.items():
        same=point_labels==labels[name]
        row['regions'][name]={'unrestricted':metric(ref[tag],w[tag],p),
          'same_surface':metric(ref[tag],w[tag],p[same]) if same.any() else None,
          'point_count':int(same.sum()),'area_fraction':float(w[tag].sum()/w.sum())}
    nn=cKDTree(p).query(p,k=2,workers=2)[0][:,1]
    row['nn_p05_mm']=float(np.percentile(nn,5));row['nn_median_mm']=float(np.median(nn))
    npz(O/'samples'/f'{cid}_seed{seed}_{method}.npz',xyz=p,pool_indices=ids,region_labels=point_labels)
    return row

def compare_pool(cid,seed,p,point_labels,area,ref,w,labels,regions,refname):
    before=hashlib.sha256(p.tobytes()).hexdigest();begin=time.monotonic()
    selected,info=eliminate(p,area);elapsed=time.monotonic()-begin
    assert before==hashlib.sha256(p.tobytes()).hexdigest()
    result=[]
    for method,ids in [('V1_common_pool',np.arange(N)),('Euclidean_elimination',selected)]:
        result.append(measure(cid,seed,p[ids],ids,method,ref,w,labels,point_labels[ids],regions,
          {'selection_seconds':elapsed if method=='Euclidean_elimination' else 0.,'kernel':info,'point_displacement_mm':0.},refname))
    print('DONE',cid,seed,round(elapsed,2),flush=True);return result

def thin_ring(thickness):
    # One solid square plate with a square through-hole. Top/bottom + hole walls + outer edge.
    rect=[]
    def add(origin,u,v,label):rect.append((np.array(origin,float),np.array(u,float),np.array(v,float),label))
    for z,label in [(-thickness/2,0),(thickness/2,1)]:
        for x,y,dx,dy in [(-40,-40,25,80),(15,-40,25,80),(-15,-40,30,25),(-15,15,30,25)]:
            add([x,y,z],[dx,0,0],[0,dy,0],label)
    for span,label in [(15,2),(40,3)]:
        for x in [-span,span]:add([x,-span,-thickness/2],[0,2*span,0],[0,0,thickness],label)
        for y in [-span,span]:add([-span,y,-thickness/2],[2*span,0,0],[0,0,thickness],label)
    origins=np.array([r[0] for r in rect]);u=np.array([r[1] for r in rect]);v=np.array([r[2] for r in rect]);lab=np.array([r[3] for r in rect])
    area=np.linalg.norm(np.cross(u,v),axis=1)
    # Fixed independent equal-area quadrature; no distance threshold selects references.
    ref=[];rw=[];rl=[]
    for i in range(len(rect)):
        nu=max(2,int(np.ceil(np.linalg.norm(u[i])/.5)));nv=max(2,int(np.ceil(np.linalg.norm(v[i])/.5)))
        uv=np.stack(np.meshgrid((np.arange(nu)+.5)/nu,(np.arange(nv)+.5)/nv,indexing='ij'),-1).reshape(-1,2)
        ref.append(origins[i]+uv[:,0,None]*u[i]+uv[:,1,None]*v[i]);rw.extend([area[i]/len(uv)]*len(uv));rl.extend([lab[i]]*len(uv))
    return origins,u,v,lab,area,np.concatenate(ref),np.array(rw),np.array(rl)

def aggregate(rows):
    out={}
    for kind in ['phantom','SkullFix','SkullBreak']:
        rr=[r for r in rows if r['case'].startswith(kind)]
        for reg in rr[0]['regions']:
            for distance in ['unrestricted','same_surface']:
                key=kind+'/'+reg+'/'+distance;out[key]={}
                for met in ['cover_0_5mm','cover_1mm','cover_2mm','p95_mm']:
                    means={method:float(np.mean([r['regions'][reg][distance][met] for r in rr if r['method']==method])) for method in ['V1_common_pool','Euclidean_elimination']}
                    out[key][met]={**means,'delta':means['Euclidean_elimination']-means['V1_common_pool']}
    return out

def main():
    if O.exists():raise RuntimeError('single new output directory only; no retry')
    scope=json.loads(SCOPE.read_text(encoding='utf-8'));cases=scope['cases']
    expected={'SkullFix_002','SkullFix_003','SkullFix_004','SkullBreak_train__000__bilateral','SkullBreak_train__001__bilateral','SkullBreak_train__002__bilateral'}
    assert {c['dataset']+'_'+c['case_id'] for c in cases}==expected and len(cases)==6
    bindings={str(p):sha(p) for p in [Path(__file__),SCOPE,B/'real_data_qc_v1.py',sb.READER,sb.LOCK]}
    for c in cases:
        for p in c['raw_paths'].values():
            assert sha(p)==c['hashes_before'][p];bindings[p]=sha(p)
    O.mkdir();(O/'samples').mkdir();(O/'cases').mkdir()
    dump(O/'protocol.json',{'status':'FROZEN_BEFORE_CHECKS_AND_GEOMETRY','source_hashes':bindings,'N':N,'pool_size':POOL,
      'seeds':SEEDS,'real_cases':sorted(expected),'phantom_thickness_mm':[.5,1.,3.],
      'kernel':'sum(max(0,1-d/R)^8); R=2sqrt(total_surface_area/N); all in-radius Euclidean pairs; delete largest sum',
      'implementation_identity':'compact-kernel WSE-inspired; not exact cyCodeBase reproduction or spectral blue-noise proof',
      'baseline':'first8192 of common32768 area-random pool; distribution V1, not historical identical random bytes',
      'sampler_inputs':'D surface geometry / total area / seed only; labels and G not passed into eliminate()',
      'reference':'real exact voxel exposed face centers; phantom independent .5mm-or-finer area quadrature',
      'real_label_limit':'only exact cut-wall J vs remaining E, no anatomical inner/outer labels',
      'decision':'descriptive pilot only; no formal gate. Stop this candidate if systematic thin-layer loss; no automatic tuning/training',
      'budgets':{'seconds':1800,'monitored_rss_GiB':6,'max_undirected_pairs':8000000,'output_MiB':128},
      'prohibitions':['no model/GPU/server','no point motion','no raw/target modification','no new holdout','no automatic retry or radius scan']})
    dump(O/'checks.json',checks());print('CHECKS_PASS',flush=True);rows=[]
    for t in [.5,1.,3.]:
        orig,u,v,lab,area,ref,w,rl=thin_ring(t)
        labels={'inner':0,'outer':1,'cut_wall':2,'outer_edge':3};regions={k:rl==v for k,v in labels.items()}
        for seed in SEEDS:
            rng=np.random.default_rng(seed);ids=rng.choice(len(area),POOL,p=area/area.sum());uv=rng.random((POOL,2))
            p=orig[ids]+uv[:,0,None]*u[ids]+uv[:,1,None]*v[ids]
            rr=compare_pool('phantom_'+str(t),seed,p,lab[ids],float(area.sum()),ref,w,labels,regions,'analytic rectangle midpoint quadrature')
            rows+=rr;dump(O/'cases'/f'phantom_{t}_seed{seed}.json',rr)
    for c in cases:
        cid=c['dataset']+'_'+c['case_id'];print('BEGIN',cid,flush=True)
        D,A,o=sb.raw.read_mask(Path(c['raw_paths']['defective']));s=sb.surface(D)
        ref,w=sb.face_geometry(s,A,o);pools=[]
        for seed in SEEDS:
            p,ids,_,_=sb.sample(s,A,o,seed,POOL);pools.append((seed,p,ids))
        # Freeze candidate indices BEFORE opening implant payload or deriving J evaluation labels.
        selected=[]
        for seed,p,ids in pools:
            begin=time.monotonic();chosen,info=eliminate(p,float(w.sum()));elapsed=time.monotonic()-begin
            selected.append((seed,p,ids,chosen,info,elapsed));npz(O/'samples'/f'{cid}_seed{seed}_selection_before_G.npz',pool_indices=chosen)
        G,F,f=sb.raw.read_mask(Path(c['raw_paths']['implant']))
        assert D.shape==G.shape and np.array_equal(A,F) and np.array_equal(o,f) and not (D&G).any()
        J=sb.contact(s,G);labels={'J':1,'E':0};regions={'J':J,'E':~J};assert J.any()
        for seed,p,ids,chosen,info,elapsed in selected:
            rr=[]
            for method,ix in [('V1_common_pool',np.arange(N)),('Euclidean_elimination',chosen)]:
                rr.append(measure(cid,seed,p[ix],ix,method,ref,w,labels,J[ids[ix]].astype(int),regions,
                  {'selection_seconds':elapsed if method=='Euclidean_elimination' else 0.,'kernel':info,'point_displacement_mm':0.,'selection_saved_before_G_decode':True},'exact exposed voxel face centers'))
            rows+=rr;dump(O/'cases'/f'{cid}_seed{seed}.json',rr);print('DONE',cid,seed,round(elapsed,2),flush=True)
        del D,G,s,ref,pools,selected;gc.collect();guard()
    assert len(rows)==54 and all(r['count']==N for r in rows)
    assert all(sha(p)==h for p,h in bindings.items())
    dump(O/'metrics.json',rows);dump(O/'summary.json',{'status':'COMPLETED_CPU_GEOMETRY_ONLY','rows':len(rows),'aggregate':aggregate(rows),
      'seconds':time.monotonic()-START,'checkpoint_peak_RSS_bytes':PEAK,'input_hashes_unchanged':True,'model_GPU_server_calls':0})
    if sum(p.stat().st_size for p in O.rglob('*') if p.is_file())>128*1024**2:raise RuntimeError('output budget')
    dump(O/'contents.json',{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file()})
    print('COMPLETED',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'failure.json').exists():dump(O/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(e),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
