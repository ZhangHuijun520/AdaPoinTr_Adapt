"""Single bounded artificial CPU batch, no real archive/reference/point array reads."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import ast,copy,hashlib,importlib.util,io,json,sys,tarfile,time
from pathlib import Path
from contextlib import ExitStack
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];F=HERE/'artificial_cpu_batch_v1'
def main():
 F.mkdir(exist_ok=False);checks=[]
 spec=importlib.util.spec_from_file_location('artificial_H1_M0_score',HERE/'bcsp_p2_h1_M0_twofold_score_v1.py');s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s)
 np=s.np;m=s.metric
 def check(n,v):
  if not bool(v):raise AssertionError(n)
  checks.append(n)
 def rejects(n,fn):
  try:fn()
  except (ValueError,RuntimeError,KeyError,AssertionError):checks.append(n)
  else:raise AssertionError(n)
 def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=s.digest(p))
 def emit(n,x):
  p=F/n;s.emit(p,x);return rec(p)
 def npz(n,**x):
  p=F/n
  with p.open('xb') as f:np.savez_compressed(f,**x)
  return rec(p)
 try:
  # Analytic tiny solid, finite exposed voxel-face references.
  g=np.zeros((5,5,5),bool);g[2,2,2]=True;d=np.zeros_like(g);d[1,2,2]=True
  ref=m.surface_references(g,d,np.eye(3),np.zeros(3));rr=npz('artificial_reference.npz',**ref)
  gt=np.tile(ref['a_centers'].astype(np.float32),(1366,1))[:8192].copy();point=npz('artificial_point.npz',partial=gt+.25,implant=gt)
  norm=dict(center=[0.,0.,0.],scale=1.);targetsha=hashlib.sha256(gt.tobytes()).hexdigest()
  cases=[];refs=[];runs=[];hrows=[];baselineidx={};coarse={}
  for fold,offset in [('C',0),('D',21)]:
   sources=['train:'+str(i).zfill(3) for i in range(offset,offset+21)]
   ids=['train__'+source.split(':')[1]+'__'+defect for source in sources for defect in sorted(s.DEFECTS)]
   coarse[fold]=ids[:7 if fold=='C' else 5]
   def run(label):return dict(label=label,variant='M0' if label.endswith(('M0','M_H1')) else 'T0',fold=fold,seed=0,n_input=8192,n_output=8192,dev_case_ids=ids,dev_sources=sources,train_sources=['train:999'],checkpoint=dict(sha256=hashlib.sha256(label.encode()).hexdigest()))
   def row(label,cid):return dict(run=label,variant='M0',fold=fold,n_input=8192,case_id=cid,source_id='train:'+cid.split('__')[1],normalization=copy.deepcopy(norm),normalization_source='defective_bbox',target_array_sha256=targetsha,input=point)
   runs.append(run(fold+'_M_H1'));hrows.extend(row(fold+'_M_H1',cid) for cid in ids)
   baselineidx[fold]=dict(schema='bcsp-p1-paired-development-index-v1',runs=[run(fold+'_T0'),run(fold+'_M0')],inputs=[row(fold+'_'+arm,cid) for arm in ['T0','M0'] for cid in ids])
   for cid in ids:
    c=dict(case_id=cid,source_id='train:'+cid.split('__')[1],fold=fold,normalization=copy.deepcopy(norm),normalization_source='defective_bbox',target_array_sha256=targetsha,point_file=point,reference=rr)
    cases.append(c);refs.append(dict(case_id=cid,source_id=c['source_id'],fold=fold,normalization=copy.deepcopy(norm),target_array_sha256=targetsha,**rr))
  hindex=dict(schema='bcsp-p2-H1-twofold-development-index-v1',runs=runs,inputs=hrows)
  rmanifest=dict(cases=refs);scoreindex=dict(schema='bcsp-p2-H1-M0-twofold-score-index-candidate-v1',cases=cases)
  check('S01 twofold210cases42sources accepted',len(s.validate_index(hindex,rmanifest,scoreindex)[2])==210)
  bad=copy.deepcopy(scoreindex);bad['cases'].pop();rejects('S02 missing case rejected',lambda:s.validate_index(hindex,rmanifest,bad))
  bad=copy.deepcopy(scoreindex);bad['cases'][105]['fold']='C';rejects('S03 wrong fold reference route rejected',lambda:s.validate_index(hindex,rmanifest,bad))
  bad=copy.deepcopy(scoreindex);bad['cases'][0]['normalization']['scale']=2;rejects('S04 coordinate drift rejected',lambda:s.validate_index(hindex,rmanifest,bad))
  bad=copy.deepcopy(scoreindex);bad['cases'][0]['target_array_sha256']='0'*64;rejects('S05 target identity drift rejected',lambda:s.validate_index(hindex,rmanifest,bad))
  # Authorization requires exact840/168 scope.
  counter=0
  def chain(auth=True,wrong=False):
   nonlocal counter
   counter+=1;qr=emit('q'+str(counter)+'.json',dict(schema='bcsp-p2-H1-M0-twofold-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,counts=dict(unique_cases=210,sources=42,model_rows=420,shared_control_rows=420,case_score_rows=839 if wrong else 840,source_score_rows=168)))
   ar=emit('a'+str(counter)+'.json',dict(schema='bcsp-p2-H1-M0-score-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=auth,user_authorization_text='ARTIFICIAL ONLY'))
   return qr,ar
  s.authorize(*chain());check('S06 full authorize valid840row request',True)
  rejects('S07 missing execution authorization rejected',lambda:s.authorize(*chain(False)))
  rejects('S08 wrong row budget rejected',lambda:s.authorize(*chain(wrong=True)))
  def stats(x):
   x=x.astype(np.float64);mu=x.mean(0);z=x-mu
   return dict(centroid=mu.tolist(),bbox_min=x.min(0).tolist(),bbox_max=x.max(0).tolist(),radius_gyration=float(np.sqrt((z*z).sum(1).mean())),covariance_eigenvalues=np.linalg.eigvalsh(z.T@z/len(x)).tolist())
  rng=dict(CPU='b'*64,CUDA='c'*64,Python='artificial',numpy='artificial')
  def archive(name,index,kind,mutate=None):
   items=[];records=[];geometry=[];runmap={r['label']:r for r in index['runs']}
   for i,x in enumerate(index['inputs'],1):
    pred=(gt+(.05 if kind=='H1' else 0.)).astype(np.float32);cp=pred[:256].copy();arrays=dict(prediction=pred)
    if x['case_id'] in coarse[x['fold']]:arrays['coarse']=cp
    stream=io.BytesIO();np.savez_compressed(stream,**arrays);raw=stream.getvalue();member='predictions/'+x['run']+'__'+x['case_id']+'.npz';items.append((member,raw))
    records.append(dict(run=x['run'],case_id=x['case_id'],source_id=x['source_id'],fold=x['fold'],n_input=8192,n_output=8192,normalization=x['normalization'],input_sha256=x['input']['sha256'],checkpoint_sha256=runmap[x['run']]['checkpoint']['sha256'],forward_index=i,prediction=dict(name=member,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
    delta=pred.astype(float).reshape(256,32,3)-cp.astype(float)[:,None,:]
    geometry.append(dict(run=x['run'],case_id=x['case_id'],frame='native_D_only_normalized_no_GT',coarse=stats(cp),dense=stats(pred),mean_dense_minus_coarse=delta.mean((0,1)).tolist(),offset_mean_squared_radius=float((delta**2).sum(2).mean())))
   done=dict(status='P2_H1_TWOFOLD_210_FORWARD_COMPLETE' if kind=='H1' else 'P1_PAIR_210_FORWARD_COMPLETE',forwards=210,request_sha256='d'*64,training_updates=0,BNCal=0,loss=0,backward=0,models=[dict(run=r['label'],forwards=105,state_before='a'*64,state_after='a'*64,RNG_before=rng,RNG_after=rng,mode='eval_inference_mode',BNCal=0,optimizer=0,backward=0) for r in index['runs']])
   if mutate:mutate(done)
   claims=[dict(forward_index=i+1,run=r['run'],case_id=r['case_id'],status='CLAIMED_BEFORE_FORWARD') for i,r in enumerate(records)]
   items.extend([('inference_manifest.jsonl','\n'.join(json.dumps(r) for r in records).encode()),('forward_attempts.jsonl','\n'.join(json.dumps(r) for r in claims).encode()),('geometry_summary.jsonl','\n'.join(json.dumps(r) for r in geometry).encode()),('inference_complete.json',json.dumps(done).encode()),('resources.jsonl',b'{"ARTIFICIAL":true}\n')])
   path=F/name
   with tarfile.open(path,'w:gz') as t:
    for member,raw in items:
     info=tarfile.TarInfo(member);info.size=len(raw);t.addfile(info,io.BytesIO(raw))
   return path
  paths={'H1':archive('artificial_H1.tar.gz',hindex,'H1'),'C':archive('artificial_C.tar.gz',baselineidx['C'],'C'),'D':archive('artificial_D.tar.gz',baselineidx['D'],'D')}
  allidx=dict(H1=hindex,**baselineidx);plan=dict(archive_inputs={})
  for kind,index in allidx.items():
   pro=dict(coarse_tensor_cases_by_fold=coarse) if kind=='H1' else dict(coarse_tensor_cases=coarse[kind])
   plan['archive_inputs'][kind]=dict(archive=rec(paths[kind]),prediction_index=emit('index_'+kind+'.json',index),prediction_protocol=emit('protocol_'+kind+'.json',pro),prediction_request_sha256='d'*64,fold=kind)
  def lookup_all(tars):
   lookup={}
   for kind,index in allidx.items():lookup.update(s.validate_archive(tars[kind],index,'d'*64,coarse if kind=='H1' else {kind:coarse[kind]},kind))
   return lookup
  with ExitStack() as stack:
   tars={k:stack.enter_context(tarfile.open(p)) for k,p in paths.items()};lookup=lookup_all(tars)
   check('S09 three real artificial archive readers select420models',len(lookup)==420 and all(k[1] in ['M0','M_H1'] for k in lookup))
   crows=s.score_case(tars,lookup,cases[0],lambda:None);drows=s.score_case(tars,lookup,cases[105],lambda:None)
   check('S10 actual unchanged metric computes both folds and shared controls',[r['arm'] for r in crows]==['M0','M_H1','Nop_D','GT_8192'] and all(r['fold']=='D' for r in drows))
   check('S11 GT8192 control zeroCD and M0 exactGT',crows[-1]['metrics']['CD_L1_mm']==0 and crows[0]['metrics']['CD_L1_mm']==0)
   check('S12 model changes affect metric not control duplication',crows[1]['metrics']['CD_L1_mm']>0 and len(crows)==4)
   badrecord=copy.deepcopy(next(iter(lookup.values())));badrecord['prediction']['sha256']='0'*64
   rejects('S13 prediction member hash drift rejected',lambda:s.load_prediction_arrays(tars[badrecord['archive_key']],badrecord))
   rejects('S14 wrong H1 completion request rejected',lambda:s.validate_archive(tars['H1'],hindex,'0'*64,coarse,'H1'))
   rejects('S15 wrong completion kind rejected',lambda:s.validate_archive(tars['H1'],hindex,'d'*64,coarse,'C'))
   wrong=copy.deepcopy(hindex);wrong['inputs'][105]['checkpoint_sha256']='0'*64
   wrong['runs'][1]['checkpoint']['sha256']='0'*64
   rejects('S16 wrong checkpoint provenance rejected',lambda:s.validate_archive(tars['H1'],wrong,'d'*64,coarse,'H1'))
  # Full840 orchestration: actual archive lookup/validation and all statistics, metric rows
  # from the two already computed artificial analytic cases, not840 repeated KD computations.
  real_score=s.score_case;calls=[];templates={'C':crows,'D':drows}
  def artificial_case(tars,lookup,c,guard):
   calls.append(c['case_id']);guard();part=copy.deepcopy(templates[c['fold']])
   for row in part:row.update(fold=c['fold'],case_id=c['case_id'],source_id=c['source_id'])
   return part
  out=F/'full840';out.mkdir();s.score_case=artificial_case
  try:rows=s.run_scoring(plan,hindex,cases,out,paths,'e'*64,lambda:None,time.monotonic())
  finally:s.score_case=real_score
  check('S17 full210case runner exact840rows420models420controls',len(rows)==840 and len(calls)==len(set(calls))==210)
  sources=s.aggregate_source(rows);check('S18 exact168source rows5defects each',len(sources)==168 and all(r['case_count']==5 for r in sources))
  result=json.loads((out/'paired_comparison.json').read_bytes())
  check('S19 source equal per-fold not pooled cases',all(result['comparison'][f]['source_count']==21 for f in ['C','D']))
  check('S20 delta names correct H1minusM0',result['comparison']['C']['metrics']['CD_L1_mm']['mean_delta_M_H1_minus_M0']>0 and 'mean_T0' not in result['comparison']['C']['metrics']['CD_L1_mm'])
  check('S21 case deltas preserve both folds',len(s.case_differences([r for r in rows if r['fold']=='D']))==105 and all(r['fold']=='D' for r in s.case_differences([r for r in rows if r['fold']=='D'])))
  risk=json.loads((out/'risk_transitions.json').read_bytes());check('S22 per-fold risk transition complete105',all(len(risk[f]['labels']['severe_geometry']['cases'])==105 for f in ['C','D']))
  done=json.loads((out/'completion.json').read_bytes());check('S23 completion840168 no forward bootstrap gate',done['score_rows']==840 and done['source_rows']==168 and done['forward_calls']==done['bootstrap']==0 and done['formal_gate'] is False)
  bad=copy.deepcopy(rows);bad.pop();rejects('S24 incomplete defect group rejected',lambda:s.aggregate_source(bad))
  e=s.describe_pairs([1,None],[2,3]);check('S25 undefined pairs retained not dropped',e['status']=='UNDEFINED_NONFINITE_PAIRS_RETAINED' and e['pair_count']==2 and e['mean_delta_M_H1_minus_M0'] is None)
  check('S26 fixed risk threshold20mm and0.9 unchanged',s.risk_labels(dict(E_P95_mm=20,**{'J_coverage_2.0mm':.1}),dict(centroid_offset_mm=20,radius_gyration_ratio=.9))==dict(placement_tail=False,compact_distribution=False,severe_geometry=False))
  check('S27 zeroJcoverage severe',s.risk_labels(dict(E_P95_mm=1,**{'J_coverage_2.0mm':0}),dict(centroid_offset_mm=0,radius_gyration_ratio=1))['severe_geometry'])
  single=[r for r in rows if r['fold']=='C'];alter=copy.deepcopy(single)
  for r in alter:r['risk_labels']['severe_geometry']=r['arm']=='M_H1'
  transitions=s.risk_transitions(alter)['labels']['severe_geometry'];check('S28 newrisk identified all105 no netcount hiding',transitions['new']==105 and transitions['M_H1_count']==105)
  # Failure of one artificial case stops orchestration; no silent case drop or retry.
  failed=F/'fail_stop';failed.mkdir();failcalls=[]
  def fail(t,l,c,g):failcalls.append(c['case_id']);raise RuntimeError('artificial failure')
  s.score_case=fail
  try:rejects('S29 first case failure stops runner',lambda:s.run_scoring(plan,hindex,cases,failed,paths,'f'*64,lambda:None,time.monotonic()))
  finally:s.score_case=real_score
  check('S30 failed runner never reaches secondcase',len(failcalls)==1 and not (failed/'completion.json').exists())
  parent=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/paired_development_evaluator_v2/scoring_implementation_v1/bcsp_p1_pair_score_v1.py'
  def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
  a=funcs(parent);b=funcs(HERE/'bcsp_p2_h1_M0_twofold_score_v1.py')
  inherited=['load_prediction_arrays','load_prediction','select_metrics','position_shape','risk_labels','stage_geometry','csv_rows']
  check('S31 geometry metric arithmetic AST inherited exactly',all(a[k]==b[k] for k in inherited))
  check('S32 metric core exact frozen hash',s.digest(s.METRIC_PATH)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766')
  result=dict(status='ARTIFICIAL_CPU_CONTRACT_PASS',checks_passed=len(checks),checks=checks,python=sys.version,packages={n:s.md.version(n) for n in ['numpy','scipy','psutil','scikit-image']},real_scoring_executed=False,real_archive_or_reference_arrays_read=False,synthetic_actual_metric_case_scores=8,synthetic_orchestrated_rows=840,metric_core_unchanged=True,server_operations=0,GPU_calls=0,limitations=['Full840 orchestration uses analytic-case template metrics; actual metric arithmetic tested on8 artificial model/control rows','No real research score computed'])
  emit('result_v1.json',result);print(json.dumps(dict(status=result['status'],checks_passed=len(checks),synthetic_case_rows=840,real_score_rows=0)))
 except BaseException as e:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(e),checks_passed=len(checks),checks=checks));raise
if __name__=='__main__':main()
