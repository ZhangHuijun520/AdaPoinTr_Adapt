"""CPU-only paired-sampler scoring. Main requires a separately hash-authorized request."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2'
import argparse,csv,hashlib,io,json,sys,tarfile,time
from pathlib import Path
import importlib.metadata as md
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import numpy as np
import psutil
import bcsp_eval_metrics_v1 as metric
ARMS=['Euclidean_elimination','surface_graph']
CONTROLS=['Nop_D_Euclidean_elimination','Nop_D_surface_graph','GT_8192']
DEFECTS={'bilateral','frontoorbital','parietotemporal','random_1','random_2'}

def require(ok,message):
 if not ok:raise ValueError(message)
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def check(record):
 p=Path(record['path']);require(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file(),'bound regular path: '+str(p))
 require(p.stat().st_size==record['bytes'] and digest(p)==record['sha256'],'bound bytes/hash: '+str(p));return p
def emit(path,value):
 with Path(path).open('x',encoding='utf-8') as f:json.dump(metric.json_safe(value),f,indent=2,allow_nan=False)
def authorize(request_record,authorization_record):
 plan=json.loads(check(request_record).read_bytes());auth=json.loads(check(authorization_record).read_bytes())
 require(plan['schema']=='bcsp-blue-noise-pair-local-scoring-request-v1' and plan['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and plan['execution_authorized'] is False,'pending paired scoring request')
 require(set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-blue-noise-pair-score-authorization-v1' and auth['request_sha256']==request_record['sha256'] and auth['explicit_user_authorization'] is True and bool(auth['user_authorization_text'].strip()),'separate acyclic scoring authorization')
 return plan

def validate_index(index,references,score_index):
 runs=index['runs'];rows=index['inputs'];cases=score_index['cases']
 require(index['schema']=='bcsp-blue-noise-pair-development-index-v1' and len(runs)==2 and [r['label'] for r in runs]==['C_'+a for a in ARMS] and len(rows)==210,'two arms/210 inputs')
 ids=runs[0]['dev_case_ids'];sources=runs[0]['dev_sources']
 require(len(ids)==len(set(ids))==105 and len(sources)==len(set(sources))==21,'fixed105 cases/21 sources')
 for run in runs:
  part=[r for r in rows if r['run']==run['label']]
  require(run['fold']=='C' and run['n_input']==8192 and run['arm'] in ARMS and run['label']=='C_'+run['arm'] and run['dev_case_ids']==ids and run['dev_sources']==sources and not set(sources)&set(run['train_sources']),'shared Fold C/source exclusion')
  require([r['case_id'] for r in part]==ids,'exact ordered input cases')
  for row in part:require(row['fold']=='C' and row['n_input']==8192 and row['arm']==run['arm'] and row['source_id']=='train:'+row['case_id'].split('__')[1] and row['source_id'] in sources,'row case/source/arm')
 require(references['status']=='FROZEN_EXISTING_FOLD_C_105_REFERENCES' and score_index['schema']=='bcsp-blue-noise-pair-score-case-index-v1','reference/score index schema')
 require([r['case_id'] for r in references['cases']]==[r['case_id'] for r in cases]==ids,'exact105 reference and score cases')
 refmap={r['case_id']:r for r in references['cases']};inputs={(r['case_id'],r['arm']):r for r in rows}
 for case in cases:
  cid=case['case_id'];ref=refmap[cid];require(case['fold']=='C' and case['source_id'] in sources and case['source_id']=='train:'+cid.split('__')[1],'case/source identity')
  require(case['reference']=={k:ref[k] for k in ['path','bytes','sha256']} and all(case[k]==ref[k] for k in ['source_id','normalization','target_array_sha256']),'unchanged fixed reference/GT/frame')
  a,b=[inputs[(cid,arm)] for arm in ARMS]
  require(all(a[k]==b[k]==case[k] for k in ['source_id','normalization','target_array_sha256','common_point_order_sha256']),'paired target/frame/permutation')
  require(set(case['point_files'])==set(ARMS),'two local point files')
  for arm in ARMS:
   i=inputs[(cid,arm)];require(all(case['point_files'][arm][k]==i['input'][k] for k in ['bytes','sha256']),'local/server frozen point bytes identity')
 for source in sources:require({r['case_id'].split('__',2)[-1] for r in cases if r['source_id']==source}==DEFECTS,'five fixed defects per source')
 return runs,rows,cases

def validate_archive(tar,index,inner_sha256):
 members=tar.getmembers();names=[m.name for m in members]
 expected=['predictions/'+r['run']+'__'+r['case_id']+'.npz' for r in index['inputs']]+['inference_manifest.jsonl','inference_complete.json','resources.jsonl']
 require(len(members)==len(set(names))==213 and names==expected and all(m.isfile() and 0<m.size<=4194304 for m in members) and sum(m.size for m in members)<=67108864,'exact ordered213 regular bounded members')
 records=[json.loads(line) for line in tar.extractfile('inference_manifest.jsonl').read().decode().splitlines()]
 done=json.loads(tar.extractfile('inference_complete.json').read());runs={r['label']:r for r in index['runs']}
 require(done['status']=='BLUE_NOISE_PAIR_210_FORWARD_COMPLETE' and done['forwards']==210 and done['request_sha256']==inner_sha256 and all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']),'completed eval-only210 batch')
 require(len(done['models'])==2 and [r['run'] for r in done['models']]==list(runs),'two model completion identities')
 for r in done['models']:
  require(r['forwards']==105 and len(r['state_before'])==64 and r['state_before']==r['state_after'] and r['CPU_rng_before']==r['CPU_rng_after'] and r['CUDA_rng_before']==r['CUDA_rng_after'] and r['Python_numpy_RNG_unchanged'] is True,'state/RNG invariance')
  require(r['mode']=='eval_inference_mode' and r['BNCal']==r['optimizer']==r['backward']==0,'no model updates')
 require(len(records)==210 and [r['forward_index'] for r in records]==list(range(1,211)) and len({(r['run'],r['case_id']) for r in records})==210,'exact210 prediction records')
 for r,i in zip(records,index['inputs']):
  require(all(r[k]==i[k] for k in ['run','case_id','source_id','fold','n_input']) and r['n_output']==8192 and r['input_sha256']==i['input']['sha256'] and r['checkpoint_sha256']==runs[i['run']]['checkpoint']['sha256'],'prediction provenance/order')
  require(r['prediction']['name']=='predictions/'+r['run']+'__'+r['case_id']+'.npz','exact prediction filename')
 return {(r['run'],r['case_id']):r for r in records}

def load_prediction(tar,record):
 blob=tar.extractfile(record['prediction']['name']).read()
 require(len(blob)==record['prediction']['bytes'] and hashlib.sha256(blob).hexdigest()==record['prediction']['sha256'],'prediction bytes/hash')
 with np.load(io.BytesIO(blob),allow_pickle=False) as z:
  require(z.files==['prediction'],'prediction-only schema');p=z['prediction'].copy()
 require(p.shape==(8192,3) and p.dtype==np.float32 and np.isfinite(p).all(),'invalid prediction stops whole batch; no omission')
 return p
def select_metrics(score):
 v=dict(E_P95_mm=score['primary_E_G_P95_mm'],J_P95_mm=score['regions']['A1']['J']['p95_mm'],all_P95_mm=score['regions']['A1']['all']['p95_mm'],CD_L1_mm=score['CD_L1_mm'])
 for region in ['E','J']:
  r=score['regions']['A1'][region]
  v[region+'_mean_mm']=r['mean_mm'];v[region+'_max_mm']=r['max_mm']
  for tau in ['0.5','1.0','2.0']:v[region+'_coverage_'+tau+'mm']=r['coverage'][tau]
  v['A2_'+region+'_P95_mm']=score['regions']['A2'][region]['p95_mm']
 for ref in ['A2','B']:
  r=score['reverse_discrete_reference'][ref];v['reverse_'+ref+'_P95_mm']=r['p95_mm']
  for tau in ['0.5','1.0','2.0']:v['reverse_'+ref+'_outlier_'+tau+'mm']=r['outlier_fraction'][tau]
 v['B_all_P95_mm']=score['regions']['B']['all']['p95_mm'];return v
def score_case(tar,lookup,case,guard):
 with np.load(check(case['reference']),allow_pickle=False) as z:ref={k:z[k] for k in z.files}
 points={}
 for arm in ARMS:
  with np.load(check(case['point_files'][arm]),allow_pickle=False) as z:
   require(set(z.files)=={'partial','implant'},'frozen point schema');points[arm]=dict(partial=z['partial'].copy(),implant=z['implant'].copy())
  for a in points[arm].values():require(a.shape==(8192,3) and a.dtype==np.float32 and np.isfinite(a).all(),'frozen point tensor contract')
 require(np.array_equal(points[ARMS[0]]['implant'],points[ARMS[1]]['implant']),'exact common GT arrays')
 target=points['Euclidean_elimination']['implant'];require(hashlib.sha256(target.tobytes()).hexdigest()==case['target_array_sha256'],'GT array digest')
 gt=metric.world_points(target,case['normalization']);rows=[]
 for arm in ARMS+CONTROLS:
  guard()
  if arm in ARMS:cloud=metric.world_points(load_prediction(tar,lookup[('C_'+arm,case['case_id'])]),case['normalization'])
  elif arm=='GT_8192':cloud=gt
  else:cloud=metric.world_points(points[arm[len('Nop_D_'):]]['partial'],case['normalization'])
  score=metric.score_cloud(cloud,ref,gt);require(score['status']=='OK','invalid score cloud stops batch')
  rows.append(dict(fold='C',case_id=case['case_id'],source_id=case['source_id'],arm=arm,status=score['status'],metrics=select_metrics(score),full_metrics=score))
 return rows

def aggregate_source(rows):
 groups={}
 for row in rows:
  require(row['fold']=='C' and row['arm'] in ARMS+CONTROLS and row['status']=='OK','valid fixed arm/fold/status');groups.setdefault((row['source_id'],row['arm']),[]).append(row)
 result=[]
 for (source,arm),part in sorted(groups.items()):
  require(len(part)==5 and len({r['case_id'] for r in part})==5 and {r['case_id'].split('__',2)[-1] for r in part}==DEFECTS,'five distinct fixed defects/source')
  require(len({tuple(sorted(r['metrics'])) for r in part})==1,'same metric columns')
  values={k:float(np.mean([r['metrics'][k] for r in part])) if all(r['metrics'][k] is not None for r in part) else None for k in part[0]['metrics']}
  result.append(dict(fold='C',source_id=source,arm=arm,case_count=5,invalid_predictions=0,metrics=values))
 return result
def describe_pairs(a,b):
 a=np.array([np.nan if v is None else v for v in a],dtype=np.float64);b=np.array([np.nan if v is None else v for v in b],dtype=np.float64)
 require(a.shape==b.shape and a.ndim==1 and len(a)>0,'paired shape')
 with np.errstate(invalid='ignore'):d=b-a
 valid=np.isfinite(a)&np.isfinite(b)&np.isfinite(d)
 if not valid.all():return dict(status='UNDEFINED_NONFINITE_PAIRS_RETAINED',pair_count=len(a),undefined_pairs=int((~valid).sum()),mean_Euclidean=None,mean_graph=None,mean_delta_graph_minus_Euclidean=None,deltas=[float(x) if np.isfinite(x) else None for x in d])
 return dict(status='OK',pair_count=len(a),undefined_pairs=0,mean_Euclidean=float(a.mean()),mean_graph=float(b.mean()),mean_delta_graph_minus_Euclidean=float(d.mean()),median_delta=float(np.median(d)),min_delta=float(d.min()),max_delta=float(d.max()),deltas=d.tolist())
def paired_summary(sources):
 rows=[r for r in sources if r['arm'] in ARMS];ids=sorted({r['source_id'] for r in rows});lookup={(r['source_id'],r['arm']):r for r in rows}
 require(len(ids)==21 and len(rows)==len(lookup)==42,'complete21 paired sources, no duplicates or drops')
 require(all((s,a) in lookup for s in ids for a in ARMS),'two arms/source')
 result={}
 for key in rows[0]['metrics']:
  d=describe_pairs([lookup[(s,'Euclidean_elimination')]['metrics'][key] for s in ids],[lookup[(s,ARMS[1])]['metrics'][key] for s in ids]);positive='coverage' in key
  d['improvement_direction']='positive' if positive else 'negative'
  if d['status']=='OK':
   x=np.array(d['deltas']);d['improved_sources']=int((x>0 if positive else x<0).sum());d['tied_sources']=int((x==0).sum());d['worse_sources']=int((x<0 if positive else x>0).sum())
  d['source_deltas']=[dict(source_id=s,delta=v) for s,v in zip(ids,d.pop('deltas'))];result[key]=d
 return dict(source_count=21,defects_per_source=5,unit='source mean of five fixed defect-level metrics, source equal',metrics=result,no_bootstrap=True,no_p_values=True,no_formal_gate=True,training_randomness_not_estimated=True)
def case_differences(rows):
 models=[r for r in rows if r['arm'] in ARMS];lookup={(r['case_id'],r['arm']):r for r in models};ids=sorted({r['case_id'] for r in models})
 require(len(ids)==105 and len(models)==len(lookup)==210,'complete105 paired model cases')
 result=[]
 for cid in ids:
  a,b=[lookup[(cid,arm)] for arm in ARMS];values={}
  for k in a['metrics']:
   x=describe_pairs([a['metrics'][k]],[b['metrics'][k]]);values[k]=x['mean_delta_graph_minus_Euclidean']
  result.append(dict(fold='C',case_id=cid,source_id=a['source_id'],defect=cid.split('__',2)[-1],metrics=values))
 return result
def defect_summary(rows):
 deltas=case_differences(rows);out={}
 for defect in sorted(DEFECTS):
  part=[r for r in deltas if r['defect']==defect];require(len(part)==21 and len({r['source_id'] for r in part})==21,'21 sources/defect')
  out[defect]=dict(paired_cases=21,mean_deltas={k:float(np.mean([r['metrics'][k] for r in part])) if all(r['metrics'][k] is not None for r in part) else None for k in part[0]['metrics']})
 return out
def csv_rows(path,rows):
 flat=[{**{k:v for k,v in r.items() if k not in {'metrics','full_metrics'}},**metric.json_safe(r['metrics'])} for r in rows]
 with Path(path).open('x',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)

def main():
 parser=argparse.ArgumentParser()
 for name in ['request','request-sha256','authorization','authorization-sha256']:parser.add_argument('--'+name,required=True)
 args=parser.parse_args()
 def rec(path,sha):return dict(path=path,bytes=Path(path).stat().st_size,sha256=sha)
 request_record=rec(args.request,args.request_sha256);plan=authorize(request_record,rec(args.authorization,args.authorization_sha256))
 require(sys.flags.isolated and sys.dont_write_bytecode and os.environ['CUDA_VISIBLE_DEVICES']=='','isolated CPU -I -B entry')
 require(check(plan['implementation']['scorer']).resolve()==Path(__file__).resolve() and check(plan['implementation']['metrics']).resolve()==Path(metric.__file__).resolve(),'final scorer/metric identities')
 require(str(Path(sys.executable).resolve())==plan['environment']['python']['path'] and check(plan['environment']['python'])==Path(sys.executable).resolve(),'fixed CPU Python')
 require({name:md.version(name) for name in plan['environment']['packages']}==plan['environment']['packages'],'fixed CPU dependency versions')
 for r in plan['evidence'].values():check(r)
 archive=check(plan['downloaded_prediction_archive'])
 for r in plan['download_sidecars']:check(r)
 refs=json.loads(check(plan['reference_manifest']).read_bytes());index=json.loads(check(plan['prediction_index']).read_bytes());score_index=json.loads(check(plan['score_case_index']).read_bytes())
 _,_,cases=validate_index(index,refs,score_index)
 out=Path(plan['output']);require(out==Path(__file__).resolve().parent.parent/'paired_scores_v1' and not any(p.is_symlink() for p in [out,*out.parents]),'fixed new owned output');out.mkdir(exist_ok=False)
 start=time.monotonic();rows=[];limits=plan['limits']
 emit(out/'single_attempt_claim.json',dict(status='CLAIMED_BEFORE_SCORING',request_sha256=args.request_sha256,no_retry=True))
 def guard():
  require(time.monotonic()-start<=limits['wall_seconds'] and psutil.Process().memory_info().rss<=limits['RSS_bytes'],'CPU scoring time/RSS')
  require(sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=limits['output_bytes'],'scoring output budget')
 try:
  emit(out/'execution_environment.json',dict(python=sys.version,executable=sys.executable,packages=plan['environment']['packages'],CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],threads=2,request_sha256=args.request_sha256))
  full=out/'case_metrics.jsonl';full.open('x').close()
  with tarfile.open(archive,'r:gz') as tar:
   lookup=validate_archive(tar,index,plan['prediction_entry_request_sha256'])
   for case in cases:
    part=score_case(tar,lookup,case,guard);rows.extend(part)
    with full.open('a',encoding='utf-8') as f:
     for row in part:f.write(json.dumps(metric.json_safe(row),allow_nan=False)+'\n')
    print('SCORED',case['case_id'],flush=True)
  require(len(rows)==525,'210 models +315 fixed CPU control scores')
  sources=aggregate_source(rows);require(len(sources)==105,'21sources x five arms including controls')
  summary=paired_summary(sources);deltas=case_differences(rows)
  emit(out/'source_metrics.json',sources);emit(out/'paired_comparison.json',dict(status='SINGLE_FOLD_SINGLE_SEED_DESCRIPTIVE_PAIRED_COMPARISON',case_count=105,model_predictions=210,controls=315,comparison=summary,request_sha256=args.request_sha256))
  emit(out/'defect_comparison.json',defect_summary(rows))
  # Preserve every source and case in ordered regression lists; no result-based selection.
  emit(out/'regression_rankings.json',dict(source_rankings={k:sorted(v['source_deltas'],key=lambda r:(r['delta'] is None,(-r['delta'] if v['improvement_direction']=='negative' else r['delta']) if r['delta'] is not None else 0,r['source_id'])) for k,v in summary['metrics'].items()},case_deltas=deltas,selection='all21 sources and all105 cases retained'))
  csv_rows(out/'case_metrics.csv',rows);csv_rows(out/'source_metrics.csv',sources);csv_rows(out/'paired_case_deltas.csv',deltas)
  guard();require(digest(archive)==plan['downloaded_prediction_archive']['sha256'],'download archive stable after scoring')
  emit(out/'completion.json',dict(status='LOCAL_PAIRED_CPU_SCORING_COMPLETE',model_predictions=210,controls=315,score_rows=525,source_rows=105,seconds=time.monotonic()-start,archive_sha256=plan['downloaded_prediction_archive']['sha256'],request_sha256=args.request_sha256,server_operations=0,model_imports=0,forward_calls=0,bootstrap=0,formal_gate=False))
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',completed_score_rows=len(rows),error=repr(exc)));raise
if __name__=='__main__':main()
