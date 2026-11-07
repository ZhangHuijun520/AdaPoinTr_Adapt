"""Independent NumPy audit of saved arrays and coefficients; never fits a probe."""
import hashlib,io,json,math,tarfile,time
from pathlib import Path
import numpy as np
S=Path(__file__).resolve().parent;F=S/'post_run_freeze_audit_20261107_v1';D=F/'downloads';START=time.monotonic();CHECKS=[]
def need(ok,msg):
 if not ok:raise ValueError(msg)
def good(msg,ok=True):need(ok,msg);CHECKS.append(msg)
def binding(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def eq(a,b,msg='numeric'):
 if isinstance(b,dict):
  need(isinstance(a,dict) and set(a)==set(b),'keys '+msg)
  for k in b:eq(a[k],b[k],msg+'.'+k)
 elif isinstance(b,(list,tuple)):
  need(len(a)==len(b),'length '+msg)
  for i,(x,y) in enumerate(zip(a,b)):eq(x,y,msg+'.'+str(i))
 elif isinstance(b,np.ndarray):need(np.asarray(a).shape==b.shape and np.isfinite(np.asarray(a,dtype=float)).all() and np.allclose(a,b,rtol=1e-9,atol=1e-10),'array '+msg)
 elif isinstance(b,(float,np.floating)):need(math.isfinite(a) and math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10),'float '+msg)
 else:need(a==b,'value '+msg)
def main():
 try:
  remote=read(F/'remote_audit_report_v1.json');good('remote_output_freeze_pass',remote['status']=='REMOTE_READONLY_OUTPUT_FREEZE_PASS')
  q=read(S/'condition_probe_execution_request_v1.json');good('request_hash',binding(S/'condition_probe_execution_request_v1.json')['sha256']==remote['request_sha256']=='9f2a04c381070d54d9e82cc70e800403b12ac7867124ff4b5e52043c1997549c')
  p3=read(S/'final_implementation_P3_v1.json');good('CPU_P3',p3['status']=='LOCAL_CONDITION_PROBE_INTEGRATION_P3_PASS' and p3['total_artificial_CPU_checks']==28)
  for k in ['entry','core','capture','P3','input_index']:
   b=binding(S/Path(q[k]['path']).name);need(b['sha256']==q[k]['sha256'] and b['bytes']==q[k]['bytes'],'frozen implementation '+k)
  for k in ['core_CPU_result','integration_CPU_result']:
   b=p3[k];need(binding(Path(b['path']))==b,'CPU result binding')
  complete=read(D/'completion.json');archive=D/'development_predictions_v1.tar.gz';ab=binding(archive)
  good('download_and_remote_archive_SHA_bytes',ab['sha256']==remote['archive']==complete['archive']['sha256'] and ab['bytes']==remote['archive_bytes']==complete['archive']['bytes'] and binding(D/'completion.json')['sha256']==remote['completion_sha256'])
  good('exit0_no_forward_rerun',(D/'exit_code.txt').read_text().strip()=='0')
  need(Path(str(archive)+'.sha256').read_text().split()[0]==ab['sha256'] and int(Path(str(archive)+'.bytes').read_text())==ab['bytes'],'archive sidecars')
  blobs={};total=0
  with tarfile.open(archive,'r:gz') as tf:
   members=tf.getmembers();need(len(members)==1692,'1692 members')
   for m in members:
    need(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and m.name not in blobs and m.size<16*1024**2,'safe member');b=tf.extractfile(m).read();total+=len(b);need(total<128*1024**2,'uncompressed budget');blobs[m.name]=b
  expected={r['name']:r for r in complete['archive']['members']};good('1692_archive_member_exact_set',set(blobs)==set(expected) and len(expected)==1692)
  for n,b in blobs.items():need(len(b)==expected[n]['bytes'] and hashlib.sha256(b).hexdigest()==expected[n]['sha256'],'member hash '+n)
  good('all_archive_member_SHA_and_bytes')
  need(Path(str(archive)+'.contents.sha256').read_text()==''.join(r['sha256']+'  '+r['name']+'\n' for r in complete['archive']['members']),'contents sidecar')
  idx=read(S/'condition_probe_input_index_v1.json');runs=idx['runs'];inputs=idx['inputs'];good('fixed_four_models1680_index',len(inputs)==1680 and [r['label'] for r in runs]==['C_T0','C_M0','D_T0','D_M0'])
  journal=[json.loads(s) for s in blobs['prefix_attempts.jsonl'].decode().splitlines()];manifest=[json.loads(s) for s in blobs['tensor_manifest.jsonl'].decode().splitlines()]
  eq(journal,[dict(attempt=i+1,run=r['run'],case_id=r['case_id'],status='CLAIMED_BEFORE_PREFIX') for i,r in enumerate(inputs)],'exact ordered prefix journal');good('1680_exact_ordered_attempts')
  good('1680_unique_manifest_and_features',len(manifest)==1680 and len({r['file']['name'] for r in manifest})==1680 and len([n for n in blobs if n.startswith('features/')])==1680)
  allrows={};shared={};npz_count=0
  for m,r in zip(manifest,inputs):
   run=next(x for x in runs if x['label']==r['run']);fields=dict(run=r['run'],fold=r['fold'],variant=r['variant'],role=r['role'],case_id=r['case_id'],source_id=r['source_id'],scale=r['normalization']['scale'],input_sha256=r['input']['sha256'],target_array_sha256=r['target_array_sha256'],checkpoint_sha256=run['checkpoint']['sha256'],normalization=r['normalization'])
   for k,v in fields.items():eq(m[k],v,'manifest '+k)
   name='features/'+r['run']+'__'+r['case_id']+'.npz';need(m['file']['name']==name,'feature name');b=blobs[name];need(hashlib.sha256(b).hexdigest()==m['file']['sha256'] and len(b)==m['file']['bytes'],'manifest hash')
   with np.load(io.BytesIO(b),allow_pickle=False) as z:
    need(set(z.files)=={'feature1024','coarse4','target4','geometry18'},'feature schema');a={k:z[k].copy() for k in z.files}
   for k,n in [('feature1024',1024),('coarse4',4),('target4',4),('geometry18',18)]:need(a[k].shape==(n,) and np.isfinite(a[k]).all() and a[k].dtype==(np.float32 if k=='feature1024' else np.float64),'feature dtype/shape/finite '+k)
   key=(r['fold'],r['case_id'])
   if key in shared:
    for k in ['target4','geometry18']:need(np.array_equal(shared[key][k],a[k]),'same fold pair input/GT summary')
   else:shared[key]=a
   if r['role']=='development':
    frozen=r['frozen_coarse'];need(np.allclose(a['coarse4'][:3],frozen['centroid'],rtol=1e-9,atol=1e-7) and np.isclose(np.exp(a['coarse4'][3]),frozen['radius_gyration'],rtol=1e-8,atol=1e-7),'saved coarse native equivalence')
   allrows[r['run'],r['case_id']]=dict(r,**a);npz_count+=1
  good('1680_array_schemas_finite_manifest_bindings_and_same_input_pair');good('420_development_coarse_moments_match_native_baselines')
  resource=[json.loads(s) for s in blobs['resources.jsonl'].decode().splitlines()];good('3372_resource_samples_all_pass',len(resource)==3372 and all(all(v['checks'].values()) and not v['failed_checks'] for v in resource))
  expected_phases=[];counter=0
  for run in runs:
   expected_phases.append(('model_start:'+run['label'],counter))
   for _ in range(420):expected_phases.append(('before_prefix',counter));counter+=1;expected_phases.append(('after_prefix',counter))
   expected_phases.extend([('before_CPU_readout',counter),('after_CPU_readout',counter)])
  need([(v['phase'],v['forwards']) for v in resource]==expected_phases,'exact resource phase/count sequence')
  done=json.loads(blobs['probe_complete.json']);need(done['prefixes']==1680 and done['formal_gate'] is False and all(done[k]==0 for k in ['backward','optimizer_steps','dense_forwards','BNCal']),'done scope')
  eq(done['model_evidence'],[dict(run=r['label'],prefix_calls=420,state_unchanged=True,RNG_unchanged=True) for r in runs]);good('four_model_recorded_state_RNG_assertions_and_zero_updates')
  values={};max_residual=0
  for run in runs:
   label=run['label'];part=[allrows[label,r['case_id']] for r in inputs if r['run']==label];train=[r for r in part if r['role']=='train'];dev=[r for r in part if r['role']=='development'];ts={r['source_id'] for r in train};ds=sorted({r['source_id'] for r in dev})
   need(len(train)==315 and len(dev)==105 and len(ts)==63 and len(ds)==21 and not ts&set(ds),'source/fold isolation')
   for group in [train,dev]:need(all(sum(r['source_id']==s for r in group)==5 for s in {r['source_id'] for r in group}),'five defects/source')
   with np.load(io.BytesIO(blobs[label+'_readout.npz']),allow_pickle=False) as z:saved={k:z[k].copy() for k in z.files}
   need(len(saved)==20 and all(np.isfinite(v).all() for v in saved.values()),'readout schema/finite');summary=json.loads(blobs[label+'_summary.json'])
   need(summary['run']==label and summary['development_fitted'] is False and summary['formal_gate'] is False,'summary contract');eq(summary['case_ids'],[r['case_id'] for r in dev]);eq(summary['metric_order'],['centroid_mm','centroid_over_GT_radius','absolute_log_radius_error'])
   y=np.array([r['target4'] for r in train]);yd=np.array([r['target4'] for r in dev]);ym=y.mean(0);ys=np.sqrt(((y-ym)**2).mean(0));ys_safe=np.where(ys>0,ys,1);pred={'constant':np.tile(ym,(105,1)),'coarse':np.array([r['coarse4'] for r in dev])}
   for k,n in [('geometry18',18),('feature1024',1024)]:
    x=np.array([r[k] for r in train],dtype='float64');xd=np.array([r[k] for r in dev],dtype='float64');xm=x.mean(0);xs=np.sqrt(((x-xm)**2).mean(0));xs_safe=np.where(xs>0,xs,1);W=saved[k+'__coefficient'];need(W.shape==(n,4),'coef shape')
    for key,val in [('x_mean',xm),('x_scale',xs_safe),('y_mean',ym),('y_scale',ys_safe)]:eq(saved[k+'__'+key],val,'training-only '+k+key)
    need(np.array_equal(saved[k+'__constant_y'],ys==0),'constant target mask');X=(x-xm)/xs_safe;Y=(y-ym)/ys_safe;X[:,xs==0]=0;Y[:,ys==0]=0
    residual=X.T@(X@W-Y)/315+W;norm=float(np.max(np.abs(residual)));max_residual=max(max_residual,norm);need(norm<1e-8,'ridge stationary equation '+label+k)
    # Evaluate saved coefficients only: no linear solve, optimization or refitting.
    z=(xd-saved[k+'__x_mean'])/saved[k+'__x_scale'];pred[k]=(z@W)*saved[k+'__y_scale']+saved[k+'__y_mean'];pred[k][:,saved[k+'__constant_y']]=saved[k+'__y_mean'][saved[k+'__constant_y']]
    eq(summary['fits'][k],dict(schema='fixed-source-weighted-ridge-v1',lambda_mean_objective=1.,train_sources=sorted(ts)))
   metrics={};bysource={}
   for arm,p in pred.items():
    eq(saved['prediction__'+arm],p,'saved predictions '+label+arm);dist=np.linalg.norm(p[:,:3]-yd[:,:3],axis=1);v=np.c_[dist*np.array([r['normalization']['scale'] for r in dev]),dist/np.exp(yd[:,3]),np.abs(p[:,3]-yd[:,3])];eq(saved['error__'+arm],v,'case errors');metrics[arm]=v;bysource[arm]={sid:v[[r['source_id']==sid for r in dev]].mean(0) for sid in ds}
   expected_summary={}
   for arm,ss in bysource.items():
    v=np.array([ss[s] for s in ds]);delta=v-np.array([bysource['coarse'][s] for s in ds]);expected_summary[arm]=dict(source_mean=v.mean(0),source_median=np.median(v,axis=0),mean_delta_vs_coarse=delta.mean(0),improved_sources=(delta<0).sum(0),tied_sources=(delta==0).sum(0),worse_sources=(delta>0).sum(0),source_errors=ss)
   eq(summary['source_equal'],expected_summary,'independent source aggregation '+label)
   strata={}
   for defect in sorted({r['case_id'].split('__',2)[2] for r in dev}):
    ix=[i for i,r in enumerate(dev) if r['case_id'].split('__',2)[2]==defect];need(len(ix)==21,'21 cases/defect');strata[defect]={arm:v[ix].mean(0) for arm,v in metrics.items()}
   eq(summary['defects'],strata,'five defect strata');values[label]=summary
  good('all_train_only_standardization_and_fixed_ridge_stationary_equations_no_refit');good('all_saved_predictions_case_errors_and420_dev_rows_recomputed_from_saved_coefficients');good('all84_model_source_rows_and_strata_mean_median_delta_winloss_consistent')
  report=dict(status='FORMAL_POST_PROBE_FREEZE_AUDIT_PASS',request_sha256=remote['request_sha256'],checks=CHECKS,counts=dict(prefixes=1680,feature_files=1680,model_runs=4,training_rows=1260,development_rows=420,model_source_rows=84,resource_records=3372,archive_members=1692,server_output_files=remote['exact_output_files']),max_ridge_stationarity_residual=max_residual,archive=ab,download_manifest=[binding(p) for p in D.iterdir()],remote_report=binding(F/'remote_audit_report_v1.json'),CPU_P3= binding(S/'final_implementation_P3_v1.json'),seconds=time.monotonic()-START,refit=False,linear_solve=False,forward_calls=0,model_imports=0,server_writes=0,limitations=['Model/BN/RNG equality recorded as worker booleans after hashed-code assertions; before/after tensor/RNG fingerprints were not persisted and cannot be independently rehashed','Raw Q arrays not saved; native equivalence audited from saved Q moments and frozen worker check','No original point arrays, checkpoints or nearest-neighbour geometry recomputed','Single-seed exploratory development probe; no significance, bootstrap, clinical or H2 gate'])
  with (F/'audited_values_v1.json').open('x',encoding='utf-8') as f:json.dump(values,f,indent=2)
 except BaseException as exc:report=dict(status='FORMAL_POST_PROBE_FREEZE_AUDIT_FAILED_STOP_NO_RETRY',passed_checks=CHECKS,error=repr(exc),seconds=time.monotonic()-START,refit=False,forward_calls=0)
 with (F/'formal_audit_report_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k!='download_manifest'}))
 if report['status']!='FORMAL_POST_PROBE_FREEZE_AUDIT_PASS':raise SystemExit(1)
if __name__=='__main__':main()
