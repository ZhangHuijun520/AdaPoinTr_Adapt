from pathlib import Path
import os
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['MPLBACKEND']='Agg';os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import json,hashlib,tarfile,io,csv,time,importlib.util,html
W=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;start=time.monotonic()
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def check(r):
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and digest(p)==r['sha256'];return p
scope=json.loads((D/'fixed_visual_scope_v1.json').read_bytes());check(scope['source_audit'])
q=json.loads((W/'outputs/scq_rive_score_implementation_20261116_v1/local_scoring_execution_request_v1.json').read_bytes());idx=json.loads(check(q['score_case_index']).read_bytes());scored=[json.loads(x) for x in (W/'outputs/scq_rive_score_implementation_20261116_v1/unified_scores_v1/case_metrics.jsonl').read_text(encoding='utf-8').splitlines()];lookup={(r['fold'],r['case_id'],r['arm']):r for r in scored};cases={(r['fold'],r['case_id']):r for r in idx['cases']};bindings={(r['fold'],r['case_id'],r['arm']):r for r in idx['prediction_records']}
mp=check(q['implementation']['metrics']);sp=importlib.util.spec_from_file_location('frozen_geom_metric',mp);metric=importlib.util.module_from_spec(sp);sp.loader.exec_module(metric)
archive=check(q['archive_inputs']['SCQ_RIVE']['archive']);figdir=D/'figures';figdir.mkdir();records=[];transitions=[];panels=[];binding_records=[];world_data={}
plt.rcParams.update({'font.size':8,'axes.titlesize':8,'axes.labelsize':7,'figure.facecolor':'white','font.family':'DejaVu Sans'})
def pose(x,gt):
 mu=x.mean(0);g=gt.mean(0);rad=np.sqrt(np.mean(np.sum((x-mu)**2,axis=1)));rg=np.sqrt(np.mean(np.sum((gt-g)**2,axis=1)))
 return mu,float(np.linalg.norm(mu-g)),float(rad/rg)
def stats(x,ref,gt,a2):
 dist=metric.nearest(ref['a_centers'],x);e=~ref['a_is_j'];j=ref['a_is_j'];w=ref['a_weights'];rev=metric.nearest(x,a2);mu,ce,ratio=pose(x,gt)
 return dict(centroid=mu.tolist(),centroid_offset_mm=ce,radius_ratio=ratio,E_P95_mm=metric.weighted_quantile(dist[e],w[e]),J_P95_mm=metric.weighted_quantile(dist[j],w[j]),E_cover2=float(np.average(dist[e]<=2,weights=w[e])),J_cover2=float(np.average(dist[j]<=2,weights=w[j])),reverse_A2_P95_mm=float(np.quantile(rev,.95,method='higher')),reverse_outlier20=float(np.mean(rev>20)),CD_L1_mm=.5*(metric.nearest(x,gt).mean()+metric.nearest(gt,x).mean())),rev
with tarfile.open(archive,'r:gz') as tar:
 for ci,item in enumerate(scope['cases']):
  assert time.monotonic()-start<600
  key=item['fold'],item['case_id'];case=cases[key]
  with np.load(check(case['reference']),allow_pickle=False) as z:ref={k:z[k].copy() for k in z.files}
  with np.load(check(case['point_file']),allow_pickle=False) as z:gt=metric.world_points(z['implant'],case['normalization']);partial=metric.world_points(z['partial'],case['normalization'])
  a2=metric.a2_reference(ref)[0];clouds={};distances={};metrics={}
  for arm in scope['arms']:
   b=bindings[key[0],key[1],arm];blob=tar.extractfile(b['member']).read();assert len(blob)==b['bytes'] and hashlib.sha256(blob).hexdigest()==b['sha256'];binding_records.append(b)
   with np.load(io.BytesIO(blob),allow_pickle=False) as z:arr={k:z[k].copy() for k in z.files}
   assert np.allclose(arr['Q0']+arr['delta0'],arr['Q1'],rtol=2e-5,atol=2e-6) and np.allclose(arr['Q1']+arr['delta1'],arr['Q2'],rtol=2e-5,atol=2e-6)
   for st,k in [('Q0','Q0'),('Q1','Q1'),('Q2','Q2'),('dense','prediction')]:
    x=metric.world_points(arr[k],case['normalization']);v,rev=stats(x,ref,gt,a2);v.update(fold=key[0],case_id=key[1],role=item['role'],arm=arm,stage=st,points=len(x));records.append(v);clouds[arm,st]=x;distances[arm,st]=rev;metrics[arm,st]=v
   actual=lookup[key[0],key[1],arm]['metrics'];v=metrics[arm,'dense']
   for x,y in [('E_P95_mm','E_P95_mm'),('J_P95_mm','J_P95_mm'),('E_cover2','E_coverage_2.0mm'),('J_cover2','J_coverage_2.0mm'),('CD_L1_mm','CD_L1_mm'),('reverse_outlier20','reverse_A2_outlier_20.0mm'),('centroid_offset_mm','centroid_offset_mm')]:assert np.isclose(v[x],actual[y],rtol=1e-10,atol=1e-10),(key,arm,x)
   for a,b in zip(scope['stages'][:-1],scope['stages'][1:]):
    va,vb=metrics[arm,a],metrics[arm,b];err=np.asarray(va['centroid'])-gt.mean(0);delta=np.asarray(vb['centroid'])-va['centroid'];dot=2*float(err@delta);sq=float(delta@delta);change=vb['centroid_offset_mm']**2-va['centroid_offset_mm']**2;assert np.isclose(change,dot+sq,rtol=1e-9,atol=1e-8)
    transitions.append(dict(fold=key[0],case_id=key[1],role=item['role'],arm=arm,transition=a+'->'+b,centroid_squared_change_mm2=change,direction_term_2e_dot_delta_mm2=dot,step_squared_norm_mm2=sq,**{'delta_'+k:vb[k]-va[k] for k in ['centroid_offset_mm','E_P95_mm','J_P95_mm','E_cover2','J_cover2','reverse_outlier20','radius_ratio']}))
  # Shared equal-scale world bounds include every full stage cloud and GT; display does not filter metrics.
  combined=np.concatenate([gt,*clouds.values()]);lo=combined.min(0);hi=combined.max(0);mid=(lo+hi)/2;span=max(hi-lo)*1.08
  gtshow=gt[::max(1,int(np.ceil(len(gt)/2200)))];pshow=partial[::max(1,int(np.ceil(len(partial)/1800)))];jxyz=ref['a_centers'][ref['a_is_j']];jshow=jxyz[::max(1,int(np.ceil(len(jxyz)/900)))]
  fig,axs=plt.subplots(6,4,figsize=(14,16.5),layout='constrained')
  for ai,arm in enumerate(scope['arms']):
   for vi,(u,v,label) in enumerate([(0,1,'XY'),(0,2,'XZ'),(1,2,'YZ')]):
    for sj,st in enumerate(scope['stages']):
     ax=axs[ai*3+vi,sj];x=clouds[arm,st];rev=distances[arm,st];vstat=metrics[arm,st];step=max(1,int(np.ceil(len(x)/2200)))
     ax.scatter(pshow[:,u],pshow[:,v],s=.4,c='#9ab5bb',alpha=.16,rasterized=True);ax.scatter(gtshow[:,u],gtshow[:,v],s=.7,c='#737373',alpha=.27,rasterized=True);ax.scatter(jshow[:,u],jshow[:,v],s=1,c='#d81b60',alpha=.4,rasterized=True)
     ax.scatter(x[::step,u],x[::step,v],c=rev[::step],s=2.8 if st!='dense' else 1.4,cmap='viridis',vmin=0,vmax=40,alpha=.85,rasterized=True)
     mu=x.mean(0);ax.scatter(*mu[[u,v]],marker='+',s=35,c='#f04d25',linewidths=1)
     ax.set_xlim(mid[u]-span/2,mid[u]+span/2);ax.set_ylim(mid[v]-span/2,mid[v]+span/2);ax.set_aspect('equal');ax.grid(alpha=.12)
     ax.set_title(f"{st} | centroid {vstat['centroid_offset_mm']:.1f}mm\nE95 {vstat['E_P95_mm']:.1f} J95 {vstat['J_P95_mm']:.1f}; J2 {vstat['J_cover2']*100:.1f}%")
     if sj==0:ax.set_ylabel(arm+' '+label+' (mm)')
     if ai==1 and vi==2:ax.set_xlabel('world '+label+' (mm)')
  fig.suptitle(key[0]+' '+key[1]+' | '+item['role']+'\nGray=GT; pale teal=input; magenta=GT interface; +=prediction centroid.\nColor=prediction-to-A2 distance (display saturated at40mm; statistics untruncated).',fontsize=11)
  fig.colorbar(ScalarMappable(norm=Normalize(0,40),cmap='viridis'),ax=axs.ravel().tolist(),fraction=.012,pad=.015,label='prediction-to-A2 distance (mm)')
  name=key[0]+'__'+key[1]+'.png';fig.savefig(figdir/name,dpi=135);plt.close(fig);panels.append(dict(**item,image='figures/'+name));print('DIAGNOSED',key[0],key[1],flush=True)
assert len(records)==88 and len(transitions)==66 and len(binding_records)==22 and digest(archive)==q['archive_inputs']['SCQ_RIVE']['archive']['sha256']
for name,rs in [('stage_metrics_v1.csv',records),('stage_transition_changes_v1.csv',transitions)]:
 flat=[{k:v for k,v in r.items() if k!='centroid'} for r in rs]
 with (D/name).open('x',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
result=dict(status='FIXED11_EXISTING_PREDICTION_STAGE_DIAGNOSTIC_COMPLETE',cases=scope['cases'],records=records,transitions=transitions,bindings=binding_records,panels=panels,seconds=time.monotonic()-start,checks=dict(selected_before_array_reads=True,exact22_prediction_members=True,all88stage_metrics=True,dense_matches_frozen_scores=True,stage_equations=True,centroid_squared_decomposition=True,archive_unchanged=True),operations=dict(forward=0,training=0,checkpoint_loads=0,server_calls=0),limitations=['Posthoc selected-case diagnosis, not unbiased method performance or causal intervention.','Stage point counts differ256vs8192; do not attribute all Q2-to-dense changes to one module.','Nearest reference distances are discrete geometry evidence, not clinical validation.','Display only uses deterministic strides; all metrics use full arrays, no registration/outlier removal.'])
(D/'stage_diagnostic_result_v1.json').write_bytes((json.dumps(metric.json_safe(result),indent=2)+'\n').encode());assert sum(p.stat().st_size for p in D.rglob('*') if p.is_file())<536870912
htmltext='<!doctype html><meta charset="utf-8"><title>RIVE fixed11 diagnostics</title><style>body{font:16px sans-serif;max-width:1450px;margin:auto}img{width:100%}section{border-top:2px solid #ccc;margin-top:30px}</style><h1>RIVE: 9 new severe cases + 2 fixed improved controls</h1><p>Existing predictions only; same bounds and color scale per case; no registration or filtering. Selected diagnostics, not independent efficacy evidence.</p>'+''.join('<section><h2>'+html.escape(x['fold']+' '+x['case_id']+' '+x['role'])+'</h2><img loading="lazy" src="'+x['image']+'"></section>' for x in panels)
(D/'index.html').write_text(htmltext,encoding='utf-8');print(json.dumps(dict(status=result['status'],stage_rows=88,transitions=66,seconds=result['seconds'])))
