# -*- coding: utf-8 -*-
"""Single frozen D-only spatial/area stratification pilot, CPU only."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
import gc,hashlib,importlib.util,json,sys,time,traceback
from pathlib import Path
import numpy as np
import psutil
from scipy.spatial import cKDTree
B=Path(__file__).resolve().parent
O=B/'spatial_stratified_pilot_20261103_v1'
PLAN=B/'input_support_analysis_20261103_v1/report_and_next_pilot_zh_v1.md'
SCOPE=B.parent/'cranial_geometry_diagnostic_20261023/raw_pairing_v1/scope.json'
OLD=B/'input_interface_sampling_20261102_v1'
START=time.monotonic();PEAK=0

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for v in iter(lambda:f.read(1048576),b''):h.update(v)
    return h.hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def loadmod(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sb=loadmod('unchanged_V1_sampler',B/'real_data_qc_v1.py')
def guard():
    global PEAK
    rss=psutil.Process().memory_info().rss;PEAK=max(PEAK,rss)
    if time.monotonic()-START>900 or rss>4*1024**3:raise RuntimeError('15min/4GiB monitored budget exceeded')
sb.guard=guard

def spatial_order(surface):
    q,axis,sign=surface
    c=q.astype(np.int64)*2;c[np.arange(len(q)),axis]+=sign
    u=(c-c.min(0)).astype(np.uint64);bits=max(1,int(u.max()).bit_length())
    if bits>21:raise ValueError('Morton uint64 width exceeded')
    code=np.zeros(len(q),np.uint64)
    for bit in range(bits):
        for a in range(3):code|=((u[:,a]>>np.uint64(bit))&np.uint64(1))<<np.uint64(3*bit+a)
    return np.lexsort((q[:,2],q[:,1],q[:,0],sign,axis,code))

def stratified(surface,A,o,seed,n=8192):
    # No C/G/J/ROI/target/learned error arguments or global case labels.
    x,w=sb.face_geometry(surface,A,o);order=spatial_order(surface)
    cumulative=np.cumsum(w[order]);rng=np.random.default_rng(seed)
    positions=(np.arange(n)+rng.random(n))*(cumulative[-1]/n)
    ids=order[np.searchsorted(cumulative,positions,side='right')]
    p=x[ids].copy();uv=rng.random((n,2))-.5
    for a in range(3):
        sel=surface[1][ids]==a
        p[sel]+=uv[sel,0,None]*A[(a+1)%3]+uv[sel,1,None]*A[(a+2)%3]
    return p,ids

def membership(p,s,ids,A,o):
    v=(p-o)@np.linalg.inv(A)-s[0][ids];a=s[1][ids];sign=s[2][ids]
    error=float(np.abs(v[np.arange(len(v)),a]-.5*sign).max())
    assert error<1e-9 and np.abs(v).max()<.5+1e-9
    return error

def checks():
    m=np.zeros((5,6,7),bool);m[1:4,2:4,2:5]=True;m[2,3,3]=False
    s=sb.surface(m);A=np.diag([.4,.5,.7]);o=np.array([3.,-5.,9.]);copy=[a.copy() for a in s]
    p,ids=stratified(s,A,o,0);membership(p,s,ids,A,o)
    p2,i2=stratified(s,A,o,0);assert np.array_equal(p,p2) and np.array_equal(ids,i2)
    permutation=np.random.default_rng(873).permutation(len(s[0]));ss=tuple(a[permutation] for a in s)
    p3,i3=stratified(ss,A,o,0);assert np.array_equal(p,p3) and np.array_equal(ids,permutation[i3])
    t=.437;R=np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1.]])
    translation=np.array([-7.,11.,2.]);pr,ir=stratified(s,A@R,o@R+translation,0)
    rigid_error=float(np.max(np.linalg.norm(pr-(p@R+translation),axis=1)))
    assert np.array_equal(ids,ir) and rigid_error<1e-9
    assert all(np.array_equal(a,b) for a,b in zip(s,copy))
    _,w=sb.face_geometry(s,A,o);count=np.bincount(ids,minlength=len(w))
    assert np.max(np.abs(count-8192*w/w.sum()))<=2+1e-9
    assert len(p)==8192 and np.isfinite(p).all()
    return {'status':'PASS','checks':7,'items':['selected face membership','same-seed exact repeatability',
      'face-list permutation exact coordinate invariance','fixed affine rigid covariance',
      'D surface inputs unchanged','per-face stratified area count discrepancy <=2','fixed count and finite values'],
      'rigid_max_error_mm':rigid_error,'scope':'same voxel topology and index frame; no revoxelization claim'}

def metrics(d,w):
    ix=np.argsort(d);cum=np.cumsum(w[ix])
    return {'cover_1mm':float(np.average(d<=1,weights=w)),'cover_2mm':float(np.average(d<=2,weights=w)),
            'p95_mm':float(d[ix[np.searchsorted(cum,.95*cum[-1])]])}
def distances(tree,ref):
    out=[]
    for start in range(0,len(ref),65536):guard();out.append(tree.query(ref[start:start+65536],workers=2)[0])
    return np.concatenate(out)
def fov(s,shape):
    q,a,z=s;at=q[np.arange(len(q)),a]
    return ((z==-1)&(at==0))|((z==1)&(at==np.array(shape)[a]-1))
def store(p,**arrays):
    with p.open('xb') as f:np.savez_compressed(f,**arrays)

def run_case(cid,D,A,o,evaluate,phantom=False):
    guard();s=sb.surface(D);x,w=sb.face_geometry(s,A,o);ff=fov(s,D.shape)
    center,scale=sb.frame(D,A,o);samples=[]
    for seed in [0,1,2]:
        for method in ['uniform8k','Morton_area_stratified8k']:
            begin=time.monotonic()
            if method=='uniform8k':
                pts,ids,_,_=sb.sample(s,A,o,seed,16384);pts=pts[:8192];ids=ids[:8192]
            else:pts,ids=stratified(s,A,o,seed)
            seconds=time.monotonic()-begin;membership(pts,s,ids,A,o)
            norm=((pts-center)/scale).astype(np.float32)
            assert np.max(np.linalg.norm(norm.astype(float)*scale+center-pts,axis=1))<1e-3
            path=O/'samples'/f'{cid}_seed{seed}_{method}.npz'
            store(path,xyz=pts,partial=norm,face_ids=ids,center=center,scale=np.array(scale))
            with np.load(path,allow_pickle=False) as z:assert np.array_equal(z['xyz'],pts) and np.array_equal(z['partial'],norm)
            samples.append((seed,method,pts,ids,seconds,str(path.relative_to(O)),sha(path)))
            guard()
    # All six input sets are persisted before evaluating against C/G/J.
    G,C,target=evaluate()
    assert C.shape==D.shape==G.shape and np.array_equal(C,D|G) and not (D&G).any()
    J=sb.contact(s,G);assert J.any() and (~J).any()
    treeJ=cKDTree(x[J]);rows=[]
    radius=np.linalg.norm(x,axis=1) if phantom else None
    for seed,method,p,ids,seconds,path,digest in samples:
        tree=cKDTree(p);dist=distances(tree,x);nn=tree.query(p,k=2,workers=2)[0][:,1]
        row={'case':cid,'dataset':'phantom' if phantom else cid.split('_')[0], 'phantom':phantom,'seed':seed,
          'method':method,'input_count':8192,'J':metrics(dist[J],w[J]),'E':metrics(dist[~J],w[~J]),'all':metrics(dist,w),
          'J_face_point_count':int(J[ids].sum()),'support_2mm_center_reference_count':int((treeJ.query(p,workers=2)[0]<=2).sum()),
          'NN_median_mm':float(np.median(nn)),'NN_p05_mm':float(np.percentile(nn,5)),
          'NN_fraction_lt_0_5mm':float(np.mean(nn<.5)),
          'FOV_sample_count':int(ff[ids].sum()),'FOV_area_fraction':float(w[ff].sum()/w.sum()),
          'J_area_fraction':float(w[J].sum()/w.sum()),'sampling_seconds_including_sort':seconds,
          'input_saved_before_evaluation_decode':True,'sample_path':path,'sample_sha256':digest,'target':target}
        if phantom:
            for name,mask in [('inner',(~J)&(np.abs(radius-17)<=np.abs(radius-20))),('outer',(~J)&(np.abs(radius-17)>np.abs(radius-20)))]:
                assert mask.any();row[name]=metrics(dist[mask],w[mask]);row[name+'_sample_count']=int(mask[ids].sum())
        rows.append(row)
    dump(O/'cases'/f'{cid}.json',rows)
    print('DONE',cid,[(r['method'],round(r['J']['cover_2mm'],4)) for r in rows[:2]],flush=True)
    guard()
    if sum(p.stat().st_size for p in O.rglob('*') if p.is_file())>256*1024**2:raise RuntimeError('256MiB output budget')
    return rows

def aggregate(rows):
    out={}
    for method in ['uniform8k','Morton_area_stratified8k']:
        rr=[r for r in rows if r['method']==method];assert rr
        out[method]={reg:{k:float(np.mean([r[reg][k] for r in rr])) for k in ['cover_1mm','cover_2mm','p95_mm']} for reg in ['J','E','all']}
        for k in ['J_face_point_count','support_2mm_center_reference_count','NN_median_mm','NN_p05_mm','NN_fraction_lt_0_5mm','FOV_sample_count','sampling_seconds_including_sort']:
            out[method][k]=float(np.mean([r[k] for r in rr]))
    a,b=out['uniform8k'],out['Morton_area_stratified8k']
    out['delta_candidate_minus_baseline']={reg:{k:b[reg][k]-a[reg][k] for k in a[reg]} for reg in ['J','E','all']}
    return out

def main():
    scope=json.loads(SCOPE.read_text(encoding='utf-8'))
    cases=scope['cases'];expected={'SkullFix_002','SkullFix_003','SkullFix_004','SkullBreak_train__000__bilateral','SkullBreak_train__001__bilateral','SkullBreak_train__002__bilateral'}
    assert len(cases)==6 and {c['dataset']+'_'+c['case_id'] for c in cases}==expected
    oldrows=json.loads((OLD/'metrics.json').read_text(encoding='utf-8'))
    targets={r['case']:r['target'] for r in oldrows if not r['phantom']}
    frozen={str(p):sha(p) for p in [Path(__file__),PLAN,SCOPE,B/'real_data_qc_v1.py',sb.READER,sb.LOCK,OLD/'metrics.json']}
    for c in cases:
        for p in c['raw_paths'].values():
            assert sha(p)==c['hashes_before'][p];frozen[p]=sha(p)
        cid=c['dataset']+'_'+c['case_id'];t=targets[cid];assert sha(t['path'])==t['sha256'];frozen[t['path']]=t['sha256']
    O.mkdir(exist_ok=False);(O/'samples').mkdir();(O/'cases').mkdir()
    dump(O/'frozen_protocol.json',{'status':'FROZEN_BEFORE_TESTS_AND_SAMPLING','cases':sorted(expected),'seeds':[0,1,2],
        'methods':['uniform8k','Morton_area_stratified8k'],'input':8192,'target':8192,'target_bindings':targets,
        'source_and_implementation_sha256':frozen,'limits':{'seconds':900,'checkpoint_RSS_bytes':4*1024**3,'output_bytes':256*1024**2},
        'scientific_criteria':{'both_datasets_J_cover2_increase':True,'six_case_mean_J_cover2_delta_min':.05,
          'both_datasets_J_p95_delta_max':0,'both_datasets_E_and_all_cover2_delta_min':-.01,
          'phantom_each_inner_outer_seed_mean_cover1_delta_min':0,'phantom_layers_must_have_points':True},
        'phantom_layer_criterion_operationalization':'No decrease in each shell and each layer mean Cover@1mm across 3 seeds; frozen before results',
        'prohibitions':['no GT-assisted input selection','no modified raw geometry','no new target','no retry or tuning','no GPU/server/model/training']})
    dump(O/'artificial_checks.json',checks());print('ARTIFICIAL_CHECKS_PASS',flush=True)
    allrows=[]
    for h,phase,angle in [(1.,0.,0.),(.7,.23,.4),(1.2,.31,.7)]:
        a=np.arange(-24,24+h,h);xyz=np.stack(np.meshgrid(a,a,a,indexing='ij'),-1)+phase*h
        radius=np.linalg.norm(xyz,axis=-1);C=(radius<=20)&(radius>=17)
        normal=np.array([np.cos(angle),np.sin(angle),0]);G=C&(xyz@normal>10);D=C&~G
        allrows+=run_case('phantom_'+str(h),D,np.eye(3)*h,np.full(3,a[0]+phase*h),lambda:(G,C,{'kind':'existing analytic shell, no learned-model target'}),True)
        del C,G,D,xyz,radius;gc.collect()
    for c in cases:
        cid=c['dataset']+'_'+c['case_id'];print('BEGIN',cid,flush=True)
        paths={k:Path(p) for k,p in c['raw_paths'].items()}
        D,A,o=sb.raw.read_mask(paths['defective'])
        def evaluate():
            G,F,f=sb.raw.read_mask(paths['implant']);C,H,v=sb.raw.read_mask(paths['complete'])
            assert np.array_equal(A,F) and np.array_equal(A,H) and np.array_equal(o,f) and np.array_equal(o,v)
            t=targets[cid]
            with np.load(t['path'],allow_pickle=False) as z:assert z['xyz'].shape==(8192,3) and np.isfinite(z['xyz']).all()
            return G,C,t
        allrows+=run_case(cid,D,A,o,evaluate);del D;gc.collect();guard()
    dump(O/'metrics.json',allrows)
    # Check exact historical baseline metrics to avoid comparing different extraction/sampling definitions.
    for row in allrows:
        if row['phantom'] or row['method']!='uniform8k':continue
        old=next(r for r in oldrows if r['case']==row['case'] and r['seed']==row['seed'] and r['method']=='uniform8k')
        for region in ['J','E','all']:
            for k in ['cover_1mm','cover_2mm','p95_mm']:assert abs(row[region][k]-old[region][k])<1e-10
    assert all(sha(p)==h for p,h in frozen.items())
    real=[r for r in allrows if not r['phantom']]
    ag={'all_real':aggregate(real)}
    for ds in ['SkullFix','SkullBreak']:ag[ds]=aggregate([r for r in real if r['dataset']==ds])
    checks_gate={'both_datasets_J_cover2_increase':all(ag[d]['delta_candidate_minus_baseline']['J']['cover_2mm']>0 for d in ['SkullFix','SkullBreak']),
      'six_case_J_cover2_gain_ge_5pp':ag['all_real']['delta_candidate_minus_baseline']['J']['cover_2mm']>=.05,
      'both_datasets_J_p95_not_worse':all(ag[d]['delta_candidate_minus_baseline']['J']['p95_mm']<=0 for d in ['SkullFix','SkullBreak']),
      'both_datasets_E_all_cover2_loss_le_1pp':all(ag[d]['delta_candidate_minus_baseline'][reg]['cover_2mm']>=-.01 for d in ['SkullFix','SkullBreak'] for reg in ['E','all'])}
    layers=[]
    for cid in sorted({r['case'] for r in allrows if r['phantom']}):
        for layer in ['inner','outer']:
            means={m:float(np.mean([r[layer]['cover_1mm'] for r in allrows if r['case']==cid and r['method']==m])) for m in ['uniform8k','Morton_area_stratified8k']}
            layers.append({'case':cid,'layer':layer,**means,'delta':means['Morton_area_stratified8k']-means['uniform8k']})
    checks_gate['all_phantom_layers_cover1_not_worse']=all(r['delta']>=0 for r in layers)
    checks_gate['all_phantom_layers_sampled']=all(r[layer+'_sample_count']>0 for r in allrows if r['phantom'] for layer in ['inner','outer'])
    dump(O/'summary.json',{'status':'GEOMETRIC_PILOT_PASS_NO_TRAINING' if all(checks_gate.values()) else 'CANDIDATE_STOPPED_SCIENTIFIC_CRITERIA_NOT_MET',
        'gates':checks_gate,'aggregate':ag,'phantom_layer_comparison':layers,'rows':len(allrows),'real_cases':6,'phantoms':3,
        'seconds':time.monotonic()-START,'checkpoint_peak_RSS_bytes':PEAK,'source_and_target_hashes_unchanged':True,
        'historical_baseline_metrics_reproduced':True,'forward_training_GPU_calls':0,'no_retry_or_parameter_scan':True})
    print('COMPLETED',json.dumps(checks_gate),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'failure.json').exists():dump(O/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(e),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
