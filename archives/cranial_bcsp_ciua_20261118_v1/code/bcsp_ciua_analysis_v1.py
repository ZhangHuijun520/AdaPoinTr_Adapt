"""Fixed CIUA mathematics. No imports of numerical runtimes until invoked."""
TYPES=('bilateral','frontoorbital','parietotemporal','random_1','random_2')
FEATURES=('D18','z','zF','zf')


def need(ok, why):
    if not ok:raise ValueError(why)


def validate_rows(rows):
    need(len(rows)==840,'exact840 model-case rows')
    need(len({(r['run'],r['case_id']) for r in rows})==840,'unique model-case')
    need({r['run'] for r in rows}=={'G2_C','G2_D'},'G2 C/D only')
    devs=[]
    for fold in ('C','D'):
        sets=[]
        for role,n,ns in [('train',315,63),('development',105,21)]:
            rr=[r for r in rows if r['fold']==fold and r['role']==role]
            need(len(rr)==n,'315/105 role count')
            sources={r['source_id'] for r in rr};need(len(sources)==ns,'63/21 sources')
            for s in sources:
                cases=[r for r in rr if r['source_id']==s]
                need(len(cases)==5 and {r['case_id'].split('__',2)[2] for r in cases}==set(TYPES),'five defects/source')
            for r in rr:
                need(r['run']=='G2_'+fold and r['source_id']=='train:'+r['case_id'].split('__')[1] and r['case_id'].startswith('train__'),'canonical identity')
            sets.append(sources)
        need(not sets[0]&sets[1],'samefold source leakage')
        devs.append(sets[1])
    need(not devs[0]&devs[1],'C/D dev sources disjoint')


def moments(np,p):
    p=np.asarray(p,dtype=np.float64)
    need(p.ndim==2 and p.shape[1]==3 and len(p)>0 and np.isfinite(p).all(),'finite point cloud')
    c=p.mean(0);r=float(np.sqrt(((p-c)**2).sum(1).mean()))
    need(r>1e-6,'degenerate radius')
    return np.r_[c,np.log(r)]


def octants(np,p,b):
    p=np.asarray(p,dtype=np.float64);b=np.asarray(b,dtype=np.float64)
    need(p.ndim==2 and p.shape[1]==3 and len(p)>0 and b.shape==(3,) and np.isfinite(p).all() and np.isfinite(b).all(),'octant finite points and D bbox')
    k=(p>=b).astype(np.int64)@np.array([1,2,4],dtype=np.int64)
    return np.bincount(k,minlength=8)/len(p)


def targets(np,G,D):
    b=(D.min(0).astype(np.float64)+D.max(0).astype(np.float64))/2
    return np.r_[moments(np,G),octants(np,G,b)]


def simplex(np,p):
    p=np.asarray(p,dtype=np.float64);need(p.ndim==2 and p.shape[1]==8 and np.isfinite(p).all(),'8D finite simplex input')
    u=np.sort(p,axis=1)[:,::-1];cs=np.cumsum(u,axis=1)-1
    good=u-cs/np.arange(1,9)[None,:]>0
    rho=good.sum(1)-1;theta=cs[np.arange(len(p)),rho]/(rho+1)
    return np.maximum(p-theta[:,None],0)


def weights(np,sources):
    groups=sorted(set(sources));need(groups,'nonempty sources')
    return np.array([1/(len(groups)*sources.count(s)) for s in sources],dtype=np.float64)


def fit(np,x,y,sources):
    x=np.asarray(x,dtype=np.float64);y=np.asarray(y,dtype=np.float64)
    need(x.ndim==y.ndim==2 and len(x)==len(y)==len(sources) and np.isfinite(x).all() and np.isfinite(y).all(),'finite aligned fit')
    w=weights(np,list(sources));xm=w@x;ym=w@y
    xs=np.sqrt(w@((x-xm)**2));ys=np.sqrt(w@((y-ym)**2))
    xscale=np.where(xs>0,xs,1.);yscale=np.where(ys>0,ys,1.)
    X=(x-xm)/xscale;Y=(y-ym)/yscale;X[:,xs==0]=0;Y[:,ys==0]=0
    a=X*np.sqrt(w[:,None]);b=Y*np.sqrt(w[:,None])
    if x.shape[1]>len(x):W=a.T@np.linalg.solve(a@a.T+np.eye(len(a)),b)
    else:W=np.linalg.solve(a.T@a+np.eye(x.shape[1]),a.T@b)
    residual=float(np.abs(a.T@(a@W-b)+W).max())
    need(np.isfinite(W).all() and residual<=1e-8,'ridge stationary lambda1 mean objective')
    singular=np.linalg.svd(a,compute_uv=False)
    return dict(x_mean=xm,x_scale=xscale,y_mean=ym,y_scale=yscale,coefficient=W,constant_y=ys==0,constant_x=xs==0,stationarity=residual,dimension=x.shape[1],rank=int(np.linalg.matrix_rank(a)),singular_values=singular,effective_df=float(np.sum(singular**2/(singular**2+1))),train_sources=sorted(set(sources)),lambda_mean_objective=1.)


def predict(np,f,x):
    x=np.asarray(x,dtype=np.float64)
    need(x.ndim==2 and x.shape[1]==len(f['x_mean']) and np.isfinite(x).all(),'finite predict input')
    z=(x-f['x_mean'])/f['x_scale'];z[:,f['constant_x']]=0
    out=(z@f['coefficient'])*f['y_scale']+f['y_mean'];out[:,f['constant_y']]=f['y_mean'][f['constant_y']]
    need(np.isfinite(out).all(),'finite readout predictions')
    return out


def errors(np,p,y,scales):
    p=np.asarray(p,dtype=np.float64);y=np.asarray(y,dtype=np.float64);s=np.asarray(scales,dtype=np.float64)
    need(p.shape==y.shape and p.ndim==2 and p.shape[1]==12 and s.shape==(len(y),) and np.isfinite(p).all() and np.isfinite(y).all() and np.isfinite(s).all() and (s>0).all(),'12 target prediction / world scale')
    return np.c_[np.linalg.norm(p[:,:3]-y[:,:3],axis=1)*s,np.abs(p[:,3]-y[:,3]),.5*np.abs(simplex(np,p[:,4:])-y[:,4:]).sum(1)]


def group(np,values,rows):
    sources=sorted({r['source_id'] for r in rows})
    out=np.stack([np.asarray(values)[[i for i,r in enumerate(rows) if r['source_id']==s]].mean(0) for s in sources])
    return sources,out


def permutation(np,rows,fold):
    need(fold in ('C','D'),'fold seed')
    sources=sorted({r['source_id'] for r in rows})
    need(len(sources)==63 and len(rows)==315,'63 train source permutation')
    perm=np.random.Generator(np.random.PCG64(2026111803 if fold=='C' else 2026111804)).permutation(63)
    lookup={(r['source_id'],r['case_id'].split('__',2)[2]):i for i,r in enumerate(rows)}
    mapping=dict(zip(sources,[sources[j] for j in perm]))
    indices=np.array([lookup[mapping[r['source_id']],r['case_id'].split('__',2)[2]] for r in rows])
    return indices,dict(mapping=mapping,fixed_points=sum(k==v for k,v in mapping.items()))


def bootstrap(np,fold):
    need(fold in ('C','D'),'bootstrap fold')
    return np.random.Generator(np.random.PCG64(2026111801 if fold=='C' else 2026111802)).integers(0,21,size=(2000,21))


def compare(np,a,b,indices):
    d=np.asarray(a)-np.asarray(b);need(d.shape==(21,3) and np.isfinite(d).all(),'21 source paired difference')
    return dict(mean=d.mean(0).tolist(),median=np.median(d,axis=0).tolist(),improved=(d < -1e-12).sum(0).tolist(),worse=(d>1e-12).sum(0).tolist(),tied=(np.abs(d)<=1e-12).sum(0).tolist(),CI95=np.quantile(d[indices].mean(1),[.025,.975],axis=0,method='linear').tolist(),source_differences=d.tolist())


def pass_gate(np,a,b,centroid):
    d=np.asarray(a)-np.asarray(b)
    # 1e-12 is arithmetic boundary handling, not a new scientific effect threshold.
    return bool(d[:,0].mean()<=-centroid+1e-12 and d[:,2].mean()<=-.03+1e-12 and (d[:,0]<-1e-12).sum()>=14 and (d[:,2]<-1e-12).sum()>=14)


def decide(np,folds):
    result={}
    for feature in ('z','zF','zf'):
        I=all(f['octant_informative'] and pass_gate(np,f['source_errors'][feature],f['source_errors']['D18'],2.) for f in folds.values())
        U=I and all(pass_gate(np,f['source_errors'][feature],f['source_errors']['Q'],1.) for f in folds.values())
        trade=any((f['source_errors'][feature]-f['source_errors']['Q'])[:,1].mean()>.01+1e-12 for f in folds.values())
        extra=feature!='z' and all(pass_gate(np,f['source_errors'][feature],f['source_errors']['z'],1.) and (f['source_errors'][feature]-f['source_errors']['z'])[:,1].mean()<=.01+1e-12 for f in folds.values())
        result[feature]=dict(I_PASS=bool(I),U_PASS=bool(U and not trade),TRADEOFF=bool(trade),aggregation_increment=bool(extra),training_authorized=False)
    return result


def analyze(np,rows,features,labels,q_labels):
    """Complete fixed two-fold path; callers perform payload identity/authorization."""
    validate_rows(rows)
    need(set(features)==set(FEATURES),'fixed four feature groups')
    widths=dict(D18=18,z=1024,zF=1408,zf=1408)
    for key in FEATURES:
        need(features[key].shape==(840,widths[key]) and np.isfinite(features[key]).all(),'fixed feature dimensions')
    need(labels.shape==q_labels.shape==(840,12) and np.isfinite(labels).all() and np.isfinite(q_labels).all(),'840 finite labels and Q labels')
    need(all((y[:,4:]>=0).all() and np.allclose(y[:,4:].sum(1),1,rtol=0,atol=1e-12) for y in (labels,q_labels)),'valid GT and native Q octants')
    output={};solve_count=0
    for fold in ('C','D'):
        it=[i for i,r in enumerate(rows) if r['fold']==fold and r['role']=='train'];iv=[i for i,r in enumerate(rows) if r['fold']==fold and r['role']=='development']
        tr=[rows[i] for i in it];dv=[rows[i] for i in iv];sources=[r['source_id'] for r in tr]
        yt=labels[it];yv=labels[iv];scale=np.array([r['normalization']['scale'] for r in dv]);ts=np.array([r['normalization']['scale'] for r in tr])
        perm,pinfo=permutation(np,tr,fold);bt=bootstrap(np,fold);preds={};fits={};train_errors={}
        const=weights(np,sources)@yt;preds['constant']=np.broadcast_to(const,(105,12)).copy();preds['Q']=q_labels[iv].copy()
        for key in FEATURES:
            for control,Y in [('real',yt),('permuted',yt[perm])]:
                f=fit(np,features[key][it],Y,sources);solve_count+=1
                name=key if control=='real' else key+'_permuted'
                fits[name]=f;preds[name]=predict(np,f,features[key][iv])
                train_errors[name]=errors(np,predict(np,f,features[key][it]),yt,ts)
        case_errors={k:errors(np,v,yv,scale) for k,v in preds.items()}
        se={k:group(np,v,dv)[1] for k,v in case_errors.items()}
        comparisons={k+'_minus_'+b:compare(np,se[k],se[b],bt) for k in ('z','zF','zf') for b in ('D18','Q','z') if k!=b}
        pi=yt[:,4:];entropy=-(np.where(pi>0,pi,1)*np.log(np.where(pi>0,pi,1))).sum(1)
        output[fold]=dict(rows=dv,predictions=preds,fits=fits,case_errors=case_errors,train_errors=train_errors,source_order=group(np,case_errors['Q'],dv)[0],source_errors=se,comparisons=comparisons,bootstrap_indices=bt,permutation=pinfo,octant_informative=bool(np.max(np.abs(pi-pi[0]))>1e-12),octant_train_stats=dict(variance=pi.var(0).tolist(),entropy_mean=float(entropy.mean()),nonzero_bins=(pi>0).sum(1).tolist(),dominant_fraction=pi.max(1).tolist()),type_means={typ:{k:val[[i for i,r in enumerate(dv) if r['case_id'].endswith('__'+typ)]].mean(0).tolist() for k,val in case_errors.items()} for typ in TYPES})
    need(solve_count==16,'exact16 fixed multioutput solves')
    return dict(folds=output,decisions=decide(np,output),solves=solve_count,case_model_rows=210,feature_methods=10,training_authorized=False)
