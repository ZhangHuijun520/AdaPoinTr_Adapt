# -*- coding: utf-8 -*-
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLBACKEND='Agg')
import pathlib,sys,json,hashlib,time,importlib.util,gc,traceback
import numpy as np
from scipy.spatial import cKDTree
import psutil
N=pathlib.Path(__file__).resolve().parent/'outputs/cranial_bcsp_geov1_20261024';sys.path.insert(0,str(N))
from stageA_locator_v1 import localize,planes,fps_indices,PARAMETERS
sp=importlib.util.spec_from_file_location('geo',N/'cpu_geometry_package_v1.py');geo=importlib.util.module_from_spec(sp);sp.loader.exec_module(geo)
O=N/'interface_stageA_20261102_v1';O.mkdir(exist_ok=False);START=time.monotonic();peak=0
def save(name,obj):
 with (O/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,allow_nan=False)
def guard():
 global peak
 peak=max(peak,psutil.Process().memory_info().rss);assert peak<=8*1024**3 and time.monotonic()-START<1800 and sum(p.stat().st_size for p in O.glob('*') if p.is_file())<=512*1024**2
def brief(r):return {k:v for k,v in r.items() if not k.endswith('_indices')}
def metrics(q,w,p):
 d=cKDTree(p).query(q,workers=2)[0];ix=np.argsort(d);return {'cover6':float(np.average(d<=6,weights=w)),'cover2':float(np.average(d<=2,weights=w)),'p95_mm':float(d[ix[np.searchsorted(np.cumsum(w[ix]),.95*w.sum())]])}
def evaluate(cid,seed,p,r,S,artificial=False):
 q=S[0][S[2]];w=S[3][S[2]];anchors=p[r['anchor_indices']];base=p[r['global_FPS32_indices']];di=cKDTree(q).query(anchors)[0];idx=np.unique(np.concatenate(cKDTree(p).query_ball_point(anchors,6.)));nn=cKDTree(p[idx]).query(p[idx],k=2)[0][:,1] if len(idx)>1 else np.array([0.]);dj=cKDTree(q).query(p[idx])[0]
 row={'case':cid,'seed':seed,'artificial':artificial,**brief(r),'precision2':float(np.mean(di<=2)),'candidate':metrics(q,w,anchors),'global_FPS32':metrics(q,w,base),'D_support_points':len(idx),'D_support_points_near_J_2mm':int((dj<=2).sum()),'D_support_NN_median_mm':float(np.median(nn))}
 np.savez_compressed(O/(cid+'_seed'+str(seed)+'_anchors.npz'),anchors=anchors,valid_anchors=p[r['valid_anchor_indices']],candidates=p[r['candidate_indices']],global_FPS32=base)
 save(cid+'_seed'+str(seed)+'.json',row);guard();print('CASE',cid,seed,'success',r['success'],'valid',r['valid_anchors'],'precision2',row['precision2'],'gain6',row['candidate']['cover6']-row['global_FPS32']['cover6'],flush=True);return row
try:
 save('frozen_parameters.json',{'locator':PARAMETERS,'protocol_sha256':hashlib.sha256((N.parents[1]/'docs/cranial_bcsp_geov1_20261024/interface_local_geometry_minimal_protocol_zh_v1_20261102.md').read_bytes()).hexdigest(),'locator_sha256':hashlib.sha256((N/'stageA_locator_v1.py').read_bytes()).hexdigest(),'guard':'30 minutes,8GiB RSS,512MiB output,2 threads','invariance_rule':'report success invariance and anchor-set Hausdorff; <=2mm chosen before batch as geometric agreement tolerance, not new clinical threshold'})
 # Implementation contract checks on artificial inputs; no geometry pass required here.
 rng=np.random.default_rng(7);p=rng.uniform(-500,500,(8192,3));before=p.copy();r=localize(p);perm=rng.permutation(len(p));s=localize(p[perm]);assert np.array_equal(p,before);assert np.array_equal(p[r['anchor_indices']],p[perm][s['anchor_indices']]);assert not r['success'] and r['fallback_anchors']==32
 for bad in [np.zeros((4,3)),np.full((8192,3),np.nan),np.zeros((8192,3))]:
  try:localize(bad)
  except ValueError:pass
  else:raise AssertionError('bad tensor accepted')
 save('CPU_contract_tests.json',{'passed':['D-only signature','input immutable','point permutation exact coordinates','insufficient evidence rejected','fallback does not convert failure','wrong count rejected','NaN rejected','duplicate coordinates rejected'],'count':8});guard()
 rows=[];art=[];invariance=None
 for h,phase,angle in [(1.,0.,0.),(.7,.23,.4),(1.2,.31,.7)]:
  ax=np.arange(-24,24+h,h);x=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),-1)+phase*h;rad=np.linalg.norm(x,axis=-1);C=(rad<=20)&(rad>=17);G=C&(x@np.array([np.cos(angle),np.sin(angle),0])>10);D=C&~G;A=np.eye(3)*h;o=np.full(3,ax[0]+phase*h);S=geo.surf(D,G,A,o)
  p=np.load(N/'input_interface_sampling_20261102_v1'/('phantom_'+str(h)+'_uniform8k.npz'))['xyz'];r=localize(p);art.append(evaluate('phantom_'+str(h),0,p,r,S,True))
  if h==1.:
   ang=.37;Q=np.array([[np.cos(ang),-np.sin(ang),0],[np.sin(ang),np.cos(ang),0],[0,0,1]]);shift=np.array([17.,-9.,4.]);rp=localize(p@Q.T+shift);perm=np.random.default_rng(91).permutation(len(p));rr=localize(p[perm]);back=(p@Q.T+shift)[rp['anchor_indices']];back=(back-shift)@Q;a=p[r['anchor_indices']];haus=max(cKDTree(a).query(back)[0].max(),cKDTree(back).query(a)[0].max());invariance={'success_unchanged':r['success']==rp['success'],'anchor_Hausdorff_mm':float(haus),'geometric_agreement_2mm':bool(haus<=2),'permutation_exact':bool(np.array_equal(a,p[perm][rr['anchor_indices']]))};save('artificial_invariance.json',invariance)
 # One fixed negative/difficult geometry per class, no parameter sweep.
 for name in ['uncut_shell','parallel_planes','natural_hole_shell']:
  rng=np.random.default_rng(0)
  if name=='parallel_planes':p=np.column_stack([rng.uniform(-50,50,(8192,2)),np.where(np.arange(8192)%2,1.5,-1.5)])
  else:
   ax=np.arange(-24,25,1.);x=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),-1);rad=np.linalg.norm(x,axis=-1);C=(rad<=20)&(rad>=17)
   if name=='natural_hole_shell':C=C&~((x[...,0]**2+x[...,1]**2<=16)&(x[...,2]>0))
   S=geo.surf(C,np.zeros_like(C),np.eye(3),np.full(3,-24));p,_=geo.sample_faces(S,np.eye(3),0,8192)
  r=localize(p);save(name+'.json',brief(r));art.append({'case':name,'success':r['success'],'valid_anchors':r['valid_anchors']});guard();print('NEGATIVE',name,r['success'],flush=True)
 scope=json.loads((N.parent/'cranial_geometry_diagnostic_20261023/raw_pairing_v1/scope.json').read_text());targets={}
 for c in scope['cases']:
  cid=c['dataset']+'_'+c['case_id'];paths={k:pathlib.Path(v) for k,v in c['raw_paths'].items()};dp=paths['defective'];assert geo.prior.sha(dp)==c['hashes_before'][str(dp)];D,A,o=geo.prior.read_mask(dp);SD=geo.surf(D,np.zeros_like(D),A,o);prepared=[]
  for seed in [0,1,2]:
   p,ids=geo.sample_faces(SD,A,seed,16384);p=p[:8192]
   if seed==0:assert np.array_equal(p,np.load(N/'cpu_result_v1'/(cid+'_D_V1_8192.npz'))['xyz'])
   prepared.append((seed,p,localize(p)));guard()
  G,B,b=geo.prior.read_mask(paths['implant']);assert np.array_equal(A,B) and np.array_equal(o,b);S=geo.surf(D,G,A,o)
  for seed,p,r in prepared:rows.append(evaluate(cid,seed,p,r,S))
  target=N/'cpu_result_v1'/(cid+'_G_V1_8192.npz');targets[cid]=geo.prior.sha(target)
  for role in ['defective','implant']:assert geo.prior.sha(paths[role])==c['hashes_before'][str(paths[role])]
  del D,G,SD,S,prepared;gc.collect()
 cases=sorted({r['case'] for r in rows});cm=[]
 for cid in cases:
  rr=[r for r in rows if r['case']==cid];cm.append({'case':cid,'successful_seeds':sum(r['success'] for r in rr),'precision2':float(np.mean([r['precision2'] for r in rr])),'gain6':float(np.mean([r['candidate']['cover6']-r['global_FPS32']['cover6'] for r in rr]))})
 closed=next(r for r in art if r['case']=='uncut_shell');gates={'success_at_least_5_cases':sum(r['successful_seeds']>=2 for r in cm)>=5,'mean_precision_at_least_50pct':np.mean([r['precision2'] for r in cm])>=.5,'mean_gain6_at_least_10pp':np.mean([r['gain6'] for r in cm])>=.1,'no_case_drop_over_5pp':all(r['gain6']>=-.05 for r in cm),'uncut_shell_rejected':not closed['success'],'artificial_invariance':invariance['success_unchanged'] and invariance['geometric_agreement_2mm'] and invariance['permutation_exact']};gates={k:bool(v) for k,v in gates.items()}
 save('summary.json',{'status':'SCIENTIFIC_PASS' if all(gates.values()) else 'SCIENTIFIC_FAIL_STOP_NO_TUNING','gates':gates,'cases':cm,'artificial':art,'targets_unchanged_hashes':targets,'rows':len(rows),'seconds':time.monotonic()-START,'sampled_peak_RSS_bytes':peak,'models':0,'GPU':0,'training':0,'new_sources':0});print('GATES',json.dumps(gates),flush=True)
except BaseException:
 (O/'failure.txt').write_text(traceback.format_exc());raise
