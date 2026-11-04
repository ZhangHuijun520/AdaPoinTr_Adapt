"""Fixed two-group local representation; no anatomical labels or locator."""
import numpy as np

def group16(neighbors_relative,method):
 x=np.asarray(neighbors_relative,dtype=np.float64)
 if x.ndim!=3 or x.shape[1:]!=(16,3) or not np.isfinite(x).all():raise ValueError('finite [patch,16,3] required')
 if method not in ['A','B']:raise ValueError('fixed A/B only')
 a=np.empty((len(x),16),int)
 for i,p in enumerate(x):a[i]=np.lexsort((p[:,2],p[:,1],p[:,0],np.sum(p*p,axis=1)))
 base=np.concatenate([a[:,::2],a[:,1::2]],axis=1);fallback=np.zeros(len(x),bool);eigen=np.zeros((len(x),3))
 if method=='A':return base,fallback,eigen
 q=x-x.mean(1,keepdims=True);cov=np.einsum('nki,nkj->nij',q,q)/16;eigen,v=np.linalg.eigh(cov);fallback=(eigen[:,1]-eigen[:,0])<=1e-6*np.maximum(eigen.sum(1),1e-12)
 projection=np.einsum('nki,ni->nk',q,v[:,:,0]);out=base.copy()
 for i,p in enumerate(x):
  if not fallback[i]:out[i]=np.lexsort((p[:,2],p[:,1],p[:,0],projection[i]))
 return out,fallback,eigen

def symmetric_summary(features,indices):
 h=np.asarray(features);ix=np.asarray(indices)
 if h.ndim!=3 or h.shape[1:]!=(16,64) or ix.shape!=(len(h),16):raise ValueError('edge-feature contract')
 z=h[np.arange(len(h))[:,None],ix];s1=z[:,:8].max(1);s2=z[:,8:].max(1)
 return np.concatenate([(s1+s2)/2,np.abs(s1-s2)],axis=1)
