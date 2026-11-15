SPEC={'request_sha256': '187a19712d92cb5cdf92eebc2a46ffe5caf6e99614224bc8fbac0a2498e76b82', 'request_path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/FoldC_T0_M0_development_execution_request_v2.json', 'controls': [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/bcsp_p1_paired_predict_v2.py', 'bytes': 22296, 'sha256': '7f31ecddfed05bd49f3e42093b99477643ddce733dadbebb80f58d08f17f5d1c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/FoldC_T0_M0_development_execution_request_v2.json', 'bytes': 12453, 'sha256': '187a19712d92cb5cdf92eebc2a46ffe5caf6e99614224bc8fbac0a2498e76b82'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/launch_once_template_v2.sh', 'bytes': 2427, 'sha256': 'd2370c997fbb92a2167b78d7e818590cd165222438422d6c7c8449b2716aaff7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/local_P3_v2.json', 'bytes': 2878, 'sha256': 'f3cafe010fbadeaf755369ecb89f8056f7356d13afc37a629858a04b134b21f6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/M0_post_training_and_pair_freeze_audit_v1.json', 'bytes': 58084, 'sha256': 'bcbfb9a65742ab7c9da4a2d01c55b5f9a78bc77da66e38cf078f3074e0968815'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/paired_development_input_index_v1.json', 'bytes': 170709, 'sha256': '576feea085172538c2a0dc52f8e8e7a8eb8087bba1a5542ea7fc1eeb6a72f3bc'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/paired_development_protocol_v1.json', 'bytes': 3161, 'sha256': '237ac077bef166b6d2246bd0b6fc6ebfe36b4904b3789b99bc11b335e047f77a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/paired_FoldC_training_freeze_receipt_v1.json', 'bytes': 2103, 'sha256': '1b76274551cf88721d48e819cf70fe58c0425b13f94c3ad0c3299ef2f907cfe6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/T0_post_training_freeze_audit_v1.json', 'bytes': 48076, 'sha256': '428702c74772018d12a6f25131834e0c370c9b712c51a31f45497e3694ed5e42'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/control/paired_authorization_v2.json', 'bytes': 394, 'sha256': 'a63cb835fc2967ac432ad5151171eecc28e5f62f0d89b60b16b4919fc4e6070e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/control/paired_runtime_v2.json', 'bytes': 227, 'sha256': '33d91bacd4565a7bc9f97f5b62b08657f4adee50e1204f938b4bba0a012b4777'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/control/paired_launch_once_v2.sh', 'bytes': 2571, 'sha256': 'f1b9a603a5a71ff58832ce183872adc1ed4aec1633c0bc20b4d8c67d2c282640'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v2/control/paired_launch_attempt_v2.json', 'bytes': 125, 'sha256': 'd3a562948f2d3a667335c4ca84a3c2d4aee395f12879187c19254e6239e7f2e3'}], 'observed_archive': {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/FoldC_T0_M0_development_20261106_v2/development_predictions_v1.tar.gz', 'bytes': 19045938, 'sha256': '068dd9812c410c2b84451740a3ed2eb2f12326d8a66fe3bc3ee4623ab3f9b733'}, 'limits': {'read_bytes': 2147483648, 'wall_seconds': 60}}
"""In-memory server audit. SPEC is frozen locally; stdlib only; no server writes."""
import base64,zlib,array,ast,datetime,hashlib,io,json,math,os,shutil,socket,struct,subprocess,sys,tarfile,time,zipfile
from pathlib import Path
START=time.monotonic();READ=0;PHASE='identity';CHECKS=[];HASH_CACHE={};READ_STAMPS={}
def need(ok,reason):
 if not ok:raise RuntimeError(reason)
def budget(n=0):
 global READ
 READ+=n
 need(READ<=SPEC['limits']['read_bytes'] and time.monotonic()-START<=SPEC['limits']['wall_seconds'],'audit read/time budget')
def safe(p):
 p=Path(p);need(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'link/absolute path: '+str(p));return p
def stamp(p):
 s=Path(p).stat();return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns)
def inventory(out):
 found={}
 for p in [out,*out.rglob('*')]:
  safe(p);need(p.is_file() or p.is_dir(),'special output');need(len(found)<512,'output inventory count');found[str(p)]=stamp(p)
 return found
def read(p,cap=4194304):
 p=safe(p);need(p.is_file() and p.stat().st_size<=cap,'ordinary file size/type: '+str(p));before=stamp(p);raw=p.read_bytes();budget(len(raw));need(stamp(p)==before,'file changed during read: '+str(p));READ_STAMPS[str(p)]=before;return raw
def hashed(p,cap=536870912):
 p=safe(p)
 if str(p) in HASH_CACHE:return HASH_CACHE[str(p)]
 st=p.stat();need(p.is_file() and st.st_size<=cap,'hash file size/type: '+str(p));h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):budget(len(b));h.update(b)
 after=p.stat();need((st.st_ino,st.st_size,st.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'file changed: '+str(p))
 result=dict(path=str(p),bytes=st.st_size,sha256=h.hexdigest());HASH_CACHE[str(p)]=result;READ_STAMPS[str(p)]=stamp(p);return result
def exact(r):
 got=hashed(r['path']);need(all(got[k]==r[k] for k in ['bytes','sha256']),'bound hash: '+r['path']);return got
def good(name):CHECKS.append(name)
def phase(name):
 global PHASE
 PHASE=name;print(json.dumps(dict(phase=name,seconds=time.monotonic()-START)),flush=True)

def array_contract(blob,coarse_expected):
 arrays={}
 with zipfile.ZipFile(io.BytesIO(blob)) as z:
  names=z.namelist();need(names==(['prediction.npy','coarse.npy'] if coarse_expected else ['prediction.npy']),'NPZ exact array keys')
  for name in names:
   info=z.getinfo(name);need(info.file_size<=1048576 and not info.flag_bits&1,'NPZ array cap/encryption')
   raw=z.read(name);budget(len(raw));need(raw[:6]==b'\x93NUMPY','NPY magic');version=raw[6:8]
   if version==b'\x01\x00':offset=10;size=struct.unpack('<H',raw[8:10])[0]
   elif version in [b'\x02\x00',b'\x03\x00']:offset=12;size=struct.unpack('<I',raw[8:12])[0]
   else:raise RuntimeError('NPY version')
   need(size<=65536 and offset+size<=len(raw),'NPY header cap')
   count=8192 if name=='prediction.npy' else 256
   hdr=ast.literal_eval(raw[offset:offset+size].decode('utf-8' if version==b'\x03\x00' else 'latin1').strip());need(hdr==dict(descr='<f4',fortran_order=False,shape=(count,3)),'NPY dtype/shape/layout')
   data=raw[offset+size:];need(len(data)==count*3*4,'array exact byte length');values=array.array('f');need(values.itemsize==4,'float width');values.frombytes(data)
   if sys.byteorder!='little':values.byteswap()
   need(all(math.isfinite(v) for v in values),'nonfinite array');arrays[name]=values
 return arrays

def verify_summary(values,s):
 n=len(values)//3;means=[math.fsum(values[k::3])/n for k in range(3)];rg2=math.fsum((values[i]-means[i%3])**2 for i in range(len(values)))/n
 need(all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-9) for a,b in zip(means,s['centroid'])),'summary centroid mismatch')
 for label,op in [('bbox_min',min),('bbox_max',max)]:need(s[label]==[op(values[k::3]) for k in range(3)],'summary bbox mismatch')
 need(math.isclose(s['radius_gyration']**2,rg2,rel_tol=1e-8,abs_tol=1e-9),'summary gyration mismatch')
 need(len(s['covariance_eigenvalues'])==3 and all(math.isfinite(v) and v>=-1e-9 for v in s['covariance_eigenvalues']) and math.isclose(sum(s['covariance_eigenvalues']),rg2,rel_tol=1e-8,abs_tol=1e-9),'summary covariance trace')

try:
 phase('identity_controls')
 raw=read(SPEC['request_path']);need(hashlib.sha256(raw).hexdigest()==SPEC['request_sha256'],'authorized request SHA');q=json.loads(raw);L=q['launch_contract'];I=q['identity'];out=safe(q['output']);root=safe(Path(SPEC['request_path']).parent)
 need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'],'hostname/uid');os.chdir(I['project']);need(str(Path.cwd())==I['project'],'project cwd')
 TREE_BEFORE=inventory(out)
 need(subprocess.run(['/usr/bin/tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode==1,'session not ended')
 need(read(L['exit_code'],64).strip()==b'0','exit code')
 pid=read(L['pid'],64).decode().strip();need(pid.isdigit(),'PID');proc=Path('/proc')/pid/'cmdline';cmd=proc.read_bytes() if proc.exists() else b'';need(q['entry']['path'].encode() not in cmd,'worker live')
 controls=[exact(r) for r in SPEC['controls']];need(len(controls)==13,'13 exact files')
 need({p.name for p in root.iterdir()}=={Path(r['path']).name for r in SPEC['controls'][:9]}|{'control'},'installation exact set')
 need({p.name for p in (root/'control').iterdir()}=={Path(r['path']).name for r in SPEC['controls'][9:]},'exact4 controls')
 a_raw=read(L['authorization']);a=json.loads(a_raw);runtime=json.loads(read(L['runtime']));claim=json.loads(read(q['launch_attempt']))
 need(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-development-authorization-v1' and a['request_sha256']==SPEC['request_sha256'] and a['explicit_user_authorization'] is True and SPEC['request_sha256'] in a['user_authorization_text'],'authorization')
 need(runtime==dict(schema='bcsp-development-runtime-v1',request_sha256=SPEC['request_sha256'],authorization_sha256=hashlib.sha256(a_raw).hexdigest()),'one-way runtime')
 need(claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=SPEC['request_sha256']),'single-use claim')
 good('identity_exit0_session_worker_ended_and13_frozen_installation_controls_rehashed')
 good('authorization_runtime_single_attempt_match_original_materialization')
 phase('frozen_sources_inputs')
 for r in [q['input_index'],q['protocol'],q['fold_binding'],q['source_index'],q['source_manifest'],q['static_config'],q['numeric_policy'],q['helper'],*q['implementation'].values()]:exact(r)
 index=json.loads(read(q['input_index']['path']));protocol=json.loads(read(q['protocol']['path']));fold=json.loads(read(q['fold_binding']['path']))['folds']['C'];runs=index['runs'];inputs=index['inputs'];models={r['label']:r for r in runs}
 need([r['label'] for r in runs]==['C_T0','C_M0'] and len(inputs)==210,'two arms/210')
 need(len(fold['dev_sources'])==21 and len(fold['train_sources'])==63 and not set(fold['dev_sources'])&set(fold['train_sources']),'source separation')
 checkpoints=[exact(r['checkpoint']) for r in runs]
 for r in runs:
  selected=[x for x in inputs if x['run']==r['label']];need(len(selected)==105 and [x['case_id'] for x in selected]==r['dev_case_ids']==fold['dev_case_ids'] and r['dev_sources']==fold['dev_sources'] and r['train_sources']==fold['train_sources'],'ordered105/fold')
  need(r['variant']==r['label'][2:] and r['n_input']==r['n_output']==8192 and r['seed']==0,'model/input identity')
 for x,y in zip(inputs[:105],inputs[105:]):need(all(x[k]==y[k] for k in ['case_id','source_id','input','normalization','normalization_source','target_array_sha256']),'paired input/frame')
 unique={x['input']['path']:x['input'] for x in inputs};need(len(unique)==105,'105 inputs')
 for r in unique.values():exact(r)
 source=[r for r in json.loads(read(q['source_index']['path']))['inputs'] if r['run']=='C_8192'];source_manifest={r['case_id']:r for r in [json.loads(x) for x in read(q['source_manifest']['path']).splitlines()]}
 need(len(source)==105 and len(source_manifest)==420,'source index/manifest count')
 for row,original in zip(inputs[:105],source):
  need(all(row[k]==original[k] for k in ['case_id','source_id','input']),'original input provenance');m=source_manifest[row['case_id']];need(all(row[k]==m[k] for k in ['source_id','normalization','normalization_source','target_array_sha256']),'D-only coordinates/target')
 good('two_frozen_checkpoints_105_input_files_and_reused_factory_encoder_helper_rehashed')
 good('same105_cases21_sources_5_defects_source_separation_order_D_only_normalization')
 phase('output_state_RNG')
 archive_name='development_predictions_v1.tar.gz';expected_root={'predictions','tmp','launch.log','worker.pid','exit_code.txt','resources.jsonl','inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','completion.json',archive_name,archive_name+'.sha256',archive_name+'.bytes',archive_name+'.contents.sha256'}
 need({p.name for p in out.iterdir()}==expected_root and not list((out/'tmp').iterdir()),'exact output entries/empty tmp')
 log=read(out/'launch.log');need(b'Traceback (most recent call last)' not in log and log.count(b'MODEL - INFO - Transformer with config')==2,'two model startup/no traceback')
 records=[json.loads(x) for x in read(out/'inference_manifest.jsonl').splitlines()];attempts=[json.loads(x) for x in read(out/'forward_attempts.jsonl').splitlines()];geometry=[json.loads(x) for x in read(out/'geometry_summary.jsonl').splitlines()];done=json.loads(read(out/'inference_complete.json'));completion=json.loads(read(out/'completion.json'))
 need(len(records)==len(attempts)==len(geometry)==210 and [r['forward_index'] for r in records]==[r['forward_index'] for r in attempts]==list(range(1,211)),'exact210 records/claims')
 need(done['status']=='P1_PAIR_210_FORWARD_COMPLETE' and completion['status']=='PREDICTIONS_ARCHIVED_AWAITING_LOCAL_SCORING' and done['forwards']==completion['forwards']==210 and done['request_sha256']==completion['request_sha256']==SPEC['request_sha256'],'completion request/count')
 need(all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']),'forbidden counters')
 need([r['run'] for r in done['models']]==['C_T0','C_M0'],'two model evidence')
 for m,variant in zip(done['models'],['T0','M0']):
  need(m['forwards']==105 and len(m['state_before'])==64 and m['state_before']==m['state_after'],'parameter/BN invariant')
  need(set(m['RNG_before'])=={'CPU','CUDA','Python','numpy'} and m['RNG_before']==m['RNG_after'] and all(m['RNG_before'].values()) and len(m['RNG_before']['CPU'])==len(m['RNG_before']['CUDA'])==64,'four RNG invariants')
  need(m['mode']=='eval_inference_mode' and m['BNCal']==m['optimizer']==m['backward']==0,'eval-only evidence')
  c=m['construction'];need(c['variant']==variant and c['seed']==0 and c['common_state_unchanged'] and not c['artificial_fixture'] and c['replaced_global_branches']==(6 if variant=='M0' else 0) and not c['old_adapter_added'],'factory variant identity')
  if variant=='M0':need(len(c['initialized_mixers'])==6 and c['shared_bidirectional_scans_per_forward']==12 and all(x['mixer_class']=='mamba_ssm.modules.mamba_simple.Mamba' for x in c['initialized_mixers']),'native Mamba construction evidence')
 need(done['models'][0]['construction']['common_state']==done['models'][1]['construction']['common_state'],'shared initialization exact')
 good('210_attempts210_predictions_complete_zero_updates_BNCal_loss_backward')
 good('both_models_parameter_BN_CPU_CUDA_Python_NumPy_RNG_before_after_equal')
 good('native_T0_M0_factory_identity_and_common_initialization_evidence')
 phase('210_prediction_files')
 expected_files=[];live={};counts={label:0 for label in models};coarse_count=0;representatives=set(protocol['coarse_tensor_cases'])
 need(len(representatives)==7,'7 predetermined coarse cases')
 for i,(observed,wanted,journal,geo) in enumerate(zip(records,inputs,attempts,geometry),1):
  label=wanted['run'];need(all(observed[k]==wanted[k] for k in ['run','variant','case_id','source_id','fold','n_input','normalization']),'prediction row provenance/order')
  need(observed['n_output']==8192 and observed['input_sha256']==wanted['input']['sha256'] and observed['checkpoint_sha256']==models[label]['checkpoint']['sha256'],'checkpoint/input provenance')
  need(journal==dict(forward_index=i,run=label,case_id=wanted['case_id'],status='CLAIMED_BEFORE_FORWARD'),'forward claim identity')
  need(geo['run']==label and geo['case_id']==wanted['case_id'] and geo['frame']=='native_D_only_normalized_no_GT','geometry row identity/frame')
  name='predictions/'+label+'__'+wanted['case_id']+'.npz';r=observed['prediction'];need(r['name']==name,'prediction filename');blob=read(out/name,1048576);actual=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest());need(actual['bytes']==r['bytes'] and actual['sha256']==r['sha256'],'prediction bytes/SHA')
  keep=wanted['case_id'] in representatives;arrays=array_contract(blob,keep);coarse_count+=int(keep);verify_summary(arrays['prediction.npy'],geo['dense'])
  if keep:verify_summary(arrays['coarse.npy'],geo['coarse'])
  else:need(all(math.isfinite(x) for key in ['centroid','bbox_min','bbox_max','covariance_eigenvalues'] for x in geo['coarse'][key]) and math.isfinite(geo['coarse']['radius_gyration']),'finite coarse summary')
  need(len(geo['mean_dense_minus_coarse'])==3 and all(math.isfinite(x) for x in geo['mean_dense_minus_coarse']) and math.isfinite(geo['offset_mean_squared_radius']) and geo['offset_mean_squared_radius']>=0,'finite offset summary')
  live[name]=actual;expected_files.append(name);counts[label]+=1
 need({p.name for p in (out/'predictions').iterdir()}=={Path(n).name for n in expected_files} and len(set(expected_files))==210 and counts=={'C_T0':105,'C_M0':105} and coarse_count==14,'prediction/coarse strict set/count')
 good('all210_NPZ_hashes_float32_finite8192x3_and14_coarse256x3_verified_no_GT_arrays')
 good('210_geometry_rows_and_dense14_saved_coarse_summaries_cross_checked')
 phase('resources_archive')
 resources=[json.loads(x) for x in read(out/'resources.jsonl').splitlines()];sequence=[];offset=0
 for label in models:
  sequence.append(('model_start:'+label,offset))
  for k in range(105):sequence.extend([('before_forward',offset+k),('after_forward',offset+k+1)])
  offset+=105
 sequence.append(('all_complete',210));need([(x['phase'],x['forwards']) for x in resources]==sequence,'423 resource sequence')
 L=q['limits'];previous=-1;maxima={k:0 for k in ['RSS_bytes','device_MiB','peak_allocated','peak_reserved','output_bytes']}
 for r in resources:
  v=r['values'];need(all(isinstance(x,(int,float)) and math.isfinite(x) for x in v.values()),'finite resources')
  recomputed=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=L['wall_seconds'],disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
  need(r['checks']==recomputed and all(recomputed.values()) and not r['failed_checks'],'resource thresholds');need(v['elapsed_seconds']>=previous and r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE','resource time/PID policy');previous=v['elapsed_seconds']
  for k in maxima:maxima[k]=max(maxima[k],v[k])
 good('423_resource_records_sequence_and_all_thresholds_independently_recomputed')
 for name in ['inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl']:
  blob=read(out/name);live[name]=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest());expected_files.append(name)
 receipt=completion['archive'];archive=hashed(out/archive_name,67108864);need(all(archive[k]==receipt[k]==SPEC['observed_archive'][k] for k in ['path','bytes','sha256']),'archive hash/size/path')
 need([r['name'] for r in receipt['members']]==expected_files and len(expected_files)==215,'215 member receipt order')
 for r in receipt['members']:need(r['bytes']==live[r['name']]['bytes'] and r['sha256']==live[r['name']]['sha256'],'member receipt vs live')
 with tarfile.open(out/archive_name) as t:
  members=t.getmembers();need(len(members)==215 and [m.name for m in members]==expected_files and len({m.name for m in members})==215,'tar exact member sequence')
  for m in members:
   need(m.isfile() and m.size==live[m.name]['bytes'] and m.size<=4194304,'archive member type/size');blob=t.extractfile(m).read();budget(len(blob));need(hashlib.sha256(blob).hexdigest()==live[m.name]['sha256'],'archive member hash')
 need(read(out/(archive_name+'.sha256'),1024).decode()==archive['sha256']+'  '+archive_name+'\n','SHA sidecar')
 need(read(out/(archive_name+'.bytes'),128).decode()==str(archive['bytes'])+'\n','bytes sidecar')
 need(read(out/(archive_name+'.contents.sha256'),131072).decode()==''.join(live[n]['sha256']+'  '+n+'\n' for n in expected_files),'contents sidecar')
 downloads=[archive]+[hashed(out/(archive_name+s),131072) for s in ['.sha256','.bytes','.contents.sha256']]
 good('archive215_members_each_rehashed_equal_live_and_all4_download_files_verified')
 output_manifest=[hashed(p) for p in sorted(out.rglob('*')) if p.is_file()];need(len(output_manifest)==223,'223 output files')
 total_output=sum(r['bytes'] for r in output_manifest);need(total_output<=L['output_bytes'],'final output cap')
 for r in output_manifest:need(hashlib.sha256(read(r['path'],67108864)).hexdigest()==r['sha256'],'final output content recheck')
 need(inventory(out)==TREE_BEFORE and all(stamp(p)==s for p,s in READ_STAMPS.items()),'evidence changed during audit')
 good('complete223_output_files_rehashed_and_content_metadata_stable_atime_excluded')
 metadata=[dict(path=str(p),bytes=p.stat().st_size,sha256=hashed(p)['sha256'],content_base64=base64.b64encode(read(p)).decode()) for p in sorted(out.iterdir()) if p.is_file() and p.name!=archive_name]
 state_evidence=[{k:v for k,v in m.items() if k!='construction'} for m in done['models']]
 result=dict(status='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),hostname=socket.gethostname(),uid=os.getuid(),request_sha256=SPEC['request_sha256'],checks=CHECKS,exit_code=0,forward_attempts=210,successful_predictions=210,unique_cases=105,dev_sources=21,per_model=counts,coarse_arrays=14,state_evidence=state_evidence,resource_records=423,resource_maxima=maxima,recorded_inference_seconds=previous,control_hashes=controls,checkpoint_hashes=checkpoints,input_file_hashes=[HASH_CACHE[p] for p in unique],output_manifest=output_manifest,archive_members=215,download_files=downloads,actual_output_bytes=total_output,free_disk_bytes=shutil.disk_usage(out).free,read_bytes=READ,seconds=time.monotonic()-START,frozen_metadata=metadata,limitations=['Recorded state/RNG fingerprints validated; model states not independently reconstructed','CPU/stdlb integrity audit does not prove CUDA numerical determinism or clinical accuracy','Resource monitoring is sampled, not a hard cgroup limit; GPU peak counters are reset for each model'],server_writes=0,checkpoint_deserialization=False,model_imports=0,CUDA_calls=0,forward_calls=0,scoring_executed=False,downloaded_prediction_archive_to_Windows=False)
 data=json.dumps(result,allow_nan=False).encode();print(json.dumps(dict(status=result['status'],audit_json_sha256=hashlib.sha256(data).hexdigest(),audit_json_zlib_base64=base64.b64encode(zlib.compress(data,9)).decode())),flush=True)
except BaseException as exc:
 print(json.dumps(dict(status='FORMAL_POST_PREDICTION_FREEZE_AUDIT_FAILED_STOP',phase=PHASE,error=repr(exc),passed_checks=CHECKS,read_bytes=READ,seconds=time.monotonic()-START,server_writes=0,forward_calls=0,checkpoint_deserialization=False)),flush=True);raise
