"""Frozen D-only three-plane locator. No mask, G, R or labels accepted."""
import numpy as np
from scipy.spatial import cKDTree

PARAMETERS=dict(centers=512,radius_mm=8.,maximum_neighbors=128,minimum_neighbors=24,hypotheses=96,plane_threshold_mm=1.,minimum_plane_support=8,parallel_dot=.9,thickness_min_mm=1.,thickness_max_mm=12.,transverse_dot=.35,bridge_tolerance_mm=1.5,component_radius_mm=6.,minimum_component_points=6,anchors=32,minimum_valid_anchors=16,seed=20261102)

def canonical(p):
 return np.lexsort((p[:,2],p[:,1],p[:,0]))

def fps_indices(p,n):
 if len(p)==0:return np.empty(0,int)
 order=canonical(p);x=p[order];d=np.full(len(x),np.inf);chosen=np.zeros(len(x),bool);far=int(np.argmax(np.sum((x-x.mean(0))**2,axis=1)));ids=[]
 for _ in range(min(n,len(x))):
  ids.append(order[far]);chosen[far]=True;d=np.minimum(d,np.sum((x-x[far])**2,axis=1));d[chosen]=-1.;far=int(np.argmax(d))
 return np.array(ids,int)

def planes(p,rng):
 remain=np.arange(len(p));result=[];valid_counts=[]
 for _ in range(3):
  if len(remain)<8:break
  q=p[remain];tri=np.array([rng.choice(len(q),3,replace=False) for _ in range(96)])
  normal=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]);length=np.linalg.norm(normal,axis=1);ok=length>1e-10;valid_counts.append(int(ok.sum()))
  if not ok.any():break
  normal=normal[ok]/length[ok,None];offset=np.einsum('ij,ij->i',normal,q[tri[ok,0]])
  distances=np.abs(q@normal.T-offset);ins=distances<=1.;counts=ins.sum(0);means=np.sum(distances*ins,axis=0)/np.maximum(counts,1)
  best=np.lexsort((np.arange(len(counts)),means,-counts))[0]
  if counts[best]<8:break
  ii=remain[ins[:,best]];result.append((normal[best],p[ii].mean(0),ii));remain=remain[~ins[:,best]]
 return result,valid_counts

def localize(partial_mm):
 p=np.asarray(partial_mm,dtype=np.float64)
 if p.shape!=(8192,3) or not np.isfinite(p).all():raise ValueError('finite 8192x3 D-only input required')
 if len(np.unique(p,axis=0))!=8192:raise ValueError('duplicate coordinates not supported by fixed tie contract')
 # Canonical order also governs RANSAC hypotheses and geometric ties.
 order=canonical(p);p=p[order];tree=cKDTree(p);centers=fps_indices(p,512);rng=np.random.default_rng(20261102)
 counts=dict(insufficient_neighbors=0,insufficient_planes=0,no_bridge_configuration=0,accepted_patches=0);candidate=np.zeros(len(p),bool);patches=[];hyp=[]
 for ci in centers:
  idx=np.array(tree.query_ball_point(p[ci],8.),int);dist=np.sum((p[idx]-p[ci])**2,axis=1);idx=idx[np.lexsort((idx,dist))][:128]
  if len(idx)<24:counts['insufficient_neighbors']+=1;continue
  pp=p[idx];fit,v=planes(pp,rng);hyp.extend(v)
  if len(fit)<3:counts['insufficient_planes']+=1;continue
  found=[]
  for i,j,k in [(0,1,2),(0,2,1),(1,2,0)]:
   a,ca,ia=fit[i];b,cb,ib=fit[j];c,cc,ic=fit[k]
   dot=float(a@b)
   if abs(dot)<.9 or abs(a@c)>.35 or abs(b@c)>.35:continue
   normal=a+(b if dot>=0 else -b);normal/=np.linalg.norm(normal);sep=abs(float((cb-ca)@normal))
   if not 1.<=sep<=12.:continue
   proj=pp[ic]@normal;pa=float(ca@normal);pb=float(cb@normal)
   if np.min(abs(proj-pa))>1.5 or np.min(abs(proj-pb))>1.5:continue
   found.append((min(len(ia),len(ib),len(ic))/len(pp),idx[ic],sep))
  if not found:counts['no_bridge_configuration']+=1;continue
  counts['accepted_patches']+=1
  for score,ids,sep in sorted(found,key=lambda x:-x[0]):candidate[ids]=True;patches.append(dict(score=score,points=len(ids),separation_mm=sep))
 ids=np.flatnonzero(candidate);component_sizes=[];kept=np.empty(0,int)
 if len(ids):
  adj=cKDTree(p[ids]).query_ball_point(p[ids],6.);seen=np.zeros(len(ids),bool);keep=[]
  for i in range(len(ids)):
   if seen[i]:continue
   seen[i]=True;stack=[i];component=[]
   while stack:
    v=stack.pop();component.append(v)
    for nb in adj[v]:
     if not seen[nb]:seen[nb]=True;stack.append(nb)
   component_sizes.append(len(component))
   if len(component)>=6:keep.extend(component)
  kept=ids[np.array(keep,int)] if keep else np.empty(0,int)
 valid=kept[fps_indices(p[kept],32)] if len(kept) else np.empty(0,int)
 anchors=list(valid)
 for ix in centers:
  if len(anchors)>=32:break
  if ix not in anchors:anchors.append(int(ix))
 assert len(anchors)==32
 return {'anchor_indices':order[np.array(anchors)],'valid_anchor_indices':order[valid],'candidate_indices':order[kept],'global_FPS32_indices':order[centers[:32]],'success':len(valid)>=16,'valid_anchors':len(valid),'fallback_anchors':32-len(valid),'patch_counts':counts,'candidate_component_sizes':component_sizes,'valid_hypotheses_total':int(sum(hyp)),'plane_fit_attempts':len(hyp),'patch_scores':sorted(patches,key=lambda x:-x['score'])}
