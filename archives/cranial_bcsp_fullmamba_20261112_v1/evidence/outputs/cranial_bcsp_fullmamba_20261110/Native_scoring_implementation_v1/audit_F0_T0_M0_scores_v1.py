"""Independent read-only F0/T0/M0 freeze audit: no scoring/model/geometry imports."""
import csv,hashlib,io,json,math,statistics,time,ctypes
from pathlib import Path
S=Path(__file__).resolve().parent;A=S/'authorized_execution_v1';O=S/'unified_scores_v1';F=S/'post_scoring_freeze_audit_20261111_v1'
SHA='eaa35866db0c8dc231ee0b6f2cfd8a0d72436d088d5066bbf694acc7313ec175'
ARMS=['T0','M0','F0'];PAIRS=[('M0','F0'),('T0','F0'),('T0','M0')];ALL=ARMS+['Nop_D','GT_8192'];DEFECTS={'bilateral','frontoorbital','parietotemporal','random_1','random_2'}
LARGE_FILES={'E:\\ResearchBackups\\AdaPoinTr\\BCSP_FULLMAMBA_F0\\2026-11-11_native_development_eval\\development_predictions_v1.tar.gz': {'path': 'E:\\ResearchBackups\\AdaPoinTr\\BCSP_FULLMAMBA_F0\\2026-11-11_native_development_eval\\development_predictions_v1.tar.gz', 'bytes': 180647685, 'sha256': '32b80af60b4e3819e98c6bc096282e2bb71e3fe3b253e11c2a1623ec5e4aaac6'}, 'E:\\ResearchBackups\\AdaPoinTr\\BCSP_MAMBA_P1\\2026-11-06_FoldC_paired_development_eval\\development_predictions_v1.tar.gz': {'path': 'E:\\ResearchBackups\\AdaPoinTr\\BCSP_MAMBA_P1\\2026-11-06_FoldC_paired_development_eval\\development_predictions_v1.tar.gz', 'bytes': 19045938, 'sha256': '068dd9812c410c2b84451740a3ed2eb2f12326d8a66fe3bc3ee4623ab3f9b733'}, 'E:\\ResearchBackups\\AdaPoinTr\\BCSP_MAMBA_P1\\2026-11-06_FoldD_paired_development_eval\\development_predictions_v1.tar.gz': {'path': 'E:\\ResearchBackups\\AdaPoinTr\\BCSP_MAMBA_P1\\2026-11-06_FoldD_paired_development_eval\\development_predictions_v1.tar.gz', 'bytes': 19045760, 'sha256': '8e9c7d5bc49ee91819a7c555ba6b34c5a936f60fcc6f468eadbfcbe4467b9af3'}}
START=time.monotonic();READ=0;STAMPS={};CACHE={};CHECKS=[];MANIFEST=[]
def need(ok,msg):
 if not ok:raise ValueError(msg)
def good(name,ok=True):need(ok,name);CHECKS.append(name)
def stamp(p):
 s=p.stat();return (s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def checked(p,binding=None,keep=True):
 global READ
 p=Path(p);need(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),'file path/type/link: '+str(p))
 if str(p) not in CACHE:
  before=stamp(p);need(p.stat().st_size<=67108864 or (str(p) in LARGE_FILES and p.stat().st_size==LARGE_FILES[str(p)]['bytes']),'per file cap or exact archive exception: '+str(p));h=hashlib.sha256();parts=[]
  with p.open('rb') as f:
   for blob in iter(lambda:f.read(1048576),b''):
    READ+=len(blob);need(READ<=2147483648 and time.monotonic()-START<=120,'read/time budget');h.update(blob)
    if keep:parts.append(blob)
  need(stamp(p)==before,'read drift: '+str(p));STAMPS[str(p)]=before;row=dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest());MANIFEST.append(row);CACHE[str(p)]=(row,b''.join(parts) if keep else None)
 row,raw=CACHE[str(p)]
 if str(p) in LARGE_FILES:need(all(row[k]==LARGE_FILES[str(p)][k] for k in ['bytes','sha256']),'exact large archive binding')
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
  flat={**{k:v for k,v in r.items() if k not in {'metrics','full_metrics','position_shape','risk_labels','stage_geometry'}},**r['metrics']};need(set(a)==set(flat),'CSV columns')
  for k,v in flat.items():
   if isinstance(v,float):equal(float(a[k]),v,'CSV '+path.name+'.'+k)
   else:need(a[k]==('' if v is None else str(v)),'CSV field: '+k)
def verify_P1_row(r,base):
 p=r['position_shape'];centroid_delta=[a-b for a,b in zip(p['prediction_centroid_mm'],p['GT8192_centroid_mm'])];distance=math.sqrt(math.fsum(x*x for x in centroid_delta));ratio=p['prediction_radius_gyration_mm']/p['GT8192_radius_gyration_mm']
 equal(p['centroid_offset_vector_mm'],centroid_delta,'pose vector');equal(p['centroid_offset_mm'],distance,'pose norm');equal(p['radius_gyration_ratio'],ratio,'pose ratio')
 equal(p['prediction_radius_gyration_mm']**2,math.fsum(p['covariance_eigenvalues_mm2']),'prediction covariance trace');equal(p['GT8192_radius_gyration_mm']**2,math.fsum(p['GT8192_covariance_eigenvalues_mm2']),'GT covariance trace')
 labels=dict(placement_tail=distance>20.,compact_distribution=ratio<.9,severe_geometry=(base['E_P95_mm'] is not None and base['E_P95_mm']>20.) or base['J_coverage_2.0mm']==0.)
 equal(r['risk_labels'],labels,'risk thresholds')
 reverse20=r['metrics']['reverse_A2_outlier_20.0mm'];need(0<=reverse20<=base['reverse_A2_outlier_2.0mm'] and math.isclose(reverse20*8192,round(reverse20*8192),abs_tol=1e-9),'20mm discrete outlier monotonicity/count')
 base['reverse_A2_outlier_20.0mm']=reverse20
 base.update(centroid_offset_mm=distance,radius_gyration_ratio=ratio,**{k:float(v) for k,v in labels.items()});equal(r['metrics'],base,'P1 selected metrics')
 if r['arm'] in ARMS:
  stage=r['stage_geometry'];equal(stage['dense'],p,'same dense pose');need(stage['frame']=='native_world_mm_no_alignment' and stage['dense_points']==8192 and stage['coarse']['points']==256,'stage frame/point budgets')
  equal(stage['coarse']['radius_gyration_ratio'],stage['coarse']['radius_gyration_mm']/p['GT8192_radius_gyration_mm'],'coarse ratio')
  equal(stage['coarse']['centroid_offset_mm'],math.sqrt(math.fsum((a-b)**2 for a,b in zip(stage['coarse']['centroid_mm'],p['GT8192_centroid_mm']))),'coarse centroid norm')
  equal(stage['mean_dense_minus_coarse_mm'],[a-b for a,b in zip(p['prediction_centroid_mm'],stage['coarse']['centroid_mm'])],'dense-minus-coarse centroid')
  energy=stage['offset_mean_squared_radius_mm2']-math.fsum(v*v for v in stage['mean_dense_minus_coarse_mm']);equal(stage['offset_centered_variance_mm2'],energy,'offset centered variance')
  equal(stage['cross_term_twice_covariance_mm2'],p['prediction_radius_gyration_mm']**2-stage['coarse']['radius_gyration_mm']**2-energy,'cross covariance algebra')
 else:need(r['stage_geometry'] is None,'controls have no coarse model stage')

def risk_table(rows,ids,pair):
 lookup={(r['case_id'],r['arm']):r for r in rows};result={}
 for label in ['placement_tail','compact_distribution','severe_geometry']:
  records=[]
  for cid in sorted(ids):
   a,b=[lookup[(cid,arm)]['risk_labels'][label] for arm in pair];records.append(dict(case_id=cid,source_id='train:'+cid.split('__')[1],defect=cid.split('__',2)[-1],baseline_arm=pair[0],candidate_arm=pair[1],baseline=a,candidate=b,new=b and not a,rescued=a and not b))
  result[label]=dict(baseline_arm=pair[0],candidate_arm=pair[1],baseline_count=sum(r['baseline'] for r in records),candidate_count=sum(r['candidate'] for r in records),new=sum(r['new'] for r in records),rescued=sum(r['rescued'] for r in records),cases=records,by_defect={d:dict(new=sum(r['new'] for r in records if r['defect']==d),rescued=sum(r['rescued'] for r in records if r['defect']==d)) for d in sorted(DEFECTS)})
 return dict(labels=result,clinical_certification=False,overlapping_labels=True,GT_alignment=False)


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
  q=js(S/'local_scoring_execution_request_v1.json');good('exact_authorized_request_SHA256',checked(S/'local_scoring_execution_request_v1.json')[0]['sha256']==SHA)
  before=tree(O);good('exact12_regular_output_files',set(p.name for p in O.iterdir())==set(q['expected_result_files']) and all(p.is_file() for p in O.iterdir()) and str(O)==q['output'])
  for p in O.iterdir():checked(p)
  bindings(q);good('all_request_bound_code_CPU_archives_sidecars_and_evidence_hashes')
  p3=js(q['P3']['path']);bindings(p3);tests=js(p3['CPU_result']['path']);good('final_P3_and42_CPU_contracts',p3['status']=='LOCAL_F0_T0_M0_SCORING_P3_PASS' and p3['CPU_tests']==42 and all(p3['checks'].values()) and tests['status']=='F0_T0_M0_SCORING_CPU_CONTRACT_PASS')
  index=js(q['score_case_index']['path']);cases=index['cases'];bindings(cases);keys=[(c['fold'],c['case_id']) for c in cases];source_for={(c['fold'],c['case_id']):c['source_id'] for c in cases};case_for={(c['fold'],c['case_id']):c for c in cases}
  ids={f:[c['case_id'] for c in cases if c['fold']==f] for f in ['C','D']};sources={f:sorted({source_for[f,c] for c in ids[f]}) for f in ids}
  good('210_fixed_cases42_disjoint_sources_all_reference_and_point_hashes',len(keys)==len(set(keys))==210 and all(len(ids[f])==105 and len(sources[f])==21 for f in ids) and not set(sources['C'])&set(sources['D']))
  for p in A.iterdir():checked(p)
  auth=js(A/'score_authorization_v1.json');good('explicit_separate_authorization',auth['schema']=='bcsp-f0-T0-M0-score-authorization-v1' and auth['request_sha256']==SHA and auth['explicit_user_authorization'] is True and SHA in auth['user_authorization_text'])
  inv=js(A/'invocation_materialization_v1.json');good('invocation_auth_hash_and_external_timeout',inv['request_sha256']==SHA and inv['authorization_sha256']==checked(A/'score_authorization_v1.json')[0]['sha256'] and inv['timeout_seconds']==18030)
  worker=js(A/'worker_started_v1.json');kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];kernel.OpenProcess.restype=ctypes.c_void_p;handle=kernel.OpenProcess(0x1000,0,worker['pid'])
  if handle:
   code=ctypes.c_uint32();kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)];need(kernel.GetExitCodeProcess(handle,ctypes.byref(code)) and code.value!=259,'worker active/unknown');kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle(handle)
  else:need(ctypes.get_last_error()==87,'worker state unknown')
  good('worker_ended')
  result=js(A/'execution_result_v1.json');complete=js(O/'completion.json');good('exit0_no_timeout_no_retry_single_claim',result['returncode']==0 and result['timeout'] is False and result['error'] is None and result['failure'] is None and result['retries']==0 and js(O/'single_attempt_claim.json')==dict(status='CLAIMED_BEFORE_SCORING',request_sha256=SHA,no_retry=True) and js(A/'attempt_started_v1.json')['status']=='CLAIMED_BEFORE_LOCAL_SUBPROCESS')
  equal(result['completion'],complete);good('completion1050case210source_no_model_forward_bootstrap_gate',complete['status']=='LOCAL_F0_T0_M0_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE' and [complete[k] for k in ['model_predictions','controls','score_rows','source_rows']]==[630,420,1050,210] and complete['request_sha256']==SHA and complete['archive_sha256']=={k:v['archive']['sha256'] for k,v in q['archive_inputs'].items()} and all(complete[k]==0 for k in ['server_operations','model_imports','forward_calls','bootstrap']) and complete['formal_gate'] is False)
  stdout=checked(A/'stdout_v1.txt');stderr=checked(A/'stderr_v1.txt');good('210_stdout_cases_empty_stderr_match_exit_record',stdout[1].decode().splitlines()==['SCORED '+f+' '+cid for f,cid in keys] and stderr[1]==b'' and stdout[0]['sha256']==result['stdout_sha256'] and stderr[0]['sha256']==result['stderr_sha256'])
  env=js(O/'execution_environment.json');good('fixed_CPU_environment_identity',env['packages']==q['environment']['packages'] and env['python']==q['environment']['python_version'] and env['executable']==q['environment']['python']['path'] and env['CUDA_VISIBLE_DEVICES']=='' and env['threads']==2 and env['request_sha256']==SHA)
  rows=[json.loads(x) for x in checked(O/'case_metrics.jsonl')[1].decode().splitlines()];lookup={(r['fold'],r['case_id'],r['arm']):r for r in rows};columns=set(rows[0]['metrics'])
  good('ordered1050_unique_case_arm_rows',len(rows)==len(lookup)==1050 and [(r['fold'],r['case_id'],r['arm']) for r in rows]==[(f,c,a) for f,c in keys for a in ALL])
  # Read only already-frozen Native geometry JSON, never prediction/GT arrays.
  root=S.parents[2];predroot=S.parent/'Native_prediction_implementation_v1/resource_rebind_v2/post_prediction_freeze_audit_v1'
  predhash=js(predroot/'hashes_after_result_v1.json');nativepath=predroot/'downloads/output/geometry_summary.jsonl'
  binding=next(r for r in predhash['files'] if r['name']=='geometry_summary.jsonl')
  need(checked(nativepath)[0]['sha256']==binding['sha256'],'F0 Native geometry provenance')
  native={(r['run'],r['case_id']):r for r in map(json.loads,checked(nativepath)[1].decode().splitlines())};need(len(native)==210,'210 F0 summaries')
  for r in rows:
   need(r['source_id']==source_for[r['fold'],r['case_id']] and r['status']=='OK','case source/status');full=r['full_metrics'];need(full['status']=='OK' and full['point_count']==8192,'full metric point budget');verify_P1_row(r,select(full));need(set(r['metrics'])==columns,'fixed metric columns')
   for k,v in r['metrics'].items():need(v is None or (isinstance(v,(int,float)) and math.isfinite(v) and v>=0 and (v<=1 if 'coverage' in k or 'outlier' in k else True)),'metric domain')
   if r['arm']=='GT_8192':equal(r['metrics']['CD_L1_mm'],0.)
   if r['arm']=='F0':
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
  good('all1050_selected_metrics_pose_stage_risk_GT_and_F0_Native_summaries')
  risks=js(O/'risk_transitions.json')
  for f in ids:
   for pair in PAIRS:equal(risks[f][pair[1]+'_minus_'+pair[0]],risk_table([r for r in rows if r['fold']==f],ids[f],pair),'risk '+f+str(pair))
  good('six_risk_tables_all_cases_defects_new_rescued_independently_recomputed')
  groups={}
  for r in rows:groups.setdefault((r['fold'],r['source_id'],r['arm']),[]).append(r)
  expected=[]
  for (f,sid,arm),part in sorted(groups.items()):
   need(len(part)==5 and {r['case_id'].split('__',2)[-1] for r in part}==DEFECTS,'five fixed defects/source');expected.append(dict(fold=f,source_id=sid,arm=arm,case_count=5,invalid_predictions=0,metrics={k:mean([r['metrics'][k] for r in part]) if all(r['metrics'][k] is not None for r in part) else None for k in columns}))
  equal(js(O/'source_metrics.json'),expected);good('210_independently_recomputed_source_means',len(expected)==210)
  bs={(r['fold'],r['source_id'],r['arm']):r['metrics'] for r in expected};comparison=js(O/'paired_comparison.json');rankings=js(O/'regression_rankings.json');defects={};all_deltas=[]
  good('three_fixed_descriptive_comparison_identities',comparison['status']=='F0_T0_M0_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS' and comparison['fixed_comparisons']==['F0_minus_M0','F0_minus_T0','M0_minus_T0'] and comparison['primary_metric']=='A1 area-weighted E_P95 mm' and comparison['case_count']==210 and comparison['model_predictions']==630 and comparison['controls']==420 and comparison['request_sha256']==SHA)
  for f in ids:
   defects[f]={}
   for pair in PAIRS:
    label=pair[1]+'_minus_'+pair[0];summ=comparison['comparison'][f][label];need(summ['baseline_arm']==pair[0] and summ['candidate_arm']==pair[1] and summ['source_count']==21 and summ['defects_per_source']==5 and all(summ[k] for k in ['no_bootstrap','no_p_values','no_formal_gate','training_randomness_not_estimated']),'pair identity/source unit')
    for key in columns:
     a=[bs[f,s,pair[0]][key] for s in sources[f]];b=[bs[f,s,pair[1]][key] for s in sources[f]];d=[y-x if x is not None and y is not None else None for x,y in zip(a,b)];z=summ['metrics'][key];need(z['pair_count']==21 and z['undefined_pairs']==d.count(None),'retained pairs');equal(z['source_deltas'],[dict(source_id=s,delta=v) for s,v in zip(sources[f],d)])
     if None not in d:
      need(z['status']=='OK','summary status')
      for k,v in dict(mean_a=mean(a),mean_b=mean(b),mean_delta_b_minus_a=mean(d),median_delta=statistics.median(d),min_delta=min(d),max_delta=max(d)).items():equal(z[k],v,'summary '+f+label+key+k)
      direction='descriptive_not_ordered' if key=='radius_gyration_ratio' else 'positive' if 'coverage' in key else 'negative';need(z['improvement_direction']==direction,'improvement direction')
      if direction!='descriptive_not_ordered':
       need(z['improved_sources']==sum(x>0 if direction=='positive' else x<0 for x in d) and z['worse_sources']==sum(x<0 if direction=='positive' else x>0 for x in d) and z['tied_sources']==d.count(0),'winloss counts');ranked=sorted(z['source_deltas'],key=lambda r:(r['delta'] is None,(-r['delta'] if direction=='negative' else r['delta']) if r['delta'] is not None else 0,r['source_id']));equal(rankings[f][label]['source_rankings'][key],ranked)
     else:need(z['status']=='UNDEFINED_NONFINITE_PAIRS_RETAINED' and z['mean_delta_b_minus_a'] is None,'undefined retained')
    cd=[]
    for cid in sorted(ids[f]):
     a,b=[lookup[f,cid,arm] for arm in pair];cd.append(dict(fold=f,case_id=cid,source_id=a['source_id'],defect=cid.split('__',2)[-1],metrics={k:b['metrics'][k]-a['metrics'][k] if a['metrics'][k] is not None and b['metrics'][k] is not None else None for k in columns},comparison=label))
    equal(rankings[f][label]['case_deltas'],cd);all_deltas+=cd;defects[f][label]={}
    for defect in sorted(DEFECTS):
     part=[r for r in cd if r['defect']==defect];need(len(part)==21,'21 sources/defect');defects[f][label][defect]=dict(paired_cases=21,mean_deltas={k:mean([r['metrics'][k] for r in part]) if all(r['metrics'][k] is not None for r in part) else None for k in columns})
  equal(js(O/'defect_comparison.json'),defects);good('all_six_source_pair_statistics_rankings630_case_deltas_and30_defect_summaries')
  csv_check(O/'case_metrics.csv',rows);csv_check(O/'source_metrics.csv',expected);csv_check(O/'paired_case_deltas.csv',all_deltas);good('three_CSV_JSON_values_and_exact_order')
  p1=root/'outputs/cranial_bcsp_mamba_p1_20261104'
  for f,sub in [('C','paired_development_evaluator_v2'),('D','FoldD_paired_development_entry_v1')]:
   prior=js(p1/sub/'post_scoring_freeze_audit_v1/audit_report_v1.json');need(prior['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS','prior formal P1 audit');binding=next(r for r in prior['output_manifest'] if Path(r['path']).name=='case_metrics.jsonl');raw=checked(binding['path'],binding)[1];old={(r['case_id'],r['arm']):r for r in map(json.loads,raw.decode().splitlines())}
   for cid in ids[f]:
    for arm in ['T0','M0','Nop_D','GT_8192']:
     for k in ['metrics','full_metrics','position_shape','risk_labels','stage_geometry']:equal(lookup[f,cid,arm][k],old[cid,arm][k],'frozen M0/control crosscheck '+f+cid+arm+k)
  good('all840_T0_M0_and_shared_control_rows_equal_frozen_P1_scores')
  need(all(complete[k]==0 for k in ['server_operations','model_imports','forward_calls','bootstrap']),'no extra model/statistical execution')
  good('wall_and_final_output_within_frozen_limits',complete['seconds']<=q['limits']['wall_seconds'] and result['elapsed_seconds']<=18030 and sum(p.stat().st_size for p in O.iterdir())<=q['limits']['output_bytes'])
  need([sum(r['stage_geometry']['coarse']['tensor_saved'] for r in rows if r['arm']==arm) for arm in ARMS]==[12,12,210],'coarse availability')
  good('actual_coarse_availability_12_12_210_not_misrepresented')
  need(inv['argv']==[q['environment']['python']['path'],*q['environment']['flags'],q['implementation']['scorer']['path'],'--request',str(S/'local_scoring_execution_request_v1.json'),'--request-sha256',SHA,'--authorization',str(A/'score_authorization_v1.json'),'--authorization-sha256',checked(A/'score_authorization_v1.json')[0]['sha256']],'actual argv')
  good('actual_process_argv_matches_frozen_request_and_authorization')
  good('stable_output_and_all_read_content_fingerprints_atime_excluded',tree(O)==before and all(stamp(Path(p))==v for p,v in STAMPS.items()))
  report=dict(status='FORMAL_F0_T0_M0_POST_SCORING_FREEZE_AUDIT_PASS',checks=CHECKS,checks_passed=len(CHECKS),request_sha256=SHA,counts=dict(cases=210,sources=42,model_scores=630,controls=420,case_rows=1050,source_rows=210,source_pair_summaries=6,case_pair_deltas=630),exit_code=0,output_manifest=[r for r in MANIFEST if Path(r['path']).parent==O],all_read_file_manifest=MANIFEST,read_bytes=READ,seconds=time.monotonic()-START,independent_aggregation_recomputed=True,geometry_distance_recomputed=False,arrays_decoded=False,scoring_rerun=False,model_imports=0,GPU_calls=0,server_operations=0,formal_gate=False,limitations=['Independent saved-metric/pose/aggregation checks; nearest-neighbour geometry distances not recomputed','Single seed/fold, repeated development data; no significance/bootstrap/clinical or formal gate claim','Package identity from frozen Python binary/version records; dependency binary tree not rescanned','RSS guard samples were not persisted as a resource time series; peak RSS cannot be independently reconstructed','Only common12 baseline cases/arm have actual coarse tensors; F0 has210; do not imply complete paired coarse tensors'])
 except BaseException as exc:
  report=dict(status='FORMAL_POST_SCORING_FREEZE_AUDIT_FAILED_STOP_NO_RETRY',passed_checks=CHECKS,error=repr(exc),read_bytes=READ,seconds=time.monotonic()-START,scoring_rerun=False)
 with (F/'audit_report_v1.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2,allow_nan=False)
 print(json.dumps({k:v for k,v in report.items() if k not in {'all_read_file_manifest','output_manifest'}}))
 if report['status']!='FORMAL_F0_T0_M0_POST_SCORING_FREEZE_AUDIT_PASS':raise SystemExit(1)
if __name__=='__main__':main()
