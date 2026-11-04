# -*- coding: utf-8 -*-
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLBACKEND='Agg')
import pathlib,sys,json,hashlib,time,tarfile,io,traceback
import numpy as np
from scipy.spatial import cKDTree
import psutil
N=pathlib.Path(__file__).resolve().parent/'outputs/cranial_bcsp_geov1_20261024';sys.path.insert(0,str(N))
from multisurface_grouping_v1 import group16,symmetric_summary
O=N/'multisurface_CPU_20261102_v1';O.mkdir(exist_ok=False);START=time.monotonic();peak=0
def save(name,x):
 with (O/name).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,allow_nan=False)
def guard():
 global peak
 peak=max(peak,psutil.Process().memory_info().rss);assert time.monotonic()-START<=900 and peak<=8*1024**3 and sum(p.stat().st_size for p in O.glob('*') if p.is_file())<=256*1024**2
ang=.37;Q=np.array([[np.cos(ang),-np.sin(ang),0],[np.sin(ang),np.cos(ang),0],[0,0,1.]])
def agreement(a,b):return np.all(a[:,:8]==b[:,:8],1)
def sets_equal_unordered(a,b):
 sa=np.sort(a[:,:8],axis=1);sb=np.sort(b[:,:8],axis=1);other=np.sort(b[:,8:],axis=1);return np.all(sa==sb,1)|np.all(sa==other,1)
def stability(x,indices,method):
 rotated=x@Q.T;ri,fb,_=group16(rotated,method);return {'nondegenerate_patches':int((~fb).sum()),'same_partition_fraction':float(sets_equal_unordered(indices,ri).mean()),'nondegenerate_same_partition_fraction':float(sets_equal_unordered(indices[~fb],ri[~fb]).mean()) if (~fb).any() else None}
def layer_metric(ix,labels,z,height):
 lab=labels[np.arange(len(ix))[:,None],ix];correct=(lab[:,:8]==0).sum(1)+(lab[:,8:]==1).sum(1);purity=np.maximum(correct,16-correct)/16
 zz=z[np.arange(len(ix))[:,None],ix];est=np.abs(zz[:,:8].mean(1)-zz[:,8:].mean(1));both=(labels.min(1)==0)&(labels.max(1)==1)
 return {'best_label_swap_accuracy_mean':float(purity.mean()),'both_layers_present_fraction':float(both.mean()),'accuracy_given_both_layers':float(purity[both].mean()) if both.any() else None,'separation_MAE_mm':float(np.abs(est-height).mean()),'both_layer_representatives_within1mm':float((np.maximum(np.abs(np.minimum(zz[:,:8].mean(1),zz[:,8:].mean(1))+height/2),np.abs(np.maximum(zz[:,:8].mean(1),zz[:,8:].mean(1))-height/2))<=1).mean())}
try:
 protocol=N.parents[1]/'docs/cranial_bcsp_geov1_20261024/local_multisurface_minimal_hypothesis_zh_v1_20261102.md'
 save('scope.json',{'protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),'implementation_sha256':hashlib.sha256((N/'multisurface_grouping_v1.py').read_bytes()).hexdigest(),'methods':['A distance-interleaved 8+8','B smallest-PCA-projection median 8+8'],'k':16,'no_axis_or_parameter_search':True,'artificial_rigid_test':'fixed z rotation .37 rad, translation applied to world coordinates then relative coordinates; no new KNN','budget_seconds':900,'layer_purity_definition':'best binary layer-label assignment accuracy allowing group swap; missing-layer patches score .5; conditional two-layer results also reported','sphere_systematic_worse_rule':'mean B-A binary layer purity over each of three shell settings must be nonnegative; J patches separately reported, not labeled inner/outer'})
 # Artificial implementation contracts, not hypothesis tests.
 rng=np.random.default_rng(11);x=rng.normal(size=(24,16,3));h=rng.normal(size=(24,16,64));original=x.copy();tests=[]
 for method in ['A','B']:
  ix,fb,e=group16(x,method);assert np.array_equal(np.sort(ix,axis=1),np.tile(np.arange(16),(len(x),1)));tests.append(method+' equal groups cover all16')
  u=symmetric_summary(h,ix);sw=np.concatenate([ix[:,8:],ix[:,:8]],axis=1);assert np.array_equal(u,symmetric_summary(h,sw));tests.append(method+' group-swap invariant fusion')
  perm=rng.permutation(16);ip,_,_=group16(x[:,perm],method);mapped=perm[ip];assert sets_equal_unordered(ix,mapped).all() and np.allclose(u,symmetric_summary(h[:,perm],ip));tests.append(method+' point-permutation invariant partition/fusion')
 assert np.array_equal(x,original);tests.append('input immutable')
 _,fb,_=group16(np.zeros((1,16,3)),'B');assert fb[0];tests.append('degenerate covariance falls back')
 for bad in [np.zeros((2,15,3)),np.full((2,16,3),np.nan)]:
  try:group16(bad,'B')
  except ValueError:pass
  else:raise AssertionError('invalid grouping input accepted')
 tests.append('invalid shape and nonfinite rejected');save('CPU_contracts.json',{'passed':tests,'count':len(tests),'no_model_or_learned_feature_computation':True})
 parallel=[];stabilities=[]
 for height in [1.,3.,5.]:
  for n in [8192,16384]:
   rng=np.random.default_rng(0);p=np.column_stack([rng.uniform(-50,50,(n,2)),np.where(np.arange(n)%2,height/2,-height/2)]);nn=cKDTree(p).query(p,k=33,workers=2)[1][:,1:17];relative=p[nn]-p[:,None];labels=(p[nn,2]>0).astype(int)
   row={'kind':'parallel','thickness_mm':height,'n':n,'neighbors':'existing k16 excludes self; no k32 comparison'}
   for method in ['A','B']:
    ix,fb,e=group16(relative,method);row[method]=layer_metric(ix,labels,p[nn,2],height);row[method]['fallback_fraction']=float(fb.mean());st=stability(relative,ix,method);row[method]['rigid_partition']=st
    if method=='B':stabilities.append(st)
   parallel.append(row);save('parallel_'+str(height)+'_'+str(n)+'.json',row);print('PARALLEL',height,n,row['A']['best_label_swap_accuracy_mean'],row['B']['best_label_swap_accuracy_mean'],flush=True);guard()
 # Existing shell point sets, with fixed512 surrogate centers and16 neighbors.
 import importlib.util
 spec=importlib.util.spec_from_file_location('cpu_geo',N/'cpu_geometry_package_v1.py');geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
 spec=importlib.util.spec_from_file_location('fps_geo',N/'consolidated_binding_probe_v1.py');fpsmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(fpsmod)
 shells=[];real=[]
 for hh,phase,angle in [(1.,0.,0.),(.7,.23,.4),(1.2,.31,.7)]:
  ax=np.arange(-24,24+hh,hh);w=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),-1)+phase*hh;rad=np.linalg.norm(w,axis=-1);C=(rad<=20)&(rad>=17);G=C&(w@np.array([np.cos(angle),np.sin(angle),0])>10);D=C&~G;A=np.eye(3)*hh;o=np.full(3,ax[0]+phase*hh);S=geo.surf(D,G,A,o);p,ids=geo.sample_faces(S,A,0,16384);p=p[:8192];ids=ids[:8192];centers=fpsmod.fps(p,512);nn=cKDTree(p).query(p[centers],k=16,workers=2)[1];rel=p[nn]-p[centers,None];jt=S[2][ids[nn]];radius=np.linalg.norm(p[nn],axis=2);labels=(abs(radius-20)<abs(radius-17)).astype(int);valid=~jt.any(1)
  row={'kind':'shell','spacing':hh,'non_J_patches':int(valid.sum()),'patches_with_J':int((~valid).sum())}
  for method in ['A','B']:
   ix,fb,e=group16(rel,method);row[method]=layer_metric(ix[valid],labels[valid],radius[valid]-18.5,3.);row[method]['fallback_fraction']=float(fb.mean());row[method]['rigid_partition']=stability(rel,ix,method)
   selected=jt[np.arange(512)[:,None],ix];row[method]['J_neighbor_balance_mean_abs_difference']=float(np.mean(abs(selected[:,:8].sum(1)-selected[:,8:].sum(1))));row[method]['J_patches_not_anatomically_labeled']=int((~valid).sum())
   if method=='B':stabilities.append(row[method]['rigid_partition'])
  shells.append(row);save('shell_'+str(hh)+'.json',row);guard()
 # Single-plane/uncut shell controls: only relative geometric fragmentation is interpretable.
 rng=np.random.default_rng(0);single=np.column_stack([rng.uniform(-50,50,(8192,2)),np.zeros(8192)]);ax=np.arange(-24,25,1.);w=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),-1);rad=np.linalg.norm(w,axis=-1);C=(rad<=20)&(rad>=17);S=geo.surf(C,np.zeros_like(C),np.eye(3),np.full(3,-24));uncut,_=geo.sample_faces(S,np.eye(3),0,8192)
 for name,p in [('single_plane',single),('uncut_shell',uncut)]:
  ii=fpsmod.fps(p,512);nn=cKDTree(p).query(p[ii],k=16,workers=2)[1];rel=p[nn]-p[ii,None];ix,fb,e=group16(rel,'B');save(name+'.json',{'B_fallback_fraction':float(fb.mean()),'B_rigid':stability(rel,ix,'B'),'interpretation':'two groups are forced even on one surface; no anatomical separation label','no_new_model':True});guard()
 # Six existing CPU surrogate point/neighborhood sets; no new FPS or16k real sampling.
 bindings=json.loads((N/'consolidated_binding_v1/input_hashes.json').read_text())
 for b in bindings:
  cid=b['case'];path=N/'cpu_result_v1'/(cid+'_D_V1_8192.npz');expected=b['hashes'][str(path.resolve())];assert hashlib.sha256(path.read_bytes()).hexdigest()==expected;p=np.load(path)['xyz'];ii=np.load(N/'consolidated_binding_v1'/(cid+'_8192_fps_indices.npz'))['first'];nn=cKDTree(p).query(p[ii],k=16,workers=2)[1];rel=p[nn]-p[ii,None];item={'case':cid,'kind':'historical_CPU_surrogate_not_actual_model','methods':{}}
  for method in ['A','B']:
   ix,fb,e=group16(rel,method);item['methods'][method]={'fallback_fraction':float(fb.mean()),'rigid':stability(rel,ix,method)}
   np.savez_compressed(O/(cid+'_'+method+'_groups.npz'),query=p[ii],neighbors=p[nn],groups=ix)
  real.append(item);guard()
 arc=pathlib.Path('E:/ResearchBackups/AdaPoinTr/BCSP_INPUT_DENSITY_V1/2026-11-02_actual_proxy_trace/development_predictions_v1.tar.gz');assert hashlib.sha256(arc.read_bytes()).hexdigest()=='637cc82bb5ce20f3ef2f115df5147accf5792e300b095f6d792e07c4840d3181'
 actual=[]
 with tarfile.open(arc) as t:
  for m in t.getmembers():
   if not m.name.endswith('_trace.npz'):continue
   z=np.load(io.BytesIO(t.extractfile(m).read()));q=z['graph2_query_coordinates'][0].T;k=z['graph2_key_coordinates'][0].T;nn=z['graph2_knn_indices'][0].astype(int);scale=next(r for r in json.loads((N/'development_eval_v1/reference_bank_v2/reference_manifest_v1.json').read_text())['cases'] if r['case_id'] in m.name)['normalization']['scale'];rel=(k[nn]-q[:,None])*scale;item={'trace':m.name,'kind':'actual_saved_CUDA_graph2','methods':{}}
   for method in ['A','B']:
    ix,fb,e=group16(rel,method);item['methods'][method]={'fallback_fraction':float(fb.mean()),'rigid':stability(rel,ix,method)};np.savez_compressed(O/(pathlib.Path(m.name).stem+'_'+method+'_groups.npz'),neighbors_relative_mm=rel,groups=ix)
   actual.append(item);guard()
 byheight=[]
 for h in [1.,3.,5.]:
  rr=[r for r in parallel if r['thickness_mm']==h];byheight.append({'height':h,'accuracy_gain':float(np.mean([r['B']['best_label_swap_accuracy_mean']-r['A']['best_label_swap_accuracy_mean'] for r in rr])),'separation_error_change':float(np.mean([r['B']['separation_MAE_mm']-r['A']['separation_MAE_mm'] for r in rr]))})
 gates={'contracts':True,'artificial_nondegenerate_rigid_invariance':all(s['nondegenerate_same_partition_fraction'] is None or s['nondegenerate_same_partition_fraction']==1 for s in stabilities),'purity_gain10pp_two_heights':sum(r['accuracy_gain']>=.1 for r in byheight)>=2,'no_height_drop5pp':all(r['accuracy_gain']>=-.05 for r in byheight),'separation_error_not_increased':all(r['separation_error_change']<=1e-12 for r in byheight),'no_shell_setting_mean_purity_drop':all(r['B']['best_label_swap_accuracy_mean']>=r['A']['best_label_swap_accuracy_mean'] for r in shells)}
 save('results.json',{'status':'GEOMETRIC_PASS_PENDING_REVIEW' if all(gates.values()) else 'SCIENTIFIC_FAIL_STOP_NO_RETRY','gates':gates,'height_results':byheight,'parallel':parallel,'shell':shells,'real_CPU':real,'actual_CUDA_saved':actual,'seconds':time.monotonic()-START,'RSS_sampled_peak_bytes':peak,'model_calls':0,'new_GPU':0,'training':0});print('GATES',json.dumps(gates),flush=True)
except BaseException:
 (O/'failure.txt').write_text(traceback.format_exc());raise
