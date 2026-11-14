"""Freeze final local evidence and pending request. No remote writes or GPU calls."""
import ast,hashlib,json,tarfile,shutil
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;B=S.parent
PROJECT='/home/jovyan/adapointr_work/PoinTr'
REMOTE=PROJECT+'/third_party/bcsp_f0_CD_condition_diagnostic_20261111_v1'
RUN='F0_CD_condition_diagnostic_20261111_v1'
def digest(b):return hashlib.sha256(b).hexdigest()
def rec(p,path=None):return dict(path=path or str(p.absolute()),bytes=p.stat().st_size,sha256=digest(p.read_bytes()))
def emit(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 O=S/'frozen_pending_transport_v1';O.mkdir();payload=O/'payload';payload.mkdir()
 cpu=json.loads((S/'artificial_cpu_batch_v1/result.json').read_bytes());integ=json.loads((S/'artificial_entry_integration_v1/result.json').read_bytes())
 assert cpu['status']=='ARTIFICIAL_CPU_CONTRACT_PASS' and cpu['count']==34 and integ['status']=='ARTIFICIAL_ENTRY_INTEGRATION_PASS' and integ['count']==7
 entry=S/'bcsp_f0_condition_diagnostic_v1.py';adapter=S/'bcsp_f0_condition_adapter_v1.py'
 for result in (cpu,integ):
  assert result['production_sources']==[rec(adapter),rec(entry)]
 sources=[entry,adapter,S/'test_f0_condition_cpu_v1.py',S/'test_condition_entry_integration_cpu_v1.py'];static=[]
 for p in sources:
  tree=ast.parse(p.read_text(encoding='utf-8'));compile(tree,str(p),'exec');static.append(rec(p))
 readiness=json.loads((S/'server_readiness_v1/assets_result.json').read_bytes());identity=json.loads((S/'server_readiness_v1/identity_result.json').read_bytes())
 assert readiness['status']=='EXACT40_CACHES_TWO_WEIGHTS_REUSED_SOURCES_PASS' and readiness['new_targets_absent'] and identity['GPU'][4]=='0'
 emit(S/'post_test_freeze_and_P3_v1.json',dict(status='F0_CONDITION_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],adapter_sha256=rec(adapter)['sha256'],
  checks=dict(final_sources_equal_both_CPU_batches=True,AST_compile_four_sources=True,actual_F0_tensor_CPU34=True,actual_entry_integration_CPU7=True,exact40_cache_two_weight_identity=True,new_targets_absent=True,
  frozen10_pairs_no_reselection=True,Native_replay_zero=True,no_GT_payload=True,exact30_suffix30_head720_native_SSM=True,encoder_coarse_optimizer_zero=True,original_F0_source_unchanged=True,
  prefix_and_local_hooks_isolated=True,exception_removes_hooks=True,original_head_two_max_pool_operations_preserved=True,state_BN_RNG_unchanged_CPU=True,raw_F_null_keeps_LN_beta_and_PE=True,
  per_layer_group_effects_not_accuracy=True,no_current_noise_floor_claim=True,no_extra_GPU_preflight=True,separate_full_hash_execution_required=True),
  evidence=[rec(S/'artificial_cpu_batch_v1/result.json'),rec(S/'artificial_entry_integration_v1/result.json'),rec(S/'server_readiness_v1/identity_result.json'),rec(S/'server_readiness_v1/assets_result.json')],
  static_sources=static,limitations=['CPU mixer is artificial; actual Mamba/CUDA intervention response not yet tested.','Entry-loop fixture is a lightweight suffix surrogate; tensor semantics tested separately.','Literal pair table was enumerated pre-Native, not proven pretraining.','Post-execution formal freeze audit required before scientific interpretation.'],
  scientific_gate='NOT_RUN_NO_STRUCTURAL_DECISION_NO_TRAINING',server_installation=0,GPU_diagnostic_calls=0))
 emit(S/'CPU_contract_evidence_v1.json',dict(tensor_batch=cpu,entry_batch=integ,original_result_records=[rec(S/'artificial_cpu_batch_v1/result.json'),rec(S/'artificial_entry_integration_v1/result.json')]))
 for p in [entry,adapter,S/'context_index_candidate_v1.json',S/'diagnostic_scope_v1.json',S/'post_test_freeze_and_P3_v1.json',S/'CPU_contract_evidence_v1.json']:
  shutil.copyfile(p,payload/p.name)
 old=json.loads((B/'Native_prediction_implementation_v1/resource_rebind_v2/transport_payload/F0_CD_native_prediction_execution_request_v2.json').read_bytes())
 scope=json.loads((S/'diagnostic_scope_v1.json').read_bytes())
 q={k:old[k] for k in ['identity','model_root','static_config','preflight_scope','dependencies','environment','limits','helper','implementation']}
 q.update(schema='f0-30-decoder-only-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='CRANIAL_BCSP_FULLMAMBA_9_2_CONDITION_DIAGNOSTIC',run_id=RUN,
  conditions=scope['conditions'],decoder_calls=30,head_calls=30,native_ssm_calls=720,encoder_calls=0,coarse_calls=0,Native_replay=0,loss_calls=0,backward=0,optimizer_steps=0,BNCal=0,training=0,GT_access=0,
  null_site=scope['null_site'],fixed_recipient=scope['fixed_recipient'],query_groups=scope['query_groups'],comparison=scope['comparison'],
  entry=rec(entry,REMOTE+'/'+entry.name),adapter=rec(adapter,REMOTE+'/'+adapter.name),
  context_index=rec(S/'context_index_candidate_v1.json',REMOTE+'/context_index_candidate_v1.json'),protocol=rec(S/'diagnostic_scope_v1.json',REMOTE+'/diagnostic_scope_v1.json'),
  P3=rec(S/'post_test_freeze_and_P3_v1.json',REMOTE+'/post_test_freeze_and_P3_v1.json'),CPU_evidence=rec(S/'CPU_contract_evidence_v1.json',REMOTE+'/CPU_contract_evidence_v1.json'),native_helper=old['entry'],
  selection_registration_timing='RULE_PRETRAINING_LITERAL_IDS_PRE_NATIVE_NOT_PRETRAINING',
  provenance_only_local_paths='Local evidence paths nested in index/P3 are provenance metadata; runtime never executes or reads Windows paths.',
  output=PROJECT+'/logs/cranial_bcsp_fullmamba/'+RUN,launch_attempt=REMOTE+'/control/decoder_diagnostic_single_attempt_claim_v1.json',
  single_attempt=True,automatic_retry=False,resume=False,post_execution_audit_required=True,
  scope_notes=['No re-run of Native, encoder, coarse predictor, query initializer, loss or optimizer.','Exactly three isolated interventions on the original ten frozen recipient/donor pairs.','All results are OOD sensitivity diagnostics, not official model performance.','No condition-response magnitude acceptance gate.','Keep existing numeric and resource thresholds.','No new training, hyperparameter search or structural change.'])
 L=dict(request_path=REMOTE+'/F0_CD_decoder_diagnostic_execution_request_v1.json',authorization=REMOTE+'/control/decoder_diagnostic_authorization_v1.json',runtime=REMOTE+'/control/decoder_diagnostic_runtime_v1.json',launcher=REMOTE+'/control/decoder_diagnostic_once_v1.sh',tmux_session='f0_cd_condition_20261111_v1',log=q['output']+'/launch.log',pid=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
 q['launch_contract']=L
 qfile=payload/'F0_CD_decoder_diagnostic_execution_request_v1.json';emit(qfile,q)
 # Verify the unchanged launcher renderer is path-safe, bounded and has the fixed timeout.
 import importlib.util,sys
 nativepath=B/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py'
 spec=importlib.util.spec_from_file_location('condition_launcher_static',nativepath);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 rendered=m.render_launcher(q,rec(qfile)['sha256'],'a'*64,'b'*64)
 assert q['entry']['path'] in rendered and 'mkdir -- '+q['output'] in rendered and max(map(len,rendered.splitlines()))<=2048
 assert '\\' not in str(PurePosixPath(L['launcher']).parent) and '7200s' in rendered
 emit(O/'launcher_render_static_review_v1.json',dict(status='PASS',materialized_launcher=False,line_max_bytes=max(len(l.encode()) for l in rendered.splitlines()),source_sha256=rec(nativepath)['sha256'],fixed_timeout_seconds=7200))
 files=[dict(member='payload/'+p.name,target=REMOTE+'/'+p.name,bytes=p.stat().st_size,sha256=digest(p.read_bytes()),overwrite=False) for p in sorted(payload.iterdir())]
 assert len(files)==7
 mapping=dict(status='FROZEN_PENDING_EXPLICIT_EXECUTION_AUTHORIZATION',remote_root=REMOTE,files=files,request_sha256=rec(qfile)['sha256'],
  pre_write='reconfirm hostname UID GPU, archive +3 sidecars, every7 target and new root/control/output absent, parent chain not symlink; exclusive creation only; abort on any mismatch',
  execution='only after separate authorization for request fullSHA; receipt -> SHA -> runtime -> launcher -> one claim -> one tmux attempt; stop first failure',
  not_materialized=[L['authorization'],L['runtime'],L['launcher'],q['launch_attempt'],q['output']],no_install_or_execution_performed=True)
 emit(O/'installation_mapping_v1.json',mapping)
 arc=O/'bcsp_f0_CD_condition_diagnostic_pending_20261111_v1.tar.gz'
 with arc.open('xb') as raw:
  with tarfile.open(fileobj=raw,mode='w:gz') as t:
   t.add(O/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
   for p in sorted(payload.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc,'r:gz') as t:
  members=t.getmembers();assert len(members)==8 and all(x.isfile() and x.size<1048576 for x in members)
  listing=''.join(digest(t.extractfile(x).read())+'  '+x.name+'\n' for x in members)
 for suffix,value in [('.sha256',digest(arc.read_bytes())+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:
  with Path(str(arc)+suffix).open('x',encoding='ascii') as f:f.write(value)
 emit(O/'transport_freeze_receipt_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_EXECUTION_AUTHORIZATION',request=rec(qfile),archive=rec(arc),members=8,install_files=7,server_writes=0,GPU_calls=0,authorization_materialized=False))
 print(json.dumps(dict(request_SHA256=rec(qfile)['sha256'],archive_SHA256=rec(arc)['sha256'],archive_bytes=arc.stat().st_size),indent=2))
if __name__=='__main__':main()
