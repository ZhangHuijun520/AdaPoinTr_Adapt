"""Freeze local P3 and final pending request/bundle; never connects or executes prediction."""
import ast,hashlib,io,json,shutil,tarfile
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];H=HERE.parent/'H1_implementation_v1'
P1=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104'
OUT=HERE/'pending_request_v1';REMOTE='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def emit(p,v):
 raw=(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
 if p.exists():
  assert p.read_bytes()==raw,'existing local preparation differs: '+str(p)
 else:
  with p.open('xb') as f:f.write(raw)
result_path=HERE/'artificial_cpu_batch_v1/result_v1.json';result=read(result_path)
assert result['status']=='ARTIFICIAL_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==38
assert not (HERE/'artificial_cpu_batch_v1/failure_v1.json').exists()
static=read(HERE/'static_review_v1.json')
for r in static['files']:assert sha(HERE/r['name'])==r['sha256']
entry=HERE/'bcsp_p2_h1_twofold_predict_v1.py';parent=P1/'paired_development_evaluator_v2/bcsp_p1_paired_predict_v2.py'
def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
A=nodes(parent);B=nodes(entry)
inherited=['load_partial','load_checkpoint','predict_once','ExactSourceReads','source_module','load_p1_factory','make_policy','Budget','pack','rng_state','geometry_summary']
assert all(A[n]==B[n] for n in inherited)
assert sha(parent)=='7f31ecddfed05bd49f3e42093b99477643ddce733dadbebb80f58d08f17f5d1c'
assert read(P1/'paired_development_evaluator_v2/local_P3_v2.json')['static_parse'] is True
for name,h in [('bcsp_p1_model_factory_v1.py','59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4'),('bcsp_mamba_encoder_v1.py','5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8')]:
 assert sha(P1/'minimal_implementation_v1'/name)==h
p3=dict(status='LOCAL_H1_TWOFOLD_PREDICTION_P3_PASS',entry_sha256=sha(entry),test_sha256=sha(HERE/'test_h1_twofold_cpu_v1.py'),
 CPU_result_sha256=sha(result_path),CPU_contracts=38,parent_entry_sha256=sha(parent),inherited_AST_unchanged=inherited,
 review_checks=dict(full_twofold_index_and_provenance=True,real_formal_training_audit_metadata_validated=True,H1_exact_config_only=True,
   native_model_parameters_and_checkpoint_schema_unchanged=True,partial_only_no_GT_input=True,exact_210_synthetic_predictions=True,
   per_fold105_and_manifest_fold=True,per_fold_coarse_representatives7and5=True,state_BN_RNG_preserved=True,
   failure_RNG_state_nonfinite_stop_no_second_model=True,exact_source_read_write_drift_checks=True,
   actual_checkpoint_loader_on_artificial_weights=True,inherited_source_reader_and_file_policy_AST_unchanged=True,
   no_extra_forward_loss_backward_optimizer_BNCal=True),
 real_models_loaded=0,real_checkpoints_loaded=0,real_point_payloads_read=0,server_operations=0,CUDA_tests_run=0,
 limitations=['CPU uses tiny synthetic models, artificial checkpoint and NPZ; no native Mamba/PointNet2/CUDA runtime verification',
  'Source read policy behavior inherited from exact audited P1 implementation; safety functions checked for AST equality',
  'Server readiness/identity/asset hashes must be checked before authorized installation and execution'])
emit(HERE/'implementation_P3_v1.json',p3)
OUT.mkdir(exist_ok=True);payload=OUT/'transport_payload';payload.mkdir(exist_ok=True);mapping=[]
def stage(p,name):
 dest=payload/name
 if dest.exists():assert dest.read_bytes()==p.read_bytes(),'existing staged bytes differ'
 else:
  with dest.open('xb') as f:f.write(p.read_bytes())
 r=dict(path=REMOTE+'/'+name,bytes=dest.stat().st_size,sha256=sha(dest));mapping.append(dict(local=str(dest),target=r['path'],bytes=r['bytes'],sha256=r['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'));return r
base=read(P1/'paired_development_evaluator_v2/transport_payload/FoldC_T0_M0_development_execution_request_v2.json');q=dict(base);q.pop('pair_receipt')
q.update(schema='bcsp-p2-H1-twofold-development-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='CRANIAL_BCSP_MAMBA_P2_H1',
 run_id='C_D_M_H1_development_20261106_v1',fold='C_D',seed=0,batch_size=1,unique_cases=210,forward_budget=210,backward=0,optimizer_steps=0,BNCal=0,loss_calls=0,
 output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1/C_D_M_H1_development_20261106_v1',launch_attempt=REMOTE+'/control/single_attempt_claim_v1.json')
q['entry']=stage(entry,entry.name)
q['input_index']=stage(HERE/'H1_C_D_input_index_v1.json','H1_C_D_input_index_v1.json')
q['protocol']=stage(HERE/'H1_C_D_prediction_protocol_v1.json','H1_C_D_prediction_protocol_v1.json')
q['P3']=stage(HERE/'implementation_P3_v1.json','implementation_P3_v1.json')
q['training_audits']={'C':stage(H/'post_training_freeze_audit_v1/audit_report_v1.json','H1_C_post_training_freeze_audit_v1.json'),
 'D':stage(H/'FoldD_request_v1/post_training_freeze_audit_v1/audit_report_v1.json','H1_D_post_training_freeze_audit_v1.json')}
stage(result_path,'CPU_contract_result_v1.json')
q['static_config']=read(H/'first_FoldC_request_v1/transport_payload/M_H1_foldC_seed0_training_execution_request_v1.json')['static_config']
q['limits']=dict(wall_seconds=7200,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296)
out=q['output'];control=REMOTE+'/control';request_name='H1_C_D_development_execution_request_v1.json'
q['launch_contract']=dict(tmux_session='bcsp_p2_H1_CD_eval_20261106_v1',authorization=control+'/prediction_authorization_v1.json',runtime=control+'/prediction_runtime_v1.json',launcher=control+'/prediction_launch_once_v1.sh',log=out+'/launch.log',pid=out+'/worker.pid',exit_code=out+'/exit_code.txt',single_attempt=True,timeout_seconds=7200,
 materialization_order='authorization -> hash -> runtime -> hash -> launcher; exclusive claim before unique tmux',parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,
 transport='Original bytes, lossless compressed Base64 short envelope <=2048 bytes; never multiline long terminal payload',
 launcher_argv_template=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','7200s',q['identity']['python_realpath'],'-I','-S','-B',q['entry']['path'],
 '--request',REMOTE+'/'+request_name,'--request-sha256','<THIS_REQUEST_SHA256>','--authorization',control+'/prediction_authorization_v1.json','--authorization-sha256','<AUTHORIZATION_SHA256>',
 '--runtime',control+'/prediction_runtime_v1.json','--runtime-sha256','<RUNTIME_SHA256>'])
q['installation_prerequisites']=['Current hostname/UID/Python/GPU match exact frozen identity; idle GPU and disk thresholds pass',
 'Uploaded package and four sidecars exact; all new installation targets absent; parents real and inside project',
 'Two H1 checkpoints measured SHA256/bytes match; both training freezes and all reused source/provider/numeric/config bindings match',
 'All210 exact allowlisted partial input file hashes and fixed source/target/frame metadata match',
 'No materialization or unique launch claim before separate full request SHA256 execution authorization; any failure stops']
q['not_authorized']=['Execution before separate complete request hash authorization','New training/BNCal/backward/loss/optimizer steps','M0/T0 baseline re-inference',
 'Warmup, TTA, ICP/GT alignment, new cases or protected data','Automatic retry/resume','Repeated GPU preflight','Scoring/bootstrap/formal gate in prediction',
 'Dependency download/build/install/upgrade','Changing H1, point counts, source order or resource limits']
q['provenance']=dict(purpose='Native frozen H1 C105+D105 prediction; compare later to frozen P1 M0 archive without baseline forwards',
 H1_C_D_training_formally_frozen=True,current_server_rechecked=False,
 identity_source='Last frozen v2iwsa-0 identity; not assumed still current',
 implementation_scope='One isolated twofold entry; unchanged P1 model/factory/encoder/provider and reused read/state guards',
 prior_CPU_pass_is_not_CUDA_or_performance_pass=True,repeat_GPU_preflight_authorized=False,
 training_or_prediction_started=False,baseline_archive_payload_verification_before_scoring_required=True,
 checkpoints_schema='BCSP_INPUT_DENSITY_V1 stage retained as provenance, H1 identity established by exact hash and P2 audit',
 expected_counts=dict(models=2,forwards_C=105,forwards_D=105,total_forwards=210,loss_calls=0,backward=0,optimizer_steps=0,BNCal=0))
assert q['launch_contract']['launcher_argv_template'][8]==q['entry']['path']
assert PurePosixPath(q['launch_contract']['authorization']).parent==PurePosixPath(control)
request=payload/request_name;emit(request,q)
mapping.append(dict(local=str(request),target=REMOTE+'/'+request.name,bytes=request.stat().st_size,sha256=sha(request),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
reused={k:q[k] for k in ['model_root','preflight_scope','static_config','numeric_policy','source_index','source_manifest','fold_binding','helper','implementation','dependencies']}
emit(OUT/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED',remote_root=REMOTE,files=mapping,reused_exact_bindings=reused,server_rechecked=False,
 materials_not_created=[q['launch_contract'][k] for k in ['authorization','runtime','launcher']]+[q['launch_attempt'],q['output']]))
archive=OUT/'bcsp_p2_H1_twofold_prediction_pending_20261106_v1.tar.gz'
members=[(p,'payload/'+p.name) for p in sorted(payload.iterdir())]+[(OUT/'installation_mapping_v1.json','installation_mapping_v1.json')]
with tarfile.open(archive,'w:gz') as t:
 for path,name in members:
  raw=path.read_bytes();info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o600;info.mtime=0;t.addfile(info,io.BytesIO(raw))
Path(str(archive)+'.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
Path(str(archive)+'.bytes').write_text(str(archive.stat().st_size)+'\n',encoding='ascii')
Path(str(archive)+'.contents.sha256').write_text(''.join(sha(p)+'  '+n+'\n' for p,n in members),encoding='utf-8')
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_path=str(request.absolute()),request_sha256=sha(request),archive_path=str(archive.absolute()),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,new_install_files=len(mapping),CPU_contracts=38,P3=p3['status'],prediction_budget=210,server_operations=0,controls_materialized=False,predictions_executed=0)
emit(OUT/'preparation_receipt_v1.json',receipt)
print(json.dumps({k:receipt[k] for k in ['status','request_sha256','archive_sha256','archive_bytes','new_install_files','CPU_contracts']}))
