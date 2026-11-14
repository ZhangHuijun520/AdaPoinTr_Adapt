"""Adapt the independent stdlib auditor; never imports scorer or computes geometry."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[2]
P=R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_scoring_implementation_v1/audit_H2_three_arm_scores_v1.py'
q=json.loads((S/'local_scoring_execution_request_v1.json').read_bytes())
t=P.read_text(encoding='utf-8')
t=t.replace('Independent read-only H2 three-arm freeze audit','Independent read-only F0/T0/M0 freeze audit')
t=t.replace('3531fa8ca3282a7896be7df2b501be0ec1687f0448ebe7a613d2414e32d4f2b3','eaa35866db0c8dc231ee0b6f2cfd8a0d72436d088d5066bbf694acc7313ec175')
t=t.replace('post_scoring_freeze_audit_20261107_v1','post_scoring_freeze_audit_20261111_v1')
t=t.replace("ARMS=['M0','H2_AUX','H2_COUPLE'];PAIRS=[('H2_AUX','H2_COUPLE'),('M0','H2_COUPLE'),('M0','H2_AUX')]","ARMS=['T0','M0','F0'];PAIRS=[('M0','F0'),('T0','F0'),('T0','M0')]")
t=t.replace('s.st_size,s.st_mtime_ns)','s.st_size,s.st_mtime_ns,s.st_ctime_ns)')
t=t.replace("need(p.stat().st_size<=67108864,'per file cap: '+str(p));h=hashlib.sha256();parts=[]","need(p.stat().st_size<=67108864 or (str(p) in LARGE_FILES and p.stat().st_size==LARGE_FILES[str(p)]['bytes']),'per file cap or exact archive exception: '+str(p));h=hashlib.sha256();parts=[]")
t=t.replace('READ<=1073741824','READ<=2147483648')
t=t.replace("row,raw=CACHE[str(p)]\n if binding:","row,raw=CACHE[str(p)]\n if str(p) in LARGE_FILES:need(all(row[k]==LARGE_FILES[str(p)][k] for k in ['bytes','sha256']),'exact large archive binding')\n if binding:")
t=t.replace('START=time.monotonic();READ=0;','LARGE_FILES='+repr({v['archive']['path']:v['archive'] for v in q['archive_inputs'].values()})+'\nSTART=time.monotonic();READ=0;')
t=t.replace("p3['status']=='LOCAL_H2_M0_THREE_ARM_SCORING_P3_PASS' and p3['CPU_tests']==35","p3['status']=='LOCAL_F0_T0_M0_SCORING_P3_PASS' and p3['CPU_tests']==42")
t=t.replace("tests['status']=='H2_THREE_ARM_SCORING_CPU_CONTRACT_PASS'","tests['status']=='F0_T0_M0_SCORING_CPU_CONTRACT_PASS'")
t=t.replace('final_P3_and35_CPU_contracts','final_P3_and42_CPU_contracts')
t=t.replace("auth['schema']=='bcsp-p2-H2-M0-score-authorization-v1'","auth['schema']=='bcsp-f0-T0-M0-score-authorization-v1'")
t=t.replace('LOCAL_H2_M0_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE','LOCAL_F0_T0_M0_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE')
begin=t.index('  # Bound Native moment records')
end=t.index('  for r in rows:',begin)
prefix="""  # Read only already-frozen Native geometry JSON, never prediction/GT arrays.
  root=S.parents[2];predroot=S.parent/'Native_prediction_implementation_v1/resource_rebind_v2/post_prediction_freeze_audit_v1'
  predhash=js(predroot/'hashes_after_result_v1.json');nativepath=predroot/'downloads/output/geometry_summary.jsonl'
  binding=next(r for r in predhash['files'] if r['name']=='geometry_summary.jsonl')
  need(checked(nativepath)[0]['sha256']==binding['sha256'],'F0 Native geometry provenance')
  native={(r['run'],r['case_id']):r for r in map(json.loads,checked(nativepath)[1].decode().splitlines())};need(len(native)==210,'210 F0 summaries')
"""
t=t[:begin]+prefix+t[end:]
begin=t.index("   if r['arm'].startswith('H2_'):")
end=t.index("  good('all_selected_metrics_pose",begin)
replacement="""   if r['arm']=='F0':
    g=native[r['fold']+'_F0',r['case_id']];stage=r['stage_geometry'];norm=case_for[r['fold'],r['case_id']]['normalization'];scale=norm['scale'];center=norm['center']
    need(stage['coarse']['tensor_saved'] is True and 'H2' not in stage,'Native F0 all-Q only')
    for part in ['coarse','dense']:
     src=g[part];dst=stage['coarse'] if part=='coarse' else stage['dense']
     mean=[v*scale+c for v,c in zip(src['centroid'],center)]
     equal(dst['centroid_mm'] if part=='coarse' else dst['prediction_centroid_mm'],mean,'Native F0 centroid')
     equal(dst['radius_gyration_mm'] if part=='coarse' else dst['prediction_radius_gyration_mm'],src['radius_gyration']*scale,'Native F0 radius')
     equal(dst['bbox_mm'] if part=='coarse' else dst['prediction_bbox_mm'],[[v*scale+c for v,c in zip(src[key],center)] for key in ['bbox_min','bbox_max']],'Native F0 bbox')
     equal(dst['covariance_eigenvalues_mm2'],[v*scale**2 for v in src['covariance_eigenvalues']],'Native F0 covariance')
    equal(stage['mean_dense_minus_coarse_mm'],[v*scale for v in g['mean_dense_minus_coarse']],'Native F0 offset mean')
    equal(stage['offset_mean_squared_radius_mm2'],g['offset_mean_squared_radius']*scale**2,'Native F0 offset energy')
"""
t=t[:begin]+replacement+t[end:]
t=t.replace('all_selected_metrics_pose_stage_algebra_risk_thresholds_GT_and_H2_summaries','all1050_selected_metrics_pose_stage_risk_GT_and_F0_Native_summaries')
old="""good('primary_and_secondary_descriptive_comparison_identity',comparison['status']=='H2_THREE_ARM_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS' and comparison['primary_comparison']=='H2_COUPLE_minus_H2_AUX' and comparison['secondary_comparisons']==['H2_COUPLE_minus_M0','H2_AUX_minus_M0'] and"""
new="""good('three_fixed_descriptive_comparison_identities',comparison['status']=='F0_T0_M0_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS' and comparison['fixed_comparisons']==['F0_minus_M0','F0_minus_T0','M0_minus_T0'] and comparison['primary_metric']=='A1 area-weighted E_P95 mm' and"""
assert old in t;t=t.replace(old,new)
t=t.replace("for arm in ['M0','Nop_D','GT_8192']:","for arm in ['T0','M0','Nop_D','GT_8192']:")
t=t.replace('all630_M0_and_shared_control_rows_equal_frozen_P1_scores','all840_T0_M0_and_shared_control_rows_equal_frozen_P1_scores')
anchor="  good('stable_output_and_all_read_content_fingerprints_atime_excluded'"
pos=t.index(anchor)
extra="""  need(all(complete[k]==0 for k in ['server_operations','model_imports','forward_calls','bootstrap']),'no extra model/statistical execution')
  good('wall_and_final_output_within_frozen_limits',complete['seconds']<=q['limits']['wall_seconds'] and result['elapsed_seconds']<=18030 and sum(p.stat().st_size for p in O.iterdir())<=q['limits']['output_bytes'])
  need([sum(r['stage_geometry']['coarse']['tensor_saved'] for r in rows if r['arm']==arm) for arm in ARMS]==[12,12,210],'coarse availability')
  good('actual_coarse_availability_12_12_210_not_misrepresented')
  need(inv['argv']==[q['environment']['python']['path'],*q['environment']['flags'],q['implementation']['scorer']['path'],'--request',str(S/'local_scoring_execution_request_v1.json'),'--request-sha256',SHA,'--authorization',str(A/'score_authorization_v1.json'),'--authorization-sha256',checked(A/'score_authorization_v1.json')[0]['sha256']],'actual argv')
  good('actual_process_argv_matches_frozen_request_and_authorization')
"""
t=t[:pos]+extra+t[pos:]
t=t.replace('FORMAL_H2_THREE_ARM_POST_SCORING_FREEZE_AUDIT_PASS','FORMAL_F0_T0_M0_POST_SCORING_FREEZE_AUDIT_PASS')
t=t.replace("'Package identity from frozen binary/version records, no environment import/rerun'","'Package identity from frozen Python binary/version records; dependency binary tree not rescanned','RSS guard samples were not persisted as a resource time series; peak RSS cannot be independently reconstructed','Only common12 baseline cases/arm have actual coarse tensors; F0 has210; do not imply complete paired coarse tensors'")
ast.parse(t)
target=S/'audit_F0_T0_M0_scores_v1.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(t)
review=dict(status='INDEPENDENT_READONLY_AUDIT_STATIC_PASS',parent=dict(path=str(P),sha256=hashlib.sha256(P.read_bytes()).hexdigest()),auditor_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),request_sha256='eaa35866db0c8dc231ee0b6f2cfd8a0d72436d088d5066bbf694acc7313ec175',maximum_read_bytes=2147483648,maximum_seconds=120,default_per_file_cap_bytes=67108864,exact_large_archive_exceptions={p:r for p,r in {v['archive']['path']:v['archive'] for v in q['archive_inputs'].values()}.items()},output_files=12,expected_case_rows=1050,expected_source_rows=210,metric_or_scorer_import=False,GT_or_prediction_array_decode=False,scoring_rerun=False)
with (S/'score_audit_scope_v1.json').open('x',encoding='utf-8') as f:json.dump(review,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=review['status'],auditor=str(target),frozen_request_sha256=review['request_sha256'])))
