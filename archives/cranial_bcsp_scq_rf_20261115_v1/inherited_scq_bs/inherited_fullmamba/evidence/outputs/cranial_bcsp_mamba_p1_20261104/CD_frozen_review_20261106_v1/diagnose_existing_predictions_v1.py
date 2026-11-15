import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'mplconfig')
import json,hashlib,tarfile,io,importlib.util,time,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
START=time.monotonic();B=ROOT.parent
plan=json.loads((ROOT/'frozen_diagnostic_selection_v1.json').read_text(encoding='utf8'));review=json.loads((ROOT/'frozen_CD_descriptive_review_v1.json').read_text(encoding='utf8'))
def check(r):
 p=Path(r['path']);assert p.is_file() and p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];return p
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
metric_path=B.parent/'cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py';assert hashlib.sha256(metric_path.read_bytes()).hexdigest()=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766';spec=importlib.util.spec_from_file_location('frozen_metric_diagnostic',metric_path);metric=importlib.util.module_from_spec(spec);spec.loader.exec_module(metric)
FIG=ROOT/'figures';FIG.mkdir();data=[];inputs=[];arcs={}
for fold,d in review.items():
 R=Path(d['root']);V=load(R/'local_download_verification_v1/verification_result_v1.json');arcs[fold]=tarfile.open(check(V['download_files'][0]),'r:gz');inputs.append(V['download_files'][0]);cases=load(R/'CPU_scoring_preparation_v1'/('P1_score_case_index_v1.json' if fold=='C' else 'P1_D_score_case_index_v1.json'))['cases'];d['cases_lookup']={c['case_id']:c for c in cases}
try:
 for item in plan['selected_cases']:
  assert time.monotonic()-START<600
  fold,cid=item['fold'],item['case_id'];d=review[fold];R=Path(d['root']);case=d['cases_lookup'][cid];check(case['reference']);check(case['point_file']);inputs.extend([case['reference'],case['point_file']])
  with np.load(case['point_file']['path'],allow_pickle=False) as z:gt=metric.world_points(z['implant'],case['normalization'])
  with np.load(case['reference']['path'],allow_pickle=False) as z:ref={k:z[k] for k in z.files}
  a2,_,_=metric.a2_reference(ref);E=~ref['a_is_j'];J=ref['a_is_j'];clouds={};stats={};manifest=[json.loads(l) for l in arcs[fold].extractfile('inference_manifest.jsonl').read().splitlines()];lookup={(r['run'],r['case_id']):r for r in manifest};saved=next(r for r in d['case_deltas'] if r['case_id']==cid)
  for arm in ['T0','M0']:
   mr=lookup[(fold+'_'+arm,cid)];blob=arcs[fold].extractfile(mr['prediction']['name']).read();assert len(blob)==mr['prediction']['bytes'] and hashlib.sha256(blob).hexdigest()==mr['prediction']['sha256']
   with np.load(io.BytesIO(blob),allow_pickle=False) as z:p=metric.world_points(z['prediction'],case['normalization'])
   assert p.shape==(8192,3) and np.isfinite(p).all();reverse=metric.nearest(p,a2);forward=metric.nearest(ref['a_centers'],p);se=metric.stats(forward[E],ref['a_weights'][E]);sj=metric.stats(forward[J],ref['a_weights'][J]);out=reverse>20
   # Recheck selected geometry only against existing scores, never replace official metrics.
   observed=dict(E_P95_mm=se['p95_mm'],J_P95_mm=sj['p95_mm'],E_coverage_2mm=se['coverage']['2.0'],J_coverage_2mm=sj['coverage']['2.0'],reverse20_fraction=float(out.mean()))
   original=saved[arm]
   for key,originalkey in [('E_P95_mm','E_P95_mm'),('J_P95_mm','J_P95_mm'),('E_coverage_2mm','E_coverage_2.0mm'),('J_coverage_2mm','J_coverage_2.0mm'),('reverse20_fraction','reverse_A2_outlier_20.0mm')]:assert np.isclose(observed[key],original[originalkey],rtol=1e-10,atol=1e-10)
   record=dict(fold=fold,case_id=cid,arm=arm,reasons=item['reasons'],**observed,outlier20_count=int(out.sum()),outlier20_bbox=np.stack([p[out].min(0),p[out].max(0)]).tolist() if out.any() else None,centroid_offset_mm=original['centroid_offset_mm'],CD_L1_mm=original['CD_L1_mm'],uncovered_E_area_mm2=float(ref['a_weights'][E][forward[E]>2].sum()),E_area_mm2=float(ref['a_weights'][E].sum()),uncovered_J_area_mm2=float(ref['a_weights'][J][forward[J]>2].sum()),J_area_mm2=float(ref['a_weights'][J].sum()),prediction_binding=mr['prediction'],frame='native_world_mm_no_alignment')
   stats[arm]=(p,reverse,forward,record);clouds[arm]=p;data.append(record)
  # Shared full bounds across both models/views. No outlier clipping or GT alignment.
  allp=np.concatenate([gt,clouds['T0'],clouds['M0']]);lo=allp.min(0);hi=allp.max(0);pad=np.maximum((hi-lo)*.04,2);lo-=pad;hi+=pad
  fig,axes=plt.subplots(4,3,figsize=(13,15),layout='constrained');proj=[(0,1),(0,2),(1,2)];names=['X','Y','Z']
  Eids=np.flatnonzero(E)[::max(1,int(E.sum())//6000)];Jids=np.flatnonzero(J)[::max(1,int(J.sum())//1200)]
  for i,arm in enumerate(['T0','M0']):
   p,reverse,forward,r=stats[arm];colors=np.where(reverse>20,'#d73027',np.where(reverse>2,'#f6a21a','#2369b5'))
   for j,(x,y) in enumerate(proj):
    ax=axes[i,j];ax.scatter(gt[:,x],gt[:,y],s=1,c='#777777',alpha=.22,rasterized=True);ax.scatter(p[:,x],p[:,y],s=1.5,c=colors,alpha=.65,rasterized=True)
    ax.set_title(f"{arm} pred→A2 | >20mm {r['outlier20_count']}/8192 | CD {r['CD_L1_mm']:.2f}")
    ax=axes[i+2,j];ax.scatter(p[:,x],p[:,y],s=1,c='#bbbbbb',alpha=.2,rasterized=True);v=ref['a_centers'][Eids];ax.scatter(v[:,x],v[:,y],s=2,c=np.where(forward[Eids]>2,'#cf4b21','#147fb0'),alpha=.6,rasterized=True);v=ref['a_centers'][Jids];ax.scatter(v[:,x],v[:,y],s=2,c='#08783e',alpha=.45,rasterized=True)
    ax.set_title(f"{arm} E coverage@2mm {100*r['E_coverage_2mm']:.1f}% | J {100*r['J_coverage_2mm']:.1f}%")
   for row in [i,i+2]:
    for j,(x,y) in enumerate(proj):
     ax=axes[row,j];ax.set_xlim(lo[x],hi[x]);ax.set_ylim(lo[y],hi[y]);ax.set_aspect('equal',adjustable='box');ax.set_xlabel(names[x]+' (mm)');ax.set_ylabel(names[y]+' (mm)');ax.grid(alpha=.15)
  fig.suptitle(f"Fold {fold} | {cid}\nTop: gray GT8192; prediction blue≤2 / orange2–20 / red>20mm to A2\nBottom: E blue≤2 / orange>2mm to prediction; green J reference. Shared native-world bounds; no alignment.\nReference dots use deterministic stride for display only; NN/area diagnostics use all points/faces.",fontsize=12)
  name=fold+'__'+cid+'.png';fig.savefig(FIG/name,dpi=115);plt.close(fig);print(json.dumps(dict(case=fold+':'+cid,figure=name,stats={a:{k:stats[a][3][k] for k in ['E_P95_mm','E_coverage_2mm','outlier20_count','centroid_offset_mm','CD_L1_mm']} for a in ['T0','M0']})),flush=True)
finally:
 for t in arcs.values():t.close()
assert len(data)==2*len(plan['selected_cases']);assert 'torch' not in __import__('sys').modules
with (ROOT/'selected_case_geometry_v1.json').open('x',encoding='utf8') as f:json.dump(dict(status='SELECTED_PREDICTIONS_GEOMETRY_DIAGNOSTIC_COMPLETE',records=data,selected_cases=len(plan['selected_cases']),prediction_arrays=len(data),official_metrics_unchanged=True,selected_geometric_rechecks_match_frozen_scores=True,no_alignment=True,server_calls=0,GPU_calls=0,model_calls=0,seconds=time.monotonic()-START),f,indent=2)
with (ROOT/'diagnostic_input_bindings_v1.json').open('x',encoding='utf8') as f:json.dump(inputs,f,indent=2)
with (ROOT/'selected_case_geometry_v1.csv').open('x',encoding='utf8',newline='') as f:
 fields=['fold','case_id','arm','E_P95_mm','J_P95_mm','E_coverage_2mm','J_coverage_2mm','reverse20_fraction','outlier20_count','centroid_offset_mm','CD_L1_mm','uncovered_E_area_mm2','E_area_mm2','uncovered_J_area_mm2','J_area_mm2'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in data)
print(json.dumps(dict(status='COMPLETE',cases=len(plan['selected_cases']),arrays=len(data),seconds=time.monotonic()-START)))
