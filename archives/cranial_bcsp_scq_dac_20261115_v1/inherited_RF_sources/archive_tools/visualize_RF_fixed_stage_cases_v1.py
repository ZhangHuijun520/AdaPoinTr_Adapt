"""Seven fixed existing cases, three arms: CPU diagnostics only, no model/checkpoint."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLBACKEND='Agg')
from pathlib import Path
import hashlib,html,importlib.util,io,json,tarfile,time
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_rf_stage_visual_20261115_v1';O.mkdir()
os.environ['MPLCONFIGDIR']=str(O/'mpl_cache')
import numpy as np
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image,ImageOps,ImageDraw
ARMS=['S-ref','RF-Static','RF-Requery'];STAGES=['Q0','Q1','Q2','dense'];COLORS=['#64748b','#d97706','#2563eb'];START=time.monotonic();READ=[]
F=R/'outputs/scq_rf_score_freeze_20261115_v1';S=R/'outputs/scq_rf_score_impl_20261115_v1'
def need(v,msg):assert v,msg
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def exact(r):
 p=Path(r['path']);need(p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),'regular source path');need(p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'source hash '+str(p));READ.append(dict(r));return p
def read(p):return json.loads(p.read_bytes())
def emit(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def world(x,n):return np.asarray(x,np.float64)*n['scale']+np.asarray(n['center'],np.float64)
def bounds(x,pad):return np.stack([x.min(0)-pad,x.max(0)+pad])
def roi_count(x,b):return int(np.all((x>=b[0])&(x<=b[1]),axis=1).sum())
def stage_stats(x,G,a2tree,ref,metric):
 centroid=x.mean(0);g=G.mean(0);radius=np.sqrt(((x-centroid)**2).sum(1).mean());gr=np.sqrt(((G-g)**2).sum(1).mean());dist=a2tree.query(x,workers=2)[0]
 target=cKDTree(x).query(ref['a_centers'],workers=2)[0];support={}
 for label,mask in [('E',~ref['a_is_j']),('J',ref['a_is_j'])]:support[label]=metric.stats(target[mask],ref['a_weights'][mask])
 return dict(points=len(x),centroid_mm=centroid.tolist(),centroid_error_vector_mm=(centroid-g).tolist(),centroid_error_mm=float(np.linalg.norm(centroid-g)),radius_ratio=float(radius/gr),to_A2_P95_mm=float(np.quantile(dist,.95)),to_A2_gt20_fraction=float((dist>20).mean()),support_E_P95_mm=support['E']['p95_mm'],support_J_P95_mm=support['J']['p95_mm'],support_E_cover2=support['E']['coverage']['2.0'],support_J_cover2=support['J']['coverage']['2.0']),dist
def projection(stem,view,D,G,J,clouds,distances,stats,box,roi):
 u,v=view;fig,axes=plt.subplots(3,4,figsize=(16,11));fig.subplots_adjust(left=.055,right=.93,bottom=.085,top=.88,hspace=.42,wspace=.24)
 fig.suptitle(stem+' | '+('XYZ'[u]+'XYZ'[v])+' | native world mm, no alignment',fontsize=14,y=.985)
 fig.text(.5,.95,'Rows: S-ref / Static / Requery | columns: Q0 / Q1 / Q2 (256) / dense (8192)',ha='center',fontsize=10)
 fig.text(.5,.922,'Gray=input, teal=GT block, purple=J faces. Model color: distance to A2; display cap40mm, statistics uncapped.',ha='center',fontsize=9)
 for i,arm in enumerate(ARMS):
  for j,stage in enumerate(STAGES):
   ax=axes[i,j];x=clouds[arm][stage];m=stats[arm][stage]
   for p,c,sz,alpha in [(D,'#94a3b8',.7,.15),(G,'#009688',1.2,.3),(J,'#a855f7',1.5,.35)]:ax.scatter(p[:,u],p[:,v],s=sz,c=c,alpha=alpha,edgecolors='none',rasterized=True)
   ax.scatter(x[:,u],x[:,v],c=distances[arm][stage],cmap='magma',vmin=0,vmax=40,s=8 if stage!='dense' else 1.4,alpha=.92 if stage!='dense' else .75,edgecolors='none',rasterized=True)
   ax.scatter([x[:,u].mean()],[x[:,v].mean()],c='#111827',marker='+',s=50);ax.scatter([G[:,u].mean()],[G[:,v].mean()],c='#009688',marker='x',s=40)
   ax.add_patch(Rectangle((roi[0,u],roi[0,v]),roi[1,u]-roi[0,u],roi[1,v]-roi[0,v],fill=False,ls='--',lw=.6,color='#475569'))
   ax.set(xlim=box[:,u],ylim=box[:,v],xlabel='XYZ'[u]+' mm',ylabel='XYZ'[v]+' mm');ax.set_aspect('equal',adjustable='box');ax.tick_params(labelsize=7);ax.grid(alpha=.14)
   ax.set_title(arm+' / '+stage+'\ncentroid %.1fmm | tail %.1f%% | J2 %.1f%%'%(m['centroid_error_mm'],100*m['to_A2_gt20_fraction'],100*m['support_J_cover2']),fontsize=9)
 cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,40),cmap='magma'),cax=fig.add_axes([.948,.2,.013,.55]));cb.set_label('Point-to-A2 mm')
 fig.text(.49,.025,'Equal global axes include ALL stages and outliers. Dashed box = GT bbox +10mm, display only. Projection overlap is not3D contact.',ha='center',fontsize=9)
 p=O/'figures'/(stem+'_'+('XYZ'[u]+'XYZ'[v])+'.png');fig.savefig(p,dpi=135,facecolor='white');plt.close(fig);return p
def interactive(stem,D,G,J,clouds,distances,box,roi):
 fig=make_subplots(rows=3,cols=4,specs=[[{'type':'scene'}]*4 for _ in ARMS],subplot_titles=[a+' '+s for a in ARMS for s in STAGES])
 for i,arm in enumerate(ARMS,1):
  for j,stage in enumerate(STAGES,1):
   for name,x,c,size,opacity in [('D input',D,'#94a3b8',1,.12),('GT block',G,'#009688',1.4,.3),('J faces',J,'#a855f7',1.7,.4)]:fig.add_trace(go.Scatter3d(x=x[:,0],y=x[:,1],z=x[:,2],mode='markers',name=name,legendgroup=name,showlegend=i==j==1,marker=dict(color=c,size=size,opacity=opacity)),row=i,col=j)
   x=clouds[arm][stage];fig.add_trace(go.Scatter3d(x=x[:,0],y=x[:,1],z=x[:,2],mode='markers',showlegend=False,marker=dict(size=2.5 if stage!='dense' else 1.5,opacity=.85,color=distances[arm][stage],cmin=0,cmax=40,colorscale='Magma',showscale=i==3 and j==4,colorbar=dict(title='A2 mm',len=.5))),row=i,col=j)
 scenes=['scene']+['scene'+str(i) for i in range(2,13)]
 def config(b):return dict(xaxis=dict(title='X mm',range=b[:,0].tolist()),yaxis=dict(title='Y mm',range=b[:,1].tolist()),zaxis=dict(title='Z mm',range=b[:,2].tolist()),aspectmode='data',camera=dict(eye=dict(x=1.3,y=1.3,z=1.1)))
 def ranges(b):return {s+'.'+axis+'.range':b[:,j].tolist() for s in scenes for j,axis in enumerate(['xaxis','yaxis','zaxis'])}
 fig.update_layout(**{s:config(box) for s in scenes},height=1200,width=1650,title=stem+' | fixed stages, synchronized 3D cameras',margin=dict(l=5,r=60,t=110,b=35),legend=dict(orientation='h',y=-.025),updatemenus=[dict(type='buttons',direction='right',x=.01,y=1.065,buttons=[dict(label='Global: all outliers',method='relayout',args=[ranges(box)]),dict(label='GT ROI +10mm: display only',method='relayout',args=[ranges(roi)])])])
 sync="""const gd=document.getElementById('{plot_id}');let lock=false;gd.on('plotly_relayout',e=>{if(lock)return;const k=Object.keys(e).find(k=>/^scene\\d*\\.camera$/.test(k));if(!k)return;lock=true;const v={};['scene',...Array.from({length:11},(_,i)=>'scene'+(i+2))].forEach(s=>{if(s+'.camera'!==k)v[s+'.camera']=e[k]});Plotly.relayout(gd,v).finally(()=>lock=false);});"""
 page=fig.to_html(full_html=True,include_plotlyjs=True,include_mathjax=False,post_script=sync,config=dict(displaylogo=False,responsive=True));need('<script src=' not in page.lower(),'self contained HTML')
 p=O/'html'/(stem+'.html');p.open('x',encoding='utf-8').write(page);return p
def main():
 (O/'figures').mkdir();(O/'html').mkdir();auditfile=F/'audit_report_v1.json';audit=read(auditfile);need(audit['status']=='FORMAL_SCQ_RF_POST_SCORING_FREEZE_AUDIT_PASS','formal audit prerequisite')
 q=read(S/'local_scoring_execution_request_v1.json');idx=read(exact(q['score_case_index']));cases={(c['fold'],c['case_id']):c for c in idx['cases']};records={(r['fold'],r['case_id'],r['arm']):r for r in idx['prediction_records']}
 bind=next(r for r in audit['output_manifest'] if Path(r['path']).name=='case_metrics.jsonl');scores={(r['fold'],r['case_id'],r['arm']):r for r in map(json.loads,exact(bind).read_text(encoding='utf-8').splitlines())}
 rb=next(r for r in audit['output_manifest'] if Path(r['path']).name=='risk_transitions.json');risk=read(exact(rb));pair='RF-Requery_minus_RF-Static'
 fixed=[]
 for f in 'CD':
  t=risk[f][pair]['labels']['severe_geometry'];new=sorted(r['case_id'] for r in t['cases'] if r['new']);shared=sorted(r['case_id'] for r in t['cases'] if r['baseline'] and r['candidate']);rescued=sorted(r['case_id'] for r in t['cases'] if r['rescued'])
  fixed += [(f,c,'new_severe_vs_Static') for c in new]+[(f,c,'shared_severe') for c in shared]+[(f,rescued[0],'fixed_rescued_control')]
 need(len(fixed)==7 and sum(role=='new_severe_vs_Static' for f,c,role in fixed)==3 and sum(role=='shared_severe' for f,c,role in fixed)==2 and sum(role=='fixed_rescued_control' for f,c,role in fixed)==2,'fixed7 selection')
 need({(f,c) for f,c,role in fixed if role=='fixed_rescued_control'}=={('C','train__025__random_2'),('D','train__008__frontoorbital')},'fixed improvement controls')
 emit('fixed_visual_scope_v1.json',dict(status='FROZEN_SEVEN_CASE_DIAGNOSTIC_SCOPE',cases=[dict(fold=f,case_id=c,role=role) for f,c,role in fixed],arms=ARMS,stages=STAGES,prediction_files=21,views=['XY','XZ','YZ'],coarse_points=256,dense_points=8192,control_selection='lexicographically first rescued-versus-Static case per fold, selected before array reads',audit=rec(auditfile),limits=dict(wall_seconds=600,output_bytes=536870912),operations=dict(forward=0,training=0,checkpoint_loads=0,server_calls=0),no_registration_or_filter=True,reference='Frozen A1 E/J and A2; world-mm D-only inverse normalization; new stage distances are posthoc diagnostics, not replacement formal scores'))
 metricpath=exact(q['implementation']['metrics']);sp=importlib.util.spec_from_file_location('RF_existing_reference_helpers',metricpath);metric=importlib.util.module_from_spec(sp);sp.loader.exec_module(metric)
 archive=exact(q['archive_inputs']['SCQ_RF']['archive']);results=[]
 with tarfile.open(archive) as tar:
  for fold,cid,role in fixed:
   case=cases[fold,cid];n=case['normalization']
   with np.load(exact(case['point_file']),allow_pickle=False) as z:D0=z['partial'].copy();G0=z['implant'].copy()
   need(hashlib.sha256(G0.tobytes()).hexdigest()==case['target_array_sha256'] and D0.shape==G0.shape==(8192,3),'D GT binding');D,G=world(D0,n),world(G0,n)
   with np.load(exact(case['reference']),allow_pickle=False) as z:ref={k:z[k].copy() for k in z.files}
   A2,_,_=metric.a2_reference(ref);a2tree=cKDTree(A2);J=ref['a_centers'][ref['a_is_j']];clouds={};stats={};distances={};transitions={}
   for arm in ARMS:
    r=records[fold,cid,arm];blob=tar.extractfile(r['member']).read();need(len(blob)==r['bytes'] and hashlib.sha256(blob).hexdigest()==r['sha256'],'prediction member hash')
    with np.load(io.BytesIO(blob),allow_pickle=False) as z:arrays={k:z[k].copy() for k in z.files}
    need(list(arrays)==['prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'],'nine arrays');need(all(v.dtype==np.float32 and np.isfinite(v).all() and v.shape==((8192,3) if k=='prediction' else (256,3)) for k,v in arrays.items()),'stage shapes and finite')
    need(np.array_equal(arrays['Q2'],arrays['coarse']) and np.array_equal(arrays['Q0'],arrays['Qraw']) and np.allclose(arrays['Q0']+arrays['delta0'],arrays['Q1'],rtol=2e-5,atol=2e-6) and np.allclose(arrays['Q1']+arrays['delta1'],arrays['Q2'],rtol=2e-5,atol=2e-6),'native stage alignment')
    clouds[arm]={s:world(arrays['prediction' if s=='dense' else s],n) for s in STAGES};stats[arm]={};distances[arm]={};transitions[arm]=[]
    for stage,x in clouds[arm].items():stats[arm][stage],distances[arm][stage]=stage_stats(x,G,a2tree,ref,metric)
    score=scores[fold,cid,arm]
    for field,metricfield in [('support_E_P95_mm','E_P95_mm'),('support_J_P95_mm','J_P95_mm'),('support_E_cover2','E_coverage_2.0mm'),('support_J_cover2','J_coverage_2.0mm'),('to_A2_gt20_fraction','reverse_A2_outlier_20.0mm'),('centroid_error_mm','centroid_offset_mm')]:need(np.isclose(stats[arm]['dense'][field],score['metrics'][metricfield],rtol=1e-10,atol=1e-10),'dense diagnostic equals frozen score '+field)
    for a,b in zip(STAGES,STAGES[1:]):
     x,y=clouds[arm][a],clouds[arm][b];shift=y.mean(0)-x.mean(0);err=x.mean(0)-G.mean(0);squared=float(2*err@shift+shift@shift);need(np.isclose(squared,np.linalg.norm(y.mean(0)-G.mean(0))**2-np.linalg.norm(err)**2,rtol=1e-9,atol=1e-8),'centroid squared decomposition')
     displacement=(y.reshape(256,32,3)-x[:,None,:]).reshape(-1,3) if b=='dense' else y-x
     transitions[arm].append(dict(from_stage=a,to_stage=b,point_budget_equal=b!='dense',centroid_shift_mm=shift.tolist(),centroid_squared_error_change_mm2=squared,centroid_error_change_mm=stats[arm][b]['centroid_error_mm']-stats[arm][a]['centroid_error_mm'],E_P95_change_mm=stats[arm][b]['support_E_P95_mm']-stats[arm][a]['support_E_P95_mm'],J_P95_change_mm=stats[arm][b]['support_J_P95_mm']-stats[arm][a]['support_J_P95_mm'],J_cover2_change=stats[arm][b]['support_J_cover2']-stats[arm][a]['support_J_cover2'],outlier20_change=stats[arm][b]['to_A2_gt20_fraction']-stats[arm][a]['to_A2_gt20_fraction'],displacement_mean_mm=float(np.linalg.norm(displacement,axis=1).mean()),displacement_P95_mm=float(np.quantile(np.linalg.norm(displacement,axis=1),.95))))
   box=bounds(np.vstack([D,G,*[clouds[a][s] for a in ARMS for s in STAGES]]),5);roi=bounds(G,10);stem=fold+'__'+cid
   plots=[projection(stem,v,D,G,J,clouds,distances,stats,box,roi) for v in [(0,1),(0,2),(1,2)]];page=interactive(stem,D,G,J,clouds,distances,box,roi)
   results.append(dict(fold=fold,case_id=cid,role=role,normalization=n,stages=stats,transitions=transitions,ROI_counts={a:{s:roi_count(clouds[a][s],roi) for s in STAGES} for a in ARMS},global_bounds_mm=box.tolist(),GT_ROI_mm=roi.tolist(),frozen_metrics={a:scores[fold,cid,a]['metrics'] for a in ARMS},figures=[rec(p) for p in plots],HTML=rec(page)))
   need(time.monotonic()-START<=600 and sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<=536870912,'fixed time/output budget')
   print(json.dumps(dict(case=stem,role=role,status='RENDERED',Requery_centroids=[stats['RF-Requery'][s]['centroid_error_mm'] for s in STAGES],Requery_E95=[stats['RF-Requery'][s]['support_E_P95_mm'] for s in STAGES])),flush=True)
 fig,axes=plt.subplots(7,3,figsize=(16,23));fig.subplots_adjust(left=.07,right=.98,bottom=.06,top=.95,hspace=.62,wspace=.28)
 for i,r in enumerate(results):
  for j,(field,label,mul) in enumerate([('centroid_error_mm','Centroid error mm',1),('to_A2_gt20_fraction','Points >20mm from A2 (%)',100),('support_J_cover2','A1 J coverage@2mm (%)',100)]):
   ax=axes[i,j]
   for a,c in zip(ARMS,COLORS):ax.plot(range(4),[r['stages'][a][s][field]*mul for s in STAGES],'-o',c=c,lw=1.4,ms=3,label=a)
   ax.set_xticks(range(4),STAGES);ax.set_ylabel(label,fontsize=9);ax.set_title(r['fold']+' '+r['case_id']+' | '+r['role'],fontsize=8);ax.grid(alpha=.2)
   if i==0 and j==0:ax.legend(fontsize=8)
 fig.suptitle('Seven fixed cases: same-forward native stage diagnostics',fontsize=15);fig.text(.5,.015,'Q0/Q1/Q2:256 points each. Dense:8192; different point budget. No GT alignment, model rerun, filtering or population claim.',ha='center',fontsize=10)
 summary=O/'seven_case_stage_summary_v1.png';fig.savefig(summary,dpi=145,facecolor='white');plt.close(fig)
 sheet=Image.new('RGB',(1600,4*575),'#f1f5f9')
 for i,r in enumerate(results):
  with Image.open(r['figures'][1]['path']) as im:tile=ImageOps.contain(im.convert('RGB'),(800,550));sheet.paste(tile,((i%2)*800,(i//2)*575))
  ImageDraw.Draw(sheet).text(((i%2)*800+8,(i//2)*575+550),r['fold']+' '+r['case_id']+' '+r['role'],fill='black')
 sheet.save(O/'seven_case_contact_sheet_v1.png')
 cards=[]
 for r in results:
  stem=r['fold']+'__'+r['case_id'];cards.append('<section><h2>'+html.escape(stem)+'</h2><p>'+r['role']+' | <a href="html/'+stem+'.html">Open synchronized3D (global / GT ROI)</a></p>'+''.join('<img loading="lazy" src="figures/'+Path(p['path']).name+'">' for p in r['figures'])+'</section>')
 (O/'index.html').open('x',encoding='utf-8').write('<!doctype html><meta charset="utf-8"><title>SCQ-RF fixed stage diagnosis</title><style>body{font:16px system-ui;background:#f8fafc;color:#0f172a;margin:24px}section{background:white;padding:16px;margin:20px 0}img{width:100%;height:auto}a{color:#1d4ed8}</style><h1>SCQ-RF: Q0 → Q1 → Q2 → dense</h1><p>7 fixed posthoc cases,3 arms. Existing arrays only; no new forward or alignment. ROI is display-only; all statistics retain all points. Q0 is not a model-without-feedback counterfactual. Coarse and dense point budgets differ.</p><img src="seven_case_stage_summary_v1.png">'+''.join(cards))
 emit('stage_diagnostic_result_v1.json',dict(status='SEVEN_FIXED_CASE_RF_STAGE_VISUALIZATION_COMPLETE',cases=results,source_bindings=READ,seconds=time.monotonic()-START,operations=dict(existing_prediction_files_decoded=21,new_forward=0,training=0,checkpoint_loads=0,server_operations=0,GPU_calls=0,full_formal_score_rerun=0,registration=0,resampling=0),limitations=['Selected cases are posthoc diagnostic examples, not an independent validation population.','Q0/Q1 snapshots are from each fully trained model; not causal counterfactual models or a common frozen representation across arms.','Within Q0/Q1/Q2 point budget is256; dense8192 support/outlier statistics have different sampling budgets.','New distances are diagnostic descriptions only. Dense diagnostics checked against frozen score values; formal results remain unchanged.','Fixed orthogonal projections can overlap without3D contact; inspect offline3D; ROI is display-only and never filters statistics.','Dense child offsets use the previously validated native256-by32 output order.','D Static training device/driver differs; no pure D mechanism attribution.']))
 emit('visual_artifact_manifest_v1.json',dict(files=[rec(p) for p in sorted(O.rglob('*')) if p.is_file() and 'mpl_cache' not in p.parts],source_files_unchanged=all(sha(Path(r['path']))==r['sha256'] for r in READ),new_forward=0,training=0))
 print('SEVEN_FIXED_CASE_RF_STAGE_VISUALIZATION_COMPLETE',flush=True)
try:main()
except BaseException as exc:emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),new_forward=0));raise
