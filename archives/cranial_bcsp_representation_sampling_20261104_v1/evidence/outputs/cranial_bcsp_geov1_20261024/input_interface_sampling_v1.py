"""Fixed six development cases and analytic shells; D-only PCA sampler."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLBACKEND='Agg')
import sys,json,time,hashlib,gc,importlib.util
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
import psutil
N=Path(__file__).resolve().parent;O=N/'input_interface_sampling_20261102_v1';O.mkdir(exist_ok=False)
os.environ['MPLCONFIGDIR']=str(O/'mplconfig')
spec=importlib.util.spec_from_file_location('geo',N/'cpu_geometry_package_v1.py');geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
START=time.monotonic()
protocol={'pool_points':32768,'PCA_neighbors':32,'candidate_top_fraction':.1,'candidate_score':'smallest local covariance eigenvalue / eigenvalue sum','enhanced_global':4096,'enhanced_local':4096,'input_total':8192,'target_total':8192,'seeds':[0,1,2],'D_only_sampler_arguments':'surface centers, face axes, physical face areas and affine; no G/R/J/complete mask','scope':'fixed six development cases plus three analytic shell discretizations; no tuning','limitations':'curvature is not a rim label; no anatomical inner/outer labels; descriptive pilot, no significance/gate'}
(O/'protocol.json').write_text(json.dumps(protocol,indent=2))
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf-8')
def guard():
 assert time.monotonic()-START<1800 and psutil.Process().memory_info().rss<8*1024**3
def draw(x,ax,w,A,rng,n):
 ids=rng.choice(len(x),n,p=w/w.sum());p=x[ids].copy();uv=rng.uniform(-.5,.5,(n,2))
 for a in range(3):
  q=ax[ids]==a;p[q]+=uv[q,0,None]*A[(a+1)%3]+uv[q,1,None]*A[(a+2)%3]
 return p,ids
def sampler(x,ax,w,A,seed):
 # Inputs contain only D boundary geometry. All candidate thresholds frozen above.
 rng=np.random.default_rng(seed);pool,faceids=draw(x,ax,w,A,rng,32768)
 _,nn=cKDTree(pool).query(pool,k=32,workers=2);score=np.empty(len(pool))
 for start in range(0,len(pool),2048):
  q=pool[nn[start:start+2048]];q=q-q.mean(1,keepdims=True);cov=np.einsum('nki,nkj->nij',q,q)/32;e=np.linalg.eigvalsh(cov);score[start:start+len(q)]=e[:,0]/np.maximum(e.sum(1),1e-12)
 top=np.argsort(score,kind='stable')[-3277:]
 local_ix=rng.choice(top,4096,replace=True)
 # Re-draw within the selected faces; no duplicate coordinates from replacing pool indices.
 localfaces=faceids[local_ix];lp=x[localfaces].copy();uv=rng.uniform(-.5,.5,(4096,2))
 for a in range(3):
  sel=ax[localfaces]==a;lp[sel]+=uv[sel,0,None]*A[(a+1)%3]+uv[sel,1,None]*A[(a+2)%3]
 glob,gi=draw(x,ax,w,A,rng,4096)
 return np.concatenate([glob,lp]),np.concatenate([gi,localfaces]),pool[top],{'PCA_score_top_min':float(score[top].min()),'PCA_score_median':float(np.median(score))}
def metrics(ref,p,w):
 d=cKDTree(p).query(ref,workers=2)[0];order=np.argsort(d);q=d[order[np.searchsorted(np.cumsum(w[order]),.95*w.sum())]]
 return {'p95_mm':float(q),'cover_2mm':float(np.average(d<=2,weights=w)),'cover_1mm':float(np.average(d<=1,weights=w))}
def run_case(cid,D,A,o,load_evaluation,phantom=False):
 # J metadata is obtained only after all three D-only selections complete.
 SD=geo.surf(D,np.zeros_like(D),A,o);x,ax,_,w=SD;samples=[]
 for seed in [0,1,2]:
  base,bi=geo.sample_faces(SD,A,seed,16384);base=base[:8192];bi=bi[:8192]
  p,ids,top,diagnostic=sampler(x,ax,w,A,seed);samples.append((seed,base,bi,p,ids,top,diagnostic));guard()
 G,C,target_binding=load_evaluation()
 J=geo.surf(D,G,A,o)[2];assert J.any()
 refs=x[J];treeJ=cKDTree(refs);rows=[]
 areaJ=float(w[J].sum());areaAll=float(w.sum())
 for seed,b,bi,p,ids,top,diag in samples:
  topdist=treeJ.query(top,workers=2)[0]
  for method,pts,fids in [('uniform8k',b,bi),('D_PCA_4k_plus_4k',p,ids)]:
   d=treeJ.query(pts,workers=2)[0];nn=cKDTree(pts).query(pts,k=2,workers=2)[0][:,1]
   row={'case':cid,'phantom':phantom,'seed':seed,'method':method,'input_points':len(pts),'J':metrics(refs,pts,w[J]),'E':metrics(x[~J],pts,w[~J]),'all':metrics(x,pts,w),'J_face_point_count':int(J[fids].sum()),'support_2mm_center_reference_count':int((d<=2).sum()),'NN_spacing_median_mm':float(np.median(nn)),'NN_spacing_p05_mm':float(np.percentile(nn,5)),'top_candidate_support_precision_2mm':float((topdist<=2).mean()),'J_area_fraction':areaJ/areaAll,'target':target_binding,**diag};rows.append(row)
   if seed==0:np.savez_compressed(O/(cid+'_'+method+'.npz'),xyz=pts,face_ids=fids)
 dump(O/(cid+'_metrics.json'),rows)
 print('DONE',cid,[(r['method'],round(r['J']['cover_2mm'],3),round(r['all']['cover_2mm'],3)) for r in rows[:2]],flush=True)
 return rows
allrows=[]
# Exactly reproduce the three existing shell phantom discretizations.
for h,phase,angle in [(1.,0.,0.),(.7,.23,.4),(1.2,.31,.7)]:
 a=np.arange(-24,24+h,h);x=np.stack(np.meshgrid(a,a,a,indexing='ij'),-1)+phase*h;rad=np.linalg.norm(x,axis=-1);C=(rad<=20)&(rad>=17);normal=np.array([np.cos(angle),np.sin(angle),0]);G=C&(x@normal>10);D=C&~G
 allrows+=run_case('phantom_'+str(h),D,np.eye(3)*h,np.full(3,a[0]+phase*h),lambda:(G,C,{'kind':'analytic shell target fixed; no model target artifact'}),True)
scope=json.loads((N.parent/'cranial_geometry_diagnostic_20261023/raw_pairing_v1/scope.json').read_text())
for c in scope['cases']:
 cid=c['dataset']+'_'+c['case_id'];paths={k:Path(v) for k,v in c['raw_paths'].items()};print('BEGIN',cid,flush=True)
 # Only D is decoded before selection; paths/hashes are source bindings, not geometry inputs.
 assert geo.prior.sha(paths['defective'])==c['hashes_before'][str(paths['defective'])]
 D,A,o=geo.prior.read_mask(paths['defective'])
 def evaluate():
  G,B,b=geo.prior.read_mask(paths['implant']);C,F,f=geo.prior.read_mask(paths['complete']);assert np.array_equal(A,B) and np.array_equal(A,F) and np.array_equal(o,b) and np.array_equal(o,f)
  assert np.array_equal(C,D|G) and not (D&G).any()
  for k,path in paths.items():assert geo.prior.sha(path)==c['hashes_before'][str(path)]
  target=N/'cpu_result_v1'/(cid+'_G_V1_8192.npz');assert target.exists();data=np.load(target);assert len(data['xyz'])==8192
  return G,C,{'path':str(target),'sha256':geo.prior.sha(target),'unchanged_existing_8192_target':True}
 allrows+=run_case(cid,D,A,o,evaluate);del D;gc.collect();guard()
dump(O/'metrics.json',allrows)
dump(O/'completion.json',{'cases_real':6,'phantoms':3,'rows':len(allrows),'seconds':time.monotonic()-START,'GPU':0,'training':0,'source_modifications':0,'PCA_selection_accesses_G_R_J':False})
