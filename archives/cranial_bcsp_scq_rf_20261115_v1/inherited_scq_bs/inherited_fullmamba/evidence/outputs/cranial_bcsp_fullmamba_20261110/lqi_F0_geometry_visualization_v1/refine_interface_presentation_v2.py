"""One presentation-only refinement; existing arrays/scores/selection unchanged."""
import os
os.environ.update(MPLBACKEND='Agg',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
import importlib.util,json,tarfile,copy
from pathlib import Path
S=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('fixed_seven_existing',S/'render_fixed_seven_cases_v1.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
ns=dict(m.__dict__)
exec(compile("def render_interface(stem,D,G,J,models,target_box,score):\n fig,axes=plt.subplots(3,2,figsize=(11,12));fig.subplots_adjust(left=.075,right=.98,bottom=.10,top=.88,hspace=.30,wspace=.23)\n fig.suptitle(stem+' | fixed target ROI and contact-support view',fontsize=13,y=.98)\n fig.text(.5,.95,'Display clipping only: GT bbox +5 mm; all points retained in overview/HTML',ha='center',fontsize=10)\n counts={arm:{key:crop_count(x,target_box) for key,x in models[arm].items()} for arm in ['F0','LQI']}\n fig.text(.5,.925,'3D points inside ROI: F0 P %d/8192, Q %d/256 | LQI P %d/8192, Q %d/256'%(counts['F0']['P'],counts['F0']['Q'],counts['LQI']['P'],counts['LQI']['Q']),ha='center',fontsize=10)\n for row,uv in enumerate([(0,1),(0,2),(1,2)]):\n  for col,arm in enumerate(['F0','LQI']):\n   ax=axes[row,col];scatter(ax,D,uv,COLORS['D'],2,.3);scatter(ax,G,uv,COLORS['GT'],3,.3)\n   scatter(ax,models[arm]['P'],uv,COLORS[arm],3,.55)\n   scatter(ax,J,uv,COLORS['J'],1,.15)\n   setup(ax,target_box,uv)\n   if row==0:ax.set_title(arm+' dense + fixed GT contact faces',fontsize=11)\n fig.legend(handles=legends(),loc='lower center',bbox_to_anchor=(.5,.035),ncol=5,frameon=False,fontsize=7.5)\n fig.text(.5,.012,'J points are existing world-mm voxel-face references, not a newly fitted mesh. Projection overlap is not contact.',ha='center',fontsize=7.5)\n p=S/'figures'/(stem+'_interface_v2.png');fig.savefig(p,dpi=165,facecolor='white');plt.close(fig);return p,counts",'<interface-layout-only-v2>','exec'),ns)

result=m.read(S/'visualization_result_v1.json');plan=m.read(S.parent/'lqi_F0_scoring_implementation_v1/local_scoring_execution_request_v1.json')
with tarfile.open(m.exact(plan['archive_inputs']['F0']['archive']),'r:gz') as f0,tarfile.open(m.exact(plan['archive_inputs']['LQI']['archive']),'r:gz') as lqi:
 tars=dict(F0=f0,LQI=lqi)
 for r in result['cases']:
  with m.np.load(m.exact(r['point_file']),allow_pickle=False) as z:D=m.world(z['partial'],r['normalization']);G=m.world(z['implant'],r['normalization'])
  with m.np.load(m.exact(r['reference_file']),allow_pickle=False) as z:J=z['a_centers'][z['a_is_j']]
  models={}
  for arm in ['F0','LQI']:
   pn,qn=m.load_prediction(tars[arm],r['predictions'][arm]);models[arm]=dict(P=m.world(pn,r['normalization']),Q=m.world(qn,r['normalization']))
  score={arm:dict(metrics=r['frozen_metrics'][arm]) for arm in ['F0','LQI']}
  path,counts=ns['render_interface'](r['fold']+'__'+r['case_id'],D,G,J,models,m.np.asarray(r['target_ROI_mm']),score)
  assert counts==r['ROI_inside_counts'];r['figures'][1]=m.rec(path)
result['presentation_refinement']='Only interface marker opacity/size and legend/footer layout changed; all input/prediction/GT/J points and view bounds unchanged.'
result['original_visualization_result']=m.rec(S/'visualization_result_v1.json')
m.emit('visualization_result_v2.json',result)
text=(S/'index.html').read_text(encoding='utf-8').replace('_interface.png','_interface_v2.png')
with (S/'index_v2.html').open('x',encoding='utf-8') as f:f.write(text)
from PIL import Image,ImageOps,ImageDraw
sheet=Image.new('RGB',(1200,700*4),'#e2e8f0')
for i,r in enumerate(result['cases']):
 with Image.open(r['figures'][1]['path']) as im:
  tile=ImageOps.contain(im.convert('RGB'),(600,670));sheet.paste(tile,((i%2)*600+(600-tile.width)//2,(i//2)*700));ImageDraw.Draw(sheet).text(((i%2)*600+10,(i//2)*700+680),r['fold']+' / '+r['case_id'],fill='black')
sheet.save(S/'seven_case_interface_contact_sheet_v2.png')
print('PRESENTATION_REFINEMENT_COMPLETE_POINTS_AND_COUNTS_UNCHANGED')
