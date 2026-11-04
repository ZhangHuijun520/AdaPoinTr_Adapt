# -*- coding: utf-8 -*-
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',MPLBACKEND='Agg')
import json,hashlib,tarfile,io
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
N=Path(__file__).resolve().parent;E=N/'development_eval_v1';O=N/'prediction_proxy_diagnosis_20261102_v1';O.mkdir(exist_ok=False)
os.environ['MPLCONFIGDIR']=str(O/'mplconfig')
import matplotlib.pyplot as plt
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf-8')
p=E/'local_scoring_v1/results/case_metrics.jsonl';rows=[json.loads(l) for l in p.read_text().splitlines()];assert len(rows)==1050
lookup={(r['case_id'],r['arm']):r for r in rows};pairs=[]
for r in rows:
 if r['arm'] not in ['8192','16384']:continue
 inp=lookup[(r['case_id'],'Nop_D_'+r['arm'])];gt=lookup[(r['case_id'],'GT_8192')]
 pairs.append({'case_id':r['case_id'],'source_id':r['source_id'],'fold':r['fold'],'arm':r['arm'],'input_J2':inp['metrics']['J_coverage_2.0mm'],'prediction_J2':r['metrics']['J_coverage_2.0mm'],'GT_J2':gt['metrics']['J_coverage_2.0mm'],'input_Jp95':inp['metrics']['J_P95_mm'],'prediction_Jp95':r['metrics']['J_P95_mm']})
assert len(pairs)==420
summary={}
for arm in ['8192','16384']:
 rr=[r for r in pairs if r['arm']==arm];summary[arm]={k:float(np.mean([r[k] for r in rr])) for k in ['input_J2','prediction_J2','GT_J2','input_Jp95','prediction_Jp95']};summary[arm]['cases_prediction_J2_below_input']=sum(r['prediction_J2']<r['input_J2'] for r in rr)
proxy=json.loads((N/'consolidated_binding_v1/proxy_metrics.json').read_text());ps={}
for n in [8192,16384]:
 ps[str(n)]={}
 for stage in ['input','center512','proxy256','first_layer_direct_neighborhood_union']:
  rr=[r for r in proxy if r['n']==n and r['stage']==stage];assert len(rr)==6
  ps[str(n)][stage]={k:float(np.mean([r[k] for r in rr])) for k in ['J_cover_2mm','J_p95_mm','points']}
 rr=[r for r in proxy if r['n']==n and r['stage']=='input'];ps[str(n)]['near_interface_input_retained_in_direct_neighborhood_fraction']=float(sum(r['interface_near_in_direct_union'] for r in rr)/sum(r['interface_near_raw_points'] for r in rr))
# Select first manifest case in each fold BEFORE looking at its errors. No model execution.
manifest=json.loads((E/'reference_bank_v2/reference_manifest_v1.json').read_text());selected=[next(r for r in manifest['cases'] if r['fold']==f) for f in ['C','D']]
plan=json.loads((E/'local_scoring_v1/scoring_plan_v1.json').read_text());archive=Path(plan['downloaded_prediction_archive']['path']);assert sha(archive)==plan['downloaded_prediction_archive']['sha256']
details=[];archive_schema={}
with tarfile.open(archive,'r:gz') as tar:
 names=tar.getnames();assert len(names)==423;archive_schema={'members':423,'prediction_files':sum(n.startswith('predictions/') for n in names),'actual_proxy_artifacts':sum('proxy' in n.lower() for n in names)}
 records=[json.loads(l) for l in tar.extractfile('inference_manifest.jsonl').read().decode().splitlines()];rec={(r['case_id'],str(r['n_input'])):r for r in records}
 for r in selected:
  assert sha(r['path'])==r['sha256'];ref=np.load(r['path']);j=ref['a_is_j'];q=ref['a_centers'][j];w=ref['a_weights'][j];norm=r['normalization']
  for arm in ['8192','16384']:
   pf=r['point_files'][arm];assert sha(pf['path'])==pf['sha256'];z=np.load(pf['path']);inp=z['partial']*norm['scale']+np.array(norm['center']);gt=z['implant']*norm['scale']+np.array(norm['center'])
   record=rec[(r['case_id'],arm)];blob=tar.extractfile(record['prediction']['name']).read();assert hashlib.sha256(blob).hexdigest()==record['prediction']['sha256'];predz=np.load(io.BytesIO(blob));assert predz.files==['prediction'];pred=predz['prediction']*norm['scale']+np.array(norm['center'])
   di=cKDTree(inp).query(q,workers=2)[0];dp=cKDTree(pred).query(q,workers=2)[0];dg=cKDTree(gt).query(q,workers=2)[0]
   group=(di>2).astype(int)*2+(dp>2).astype(int);fractions=[float(w[group==k].sum()/w.sum()) for k in range(4)]
   details.append({'case_id':r['case_id'],'fold':r['fold'],'arm':arm,'selection':'first reference-manifest case per fold, not performance-selected','J_area_fractions':dict(zip(['input_supported_prediction_covered','input_supported_prediction_missed','input_unsupported_prediction_covered','both_missed'],fractions)),'GT_J2':float(np.average(dg<=2,weights=w))})
   fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');ids=np.linspace(0,len(q)-1,min(6000,len(q)),dtype=int);colors=np.array(['#009e73','#d55e00','#0072b2','#777777']);ax.scatter(*q[ids].T,c=colors[group[ids]],s=2);ax.set_title(r['case_id']+' / '+arm+'\nJ face centers: orange=input-supported but prediction misses (>2mm)');ax.set_xlabel('world x mm');ax.set_ylabel('world y mm');ax.set_zlabel('world z mm');ax.set_box_aspect(np.maximum(np.ptp(q,axis=0),1));fig.tight_layout();fig.savefig(O/(r['case_id']+'_'+arm+'.png'),dpi=130);plt.close(fig)
save('case_pairs.json',pairs);save('summary.json',{'prediction_vs_input':summary,'historical_CPU_surrogate':ps,'archive_schema':archive_schema,'selected_face_analysis':details,'no_actual_forward_proxy_trajectory':True,'models_loaded':0,'forward':0,'training':0})
fig,axs=plt.subplots(1,2,figsize=(11,5),constrained_layout=True)
for ax,arm in zip(axs,['8192','16384']):
 rr=[r for r in pairs if r['arm']==arm];ax.scatter([r['input_J2']*100 for r in rr],[r['prediction_J2']*100 for r in rr],s=12,alpha=.65);ax.plot([0,100],[0,100],'k--',lw=1);ax.set_title(arm+' input: 210 paired defect cases');ax.set_xlabel('Input J coverage at 2 mm (%)');ax.set_ylabel('Prediction J coverage at 2 mm (%)');ax.set_xlim(0,100);ax.set_ylim(0,100)
fig.suptitle('Interface information is often present in input but not reproduced in output\nDescriptive cases; five defects/source are not independent repeats');fig.savefig(O/'input_prediction_pairs.png',dpi=150);plt.close(fig)
save('provenance.json',{'case_metrics_sha256':sha(p),'proxy_metrics_sha256':sha(N/'consolidated_binding_v1/proxy_metrics.json'),'archive_sha256':sha(archive)})
print(json.dumps({'summary':summary,'proxy':ps,'details':details}),flush=True)
