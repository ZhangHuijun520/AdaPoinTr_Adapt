"""Read saved score artifacts, independently check reductions; no NN/scoring/model calls."""
from pathlib import Path
import csv,hashlib,json,statistics
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_dac_r01_preparation_20261115_v1/fixed20_offline_geometry_v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(O/'output_manifest.json')
for r in manifest['files']:
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
rows=[json.loads(s) for s in (O/'case_scores.jsonl').read_text().splitlines()];done=read(O/'completion.json')
assert len(rows)==60 and done['status']=='FIXED20_FROZEN_WEIGHT_CPU_GEOMETRY_COMPLETE' and done['historical_R_rows_reproduced']==20
assert {(r['fold'],r['case_id'],r['arm']) for r in rows}=={(r['fold'],r['case_id'],arm) for r in rows for arm in ('R','A','DAC')}
by={(r['fold'],r['case_id'],r['arm']):r for r in rows}
for r in rows:
 m=r['metrics'];p=r['position_shape']
 assert r['risk_labels']==dict(placement_tail=p['centroid_offset_mm']>20.,compact_distribution=p['radius_gyration_ratio']<.9,severe_geometry=m['E_P95_mm']>20. or m['J_coverage_2.0mm']==0.)
 assert m['E_P95_mm']==r['full_metrics']['regions']['A1']['E']['p95_mm'] and m['J_P95_mm']==r['full_metrics']['regions']['A1']['J']['p95_mm'] and m['J_coverage_2.0mm']==r['full_metrics']['regions']['A1']['J']['coverage']['2.0']
for s in read(O/'fold_fixed_case_summary.json'):
 part=[r for r in rows if r['fold']==s['fold'] and r['arm']==s['arm']]
 assert len(part)==10 and sum(r['risk_labels']['severe_geometry'] for r in part)==s['severe']
 for k,v in s['metrics'].items():assert abs(statistics.mean(r['metrics'][k] for r in part)-v)<1e-10
deltas=read(O/'paired_case_deltas.json');assert len(deltas)==60
for r in deltas:
 cand,base=r['comparison'].split('-');a,b=(by[r['fold'],r['case_id'],arm] for arm in (cand,base))
 assert all(abs(v-(a['metrics'][k]-b['metrics'][k]))<1e-12 for k,v in r['metrics'].items())
for r in read(O/'severe_transitions.json'):
 cand,base=r['comparison'].split('-');part=[x for x in rows if x['fold']==r['fold'] and x['arm']==cand]
 rebuilt=dict(new=[],rescued=[],shared=[],stable_nonsevere=[])
 for x in part:
  old=by[r['fold'],x['case_id'],base]['risk_labels']['severe_geometry'];new=x['risk_labels']['severe_geometry']
  key='shared' if old and new else 'new' if new else 'rescued' if old else 'stable_nonsevere';rebuilt[key].append(x['case_id'])
 assert all(r[k]==v for k,v in rebuilt.items()) and r['counts']=={k:len(v) for k,v in rebuilt.items()}
with (O/'case_scores.csv').open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f))
assert len(csvrows)==60
for a,b in zip(csvrows,rows):
 assert a['case_id']==b['case_id'] and a['arm']==b['arm'] and all(abs(float(a[k])-v)<1e-12 for k,v in b['metrics'].items())
res=[json.loads(l) for l in (O/'resources.jsonl').read_text().splitlines()];assert len(res)==141 and max(x['RSS_bytes'] for x in res)<=8589934592 and max(x['elapsed_seconds'] for x in res)<=1800
paired=[]
for fold in 'CD':
 for pair in ('DAC-A','DAC-R','A-R'):
  part=[r for r in deltas if r['fold']==fold and r['comparison']==pair];assert len(part)==10
  record=dict(fold=fold,comparison=pair,cases=10,metrics={})
  for k in ('E_P95_mm','J_P95_mm','E_coverage_2.0mm','J_coverage_2.0mm','CD_L1_mm','reverse_A2_P95_mm','reverse_A2_outlier_20.0mm'):
   v=[r['metrics'][k] for r in part];improve=sum(x>0 if 'coverage' in k else x<0 for x in v)
   record['metrics'][k]=dict(mean=statistics.mean(v),median=statistics.median(v),improved=improve,worsened=sum(x!=0 for x in v)-improve,equal=sum(x==0 for x in v))
  paired.append(record)
result=dict(status='SAVED_FIXED20_GEOMETRY_RESULTS_HASH_AND_REDUCTION_VERIFIED',case_score_rows=60,paired_deltas=60,resource_samples=141,source_count=len({r['source_id'] for r in rows}),source_counts_by_fold={f:len({r['source_id'] for r in rows if r['fold']==f}) for f in 'CD'},score_rows_recomputed_in_this_verification=0,NN_calls=0,forward=0,server_calls=0,paired_descriptive=paired,limitations=['Fixed selected20 pressure/hash cases, incomplete source defect sets, no21-source formal gate','Old Requery trained weights and counterfactual head combinations; not new end-to-end DAC training','RNG audit retained its previously disclosed fingerprint limitation'])
with (O/'saved_result_consistency_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
decision=dict(status='RECOMMEND_NO_NEW_TRAINING_FOR_CURRENT_FIXED_DAC_FORMULA',basis='Frozen-weight R1 scientific budget decision, not a formal M/U/R gate or proof all end-to-end DAC training is impossible',evidence=['DAC-A E/J P95 mean worse in both fixed10-case folds','DAC-R E P95 changes small and J Cover2 mean down in both folds','DAC-R severe3/2 unchanged, no rescued severe','Average has reverse-tail and rescue-case tradeoffs, not an automatic replacement'],next='Close current DAC formula or separately discuss a new hypothesis; no gate/epsilon/temperature search and no training request created',new_forward=0,new_training=0)
with (O/'candidate_training_recommendation_v1.json').open('x',encoding='utf-8') as f:json.dump(decision,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=result['status'],sources=result['source_counts_by_fold'],recommendation=decision['status'])))
