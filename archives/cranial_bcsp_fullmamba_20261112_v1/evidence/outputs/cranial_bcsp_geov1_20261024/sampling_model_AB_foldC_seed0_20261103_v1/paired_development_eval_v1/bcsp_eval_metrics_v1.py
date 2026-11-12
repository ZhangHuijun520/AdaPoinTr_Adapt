"""World-mm discrete surface-reference metrics; no model, file or GPU side effects."""
import numpy as np
from scipy.spatial import cKDTree

TAUS=(.5,1.,2.)
def require(ok,message):
 if not ok:raise ValueError(message)

def surface_references(g,d,affine,origin):
 g=np.asarray(g,dtype=bool);d=np.asarray(d,dtype=bool)
 a=np.asarray(affine,dtype=np.float64);o=np.asarray(origin,dtype=np.float64)
 require(g.ndim==3 and g.shape==d.shape and g.any() and not np.any(g&d),'G/D geometry')
 require(a.shape==(3,3) and o.shape==(3,) and np.isfinite(a).all() and np.isfinite(o).all() and abs(np.linalg.det(a))>1e-9,'affine')
 bounds=[np.flatnonzero(g.any(axis=tuple(k for k in range(3) if k!=axis))) for axis in range(3)]
 lo=np.array([x[0] for x in bounds]);hi=np.array([x[-1]+1 for x in bounds])
 crop=g[tuple(slice(x,y) for x,y in zip(lo,hi))]
 qs=[];axes=[];signs=[]
 for axis in range(3):
  for sign in [-1,1]:
   left=[slice(None)]*3;right=left.copy()
   left[axis]=slice(None,-1) if sign==1 else slice(1,None)
   right[axis]=slice(1,None) if sign==1 else slice(None,-1)
   exposed=crop.copy();exposed[tuple(left)]&=~crop[tuple(right)]
   q=np.argwhere(exposed).astype(np.int32)+lo
   qs.append(q);axes.append(np.full(len(q),axis,np.int8));signs.append(np.full(len(q),sign,np.int8))
 q=np.concatenate(qs);axis=np.concatenate(axes);sign=np.concatenate(signs)
 centers=q.astype(np.float64);centers[np.arange(len(q)),axis]+=.5*sign
 centers=centers@a+o
 areas=np.array([np.linalg.norm(np.cross(a[(k+1)%3],a[(k+2)%3])) for k in range(3)])[axis]
 neighbor=q.copy();neighbor[np.arange(len(q)),axis]+=sign
 inside=np.all((neighbor>=0)&(neighbor<np.array(d.shape)),axis=1)
 is_j=np.zeros(len(q),bool);is_j[inside]=d[tuple(neighbor[inside].T)]
 from skimage.measure import marching_cubes
 vertices,faces,_,_=marching_cubes(np.pad(crop.astype(np.float32),1),level=.5,allow_degenerate=False)
 world=(vertices.astype(np.float64)+lo-1)@a+o
 triangles=world[faces]
 b_centers=triangles.mean(axis=1)
 b_weights=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)*.5
 require(np.all(areas>0) and np.all(b_weights>0),'positive reference areas')
 return dict(a_centers=centers,a_weights=areas,a_is_j=is_j,a_axes=axis,
             b_centers=b_centers,b_weights=b_weights,affine=a,origin=o)

def a2_reference(ref):
 a=ref['affine'];offset=np.empty((3,4,3),np.float64)
 for axis in range(3):
  offset[axis]=[u*a[(axis+1)%3]+v*a[(axis+2)%3] for u in [-.25,.25] for v in [-.25,.25]]
 xyz=(ref['a_centers'][:,None,:]+offset[ref['a_axes']]).reshape(-1,3)
 return xyz,np.repeat(ref['a_weights']/4,4),np.repeat(ref['a_is_j'],4)

def nearest(query,points):
 query=np.asarray(query,np.float64);points=np.asarray(points,np.float64)
 require(query.ndim==points.ndim==2 and query.shape[1]==points.shape[1]==3,'NN shape')
 require(np.isfinite(query).all() and np.isfinite(points).all(),'NN finite')
 if not len(points):return np.full(len(query),np.inf)
 tree=cKDTree(points);parts=[]
 for start in range(0,len(query),65536):parts.append(tree.query(query[start:start+65536],workers=2)[0])
 return np.concatenate(parts) if parts else np.empty(0,np.float64)

def weighted_quantile(dist,weights,q=.95):
 dist=np.asarray(dist,np.float64);weights=np.asarray(weights,np.float64)
 require(dist.ndim==weights.ndim==1 and len(dist)==len(weights)>0,'quantile shape/nonempty')
 require(np.all(weights>0) and np.isfinite(weights).all() and 0<q<=1 and not np.isnan(dist).any(),'quantile values')
 order=np.argsort(dist,kind='mergesort');cum=np.cumsum(weights[order],dtype=np.float64)
 return float(dist[order[min(np.searchsorted(cum,q*cum[-1],side='left'),len(dist)-1)]])

def stats(dist,weights=None):
 dist=np.asarray(dist,np.float64)
 if not len(dist):return dict(status='EMPTY_REGION',mean_mm=None,p95_mm=None,max_mm=None,coverage={str(t):None for t in TAUS})
 w=np.ones(len(dist),np.float64) if weights is None else np.asarray(weights,np.float64)
 require(np.all(w>0) and np.isfinite(w).all(),'stats weights')
 return dict(status='OK' if np.isfinite(dist).all() else 'NONFINITE_DISTANCE',
  mean_mm=float(np.average(dist,weights=w)),p95_mm=weighted_quantile(dist,w),max_mm=float(dist.max()),
  coverage={str(t):float(np.average(dist<=t,weights=w)) for t in TAUS})

def score_cloud(points,ref,gt):
 p=np.asarray(points,np.float64);gt=np.asarray(gt,np.float64)
 require(gt.ndim==2 and gt.shape[1:]==(3,) and len(gt)>0 and np.isfinite(gt).all(),'GT reference shape/finite/nonempty')
 valid=p.ndim==2 and p.shape[1:]==(3,) and len(p)>0 and np.isfinite(p).all()
 n=len(p) if p.ndim>0 else 0
 a2,w2,j2=a2_reference(ref)
 groups={}
 for name,xyz,w,j in [('A1',ref['a_centers'],ref['a_weights'],ref['a_is_j']),('A2',a2,w2,j2)]:
  dist=nearest(xyz,p) if valid else np.full(len(xyz),np.inf)
  groups[name]={label:stats(dist[tag],w[tag]) for label,tag in [('all',np.ones(len(xyz),bool)),('E',~j),('J',j)]}
 db=nearest(ref['b_centers'],p) if valid else np.full(len(ref['b_centers']),np.inf)
 groups['B']={'all':stats(db,ref['b_weights']),'E':None,'J':None,'partition_status':'NO_EXACT_MC_INTERFACE_LABELS'}
 reverse={}
 for name,xyz in [('A2',a2),('B',ref['b_centers'])]:
  dist=nearest(p,xyz) if valid else np.array([np.inf])
  reverse[name]=stats(dist)
  reverse[name]['outlier_fraction']={str(t):float(np.mean(dist>t)) for t in TAUS}
 cd=.5*(float(nearest(p,gt).mean())+float(nearest(gt,p).mean())) if valid else float('inf')
 return dict(status='OK' if valid else 'INVALID_PREDICTION',point_count=n,
  duplicate_points=int(n-len(np.unique(p,axis=0))) if valid else None,
  primary_E_G_P95_mm=groups['A1']['E']['p95_mm'],regions=groups,reverse_discrete_reference=reverse,CD_L1_mm=cd)

def world_points(normalized,normalization):
 p=np.asarray(normalized,np.float64);c=np.asarray(normalization['center'],np.float64);s=float(normalization['scale'])
 require(p.ndim==2 and p.shape[1]==3 and c.shape==(3,) and np.isfinite(c).all() and np.isfinite(s) and s>0,'normalization')
 return p*s+c

def json_safe(value):
 if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [json_safe(v) for v in value]
 if isinstance(value,(float,np.floating)) and not np.isfinite(value):return 'POS_INF' if value==np.inf else 'UNDEFINED'
 return value

def paired_bootstrap(deltas,seed=20261024,n=10000):
 d=np.asarray(deltas,np.float64)
 if not len(d) or not np.isfinite(d).all():return dict(status='UNDEFINED_NONFINITE_SOURCE_DIFFERENCES',mean=None,CI95=None,source_count=len(d))
 rng=np.random.default_rng(seed);means=np.empty(n,np.float64)
 for i in range(n):means[i]=d[rng.integers(0,len(d),len(d))].mean()
 return dict(status='OK',mean=float(d.mean()),CI95=np.percentile(means,[2.5,97.5]).tolist(),source_count=len(d),bootstrap_replicates=n,seed=seed)
