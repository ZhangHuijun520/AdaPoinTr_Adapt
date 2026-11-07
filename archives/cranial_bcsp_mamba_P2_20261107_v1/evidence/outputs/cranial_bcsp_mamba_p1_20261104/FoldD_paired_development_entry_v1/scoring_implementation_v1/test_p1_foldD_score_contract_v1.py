"""One artificial CPU batch. No real prediction/archive/reference payload reads."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import copy,hashlib,importlib.metadata as md,io,json,sys,tarfile,unittest,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bcsp_p1_foldD_pair_score_v1 as s
np=s.np;m=s.metric
N=Path(__file__).resolve().parent;F=N/'cpu_contract_v1'
def binding(path):return dict(path=str(path),bytes=path.stat().st_size,sha256=s.digest(path))
def jsonfile(name,value):
 p=F/name
 with p.open('x') as f:json.dump(value,f)
 return binding(p)
def npzfile(name,**value):
 p=F/name
 with p.open('xb') as f:np.savez_compressed(f,**value)
 return binding(p)
def model_rows():
 rows=[]
 for k in range(21):
  for j,defect in enumerate(sorted(s.DEFECTS)):
   for arm in s.ARMS:
    rows.append(dict(fold='D',source_id='train:'+str(k).zfill(3),case_id='train__'+str(k).zfill(3)+'__'+defect,arm=arm,status='OK',metrics=dict(E_P95_mm=float(k+j+(1 if arm=='T0' else 0)),J_coverage_2mm=.5 if arm=='T0' else .75)))
 return rows
class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  F.mkdir()
  g=np.zeros((5,5,5),bool);g[2,2,2]=True;d=np.zeros_like(g);d[1,2,2]=True
  cls.ref=m.surface_references(g,d,np.eye(3),np.zeros(3));refrecord=npzfile('synthetic_reference.npz',**cls.ref)
  target=np.tile(cls.ref['a_centers'].astype(np.float32),(1366,1))[:8192].copy();cls.target=target
  cls.point=npzfile('synthetic_V1.npz',partial=target+.25,implant=target)
  ids=['train__'+str(k).zfill(3)+'__'+defect for k in range(21) for defect in sorted(s.DEFECTS)];sources=['train:'+str(k).zfill(3) for k in range(21)]
  cls.cases=[dict(case_id=cid,source_id='train:'+cid.split('__')[1],fold='D',normalization=dict(center=[0.,0.,0.],scale=1.),target_array_sha256=hashlib.sha256(target.tobytes()).hexdigest(),point_file=cls.point,reference=refrecord) for cid in ids]
  refs=[dict(case_id=c['case_id'],source_id=c['source_id'],fold='D',normalization=c['normalization'],target_array_sha256=c['target_array_sha256'],**refrecord) for c in cls.cases]
  cls.refs=dict(status='FROZEN_EXISTING_FOLD_D_105_REFERENCES',cases=refs);cls.score_index=dict(schema='bcsp-p1-paired-score-case-index-preparation-v1',cases=cls.cases)
  runs=[dict(label='D_'+a,variant=a,seed=0,fold='D',n_input=8192,n_output=8192,dev_case_ids=ids,dev_sources=sources,train_sources=['train:999'],checkpoint=dict(sha256=str(k+1)*64)) for k,a in enumerate(s.ARMS)]
  inputs=[dict(run='D_'+a,variant=a,fold='D',n_input=8192,case_id=c['case_id'],source_id=c['source_id'],normalization=c['normalization'],target_array_sha256=c['target_array_sha256'],input=dict(cls.point,path='/synthetic_server/'+c['case_id']+'.npz')) for a in s.ARMS for c in cls.cases]
  cls.index=dict(schema='bcsp-p1-paired-development-index-v1',runs=runs,inputs=inputs)
  cls.coarse_cases=ids[:5];cls.records=[];cls.payload=[];cls.geometry=[]
  def stats(x):
   y=x.astype(np.float64);mean=y.mean(0);c=y-mean
   return dict(centroid=mean.tolist(),bbox_min=y.min(0).tolist(),bbox_max=y.max(0).tolist(),radius_gyration=float(np.sqrt((c*c).sum(1).mean())),covariance_eigenvalues=np.linalg.eigvalsh(c.T@c/len(y)).tolist())
  for k,i in enumerate(inputs):
   pred=target.copy();coarse=pred[:256].copy();arrays=dict(prediction=pred)
   if i['case_id'] in cls.coarse_cases:arrays['coarse']=coarse
   mem=io.BytesIO();np.savez_compressed(mem,**arrays);blob=mem.getvalue()
   name='predictions/'+i['run']+'__'+i['case_id']+'.npz';cls.payload.append((name,blob))
   cls.records.append(dict(run=i['run'],case_id=i['case_id'],source_id=i['source_id'],fold='D',n_input=8192,n_output=8192,normalization=i['normalization'],input_sha256=i['input']['sha256'],checkpoint_sha256=runs[k//105]['checkpoint']['sha256'],forward_index=k+1,prediction=dict(name=name,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())))
   offset=pred.astype(np.float64).reshape(256,32,3)-coarse.astype(np.float64)[:,None,:]
   cls.geometry.append(dict(run=i['run'],case_id=i['case_id'],frame='native_D_only_normalized_no_GT',dense=stats(pred),coarse=stats(coarse),mean_dense_minus_coarse=offset.mean((0,1)).tolist(),offset_mean_squared_radius=float((offset**2).sum(2).mean())))
  rng=dict(CPU='b'*64,CUDA='c'*64,Python='synthetic',numpy='synthetic')
  evidence=[dict(run=r['label'],forwards=105,state_before='a'*64,state_after='a'*64,RNG_before=copy.deepcopy(rng),RNG_after=copy.deepcopy(rng),mode='eval_inference_mode',BNCal=0,optimizer=0,backward=0) for r in runs]
  cls.done=dict(status='P1_PAIR_210_FORWARD_COMPLETE',forwards=210,request_sha256='d'*64,models=evidence,training_updates=0,BNCal=0,loss=0,backward=0)

 @classmethod
 def archive(cls,records=None,done=None,drop=False,duplicate=False,payload=None):
  out=io.BytesIO();items=list(cls.payload if payload is None else payload)
  claims=[dict(forward_index=k+1,run=r['run'],case_id=r['case_id'],status='CLAIMED_BEFORE_FORWARD') for k,r in enumerate(cls.records)]
  items+=[('inference_manifest.jsonl','\n'.join(json.dumps(r) for r in (cls.records if records is None else records)).encode()),('forward_attempts.jsonl','\n'.join(json.dumps(r) for r in claims).encode()),('geometry_summary.jsonl','\n'.join(json.dumps(r) for r in cls.geometry).encode()),('inference_complete.json',json.dumps(cls.done if done is None else done).encode()),('resources.jsonl',b'{"synthetic":true}\n')]
  if drop:items.pop(0)
  if duplicate:items[1]=items[0]
  with tarfile.open(fileobj=out,mode='w:gz') as tf:
   for name,blob in items:
    r=tarfile.TarInfo(name);r.size=len(blob);tf.addfile(r,io.BytesIO(blob))
  out.seek(0);return tarfile.open(fileobj=out,mode='r:gz')
 def test_01_artificial_full_index(self):self.assertEqual(len(s.validate_index(self.index,self.refs,self.score_index)[2]),105)
 def test_02_missing_reference(self):
  x=copy.deepcopy(self.refs);x['cases'].pop()
  with self.assertRaises(ValueError):s.validate_index(self.index,x,self.score_index)
 def test_03_training_source_rejected(self):
  x=copy.deepcopy(self.index);x['runs'][0]['train_sources'].append('train:000')
  with self.assertRaises(ValueError):s.validate_index(x,self.refs,self.score_index)
 def test_04_target_frame_order_mismatch(self):
  for key,value in [('target_array_sha256','bad'),('normalization',dict(center=[1,2,3],scale=2)),('input',dict(path='/bad',bytes=1,sha256='bad'))]:
   x=copy.deepcopy(self.index);x['inputs'][105][key]=value
   with self.assertRaises(ValueError):s.validate_index(x,self.refs,self.score_index)
 def test_05_full215_member_reader(self):
  with self.archive() as tf:self.assertEqual(len(s.validate_archive(tf,self.index,'d'*64,self.coarse_cases)),210)
 def test_06_missing_member_rejected(self):
  with self.archive(drop=True) as tf:
   with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64,self.coarse_cases)
 def test_07_duplicate_member_rejected(self):
  with self.archive(duplicate=True) as tf:
   with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64,self.coarse_cases)
 def test_08_wrong_checkpoint_provenance(self):
  x=copy.deepcopy(self.records);x[0]['checkpoint_sha256']='bad'
  with self.archive(records=x) as tf:
   with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64,self.coarse_cases)
 def test_09_counts_and_RNG_failure(self):
  for field in ['count','RNG','BNCal']:
   x=copy.deepcopy(self.done)
   if field=='count':x['forwards']=209
   elif field=='RNG':x['models'][1]['RNG_after']['CUDA']='bad'
   else:x['BNCal']=1
   with self.archive(done=x) as tf:
    with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64,self.coarse_cases)
 def test_10_malformed_prediction_stops(self):
  for pred in [np.zeros((8,3),np.float32),np.full((8192,3),np.nan,np.float32),np.zeros((8192,3),np.float64)]:
   mem=io.BytesIO();np.savez_compressed(mem,prediction=pred);blob=mem.getvalue();r=copy.deepcopy(self.records[0]);r['coarse_expected']=False;r['prediction'].update(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
   payload=list(self.payload);payload[0]=(payload[0][0],blob)
   with self.archive(payload=payload) as tf:
    with self.assertRaises(ValueError):s.load_prediction(tf,r)
 def test_11_exact_shared_GT_required(self):
  target=self.target.copy();target[0,0]=1.;bad=npzfile('synthetic_bad_GT.npz',partial=self.target,implant=target);case=copy.deepcopy(self.cases[0]);case['point_file']=bad
  with self.archive() as tf:
   lookup=s.validate_archive(tf,self.index,'d'*64,self.coarse_cases)
   with self.assertRaises(ValueError):s.score_case(tf,lookup,case,lambda:None)
 def test_12_integrated_case_reader_four_scores(self):
  with self.archive() as tf:
   lookup=s.validate_archive(tf,self.index,'d'*64,self.coarse_cases);rows=s.score_case(tf,lookup,self.cases[0],lambda:None)
   self.assertEqual([r['arm'] for r in rows],s.ARMS+s.CONTROLS);self.assertEqual(len(rows),4);self.assertEqual(rows[-1]['metrics']['CD_L1_mm'],0.)
 def test_13_area_weighted_P95(self):self.assertEqual(m.weighted_quantile([0,10],[99,1]),0.)
 def test_14_E_J_reference_and_mm(self):
  self.assertEqual(self.ref['a_is_j'].sum(),1);np.testing.assert_array_equal(m.world_points([[1,2,3]],dict(center=[2,3,4],scale=2)),[[4,7,10]])
  self.assertEqual(m.stats([.5,1,2])['coverage']['2.0'],1.)
 def test_15_symmetric_CD_unsquared(self):self.assertEqual(m.score_cloud([[0,0,0]],self.ref,[[3,4,0]])['CD_L1_mm'],5.)
 def test_16_source_five_defect_mean(self):
  x=s.aggregate_source(model_rows());self.assertEqual(len(x),42);self.assertEqual(x[0]['case_count'],5)
 def test_17_missing_or_duplicate_defect_rejected(self):
  rows=model_rows();rows.pop()
  with self.assertRaises(ValueError):s.aggregate_source(rows)
  rows=model_rows();rows[0]['case_id']=rows[2]['case_id']
  with self.assertRaises(ValueError):s.aggregate_source(rows)
 def test_18_source_equal_distance_and_coverage_direction(self):
  out=s.paired_summary(s.aggregate_source(model_rows()));e=out['metrics']['E_P95_mm'];j=out['metrics']['J_coverage_2mm']
  self.assertEqual(e['mean_delta_M0_minus_T0'],-1.);self.assertEqual(e['improved_sources'],21);self.assertEqual(j['mean_delta_M0_minus_T0'],.25);self.assertEqual(j['improved_sources'],21)
 def test_19_nonfinite_pair_not_dropped(self):
  rows=s.aggregate_source(model_rows());rows[0]['metrics']['E_P95_mm']=None;x=s.paired_summary(rows)['metrics']['E_P95_mm']
  self.assertEqual(x['pair_count'],21);self.assertEqual(x['undefined_pairs'],1);self.assertIsNone(x['mean_delta_M0_minus_T0']);self.assertEqual(len(x['source_deltas']),21)
 def test_20_no_bootstrap_or_RNG_consumption(self):
  old=m.paired_bootstrap;m.paired_bootstrap=lambda *a,**k:(_ for _ in ()).throw(AssertionError('bootstrap forbidden'))
  try:
   before=np.random.get_state();r=s.paired_summary(s.aggregate_source(model_rows()));after=np.random.get_state();self.assertTrue(r['no_bootstrap']);np.testing.assert_array_equal(before[1],after[1]);self.assertEqual(before[2:],after[2:])
  finally:m.paired_bootstrap=old
 def test_21_all105_case_and_five_defect_summaries(self):
  rows=model_rows();self.assertEqual(len(s.case_differences(rows)),105);self.assertEqual(len(s.defect_summary(rows)),5);self.assertTrue(all(v['paired_cases']==21 for v in s.defect_summary(rows).values()))
 def chain(self,prefix,reverse=False,drift=False):
  q=jsonfile(prefix+'_request.json',dict(schema='bcsp-p1-foldD-paired-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,fold='D'))
  a=dict(schema='bcsp-p1-paired-score-authorization-v1',request_sha256='bad' if drift else q['sha256'],explicit_user_authorization=True,user_authorization_text='SYNTHETIC FIXTURE ONLY; not production authorization')
  if reverse:a['runtime_sha256']='bad'
  return q,jsonfile(prefix+'_authorization.json',a)
 def test_22_artificial_authorization_chain(self):self.assertEqual(s.authorize(*self.chain('good'))['status'],'AWAITING_EXPLICIT_USER_AUTHORIZATION')
 def test_23_authorization_drift_and_reverse_rejected(self):
  for kw in [dict(reverse=True),dict(drift=True)]:
   with self.assertRaises(ValueError):s.authorize(*self.chain('bad'+str(len(list(F.iterdir()))),**kw))
 def test_24_metric_source_unchanged_no_Torch(self):
  original=N.parents[2]/'cranial_bcsp_geov1_20261024/development_eval_v1/bcsp_eval_metrics_v1.py'
  self.assertEqual(s.digest(Path(m.__file__)),s.digest(original));self.assertNotIn('torch',sys.modules)
 def test_25_all_four_RNG_streams_rejected(self):
  for key in ['CPU','CUDA','Python','numpy']:
   done=copy.deepcopy(self.done);done['models'][0]['RNG_after'][key]='bad'
   with self.archive(done=done) as tf:
    with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64,self.coarse_cases)
 def test_26_optional_coarse_exact10(self):
  count=0
  with self.archive() as tf:
   lookup=s.validate_archive(tf,self.index,'d'*64,self.coarse_cases)
   for record in lookup.values():count+=int('coarse' in s.load_prediction_arrays(tf,record))
  self.assertEqual(count,10)
 def test_27_unexpected_coarse_rejected(self):
  r=copy.deepcopy(self.records[0]);r['coarse_expected']=False
  with self.archive() as tf:
   with self.assertRaises(ValueError):s.load_prediction_arrays(tf,r)
 def test_28_missing_coarse_rejected(self):
  r=copy.deepcopy(self.records[8]);r['coarse_expected']=True
  with self.archive() as tf:
   with self.assertRaises(ValueError):s.load_prediction_arrays(tf,r)
 def test_29_native_world_pose_no_alignment(self):
  gt=np.array([[-1,0,0],[1,0,0]],np.float64);pose=s.position_shape(gt+[21,0,0],gt)
  self.assertAlmostEqual(pose['centroid_offset_mm'],21.);self.assertAlmostEqual(pose['radius_gyration_ratio'],1.)
 def test_30_strict_threshold_boundaries(self):
  metrics=dict(E_P95_mm=20.,**{'J_coverage_2.0mm':1.})
  self.assertEqual(s.risk_labels(metrics,dict(centroid_offset_mm=20.,radius_gyration_ratio=.9)),dict(placement_tail=False,compact_distribution=False,severe_geometry=False))
  metrics['E_P95_mm']=20.001;self.assertTrue(s.risk_labels(metrics,dict(centroid_offset_mm=20.001,radius_gyration_ratio=.899))['severe_geometry'])
 def test_31_zero_J_coverage_severe(self):
  self.assertTrue(s.risk_labels(dict(E_P95_mm=1.,**{'J_coverage_2.0mm':0.}),dict(centroid_offset_mm=0.,radius_gyration_ratio=1.))['severe_geometry'])
 def test_32_zero_radius_prediction_allowed_labelled(self):
  gt=np.array([[-1,0,0],[1,0,0]],np.float64);pose=s.position_shape(np.zeros((8192,3)),gt);self.assertEqual(pose['radius_gyration_ratio'],0.)
 def test_33_population_ratio_matches_prior_equal_counts(self):
  a=self.target.astype(np.float64);p=a*.8+[3,0,0];pose=s.position_shape(p,a);ratio=np.sqrt(np.trace(np.cov(p.T))/np.trace(np.cov(a.T)));self.assertAlmostEqual(pose['radius_gyration_ratio'],ratio)
 def test_34_stage_decomposition(self):
  g=self.geometry[0];r=s.stage_geometry(g,self.target.astype(np.float64),self.target.astype(np.float64),dict(center=[0,0,0],scale=1),self.target[:256].astype(np.float64))
  self.assertTrue(r['coarse']['tensor_saved']);self.assertAlmostEqual(r['dense']['prediction_radius_gyration_mm']**2,r['coarse']['radius_gyration_mm']**2+r['offset_centered_variance_mm2']+r['cross_term_twice_covariance_mm2'])
 def test_35_stage_frame_mismatch_rejected(self):
  g=copy.deepcopy(self.geometry[0]);g['dense']['centroid'][0]+=1
  with self.assertRaises(ValueError):s.stage_geometry(g,self.target,self.target,dict(center=[0,0,0],scale=1))
 def test_36_coarse_tensor_mismatch_rejected(self):
  with self.assertRaises(ValueError):s.stage_geometry(self.geometry[0],self.target,self.target,dict(center=[0,0,0],scale=1),self.target[:256]+1)
 def test_37_radius_ratio_has_no_win_direction(self):
  rows=model_rows()
  for row in rows:row['metrics']['radius_gyration_ratio']=.8 if row['arm']=='T0' else 1.2
  summary=s.paired_summary(s.aggregate_source(rows))['metrics']['radius_gyration_ratio'];self.assertEqual(summary['improvement_direction'],'descriptive_not_ordered');self.assertNotIn('improved_sources',summary)
 def test_38_risk_transitions_all_pairs(self):
  rows=model_rows()
  for row in rows:row['risk_labels']=dict(placement_tail=row['arm']=='T0',compact_distribution=row['arm']=='M0',severe_geometry=False)
  labels=s.risk_transitions(rows)['labels'];self.assertEqual(labels['placement_tail']['rescued'],105);self.assertEqual(labels['compact_distribution']['new'],105);self.assertEqual(len(labels['severe_geometry']['cases']),105)
 def test_39_gt_control_zero_CD_no_duplicate_Nop(self):
  with self.archive() as tf:
   lookup=s.validate_archive(tf,self.index,'d'*64,self.coarse_cases);rows=s.score_case(tf,lookup,self.cases[8],lambda:None)
  self.assertEqual([r['arm'] for r in rows],['T0','M0','Nop_D','GT_8192']);self.assertEqual(rows[3]['metrics']['CD_L1_mm'],0.)
 def test_40_integrated105_case420_row_runner(self):
  out=F/'full105';out.mkdir();archive=F/'synthetic_full215.tar.gz'
  with self.archive() as tf:
   # Preserve the complete synthetic archive bytes, not just reconstructed metadata.
   with tarfile.open(archive,'w:gz') as dest:
    for member in tf.getmembers():dest.addfile(member,tf.extractfile(member))
  protocol=jsonfile('synthetic_prediction_protocol.json',dict(coarse_tensor_cases=self.coarse_cases));plan=dict(prediction_protocol=protocol,prediction_entry_request_sha256='d'*64,downloaded_prediction_archive=binding(archive))
  counter=[]
  from contextlib import redirect_stdout
  log=io.StringIO()
  with redirect_stdout(log):rows=s.run_scoring(plan,self.index,self.cases,out,archive,'e'*64,lambda:counter.append(1),time.monotonic())
  (F/'integrated105_stdout.txt').write_text(log.getvalue(),encoding='utf8')
  done=json.loads((out/'completion.json').read_bytes());self.assertEqual(len(rows),420);self.assertTrue(all(r['fold']=='D' for r in rows));self.assertEqual(done['score_rows'],420);self.assertEqual(done['source_rows'],84)
  self.assertEqual(len((out/'case_metrics.jsonl').read_text().splitlines()),420);self.assertEqual(len(json.loads((out/'source_metrics.json').read_bytes())),84);self.assertEqual(len(counter),421)
  self.assertEqual(len(json.loads((out/'risk_transitions.json').read_bytes())['labels']['severe_geometry']['cases']),105)
  self.assertNotIn('torch',sys.modules)
 def test_41_reverse_outlier20_strict_threshold(self):
  distances=m.nearest([[20,0,0],[20.01,0,0]],[[0,0,0]]);self.assertEqual(float(np.mean(distances>20.)),.5)
 def test_42_no_production_archive_access(self):
  self.assertNotIn('torch',sys.modules);self.assertTrue(all(str(Path(x['reference']['path'])).startswith(str(F)) for x in self.cases))


 def test_43_C_model_fold_denied(self):
  x=copy.deepcopy(self.index);x['runs'][0]['fold']='C'
  with self.assertRaises(ValueError):s.validate_index(x,self.refs,self.score_index)
 def test_44_C_row_fold_denied(self):
  x=copy.deepcopy(self.index);x['inputs'][0]['fold']='C'
  with self.assertRaises(ValueError):s.validate_index(x,self.refs,self.score_index)
 def test_45_C_reference_status_denied(self):
  x=copy.deepcopy(self.refs);x['status']='FROZEN_EXISTING_FOLD_C_105_REFERENCES'
  with self.assertRaises(ValueError):s.validate_index(self.index,x,self.score_index)
 def test_46_C_score_case_fold_denied(self):
  x=copy.deepcopy(self.score_index);x['cases'][0]['fold']='C'
  with self.assertRaises(ValueError):s.validate_index(self.index,self.refs,x)
 def test_47_C_arm_labels_denied(self):
  x=copy.deepcopy(self.index);x['runs'][0]['label']='C_T0'
  with self.assertRaises(ValueError):s.validate_index(x,self.refs,self.score_index)
 def test_48_seven_representatives_denied(self):
  with self.archive() as tf:
   with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64,self.index['runs'][0]['dev_case_ids'][:7])
 def test_49_C_request_fold_denied(self):
  q=jsonfile('C_q.json',dict(schema='bcsp-p1-foldD-paired-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,fold='C'))
  a=jsonfile('C_a.json',dict(schema='bcsp-p1-paired-score-authorization-v1',request_sha256=q['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL ONLY'))
  with self.assertRaises(ValueError):s.authorize(q,a)

if __name__=='__main__':
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts));text=stream.getvalue()
 with (F/'stdout.txt').open('x',encoding='utf-8') as f:f.write(text)
 with (N/'CPU_contract_result_v1.json').open('x') as f:json.dump(dict(status='PASS' if result.wasSuccessful() else 'FAILED_STOP_NO_RETRY',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),real_prediction_reads=0,real_reference_reads=0,real_model_calls=0,server_calls=0,GPU_calls=0,packages={x:md.version(x) for x in ['numpy','scipy','psutil','scikit-image']},python=sys.version,scorer_sha256=s.digest(Path(s.__file__)),metric_sha256=s.digest(Path(m.__file__)),test_sha256=s.digest(Path(__file__)),stdout_sha256=s.digest(F/'stdout.txt')),f,indent=2)
 print(text);raise SystemExit(0 if result.wasSuccessful() else 1)
