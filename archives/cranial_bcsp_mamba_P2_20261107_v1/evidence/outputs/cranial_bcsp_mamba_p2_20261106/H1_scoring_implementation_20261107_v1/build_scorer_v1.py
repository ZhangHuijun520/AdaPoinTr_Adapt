"""Local source derivation only; no scoring or imports of geometry payloads."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
P1=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104'
parent=P1/'paired_development_evaluator_v2/scoring_implementation_v1/bcsp_p1_pair_score_v1.py'
s=parent.read_text(encoding='utf-8')
parent_sha=hashlib.sha256(parent.read_bytes()).hexdigest()
s=s.replace('M0','M_H1').replace('T0','M0')
s=s.replace("Path(__file__).resolve().parents[3]/'cranial_bcsp_geov1_20261024", "Path(__file__).resolve().parents[2]/'cranial_bcsp_geov1_20261024")
s=s.replace('CPU-only P1','CPU-only P2 H1/M0 twofold')
def replace_fn(s,name,new):
 n=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name==name)
 lines=s.splitlines(keepends=True);return ''.join(lines[:n.lineno-1])+new+'\n\n'+''.join(lines[n.end_lineno:])
s=replace_fn(s,'authorize','''def authorize(request_record,authorization_record):
 plan=json.loads(check(request_record).read_bytes());auth=json.loads(check(authorization_record).read_bytes())
 require(plan['schema']=='bcsp-p2-H1-M0-twofold-local-scoring-request-v1' and plan['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and plan['execution_authorized'] is False,'pending scoring request')
 require(plan['counts']==dict(unique_cases=210,sources=42,model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168),'exact scoring scope')
 require(set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-p2-H1-M0-score-authorization-v1' and auth['request_sha256']==request_record['sha256'] and auth['explicit_user_authorization'] is True and bool(auth['user_authorization_text'].strip()),'separate score authorization')
 return plan''')
s=replace_fn(s,'validate_index','''def validate_index(index,references,score_index):
 cases=score_index['cases'];require(index['schema']=='bcsp-p2-H1-twofold-development-index-v1' and [r['label'] for r in index['runs']]==['C_M_H1','D_M_H1'],'twofold H1 index')
 require(score_index['schema']=='bcsp-p2-H1-M0-twofold-score-index-candidate-v1' and len(cases)==210 and len(index['inputs'])==210,'210 cases')
 refmap={r['case_id']:r for r in references['cases']};require(len(refmap)==len(references['cases'])==210,'unique210references')
 lookup={r['case_id']:r for r in index['inputs']};require(len(lookup)==210,'unique210inputs')
 for f in ['C','D']:
  run=next(r for r in index['runs'] if r['fold']==f);part=[c for c in cases if c['fold']==f]
  require(len(part)==105 and [c['case_id'] for c in part]==run['dev_case_ids'] and len(run['dev_sources'])==21 and not set(run['train_sources'])&set(run['dev_sources']),'ordered105 and source separation')
  require({c['source_id'] for c in part}==set(run['dev_sources']),'source identity')
  for source in run['dev_sources']:require({c['case_id'].split('__',2)[-1] for c in part if c['source_id']==source}==DEFECTS,'five defects/source')
 for c in cases:
  a=lookup[c['case_id']];ref=refmap[c['case_id']]
  require(all(c[k]==a[k]==ref[k] for k in ['case_id','source_id','fold','normalization','target_array_sha256']),'shared frame/target')
  require(c['normalization_source']==a['normalization_source']=='defective_bbox','D-only frame')
  require(c['reference']=={k:ref[k] for k in ['path','bytes','sha256']} and all(c['point_file'][k]==a['input'][k] for k in ['bytes','sha256']),'reference/point binding')
 require(len({c['case_id'] for c in cases})==210 and len({c['source_id'] for c in cases})==42,'unique210/42')
 return index['runs'],index['inputs'],cases''')
s=replace_fn(s,'validate_archive','''def validate_archive(tar,index,inner_sha256,coarse_cases,kind):
 members=tar.getmembers();names=[m.name for m in members]
 expected=['predictions/'+r['run']+'__'+r['case_id']+'.npz' for r in index['inputs']]+['inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl']
 require(len(members)==len(set(names))==215 and names==expected and all(m.isfile() and 0<m.size<=4194304 for m in members) and sum(m.size for m in members)<=67108864,'exact215 bounded archive')
 records=[json.loads(x) for x in tar.extractfile('inference_manifest.jsonl').read().splitlines()];claims=[json.loads(x) for x in tar.extractfile('forward_attempts.jsonl').read().splitlines()];geometry=[json.loads(x) for x in tar.extractfile('geometry_summary.jsonl').read().splitlines()]
 done=json.loads(tar.extractfile('inference_complete.json').read());runs={r['label']:r for r in index['runs']}
 status='P2_H1_TWOFOLD_210_FORWARD_COMPLETE' if kind=='H1' else 'P1_PAIR_210_FORWARD_COMPLETE'
 require(done['status']==status and done['forwards']==210 and done['request_sha256']==inner_sha256 and all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']),'prediction execution identity')
 require([r['run'] for r in done['models']]==list(runs),'exact model labels')
 for r in done['models']:
  require(r['forwards']==105 and len(r['state_before'])==64 and r['state_before']==r['state_after'] and set(r['RNG_before'])=={'CPU','CUDA','Python','numpy'} and r['RNG_before']==r['RNG_after'] and all(r['RNG_before'].values()),'state/RNG invariants')
  require(r['mode']=='eval_inference_mode' and r['BNCal']==r['optimizer']==r['backward']==0,'eval-only')
 require(len(records)==len(claims)==len(geometry)==210 and [r['forward_index'] for r in records]==list(range(1,211)) and len({(r['run'],r['case_id']) for r in records})==210,'all210 distinct')
 lookup={}
 for k,(r,i,c,g) in enumerate(zip(records,index['inputs'],claims,geometry),1):
  require(all(r[key]==i[key] for key in ['run','case_id','source_id','fold','n_input','normalization']) and r['n_output']==8192 and r['input_sha256']==i['input']['sha256'] and r['checkpoint_sha256']==runs[i['run']]['checkpoint']['sha256'],'prediction provenance')
  require(c==dict(forward_index=k,run=r['run'],case_id=r['case_id'],status='CLAIMED_BEFORE_FORWARD'),'claim order')
  require(g['run']==r['run'] and g['case_id']==r['case_id'] and g['frame']=='native_D_only_normalized_no_GT','same-forward geometry')
  require(r['prediction']['name']=='predictions/'+r['run']+'__'+r['case_id']+'.npz','exact filename')
  require(r['fold'] in coarse_cases and len(coarse_cases[r['fold']])==(7 if r['fold']=='C' else 5),'fixed coarse representatives')
  if kind=='H1' or r['run'].endswith('_M0'):
   arm='M_H1' if kind=='H1' else 'M0'
   lookup[(r['fold'],arm,r['case_id'])]=dict(r,geometry=g,coarse_expected=r['case_id'] in coarse_cases[r['fold']],archive_key=kind)
 return lookup''')
# Minimal adaptations to existing metric/geometry calculation; no arithmetic changes.
s=s.replace('def score_case(tar,lookup,case,guard):','def score_case(tars,lookup,case,guard):')
s=s.replace("record=lookup[('C_'+arm,case['case_id'])];arrays=load_prediction_arrays(tar,record)","record=lookup[(case['fold'],arm,case['case_id'])];arrays=load_prediction_arrays(tars[record['archive_key']],record)")
s=s.replace("rows.append(dict(fold='C',case_id=case['case_id']","rows.append(dict(fold=case['fold'],case_id=case['case_id']")
# Aggregate separately by fold to retain the inherited five-defect source arithmetic.
s=s.replace("require(row['fold']=='C' and row['arm']", "require(row['fold'] in ('C','D') and row['arm']")
s=s.replace("groups.setdefault((row['source_id'],row['arm']),[])","groups.setdefault((row['fold'],row['source_id'],row['arm']),[])")
s=s.replace('for (source,arm),part in sorted(groups.items()):','for (fold,source,arm),part in sorted(groups.items()):')
s=s.replace("result.append(dict(fold='C',source_id=source", "result.append(dict(fold=fold,source_id=source")
s=s.replace("result.append(dict(fold='C',case_id=cid", "result.append(dict(fold=a['fold'],case_id=cid")
s=replace_fn(s,'run_scoring','''def run_scoring(plan,index,cases,out,archives,request_sha256,guard,start):
 from contextlib import ExitStack
 rows=[];full=out/'case_metrics.jsonl';full.open('x').close()
 with ExitStack() as stack:
  tars={k:stack.enter_context(tarfile.open(path,'r:gz')) for k,path in archives.items()};lookup={}
  for k,spec in plan['archive_inputs'].items():
   predindex=json.loads(check(spec['prediction_index']).read_bytes());pro=json.loads(check(spec['prediction_protocol']).read_bytes())
   coarse=pro['coarse_tensor_cases_by_fold'] if k=='H1' else {spec['fold']:pro['coarse_tensor_cases']}
   part=validate_archive(tars[k],predindex,spec['prediction_request_sha256'],coarse,k)
   require(not set(lookup)&set(part),'duplicate model/case across archives');lookup.update(part)
  require(len(lookup)==420 and all((c['fold'],arm,c['case_id']) in lookup for c in cases for arm in ARMS),'exact420model lookups')
  for case in cases:
   part=score_case(tars,lookup,case,guard);rows.extend(part)
   with full.open('a',encoding='utf-8') as f:
    for row in part:f.write(json.dumps(metric.json_safe(row),allow_nan=False)+'\\n')
   print('SCORED',case['fold'],case['case_id'],flush=True)
 require(len(rows)==840,'420 models plus420 shared controls')
 sources=aggregate_source(rows);require(len(sources)==168,'42 sources times4 arms')
 comparison={};risks={};defects={};deltas=[];rankings={}
 for fold in ['C','D']:
  selected=[r for r in rows if r['fold']==fold];ss=[r for r in sources if r['fold']==fold]
  require(len(selected)==420 and len(ss)==84,'perfold420rows84sources')
  comparison[fold]=paired_summary(ss);risks[fold]=risk_transitions(selected);defects[fold]=defect_summary(selected)
  differences=case_differences(selected);deltas.extend(differences)
  rankings[fold]=dict(source_rankings={k:sorted(v['source_deltas'],key=lambda r:(r['delta'] is None,(-r['delta'] if v['improvement_direction']=='negative' else r['delta']) if r['delta'] is not None else 0,r['source_id'])) for k,v in comparison[fold]['metrics'].items() if v['improvement_direction']!='descriptive_not_ordered'},case_deltas=differences)
 emit(out/'source_metrics.json',sources);emit(out/'paired_comparison.json',dict(status='TWOFOLD_SINGLE_SEED_DESCRIPTIVE_PAIRED_COMPARISON',case_count=210,model_predictions=420,controls=420,comparison=comparison,request_sha256=request_sha256))
 emit(out/'defect_comparison.json',defects);emit(out/'regression_rankings.json',rankings);emit(out/'risk_transitions.json',risks)
 csv_rows(out/'case_metrics.csv',rows);csv_rows(out/'source_metrics.csv',sources);csv_rows(out/'paired_case_deltas.csv',deltas)
 guard()
 for k,path in archives.items():require(digest(path)==plan['archive_inputs'][k]['archive']['sha256'],'archive stable after scoring')
 emit(out/'completion.json',dict(status='LOCAL_H1_M0_TWOFOLD_CPU_SCORING_COMPLETE',model_predictions=420,controls=420,score_rows=840,source_rows=168,seconds=time.monotonic()-start,archive_sha256={k:spec['archive']['sha256'] for k,spec in plan['archive_inputs'].items()},request_sha256=request_sha256,server_operations=0,model_imports=0,forward_calls=0,bootstrap=0,formal_gate=False))
 return rows''')
s=s.replace("archive=check(plan['downloaded_prediction_archive'])\n for r in plan['download_sidecars']:check(r)","archives={k:check(v['archive']) for k,v in plan['archive_inputs'].items()}\n for v in plan['archive_inputs'].values():\n  for r in v['sidecars']:check(r)")
s=s.replace("out==Path(__file__).resolve().parent.parent/'paired_scores_v1'", "out==Path(__file__).resolve().parent/'unified_scores_v1'")
s=s.replace('rows=run_scoring(plan,index,cases,out,archive,args.request_sha256,guard,start)','rows=run_scoring(plan,index,cases,out,archives,args.request_sha256,guard,start)')
ast.parse(s)
assert "lookup[('C_'" not in s and "fold='C'" not in s
with (HERE/'bcsp_p2_h1_M0_twofold_score_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
with (HERE/'source_derivation_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(parent=str(parent),parent_sha256=parent_sha,new_source_sha256=hashlib.sha256(s.encode()).hexdigest(),metric_core_unchanged=True,scoring_executed=False),f,indent=2)
print('Isolated scorer created; not imported or executed.')
