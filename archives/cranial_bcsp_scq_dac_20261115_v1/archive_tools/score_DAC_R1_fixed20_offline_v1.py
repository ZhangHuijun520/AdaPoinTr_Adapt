"""Authorized fixed20 frozen-output geometry attribution. CPU only, old metric unchanged."""
import os
for key,value in {'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2'}.items():os.environ[key]=value
from pathlib import Path
from collections import Counter
import csv,hashlib,importlib.util,importlib.metadata as md,io,json,sys,tarfile,time,traceback
import numpy as np
import psutil
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_dac_r01_preparation_20261115_v1';F=B/'post_diagnostic_freeze_v1';O=B/'fixed20_offline_geometry_v1'
METRIC_SHA='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
SCORER_SHA='2de4ef5be44c63c7796cdc61f03af8015b562d8b6713db367c19a721b2cb0f3b'
ARMS=('R','A','DAC');PAIRS=(('A','DAC'),('R','DAC'),('R','A'))
def read(p):return json.loads(p.read_bytes())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def record(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def exact(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p);return p
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def csvwrite(p,rows):
 with p.open('x',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 O.mkdir();start=time.monotonic();processed=[];resources=[]
 def guard(phase,case=None,arm=None):
  proc=psutil.Process();rss=proc.memory_info().rss;elapsed=time.monotonic()-start;size=sum(p.stat().st_size for p in O.iterdir() if p.is_file())
  event=dict(phase=phase,case=case,arm=arm,RSS_bytes=rss,elapsed_seconds=elapsed,output_bytes=size)
  with (O/'resources.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\n');f.flush()
  resources.append(event);assert rss<=8589934592 and elapsed<=1800 and size<=268435456,'fixed CPU budget'
 try:
  audit=read(F/'freeze_verification_v1.json');assert audit['status']=='FORMAL_DAC_R1_FREEZE_PASS_WITH_DISCLOSED_RNG_EVIDENCE_LIMITATION' and all(audit['checks'].values())
  selection=B/'selected20_cases_v1.json';assert sha(selection)=='09c032654a369b9830f6389b3479f302a85ac5a79023c0bb63d5ae4e06621763';selected=read(selection)['cases']
  previous=R/'outputs/scq_rf_score_impl_20261115_v1';oldrequest=read(previous/'local_scoring_execution_request_v1.json')
  versions={name:md.version(name) for name in oldrequest['environment']['packages']};assert versions==oldrequest['environment']['packages'],'frozen CPU packages'
  metricpath=exact(oldrequest['implementation']['metrics']);assert sha(metricpath)==METRIC_SHA
  scorerpath=exact(oldrequest['implementation']['scorer']);assert sha(scorerpath)==SCORER_SHA
  sp=importlib.util.spec_from_file_location('dac_existing_RF_metric_functions',scorerpath);legacy=importlib.util.module_from_spec(sp);sp.loader.exec_module(legacy);metric=legacy.metric
  assert sha(Path(metric.__file__))==METRIC_SHA and 'torch' not in sys.modules
  indexpath=exact(oldrequest['score_case_index']);scoreindex=read(indexpath);lookup={r['case_id']:r for r in scoreindex['cases']}
  baseline=previous/'unified_scores_v1/case_metrics.jsonl';frozen_audit=read(R/'outputs/scq_rf_score_freeze_20261115_v1/audit_report_v1.json')
  baseline_record=next(x for x in frozen_audit['output_manifest'] if Path(x['path']).name==baseline.name)
  assert sha(baseline)==baseline_record['sha256'] and baseline.stat().st_size==baseline_record['bytes']
  oldrows=[json.loads(line) for line in baseline.read_text(encoding='utf-8').splitlines()]
  wanted={(r['fold'],r['case_id']) for r in selected};oldR={(r['fold'],r['case_id']):r for r in oldrows if r['arm']=='RF-Requery' and (r['fold'],r['case_id']) in wanted};assert len(oldR)==20
  tar=F/'downloads/development_predictions_v1.tar.gz';assert sha(tar)==audit['archive']['sha256'] and tar.stat().st_size==audit['archive']['bytes']
  cases=[]
  for row in selected:
   c=lookup[row['case_id']];assert c['fold']==row['fold'] and c['normalization']==row['normalization'] and c['source_id']==row['source_id'] and c['point_file']['sha256']==row['input']['sha256']
   exact(c['reference']);exact(c['point_file']);cases.append(c)
  frozen_inputs=[record(p) for p in (metricpath,scorerpath,indexpath,baseline,selection,tar)]+[r for c in cases for r in (c['reference'],c['point_file'])]
  emit(O/'frozen_analysis_scope_v1.json',dict(status='AUTHORIZED_FIXED20_OFFLINE_GEOMETRY',user_request='下一步复用这20例输出，限定检查E/J、反向离群及重要挽回病例的影响，再决定是否训练，无需新增forward。',selection=record(selection),diagnostic_archive=record(tar),freeze_audit=record(F/'freeze_verification_v1.json'),metrics=record(metricpath),scorer_functions=record(scorerpath),case_index=record(indexpath),baseline=record(baseline),references=[c['reference'] for c in cases],GT8192_point_files=[c['point_file'] for c in cases],models=['frozen R weights Native','same-weights Average counterfactual','same-weights DAC counterfactual'],score_rows=60,unique_cases=20,sources=len({c['source_id'] for c in cases}),no_new_forward=True,no_model_checkpoint_load=True,GT_alignment=False,postfilter=False,bootstrap=False,training=False,metric_or_threshold_changes=False,limits=dict(wall_seconds=1800,RSS_bytes=8589934592,output_bytes=268435456,threads=2)))
  emit(O/'execution_environment.json',dict(python=sys.version,packages=versions,CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],model_imports=0))
  emit(O/'single_attempt_claim.json',dict(status='CLAIMED_BEFORE_ANY_NN_SCORING',cases=20,rows=60,automatic_retry=False))
  scorepath=O/'case_scores.jsonl';scorepath.open('x').close();case_records=[]
  with tarfile.open(tar,'r:gz') as archive:
   for i,(row,case) in enumerate(zip(selected,cases)):
    guard('before_case',case['case_id'])
    with np.load(exact(case['reference']),allow_pickle=False) as z:ref={k:z[k].copy() for k in z.files}
    with np.load(exact(case['point_file']),allow_pickle=False) as z:target=z['implant'].copy()
    assert target.shape==(8192,3) and target.dtype==np.float32 and np.isfinite(target).all() and hashlib.sha256(target.tobytes()).hexdigest()==case['target_array_sha256']
    gt=metric.world_points(target,case['normalization']);member='cases/'+row['run']+'__'+row['case_id']+'.npz';raw=archive.extractfile(member).read()
    assert hashlib.sha256(raw).hexdigest()==read(F/'inventory_before_result_v1.json')['results']['output']['files'][member]['sha256']
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:arrays={k:z[k].copy() for k in ('P_R','P_A','P_D','Q2_R','Q2_A','Q2_D')}
    for arm,key in zip(ARMS,('P_R','P_A','P_D')):
     guard('before_score',case['case_id'],arm)
     points=arrays[key];assert points.shape==(1,8192,3) and points.dtype==np.float32 and np.isfinite(points).all()
     cloud=metric.world_points(points[0],case['normalization']);score=metric.score_cloud(cloud,ref,gt);assert score['status']=='OK'
     metrics=legacy.select_metrics(score);a2,_,_=metric.a2_reference(ref);reverse=metric.nearest(cloud,a2);metrics['reverse_A2_outlier_20.0mm']=float(np.mean(reverse>20.))
     pose=legacy.position_shape(cloud,gt);risk=legacy.risk_labels(metrics,pose)
     metrics.update(centroid_offset_mm=pose['centroid_offset_mm'],radius_gyration_ratio=pose['radius_gyration_ratio'],**{k:float(v) for k,v in risk.items()})
     if arm=='R':
      old=oldR[(row['fold'],row['case_id'])]
      assert set(metrics)==set(old['metrics']) and all(np.isclose(metrics[k],old['metrics'][k],atol=1e-8,rtol=1e-8) for k in metrics),'R score/history mismatch'
      assert risk==old['risk_labels']
     scored=dict(fold=row['fold'],case_id=row['case_id'],source_id=row['source_id'],defect_type=row['defect_type'],selection=row['selection'],arm=arm,interpretation='FROZEN_WEIGHT_COUNTERFACTUAL_DIAGNOSTIC_NOT_RETRAINED_NATIVE_PERFORMANCE',metrics=metrics,risk_labels=risk,position_shape=pose,full_metrics=score)
     with scorepath.open('a',encoding='utf-8') as f:f.write(json.dumps(metric.json_safe(scored),ensure_ascii=False,allow_nan=False)+'\n');f.flush()
     case_records.append(scored);processed.append((row['case_id'],arm));guard('after_score',case['case_id'],arm)
    print(json.dumps(dict(completed_cases=i+1,total_cases=20,completed_rows=len(processed))),flush=True)
  assert len(case_records)==60 and len({(r['fold'],r['case_id'],r['arm']) for r in case_records})==60
  flat=[{k:r[k] for k in ('fold','case_id','source_id','defect_type','selection','arm')}|r['metrics'] for r in case_records];csvwrite(O/'case_scores.csv',flat)
  bykey={(r['fold'],r['case_id'],r['arm']):r for r in case_records};summaries=[];deltas=[];transitions=[]
  for fold in 'CD':
   chosen=[r for r in selected if r['fold']==fold]
   for arm in ARMS:
    part=[bykey[fold,r['case_id'],arm] for r in chosen]
    summaries.append(dict(fold=fold,arm=arm,cases=10,sources=len({r['source_id'] for r in part}),aggregation='FIXED10_CASE_EQUAL_NOT_FULL_SOURCE_PROTOCOL',metrics={k:float(np.mean([r['metrics'][k] for r in part])) for k in part[0]['metrics']},severe=sum(r['risk_labels']['severe_geometry'] for r in part)))
   for baseline_arm,candidate in PAIRS:
    trans=dict(fold=fold,comparison=candidate+'-'+baseline_arm,new=[],rescued=[],shared=[],stable_nonsevere=[])
    for row in chosen:
     old,new=(bykey[fold,row['case_id'],arm] for arm in (baseline_arm,candidate));delta={k:new['metrics'][k]-old['metrics'][k] for k in new['metrics']}
     deltas.append(dict(fold=fold,case_id=row['case_id'],source_id=row['source_id'],defect_type=row['defect_type'],selection=row['selection'],comparison=candidate+'-'+baseline_arm,metrics=delta))
     bsev,nsev=old['risk_labels']['severe_geometry'],new['risk_labels']['severe_geometry'];key='shared' if bsev and nsev else 'new' if nsev else 'rescued' if bsev else 'stable_nonsevere';trans[key].append(row['case_id'])
    trans['counts']={k:len(trans[k]) for k in ('new','rescued','shared','stable_nonsevere')};transitions.append(trans)
  emit(O/'fold_fixed_case_summary.json',summaries);emit(O/'paired_case_deltas.json',deltas);emit(O/'severe_transitions.json',transitions)
  csvwrite(O/'paired_case_deltas.csv',[{k:r[k] for k in ('fold','case_id','source_id','defect_type','selection','comparison')}|r['metrics'] for r in deltas])
  guard('complete')
  for frozen in frozen_inputs:exact(frozen)
  emit(O/'completion.json',dict(status='FIXED20_FROZEN_WEIGHT_CPU_GEOMETRY_COMPLETE',cases=20,score_rows=60,pairs=60,historical_R_rows_reproduced=20,seconds=time.monotonic()-start,peak_sampled_RSS_bytes=max(r['RSS_bytes'] for r in resources),server_calls=0,forward=0,model_imports=0,checkpoint_loads=0,training=0,bootstrap=False,formal_training_gate=False))
  files=[record(p) for p in O.iterdir() if p.is_file()];emit(O/'output_manifest.json',dict(status='OUTPUT_CONTENT_HASHES_FROZEN',files=files))
  print(json.dumps(dict(status='FIXED20_CPU_GEOMETRY_COMPLETE',rows=60,seconds=time.monotonic()-start)),flush=True)
 except BaseException as exc:
  emit(O/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),traceback=traceback.format_exc(),completed_rows=len(processed),forward=0,training=0));raise
if __name__=='__main__':main()
