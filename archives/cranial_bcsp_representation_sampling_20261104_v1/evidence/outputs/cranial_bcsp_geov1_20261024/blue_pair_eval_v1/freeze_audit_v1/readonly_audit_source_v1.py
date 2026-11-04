"""In-memory server audit. SPEC is frozen locally; stdlib only; no server writes."""
import array,ast,datetime,hashlib,io,json,math,os,shutil,socket,struct,subprocess,sys,tarfile,time,zipfile
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
def array_contract(blob):
 with zipfile.ZipFile(io.BytesIO(blob)) as z:
  names=z.namelist();need(names==['prediction.npy'],'NPZ exact prediction-only member')
  info=z.getinfo(names[0]);need(info.file_size<=1048576 and not info.flag_bits&1,'NPZ array size/encryption')
  raw=z.read(names[0]);need(raw[:6]==b'\x93NUMPY','NPY magic');version=raw[6:8]
  if version==b'\x01\x00':offset=10;size=struct.unpack('<H',raw[8:10])[0]
  elif version in [b'\x02\x00',b'\x03\x00']:offset=12;size=struct.unpack('<I',raw[8:12])[0]
  else:raise RuntimeError('NPY version')
  need(size<=65536 and offset+size<=len(raw),'NPY header length')
  hdr=ast.literal_eval(raw[offset:offset+size].decode('utf-8' if version==b'\x03\x00' else 'latin1').strip())
  need(hdr==dict(descr='<f4',fortran_order=False,shape=(8192,3)),'NPY float32/8192x3 schema')
  data=raw[offset+size:];need(len(data)==8192*3*4,'NPY exact tensor bytes')
  values=array.array('f');need(values.itemsize==4,'host float width');values.frombytes(data)
  if sys.byteorder!='little':values.byteswap()
  need(all(math.isfinite(x) for x in values),'nonfinite prediction')

try:
 need(socket.gethostname()==SPEC['identity']['hostname'] and os.getuid()==SPEC['identity']['uid'],'current container identity')
 os.chdir('/home/jovyan/adapointr_work/PoinTr');need(str(Path.cwd())=='/home/jovyan/adapointr_work/PoinTr','project root')
 out=safe(SPEC['output']);need(out.is_dir(),'output directory');TREE_BEFORE=inventory(out)
 alive=subprocess.run(['/usr/bin/tmux','has-session','-t',SPEC['session']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
 need(alive.returncode==1,'evaluation session still active/tmux unavailable')
 need(read(out/'exit_code.txt',64).strip()==b'0','exit code not0')
 good('identity_correct_session_ended_exit0')
 PHASE='controls_and_frozen_models'
 controls=[exact(r) for r in SPEC['controls']]
 outer=json.loads(read(SPEC['control']+'/execution_scope.json'));q=json.loads(read(SPEC['control']+'/entry_request.json'))
 need(outer['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and outer['execution_authorized'] is False,'immutable outer pending request')
 need(hashlib.sha256(read(SPEC['control']+'/execution_scope.json')).hexdigest()==SPEC['outer_sha256'],'outer request identity')
 need(hashlib.sha256(read(SPEC['control']+'/entry_request.json')).hexdigest()==SPEC['inner_sha256'],'inner request identity')
 auth_path=SPEC['control']+'/authorization.json';auth_raw=read(auth_path);auth=json.loads(auth_raw);runtime=json.loads(read(SPEC['control']+'/runtime.json'))
 need(set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-development-authorization-v1' and auth['request_sha256']==SPEC['inner_sha256'] and auth['explicit_user_authorization'] is True and SPEC['outer_sha256'] in auth['user_authorization_text'],'explicit acyclic authorization')
 need(runtime==dict(schema='bcsp-development-runtime-v1',request_sha256=SPEC['inner_sha256'],authorization_sha256=hashlib.sha256(auth_raw).hexdigest()),'runtime one-way authorization SHA')
 need(json.loads(read(SPEC['control']+'/launch_attempt.json'))==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=SPEC['inner_sha256']),'single-use attempt claim')
 exact(q['fold_binding']);folds=json.loads(read(q['fold_binding']['path']));index=json.loads(read(q['input_index']['path']));runs=index['runs'];inputs=index['inputs']
 need(len(runs)==2 and len(inputs)==210 and [r['label'] for r in runs]==['C_Euclidean_elimination','C_surface_graph'],'fixed four-run identity/order')
 models={r['label']:r for r in runs};checkpoints=[exact(r['checkpoint']) for r in runs]
 need(len(folds['folds']['C']['dev_sources'])==21 and set(folds['folds']['C']['dev_sources']).isdisjoint(folds['folds']['C']['train_sources']),'Fold C source separation')
 for r in runs:
  f=folds['folds'][r['fold']];part=[i for i in inputs if i['run']==r['label']]
  need(r['dev_case_ids']==f['dev_case_ids']==[i['case_id'] for i in part] and len(part)==len(set(i['case_id'] for i in part))==105,'105 exact ordered dev cases/run')
  need(r['dev_sources']==f['dev_sources'] and len(set(r['dev_sources']))==21 and not set(r['dev_sources'])&set(f['train_sources']),'own train/dev source exclusion')
  for i in part:need(i['source_id']=='train:'+i['case_id'].split('__')[1] and i['source_id'] in r['dev_sources'],'input source identity')
 good('controls_authorization_runtime_claim_unchanged_and_two_checkpoint_SHA_recomputed')
 good('two_models_105_dev_cases_each_21_shared_development_sources')
 need({p.name for p in safe(SPEC['control']).iterdir()}=={'execution_scope.json','entry_request.json','authorization.json','runtime.json','evaluate_once.sh','launch_attempt.json'},'exact six control files')
 need(SPEC['controls'][:213]==[dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']) for r in outer['install_mapping']],'installed mapping equality')
 need(len(SPEC['controls'])==219 and len({r['path'] for r in SPEC['controls']})==219,'exact219 installation/control bindings')
 need(q['schema']=='bcsp-blue-noise-pair-development-prediction-v1' and q['science']['total_forwards']==210 and q['science']['training_updates']==0,'paired request science')
 for r in SPEC['reused_assets']:exact(r)
 for r in [q['static_config'],q['preflight_scope'],q['helper'],q['input_index'],q['paired_data_receipt']]:exact(r)
 receipt=json.loads(read(q['paired_data_receipt']['path']))
 need(receipt['status']=='PAIRED_105_CASES_210_INPUTS_VERIFIED' and receipt['GT_equal'] and receipt['common_input_permutation'],'paired dev receipt')
 for a,b in zip(inputs[:105],inputs[105:]):
  need(a['arm']=='Euclidean_elimination' and b['arm']=='surface_graph' and all(a[k]==b[k] for k in ['case_id','source_id','normalization','target_array_sha256','common_point_order_sha256']),'paired target/frame/order metadata')
  for row in [a,b]:need(row['input']['path']==index['data_root']+'/'+row['arm']+'/points/'+row['case_id']+'_8192.npz','exact dev payload path')
 good('all219_installed_files_controls_and_bound_source_provider_checkpoint_hashes_verified')
 good('same105_cases_GT_frame_permutation_and_source_exclusion')
 PHASE='complete_output_set'
 archive_name='development_predictions_v1.tar.gz'
 expected_names={'predictions','tmp','launch.log','worker.pid','resources.jsonl','inference_manifest.jsonl','inference_complete.json','completion.json','exit_code.txt',archive_name,archive_name+'.sha256',archive_name+'.bytes',archive_name+'.contents.sha256'}
 need({p.name for p in out.iterdir()}==expected_names,'unexpected/missing output root entries')
 for p in out.iterdir():safe(p)
 temp=safe(out/'tmp');temp_items=list(temp.rglob('*'));need(len(temp_items)<=64,'temp metadata count')
 for p in temp_items:need(not p.is_symlink() and p.suffix.lower() not in {'.pth','.pt','.ckpt','.npz','.npy','.nrrd','.stl','.ply'},'unexpected temp link/payload')
 need(read(out/'worker.pid',64).strip().isdigit(),'worker PID format')
 need(not Path('/proc/'+read(out/'worker.pid',64).decode().strip()).exists(),'worker still live')
 log=read(out/'launch.log');need(b'Traceback (most recent call last)' not in log and log.count(b'MODEL - INFO - Transformer with config')==2,'startup log four models/no traceback')
 records=[json.loads(line) for line in read(out/'inference_manifest.jsonl').splitlines()]
 done=json.loads(read(out/'inference_complete.json'));completion=json.loads(read(out/'completion.json'))
 need(len(records)==210 and len({(x['run'],x['case_id']) for x in records})==210,'manifest420 distinct records')
 need([x['forward_index'] for x in records]==list(range(1,211)),'consecutive forward indices1..420')
 need(done['status']=='BLUE_NOISE_PAIR_210_FORWARD_COMPLETE' and completion['status']=='PREDICTIONS_ARCHIVED_AWAITING_LOCAL_SCORING' and done['forwards']==completion['forwards']==210,'successful completion counters')
 need(done['request_sha256']==completion['request_sha256']==SPEC['inner_sha256'],'completion request identity')
 need(all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']),'forbidden action counters')
 need(len(done['models'])==2 and [m['run'] for m in done['models']]==list(models),'complete model state records')
 for m in done['models']:
  need(m['forwards']==105 and len(m['state_before'])==64 and m['state_before']==m['state_after'],'parameters/BN buffers invariant')
  need(m['CPU_rng_before']==m['CPU_rng_after'] and len(m['CPU_rng_before'])==64,'recorded CPU RNG invariance')
  need(m['CUDA_rng_before']==m['CUDA_rng_after'] and len(m['CUDA_rng_before'])==64 and m['Python_numpy_RNG_unchanged'] is True,'recorded CUDA/Python/NumPy RNG invariance')
  need(m['mode']=='eval_inference_mode' and m['BNCal']==m['optimizer']==m['backward']==0,'eval-only model evidence')
 good('consecutive210_records_two105_forwards_model_and_recorded_CPU_RNG_invariance_zero_updates_BNCal')
 PHASE='individual_predictions'
 expected_files=[];live={};counts={label:0 for label in models}
 for observed,wanted in zip(records,inputs):
  label=wanted['run'];need((observed['run'],observed['case_id'],observed['source_id'],observed['fold'],observed['n_input'])==(label,wanted['case_id'],wanted['source_id'],wanted['fold'],wanted['n_input']),'prediction identity/order mismatch')
  need(observed['n_output']==8192 and observed['input_sha256']==wanted['input']['sha256'] and observed['checkpoint_sha256']==models[label]['checkpoint']['sha256'],'input/checkpoint provenance')
  name='predictions/'+label+'__'+wanted['case_id']+'.npz';r=observed['prediction'];need(r['name']==name,'prediction exact filename')
  raw=read(out/name,1048576);actual=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
  need(actual['bytes']==r['bytes'] and actual['sha256']==r['sha256'],'prediction bytes/hash: '+name);array_contract(raw)
  expected_files.append(name);live[name]=actual;counts[label]+=1
 need({p.name for p in (out/'predictions').iterdir()}=={Path(n).name for n in expected_files},'prediction directory strict set')
 need(all(v==105 for v in counts.values()),'per-run105')
 good('210_live_prediction_SHA_and_regular_NPZ_finite_float32_8192x3_independently_verified')
 PHASE='resource_log'
 resources=[json.loads(x) for x in read(out/'resources.jsonl').splitlines()];sequence=[];offset=0
 for label in models:
  sequence.append(('model_start:'+label,offset))
  for k in range(105):sequence.extend([('before_forward',offset+k),('after_forward',offset+k+1)])
  offset+=105
 sequence.append(('all_complete',210));need([(r['phase'],r['forwards']) for r in resources]==sequence,'exact423 resource phase/count records')
 L=q['limits'];previous=-1;maxima={k:0 for k in ['RSS_bytes','device_MiB','peak_allocated','peak_reserved','output_bytes']}
 for r in resources:
  v=r['values'];need(all(isinstance(x,(int,float)) and math.isfinite(x) for x in v.values()),'finite resource values')
  recomputed=dict(RSS=v['RSS_bytes']<=L['RSS_bytes'],output=v['output_bytes']<=L['output_bytes'],device=v['device_MiB']<=L['device_MiB'],allocated=v['peak_allocated']<=L['torch_peak_bytes'],reserved=v['peak_reserved']<=L['torch_peak_bytes'],wall=v['elapsed_seconds']<=L['wall_seconds'],disk=v['free_disk_bytes']>=L['minimum_free_disk_bytes'])
  need(r['checks']==recomputed and all(recomputed.values()) and not r['failed_checks'],'resource guard result mismatch/failure')
  need(v['elapsed_seconds']>=previous,'resource time ordering');previous=v['elapsed_seconds']
  need(r['PID_policy']=='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE','PID policy changed')
  for k in maxima:maxima[k]=max(maxima[k],v[k])
 good('423_resource_records_exact_sequence_and_original_thresholds_independently_recomputed')
 PHASE='archive_and_sidecars'
 for name in ['inference_manifest.jsonl','inference_complete.json','resources.jsonl']:
  data=read(out/name);live[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest());expected_files.append(name)
 receipt=completion['archive'];need(receipt['path']==str(out/archive_name),'archive exact path')
 archive=hashed(out/archive_name,67108864);need(all(archive[k]==receipt[k]==SPEC['observed_archive'][k] for k in ['path','bytes','sha256']),'independent archive hash/size binding')
 need([r['name'] for r in receipt['members']]==expected_files and len(receipt['members'])==213,'completion archive member order/count')
 for r in receipt['members']:need(r['bytes']==live[r['name']]['bytes'] and r['sha256']==live[r['name']]['sha256'],'archive member receipt/live equality')
 with tarfile.open(out/archive_name,'r:gz') as t:
  members=t.getmembers();need(len(members)==213 and [m.name for m in members]==expected_files and len({m.name for m in members})==213,'tar exact member order/set/no duplicates')
  total=0
  for m in members:
   need(m.isfile() and m.size==live[m.name]['bytes'] and m.size<=4194304,'tar regular exact-size member')
   blob=t.extractfile(m).read();total+=len(blob);budget(len(blob));need(total<=67108864 and hashlib.sha256(blob).hexdigest()==live[m.name]['sha256'],'tar payload integrity: '+m.name)
 need(read(out/(archive_name+'.sha256'),1024).decode()==archive['sha256']+'  '+archive_name+'\n','SHA256 sidecar exact contents')
 need(read(out/(archive_name+'.bytes'),128).decode()==str(archive['bytes'])+'\n','bytes sidecar exact contents')
 content=''.join(live[n]['sha256']+'  '+n+'\n' for n in expected_files)
 need(read(out/(archive_name+'.contents.sha256'),131072).decode()==content,'content sidecar exact213 hashes/order')
 downloads=[archive]+[hashed(out/(archive_name+suffix),131072) for suffix in ['.sha256','.bytes','.contents.sha256']]
 total_output=sum(p.stat().st_size for p in out.rglob('*') if p.is_file());need(total_output<=L['output_bytes'],'actual final output bytes')
 good('archive213_members_match_live_files_and_all_four_download_artifacts_independently_hashed')
 good('strict_output_set_no_failure_receipt_no_weight_payload_in_prediction_archive')
 output_manifest=[hashed(p) for p in sorted(out.rglob('*')) if p.is_file()]
 need(len(output_manifest)==221,'exact221 output files')
 need(inventory(out)==TREE_BEFORE,'output tree changed during audit')
 need(all(stamp(p)==s for p,s in READ_STAMPS.items()),'bound read files changed during audit')
 good('complete221_file_output_manifest_and_all_read_fingerprints_stable_atime_excluded')
 result=dict(status='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),hostname=socket.gethostname(),uid=os.getuid(),
  outer_request_sha256=SPEC['outer_sha256'],inner_request_sha256=SPEC['inner_sha256'],checks=CHECKS,exit_code=0,forwards=210,unique_cases=len({i['case_id'] for i in inputs}),unique_sources=len({i['source_id'] for i in inputs}),per_run=counts,
  state_evidence=done['models'],training_updates=0,BNCal=0,loss=0,backward=0,resource_records=len(resources),resource_maxima=maxima,recorded_inference_budget_seconds=previous,
  checkpoint_hashes=checkpoints,control_hashes=controls,output_manifest=output_manifest,prediction_manifest=[dict(name=n,**live[n]) for n in expected_files],archive_members=213,download_files=downloads,
  actual_output_bytes=total_output,free_disk_bytes=shutil.disk_usage(out).free,read_bytes=READ,seconds=time.monotonic()-START,temporary_entry_count=len(temp_items),
  limitations=['Recorded model state and CPU/CUDA RNG fingerprints plus Python/NumPy invariant assertion verified; no independent reconstruction','No independent proof of CUDA numerical equality or clinical implant contact','Sampled resource monitoring is not a hard cgroup limit'],
  server_writes=0,checkpoint_deserialization=False,model_imports=0,CUDA_calls=0,forward_calls=0,scoring_executed=False,downloaded_to_Windows=False)
 print(json.dumps(result,allow_nan=False),flush=True)
except BaseException as exc:
 print(json.dumps(dict(status='FORMAL_POST_PREDICTION_FREEZE_AUDIT_FAILED_STOP',phase=PHASE,error=repr(exc),passed_checks=CHECKS,read_bytes=READ,seconds=time.monotonic()-START,server_writes=0,forward_calls=0,checkpoint_deserialization=False)),flush=True);raise
