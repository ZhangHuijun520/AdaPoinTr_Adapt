"""Local CPU scoring AFTER manual prediction download and separate authorization."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2'
import argparse,csv,hashlib,io,json,sys,tarfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import psutil
from bcsp_eval_metrics_v1 import score_cloud,world_points,json_safe,paired_bootstrap

def require(ok,text):
 if not ok:raise ValueError(text)
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def check(r):
 p=Path(r['path']);require(not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],'bound file: '+str(p));return p
def emit(p,obj):
 with Path(p).open('x') as f:json.dump(json_safe(obj),f,indent=2,allow_nan=False)
def select_metrics(r):
 v=dict(E_P95_mm=r['primary_E_G_P95_mm'],J_P95_mm=r['regions']['A1']['J']['p95_mm'],all_P95_mm=r['regions']['A1']['all']['p95_mm'],CD_L1_mm=r['CD_L1_mm'])
 for region in ['E','J']:
  for tau in ['0.5','1.0','2.0']:v[region+'_coverage_'+tau+'mm']=r['regions']['A1'][region]['coverage'][tau]
 v['reverse_A2_P95_mm']=r['reverse_discrete_reference']['A2']['p95_mm']
 v['B_all_P95_mm']=r['regions']['B']['all']['p95_mm']
 return v
def aggregate_source(rows):
 # Five defects are one source-level paired observation; no row is discarded.
 grouped={}
 for r in rows:grouped.setdefault((r['fold'],r['source_id'],r['arm']),[]).append(r)
 result=[]
 for (fold,source,arm),part in sorted(grouped.items()):
  require(len(part)==5 and len({r['case_id'] for r in part})==5,'five distinct defects/source')
  require(len({r['case_id'].split('__',2)[-1] for r in part})==5,'five defect identities')
  metrics={k:float(np.mean([r['metrics'][k] for r in part])) if all(r['metrics'][k] is not None for r in part) else None for k in part[0]['metrics']}
  result.append(dict(fold=fold,source_id=source,arm=arm,case_count=5,invalid_predictions=sum(r['status']!='OK' for r in part),metrics=metrics))
 return result
def paired_summary(sources):
 out={}
 for fold in ['C','D','ALL']:
  selected=[r for r in sources if (fold=='ALL' or r['fold']==fold) and r['arm'] in ['8192','16384']]
  ids=sorted({r['source_id'] for r in selected});lookup={(r['source_id'],r['arm']):r for r in selected}
  require(len(ids)==(42 if fold=='ALL' else 21) and len(lookup)==2*len(ids),'complete paired sources')
  metrics={}
  for k in selected[0]['metrics']:
   a=np.array([lookup[(s,'8192')]['metrics'][k] if lookup[(s,'8192')]['metrics'][k] is not None else np.nan for s in ids],float)
   b=np.array([lookup[(s,'16384')]['metrics'][k] if lookup[(s,'16384')]['metrics'][k] is not None else np.nan for s in ids],float)
   with np.errstate(invalid='ignore'):delta=b-a
   metrics[k]=dict(mean_8192=float(a.mean()),mean_16384=float(b.mean()),delta_16k_minus_8k=paired_bootstrap(delta),improvement_direction='positive' if 'coverage' in k else 'negative',nonfinite_source_pairs=int((~np.isfinite(delta)).sum()))
  out[fold]=dict(source_count=len(ids),metrics=metrics)
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--plan-sha256',required=True);p.add_argument('--authorization',required=True);p.add_argument('--authorization-sha256',required=True);args=p.parse_args()
 require(digest(args.plan)==args.plan_sha256 and digest(args.authorization)==args.authorization_sha256,'explicit plan/auth hashes')
 plan=json.loads(Path(args.plan).read_bytes());auth=json.loads(Path(args.authorization).read_bytes())
 require(auth==dict(schema='bcsp-local-score-authorization-v1',plan_sha256=args.plan_sha256,explicit_user_authorization=True),'scoring authorization')
 archive=check(plan['downloaded_prediction_archive']);refs=json.loads(check(plan['reference_manifest']).read_bytes())
 expected=json.loads(check(plan['input_index']).read_bytes());out=Path(plan['output']);out.mkdir(exist_ok=False)
 start=time.monotonic();rows=[];full=out/'case_metrics.jsonl';full.open('x').close()
 def guard():
  require(time.monotonic()-start<=7200 and psutil.Process().memory_info().rss<=8589934592,'CPU scoring time/RSS')
  require(sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=2147483648,'scoring output budget')
 try:
  with tarfile.open(archive,'r:gz') as tar:
   members=tar.getmembers();names=[m.name for m in members]
   require(len(names)==len(set(names))==423 and all(m.isfile() and 0<m.size<=67108864 for m in members),'archive regular bounded members')
   prediction_names={'predictions/'+r['run']+'__'+r['case_id']+'.npz' for r in expected['inputs']}
   require(set(names)==prediction_names|{'inference_manifest.jsonl','inference_complete.json','resources.jsonl'},'exact archive contents')
   records=[json.loads(x) for x in tar.extractfile('inference_manifest.jsonl').read().decode().splitlines()]
   done=json.loads(tar.extractfile('inference_complete.json').read())
   require(done['status']=='FOUR_MODEL_420_FORWARD_COMPLETE' and done['forwards']==420 and done['training_updates']==done['BNCal']==done['loss']==done['backward']==0,'prediction completion')
   require(done['request_sha256']==plan['prediction_entry_request_sha256'] and len(done['models'])==4 and {m['run'] for m in done['models']}=={r['label'] for r in expected['runs']},'prediction request/model identities')
   for model in done['models']:
    require(model['forwards']==105 and model['state_before']==model['state_after'] and model['mode']=='eval_inference_mode' and model['BNCal']==model['optimizer']==model['backward']==0,'frozen eval state evidence')
   require(len(records)==420 and len({(r['run'],r['case_id']) for r in records})==420 and [r['forward_index'] for r in records]==list(range(1,421)),'exact420 prediction records')
   lookup={(r['run'],r['case_id']):r for r in records};inputs={(r['run'],r['case_id']):r for r in expected['inputs']};runs={r['label']:r for r in expected['runs']}
   require(set(lookup)==set(inputs),'prediction case identities')
   for row in refs['cases']:
    guard();refpath=check(row)
    with np.load(refpath,allow_pickle=False) as z:ref={k:z[k] for k in z.files}
    points={}
    for arm in ['8192','16384']:
     with np.load(check(row['point_files'][arm]),allow_pickle=False) as z:points[arm]=dict(partial=z['partial'].copy(),implant=z['implant'].copy())
    require(np.array_equal(points['8192']['partial'],points['16384']['partial'][:8192]) and np.array_equal(points['8192']['implant'],points['16384']['implant']),'paired inputs and shared GT')
    require(hashlib.sha256(points['8192']['implant'].tobytes()).hexdigest()==row['target_array_sha256'],'frozen GT target')
    norm=row['normalization'];gt=world_points(points['8192']['implant'],norm)
    for arm in ['8192','16384','Nop_D_8192','Nop_D_16384','GT_8192']:
     guard();status='OK'
     if arm in ['8192','16384']:
      key=(row['fold']+'_'+arm,row['case_id']);r=lookup[key];i=inputs[key]
      require(r['input_sha256']==i['input']['sha256'] and r['checkpoint_sha256']==runs[key[0]]['checkpoint']['sha256'] and r['source_id']==row['source_id'] and r['fold']==row['fold'] and r['n_input']==int(arm) and r['n_output']==8192,'prediction provenance')
      blob=tar.extractfile(r['prediction']['name']).read();require(len(blob)==r['prediction']['bytes'] and hashlib.sha256(blob).hexdigest()==r['prediction']['sha256'],'prediction bytes/hash')
      with np.load(io.BytesIO(blob),allow_pickle=False) as z:
       require(z.files==['prediction'],'prediction-only schema');pred=z['prediction'].copy()
      if pred.shape!=(8192,3) or pred.dtype!=np.float32 or not np.isfinite(pred).all():pred=np.empty((0,3));status='INVALID_PREDICTION'
      cloud=world_points(pred,norm)
     else:cloud=gt if arm=='GT_8192' else world_points(points[arm.rsplit('_',1)[1]]['partial'],norm)
     score=score_cloud(cloud,ref,gt);result=dict(fold=row['fold'],case_id=row['case_id'],source_id=row['source_id'],arm=arm,status=status,metrics=select_metrics(score))
     rows.append(result)
     with full.open('a') as f:f.write(json.dumps(json_safe(dict(**result,full_metrics=score)),allow_nan=False)+'\n')
    print('SCORED',row['case_id'],flush=True)
   require(len(rows)==1050,'420 model scores+630 fixed controls')
  sources=aggregate_source(rows);summary=paired_summary(sources)
  emit(out/'source_metrics.json',sources);emit(out/'paired_comparison.json',dict(status='FIXED_SEED0_OOF_SOURCE_PAIRED_COMPARISON',case_count=210,model_predictions=420,unique_sources=42,comparisons=summary,no_formal_gate=True,training_randomness_not_estimated=True))
  for filename,data in [('case_metrics.csv',rows),('source_metrics.csv',sources)]:
   flat=[{**{k:v for k,v in r.items() if k!='metrics'},**json_safe(r['metrics'])} for r in data]
   with (out/filename).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
  emit(out/'completion.json',dict(status='LOCAL_CPU_SCORING_COMPLETE',model_predictions=420,controls=630,source_rows=len(sources),seconds=time.monotonic()-start,archive_sha256=plan['downloaded_prediction_archive']['sha256'],plan_sha256=args.plan_sha256))
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',completed_score_rows=len(rows),error=repr(exc)));raise
if __name__=='__main__':main()
