"""One artificial CPU contract batch; never scores real prediction/GT arrays."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,io,json,sys,tarfile,time
S=Path(__file__).resolve().parent;R=S.parents[1];O=S/'CPU_contract_v1'
def main():
 O.mkdir();spec=importlib.util.spec_from_file_location('scq_score_cpu',S/'bcsp_scq_BS_two_arm_score_v1.py');s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s);np=s.np;checks=[]
 def check(n,v=True):assert v,n;checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError,KeyError):check(n);return
  raise AssertionError('unexpected accept '+n)
 def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=s.digest(p))
 def emit(n,v):p=O/n;s.emit(p,v);return rec(p)
 def npz(n,**v):
  p=O/n
  with p.open('xb') as f:np.savez_compressed(f,**v)
  return rec(p)
 try:
  prep=R/'outputs/scq_score_prep_20261114_v1';real= json.loads((prep/'SCQ_BS_score_case_index_candidate_v1.json').read_bytes());idx=json.loads((R/'outputs/scq_pred_freeze_20261114_v2/downloads/installed/SCQ_BS_CD_input_index_v2.json').read_bytes());refs=json.loads(Path(real['reference_manifest']['path']).read_bytes())
  check('01 actual frozen metadata210 cases420 members',len(s.validate_index(idx,refs,real)[2])==210)
  for name,fn in [('02 missing case',lambda v:v['cases'].pop()),('03 changed normalization',lambda v:v['cases'][0]['normalization'].update(scale=1.)),('04 target hash drift',lambda v:v['cases'][0].update(target_array_sha256='0'*64)),('05 duplicate binding',lambda v:v['prediction_records'].__setitem__(0,v['prediction_records'][1]))]:
   bad=copy.deepcopy(real);fn(bad);reject(name,lambda:s.validate_index(idx,refs,bad))
  bad=copy.deepcopy(idx);bad['inputs'][0]['save_Qraw']=False;reject('06 all raw queries required',lambda:s.validate_index(bad,refs,real))
  serial=0
  def chain(yes=True,counts=True,pair=True):
   nonlocal serial
   serial+=1;q=dict(schema='bcsp-scq-BS-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,counts=dict(unique_cases=210,sources=42,model_rows=420,shared_control_rows=420,case_score_rows=840 if counts else 839,source_score_rows=168),scientific_contract=dict(arms=['B','S'],pairs=[['B','S']] if pair else [['S','B']],controls=s.CONTROLS),limits=dict(wall_seconds=18000,RSS_bytes=8589934592,output_bytes=2147483648,threads=2))
   qr=emit('q'+str(serial)+'.json',q);ar=emit('a'+str(serial)+'.json',dict(schema='bcsp-scq-BS-score-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_CPU_ONLY'));return qr,ar
  s.authorize(*chain());check('07 complete actual authorize840 contract')
  reject('08 authorization required',lambda:s.authorize(*chain(yes=False)));reject('09 row budget drift',lambda:s.authorize(*chain(counts=False)));reject('10 pair reversed',lambda:s.authorize(*chain(pair=False)))
  # Tiny analytic voxel phantom only. Point counts match production, not anatomy.
  g=np.zeros((5,5,5),bool);g[2,2,2]=True;d=np.zeros_like(g);d[1,2,2]=True;ref=s.metric.surface_references(g,d,np.eye(3),np.zeros(3));rr=npz('phantom_reference.npz',**ref)
  gt=np.tile(ref['a_centers'].astype(np.float32),(1366,1))[:8192].copy();point=npz('phantom_point.npz',partial=gt+.25,implant=gt);norm=dict(center=[0.,0.,0.],scale=1.);targetsha=hashlib.sha256(gt.tobytes()).hexdigest()
  index=copy.deepcopy(idx);cases=copy.deepcopy(real['cases']);refrows=[]
  for c in cases:
   c.update(normalization=copy.deepcopy(norm),target_array_sha256=targetsha,point_file=point,reference=rr)
   refrows.append(dict(case_id=c['case_id'],source_id=c['source_id'],fold=c['fold'],normalization=copy.deepcopy(norm),target_array_sha256=targetsha,**rr))
  for r in index['inputs']:r.update(normalization=copy.deepcopy(norm),input=point)
  # Saved construction/RNG dictionaries are used as metadata fixtures, not models.
  saved=json.loads((R/'outputs/scq_pred_freeze_20261114_v2/downloads/output/inference_complete.json').read_bytes());modelmeta=copy.deepcopy(saved['models'])
  for m in modelmeta:m.update(state_before='a'*64,state_after='a'*64)
  rng=modelmeta[0]['RNG_before']
  for m in modelmeta:m.update(RNG_before=rng,RNG_after=rng)
  def stats(x):
   x=x.astype(np.float64);mean=x.mean(0);v=x-mean;return dict(centroid=mean.tolist(),bbox_min=x.min(0).tolist(),bbox_max=x.max(0).tolist(),radius_gyration=float(np.sqrt((v*v).sum(1).mean())),covariance_eigenvalues=np.linalg.eigvalsh(v.T@v/len(x)).tolist())
  blobs={};geoms={}
  for arm,offset in [('B',.2),('S',.05)]:
   pred=gt+offset;co=pred[:256].copy();delta=np.full_like(co,.01) if arm=='S' else np.zeros_like(co);raw=co-delta;b=io.BytesIO();np.savez_compressed(b,prediction=pred,coarse=co,Qraw=raw,delta=delta);blobs[arm]=b.getvalue()
   off=pred.astype(float).reshape(256,32,3)-co.astype(float)[:,None,:];geoms[arm]=dict(frame='native_D_only_normalized_no_GT',coarse=stats(co),dense=stats(pred),mean_dense_minus_coarse=off.mean((0,1)).tolist(),offset_mean_squared_radius=float((off**2).sum(2).mean()))
  items=[];man=[];claims=[];geometry=[];bindings=[];runs={r['label']:r for r in index['runs']}
  for i,row in enumerate(index['inputs'],1):
   arm=row['variant'];blob=blobs[arm];name=row['prediction_filename'];pr=dict(name=name,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest());items.append((name,blob))
   man.append(dict(run=row['run'],variant=arm,fold=row['fold'],case_id=row['case_id'],source_id=row['source_id'],n_input=8192,n_output=8192,normalization=copy.deepcopy(norm),input_sha256=point['sha256'],checkpoint_sha256=runs[row['run']]['checkpoint']['sha256'],forward_index=i,prediction=pr))
   claims.append(dict(forward_index=i,run=row['run'],case_id=row['case_id'],status='CLAIMED_BEFORE_FORWARD'));geometry.append(dict(run=row['run'],case_id=row['case_id'],**geoms[arm]))
   bindings.append(dict(arm=arm,fold=row['fold'],case_id=row['case_id'],archive_key='SCQ',member=name,bytes=pr['bytes'],sha256=pr['sha256'],coarse_saved=True,Qraw_saved=True,delta_saved=True))
  done=dict(status='SCQ_BS_CD_420_NATIVE_FORWARD_COMPLETE',forwards=420,context_cases=0,trace_cases=0,request_sha256='d'*64,training_updates=0,BNCal=0,loss=0,backward=0,models=modelmeta)
  for n,rows in [('inference_manifest.jsonl',man),('forward_attempts.jsonl',claims),('geometry_summary.jsonl',geometry),('cache_manifest.jsonl',[])]:items.append((n,b''.join((json.dumps(r)+'\n').encode() for r in rows)))
  items.extend([('inference_complete.json',json.dumps(done).encode()),('resources.jsonl',b'{"ARTIFICIAL_METADATA_ONLY":true}\n')]);archive=O/'artificial_SCQ.tar.gz'
  with tarfile.open(archive,'w:gz') as t:
   for name,blob in items:m=tarfile.TarInfo(name);m.size=len(blob);t.addfile(m,io.BytesIO(blob))
  synthetic=dict(schema='bcsp-scq-BS-twofold-score-index-candidate-v1',cases=cases,prediction_records=bindings,model_arms=s.ARMS,controls=s.CONTROLS)
  check('11 synthetic210 cases420 metadata',len(s.validate_index(index,dict(cases=refrows),synthetic)[2])==210)
  plan=dict(archive_inputs={'SCQ':dict(archive=rec(archive),prediction_index=emit('phantom_index.json',index),prediction_protocol=emit('phantom_protocol.json',dict(inference=dict(forward_attempt_budget=420))),prediction_request_sha256='d'*64)})
  with tarfile.open(archive) as tar:
   lookup=s.validate_archive(tar,index,'d'*64,None,'SCQ');check('12 actual426 member archive reader',len(lookup)==420)
   for arm in ['B','S']:
    ar=s.load_prediction_arrays(tar,lookup['C',arm,cases[0]['case_id']]);check('13 '+arm+' actual four-key tensor loading',set(ar)=={'prediction','coarse','Qraw','delta'})
   templates={f:s.score_case({'SCQ':tar},lookup,cases[0 if f=='C' else 105],lambda:None) for f in ['C','D']}
   check('14 frozen metric8 artificial rows',len(templates['C'])==len(templates['D'])==4)
   check('15 analytic GT zero CD and S closer than B',templates['C'][-1]['metrics']['CD_L1_mm']==0 and templates['C'][0]['metrics']['CD_L1_mm']>templates['C'][1]['metrics']['CD_L1_mm']>0)
   class View:
    def __init__(self,base,mutate=None,member=None,blob=None):self.base,self.mutate,self.member,self.blob=base,mutate,member,blob
    def __getattr__(self,n):return getattr(self.base,n)
    def getmembers(self):
     result=copy.deepcopy(self.base.getmembers())
     if self.mutate:self.mutate(result)
     return result
    def extractfile(self,n):return io.BytesIO(self.blob) if self.member==n else self.base.extractfile(n)
   reject('16 zero prediction denied',lambda:s.validate_archive(View(tar,lambda ms:setattr(ms[0],'size',0)),index,'d'*64,None,'SCQ'))
   reject('17 nonempty cache denied',lambda:s.validate_archive(View(tar,lambda ms:setattr(next(m for m in ms if m.name=='cache_manifest.jsonl'),'size',1)),index,'d'*64,None,'SCQ'))
   reject('18 wrong request identity denied',lambda:s.validate_archive(tar,index,'0'*64,None,'SCQ'))
   changed=copy.deepcopy(done);changed['models'][0]['RNG_after']={'wrong':True};reject('19 RNG drift denied',lambda:s.validate_archive(View(tar,member='inference_complete.json',blob=json.dumps(changed).encode()),index,'d'*64,None,'SCQ'))
   changed=copy.deepcopy(done);changed['models'][1]['construction']['scq']['variant']='B';reject('20 wrong SCQ construction denied',lambda:s.validate_archive(View(tar,member='inference_complete.json',blob=json.dumps(changed).encode()),index,'d'*64,None,'SCQ'))
   r=copy.deepcopy(lookup['C','B',cases[0]['case_id']]);r['prediction']['sha256']='0'*64;reject('21 member digest drift denied',lambda:s.load_prediction_arrays(tar,r))
   # Correctly rebound artificial blobs with invalid keys/value must still fail.
   for name,arrays in [('22 missing delta',dict(prediction=gt,coarse=gt[:256],Qraw=gt[:256])),('23 extra GT key',dict(prediction=gt,coarse=gt[:256],Qraw=gt[:256],delta=np.zeros_like(gt[:256]),GT=gt)),('24 nonzero B delta',dict(prediction=gt,coarse=gt[:256],Qraw=gt[:256]-.1,delta=np.full_like(gt[:256],.1)))]:
    blob=io.BytesIO();np.savez_compressed(blob,**arrays);value=blob.getvalue();r=copy.deepcopy(lookup['C','B',cases[0]['case_id']]);r['prediction'].update(bytes=len(value),sha256=hashlib.sha256(value).hexdigest())
    reject(name,lambda:s.load_prediction_arrays(View(tar,member=r['prediction']['name'],blob=value),r))
  baseline=[]
  for c in cases:
   for row in templates[c['fold']]:
    if row['arm'] in s.CONTROLS:v=copy.deepcopy(row);v.update(fold=c['fold'],case_id=c['case_id'],source_id=c['source_id']);baseline.append(v)
  bp=O/'frozen_artificial_controls.jsonl'
  with bp.open('x',encoding='utf-8') as f:
   for row in baseline:f.write(json.dumps(s.metric.json_safe(row),allow_nan=False)+'\n')
  plan['frozen_baseline_scores']=rec(bp);calls=[];original=s.score_case
  def artificial(tars,lookup,c,guard):
   guard();calls.append(c['case_id']);rows=copy.deepcopy(templates[c['fold']])
   for row in rows:row.update(fold=c['fold'],case_id=c['case_id'],source_id=c['source_id'])
   return rows
  out=O/'full840';out.mkdir();s.score_case=artificial
  try:rows=s.run_scoring(plan,index,cases,out,{'SCQ':archive},'e'*64,lambda:None,time.monotonic(),prediction_bindings=bindings)
  finally:s.score_case=original
  check('25 actual840 orchestration210 unique case calls',len(rows)==840 and len(calls)==len(set(calls))==210)
  check('26 168 source groups5 defects each',len(s.aggregate_source(rows))==168 and all(r['case_count']==5 for r in s.aggregate_source(rows)))
  comp=json.loads((out/'paired_comparison.json').read_bytes());check('27 S minus B source-equal direction',all(comp['comparison'][f]['S_minus_B']['source_count']==21 and comp['comparison'][f]['S_minus_B']['metrics']['CD_L1_mm']['mean_delta_b_minus_a']<0 for f in ['C','D']))
  complete=json.loads((out/'completion.json').read_bytes());check('28 exactly420 models420 controls840 rows168 sources',complete['model_predictions']==complete['controls']==complete['frozen_baseline_rows_verified']==420 and complete['score_rows']==840 and complete['source_rows']==168 and complete['bootstrap']==complete['forward_calls']==0 and complete['formal_gate'] is False)
  check('29 strict20mm and0.9 boundaries',s.risk_labels(dict(E_P95_mm=20,**{'J_coverage_2.0mm':.1}),dict(centroid_offset_mm=20,radius_gyration_ratio=.9))==dict(placement_tail=False,compact_distribution=False,severe_geometry=False))
  check('30 zero J coverage severe',s.risk_labels(dict(E_P95_mm=1,**{'J_coverage_2.0mm':0}),dict(centroid_offset_mm=0,radius_gyration_ratio=1))['severe_geometry'])
  part=copy.deepcopy([r for r in rows if r['fold']=='C'])
  for row in part:row['risk_labels']['severe_geometry']=row['arm']=='S'
  risks=s.risk_transitions(part,('B','S'))['labels']['severe_geometry'];check('31 new severe not netted',risks['new']==105 and risks['rescued']==0)
  for row in part:row['risk_labels']['severe_geometry']=row['arm']=='B'
  risks=s.risk_transitions(part,('B','S'))['labels']['severe_geometry'];check('32 rescued separate',risks['new']==0 and risks['rescued']==105)
  missing=copy.deepcopy(rows);missing.pop();reject('33 no dropped control or defect',lambda:s.aggregate_source(missing))
  check('34 undefined pairs retained',s.describe_pairs([1,None],[2,3])['status']=='UNDEFINED_NONFINITE_PAIRS_RETAINED')
  wrong=copy.deepcopy(bindings);wrong[0]['sha256']='0'*64;failed=O/'wrong_binding';failed.mkdir();reject('35 frozen member binding checked before scores',lambda:s.run_scoring(plan,index,cases,failed,{'SCQ':archive},'f'*64,lambda:None,time.monotonic(),prediction_bindings=wrong))
  failed=O/'first_failure';failed.mkdir();failedcalls=[]
  def broken(*a):failedcalls.append(1);raise RuntimeError('ARTIFICIAL_FIRST_FAILURE')
  s.score_case=broken
  try:reject('36 first case failure stops',lambda:s.run_scoring(plan,index,cases,failed,{'SCQ':archive},'f'*64,lambda:None,time.monotonic(),prediction_bindings=bindings))
  finally:s.score_case=original
  check('37 no second case false completion',len(failedcalls)==1 and not (failed/'completion.json').exists())
  changed=copy.deepcopy(baseline);changed[0]['metrics']['CD_L1_mm']+=.01;bp2=O/'changed_controls.jsonl'
  with bp2.open('x',encoding='utf-8') as f:
   for row in changed:f.write(json.dumps(s.metric.json_safe(row),allow_nan=False)+'\n')
  badplan=copy.deepcopy(plan);badplan['frozen_baseline_scores']=rec(bp2);failed=O/'control_drift';failed.mkdir();s.score_case=artificial
  try:reject('38 frozen control drift blocks completion',lambda:s.run_scoring(badplan,index,cases,failed,{'SCQ':archive},'f'*64,lambda:None,time.monotonic(),prediction_bindings=bindings))
  finally:s.score_case=original
  check('39 no completion after control drift',not (failed/'completion.json').exists())
  def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
  a=funcs(R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_F0_scoring_implementation_v1/bcsp_lqi_F0_two_arm_score_v1.py');b=funcs(S/'bcsp_scq_BS_two_arm_score_v1.py');keep=['select_metrics','position_shape','risk_labels','stage_geometry','score_case','aggregate_source','describe_pairs','paired_summary','case_differences','defect_summary','csv_rows','risk_transitions']
  check('40 all actual metric risk aggregate source pair functions unchanged',all(a[k]==b[k] for k in keep))
  check('41 frozen metric SHA',s.digest(s.METRIC_PATH)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766')
  check('42 D-only inverse world unchanged',np.array_equal(s.metric.world_points(np.array([[1.,2.,3.]],np.float32),dict(scale=2.,center=[10.,20.,30.])),np.array([[12.,24.,36.]])))
  emit('result_v1.json',dict(status='SCQ_BS_SCORING_CPU_CONTRACT_PASS',checks=checks,checks_passed=len(checks),python=sys.version,packages={n:s.md.version(n) for n in ['numpy','scipy','psutil','scikit-image']},source_bindings=[rec(S/'bcsp_scq_BS_two_arm_score_v1.py'),rec(Path(__file__)),rec(s.METRIC_PATH)],synthetic_actual_metric_rows=8,synthetic_orchestrated_rows=840,real_score_rows=0,real_archive_arrays_read=0,real_reference_point_arrays_read=0,server_operations=0,GPU_calls=0,limitations=['8 metric rows use a tiny analytic voxel phantom and artificial8192 tensors.','840 orchestration rows use artificial templates; not840 true metric evaluations.','Native accuracy and interface conclusions require separately authorized real scoring plus formal freeze audit.']))
  print(json.dumps(dict(status='SCQ_BS_SCORING_CPU_CONTRACT_PASS',checks=len(checks),synthetic_actual_metric_rows=8,synthetic_orchestrated_rows=840,real_score_rows=0)))
 except BaseException as exc:emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc)));raise
if __name__=='__main__':main()
