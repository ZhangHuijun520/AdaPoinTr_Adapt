# -*- coding: utf-8 -*-
"""Versioned audit-only numerical-contract repair; leave old audit and evidence intact."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];O=R/'outputs/spcg_visualization_freeze_20261117_v2';O.mkdir(exist_ok=False)
oldpath=R/'outputs/spcg_visualization_freeze_20261117_v1/readonly_diagnostic_freeze_audit_v1.py';old=oldpath.read_text(encoding='utf-8')
line="  d=support_distance[mask];w=ref['a_weights'][mask];order=np.argsort(d,kind='stable');p95=d[order[min(np.searchsorted(np.cumsum(w[order]),.95*w.sum(),side='left'),len(d)-1)]]"
assert old.count(line)==1
helper='''def audit_weighted_p95(dist,weights):
 dist=np.asarray(dist,np.float64);weights=np.asarray(weights,np.float64)
 assert dist.ndim==weights.ndim==1 and len(dist)==len(weights)>0,'quantile shape/nonempty'
 assert np.all(weights>0) and np.isfinite(weights).all() and not np.isnan(dist).any(),'quantile values'
 order=np.argsort(dist,kind='mergesort');cumulative=np.cumsum(weights[order],dtype=np.float64)
 index=min(np.searchsorted(cumulative,.95*cumulative[-1],side='left'),len(dist)-1)
 return float(dist[order[index]])

'''
new=old.replace(line,"  d=support_distance[mask];w=ref['a_weights'][mask];p95=audit_weighted_p95(d,w)")
new=new.replace('def independent_stats(',helper+'def independent_stats(')
new=new.replace('FORMAL_SPCG_FIVE_CASE_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS','FORMAL_SPCG_FIVE_CASE_POST_DIAGNOSTIC_FREEZE_AUDIT_V2_PASS')
new=new.replace('日期：2026-11-17。状态：**PASS**','日期：2026-11-17。版本：v2，仅修正审计加权P95的排序累积阈值合同；旧v1失败记录保留。状态：**PASS**')
def funcs(source):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
a,b=funcs(old),funcs(new);assert set(b)-set(a)=={'audit_weighted_p95'}
assert all(a[k]==b[k] for k in a if k not in {'main','independent_stats'})
# Prove no other changes: invert the exact permitted substitutions.
restored=new.replace(helper,'').replace("  d=support_distance[mask];w=ref['a_weights'][mask];p95=audit_weighted_p95(d,w)",line).replace('FORMAL_SPCG_FIVE_CASE_POST_DIAGNOSTIC_FREEZE_AUDIT_V2_PASS','FORMAL_SPCG_FIVE_CASE_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS').replace('日期：2026-11-17。版本：v2，仅修正审计加权P95的排序累积阈值合同；旧v1失败记录保留。状态：**PASS**','日期：2026-11-17。状态：**PASS**')
assert restored==old
p=O/'readonly_diagnostic_freeze_audit_v2.py';p.write_text(new,encoding='utf-8',newline='\n')
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
review=dict(status='STATIC_AUDIT_ONLY_CHANGE_REVIEW_PASS',old_audit=rec(oldpath),new_audit=rec(p),old_failure=rec(R/'outputs/spcg_visualization_freeze_20261117_v1/audit_failure_v1.json'),cause_investigation=rec(Path(__file__).parent/'investigation_result_v1.json'),allowed_changes=['One audit-only weightedP95 helper and one call site','Versioned success/report labeling only'],other_code_AST_unchanged=True,inverse_exact_text_diff_check=True,tolerances_unchanged=True,production_or_scientific_changes=False,regression_executed=False,audit_executed=False)
with (O/'static_change_review_v2.json').open('x',encoding='utf-8') as f:json.dump(review,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=review['status'],new_audit=review['new_audit'])))
