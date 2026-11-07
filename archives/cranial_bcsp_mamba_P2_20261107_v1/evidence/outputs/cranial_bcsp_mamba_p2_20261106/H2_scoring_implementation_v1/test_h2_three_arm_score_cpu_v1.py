"""Synthetic metrics and1050-row orchestration; real inputs used as metadata only."""
import ast,copy,hashlib,importlib.util,io,json,sys,tarfile,time
from pathlib import Path
from contextlib import ExitStack
S=Path(__file__).resolve().parent;R=S.parents[2];O=S/'artificial_cpu_batch_v1'
def main():
 O.mkdir();spec=importlib.util.spec_from_file_location('synthetic_h2_three_arm_scorer',S/'bcsp_p2_h2_M0_three_arm_score_v1.py');s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s);np=s.np;checks=[]
 def check(n,v):
  if not v:raise AssertionError(n)
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError,KeyError):checks.append(n)
  else:raise AssertionError(n)
 def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=s.digest(p))
 def emit(n,v):p=O/n;s.emit(p,v);return rec(p)
 def npz(n,**v):
  p=O/n
  with p.open('xb') as f:np.savez_compressed(f,**v)
  return rec(p)
 try:
  pre=S.parent/'H2_local_score_preparation_v1';realindex=json.loads((S.parent/'H2_fourmodel_prediction_preparation_v1/H2_C_D_fourmodel_input_index_v1.json').read_bytes());realrefs=json.loads((S.parent/'H1_scoring_implementation_20261107_v1/reference_manifest_C_D_v1.json').read_bytes());realcases=json.loads((pre/'H2_M0_twofold_score_case_index_candidate_v1.json').read_bytes())
  check('01 real frozen index/reference metadata210cases',len(s.validate_index(realindex,realrefs,realcases)[2])==210)
  bad=copy.deepcopy(realcases);bad['cases'].pop();reject('02 missing case metadata',lambda:s.validate_index(realindex,realrefs,bad))
  bad=copy.deepcopy(realcases);bad['cases'][0]['normalization']['scale']*=2;reject('03 frame drift',lambda:s.validate_index(realindex,realrefs,bad))
  bad=copy.deepcopy(realindex);bad['inputs'][105]['H2_mode']='AUX';reject('04 H2 row mode mismatch',lambda:s.validate_index(bad,realrefs,realcases))
  bad=copy.deepcopy(realcases);bad['cases'][0]['target_array_sha256']='0'*64;reject('05 GT fingerprint drift',lambda:s.validate_index(realindex,realrefs,bad))
  serial=0
  def chain(yes=True,bad=False):
   nonlocal serial
   serial+=1;qr=emit('q'+str(serial)+'.json',dict(schema='bcsp-p2-H2-M0-three-arm-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,counts=dict(unique_cases=210,sources=42,model_rows=630,shared_control_rows=420,case_score_rows=1049 if bad else 1050,source_score_rows=210)));ar=emit('a'+str(serial)+'.json',dict(schema='bcsp-p2-H2-M0-score-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_TEST_ONLY'));return qr,ar
  s.authorize(*chain());check('06 full1050row explicit authorization contract',True);reject('07 missing execution authorization',lambda:s.authorize(*chain(False)));reject('08 row count drift',lambda:s.authorize(*chain(bad=True)))
  m=s.metric;g=np.zeros((5,5,5),bool);g[2,2,2]=True;d=np.zeros_like(g);d[1,2,2]=True;reference=m.surface_references(g,d,np.eye(3),np.zeros(3));rr=npz('artificial_reference.npz',**reference);gt=np.tile(reference['a_centers'].astype(np.float32),(1366,1))[:8192].copy();point=npz('artificial_point.npz',partial=gt+.25,implant=gt);norm=dict(center=[0.,0.,0.],scale=1.);targetsha=hashlib.sha256(gt.tobytes()).hexdigest();cases=[];refs=[];runs=[];hrows=[];baselineidx={};coarse={};baselinecoarse={}
  for fold,offset in [('C',0),('D',21)]:
   sources=['train:'+str(i).zfill(3) for i in range(offset,offset+21)];ids=['train__'+v.split(':')[1]+'__'+defect for v in sources for defect in sorted(s.DEFECTS)];coarse[fold]=ids[:5];baselinecoarse[fold]=ids[:7 if fold=='C' else 5]
   def run(label,mode=None):return dict(label=label,variant='M0' if not label.endswith('_T0') else 'T0',fold=fold,mode=mode,H2={'mode':mode},seed=0,n_input=8192,n_output=8192,dev_case_ids=ids,dev_sources=sources,train_sources=['train:'+str(i).zfill(3) for i in range(100,163)],checkpoint=dict(sha256=hashlib.sha256(label.encode()).hexdigest()))
   def row(label,cid,mode=None):return dict(run=label,variant='M0',fold=fold,H2_mode=mode,n_input=8192,case_id=cid,source_id='train:'+cid.split('__')[1],normalization=copy.deepcopy(norm),normalization_source='defective_bbox',target_array_sha256=targetsha,input=point)
   for mode in ['AUX','COUPLE']:runs.append(run(fold+'_'+mode,mode));hrows.extend(row(fold+'_'+mode,cid,mode) for cid in ids)
   baselineidx[fold]=dict(runs=[run(fold+'_T0'),run(fold+'_M0')],inputs=[row(fold+'_'+arm,cid) for arm in ['T0','M0'] for cid in ids])
   for cid in ids:
    c=dict(case_id=cid,source_id='train:'+cid.split('__')[1],fold=fold,normalization=copy.deepcopy(norm),normalization_source='defective_bbox',target_array_sha256=targetsha,point_file=point,reference=rr);cases.append(c);refs.append(dict(case_id=cid,source_id=c['source_id'],fold=fold,normalization=copy.deepcopy(norm),target_array_sha256=targetsha,**rr))
  hindex=dict(schema='bcsp-p2-H2-fourmodel-development-index-v1',runs=runs,inputs=hrows);rmanifest=dict(cases=refs);scoreindex=dict(schema='bcsp-p2-H2-M0-twofold-score-index-candidate-v1',cases=cases)
  check('09 artificial fourmodel metadata valid',len(s.validate_index(hindex,rmanifest,scoreindex)[2])==210)
  def stats(x):
   x=x.astype(np.float64);mu=x.mean(0);z=x-mu;return dict(centroid=mu.tolist(),bbox_min=x.min(0).tolist(),bbox_max=x.max(0).tolist(),radius_gyration=float(np.sqrt((z*z).sum(1).mean())),covariance_eigenvalues=np.linalg.eigvalsh(z.T@z/len(x)).tolist())
  rng=dict(CPU='b'*64,CUDA='c'*64,Python='ARTIFICIAL',numpy='ARTIFICIAL')
  def archive(name,index,kind):
   items=[];records=[];geometry=[];runmap={r['label']:r for r in index['runs']}
   for i,x in enumerate(index['inputs'],1):
    shift=(.2 if x['H2_mode']=='AUX' else .1) if kind=='H2' else 0.;pred=(gt+shift).astype(np.float32);cp=pred[:256].copy();arrays=dict(prediction=pred)
    selected=coarse if kind=='H2' else baselinecoarse
    if x['case_id'] in selected[x['fold']]:arrays['coarse']=cp
    stream=io.BytesIO();np.savez_compressed(stream,**arrays);blob=stream.getvalue();member='predictions/'+x['run']+'__'+x['case_id']+'.npz';items.append((member,blob));records.append(dict(run=x['run'],case_id=x['case_id'],source_id=x['source_id'],fold=x['fold'],n_input=8192,n_output=8192,normalization=x['normalization'],input_sha256=x['input']['sha256'],checkpoint_sha256=runmap[x['run']]['checkpoint']['sha256'],forward_index=i,prediction=dict(name=member,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())))
    delta=pred.astype(float).reshape(256,32,3)-cp.astype(float)[:,None,:];geom=dict(run=x['run'],case_id=x['case_id'],frame='native_D_only_normalized_no_GT',coarse=stats(cp),dense=stats(pred),mean_dense_minus_coarse=delta.mean((0,1)).tolist(),offset_mean_squared_radius=float((delta**2).sum(2).mean()))
    if kind=='H2':
     scale=float(np.exp(np.log(1.25)*np.tanh(.1/np.log(1.25)))) if x['H2_mode']=='COUPLE' else 1.;used=dict(centroid=geom['coarse']['centroid'],radius=geom['coarse']['radius_gyration']);raw=dict(centroid=used['centroid'],radius=used['radius']/scale);geom['H2']=dict(mode=x['H2_mode'],delta=[.1],scale=[scale],raw=raw,used=used,condition_override=None,GT_read=False,loss_calls=0)
    geometry.append(geom)
   done=dict(status='P2_H2_FOURMODEL_420_NATIVE_FORWARD_COMPLETE' if kind=='H2' else 'P1_PAIR_210_FORWARD_COMPLETE',forwards=len(index['inputs']),request_sha256='d'*64,training_updates=0,BNCal=0,loss=0,backward=0,models=[dict(run=r['label'],forwards=105,state_before='a'*64,state_after='a'*64,RNG_before=rng,RNG_after=rng,mode='eval_inference_mode',BNCal=0,optimizer=0,backward=0) for r in index['runs']]);claims=[dict(forward_index=i,run=r['run'],case_id=r['case_id'],status='CLAIMED_BEFORE_FORWARD') for i,r in enumerate(records,1)]
   items.extend([(n,'\n'.join(json.dumps(r) for r in data).encode()) for n,data in [('inference_manifest.jsonl',records),('forward_attempts.jsonl',claims),('geometry_summary.jsonl',geometry)]]);items.extend([('inference_complete.json',json.dumps(done).encode()),('resources.jsonl',b'{"ARTIFICIAL":true}\n')]);path=O/name
   with tarfile.open(path,'w:gz') as tar:
    for member,blob in items:info=tarfile.TarInfo(member);info.size=len(blob);tar.addfile(info,io.BytesIO(blob))
   return path
  paths={'H2':archive('artificial_H2.tar.gz',hindex,'H2'),'C':archive('artificial_C.tar.gz',baselineidx['C'],'C'),'D':archive('artificial_D.tar.gz',baselineidx['D'],'D')};allidx=dict(H2=hindex,**baselineidx);plan=dict(archive_inputs={})
  for key,index in allidx.items():
   pro=dict(coarse_tensor_cases_by_fold=coarse) if key=='H2' else dict(coarse_tensor_cases=baselinecoarse[key]);plan['archive_inputs'][key]=dict(archive=rec(paths[key]),prediction_index=emit('index_'+key+'.json',index),prediction_protocol=emit('protocol_'+key+'.json',pro),prediction_request_sha256='d'*64,fold=key)
  with ExitStack() as stack:
   tars={k:stack.enter_context(tarfile.open(path)) for k,path in paths.items()};lookup={}
   for k,index in allidx.items():lookup.update(s.validate_archive(tars[k],index,'d'*64,coarse if k=='H2' else {k:baselinecoarse[k]},k))
   check('10 actual3archive readers select630 models ignoreT0',len(lookup)==630 and {k[1] for k in lookup}==set(s.ARMS))
   templates={f:s.score_case(tars,lookup,cases[0 if f=='C' else 105],lambda:None) for f in ['C','D']};crows=templates['C']
   check('11 actual frozen metric10 artificial rows',len(crows)==5 and [r['arm'] for r in crows]==s.ARMS+s.CONTROLS)
   check('12 shared GT and M0 exact zero CD',crows[0]['metrics']['CD_L1_mm']==crows[-1]['metrics']['CD_L1_mm']==0)
   check('13 artificialAUX worse thanCOUPLE positive errors',crows[1]['metrics']['CD_L1_mm']>crows[2]['metrics']['CD_L1_mm']>0)
   check('14 H2 offline diagnostics only attachedH2',crows[0]['stage_geometry'].get('H2') is None and all(r['stage_geometry']['H2']['GT_used_only_offline'] for r in crows[1:3]))
   bad=copy.deepcopy(next(iter(lookup.values())));bad['prediction']['sha256']='0'*64;reject('15 member hash drift',lambda:s.load_prediction_arrays(tars[bad['archive_key']],bad))
   reject('16 wrong archive execution hash',lambda:s.validate_archive(tars['H2'],hindex,'0'*64,coarse,'H2'))
   wrong=copy.deepcopy(hindex);wrong['runs'][0]['checkpoint']['sha256']='0'*64;reject('17 checkpoint provenance drift',lambda:s.validate_archive(tars['H2'],wrong,'d'*64,coarse,'H2'))
  original=s.score_case;calls=[]
  def artificial(tars,lookup,c,guard):
   guard();calls.append(c['case_id']);part=copy.deepcopy(templates[c['fold']])
   for r in part:r.update(fold=c['fold'],case_id=c['case_id'],source_id=c['source_id'])
   return part
  out=O/'full1050';out.mkdir();s.score_case=artificial
  try:rows=s.run_scoring(plan,hindex,cases,out,paths,'e'*64,lambda:None,time.monotonic())
  finally:s.score_case=original
  check('18 actual full orchestration1050 rows210 cases',len(rows)==1050 and len(calls)==len(set(calls))==210)
  sources=s.aggregate_source(rows);check('19 exact210 source groups five defects each',len(sources)==210 and all(r['case_count']==5 for r in sources))
  result=json.loads((out/'paired_comparison.json').read_bytes());check('20 sourceequal21 per pair per fold',all(x['source_count']==21 for f in ['C','D'] for x in result['comparison'][f].values()))
  c=result['comparison']['C'];check('21 primaryCOUPLEminusAUX negativeCD',c['H2_COUPLE_minus_H2_AUX']['metrics']['CD_L1_mm']['mean_delta_b_minus_a']<0)
  check('22 secondaryCOUPLEminusM0 andAUXminusM0 positiveCD',c['H2_COUPLE_minus_M0']['metrics']['CD_L1_mm']['mean_delta_b_minus_a']>0 and c['H2_AUX_minus_M0']['metrics']['CD_L1_mm']['mean_delta_b_minus_a']>0)
  risks=json.loads((out/'risk_transitions.json').read_bytes());check('23 all6risk comparisons preserve105cases',all(len(x['labels']['severe_geometry']['cases'])==105 for f in ['C','D'] for x in risks[f].values()))
  done=json.loads((out/'completion.json').read_bytes());check('24 exact630models420controls1050rows210sources',done['model_predictions']==630 and done['controls']==420 and done['score_rows']==1050 and done['source_rows']==210 and done['forward_calls']==done['bootstrap']==0 and done['formal_gate'] is False)
  check('25 all630pair deltas keep folds',sum(len(s.case_differences([r for r in rows if r['fold']==f],pair)) for f in ['C','D'] for pair in s.PAIRS)==630)
  bad=copy.deepcopy(rows);bad.pop();reject('26 missing control/defect cannot be dropped',lambda:s.aggregate_source(bad))
  undefined=s.describe_pairs([1,None],[2,3]);check('27 undefined pairs retained',undefined['status']=='UNDEFINED_NONFINITE_PAIRS_RETAINED' and undefined['pair_count']==2 and undefined['mean_delta_b_minus_a'] is None)
  check('28 unchanged20mm and0.9 boundaries',s.risk_labels(dict(E_P95_mm=20,**{'J_coverage_2.0mm':.1}),dict(centroid_offset_mm=20,radius_gyration_ratio=.9))==dict(placement_tail=False,compact_distribution=False,severe_geometry=False))
  check('29 zeroJcoverage still severe',s.risk_labels(dict(E_P95_mm=1,**{'J_coverage_2.0mm':0}),dict(centroid_offset_mm=0,radius_gyration_ratio=1))['severe_geometry'])
  part=copy.deepcopy([r for r in rows if r['fold']=='C'])
  for r in part:r['risk_labels']['severe_geometry']=r['arm']=='H2_COUPLE'
  for pair in [('H2_AUX','H2_COUPLE'),('M0','H2_COUPLE')]:v=s.risk_transitions(part,pair)['labels']['severe_geometry'];check('30 '+pair[0]+' new severe not netted away',v['new']==105 and v['candidate_count']==105)
  failout=O/'failure_stop';failout.mkdir();failcalls=[]
  def failed(*args):failcalls.append(1);raise RuntimeError('ARTIFICIAL_STOP')
  s.score_case=failed
  try:reject('31 firstcase failure stops orchestration',lambda:s.run_scoring(plan,hindex,cases,failout,paths,'f'*64,lambda:None,time.monotonic()))
  finally:s.score_case=original
  check('32 no secondcase or false completion',len(failcalls)==1 and not (failout/'completion.json').exists())
  def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
  old=funcs(S.parent/'H1_scoring_implementation_20261107_v1/bcsp_p2_h1_M0_twofold_score_v1.py');new=funcs(S/'bcsp_p2_h2_M0_three_arm_score_v1.py');keep=['load_prediction_arrays','load_prediction','select_metrics','position_shape','risk_labels','stage_geometry','aggregate_source','csv_rows']
  check('33 exact metric/risk/sourceaggregation AST preserved',all(old[k]==new[k] for k in keep));check('34 frozen metric source hash',s.digest(s.METRIC_PATH)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766')
  emit('result_v1.json',dict(status='H2_THREE_ARM_SCORING_CPU_CONTRACT_PASS',checks_passed=len(checks),checks=checks,python=sys.version,packages={n:s.md.version(n) for n in ['numpy','scipy','psutil','scikit-image']},real_archive_reference_or_point_arrays_read=False,real_score_rows=0,synthetic_actual_metric_rows=10,synthetic_orchestrated_rows=1050,metric_core_unchanged=True,server_operations=0,GPU_calls=0,limitations=['1050-row full orchestration uses two analytic-case templates; exact metric evaluated on10 artificial arm/control rows','No real research score computed']))
  print(json.dumps(dict(status='H2_THREE_ARM_SCORING_CPU_CONTRACT_PASS',checks=len(checks),synthetic_rows=1050,real_score_rows=0)))
 except BaseException as exc:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks));raise
if __name__=='__main__':main()
