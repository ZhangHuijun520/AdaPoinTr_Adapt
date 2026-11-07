"""CPU-only P2 H1/M0 twofold M0/M_H1 paired scoring. Main requires a separately hash-authorized request."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2'
import argparse,csv,hashlib,io,json,sys,tarfile,time
from pathlib import Path
import importlib.metadata as md
import importlib.util
METRIC_PATH=Path(__file__).resolve().parents[2]/'cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py'
import numpy as np
import psutil
require_metric_sha='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
if hashlib.sha256(METRIC_PATH.read_bytes()).hexdigest()!=require_metric_sha:raise RuntimeError('frozen metric source drift')
_spec=importlib.util.spec_from_file_location('p1_frozen_eval_metrics',METRIC_PATH);metric=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(metric)
ARMS=['M0','M_H1']
CONTROLS=['Nop_D','GT_8192']
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
 require(plan['schema']=='bcsp-p2-H1-M0-twofold-local-scoring-request-v1' and plan['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and plan['execution_authorized'] is False,'pending scoring request')
 require(plan['counts']==dict(unique_cases=210,sources=42,model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168),'exact scoring scope')
 require(set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-p2-H1-M0-score-authorization-v1' and auth['request_sha256']==request_record['sha256'] and auth['explicit_user_authorization'] is True and bool(auth['user_authorization_text'].strip()),'separate score authorization')
 return plan


def validate_index(index,references,score_index):
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
 return index['runs'],index['inputs'],cases


def validate_archive(tar,index,inner_sha256,coarse_cases,kind):
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
 return lookup


def load_prediction_arrays(tar,record):
 blob=tar.extractfile(record['prediction']['name']).read()
 require(len(blob)==record['prediction']['bytes'] and hashlib.sha256(blob).hexdigest()==record['prediction']['sha256'],'prediction bytes/hash')
 with np.load(io.BytesIO(blob),allow_pickle=False) as z:
  expected=['prediction','coarse'] if record['coarse_expected'] else ['prediction'];require(z.files==expected,'only frozen prediction/optional coarse keys')
  arrays={k:z[k].copy() for k in expected}
 for name,value in arrays.items():require(value.shape==((8192,3) if name=='prediction' else (256,3)) and value.dtype==np.float32 and np.isfinite(value).all(),'finite FP32 native tensor')
 return arrays

def load_prediction(tar,record):return load_prediction_arrays(tar,record)['prediction']

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
def position_shape(cloud,gt):
 cp=cloud.mean(0);cg=gt.mean(0);pc=cloud-cp;gc=gt-cg
 vp=np.linalg.eigvalsh(pc.T@pc/len(cloud));vg=np.linalg.eigvalsh(gc.T@gc/len(gt));rg=float(np.sqrt(max(float(vp.sum()),0)));grg=float(np.sqrt(vg.sum()))
 require(grg>0,'nondegenerate frozen GT');ratio=rg/grg
 return dict(centroid_offset_mm=float(np.linalg.norm(cp-cg)),centroid_offset_vector_mm=(cp-cg).tolist(),prediction_centroid_mm=cp.tolist(),GT8192_centroid_mm=cg.tolist(),radius_gyration_ratio=ratio,prediction_radius_gyration_mm=rg,GT8192_radius_gyration_mm=grg,prediction_bbox_mm=[cloud.min(0).tolist(),cloud.max(0).tolist()],GT8192_bbox_mm=[gt.min(0).tolist(),gt.max(0).tolist()],covariance_eigenvalues_mm2=vp.tolist(),GT8192_covariance_eigenvalues_mm2=vg.tolist(),covariance_denominator='population N; equal8192 cancels versus P0 sample covariance in ratios')

def risk_labels(metrics,pose):
 return dict(placement_tail=pose['centroid_offset_mm']>20.,compact_distribution=pose['radius_gyration_ratio']<.9,severe_geometry=(metrics['E_P95_mm'] is not None and metrics['E_P95_mm']>20.) or metrics['J_coverage_2.0mm']==0.)

def stage_geometry(summary,cloud,gt,normalization,coarse=None):
 scale=float(normalization['scale']);center=np.asarray(normalization['center'],np.float64);p=position_shape(cloud,gt);d=summary['dense'];c=summary['coarse']
 require(np.allclose(np.asarray(d['centroid'])*scale+center,cloud.mean(0),rtol=1e-9,atol=1e-7) and np.isclose(d['radius_gyration']*scale,p['prediction_radius_gyration_mm'],rtol=1e-8,atol=1e-7),'dense summary/native array consistency')
 cc=np.asarray(c['centroid'],np.float64)*scale+center;cr=float(c['radius_gyration'])*scale;offset=np.asarray(summary['mean_dense_minus_coarse'],np.float64)*scale
 require(cc.shape==(3,) and np.isfinite(cc).all() and np.isfinite(cr) and cr>=0 and np.allclose(cloud.mean(0)-cc,offset,rtol=1e-8,atol=1e-7),'coarse/offset summary consistency')
 if coarse is not None:
  require(np.allclose(coarse.mean(0),cc,rtol=1e-9,atol=1e-7) and np.isclose(position_shape(coarse,gt)['prediction_radius_gyration_mm'],cr,rtol=1e-8,atol=1e-7),'saved coarse tensor vs summary')
 energy=float(summary['offset_mean_squared_radius'])*scale**2;offset_variance=energy-float(offset@offset);cross=p['prediction_radius_gyration_mm']**2-cr**2-offset_variance
 return dict(frame='native_world_mm_no_alignment',dense=p,coarse=dict(points=256,centroid_mm=cc.tolist(),centroid_offset_mm=float(np.linalg.norm(cc-gt.mean(0))),radius_gyration_mm=cr,radius_gyration_ratio=cr/p['GT8192_radius_gyration_mm'],bbox_mm=(np.array([c['bbox_min'],c['bbox_max']])*scale+center).tolist(),covariance_eigenvalues_mm2=(np.asarray(c['covariance_eigenvalues'])*scale**2).tolist(),tensor_saved=coarse is not None),dense_points=8192,mean_dense_minus_coarse_mm=offset.tolist(),offset_mean_squared_radius_mm2=energy,offset_centered_variance_mm2=offset_variance,cross_term_twice_covariance_mm2=cross,interpretation='Algebraic decomposition from existing same-forward summaries; not causal attribution or equal point budgets')

def score_case(tars,lookup,case,guard):
 with np.load(check(case['reference']),allow_pickle=False) as z:ref={k:z[k] for k in z.files}
 with np.load(check(case['point_file']),allow_pickle=False) as z:
  require(set(z.files)=={'partial','implant'},'V1 point schema');partial=z['partial'].copy();target=z['implant'].copy()
 for value in [partial,target]:require(value.shape==(8192,3) and value.dtype==np.float32 and np.isfinite(value).all(),'finite V1 tensor')
 require(hashlib.sha256(target.tobytes()).hexdigest()==case['target_array_sha256'],'same fixed GT array SHA')
 gt=metric.world_points(target,case['normalization']);rows=[]
 for arm in ARMS+CONTROLS:
  guard();stage=None
  if arm in ARMS:
   record=lookup[(case['fold'],arm,case['case_id'])];arrays=load_prediction_arrays(tars[record['archive_key']],record);cloud=metric.world_points(arrays['prediction'],case['normalization']);coarse=metric.world_points(arrays['coarse'],case['normalization']) if 'coarse' in arrays else None
   stage=stage_geometry(record['geometry'],cloud,gt,case['normalization'],coarse)
  elif arm=='GT_8192':cloud=gt
  else:cloud=metric.world_points(partial,case['normalization'])
  score=metric.score_cloud(cloud,ref,gt);require(score['status']=='OK','invalid whole batch stops; no drop');metrics=select_metrics(score)
  a2,_,_=metric.a2_reference(ref);reverse=metric.nearest(cloud,a2);metrics['reverse_A2_outlier_20.0mm']=float(np.mean(reverse>20.))
  pose=position_shape(cloud,gt);labels=risk_labels(metrics,pose);metrics.update(centroid_offset_mm=pose['centroid_offset_mm'],radius_gyration_ratio=pose['radius_gyration_ratio'],**{k:float(v) for k,v in labels.items()})
  rows.append(dict(fold=case['fold'],case_id=case['case_id'],source_id=case['source_id'],arm=arm,status=score['status'],metrics=metrics,full_metrics=score,position_shape=pose,risk_labels=labels,stage_geometry=stage))
 return rows

def aggregate_source(rows):
 groups={}
 for row in rows:
  require(row['fold'] in ('C','D') and row['arm'] in ARMS+CONTROLS and row['status']=='OK','valid fixed arm/fold/status');groups.setdefault((row['fold'],row['source_id'],row['arm']),[]).append(row)
 result=[]
 for (fold,source,arm),part in sorted(groups.items()):
  require(len(part)==5 and len({r['case_id'] for r in part})==5 and {r['case_id'].split('__',2)[-1] for r in part}==DEFECTS,'five distinct fixed defects/source')
  require(len({tuple(sorted(r['metrics'])) for r in part})==1,'same metric columns')
  values={k:float(np.mean([r['metrics'][k] for r in part])) if all(r['metrics'][k] is not None for r in part) else None for k in part[0]['metrics']}
  result.append(dict(fold=fold,source_id=source,arm=arm,case_count=5,invalid_predictions=0,metrics=values))
 return result
def describe_pairs(a,b):
 a=np.array([np.nan if v is None else v for v in a],dtype=np.float64);b=np.array([np.nan if v is None else v for v in b],dtype=np.float64)
 require(a.shape==b.shape and a.ndim==1 and len(a)>0,'paired shape')
 with np.errstate(invalid='ignore'):d=b-a
 valid=np.isfinite(a)&np.isfinite(b)&np.isfinite(d)
 if not valid.all():return dict(status='UNDEFINED_NONFINITE_PAIRS_RETAINED',pair_count=len(a),undefined_pairs=int((~valid).sum()),mean_M0=None,mean_M_H1=None,mean_delta_M_H1_minus_M0=None,deltas=[float(x) if np.isfinite(x) else None for x in d])
 return dict(status='OK',pair_count=len(a),undefined_pairs=0,mean_M0=float(a.mean()),mean_M_H1=float(b.mean()),mean_delta_M_H1_minus_M0=float(d.mean()),median_delta=float(np.median(d)),min_delta=float(d.min()),max_delta=float(d.max()),deltas=d.tolist())
def paired_summary(sources):
 rows=[r for r in sources if r['arm'] in ARMS];ids=sorted({r['source_id'] for r in rows});lookup={(r['source_id'],r['arm']):r for r in rows}
 require(len(ids)==21 and len(rows)==len(lookup)==42,'complete21 paired sources, no duplicates or drops')
 require(all((s,a) in lookup for s in ids for a in ARMS),'two arms/source')
 result={}
 for key in rows[0]['metrics']:
  d=describe_pairs([lookup[(s,'M0')]['metrics'][key] for s in ids],[lookup[(s,ARMS[1])]['metrics'][key] for s in ids]);positive='coverage' in key;ordered=key!='radius_gyration_ratio'
  d['improvement_direction']=('positive' if positive else 'negative') if ordered else 'descriptive_not_ordered'
  if d['status']=='OK' and ordered:
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
   x=describe_pairs([a['metrics'][k]],[b['metrics'][k]]);values[k]=x['mean_delta_M_H1_minus_M0']
  result.append(dict(fold=a['fold'],case_id=cid,source_id=a['source_id'],defect=cid.split('__',2)[-1],metrics=values))
 return result
def defect_summary(rows):
 deltas=case_differences(rows);out={}
 for defect in sorted(DEFECTS):
  part=[r for r in deltas if r['defect']==defect];require(len(part)==21 and len({r['source_id'] for r in part})==21,'21 sources/defect')
  out[defect]=dict(paired_cases=21,mean_deltas={k:float(np.mean([r['metrics'][k] for r in part])) if all(r['metrics'][k] is not None for r in part) else None for k in part[0]['metrics']})
 return out
def csv_rows(path,rows):
 flat=[{**{k:v for k,v in r.items() if k not in {'metrics','full_metrics','position_shape','risk_labels','stage_geometry'}},**metric.json_safe(r['metrics'])} for r in rows]
 with Path(path).open('x',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)

def risk_transitions(rows):
 model=[r for r in rows if r['arm'] in ARMS];lookup={(r['case_id'],r['arm']):r for r in model};ids=sorted({r['case_id'] for r in model});require(len(model)==len(lookup)==210 and len(ids)==105,'complete risk pairs')
 result={}
 for label in ['placement_tail','compact_distribution','severe_geometry']:
  records=[]
  for cid in ids:
   a,b=[lookup[(cid,arm)]['risk_labels'][label] for arm in ARMS];records.append(dict(case_id=cid,source_id='train:'+cid.split('__')[1],defect=cid.split('__',2)[-1],M0=a,M_H1=b,new=bool(b and not a),rescued=bool(a and not b)))
  result[label]=dict(M0_count=sum(r['M0'] for r in records),M_H1_count=sum(r['M_H1'] for r in records),new=sum(r['new'] for r in records),rescued=sum(r['rescued'] for r in records),cases=records,by_defect={d:dict(new=sum(r['new'] for r in records if r['defect']==d),rescued=sum(r['rescued'] for r in records if r['defect']==d)) for d in sorted(DEFECTS)})
 return dict(labels=result,clinical_certification=False,overlapping_labels=True,GT_alignment=False)

def run_scoring(plan,index,cases,out,archives,request_sha256,guard,start):
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
    for row in part:f.write(json.dumps(metric.json_safe(row),allow_nan=False)+'\n')
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
 return rows


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
 archives={k:check(v['archive']) for k,v in plan['archive_inputs'].items()}
 for v in plan['archive_inputs'].values():
  for r in v['sidecars']:check(r)
 refs=json.loads(check(plan['reference_manifest']).read_bytes());index=json.loads(check(plan['prediction_index']).read_bytes());score_index=json.loads(check(plan['score_case_index']).read_bytes())
 _,_,cases=validate_index(index,refs,score_index)
 out=Path(plan['output']);require(out==Path(__file__).resolve().parent/'unified_scores_v1' and not any(p.is_symlink() for p in [out,*out.parents]),'fixed new owned output');out.mkdir(exist_ok=False)
 start=time.monotonic();rows=[];limits=plan['limits']
 emit(out/'single_attempt_claim.json',dict(status='CLAIMED_BEFORE_SCORING',request_sha256=args.request_sha256,no_retry=True))
 def guard():
  require(time.monotonic()-start<=limits['wall_seconds'] and psutil.Process().memory_info().rss<=limits['RSS_bytes'],'CPU scoring time/RSS')
  require(sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=limits['output_bytes'],'scoring output budget')
 try:
  emit(out/'execution_environment.json',dict(python=sys.version,executable=sys.executable,packages=plan['environment']['packages'],CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],threads=2,request_sha256=args.request_sha256))
  rows=run_scoring(plan,index,cases,out,archives,args.request_sha256,guard,start)
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',completed_score_rows=sum(1 for _ in (out/'case_metrics.jsonl').open('r',encoding='utf8')) if (out/'case_metrics.jsonl').exists() else 0,error=repr(exc)));raise
if __name__=='__main__':main()
