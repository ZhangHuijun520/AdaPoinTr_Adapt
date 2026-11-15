"""Independent local frozen-evidence verification + GT-free descriptive mechanism review."""
from pathlib import Path,PurePosixPath
from collections import Counter
import hashlib,io,json,tarfile
import numpy as np
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_dac_r01_preparation_20261115_v1';F=B/'post_diagnostic_freeze_v1';D=F/'downloads';RH='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'
def read(p):return json.loads(p.read_bytes())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
checks={}
def check(k,ok):
 checks[k]=bool(ok)
 if not ok:raise AssertionError(k)
qpath=B/'pending_request_v1/SCQ_DAC_R1_execution_request_v1.json';q=read(qpath);a=read(F/'inventory_before_result_v1.json')['results'];after=read(F/'inventory_after_result_v1.json')['results']
try:
 check('request_full_SHA256',sha(qpath)==RH and sha(D/'installed/SCQ_DAC_R1_execution_request_v1.json')==RH)
 check('stable_complete_before_after_inventories',a==after)
 root=PurePosixPath(q['entry']['path']).parent
 mapping=read(B/'pending_request_v1/candidate_no_overwrite_install_mapping_v1.json')['files']
 expected={str(PurePosixPath(r['remote']).relative_to(root)):(r['bytes'],r['sha256']) for r in mapping}
 for n in ('authorization_v1.json','runtime_v1.json','launch_once_v1.sh'):
  p=B/'authorized_execution_v1'/n;expected['control/'+n]=(p.stat().st_size,sha(p))
 marker=json.dumps(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=RH)).encode();expected['control/attempt_claim_v1.json']=(len(marker),hashlib.sha256(marker).hexdigest())
 check('exact32_installed_files_and_all_original_hashes',len(expected)==32 and set(a['installed']['files'])==set(expected) and all((a['installed']['files'][n]['bytes'],a['installed']['files'][n]['sha256'])==v for n,v in expected.items()))
 check('exact_installed_directory_set',a['installed']['directories']==['.','control','replay','weights'])
 controls=D/'installed/control';auth=read(controls/'authorization_v1.json');runtime=read(controls/'runtime_v1.json')
 check('explicit_authorization_chain',set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['request_sha256']==RH and auth['explicit_user_authorization'] is True and bool(auth['user_authorization_text']))
 check('oneway_runtime_and_consumed_single_claim',runtime==dict(schema='bcsp-dac-r1-runtime-v1',request_sha256=RH,authorization_sha256=sha(controls/'authorization_v1.json')) and read(controls/'attempt_claim_v1.json')==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=RH))
 for key,name in (('entry','bcsp_scq_dac_r1_entry_v1.py'),('core','bcsp_scq_dac_r1_core_v1.py'),('P3','local_P3_v1.json')):check('frozen_'+key,sha(D/'installed'/name)==q[key]['sha256'])
 rows=read(D/'installed/selected20_cases_v1.json')['cases'];labels=[r['run']+':'+r['case_id'] for r in rows]
 check('exact20_balanced_cases',len(rows)==20 and len(set(labels))==20 and Counter((r['fold'],r['defect_type']) for r in rows)==Counter({(f,t):2 for f in 'CD' for t in ('bilateral','frontoorbital','parietotemporal','random_1','random_2')}))
 output=D/'output';base={'launch.log','worker.pid','resources.jsonl','calls.jsonl','diagnostic_manifest.jsonl','diagnostic_complete.json','development_predictions_v1.tar.gz','development_predictions_v1.tar.gz.sha256','development_predictions_v1.tar.gz.bytes','development_predictions_v1.tar.gz.contents.sha256','completion.json','exit_code.txt'}
 casepaths=['cases/'+r['run']+'__'+r['case_id']+'.npz' for r in rows]
 check('exact32_output_files_and7_directories',set(a['output']['files'])==base|set(casepaths) and a['output']['directories']==['.','cache','cases','hf_cache','mplconfig','tmp','triton_cache'])
 check('exit_code_zero_and_no_failure_file',(output/'exit_code.txt').read_text().strip()=='0' and 'failure.json' not in a['output']['files'])
 done=read(output/'diagnostic_complete.json');counts=q['calls'];journal=[json.loads(l) for l in (output/'calls.jsonl').read_text().splitlines()]
 expected_events=[]
 for label in labels:
  expected_events.extend((kind,label+suffix) for kind,suffix in [('native',''),('first_head',''),('h1_new',''),('decoder',''),('h1_old',''),('decoder_only',':Average'),('decoder',':Average'),('decoder_only',':DAC'),('decoder',':DAC')])
 running={k:0 for k in counts}
 check('exact180_ordered_call_claims',len(journal)==len(expected_events)==180)
 for ev,(kind,case) in zip(journal,expected_events):
  running[kind]+=1
  assert ev==dict(event='CLAIMED_BEFORE_CALL',kind=kind,case=case,counts=dict(running)),(kind,case)
 check('all_progressive_counts_and_exact20_40',running==counts==done['counts'] and done['request_sha256']==RH)
 check('zero_GT_loss_backward_optimizer',done['GT_used'] is False and done['loss']==done['backward']==done['optimizer_steps']==0)
 models=done['models']
 check('two_model_state_fingerprints',len(models)==2 and {m['run'] for m in models}=={'Requery_C','Requery_D'} and all(m['cases']==10 and len(m['state_before'])==64 and m['state_before']==m['state_after'] for m in models))
 check('RNG_runtime_assertion_evidence_not_raw_fingerprints',all(m['RNG_unchanged'] is True for m in models))
 resources=[json.loads(l) for l in (output/'resources.jsonl').read_text().splitlines()];L=q['limits']
 check('exact41_resource_records',len(resources)==41)
 for i,r in enumerate(resources):
  phase='archived' if i==40 else ('before_case' if i%2==0 else 'after_case');n=20 if i==40 else (i//2+(i%2))
  v=r['values'];truth=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=600,disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
  assert r['phase']==phase and r['forwards']==n and r['checks']==truth and all(truth.values()) and not r['failed_checks']
 check('all_resource_thresholds_recomputed_from_saved_actuals',True)
 manifest=[json.loads(l) for l in (output/'diagnostic_manifest.jsonl').read_text().splitlines()];runs={r['label']:r for r in q['models']}
 check('manifest_exact20_order',len(manifest)==20 and [r['run']+':'+r['case_id'] for r in manifest]==labels)
 for row,rec,n in zip(rows,manifest,casepaths):
  assert rec['path']==n and rec['fold']==row['fold'] and rec['input_sha256']==row['input']['sha256'] and rec['normalization']==row['normalization'] and rec['checkpoint_sha256']==runs[row['run']]['checkpoint']['sha256']
  assert (rec['bytes'],rec['sha256'])==(a['output']['files'][n]['bytes'],a['output']['files'][n]['sha256'])
 check('manifest_input_weight_frame_and_file_hashes',True)
 for name,r in read(F/'metadata_result_v1.json')['files'].items():assert sha(D/name)==r['sha256'] and (D/name).stat().st_size==r['bytes']
 check('all_downloaded_control_metadata_hashes_match_remote_inventory',True)
 archive_info=read(F/'archive_result_v1.json');tar=F/'downloads/development_predictions_v1.tar.gz'
 check('downloaded_archive_SHA256',sha(tar)==archive_info['archive']['sha256']=='04c7b4fa54d0039c2502726b4eae284d093519b6ba91846c888646fc819d51ec' and tar.stat().st_size==13610252)
 check('archive24_member_source_and_resource_prefix_relationship',len(archive_info['members'])==24 and len(archive_info['notes'])==1)
 summaries=[];fields={'Q0','M','F','z','Q1','N0','Q2_R','v','N1','u','delta0','delta_A','delta_D','Q2_A','Q2_D','P_R','P_A','P_D','nu','nv','valid','c','a'}
 def close(x,y):return bool(np.allclose(x,y,atol=2e-6,rtol=2e-5))
 def same(x,y):return np.linalg.norm(x-y,axis=-1)<=1e-6+1e-4*np.maximum(np.linalg.norm(x,axis=-1),np.linalg.norm(y,axis=-1))
 with tarfile.open(tar,'r:gz') as t:
  members={m.name:m for m in t}
  for row,n in zip(rows,casepaths):
   raw=t.extractfile(members[n]).read();assert hashlib.sha256(raw).hexdigest()==a['output']['files'][n]['sha256']
   with np.load(io.BytesIO(raw),allow_pickle=False) as z:d={k:z[k].copy() for k in z.files}
   assert set(d)==fields
   for k,v in d.items():
    shape=(1,256,384) if k=='F' else (1,1024) if k=='z' else (1,256,8) if k in ('N0','N1') else (1,8192,3) if k.startswith('P_') else (1,256,1) if k in ('nu','nv','valid','c','a') else (1,256,3)
    dtype=np.int64 if k in ('N0','N1') else np.bool_ if k=='valid' else np.float32
    assert v.shape==shape and v.dtype==dtype and np.isfinite(v).all(),(row['case_id'],k)
   assert close(d['Q0']+d['delta0'],d['Q1']) and close(d['Q1']+d['v'],d['Q2_R'])
   assert close((d['u']+d['v'])*.5,d['delta_A']) and close(d['Q1']+d['delta_A'],d['Q2_A']) and close(d['Q1']+d['delta_D'],d['Q2_D'])
   nu=np.linalg.norm(d['u'],axis=-1,keepdims=True);nv=np.linalg.norm(d['v'],axis=-1,keepdims=True);valid=(nu>1e-6)&(nv>1e-6)
   cosine=np.sum((d['u']/np.maximum(nu,1e-6))*(d['v']/np.maximum(nv,1e-6)),axis=-1,keepdims=True).clip(-1,1);cosine=np.where(valid,cosine,0);alpha=.5+.5*np.maximum(cosine,0)
   assert np.array_equal(valid,d['valid']) and close(nu,d['nu']) and close(nv,d['nv']) and close(cosine,d['c']) and close(alpha,d['a'])
   assert close(d['a']*d['v']+(1-d['a'])*d['u'],d['delta_D'])
   for key,query in (('N0',d['Q0']),('N1',d['Q1'])):
    idx=d[key][0];assert ((idx>=0)&(idx<256)).all() and (np.diff(np.sort(idx,axis=-1),axis=-1)>0).all()
    distances=np.linalg.norm(d['M'][0].astype('float64')[None,:,:]-query[0].astype('float64')[:,None,:],axis=-1);cutoff=np.partition(distances,7,axis=1)[:,7]
    assert (np.take_along_axis(distances,idx,axis=1)<=cutoff[:,None]+1e-5+1e-5*cutoff[:,None]).all()
   replay=B/'replay'/(row['run']+'__'+row['case_id']+'.npz');assert sha(replay)==row['replay']['sha256']
   with np.load(replay,allow_pickle=False) as old:
    assert np.allclose(d['P_R'][0],old['prediction'],atol=1e-5,rtol=1e-4) and np.allclose(d['Q2_R'][0],old['coarse'],atol=1e-5,rtol=1e-4)
   scale=row['normalization']['scale'];da=np.linalg.norm(d['delta_D']-d['delta_A'],axis=-1);dr=np.linalg.norm(d['delta_D']-d['v'],axis=-1)
   overlap=np.mean([len(set(x)&set(y))/8 for x,y in zip(d['N0'][0],d['N1'][0])])
   summaries.append(dict(fold=row['fold'],case_id=row['case_id'],selection=row['selection'],valid_queries=int(valid.sum()),cosine_mean=float(d['c'].mean()),alpha_mean=float(d['a'].mean()),alpha_min=float(d['a'].min()),alpha_max=float(d['a'].max()),nonpositive_cos_fraction=float((d['c']<=0).mean()),neighbor_overlap_mean=float(overlap),old_new_numerically_same_fraction=float(same(d['u'],d['v']).mean()),D_A_update_same_fraction=float(same(d['delta_D'],d['delta_A']).mean()),D_R_update_same_fraction=float(same(d['delta_D'],d['v']).mean()),D_A_update_mean_mm=float(da.mean()*scale),D_R_update_mean_mm=float(dr.mean()*scale),D_A_dense_displacement_mean_mm=float(np.linalg.norm(d['P_D']-d['P_A'],axis=-1).mean()*scale),D_R_dense_displacement_mean_mm=float(np.linalg.norm(d['P_D']-d['P_R'],axis=-1).mean()*scale),D_A_dense_allclose=bool(np.allclose(d['P_D'],d['P_A'],atol=1e-6,rtol=1e-4)),D_R_dense_allclose=bool(np.allclose(d['P_D'],d['P_R'],atol=1e-6,rtol=1e-4))))
 check('all20_saved_tensor_sets_shapes_dtypes_finite',len(summaries)==20)
 check('all20_Q_stage_and_DAC_v2_formula_consistent',True)
 check('all20_actual_Memory_KNN_cutoffs_and_unique_indices',True)
 check('all20_Native_replays_independently_match_frozen_predictions',True)
 limits=dict(RNG='Only runtime equality assertion and boolean saved; no raw before/after RNG fingerprints. Source identity and successful completion corroborate assertion, not an independent RNG snapshot rehash.',resources='Cooperative saved samples; no hard peak RSS/VRAM guarantee between samples.',archive='resources.jsonl inside archive is exact prefix; the final archived sample exists only in external frozen log by original entry order.',geometry='No GT payload, E/J scoring, clinical assessment, or train authorization.')
 report=dict(status='FORMAL_DAC_R1_FREEZE_PASS_WITH_DISCLOSED_RNG_EVIDENCE_LIMITATION',request_sha256=RH,checks=checks,check_count=len(checks),calls=counts,case_files=20,control_files=4,output_files=32,installed_files=32,archive=archive_info['archive'],models=models,RNG_evidence_level='RUNTIME_ASSERTION_NOT_RAW_FINGERPRINT_PAIR',resource_peaks={k:max(r['values'][k] for r in resources) for k in ('RSS_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds')},limitations=limits,server_writes=0,new_forward=0,GT_scoring=0,training=0,request_reusable=False)
 save(F/'freeze_verification_v1.json',report)
 # Conditional next activity: descriptive review of stored tensors only, no GT scores.
 folds={}
 for fold in 'CD':
  s=[r for r in summaries if r['fold']==fold]
  fields_num=['cosine_mean','alpha_mean','neighbor_overlap_mean','old_new_numerically_same_fraction','D_A_update_same_fraction','D_R_update_same_fraction','D_A_update_mean_mm','D_R_update_mean_mm','D_A_dense_displacement_mean_mm','D_R_dense_displacement_mean_mm']
  folds[fold]={k:float(np.mean([r[k] for r in s])) for k in fields_num}
  folds[fold]['cases']=10;folds[fold]['D_A_dense_allclose_cases']=sum(r['D_A_dense_allclose'] for r in s);folds[fold]['D_R_dense_allclose_cases']=sum(r['D_R_dense_allclose'] for r in s)
  folds[fold]['degenerate_A_screen']=folds[fold]['D_A_update_same_fraction']>=.95 and folds[fold]['D_A_dense_allclose_cases']==10
  folds[fold]['degenerate_R_screen']=folds[fold]['D_R_update_same_fraction']>=.95 and folds[fold]['D_R_dense_allclose_cases']==10
 save(F/'GT_free_mechanism_review_v1.json',dict(status='DESCRIPTIVE_STORED_TENSOR_REVIEW_AFTER_QUALIFIED_FREEZE_PASS',case_summaries=summaries,folds=folds,uses_GT=False,geometry_accuracy_computed=False,interpretation='Displacements are differences between counterfactual outputs, not accuracy improvements. No train decision justified without the prespecified geometry/rescue review.',new_forward=0,new_parameters=0))
 print(json.dumps(dict(status=report['status'],checks=len(checks),resource_peaks=report['resource_peaks'],fold_mechanism=folds),ensure_ascii=True))
except BaseException as exc:
 save(F/'verification_failure_v1.json',dict(status='FORMAL_FREEZE_FAILED_STOP_NO_RETRY',passed_checks=checks,error=repr(exc),new_forward=0,server_writes=0));raise
