PARENT_RECORDS=[{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/completion.json', 'bytes': 559, 'sha256': 'f8b69958f62855b5350f8a52f6a6a29dd84a3c1072d23bcc66c5a7f51e5dcf86'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/exposure.json', 'bytes': 19465, 'sha256': '1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/initialization.json', 'bytes': 289, 'sha256': 'e8315461977374d067343282e03757c1bc7c6fcf6edc60256af8376c46fd6b07'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/metrics.jsonl', 'bytes': 2567135, 'sha256': '8c93a7dfa98ca64a237d5f9f56e3c810e89e1dc007d12c5354365d29306a2e12'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/optimizer_actual_defaults.json', 'bytes': 223, 'sha256': '9d63cc1e4fb32d46c348688146a9e8b10356a7bc3e8c1eabb9c483bac7c6e592'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/order_plan.json', 'bytes': 1248506, 'sha256': '6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d'}]
PARENT_REQUEST={'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_v3/training_execution_request_v1.json', 'bytes': 5431, 'sha256': '5cf2b4f93eb903c77702e9b493a8e8dd2700ceda448d77ea518ecc4c76e9ee0c'}
LOCAL_PAIRED_PAYLOAD_EVIDENCE={'path': 'E:\\Codex\\2026-06-06\\mamba-ccf-c-1-high-resolution\\outputs\\cranial_bcsp_geov1_20261024\\foldC_16384_training_v1\\paired315_data_verification_v1.json', 'sha256': '259c4594d6da18eb4b66901ceb9e34f8a32f16968fe36c64605417e282aa1ebd', 'paired_cases': 315, 'all_targets_byte_identical': True, 'all8192_inputs_are_16384_prefixes': True}
"""Read-only stdlib audit of this one finished training attempt; no model imports."""
import os,socket,json,hashlib,stat,time,math,subprocess
from pathlib import Path
from collections import Counter
START=time.monotonic();TOTAL=0;cache={};checks={};rows=[]
ROOT=Path('/home/jovyan/adapointr_work/PoinTr')
CODE=ROOT/'third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
CONTROL=CODE/'control_train_foldC_16384_v2'
OUT=ROOT/'logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v2'
SCOPE='7221de1a48d700f3e2b90e3904689c9e63239832203356785e8cd0f2278de2fd'

def need(ok,message):
 if not ok:raise ValueError(message)
def check(name,ok):
 checks[name]=bool(ok);need(ok,name)
def stamp(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns)
def parents(p):
 for a in p.parents:need(stat.S_ISDIR(a.lstat().st_mode),'linked/non-directory parent: '+str(a))
def read(p,binding=None,checkpoint=False):
 global TOTAL
 p=Path(p)
 if str(p) in cache:
  value=cache[str(p)]
  if binding:need(value[0]['bytes']==binding['bytes'] and value[0]['sha256']==binding['sha256'],'cached binding mismatch: '+str(p))
  return value
 parents(p);st=p.lstat();need(stat.S_ISREG(st.st_mode),'nonregular: '+str(p))
 limit=402653184 if checkpoint else 16777216
 need(st.st_size<=limit and TOTAL+st.st_size<=536870912,'read byte budget: '+str(p))
 digest=hashlib.sha256();parts=[]
 with p.open('rb') as f:
  while True:
   data=f.read(1048576)
   if not data:break
   TOTAL+=len(data);need(TOTAL<=536870912 and time.monotonic()-START<90,'audit byte/time budget')
   digest.update(data)
   if not checkpoint:parts.append(data)
 need(stamp(st)==stamp(p.lstat()),'file changed while hashing: '+str(p))
 row=dict(path=str(p),bytes=st.st_size,sha256=digest.hexdigest(),uid=st.st_uid,mode=oct(stat.S_IMODE(st.st_mode)),mtime_ns=st.st_mtime_ns,inode=st.st_ino)
 if binding:need(row['bytes']==binding['bytes'] and row['sha256']==binding['sha256'],'binding mismatch: '+str(p))
 rows.append(row);value=(row,b''.join(parts) if not checkpoint else None)
 cache[str(p)]=value;return value
def js(p,binding=None):return json.loads(read(p,binding)[1])
def canonical(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def tree():
 found={}
 for p in [OUT,*OUT.rglob('*')]:
  need(len(found)<32,'inventory entry cap');s=p.lstat()
  need(stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode),'linked/special output: '+str(p))
  found[str(p)]=stamp(s)
 return found
try:
 check('current_hostname_uid',socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000)
 parents(OUT);before=tree()
 names={'ckpt-last.pth','completion.json','exit_code.txt','exposure.json','initialization.json','launch.log','metrics.jsonl','optimizer_actual_defaults.json','order_plan.json','resources.jsonl','worker.pid'}
 check('exact_output_file_set',{p.name for p in OUT.iterdir() if p.is_file()}==names)
 check('exact_output_directory_set',{p.name for p in OUT.iterdir() if p.is_dir()}=={'tmp'} and not list((OUT/'tmp').iterdir()))
 for name in sorted(names):read(OUT/name,checkpoint=name=='ckpt-last.pth')
 scope=js(CONTROL/'training_execution_scope_v1.json')
 check('full_authorized_execution_scope_hash',cache[str(CONTROL/'training_execution_scope_v1.json')][0]['sha256']==SCOPE)
 check('exact_control_file_set',{p.name for p in CONTROL.iterdir()}=={'training_execution_scope_v1.json','migration_uncertainty_acceptance_v1.json','training_execution_request_v1.json','training_authorization_v1.json','training_runtime_v1.json','train_once_v1.sh','launch_attempt_v1.json'})
 for name in ['migration_uncertainty_acceptance_v1.json','training_execution_request_v1.json','training_authorization_v1.json','training_runtime_v1.json','train_once_v1.sh','launch_attempt_v1.json']:read(CONTROL/name)
 for r in EXPECTED_CONTROL:read(r['path'],r)
 check('seven_control_hashes_match_launch_materialization',len(EXPECTED_CONTROL)==7)
 q=js(CONTROL/'training_execution_request_v1.json');qhash=cache[str(CONTROL/'training_execution_request_v1.json')][0]['sha256']
 check('inner_request_hash',qhash==scope['entry_request']['sha256'])
 auth=js(CONTROL/'training_authorization_v1.json');runtime=js(CONTROL/'training_runtime_v1.json')
 check('one_way_authorization_runtime',auth['explicit_user_authorization'] is True and auth['request_sha256']==qhash and SCOPE in auth['user_authorization_text'] and runtime==dict(schema='bcsp-training-runtime-v1',request_sha256=qhash,authorization_sha256=cache[str(CONTROL/'training_authorization_v1.json')][0]['sha256']))
 check('single_attempt_claim',js(CONTROL/'launch_attempt_v1.json')['request_sha256']==qhash)
 pins=[q['static_config'],q['order_plan'],q['QC']['fold_binding'],q['QC']['manifests']['16384'],q['resource_rebind'],*q['implementation'].values()]
 for r in pins:read(r['path'],r)
 static=js(q['static_config']['path']);plan=js(OUT/'order_plan.json');complete=js(OUT/'completion.json');exposure=js(OUT/'exposure.json')
 check('exit_code_zero',read(OUT/'exit_code.txt')[1].strip()==b'0')
 tm=subprocess.run(['/usr/bin/tmux','has-session','-t',scope['future_paths']['tmux_session']],capture_output=True,timeout=5)
 check('fixed_tmux_absent',tm.returncode==1)
 pid=int(read(OUT/'worker.pid')[1]);check('worker_not_live',not Path('/proc/'+str(pid)).exists())
 check('frozen_order_bytes',read(OUT/'order_plan.json')[0]['sha256']==q['order_plan']['sha256'])
 order_hash=canonical(plan)
 check('order_canonical_binding',complete['order_sha256']==exposure['order_sha256']==js(OUT/'initialization.json')['order_sha256']==order_hash)
 check('completion_exact_counts',complete['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100))
 check('completion_update_traversal_exposure',complete['optimizer_updates']==3900 and complete['traversals']==100 and complete['case_exposures']==31200)
 check('BNCal_evaluation_resume_false',all(complete[k] is False for k in ['bncal_executed','evaluation_executed','resume']))
 checkpoint=read(OUT/'ckpt-last.pth',checkpoint=True)[0]
 check('checkpoint_SHA256_matches_completion',checkpoint['sha256']==complete['checkpoint_sha256'])
 fold=js(q['QC']['fold_binding']['path'])['folds']['C']
 manifest={x['case_id']:x for x in map(json.loads,read(q['QC']['manifests']['16384']['path'])[1].decode().splitlines())}
 check('fixed315_train_allowlist',len(fold['train_case_ids'])==315 and plan['case_ids']==fold['train_case_ids'] and len(fold['train_sources'])==63 and not set(fold['train_sources'])&set(fold['dev_sources']))
 metrics=list(map(json.loads,read(OUT/'metrics.jsonl')[1].decode().splitlines()))
 check('3900_metric_records',len(metrics)==3900)
 case=Counter();source=Counter();drops=Counter();index=0;losses=[]
 for e,row in enumerate(plan['epochs']):
  need(row['epoch']==e and len(row['batches'])==39 and len(row['dropped'])==3,'order dimensions')
  for b,batch in enumerate(row['batches']):
   m=metrics[index];index+=1
   need(m['step']==index and m['epoch']==e and m['batch']==b and m['case_ids']==batch and len(batch)==8,'actual step/epoch/batch/order')
   ss=[manifest[c]['source_id'] for c in batch]
   need(m['source_ids']==ss and set(batch)<=set(fold['train_case_ids']),'actual sources/allowlist')
   need(m['optimizer_step_committed'] is True and m['clip_max_norm']==10,'commit/clip')
   need(all(math.isfinite(m[k]) for k in ['loss','loss_sparse','loss_dense','grad_norm_before_clip']),'finite numeric event')
   need(math.isclose(m['loss'],m['loss_sparse']+m['loss_dense'],rel_tol=1e-6,abs_tol=1e-7),'loss sum')
   need(len(m['LR'])==2 and all(math.isclose(v,.0001*max(.9**(e/21),.02),rel_tol=1e-12) for v in m['LR']),'LR schedule')
   need(math.isclose(m['BN_momentum'],max(.9*.5**(e/21),.01),rel_tol=1e-12),'BN momentum')
   case.update(batch);source.update(ss);losses.append(m['loss'])
  drops.update(row['dropped'])
 check('full_actual_order_numeric_LR_BN_contract',index==3900)
 check('exposure_counters_match',dict(case)==exposure['case'] and dict(source)==exposure['source'] and dict(drops)==exposure['dropped_case'])
 check('31200_exposures_300_drops',sum(case.values())==sum(source.values())==31200 and sum(drops.values())==300)
 resources=list(map(json.loads,read(OUT/'resources.jsonl')[1].decode().splitlines()))
 check('3902_resource_records',len(resources)==3902)
 for i,r in enumerate(resources):
  need((r['phase'],r['committed_step'])==(('after_step',i+1) if i<3900 else ('before_final' if i==3900 else 'after_final',3900)),'resource sequence')
  need(r['limits']==static['resources'] and r['resource_guard_passed'] is True and not r['failed_checks'] and set(r['checks'])=={'allocated_within_limit','reserved_within_limit','device_within_limit'} and all(r['checks'].values()),'resource verdict')
  need(r['peak_allocated']<=21474836480 and r['peak_reserved']<=21474836480 and r['device_MiB']<=22528 and r['RSS']<=8589934592 and r['output_bytes']<=2147483648 and r['elapsed_seconds']<=86400,'resource ceilings')
  need(r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE' and r['own_PID']==pid,'PID diagnostic contract')
 check('all_recorded_resources_pass',True)

 import ast
 parent_files={}
 for record in PARENT_RECORDS:
  parent_files[Path(record['path']).name]=read(record['path'],record)
 p8=js(PARENT_REQUEST['path'],PARENT_REQUEST)
 def parent_json(name):return json.loads(parent_files[name][1])
 pair_checks={}
 def paircheck(name,ok):
  pair_checks[name]=bool(ok);check('paired_'+name,ok)
 paircheck('arms16k_vs8k_target8192',q['n_input']==16384 and p8['n_input']==8192 and static['model']['num_points']==8192)
 paircheck('same_static_order_identity_model_runtime_backend',all(q[k]==p8[k] for k in ['static_config','order_plan','identity','model_root','preflight_scope','preflight_request_sha256']) and all(q['implementation'][k]==p8['implementation'][k] for k in ['runtime','preflight_helper']))
 paircheck('same_source_fold_and_manifest_bindings',q['fold']==p8['fold']=='C' and all(q['QC'][k]==p8['QC'][k] for k in ['verification','manifests','fold_binding']))
 initial=js(OUT/'initialization.json')
 paircheck('same_initial_parameters_persistent_state_seed_order',initial==parent_json('initialization.json')==scope['paired_8k_parent']['expected_same_initialization'])
 paircheck('same_exact_order_and_exposure_counters',plan==parent_json('order_plan.json') and exposure==parent_json('exposure.json'))
 m8=list(map(json.loads,parent_files['metrics.jsonl'][1].decode().splitlines()))
 paircheck('same_actual3900_batches_case_source_order',len(m8)==len(metrics)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids']) for a,b in zip(m8,metrics)))
 paircheck('same_recorded_optimizer_defaults',js(OUT/'optimizer_actual_defaults.json')==parent_json('optimizer_actual_defaults.json'))
 paircheck('same_full_counts_and_no_BNCal_eval_resume',complete['counts']==parent_json('completion.json')['counts'] and all(parent_json('completion.json')[k] is False for k in ['bncal_executed','evaluation_executed','resume']))
 r8=p8['QC']['manifests']['8192'];other={x['case_id']:x for x in map(json.loads,read(r8['path'],r8)[1].decode().splitlines())}
 paircheck('same315_target_provenance_normalization',all(all(manifest[c][k]==other[c][k] for k in ['source_id','target_array_sha256','normalization','normalization_source','raw']) and manifest[c]['n_input']==16384 and other[c]['n_input']==8192 and manifest[c]['n_target']==other[c]['n_target']==8192 for c in fold['train_case_ids']))
 old_entry=read(p8['implementation']['entry']['path'],p8['implementation']['entry'])[1].decode()
 new_entry=read(q['implementation']['entry']['path'],q['implementation']['entry'])[1].decode()
 old_entry=old_entry.replace(Path(p8['implementation']['contract']['path']).name,Path(q['implementation']['contract']['path']).name).replace(p8['implementation']['contract']['sha256'],q['implementation']['contract']['sha256'])
 paircheck('entry_AST_same_except_contract_origin_pin',ast.dump(ast.parse(old_entry))==ast.dump(ast.parse(new_entry)))
 old_contract=read(p8['implementation']['contract']['path'],p8['implementation']['contract'])[1].decode()
 new_contract=read(q['implementation']['contract']['path'],q['implementation']['contract'])[1].decode()
 old_contract=old_contract.replace("require(q['fold'] == 'C' and q['n_input'] == 8192, 'first rebound run only')","require(q['fold'] == 'C' and q['n_input'] == 16384, 'Fold C 16k arm only')")
 paircheck('contract_AST_same_except_dedicated_arm_gate',ast.dump(ast.parse(old_contract))==ast.dump(ast.parse(new_contract)))

 check('result_tree_stable_atime_excluded',tree()==before)
 check('no_failure_markers',not (OUT/'failure.json').exists() and not (OUT/'startup_failure.json').exists())
 print(json.dumps(dict(status='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS',checks=checks,completion=complete,checkpoint=checkpoint,output_manifest=[r for r in rows if str(OUT)+'/' in r['path']],all_bound_files=rows,
 counts=dict(metric_records=len(metrics),epochs=100,updates=3900,case_exposures=sum(case.values()),dropped_exposures=sum(drops.values()),resource_records=len(resources)),
 resource_summary=dict(peak_allocated=max(r['peak_allocated'] for r in resources),peak_reserved=max(r['peak_reserved'] for r in resources),device_peak_MiB=max(r['device_MiB'] for r in resources),RSS_peak=max(r['RSS'] for r in resources),PID_warning_records=sum(bool(r['PID_warning']) for r in resources)),
 loss_summary=dict(first=losses[0],last=losses[-1],last_epoch_mean=sum(losses[-39:])/39,interpretation='Training loss only;not development or clinical performance'),
 paired_consistency=pair_checks,paired_payload_evidence=LOCAL_PAIRED_PAYLOAD_EVIDENCE,exact_source_runtime_binding_verified=True,checkpoint_loaded=False,model_imported=False,forward_calls=0,server_writes=0,hashed_bytes=TOTAL,elapsed_seconds=time.monotonic()-START,
 limitations=['Forward/backward/scheduler counters are corroborated by pinned runtime and completion; no independent GPU trace','No strict GPU process ownership guarantee by approved policy','BNCal/evaluation false is supported by pinned execution path and completion flags; no independent OS-wide file-access trace'])),flush=True)
except BaseException as exc:
 print(json.dumps(dict(status='AUDIT_FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks,all_bound_files=rows,server_writes=0,checkpoint_loaded=False,forward_calls=0)),flush=True)
 raise
