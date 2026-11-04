"""One sequential authorized geometry study; immutable sources, no torch/network."""
import os
os.environ['OMP_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
import sys, json, time, hashlib, importlib.util, csv, gc, traceback
from pathlib import Path
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
import psutil

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent/'cpu_result_v1'
spec=importlib.util.spec_from_file_location('prior',ROOT/'outputs/cranial_geometry_diagnostic_20261023/analyze_raw_pairs_v1.py')
prior=importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
START=time.monotonic(); CASE_START=START
def guard():
    assert time.monotonic()-START<3600,'batch timeout'
    assert time.monotonic()-CASE_START<900,'case timeout'
    assert psutil.Process().memory_info().rss<8*1024**3,'RSS budget'
    assert sum(p.stat().st_size for p in OUT.glob('*') if p.is_file())<1024**3,'output budget'
def save(name,obj):
    with (OUT/name).open('x',encoding='utf8') as f: json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
def surf(mask,other,A,o):
    xyz=[]; axes=[]; tags=[]
    for a in range(3):
        for s in (-1,1):
            q,j=prior.faces(mask,other,a,s); q=q.astype(float);q[:,a]+=s*.5
            xyz.append(q@A+o);axes.append(np.full(len(q),a,np.int8));tags.append(j)
    x=np.concatenate(xyz); ax=np.concatenate(axes);j=np.concatenate(tags)
    areas=np.array([np.linalg.norm(np.cross(A[(a+1)%3],A[(a+2)%3])) for a in range(3)])
    return x,ax,j,areas[ax]
def sample_faces(S,A,seed,n):
    x,ax,j,w=S;r=np.random.default_rng(seed)
    ids=r.choice(len(x),n,p=w/w.sum());p=x[ids].copy()
    uv=r.random((n,2))-.5
    for a in range(3):
        sel=ax[ids]==a;p[sel]+=uv[sel,0,None]*A[(a+1)%3]+uv[sel,1,None]*A[(a+2)%3]
    return p,ids
def mc(mask,A,o):
    v,f,_,_=marching_cubes(np.pad(mask,1),level=.5,allow_degenerate=False)
    v=(v-1)@A+o;t=v[f];w=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)/2
    return t,w
def sample_mc(M,seed,n):
    t,w=M;r=np.random.default_rng(seed);ids=r.choice(len(t),n,p=w/w.sum());uv=r.random((n,2));u=np.sqrt(uv[:,0]);v=uv[:,1]
    return (1-u[:,None])*t[ids,0]+(u*(1-v))[:,None]*t[ids,1]+(u*v)[:,None]*t[ids,2]
def distances(ref,p):
    tree=cKDTree(p);out=[]
    for b in range(0,len(ref),65536):
        guard();out.append(tree.query(ref[b:b+65536],workers=2)[0])
    return np.concatenate(out)
def metric(ref,p,w):
    d=distances(ref,p);order=np.argsort(d);cs=np.cumsum(w[order]);q=d[order[np.searchsorted(cs,.95*cs[-1])]]
    return {'p95_mm':float(q),'mean_mm':float(np.average(d,weights=w)),**{f'cover_{t}mm':float(np.average(d<=t,weights=w)) for t in (.5,1,2)}}
def test():
    z=np.zeros((5,5,5),bool);d=z.copy();g=z.copy();d[2,2,2]=1;g[3,2,2]=1
    A=np.diag([.4,.5,.7]);S=surf(d,g,A,np.ones(3));T=surf(g,d,A,np.ones(3))
    assert len(S[0])==6 and S[2].sum()==1
    assert np.allclose(S[0][S[2]],T[0][T[2]])
    assert np.isclose(S[3][S[2]].sum(),.35)
    p,ids=sample_faces(S,A,1,100);q,_=sample_faces(S,A,1,100);assert np.array_equal(p,q)
    assert metric(p,p,np.ones(100))['p95_mm']==0
    assert len(mc(d,A,np.zeros(3))[0])==8
    shell=np.ones((5,5,5),bool);shell[1:4,1:4,1:4]=0
    assert len(surf(shell,z,np.eye(3),np.zeros(3))[0])==204
    return 7
def phantom():
    rows=[]
    for thickness in (1.,3.,5.):
        for n in (8192,16384):
            r=np.random.default_rng(0);p=np.column_stack((r.uniform(-50,50,(n,2)),np.where(np.arange(n)%2,thickness/2,-thickness/2)))
            ids=cKDTree(p).query(p,k=33,workers=2)[1]
            for k in (16,32):
                rows.append({'kind':'analytic_parallel_surfaces','thickness_mm':thickness,'n':n,'k':k,'opposite_face_fraction':float(np.mean(p[ids[:,1:k+1],2]!=p[:,None,2]))})
    # Known continuous sphere shell + planar cap: radial and cap errors of voxel/MC points.
    for h,phase,angle in ((1.,0.,0.),(.7,.23,.4),(1.2,.31,.7)):
        a=np.arange(-24,24+h,h);x=np.stack(np.meshgrid(a,a,a,indexing='ij'),-1)+phase*h
        rad=np.linalg.norm(x,axis=-1);C=(rad<=20)&(rad>=17);normal=np.array([np.cos(angle),np.sin(angle),0.]);proj=x@normal
        G=C&(proj>10);D=C&~G;A=np.eye(3)*h;o=np.full(3,a[0]+phase*h)
        for label,mask,other in [('D',D,G),('G',G,D)]:
            S=surf(mask,other,A,o)
            for method in ('V0','V1','V2'):
                if method=='V0':p=np.argwhere(mask&~ndimage.binary_erosion(mask,structure=prior.STRUCT))@A+o
                elif method=='V1':p,_=sample_faces(S,A,0,8192)
                else:p=sample_mc(mc(mask,A,o),0,8192)
                rr=np.linalg.norm(p,axis=1);e=np.minimum(np.abs(rr-17),np.abs(rr-20))
                # On the valid annular cap also consider the exact cut plane.
                cap=(rr>=17)&(rr<=20);e[cap]=np.minimum(e[cap],np.abs(p[cap]@normal-10))
                rows.append({'kind':'analytic_shell_cut','spacing':h,'phase':phase,'angle':angle,'role':label,'method':method,'distance_to_analytic_boundary_p95_mm':float(np.percentile(e,95))})
    save('phantom.json',rows)
def main():
    global CASE_START
    OUT.mkdir(exist_ok=False)
    save('contract_tests.json',{'passed':test(),'scope':'targeted geometry checks; not complete production P3'})
    phantom();allrows=[];qc=[]
    scope=json.loads((ROOT/'outputs/cranial_geometry_diagnostic_20261023/raw_pairing_v1/scope.json').read_text(encoding='utf8'))
    for c in scope['cases']:
        CASE_START=time.monotonic();cid=c['dataset']+'_'+c['case_id'];print('START',cid,flush=True)
        paths={k:Path(v) for k,v in c['raw_paths'].items()};before={k:prior.sha(p) for k,p in paths.items()}
        for k,p in paths.items():assert before[k]==c['hashes_before'][str(p)],'source drift'
        C,A,o=prior.read_mask(paths['complete']);D,B,b=prior.read_mask(paths['defective']);G,F,f=prior.read_mask(paths['implant'])
        assert np.array_equal(A,B) and np.array_equal(A,F) and np.array_equal(o,b) and np.array_equal(o,f)
        assert np.array_equal(C,D|G) and not np.any(D&G)
        SD=surf(D,G,A,o);SG=surf(G,D,A,o)
        assert np.isclose(SD[3][SD[2]].sum(),SG[3][SG[2]].sum())
        assert np.array_equal(np.sort(SD[0][SD[2]],axis=0),np.sort(SG[0][SG[2]],axis=0))
        MD=mc(D,A,o);centers=np.argwhere(D&~ndimage.binary_erosion(D,structure=prior.STRUCT))@A+o
        # Fixed B reference independent of candidate RNG, Monte Carlo surface quadrature.
        bref=sample_mc(MD,99173,131072)
        case_rows=[]
        for seed in (0,1,2):
            pd,di=sample_faces(SD,A,seed,16384);pg,gi=sample_faces(SG,A,seed,16384)
            legacy=centers[np.random.default_rng(seed).choice(len(centers),8192,replace=False)]
            pmc=sample_mc(MD,seed,8192)
            for method,p,role,ids in [('V0',legacy,'D',None),('V1',pd[:8192],'D',di[:8192]),('V2',pmc,'D',None),('V1',pd,'D',di),('V1',pg[:8192],'G',gi[:8192]),('V1',pg,'G',gi)]:
                S=SD if role=='D' else SG
                for region,sel in [('all',np.ones(len(S[0]),bool)),('J',S[2]),('E',~S[2])]:
                    row={'case':cid,'seed':seed,'role':role,'method':method,'n':len(p),'reference':'A_face_center','region':region,**metric(S[0][sel],p,S[3][sel])};case_rows.append(row)
                if role=='D':case_rows.append({'case':cid,'seed':seed,'role':role,'method':method,'n':len(p),'reference':'B_MC_fixed_131072','region':'all',**metric(bref,p,np.ones(len(bref)))})
                if ids is not None:
                    sel=S[2];local=p[S[2][ids]]
                    if len(local):case_rows.append({'case':cid,'seed':seed,'role':role,'method':method,'n':len(p),'reference':'A_face_center','region':'J_provenance_only',**metric(S[0][sel],local,S[3][sel])})
                if seed==0:np.savez_compressed(OUT/(cid+'_'+role+'_'+method+'_'+str(len(p))+'.npz'),xyz=p,provenance_face_ids=np.array([],int) if ids is None else ids)
            guard()
        after={k:prior.sha(p) for k,p in paths.items()};assert before==after
        qc.append({'case':cid,'partition_mismatches':0,'J_area_mm2':float(SD[3][SD[2]].sum()),'source_hashes':before,'sources_unchanged':True,'elapsed_seconds':time.monotonic()-CASE_START})
        save(cid+'_metrics.json',case_rows);save(cid+'_qc.json',qc[-1]);allrows+=case_rows
        print('DONE',cid,flush=True)
        del C,D,G,SD,SG,MD,centers,bref;gc.collect()
    save('metrics.json',allrows);save('qc.json',qc)
    with (OUT/'metrics.csv').open('x',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    save('completion.json',{'status':'COMPLETED','cases':len(qc),'elapsed_seconds':time.monotonic()-START,'raw_sources_unchanged':True,'gpu_operations':0,'training_steps':0,'limitations':['B uses fixed Monte Carlo quadrature, convergence not certified','No global anatomical layer labels','No model/proxy computation','Phantom shell distance is sampled-to-analytic boundary, not continuous Hausdorff','No clinical accuracy claim']})
if __name__=='__main__':
    try:main()
    except BaseException:
        if OUT.exists():
            with (OUT/'failure.txt').open('x',encoding='utf8') as f:traceback.print_exc(file=f)
        raise
