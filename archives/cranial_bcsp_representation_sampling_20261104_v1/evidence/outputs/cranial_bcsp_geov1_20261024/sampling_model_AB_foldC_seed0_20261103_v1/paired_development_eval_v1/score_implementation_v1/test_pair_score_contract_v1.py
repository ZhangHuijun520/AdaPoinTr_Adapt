"""One artificial CPU batch. No real prediction/archive/reference payload reads."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import copy,hashlib,importlib.metadata as md,io,json,sys,tarfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bcsp_sampling_pair_score_v1 as s
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
    rows.append(dict(fold='C',source_id='train:'+str(k).zfill(3),case_id='train__'+str(k).zfill(3)+'__'+defect,arm=arm,status='OK',metrics=dict(E_P95_mm=float(k+j+(1 if arm=='V1' else 0)),J_coverage_2mm=.5 if arm=='V1' else .75)))
 return rows
class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  F.mkdir();target=np.zeros((8192,3),np.float32);cls.target=target
  cls.points={a:npzfile('synthetic_'+a+'.npz',partial=np.full((8192,3),k,np.float32),implant=target) for k,a in enumerate(s.ARMS)}
  g=np.zeros((5,5,5),bool);g[2,2,2]=True;d=np.zeros_like(g);d[1,2,2]=True
  cls.ref=m.surface_references(g,d,np.eye(3),np.zeros(3));refrecord=npzfile('synthetic_reference.npz',**cls.ref)
  ids=['train__'+str(k).zfill(3)+'__'+defect for k in range(21) for defect in sorted(s.DEFECTS)];sources=['train:'+str(k).zfill(3) for k in range(21)]
  cls.cases=[dict(case_id=cid,source_id='train:'+cid.split('__')[1],fold='C',normalization=dict(center=[0.,0.,0.],scale=1.),target_array_sha256=hashlib.sha256(target.tobytes()).hexdigest(),common_point_order_sha256='f'*64,point_files=cls.points,reference=refrecord) for cid in ids]
  refs=[dict(case_id=c['case_id'],source_id=c['source_id'],fold='C',normalization=c['normalization'],target_array_sha256=c['target_array_sha256'],**refrecord) for c in cls.cases]
  cls.refs=dict(status='FROZEN_EXISTING_FOLD_C_105_REFERENCES',cases=refs);cls.score_index=dict(schema='bcsp-sampling-pair-score-case-index-v1',cases=cls.cases)
  runs=[dict(label='C_'+a,arm=a,fold='C',n_input=8192,dev_case_ids=ids,dev_sources=sources,train_sources=['train:999'],checkpoint=dict(sha256=str(k+1)*64)) for k,a in enumerate(s.ARMS)]
  inputs=[dict(run='C_'+a,arm=a,fold='C',n_input=8192,case_id=c['case_id'],source_id=c['source_id'],normalization=c['normalization'],target_array_sha256=c['target_array_sha256'],common_point_order_sha256=c['common_point_order_sha256'],input=dict(cls.points[a],path='/synthetic_server/'+a+'/'+c['case_id']+'.npz')) for a in s.ARMS for c in cls.cases]
  cls.index=dict(schema='bcsp-sampling-pair-development-index-v1',runs=runs,inputs=inputs)
  mem=io.BytesIO();np.savez_compressed(mem,prediction=target);cls.pred=mem.getvalue();cls.records=[];cls.payload=[]
  for k,i in enumerate(inputs):
   name='predictions/'+i['run']+'__'+i['case_id']+'.npz';cls.payload.append((name,cls.pred))
   cls.records.append(dict(run=i['run'],case_id=i['case_id'],source_id=i['source_id'],fold='C',n_input=8192,n_output=8192,input_sha256=i['input']['sha256'],checkpoint_sha256=runs[k//105]['checkpoint']['sha256'],forward_index=k+1,prediction=dict(name=name,bytes=len(cls.pred),sha256=hashlib.sha256(cls.pred).hexdigest())))
  evidence=[dict(run=r['label'],forwards=105,state_before='a'*64,state_after='a'*64,CPU_rng_before='b'*64,CPU_rng_after='b'*64,CUDA_rng_before='c'*64,CUDA_rng_after='c'*64,Python_numpy_RNG_unchanged=True,mode='eval_inference_mode',BNCal=0,optimizer=0,backward=0) for r in runs]
  cls.done=dict(status='SAMPLING_PAIR_210_FORWARD_COMPLETE',forwards=210,request_sha256='d'*64,models=evidence,training_updates=0,BNCal=0,loss=0,backward=0)
 @classmethod
 def archive(cls,records=None,done=None,drop=False,duplicate=False,payload=None):
  out=io.BytesIO();items=list(cls.payload if payload is None else payload)
  items+=[('inference_manifest.jsonl','\n'.join(json.dumps(r) for r in (cls.records if records is None else records)).encode()),('inference_complete.json',json.dumps(cls.done if done is None else done).encode()),('resources.jsonl',b'{"synthetic":true}\n')]
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
  for key,value in [('target_array_sha256','bad'),('normalization',dict(center=[1,2,3],scale=2)),('common_point_order_sha256','bad')]:
   x=copy.deepcopy(self.index);x['inputs'][105][key]=value
   with self.assertRaises(ValueError):s.validate_index(x,self.refs,self.score_index)
 def test_05_full213_member_reader(self):
  with self.archive() as tf:self.assertEqual(len(s.validate_archive(tf,self.index,'d'*64)),210)
 def test_06_missing_member_rejected(self):
  with self.archive(drop=True) as tf:
   with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64)
 def test_07_duplicate_member_rejected(self):
  with self.archive(duplicate=True) as tf:
   with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64)
 def test_08_wrong_checkpoint_provenance(self):
  x=copy.deepcopy(self.records);x[0]['checkpoint_sha256']='bad'
  with self.archive(records=x) as tf:
   with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64)
 def test_09_counts_and_RNG_failure(self):
  for field in ['count','RNG','BNCal']:
   x=copy.deepcopy(self.done)
   if field=='count':x['forwards']=209
   elif field=='RNG':x['models'][1]['CUDA_rng_after']='bad'
   else:x['BNCal']=1
   with self.archive(done=x) as tf:
    with self.assertRaises(ValueError):s.validate_archive(tf,self.index,'d'*64)
 def test_10_malformed_prediction_stops(self):
  for pred in [np.zeros((8,3),np.float32),np.full((8192,3),np.nan,np.float32),np.zeros((8192,3),np.float64)]:
   mem=io.BytesIO();np.savez_compressed(mem,prediction=pred);blob=mem.getvalue();r=copy.deepcopy(self.records[0]);r['prediction'].update(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
   payload=list(self.payload);payload[0]=(payload[0][0],blob)
   with self.archive(payload=payload) as tf:
    with self.assertRaises(ValueError):s.load_prediction(tf,r)
 def test_11_exact_shared_GT_required(self):
  target=self.target.copy();target[0,0]=1.;bad=npzfile('synthetic_bad_GT.npz',partial=self.target,implant=target);case=copy.deepcopy(self.cases[0]);case['point_files'][s.ARMS[1]]=bad
  with self.archive() as tf:
   lookup=s.validate_archive(tf,self.index,'d'*64)
   with self.assertRaises(ValueError):s.score_case(tf,lookup,case,lambda:None)
 def test_12_integrated_case_reader_five_scores(self):
  with self.archive() as tf:
   lookup=s.validate_archive(tf,self.index,'d'*64);rows=s.score_case(tf,lookup,self.cases[0],lambda:None)
   self.assertEqual([r['arm'] for r in rows],s.ARMS+s.CONTROLS);self.assertEqual(len(rows),5);self.assertEqual(rows[-1]['metrics']['CD_L1_mm'],0.)
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
  self.assertEqual(e['mean_delta_Morton_minus_V1'],-1.);self.assertEqual(e['improved_sources'],21);self.assertEqual(j['mean_delta_Morton_minus_V1'],.25);self.assertEqual(j['improved_sources'],21)
 def test_19_nonfinite_pair_not_dropped(self):
  rows=s.aggregate_source(model_rows());rows[0]['metrics']['E_P95_mm']=None;x=s.paired_summary(rows)['metrics']['E_P95_mm']
  self.assertEqual(x['pair_count'],21);self.assertEqual(x['undefined_pairs'],1);self.assertIsNone(x['mean_delta_Morton_minus_V1']);self.assertEqual(len(x['source_deltas']),21)
 def test_20_no_bootstrap_or_RNG_consumption(self):
  old=m.paired_bootstrap;m.paired_bootstrap=lambda *a,**k:(_ for _ in ()).throw(AssertionError('bootstrap forbidden'))
  try:
   before=np.random.get_state();r=s.paired_summary(s.aggregate_source(model_rows()));after=np.random.get_state();self.assertTrue(r['no_bootstrap']);np.testing.assert_array_equal(before[1],after[1]);self.assertEqual(before[2:],after[2:])
  finally:m.paired_bootstrap=old
 def test_21_all105_case_and_five_defect_summaries(self):
  rows=model_rows();self.assertEqual(len(s.case_differences(rows)),105);self.assertEqual(len(s.defect_summary(rows)),5);self.assertTrue(all(v['paired_cases']==21 for v in s.defect_summary(rows).values()))
 def chain(self,prefix,reverse=False,drift=False):
  q=jsonfile(prefix+'_request.json',dict(schema='bcsp-sampling-pair-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False))
  a=dict(schema='bcsp-sampling-pair-score-authorization-v1',request_sha256='bad' if drift else q['sha256'],explicit_user_authorization=True,user_authorization_text='SYNTHETIC FIXTURE ONLY; not production authorization')
  if reverse:a['runtime_sha256']='bad'
  return q,jsonfile(prefix+'_authorization.json',a)
 def test_22_artificial_authorization_chain(self):self.assertEqual(s.authorize(*self.chain('good'))['status'],'AWAITING_EXPLICIT_USER_AUTHORIZATION')
 def test_23_authorization_drift_and_reverse_rejected(self):
  for kw in [dict(reverse=True),dict(drift=True)]:
   with self.assertRaises(ValueError):s.authorize(*self.chain('bad'+str(len(list(F.iterdir()))),**kw))
 def test_24_metric_source_unchanged_no_Torch(self):
  original=N.parents[2]/'development_eval_v1/bcsp_eval_metrics_v1.py'
  self.assertEqual(s.digest(Path(m.__file__)),s.digest(original));self.assertNotIn('torch',sys.modules)
if __name__=='__main__':
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts));text=stream.getvalue()
 with (F/'stdout.txt').open('x',encoding='utf-8') as f:f.write(text)
 with (N/'CPU_contract_result_v1.json').open('x') as f:json.dump(dict(status='PASS' if result.wasSuccessful() else 'FAILED_STOP_NO_RETRY',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),real_prediction_reads=0,real_reference_reads=0,real_model_calls=0,server_calls=0,GPU_calls=0,packages={x:md.version(x) for x in ['numpy','scipy','psutil','scikit-image']},python=sys.version,scorer_sha256=s.digest(Path(s.__file__)),metric_sha256=s.digest(Path(m.__file__)),test_sha256=s.digest(Path(__file__)),stdout_sha256=s.digest(F/'stdout.txt')),f,indent=2)
 print(text);raise SystemExit(0 if result.wasSuccessful() else 1)
