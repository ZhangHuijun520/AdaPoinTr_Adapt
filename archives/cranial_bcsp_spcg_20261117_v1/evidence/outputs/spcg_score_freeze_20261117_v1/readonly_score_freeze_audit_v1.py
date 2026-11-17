"""Formal read-only SPCG post-score freeze audit. Never invoke distance scoring."""
from pathlib import Path
import json,hashlib,csv,io,importlib.util,time,math
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;S=R/'outputs/spcg_score_implementation_20261117_v1';O=S/'unified_scores_v1';A=S/'authorized_execution_v1'
QS='7b6b3e5f6ade721540397e2c7977a85e2c73298f7e5cedb489b79f257eae27f8'
checks={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bound(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in [p,*p.parents]),str(p)
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'size/hash '+str(p);return p
def load(p):return json.loads(Path(p).read_bytes())
def emit(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def check(k,v):
 assert v,k;checks[k]=True
def inventory(root):
 result={};fields=('st_ino','st_dev','st_mode','st_size','st_mtime_ns','st_ctime_ns')
 for p in sorted(root.rglob('*')):
  assert p.is_file() and not p.is_symlink() and p.stat().st_size<=16777216 and len(result)<40,str(p)
  a=p.stat();h=sha(p);b=p.stat();assert all(getattr(a,k)==getattr(b,k) for k in fields)
  result[p.relative_to(root).as_posix()]=dict(bytes=b.st_size,sha256=h,fingerprint=[getattr(b,k) for k in fields])
 return result
def main():
 q=load(S/'SPCG_local_scoring_execution_request_v1.json');check('exact_authorized_request_sha256',sha(S/'SPCG_local_scoring_execution_request_v1.json')==QS)
 before=dict(output=inventory(O),execution=inventory(A))
 check('exact16_output_files',set(before['output'])==set(q['expected_result_files']) and len(before['output'])==16)
 check('exact7_execution_files',set(before['execution'])=={'process_attempt_v1.json','process_exit_v1.json','process_identity_v1.json','readiness_v1.json','score_authorization_v1.json','stdout.log','stderr.log'})
 e=load(A/'process_exit_v1.json');c=load(O/'completion.json');attempt=load(A/'process_attempt_v1.json');auth=load(A/'score_authorization_v1.json');claim=load(O/'single_attempt_claim.json');readiness=load(A/'readiness_v1.json')
 check('exit0_no_timeout_or_failure',e['status']=='PROCESS_EXITED' and e['returncode']==0 and e['timed_out'] is False and not (O/'failure.json').exists() and before['execution']['stderr.log']['bytes']==0)
 check('all_receipts_full_request_hash',all(v['request_sha256']==QS for v in [e,c,attempt,auth,claim,readiness]))
 check('single_authorized_attempt',auth['explicit_user_authorization'] is True and attempt['automatic_retry'] is False and claim['no_retry'] is True and attempt['authorization_sha256']==sha(A/'score_authorization_v1.json'))
 check('completion1050rows210sources',c['status']=='LOCAL_SPCG_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE' and (c['model_predictions'],c['controls'],c['frozen_baseline_rows_verified'],c['score_rows'],c['source_rows'])==(630,420,420,1050,210))
 check('budget_and_no_model_server_gate',0<c['seconds']<=e['seconds']<=q['limits']['wall_seconds'] and all(c[k]==0 for k in ['server_operations','model_imports','forward_calls']) and c['formal_gate'] is False)
 for r in list(q['implementation'].values())+list(q['evidence'].values())+[q[k] for k in ['P3','reference_manifest','prediction_index','score_case_index','frozen_baseline_scores']]+[q['environment']['python']]:bound(r)
 check('all_frozen_implementation_evidence_hashes',True)
 p3=load(bound(q['P3']));check('P3_pass_entry_matches',p3['status']=='LOCAL_SPCG_SCORING_P3_PASS' and all(p3['checks'].values()) and p3['scorer']==q['implementation']['scorer'])
 for spec in q['archive_inputs'].values():
  for r in [spec['archive'],spec['prediction_index'],spec['prediction_protocol']]+spec['sidecars']:bound(r)
 check('archive_and_three_sidecars_hashes',c['archive_sha256']=={k:v['archive']['sha256'] for k,v in q['archive_inputs'].items()})
 caseindex=load(bound(q['score_case_index']));cases=caseindex['cases']
 for case in cases:bound(case['reference']);bound(case['point_file'])
 check('210_reference210_point_hashes',len(cases)==210)
 env=load(O/'execution_environment.json');check('CPU_environment_matches',env['packages']==q['environment']['packages'] and env['executable']==q['environment']['python']['path'] and env['CUDA_VISIBLE_DEVICES']=='' and env['threads']==2 and env['request_sha256']==QS)
 sp=importlib.util.spec_from_file_location('spcg_readonly_summary_audit',bound(q['implementation']['scorer']));s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s);np=s.np
 def forbidden(*args,**kwargs):raise AssertionError('NO_REAL_SCORE_OR_FORWARD_IN_AUDIT')
 s.metric.score_cloud=forbidden
 s.validate_index(load(bound(q['prediction_index'])),load(bound(q['reference_manifest'])),caseindex)
 rows=[json.loads(x) for x in (O/'case_metrics.jsonl').read_text(encoding='utf-8').splitlines()];sources=load(O/'source_metrics.json');pair=load(O/'paired_comparison.json');risks=load(O/'risk_transitions.json');defects=load(O/'defect_comparison.json');ranks=load(O/'regression_rankings.json')
 keys={(r['fold'],r['case_id'],r['arm']) for r in rows}
 check('1050_unique_complete_case_arm_keys',len(rows)==len(keys)==1050 and keys=={(v['fold'],v['case_id'],a) for v in cases for a in s.ARMS+s.CONTROLS})
 cb={(v['fold'],v['case_id']):v for v in cases}
 for r in rows:
  assert r['source_id']==cb[r['fold'],r['case_id']]['source_id'] and r['status']=='OK'
  assert r['risk_labels']==s.risk_labels(r['metrics'],r['position_shape'])
  assert all(r['metrics'][k]==float(v) for k,v in r['risk_labels'].items())
  assert all(r['metrics'][k]==v for k,v in s.select_metrics(r['full_metrics']).items())
  if r['arm'] in s.ARMS:assert r['stage_geometry']['frame']=='native_world_mm_no_alignment' and r['stage_geometry']['coarse']['points']==256 and r['stage_geometry']['dense_points']==8192 and r['stage_geometry']['coarse']['tensor_saved'] is True
  else:assert r['stage_geometry'] is None
  pose=r['position_shape'];delta=np.asarray(pose['prediction_centroid_mm'])-pose['GT8192_centroid_mm']
  assert np.allclose(delta,pose['centroid_offset_vector_mm'],rtol=0,atol=1e-10) and np.isclose(np.linalg.norm(delta),pose['centroid_offset_mm'],rtol=1e-10,atol=1e-10)
 check('case_source_status_metric_risk_and_geometry_consistency',True)
 check('210_source_aggregates_exact',len(sources)==210 and s.metric.json_safe(s.aggregate_source(rows))==sources)
 for sr in sources:
  part=[r for r in rows if (r['fold'],r['source_id'],r['arm'])==(sr['fold'],sr['source_id'],sr['arm'])];assert len(part)==5
  for k,v in sr['metrics'].items():
   vals=[r['metrics'][k] for r in part];expected=None if any(x is None for x in vals) else sum(vals)/5
   assert v is None if expected is None else math.isclose(v,expected,rel_tol=1e-12,abs_tol=1e-12)
 check('independent_equal_five_defect_means',True)
 old=[json.loads(x) for x in bound(q['frozen_baseline_scores']).read_text(encoding='utf-8').splitlines()];base={(r['fold'],r['case_id'],r['arm']):r for r in old if r['arm'] in s.CONTROLS};controls=[r for r in rows if r['arm'] in s.CONTROLS]
 check('420_shared_controls_exact_frozen_equality',len(base)==len(controls)==420 and all(base[r['fold'],r['case_id'],r['arm']]==r for r in controls))
 check('pairs_counts_device_limitations_exact',pair['fixed_comparisons']==[b+'_minus_'+a for a,b in s.PAIRS] and pair['comparison_qualification']==c['comparison_qualification']==q['comparison_qualification'] and pair['request_sha256']==QS and pair['case_count']==210 and pair['model_predictions']==630 and pair['controls']==420)
 check('preregistered_bootstrap_contract',c['bootstrap']==dict(replicates_per_fold=2000,folds=2,contract=q['statistics']) and q['statistics']==s.BOOTSTRAP)
 deltas=[]
 for fold in ['C','D']:
  rr=[r for r in rows if r['fold']==fold];ss=[r for r in sources if r['fold']==fold];ids=sorted({r['source_id'] for r in ss});assert len(rr)==525 and len(ss)==105 and len(ids)==21
  ix=np.load(O/('bootstrap_indices_'+fold+'.npy'),allow_pickle=False);record=load(O/('bootstrap_index_record_'+fold+'.json'))
  assert ix.shape==(2000,21) and ix.dtype==np.int64 and record['sources']==ids and record['seed']==q['statistics']['seeds'][fold] and record['sha256']==sha(O/('bootstrap_indices_'+fold+'.npy')) and record['bootstrap_contract']==q['statistics']
  expected=np.random.Generator(np.random.PCG64(q['statistics']['seeds'][fold])).integers(0,21,size=(2000,21),dtype=np.int64)
  check(fold+'_saved_draws_independent_PCG64_reproduction',np.array_equal(ix,expected))
  for p in s.PAIRS:
   key=p[1]+'_minus_'+p[0];v=s.paired_summary(ss,p,ix);v.update(baseline_arm=p[0],candidate_arm=p[1]);assert s.metric.json_safe(v)==pair['comparison'][fold][key]
   lookup={(r['source_id'],r['arm']):r for r in ss}
   for metric,value in v['metrics'].items():
    a=[lookup[sid,p[0]]['metrics'][metric] for sid in ids];b=[lookup[sid,p[1]]['metrics'][metric] for sid in ids]
    if any(x is None or not math.isfinite(x) for x in a+b):assert value['bootstrap']['CI95'] is None
    else:
     dif=np.asarray(b)-a;ci=np.quantile(dif[ix].mean(1),[.025,.975],method='linear')
     assert np.array_equal(ci,value['bootstrap']['CI95']) and math.isclose(dif.mean(),value['mean_delta_b_minus_a'],rel_tol=1e-12,abs_tol=1e-12)
   assert s.metric.json_safe(s.risk_transitions(rr,p))==risks[fold][key] and s.metric.json_safe(s.defect_summary(rr,p))==defects[fold][key]
   dd=s.case_differences(rr,p)
   for x in dd:x.update(comparison=key)
   deltas.extend(dd)
   ranking={k:sorted(vv['source_deltas'],key=lambda r:(r['delta'] is None,(-r['delta'] if vv['improvement_direction']=='negative' else r['delta']) if r['delta'] is not None else 0,r['source_id'])) for k,vv in v['metrics'].items() if vv['improvement_direction']!='descriptive_not_ordered'}
   assert s.metric.json_safe(dict(source_rankings=ranking,case_deltas=dd))==ranks[fold][key]
 check('six_comparisons_all_metrics_mean_CI_risk_defect_rankings',True)
 def csv_expected(values):
  flat=[{**{k:v for k,v in r.items() if k not in {'metrics','full_metrics','position_shape','risk_labels','stage_geometry'}},**s.metric.json_safe(r['metrics'])} for r in values];f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat);return f.getvalue().encode()
 check('three_CSV_exact_JSON_consistency',all((O/n).read_bytes()==csv_expected(v) for n,v in [('case_metrics.csv',rows),('source_metrics.csv',sources),('paired_case_deltas.csv',deltas)]))
 stdout=(A/'stdout.log').read_text(encoding='utf-8').splitlines();check('210_ordered_case_progress_no_duplicate_attempt',stdout==['SCORED '+x['fold']+' '+x['case_id'] for x in cases])
 check('output_byte_budget',sum(v['bytes'] for v in before['output'].values())<=q['limits']['output_bytes'])
 after=dict(output=inventory(O),execution=inventory(A));check('before_after_hashes_content_attributes_stable',before==after)
 audit=dict(status='FORMAL_SPCG_THREE_ARM_TWOFOLD_POST_SCORE_FREEZE_AUDIT_PASS',request_sha256=QS,checks=checks,check_count=len(checks),inventory=after,completion=c,operations=dict(real_point_metric_recalculations=0,summary_recalculations_only=True,model_calls=0,server_calls=0,backup_writes=0),limitations=['Distance scores are not rerun; audit verifies frozen full-metric values, aggregates and bootstrap from existing rows.','No continuous CPU RSS trace exists; runtime used in-process resource assertions, normal exit and empty stderr.','Bootstrap quantifies source sampling conditional on trained models; not training seed variability, development-selection bias or training-device confounding.'])
 emit(D/'audit_verification_v1.json',audit)
 summary={'status':audit['status'],'checks':len(checks),'folds':{}}
 for fold in ['C','D']:
  ss=[r for r in sources if r['fold']==fold];rr=[r for r in rows if r['fold']==fold];arms={}
  for arm in s.ARMS:
   ar=[r for r in ss if r['arm']==arm];cr=[r for r in rr if r['arm']==arm]
   arms[arm]=dict(metrics={k:float(np.mean([r['metrics'][k] for r in ar])) for k in ['E_P95_mm','J_P95_mm','CD_L1_mm','E_coverage_2.0mm','J_coverage_2.0mm','centroid_offset_mm','radius_gyration_ratio','reverse_A2_P95_mm','reverse_A2_outlier_20.0mm']},risks={k:sum(r['risk_labels'][k] for r in cr) for k in ['severe_geometry','placement_tail','compact_distribution']})
  comp={}
  for p in s.PAIRS:
   key=p[1]+'_minus_'+p[0];comp[key]=dict(metrics={k:pair['comparison'][fold][key]['metrics'][k] for k in ['E_P95_mm','J_P95_mm','CD_L1_mm','J_coverage_2.0mm']},severe={k:v for k,v in risks[fold][key]['labels']['severe_geometry'].items() if k not in ['cases','by_defect']})
  summary['folds'][fold]=dict(arms=arms,comparisons=comp)
 emit(D/'frozen_research_summary_v1.json',summary)
 print(json.dumps(dict(status=audit['status'],checks=len(checks),output_files=len(after['output']),case_rows=len(rows),source_rows=len(sources))))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  emit(D/'audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc)));raise
