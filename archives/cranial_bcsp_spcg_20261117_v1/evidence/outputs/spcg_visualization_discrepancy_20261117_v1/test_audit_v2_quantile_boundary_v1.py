# -*- coding: utf-8 -*-
"""One artificial CPU boundary regression batch; no audit or scientific-data execution."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
from pathlib import Path
import ast,hashlib,json,importlib.util,sys
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'outputs/spcg_visualization_freeze_20261117_v2';A=O/'artificial_quantile_regression_v1';CHECKS=[]
def emit(name,v):
 with (A/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def check(name,ok):assert ok,name;CHECKS.append(name)
def main():
 A.mkdir(exist_ok=False);audit=O/'readonly_diagnostic_freeze_audit_v2.py';review=json.loads((O/'static_change_review_v2.json').read_bytes());assert rec(audit)==review['new_audit']
 tree=ast.parse(audit.read_text(encoding='utf-8'));f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='audit_weighted_p95');ns={'np':np}
 exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),str(audit)+'::quantile-only','exec'),ns);fixed=ns['audit_weighted_p95']
 metric=R/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py'
 check('frozen_metric_SHA_unchanged',hashlib.sha256(metric.read_bytes()).hexdigest()=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766')
 spec=importlib.util.spec_from_file_location('frozen_quantile_only_regression',metric);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 d=np.arange(34820,dtype=np.float64)/1000;w=np.full(34820,.16000000000000003,np.float64);order=np.argsort(d,kind='mergesort');cum=np.cumsum(w[order],dtype=np.float64)
 legacy=float(d[order[min(np.searchsorted(cum,.95*w.sum(),side='left'),len(d)-1)]]);value=fixed(d,w)
 check('artificial34820_face_boundary_matches_frozen',value==m.weighted_quantile(d,w,.95)==33.078)
 check('regression_detects_original_audit_error',legacy==33.079 and legacy!=value)
 check('sorted_cumulative_threshold_is_authority',cum[-1]!=w.sum() and .95*cum[-1]<.95*w.sum())
 for name,dd,ww in [('one_point',[7.],[3.]),('exact95CDF',list(range(20)),[1.]*20),('distance_ties',[4.,0.,4.,2.],[1.,1.,2.,1.]),('nonuniform_weights',[9.,1.,3.,8.],[.3,.1,5.,.2]),('float32_inputs',np.array([3.,2.,1.],np.float32),np.array([.1,.2,.7],np.float32)),('infinite_distance',[1.,float('inf')],[1.,1.]),('zero_distance',[0.,0.,0.],[1.,2.,3.])]:
  check(name,fixed(dd,ww)==m.weighted_quantile(dd,ww,.95))
 for name,dd,ww in [('empty',[],[]),('length_mismatch',[1.,2.],[1.]),('non_vector',[[1.,2.]],[[1.,1.]]),('zero_weight',[1.],[0.]),('negative_weight',[1.],[-1.]),('nonfinite_weight',[1.],[float('inf')]),('nan_distance',[float('nan')],[1.])]:
  rejected=False
  try:fixed(dd,ww)
  except AssertionError:rejected=True
  check(name+'_rejected',rejected)
 check('no_model_import_or_GPU','torch' not in sys.modules and os.environ['CUDA_VISIBLE_DEVICES']=='')
 emit('boundary_fixture_and_result_v1.json',dict(shape=[34820],weights_value=.16000000000000003,distance_definition='arange(34820)/1000; artificial, not actual skull distances',frozen_value=value,legacy_value=legacy,cumulative_total=float(cum[-1]),direct_sum=float(w.sum()),fixed_threshold=float(.95*cum[-1]),legacy_threshold=float(.95*w.sum())))
 result=dict(status='ARTIFICIAL_AUDIT_V2_QUANTILE_REGRESSION_PASS',checks=CHECKS,check_count=len(CHECKS),source_bindings=[rec(audit),rec(Path(__file__)),rec(metric)],real_pointsets_read=0,audit_runs=0,model_calls=0)
 emit('result_v1.json',result);print(json.dumps(dict(status=result['status'],checks=len(CHECKS))))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if A.is_dir():emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',checks=CHECKS,error=repr(e)))
  raise
