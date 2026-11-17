# -*- coding: utf-8 -*-
"""One failed cloud only: inspect numerical contracts; do not repair or rerun audit."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
from pathlib import Path
import ast,hashlib,json,io,tarfile,importlib.util
import numpy as np
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
V=R/'outputs/spcg_coarse_dense_visualization_20261117_v1';S=R/'outputs/spcg_score_implementation_20261117_v1';F=R/'outputs/spcg_visualization_freeze_20261117_v1';C=R/'outputs/spcg_score_freeze_20261117_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):
 p=Path(p);s=p.stat();return dict(path=str(p.resolve()),bytes=s.st_size,sha256=sha(p),fingerprint=[getattr(s,k) for k in ['st_ino','st_dev','st_mode','st_size','st_mtime_ns','st_ctime_ns']])
def exact(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in [p,*p.parents]);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
def load(p):return json.loads(Path(p).read_bytes())
def emit(name,v):
 with (O/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def get_function(p,name,namespace):
 tree=ast.parse(Path(p).read_text(encoding='utf-8'));nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name];assert len(nodes)==1
 module=ast.Module(body=nodes,type_ignores=[]);exec(compile(ast.fix_missing_locations(module),str(p)+'::'+name,'exec'),namespace);return namespace[name]
def differences(a,b,prefix=''):
 out=[]
 if isinstance(a,dict):
  assert set(a)==set(b)
  for k in a:out.extend(differences(a[k],b[k],prefix+'.'+k))
 elif isinstance(a,list):
  assert len(a)==len(b)
  for i,(x,y) in enumerate(zip(a,b)):out.extend(differences(x,y,prefix+'['+str(i)+']'))
 elif isinstance(a,(float,int)) and not isinstance(a,bool):
  if not np.isclose(a,b,rtol=1e-11,atol=1e-10):out.append(dict(field=prefix,saved=a,independent_audit=b,delta=float(b-a)))
 elif a!=b:out.append(dict(field=prefix,saved=a,independent_audit=b))
 return out
def main():
 assert not (O/'investigation_result_v1.json').exists()
 failure=load(F/'audit_failure_v1.json');assert failure['status']=='AUDIT_FAILED_STOP_NO_RETRY' and failure['error']=="AssertionError('train__008__random_2 G0 coarse')"
 q=load(S/'SPCG_local_scoring_execution_request_v1.json');idx=load(exact(q['score_case_index']));cid='train__008__random_2';arm='G0';fold='D';case=next(c for c in idx['cases'] if c['case_id']==cid);binding=next(b for b in idx['prediction_records'] if (b['fold'],b['arm'],b['case_id'])==(fold,arm,cid))
 metric_path=exact(q['implementation']['metrics']);archive=exact(q['archive_inputs']['SPCG']['archive']);point=exact(case['point_file']);refpath=exact(case['reference'])
 auditcode=F/'readonly_diagnostic_freeze_audit_v1.py';visualcode=C/'visualize_fixed_coarse_dense_cases_v1.py';data=V/'fixed_case_geometry_metrics_v1.json'
 targets=[F/'audit_failure_v1.json',auditcode,visualcode,metric_path,data,V/'frozen_case_scope_v1.json',V/'completion_v1.json',V/'artifact_manifest_v1.json',V/'final_delivery_manifest_v1.json',S/'SPCG_local_scoring_execution_request_v1.json',Path(q['score_case_index']['path']),archive,point,refpath]
 before=[rec(p) for p in targets]
 # Only extract pure functions; never import the top-level renderer or audit.
 spec=importlib.util.spec_from_file_location('frozen_metric_single_failure_readonly',metric_path);metric=importlib.util.module_from_spec(spec);spec.loader.exec_module(metric)
 ns={'np':np,'cKDTree':cKDTree};independent=get_function(auditcode,'independent_stats',dict(ns));original=get_function(visualcode,'stats',dict(ns))
 with np.load(point,allow_pickle=False) as z:G=metric.world_points(z['implant'],case['normalization'])
 with np.load(refpath,allow_pickle=False) as z:ref={k:z[k] for k in z.files}
 with tarfile.open(archive,'r:gz') as t:
  blob=t.extractfile(binding['member']).read();assert len(blob)==binding['bytes'] and hashlib.sha256(blob).hexdigest()==binding['sha256']
  with np.load(io.BytesIO(blob),allow_pickle=False) as z:
   assert z.files==['prediction','coarse'];coarse=z['coarse'].copy()
 assert coarse.shape==(256,3) and coarse.dtype==np.float32 and np.isfinite(coarse).all();x=metric.world_points(coarse,case['normalization']);roi=np.stack([G.min(0)-10,G.max(0)+10]);a2,_,_=metric.a2_reference(ref);tree=cKDTree(a2)
 savedcase=next(c for c in load(data)['cases'] if c['case_id']==cid);saved=savedcase['metrics'][arm]['coarse']
 old,_=original(x,G,tree,ref,metric);old['points_outside_GT_ROI']=int((~np.all((x>=roi[0])&(x<=roi[1]),axis=1)).sum())
 new=independent(x,G,tree,ref,metric,roi);saved_vs_original=differences(saved,old);saved_vs_audit=differences(saved,new)
 assert not saved_vs_original and saved_vs_audit,'must distinguish saved metric from audit implementation'
 distances=cKDTree(x).query(ref['a_centers'],workers=2)[0];details={}
 for label,mask in [('E',~ref['a_is_j']),('J',ref['a_is_j'])]:
  d=distances[mask];w=ref['a_weights'][mask];order=np.argsort(d,kind='mergesort');stable=np.argsort(d,kind='stable');cumulative=np.cumsum(w[order],dtype=np.float64);total_sum=w.sum();total_cum=cumulative[-1];tf=.95*total_cum;ta=.95*total_sum
  i_f=min(int(np.searchsorted(cumulative,tf,side='left')),len(d)-1);i_a=min(int(np.searchsorted(cumulative,ta,side='left')),len(d)-1)
  neighborhood=[dict(sorted_index=i,distance_mm=float(d[order[i]]),weight=float(w[order[i]]),cumulative_weight=float(cumulative[i]),cumulative_minus_frozen_threshold=float(cumulative[i]-tf),cumulative_minus_audit_threshold=float(cumulative[i]-ta)) for i in range(max(0,min(i_f,i_a)-2),min(len(d),max(i_f,i_a)+3))]
  details[label]=dict(reference_face_count=len(d),argsort_orders_identical=bool(np.array_equal(order,stable)),weight_sum=float(total_sum),sorted_cumulative_final=float(total_cum),total_difference=float(total_cum-total_sum),frozen_threshold=float(tf),audit_threshold=float(ta),threshold_difference=float(tf-ta),frozen_index=i_f,audit_index=i_a,frozen_distance_mm=float(d[order[i_f]]),audit_distance_mm=float(d[order[i_a]]),frozen_function_value=metric.weighted_quantile(d,w,.95),sorted_neighborhood=neighborhood)
 assert all(r['field'].endswith('.p95_mm') for r in saved_vs_audit)
 for diff in saved_vs_audit:
  label=diff['field'].split('.')[2];d=details[label];assert d['argsort_orders_identical'] and d['frozen_index']!=d['audit_index'] and diff['saved']==d['frozen_distance_mm'] and diff['independent_audit']==d['audit_distance_mm']
 after=[rec(p) for p in targets];assert before==after,'read-only source drift'
 result=dict(status='LIMITED_READONLY_CAUSE_IDENTIFIED_NO_REPAIR_NO_RERUN',case_id=cid,fold=fold,arm=arm,stage='coarse',saved_vs_frozen_original_differences=saved_vs_original,saved_vs_independent_audit_differences=saved_vs_audit,quantile_details=details,root_cause='Audit reimplementation changed weighted-percentile threshold total from sorted cumulative final to pairwise np.sum. FP64 summation order changes threshold rounding at a discrete CDF boundary and selects a neighboring distance. Frozen visualization values reproduce the authoritative frozen metric.',source_before=before,source_after=after,source_content_stable=True,prediction_member_binding=binding,operations=dict(selected_failed_pointsets_inspected=1,full_audit_reruns=0,visualization_reruns=0,source_repairs=0,model_forwards=0,training_updates=0,parameter_scans=0),limitations=['Finding applies to this exact failedG0/coarse pointset; remaining formal audit checks have not passed.','Does not reclassify the original failed audit as PASS.','Only a future separately authorized audit correction may align to the frozen numerical contract; no tolerance widening or original-score replacement is performed here.'])
 emit('investigation_result_v1.json',result)
 lines=['# 单个coarse审计差异：限定只读原因核查','',
'状态：原因已查明；未修复、未重跑正式审计。','',
'对象仅为 D折 `train__008__random_2 / G0 / coarse256`，读取已有成员、GT点集与参考数据，以原函数及失败审计函数核对这一个点集。没有重新执行整套可视化或审计。','',
'## 核查结果','',
'保存指标与冻结原始指标函数完全一致。不一致来自审计辅助实现的加权P95口径：冻结函数先排序并累加权重，以 `0.95 * cumulative[-1]` 为阈值；独立审计改用了 `0.95 * weights.sum()`。两种求和次序在FP64中有微小舍入差异，恰好遇到离散CDF边界时选中了相邻位置。这是审计实现没有严格复现冻结数值定义，不是已证实的预测、坐标或原始评分错误。','',
'|字段|保存值/mm|审计重算值/mm|差值/mm|','|---|---:|---:|---:|']
 for d in saved_vs_audit:lines.append(f"|{d['field']}|{d['saved']:.12f}|{d['independent_audit']:.12f}|{d['delta']:+.12f}|")
 lines+=['','## 分位数边界证据','']
 for label,d in details.items():
  lines+=['### '+label,'',f"权重直接求和：`{d['weight_sum']:.17g}`；排序累积末值：`{d['sorted_cumulative_final']:.17g}`。",'',f"冻结阈值：`{d['frozen_threshold']:.17g}`；审计阈值：`{d['audit_threshold']:.17g}`。",'',f"两种排序结果完全一致：`{d['argsort_orders_identical']}`；选择的零起始索引为 `{d['frozen_index']}` 与 `{d['audit_index']}`。相邻累计权重、阈值差和距离见JSON。",'']
 lines+=['## 边界与后续','',
'本次所有14个受检源文件的哈希及内容相关属性在核查前后保持一致。原图、指标、冻结指标源码、审计脚本和失败记录均未修改。未放宽容差、替换分数或将失败审计改判为通过。','',
'后续如授权修订，应仅使审计加权P95遵循冻结函数的排序/累积/阈值口径，补这个边界的回归，再执行新版正式只读审计；不修改科研产物或原评分定义。当前剩余正式审计仍未完成。','']
 report=O/'单个coarse差异_限定只读原因核查报告_zh_v1.md'
 with report.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
 emit('delivery_manifest_v1.json',dict(status=result['status'],files=[rec(p) for p in sorted(O.iterdir()) if p.is_file()]))
 print(json.dumps(dict(status=result['status'],differences=saved_vs_audit,all_sources_unchanged=True),ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except BaseException as exc:emit('investigation_failure_v1.json',dict(status='INVESTIGATION_FAILED_STOP',error=repr(exc)));raise
