"""Independent stdlib read-only score freeze audit; no geometry/model/score imports."""
import ast,csv,hashlib,io,json,math,statistics,time
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1';S=N/'score_implementation_v1';A=S/'authorized_execution_v1';O=N/'paired_scores_v1';F=N/'post_scoring_freeze_audit_v1'
SHA='0748d8e99c6589e47195a255abaf58f77751941e17c71e5e6ddb7c456ff059fa'
ARMS=['V1','Morton_area_stratified8k'];ALL=ARMS+['Nop_D_V1','Nop_D_Morton_area_stratified8k','GT_8192'];DEFECTS={'bilateral','frontoorbital','parietotemporal','random_1','random_2'}
START=time.monotonic();READ=0;STAMPS={};CACHE={};CHECKS=[];MANIFEST=[]
def need(ok,msg):
 if not ok:raise ValueError(msg)
def good(name,ok=True):need(ok,name);CHECKS.append(name)
def stamp(p):
 s=p.stat();return (s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns)
def checked(p,binding=None,keep=True):
 global READ
 p=Path(p);need(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),'file path/type/link: '+str(p))
 if str(p) not in CACHE:
  before=stamp(p);need(p.stat().st_size<=67108864,'per file cap: '+str(p));h=hashlib.sha256();parts=[]
  with p.open('rb') as f:
   for blob in iter(lambda:f.read(1048576),b''):
    READ+=len(blob);need(READ<=1073741824 and time.monotonic()-START<=120,'read/time budget');h.update(blob)
    if keep:parts.append(blob)
  need(stamp(p)==before,'read drift: '+str(p));STAMPS[str(p)]=before;row=dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest());MANIFEST.append(row);CACHE[str(p)]=(row,b''.join(parts) if keep else None)
 row,raw=CACHE[str(p)]
 if binding:need(all(row[k]==binding[k] for k in ['bytes','sha256']),'binding mismatch: '+str(p))
 return row,raw
def js(p,binding=None):return json.loads(checked(p,binding)[1])
def equal(actual,expected,path='root'):
 if isinstance(expected,dict):
  need(isinstance(actual,dict) and set(actual)==set(expected),'keys: '+path)
  for key in expected:equal(actual[key],expected[key],path+'.'+key)
 elif isinstance(expected,list):
  need(isinstance(actual,list) and len(actual)==len(expected),'list: '+path)
  for k,(a,b) in enumerate(zip(actual,expected)):equal(a,b,path+'.'+str(k))
 elif isinstance(expected,float):need(isinstance(actual,(int,float)) and math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-11,abs_tol=1e-11),'numeric: '+path)
 else:need(type(actual)==type(expected) and actual==expected,'value: '+path)
def mean(values):return math.fsum(values)/len(values)
def tree(folder):
 result={}
 for p in [folder,*folder.rglob('*')]:
  need(not p.is_symlink() and (p.is_file() or p.is_dir()) and len(result)<64,'bounded regular result tree');result[str(p)]=stamp(p)
 return result
def select(full):
 v=dict(E_P95_mm=full['primary_E_G_P95_mm'],J_P95_mm=full['regions']['A1']['J']['p95_mm'],all_P95_mm=full['regions']['A1']['all']['p95_mm'],CD_L1_mm=full['CD_L1_mm'])
 for region in ['E','J']:
  r=full['regions']['A1'][region];v[region+'_mean_mm']=r['mean_mm'];v[region+'_max_mm']=r['max_mm']
  for tau in ['0.5','1.0','2.0']:v[region+'_coverage_'+tau+'mm']=r['coverage'][tau]
  v['A2_'+region+'_P95_mm']=full['regions']['A2'][region]['p95_mm']
 for ref in ['A2','B']:
  r=full['reverse_discrete_reference'][ref];v['reverse_'+ref+'_P95_mm']=r['p95_mm']
  for tau in ['0.5','1.0','2.0']:v['reverse_'+ref+'_outlier_'+tau+'mm']=r['outlier_fraction'][tau]
 v['B_all_P95_mm']=full['regions']['B']['all']['p95_mm'];return v
def csv_check(path,expected):
 data=list(csv.DictReader(io.StringIO(checked(path)[1].decode('utf-8'))));need(len(data)==len(expected),'CSV row count')
 for a,r in zip(data,expected):
  flat={**{k:v for k,v in r.items() if k not in {'metrics','full_metrics'}},**r['metrics']};need(set(a)==set(flat),'CSV columns')
  for k,v in flat.items():
   if isinstance(v,float):equal(float(a[k]),v,'CSV '+path.name+'.'+k)
   else:need(a[k]==('' if v is None else str(v)),'CSV field: '+k)
def main():
 F.mkdir()
 try:
  qpath=S/'local_scoring_execution_request_v1.json';qraw=checked(qpath)[1];good('exact_authorized_request_SHA',hashlib.sha256(qraw).hexdigest()==SHA);q=json.loads(qraw)
  good('exact_output_set',set(p.name for p in O.iterdir())==set(q['expected_result_files']) and all(p.is_file() for p in O.iterdir()))
  before=tree(O)
  for p in O.iterdir():checked(p)
  good('new_owned_output_path',str(O)==q['output'])
  for record in [*q['implementation'].values(),q['environment']['python'],*q['evidence'].values(),q['P3'],q['reference_manifest'],q['prediction_index'],q['score_case_index'],q['implementation_note'],q['downloaded_prediction_archive'],*q['download_sidecars']]:checked(record['path'],record,keep=not record['path'].endswith(('.npz','.tar.gz','.exe')))
  p3=js(q['P3']['path']);good('P3_and_24_passing_CPU_tests',p3['status']=='LOCAL_P3_PASS_FOR_PENDING_PAIRED_CPU_SCORING' and p3['test_count']==24)
  tests=js(p3['tests']['path'],p3['tests']);checked(p3['test_stdout']['path'],p3['test_stdout']);checked(p3['test_source']['path'],p3['test_source'])
  good('final_code_still_matches_CPU_tests',tests['status']=='PASS' and tests['failures']==tests['errors']==0 and tests['scorer_sha256']==q['implementation']['scorer']['sha256'] and tests['metric_sha256']==q['implementation']['metrics']['sha256'])
  checked(p3['metric_source_unchanged']['path'],p3['metric_source_unchanged']);good('metric_definition_unchanged',p3['metric_source_unchanged']['sha256']==q['implementation']['metrics']['sha256'])
  index=js(q['score_case_index']['path']);pred=js(q['prediction_index']['path']);refs=js(q['reference_manifest']['path']);cases=index['cases'];ids=[c['case_id'] for c in cases];sources=sorted({c['source_id'] for c in cases})
  good('fixed105_cases_21_sources',len(cases)==len(set(ids))==105 and len(sources)==21 and ids==pred['runs'][0]['dev_case_ids']==pred['runs'][1]['dev_case_ids']==[r['case_id'] for r in refs['cases']])
  for c in cases:
   checked(c['reference']['path'],c['reference'],keep=False)
   for r in c['point_files'].values():checked(r['path'],r,keep=False)
  good('all315_point_and_reference_files_hash_match',True)
  for p in A.iterdir():checked(p,keep=True)
  auth=js(A/'score_authorization_v1.json');good('authorization_exact_request_and_no_reverse_binding',set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-sampling-pair-score-authorization-v1' and auth['request_sha256']==SHA and auth['explicit_user_authorization'] is True and SHA in auth['user_authorization_text'])
  invocation=js(A/'invocation_materialization_v1.json');good('materialized_authorization_SHA_and_timeout',invocation['authorization_sha256']==checked(A/'score_authorization_v1.json')[0]['sha256'] and invocation['request_sha256']==SHA and invocation['timeout_seconds']==7205)
  result=js(A/'execution_result_v1.json');complete=js(O/'completion.json');claim=js(O/'single_attempt_claim.json')
  good('successful_unique_attempt_no_retry',result['status']=='LOCAL_CPU_SCORING_FINISHED_PENDING_FORMAL_FREEZE_AUDIT' and result['returncode']==0 and result['timeout'] is False and result['error'] is None and result['failure'] is None and result['retries']==0 and claim==dict(status='CLAIMED_BEFORE_SCORING',request_sha256=SHA,no_retry=True) and js(A/'attempt_started_v1.json')['status']=='CLAIMED_BEFORE_LOCAL_SUBPROCESS')
  equal(result['completion'],complete)
  good('completion_exact525_rows_105_sources_and_no_GPU',complete['status']=='LOCAL_PAIRED_CPU_SCORING_COMPLETE' and complete['model_predictions']==210 and complete['controls']==315 and complete['score_rows']==525 and complete['source_rows']==105 and complete['request_sha256']==SHA and complete['archive_sha256']==q['downloaded_prediction_archive']['sha256'] and complete['server_operations']==complete['model_imports']==complete['forward_calls']==complete['bootstrap']==0 and complete['formal_gate'] is False)
  stdout=checked(A/'stdout_v1.txt')[1];stderr=checked(A/'stderr_v1.txt')[1]
  good('stdout_exact105_cases_stderr_empty',stdout.decode().splitlines()==['SCORED '+cid for cid in ids] and len(stderr)==0 and checked(A/'stdout_v1.txt')[0]['sha256']==result['stdout_sha256'] and checked(A/'stderr_v1.txt')[0]['sha256']==result['stderr_sha256'])
  environment=js(O/'execution_environment.json');good('frozen_CPU_environment',environment['packages']==q['environment']['packages'] and environment['python']==q['environment']['python_version'] and environment['executable']==q['environment']['python']['path'] and environment['CUDA_VISIBLE_DEVICES']=='' and environment['threads']==2 and environment['request_sha256']==SHA)
  rows=[json.loads(line) for line in checked(O/'case_metrics.jsonl')[1].decode().splitlines()];lookup={(r['case_id'],r['arm']):r for r in rows}
  good('complete_ordered525_case_scores',len(rows)==len(lookup)==525 and [(r['case_id'],r['arm']) for r in rows]==[(cid,a) for cid in ids for a in ALL])
  source_for={c['case_id']:c['source_id'] for c in cases};columns=set(rows[0]['metrics'])
  for r in rows:
   need(r['fold']=='C' and r['source_id']==source_for[r['case_id']] and r['status']=='OK','case scope/status')
   full=r['full_metrics'];need(full['status']=='OK' and full['point_count']==8192,'full metric point count/status');equal(r['metrics'],select(full),'selected metrics')
   need(set(r['metrics'])==columns,'fixed metric columns')
   for k,v in r['metrics'].items():need(v is None or (isinstance(v,(int,float)) and math.isfinite(v) and v>=0 and (v<=1 if ('coverage' in k or 'outlier' in k) else True)),'finite metric domain')
   if r['arm']=='GT_8192':equal(r['metrics']['CD_L1_mm'],0.,'self GT CD')
  good('selected_metrics_match_full_fields_domains_and_GT_control',True)
  grouped={}
  for r in rows:grouped.setdefault((r['source_id'],r['arm']),[]).append(r)
  expected_sources=[]
  for (sid,arm),part in sorted(grouped.items()):
   need(len(part)==5 and {r['case_id'].split('__',2)[-1] for r in part}==DEFECTS,'five fixed defects/source')
   v={k:mean([r['metrics'][k] for r in part]) if all(r['metrics'][k] is not None for r in part) else None for k in rows[0]['metrics']}
   expected_sources.append(dict(fold='C',source_id=sid,arm=arm,case_count=5,invalid_predictions=0,metrics=v))
  observed_sources=js(O/'source_metrics.json');equal(observed_sources,expected_sources,'independent source means');good('all105_source_rows_independent_five_defect_mean',len(expected_sources)==105)
  bysource={(r['source_id'],r['arm']):r for r in expected_sources};comparison=js(O/'paired_comparison.json');summ=comparison['comparison']
  good('paired_summary_identity_and_descriptive_only',comparison['status']=='SINGLE_FOLD_SINGLE_SEED_DESCRIPTIVE_PAIRED_COMPARISON' and comparison['case_count']==105 and comparison['model_predictions']==210 and comparison['controls']==315 and comparison['request_sha256']==SHA and summ['source_count']==21 and summ['defects_per_source']==5 and summ['no_bootstrap'] and summ['no_p_values'] and summ['no_formal_gate'] and summ['training_randomness_not_estimated'])
  for key in columns:
   a=[bysource[(sid,'V1')]['metrics'][key] for sid in sources];b=[bysource[(sid,ARMS[1])]['metrics'][key] for sid in sources];defined=[x is not None and y is not None and math.isfinite(x) and math.isfinite(y) for x,y in zip(a,b)];d=[y-x if ok else None for x,y,ok in zip(a,b,defined)];s=summ['metrics'][key]
   need(s['pair_count']==21 and s['undefined_pairs']==defined.count(False),'no dropped pairs')
   equal(s['source_deltas'],[dict(source_id=sid,delta=delta) for sid,delta in zip(sources,d)],'source deltas')
   if all(defined):
    need(s['status']=='OK','summary status')
    for k,v in dict(mean_V1=mean(a),mean_Morton=mean(b),mean_delta_Morton_minus_V1=mean(d),median_delta=statistics.median(d),min_delta=min(d),max_delta=max(d)).items():equal(s[k],v,'summary '+key+'.'+k)
    positive='coverage' in key;need(s['improvement_direction']==('positive' if positive else 'negative'),'direction')
    need(s['improved_sources']==sum(x>0 if positive else x<0 for x in d) and s['worse_sources']==sum(x<0 if positive else x>0 for x in d) and s['tied_sources']==d.count(0),'win/tie/loss')
   else:need(s['status']=='UNDEFINED_NONFINITE_PAIRS_RETAINED' and s['mean_delta_Morton_minus_V1'] is None,'undefined pairs retained')
  good('all_metric_source_equal_means_deltas_medians_and_win_loss_independently_recomputed')
  case_deltas=[]
  for cid in sorted(ids):
   a,b=[lookup[(cid,arm)] for arm in ARMS];v={k:b['metrics'][k]-a['metrics'][k] if a['metrics'][k] is not None and b['metrics'][k] is not None else None for k in a['metrics']}
   case_deltas.append(dict(fold='C',case_id=cid,source_id=a['source_id'],defect=cid.split('__',2)[-1],metrics=v))
  defects={}
  for defect in sorted(DEFECTS):
   part=[r for r in case_deltas if r['defect']==defect];need(len(part)==21,'21 cases/defect')
   defects[defect]=dict(paired_cases=21,mean_deltas={k:mean([r['metrics'][k] for r in part]) if all(r['metrics'][k] is not None for r in part) else None for k in rows[0]['metrics']})
  equal(js(O/'defect_comparison.json'),defects,'defect summary');good('five_defect_summaries_independently_recomputed')
  rankings=js(O/'regression_rankings.json');equal(rankings['case_deltas'],case_deltas,'all case deltas')
  for key,s in summ['metrics'].items():
   expected=sorted(s['source_deltas'],key=lambda r:(r['delta'] is None,(-r['delta'] if s['improvement_direction']=='negative' else r['delta']) if r['delta'] is not None else 0,r['source_id']));equal(rankings['source_rankings'][key],expected,'ranked '+key)
  good('all_case_deltas_and_all_source_regression_orderings_match')
  csv_check(O/'case_metrics.csv',rows);csv_check(O/'source_metrics.csv',expected_sources);csv_check(O/'paired_case_deltas.csv',case_deltas);good('all_three_CSV_files_match_JSON_values_and_order')
  good('no_failure_marker_or_unexpected_payload',not (O/'failure.json').exists() and not list(O.rglob('*.npz')) and not list(O.rglob('*.pth')))
  good('all_result_and_input_fingerprints_stable_atime_excluded',tree(O)==before and all(stamp(Path(p))==value for p,value in STAMPS.items()))
  report=dict(status='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS',checks=CHECKS,request_sha256=SHA,exit_code=0,counts=dict(cases=105,sources=21,model_scores=210,controls=315,case_rows=525,source_rows=105,model_source_rows=42),output_manifest=[r for r in MANIFEST if Path(r['path']).parent==O],all_read_file_manifest=MANIFEST,independent_aggregation_recomputed=True,geometry_distance_recomputed=False,real_prediction_arrays_decoded=False,scoring_rerun=False,server_operations=0,GPU_calls=0,model_imports=0,elapsed_seconds=time.monotonic()-START,read_bytes=READ,limits=dict(read_bytes=1073741824,wall_seconds=120),limitations=['Metric values checked against frozen saved full metric fields, not independently recomputed geometric distances','Source means/deltas/rankings/CSV consistency independently recomputed using stdlib','Resource success based on frozen sampled guards and completion, not independent peak RSS telemetry','One fold/one training seed; no bootstrap,p-value,formal gate or clinical validation'],scientific_interpretation_authorized_after_pass=True)
 except BaseException as exc:report=dict(status='FORMAL_POST_SCORING_FREEZE_AUDIT_FAILED_STOP_NO_RETRY',passed_checks=CHECKS,error=repr(exc),read_bytes=READ,geometry_distance_recomputed=False,scoring_rerun=False,server_operations=0)
 with (F/'audit_report_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,allow_nan=False)
 print(json.dumps({k:v for k,v in report.items() if k not in {'output_manifest','all_read_file_manifest'}}))
 if report['status']!='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS':raise SystemExit(1)
if __name__=='__main__':main()
