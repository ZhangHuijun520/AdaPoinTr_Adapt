"""Five protocol-selected existing cases; CPU geometry and plots, no model import."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLBACKEND='Agg')
from pathlib import Path
import json,hashlib,io,tarfile,importlib.util,time,html,math
R=Path(__file__).resolve().parents[2];F=Path(__file__).resolve().parent;S=R/'outputs/spcg_score_implementation_20261117_v1';O=R/'outputs/spcg_coarse_dense_visualization_20261117_v1'
O.mkdir(exist_ok=False);os.environ['MPLCONFIGDIR']=str(O/'mpl_cache')
import numpy as np
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
from PIL import Image,ImageOps,ImageDraw
START=time.monotonic();READ=[];ARMS=['G0','G1','G2'];STAGES=['coarse','dense'];CHECKS={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):
 p=Path(p);return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def exact(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in [p,*p.parents]);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p);READ.append(r);return p
def load(p):return json.loads(Path(p).read_bytes())
def emit(name,value):
 with (O/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
def check(name,ok):assert ok,name;CHECKS[name]=True
def stats(x,gt,a2tree,ref,metric):
 c=x.mean(0);gc=gt.mean(0);rg=np.sqrt(((x-c)**2).sum(1).mean());grg=np.sqrt(((gt-gc)**2).sum(1).mean())
 reverse=a2tree.query(x,workers=2)[0];dist=cKDTree(x).query(ref['a_centers'],workers=2)[0];support={}
 for label,mask in [('E',~ref['a_is_j']),('J',ref['a_is_j'])]:support[label]=metric.stats(dist[mask],ref['a_weights'][mask])
 return dict(points=len(x),centroid_mm=c.tolist(),centroid_error_vector_mm=(c-gc).tolist(),centroid_offset_mm=float(np.linalg.norm(c-gc)),radius_gyration_ratio=float(rg/grg),bbox_mm=[x.min(0).tolist(),x.max(0).tolist()],to_A2_P95_mm=float(np.quantile(reverse,.95)),to_A2_max_mm=float(reverse.max()),to_A2_gt20_fraction=float((reverse>20).mean()),support=support),reverse
def draw_case(cid,fold,D,G,J,clouds,distances,metrics,box,roi,u,v,local=False):
 fig,axes=plt.subplots(3,2,figsize=(12,12));fig.subplots_adjust(left=.075,right=.87,bottom=.09,top=.885,hspace=.39,wspace=.23)
 plane='XYZ'[u]+'XYZ'[v];mode='GT-ROI DISPLAY ONLY' if local else 'GLOBAL - ALL OUTLIERS INCLUDED'
 fig.suptitle(f'{cid} | Fold {fold} | {plane} | {mode}',fontsize=13,y=.98)
 fig.text(.5,.944,'Rows G0 / G1 / G2; columns coarse256 / dense8192. Native world mm; no registration.',ha='center',fontsize=10)
 fig.text(.5,.919,'Gray=input; teal=GT8192; purple=J faces; model color=distance to A2 (cap40mm).',ha='center',fontsize=9)
 for i,arm in enumerate(ARMS):
  for j,stage in enumerate(STAGES):
   ax=axes[i,j];x=clouds[arm][stage];m=metrics[arm][stage]
   for pts,color,size,alpha in [(D,'#94a3b8',.65,.17),(G,'#009688',1.2,.33),(J,'#a855f7',.85,.3)]:ax.scatter(pts[:,u],pts[:,v],s=size,c=color,alpha=alpha,edgecolors='none',rasterized=True)
   ax.scatter(x[:,u],x[:,v],c=distances[arm][stage],cmap='magma',vmin=0,vmax=40,s=12 if stage=='coarse' else 1.7,alpha=.95 if stage=='coarse' else .8,edgecolors='none',rasterized=True)
   ax.scatter([x[:,u].mean()],[x[:,v].mean()],marker='+',s=70,c='#111827',linewidths=1.2);ax.scatter([G[:,u].mean()],[G[:,v].mean()],marker='x',s=45,c='#009688',linewidths=1.2)
   limits=roi if local else box;ax.set_xlim(limits[:,u]);ax.set_ylim(limits[:,v]);ax.set_aspect('equal',adjustable='box');ax.set_xlabel('XYZ'[u]+' mm',fontsize=8);ax.set_ylabel('XYZ'[v]+' mm',fontsize=8);ax.tick_params(labelsize=8);ax.grid(alpha=.15)
   if not local:ax.add_patch(Rectangle((roi[0,u],roi[0,v]),roi[1,u]-roi[0,u],roi[1,v]-roi[0,v],fill=False,ls='--',lw=.75,color='#475569'))
   text=('%s / %s | centroid %.1fmm | radius %.2f\nE95 %.1f | J95 %.1f | J2 %.1f%% | tail>20 %.1f%%')%(arm,stage,m['centroid_offset_mm'],m['radius_gyration_ratio'],m['support']['E']['p95_mm'],m['support']['J']['p95_mm'],100*m['support']['J']['coverage']['2.0'],100*m['to_A2_gt20_fraction'])
   if local:text+='\n%d/%d model points outside 3D GT ROI'%(m['points_outside_GT_ROI'],len(x))
   ax.set_title(text,fontsize=8.5)
 cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,40),cmap='magma'),cax=fig.add_axes([.905,.25,.018,.49]));cb.set_label('Point-to-A2 distance / mm; >=40 capped',fontsize=9)
 fig.text(.48,.032,'Coarse/dense have DIFFERENT point budgets; support gain is descriptive, not causal.\n'+('Local axes can hide outliers; use global panels and reported outside counts.' if local else 'Same equal-aspect global limits for every model/stage. Dashed = GT bbox +10mm. Projection overlap is not3D fit.'),ha='center',fontsize=8.5)
 name=cid+'_'+plane+('_ROI' if local else '_global')+'.png';fig.savefig(O/name,dpi=155,facecolor='white');plt.close(fig);return name
def main():
 audit=load(F/'audit_verification_v1.json');check('formal_score_freeze_pass',audit['status']=='FORMAL_SPCG_THREE_ARM_TWOFOLD_POST_SCORE_FREEZE_AUDIT_PASS')
 for root,key in [(S/'unified_scores_v1','output'),(S/'authorized_execution_v1','execution')]:
  for name,r in audit['inventory'][key].items():exact(dict(path=str(root/name),bytes=r['bytes'],sha256=r['sha256']))
 q=load(S/'SPCG_local_scoring_execution_request_v1.json');check('request_identity',sha(S/'SPCG_local_scoring_execution_request_v1.json')==audit['request_sha256'])
 idx=load(exact(q['score_case_index']));rows=[json.loads(l) for l in (S/'unified_scores_v1/case_metrics.jsonl').read_text(encoding='utf-8').splitlines()];lookup={(r['fold'],r['case_id'],r['arm']):r for r in rows}
 ids=sorted({(r['fold'],r['case_id']) for r in rows});candidates=[]
 for f,cid in ids:
  a,b=lookup[f,cid,'G1'],lookup[f,cid,'G2'];delta=b['metrics']['E_P95_mm']-a['metrics']['E_P95_mm']
  if b['risk_labels']['severe_geometry'] and not a['risk_labels']['severe_geometry']:candidates.append(dict(fold=f,case_id=cid,delta_E_G2_minus_G1_mm=delta,selection='posthoc_new_severe'))
 selected=sorted(candidates,key=lambda v:(-v['delta_E_G2_minus_G1_mm'],v['case_id']))[:3]
 for f in ['C','D']:
  options=[dict(fold=f,case_id=cid,delta_E_G2_minus_G1_mm=lookup[f,cid,'G2']['metrics']['E_P95_mm']-lookup[f,cid,'G1']['metrics']['E_P95_mm'],selection='posthoc_improved_control') for ff,cid in ids if ff==f and not lookup[f,cid,'G2']['risk_labels']['severe_geometry']]
  best=min(options,key=lambda v:(v['delta_E_G2_minus_G1_mm'],v['case_id']));assert best['delta_E_G2_minus_G1_mm']<0;selected.append(best)
 check('exact_five_unique_protocol_selected_cases',len(selected)==len({v['case_id'] for v in selected})==5)
 scope=dict(status='FROZEN_BEFORE_SELECTED_ARRAY_READ',selected=selected,selection_rule='Top3 G2 new-severe versusG1 by descending deltaE thencase_id; per-fold minimum deltaE with G2 nonsevere for2 controls',source_request_sha256=audit['request_sha256'],arrays='15 existing NPZ, coarse256 and dense8192 only',plots='all-model/stage shared equal world axes; XY/XZ/YZ global and XY GTbbox+10mm detail',no_GT_alignment=True,no_point_deletion=True,no_forward=True,no_training=True,no_parameter_scan=True,no_formal_gate=True,Memory='NOT_COLLECTED',resource_budget=dict(wall_seconds=900),limitations=['Selection uses outcomes and is explanatory, not new confirmation.','Coarse256 versusdense8192 distance gains include point-budget and reconstruction effects.'])
 emit('frozen_case_scope_v1.json',scope)
 spec=importlib.util.spec_from_file_location('frozen_metric_for_selected_geometry',exact(q['implementation']['metrics']));metric=importlib.util.module_from_spec(spec);spec.loader.exec_module(metric)
 archive=q['archive_inputs']['SPCG']['archive'];path=exact(archive);bindings={(r['fold'],r['arm'],r['case_id']):r for r in idx['prediction_records']};caseby={v['case_id']:v for v in idx['cases']};results=[];pngs=[]
 with tarfile.open(path,'r:gz') as tar:
  members=tar.getmembers();check('frozen_archive635_regular_members',len(members)==635 and all(m.isfile() for m in members) and len({m.name for m in members})==635)
  for selected_case in selected:
   assert time.monotonic()-START<900,'time budget'
   cid=selected_case['case_id'];f=selected_case['fold'];case=caseby[cid]
   with np.load(exact(case['point_file']),allow_pickle=False) as z:D=metric.world_points(z['partial'],case['normalization']);G=metric.world_points(z['implant'],case['normalization'])
   with np.load(exact(case['reference']),allow_pickle=False) as z:ref={k:z[k] for k in z.files}
   a2,_,_=metric.a2_reference(ref);a2tree=cKDTree(a2);J=ref['a_centers'][ref['a_is_j']];clouds={};distances={};metrics={};prediction_bindings=[]
   for arm in ARMS:
    b=bindings[f,arm,cid];blob=tar.extractfile(b['member']).read();assert len(blob)==b['bytes'] and hashlib.sha256(blob).hexdigest()==b['sha256'];prediction_bindings.append(b)
    with np.load(io.BytesIO(blob),allow_pickle=False) as z:
     assert z.files==['prediction','coarse'];values={k:z[k].copy() for k in z.files}
    assert values['prediction'].shape==(8192,3) and values['coarse'].shape==(256,3) and all(v.dtype==np.float32 and np.isfinite(v).all() for v in values.values())
    clouds[arm]={'coarse':metric.world_points(values['coarse'],case['normalization']),'dense':metric.world_points(values['prediction'],case['normalization'])};metrics[arm]={};distances[arm]={}
    for stage,x in clouds[arm].items():metrics[arm][stage],distances[arm][stage]=stats(x,G,a2tree,ref,metric)
    dense=metrics[arm]['dense'];frozen=lookup[f,cid,arm]
    assert np.isclose(dense['centroid_offset_mm'],frozen['metrics']['centroid_offset_mm'],rtol=1e-10,atol=1e-9)
    assert all(np.isclose(dense['support'][label]['p95_mm'],frozen['metrics'][label+'_P95_mm'],rtol=1e-10,atol=1e-9) for label in ['E','J'])
    assert np.isclose(dense['to_A2_gt20_fraction'],frozen['metrics']['reverse_A2_outlier_20.0mm'])
    co=clouds[arm]['coarse'];de=clouds[arm]['dense'];offset=de.reshape(256,32,3)-co[:,None,:]
    metrics[arm]['dense_frozen_metrics']=frozen['metrics'];metrics[arm]['frozen_risk_labels']=frozen['risk_labels'];metrics[arm]['dense_minus_coarse']=dict(centroid_shift_vector_mm=(de.mean(0)-co.mean(0)).tolist(),centroid_shift_mm=float(np.linalg.norm(de.mean(0)-co.mean(0))),centroid_error_change_mm=dense['centroid_offset_mm']-metrics[arm]['coarse']['centroid_offset_mm'],radius_ratio_change=dense['radius_gyration_ratio']-metrics[arm]['coarse']['radius_gyration_ratio'],E_P95_change_mm=dense['support']['E']['p95_mm']-metrics[arm]['coarse']['support']['E']['p95_mm'],J_P95_change_mm=dense['support']['J']['p95_mm']-metrics[arm]['coarse']['support']['J']['p95_mm'],offspring_to_own_coarse_RMS_mm=float(np.sqrt(np.mean(np.sum(offset**2,axis=2)))),mapping_note='Existing dense.reshape(256,32,3) within each model only; slots do not imply anatomical matches acrossmodels.')
   roi=np.stack([G.min(0)-10,G.max(0)+10]);allxyz=np.concatenate([D,G]+[x for a in ARMS for x in clouds[a].values()]);lo=allxyz.min(0);hi=allxyz.max(0);center=(hi+lo)/2;half=max(hi-lo)*.54;box=np.stack([center-half,center+half])
   for arm in ARMS:
    for stage,x in clouds[arm].items():metrics[arm][stage]['points_outside_GT_ROI']=int((~np.all((x>=roi[0])&(x<=roi[1]),axis=1)).sum())
   figures=[draw_case(cid,f,D,G,J,clouds,distances,metrics,box,roi,*uv) for uv in [(0,1),(0,2),(1,2)]];figures.append(draw_case(cid,f,D,G,J,clouds,distances,metrics,box,roi,0,1,local=True));pngs.extend(figures)
   results.append(dict(**selected_case,normalization=case['normalization'],global_world_bounds_mm=box.tolist(),GT_ROI_display_bounds_mm=roi.tolist(),metrics=metrics,prediction_bindings=prediction_bindings,figures=figures,all_outliers_retained=True))
   print(json.dumps(dict(status='FIXED_CASE_GEOMETRY_COMPLETE',case_id=cid,figures=len(figures)),ensure_ascii=False),flush=True)
 check('15_predictions_30_stages_20_figures',len(results)==5 and sum(len(r['prediction_bindings']) for r in results)==15 and len(pngs)==20)
 check('selected_dense_metrics_reproduce_frozen_scores',True)
 for r in list(READ):exact(r)
 check('all_read_bound_sources_unchanged',True)
 emit('fixed_case_geometry_metrics_v1.json',dict(status='EXISTING_PREDICTIONS_ONLY_GEOMETRY_COMPLETE',cases=results,checks=CHECKS,source_request_sha256=audit['request_sha256'],seconds=time.monotonic()-START,no_forward=True,Memory='NOT_COLLECTED'))
 # Portable static HTML and a compact inspection montage, no external assets.
 parts=['<!doctype html><html lang="zh"><meta charset="utf-8"><title>SPCG fixed coarse/dense diagnosis</title><style>body{font-family:Arial,sans-serif;max-width:1300px;margin:auto;padding:24px;background:#f4f6fa;color:#172033}img{width:100%;background:white}section{margin:30px 0}a{color:#1756ad}summary{font-size:18px;padding:12px}</style><h1>SPCG：5例既有预测 coarse / dense 几何诊断</h1><p>事后固定选例，仅解释本轮差异。无新forward、训练或GT配准。全局视图保留所有点；ROI只是显示裁剪。coarse256与dense8192点数不同，不能将覆盖提升视为因果证明。颜色距离上限40mm，数值统计未截断。</p>']
 for r in results:
  parts.append('<section><h2>'+html.escape(r['case_id'])+' / '+r['fold']+' / '+r['selection']+'</h2><p>ΔE (G2−G1) = %.4f mm</p>'%r['delta_E_G2_minus_G1_mm'])
  for n in r['figures']:parts.append('<details'+(' open' if n.endswith('XY_global.png') else '')+'><summary>'+html.escape(n)+'</summary><img loading="lazy" src="'+n+'"></details>')
  parts.append('</section>')
 with (O/'index.html').open('x',encoding='utf-8') as f:f.write('\n'.join(parts))
 thumb=Image.new('RGB',(1000,5*535),'#edf1f7');draw=ImageDraw.Draw(thumb)
 for i,r in enumerate(results):
  draw.text((12,i*535+8),r['case_id']+' | '+r['selection'],fill='#14243b')
  for j,n in enumerate([r['figures'][0],r['figures'][-1]]):
   with Image.open(O/n) as im:t=ImageOps.contain(im.convert('RGB'),(495,495));thumb.paste(t,(j*500,i*535+32))
 thumb.save(O/'five_case_overview_v1.png')
 emit('source_bindings_v1.json',dict(files=list({r['path']:r for r in READ}.values()),archive_predictions=[b for r in results for b in r['prediction_bindings']]))
 emit('completion_v1.json',dict(status='FIVE_FIXED_CASE_COARSE_DENSE_GEOMETRY_VISUALIZATION_COMPLETE',cases=5,models_per_case=3,existing_prediction_files=15,stages=30,figures=20,forward_calls=0,training_updates=0,parameter_scans=0,GT_registration=False,checks=CHECKS,seconds=time.monotonic()-START))
 emit('artifact_manifest_v1.json',dict(files=[rec(p) for p in sorted(O.iterdir()) if p.is_file()],cache_note='mpl_cache is rendering cache, not scientific evidence'))
if __name__=='__main__':
 try:main()
 except BaseException as e:emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(e),checks=CHECKS));raise
