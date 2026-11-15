"""Formal T0 freeze audit: stdlib, opaque checkpoint hashing, no tensor loading."""
import collections,hashlib,json,math,os,pathlib,shutil,socket,stat,subprocess,time
P=pathlib.Path('/home/jovyan/adapointr_work/PoinTr');D=P/'third_party/bcsp_p1_foldD_training_20261106_v1';O=P/'logs/cranial_bcsp_mamba_p1/T0_foldD_seed0_train_20261106_v1'
Q='6a9e9bcdbfa60a6a9bc6b80c6d2d1374796aa02c919766c2fb70b3a0aa764f82'
checks={};records={};total=0;start=time.monotonic()
def check(k,v):
 checks[k]=bool(v)
 if not v:raise ValueError(k)
def clean(p):
 p=pathlib.Path(p);check('unlinked:'+str(p),not any(x.is_symlink() for x in (p,*p.parents)));return p
def meta(p):
 s=p.stat();return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,mode=stat.S_IMODE(s.st_mode),uid=s.st_uid,gid=s.st_gid)
def rec(p):
 global total
 p=clean(p);s=meta(p);cap=512*1024**2 if p==O/'ckpt-last.pth' else 16*1024**2
 check('bounded_regular:'+str(p),p.is_file() and s['bytes']<=cap and total+s['bytes']<=1024**3 and len(records)<128 and time.monotonic()-start<45)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);total+=len(b)
 check('stable_read:'+str(p),s==meta(p));r=dict(path=str(p),sha256=h.hexdigest(),**s);records[str(p)]=r;return r
def js(p):return json.loads(clean(p).read_bytes())
def lines(p):
 b=clean(p).read_bytes();check('newline_terminated:'+str(p),not b or b.endswith(b'\n'));return [json.loads(s) for s in b.splitlines() if s]
def exact(r):
 a=rec(r['path']);check('binding:'+a['path'],a['bytes']==r['bytes'] and a['sha256']==r['sha256'])
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def close(a,b):return isinstance(a,(int,float)) and math.isfinite(a) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-15)
try:
 check('hostname_uid_project',socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000 and P.resolve()==P)
 request=D/'T0_foldD_seed0_training_execution_request_v1.json';check('request_SHA256',rec(request)['sha256']==Q);q=js(request)
 check('T0_request_identity',q['variant']=='T0' and q['fold']=='D' and q['n_input']==q['n_output']==8192)
 controls={'T0_authorization_v1.json':'192c865cd34c597b89003929e13e6703f72702c4c11a1fadfb6b546de2bab861','T0_runtime_v1.json':'9c162efe1164b22007c7f9eaf51164091b9564b63114d3b32fa6d3aae80d5cd0','T0_launch_once_v1.sh':'1d2de752a21cc13a5c4ab82890ecd31462a3dcdda37c670a7af202e1db52548e'}
 for n,h in controls.items():check('control:'+n,rec(D/'control'/n)['sha256']==h)
 rec(q['launch_attempt']);check('single_claim',js(q['launch_attempt'])==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=Q))
 auth=js(D/'control/T0_authorization_v1.json');runtime=js(D/'control/T0_runtime_v1.json')
 check('one_way_authorization',set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-p1-training-authorization-v1' and auth['request_sha256']==Q and auth['explicit_user_authorization'] is True and runtime==dict(schema='bcsp-p1-training-runtime-v1',request_sha256=Q,authorization_sha256=controls['T0_authorization_v1.json']))
 for r in q['implementation'].values():exact(r)
 for k in ('numeric_policy','numeric_protocol','pair_contract','quantification_audit','quantification_request','initialization_reference','static_config','order_plan','preflight_scope'):exact(q[k])
 for k in ('qualified_receipt','verification','fold_binding'):exact(q['QC'][k])
 for r in q['QC']['manifests'].values():exact(r)
 exact(q['launch_contract']['launcher_template'])
 for name,key in [('implementation_P3_v1.json','implementation_P3_sha256'),('CPU_contract_result_v1.json','CPU_contract_result_sha256')]:check('bound_D_evidence:'+name,rec(D/name)['sha256']==q['provenance'][key])
 check('D_entry_CPU_P3',js(D/'implementation_P3_v1.json')['status']=='PASS_FOR_PENDING_T0_D_REQUEST_ONLY' and js(D/'CPU_contract_result_v1.json')['count']==62)
 check('exact_install_root',{p.name for p in D.iterdir()}=={request.name,'bcsp_p1_foldD_training_entry_v1.py','CPU_contract_result_v1.json','implementation_P3_v1.json','paired_FoldD_training_contract_v1.json','launch_once_template_v1.sh','control'})
 check('exact_control_set',{p.name for p in (D/'control').iterdir()}==set(controls)|{'T0_launch_attempt_v1.json'})
 expected_launcher=clean(q['launch_contract']['launcher_template']['path']).read_text().replace('REQUEST_SHA256',Q).replace('AUTHORIZATION_SHA256',controls['T0_authorization_v1.json']).replace('RUNTIME_SHA256',controls['T0_runtime_v1.json'])
 check('launcher_materialization',expected_launcher.encode('ascii')==(D/'control/T0_launch_once_v1.sh').read_bytes())
 policy=js(q['numeric_policy']['path']);check('policy_accepted_prior_failure_unchanged',policy['prior_v3_status']=='FAILED_STOP_NO_RETRY' and policy['bitwise_gradient_equality_required_for_training_preparation'] is False and policy['deterministic_flags_changed'] is False and policy['training_execution_authorized'] is False)
 names={'ckpt-last.pth','completion.json','exit_code.txt','exposure.json','initialization.json','launch.log','metrics.jsonl','model_construction.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','order_plan.json','payload_manifest.json','resources.jsonl','run_identity.json','worker.pid','tmp'}
 check('exact_output_set',{p.name for p in O.iterdir()}==names);clean(O/'tmp');check('tmp_empty',not list((O/'tmp').iterdir()))
 for n in sorted(names-{'tmp'}):rec(O/n)
 check('exit_zero',(O/'exit_code.txt').read_text().strip()=='0')
 check('tmux_absent',subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1)
 pid=int((O/'worker.pid').read_text());proc=pathlib.Path('/proc')/str(pid)/'cmdline';check('worker_absent',not proc.exists() or q['implementation']['entry']['path'].encode() not in proc.read_bytes())
 manifest=js(O/'payload_manifest.json')['files'];expected_manifest=names-{'tmp','worker.pid','launch.log','exit_code.txt','payload_manifest.json'}
 check('exact_payload_manifest',len(manifest)==len({r['name'] for r in manifest}) and {r['name'] for r in manifest}==expected_manifest)
 for r in manifest:
  a=records[str(O/r['name'])];check('manifest:'+r['name'],a['bytes']==r['bytes'] and a['sha256']==r['sha256'])
 completion=js(O/'completion.json');initial=js(O/'initialization.json');exposure=js(O/'exposure.json');construction=js(O/'model_construction.json');historical=js(q['initialization_reference']['path'])
 check('factory_initialization_exact',construction==dict(factory=historical['factory']) and construction['factory']['variant']=='T0' and not construction['factory']['artificial_fixture'] and construction['factory']['replaced_global_branches']==0 and construction['factory']['common_state_unchanged'])
 # Validate the full initial state fingerprint against the already frozen GPU replay; no reconstruction.
 qa=js(q['quantification_audit']['path']);qcfile=next(r for r in qa['files'] if r['path'].endswith('/gradient_quantification_20261105_v1/completion.json'));exact({k:qcfile[k] for k in ('path','bytes','sha256')});qc=js(qcfile['path']);qm=next(m for m in qc['models'] if m['variant']=='T0')
 check('persistent_initialization_matches_frozen_GPU_replay',initial['seed']==0 and initial['persistent_state_sha256']==qm['state_sha256'] and len(initial['parameter_sha256'])==64)
 identity=js(O/'run_identity.json');check('P1_identity_and_numeric_disclosure',identity==dict(stage='CRANIAL_BCSP_MAMBA_P1',variant='T0',fold='D',seed=0,numeric_policy_sha256=q['numeric_policy']['sha256'],quantification_audit_sha256=q['quantification_audit']['sha256'],prior_v3_status='FAILED_STOP_NO_RETRY',checkpoint_legacy_stage='BCSP_INPUT_DENSITY_V1',legacy_stage_is_provenance_only=True,SSM_gradient_non_bitwise_reproducibility_disclosed=True))
 plan=js(q['order_plan']['path']);check('saved_plan_equals_frozen_plan',js(O/'order_plan.json')==plan);order_hash=canonical(plan)
 check('all_canonical_order_bindings',completion['order_sha256']==initial['order_sha256']==exposure['order_sha256']==order_hash)
 check('completion_counts',completion['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100) and completion['optimizer_updates']==3900 and completion['traversals']==100 and completion['case_exposures']==31200)
 check('no_BNCal_eval_resume',completion['bncal_executed'] is False and completion['evaluation_executed'] is False and completion['resume'] is False)
 check('checkpoint_SHA256_matches_completion',records[str(O/'ckpt-last.pth')]['sha256']==completion['checkpoint_sha256'])
 fold=js(q['QC']['fold_binding']['path'])['folds']['D'];mr=lines(q['QC']['manifests']['8192']['path']);lookup={r['case_id']:r for r in mr}
 check('fold_source_boundary',len(lookup)==420 and len(fold['train_sources'])==63 and len(fold['train_case_ids'])==315 and not set(fold['train_sources'])&set(fold['dev_sources']) and plan['case_ids']==fold['train_case_ids'])
 metrics=lines(O/'metrics.jsonl');check('3900_complete_metrics',len(metrics)==3900);case=collections.Counter();source=collections.Counter();drop=collections.Counter();step=0
 for epoch,row in enumerate(plan['epochs']):
  check('plan_epoch:'+str(epoch),row['epoch']==epoch and len(row['batches'])==39 and len(row['dropped'])==3 and set(sum(row['batches'],[])+row['dropped'])==set(plan['case_ids']))
  for batch,ids in enumerate(row['batches']):
   m=metrics[step];step+=1;sources=[lookup[c]['source_id'] for c in ids]
   ok=len(ids)==8 and m['step']==step and m['epoch']==epoch and m['batch']==batch and m['case_ids']==ids and m['source_ids']==sources and all(s in fold['train_sources'] for s in sources) and m['optimizer_step_committed'] is True and m['clip_max_norm']==10
   ok=ok and m['loss_sparse']==m['loss_denoise']==0 and close(m['loss'],m['loss_dense']) and close(m['loss_dense'],m['loss_reconstruction']) and math.isfinite(m['grad_norm_before_clip']) and m['grad_norm_before_clip']>=0 and len(m['LR'])==2 and all(close(x,.0001*max(.9**(epoch/21),.02)) for x in m['LR']) and close(m['BN_momentum'],max(.9*.5**(epoch/21),.01))
   if not ok:raise ValueError('actual metric/order/numeric contract step '+str(step))
   case.update(ids);source.update(sources)
  drop.update(row['dropped'])
 check('full_actual_order_numeric_LR_BN',step==3900)
 check('reconstructed_exposure_exact',dict(case)==exposure['case'] and dict(source)==exposure['source'] and dict(drop)==exposure['dropped_case'] and sum(case.values())==sum(source.values())==31200 and sum(drop.values())==300)
 groups=js(O/'optimizer_parameter_groups.json');check('optimizer_groups_match_frozen_initialization',groups==historical['optimizer_groups'] and len(groups)==len({r['name'] for r in groups})==332)
 check('effective_optimizer_decay',all(r['weight_decay']==(0. if len(r['shape'])==1 or r['name'].endswith('.bias') else .0005) for r in groups))
 defaults=js(O/'optimizer_actual_defaults.json');check('optimizer_numeric_defaults',defaults['lr']==.0001 and defaults['betas']==[.9,.999] and defaults['eps']==1e-8 and defaults['amsgrad'] is False and defaults['foreach'] is None and defaults['fused'] is None)
 static=js(q['static_config']['path']);resources=lines(O/'resources.jsonl');L=static['resources'];check('3902_resource_records',len(resources)==3902)
 for i,r in enumerate(resources):
  expected=('after_step',i+1) if i<3900 else ('before_final' if i==3900 else 'after_final',3900)
  ok=(r['phase'],r['committed_step'])==expected and r['limits']==L and r['resource_guard_passed'] is True and all(r['checks'].values()) and not r['failed_checks'] and r['RSS']<=L['RSS_bytes'] and r['output_bytes']<=L['output_bytes'] and r['peak_allocated']<=L['torch_peak_bytes'] and r['peak_reserved']<=L['torch_peak_bytes'] and r['device_MiB']<=L['device_MiB'] and r['elapsed_seconds']<=L['wall_seconds'] and r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
  if not ok:raise ValueError('resource contract record '+str(i))
  expected_checks=dict(allocated_within_limit=r['peak_allocated']<=L['torch_peak_bytes'],reserved_within_limit=r['peak_reserved']<=L['torch_peak_bytes'],device_within_limit=r['device_MiB']<=L['device_MiB']);check('resource_numeric_thresholds:'+str(i),r['checks']==expected_checks)
 check('all_resource_contracts',True);check('current_disk_reserve',shutil.disk_usage(P).free>=L['minimum_free_disk_bytes'])
 baseline=list(records.values())
 for r in baseline:check('stable_end:'+r['path'],rec(r['path'])==r)
 check('output_tree_stable',{p.name for p in O.iterdir()}==names and not list((O/'tmp').iterdir()))
 result=dict(status='FORMAL_P1_T0_POST_TRAINING_FREEZE_AUDIT_PASS',fold='D',variant='T0',request_sha256=Q,checks_passed=len(checks),checks=checks,checkpoint=records[str(O/'ckpt-last.pth')],counts=dict(updates=3900,traversals=100,case_exposures=31200,drop_events=300,metric_records=3900,resource_records=3902),initialization=dict(record=initial,construction_reference=q['initialization_reference'],persistent_state_matches_GPU_replay=True,shared_initialization_metadata_matches=True,parameter_only_fingerprint_recomputed=False),optimizer=dict(defaults=defaults,parameter_group_count=len(groups),groups_match_frozen_T0=True),order=dict(raw_frozen_sha256=q['order_plan']['sha256'],canonical_sha256=order_hash,all_actual_batches_verified=True),resources=dict(max_RSS=max(r['RSS'] for r in resources),peak_allocated=max(r['peak_allocated'] for r in resources),peak_reserved=max(r['peak_reserved'] for r in resources),max_device_MiB=max(r['device_MiB'] for r in resources),elapsed_seconds=resources[-1]['elapsed_seconds']),files=baseline,hashed_bytes=total,audit_seconds=time.monotonic()-start,server_writes=0,new_forward_calls=0,new_backward_calls=0,checkpoint_deserialized=False,point_payloads_read=0,limitations=['Opaque checkpoint bytes hashed; checkpoint tensors/optimizer states not deserialized','Complete initial persistent-state fingerprint matched to frozen replay; parameter-only fingerprint recorded but not independently reconstructed','Counts supported by frozen runtime and complete saved logs, not model recomputation','No new full dependency inventory; active implementation/metadata bindings verified','Resource monitoring is not continuous hard RSS isolation','Training loss is not development performance; M0 and evaluation not authorized'])
except Exception as e:
 result=dict(status='AUDIT_FAILED_STOP_NO_RETRY',checks=checks,error=repr(e),hashed_bytes=total,audit_seconds=time.monotonic()-start,server_writes=0,new_forward_calls=0,new_backward_calls=0,checkpoint_deserialized=False)
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='FORMAL_P1_T0_POST_TRAINING_FREEZE_AUDIT_PASS' else 1)
