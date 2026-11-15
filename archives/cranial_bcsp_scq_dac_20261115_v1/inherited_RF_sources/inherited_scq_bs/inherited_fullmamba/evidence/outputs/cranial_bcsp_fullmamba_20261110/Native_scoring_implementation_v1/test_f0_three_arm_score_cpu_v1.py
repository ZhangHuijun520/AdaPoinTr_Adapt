"""Artificial CPU batch. Real research files are read as metadata only, never scored."""
import ast,copy,hashlib,importlib.util,io,json,sys,tarfile,time
from pathlib import Path
from contextlib import ExitStack
S=Path(__file__).resolve().parent;R=S.parents[2];O=S/'artificial_cpu_batch_v1'
def main():
 O.mkdir();spec=importlib.util.spec_from_file_location('F0_artificial_score_entry',S/'bcsp_f0_T0_M0_three_arm_score_v1.py');s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s);np=s.np;checks=[]
 def check(n,v=True):
  if not v:raise AssertionError(n)
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError,KeyError):checks.append(n);return
  raise AssertionError('unexpected accept: '+n)
 def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=s.digest(p))
 def emit(n,v):p=O/n;s.emit(p,v);return rec(p)
 def npz(n,**data):
  p=O/n
  with p.open('xb') as f:np.savez_compressed(f,**data)
  return rec(p)
 try:
  pre=S.parent/'Native_prediction_implementation_v1/local_download_and_score_preparation_v1';realcases=json.loads((pre/'F0_T0_M0_score_case_index_candidate_v1.json').read_bytes());realindex=json.loads(Path(realcases['archive_inputs']['F0']['prediction_index']['path']).read_bytes());realrefs=json.loads(Path(realcases['reference_manifest']['path']).read_bytes())
  check('01 actual frozen metadata210 cases630 predictions',len(s.validate_index(realindex,realrefs,realcases)[2])==210)
  for n,change in [('02 missing case',lambda x:x['cases'].pop()),('03 normalization drift',lambda x:x['cases'][0]['normalization'].update(scale=1.)),('04 target hash drift',lambda x:x['cases'][0].update(target_array_sha256='0'*64)),('05 duplicate model prediction',lambda x:x['prediction_records'].__setitem__(0,x['prediction_records'][1]))]:
   bad=copy.deepcopy(realcases);change(bad);reject(n,lambda:s.validate_index(realindex,realrefs,bad))
  bad=copy.deepcopy(realindex);bad['inputs'][0]['save_coarse']=False;reject('06 F0 missing required coarse',lambda:s.validate_index(bad,realrefs,realcases))
  serial=0
  def chain(yes=True,bad_count=False,bad_pair=False):
   nonlocal serial
   serial+=1;p=dict(schema='bcsp-f0-T0-M0-three-arm-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,counts=dict(unique_cases=210,sources=42,model_rows=630,shared_control_rows=420,case_score_rows=1049 if bad_count else 1050,source_score_rows=210),scientific_contract=dict(arms=s.ARMS,pairs=[list(p) for p in s.PAIRS],controls=s.CONTROLS),limits=dict(wall_seconds=18000,RSS_bytes=8589934592,output_bytes=2147483648,threads=2))
   if bad_pair:p['scientific_contract']['pairs'][0].reverse()
   qr=emit('q'+str(serial)+'.json',p);ar=emit('a'+str(serial)+'.json',dict(schema='bcsp-f0-T0-M0-score-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_TEST_ONLY'));return qr,ar
  s.authorize(*chain());check('07 actual authorize path correct1050 contract')
  reject('08 explicit authorization required',lambda:s.authorize(*chain(yes=False)));reject('09 row budget drift',lambda:s.authorize(*chain(bad_count=True)));reject('10 pair direction drift',lambda:s.authorize(*chain(bad_pair=True)))
  m=s.metric;g=np.zeros((5,5,5),bool);g[2,2,2]=True;d=np.zeros_like(g);d[1,2,2]=True;ref=m.surface_references(g,d,np.eye(3),np.zeros(3));rr=npz('artificial_reference.npz',**ref);gt=np.tile(ref['a_centers'].astype(np.float32),(1366,1))[:8192].copy();point=npz('artificial_point.npz',partial=gt+.25,implant=gt);norm=dict(center=[0.,0.,0.],scale=1.);targetsha=hashlib.sha256(gt.tobytes()).hexdigest()
  cases=[];refs=[];fruns=[];frows=[];baselines={};baselinecoarse={};cachecases={};tracecases={}
  for fold,offset in [('C',0),('D',21)]:
   sources=['train:'+str(i).zfill(3) for i in range(offset,offset+21)];ids=['train__'+v.split(':')[1]+'__'+typ for v in sources for typ in sorted(s.DEFECTS)]
   baselinecoarse[fold]=ids[:7 if fold=='C' else 5];tracecases[fold]=ids[:5];cachecases[fold]=ids[:10]
   def run(label,variant):return dict(label=label,variant=variant,fold=fold,seed=0,n_input=8192,n_output=8192,dev_case_ids=ids,dev_sources=sources,train_sources=['train:'+str(i).zfill(3) for i in range(100,163)],checkpoint=dict(sha256=hashlib.sha256(label.encode()).hexdigest()))
   def row(label,cid,variant):return dict(run=label,variant=variant,fold=fold,n_input=8192,case_id=cid,source_id='train:'+cid.split('__')[1],normalization=copy.deepcopy(norm),normalization_source='defective_bbox',target_array_sha256=targetsha,input=point,save_coarse=True,cache_context=cid in cachecases[fold],save_full_decoder_trace=cid in tracecases[fold])
   fruns.append(run(fold+'_F0','F0-P-v2'));frows.extend(row(fold+'_F0',cid,'F0-P-v2') for cid in ids)
   baselines[fold]=dict(runs=[run(fold+'_T0','T0'),run(fold+'_M0','M0')],inputs=[row(fold+'_'+arm,cid,arm) for arm in ['T0','M0'] for cid in ids])
   for cid in ids:
    c=dict(case_id=cid,source_id='train:'+cid.split('__')[1],fold=fold,normalization=copy.deepcopy(norm),normalization_source='defective_bbox',target_array_sha256=targetsha,point_file=point,reference=rr);cases.append(c);refs.append(dict(case_id=cid,source_id=c['source_id'],fold=fold,normalization=copy.deepcopy(norm),target_array_sha256=targetsha,**rr))
  fidx=dict(schema='bcsp-f0-native-development-index-candidate-v1',runs=fruns,inputs=frows);refmanifest=dict(cases=refs)
  def stats(x):
   x=x.astype(np.float64);mean=x.mean(0);z=x-mean;return dict(centroid=mean.tolist(),bbox_min=x.min(0).tolist(),bbox_max=x.max(0).tolist(),radius_gyration=float(np.sqrt((z*z).sum(1).mean())),covariance_eigenvalues=np.linalg.eigvalsh(z.T@z/len(x)).tolist())
  rng=dict(CPU='b'*64,CUDA='c'*64,Python='ARTIFICIAL',numpy='ARTIFICIAL');bindings=[]
  def make_archive(name,index,kind):
   items=[];man=[];geom=[];runmap={r['label']:r for r in index['runs']}
   for i,row in enumerate(index['inputs'],1):
    arm='F0' if kind=='F0' else row['variant'];shift={'T0':0.,'M0':.2,'F0':.1}[arm];pred=(gt+shift).astype(np.float32);cp=pred[:256].copy();withcoarse=kind=='F0' or row['case_id'] in baselinecoarse[row['fold']]
    if kind=='F0' and row['cache_context']:
     # These exact diagnostic members are not scored or array-decoded by this entry.
     items.append(('context/'+row['run']+'__'+row['case_id']+'.npz',b'ARTIFICIAL_DIAGNOSTIC_CONTEXT_NOT_A_PREDICTION'))
     if row['save_full_decoder_trace']:items.append(('traces/'+row['run']+'__'+row['case_id']+'.npz',b'ARTIFICIAL_DIAGNOSTIC_TRACE_NOT_A_PREDICTION'))
    data=dict(prediction=pred)
    if withcoarse:data['coarse']=cp
    buf=io.BytesIO();np.savez_compressed(buf,**data);blob=buf.getvalue();member='predictions/'+row['run']+'__'+row['case_id']+'.npz';items.append((member,blob))
    pr=dict(name=member,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest());bindings.append(dict(arm=arm,fold=row['fold'],case_id=row['case_id'],archive_key=kind,member=member,bytes=len(blob),sha256=pr['sha256'],coarse_saved=withcoarse))
    man.append(dict(run=row['run'],case_id=row['case_id'],source_id=row['source_id'],fold=row['fold'],n_input=8192,n_output=8192,normalization=row['normalization'],input_sha256=row['input']['sha256'],checkpoint_sha256=runmap[row['run']]['checkpoint']['sha256'],forward_index=i,prediction=pr))
    off=pred.astype(float).reshape(256,32,3)-cp.astype(float)[:,None,:]
    geom.append(dict(run=row['run'],case_id=row['case_id'],frame='native_D_only_normalized_no_GT',coarse=stats(cp),dense=stats(pred),mean_dense_minus_coarse=off.mean((0,1)).tolist(),offset_mean_squared_radius=float((off**2).sum(2).mean())))
   models=[dict(run=r['label'],forwards=105,state_before='a'*64,state_after='a'*64,RNG_before=rng,RNG_after=rng,mode='eval_inference_mode',BNCal=0,optimizer=0,backward=0) for r in index['runs']]
   done=dict(status='F0_CD_210_NATIVE_FORWARD_COMPLETE' if kind=='F0' else 'P1_PAIR_210_FORWARD_COMPLETE',forwards=210,request_sha256='d'*64,training_updates=0,BNCal=0,loss=0,backward=0,models=models)
   claims=[dict(forward_index=i,run=r['run'],case_id=r['case_id'],status='CLAIMED_BEFORE_FORWARD') for i,r in enumerate(man,1)]
   logs=[('inference_manifest.jsonl',man),('forward_attempts.jsonl',claims),('geometry_summary.jsonl',geom)]
   if kind=='F0':logs.append(('cache_manifest.jsonl',[dict(ARTIFICIAL=True)]))
   items.extend((n,'\n'.join(json.dumps(r) for r in rows).encode()) for n,rows in logs);items.extend([('inference_complete.json',json.dumps(done).encode()),('resources.jsonl',b'{"ARTIFICIAL":true}\n')])
   path=O/name
   with tarfile.open(path,'w:gz') as t:
    for n,b in items:info=tarfile.TarInfo(n);info.size=len(b);t.addfile(info,io.BytesIO(b))
   return path
  paths={'F0':make_archive('artificial_F0.tar.gz',fidx,'F0'),'C':make_archive('artificial_C.tar.gz',baselines['C'],'C'),'D':make_archive('artificial_D.tar.gz',baselines['D'],'D')}
  allindex=dict(F0=fidx,**baselines);plan=dict(archive_inputs={})
  for kind,index in allindex.items():
   proto=dict(forwards=210) if kind=='F0' else dict(coarse_tensor_cases=baselinecoarse[kind])
   plan['archive_inputs'][kind]=dict(archive=rec(paths[kind]),prediction_index=emit('index_'+kind+'.json',index),prediction_protocol=emit('protocol_'+kind+'.json',proto),prediction_request_sha256='d'*64,fold=kind)
  scoreindex=dict(schema='bcsp-f0-T0-M0-twofold-score-index-candidate-v1',cases=cases,prediction_records=bindings,model_arms=s.ARMS,controls=s.CONTROLS)
  check('11 artificial630 metadata index',len(s.validate_index(fidx,refmanifest,scoreindex)[2])==210)
  with ExitStack() as stack:
   tars={k:stack.enter_context(tarfile.open(path,'r:gz')) for k,path in paths.items()};lookup={}
   for kind,index in allindex.items():lookup.update(s.validate_archive(tars[kind],index,'d'*64,cachecases if kind=='F0' else {kind:baselinecoarse[kind]},kind))
   check('12 actual three archive readers return630 all arms',len(lookup)==630 and {k[1] for k in lookup}==set(s.ARMS))
   check('13 all F0 Q baseline optionalQ counts',[sum(r['coarse_expected'] for k,r in lookup.items() if k[1]==arm) for arm in s.ARMS]==[12,12,210])
   templates={f:s.score_case(tars,lookup,cases[0 if f=='C' else 105],lambda:None) for f in ['C','D']}
   crows=templates['C'];check('14 real frozen metric10 synthetic rows',len(crows)==5 and [r['arm'] for r in crows]==s.ARMS+s.CONTROLS)
   check('15 analytic T0 and GT zero CD',crows[0]['metrics']['CD_L1_mm']==crows[-1]['metrics']['CD_L1_mm']==0)
   check('16 analytic F0 improves M0 but worse T0',crows[1]['metrics']['CD_L1_mm']>crows[2]['metrics']['CD_L1_mm']>crows[0]['metrics']['CD_L1_mm'])
   absent=s.score_case(tars,lookup,cases[10],lambda:None)
   check('17 actual no-coarse baseline load and all-F0Q',all(r['stage_geometry']['coarse']['tensor_saved'] is False for r in absent[:2]) and absent[2]['stage_geometry']['coarse']['tensor_saved'] is True)
   check('18 no H2 diagnostics or extra cache scoring',all('H2' not in r['stage_geometry'] for r in crows[:3]) and len(lookup)==630)
   bad=copy.deepcopy(lookup[('C','F0',cases[0]['case_id'])]);bad['prediction']['sha256']='0'*64;reject('19 prediction member hash drift',lambda:s.load_prediction_arrays(tars['F0'],bad))
   bad=copy.deepcopy(lookup[('C','F0',cases[0]['case_id'])]);bad['coarse_expected']=False;reject('20 unexpected coarse forbidden',lambda:s.load_prediction_arrays(tars['F0'],bad))
   reject('21 wrong execution request hash',lambda:s.validate_archive(tars['F0'],fidx,'0'*64,cachecases,'F0'))
   bad=copy.deepcopy(fidx);bad['runs'][0]['checkpoint']['sha256']='0'*64;reject('22 checkpoint provenance drift',lambda:s.validate_archive(tars['F0'],bad,'d'*64,cachecases,'F0'))
   bad=copy.deepcopy(fidx);bad['inputs'][0]['cache_context']=False;reject('23 cache whitelist mismatch',lambda:s.validate_archive(tars['F0'],bad,'d'*64,cachecases,'F0'))
  calls=[];original=s.score_case
  def artificial(tars,lookup,c,guard):
   guard();calls.append(c['case_id']);part=copy.deepcopy(templates[c['fold']])
   for r in part:
    r.update(fold=c['fold'],case_id=c['case_id'],source_id=c['source_id'])
    if r['arm'] in s.ARMS:r['stage_geometry']['coarse']['tensor_saved']=r['arm']=='F0' or c['case_id'] in baselinecoarse[c['fold']]
   return part
  out=O/'full1050';out.mkdir();s.score_case=artificial
  try:result=s.run_scoring(plan,fidx,cases,out,paths,'e'*64,lambda:None,time.monotonic(),prediction_bindings=bindings)
  finally:s.score_case=original
  check('24 actual1050 orchestration counts210 unique case calls',len(result)==1050 and len(calls)==len(set(calls))==210)
  source=s.aggregate_source(result);check('25 source210 groups with five defects each',len(source)==210 and all(r['case_count']==5 for r in source))
  comparison=json.loads((out/'paired_comparison.json').read_bytes());c=comparison['comparison']['C']
  check('26 all six comparisons21source equal',all(v['source_count']==21 for f in ['C','D'] for v in comparison['comparison'][f].values()))
  check('27 F0minusM0 correct negativeCD',c['F0_minus_M0']['metrics']['CD_L1_mm']['mean_delta_b_minus_a']<0)
  check('28 F0minusT0 andM0minusT0 correct positiveCD',c['F0_minus_T0']['metrics']['CD_L1_mm']['mean_delta_b_minus_a']>0 and c['M0_minus_T0']['metrics']['CD_L1_mm']['mean_delta_b_minus_a']>0)
  complete=json.loads((out/'completion.json').read_bytes());check('29 exact630models420shared1050rows210sources',complete['model_predictions']==630 and complete['controls']==420 and complete['score_rows']==1050 and complete['source_rows']==210 and complete['forward_calls']==complete['bootstrap']==0 and complete['formal_gate'] is False)
  risk=json.loads((out/'risk_transitions.json').read_bytes());check('30 each riskpair105 cases preserved',all(len(v['labels']['severe_geometry']['cases'])==105 for f in ['C','D'] for v in risk[f].values()))
  bad=copy.deepcopy(result);bad.pop();reject('31 missing defect or control cannot be dropped',lambda:s.aggregate_source(bad))
  undefined=s.describe_pairs([1,None],[2,3]);check('32 undefined pairs retained not silently dropped',undefined['pair_count']==2 and undefined['status']=='UNDEFINED_NONFINITE_PAIRS_RETAINED' and undefined['mean_delta_b_minus_a'] is None)
  check('33 strict20mm0.9 boundaries unchanged',s.risk_labels(dict(E_P95_mm=20,**{'J_coverage_2.0mm':.1}),dict(centroid_offset_mm=20,radius_gyration_ratio=.9))==dict(placement_tail=False,compact_distribution=False,severe_geometry=False))
  check('34 zero contact coverage remains severe',s.risk_labels(dict(E_P95_mm=1,**{'J_coverage_2.0mm':0}),dict(centroid_offset_mm=0,radius_gyration_ratio=1))['severe_geometry'])
  part=copy.deepcopy([r for r in result if r['fold']=='C'])
  for r in part:r['risk_labels']['severe_geometry']=r['arm']=='F0'
  for pair in [('M0','F0'),('T0','F0')]:
   rr=s.risk_transitions(part,pair)['labels']['severe_geometry'];check('35 '+pair[0]+' new severe cases separately',rr['new']==105 and rr['rescued']==0)
  badbinding=copy.deepcopy(bindings);badbinding[0]['sha256']='0'*64;fail=O/'wrong_binding';fail.mkdir()
  reject('36 exact pre-scoring member index binding',lambda:s.run_scoring(plan,fidx,cases,fail,paths,'f'*64,lambda:None,time.monotonic(),prediction_bindings=badbinding))
  fail=O/'forced_failure';fail.mkdir();failcalls=[]
  def broken(*args):failcalls.append(1);raise RuntimeError('ARTIFICIAL_STOP')
  s.score_case=broken
  try:reject('37 first case failure stops whole batch',lambda:s.run_scoring(plan,fidx,cases,fail,paths,'f'*64,lambda:None,time.monotonic(),prediction_bindings=bindings))
  finally:s.score_case=original
  check('38 no second case or false completion',len(failcalls)==1 and not (fail/'completion.json').exists())
  def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
  old=funcs(R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_scoring_implementation_v1/bcsp_p2_h2_M0_three_arm_score_v1.py');new=funcs(S/'bcsp_f0_T0_M0_three_arm_score_v1.py');keep=['load_prediction_arrays','load_prediction','select_metrics','position_shape','risk_labels','stage_geometry','aggregate_source','describe_pairs','paired_summary','case_differences','defect_summary','csv_rows','risk_transitions']
  check('39 all inherited metric/risk/source/pair functions AST unchanged',all(old[k]==new[k] for k in keep))
  check('40 frozen metric exactSHA256',s.digest(s.METRIC_PATH)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766')
  check('41 D-only inverse to world unchanged',np.array_equal(s.metric.world_points(np.array([[1.,2.,3.]],np.float32),dict(scale=2.,center=[10.,20.,30.])),np.array([[12.,24.,36.]])))
  emit('result_v1.json',dict(status='F0_T0_M0_SCORING_CPU_CONTRACT_PASS',checks_passed=len(checks),checks=checks,python=sys.version,packages={n:s.md.version(n) for n in ['numpy','scipy','psutil','scikit-image']},source_bindings=[rec(S/'bcsp_f0_T0_M0_three_arm_score_v1.py'),rec(Path(__file__)),rec(s.METRIC_PATH)],real_score_rows=0,real_archive_reference_point_arrays_read=False,synthetic_actual_metric_rows=15,synthetic_orchestrated_rows=1050,server_operations=0,GPU_calls=0,limitations=['1050-row orchestration uses two artificial-case templates; actual metric evaluated on15 artificial model/control rows','Fake diagnostic cache payloads intentionally never decoded/scored; real caches already formally frozen','Metadata contracts used real source indices only; no real prediction/GT arrays read']))
  print(json.dumps(dict(status='F0_T0_M0_SCORING_CPU_CONTRACT_PASS',checks=len(checks),synthetic_orchestrated_rows=1050,synthetic_actual_metric_rows=15,real_score_rows=0)),flush=True)
 except BaseException as exc:emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc)));raise
if __name__=='__main__':main()
