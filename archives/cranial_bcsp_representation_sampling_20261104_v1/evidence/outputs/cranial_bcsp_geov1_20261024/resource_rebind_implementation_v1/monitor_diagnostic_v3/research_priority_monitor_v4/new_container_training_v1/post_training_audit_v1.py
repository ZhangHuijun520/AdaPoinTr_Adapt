"""Read-only stdlib audit of this one finished training attempt; no model imports."""
import os,socket,json,hashlib,stat,time,math,subprocess
from pathlib import Path
from collections import Counter
START=time.monotonic();TOTAL=0;cache={};checks={};rows=[]
ROOT=Path('/home/jovyan/adapointr_work/PoinTr')
CODE=ROOT/'third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
CONTROL=CODE/'control_train_v3'
OUT=ROOT/'logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3'
SCOPE='16655f4494fe2458619129958a370d240866a15b339ec2d40b595d827b675f0a'

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
 scope=js(CONTROL/'training_execution_scope_v3.json')
 check('full_authorized_execution_scope_hash',cache[str(CONTROL/'training_execution_scope_v3.json')][0]['sha256']==SCOPE)
 check('exact_control_file_set',{p.name for p in CONTROL.iterdir()}=={'training_execution_scope_v3.json','migration_uncertainty_acceptance_v1.json','training_execution_request_v1.json','training_authorization_v1.json','training_runtime_v1.json','train_once_v1.sh','launch_attempt_v1.json'})
 for name in ['migration_uncertainty_acceptance_v1.json','training_execution_request_v1.json','training_authorization_v1.json','training_runtime_v1.json','train_once_v1.sh','launch_attempt_v1.json']:read(CONTROL/name)
 for r in EXPECTED_CONTROL:read(r['path'],r)
 check('seven_control_hashes_match_launch_materialization',len(EXPECTED_CONTROL)==7)
 q=js(CONTROL/'training_execution_request_v1.json');qhash=cache[str(CONTROL/'training_execution_request_v1.json')][0]['sha256']
 check('inner_request_hash',qhash==scope['entry_request']['sha256'])
 auth=js(CONTROL/'training_authorization_v1.json');runtime=js(CONTROL/'training_runtime_v1.json')
 check('one_way_authorization_runtime',auth['explicit_user_authorization'] is True and auth['request_sha256']==qhash and SCOPE in auth['user_authorization_text'] and runtime==dict(schema='bcsp-training-runtime-v1',request_sha256=qhash,authorization_sha256=cache[str(CONTROL/'training_authorization_v1.json')][0]['sha256']))
 check('single_attempt_claim',js(CONTROL/'launch_attempt_v1.json')['request_sha256']==qhash)
 pins=[q['static_config'],q['order_plan'],q['QC']['fold_binding'],q['QC']['manifests']['8192'],q['resource_rebind'],*q['implementation'].values()]
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
 manifest={x['case_id']:x for x in map(json.loads,read(q['QC']['manifests']['8192']['path'])[1].decode().splitlines())}
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
 check('result_tree_stable_atime_excluded',tree()==before)
 check('no_failure_markers',not (OUT/'failure.json').exists() and not (OUT/'startup_failure.json').exists())
 print(json.dumps(dict(status='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS',checks=checks,completion=complete,checkpoint=checkpoint,output_manifest=[r for r in rows if str(OUT)+'/' in r['path']],all_bound_files=rows,
 counts=dict(metric_records=len(metrics),epochs=100,updates=3900,case_exposures=sum(case.values()),dropped_exposures=sum(drops.values()),resource_records=len(resources)),
 resource_summary=dict(peak_allocated=max(r['peak_allocated'] for r in resources),peak_reserved=max(r['peak_reserved'] for r in resources),device_peak_MiB=max(r['device_MiB'] for r in resources),RSS_peak=max(r['RSS'] for r in resources),PID_warning_records=sum(bool(r['PID_warning']) for r in resources)),
 loss_summary=dict(first=losses[0],last=losses[-1],last_epoch_mean=sum(losses[-39:])/39,interpretation='Training loss only;not development or clinical performance'),
 exact_source_runtime_binding_verified=True,checkpoint_loaded=False,model_imported=False,forward_calls=0,server_writes=0,hashed_bytes=TOTAL,elapsed_seconds=time.monotonic()-START,
 limitations=['Forward/backward/scheduler counters are corroborated by pinned runtime and completion; no independent GPU trace','No strict GPU process ownership guarantee by approved policy','BNCal/evaluation false is supported by pinned execution path and completion flags; no independent OS-wide file-access trace'])),flush=True)
except BaseException as exc:
 print(json.dumps(dict(status='AUDIT_FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks,all_bound_files=rows,server_writes=0,checkpoint_loaded=False,forward_calls=0)),flush=True)
 raise
