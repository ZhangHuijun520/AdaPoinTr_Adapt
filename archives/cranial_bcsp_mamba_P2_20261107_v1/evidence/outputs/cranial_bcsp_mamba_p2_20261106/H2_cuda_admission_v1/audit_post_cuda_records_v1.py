"""Independent stdlib post-CUDA audit. No Torch/NumPy imports or new gradients."""
import ast,hashlib,json,math,re,struct,time,zipfile
from pathlib import Path
S=Path(__file__).resolve().parent;F=S/'post_cuda_freeze_audit_20261107_v1';D=F/'downloads';START=time.monotonic();CHECKS=[]
def need(ok,msg):
 if not ok:raise ValueError(msg)
def good(msg,ok=True):need(ok,msg);CHECKS.append(msg)
def bind(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def close(a,b,msg):need(math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-6,abs_tol=2e-6),msg)
def fp(s):return isinstance(s,str) and re.fullmatch('[0-9a-f]{64}',s) is not None
def npy(blob):
 need(blob[:6]==b'\x93NUMPY' and blob[6:8] in [b'\x01\x00',b'\x02\x00'],'NPY format')
 n=2 if blob[6]==1 else 4;size=int.from_bytes(blob[8:8+n],'little');header=ast.literal_eval(blob[8+n:8+n+size].decode('latin1').strip());raw=blob[8+n+size:]
 need(header['descr']=='<f4' and header['shape']==(8192,3) and not header['fortran_order'] and len(raw)==8192*3*4,'fixed synthetic array')
 values=struct.unpack('<'+str(8192*3)+'f',raw);need(all(map(math.isfinite,values)),'synthetic finite values');return values,raw
def main():
 try:
  remote=read(F/'remote_file_audit_v1.json');good('remote_exact12_files_frozen_assets_and_stable_content',remote['status']=='REMOTE_POST_CUDA_READONLY_FILES_PASS' and remote['exact_output_files']==12 and remote['output_metadata_before_after_equal'] and remote['atime_excluded'] and remote['worker_absent'] and remote['tmux_absent'] and remote['exit_code']==0)
  qpath=S/'H2_artificial_cuda_execution_request_v1.json';q=read(qpath);qh=bind(qpath)['sha256'];good('authorized_complete_request_SHA',qh==remote['request_sha256']=='6e20c58d6ceee32b2f77858b9bb394535d39d999630302e0a115299e66de6e7a')
  for p in D.iterdir():need(bind(p)['sha256']==remote['output_SHA256']['./'+p.name],'fresh local/server file identity '+p.name)
  good('fresh_downloads_all_match_current_server_hashes',len(list(D.iterdir()))==12)
  manifest=read(D/'payload_manifest.json')['files'];expected={'AUX_optimizer_groups.json','AUX_result.json','COUPLE_optimizer_groups.json','COUPLE_result.json','attempts.jsonl','completion.json','native_SSM_origins.json','resources.jsonl'}
  good('exact8_payload_manifest_members',len(manifest)==len({r['name'] for r in manifest})==8 and {r['name'] for r in manifest}==expected)
  for r in manifest:
   b=bind(D/r['name']);need(b['bytes']==r['bytes'] and b['sha256']==r['sha256'],'payload hash '+r['name'])
  good('all_payload_hashes_and_bytes')
  expected_counts=dict(forward_attempts=2,forward_returns=2,loss_calls=2,backward_attempts=2,backward_returns=2,optimizer_steps=0);done=read(D/'completion.json')
  good('exit0_exact2F2B0_no_data_weights_training_BNCal',done['status']=='H2_SYNTHETIC_CUDA_COMPLETE_PENDING_FREEZE_AUDIT' and done['request_sha256']==qh and done['counts']==expected_counts and done['model_modes']==['AUX','COUPLE'] and done['weight_BN_RNG_equal'] is True and done['real_data_reads']==done['checkpoint_loads']==0 and done['optimizer_constructed'] is False and done['training_executed'] is False and done['BNCal'] is False and (D/'exit_code.txt').read_text().strip()=='0')
  journal=[json.loads(x) for x in (D/'attempts.jsonl').read_text().splitlines()];need(journal==[dict(event='CLAIMED_BEFORE_'+op,mode=mode,index=i) for i,mode in enumerate(['AUX','COUPLE'],1) for op in ['FORWARD','BACKWARD']],'exact four claims');good('unique_two_forward_two_backward_attempt_journal')
  p3=read(S/'entry_P3_v1.json');ip3=read(S.parent/'H2_implementation_v1/implementation_P3_v1.json');good('CPU_entry8_and_H2_33_P3_source_bindings',p3['status']=='LOCAL_H2_CUDA_ENTRY_CPU_P3_PASS' and p3['CPU_checks']==8 and ip3['status']=='LOCAL_H2_IMPLEMENTATION_P3_PASS' and ip3['CPU_checks']==33)
  for b in [p3['CPU_result'],p3['H2_implementation_P3'],p3['fixture'],*p3['sources']]:need(bind(b['path'])==b,'local P3 evidence hash')
  cpu=read(p3['CPU_result']['path']);need(cpu['status']=='H2_CUDA_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['errors']==cpu['failures']==0,'CPU result status')
  for b in cpu['bindings']:need(bind(b['path'])==b,'CPU current source binding')
  fixture_path=S/'artificial_h2_input_v1.npz';definition=read(S/'artificial_fixture_definition_v1.json');need(bind(fixture_path)['sha256']==q['artificial_input']['sha256']==definition['payload']['sha256'],'synthetic input hash')
  with zipfile.ZipFile(fixture_path) as z:
   need(set(z.namelist())=={'partial.npy','target.npy'},'only synthetic inputs');arrays={}
   for key in ['partial','target']:
    values,raw=npy(z.read(key+'.npy'));need(hashlib.sha256(raw).hexdigest()==definition['arrays'][key]['sha256'],'synthetic array hash');arrays[key]=values
  v=arrays['target'];gt_center=[math.fsum(v[k::3])/8192 for k in range(3)];gt_radius=math.sqrt(math.fsum(sum((v[3*i+j]-gt_center[j])**2 for j in range(3)) for i in range(8192))/8192);good('synthetic_fixture_bytes_arrays_and_GT_moments_only_no_real_data')
  results={};groupbank={};statebank={};maxima={}
  for i,mode in enumerate(['AUX','COUPLE'],1):
   z=read(D/(mode+'_result.json'));groups=read(D/(mode+'_optimizer_groups.json'));group={r['name']:r for r in groups};need(len(group)==len(groups),'unique parameter groups');groupbank[mode]=groups
   need(z['mode']==mode and z['model_mode']=='eval_with_autograd' and z['optimizer_constructed'] is False and math.isfinite(z['loss']),'model result scope')
   need(z['counts']==dict(forward_attempts=i,forward_returns=i,loss_calls=i,backward_attempts=i,backward_returns=i,optimizer_steps=0),'per-mode cumulative counts')
   need(fp(z['state_before']) and z['state_before']==z['state_after'],'full weight/BN hash '+mode);statebank[mode]=z['state_before']
   rng=z['RNG_before'];need(set(rng)=={'CPU','CUDA','Python','numpy'} and rng==z['RNG_after'] and fp(rng['CPU']) and fp(rng['CUDA']) and all(isinstance(rng[k],str) and len(rng[k])>0 for k in ['Python','numpy']),'four RNG representations '+mode)
   construction=z['construction'];need(construction['variant']=='M0' and construction['seed']==0 and construction['artificial_fixture'] is False and construction['replaced_global_branches']==6 and construction['common_state_unchanged'] and construction['common_state_after_H2_unchanged'] and construction['H2_mode']==mode,'real native model construction')
   need(construction['mamba_config']==dict(d_model=384,d_state=16,d_conv=4,expand=2,use_fast_path=True),'native Mamba config')
   mixers=construction['initialized_mixers'];need([r['block'] for r in mixers]==list(range(6)) and all(r['mixer_class']=='mamba_ssm.modules.mamba_simple.Mamba' and all(fp(v) for v in r['parameter_fingerprints'].values()) for r in mixers),'six native mixer initialization records')
   need(group['h2_range_head.weight']['shape']==[1,1024] and group['h2_range_head.bias']['shape']==[1] and group['h2_range_head.weight']['weight_decay']==.0005 and group['h2_range_head.bias']['weight_decay']==0,'new1025 parameter grouping')
   ssms=[r for r in groups if r['name'].endswith('.A_log') or r['name'].endswith('.attn.mixer.D')];need(len(ssms)==12 and all(r['weight_decay']==0 and r['reason']=='explicit_no_weight_decay' for r in ssms),'12 SSM no-decay parameter records')
   total=sum(math.prod(r['shape']) for r in groups);need(total==construction['total_parameters']+1025,'only1025 new parameters')
   grad=z['gradient_norms'];need(len(grad)>0 and set(grad)<=set(group) and all(isinstance(n,(float,int)) and math.isfinite(n) and n>=0 for n in grad.values()),'all saved gradient norms finite/nonnegative')
   need(grad.get('h2_range_head.weight',0)>0 and grad.get('h2_range_head.bias',0)>0 and any(n.startswith('base_model.coarse_pred.') and x>0 for n,x in grad.items()) and any(n.startswith('base_model.encoder.') and x>0 for n,x in grad.items()),'nonzero head/coarse/encoder gradients')
   fixture=z['fixture_head'];need(fixture==dict(weight=1e-3/1024,bias=.1,configured_before_snapshot=True),'same fixed synthetic head setup')
   log=z['H2_log'];need(log['H2_mode']==mode and log['H2_generation']==1 and log['loss_dense_includes_H2_aux'] is True,'single-context log')
   need(all(len(log[k])==1 for k in ['H2_delta','H2_target_t','H2_scale','H2_radius_raw','H2_radius_used','H2_radius_dense','H2_radius_GT']),'one artificial case')
   delta=log['H2_delta'][0];target=log['H2_target_t'][0];scale=log['H2_scale'][0];rr=log['H2_radius_raw'][0];ru=log['H2_radius_used'][0];rg=log['H2_radius_GT'][0]
   need(all(math.isfinite(x) for x in [delta,target,scale,rr,ru,rg,log['H2_radius_dense'][0]]) and min(rr,ru,rg,log['H2_radius_dense'][0])>1e-6,'finite positive guarded moments')
   close(target,math.log(rg)-math.log(rr),'dynamic residual target uses raw Q');error=delta-target;aux=(error*error/.2 if abs(error)<.1 else abs(error)-.05)
   close(log['H2_aux_raw'],aux,'SmoothL1 beta.1');close(log['H2_aux_weighted'],.1*aux,'aux weight.1');close(z['loss'],log['loss_original_reconstruction']+.1*aux,'original reconstruction plus aux exactly once')
   a=math.log(1.25);expected_scale=1. if mode=='AUX' else math.exp(a*math.tanh(delta/a));close(scale,expected_scale,'condition detached scale value');need(.8-1e-6<=scale<=1.25+1e-6,'scale bounds')
   if mode=='COUPLE':need(abs(scale-1)>1e-6,'nonzero fixture coupling')
   for x,y in zip(log['H2_centroid_raw'][0],log['H2_centroid_used'][0]):close(x,y,'coarse centroid preserved')
   close(ru,rr*scale,'coarse radius scaling identity');close(rg,gt_radius,'independent synthetic GT radius')
   for x,y in zip(log['H2_centroid_GT'][0],gt_center):close(x,y,'independent synthetic GT center')
   expected_bias=.1*min(abs(error)/.1,1.);close(grad['h2_range_head.bias'],expected_bias,'head bias grad norm equals aux-only derivative')
   results[mode]=dict(loss=z['loss'],gradient_norm_records=len(grad),nonzero_gradient_norm_records=sum(v>0 for v in grad.values()),head_weight_norm=grad['h2_range_head.weight'],head_bias_norm=grad['h2_range_head.bias'],six_Mamba_A_log_norms={n:v for n,v in grad.items() if n.endswith('.A_log')},state_before=z['state_before'],state_after=z['state_after'],RNG_fingerprints={k:hashlib.sha256(v.encode()).hexdigest() if k in ['Python','numpy'] else v for k,v in rng.items()},delta=delta,scale=scale,auxiliary_raw=aux,parameters_including_head=total)
  good('two_native_M0_models_six_mixers_and_common_initialization',read(D/'AUX_result.json')['construction']['common_state']==read(D/'COUPLE_result.json')['construction']['common_state'] and read(D/'AUX_result.json')['construction']['initialized_mixers']==read(D/'COUPLE_result.json')['construction']['initialized_mixers'])
  good('two_full_parameter_BN_state_hashes_and_all_RNG_before_after_equal');good('identical_parameter_groups_only1025_head_parameters_and_SSM_no_decay',groupbank['AUX']==groupbank['COUPLE']);good('all_saved_gradient_norms_finite_nonzero_critical_branches');good('aux_target_loss_head_bias_derivative_and_soft_coupling_algebra')
  origins=read(D/'native_SSM_origins.json');need(origins['version']=='2.3.1' and len(origins['origins'])==len(set(origins['origins']))==7 and set(origins['origins'])<=set(r['path'] for r in q['dependencies']),'pinned native origins');good('seven_native_SSM_module_origins_pinned')
  resources=[json.loads(s) for s in (D/'resources.jsonl').read_text().splitlines()];need(len(resources)==7 and all(all(r['checks'].values()) and r['failed_checks']==[] and r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE' for r in resources),'seven resource guards')
  need([(r['phase'],r['forwards']) for r in resources]==[('before_forward:AUX',0),('before_backward:AUX',1),('after_backward:AUX',1),('before_forward:COUPLE',1),('before_backward:COUPLE',2),('after_backward:COUPLE',2),('all_complete',2)],'resource phase/count order')
  limits=q['limits']
  for r in resources:
   v=r['values'];need(v['RSS_bytes']<=limits['RSS_bytes'] and v['output_bytes']<=limits['output_bytes'] and v['device_MiB']<=limits['device_MiB'] and v['peak_allocated']<=limits['torch_peak_bytes'] and v['peak_reserved']<=limits['torch_peak_bytes'] and v['elapsed_seconds']<=limits['wall_seconds'] and v['free_disk_bytes']>=limits['minimum_free_disk_bytes'],'independent resource threshold checks')
  maxima={k:max(r['values'][k] for r in resources) for k in ['RSS_bytes','output_bytes','device_MiB','peak_allocated','peak_reserved','elapsed_seconds']};good('seven_resource_samples_independently_checked')
  report=dict(status='FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS',request_sha256=qh,checks=CHECKS,counts=expected_counts,models=results,resource_sample_maxima=maxima,output_manifest=[bind(p) for p in D.iterdir()],remote_file_audit=bind(F/'remote_file_audit_v1.json'),seconds=time.monotonic()-START,new_forward=0,new_backward=0,optimizer_steps=0,model_imports=0,torch_imported=False,numpy_imported=False,server_writes=0,training_authorized=False,limitations=['Saved complete-state fingerprints compared and tied to frozen executed code; synthetic model tensors themselves were not persisted, so state hashes cannot be recomputed from weights','Full gradient tensors were not saved; finite/nonzero norms and aux bias derivative checked independently, per-element finiteness relies on the frozen worker check','Python/NumPy RNG serialized strings compared exactly and compactly hashed; CPU/CUDA RNG byte hashes compared, no RNG sampling/restoration','Only eval/autograd synthetic batch1 path; not training-mode BN, batch8 resource admission, 3900-step stability, or H2 scientific/clinical benefit','No cross-arm bitwise gradient-equality requirement; accepted finite Mamba backward nondeterminism retained'])
 except BaseException as exc:report=dict(status='FORMAL_POST_H2_CUDA_FREEZE_AUDIT_FAILED_STOP_NO_RETRY',passed_checks=CHECKS,error=repr(exc),seconds=time.monotonic()-START,new_forward=0,new_backward=0,server_writes=0)
 with (F/'formal_audit_report_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,allow_nan=False)
 print(json.dumps({k:v for k,v in report.items() if k not in ['output_manifest','models']}))
 if report['status']!='FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS':raise SystemExit(1)
if __name__=='__main__':main()
