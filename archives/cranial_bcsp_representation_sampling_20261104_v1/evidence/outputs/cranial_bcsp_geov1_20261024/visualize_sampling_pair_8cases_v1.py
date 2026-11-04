"""One fixed eight-case CPU visualization; no model calls, registration or score changes."""
import os
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2'
import hashlib,html,io,json,sys,tarfile,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize,TwoSlopeNorm
from matplotlib.lines import Line2D
import plotly.graph_objects as go
from plotly.subplots import make_subplots
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1';V=N/'geometry_review_8cases_v1'
sys.path.insert(0,str(N));import bcsp_eval_metrics_v1 as m
SOURCES=['051','053','013','041'];DEFECTS=['bilateral','frontoorbital'];IDS=['train__'+s+'__'+d for s in SOURCES for d in DEFECTS]
ARMS=['V1','Morton_area_stratified8k'];COLORS=['#1479bb','#dc7831'];START=time.monotonic();READ={}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':8,'legend.fontsize':8,'savefig.facecolor':'white'})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p);return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def check(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];READ[str(p)]=bind(p);return p
def dump(name,value):
 with (V/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False)
def subset(a,n):return np.arange(len(a)) if len(a)<=n else np.linspace(0,len(a)-1,n,dtype=int)
def bbox(arrays,pad=4):
 allp=np.concatenate(arrays);lo=allp.min(0)-pad;hi=allp.max(0)+pad;c=(lo+hi)/2;half=(hi-lo).max()/2;return c-half,c+half
def axes3(ax,limits):
 lo,hi=limits;ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='X (mm)',ylabel='Y (mm)',zlabel='Z (mm)');ax.view_init(elev=25,azim=-60);ax.set_box_aspect((1,1,1));ax.tick_params(labelsize=7,pad=0)
def cdf(dist,weights):
 order=np.argsort(dist,kind='mergesort');x=dist[order];y=np.cumsum(weights[order]);y/=y[-1];idx=subset(x,1200);return x[idx],y[idx]
def scene(limits):
 lo,hi=limits
 return dict(xaxis=dict(title='X (mm)',range=[lo[0],hi[0]]),yaxis=dict(title='Y (mm)',range=[lo[1],hi[1]]),zaxis=dict(title='Z (mm)',range=[lo[2],hi[2]]),aspectmode='cube',camera=dict(eye=dict(x=1.6,y=-2.,z=1.2),projection=dict(type='orthographic')))
def interactive(cid,d,gt,j,pred,reverse,limits,metrics):
 fig=make_subplots(rows=1,cols=2,specs=[[{'type':'scene'},{'type':'scene'}]],subplot_titles=['V1','Morton area-stratified 8k'])
 for a,arm in enumerate(ARMS):
  col=a+1
  for xyz,name,color,size,opacity in [(d,'Defective D input (V1 context)','#9b9b9b',1.1,.16),(gt,'GT missing-bone boundary','#26855c',1.6,.23),(j[subset(j,4000)],'GT shared cut wall J','#9b46ab',2.,.60)]:
   fig.add_trace(go.Scatter3d(x=xyz[:,0],y=xyz[:,1],z=xyz[:,2],mode='markers',name=name,legendgroup=name,showlegend=a==0,marker=dict(color=color,size=size,opacity=opacity),hoverinfo='skip'),row=1,col=col)
  p=pred[arm];dist=reverse[arm]
  fig.add_trace(go.Scatter3d(x=p[:,0],y=p[:,1],z=p[:,2],customdata=dist,mode='markers',name=('V1' if a==0 else 'Morton')+' prediction',marker=dict(color=dist,colorscale='Viridis',cmin=0,cmax=20,size=2.,opacity=.95,showscale=a==0,colorbar=dict(title='Pred → A2<br>mm (≥20 clipped)',x=1.02)),hovertemplate='X %{x:.2f}<br>Y %{y:.2f}<br>Z %{z:.2f}<br>Pred→A2 %{customdata:.3f} mm<extra></extra>'),row=1,col=col)
 fig.update_layout(title=cid+' | same world frame, camera and untrimmed limits',scene=scene(limits),scene2=scene(limits),height=750,width=1450,margin=dict(l=5,r=110,b=100,t=70),legend=dict(orientation='h',y=-.06),template='plotly_white')
 sync="""var gd=document.getElementById('{plot_id}'); var lock=false; gd.on('plotly_relayout',function(e){if(lock)return;var update={};if(e['scene.camera'])update['scene2.camera']=e['scene.camera'];else if(e['scene2.camera'])update['scene.camera']=e['scene2.camera'];else return;lock=true;Plotly.relayout(gd,update).then(function(){lock=false;},function(){lock=false;});});"""
 fig.write_html(V/(cid+'.html'),include_plotlyjs='directory',full_html=True,auto_open=False,post_script=sync)
def main():
 V.mkdir();auditfile=N/'post_scoring_freeze_audit_v1/audit_report_v1.json';audit=json.loads(auditfile.read_bytes());assert audit['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS'
 for r in audit['output_manifest']:check(r)
 request=N/'score_implementation_v1/local_scoring_execution_request_v1.json';q=json.loads(request.read_bytes());assert sha(request)=='0748d8e99c6589e47195a255abaf58f77751941e17c71e5e6ddb7c456ff059fa'
 archive=check(q['downloaded_prediction_archive']);case_index=json.loads(check(q['score_case_index']).read_bytes());lut={r['case_id']:r for r in case_index['cases']}
 official={(r['case_id'],r['arm']):r for r in map(json.loads,(N/'paired_scores_v1/case_metrics.jsonl').read_text(encoding='utf-8').splitlines())}
 dump('frozen_visual_review_scope_v1.json',dict(status='FIXED_BEFORE_SELECTED_ARRAY_READS',cases=IDS,selection='two regressed sources051/053 and two improved013/041;bilateral/frontoorbital each',purpose='descriptive error morphology, not unbiased new evaluation',archive=bind(archive),parent_audit=bind(auditfile),limits=dict(wall_seconds=600,output_bytes=268435456),display=dict(camera_elev_azim=[25,-60],prediction_distance_color_mm=[0,20],J_difference_color_mm=[-20,20],slab_axis='Y',slab_half_width_mm=2,slab_center='GT8192 median Y',all_predicted_points_retained=True,registration=False,display_only_reference_subsampling='equally spaced indices, max4000 J for interactive; max5000 for J map'),diagnostic_distance_levels_mm=[2,10,20],clinical_thresholds=False,model_calls=0,new_predictions=0,raw_CT_or_NRRD_read=False))
 results=[]
 with tarfile.open(archive,'r:gz') as tar:
  manifest={ (r['run'],r['case_id']):r for r in map(json.loads,tar.extractfile('inference_manifest.jsonl').read().decode().splitlines())}
  for cid in IDS:
   case=lut[cid];data={}
   for arm in ARMS:
    with np.load(check(case['point_files'][arm]),allow_pickle=False) as z:data[arm]={key:z[key].copy() for key in ['partial','implant']}
   assert np.array_equal(data['V1']['implant'],data[ARMS[1]]['implant'])
   norm=case['normalization'];gt=m.world_points(data['V1']['implant'],norm);d=m.world_points(data['V1']['partial'],norm);pred={}
   for arm in ARMS:
    record=manifest[('C_'+arm,cid)];blob=tar.extractfile(record['prediction']['name']).read();assert len(blob)==record['prediction']['bytes'] and hashlib.sha256(blob).hexdigest()==record['prediction']['sha256']
    with np.load(io.BytesIO(blob),allow_pickle=False) as z:p=z['prediction'].copy()
    assert p.shape==(8192,3) and p.dtype==np.float32 and np.isfinite(p).all();pred[arm]=m.world_points(p,norm)
   with np.load(check(case['reference']),allow_pickle=False) as z:ref={key:z[key] for key in z.files}
   a2,_,_=m.a2_reference(ref);rtree=cKDTree(a2);reverse={arm:rtree.query(pred[arm],workers=2)[0] for arm in ARMS};del rtree,a2
   directed={arm:cKDTree(pred[arm]).query(ref['a_centers'],workers=2)[0] for arm in ARMS}
   ej=ref['a_is_j'];wall=ref['a_centers'][ej];diag={};center_y=float(np.median(gt[:,1]))
   for arm in ARMS:
    values=reverse[arm];selected=official[(cid,arm)]['full_metrics'];expected_p95=selected['reverse_discrete_reference']['A2']['p95_mm'];actual_p95=m.weighted_quantile(values,np.ones(len(values)))
    assert np.isclose(actual_p95,expected_p95,rtol=1e-10,atol=1e-9)
    ep95=m.weighted_quantile(directed[arm][~ej],ref['a_weights'][~ej]);jp95=m.weighted_quantile(directed[arm][ej],ref['a_weights'][ej])
    assert np.isclose(ep95,official[(cid,arm)]['metrics']['E_P95_mm']) and np.isclose(jp95,official[(cid,arm)]['metrics']['J_P95_mm'])
    p=pred[arm];diag[arm]=dict(official_metrics=official[(cid,arm)]['metrics'],reverse_median_mm=float(np.median(values)),reverse_p95_mm=float(actual_p95),reverse_fractions={str(t):float(np.mean(values>t)) for t in [2,10,20]},centroid_offset_vector_mm=(p.mean(0)-gt.mean(0)).tolist(),centroid_offset_norm_mm=float(np.linalg.norm(p.mean(0)-gt.mean(0))),bbox_extent_mm=np.ptp(p,axis=0).tolist(),slab_predicted_points=int((np.abs(p[:,1]-center_y)<=2).sum()),all8192_points_used=True)
   full_limits=bbox([d,gt,*pred.values()]);focus_limits=bbox([gt,*pred.values()]);low,high=focus_limits;context=d[np.all((d>=low)&(d<=high),axis=1)]
   fig=plt.figure(figsize=(17,11));axes=[fig.add_subplot(2,3,k+1,projection='3d' if k<3 else None) for k in range(6)]
   ax=axes[0];ax.scatter(*d.T,s=.6,c='#aaaaaa',alpha=.14,rasterized=True)
   ax.scatter(*gt.T,s=.9,c='#27885a',alpha=.45,rasterized=True)
   for arm,color in zip(ARMS,COLORS):ax.scatter(*pred[arm].T,s=.8,c=color,alpha=.45,rasterized=True)
   axes3(ax,full_limits);ax.set_title('Full context: D grey / GT green / V1 blue / Morton orange')
   mapper=None
   for col,arm in enumerate(ARMS,1):
    ax=axes[col];ax.scatter(*context.T,s=.5,c='#bbbbbb',alpha=.10,rasterized=True);ax.scatter(*gt.T,s=.65,c='#529777',alpha=.15,rasterized=True)
    mapper=ax.scatter(*pred[arm].T,s=1.5,c=reverse[arm],cmap='viridis',norm=Normalize(0,20),alpha=.95,rasterized=True)
    axes3(ax,focus_limits);ax.set_title(('V1' if col==1 else 'Morton')+' | prediction → full A2 reference')
   cbar=fig.colorbar(mapper,ax=axes[1:3],fraction=.025,pad=.035,extend='max');cbar.set_label('Nearest reference distance (mm); ≥20 saturated')
   ax=axes[3]
   for xyz,color,label,size in [(d,'#aaaaaa','D input',3),(gt,'#27885a','GT',4),(pred['V1'],COLORS[0],'V1',4),(pred[ARMS[1]],COLORS[1],'Morton',4)]:
    mask=np.abs(xyz[:,1]-center_y)<=2;ax.scatter(xyz[mask,0],xyz[mask,2],s=size,c=color,alpha=.6,label=label)
   ax.set(xlim=(low[0],high[0]),ylim=(low[2],high[2]),xlabel='X (mm)',ylabel='Z (mm)',title=f'Fixed Y slab: {center_y:.1f} ±2 mm (point projection)');ax.set_aspect('equal',adjustable='box');ax.legend(loc='best',markerscale=2)
   ax=axes[4]
   for arm,color in zip(ARMS,COLORS):
    for region,mask,style in [('E',~ej,'-'),('J',ej,'--')]:
     x,y=cdf(directed[arm][mask],ref['a_weights'][mask]);ax.plot(x,y,color=color,ls=style,lw=1.4,label=('V1' if arm=='V1' else 'Morton')+' '+region)
   ax.axvline(2,color='#777777',ls=':',lw=1);ax.set(xlabel='A1 reference → prediction distance (mm)',ylabel='Area-weighted cumulative fraction',ylim=(0,1.01),title='E and J coverage / tail behavior');ax.grid(alpha=.2);ax.legend(loc='lower right')
   ax=axes[5];delta=directed[ARMS[1]][ej]-directed['V1'][ej];ix=subset(wall,5000)
   sc=ax.scatter(wall[ix,0],wall[ix,2],c=delta[ix],cmap='coolwarm',norm=TwoSlopeNorm(0,-20,20),s=3,rasterized=True)
   ax.set(xlabel='J reference X (mm)',ylabel='J reference Z (mm)',title='Cut wall J: Morton−V1 distance (no alignment)');ax.set_aspect('equal',adjustable='datalim');fig.colorbar(sc,ax=ax,fraction=.04,pad=.03,extend='both').set_label('mm; blue better / red worse')
   fig.suptitle(cid+' | fixed 8-case geometry review | sampled surfaces, not CT slices',fontsize=15,y=.99)
   note=[]
   for arm,label in zip(ARMS,['V1','Morton']):
    a=diag[arm];v=a['official_metrics'];note.append(f"{label}: E95 {v['E_P95_mm']:.2f} mm | J95 {v['J_P95_mm']:.2f} mm | pred→ref median/P95 {a['reverse_median_mm']:.2f}/{a['reverse_p95_mm']:.2f} mm | >20 mm {100*a['reverse_fractions']['20']:.1f}% | centroid offset {a['centroid_offset_norm_mm']:.2f} mm")
   fig.text(.03,.028,'\n'.join(note),fontsize=9,va='bottom');fig.subplots_adjust(left=.035,right=.93,bottom=.105,top=.925,wspace=.25,hspace=.25)
   fig.savefig(V/(cid+'.png'),dpi=150);plt.close(fig)
   interactive(cid,d,gt,wall,pred,reverse,focus_limits,official)
   results.append(dict(case_id=cid,source_id=case['source_id'],GT_bbox_extent_mm=np.ptp(gt,axis=0).tolist(),GT_slab_Y_mm=center_y,diagnostics=diag,prediction_geometry_not_modified=True,selected_official_metrics_reproduced=True))
   print('VISUALIZED',cid,flush=True);assert time.monotonic()-START<600 and sum(p.stat().st_size for p in V.iterdir() if p.is_file())<268435456
 dump('selected_case_geometry_diagnostics_v1.json',dict(status='FIXED_8_CASE_REVIEW_COMPLETE',cases=results,levels_mm=[2,10,20],levels_role='descriptive display only; original2mm score threshold unchanged',registration=False,centroid_interpretation='point-distribution diagnostic,not fitted translation',new_model_calls=0,new_predictions=0,scoring_all105_rerun=False,selected_reference_distances_recomputed_for_coloring=True,seconds=time.monotonic()-START))
 head='<!doctype html><meta charset="utf-8"><title>固定8例几何审阅</title><style>body{font:16px system-ui;max-width:1300px;margin:32px auto;background:#f4f6f8;color:#132a3a}section{background:white;padding:20px;margin:20px 0;border-radius:12px}img{width:100%}a{color:#0767b0}p{line-height:1.7}</style><h1>V1／Morton：固定8例几何审阅</h1><p>不新增推理、不配准。双面板3D交互初始相同范围与相机，并联动旋转；颜色表示预测点到完整A2参考的距离，20mm以上饱和，悬停显示真实距离。绿色为GT、紫色为共享切壁J、灰色为V1残缺骨点集。薄层图是点云投影，不是CT。病例按预先固定的两个回退与两个改善来源选择，不能用于重新计算成功率或剔除病例。</p>'
 for cid in IDS:head+='<section><h2>'+html.escape(cid)+'</h2><p><a href="'+cid+'.html">打开离线双面板交互3D</a> · <a href="'+cid+'.png">查看原尺寸六面板图</a></p><img src="'+cid+'.png" loading="lazy"></section>'
 with (V/'index.html').open('x',encoding='utf-8') as f:f.write(head)
 for r in READ.values():assert Path(r['path']).stat().st_size==r['bytes'] and sha(r['path'])==r['sha256']
 dump('source_readback_receipt_v1.json',dict(status='ALL_SELECTED_INPUT_AND_FROZEN_SCORE_HASHES_STABLE',files=list(READ.values()),write_scope=str(V),server_calls=0,model_calls=0,real_CT_read=False))
 dump('artifact_manifest_v1.json',dict(status='VISUAL_REVIEW_CREATED_PENDING_VISUAL_INSPECTION',files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(V.iterdir()) if p.is_file()]))
 print('FIXED_8_CASE_VISUALIZATION_COMPLETE_NO_MODEL_CALLS',flush=True)
if __name__=='__main__':main()
