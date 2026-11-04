"""One bounded artificial experiment, exact unrolled U surface; no real data/model."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLBACKEND='Agg')
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_artificial_mechanism_20261103_v1'
os.environ['MPLCONFIGDIR']=str(B/'blue_noise_artificial_mechanism_plot_cache_v1')
import csv,hashlib,heapq,json,sys,time,traceback
import numpy as np
import psutil
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix

N=8192;M=32768;L=80.;W=80.;START=time.monotonic();PEAK=0
METHODS=['Euclidean','no_opposite_shortcut','intrinsic_unrolled']

def guard():
    global PEAK
    PEAK=max(PEAK,psutil.Process().memory_info().rss)
    if time.monotonic()-START>1200 or PEAK>4*1024**3:raise RuntimeError('20min / monitored4GiB budget')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def npz(p,**arrays):
    with p.open('xb') as f:np.savez_compressed(f,**arrays)

def embed(uv,t,flat=False):
    s,y=uv.T;labels=np.where(s<L,0,np.where(s<=L+t,1,2))
    if flat:return np.c_[s,y,np.zeros(len(s))],labels
    p=np.c_[np.where(labels==0,L-s,np.where(labels==1,0,s-L-t)),y,np.where(labels==0,0,np.where(labels==1,s-L,t))]
    return p,labels

def edges(p,uv,labels,R):
    tree=cKDTree(p);count=(int(tree.count_neighbors(tree,R))-len(p))//2
    if count>5000000:raise RuntimeError('5M undirected pairs budget')
    ij=tree.query_pairs(R,output_type='ndarray');a,b=ij.T
    de=np.sqrt(np.sum((p[a]-p[b])**2,axis=1));dg=np.sqrt(np.sum((uv[a]-uv[b])**2,axis=1))
    assert (dg>=de-1e-10).all()
    opposite=((labels[a]==0)&(labels[b]==2))|((labels[a]==2)&(labels[b]==0))
    # Same patch, connected cross-patch, or true opposite-sheet long-path shortcut.
    cat=np.where(labels[a]==labels[b],0,np.where(opposite&(dg>R),2,1)).astype(np.int8)
    we=np.maximum(0,1-de/R)**8;wg=np.maximum(0,1-dg/R)**8
    graph=coo_matrix((np.r_[np.arange(len(ij)),np.arange(len(ij))]+1,(np.r_[a,b],np.r_[b,a])),shape=(len(p),len(p))).tocsr()
    return graph,cat,we,wg,{'pairs':len(ij),'shortcut_pairs':int((cat==2).sum()),
      'initial_kernel_share_by_class':[float(we[cat==k].sum()/we.sum()) for k in range(3)]}

def run_elimination(graph,cat,w,n):
    """Log actual alive-neighbor score components for every deletion."""
    adj_weight=w[graph.data-1];adj_cat=cat[graph.data-1]
    row=np.repeat(np.arange(graph.shape[0]),np.diff(graph.indptr))
    scores=np.stack([np.bincount(row,weights=adj_weight*(adj_cat==k),minlength=graph.shape[0]) for k in range(3)])
    initial=scores.copy();total=scores.sum(0);alive=np.ones(graph.shape[0],bool);version=np.zeros(len(alive),np.int64)
    heap=[(-float(v),i,0) for i,v in enumerate(total)];heapq.heapify(heap)
    deleted=[];history=[]
    for step in range(graph.shape[0]-n):
        while True:
            _,i,v=heapq.heappop(heap)
            if alive[i] and version[i]==v:break
        deleted.append(i);history.append(scores[:,i].copy());alive[i]=False
        lo,hi=graph.indptr[i:i+2];js=graph.indices[lo:hi];weights=adj_weight[lo:hi];categories=adj_cat[lo:hi]
        active=alive[js]&(weights>0);js=js[active];weights=weights[active];categories=categories[active]
        for k in range(3):
            tag=categories==k;scores[k,js[tag]]-=weights[tag]
        version[js]+=1
        for j in js:heapq.heappush(heap,(-float(scores[:,j].sum()),int(j),int(version[j])))
        if step%1024==0:
            guard()
            if len(heap)>8*len(alive):
                heap=[(-float(scores[:,j].sum()),int(j),int(version[j])) for j in np.flatnonzero(alive)];heapq.heapify(heap)
    selected=np.flatnonzero(alive)
    assert len(selected)==n and np.min(scores)>-1e-10
    return selected,np.array(deleted),np.array(history),initial

def checks():
    rng=np.random.default_rng(909);uv=rng.random((90,2))*[161,80];p,labels=embed(uv,1,True);R=70.
    graph,cat,we,wg,_=edges(p,uv,labels,R);assert np.array_equal(we,wg) and not (cat==2).any()
    selected,deleted,hist,_=run_elimination(graph,cat,we,20)
    dense=coo_matrix((we[graph.data-1],(np.repeat(np.arange(90),np.diff(graph.indptr)),graph.indices)),shape=(90,90)).toarray()
    alive=np.ones(90,bool)
    for expected in deleted:
        score=dense[:,alive].sum(1);score[~alive]=-np.inf
        assert int(np.argmax(score))==int(expected);alive[expected]=False
    assert np.array_equal(np.flatnonzero(alive),selected)
    test_uv=np.array([[40.,10.],[121.,10.],[79.9,10.],[80.1,10.]])
    p,lab=embed(test_uv,1);g,c,e,i,_=edges(p,test_uv,lab,2.5)
    # Opposite sheets far along the true surface are removed; wall connection is retained.
    pairs={(a,int(b)):int(c[int(idx)-1]) for a in range(4) for b,idx in zip(g.indices[g.indptr[a]:g.indptr[a+1]],g.data[g.indptr[a]:g.indptr[a+1]])}
    assert pairs[(0,1)]==2 and pairs[(2,3)]==1
    return {'status':'PASS','checks':['flat Euclidean and exact intrinsic weights identical','flat no shortcut category',
      'heap deletion order equals exhaustive greedy','opposite far-path classification','wall connection preserved',
      'exact cardinality'],'limitations':'no nonmanifold/general mesh path solver; analytic U only'}

def reference(t):
    refs=[];weights=[];labels=[]
    for lo,hi,label in [(0,L,0),(L,L+t,1),(L+t,2*L+t,2)]:
        ns=max(2,int(np.ceil((hi-lo)/.5)));ny=int(W/.5)
        uv=np.stack(np.meshgrid(lo+(np.arange(ns)+.5)*(hi-lo)/ns,(np.arange(ny)+.5)*W/ny,indexing='ij'),-1).reshape(-1,2)
        refs.append(uv);weights.extend([W*(hi-lo)/len(uv)]*len(uv));labels.extend([label]*len(uv))
    return np.concatenate(refs),np.array(weights),np.array(labels)

def metric(d,w):
    ids=np.argsort(d);cw=np.cumsum(w[ids])
    return {'cover_0_5mm':float(np.average(d<=.5,weights=w)),'cover_1mm':float(np.average(d<=1,weights=w)),
      'cover_2mm':float(np.average(d<=2,weights=w)),'p95_mm':float(d[ids[np.searchsorted(cw,.95*cw[-1])]])}

def measure(p,uv,labels,selected,ref,rp,rw,rl):
    tree=cKDTree(p[selected]);dt=tree.query(rp,workers=2)[0]
    dg=cKDTree(uv[selected]).query(ref,workers=2)[0]
    result={'all_Euclidean':metric(dt,rw),'all_intrinsic':metric(dg,rw),'regions':{}}
    for name,label in [('lower',0),('wall',1),('upper',2)]:
        rtag=rl==label;ix=selected[labels[selected]==label];assert len(ix)>0
        ds=cKDTree(p[ix]).query(rp[rtag],workers=2)[0]
        result['regions'][name]={'count':len(ix),'same_patch':metric(ds,rw[rtag]),
          'intrinsic_all_points':metric(dg[rtag],rw[rtag]),'Euclidean_all_points':metric(dt[rtag],rw[rtag])}
    return result

def main():
    if O.exists():raise RuntimeError('do not overwrite existing output')
    frozen={str(p):sha(p) for p in [Path(__file__),B/'blue_noise_pilot_v1.py']}
    O.mkdir();(O/'sets').mkdir();(O/'logs').mkdir()
    dump(O/'protocol.json',{'status':'FROZEN_BEFORE_CPU_CHECKS','hashes':frozen,'N':N,'pool':M,'seeds':[0,1,2],
      'geometry':[{'name':'flat_control','t':1.,'flat':True},{'name':'U_t0.5','t':.5,'flat':False},{'name':'U_t1.0','t':1.,'flat':False},{'name':'U_t3.0','t':3.,'flat':False}],
      'surface':'open-ended U strip, two 80x80 plates joined by 80xt wall; all one connected developable surface; not a closed bone solid',
      'exact_distance':'Euclidean in unrolled (s,y); analytic intrinsic shortest path on rectangular domain',
      'R':'2sqrt(total surface area/8192), identical across methods within each geometry; no tuning',
      'kernel':'(max(0,1-distance/R))^8; original coordinates never move',
      'methods':METHODS,'ablated_edges':'only opposite-plate pairs with intrinsic distance>R; local wall/plate connections retained in no_opposite_shortcut',
      'edge_classes':['same patch','connected cross patch incl near-wall opposite points with intrinsic distance<=R','opposite plates with intrinsic distance>R'],
      'logging':'every deleted index plus three live kernel components and initial components; survivors saved',
      'evaluation':'independent .5mm or finer quadrature; same-patch, all Euclidean and all exact intrinsic distances at .5/1/2mm',
      'decision':'descriptive paired mechanism comparison; do not infer clinical or real data/model superiority',
      'prohibitions':['no real payload','no change to production sampler','no radius/weight search','no GPU/server/model'],
      'budgets':{'seconds':1200,'monitored_RSS_GiB':4,'max_pairs':5000000,'output_MiB':192}})
    dump(O/'checks.json',checks());print('CHECKS_PASS',flush=True);rows=[];logs=[]
    for name,t,flat in [('flat_control',1.,True),('U_t0.5',.5,False),('U_t1.0',1.,False),('U_t3.0',3.,False)]:
        area=(2*L+t)*W;R=2*np.sqrt(area/N);ref,rw,rl=reference(t);rp,_=embed(ref,t,flat)
        for seed in [0,1,2]:
            guard();print('BEGIN',name,seed,flush=True)
            uv=np.random.default_rng(seed).random((M,2))*[2*L+t,W];p,labels=embed(uv,t,flat)
            npz(O/'sets'/f'{name}_seed{seed}_pool.npz',xyz=p,uv=uv,labels=labels)
            graph,cat,we,wg,edge_info=edges(p,uv,labels,R);selections={}
            for method in METHODS:
                weights=we if method=='Euclidean' else np.where(cat==2,0,we) if method=='no_opposite_shortcut' else wg
                begin=time.monotonic();selected,deleted,history,initial=run_elimination(graph,cat,weights,N)
                selections[method]=selected
                npz(O/'sets'/f'{name}_seed{seed}_{method}.npz',pool_indices=selected)
                npz(O/'logs'/f'{name}_seed{seed}_{method}.npz',deleted_pool_indices=deleted,live_kernel_components=history,
                  initial_components=initial[:,deleted].T,deleted_patch=labels[deleted])
                row={'geometry':name,'t':t,'flat':flat,'seed':seed,'method':method,'R':float(R),
                  'elimination_seconds':time.monotonic()-begin,'edges':edge_info,**measure(p,uv,labels,selected,ref,rp,rw,rl)}
                rows.append(row)
                for label,labelname in [(0,'lower'),(1,'wall'),(2,'upper')]:
                    h=history[labels[deleted]==label];total=h.sum(1);valid=total>1e-15
                    logs.append({'geometry':name,'seed':seed,'method':method,'patch':labelname,'deleted':len(h),
                      'mean_live_weight_share':[float(np.mean(h[valid,k]/total[valid])) if valid.any() else 0. for k in range(3)],
                      'fraction_with_positive_shortcut':float(np.mean(h[:,2]>1e-15))})
                print('DONE',name,seed,method,flush=True)
            if flat:
                assert all(np.array_equal(selections['Euclidean'],selections[m]) for m in METHODS)
            dump(O/f'{name}_seed{seed}.json',rows[-3:])
    assert len(rows)==36 and all(sha(Path(p))==h for p,h in frozen.items())
    dump(O/'metrics.json',rows);dump(O/'deletion_summary.json',logs)
    dump(O/'summary.json',{'status':'COMPLETED_ARTIFICIAL_MECHANISM_ONLY','models':0,'real_payload_reads':0,
      'rows':36,'independent_pools':12,'same_pool_paired':True,'flat_three_methods_exact_same_indices':True,
      'original_sampler_unchanged':True,'seconds':time.monotonic()-START,'checkpoint_RSS_peak_bytes':PEAK})
    if sum(p.stat().st_size for p in O.rglob('*') if p.is_file())>192*1024**2:raise RuntimeError('192MiB output bound')
    dump(O/'contents.json',{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file()})
    print('COMPLETED',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'failure.json').exists():dump(O/'failure.json',{'status':'FAILED_STOP','error':repr(e),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
