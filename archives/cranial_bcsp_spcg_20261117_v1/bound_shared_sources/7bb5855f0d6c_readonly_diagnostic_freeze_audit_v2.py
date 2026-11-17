# -*- coding: utf-8 -*-
"""Read-only audit of five existing-array diagnostics. No rendering/model/updates."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
from pathlib import Path
import ast,json,hashlib,io,tarfile,re,importlib.util,time
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
R=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent;O=R/'outputs/spcg_coarse_dense_visualization_20261117_v1';S=R/'outputs/spcg_score_implementation_20261117_v1';F=R/'outputs/spcg_score_freeze_20261117_v1';CHECKS={};START=time.monotonic()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):
 p=Path(p);return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def exact(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in [p,*p.parents]),str(p)
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'bound bytes/hash '+str(p);return p
def load(p):return json.loads(Path(p).read_bytes())
def emit(name,obj):
 with (A/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
def check(name,ok):assert ok,name;CHECKS[name]=True
def inventory(root):
 result={};fields=('st_ino','st_dev','st_mode','st_size','st_mtime_ns','st_ctime_ns')
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink(),str(p)
  if p.is_dir():continue
  assert p.is_file() and p.stat().st_size<16777216 and len(result)<100
  a=p.stat();h=sha(p);b=p.stat();assert all(getattr(a,k)==getattr(b,k) for k in fields)
  result[p.relative_to(root).as_posix()]=dict(bytes=b.st_size,sha256=h,fingerprint=[getattr(b,k) for k in fields])
 return result
def equal(a,b):
 if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 if isinstance(a,(float,int)) and not isinstance(a,bool):return isinstance(b,(float,int)) and np.isfinite(a) and np.isfinite(b) and bool(np.isclose(a,b,rtol=1e-11,atol=1e-10))
 return a==b
def audit_weighted_p95(dist,weights):
 dist=np.asarray(dist,np.float64);weights=np.asarray(weights,np.float64)
 assert dist.ndim==weights.ndim==1 and len(dist)==len(weights)>0,'quantile shape/nonempty'
 assert np.all(weights>0) and np.isfinite(weights).all() and not np.isnan(dist).any(),'quantile values'
 order=np.argsort(dist,kind='mergesort');cumulative=np.cumsum(weights[order],dtype=np.float64)
 index=min(np.searchsorted(cumulative,.95*cumulative[-1],side='left'),len(dist)-1)
 return float(dist[order[index]])

def independent_stats(x,gt,tree,ref,metric,roi):
 center=x.mean(0);gc=gt.mean(0);rg=np.sqrt(np.mean(np.sum((x-center)**2,axis=1)));grg=np.sqrt(np.mean(np.sum((gt-gc)**2,axis=1)))
 reverse=tree.query(x,workers=2)[0];support_distance=cKDTree(x).query(ref['a_centers'],workers=2)[0];support={}
 for name,mask in [('E',~ref['a_is_j']),('J',ref['a_is_j'])]:
  d=support_distance[mask];w=ref['a_weights'][mask];p95=audit_weighted_p95(d,w)
  support[name]=dict(status='OK',mean_mm=float(np.average(d,weights=w)),p95_mm=float(p95),max_mm=float(d.max()),coverage={str(t):float(np.average(d<=t,weights=w)) for t in [.5,1.,2.]})
 return dict(points=len(x),centroid_mm=center.tolist(),centroid_error_vector_mm=(center-gc).tolist(),centroid_offset_mm=float(np.linalg.norm(center-gc)),radius_gyration_ratio=float(rg/grg),bbox_mm=[x.min(0).tolist(),x.max(0).tolist()],to_A2_P95_mm=float(np.quantile(reverse,.95)),to_A2_max_mm=float(reverse.max()),to_A2_gt20_fraction=float(np.mean(reverse>20)),support=support,points_outside_GT_ROI=int(np.sum(~np.all((x>=roi[0])&(x<=roi[1]),axis=1))))
def main():
 before=inventory(O);scientific={k:v for k,v in before.items() if not k.startswith('mpl_cache/')};cache={k:v for k,v in before.items() if k.startswith('mpl_cache/')}
 final=load(O/'final_delivery_manifest_v1.json');artifact=load(O/'artifact_manifest_v1.json');scope=load(O/'frozen_case_scope_v1.json');diag=load(O/'fixed_case_geometry_metrics_v1.json');completion=load(O/'completion_v1.json');quality=load(O/'delivery_quality_check_v1.json');bindings=load(O/'source_bindings_v1.json')
 for m in [final,artifact]:
  for r in m['files']:exact(r)
 expected={Path(r['path']).name for r in final['files']}|{'final_delivery_manifest_v1.json'}
 check('exact30_scientific_files_and_one_render_cache',set(scientific)==expected and len(scientific)==30 and set(cache)=={'mpl_cache/fontlist-v390.json'})
 check('both_post_render_manifests_match_all_bound_hashes',len(final['files'])==29 and len(artifact['files'])==26)
 check('completion_scope_5cases15files30stages20figures',completion['status']=='FIVE_FIXED_CASE_COARSE_DENSE_GEOMETRY_VISUALIZATION_COMPLETE' and all(completion[k]==v for k,v in dict(cases=5,models_per_case=3,existing_prediction_files=15,stages=30,figures=20,forward_calls=0,training_updates=0,parameter_scans=0).items()) and completion['GT_registration'] is False and all(completion['checks'].values()))
 check('no_render_or_model_in_audit','matplotlib' not in __import__('sys').modules and 'torch' not in __import__('sys').modules)
 prior=load(F/'audit_verification_v1.json');q=load(S/'SPCG_local_scoring_execution_request_v1.json')
 check('formal_score_freeze_and_request_identity',prior['status']=='FORMAL_SPCG_THREE_ARM_TWOFOLD_POST_SCORE_FREEZE_AUDIT_PASS' and sha(S/'SPCG_local_scoring_execution_request_v1.json')==scope['source_request_sha256']==diag['source_request_sha256']==prior['request_sha256'])
 for root,key in [(S/'unified_scores_v1','output'),(S/'authorized_execution_v1','execution')]:
  for n,r in prior['inventory'][key].items():exact(dict(path=str(root/n),bytes=r['bytes'],sha256=r['sha256']))
 for r in bindings['files']:exact(r)
 check('prior_score_freeze_and36_source_bindings_unchanged',len(bindings['files'])==36)
 rows=[json.loads(l) for l in (S/'unified_scores_v1/case_metrics.jsonl').read_text(encoding='utf-8').splitlines()];look={(r['fold'],r['case_id'],r['arm']):r for r in rows};ids=sorted({(r['fold'],r['case_id']) for r in rows});new=[]
 for f,cid in ids:
  a,b=look[f,cid,'G1'],look[f,cid,'G2']
  if b['risk_labels']['severe_geometry'] and not a['risk_labels']['severe_geometry']:new.append(dict(fold=f,case_id=cid,delta_E_G2_minus_G1_mm=b['metrics']['E_P95_mm']-a['metrics']['E_P95_mm'],selection='posthoc_new_severe'))
 selected=sorted(new,key=lambda x:(-x['delta_E_G2_minus_G1_mm'],x['case_id']))[:3]
 for f in ['C','D']:
  options=[dict(fold=f,case_id=cid,delta_E_G2_minus_G1_mm=look[f,cid,'G2']['metrics']['E_P95_mm']-look[f,cid,'G1']['metrics']['E_P95_mm'],selection='posthoc_improved_control') for ff,cid in ids if ff==f and not look[f,cid,'G2']['risk_labels']['severe_geometry']]
  selected.append(min(options,key=lambda x:(x['delta_E_G2_minus_G1_mm'],x['case_id'])))
 check('exact_protocol_case_selection_no_substitution',selected==scope['selected'] and len(selected)==len({x['case_id'] for x in selected})==len(diag['cases'])==5)
 check('read_only_scope_no_alignment_training_scan',all(scope[k] is True for k in ['no_GT_alignment','no_point_deletion','no_forward','no_training','no_parameter_scan','no_formal_gate']) and scope['Memory']==diag['Memory']=='NOT_COLLECTED')
 idx=load(exact(q['score_case_index']));cases={r['case_id']:r for r in idx['cases']};pred={(r['fold'],r['arm'],r['case_id']):r for r in idx['prediction_records']};ar=q['archive_inputs']['SPCG']['archive'];path=exact(ar)
 spec=importlib.util.spec_from_file_location('frozen_metric_audit_only',exact(q['implementation']['metrics']));metric=importlib.util.module_from_spec(spec);spec.loader.exec_module(metric)
 def deny(*args,**kwargs):raise AssertionError('NO_MODEL_OR_FORMAL_SCORE_IN_AUDIT')
 metric.score_cloud=deny
 allfigures=[];allpred=[];stage_count=0;claims=[]
 with tarfile.open(path,'r:gz') as tar:
  for result,sel in zip(diag['cases'],selected):
   assert all(result[k]==v for k,v in sel.items());cid=result['case_id'];f=result['fold'];case=cases[cid];assert result['normalization']==case['normalization'] and result['all_outliers_retained'] is True
   with np.load(exact(case['point_file']),allow_pickle=False) as z:
    assert set(z.files)=={'partial','implant'};target=z['implant'];assert hashlib.sha256(target.tobytes()).hexdigest()==case['target_array_sha256'];D=metric.world_points(z['partial'],case['normalization']);G=metric.world_points(target,case['normalization'])
   with np.load(exact(case['reference']),allow_pickle=False) as z:ref={k:z[k] for k in z.files}
   a2,_,_=metric.a2_reference(ref);tree=cKDTree(a2);roi=np.stack([G.min(0)-10,G.max(0)+10]);assert np.array_equal(roi,result['GT_ROI_display_bounds_mm']);clouds=[]
   assert result['prediction_bindings']==[pred[f,arm,cid] for arm in ['G0','G1','G2']]
   allpred.extend(result['prediction_bindings'])
   for arm in ['G0','G1','G2']:
    b=pred[f,arm,cid];member=tar.getmember(b['member']);assert member.isfile() and member.size==b['bytes'];blob=tar.extractfile(member).read();assert hashlib.sha256(blob).hexdigest()==b['sha256']
    with np.load(io.BytesIO(blob),allow_pickle=False) as z:
     assert z.files==['prediction','coarse'];arrays={k:z[k].copy() for k in z.files}
    assert arrays['prediction'].shape==(8192,3) and arrays['coarse'].shape==(256,3) and all(x.dtype==np.float32 and np.isfinite(x).all() for x in arrays.values())
    co=metric.world_points(arrays['coarse'],case['normalization']);de=metric.world_points(arrays['prediction'],case['normalization']);clouds.extend([co,de]);m=result['metrics'][arm]
    for name,x in [('coarse',co),('dense',de)]:assert equal(independent_stats(x,G,tree,ref,metric,roi),m[name]),cid+' '+arm+' '+name;stage_count+=1
    assert m['dense_frozen_metrics']==look[f,cid,arm]['metrics'] and m['frozen_risk_labels']==look[f,cid,arm]['risk_labels']
    dense=m['dense'];assert all(np.isclose(dense['support'][name]['p95_mm'],look[f,cid,arm]['metrics'][name+'_P95_mm'],rtol=1e-11,atol=1e-10) for name in ['E','J'])
    assert np.isclose(dense['centroid_offset_mm'],look[f,cid,arm]['metrics']['centroid_offset_mm'],rtol=1e-11,atol=1e-10)
    offset=de.reshape(256,32,3)-co[:,None,:];change=m['dense_minus_coarse']
    expected_change=dict(centroid_shift_vector_mm=(de.mean(0)-co.mean(0)).tolist(),centroid_shift_mm=float(np.linalg.norm(de.mean(0)-co.mean(0))),centroid_error_change_mm=m['dense']['centroid_offset_mm']-m['coarse']['centroid_offset_mm'],radius_ratio_change=m['dense']['radius_gyration_ratio']-m['coarse']['radius_gyration_ratio'],E_P95_change_mm=m['dense']['support']['E']['p95_mm']-m['coarse']['support']['E']['p95_mm'],J_P95_change_mm=m['dense']['support']['J']['p95_mm']-m['coarse']['support']['J']['p95_mm'],offspring_to_own_coarse_RMS_mm=float(np.sqrt(np.mean(np.sum(offset**2,axis=2)))),mapping_note=change['mapping_note'])
    assert equal(change,expected_change)
   xyz=np.concatenate([D,G]+clouds);lo=xyz.min(0);hi=xyz.max(0);center=(hi+lo)/2;half=max(hi-lo)*.54;box=np.stack([center-half,center+half]);assert np.array_equal(box,result['global_world_bounds_mm']) and np.all(xyz>=box[0]) and np.all(xyz<=box[1])
   figs=[cid+'_'+p+'_global.png' for p in ['XY','XZ','YZ']]+[cid+'_XY_ROI.png'];assert result['figures']==figs;allfigures.extend(figs)
   for name in figs:
    with Image.open(O/name) as im:assert im.size==(1860,1860) and im.format=='PNG';im.verify()
   claims.append(dict(case_id=cid,fold=f,selection=sel['selection'],G2_coarse_centroid_mm=result['metrics']['G2']['coarse']['centroid_offset_mm'],G2_dense_centroid_mm=result['metrics']['G2']['dense']['centroid_offset_mm'],G2_dense_reverse_gt20_fraction=result['metrics']['G2']['dense']['to_A2_gt20_fraction']))
 check('15_native_members_hash_schema_shapes',len(allpred)==len({r['member'] for r in allpred})==15 and allpred==bindings['archive_predictions'])
 check('all30_stage_metrics_independently_recomputed',stage_count==30)
 check('all15_dense_values_match_frozen_scores',True)
 check('all15_parent_child_offsets_and_stage_differences',True)
 check('five_global_ranges_include_all_points_and_fixed_GT_ROI',True)
 check('20_PNG_files_names_dimensions_integrity',len(allfigures)==len(set(allfigures))==20 and set(n for n in scientific if n.endswith('.png'))==set(allfigures)|{'five_case_overview_v1.png'})
 with Image.open(O/'five_case_overview_v1.png') as im:assert im.size==(1000,2675);im.verify()
 doc=(O/'index.html').read_text(encoding='utf-8');check('HTML_exact20_local_images_no_external_assets',re.findall(r'<img[^>]*src="([^"]+)"',doc)==allfigures and 'http://' not in doc and 'https://' not in doc and all(x['case_id'] in doc for x in selected))
 exact(quality['report']);report=Path(quality['report']['path']).read_text(encoding='utf-8')
 assert quality['status']=='RENDER_AND_DELIVERY_CHECK_PASS_NOT_FORMAL_FREEZE_AUDIT' and quality['main_figures']==20
 for result in diag['cases']:
  for arm in ['G0','G1','G2']:
   m=result['metrics'][arm];co,de=m['coarse'],m['dense'];line=f"|{result['case_id']}|{arm}|{co['centroid_offset_mm']:.3f}|{de['centroid_offset_mm']:.3f}|{co['support']['E']['p95_mm']:.3f}|{de['support']['E']['p95_mm']:.3f}|{de['support']['J']['p95_mm']:.3f}|{100*de['support']['J']['coverage']['2.0']:.2f}|{100*de['to_A2_gt20_fraction']:.2f}|"
   assert line in report
 check('report15_model_rows_exact_and5_cases',True)
 check('coarse_failure_claim_supported_in3_selected_regressions',all(r['metrics']['G2']['coarse']['support']['E']['p95_mm']>20 and r['metrics']['G2']['coarse']['centroid_offset_mm']>20 for r in diag['cases'][:3]))
 d=diag['cases'][-1]['metrics']['G2']['dense'];check('improved_control_not_misrepresented_as_normal',d['to_A2_gt20_fraction']>.32 and d['centroid_offset_mm']>26 and '32.42%' in report and '不是正常病例' in report)
 check('causal_and_point_budget_limitations_disclosed',all(x in report for x in ['点数不同','Memory','不能','同权重反事实','跨设备','事后解释']))
 current_code=[rec(F/'visualize_fixed_coarse_dense_cases_v1.py'),rec(F/'write_fixed_visualization_report_v1.py')]
 after=inventory(O);check('all30_scientific_and_render_cache_hash_attributes_stable',before==after)
 result=dict(status='FORMAL_SPCG_FIVE_CASE_POST_DIAGNOSTIC_FREEZE_AUDIT_V2_PASS',check_count=len(CHECKS),checks=CHECKS,inventory=after,scientific_files=len(scientific),render_cache_files=len(cache),counts=dict(cases=5,existing_predictions=15,coarse_dense_stages=30,main_figures=20,overview_figures=1),source_request_sha256=scope['source_request_sha256'],current_code_bindings=current_code,case_claim_checks=claims,seconds=time.monotonic()-START,operations=dict(new_forward=0,training_updates=0,parameter_scans=0,new_rendering=0,formal_scoring_runs=0,existing_stage_geometry_recalculations=30,server_operations=0),limitations=['Diagnostic point distances were recomputed only to verify the existing30 stages, not to add cases/metrics or rerun formal scoring.','Current renderer/report source hashes frozen by this audit; no independently pre-run source-hash receipt was recorded for the visualization invocation.','Pixel content is anchored by post-render manifests; this audit verifies image integrity/labels in source/HTML/bounds and recorded visual QA, not OCR or complete pixel regeneration.','Posthoc5cases do not estimate population failure rate or unique causal root.','Coarse256 vsdense8192 point-budget confounding remains; Memory not collected; D_G0 cross-device reference remains.'])
 emit('audit_verification_v1.json',result)
 report_text='''# SPCG 五例 coarse／dense 诊断：正式只读冻结审计

日期：2026-11-17。版本：v2，仅修正审计加权P95的排序累积阈值合同；旧v1失败记录保留。状态：**PASS**，共 CHECKS 项检查通过。

审计范围为5例固定病例、15份既有预测、30个coarse/dense阶段、20张主图和1张总览。30个科学交付文件及1个绘图缓存文件已逐项记录SHA256、大小和内容相关属性，审计前后完全稳定；未重绘、运行模型或修改原产物。

重新从完整冻结评分独立复核了选例规则：3例G2相对G1新增严重，按ΔE降序；另在每折取G2不严重且ΔE最小的一例。未更换病例。15个tar成员哈希、数组键、FP32形状及反归一化一致；5份参考/点集及原评分冻结证据仍一致。

仅为核对已有数值，独立重算30个既有阶段的质心、范围、半径、E/J面积加权支持、反向距离/离群，以及15组coarse→dense位移和每中心32子点RMS。全部与保存记录一致；15个dense的对应E/J/质心与正式冻结评分相符。此过程不是新的正式评分任务，也未追加统计指标或病例。

检查了20张PNG完整性和1860×1860尺寸、总览1000×2675、HTML的20个本地图片链接，以及报告15个模型行的数值。全局坐标范围包含全部输入/GT/预测，ROI是GT框外扩10mm的显示范围，未删除模型点。颜色40mm上限仅用于显示，指标未截断。

结论保留：3个选中退化病例在已观察coarse节点就有显著偏位/漏覆盖；dense未纠正。改善对照不等于正常，D折046仍有32.42%反向>20mm点。该观察不足以定位唯一内部根因，也不能外推5个事后病例到全队列。不能直接将256到8192点的覆盖改善当成因果增益。

边界：当前绘图/报告脚本哈希由本次审计冻结，先前没有独立的运行前源码哈希回执；现有图像已有运行后清单绑定。本次不通过重绘比像素来补造该证据，而是记录这一溯源局限，并核验图文件完整性、数据范围、源定义、HTML及已有可视QA。Memory未采集、D折G0跨设备限制不变。

完整清单、27类上下文检查的实际逐项结果、代码与图表哈希见 `audit_verification_v1.json`；该JSON中的check_count为本次实际计数。正式冻结已完成，未自动追加训练、调参或新的机制诊断。
'''.replace('CHECKS',str(len(CHECKS))).replace('27类上下文检查的实际逐项结果','全部逐项检查结果')
 with (A/'正式诊断后冻结审计报告_zh_v1.md').open('x',encoding='utf-8') as f:f.write(report_text)
 emit('delivery_manifest_v1.json',dict(status=result['status'],files=[rec(p) for p in sorted(A.iterdir()) if p.is_file()]))
 print(json.dumps(dict(status=result['status'],checks=len(CHECKS),scientific_files=len(scientific),cases=5,existing_predictions=15,stages=30,main_figures=20,new_forward=0)))
if __name__=='__main__':
 try:main()
 except BaseException as exc:emit('audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP_NO_RETRY',checks=CHECKS,error=repr(exc)));raise
