"""Readonly trained RF S-ref_C freeze; hashes checkpoint bytes without deserializing/loading it."""
from pathlib import Path
from collections import Counter
import ast,json,hashlib,subprocess,base64,zlib,shlex,math
R=Path(__file__).resolve().parent.parent;B=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1';H=R/'outputs/scq_rf_Static_D_implementation_20261115_v1/selector_diagnostic_hotfix_v2';D=H/'post_training_freeze_v1';A=H/'authorized_execution_v2'
Q=H/'pending_transport_v2/payload/SCQ_RF_Static_D_training_execution_request_v2.json';RH='9d7ac459e9a969c36df67ddaee4c5c0aaac2c68b322dcf58097c54f59caa402b'

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
 assert sha(Q)==RH;q=read(Q);mp=read(H/'pending_transport_v2/installation_mapping_v2.json');L=q['launch_contract'];C=mp['remote_root']
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
 values=dict(HOST='shu-common-25721452-notebook-qx2k0r-0',OUT=q['output'],ROOT=C,SESSION=L['tmux_session'],ENTRY=q['implementation']['entry']['path'])
 inv=remote('inventory_before',code,values);emit('remote_inventory_before_v2.json',inv)
 names={'launch.log','worker.pid','resources.jsonl','order_plan.json','model_construction.json','run_identity.json','SCQ_geometry.jsonl','exposure.json','payload_manifest.json','initialization.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','metrics.jsonl','ckpt-last.pth','completion.json','exit_code.txt'}
 check('exact16output_files',set(n for n in inv['files'] if n.startswith('output/'))=={'output/'+n for n in names})
 expected_install={'install/'+Path(r['target']).name for r in mp['files']}|{'install/control/'+n for n in ['authorization_v2.json','runtime_v2.json','launch_once_v2.sh','attempt_claim_v2.json']}
 check('exact12installed_files',set(n for n in inv['files'] if n.startswith('install/'))==expected_install)
 check('exactdirectories',set(inv['directories'])=={'output/tmp','install/control'})
 for r in mp['files']:assert inv['files']['install/'+Path(r['target']).name]=={k:r[k] for k in ['bytes','sha256']}
 for n in ['authorization_v2.json','runtime_v2.json','launch_once_v2.sh']:assert inv['files']['install/control/'+n]==dict(bytes=(A/n).stat().st_size,sha256=sha(A/n))
 check('all8payload_and3current_controls_match',True)
 for n in sorted(names-{'ckpt-last.pth'}):
  target=D/'output'/n;target.parent.mkdir(exist_ok=True);call('get_'+n.replace('.','_'),['get',q['output']+'/'+n,'/mnt/e/'+target.as_posix()[3:],'--timeout','60'])
  assert inv['files']['output/'+n]==dict(bytes=target.stat().st_size,sha256=sha(target))
 for n in ['authorization_v2.json','runtime_v2.json','launch_once_v2.sh','attempt_claim_v2.json']:
  target=D/'control'/n;target.parent.mkdir(exist_ok=True);call('get_'+n.replace('.','_'),['get',C+'/control/'+n,'/mnt/e/'+target.as_posix()[3:],'--timeout','60'])
  assert inv['files']['install/control/'+n]==dict(bytes=target.stat().st_size,sha256=sha(target))
 print('19 noncheckpoint readbacks hash matched; checkpoint streamed remotely',flush=True)
 after=remote('inventory_after',code,values);emit('remote_inventory_after_v2.json',after)
 check('before_after_all28file_hashes_stable',inv==after)
 out=D/'output';readout=lambda n:read(out/n);lines=lambda n:[json.loads(s) for s in (out/n).read_text().splitlines()]
 auth=read(D/'control/authorization_v2.json');rt=read(D/'control/runtime_v2.json');claim=read(D/'control/attempt_claim_v2.json')
 check('oneway_authorization_and_singleclaim',auth['request_sha256']==RH and auth['explicit_user_authorization'] and set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and rt==dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=RH,authorization_sha256=sha(D/'control/authorization_v2.json')) and claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=RH))
 comp=readout('completion.json');init=readout('initialization.json');model=readout('model_construction.json');identity=readout('run_identity.json')
 counts=dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100)
 check('completion_counts_exact',comp['counts']==counts and comp['optimizer_updates']==3900 and comp['traversals']==100 and comp['case_exposures']==31200)
 checkpoint=inv['files']['output/ckpt-last.pth'];check('checkpoint_fresh_SHA_matches',checkpoint['sha256']==comp['checkpoint_sha256'] and checkpoint['bytes']>0)
 check('no_BNCal_eval_resume',comp['bncal_executed'] is comp['evaluation_executed'] is comp['resume'] is False)
 manifest=readout('payload_manifest.json')['files'];check('exact12member_payload_manifest',len(manifest)==12 and {r['name'] for r in manifest}==names-{'payload_manifest.json','exit_code.txt','worker.pid','launch.log'} and all(inv['files']['output/'+r['name']]=={k:r[k] for k in ['bytes','sha256']} for r in manifest))
 plan=readout('order_plan.json');canonical=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 check('raw_andcanonical_order_bindings',sha(out/'order_plan.json')==q['order_plan']['sha256'] and init['order_sha256']==comp['order_sha256']==canonical)
 foldpath=B/'candidate_payload/fold_binding.json';mf=B/'candidate_payload/manifest_8192.jsonl';check('frozen_metadata_identity',sha(foldpath)==q['QC']['fold_binding']['sha256'] and sha(mf)==q['QC']['manifests']['8192']['sha256'])
 fold=read(foldpath)['folds']['D'];byid={r['case_id']:r for r in [json.loads(s) for s in mf.read_text().splitlines()]};source={c:r['source_id'] for c,r in byid.items()}
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
  parts=g['geometry'];assert set(parts)=={'coarse','dense','Q0','Q1','Q2','delta','delta0','delta1','N0_N1_equal'} and parts['N0_N1_equal'] is True
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
 check('all3900_batches_LR_BN_losses_RF_stages_and_Static_indices',True)
 exp=readout('exposure.json');check('exposure_recomputed',dict(cases)==exp['case'] and dict(sources)==exp['source'] and dict(drops)==exp['dropped_case'] and exp['order_sha256']==canonical and sum(cases.values())==31200 and sum(drops.values())==300 and all(cases[c]+drops[c]==100 for c in plan['case_ids']))
 mirror={k:Path(v) for k,v in read(H/'final_local_mirror_v2.json').items()}
 nr=q['admission']['construction'];np=mirror[nr['path']];assert sha(np)==nr['sha256'] and np.stat().st_size==nr['bytes']
 native=read(np);common=native['models'][0]['shared_initial_state_SHA256']
 check('formal_RF_admission_source_exact',common=='b7e5b640c1f0e709ab6697139db1267584266a51b4e0e29f2d5217bfd1236cc5' and native['models'][0]['phase']=='S_ref_eval1')
 check('native_common_initialization_matches',model['common_initial_state_SHA256']==common and model['factory']['parent']['parent']['artificial_fixture'] is False and model['factory']['parent']['scq']['variant']=='S' and model['factory']['rf']['variant']=='RF-Static' and model['factory']['rf']['additional_parameters']==231171 and model['factory']['rf']['total_parameters']==40827847 and model['factory']['rf']['initialization_sha256']==q['rf_initialization']['sha256'])
 check('both_frozen_head_initializers',model['factory']['parent']['scq']['initialization_sha256']==q['initialization']['sha256'] and model['factory']['rf']['common_state_preserved'] and model['factory']['rf']['CPU_RNG_preserved'])
 expected_new={'base_model.scq.W1.weight':.0005,'base_model.scq.W2.weight':.0005,'base_model.scq.W1.bias':0.,'base_model.scq.W2.bias':0.,'base_model.rf.V1.weight':.0005,'base_model.rf.V2.weight':.0005,'base_model.rf.V1.bias':0.,'base_model.rf.V2.bias':0.}
 check('all8_SCQ_RF_parameter_groups',model['new_optimizer_groups']==expected_new)
 groups=readout('optimizer_parameter_groups.json');defaults=readout('optimizer_actual_defaults.json');check('unique419parameters_total',len(groups)==len({r['name'] for r in groups})==419 and sum(math.prod(r['shape']) for r in groups)==40827847 and len([r for r in groups if r['name'].startswith('base_model.rf.')])==4)
 for r in groups:assert r['weight_decay']==(0 if r['name'].endswith(('.A_log','.D','.bias')) or len(r['shape'])==1 else .0005)
 check('SSM_andoptimizer_contract',all(sum(r['name'].endswith(s) and r['weight_decay']==0 for r in groups)==22 for s in ['.A_log','.D']) and defaults['lr']==.0001 and defaults['betas']==[.9,.999] and defaults['eps']==1e-8 and not defaults['amsgrad'] and not defaults['maximize'] and defaults['foreach'] is defaults['fused'] is None)
 check('runidentity',identity['variant']=='RF-Static' and identity['fold']=='D' and identity['stage']==q['stage'] and identity['native_admission_sha256']==q['admission']['audit']['sha256'] and identity['arm']=='RF-Static' and identity['legacy_stage_is_provenance_only'] is True and model['arm']=='RF-Static' and model['stage']==q['stage'] and identity['SSM_gradient_non_bitwise_reproducibility_disclosed'])
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

 # Historical records retain their original device identity. Only selector may differ in environment.
 historical=q['historical_identity'];current=q['identity']
 check('only_three_identity_fields_changed',{k for k in current if current[k]!=historical[k]}=={'hostname','gpu_uuid','driver_version'})
 migration=q['accepted_device_migration'];migration_path=mirror[migration['path']]
 check('accepted_migration_evidence_hash',sha(migration_path)==migration['sha256'] and migration_path.stat().st_size==migration['bytes'])
 check('current_selector_bound',q['environment']['CUDA_VISIBLE_DEVICES']==current['gpu_uuid'])
 check('cross_device_qualification_explicit',q['comparison_qualification']==dict(C_pair='SAME_DEVICE_PRIMARY_MECHANISM_EVIDENCE',D_Static_vs_Requery='DEVICE_AND_DRIVER_CONFOUNDED_SUPPLEMENTARY_EVIDENCE',strict_same_device_D_pair=False,do_not_attribute_all_differences_to_requery=True))
 def bound_set(ref):
  paths={k:mirror[r['path']] for k,r in ref.items()}
  for k,p in paths.items():assert sha(p)==ref[k]['sha256'] and p.stat().st_size==ref[k]['bytes']
  return paths
 def audited_output(a,p,name):
  f=p/name;assert sha(f)==a['artifacts']['output/'+name]['sha256'] and f.stat().st_size==a['artifacts']['output/'+name]['bytes'];return f
 def pair(ref,label,RF):
  paths=bound_set(ref);a=read(paths['audit']);bq=read(paths['request']);bm=read(paths['construction']);bd=paths['construction'].parent
  expected_status='FORMAL_RF_REQUERY_D_TRAINING_PAIR_FREEZE_AUDIT_PASS' if RF else 'FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS'
  check(label+'_frozen_audit',a['status']==expected_status and all(a['checks'].values()) and a['check_count']==(43 if RF else 30) and a['identity']==historical and a['updates']==3900 and a['exposures']==31200)
  keys=['science','resources','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','pair_contract','initialization','admission']
  check(label+'_scientific_contract_identical',all(q[k]==bq[k] for k in keys))
  env=bq['environment'];check(label+'_environment_only_selector_changed',set(env)==set(q['environment']) and {k for k in env if env[k]!=q['environment'][k]}=={'CUDA_VISIBLE_DEVICES'} and env['CUDA_VISIBLE_DEVICES']==historical['gpu_uuid'])
  check(label+'_shared_factory_initial_state',model['common_initial_state_SHA256']==bm['common_initial_state_SHA256']==a['common_initial_state_SHA256'] and model['factory']['parent']==(bm['factory']['parent'] if RF else bm['factory']))
  check(label+'_order_exposures_optimizer_defaults_exact',all(sha(out/n)==sha(audited_output(a,bd,n)) for n in ['order_plan.json','exposure.json','optimizer_actual_defaults.json']))
  bmetrics=[json.loads(x) for x in audited_output(a,bd,'metrics.jsonl').read_text().splitlines()]
  check(label+'_all3900_batches_schedules_paired',len(bmetrics)==3900 and all(all(x[k]==y[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm','optimizer_step_committed']) for x,y in zip(metrics,bmetrics)))
  bgroups=read(audited_output(a,bd,'optimizer_parameter_groups.json'))
  check(label+'_optimizer_groups_exact',(groups if RF else [r for r in groups if not r['name'].startswith('base_model.rf.')])==bgroups)
  check(label+'_same_sources_except_entry_bridge',all(q['implementation'][k]==r for k,r in bq['implementation'].items() if k not in ('entry','bridge')))
  if RF:
   bi=read(paths['initialization']);check(label+'_full_initial_parameters_buffers_exact',all(init[k]==bi[k]==q['expected_model_initialization'][k] for k in ['parameter_sha256','persistent_state_sha256','seed']))
   x=model['factory']['rf'];y=bm['factory']['rf'];check(label+'_RF_factory_only_variant_differs',set(x)==set(y) and all(x[k]==y[k] for k in x if k!='variant') and y['variant']=='RF-Requery' and x['variant']=='RF-Static')
  return sha(paths['audit'])
 pairs={label:pair(q[key],label,RF) for key,label,RF in [('paired_baseline','Sref_D',False),('paired_requery','Requery_D',True)]}
 check('expected_full_RF_initialization',all(init[k]==q['expected_model_initialization'][k] for k in ['parameter_sha256','persistent_state_sha256','seed']))
 expected={'Sref_C':('FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS',26),'Static_C':('FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',34),'Requery_C':('FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS',43)}
 continuation={}
 for key,r in q['continuation_evidence'].items():
  p=mirror[r['path']];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'];a=read(p)
  assert a['status']==expected[key][0] and a['check_count']==expected[key][1] and all(a['checks'].values()) and a['identity']==historical and a['common_initial_state_SHA256']==common
  continuation[key]=dict(sha256=sha(p),status=a['status'])
  if key=='Static_C':
   source=R/'outputs/scq_rf_Static_C_implementation_20261114_v1/post_training_freeze_v1/output'
   ci=read(audited_output(a,source,'initialization.json'));cm=read(audited_output(a,source,'model_construction.json'))
   check('Static_C_same_full_initialization_and_RF_factory',all(init[k]==ci[k] for k in ['parameter_sha256','persistent_state_sha256','seed']) and model['factory']==cm['factory'])
 check('all_C_trio_evidence_hashes_and_historical_identity',set(continuation)==set(expected))
 matrix=read(pair_path);check('D_matrix_order_and_data_unchanged',all(matrix['FoldD'][k]==q[k] for k in ['QC','order_plan','data_root']) and matrix['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'])
 check('run_identity_current_and_historical_disclosed',identity['execution_identity']==current and identity['historical_pair_identity']==historical and identity['cross_device_confounded_D_comparison'] is True)
 summary=dict(Static_N0_N1_equal_steps=sum(g['geometry']['N0_N1_equal'] for g in geo),RF_second_residual_mean=sum(sum(g['geometry']['delta1']['mean_norm']) for g in geo)/(3900*8),max_query_delta_norm=max(max(g['geometry']['delta']['max_norm']) for g in geo),units='D-only normalized; descriptive only, no efficacy conclusion')
 result=dict(status='FORMAL_RF_STATIC_D_TRAINING_PAIR_FREEZE_AUDIT_PASS',variant='RF-Static',fold='D',identity=current,historical_identity=historical,comparison_qualification=q['comparison_qualification'],request_sha256=RH,updates=3900,traversals=100,exposures=31200,drops=300,order_sha256=canonical,checkpoint=checkpoint,initialization=init,common_initial_state_SHA256=common,checks=checks,check_count=len(checks),counts=counts,peaks={k:max(r[k] for r in resources) for k in ['RSS','peak_allocated','peak_reserved','device_MiB','elapsed_seconds']},paired_audits=pairs,C_continuation_audits=continuation,delta_summary=summary,artifacts=inv['files'],BNCal=False,evaluation=False,resume=False,operations=dict(new_forward=0,new_backward=0,server_writes=0,checkpoint_loaded=False,checkpoint_downloaded=False),limitations=['D Static comparison is GPU/driver confounded supplementary evidence; C same-device pair remains primary mechanism evidence.','Checkpoint streamed twice without deserialization; initialization fingerprints verified against frozen records, not reconstructed tensors.','Static neighbor reuse verified from logged summaries and bound implementation, not independently recomputed KNN.','Resource telemetry is sampled; no PID namespace ownership guarantee or per-row free-disk telemetry.','No scientific efficacy conclusion from training logs.'])
 emit('freeze_verification_v1.json',result);print(json.dumps(dict(status=result['status'],checks=len(checks),checkpoint=checkpoint,updates=3900,peaks=result['peaks'])))
except BaseException as exc:
 emit('audit_failure_v1.json',dict(status='AUDIT_FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),new_forward=0));raise
