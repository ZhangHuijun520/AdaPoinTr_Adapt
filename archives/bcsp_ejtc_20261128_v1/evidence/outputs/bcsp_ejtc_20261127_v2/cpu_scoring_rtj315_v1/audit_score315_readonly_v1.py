"""Independent arithmetic reconstruction from frozen scores; never calls scoring core."""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
d=Path(__file__).resolve().parent;out=d/'cpu_scored_once_v1';e=d/'post_score_freeze_audit_v1';e.mkdir(exist_ok=False)
h=lambda b:hashlib.sha256(b).hexdigest()
qpath=d/'EJTC_RTJ_D_CPU_scoring_execution_request_v1.json';rid=h(qpath.read_bytes());assert rid=='d45c5342e22ba09a937354efa928f42d2462999c5affa63a9d4f559a8237438e'
q=json.loads(qpath.read_bytes());load=lambda p:json.loads(p.read_bytes())
def inventory():return {p.name:dict(bytes=p.stat().st_size,sha256=h(p.read_bytes())) for p in sorted(out.iterdir()) if p.is_file()}
first=inventory();assert set(first)==set(q['expected_outputs']) and len(list(out.iterdir()))==5
exit=load(d/'score315_execution_exit_v1.json');assert exit['exit_code']==0 and exit['request_sha256']==rid
completion=load(out/'completion.json');assert completion['counts']==q['counts'] and completion['request_sha256']==rid and completion['formal_gate_executed'] is False
auth=load(d/'score315_user_authorization_v1.json');assert auth['request_sha256']==rid and auth['explicit_user_authorization'] is True and rid in auth['user_authorization_text']
for r in q.values():
 if isinstance(r,dict) and {'path','bytes','sha256'}<=set(r):
  p=Path(r['path']);assert p.stat().st_size==r['bytes'] and h(p.read_bytes())==r['sha256']
monitor=[json.loads(r) for r in (d/'score315_resource_monitor_v1.jsonl').read_bytes().splitlines()]
assert monitor and all(r['elapsed_seconds']<=q['limits']['wall_seconds'] and r['RSS_bytes']<=q['limits']['RSS_bytes'] and r['output_bytes']<=q['limits']['output_bytes'] for r in monitor)
assert exit['seconds']<=q['limits']['wall_seconds']
rows=[json.loads(r) for r in (out/'model_scores.jsonl').read_bytes().splitlines()];assert len(rows)==315
by={(r['arm'],r['case_id']):r for r in rows};assert len(by)==315 and set(by)=={(a,c) for a in q['arms'] for c in q['case_ids']}
index=load(Path(q['case_index']['path']))['cases'];sources=q['source_ids'];assert len(sources)==21
for c in index:
 for a in q['arms']:
  r=by[a,c['case_id']];assert r['fold']=='D' and r['source_id']==c['source_id']
  assert r['severe_geometry']==(r['dense']['E_P95_mm']>20 or r['dense']['J_Cover_at_2']==0)
  g=r['geometry']['far_parent_child'];assert g['near_parent_far_child']+g['far_parent_far_child']==g['far_children'] and g['children']==8192 and g['far_children']/8192==r['dense']['far20']
  diag=r['diagnostics'];assert 0<=diag['J_Cover_at_1']<=r['dense']['J_Cover_at_2']<=diag['J_Cover_at_3']<=1
  assert math.isclose(diag['J_area_1_to_3_mm2']/diag['J_area_mm2'],diag['J_fraction_1_to_3'],abs_tol=1e-14)
indices=np.load(out/'source_bootstrap_indices.npy',allow_pickle=False);expected=np.random.Generator(np.random.PCG64(2026112807)).integers(0,21,size=(2000,21),dtype=np.int64);assert np.array_equal(indices,expected)
summary=load(out/'paired_summary.json');assert set(summary)=={'J_minus_R','J_minus_T','T_minus_R'}
def equal(x,y):
 if isinstance(x,dict):assert set(x)==set(y);[equal(x[k],y[k]) for k in x]
 elif isinstance(x,list):assert len(x)==len(y);[equal(a,b) for a,b in zip(x,y)]
 elif isinstance(x,(float,int)) and not isinstance(x,bool):assert math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12),(x,y)
 else:assert x==y,(x,y)
for left,right in [('J','R'),('J','T'),('T','R')]:
 saved=summary[left+'_minus_'+right];pairs=[]
 for cid in q['case_ids']:
  a,b=by[left,cid],by[right,cid]
  pairs.append(dict(case_id=cid,source_id=a['source_id'],defect=cid.split('__')[-1],B_severe=b['severe_geometry'],A_severe=a['severe_geometry'],delta={s:{k:a[s][k]-b[s][k] for k in a[s]} for s in ('coarse','dense')}))
 equal(pairs,saved['pairs']);s=saved['summary'];assert s['source_ids']==sources and s['arm_aliases']=={'A':left,'B':right}
 for stage in ('coarse','dense'):
  for k,v in s['metrics'][stage].items():
   factor=100 if k=='far20' or 'Cover' in k else 1
   vals=np.array([np.mean([p['delta'][stage][k] for p in pairs if p['source_id']==src]) for src in sources])*factor
   equal(v['by_source'],vals.tolist());equal(v['delta_A_minus_B'],float(vals.mean()))
   equal(v['CI95'],np.percentile(vals[indices].mean(axis=1),[2.5,97.5]).tolist())
   leave=(vals.sum()-vals)/20;equal(v['leave_one_source_range'],[float(leave.min()),float(leave.max())])
   equal(v['arm_mean'],{alias:float(np.mean([np.mean([by[arm,c['case_id']][stage][k] for c in index if c['source_id']==src]) for src in sources])*factor) for alias,arm in [('A',left),('B',right)]})
   if k!='radius_gyration_ratio':assert v['improved_sources']==int((vals>0 if 'Cover' in k else vals<0).sum())
  for defect,record in s['defect_deltas'][stage].items():
   p=[r for r in pairs if r['defect']==defect];assert len(p)==21;equal(record,{k:float(np.mean([r['delta'][stage][k] for r in p])) for k in p[0]['delta'][stage]})
 severe=dict(B=[p['case_id'] for p in pairs if p['B_severe']],A=[p['case_id'] for p in pairs if p['A_severe']],new=[p['case_id'] for p in pairs if p['A_severe'] and not p['B_severe']],rescued=[p['case_id'] for p in pairs if p['B_severe'] and not p['A_severe']],common=[p['case_id'] for p in pairs if p['A_severe'] and p['B_severe']])
 equal(severe,s['severe_case_ids'])
diagnostic=load(out/'diagnostic_summary.json')['source_equal_arm_means']
for arm,record in diagnostic.items():equal(record,{k:float(np.mean([np.mean([r['diagnostics'][k] for r in rows if r['arm']==arm and r['source_id']==src]) for src in sources])) for k in rows[0]['diagnostics']})
last=inventory();assert first==last
receipt=dict(status='FORMAL_READ_ONLY_EJTC_SCORE315_POST_SCORING_FREEZE_AUDIT_PASS',request_sha256=rid,counts=q['counts'],output_hashes=first,stable_before_after=True,independent_reconstruction=True,comparisons_recomputed=3,case_pair_deltas_recomputed=315,source_bootstrap_CI_and_leave_one_recomputed=True,severe_lists_and_diagnostics_recomputed=True,recorded_resources_pass=True,exit_code=0,real_distance_scores_rerun=0,score_output_modified=False,test= dict(path=str(Path(__file__)),sha256=h(Path(__file__).read_bytes())),scope='Audit of frozen score outputs, not a second geometry scoring run; no GPU, server or training operations')
with (e/'formal_score_freeze_audit_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt,ensure_ascii=False))
