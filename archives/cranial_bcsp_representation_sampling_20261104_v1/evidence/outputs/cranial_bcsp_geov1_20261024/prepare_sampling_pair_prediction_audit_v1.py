"""Bind the successful prior prediction auditor to this exact paired attempt."""
import ast,base64,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1';A=N/'authorized_execution_v1';F=N/'freeze_audit_v1'
SHA='76673ba94626253161dc70f0a33006d21c8094bced8148496c68c6c3490f0f4c'
def h(b):return hashlib.sha256(b).hexdigest()
def save(n,b):
 with (F/n).open('xb') as f:f.write(b)
def main():
 sr=(N/'development_execution_request_v1.json').read_bytes();assert h(sr)==SHA;s=json.loads(sr)
 qr=Path(s['entry_request']['path']).read_bytes();assert h(qr)==s['entry_request']['sha256'];q=json.loads(qr)
 events=json.loads((A/'execute_once_events.json').read_bytes());controls=next(x['files'] for x in events if x.get('status')=='EVALUATION_MATERIALIZED_ATTEMPT_CLAIMED')
 assert len(controls)==219 and controls[:213]==[dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']) for r in s['install_mapping']]
 obs=json.loads((A/'prediction_observation_02_result.json').read_bytes());assert obs['exit_code']=='0' and obs['prediction_records']==210
 spec=dict(schema='bcsp-sampling-pair-readonly-post-prediction-audit-v1',outer_sha256=SHA,inner_sha256=h(qr),identity=q['identity'],output=q['output'],control=q['control'],session=s['tmux_session'],controls=controls,reused_assets=s['reused_assets'],observed_archive=obs['completion_archive'],limits=dict(read_bytes=2147483648,wall_seconds=90),read_scope='Exact213 installed files and6controls;two checkpoint stream hashes and frozen assets;210 live predictions;213-member archive andfour download files;complete output tree',server_writes=0,model_imports=0,checkpoint_deserialization=False,CUDA_calls=0,forward_calls=0,scoring_executed=False)
 code=(B/'development_eval_v1/post_prediction_freeze_audit_v1.py').read_text(encoding='utf-8')
 code=code.replace('len(runs)==4 and len(inputs)==420', 'len(runs)==2 and len(inputs)==210').replace("['C_8192','C_16384','D_8192','D_16384']","['C_V1','C_Morton_area_stratified8k']")
 code=code.replace("need(set(folds['folds']['C']['dev_sources']).isdisjoint(folds['folds']['D']['dev_sources']),'OOF source disjointness')", "need(len(folds['folds']['C']['dev_sources'])==21 and set(folds['folds']['C']['dev_sources']).isdisjoint(folds['folds']['C']['train_sources']),'Fold C source separation')")
 code=code.replace("log.count(b'MODEL - INFO - Transformer with config')==4", "log.count(b'MODEL - INFO - Transformer with config')==2")
 code=code.replace('len(records)==420','len(records)==210').replace("for x in records})==420","for x in records})==210").replace('range(1,421)','range(1,211)')
 code=code.replace('FOUR_MODEL_420_FORWARD_COMPLETE','SAMPLING_PAIR_210_FORWARD_COMPLETE').replace("completion['forwards']==420","completion['forwards']==210").replace("len(done['models'])==4","len(done['models'])==2")
 code=code.replace("('all_complete',420)","('all_complete',210)").replace('forwards=420','forwards=210').replace('==423','==213')
 code=code.replace('exact845','exact423').replace('845_resource','423_resource').replace('archive423','archive213').replace('sidecar exact423','sidecar exact213').replace('four_checkpoint','two_checkpoint').replace('four_models_105_dev_cases_each_42_disjoint_OOF_sources','two_models_105_dev_cases_each_21_shared_development_sources').replace('consecutive420_records_four105','consecutive210_records_two105').replace('420_live_prediction','210_live_prediction')
 # Add exact one-way grant and installed mapping checks, not a model invocation.
 code=code.replace("bool(auth['user_authorization_text'].strip())", "SPEC['outer_sha256'] in auth['user_authorization_text']")
 anchor=" PHASE='complete_output_set'"
 addition=''' need({p.name for p in safe(SPEC['control']).iterdir()}=={'execution_scope.json','entry_request.json','authorization.json','runtime.json','evaluate_once.sh','launch_attempt.json'},'exact six control files')
 need(SPEC['controls'][:213]==[dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']) for r in outer['install_mapping']],'installed mapping equality')
 need(len(SPEC['controls'])==219 and len({r['path'] for r in SPEC['controls']})==219,'exact219 installation/control bindings')
 need(q['schema']=='bcsp-sampling-pair-development-prediction-v1' and q['science']['total_forwards']==210 and q['science']['training_updates']==0,'paired request science')
 for r in SPEC['reused_assets']:exact(r)
 for r in [q['static_config'],q['preflight_scope'],q['helper'],q['input_index'],q['paired_data_receipt']]:exact(r)
 receipt=json.loads(read(q['paired_data_receipt']['path']))
 need(receipt['status']=='PAIRED_105_CASES_210_INPUTS_VERIFIED' and receipt['GT_equal'] and receipt['common_input_permutation'],'paired dev receipt')
 for a,b in zip(inputs[:105],inputs[105:]):
  need(a['arm']=='V1' and b['arm']=='Morton_area_stratified8k' and all(a[k]==b[k] for k in ['case_id','source_id','normalization','target_array_sha256','common_point_order_sha256']),'paired target/frame/order metadata')
  for row in [a,b]:need(row['input']['path']==index['data_root']+'/'+row['arm']+'/points/'+row['case_id']+'_8192.npz','exact dev payload path')
 good('all219_installed_files_controls_and_bound_source_provider_checkpoint_hashes_verified')
 good('same105_cases_GT_frame_permutation_and_source_exclusion')
'''
 assert code.count(anchor)==1;code=code.replace(anchor,addition+anchor)
 anchor="  need(m['CPU_rng_before']==m['CPU_rng_after'] and len(m['CPU_rng_before'])==64,'recorded CPU RNG invariance')"
 assert code.count(anchor)==1
 code=code.replace(anchor,anchor+"\n  need(m['CUDA_rng_before']==m['CUDA_rng_after'] and len(m['CUDA_rng_before'])==64 and m['Python_numpy_RNG_unchanged'] is True,'recorded CUDA/Python/NumPy RNG invariance')")
 code=code.replace("need(read(out/'worker.pid',64).strip().isdigit(),'worker PID format')", "need(read(out/'worker.pid',64).strip().isdigit(),'worker PID format')\n need(not Path('/proc/'+read(out/'worker.pid',64).decode().strip()).exists(),'worker still live')")
 code=code.replace('state and CPU RNG evidence verified;CUDA RNG state was not recorded','state and CPU/CUDA RNG fingerprints plus Python/NumPy invariant assertion verified; no independent reconstruction')
 # Track content-relevant stamps for all reads; atime is intentionally excluded.
 code=code.replace("START=time.monotonic();READ=0;PHASE='identity';CHECKS=[]", "START=time.monotonic();READ=0;PHASE='identity';CHECKS=[];HASH_CACHE={};READ_STAMPS={}")
 code=code.replace("def read(p,cap=4194304):", "def stamp(p):\n s=Path(p).stat();return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns)\ndef inventory(out):\n found={}\n for p in [out,*out.rglob('*')]:\n  safe(p);need(p.is_file() or p.is_dir(),'special output');need(len(found)<512,'output inventory count');found[str(p)]=stamp(p)\n return found\ndef read(p,cap=4194304):")
 code=code.replace("raw=p.read_bytes();budget(len(raw));return raw", "before=stamp(p);raw=p.read_bytes();budget(len(raw));need(stamp(p)==before,'file changed during read: '+str(p));READ_STAMPS[str(p)]=before;return raw")
 code=code.replace("p=safe(p);st=p.stat();need(p.is_file()", "p=safe(p)\n if str(p) in HASH_CACHE:return HASH_CACHE[str(p)]\n st=p.stat();need(p.is_file()")
 code=code.replace("return dict(path=str(p),bytes=st.st_size,sha256=h.hexdigest())", "result=dict(path=str(p),bytes=st.st_size,sha256=h.hexdigest());HASH_CACHE[str(p)]=result;READ_STAMPS[str(p)]=stamp(p);return result")
 code=code.replace("out=safe(SPEC['output']);need(out.is_dir(),'output directory')", "out=safe(SPEC['output']);need(out.is_dir(),'output directory');TREE_BEFORE=inventory(out)")
 anchor=" result=dict(status='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS'"
 addition=''' output_manifest=[hashed(p) for p in sorted(out.rglob('*')) if p.is_file()]
 need(len(output_manifest)==221,'exact221 output files')
 need(inventory(out)==TREE_BEFORE,'output tree changed during audit')
 need(all(stamp(p)==s for p,s in READ_STAMPS.items()),'bound read files changed during audit')
 good('complete221_file_output_manifest_and_all_read_fingerprints_stable_atime_excluded')
'''
 assert code.count(anchor)==1;code=code.replace(anchor,addition+anchor)
 code=code.replace("checkpoint_hashes=checkpoints,control_hashes=controls,", "checkpoint_hashes=checkpoints,control_hashes=controls,output_manifest=output_manifest,")
 code=code.replace('archive_members=423','archive_members=213')
 # Check the emitted semantic counts after adaptation, before execution.
 assert 'forwards=420' not in code and '==420' not in code and '==423' not in code and 'range(1,421)' not in code
 ast.parse(code)
 F.mkdir();save('scope.json',json.dumps(spec,indent=2).encode());save('readonly_audit_source_v1.py',code.encode())
 payload=b'import base64,json\nSPEC=json.loads(base64.b64decode('+repr(base64.b64encode(json.dumps(spec).encode()).decode()).encode()+b'))\n'+code.encode()
 ast.parse(payload);save('frozen_payload.py',payload)
 template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_bytes();assert h(template)=='c705224bc0ffa2e094ff0b4a69ed4ba582480178a63a2bb3fa2e91757e31fd26'
 driver=template.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(payload).encode());ast.parse(driver);save('short_driver.py',driver)
 save('static_review_v1.json',json.dumps(dict(status='STATIC_PASS',auditor_sha256=h(code.encode()),payload_sha256=h(payload),driver_sha256=h(driver),read_only=True,counts=dict(models=2,forwards=210,resource_records=423,archive_members=213,installed_and_controls=219,output_files=221),limits=spec['limits'],no_model_or_checkpoint_load=True),indent=2).encode())
 print('PAIRED_PREDICTION_AUDIT_FROZEN_STATIC_PASS')
if __name__=='__main__':main()
