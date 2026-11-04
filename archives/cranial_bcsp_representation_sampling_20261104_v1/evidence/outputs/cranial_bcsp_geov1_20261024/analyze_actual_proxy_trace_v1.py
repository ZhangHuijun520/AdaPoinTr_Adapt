# -*- coding: utf-8 -*-
"""Offline evaluation of fixed four observed traces, no model/torch imports."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='2',MPLBACKEND='Agg')
import json,tarfile,io,hashlib,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
N=Path(__file__).resolve().parent;P=N/'actual_proxy_trace_20261102_v1';O=P/'local_analysis_v1';O.mkdir(exist_ok=False)
os.environ['MPLCONFIGDIR']=str(O/'mplconfig')
import matplotlib.pyplot as plt
B=Path('E:/ResearchBackups/AdaPoinTr/BCSP_INPUT_DENSITY_V1/2026-11-02_actual_proxy_trace');arc=B/'development_predictions_v1.tar.gz'
digest=lambda b:hashlib.sha256(b).hexdigest()
expected='637cc82bb5ce20f3ef2f115df5147accf5792e300b095f6d792e07c4840d3181'
assert arc.stat().st_size==4271350==int((B/(arc.name+'.bytes')).read_text().strip())
assert digest(arc.read_bytes())==expected==(B/(arc.name+'.sha256')).read_text().split()[0]
listing={}
for l in (B/(arc.name+'.contents.sha256')).read_text().splitlines():
 h,name=l.split(None,1);name=name.strip();assert name not in listing;listing[name]=h
assert len(listing)==11
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf-8')
refs=json.loads((N/'development_eval_v1/reference_bank_v2/reference_manifest_v1.json').read_text());rmap={r['case_id']:r for r in refs['cases']}
rows=[]
def metric(q,w,pts):
 d=cKDTree(pts).query(q,workers=2)[0];ix=np.argsort(d);p95=d[ix[np.searchsorted(np.cumsum(w[ix]),.95*w.sum())]]
 return {'points':len(pts),'J_cover2':float(np.average(d<=2,weights=w)),'J_cover1':float(np.average(d<=1,weights=w)),'J_p95_mm':float(p95)}
with tarfile.open(arc,'r:gz') as t:
 members=t.getmembers();assert len(members)==11 and set(m.name for m in members)==set(listing) and all(m.isfile() for m in members)
 payload={m.name:t.extractfile(m).read() for m in members};assert all(digest(b)==listing[k] for k,b in payload.items())
 done=json.loads(payload['inference_complete.json']);assert done['forwards']==4 and done['training_updates']==done['BNCal']==done['backward']==0
 assert all(m['state_before']==m['state_after'] and m['CPU_rng_before']==m['CPU_rng_after'] for m in done['models'])
 for m in sorted(k for k in payload if k.endswith('_trace.npz')):
  run=m.split('/')[-1].split('__',1)[0];cid=m.split('/')[-1].split('__',1)[1][:-10];r=rmap[cid];assert run.startswith(r['fold']+'_')
  assert digest(Path(r['path']).read_bytes())==r['sha256'];ref=np.load(r['path']);j=ref['a_is_j'];q=ref['a_centers'][j];w=ref['a_weights'][j];norm=r['normalization'];z=np.load(io.BytesIO(payload[m]));assert len(z.files)==18
  world=lambda x:np.asarray(x,dtype=float)*norm['scale']+np.array(norm['center'])
  raw=world(z['fps512_input_coordinates'][0].T);c512=world(z['fps512_output_coordinates'][0].T);c256=world(z['fps256_output_coordinates'][0].T);f1=z['fps512_indices'][0].astype(int);f2=z['fps256_indices'][0].astype(int)
  assert np.array_equal(raw[f1],c512) and np.array_equal(c512[f2],c256)
  pf=r['point_files'][run.split('_')[1]];assert digest(Path(pf['path']).read_bytes())==pf['sha256'];point=np.load(pf['path']);assert np.array_equal(z['fps512_input_coordinates'][0].T,point['partial'])
  gs=[z['graph%d_knn_indices'%k][0].astype(int) for k in range(1,5)];g1,g2,g3,g4=gs
  assert [g.shape for g in gs]==[(len(raw),16),(512,16),(512,16),(256,16)]
  for k,(nk,nq) in enumerate([(len(raw),len(raw)),(len(raw),512),(512,512),(512,256)]):assert gs[k].min()>=0 and gs[k].max()<nk
  predname=m.replace('_trace.npz','.npz');pred=world(np.load(io.BytesIO(payload[predname]))['prediction']);gt=world(point['implant'])
  near=cKDTree(q).query(raw,workers=2)[0]<=1
  direct=np.unique(g2);i3=np.unique(np.r_[g4.ravel(),f2]);i2=np.unique(np.r_[g3[i3].ravel(),i3]);i1=np.unique(np.r_[g2[i2].ravel(),f1[i2]]);reach=np.unique(np.r_[g1[i1].ravel(),i1])
  support1=near|near[g1].any(1);support2=support1[f1]|support1[g2].any(1);support3=support2|support2[g3].any(1);support4=support3[f2]|support3[g4].any(1)
  stage={'input':raw,'center512_coordinates':c512,'proxy256_coordinates':c256,'graph2_direct_input_union':raw[direct],'final_proxy_possible_raw_dependency_union':raw[reach],'prediction':pred,'GT8192':gt}
  metrics={k:metric(q,w,v) for k,v in stage.items()}
  row={'run':run,'case_id':cid,'source_id':r['source_id'],'metrics':metrics,'input_points_within1mm_of_J_centers':int(near.sum()),'interface_point_fraction_retained_in_graph2_direct_union':float(near[direct].sum()/max(1,near.sum())),'interface_point_fraction_in_final_possible_dependency_union':float(near[reach].sum()/max(1,near.sum())),'center512_features_with_possible_near_J_dependency':int(support2.sum()),'proxy256_features_with_possible_near_J_dependency':int(support4.sum()),'dependency_interpretation':'possible computational connectivity only; not measured feature preservation, max-pool selection or causal importance'}
  rows.append(row);dump(O/(run+'_metrics.json'),row)
  np.savez_compressed(O/(run+'_world_geometry.npz'),input=raw,center512=c512,proxy256=c256,J=q,J_weights=w,possible_raw_indices=reach)
dump(O/'results.json',{'rows':rows,'archive_sha256':expected,'members_verified':11,'models_loaded':0,'GPU':0,'new_forward':0})
fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
stages=['input','center512_coordinates','proxy256_coordinates','graph2_direct_input_union','final_proxy_possible_raw_dependency_union','prediction','GT8192'];labels=['input','512 coord','256 coord','direct union','possible union','prediction','GT']
for r in rows:
 axes[0].plot(range(len(stages)),[100*r['metrics'][s]['J_cover2'] for s in stages],'o-',label=r['run']);axes[1].plot(range(len(stages)),[r['metrics'][s]['J_p95_mm'] for s in stages],'o-',label=r['run'])
for ax in axes:ax.set_xticks(range(len(stages)),labels,rotation=25);ax.grid(alpha=.2)
axes[0].set_title('Actual traces: J coverage at 2 mm (%)');axes[1].set_title('Actual traces: J P95 (mm)');axes[0].legend();fig.suptitle('Coordinates, possible neighborhood support, and output are different evidence\nTwo fixed cases; no additional model execution');fig.savefig(O/'actual_trace_interface_metrics.png',dpi=150);plt.close(fig)
for r in rows:print(json.dumps(r),flush=True)
