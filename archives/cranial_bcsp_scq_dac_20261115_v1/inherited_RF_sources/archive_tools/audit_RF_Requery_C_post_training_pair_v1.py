"""Readonly trained RF S-ref_C freeze; hashes checkpoint bytes without deserializing/loading it."""
from pathlib import Path
from collections import Counter
import ast,json,hashlib,subprocess,base64,zlib,shlex,math
R=Path(__file__).resolve().parent.parent;B=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1';H=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1';D=H/'post_training_freeze_v1';A=H/'authorized_execution_v1'
Q=H/'pending_transport_v1/payload/SCQ_RF_Requery_C_training_execution_request_v1.json';RH='27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def emit(n,j):
 with (D/n).open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)
def call(label,args,seconds=60):
 x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000',*args],capture_output=True,timeout=seconds+15)
 for n,b in [('stdout',x.stdout),('stderr',x.stderr)]:
  with (D/(label+'_'+n+'.bin')).open('xb') as f:f.write(b)
 assert x.returncode==0,(label,x.stdout.decode(errors='replace')[-1200:]);return x.stdout
def remote(label,code,values):
 class Bind(ast.NodeTransformer):
  def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
 code=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(code))));ast.parse(code,feature_version=(3,8));blob=base64.b64encode(zlib.compress(code.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import zlib,base64;exec(zlib.decompress(base64.b64decode('+repr(blob)+')))']);assert len(cmd.encode())<=2048
 return json.loads(call(label,['exec','--timeout','60','--',cmd]))
checks={}
def check(n,v):
 checks[n]=bool(v);assert v,n
try:
 D.mkdir()
 assert sha(Q)==RH;q=read(Q);mp=read(H/'pending_transport_v1/installation_mapping_v1.json');L=q['launch_contract'];C=mp['remote_root']
 code="""from pathlib import Path
import socket,os,subprocess,json,hashlib
assert socket.gethostname()==HOST and os.getuid()==1000
out=Path(OUT);root=Path(ROOT)
assert (out/'exit_code.txt').read_text().strip()=='0'
assert subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==1
pid=int((out/'worker.pid').read_text());proc=Path('/proc/'+str(pid));assert not proc.exists() or ENTRY.encode() not in (proc/'cmdline').read_bytes()
files={};dirs=[];total=0
for label,p in [('output',out),('install',root)]:
 assert not any(x.is_symlink() for x in (p,*p.parents))
 for f in sorted(p.rglob('*')):
  assert not f.is_symlink();name=label+'/'+str(f.relative_to(p))
  if f.is_dir():dirs.append(name);continue
  n=f.stat().st_size;total+=n;assert n<=1073741824 and total<=2147483648 and len(files)<80
  before=f.stat();h=hashlib.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(4194304),b''):h.update(b)
  after=f.stat();assert (before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns)
  files[name]=dict(bytes=n,sha256=h.hexdigest())
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),exit_code=0,worker_not_live=True,tmux_absent=True,files=files,directories=dirs,hashed_bytes=total)))
"""
 values=dict(HOST=q['identity']['hostname'],OUT=q['output'],ROOT=C,SESSION=L['tmux_session'],ENTRY=q['implementation']['entry']['path'])
 inv=remote('inventory_before',code,values);emit('remote_inventory_before_v2.json',inv)
 names={'launch.log','worker.pid','resources.jsonl','order_plan.json','model_construction.json','run_identity.json','SCQ_geometry.jsonl','exposure.json','payload_manifest.json','initialization.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','metrics.jsonl','ckpt-last.pth','completion.json','exit_code.txt'}
 check('exact16output_files',set(n for n in inv['files'] if n.startswith('output/'))=={'output/'+n for n in names})
 expected_install={'install/'+Path(r['target']).name for r in mp['files']}|{'install/control/'+n for n in ['authorization_v1.json','runtime_v1.json','launch_once_v1.sh','attempt_claim_v1.json']}
 check('exact13installed_files',set(n for n in inv['files'] if n.startswith('install/'))==expected_install)
 check('exactdirectories',set(inv['directories'])=={'output/tmp','install/control'})
 for r in mp['files']:assert inv['files']['install/'+Path(r['target']).name]=={k:r[k] for k in ['bytes','sha256']}
 for n in ['authorization_v1.json','runtime_v1.json','launch_once_v1.sh']:assert inv['files']['install/control/'+n]==dict(bytes=(A/n).stat().st_size,sha256=sha(A/n))
 check('all9payload_and3current_controls_match',True)
 for n in sorted(names-{'ckpt-last.pth'}):
  target=D/'output'/n;target.parent.mkdir(exist_ok=True);call('get_'+n.replace('.','_'),['get',q['output']+'/'+n,'/mnt/e/'+target.as_posix()[3:],'--timeout','60'])
  assert inv['files']['output/'+n]==dict(bytes=target.stat().st_size,sha256=sha(target))
 for n in ['authorization_v1.json','runtime_v1.json','launch_once_v1.sh','attempt_claim_v1.json']:
  target=D/'control'/n;target.parent.mkdir(exist_ok=True);call('get_'+n.replace('.','_'),['get',C+'/control/'+n,'/mnt/e/'+target.as_posix()[3:],'--timeout','60'])
  assert inv['files']['install/control/'+n]==dict(bytes=target.stat().st_size,sha256=sha(target))
 print('19 noncheckpoint readbacks hash matched; checkpoint streamed remotely',flush=True)
 after=remote('inventory_after',code,values);emit('remote_inventory_after_v2.json',after)
 check('before_after_all29file_hashes_stable',inv==after)
 out=D/'output';readout=lambda n:read(out/n);lines=lambda n:[json.loads(s) for s in (out/n).read_text().splitlines()]
 auth=read(D/'control/authorization_v1.json');rt=read(D/'control/runtime_v1.json');claim=read(D/'control/attempt_claim_v1.json')
 check('oneway_authorization_and_singleclaim',auth['request_sha256']==RH and auth['explicit_user_authorization'] and set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and rt==dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=RH,authorization_sha256=sha(D/'control/authorization_v1.json')) and claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=RH))
 comp=readout('completion.json');init=readout('initialization.json');model=readout('model_construction.json');identity=readout('run_identity.json')
 counts=dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100)
 check('completion_counts_exact',comp['counts']==counts and comp['optimizer_updates']==3900 and comp['traversals']==100 and comp['case_exposures']==31200)
 checkpoint=inv['files']['output/ckpt-last.pth'];check('checkpoint_fresh_SHA_matches',checkpoint['sha256']==comp['checkpoint_sha256'] and checkpoint['bytes']>0)
 check('no_BNCal_eval_resume',comp['bncal_executed'] is comp['evaluation_executed'] is comp['resume'] is False)
 manifest=readout('payload_manifest.json')['files'];check('exact12member_payload_manifest',len(manifest)==12 and {r['name'] for r in manifest}==names-{'payload_manifest.json','exit_code.txt','worker.pid','launch.log'} and all(inv['files']['output/'+r['name']]=={k:r[k] for k in ['bytes','sha256']} for r in manifest))
 plan=readout('order_plan.json');canonical=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 check('raw_andcanonical_order_bindings',sha(out/'order_plan.json')==q['order_plan']['sha256'] and init['order_sha256']==comp['order_sha256']==canonical)
 foldpath=B/'candidate_payload/fold_binding.json';mf=B/'candidate_payload/manifest_8192.jsonl';check('frozen_metadata_identity',sha(foldpath)==q['QC']['fold_binding']['sha256'] and sha(mf)==q['QC']['manifests']['8192']['sha256'])
 fold=read(foldpath)['folds']['C'];byid={r['case_id']:r for r in [json.loads(s) for s in mf.read_text().splitlines()]};source={c:r['source_id'] for c,r in byid.items()}
 check('315case63source21dev',plan['case_ids']==fold['train_case_ids'] and len(set(plan['case_ids']))==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21 and not set(fold['train_sources'])&set(fold['dev_sources']))
 metrics=lines('metrics.jsonl');geo=lines('SCQ_geometry.jsonl');check('3900metrics_geometry',len(metrics)==len(geo)==3900)
 cases=Counter();sources=Counter();drops=Counter()
 for epoch,row in enumerate(plan['epochs']):
  assert row['epoch']==epoch and len(row['batches'])==39 and len(row['dropped'])==3
  full=sum(row['batches'],[])+row['dropped'];assert len(full)==len(set(full))==315 and set(full)==set(plan['case_ids']);drops.update(row['dropped'])
 for i,(m,g) in enumerate(zip(metrics,geo)):
  epoch,batch=divmod(i,39);ids=plan['epochs'][epoch]['batches'][batch]
  assert (m['step'],m['epoch'],m['batch'])==(i+1,epoch,batch) and m['case_ids']==ids and m['source_ids']==[source[c] for c in ids] and m['optimizer_step_committed'] is True
  assert all(math.isfinite(m[k]) for k in ['loss','loss_sparse','loss_dense','loss_reconstruction','loss_denoise','grad_norm_before_clip']) and m['grad_norm_before_clip']>=0 and m['clip_max_norm']==10
  assert m['loss_sparse']==m['loss_denoise']==0 and m['loss']==m['loss_dense']==m['loss_reconstruction']
  assert len(m['LR'])==2 and all(math.isclose(x,1e-4*max(.9**(epoch/21),.02),rel_tol=1e-12) for x in m['LR']) and math.isclose(m['BN_momentum'],max(.9*.5**(epoch/21),.01),rel_tol=1e-12)
  assert (g['step'],g['epoch'],g['batch'])==(i+1,epoch,batch) and g['case_ids']==ids and g['frame']=='D-only normalized'
  parts=g['geometry'];assert set(parts)=={'coarse','dense','Q0','Q1','Q2','delta','delta0','delta1','N0_N1_equal','neighbor_set_overlap'} and type(parts['N0_N1_equal']) is bool
  assert len(parts['neighbor_set_overlap'])==8 and all(math.isfinite(x) and 0<=x<=1 for x in parts['neighbor_set_overlap'])
  if parts['N0_N1_equal']:assert parts['neighbor_set_overlap']==[1.]*8
  for name in ['coarse','dense']:
   p=parts[name];assert all(len(p[k])==8 for k in ['centroid','radius','minimum','maximum'])
   for center,radius,lo,hi in zip(p['centroid'],p['radius'],p['minimum'],p['maximum']):
    assert len(center)==len(lo)==len(hi)==3 and all(math.isfinite(x) for x in center+lo+hi+[radius]) and radius>=0
    assert all(a<=b and a-1e-5<=c<=b+1e-5 for a,b,c in zip(lo,hi,center))
  for name in ['Q0','Q1','Q2']:
   t=parts[name];assert set(t)=={'centroid','radius'} and len(t['centroid'])==len(t['radius'])==8
   assert all(len(c)==3 and all(math.isfinite(x) for x in c) for c in t['centroid']) and all(math.isfinite(x) and x>=0 for x in t['radius'])
  assert parts['Q2']=={k:parts['coarse'][k] for k in ['centroid','radius']}
  for dname,rawname,usedname in [('delta','Q0','Q2'),('delta0','Q0','Q1'),('delta1','Q1','Q2')]:
   delta=parts[dname];assert set(delta)=={'mean_norm','max_norm','centroid'} and all(len(delta[k])==8 for k in delta)
   for rawc,usedc,dc,mean_norm,max_norm in zip(parts[rawname]['centroid'],parts[usedname]['centroid'],delta['centroid'],delta['mean_norm'],delta['max_norm']):
    assert len(dc)==3 and all(math.isfinite(x) for x in dc+[mean_norm,max_norm]) and 0<=mean_norm<=max_norm+1e-6
    assert math.sqrt(sum(x*x for x in dc))<=mean_norm+1e-5 and all(math.isclose(u-r,d,rel_tol=2e-4,abs_tol=2e-6) for u,r,d in zip(usedc,rawc,dc))
  for d,d0,d1 in zip(parts['delta']['centroid'],parts['delta0']['centroid'],parts['delta1']['centroid']):
   assert all(math.isclose(x,y+z,rel_tol=2e-4,abs_tol=2e-6) for x,y,z in zip(d,d0,d1))
  assert all(t<=a+b+1e-5 for t,a,b in zip(parts['delta']['mean_norm'],parts['delta0']['mean_norm'],parts['delta1']['mean_norm']))
  if i==0:assert parts['Q1']==parts['Q2'] and parts['delta1']['max_norm']==[0.]*8
  ls=g['loss_components'];assert set(ls)=={'coarse_CD','dense_CD'} and all(math.isfinite(x) and x>=0 for x in ls.values()) and g['reconstruction_sum']==ls['coarse_CD']+ls['dense_CD'] and math.isclose(g['reconstruction_sum'],m['loss'],rel_tol=2e-7,abs_tol=1e-7)
  cases.update(ids);sources.update(m['source_ids'])
 check('all3900_batches_LR_BN_losses_RF_stages_and_measured_Requery_neighbors',True)
 exp=readout('exposure.json');check('exposure_recomputed',dict(cases)==exp['case'] and dict(sources)==exp['source'] and dict(drops)==exp['dropped_case'] and exp['order_sha256']==canonical and sum(cases.values())==31200 and sum(drops.values())==300 and all(cases[c]+drops[c]==100 for c in plan['case_ids']))
 mirror={k:Path(v) for k,v in read(H/'final_local_mirror_v1.json').items()}
 nr=q['admission']['construction'];np=mirror[nr['path']];assert sha(np)==nr['sha256'] and np.stat().st_size==nr['bytes']
 native=read(np);common=native['models'][0]['shared_initial_state_SHA256']
 check('formal_RF_admission_source_exact',common=='b7e5b640c1f0e709ab6697139db1267584266a51b4e0e29f2d5217bfd1236cc5' and native['models'][0]['phase']=='S_ref_eval1')
 check('native_common_initialization_matches',model['common_initial_state_SHA256']==common and model['factory']['parent']['parent']['artificial_fixture'] is False and model['factory']['parent']['scq']['variant']=='S' and model['factory']['rf']['variant']=='RF-Requery' and model['factory']['rf']['additional_parameters']==231171 and model['factory']['rf']['total_parameters']==40827847 and model['factory']['rf']['initialization_sha256']==q['rf_initialization']['sha256'])
 check('both_frozen_head_initializers',model['factory']['parent']['scq']['initialization_sha256']==q['initialization']['sha256'] and model['factory']['rf']['common_state_preserved'] and model['factory']['rf']['CPU_RNG_preserved'])
 expected_new={'base_model.scq.W1.weight':.0005,'base_model.scq.W2.weight':.0005,'base_model.scq.W1.bias':0.,'base_model.scq.W2.bias':0.,'base_model.rf.V1.weight':.0005,'base_model.rf.V2.weight':.0005,'base_model.rf.V1.bias':0.,'base_model.rf.V2.bias':0.}
 check('all8_SCQ_RF_parameter_groups',model['new_optimizer_groups']==expected_new)
 groups=readout('optimizer_parameter_groups.json');defaults=readout('optimizer_actual_defaults.json');check('unique419parameters_total',len(groups)==len({r['name'] for r in groups})==419 and sum(math.prod(r['shape']) for r in groups)==40827847 and len([r for r in groups if r['name'].startswith('base_model.rf.')])==4)
 for r in groups:assert r['weight_decay']==(0 if r['name'].endswith(('.A_log','.D','.bias')) or len(r['shape'])==1 else .0005)
 check('SSM_andoptimizer_contract',all(sum(r['name'].endswith(s) and r['weight_decay']==0 for r in groups)==22 for s in ['.A_log','.D']) and defaults['lr']==.0001 and defaults['betas']==[.9,.999] and defaults['eps']==1e-8 and not defaults['amsgrad'] and not defaults['maximize'] and defaults['foreach'] is defaults['fused'] is None)
 check('runidentity',identity['variant']=='RF-Requery' and identity['fold']=='C' and identity['stage']==q['stage'] and identity['native_admission_sha256']==q['admission']['audit']['sha256'] and identity['arm']=='RF-Requery' and identity['legacy_stage_is_provenance_only'] is True and model['arm']=='RF-Requery' and model['stage']==q['stage'] and identity['SSM_gradient_non_bitwise_reproducibility_disclosed'])
 for k in ['parameter_sha256','persistent_state_sha256']:assert len(init[k])==64 and all(x in '0123456789abcdef' for x in init[k])
 check('initialization_record_valid_seed0',init['seed']==0)
 resources=lines('resources.jsonl');pair_path=mirror[q['pair_contract']['path']];assert sha(pair_path)==q['pair_contract']['sha256'];limits=read(pair_path)['resources'];check('3902resource_records',len(resources)==3902)
 prev=-1
 for i,r in enumerate(resources):
  phase,step=('after_step',i+1) if i<3900 else ('before_final' if i==3900 else 'after_final',3900)
  assert r['phase']==phase and r['committed_step']==step and r['limits']==limits and prev<=r['elapsed_seconds']<=limits['wall_seconds'];prev=r['elapsed_seconds']
  checkvals=dict(allocated_within_limit=r['peak_allocated']<=limits['torch_peak_bytes'],reserved_within_limit=r['peak_reserved']<=limits['torch_peak_bytes'],device_within_limit=r['device_MiB']<=limits['device_MiB'])
  assert r['checks']==checkvals and all(checkvals.values()) and r['resource_guard_passed'] and r['failed_checks']==[] and r['RSS']<=limits['RSS_bytes'] and r['output_bytes']<=limits['output_bytes'] and r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
 check('allresource_conditions_recomputed',True)
 pre=read(A/'train315_hashes.json');check('authorized315payloadprehash_pass',pre['status']=='TRAIN315_EXACT_HASHES_PASS' and pre['files']==315 and pre['sources']==63 and pre['array_reads']==0)
 ref=q['paired_baseline'];paths={k:mirror[r['path']] for k,r in ref.items()}
 for key,p in paths.items():assert sha(p)==ref[key]['sha256'] and p.stat().st_size==ref[key]['bytes']
 ba=read(paths['audit']);bm=read(paths['construction']);bq=read(paths['request']);bD=paths['construction'].parent
 check('formal_Sref_reference_hashes_and_counts',ba['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and ba['check_count']==26 and all(ba['checks'].values()) and ba['identity']==q['identity'] and ba['updates']==3900 and ba['exposures']==31200)
 check('paired_science_resource_data_order_identical',all(q[k]==bq[k] for k in ['science','identity','resources','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','admission']))
 check('paired_full_S_state_and_factory_preserved',model['common_initial_state_SHA256']==bm['common_initial_state_SHA256']==ba['common_initial_state_SHA256'] and model['factory']['parent']==bm['factory'])
 check('paired_order_exposure_optimizer_defaults_identical',all(sha(out/n)==sha(bD/n) for n in ['order_plan.json','exposure.json','optimizer_actual_defaults.json']))
 bmetrics=[json.loads(x) for x in (bD/'metrics.jsonl').read_text().splitlines()];bgroups=read(bD/'optimizer_parameter_groups.json')
 for name in ['metrics.jsonl','optimizer_parameter_groups.json']:assert sha(bD/name)==ba['artifacts']['output/'+name]['sha256']
 check('paired_all3900_actual_batches_and_schedules',len(bmetrics)==3900 and all(all(x[k]==y[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']) for x,y in zip(metrics,bmetrics)))
 check('paired_all_shared_optimizer_groups_exact',[r for r in groups if not r['name'].startswith('base_model.rf.')]==bgroups)
 check('same_frozen_shared_sources_except_entry_bridge',all(q['implementation'][k]==r for k,r in bq['implementation'].items() if k not in ('entry','bridge')))

 sr=q['paired_static'];sp={k:mirror[r['path']] for k,r in sr.items()}
 for key,p in sp.items():assert sha(p)==sr[key]['sha256'] and p.stat().st_size==sr[key]['bytes']
 sa=read(sp['audit']);sm=read(sp['construction']);sq=read(sp['request']);sD=sp['construction'].parent
 check('formal_Static_reference_hashes_and_counts',sa['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and sa['check_count']==34 and all(sa['checks'].values()) and sa['identity']==q['identity'] and (sa['updates'],sa['traversals'],sa['exposures'],sa['drops'])==(3900,100,31200,300))
 check('Static_same_Sref_frozen_reference',sa['paired_baseline_audit_sha256']==sha(paths['audit']))
 check('Static_science_resources_data_both_initializers_identical',all(q[k]==sq[k] for k in ['science','identity','resources','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','rf_initialization','admission']))
 check('exact_full_Static_initial_parameters_and_buffers',init==read(sp['initialization'])==sa['initialization']==q['expected_full_initialization'])
 check('Static_same_full_common_S_initial_state',model['common_initial_state_SHA256']==sm['common_initial_state_SHA256']==sa['common_initial_state_SHA256']==common and model['factory']['parent']==sm['factory']['parent'])
 rf_evidence=model['factory']['rf'];static_rf=sm['factory']['rf']
 check('same_RF_factory_contract_except_arm',set(rf_evidence)==set(static_rf) and all(rf_evidence[k]==static_rf[k] for k in rf_evidence if k!='variant') and static_rf['variant']=='RF-Static')
 for name in ['order_plan.json','exposure.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','metrics.jsonl']:
  assert sha(sD/name)==sa['artifacts']['output/'+name]['sha256']
 check('Static_identical_order_exposure_defaults_all419groups',all(sha(out/n)==sha(sD/n) for n in ['order_plan.json','exposure.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json']))
 static_metrics=[json.loads(x) for x in (sD/'metrics.jsonl').read_text().splitlines()]
 check('Static_all3900_actual_batches_and_schedules',len(static_metrics)==3900 and all(all(x[k]==y[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']) for x,y in zip(metrics,static_metrics)))
 check('Static_frozen_sources_identical_except_entry_bridge',all(q['implementation'][k]==r for k,r in sq['implementation'].items() if k not in ('entry','bridge')))
 delta_summary=dict(max_query_delta_norm=max(max(r['geometry']['delta']['max_norm']) for r in geo),mean_batch_delta_norm=sum(sum(r['geometry']['delta']['mean_norm']) for r in geo)/(3900*8),nonzero_delta_steps=sum(any(v>0 for v in r['geometry']['delta']['max_norm']) for r in geo),units='D-only normalized, descriptive logging only; no accuracy conclusion',RF_second_residual_mean=sum(sum(r['geometry']['delta1']['mean_norm']) for r in geo)/(3900*8),Requery_N0_N1_equal_steps=sum(r['geometry']['N0_N1_equal'] for r in geo),mean_neighbor_set_overlap=sum(sum(r['geometry']['neighbor_set_overlap']) for r in geo)/(3900*8),minimum_case_neighbor_set_overlap=min(min(r['geometry']['neighbor_set_overlap']) for r in geo))
 result=dict(status='FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',variant='RF-Requery',fold='C',identity=q['identity'],request_sha256=RH,updates=3900,traversals=100,exposures=31200,drops=300,order_sha256=canonical,checkpoint=checkpoint,initialization=init,common_initial_state_SHA256=common,checks=checks,check_count=len(checks),peaks={k:max(r[k] for r in resources) for k in ['RSS','peak_allocated','peak_reserved','device_MiB','elapsed_seconds']},counts=counts,arm='RF-Requery',paired_baseline_audit_sha256=sha(paths['audit']),paired_Static_audit_sha256=sha(sp['audit']),delta_summary=delta_summary,artifacts=inv['files'],BNCal=False,evaluation=False,resume=False,operations=dict(new_forward=0,new_backward=0,server_writes=0,checkpoint_loaded=False,checkpoint_downloaded=False),limitations=['Checkpoint streamed twice without deserialization; no posthoc model restoration forward.','Common initialization matches hash recorded by bound factory; audit does not independently reconstruct full tensors.','RSS/SMI sampled and original runtime free-disk guard lacks per-row disk telemetry; no PID namespace ownership claim.','No scientific efficacy inference from training loss.','Neighbor equality and overlap are recorded summaries, not independently recomputed KNN from full tensors in this read-only audit.'])
 emit('freeze_verification_v1.json',result);print(json.dumps(dict(status=result['status'],checks=len(checks),checkpoint=checkpoint,updates=3900,peaks=result['peaks'])))
except BaseException as exc:
 emit('audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),new_forward=0));raise
