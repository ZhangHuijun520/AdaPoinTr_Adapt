"""Construct independent stdlib audit from previously reviewed algebra helpers."""
from pathlib import Path
import ast
S=Path(__file__).resolve().parent
root=S.parents[2]
old=root/'outputs/cranial_bcsp_mamba_p1_20261104/paired_development_evaluator_v2/audit_P1_pair_scores_v1.py'
src=old.read_text(encoding='utf-8')
helpers=src[src.index('START=time.monotonic()'):src.index('def main():')].replace('M0','M_H1').replace('T0','M0')
header='''"""Independent read-only H1/M0 freeze audit: no scoring/model/geometry imports."""
import csv,hashlib,io,json,math,statistics,time,ctypes
from pathlib import Path
S=Path(__file__).resolve().parent;A=S/'authorized_execution_v1';O=S/'unified_scores_v1';F=S/'post_scoring_freeze_audit_20261107_v1'
SHA='a962c57510371c880fa3510a56c2ffe4081537201797210a5769558dd07f94ab'
ARMS=['M0','M_H1'];ALL=ARMS+['Nop_D','GT_8192'];DEFECTS={'bilateral','frontoorbital','parietotemporal','random_1','random_2'}
'''
main=r'''
def bindings(obj):
 if isinstance(obj,dict):
  if {'path','bytes','sha256'}<=set(obj):checked(obj['path'],obj,keep=not obj['path'].endswith(('.npz','.tar.gz','.exe')))
  else:
   for v in obj.values():bindings(v)
 elif isinstance(obj,list):
  for v in obj:bindings(v)

def main():
 F.mkdir()
 try:
  q=js(S/'local_scoring_execution_request_v1.json');good('exact_authorized_request_SHA',checked(S/'local_scoring_execution_request_v1.json')[0]['sha256']==SHA)
  before=tree(O);good('exact_twelve_regular_output_files',set(p.name for p in O.iterdir())==set(q['expected_result_files']) and all(p.is_file() for p in O.iterdir()) and str(O)==q['output'])
  for p in O.iterdir():checked(p)
  bindings(q);good('all_request_bound_code_environment_archives_sidecars_evidence_hashes')
  p3=js(q['P3']['path']);bindings(p3)
  tests=js(p3['CPU_result']['path']);good('P3_and32_CPU_contracts',p3['status']=='LOCAL_H1_M0_TWOFOLD_SCORING_P3_PASS' and p3['CPU_tests']==32 and all(p3['review_checks'].values()) and tests['status']=='ARTIFICIAL_CPU_CONTRACT_PASS')
  index=js(q['score_case_index']['path']);cases=index['cases'];bindings(cases)
  keys=[(c['fold'],c['case_id']) for c in cases];source_for={(c['fold'],c['case_id']):c['source_id'] for c in cases}
  ids={f:[c['case_id'] for c in cases if c['fold']==f] for f in ['C','D']};sources={f:sorted({source_for[f,c] for c in ids[f]}) for f in ids}
  good('210_fixed_cases42_disjoint_sources_all_reference_and_input_hashes',len(keys)==len(set(keys))==210 and all(len(ids[f])==105 and len(sources[f])==21 for f in ids) and not set(sources['C'])&set(sources['D']))
  for p in A.iterdir():checked(p)
  auth=js(A/'score_authorization_v1.json');good('explicit_one_way_authorization',auth['schema']=='bcsp-p2-H1-M0-score-authorization-v1' and auth['request_sha256']==SHA and auth['explicit_user_authorization'] is True and SHA in auth['user_authorization_text'] and 'runtime_sha256' not in auth)
  inv=js(A/'invocation_materialization_v1.json');good('invocation_auth_binding_and_timeout',inv['request_sha256']==SHA and inv['authorization_sha256']==checked(A/'score_authorization_v1.json')[0]['sha256'] and inv['timeout_seconds']==14430)
  worker=js(A/'worker_started_v1.json');kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];kernel.OpenProcess.restype=ctypes.c_void_p;handle=kernel.OpenProcess(0x1000,0,worker['pid'])
  if handle:
   code=ctypes.c_uint32();kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)];need(kernel.GetExitCodeProcess(handle,ctypes.byref(code)) and code.value!=259,'worker active/unknown');kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle(handle)
  else:need(ctypes.get_last_error()==87,'worker state unknown')
  good('worker_ended')
  result=js(A/'execution_result_v1.json');complete=js(O/'completion.json')
  good('unique_attempt_exit0_no_timeout_no_retry',result['returncode']==0 and result['timeout'] is False and result['error'] is None and result['failure'] is None and result['retries']==0 and js(O/'single_attempt_claim.json')==dict(status='CLAIMED_BEFORE_SCORING',request_sha256=SHA,no_retry=True) and js(A/'attempt_started_v1.json')['status']=='CLAIMED_BEFORE_LOCAL_SUBPROCESS')
  equal(result['completion'],complete)
  good('completion840case168source_and_no_GPU_forward_bootstrap_gate',complete['status']=='LOCAL_H1_M0_TWOFOLD_CPU_SCORING_COMPLETE' and [complete[k] for k in ['model_predictions','controls','score_rows','source_rows']]==[420,420,840,168] and complete['request_sha256']==SHA and complete['archive_sha256']=={k:v['archive']['sha256'] for k,v in q['archive_inputs'].items()} and all(complete[k]==0 for k in ['server_operations','model_imports','forward_calls','bootstrap']) and complete['formal_gate'] is False)
  stdout=checked(A/'stdout_v1.txt');stderr=checked(A/'stderr_v1.txt');good('exact210_stdout_cases_empty_stderr',stdout[1].decode().splitlines()==['SCORED '+f+' '+cid for f,cid in keys] and stderr[1]==b'' and stdout[0]['sha256']==result['stdout_sha256'] and stderr[0]['sha256']==result['stderr_sha256'])
  env=js(O/'execution_environment.json');good('frozen_CPU_environment',env['packages']==q['environment']['packages'] and env['python']==q['environment']['python_version'] and env['executable']==q['environment']['python']['path'] and env['CUDA_VISIBLE_DEVICES']=='' and env['threads']==2 and env['request_sha256']==SHA)
  rows=[json.loads(x) for x in checked(O/'case_metrics.jsonl')[1].decode().splitlines()];lookup={(r['fold'],r['case_id'],r['arm']):r for r in rows};columns=set(rows[0]['metrics'])
  good('ordered840_unique_case_arm_rows',len(rows)==len(lookup)==840 and [(r['fold'],r['case_id'],r['arm']) for r in rows]==[(f,c,a) for f,c in keys for a in ALL])
  for r in rows:
   need(r['source_id']==source_for[r['fold'],r['case_id']] and r['status']=='OK','case scope/status');full=r['full_metrics'];need(full['status']=='OK' and full['point_count']==8192,'full metric status/budget');verify_P1_row(r,select(full));need(set(r['metrics'])==columns,'fixed columns')
   for k,v in r['metrics'].items():need(v is None or (isinstance(v,(int,float)) and math.isfinite(v) and v>=0 and (v<=1 if 'coverage' in k or 'outlier' in k else True)),'finite metric domain')
   if r['arm']=='GT_8192':equal(r['metrics']['CD_L1_mm'],0.)
  good('all_selected_metrics_pose_stage_algebra_thresholds_and_GT_control')
  risks=js(O/'risk_transitions.json')
  for f in ids:equal(risks[f],risk_table([r for r in rows if r['fold']==f],ids[f]),'risk '+f)
  good('bothfold_risk_counts_new_rescued_and_all_defect_strata')
  groups={}
  for r in rows:groups.setdefault((r['fold'],r['source_id'],r['arm']),[]).append(r)
  expected=[]
  for (f,sid,arm),part in sorted(groups.items()):
   need(len(part)==5 and {r['case_id'].split('__',2)[-1] for r in part}==DEFECTS,'five defects/source')
   expected.append(dict(fold=f,source_id=sid,arm=arm,case_count=5,invalid_predictions=0,metrics={k:mean([r['metrics'][k] for r in part]) if all(r['metrics'][k] is not None for r in part) else None for k in columns}))
  equal(js(O/'source_metrics.json'),expected);good('168_independently_recomputed_source_means',len(expected)==168)
  bs={(r['fold'],r['source_id'],r['arm']):r['metrics'] for r in expected};comparison=js(O/'paired_comparison.json')
  good('descriptive_twofold_summary_identity',comparison['status']=='TWOFOLD_SINGLE_SEED_DESCRIPTIVE_PAIRED_COMPARISON' and comparison['case_count']==210 and comparison['model_predictions']==420 and comparison['controls']==420 and comparison['request_sha256']==SHA)
  defects={};rankings=js(O/'regression_rankings.json');all_deltas=[]
  for f in ids:
   summ=comparison['comparison'][f];need(summ['source_count']==21 and summ['defects_per_source']==5 and all(summ[k] for k in ['no_bootstrap','no_p_values','no_formal_gate','training_randomness_not_estimated']),'source unit/disclosure')
   for key in columns:
    a=[bs[f,s,'M0'][key] for s in sources[f]];b=[bs[f,s,'M_H1'][key] for s in sources[f]];d=[y-x if x is not None and y is not None else None for x,y in zip(a,b)];z=summ['metrics'][key]
    need(z['pair_count']==21 and z['undefined_pairs']==d.count(None),'retained pairs');equal(z['source_deltas'],[dict(source_id=s,delta=v) for s,v in zip(sources[f],d)])
    if None not in d:
     need(z['status']=='OK','status')
     for k,v in dict(mean_M0=mean(a),mean_M_H1=mean(b),mean_delta_M_H1_minus_M0=mean(d),median_delta=statistics.median(d),min_delta=min(d),max_delta=max(d)).items():equal(z[k],v,'summary '+f+key+k)
     direction='descriptive_not_ordered' if key=='radius_gyration_ratio' else 'positive' if 'coverage' in key else 'negative';need(z['improvement_direction']==direction,'direction')
     if direction!='descriptive_not_ordered':
      need(z['improved_sources']==sum(x>0 if direction=='positive' else x<0 for x in d) and z['worse_sources']==sum(x<0 if direction=='positive' else x>0 for x in d) and z['tied_sources']==d.count(0),'wins')
      ranked=sorted(z['source_deltas'],key=lambda r:(r['delta'] is None,(-r['delta'] if direction=='negative' else r['delta']) if r['delta'] is not None else 0,r['source_id']));equal(rankings[f]['source_rankings'][key],ranked)
    else:need(z['status']=='UNDEFINED_NONFINITE_PAIRS_RETAINED' and z['mean_delta_M_H1_minus_M0'] is None,'undefined retained')
   cd=[]
   for cid in sorted(ids[f]):
    a,b=[lookup[f,cid,arm] for arm in ARMS];cd.append(dict(fold=f,case_id=cid,source_id=a['source_id'],defect=cid.split('__',2)[-1],metrics={k:b['metrics'][k]-a['metrics'][k] if a['metrics'][k] is not None and b['metrics'][k] is not None else None for k in columns}))
   equal(rankings[f]['case_deltas'],cd);all_deltas+=cd;defects[f]={}
   for defect in sorted(DEFECTS):
    part=[r for r in cd if r['defect']==defect];need(len(part)==21,'21/defect');defects[f][defect]=dict(paired_cases=21,mean_deltas={k:mean([r['metrics'][k] for r in part]) if all(r['metrics'][k] is not None for r in part) else None for k in columns})
  equal(js(O/'defect_comparison.json'),defects);good('all_source_deltas_means_medians_winloss_rankings_and_defect_summaries')
  csv_check(O/'case_metrics.csv',rows);csv_check(O/'source_metrics.csv',expected);csv_check(O/'paired_case_deltas.csv',all_deltas);good('three_CSV_JSON_values_and_order')
  root=S.parents[2];p1=root/'outputs/cranial_bcsp_mamba_p1_20261104'
  for f,sub in [('C','paired_development_evaluator_v2'),('D','FoldD_paired_development_entry_v1')]:
   prior=js(p1/sub/'post_scoring_freeze_audit_v1/audit_report_v1.json');need(prior['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS','prior audit')
   binding=next(r for r in prior['output_manifest'] if Path(r['path']).name=='case_metrics.jsonl');raw=checked(binding['path'],binding)[1];old={(r['case_id'],r['arm']):r for r in map(json.loads,raw.decode().splitlines())}
   for cid in ids[f]:
    for arm in ['M0','Nop_D','GT_8192']:
     for k in ['metrics','full_metrics','position_shape','risk_labels','stage_geometry']:equal(lookup[f,cid,arm][k],old[cid,arm][k],'frozen P1 numeric crosscheck '+f+cid+arm+k)
  good('all630_M0_and_shared_control_rows_match_frozen_P1_scores')
  good('stable_all_content_fingerprints_atime_excluded',tree(O)==before and all(stamp(Path(p))==v for p,v in STAMPS.items()))
  report=dict(status='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS',checks=CHECKS,request_sha256=SHA,counts=dict(cases=210,sources=42,model_scores=420,controls=420,case_rows=840,source_rows=168),exit_code=0,output_manifest=[r for r in MANIFEST if Path(r['path']).parent==O],all_read_file_manifest=MANIFEST,read_bytes=READ,seconds=time.monotonic()-START,limits=dict(total_read_bytes=1073741824,per_file_bytes=67108864,wall_seconds=120),independent_aggregation_recomputed=True,geometry_distance_recomputed=False,arrays_decoded=False,scoring_rerun=False,model_imports=0,GPU_calls=0,server_operations=0,limitations=['Saved metric arithmetic and aggregation audited; geometric nearest-neighbour distances not recomputed','Single training seed per fold; no significance inference, bootstrap, formal gate or clinical certification','Environment identity verified from frozen binary/package records, no package import or rerun'])
 except BaseException as exc:
  report=dict(status='FORMAL_POST_SCORING_FREEZE_AUDIT_FAILED_STOP_NO_RETRY',passed_checks=CHECKS,error=repr(exc),read_bytes=READ,seconds=time.monotonic()-START,scoring_rerun=False)
 with (F/'audit_report_v1.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2,allow_nan=False)
 print(json.dumps({k:v for k,v in report.items() if k not in {'all_read_file_manifest','output_manifest'}}))
 if report['status']!='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS':raise SystemExit(1)
if __name__=='__main__':main()
'''
target=S/'audit_H1_M0_scores_v1.py'
code=header+helpers+main
ast.parse(code)
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(code)
print(target)
