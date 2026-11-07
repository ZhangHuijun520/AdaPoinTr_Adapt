"""Dedicated3-arm CPU scorer derivative; metric module and numerical/risk definitions unchanged."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;H=S.parent/'H1_scoring_implementation_20261107_v1';p=H/'bcsp_p2_h1_M0_twofold_score_v1.py';src=p.read_text(encoding='utf-8');tree=ast.parse(src);repl={}
repl['validate_index']='''def validate_index(index,references,score_index):
 cases=score_index['cases'];require(index['schema']=='bcsp-p2-H2-fourmodel-development-index-v1' and [r['label'] for r in index['runs']]==['C_AUX','C_COUPLE','D_AUX','D_COUPLE'],'fourmodel H2 index')
 require(score_index['schema']=='bcsp-p2-H2-M0-twofold-score-index-candidate-v1' and len(cases)==210 and len(index['inputs'])==420,'210unique cases420 H2 rows')
 refmap={r['case_id']:r for r in references['cases']};require(len(refmap)==len(references['cases'])==210,'unique210references')
 lookup={}
 for r in index['inputs']:
  if r['case_id'] in lookup:require(all(r[k]==lookup[r['case_id']][k] for k in ['case_id','source_id','fold','normalization','normalization_source','target_array_sha256','input']),'same-fold H2 shared input')
  else:lookup[r['case_id']]=r
 require(len(lookup)==210 and len({(r['run'],r['case_id']) for r in index['inputs']})==420,'exact paired H2 identities')
 for f in ['C','D']:
  part=[c for c in cases if c['fold']==f]
  for mode in ['AUX','COUPLE']:
   run=next(r for r in index['runs'] if r['label']==f+'_'+mode);rows=[r for r in index['inputs'] if r['run']==run['label']]
   require(run['fold']==f and run['mode']==mode and run['H2']['mode']==mode and len(rows)==105 and [r['case_id'] for r in rows]==[c['case_id'] for c in part]==run['dev_case_ids'],'ordered105 each arm/fold')
   require(len(run['dev_sources'])==21 and len(run['train_sources'])==63 and not set(run['train_sources'])&set(run['dev_sources']) and {c['source_id'] for c in part}==set(run['dev_sources']),'source identity and split')
   require(all(r['H2_mode']==mode and r['fold']==f for r in rows),'row mode/fold')
   for source in run['dev_sources']:require({c['case_id'].split('__',2)[-1] for c in part if c['source_id']==source}==DEFECTS,'five defects/source')
 for c in cases:
  a=lookup[c['case_id']];ref=refmap[c['case_id']]
  require(all(c[k]==a[k]==ref[k] for k in ['case_id','source_id','fold','normalization','target_array_sha256']),'shared frame/target')
  require(c['normalization_source']==a['normalization_source']=='defective_bbox','D-only frame')
  require(c['reference']=={k:ref[k] for k in ['path','bytes','sha256']} and all(c['point_file'][k]==a['input'][k] for k in ['bytes','sha256']),'reference/point binding')
 require(len({c['case_id'] for c in cases})==210 and len({c['source_id'] for c in cases})==42,'unique210/42')
 return index['runs'],index['inputs'],cases
'''
archive=ast.get_source_segment(src,next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_archive'))
archive=archive.replace("len(members)==len(set(names))==215","len(members)==len(set(names))==(425 if kind=='H2' else 215)").replace("sum(m.size for m in members)<=67108864","sum(m.size for m in members)<=(134217728 if kind=='H2' else 67108864)").replace('exact215 bounded archive','exact bounded H2 or baseline archive')
archive=archive.replace("status='P2_H1_TWOFOLD_210_FORWARD_COMPLETE' if kind=='H1' else 'P1_PAIR_210_FORWARD_COMPLETE'","expected_count=420 if kind=='H2' else 210\n status='P2_H2_FOURMODEL_420_NATIVE_FORWARD_COMPLETE' if kind=='H2' else 'P1_PAIR_210_FORWARD_COMPLETE'")
archive=archive.replace("done['forwards']==210","done['forwards']==expected_count").replace("len(records)==len(claims)==len(geometry)==210","len(records)==len(claims)==len(geometry)==expected_count").replace("list(range(1,211))","list(range(1,expected_count+1))").replace("len({(r['run'],r['case_id']) for r in records})==210","len({(r['run'],r['case_id']) for r in records})==expected_count")
archive=archive.replace("len(coarse_cases[r['fold']])==(7 if r['fold']=='C' else 5)","len(coarse_cases[r['fold']])==(5 if kind=='H2' else (7 if r['fold']=='C' else 5))")
archive=archive.replace("if kind=='H1' or r['run'].endswith('_M0'):","if kind=='H2' or r['run'].endswith('_M0'):").replace("arm='M_H1' if kind=='H1' else 'M0'","arm='H2_'+runs[r['run']]['mode'] if kind=='H2' else 'M0'\n   if kind=='H2':\n    mode=runs[r['run']]['mode'];h=g['H2'];require(mode in ['AUX','COUPLE'] and h['mode']==mode and h['condition_override'] is None and h['GT_read'] is False and h['loss_calls']==0,'Native H2 only')")
archive=archive.replace("return lookup","require(len(lookup)==(420 if kind=='H2' else 105),'exact selected model count')\n return lookup")
repl['validate_archive']=archive+'\n'
# Generalize only pair labels/count selectors; numeric formulas remain the same.
for name in ['paired_summary','case_differences','defect_summary','risk_transitions']:
 n=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name);f=ast.get_source_segment(src,n)
 signature={'paired_summary':'sources','case_differences':'rows','defect_summary':'rows','risk_transitions':'rows'}[name]
 f=f.replace('def '+name+'('+signature+'):',"def "+name+"("+signature+",pair):\n require(tuple(pair) in PAIRS,'fixed comparison pair')")
 f=f.replace("r['arm'] in ARMS","r['arm'] in pair").replace("for a in ARMS","for a in pair").replace("for arm in ARMS","for arm in pair").replace("lookup[(s,'M0')]","lookup[(s,pair[0])]").replace('ARMS[1]','pair[1]')
 f=f.replace("case_differences(rows)","case_differences(rows,pair)")
 f=f.replace('mean_delta_M_H1_minus_M0','mean_delta_b_minus_a').replace('mean_M_H1','mean_b').replace('mean_M0','mean_a')
 f=f.replace("M0=a,M_H1=b","baseline_arm=pair[0],candidate_arm=pair[1],baseline=a,candidate=b").replace("M0_count=sum(r['M0'] for r in records),M_H1_count=sum(r['M_H1'] for r in records)","baseline_arm=pair[0],candidate_arm=pair[1],baseline_count=sum(r['baseline'] for r in records),candidate_count=sum(r['candidate'] for r in records)")
 repl[name]=f+'\n'
repl['run_scoring']='''def run_scoring(plan,index,cases,out,archives,request_sha256,guard,start):
 from contextlib import ExitStack
 rows=[];full=out/'case_metrics.jsonl';full.open('x').close()
 with ExitStack() as stack:
  tars={k:stack.enter_context(tarfile.open(path,'r:gz')) for k,path in archives.items()};lookup={}
  for k,spec in plan['archive_inputs'].items():
   predindex=json.loads(check(spec['prediction_index']).read_bytes());pro=json.loads(check(spec['prediction_protocol']).read_bytes())
   coarse=pro['coarse_tensor_cases_by_fold'] if k=='H2' else {spec['fold']:pro['coarse_tensor_cases']}
   part=validate_archive(tars[k],predindex,spec['prediction_request_sha256'],coarse,k)
   require(not set(lookup)&set(part),'duplicate model/case across archives');lookup.update(part)
  require(len(lookup)==630 and all((c['fold'],arm,c['case_id']) in lookup for c in cases for arm in ARMS),'exact630model lookups')
  for case in cases:
   part=score_case(tars,lookup,case,guard);rows.extend(part)
   with full.open('a',encoding='utf-8') as f:
    for row in part:f.write(json.dumps(metric.json_safe(row),allow_nan=False)+'\\n')
   print('SCORED',case['fold'],case['case_id'],flush=True)
 require(len(rows)==1050,'630 models plus420 shared controls')
 sources=aggregate_source(rows);require(len(sources)==210,'42 sources times5 arms')
 comparison={};risks={};defects={};deltas=[];rankings={}
 for fold in ['C','D']:
  selected=[r for r in rows if r['fold']==fold];ss=[r for r in sources if r['fold']==fold];require(len(selected)==525 and len(ss)==105,'perfold525rows105sources')
  comparison[fold]={};risks[fold]={};defects[fold]={};rankings[fold]={}
  for pair in PAIRS:
   key=pair[1]+'_minus_'+pair[0];summary=paired_summary(ss,pair);summary.update(baseline_arm=pair[0],candidate_arm=pair[1])
   comparison[fold][key]=summary;risks[fold][key]=risk_transitions(selected,pair);defects[fold][key]=defect_summary(selected,pair)
   differences=case_differences(selected,pair)
   for row in differences:row.update(comparison=key)
   deltas.extend(differences)
   rankings[fold][key]=dict(source_rankings={k:sorted(v['source_deltas'],key=lambda r:(r['delta'] is None,(-r['delta'] if v['improvement_direction']=='negative' else r['delta']) if r['delta'] is not None else 0,r['source_id'])) for k,v in summary['metrics'].items() if v['improvement_direction']!='descriptive_not_ordered'},case_deltas=differences)
 emit(out/'source_metrics.json',sources);emit(out/'paired_comparison.json',dict(status='H2_THREE_ARM_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS',primary_comparison='H2_COUPLE_minus_H2_AUX',secondary_comparisons=['H2_COUPLE_minus_M0','H2_AUX_minus_M0'],case_count=210,model_predictions=630,controls=420,comparison=comparison,request_sha256=request_sha256))
 emit(out/'defect_comparison.json',defects);emit(out/'regression_rankings.json',rankings);emit(out/'risk_transitions.json',risks)
 csv_rows(out/'case_metrics.csv',rows);csv_rows(out/'source_metrics.csv',sources);csv_rows(out/'paired_case_deltas.csv',deltas)
 guard()
 for k,path in archives.items():require(digest(path)==plan['archive_inputs'][k]['archive']['sha256'],'archive stable after scoring')
 emit(out/'completion.json',dict(status='LOCAL_H2_M0_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE',model_predictions=630,controls=420,score_rows=1050,source_rows=210,seconds=time.monotonic()-start,archive_sha256={k:spec['archive']['sha256'] for k,spec in plan['archive_inputs'].items()},request_sha256=request_sha256,server_operations=0,model_imports=0,forward_calls=0,bootstrap=0,formal_gate=False))
 return rows
'''
lines=src.splitlines(keepends=True)
for n in sorted([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in repl],key=lambda n:n.lineno,reverse=True):lines[n.lineno-1:n.end_lineno]=[repl[n.name]]
src=''.join(lines).replace("ARMS=['M0','M_H1']","ARMS=['M0','H2_AUX','H2_COUPLE']\nPAIRS=[('H2_AUX','H2_COUPLE'),('M0','H2_COUPLE'),('M0','H2_AUX')]")
src=src.replace('bcsp-p2-H1-M0-twofold-local-scoring-request-v1','bcsp-p2-H2-M0-three-arm-local-scoring-request-v1').replace('bcsp-p2-H1-M0-score-authorization-v1','bcsp-p2-H2-M0-score-authorization-v1').replace('model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168','model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210')
src=src.replace('mean_delta_M_H1_minus_M0','mean_delta_b_minus_a').replace('mean_M_H1','mean_b').replace('mean_M0','mean_a')
src=src.replace('CPU-only P2 H1/M0 twofold M0/M_H1 paired scoring.','CPU-only H2/M0 twofold three-arm scoring; Native predictions only.')
# Same-world geometry observations are descriptive and do not alter the frozen metric/risk values.
anchor="   stage=stage_geometry(record['geometry'],cloud,gt,case['normalization'],coarse)"
assert src.count(anchor)==1;src=src.replace(anchor,anchor+"\n   if arm.startswith('H2_'):stage['H2']=h2_offline_geometry(record['geometry']['H2'],gt,case['normalization'],pose=None)")
addition='''def h2_offline_geometry(summary,gt,normalization,pose=None):
 mode=summary['mode'];require(mode in ['AUX','COUPLE'] and summary['condition_override'] is None and summary['GT_read'] is False and summary['loss_calls']==0,'Native H2 geometry provenance')
 require(len(summary['delta'])==len(summary['scale'])==1,'one native condition')
 scale=float(normalization['scale']);center=np.asarray(normalization['center'],np.float64);rg=float(np.sqrt(((gt-gt.mean(0))**2).sum(1).mean()))
 raw_r=float(summary['raw']['radius'])*scale;used_r=float(summary['used']['radius'])*scale;delta=float(summary['delta'][0]);s=float(summary['scale'][0])
 require(rg>0 and raw_r>0 and used_r>0 and np.isfinite([rg,raw_r,used_r,delta,s]).all(),'finite H2 offline moments')
 if mode=='AUX':require(s==1 and summary['raw']==summary['used'],'AUX identity')
 else:
  expected=float(np.exp(np.log(1.25)*np.tanh(delta/np.log(1.25))))
  require(np.isclose(s,expected,rtol=2e-6,atol=1e-6) and .8-1e-6<=s<=1.25+1e-6 and np.isclose(used_r,raw_r*s,rtol=2e-6,atol=1e-6),'fixed COUPLE formula')
  require(np.allclose(summary['raw']['centroid'],summary['used']['centroid'],rtol=2e-6,atol=1e-6),'coarse center invariant')
 target=float(np.log(rg)-np.log(raw_r))
 return dict(mode=mode,delta=delta,scale=s,GT_radius_mm=rg,raw_radius_mm=raw_r,used_radius_mm=used_r,raw_abs_log_radius_error=abs(target),used_abs_log_radius_error=abs(float(np.log(rg)-np.log(used_r))),residual_target=target,abs_delta_target_error=abs(delta-target),raw_centroid_offset_mm=float(np.linalg.norm(np.asarray(summary['raw']['centroid'])*scale+center-gt.mean(0))),used_centroid_offset_mm=float(np.linalg.norm(np.asarray(summary['used']['centroid'])*scale+center-gt.mean(0))),GT_used_only_offline=True,not_a_shape_or_interface_benefit_claim=True)

'''
src=src.replace('def score_case(',addition+'def score_case(');ast.parse(src)
with (S/'bcsp_p2_h2_M0_three_arm_score_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(src)
with (S/'source_derivation_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(parent=str(p.absolute()),parent_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),scorer_sha256=hashlib.sha256(src.encode()).hexdigest(),metric_source_unchanged=True,model_arms=['M0','H2_AUX','H2_COUPLE'],pairs=[['H2_AUX','H2_COUPLE'],['M0','H2_COUPLE'],['M0','H2_AUX']]),f,indent=2)
print('H2_THREE_ARM_SCORER_STATIC_PARSE_PASS')
