"""Seven fixed cases, existing arrays only: world-mm geometry views, no scoring/model."""
import os
os.environ.update(MPLBACKEND='Agg',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='')
import ast,hashlib,html,io,json,math,time,tarfile
from pathlib import Path
S=Path(__file__).resolve().parent;B=S.parent
os.environ['MPLCONFIGDIR']=str(S/'matplotlib_cache_v1')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image,ImageOps,ImageDraw

COLORS=dict(D='#94a3b8',GT='#059669',J='#a855f7',F0='#2563eb',LQI='#ea580c')
FIXED=[('C','train__012__parietotemporal','new_severe'),('C','train__013__frontoorbital','new_severe'),('C','train__038__random_1','new_severe'),('C','train__041__frontoorbital','new_severe'),('D','train__060__bilateral','new_severe'),('D','train__008__frontoorbital','clear_improvement'),('D','train__052__frontoorbital','clear_improvement')]
START=time.monotonic();READ=[]
def require(ok,msg):
 if not ok:raise ValueError(msg)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=digest(p))
def exact(r):
 p=Path(r['path']);require(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),'regular bound path')
 require(p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],'source bytes/hash '+str(p));READ.append(r);return p
def read(p):return json.loads(p.read_bytes())
def emit(name,value):
 with (S/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def world(x,n):return np.asarray(x,np.float64)*n['scale']+np.asarray(n['center'],np.float64)
def points(x,n):require(x.shape==(n,3) and x.dtype==np.float32 and np.isfinite(x).all(),'finite frozen FP32 points')
def load_prediction(tar,r):
 m=tar.getmember(r['member']);require(m.isfile() and m.size==r['bytes'] and m.size<1048576,'bounded prediction member')
 raw=tar.extractfile(m).read();require(hashlib.sha256(raw).hexdigest()==r['sha256'],'prediction member SHA256')
 with np.load(io.BytesIO(raw),allow_pickle=False) as z:
  require(z.files==['prediction','coarse'],'frozen prediction keys');p,q=z['prediction'].copy(),z['coarse'].copy()
 points(p,8192);points(q,256);return p,q
def bounds(x,pad=5.):return np.array([x.min(0)-pad,x.max(0)+pad])
def crop_count(x,box):return int(np.all((x>=box[0])&(x<=box[1]),axis=1).sum())
def setup(ax,box,uv):
 u,v=uv;ax.set_xlim(box[:,u]);ax.set_ylim(box[:,v]);ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.16,lw=.5);ax.set_xlabel('XYZ'[u]+' (mm)',fontsize=8);ax.set_ylabel('XYZ'[v]+' (mm)',fontsize=8);ax.tick_params(labelsize=7)
def scatter(ax,x,uv,color,size,alpha):ax.scatter(x[:,uv[0]],x[:,uv[1]],c=color,s=size,alpha=alpha,edgecolors='none',rasterized=True)
def legends():return [Line2D([],[],marker='o',linestyle='',color=COLORS[k],markersize=5,label=label) for k,label in [('D','Observed input D'),('GT','Missing block GT'),('J','GT contact faces J'),('F0','F0 output'),('LQI','LQI output')]]
def render_overview(stem,D,G,J,models,global_box,target_box,score):
 fig,axes=plt.subplots(3,4,figsize=(16,10));fig.subplots_adjust(left=.05,right=.99,bottom=.075,top=.88,hspace=.26,wspace=.21)
 fig.suptitle(stem+' | unaligned world coordinates | all original points',fontsize=14,y=.98)
 fig.text(.5,.94,'E_P95: F0 %.2f / LQI %.2f mm; J Cover@2mm: %.1f / %.1f%%'%(score['F0']['metrics']['E_P95_mm'],score['LQI']['metrics']['E_P95_mm'],100*score['F0']['metrics']['J_coverage_2.0mm'],100*score['LQI']['metrics']['J_coverage_2.0mm']),ha='center',fontsize=11)
 for row,uv in enumerate([(0,1),(0,2),(1,2)]):
  for col,(arm,key,label) in enumerate([('F0','Q','F0 coarse Q (256)'),('F0','P','F0 dense P (8192)'),('LQI','Q','LQI coarse Q (256)'),('LQI','P','LQI dense P (8192)')]):
   ax=axes[row,col];scatter(ax,D,uv,COLORS['D'],1.5,.18);scatter(ax,G,uv,COLORS['GT'],1.6,.25)
   x=models[arm][key];scatter(ax,x,uv,COLORS[arm],7 if key=='Q' else 1.5,.8 if key=='Q' else .6)
   u,v=uv;ax.add_patch(Rectangle((target_box[0,u],target_box[0,v]),target_box[1,u]-target_box[0,u],target_box[1,v]-target_box[0,v],fill=False,ls='--',lw=.7,color='#475569'))
   setup(ax,global_box,uv)
   if row==0:ax.set_title(label,fontsize=10)
 fig.legend(handles=legends(),loc='lower center',ncol=5,frameon=False,fontsize=9)
 fig.text(.5,.035,'Dashed box = fixed GT bbox +5 mm. Same axes in each row. No registration, no point resampling.',ha='center',fontsize=9)
 p=S/'figures'/(stem+'_global.png');fig.savefig(p,dpi=165,facecolor='white');plt.close(fig);return p
def render_interface(stem,D,G,J,models,target_box,score):
 fig,axes=plt.subplots(3,2,figsize=(11,12));fig.subplots_adjust(left=.075,right=.98,bottom=.075,top=.88,hspace=.30,wspace=.23)
 fig.suptitle(stem+' | fixed target ROI and contact-support view',fontsize=13,y=.98)
 fig.text(.5,.95,'Display clipping only: GT bbox +5 mm; all points retained in overview/HTML',ha='center',fontsize=10)
 counts={arm:{key:crop_count(x,target_box) for key,x in models[arm].items()} for arm in ['F0','LQI']}
 fig.text(.5,.925,'3D points inside ROI: F0 P %d/8192, Q %d/256 | LQI P %d/8192, Q %d/256'%(counts['F0']['P'],counts['F0']['Q'],counts['LQI']['P'],counts['LQI']['Q']),ha='center',fontsize=10)
 for row,uv in enumerate([(0,1),(0,2),(1,2)]):
  for col,arm in enumerate(['F0','LQI']):
   ax=axes[row,col];scatter(ax,D,uv,COLORS['D'],2,.3);scatter(ax,G,uv,COLORS['GT'],3,.3)
   scatter(ax,models[arm]['P'],uv,COLORS[arm],3,.55)
   scatter(ax,J,uv,COLORS['J'],4,.65)
   setup(ax,target_box,uv)
   if row==0:ax.set_title(arm+' dense + fixed GT contact faces',fontsize=11)
 fig.legend(handles=legends(),loc='lower center',ncol=3,frameon=False,fontsize=9)
 fig.text(.5,.025,'J points are existing world-mm voxel-face references, not a newly fitted mesh. Projection overlap is not contact.',ha='center',fontsize=8)
 p=S/'figures'/(stem+'_interface.png');fig.savefig(p,dpi=165,facecolor='white');plt.close(fig);return p,counts
def interactive(stem,D,G,J,models,global_box,target_box):
 fig=make_subplots(rows=1,cols=2,specs=[[{'type':'scene'},{'type':'scene'}]],subplot_titles=['F0','LQI'])
 for col,arm in enumerate(['F0','LQI'],1):
  for key,x,label,sz,alpha,visible in [('D',D,'Observed input D',1.4,.12,True),('GT',G,'Missing block GT',1.7,.3,True),('J',J,'GT contact faces J',2.5,.8,True),(arm,models[arm]['P'],arm+' dense P',1.8,.65,True),(arm,models[arm]['Q'],arm+' coarse Q',3.5,1.,'legendonly')]:
   fig.add_trace(go.Scatter3d(x=x[:,0],y=x[:,1],z=x[:,2],mode='markers',name=label,legendgroup=label,showlegend=col==1 or key==arm,visible=visible,marker=dict(size=sz,color=COLORS[key],opacity=alpha),hoverinfo='x+y+z+name'),row=1,col=col)
 def scene(box):return dict(xaxis=dict(title='X (mm)',range=box[:,0].tolist()),yaxis=dict(title='Y (mm)',range=box[:,1].tolist()),zaxis=dict(title='Z (mm)',range=box[:,2].tolist()),aspectmode='data',camera=dict(eye=dict(x=1.4,y=1.4,z=1.1)))
 def relayout_box(box):return {sc+'.'+axis+'.range':box[:,i].tolist() for sc in ['scene','scene2'] for i,axis in enumerate(['xaxis','yaxis','zaxis'])}
 fig.update_layout(title=stem+' | original world-mm arrays, no alignment',scene=scene(global_box),scene2=scene(global_box),height=760,margin=dict(l=0,r=0,t=110,b=30),legend=dict(orientation='h',y=-.04),updatemenus=[dict(type='buttons',direction='right',x=.02,y=1.10,buttons=[dict(label='Global: all points',method='relayout',args=[relayout_box(global_box)]),dict(label='Target ROI +5mm (display only)',method='relayout',args=[relayout_box(target_box)])])],annotations=list(fig.layout.annotations)+[dict(text='Drag either view: cameras synchronize. Toggle coarse points in legend. ROI never changes stored arrays.',x=.5,y=1.08,xref='paper',yref='paper',showarrow=False,font=dict(size=11))])
 require(len(fig.data)==10,'ten full array traces, no downsampling')
 sync="""const gd=document.getElementById('{plot_id}');let syncing=false;gd.on('plotly_relayout',e=>{if(syncing)return;const k=e['scene.camera']?'scene.camera':e['scene2.camera']?'scene2.camera':null;if(!k)return;syncing=true;const target=k==='scene.camera'?'scene2.camera':'scene.camera';Plotly.relayout(gd,{[target]:e[k]}).finally(()=>{syncing=false;});});"""
 raw=fig.to_html(full_html=True,include_plotlyjs=True,include_mathjax=False,post_script=sync,config=dict(displaylogo=False,responsive=True))
 require('<script src=' not in raw.lower(),'self-contained HTML, no external script')
 p=S/'html'/(stem+'.html')
 with p.open('x',encoding='utf-8') as f:f.write(raw)
 return p

def main():
 require(not (S/'figures').exists() and not (S/'html').exists(),'fresh visualization folders')
 (S/'figures').mkdir();(S/'html').mkdir()
 qpath=B/'lqi_F0_scoring_implementation_v1/local_scoring_execution_request_v1.json'
 require(digest(qpath)=='b394b3b8814ac729d07a79fe607cbf0636b1ee596546304f8f416bc66e88304a','frozen score request')
 plan=read(qpath);audit_path=B/'lqi_F0_scoring_implementation_v1/post_scoring_freeze_audit_v1/audit_report_v1.json';audit=read(audit_path)
 require(audit['status']=='FORMAL_LQI_F0_POST_SCORING_FREEZE_AUDIT_PASS','formal audit prerequisite')
 score_path=B/'lqi_F0_scoring_implementation_v1/unified_scores_v1/case_metrics.jsonl'
 score_bind=next(r for r in audit['output_manifest'] if Path(r['path']).name=='case_metrics.jsonl');exact(score_bind)
 scores={(r['fold'],r['case_id'],r['arm']):r for r in [json.loads(x) for x in score_path.read_text(encoding='utf-8').splitlines()]}
 scope=read(exact(plan['score_case_index']));cases={(r['fold'],r['case_id']):r for r in scope['cases']};records={(r['fold'],r['case_id'],r['arm']):r for r in scope['prediction_records']}
 reliability=read(B/'lqi_F0_scoring_implementation_v1/post_scoring_freeze_audit_v1/case_level_reliability_values_v1.json')
 require({(x['fold'],x['case_id']) for x in reliability['new_severe_cases']}=={(f,c) for f,c,role in FIXED if role=='new_severe'},'exact five newly severe cases')
 emit('fixed_selection_and_visual_contract_v1.json',dict(status='FROZEN_POST_HOC_DIAGNOSTIC_SELECTION',cases=[dict(fold=f,case_id=c,role=role) for f,c,role in FIXED],source_audit=rec(audit_path),score_request_sha256=digest(qpath),points=dict(input=8192,GT=8192,coarse_per_model=256,dense_per_model=8192),views=dict(projections=['XY','XZ','YZ'],camera='same initial world-coordinate camera; interactive synchronization',global_box='union D/GT/bothQ/bothP +5mm',interface_ROI='GT bbox +5mm fixed; display clipping only',colors=COLORS),new_forward=0,new_training=0,new_scoring=0,registration=False,resampling=False,parameter_search=False,maximum_seconds=300,maximum_output_bytes=268435456))
 archive_paths={arm:exact(plan['archive_inputs'][arm]['archive']) for arm in ['F0','LQI']}
 result=[]
 with tarfile.open(archive_paths['F0'],'r:gz') as f0,tarfile.open(archive_paths['LQI'],'r:gz') as lqi:
  tars={'F0':f0,'LQI':lqi}
  for fold,cid,role in FIXED:
   c=cases[fold,cid];point_path=exact(c['point_file']);ref_path=exact(c['reference'])
   with np.load(point_path,allow_pickle=False) as z:
    require(set(z.files)=={'partial','implant'},'fixed point schema');dn,gn=z['partial'].copy(),z['implant'].copy()
   points(dn,8192);points(gn,8192);require(hashlib.sha256(gn.tobytes()).hexdigest()==c['target_array_sha256'],'fixed GT array hash')
   D,G=world(dn,c['normalization']),world(gn,c['normalization'])
   with np.load(ref_path,allow_pickle=False) as z:
    centers,mask=z['a_centers'].copy(),z['a_is_j'].copy()
   require(centers.ndim==2 and centers.shape[1]==3 and mask.shape==(len(centers),) and mask.dtype==bool and np.isfinite(centers).all(),'frozen world-space reference schema')
   J=centers[mask];require(len(J)>0,'contact reference exists')
   models={};score={arm:scores[fold,cid,arm] for arm in ['F0','LQI']}
   for arm in ['F0','LQI']:
    pn,qn=load_prediction(tars[arm],records[fold,cid,arm]);P,Q=world(pn,c['normalization']),world(qn,c['normalization']);models[arm]=dict(P=P,Q=Q)
    for key,x in [('P',P),('Q',Q)]:
     expected=score[arm]['position_shape']['prediction_centroid_mm'] if key=='P' else score[arm]['stage_geometry']['coarse']['centroid_mm']
     require(np.allclose(x.mean(0),expected,rtol=1e-10,atol=1e-7),'same world coordinates as frozen score')
   box=bounds(np.vstack([D,G,*[x for m in models.values() for x in m.values()]]));local=bounds(G);stem=fold+'__'+cid
   overview=render_overview(stem,D,G,J,models,box,local,score);contact,counts=render_interface(stem,D,G,J,models,local,score);page=interactive(stem,D,G,J,models,box,local)
   result.append(dict(fold=fold,case_id=cid,role=role,normalization=c['normalization'],reference_J_faces=len(J),global_box_mm=box.tolist(),target_ROI_mm=local.tolist(),ROI_inside_counts=counts,original_counts=dict(D=len(D),GT=len(G),F0_Q=256,F0_P=8192,LQI_Q=256,LQI_P=8192),frozen_metrics={arm:score[arm]['metrics'] for arm in score},frozen_stage_geometry={arm:score[arm]['stage_geometry'] for arm in score},predictions={arm:records[fold,cid,arm] for arm in ['F0','LQI']},point_file=c['point_file'],reference_file=c['reference'],figures=[rec(overview),rec(contact)],interactive_HTML=rec(page)))
   require(time.monotonic()-START<=300 and sum(p.stat().st_size for p in S.rglob('*') if p.is_file())<=268435456,'visualization time/output budget')
   print(json.dumps(dict(case=stem,status='RENDERED',ROI_counts=counts)),flush=True)
 # A compact sheet supports visual QA of all seven fixed cases, not case selection.
 thumbs=[]
 for r in result:
  with Image.open(r['figures'][0]['path']) as im:
   tile=ImageOps.contain(im.convert('RGB'),(800,500));canvas=Image.new('RGB',(800,520),'white');canvas.paste(tile,((800-tile.width)//2,0));ImageDraw.Draw(canvas).text((12,502),r['fold']+' / '+r['case_id'],fill='black');thumbs.append(canvas)
 sheet=Image.new('RGB',(1600,520*4),'#e2e8f0')
 for i,im in enumerate(thumbs):sheet.paste(im,((i%2)*800,(i//2)*520))
 sheet.save(S/'seven_case_overview_contact_sheet_v1.png')
 cards=[]
 for r in result:
  stem=r['fold']+'__'+r['case_id'];cards.append('<section><h2>'+html.escape(r['fold']+' / '+r['case_id'])+'</h2><p>'+r['role']+' | <a href="html/'+stem+'.html">Open synchronized 3D comparison</a></p><a href="figures/'+stem+'_global.png"><img loading="lazy" src="figures/'+stem+'_global.png"></a><a href="figures/'+stem+'_interface.png"><img loading="lazy" src="figures/'+stem+'_interface.png"></a></section>')
 index='<!doctype html><html><head><meta charset="utf-8"><title>LQI / F0 fixed seven-case geometry review</title><style>body{font:16px system-ui;margin:28px;background:#f8fafc;color:#0f172a}main{max-width:1500px;margin:auto}section{background:white;padding:20px;margin:24px 0;border:1px solid #cbd5e1}img{width:100%;height:auto}a{color:#1d4ed8}</style></head><body><main><h1>LQI / F0: fixed seven-case geometry review</h1><p>Five new severe cases + two fixed improvements. Original world-mm coordinates; no alignment, resampling, inference or training. Diagnostic post-hoc views, not new performance scores.</p><p>Global views retain every point. Interface views clip the display to GT bbox +5mm only. Purple J references are fixed contact-face centers; projection overlap alone does not prove 3D contact.</p>'+''.join(cards)+'</main></body></html>'
 with (S/'index.html').open('x',encoding='utf-8') as f:f.write(index)
 emit('visualization_result_v1.json',dict(status='FIXED_SEVEN_EXISTING_PREDICTION_VIEWS_COMPLETE',cases=result,counts=dict(cases=7,model_case_pairs=14,PNG_views=14,interactive_HTML=7),source_bindings=READ,source_score_audit=rec(audit_path),seconds=time.monotonic()-START,operations=dict(new_forward=0,training=0,scoring=0,registration=0,resampling=0,server_operations=0,GPU_calls=0),limitations=['Fixed post-hoc diagnostic selection, not independent performance estimate','Orthographic projections can overlap separate surfaces; synchronized3D supplied for spatial review','GT bbox+5mm is display-only crop, with inside counts; global views show outliers outside it','J centers are frozen reference faces, not a new anatomical mesh','Actual encoder memory/neighborhood and pre-coarse tensors not available; no claims about their values']))
 print('FIXED_SEVEN_CASES_COMPLETE',flush=True)

if __name__=='__main__':
 try:main()
 except BaseException as exc:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),new_forward=0));raise
