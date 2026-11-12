"""Local cross-evidence audit and descriptive summaries; no model or array loading."""
import ast,collections,hashlib,importlib.util,json,math,statistics
from pathlib import Path,PurePosixPath
F=Path(__file__).resolve().parent;B=F.parent;D=F/'downloads';O=D/'output';I=D/'installed';V=F/'continuation_v2'
QH='a21965cdefdf4a7903b5cb52b235dc5e30f0cd9d25a25915734967ee6ff7eda2';checks={}
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def check(k,v):
 if not v:raise AssertionError(k)
 checks[k]=True
def emit(n,x):
 with (F/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def finite(x):
 if isinstance(x,float):return math.isfinite(x)
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,list):return all(finite(v) for v in x)
 return True
def rng_valid(r):
 assert set(r)=={'CPU','CUDA','Python','numpy'}
 assert all(len(r[k])==64 and len(bytes.fromhex(r[k]))==32 for k in ('CPU','CUDA'))
 py=ast.literal_eval(r['Python']);assert len(py)==3 and py[0]==3 and len(py[1])==625
 prefix=repr('MT19937');s=r['numpy'];assert s.startswith(prefix) and len(bytes.fromhex(s[len(prefix):len(prefix)+4992]))==2496
 tail=ast.literal_eval(s[len(prefix)+4992:]);assert len(tail)==3 and 0<=tail[0]<=624 and tail[1] in (0,1) and math.isfinite(tail[2]);return True
def main():
 qfile=I/'F0_CD_decoder_diagnostic_execution_request_v1.json';q=read(qfile);index=read(I/'context_index_candidate_v1.json')
 check('01 exact authorized request unchanged',sha(qfile)==QH and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION')
 inv=read(F/'inventory_before_result_v1.json');after=read(V/'inventory_after_result_v2.json')
 check('02 output and install content fingerprints stable excluding atime',inv==after)
 labels=[r['run']+'__'+r['recipient']+'__'+c for r in index['pairs'] for c in q['conditions']]
 expected={folder+'/'+label+'.npz' for label in labels for folder in ('predictions','traces')}|{'calls.jsonl','completion.json','development_predictions_v1.tar.gz','development_predictions_v1.tar.gz.bytes','development_predictions_v1.tar.gz.contents.sha256','development_predictions_v1.tar.gz.sha256','diagnostic_complete.json','exit_code.txt','isolation.jsonl','launch.log','resources.jsonl','responses.jsonl','worker.pid'}
 check('03 exact73 output files4 directories',set(inv['output']['files'])==expected and len(expected)==73 and set(inv['output']['directories'])=={'.','predictions','traces','tmp'})
 mapping=read(B/'frozen_pending_transport_v1/installation_mapping_v1.json');controls={'decoder_diagnostic_authorization_v1.json','decoder_diagnostic_runtime_v1.json','decoder_diagnostic_once_v1.sh','decoder_diagnostic_single_attempt_claim_v1.json','readiness_and_installation_receipt_v1.json','startup_receipt_v1.json'}
 check('04 exact7 installed files6 controls2 directories',set(inv['install']['files'])=={PurePosixPath(r['target']).name for r in mapping['files']}|{'control/'+n for n in controls} and len(inv['install']['files'])==13 and set(inv['install']['directories'])=={'.','control'})
 hb=read(F/'hashes_before_result_v1.json');ha=read(V/'hashes_after_result_v2.json');hm={r['name']:r for r in hb['files']}
 check('05 independent full hashes stable before after',hb['files']==ha['files'] and set(hm)==expected)
 check('06 hash sizes agree content fingerprint',all(r['bytes']==inv['output']['files'][n][3] for n,r in hm.items()))
 check('07 all7 installed files match frozen package',all(sha(I/PurePosixPath(r['target']).name)==r['sha256'] and (I/PurePosixPath(r['target']).name).stat().st_size==r['bytes'] for r in mapping['files']))
 md=read(F/'metadata_result_v1.json')
 check('08 every downloaded metadata original bytes match',all(sha(D/n)==r['sha256'] and (D/n).stat().st_size==r['bytes'] for n,r in md['files'].items()))
 check('09 downloaded output metadata matches independent hash pass',all(hm[n.split('/',1)[1]]['sha256']==r['sha256'] for n,r in md['files'].items() if n.startswith('output/')))
 check('10 both observed exit0 worker tmux absent',read(F/'finished_result_v1.json')['status']==read(V/'finished_after_result_v2.json')['status']=='EXIT0_WORKER_TMUX_ABSENT' and (O/'exit_code.txt').read_text().strip()=='0')
 C=I/'control';auth=read(C/'decoder_diagnostic_authorization_v1.json');runtime=read(C/'decoder_diagnostic_runtime_v1.json')
 check('11 explicit authorization full request binding',set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-development-authorization-v1' and auth['request_sha256']==QH and auth['explicit_user_authorization'] is True and QH in auth['user_authorization_text'])
 check('12 one way runtime receipt binding',runtime==dict(schema='bcsp-development-runtime-v1',request_sha256=QH,authorization_sha256=sha(C/'decoder_diagnostic_authorization_v1.json')))
 check('13 single claim and no execution failure',read(C/'decoder_diagnostic_single_attempt_claim_v1.json')==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH) and not any('failure' in n for n in expected|set(inv['install']['files'])))
 entry=I/'bcsp_f0_condition_diagnostic_v1.py';spec=importlib.util.spec_from_file_location('frozen_inert_diagnostic_audit',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
 def rr(p):return rec(p)
 original_bound=e.bound
 def downloaded_bound(r):
  if r['path'].startswith(q['entry']['path'].rsplit('/',1)[0]+'/'):
   r=dict(r,path=str(I/PurePosixPath(r['path']).name))
  return original_bound(r)
 e.bound=downloaded_bound
 e.authorize(rr(qfile),rr(C/'decoder_diagnostic_authorization_v1.json'),rr(C/'decoder_diagnostic_runtime_v1.json'))
 check('14 actual inert authorize and fixed ten pair metadata',True)
 source=B.parent/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py';check('15 frozen native helper local source matches',sha(source)==q['native_helper']['sha256'])
 sp=importlib.util.spec_from_file_location('frozen_native_launcher_audit',source);p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)
 check('16 launcher exactly frozen renderer', (C/'decoder_diagnostic_once_v1.sh').read_text()==p.render_launcher(q,QH,sha(C/'decoder_diagnostic_authorization_v1.json'),sha(C/'decoder_diagnostic_runtime_v1.json')))
 startup=read(C/'startup_receipt_v1.json');receipt=read(C/'readiness_and_installation_receipt_v1.json')
 check('17 startup receipt chain session',startup['request_sha256']==QH and startup['tmux_returncode']==0 and startup['session']==q['launch_contract']['tmux_session'] and startup['authorization_sha256']==sha(C/'decoder_diagnostic_authorization_v1.json') and startup['runtime_sha256']==sha(C/'decoder_diagnostic_runtime_v1.json') and startup['launcher_sha256']==sha(C/'decoder_diagnostic_once_v1.sh'))
 check('18 no overwrite installation receipt',receipt['status']=='SEVEN_EXCLUSIVE_INSTALL_HASHES_PASS' and receipt['request_sha256']==QH and receipt['overwritten_files']==0 and receipt['frozen_cache_files_hashed']==40 and receipt['checkpoint_files_hashed']==2)
 assets=read(F/'assets_result_v1.json');am={r['path']:r for r in assets['records']}
 check('19 exact40 original caches and both weights freshly rehashed',all(am[r[k]['path']]['sha256']==r[k]['sha256'] for r in index['pairs'] for k in ('recipient_context','donor_context','Native_trace','Native_prediction')) and all(am[r['checkpoint']['path']]['sha256']==r['checkpoint']['sha256'] for r in index['runs']))
 check('20 frozen provider dependencies mother and implementation rehashed',all(am[r['path']]['sha256']==r['sha256'] for r in receipt['read_manifest'] if not r['path'].startswith(q['entry']['path'].rsplit('/',1)[0]+'/')))
 check('21 prior CPU34 plus integration7 and final P3 source bindings',read(I/'post_test_freeze_and_P3_v1.json')['status']=='F0_CONDITION_LOCAL_P3_PASS' and read(I/'CPU_contract_evidence_v1.json')['tensor_batch']['count']==34 and read(I/'CPU_contract_evidence_v1.json')['entry_batch']['count']==7)
 done=read(O/'diagnostic_complete.json');complete=read(O/'completion.json')
 check('22 complete30 decoder30 head720SSM zero prohibited calls',done['decoder_calls']==done['head_calls']==30 and done['native_ssm_calls']==720 and all(done[k]==0 for k in ('encoder_calls','coarse_calls','Native_replay','backward','optimizer_steps')) and done['request_sha256']==complete['request_sha256']==QH and complete['status']=='DIAGNOSTICS_ARCHIVED_AWAITING_FREEZE_AUDIT')
 journal=rows(O/'calls.jsonl');isolation=rows(O/'isolation.jsonl');responses=rows(O/'responses.jsonl');resources=rows(O/'resources.jsonl')
 check('23 exact30 claims returns labels order no retry',len(journal)==60 and all(journal[i*2]==dict(index=i+1,label=label,status='CLAIMED_BEFORE_SUFFIX') and journal[i*2+1]==dict(index=i+1,label=label,status='SUFFIX_COMPLETE') for i,label in enumerate(labels)))
 check('24 exact30 isolation proofs and720SSM counters',len(isolation)==30 and all(r['index']==i+1 and r['label']==labels[i] and r['counts']==dict(decoder=1,head=1,self_ssm=16,cond_ssm=8,local_cross=1,forbidden=0,donor_knn=int(labels[i].endswith('__local_graph_donor'))) and r['z_Q_X_unchanged'] and r['donor_unchanged'] for i,r in enumerate(isolation)))
 check('25 each8 layer branch source and null site',all(r['isolation']==[dict(layer=j,prefix_source='donor' if labels[i].endswith('__prefix_donor') else 'recipient',raw_feature_zero=labels[i].endswith('__prefix_feature_null'),local_source='donor' if labels[i].endswith('__local_graph_donor') else 'recipient') for j in range(8)] for i,r in enumerate(isolation)))
 expected_slots={(j,k,'all') for j in range(8) for k in ('input','after_self','prefix_suffix','after_cross','output')}|{(j,'prefix_suffix',g) for j in range(8) for g in ('early','middle','late')}
 check('26 exact30 responses1920 unique layer group slots',len(responses)==30 and all(r['index']==i+1 and r['label']==labels[i] and r['donor']==index['pairs'][i//3]['donor'] and len(r['layers'])==64 and {(s['layer'],s['stage'],s['group']) for s in r['layers']}==expected_slots for i,r in enumerate(responses)) and all(finite(r) for r in responses))
 check('27 all30 Q X layerchain and firstbranch isolation independently inspected',read(F/'arrays_result_v1.json')['status']=='ALL30_ARRAYS_FIXED_Q_X_CHAIN_ISOLATION_PASS')
 recomputations=[read(V/('responses_'+fold+'_result_v2.json')) for fold in ('C','D')]
 check('28 independently recomputed all1980 numeric responses',all(r['status']=='RESPONSE_RECOMPUTE_PASS' and r['case_conditions']==15 and r['comparisons']==990 and r['max_absolute_float_error']<1e-10 for r in recomputations))
 models=done['models'];check('29 two models all parameters and BN buffers unchanged',len(models)==2 and [r['run'] for r in models]==['C_F0','D_F0'] and all(r['state_before']==r['state_after'] and len(bytes.fromhex(r['state_before']))==32 for r in models))
 check('30 CPU CUDA Python NumPy RNG unchanged valid formats',all(r['RNG_before']==r['RNG_after'] and rng_valid(r['RNG_before']) for r in models))
 check('31 all61 resource samples all frozen thresholds pass',len(resources)==61 and [r['forwards'] for r in resources]==[(i+1)//2 for i in range(60)]+[30] and all(all(r['checks'].values()) and not r['failed_checks'] and r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE' for r in resources))
 # before/after labels count pattern is 0,1,1,2,...,29,30,30.
 archive=complete['archive'];ar=hm['development_predictions_v1.tar.gz']
 check('32 archive whole hash size and sidecars',archive['sha256']==ar['sha256']==(O/'development_predictions_v1.tar.gz.sha256').read_text().split()[0] and archive['bytes']==ar['bytes']==int((O/'development_predictions_v1.tar.gz.bytes').read_text()))
 members=archive['members'];check('33 exact65 archive members parity against output',len(members)==65 and {r['name'] for r in members}=={n for n in expected if n.startswith(('predictions/','traces/'))}|{'calls.jsonl','responses.jsonl','isolation.jsonl','diagnostic_complete.json','resources.jsonl'} and all(hm[r['name']]==r for r in members) and read(F/'archive_result_v1.json')['members']==65)
 check('34 exact archive contents checksum listing', (O/'development_predictions_v1.tar.gz.contents.sha256').read_text()==''.join(r['sha256']+'  '+r['name']+'\n' for r in members))
 limits=q['limits'];check('35 final output and disk within budget',sum(r['bytes'] for r in hm.values())<=limits['output_bytes'] and read(V/'finished_after_result_v2.json')['free_disk_bytes']>=limits['minimum_free_disk_bytes'])
 peak={k:max(r['values'][k] for r in resources) for k in ('RSS_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds')}
 emit('formal_post_diagnostic_freeze_audit_result_v1.json',dict(status='FORMAL_F0_30_DECODER_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS',checks=checks,check_count=len(checks),request_sha256=QH,archive=archive,counts=dict(decoder=30,head=30,native_SSM=720,predictions=30,traces=30,layer_response_rows=1920,dense_response_comparisons=60,encoder=0,coarse=0,backward=0,optimizer_steps=0),resources_peak=peak,output_bytes=sum(r['bytes'] for r in hm.values()),audit_response_max_error=max(r['max_absolute_float_error'] for r in recomputations),read_only=True,new_model_calls=0,server_writes=0,prior_v1_response_audit_failure_preserved=True,limitation='Read-only reconstruction validates records and arrays; it cannot retrospectively attest every internal runtime instruction independently of the bound instrumented source.'))
 # Descriptive summaries only after every audit criterion has passed.
 summaries=[]
 for fold in ('C','D','ALL'):
  for condition in q['conditions']:
   selected=[r for r in responses if (fold=='ALL' or r['label'].startswith(fold+'_F0')) and r['label'].endswith('__'+condition)]
   vals=[r['dense']['world_mm']['RMSE'] for r in selected]
   def stage(layer,stage,group='all'):
    return [next(s['RMSE'] for s in r['layers'] if s['layer']==layer and s['stage']==stage and s['group']==group) for r in selected]
   summaries.append(dict(fold=fold,condition=condition,n=len(selected),dense_coordinate_RMSE_mm_mean=statistics.mean(vals),dense_coordinate_RMSE_mm_median=statistics.median(vals),dense_coordinate_RMSE_mm_min=min(vals),dense_coordinate_RMSE_mm_max=max(vals),dense_allclose_count=sum(r['dense']['normalized']['allclose'] for r in selected),layer0_prefix_RMSE_mean=statistics.mean(stage(0,'prefix_suffix')),layer0_aftercross_RMSE_mean=statistics.mean(stage(0,'after_cross')),layer7_prefix_RMSE_mean=statistics.mean(stage(7,'prefix_suffix')),layer7_output_RMSE_mean=statistics.mean(stage(7,'output')),layer0_prefix_by_group={g:statistics.mean(stage(0,'prefix_suffix',g)) for g in ('early','middle','late')},layer7_prefix_by_group={g:statistics.mean(stage(7,'prefix_suffix',g)) for g in ('early','middle','late')}))
 case_rows=[]
 for i,r in enumerate(responses):case_rows.append(dict(label=r['label'],donor=r['donor'],condition=q['conditions'][i%3],fold=index['pairs'][i//3]['run'][0],case_id=index['pairs'][i//3]['recipient'],dense_coordinate_RMSE_mm=r['dense']['world_mm']['RMSE'],dense_max_abs_coordinate_mm=r['dense']['world_mm']['max_abs'],dense_relative_L2=r['dense']['normalized']['relative_L2']))
 emit('frozen_diagnostic_descriptive_values_v1.json',dict(status='DESCRIPTIVE_ONLY_AFTER_FORMAL_AUDIT_PASS',audit=rec(F/'formal_post_diagnostic_freeze_audit_result_v1.json'),summaries=summaries,case_rows=case_rows,not_official_performance=True,not_hypothesis_test=True))
 print(json.dumps(dict(status='FORMAL_AUDIT_PASS',checks=len(checks),archive_SHA256=archive['sha256'],summaries=summaries),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
