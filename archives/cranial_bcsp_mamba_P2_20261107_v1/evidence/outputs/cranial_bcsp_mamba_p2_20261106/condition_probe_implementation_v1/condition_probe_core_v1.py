"""Fixed linear information probe; no checkpoint loading or model training."""
import numpy as np

def require(ok,message):
    if not ok:raise ValueError(message)

def finite(x,columns=None):
    x=np.asarray(x,dtype=np.float64)
    require(x.ndim==2 and len(x)>0 and np.isfinite(x).all(),'finite nonempty matrix')
    if columns is not None:require(x.shape[1]==columns,'column count')
    return x

def moments(points):
    p=finite(points,3);mu=p.mean(0);radius=np.sqrt(np.mean(np.sum((p-mu)**2,axis=1)))
    require(radius>0,'positive radius required')
    return np.r_[mu,np.log(radius)]

def geometry18(partial):
    p=finite(partial,3);c=p-p.mean(0);cov=c.T@c/len(p)
    return np.r_[p.mean(0),cov[np.triu_indices(3)],np.quantile(p,[.1,.5,.9],axis=0,method='linear').T.ravel()]

def source_weights(sources):
    require(len(sources)>0,'sources required');counts={s:sources.count(s) for s in set(sources)}
    return np.array([1/(len(counts)*counts[s]) for s in sources],dtype=np.float64)

def fit_ridge(x,y,sources):
    x=finite(x);y=finite(y,4);require(len(x)==len(y)==len(sources),'training alignment')
    w=source_weights(list(sources));xm=w@x;ym=w@y
    xs=np.sqrt(w@((x-xm)**2));ys=np.sqrt(w@((y-ym)**2))
    xs_safe=np.where(xs>0,xs,1.);ys_safe=np.where(ys>0,ys,1.)
    X=(x-xm)/xs_safe;Y=(y-ym)/ys_safe;X[:,xs==0]=0;Y[:,ys==0]=0
    # mean-weighted residual sum over outputs + lambda||W||_F^2, lambda=1.
    a=X*np.sqrt(w[:,None]);b=Y*np.sqrt(w[:,None])
    # Dual for 1024 features / 315 rows; primal for the 18 geometry features.
    coef=(a.T@np.linalg.solve(a@a.T+np.eye(len(a)),b) if X.shape[1]>len(X)
          else np.linalg.solve(a.T@a+np.eye(X.shape[1]),a.T@b))
    require(np.isfinite(coef).all(),'finite coefficients')
    return dict(schema='fixed-source-weighted-ridge-v1',lambda_mean_objective=1.,x_mean=xm,x_scale=xs_safe,y_mean=ym,y_scale=ys_safe,coefficient=coef,constant_y=ys==0,train_sources=sorted(set(sources)))

def predict(fit,x):
    x=finite(x,len(fit['x_mean']));out=((x-fit['x_mean'])/fit['x_scale'])@fit['coefficient']
    out=out*fit['y_scale']+fit['y_mean'];out[:,fit['constant_y']]=fit['y_mean'][fit['constant_y']]
    require(np.isfinite(out).all(),'finite prediction');return out

def errors(pred,target,scales):
    pred=finite(pred,4);target=finite(target,4);s=np.asarray(scales,dtype=np.float64)
    require(pred.shape==target.shape and s.shape==(len(pred),) and np.isfinite(s).all() and (s>0).all(),'aligned scales')
    dist=np.linalg.norm(pred[:,:3]-target[:,:3],axis=1);r=np.exp(target[:,3]);require(np.isfinite(r).all() and (r>0).all(),'target radius')
    return np.c_[dist*s,dist/r,np.abs(pred[:,3]-target[:,3])]

def compare(train,dev):
    """Each row is an already frozen per-fold tensor record. No development fit."""
    require(len(train)==315 and len(dev)==105,'315/105 fixed fold scope')
    def validate(rows,ns):
        require(len({r['case_id'] for r in rows})==len(rows),'unique case ids')
        sources=[r['source_id'] for r in rows];require(len(set(sources))==ns and all(sources.count(s)==5 for s in set(sources)),'five defects/source')
        require(all(r['source_id']=='train:'+r['case_id'].split('__')[1] for r in rows),'source identity')
        require(all({r['case_id'].split('__',2)[2] for r in rows if r['source_id']==s}=={'bilateral','frontoorbital','parietotemporal','random_1','random_2'} for s in set(sources)),'five defect set')
    validate(train,63);validate(dev,21)
    ts={r['source_id'] for r in train};ds={r['source_id'] for r in dev};require(not ts&ds,'train/dev source leakage')
    require(len({r['fold'] for r in train+dev})==1 and len({r['variant'] for r in train+dev})==1,'one corresponding model/fold')
    yt=finite([r['target4'] for r in train],4);yd=finite([r['target4'] for r in dev],4);sources=[r['source_id'] for r in train]
    constant=source_weights(sources)@yt;preds={'constant':np.tile(constant,(len(dev),1)),'coarse':finite([r['coarse4'] for r in dev],4)};fits={}
    for key,width in [('geometry18',18),('feature1024',1024)]:
        x=finite([r[key] for r in train],width);z=finite([r[key] for r in dev],width)
        fits[key]=fit_ridge(x,yt,sources);preds[key]=predict(fits[key],z)
    metrics={k:errors(v,yd,[r['scale'] for r in dev]) for k,v in preds.items()}
    bysource={k:{s:np.mean(v[[r['source_id']==s for r in dev]],axis=0) for s in sorted(ds)} for k,v in metrics.items()}
    return dict(predictions=preds,case_errors=metrics,source_errors=bysource,fits=fits,development_fitted=False,model_updates=0)
