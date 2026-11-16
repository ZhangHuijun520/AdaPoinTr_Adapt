from pathlib import Path
import json,hashlib,ast,csv,io,importlib.util,collections,time,os
W=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;S=W/'outputs/scq_rive_score_implementation_20261116_v1';O=S/'unified_scores_v1';A=S/'authorized_execution_v1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bound(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p);return p
qp=S/'local_scoring_execution_request_v1.json';qs=sha(qp);assert qs=='fb84bccd3ebcbaa5346ff8897d8e05cf9c10586c99411040bd01dae51856b9e7';q=json.loads(qp.read_bytes())
def inventory(root):
 result={}
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink() and p.is_file(),str(p)
  s=p.stat();assert s.st_size<=16777216 and len(result)<40
  h=sha(p);z=p.stat();keys=('st_ino','st_dev','st_mode','st_size','st_mtime_ns','st_ctime_ns');assert all(getattr(s,k)==getattr(z,k) for k in keys)
  result[p.relative_to(root).as_posix()]=dict(bytes=s.st_size,sha256=h,fingerprint=[getattr(s,k) for k in keys])
 return result
before=dict(output=inventory(O),execution=inventory(A));checks={}
def check(k,v):assert v,k;checks[k]=True
check('exact12_output_files',set(before['output'])==set(q['expected_result_files']))
check('exact7_execution_files',set(before['execution'])=={'attempt_started_v1.json','execution_result_v1.json','invocation_materialization_v1.json','score_authorization_v1.json','stderr_v1.txt','stdout_v1.txt','worker_started_v1.json'})
e=json.loads((A/'execution_result_v1.json').read_bytes());c=json.loads((O/'completion.json').read_bytes());check('exit0_no_timeout_failure',e['returncode']==0 and not e['timeout'] and e['error'] is None and e['failure'] is None and not (O/'failure.json').exists())
check('completion_identical_to_exit_record',e['completion']==c and c['status']=='LOCAL_SCQ_RIVE_TWO_ARM_TWOFOLD_CPU_SCORING_COMPLETE')
check('complete840rows168sources',(c['model_predictions'],c['controls'],c['frozen_baseline_rows_verified'],c['score_rows'],c['source_rows'])==(420,420,420,840,168))
check('no_server_model_forward_bootstrap_gate',all(c[k]==0 for k in ('server_operations','model_imports','forward_calls','bootstrap')) and c['formal_gate'] is False and e['retries']==0)
check('elapsed_budget',0<c['seconds']<=e['elapsed_seconds']<=q['limits']['wall_seconds'])
check('stdout_stderr_hashes',sha(A/'stdout_v1.txt')==e['stdout_sha256'] and sha(A/'stderr_v1.txt')==e['stderr_sha256'] and (A/'stderr_v1.txt').stat().st_size==0)
a=json.loads((A/'score_authorization_v1.json').read_bytes());claim=json.loads((O/'single_attempt_claim.json').read_bytes());attempt=json.loads((A/'attempt_started_v1.json').read_bytes());inv=json.loads((A/'invocation_materialization_v1.json').read_bytes())
check('authorization_claim_fullhash',a['request_sha256']==claim['request_sha256']==attempt['request_sha256']==inv['request_sha256']==e['request_sha256']==c['request_sha256']==qs and a['explicit_user_authorization'] is True and claim['no_retry'] is True and attempt['no_retry'] is True)
check('authorization_materialized_hash',inv['authorization_sha256']==sha(A/'score_authorization_v1.json'))
for r in q['implementation'].values():bound(r)
for r in q['evidence'].values():bound(r)
for k in ('P3','reference_manifest','prediction_index','score_case_index','frozen_baseline_scores'):bound(q[k])
bound(q['environment']['python']);check('all_code_evidence_input_bindings',True)
p3=json.loads(bound(q['P3']).read_bytes());check('implementation_P3_pass',p3['status']=='LOCAL_SCQ_RIVE_SCORING_P3_PASS' and all(p3['checks'].values()) and p3['scorer']==q['implementation']['scorer'])
for spec in q['archive_inputs'].values():
 for k in ('archive','prediction_index','prediction_protocol'):bound(spec[k])
 for r in spec['sidecars']:bound(r)
check('archive_fourfiles_still_frozen',c['archive_sha256']=={k:v['archive']['sha256'] for k,v in q['archive_inputs'].items()})
idx=json.loads(bound(q['score_case_index']).read_bytes());cases=idx['cases']
for case in cases:bound(case['reference']);bound(case['point_file'])
check('210references210point_hashes',len(cases)==210)
sp=importlib.util.spec_from_file_location('rive_score_readonly_aggregate',bound(q['implementation']['scorer']));s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
rows=[json.loads(x) for x in (O/'case_metrics.jsonl').read_text(encoding='utf-8').splitlines()];sources=json.loads((O/'source_metrics.json').read_bytes());pair=json.loads((O/'paired_comparison.json').read_bytes());risk=json.loads((O/'risk_transitions.json').read_bytes());defects=json.loads((O/'defect_comparison.json').read_bytes());ranks=json.loads((O/'regression_rankings.json').read_bytes())
check('840_unique_keys',len(rows)==len({(r['fold'],r['case_id'],r['arm']) for r in rows})==840)
check('all_fixed_cases_four_roles',set((r['fold'],r['case_id'],r['arm']) for r in rows)=={(x['fold'],x['case_id'],arm) for x in cases for arm in s.ARMS+s.CONTROLS})
caseby={(x['fold'],x['case_id']):x for x in cases}
for r in rows:
 x=caseby[r['fold'],r['case_id']];assert r['source_id']==x['source_id'] and r['status']=='OK'
 assert r['risk_labels']==s.risk_labels(r['metrics'],r['position_shape'])
 for label,v in r['risk_labels'].items():assert r['metrics'][label]==float(v)
check('source_status_risk_thresholds',True)
check('168_source_aggregate_recomputed',s.metric.json_safe(s.aggregate_source(rows))==sources and len(sources)==168)
for sr in sources:
 part=[r for r in rows if (r['fold'],r['source_id'],r['arm'])==(sr['fold'],sr['source_id'],sr['arm'])];assert len(part)==5
 for k,v in sr['metrics'].items():
  vals=[r['metrics'][k] for r in part]
  expected=None if any(x is None for x in vals) else sum(vals)/5
  assert v is None if expected is None else abs(v-expected)<=1e-10*max(1,abs(expected))
check('independent_five_defect_source_means',True)
base=[json.loads(x) for x in bound(q['frozen_baseline_scores']).read_text(encoding='utf-8').splitlines()];bl={(r['fold'],r['case_id'],r['arm']):r for r in base if r['arm'] in s.CONTROLS};curr=[r for r in rows if r['arm'] in s.CONTROLS]
check('all420_controls_exactly_frozen',len(bl)==len(curr)==420 and all(bl[r['fold'],r['case_id'],r['arm']]==r for r in curr))
check('single_comparison_qualification_bound',pair['fixed_comparisons']==['RF-Requery_minus_RF-Static'] and pair['comparison_qualification']==c['comparison_qualification']==q['comparison_qualification'] and pair['request_sha256']==qs)
deltas=[]
for fold in 'CD':
 rr=[r for r in rows if r['fold']==fold];ss=[r for r in sources if r['fold']==fold];assert len(rr)==420 and len(ss)==84
 p=('RF-Static','RF-Requery');key='RF-Requery_minus_RF-Static';v=s.paired_summary(ss,p);v.update(baseline_arm=p[0],candidate_arm=p[1]);assert s.metric.json_safe(v)==pair['comparison'][fold][key]
 assert s.metric.json_safe(s.risk_transitions(rr,p))==risk[fold][key] and s.metric.json_safe(s.defect_summary(rr,p))==defects[fold][key]
 dd=s.case_differences(rr,p)
 for x in dd:x.update(comparison=key)
 deltas.extend(dd)
 rankings={k:sorted(vv['source_deltas'],key=lambda r:(r['delta'] is None,(-r['delta'] if vv['improvement_direction']=='negative' else r['delta']) if r['delta'] is not None else 0,r['source_id'])) for k,vv in v['metrics'].items() if vv['improvement_direction']!='descriptive_not_ordered'}
 assert s.metric.json_safe(dict(source_rankings=rankings,case_deltas=dd))==ranks[fold][key]
check('twofold_pairs_risks_defects_rankings_recomputed',True)
def csv_expected(rows):
 flat=[{**{k:v for k,v in r.items() if k not in {'metrics','full_metrics','position_shape','risk_labels','stage_geometry'}},**s.metric.json_safe(r['metrics'])} for r in rows]
 f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat);return f.getvalue().encode()
check('all3CSV_byte_consistency',all((O/n).read_bytes()==csv_expected(rs) for n,rs in [('case_metrics.csv',rows),('source_metrics.csv',sources),('paired_case_deltas.csv',deltas)]))
check('exact210_stdout_cases',len((A/'stdout_v1.txt').read_text(encoding='utf-8').splitlines())==210)
check('all_counts_summary_no_inference',pair['case_count']==210 and pair['model_predictions']==pair['controls']==420)
check('output_size_bound',sum(v['bytes'] for v in before['output'].values())<=q['limits']['output_bytes'])
after=dict(output=inventory(O),execution=inventory(A));check('before_after_all_hash_attributes_stable',before==after)
audit=dict(status='FORMAL_RIVE_TWO_ARM_POST_SCORE_FREEZE_AUDIT_PASS',request_sha256=qs,checks=checks,check_count=len(checks),inventory=after,completion=c,operations=dict(real_scores_recomputed=0,summary_recalculations_only=True,server_calls=0,model_calls=0,backup_writes=0),limitations=['Audit recomputes summaries from frozen scores, not every point-distance metric.','CPU RSS during scoring was guarded in-process; no continuous resource log is added by this audit.','Single seed, exploratory development comparison, no bootstrap/p-values/formal gate.'])
(D/'audit_verification_v1.json').write_bytes((json.dumps(audit,indent=2)+'\n').encode());print(json.dumps(dict(status=audit['status'],checks=len(checks),counts=q['counts'])))
